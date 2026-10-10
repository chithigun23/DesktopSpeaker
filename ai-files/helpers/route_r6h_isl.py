"""flatpak: route_r6h_isl.py BOARD [REF.json] : power-island continuity (fill outline count + area per non-GND In2 zone and F/B power pours),
In2 signal tracks per net (length, min gap to non-GND In2 zone outlines), foreign vias inside islands. Writes BOARD.isl.json; compares with REF.json if given."""
import sys, json, pcbnew
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1])
import fnmatch
PATS = json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/R6h.kicad_pro'))['net_settings']['netclass_patterns']
def cl(n):
    for p in PATS:
        if fnmatch.fnmatchcase(n, p['pattern']): return p['netclass']
    return 'Default'
out = {'zones': {}, 'in2sig': {}, 'viain': []}
for z in b.Zones():
    if z.GetIsRuleArea(): continue
    n = str(z.GetNetname())
    if n in ('GND', ''): continue
    for L, ln in ((pcbnew.F_Cu, 'F'), (pcbnew.In2_Cu, '2'), (pcbnew.B_Cu, 'B')):
        if not z.IsOnLayer(L) or not z.HasFilledPolysForLayer(L): continue
        fp = z.GetFilledPolysList(L)
        out['zones'][z.GetZoneName() + ':' + ln] = [fp.OutlineCount(), round(fp.Area() / MM / MM, 2)]
isl = [z for z in b.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.In2_Cu) and str(z.GetNetname()) not in ('GND', '')]
for t in b.GetTracks():
    n = str(t.GetNetname())
    if t.GetClass() == 'PCB_VIA':
        if n == 'GND': continue
        for z in isl:
            if str(z.GetNetname()) != n and z.Outline().Collide(t.GetPosition(), int(t.GetWidth(pcbnew.F_Cu) / 2)):
                out['viain'].append([z.GetZoneName(), n, round(t.GetX() / MM, 2), round(t.GetY() / MM, 2)])
        continue
    if t.GetLayer() != pcbnew.In2_Cu: continue
    if cl(n) not in ('Default', 'I2C', 'SIGNAL', 'AUDIO', 'I2S_CLK', 'USB'): continue
    sh = t.GetEffectiveShape(); g = 9.0
    for z in isl:
        if str(z.GetNetname()) == n: continue
        for c in range(0, 900, 10):
            if z.Outline().Collide(sh, int(c / 1000 * MM)): g = min(g, c / 1000); break
    d = out['in2sig'].setdefault(n, [0.0, 9.0]); d[0] = round(d[0] + t.GetLength() / MM, 2); d[1] = min(d[1], g)
json.dump(out, open(sys.argv[1].replace('.kicad_pcb', '.isl.json'), 'w'), indent=0)
print('foreign non-GND vias in In2 islands:', len(out['viain']))
print('In2 signal nets:', {k: v for k, v in out['in2sig'].items()})
bad = [k for k, v in out['in2sig'].items() if v[1] < 0.3]
print('In2 signal < 0.3 mm to an island outline:', bad)
if len(sys.argv) > 2:
    r = json.load(open(sys.argv[2]))
    for k in sorted(set(r['zones']) | set(out['zones'])):
        a, c = r['zones'].get(k), out['zones'].get(k)
        if a != c and (a is None or c is None or a[0] != c[0] or abs(a[1] - c[1]) > 0.05 * max(a[1], 0.5)): print('  zone change', k, a, '->', c)
        elif a != c: print('  zone area', k, a, '->', c)
    rv = set(map(tuple, r['viain'])); nv = set(map(tuple, out['viain']))
    for v in sorted(nv - rv): print('  NEW via in island', v)
    for v in sorted(rv - nv): print('  removed via in island', v)
