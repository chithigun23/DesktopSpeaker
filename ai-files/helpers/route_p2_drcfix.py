"""flatpak: route_p2_drcfix.py IN.kicad_pcb DRC.json OUT.kicad_pcb QUEUE.json : remove the lower-priority copper of each clearance/dangling/keepout violation.
GND/other tracks item level for GND; whole net otherwise. QUEUE.json = nets to reroute."""
import sys, json, fnmatch, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); d = json.load(open(sys.argv[2]))
pro = json.load(open(sys.argv[1].replace('.kicad_pcb', '.kicad_pro'))); pats = pro['net_settings']['netclass_patterns']
def cl(n):
    for p in pats:
        if fnmatch.fnmatchcase(n, p['pattern']): return p['netclass']
    return 'SIGNAL'
RANK = {'POWER_HI': 0, 'PVDD': 1, 'SPK_OUT': 2, 'SWITCH': 3, 'BOOT': 4, 'USB': 5, 'I2S_CLK': 6, 'AUDIO': 7}  # lower = keep; others (not listed) = 20 ; GND = 30
def rk(n): return 30 if cl(n) == 'GND' else RANK.get(cl(n), 20)
byu = {t.m_Uuid.AsString(): t for t in b.Tracks()}
rm_items = {}; rm_nets = set(); n_v = 0
for v in d['violations']:
    ty = v['type']
    its = [byu[i['uuid']] for i in v['items'] if i['uuid'] in byu]
    if ty in ('track_dangling', 'via_dangling', 'hole_to_hole', 'holes_co_located'):
        for t in its[-1:] if ty.startswith('hole') else its:
            rm_items[t.m_Uuid.AsString()] = t
    elif ty in ('clearance', 'items_not_allowed', 'copper_edge_clearance', 'shorting_items', 'hole_clearance') :
        if ty == 'clearance' and v['description'].find('Pad') >= 0 and False: pass
        if not its: continue
        n_v += 1
        t = max(its, key=lambda x: rk(str(x.GetNetname())))
        if len(its) == 2 and rk(str(its[0].GetNetname())) == rk(str(its[1].GetNetname())): t = its[1]
        n = str(t.GetNetname())
        if cl(n) == 'GND': rm_items[t.m_Uuid.AsString()] = t
        else: rm_nets.add(n)
for u, t in rm_items.items():
    try: b.Remove(t)
    except Exception: pass
cnt = 0
for t in list(b.Tracks()):
    if str(t.GetNetname()) in rm_nets: b.Remove(t); cnt += 1
import os
op = sys.argv[1].replace('.kicad_pcb', '-f.open2.json')
if os.path.exists(op):
    for n, v in json.load(open(op)).items():
        if cl(n) in ('SWITCH', 'POWER_HI', 'PVDD', 'SPK_OUT', 'BOOT'): rm_nets.add(n)
pcbnew.SaveBoard(sys.argv[3], b)
json.dump(sorted(rm_nets), open(sys.argv[4], 'w'))
print('violations', n_v, 'gnd/dangling items', len(rm_items), 'nets', len(rm_nets), sorted(rm_nets))
