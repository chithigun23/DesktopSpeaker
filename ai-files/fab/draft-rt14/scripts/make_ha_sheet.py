#!/usr/bin/env python3
"""make_ha_sheet.py FOOTPRINTS.json HA8.json STENCIL.json ACCURACY.csv OUT.md BOARD_LABEL   (plain python3)
Hand-assembly placement-order sheet (stencil + tweezers + hotplate, all SMD on F.Cu, THT by iron afterwards).
FOOTPRINTS.json from fpdump.py, HA8.json = routing gate output (pairs: ref, ref, courtyard gap, tier need, tier),
STENCIL.json from stencil_check.py, ACCURACY.csv = ai-files/cad/models-v13/accuracy-table.csv (model heights)."""
import json, sys, csv, re, collections
fps = {f['ref']: f for f in json.load(open(sys.argv[1]))}
ha8 = json.load(open(sys.argv[2]))['fails']
st = json.load(open(sys.argv[3]))
acc = {r['ref']: r for r in csv.DictReader(open(sys.argv[4]))}
out, label = sys.argv[5], sys.argv[6]

def h(ref):
    r = acc.get(ref)
    if not r: return None
    for k in ('model_after_LxWxH', 'real_LxWxH'):
        m = re.match(r'^[-\d.]+x[-\d.]+x([\d.]+)$', r.get(k, '') or '')
        if m: return float(m.group(1))
    return None

def rk(r):
    m = re.match(r'([A-Za-z]+)(\d+)', r); return (m.group(1), int(m.group(2))) if m else (r, 0)

def lib(r): return fps[r]['lib'].split(':')[-1]
def L(refs): return ', '.join(sorted(refs, key=rk))

NOFIT = {'R256': 'DNP (fit a 0R at the bench only for forced PWM on U25)', 'J7': 'Tag-Connect TC2030 footprint, no part',
         'SW101': 'panel rocker CW GRB112B802BR1, wired at enclosure assembly'}
skip = {r for r, f in fps.items() if f['board_only'] or r in NOFIT or r.startswith('LOGO')}
tp_smd = sorted([r for r in fps if r.startswith('TP') and not fps[r]['tht']], key=rk)
tp_tht = sorted([r for r in fps if r.startswith('TP') and fps[r]['tht']], key=rk)
tht = sorted([r for r, f in fps.items() if f['tht'] and r not in skip and not r.startswith('TP')], key=rk)
smd = [r for r, f in fps.items() if r not in skip and not f['tht'] and not r.startswith('TP')]

FINE = ('BQ25792', 'TPS25730D', 'TAS5825M', 'TPS61088', 'TPA6132', 'TPS7B8450', 'TPS63802', 'MAX17048', 'CSD17579',
        'PCM1862', 'STM32G071', 'PCM2902', 'TS5A23157', 'TPS2116', 'TPD2E2U06', 'TVS2200')
tight = sorted([p for p in ha8 if p[2] < 0.20 and p[0] not in NOFIT and p[1] not in NOFIT], key=lambda p: p[2])
first = ['C215', 'C212']
g_fine = sorted([r for r in smd if any(k in lib(r) for k in FINE)], key=rk)
tall_smd = sorted([r for r in smd if (h(r) or 0) >= 3.0 and r not in g_fine], key=lambda r: (h(r) or 0, rk(r)))
mid = sorted([r for r in smd if 1.4 <= (h(r) or 0) < 3.0 and r not in g_fine and r not in tall_smd], key=rk)
pas0402 = sorted([r for r in smd if '0402' in lib(r) and r not in first], key=rk)
pas_big = sorted([r for r in smd if re.search(r'0805|1206', lib(r)) and r not in first and r not in mid and r not in tall_smd], key=rk)
rest = sorted([r for r in smd if r not in set(first + g_fine + tall_smd + mid + pas0402 + pas_big)], key=rk)

# tight pairs: neighbours of fine-pitch ICs first
tp_rows = list(tight)
tight_parts = sorted({x for p in tight for x in p[:2] if x in smd}, key=rk)

