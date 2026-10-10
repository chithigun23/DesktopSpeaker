#!/usr/bin/env python3
"""One-shot schematic/PCB sync for the sync-y200-c275 pass (2026-10-10).

1. Schematic MPN / Manufacturer / LCSC fields <- BOM CSV, keyed by reference designator, for every BOM row that
   has an LCSC code (PACK, test points and the J5 mating rows are skipped). Manufacturer names that are the same
   company (case, TI = Texas Instruments, ST = STMicroelectronics, Maxim = Analog Devices, Korean Hroparts [Elec])
   keep the schematic's long form; new names are written in canonical form (parenthetical notes stripped).
   The LCSC code goes into the symbol's existing 'LCSC' or 'LCSC Part' field; a missing field is added as 'LCSC'
   (cloned from the symbol's hidden Footprint property).
2. Value change C226/C227 22pF C0G -> 15pF C0G (Y200 12 pF replacement); Datasheet links for Y200 and C275
   (both were empty) set to the downloaded datasheets.
3. PCB: for every changed reference, the footprint gets all of the symbol's final fields except Reference and
   Footprint (Value, Datasheet, Description, MPN, Manufacturer, LCSC...; new ones are hidden F.Fab properties cloned
   from its Description property), so schematic/PCB field parity holds for that footprint.
4. C275 3D model: CP_Elec_8x10.step -> CP_Elec_6.3x7.7.step (KiCad library model, D8 size of the Panasonic
   EEH-ZA datasheet) on the PCB footprint and in kicad-library/footprint/CP_Elec_8x10.kicad_mod (C275 is the only
   user). Pads, courtyard and silk unchanged.
No wires, labels, pins, positions or references are touched.
Refuses to run twice (ai-files/backups/DesktopSpeaker.kicad_pcb.pre-sync must not exist).
Usage (project root): python3 ai-files/helpers/sync_y200_c275.py <path/to/CP_Elec_6.3x7.7.step>
"""
import csv, glob, json, os, re, shutil, sys, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KD = ROOT / 'DesktopSpeaker-kicad'
PCB = KD / 'DesktopSpeaker.kicad_pcb'
LIBFP = KD / 'kicad-library/footprint/CP_Elec_8x10.kicad_mod'
STEP_DST = KD / 'kicad-library/3d/CP_Elec_6.3x7.7.step'
BOM = ROOT / 'ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv'
BK = ROOT / 'ai-files/backups'
REPORT = ROOT / 'ai-files/reports/sync-y200-c275-diff.json'
OLD_MODEL = '${KIPRJMOD}/kicad-library/3d/CP_Elec_8x10.step'
NEW_MODEL = '${KIPRJMOD}/kicad-library/3d/CP_Elec_6.3x7.7.step'
VALUE_CHANGES = {'C226': ('22pF C0G', '15pF C0G'), 'C227': ('22pF C0G', '15pF C0G')}
DS = '${KIPRJMOD}/../ai-files/datasheets/'
DATASHEET_CHANGES = {'Y200': DS + 'YXC_YSX321SL_X322524576MOB4SI.pdf', 'C275': DS + 'Panasonic_EEH-ZA_hybrid_polymer.pdf'}
SKIP_MIRROR = ('Reference', 'Footprint')

if (BK / (PCB.name + '.pre-sync')).exists():
    sys.exit('refusing: backups/%s.pre-sync exists (already applied)' % PCB.name)
if len(sys.argv) != 2 or not Path(sys.argv[1]).is_file():
    sys.exit(__doc__)
STEP_SRC = Path(sys.argv[1])

# ---------------------------------------------------------------- s-expression helpers
STR = r'"((?:[^"\\]|\\.)*)"'

def skip_str(t, j):
    j += 1
    while t[j] != '"':
        j += 2 if t[j] == '\\' else 1
    return j + 1

def match_paren(t, i):
    depth, j = 0, i
    while True:
        c = t[j]
        if c == '"':
            j = skip_str(t, j); continue
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1

def children(t, s, e):
    j = s + 1
    while j < e - 1:
        c = t[j]
        if c == '"':
            j = skip_str(t, j)
        elif c == '(':
            k = match_paren(t, j); yield j, k; j = k
        else:
            j += 1

def q(v):
    return '"%s"' % v.replace('\\', '\\\\').replace('"', '\\"')

def unq(v):
    return re.sub(r'\\(.)', r'\1', v)

def props_of(t, s, e):
    out = {}
    for cs, ce in children(t, s, e):
        m = re.match(r'\(property\s+' + STR + r'\s+' + STR, t[cs:ce], re.S)
        if m:
            name = unq(m.group(1))
            vs = cs + m.start(2) - 1
            out[name] = dict(value=unq(m.group(2)), vspan=(vs, cs + m.end(2) + 1), span=(cs, ce))
    return out

