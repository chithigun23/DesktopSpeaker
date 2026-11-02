#!/usr/bin/env python3
"""prune2.py BOARD.kicad_pcb GEO.json DRC.json OUTPLAN : remove dead copper reported by DRC (track_dangling / via_dangling)
without breaking connections (venv python, shapely).
For every net with a dangling report, repeat until stable:
  * a via touching copper of at most one segment and no pad is dead: delete it;
  * a segment end touching nothing (no other segment of the net on its layer, no via, no pad) is free:
      - if nothing else touches the segment, delete it;
      - otherwise trim the free end back to the attachment closest to it along the segment (same line, so the angle is
        unchanged; trims shorter than 0.01 mm are skipped).
Vias touched by two or more segments on one layer only are reported, not changed (they need a manual fix)."""
import sys, os, json, math, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcbtext import read, items
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
board, geo, drc, outp = sys.argv[1:5]
IT = items(board, read(board)); G = json.load(open(geo)); D = json.load(open(drc))
nets = set()
for v in D['violations']:
    if v['type'] in ('track_dangling', 'via_dangling'):
        nets.add(re.search(r'\[(.*?)\]', v['items'][0]['description']).group(1))
plan = dict(seg_del=[], seg_set={}, via_del=[], via_del_xy=[])
E = 0.002
for net in sorted(nets):
    segs = {d['uuid']: dict(d) for d in IT if d['kind'] == 'segment' and d.get('net') == net}
    vias = {d['uuid']: dict(d) for d in IT if d['kind'] == 'via' and d.get('net') == net}
    arcs = [d for d in IT if d['kind'] == 'arc' and d.get('net') == net]
    pads = []
    for p in G['pads']:
        if p['net'] != net: continue
        for L, pl in p['poly'].items():
            g = unary_union([Polygon(r[0], r[1:]).buffer(0) for r in pl if len(r[0]) >= 3])
            pads.append((L, g))
    zones = [(L, unary_union([Polygon(r[0], r[1:]).buffer(0) for r in pl if len(r[0]) >= 3])) for z in G['zones'] if z['net'] == net and not z['teardrop'] for L, pl in z['fills'].items()]
    arcg = [(a['layer'], LineString([a['start'], a.get('mid', a['start']), a['end']]).buffer(a['width'] / 2)) for a in arcs]
    changed = True; it = 0
    while changed and it < 50:
        changed = False; it += 1
        sg = {u: LineString([s['start'], s['end']]).buffer(s['width'] / 2) for u, s in segs.items()}
        vg = {u: Point(v['at']).buffer(v['size'] / 2) for u, v in vias.items()}
        def touch_point(L, P, excl):
            q = Point(P)
            if any(g.distance(q) < E for u, g in sg.items() if u != excl and segs[u]['layer'] == L): return True
            if any(g.distance(q) < E for g in vg.values()): return True
            if any(L == pl and g.distance(q) < E for pl, g in pads + zones + arcg): return True
            return False
        for u, v in list(vias.items()):
            ts = [w for w, g in sg.items() if g.intersects(vg[u])]
            tp = [1 for L, g in pads + zones + arcg if g.intersects(vg[u])]
            if len(ts) <= 1 and not tp:
                plan['via_del'].append(u); plan['via_del_xy'].append(list(v['at'])); del vias[u]; changed = True; break
        if changed: continue
        for u, s in list(segs.items()):
            L = s['layer']; fa = not touch_point(L, s['start'], u); fb = not touch_point(L, s['end'], u)
            if not (fa or fb): continue
            line = LineString([s['start'], s['end']])
            att = []
            for w, g in sg.items():
                if w == u or segs[w]['layer'] != L or not g.intersects(sg[u]): continue
                att.append(line.project(g.intersection(line.buffer(s['width'] / 2)).centroid))
            for g in vg.values():
                if g.intersects(sg[u]): att.append(line.project(g.centroid))
            for pl, g in pads + zones + arcg:
                if pl == L and g.intersects(sg[u]): att.append(line.project(g.intersection(sg[u]).centroid))
            if fa and fb or not att:
                plan['seg_del'].append(u); del segs[u]; changed = True; break
            if fa: t = min(att)
            else: t = max(att)
            P = line.interpolate(t); P = (round(P.x, 4), round(P.y, 4))
            new = [P[0], P[1], *s['end']] if fa else [*s['start'], P[0], P[1]]
            if math.dist(new[:2], new[2:]) < 0.01 or math.dist(P, s['start'] if fa else s['end']) < 0.01: continue
            key = s['uuid']; base = plan['seg_set'].get(key)
            plan['seg_set'][key] = new
            s['start'], s['end'] = (tuple(new[:2]), tuple(new[2:])); changed = True; break
    for u, v in vias.items():
        ts = [w for w, s in segs.items() if LineString([s['start'], s['end']]).buffer(s['width'] / 2).intersects(Point(v['at']).buffer(v['size'] / 2))]
        lays = {segs[w]['layer'] for w in ts}
        if len(lays) == 1 and len(ts) >= 2: print('MANUAL via', net, v['at'], 'segments on', lays, len(ts))
json.dump(plan, open(outp, 'w'), indent=1)
print('prune2', {k: len(v) for k, v in plan.items()})
