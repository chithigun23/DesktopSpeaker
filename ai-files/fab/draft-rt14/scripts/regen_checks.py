#!/usr/bin/env python3
"""regen_checks.py SUBCOMMAND ...  (plain python3, no dependencies) : gate helpers for regen_final.sh.
Every gate prints one line 'GATE <name> <PASS|FAIL|WARN|INFO> <detail>'.

  drc DRC.json PARITY_BASELINE.json            DRC violations / unconnected / schematic parity (new vs inherited) / lib mismatch
  fillcmp A.sig.json B.sig.json LABEL          zone-fill signatures equal (0.01 mm2 per zone layer)
  tdcmp INPUT.sig.json REGEN.sig.json          teardrops of the input equal a headless regeneration
  segadd IN.kicad_pcb OUT.kicad_pcb SPEC...    append test segments, SPEC = layer,net,width,x1,y1,x2,y2
  drustrip IN.kicad_dru OUT.kicad_dru RULE...  copy a rule file without the named rules
  druappend IN.kicad_dru OUT.kicad_dru         copy a rule file plus the I2S_CLK 5 mm width sentinel rule
  sentinel A.json B.json C.json                prove the custom rules are read and rules 20/21 act (see regen_final.sh)
  cpl POS_KICAD.csv OUT_JLC.csv FP.json        JLC CPL (Designator, Mid X, Mid Y, Layer, Rotation) + exclusion checks
  bom JLC_BOM.csv REF_BOM.csv FP.json CPL.csv  regenerated BOM vs committed BOM, BOM vs board footprints, CPL vs BOM
  fabcheck FABCHECK.txt                        evaluate fab_check.py output
  stencil STENCIL.json                         evaluate stencil_check.py output
"""
import sys, json, csv, re, uuid, collections

def gate(name, res, detail=''):
    print('GATE %s %s %s' % (name, res, detail), flush=True)

def rule_of(v):
    d = v.get('description', '')
    return d.split("rule '")[1].split("'")[0] if "rule '" in d else ''

def pkey(x):
    return (x['type'], x['description'], tuple(sorted(i['description'] for i in x['items'])))

cmd = sys.argv[1]; a = sys.argv[2:]

if cmd == 'drc':
    d = json.load(open(a[0])); base = json.load(open(a[1]))
    v = d['violations']; c = collections.Counter(x['type'] for x in v)
    gate('drc_violations', 'PASS' if not v else 'FAIL', '%d %s' % (len(v), dict(c)))
    for x in v[:15]:
        print('    %s | %s | %s' % (x['type'], x['description'][:90], '; '.join('%s @(%.2f, %.2f)' % (i['description'][:60], i['pos']['x'], i['pos']['y']) for i in x['items'])))
    u = d['unconnected_items']
    gate('drc_unconnected', 'PASS' if not u else 'FAIL', '%d' % len(u))
    lm = c.get('lib_footprint_mismatch', 0) + c.get('lib_footprint_issues', 0)
    gate('lib_footprint_mismatch', 'PASS' if lm == 0 else 'FAIL', '%d' % lm)
    p = d.get('schematic_parity', []); bp = base.get('schematic_parity', base if isinstance(base, list) else [])
    A = collections.Counter(map(pkey, p)); B = collections.Counter(map(pkey, bp))
    new = A - B; gone = B - A
    gate('schematic_parity', 'PASS' if not new else 'FAIL', '%d issues (%s), %d new vs the inherited %d, %d gone' % (
        len(p), dict(collections.Counter(x['type'] for x in p)), sum(new.values()), len(bp), sum(gone.values())))
    for k in list(new)[:10]: print('    new:', k[0], '|', k[1][:80], '|', k[2][:2])

elif cmd == 'fillcmp':
    A = json.load(open(a[0])); B = json.load(open(a[1]))
    ka, kb = A['area'], B['area']
    diff = [(k, ka.get(k), kb.get(k)) for k in sorted(set(ka) | set(kb)) if abs((ka.get(k) or 0) - (kb.get(k) or 0)) > 0.01]
    same = not diff and A['teardrop_zones'] == B['teardrop_zones']
    print('FILLCMP', 'SAME' if same else 'DIFF', len(diff), diff[:5])
    sys.exit(0 if same else 1)

elif cmd == 'tdcmp':
    A = json.load(open(a[0])); B = json.load(open(a[1]))
    ka, kb = A['area'], B['area']
    diff = [k for k in set(ka) | set(kb) if abs((ka.get(k) or 0) - (kb.get(k) or 0)) > 0.01]
    ok = A['teardrop_zones'] == B['teardrop_zones'] and not diff
    gate('teardrops_current', 'PASS' if ok else 'FAIL',
         'input %d teardrop zones, headless regeneration %d; zone layers differing %d%s' % (
             A['teardrop_zones'], B['teardrop_zones'], len(diff),
             '' if ok else ' (rerun with --teardrops to export the regenerated teardrops, or redo them in the GUI)'))