# ---------------------------------------------------------------- BOM
CANON = {'TI': 'Texas Instruments', 'ST': 'STMicroelectronics', 'MURATA': 'Murata', 'YAGEO': 'Yageo',
         'PANASONIC': 'Panasonic'}
ALIASES = {('analog devices', 'maxim'), ('korean hroparts', 'korean hroparts elec')}

def canon(m):
    m = re.sub(r'\s*\(.*\)\s*$', '', m).strip()
    return CANON.get(m.upper(), m)

def same_company(sch, bom):
    if not sch:
        return False
    a, b = sch.strip().lower(), canon(bom).lower()
    return a == b or (a, b) in ALIASES

def bom_refs(cell):
    cell = cell.strip()
    if cell.startswith('(') and cell.endswith(')'):
        cell = cell[1:-1].replace(' DNP', '').strip()
    refs = []
    for tok in [x.strip() for x in cell.split(',') if x.strip()]:
        m = re.fullmatch(r'([A-Z]+)(\d+)-([A-Z]+)(\d+)', tok)
        if m:
            refs += ['%s%d' % (m.group(1), k) for k in range(int(m.group(2)), int(m.group(4)) + 1)]
        elif re.fullmatch(r'[A-Z]+\d+', tok):
            refs.append(tok)
        else:
            return None
    return refs

rows = list(csv.reader(open(BOM, newline='', encoding='utf-8')))
want, skipped = {}, []
for r in rows[1:]:
    refs = bom_refs(r[0])
    if refs is None or not r[4].strip():
        skipped.append(r[0]); continue
    for ref in refs:
        if ref in want:
            sys.exit('reference %s in two BOM rows' % ref)
        want[ref] = dict(Manufacturer=r[2].strip(), MPN=r[3].strip(), LCSC=r[4].strip())

# ---------------------------------------------------------------- schematics
diff, final = [], {}
touched = []
for f in sorted(glob.glob(str(KD / '*.kicad_sch'))):
    t = open(f, encoding='utf-8').read()
    root = t.index('(kicad_sch')
    edits = []  # (start, end, replacement)
    for s, e in children(t, root, match_paren(t, root)):
        if not re.match(r'\(symbol\s*\(lib_id', t[s:s + 40]):
            continue
        refs = set(re.findall(r'\(reference\s+' + STR, t[s:e]))
        if len(refs) != 1:
            sys.exit('symbol with refs %s in %s' % (refs, f))
        ref = refs.pop()
        if ref not in want and ref not in VALUE_CHANGES and ref not in DATASHEET_CHANGES:
            continue
        p = props_of(t, s, e)
        if p['Reference']['value'] != ref:
            sys.exit('Reference property mismatch %s' % ref)
        changes = []
        if ref in VALUE_CHANGES:
            old, new = VALUE_CHANGES[ref]
            if p['Value']['value'] != old:
                sys.exit('%s value is %r, expected %r' % (ref, p['Value']['value'], old))
            changes.append(('Value', old, new))
        if ref in DATASHEET_CHANGES:
            cur = p.get('Datasheet', {}).get('value', '')
            if cur not in ('', '~'):
                sys.exit('%s Datasheet already %r' % (ref, cur))
            changes.append(('Datasheet', cur, DATASHEET_CHANGES[ref]))
        lcsc_names = [n for n in ('LCSC', 'LCSC Part') if n in p] or ['LCSC']
        if ref in want:
            w = want[ref]
            cur = p.get('Manufacturer', {}).get('value', None)
            if not same_company(cur or '', w['Manufacturer']):
                changes.append(('Manufacturer', cur, canon(w['Manufacturer'])))
            cur = p.get('MPN', {}).get('value', None)
            if (cur or '') != w['MPN']:
                changes.append(('MPN', cur, w['MPN']))
            for n in lcsc_names:
                cur = p.get(n, {}).get('value', None)
                if (cur or '') != w['LCSC']:
                    changes.append((n, cur, w['LCSC']))
        if not changes:
            continue
        fp = t[slice(*p['Footprint']['span'])]
        adds = []
        for name, old, new in changes:
            if name in p:
                edits.append((*p[name]['vspan'], q(new)))
            else:
                clone = re.sub(r'^\(property\s+' + STR + r'\s+' + STR, '(property %s %s' % (q(name), q(new)), fp, flags=re.S)
                adds.append(' ' + clone)
            diff.append(dict(ref=ref, sheet=os.path.basename(f), field=name, old=old, new=new,
                             action='set' if name in p else 'added'))
        if adds:
            last = max(v['span'][1] for v in p.values())
            edits.append((last, last, ''.join(adds)))
        fin = {k: v['value'] for k, v in p.items()}
        for name, old, new in changes:
            fin[name] = new
        final[ref] = {k: v for k, v in fin.items() if k not in SKIP_MIRROR}
    if edits:
        shutil.copy2(f, BK / (os.path.basename(f) + '.pre-sync'))
        for a, b, rep in sorted(edits, key=lambda x: x[0], reverse=True):
            t = t[:a] + rep + t[b:]
        open(f, 'w', encoding='utf-8').write(t)
        touched.append(os.path.basename(f))