S = []
S.append('# Hand-assembly placement sheet (DRAFT, %s)' % label)
S.append('')
S.append('DRAFT for the routed board %s; part positions do not change in the remaining GUI copper work, so the order holds for the final board '
         '(regenerate with `scripts/make_ha_sheet.py` after `regen_final.sh` to be sure). Process (owner, 2026-11-01): one 0.10 mm stainless stencil '
         '(laser cut, electropolished), leaded paste (assume SnPb, liquidus about 183 C), tweezers, large hotplate, iron/hot air for rework. '
         'All SMD parts are on F.Cu; B.Cu carries no parts, so the board lies flat on the plate.' % label)
S.append('')
S.append('Heights are the 3D-model heights from `ai-files/cad/models-v13/accuracy-table.csv` (datasheet-checked unless marked there as unverified).')
S.append('')
S.append('## 0. Before printing')
S.append('')
S.append('- Stencil check result (`stencil/stencil-report.md`): %d apertures, %d fail area ratio 0.66 / aspect 1.5 at 0.10 mm. '
         'Exposed pads outside the windowing rules: %s.' % (st['summary']['apertures'], st['summary']['fail_ar_or_aspect'],
         ', '.join('%s (%s)' % (e['pad'], '; '.join(e['problems'])) for e in st['thermal'] if e['problems'])))
S.append('- The stencil as exported prints full paste on the U6/U7 (16 open vias each) and U25 (8 open vias) exposed pads: expect solder to wick into the vias and some voiding. '
         'Either order the stencil after a paste-only footprint fix (windowed panes between the vias, 50-75 %, no copper change) or reduce by hand: cover part of those three apertures with Kapton before printing.')
S.append('- 22 test points TP1-TP22 (Keystone 5015 SMD loops) are not populated, but their 3.4 x 1.8 mm pads get paste: harmless solder bumps, or tape their apertures.')
S.append('- Print once on a spare board and check registration through the openings (pad edges visible = misaligned).')
S.append('')
S.append('## 1. Tight pairs first (courtyard gap < 0.20 mm)')
S.append('')
S.append('Place these before their neighbours close them in. **C215 and C212 (0.14 mm apart) go first, before U24 and Y200.**')
S.append('')
S.append('| pair | courtyard gap (mm) | tier need (mm) | note |')
S.append('|---|---|---|---|')
for a, b, gap, need, tier in tp_rows:
    ic = [x for x in (a, b) if x in g_fine]
    if {a, b} & {'C215', 'C212'}: note = 'C215 and C212 first (step 2.1), then U24 and Y200'
    elif ic: note = '%s first (step 2.2), then the passive from its free side' % ic[0]
    elif any(x[0] in 'UQLJ' for x in (a, b)):
        big = [x for x in (a, b) if x[0] in 'UQLJ'][0]
        note = 'passive first, then %s (later step); check the gap before reflow' % big
    else: note = 'passive pair: place both in one sitting, push apart with tweezers before reflow'
    S.append('| %s - %s | %.3f | %.2f | %s |' % (a, b, gap, need, note))