elif cmd == 'segadd':
    s = open(a[0]).read().rstrip()
    assert s.endswith(')')
    add = ''
    for spec in a[2:]:
        L, net, w, x1, y1, x2, y2 = spec.split(',')
        add += ('\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(width %s)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'
                % (x1, y1, x2, y2, w, L, net, uuid.uuid4()))
        if '(net "%s")' % net not in s: print('WARNING net not on board:', net)
    open(a[1], 'w').write(s[:-1] + add + ')\n')

elif cmd == 'drustrip':
    s = open(a[0]).read(); out = s
    for r in a[2:]:
        m = re.search(r'\(rule %s\b' % re.escape(r), out)
        if not m: print('WARNING rule not found', r); continue
        i = m.start(); depth = 0; j = i
        while True:
            if out[j] == '(': depth += 1
            elif out[j] == ')':
                depth -= 1
                if depth == 0: break
            j += 1
        out = out[:i] + out[j + 1:]
    open(a[1], 'w').write(out)

elif cmd == 'druappend':
    s = open(a[0]).read()
    open(a[1], 'w').write(s + "\n(rule sentinel_route_oct\n  (condition \"A.NetClass == 'I2S_CLK'\")\n  (constraint track_width (min 5mm)))\n")

elif cmd == 'sentinel':
    def hits(fn):
        d = json.load(open(fn)); out = []
        for v in d['violations']:
            out.append((v['type'], rule_of(v), ' '.join(i['description'] for i in v['items'])))
        return out
    A, B, C = hits(a[0]), hits(a[1]), hits(a[2])
    s1 = sum(1 for t, r, i in A if r == 'sentinel_route_oct')
    a_fb = any(r == 'in2_power_only' and 'U14-FB' in i and 'In2.Cu' in i for t, r, i in A)
    a_g0 = any(r == 'in2_power_only' and 'HP_G0' in i and 'In2.Cu' in i for t, r, i in A)
    b_g0 = any(r == 'in2_power_only' and 'HP_G0' in i and 'In2.Cu' in i for t, r, i in B)
    b_sw = sum(1 for t, r, i in B if t == 'hole_clearance' and 'SW100' in i)
    a_sw = sum(1 for t, r, i in A if t == 'hole_clearance' and 'SW100' in i)
    c_w = any(r == 'rt10_in2_slow_width' for t, r, i in C)
    gate('sentinel_rules_read', 'PASS' if s1 > 0 else 'FAIL', 'I2S_CLK 5 mm width sentinel fires %d times' % s1)
    ok21 = a_fb and not a_g0 and b_g0 and c_w
    gate('sentinel_rule21', 'PASS' if ok21 else 'FAIL',
         'A: U14-FB In2 blocked %s, HP_G0 In2 allowed %s; B (rules 20/21 removed): HP_G0 blocked %s; C: HP_G0 0.20 mm width rule %s'
         % (a_fb, not a_g0, b_g0, c_w))
    gate('sentinel_rule20', 'PASS' if (b_sw > 0 and a_sw == 0) else 'FAIL',
         'SW100 hole_clearance violations with rule 20: %d, without: %d' % (a_sw, b_sw))

