"""flatpak: route_r6a_metrics.py BOARD OUT.json : via counts (size, net, EP), power-net copper by layer (tracks: length/width range, zones: fill area), locked counts"""
import sys, json, collections
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
b = pcbnew.LoadBoard(sys.argv[1]); out = {}
vias = [t for t in b.Tracks() if t.GetClass() == 'PCB_VIA']
out['vias_total'] = len(vias)
out['vias_by_size'] = dict(collections.Counter('%.2f/%.2f' % (v.GetWidth(pcbnew.F_Cu) / MM, v.GetDrill() / MM) for v in vias))
out['vias_by_class'] = dict(collections.Counter(ncls(str(v.GetNetname())) for v in vias))
out['vias_by_net_power'] = {n: c for n, c in collections.Counter(str(v.GetNetname()) for v in vias).items() if ncls(n) in ('POWER_HI', 'PVDD', 'SWITCH', 'BOOT', 'PWR_5V', 'PWR_3V')}
ep = {}
for ref, num in (('U6', 33), ('U7', 33), ('U25', 21)):
    p = pad(b, ref, num); sh = p.GetEffectivePolygon(pcbnew.F_Cu)
    ep['%s.%s' % (ref, num)] = sum(1 for v in vias if str(v.GetNetname()) == 'GND' and sh.Contains(v.GetPosition()))
p = fp(b, 'U11'); ep['U11 footprint thermal vias (pads, 0.2 drill)'] = sum(1 for q in p.Pads() if q.GetDrillSizeX() > 0)
out['EP_vias'] = ep
out['locked'] = {'tracks': sum(1 for t in b.Tracks() if t.IsLocked()), 'tracks_total': len(list(b.Tracks())), 'zones': sum(1 for z in b.Zones() if z.IsLocked()), 'zones_total': len(list(b.Zones()))}
cu = {}
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
for t in b.Tracks():
    if t.GetClass() == 'PCB_VIA': continue
    n = str(t.GetNetname()); c = ncls(n)
    if c not in ('POWER_HI', 'PVDD', 'SPK_OUT', 'SWITCH', 'BOOT', 'PWR_5V', 'PWR_3V'): continue
    d = cu.setdefault(n, {}).setdefault(LN[t.GetLayer()], {'len': 0, 'wmin': 9, 'wmax': 0})
    w = t.GetWidth() / MM; d['len'] += t.GetLength() / MM; d['wmin'] = min(d['wmin'], w); d['wmax'] = max(d['wmax'], w)
for z in b.Zones():
    if z.GetIsRuleArea(): continue
    n = str(z.GetNetname())
    for l in z.GetLayerSet().Seq():
        if not z.HasFilledPolysForLayer(l): continue
        a = z.GetFilledPolysList(l).Area() / 1e12
        d = cu.setdefault(n, {}).setdefault(LN[l] + '_zone', {'area_mm2': 0, 'zones': []})
        d['area_mm2'] += round(a, 1); d['zones'].append(z.GetZoneName())
for n in cu:
    for k, d in cu[n].items():
        if 'len' in d: d['len'] = round(d['len'], 1); d['wmin'] = round(d['wmin'], 2); d['wmax'] = round(d['wmax'], 2)
out['copper'] = cu
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'copper'}, indent=0))