present = set()
for f in glob.glob(str(KD / '*.kicad_sch')):
    present |= set(re.findall(r'\(reference\s+' + STR, open(f, encoding='utf-8').read()))
not_in_sch = sorted(set(want) - present)

# ---------------------------------------------------------------- PCB
shutil.copy2(PCB, BK / (PCB.name + '.pre-sync'))
t = open(PCB, encoding='utf-8').read()
root = t.index('(kicad_pcb')
edits, pcb_diff, seen = [], [], set()
for s, e in children(t, root, match_paren(t, root)):
    if not t.startswith('(footprint', s):
        continue
    p = props_of(t, s, e)
    ref = p.get('Reference', {}).get('value')
    if ref in seen and (ref in final or ref == 'C275'):
        sys.exit('duplicate footprint ' + ref)
    seen.add(ref)
    if ref == 'C275':
        seg = t[s:e]
        k = seg.find('(model %s' % q(OLD_MODEL))
        if k < 0 or seg.count('(model ') != 1:
            sys.exit('C275 model not as expected')
        a = s + k + len('(model ')
        edits.append((a, a + len(q(OLD_MODEL)), q(NEW_MODEL)))
        pcb_diff.append(dict(ref=ref, field='3D model', old=OLD_MODEL, new=NEW_MODEL))
    if ref not in final:
        continue
    fin = final[ref]
    wantf = list(fin.items())
    desc = t[slice(*p['Description']['span'])]
    adds = []
    for name, val in wantf:
        if val is None:
            continue
        if name in p:
            if p[name]['value'] != val:
                edits.append((*p[name]['vspan'], q(val)))
                pcb_diff.append(dict(ref=ref, field=name, old=p[name]['value'], new=val))
        else:
            clone = re.sub(r'^\(property\s+' + STR + r'\s+' + STR, '(property %s %s' % (q(name), q(val)), desc, flags=re.S)
            clone = re.sub(r'\(uuid\s+"[^"]*"\)', '(uuid "%s")' % uuid.uuid4(), clone, count=1)
            adds.append('\n\t\t' + clone)
            pcb_diff.append(dict(ref=ref, field=name, old=None, new=val))
    if adds:
        a = p['Description']['span'][1]
        edits.append((a, a, ''.join(adds)))
pcb_missing = sorted(set(final) - seen)
for a, b, rep in sorted(edits, key=lambda x: x[0], reverse=True):
    t = t[:a] + rep + t[b:]
open(PCB, 'w', encoding='utf-8').write(t)

# ---------------------------------------------------------------- library footprint + model
shutil.copy2(LIBFP, BK / (LIBFP.name + '.pre-sync'))
lt = LIBFP.read_text(encoding='utf-8')
if lt.count(q(OLD_MODEL)) != 1:
    sys.exit('library CP_Elec_8x10 model not as expected')
LIBFP.write_text(lt.replace(q(OLD_MODEL), q(NEW_MODEL)), encoding='utf-8')
if STEP_DST.exists():
    sys.exit('%s exists' % STEP_DST)
shutil.copy2(STEP_SRC, STEP_DST)

out = dict(schematic_changes=diff, pcb_changes=pcb_diff, sheets_touched=touched, bom_rows_skipped=skipped,
           bom_refs_not_in_schematic=not_in_sch, changed_refs_without_footprint=pcb_missing,
           counts=dict(schematic_field_changes=len(diff), refs_changed=len(final), pcb_changes=len(pcb_diff)))
REPORT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
for d in diff:
    print('%-6s %-26s %-13s %r -> %r (%s)' % (d['ref'], d['sheet'], d['field'], d['old'], d['new'], d['action']))
print('PCB:', len(pcb_diff), 'changes;', 'C275 model ->', NEW_MODEL)
print(json.dumps(out['counts']), 'sheets', touched, 'skipped rows', skipped, 'not in sch', not_in_sch,
      'no footprint', pcb_missing)