elif cmd == 'cpl':
    rows = list(csv.DictReader(open(a[0]))); fps = {f['ref']: f for f in json.load(open(a[2]))}
    must_out = {r for r, f in fps.items() if f['dnp'] or f['no_pos'] or f['board_only']}
    must_out |= {'SW101', 'R256'}
    with open(a[1], 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        for r in rows:
            if r['Ref'] in must_out: continue
            w.writerow([r['Ref'], '%.4fmm' % float(r['PosX']), '%.4fmm' % float(r['PosY']),
                        'Top' if r['Side'] == 'top' else 'Bottom', '%.2f' % float(r['Rot'])])
    out = [r['Ref'] for r in rows if r['Ref'] not in must_out]
    leaked = sorted(set(r['Ref'] for r in rows) & must_out)
    bottom = [r['Ref'] for r in rows if r['Side'] != 'top']
    tps = [r for r in out if r.startswith('TP')]
    gate('cpl_exclusions', 'PASS' if not leaked else 'WARN',
         '%d rows (%d test points); excluded %s%s' % (len(out), len(tps), ', '.join(sorted(x for x in must_out if not re.match(r'^H', x))) + ', H*',
                                                      ('; filtered from the KiCad file: %s' % leaked) if leaked else ''))
    gate('cpl_single_side', 'PASS' if not bottom else 'FAIL', 'bottom-side rows: %s' % (bottom or 'none'))

elif cmd == 'bom':
    def load(fn): return list(csv.DictReader(open(fn)))
    new, ref = load(a[0]), load(a[1]); fps = {f['ref']: f for f in json.load(open(a[2]))}
    cpl = {r['Designator'] for r in csv.DictReader(open(a[3]))}
    def key(r): return tuple(r[k] for k in ('Comment', 'Designator', 'Footprint', 'LCSC Part #', 'MPN', 'Manufacturer', 'Qty'))
    A = set(map(key, new)); B = set(map(key, ref))
    gate('bom_vs_committed', 'PASS' if A == B else 'WARN', '%d lines / %d placements vs committed %d / %d; lines only in new %d, only in committed %d'
         % (len(new), sum(int(r['Qty']) for r in new), len(ref), sum(int(r['Qty']) for r in ref), len(A - B), len(B - A)))
    for k in sorted(A - B)[:8]: print('    new only:', k)
    for k in sorted(B - A)[:8]: print('    committed only:', k)
    refs = {}; bad = []
    for r in new:
        for d in r['Designator'].split(','):
            refs[d] = r['Footprint']
            f = fps.get(d)
            if f is None: bad.append('%s not on board' % d)
            elif f['lib'].split(':')[-1] != r['Footprint']: bad.append('%s BOM %s board %s' % (d, r['Footprint'], f['lib']))
    nocode = [r['Designator'] for r in new if not r['LCSC Part #'].strip()]
    gate('bom_vs_board', 'PASS' if not bad and not nocode else 'FAIL', '%d placements; footprint/ref mismatches %d %s; lines without LCSC code %d'
         % (len(refs), len(bad), bad[:5], len(nocode)))
    tp = {x for x in cpl if x.startswith('TP')}
    miss = sorted(set(refs) - cpl); extra = sorted(cpl - set(refs) - tp)
    gate('cpl_vs_bom', 'PASS' if not miss and not extra else 'FAIL', 'CPL %d = BOM %d + %d test points; BOM refs missing in CPL %s; CPL refs without BOM line %s'
         % (len(cpl), len(refs), len(tp), miss or 'none', extra or 'none'))

elif cmd == 'fabcheck':
    t = open(a[0]).read()
    m = re.search(r'missing (\[.*?\])', t); miss = m.group(1) if m else '?'
    gate('fab_files', 'PASS' if miss == '[]' else 'FAIL', 'missing %s' % miss)
    ex = re.findall(r'^\s+(\S+)\s+flashes.*EXCEEDS OUTLINE', t, re.M)
    other = [x for x in ex if x != 'F_Silkscreen.gto']
    gate('fab_extents', 'FAIL' if other else ('WARN' if ex else 'PASS'),
         'outside the outline: %s%s' % (ex or 'none', ' (F.Silkscreen: BM83 module outline overhangs the left edge by design; JLC clips silk)' if 'F_Silkscreen.gto' in ex else ''))
    b = re.search(r'PTH pads (\d+), NPTH (\d+), vias (\d+), pads with F.Paste (\d+)', t)
    ph = re.search(r'  PTH.drl: hits (\d+)', t); nh = re.search(r'  NPTH.drl: hits (\d+)', t)
    if b and ph and nh:
        pth, npth, vias = int(b.group(1)), int(b.group(2)), int(b.group(3))
        gate('fab_drill_hits', 'PASS' if int(ph.group(1)) == pth + vias and int(nh.group(1)) == npth else 'FAIL',
             'PTH %s = %d pads + %d vias; NPTH %s = %d pads' % (ph.group(1), pth, vias, nh.group(1), npth))
    pf = re.search(r'F_Paste.gtp\s+flashes\s+(\d+)', t)
    if pf and b: gate('fab_paste_flashes', 'INFO', 'F.Paste flashes %s, pads with F.Paste %s (regions for custom openings are not flashes)' % (pf.group(1), b.group(4)))
    pr = re.search(r'position rows (\d+) vs footprints not excluded/DNP (\d+)', t)
    if pr: gate('fab_position_rows', 'PASS' if pr.group(1) == pr.group(2) else 'WARN', 'CPL rows %s, board footprints not excluded/DNP %s' % pr.groups())
    gj = re.search(r'gbrjob layers (\d+)', t)
    if gj: gate('fab_gbrjob', 'PASS' if gj.group(1) == '11' else 'FAIL', '%s layers in the job file' % gj.group(1))
    bs = re.findall(r'B-side SMD pad: (\S+ \S+) paste (\w+)', t)
    gate('fab_bside_smd', 'PASS' if all(p == 'False' for _, p in bs) else 'FAIL', 'B-side SMD pads %d (paste on B: %d)%s' % (
        len(bs), sum(p == 'True' for _, p in bs), ': ' + ', '.join(sorted({x.split()[0] for x, _ in bs})) if bs else ''))

elif cmd == 'stencil':
    d = json.load(open(a[0]))['summary']
    gate('stencil_area_ratio', 'PASS' if d['fail_ar_or_aspect'] == 0 else 'FAIL',
         '%d apertures at %.2f mm: %d below AR 0.66 or aspect 1.5' % (d['apertures'], d['thickness_mm'], d['fail_ar_or_aspect']))
    gate('stencil_thermal_pads', 'PASS' if d['thermal_pads_with_problems'] == 0 else 'WARN',
         '%d of %d exposed pads outside the HA windowing rules (see stencil report)' % (d['thermal_pads_with_problems'], d['thermal_pads']))
else:
    sys.exit('unknown subcommand ' + cmd)
