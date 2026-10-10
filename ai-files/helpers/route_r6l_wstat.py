"""flatpak: route_r6l_wstat.py BOARD [OUT.json] : per-net track statistics for power-type classes (POWER_HI, PVDD, SPK_OUT, SWITCH, PWR_5V, PWR_3V, PWR_LOCAL, GND):
min width, length-weighted width histogram per layer, total length, vias. Used for the R6l overspec before/after table."""
import sys, json, fnmatch, collections, pcbnew
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1])
pats = json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/R6l.kicad_pro'))['net_settings']['netclass_patterns']
def cl(n):
    for p in pats:
        if fnmatch.fnmatchcase(n, p['pattern']): return p['netclass']
    return 'Default'
CL = ('POWER_HI', 'PVDD', 'SPK_OUT', 'SWITCH', 'PWR_5V', 'PWR_3V', 'PWR_LOCAL')
LN = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: '2', pcbnew.B_Cu: 'B', pcbnew.In1_Cu: '1'}
st = collections.defaultdict(lambda: dict(cls='', len=0.0, minw=99.0, minw_long=99.0, hist=collections.Counter(), vias=0, seg=0))
for t in b.GetTracks():
    n = str(t.GetNetname()); c = cl(n)
    if c not in CL: continue
    s = st[n]; s['cls'] = c
    if t.GetClass() == 'PCB_VIA': s['vias'] += 1; continue
    L = t.GetLength() / MM; w = round(t.GetWidth() / MM, 3)
    s['len'] += L; s['seg'] += 1; s['minw'] = min(s['minw'], w)
    if L >= 1.0: s['minw_long'] = min(s['minw_long'], w)
    s['hist']['%s%.2f' % (LN.get(t.GetLayer(), '?'), w)] += L
out = {}
for n in sorted(st, key=lambda k: (st[k]['cls'], k)):
    s = st[n]
    if s['seg'] == 0: continue
    lw = sum(float(k[1:]) * v for k, v in s['hist'].items()) / max(s['len'], 1e-9)
    out[n] = dict(cls=s['cls'], len=round(s['len'], 1), seg=s['seg'], minw=s['minw'], minw_long=(s['minw_long'] if s['minw_long'] < 99 else None), wavg=round(lw, 3), vias=s['vias'],
                  hist={k: round(v, 1) for k, v in sorted(s['hist'].items())})
    print('%-10s %-34s len %6.1f seg %3d minw %.2f minw(>=1mm) %s avg %.2f | %s' % (s['cls'], n[-34:], s['len'], s['seg'], s['minw'], out[n]['minw_long'], lw, ' '.join('%s:%.1f' % kv for kv in sorted(out[n]['hist'].items()))))
if len(sys.argv) > 2: json.dump(out, open(sys.argv[2], 'w'), indent=0)
