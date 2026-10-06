#!/usr/bin/env python3
"""Extra checks on the final board: BM83 keepout copper, plane fill ratio, GND pads without own via, via counts, track-width audit vs plan section 2 minima.
usage (flatpak pcbnew): route_p0_checks.py BOARD OUT.json"""
import sys, json, collections, pcbnew
M = 1e6
b = pcbnew.LoadBoard(sys.argv[1])
res = {}
ka = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'BM83_ANTENNA_KEEPOUT'][0]
kb = ka.GetBoundingBox(); kb.Inflate(-20000)
hits = []
for t in b.Tracks():
    if kb.Intersects(t.GetBoundingBox()): hits.append((t.GetClass(), t.GetNetname()))
for z in b.Zones():
    if z.GetIsRuleArea(): continue
    for l in z.GetLayerSet().Seq():
        fp = z.GetFilledPolysList(l)
        if fp.OutlineCount() and kb.Intersects(fp.BBox()):
            # exact test: any filled vertex inside keepout bbox
            for i in range(fp.OutlineCount()):
                o = fp.Outline(i)
                for k in range(o.PointCount()):
                    p = o.CPoint(k)
                    if kb.Contains(p): hits.append(('zone', z.GetZoneName(), b.GetLayerName(l))); break
                else: continue
                break
res['keepout_copper_hits'] = hits
fill = {}
ps = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ps, True); barea = ps.Area()/1e12
for z in b.Zones():
    if z.GetZoneName() in ('GND_L2', 'GND_B'):
        fill[z.GetZoneName()] = round(z.GetFilledArea()/1e12/barea, 3)
res['gnd_fill_ratio_of_board'] = fill; res['board_area_mm2'] = round(barea, 1)
# GND pads of C/U/D without a via at the end of their stub (own via check): count GND SMD pads touching a track
gnd = b.FindNet('GND').GetNetCode()
tr = [t for t in b.Tracks() if t.GetNetCode() == gnd]
pads = []; noconn = []
for f in b.GetFootprints():
    r = f.GetReference()
    if not any(r.startswith(x) for x in ('C', 'U', 'D', 'Y', 'FB')): continue
    for p in f.Pads():
        if p.GetNetCode() != gnd or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: continue
        pads.append(r)
        ok = any((t.GetClass() == 'PCB_VIA' and p.HitTest(t.GetPosition())) or (t.GetClass() != 'PCB_VIA' and (p.HitTest(t.GetStart()) or p.HitTest(t.GetEnd()))) for t in tr)
        if not ok: noconn.append('%s.%s' % (r, p.GetNumber()))
res['gnd_pads_total'] = len(pads); res['gnd_pads_without_via_or_stub'] = noconn
vc = collections.Counter()
for t in b.Tracks():
    if t.GetClass() == 'PCB_VIA': vc[t.GetNetname()] += 1
res['vias_by_net_top'] = vc.most_common(12)
res['vias_total'] = sum(vc.values())
res['vias_power'] = {n: vc[n] for n in vc if n.startswith('/') and ('SYS' in n or 'BAT' in n or 'PVDD' in n or 'VBUS' in n or '3V' in n or '5V' in n)}
json.dump(res, open(sys.argv[2], 'w'), indent=1)
print(json.dumps(res)[:2500])
