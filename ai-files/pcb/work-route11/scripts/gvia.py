#!/usr/bin/env python3
"""gvia.py GEO.json REF-NUM [REF-NUM ...] [--rmax 2.5] [--w 0.3] [--net GND] : for each pad of net GND (or --net), the nearest legal
0.6/0.3 via spot on one of the 8 octilinear rays from the pad centre, joined by one straight stub (pad centre -> via).
Legality (design aid; kicad-cli DRC is the gate): via and stub keep the strict clearance (0.2 inside neck areas) to every
other-net item on F.Cu (stub, via) and B.Cu/In1/In2 items that are not GND zones (via), hole-hole 0.3, hole-copper 0.25,
edge 0.5, via land inside In1 and In2 GND fill (GND only), no rule-area/BM83 keep-out. Prints the plan lines (JSON)."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hr
import rules_snap as RU
from shapely.geometry import Point, LineString

a = sys.argv[1:]
geo = a[0]
rmax = float(a[a.index('--rmax') + 1]) if '--rmax' in a else 2.5
W = float(a[a.index('--w') + 1]) if '--w' in a else 0.3
NET = a[a.index('--net') + 1] if '--net' in a else 'GND'
VD = float(a[a.index('--vd') + 1]) if '--vd' in a else 0.6
skip = {a[i + 1] for i, x in enumerate(a) if x.startswith('--')}
refs = [x for x in a[1:] if '-' in x and not x.startswith('--') and x not in skip]
B = hr.Board(geo)
NC = B.netcls
if '--plan' in a:
    PL = json.load(open(a[a.index('--plan') + 1]))
    dels = set(PL.get('seg_del', []))
    for L in list(B.items):
        B.items[L] = [it for it in B.items[L] if not (it.typ == 'Track' and any(it.name.startswith(u) for u in dels))]
    for s_ in PL.get('seg_add', []): B.add_track(s_[0], s_[1], s_[2], (s_[3], s_[4]), (s_[5], s_[6]))
    for v_ in PL.get('via_add', []): B.add_via(v_[0], v_[1], v_[2], v_[3], v_[4])
    B.rebuild()


def inneck(g):
    return B.neck.intersects(g)


def clear(g, L, cls, typ, extra=0.0):
    for it in B.query(L, g.buffer(2.5)):
        if it.net == NET: continue
        if it.typ == 'Zone' and L in ('In1.Cu', 'In2.Cu'): continue
        if it.typ == 'Zone' and it.net != NET:
            continue          # other-net pours carve back on refill
        req = 0.2 if (inneck(g) or inneck(it.geom)) else max(RU.clr_strict(cls, NET, it.cls, it.typ), RU.clr_strict(it.cls, it.net, cls, typ) if it.typ != 'Pad' else 0.2)
        if g.distance(it.geom) < req + extra - 1e-4: return False
    return True


out = []
for ref in refs:
    P = B.pads[ref]; c = P['_c']
    pg = P.get('F.Cu')
    best = None
    for k in range(8):
        dx, dy = hr.DIRS[k]
        n = math.hypot(dx, dy); ux, uy = dx / n, dy / n
        d = 0.3
        while d <= rmax + 1e-9:
            x, y = round(c[0] + ux * d, 4), round(c[1] + uy * d, 4)
            d += 0.05
            v = Point(x, y)
            if pg is not None and pg.distance(v) < VD / 2 + 0.05: continue      # no via in pad (hand assembly)
            vg = v.buffer(VD / 2, 16)
            if NET == 'GND' and not B.gnd12.contains(v): continue
            if not B.outline.buffer(-0.5 - VD / 2).contains(v): continue
            if B.modko.buffer(VD / 2).intersects(v): continue
            ok = True
            for ar in B.areas:
                if (ar['no_vias'] or (ar['name'].startswith('BKO_') and RU.bko_applies(NC.get(NET, 'GND'), NET))) and hr.mk(ar['outline']).buffer(VD / 2).contains(v): ok = False; break
            if not ok: continue
            if any(h[0].distance(v) < 0.3 + 0.15 - 1e-4 for h in B.holes): continue
            if any(h[0].distance(vg) < 0.25 - 1e-4 for h in B.holes if h[1] != NET): continue
            cls = NC.get(NET, 'GND')
            if not all(clear(vg, L, cls, 'Via') for L in ('F.Cu', 'B.Cu', 'In1.Cu', 'In2.Cu')): continue
            st = LineString([c, (x, y)]).buffer(W / 2, 16)
            if not clear(st, 'F.Cu', cls, 'Track'): continue
            L = math.dist(c, (x, y))
            if best is None or L < best[0]: best = (L, x, y)
            break
    if best:
        print('%s %s via (%.4f,%.4f) stub %.2f mm' % (ref, NET, best[1], best[2], best[0]))
        out.append(dict(ref=ref, c=c, via=[best[1], best[2]], L=best[0]))
    else:
        print('%s %s NO SPOT within %.1f' % (ref, NET, rmax)); out.append(dict(ref=ref, c=c, via=None))
print(json.dumps(out))