S.append('')
S.append('## 2. SMD placement order (one reflow)')
S.append('')
S.append('| step | group | parts |')
S.append('|---|---|---|')
S.append('| 2.1 | tight pair at U24/Y200 | C215, C212 |')
S.append('| 2.2 | fine-pitch and exposed-pad ICs (align under magnification; pin 1 as on the silk) | %s |' % L(g_fine))
S.append('| 2.3 | 0402 passives (%d), region by region | %s |' % (len(pas0402), L(pas0402)))
S.append('| 2.4 | 0805/1206 passives (%d) | %s |' % (len(pas_big), L(pas_big)))
S.append('| 2.5 | small discretes, crystals, SOT/SOD/SC-70 and other low parts | %s |' % L(rest))
S.append('| 2.6 | medium-height parts (1.4-3 mm) | %s |' % ', '.join('%s (%.1f)' % (r, h(r)) for r in mid))
S.append('| 2.7 | tall SMD last (>= 3 mm) | %s |' % ', '.join('%s (%.1f)' % (r, h(r)) for r in tall_smd))
S.append('')
S.append('Notes:')
S.append('- U1 (BM83 module, 2.5 mm) floats on paste: place it after the 0402s around it, press lightly, check castellation alignment after reflow and touch up with the iron and flux.')
S.append('- J1 (USB-C, hybrid): the SMD signal pads reflow on paste; the 4 shell legs are PTH and are soldered with the iron after reflow.')
S.append('- C275 (Panasonic EEH-ZA hybrid polymer, 7.7 mm) is an SMD reflow part on paste; confirm the reflow limit in its datasheet (the plate peak for SnPb paste is far below 260 C). It is the tallest SMD: place it last so the tweezers can still reach its neighbours.')
S.append('- SW100 (TE 1977066-1): the two locating pegs sit 0.075 mm from the terminal lands by the TE land pattern (rule 20); JLC may nick the pad corners. Check the pad shapes on delivery; if nicked, the joint still forms (or trim the outer pads to 0.65 mm in the footprint before ordering, 0.175 mm gap).')
S.append('- Via-in-pad on RT-14 (`via_in_pad.py`): via centre inside a non-exposed pad: C215.1, R185.2; via hole touching or within 0.15 mm of a same-net pad: U16.4, C274.1 (touching), R209.1, U2.10, U4.10, C102.1, C130.2, R153.2. Vias are tented, but inside a pad opening the hole is open: solder may wick; inspect these joints (or move the vias 0.2-0.3 mm in the GUI).')
S.append('')
S.append('## 3. Reflow, inspect')
S.append('')
S.append('- Hotplate: ramp <= 2 C/s, soak, peak about 205-225 C for SnPb, watch the paste go shiny, then off the plate onto a heat-safe surface (hand-assembly research section 2).')
S.append('- Inspect fine-pitch ICs for bridges (U4 0.4 mm pitch, U11, U6/U7, U3, U24, U2), tombstones on 0402s, and the C215/C212 pair.')
S.append('')
S.append('## 4. Through-hole parts by iron (low to tall)')
S.append('')
S.append('| part | height (mm) | note |')
S.append('|---|---|---|')
for r in sorted(tht, key=lambda r: (h(r) or 99, rk(r))):
    n = {'SW102': 'encoder: iron only, plastic body; shaft must point up', 'J2': 'audio jack, plastic', 'J3': 'audio jack, plastic',
         'J5': 'Micro-Fit pack connector', 'J9': 'speaker VH', 'J10': 'speaker VH', 'J11': 'woofer VH'}.get(r, '')
    hh = h(r)
    S.append('| %s %s | %s | %s |' % (r, lib(r)[:40], '%.1f' % hh if hh else '-', n))
S.append('| J1 shell legs | - | after reflow |')
S.append('| %s | %s | Keystone 5010-5014 THT test points: optional, fit if wanted (height unverified) |' % (L(tp_tht), '%.1f' % h(tp_tht[0]) if tp_tht and h(tp_tht[0]) else '-'))
S.append('')
S.append('## 5. Not fitted on the board')
S.append('')
for r, why in NOFIT.items(): S.append('- %s: %s' % (r, why))
S.append('- %s: SMD test-point loops, not populated by default (see 0).' % L(tp_smd))
S.append('- Mounting holes H1-H9, HA1, HA2 and LOGO1 have no part.')
S.append('')
S.append('Counts: %d SMD placements (%d fine-pitch/EP ICs, %d 0402, %d 0805/1206, %d other low, %d medium, %d tall), %d THT parts by iron.' % (
    len(smd), len(g_fine), len(pas0402) + 2, len(pas_big), len(rest), len(mid), len(tall_smd), len(tht)))
open(out, 'w').write('\n'.join(S) + '\n')
print('sheet', out, 'smd', len(smd), 'tht', len(tht), 'tight pairs', len(tight))
