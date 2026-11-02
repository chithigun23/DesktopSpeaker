#!/usr/bin/env python3
"""ripwin.py GEO.json BOARD.kicad_pcb NETS x0 y0 x1 y1 OUTPLAN.json OUTCOMP.json [--keep uuid,..]
Rip-up window (RT-8): for every net in NETS (comma list or @file) delete the segments with an end point inside the box and
the vias inside the box; then delete remaining copper fragments of the net that touch no pad (floating). Writes an edit.py
plan (seg_del, via_del, via_del_xy) and per net the copper components left (pads + open ends) that must be re-joined.
venv python (shapely)."""
import sys, os, json, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcbtext import read, items
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

geo, board, nets = sys.argv[1:4]
x0, y0, x1, y1 = map(float, sys.argv[4:8]); outp, outc = sys.argv[8:10]
keep = set(sys.argv[sys.argv.index('--keep') + 1].split(',')) if '--keep' in sys.argv else set()
NETS = [l.strip() for l in open(nets[1:])] if nets.startswith('@') else nets.split(',')
NETS = [n for n in NETS if n]
D = json.load(open(geo))
IT = items(board, read(board))
inb = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1


def mk(pl):
    ps = [Polygon(r[0], r[1:]).buffer(0) for r in pl if len(r[0]) >= 3]
    return unary_union(ps)


plan = dict(seg_del=[], via_del=[], via_del_xy=[])
comps = {}
for net in NETS:
    segs = [d for d in IT if d['kind'] == 'segment' and d.get('net') == net]
    vias = [d for d in IT if d['kind'] == 'via' and d.get('net') == net]
    arcs = [d for d in IT if d['kind'] == 'arc' and d.get('net') == net]
    pads = [p for p in D['pads'] if p['net'] == net]
    dseg = [s for s in segs if (inb(s['start']) or inb(s['end'])) and not any(s['uuid'].startswith(k) for k in keep)]
    dvia = [v for v in vias if inb(v['at'])]
    rs = [s for s in segs if s not in dseg]; rv = [v for v in vias if v not in dvia]
    # connectivity of what is left: nodes = pads, segments, vias, arcs
    nodes = []
    for p in pads:
        for L, pl in p['poly'].items():
            nodes.append(('pad', '%s-%s' % (p['ref'], p['num']), {L}, mk(pl)))
    for s in rs:
        nodes.append(('seg', s['uuid'], {s['layer']}, LineString([s['start'], s['end']]).buffer(s['width'] / 2)))
    for a in arcs:
        nodes.append(('arc', a['uuid'], {a['layer']}, LineString([a['start'], a.get('mid', a['start']), a['end']]).buffer(a['width'] / 2)))
    for v in rv:
        nodes.append(('via', v['uuid'], {'F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'}, Point(v['at']).buffer(v['size'] / 2)))
    n = len(nodes); par = list(range(n))

    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for i in range(n):
        for j in range(i + 1, n):
            a, b = nodes[i], nodes[j]
            if a[0] == 'pad' and b[0] == 'pad' and a[1] == b[1]: par[f(i)] = f(j); continue
            if a[2] & b[2] and a[3].intersects(b[3]): par[f(i)] = f(j)
    groups = collections.defaultdict(list)
    for i in range(n): groups[f(i)].append(i)
    out = []
    for g in groups.values():
        P = sorted({nodes[i][1] for i in g if nodes[i][0] == 'pad'})
        if not P:      # floating fragment: delete
            for i in g:
                if nodes[i][0] == 'seg': dseg.append(next(s for s in rs if s['uuid'] == nodes[i][1]))
                if nodes[i][0] == 'via': dvia.append(next(v for v in rv if v['uuid'] == nodes[i][1]))
            continue
        # open ends: end points of remaining segments that were joined to deleted copper
        ends = []
        dgeo = [(s['layer'], LineString([s['start'], s['end']]).buffer(s['width'] / 2 + 0.01)) for s in dseg] + \
               [('*', Point(v['at']).buffer(v['size'] / 2 + 0.01)) for v in dvia]
        for i in g:
            if nodes[i][0] == 'via':
                v = next(v for v in rv if v['uuid'] == nodes[i][1])
                if any(gg.intersects(Point(v['at']).buffer(v['size'] / 2)) for L, gg in dgeo):
                    ends.append([v['at'][0], v['at'][1], 'via'])
                continue
            if nodes[i][0] != 'seg': continue
            s = next(s for s in rs if s['uuid'] == nodes[i][1])
            for e in (s['start'], s['end']):
                if any((L == '*' or L == s['layer']) and gg.contains(Point(e)) for L, gg in dgeo):
                    ends.append([e[0], e[1], s['layer']])
        out.append(dict(pads=P, ends=ends))
    for s in dseg:
        if s['uuid'] not in plan['seg_del']: plan['seg_del'].append(s['uuid'])
    for v in dvia:
        if v['uuid'] not in plan['via_del']: plan['via_del'].append(v['uuid']); plan['via_del_xy'].append(list(v['at']))
    comps[net] = out
    print('%-30s del seg %3d via %2d  comps %d: %s' % (net, len(dseg), len(dvia), len(out), ' | '.join(','.join(c['pads'][:4]) + (' ends%s' % [(round(e[0], 2), round(e[1], 2), e[2][0]) for e in c['ends']] if c['ends'] else '') for c in out)))
json.dump(plan, open(outp, 'w'), indent=1)
json.dump(comps, open(outc, 'w'), indent=1)
print('plan', {k: len(v) for k, v in plan.items()})
