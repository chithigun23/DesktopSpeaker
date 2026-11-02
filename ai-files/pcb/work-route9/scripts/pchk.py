#!/usr/bin/env python3
"""pchk.py GEO.json PLAN.json [--zones] : pre-DRC clearance check of the copper a plan adds (edit.py format) against the board model.
Not a gate (kicad-cli DRC is); a fast design aid. Clearance model: route_oct_rules strict values outside neck areas,
0.2 mm when either item touches a NECK_/fine-pitch courtyard (DRC rule neck_ic is last), hole 0.25, own-net ignored.
Also checks added items against each other. Zones of other nets are listed as 'carve' (refill backs off), not as errors.
Prints every pair closer than required, and the exactness of each added segment (0/45/90)."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hr
from shapely.geometry import LineString, Point
import rules_snap as RU

geo, planf = sys.argv[1:3]
SHOWZ = '--zones' in sys.argv
B = hr.Board(geo)
PL = json.load(open(planf))
D = B.D
dels = PL.get('seg_del', [])
vdel = []
vset = []
if '--board' in sys.argv:
    from pcbtext import read as _r0, items as _i0
    _bp = sys.argv[sys.argv.index('--board') + 1]
    _vi = [d for d in _i0(_bp, _r0(_bp)) if d['kind'] == 'via']
    for u in PL.get('via_del', []):
        vdel += [d['at'] for d in _vi if d['uuid'].startswith(u)]
    for u, nv in PL.get('via_set', {}).items():
        for d in _vi:
            if d['uuid'].startswith(u):
                vdel.append(d['at']); vset.append([d['net'], nv[0], nv[1], d['size'], d['drill']])
    for u, nv in PL.get('seg_set', {}).items():
        PL.setdefault('seg_del', []).append(u)
        d = next(d for d in _i0(_bp, _r0(_bp)) if d['kind'] == 'segment' and d['uuid'].startswith(u))
        PL.setdefault('seg_keep', []).append([d['layer'], d['net'], d['width']] + list(nv))
for L in list(B.items):
    B.items[L] = [it for it in B.items[L] if not (it.typ == 'Track' and any(it.name.startswith(u) for u in dels))
                  and not (it.typ == 'Via' and any(abs(it.geom.centroid.x - x) < 1e-3 and abs(it.geom.centroid.y - y) < 1e-3 for x, y in vdel))]
B.holes = [h for h in B.holes if not any(abs(h[0].centroid.x - x) < 1e-3 and abs(h[0].centroid.y - y) < 1e-3 for x, y in vdel)]
# footprint moves (rotation unchanged): translate pad copper of moved parts (old position from --board text)
if '--board' in sys.argv and PL.get('fp_move'):
    from shapely import affinity
    from pcbtext import read as _rd
    bl = _rd(sys.argv[sys.argv.index('--board') + 1])
    for ref, v in PL['fp_move'].items():
        i = next(k for k, L in enumerate(bl) if L.strip() == '(property "Reference" "%s"' % ref)
        j = i
        while not bl[j].startswith('\t\t(at '): j -= 1
        o = bl[j].strip()[4:-1].split()
        dx, dy = v[0] - float(o[0]), v[1] - float(o[1])
        for L in list(B.items):
            for it in B.items[L]:
                if it.typ == 'Pad' and it.name.startswith(ref + '-'): it.geom = affinity.translate(it.geom, dx, dy)
        print('moved pads of', ref, 'by %.3f %.3f' % (dx, dy))
B.rebuild()
NC = D['netclass']
new = []
for a in PL.get('seg_add', []):
    L, net, w, x1, y1, x2, y2 = a
    g = LineString([(x1, y1), (x2, y2)]).buffer(w / 2, 16) if (x1, y1) != (x2, y2) else Point(x1, y1).buffer(w / 2, 16)
    new.append(dict(L=[L], net=net, g=g, typ='Track', desc='%s %s w%.2f (%.3f,%.3f)-(%.3f,%.3f)' % (L[0], net.split('/')[-1], w, x1, y1, x2, y2), hole=None))
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    if not (dx < 1e-6 or dy < 1e-6 or abs(dx - dy) < 1e-6):
        print('NOT EXACT', new[-1]['desc'])
for a in PL.get('seg_keep', []):
    L, net, w, x1, y1, x2, y2 = a
    B.add_track(L, net, w, (x1, y1), (x2, y2))
for v in vset:
    B.add_via(*v)
B.rebuild()
for v in PL.get('via_add', []):
    net, x, y, d, dr = v
    new.append(dict(L=['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'], net=net, g=Point(x, y).buffer(d / 2, 16), typ='Via', desc='via %s (%.3f,%.3f) %.2f' % (net.split('/')[-1], x, y, d),
                    hole=Point(x, y).buffer(dr / 2, 16)))


def inneck(g):
    return B.neck.intersects(g)


bad = 0
carve = {}
for n in new:
    cls = NC.get(n['net'], 'Default')
    for L in n['L']:
        if L in ('In1.Cu', 'In2.Cu'):
            continue
        for it in B.query(L, n['g'].buffer(2.5)):
            if it.net == n['net']: continue
            d = n['g'].distance(it.geom)
            if it.typ == 'Zone':
                if d < 0.45 and it.net != 'GND': carve[(it.name or '?', it.net, L)] = min(d, carve.get((it.name or '?', it.net, L), 9))
                continue
            req = 0.2 if (inneck(n['g']) or inneck(it.geom)) else max(RU.clr_strict(cls, n['net'], it.cls, it.typ), RU.clr_strict(it.cls, it.net, cls, n['typ']) if it.typ != 'Pad' else 0.2)
            if cls == 'USB' and it.cls == 'USB': req = 0.15
            if d < req - 1e-4:
                bad += 1; print('CLR %.3f < %.2f  %s  vs %s %s %s %s' % (d, req, n['desc'], it.typ, it.net, it.cls, it.name))
    # holes
    for h, hn, plated in B.holes:
        if hn == n['net'] and plated: continue
        d = n['g'].distance(h)
        if d < 0.25 - 1e-4:
            bad += 1; print('HOLE %.3f < 0.25  %s  vs hole %s' % (d, n['desc'], hn))
    if n['hole'] is not None:
        for h, hn, plated in B.holes:
            if h.distance(n['hole']) < 0.3 - 1e-4 and not h.equals(n['hole']):
                bad += 1; print('H2H %.3f %s vs hole %s' % (h.distance(n['hole']), n['desc'], hn))
for i, a in enumerate(new):
    for b in new[i + 1:]:
        if a['net'] == b['net'] or not set(a['L']) & set(b['L']): continue
        d = a['g'].distance(b['g'])
        ca, cb = NC.get(a['net'], 'Default'), NC.get(b['net'], 'Default')
        req = 0.2 if (inneck(a['g']) or inneck(b['g'])) else max(RU.clr_strict(ca, a['net'], cb, b['typ']), RU.clr_strict(cb, b['net'], ca, a['typ']))
        if d < req - 1e-4:
            bad += 1; print('NEW %.3f < %.2f  %s  vs  %s' % (d, req, a['desc'], b['desc']))
if SHOWZ:
    for k, d in sorted(carve.items()):
        print('carve %-28s %-34s %s %.3f' % (k[0], k[1], k[2], d))
print('pchk: %d issues, %d new items' % (bad, len(new)))
