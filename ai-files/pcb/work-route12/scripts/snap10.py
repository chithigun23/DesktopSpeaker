#!/usr/bin/env python3
"""snap10.py BOARD.kicad_pcb PLAN.json OUT.json : RT-10 post-process of hr10 plans. hr10's lattice is anchored at the start point, so a
route can stop up to one lattice step short of (or beside) the target copper. Every open end of a new segment (not shared with another
new segment or new via) is extended ALONG ITS OWN DIRECTION by at most 0.15 mm onto the nearest same-net point (existing via centre,
segment end, pad centre) or onto a same-net segment centre line. Angles stay exact; ends that cannot be snapped are reported."""
import sys, json, math
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from pcbtext import items
brd, pf, out = sys.argv[1:4]
P = json.load(open(pf)); IT = items(brd, kinds=('segment', 'via'))
dels = set(P.get('seg_del', [])); vdel = set(P.get('via_del', []))
pts = {}; lines = {}
for d in IT:
    if d['kind'] == 'via' and not any(d['uuid'].startswith(u) for u in vdel): pts.setdefault(d['net'], []).append(tuple(d['at']))
    if d['kind'] == 'segment' and not any(d['uuid'].startswith(u) for u in dels):
        pts.setdefault(d['net'], []).append(tuple(d['start'])); pts.setdefault(d['net'], []).append(tuple(d['end']))
        lines.setdefault((d['net'], d['layer']), []).append((tuple(d['start']), tuple(d['end'])))
for v in P.get('via_add', []): pts.setdefault(v[0], []).append((v[1], v[2]))
key = lambda p: (round(p[0], 4), round(p[1], 4))
cnt = {}
for s in P['seg_add']:
    for p in (s[3:5], s[5:7]): cnt[(s[1], key(p))] = cnt.get((s[1], key(p)), 0) + 1
vset = {(v[0], key(v[1:3])) for v in P.get('via_add', [])}
rep = []
for s in P['seg_add']:
    for e in (0, 1):
        p = s[3:5] if e == 0 else s[5:7]; q = s[5:7] if e == 0 else s[3:5]
        if cnt[(s[1], key(p))] > 1 or (s[1], key(p)) in vset: continue
        if any(math.dist(p, x) < 1e-4 for x in pts.get(s[1], [])): continue
        dx, dy = p[0] - q[0], p[1] - q[1]; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L
        best = None
        for x in pts.get(s[1], []):
            t = (x[0] - p[0]) * ux + (x[1] - p[1]) * uy; off = abs((x[0] - p[0]) * uy - (x[1] - p[1]) * ux)
            if 0 < t <= 0.15 and off < 1e-3 and (best is None or t < best): best = t
        if best is None:
            for a, b in lines.get((s[1], s[0]), []):
                ex, ey = b[0] - a[0], b[1] - a[1]; den = ux * ey - uy * ex
                if abs(den) < 1e-9: continue
                t = ((a[0] - p[0]) * ey - (a[1] - p[1]) * ex) / den; u = ((a[0] - p[0]) * uy - (a[1] - p[1]) * ux) / den
                if 0 < t <= 0.15 and -1e-6 <= u <= 1 + 1e-6 and (best is None or t < best): best = t
        if best is None: rep.append(('UNSNAPPED', s[1], s[0], p)); continue
        np_ = [round(p[0] + ux * best, 4), round(p[1] + uy * best, 4)]
        rep.append(('snap', s[1], s[0], p, np_))
        if e == 0: s[3:5] = np_
        else: s[5:7] = np_
json.dump(P, open(out, 'w'), indent=1)
for r in rep: print(*r)
