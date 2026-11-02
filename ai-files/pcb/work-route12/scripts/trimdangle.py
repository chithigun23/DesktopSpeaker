#!/usr/bin/env python3
"""trimdangle.py BOARD.kicad_pcb DRC.json OUT.json : for each dangling track end reported by DRC, cut the segment back to the nearest
point where another same-net segment end or via lies on it (the route attach point). Emits seg_set entries (edit.py)."""
import sys, json, math
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from pcbtext import items
IT = items(sys.argv[1]); D = json.load(open(sys.argv[2]))
segs = [d for d in IT if d['kind'] == 'segment']; vias = [d for d in IT if d['kind'] == 'via']
def onseg(p, a, b, tol=0.005):
    ax, ay = a; bx, by = b; L = math.dist(a, b)
    if L < 1e-9: return False
    t = ((p[0]-ax)*(bx-ax) + (p[1]-ay)*(by-ay)) / L**2
    if t < -1e-6 or t > 1 + 1e-6: return False
    return math.dist(p, (ax + t*(bx-ax), ay + t*(by-ay))) < tol
out = {}
for v in D['violations']:
    if v['type'] != 'track_dangling': continue
    u = v['items'][0]['uuid']; S = next((d for d in segs if d['uuid'] == u), None)
    if not S: continue
    a, b = S['start'], S['end']
    ends = {}
    for k in (a, b):
        ends[k] = sum(1 for d in segs if d is not S and d['net'] == S['net'] and d.get('layer') == S.get('layer') and (math.dist(k, d['start']) < 0.005 or math.dist(k, d['end']) < 0.005)) \
                  + sum(1 for w in vias if w['net'] == S['net'] and math.dist(k, w['at']) < 0.005)
    dang = [k for k in (a, b) if ends[k] == 0]
    if len(dang) != 1: print('skip', u, ends); continue
    dk = dang[0]; keep = b if dk == a else a
    tol = S['width'] / 2 + 0.01
    def proj(q):
        ax, ay = a; bx, by = b; L2 = math.dist(a, b) ** 2; t = ((q[0]-ax)*(bx-ax) + (q[1]-ay)*(by-ay)) / L2
        return (round(ax + t*(bx-ax), 4), round(ay + t*(by-ay), 4))
    pts = [proj(d[e]) for d in segs if d is not S and d['net'] == S['net'] and d.get('layer') == S.get('layer') for e in ('start', 'end') if onseg(d[e], a, b, tol)]
    pts += [proj(w['at']) for w in vias if w['net'] == S['net'] and onseg(w['at'], a, b, tol)]
    pts = [p for p in pts if math.dist(p, keep) > 0.005]
    if not pts: print('no attach', u); continue
    p = min(pts, key=lambda q: math.dist(q, dk))
    out[u[:8]] = [keep[0], keep[1], p[0], p[1]]
    print(S['net'], 'cut', dk, '->', p)
json.dump(dict(seg_set=out), open(sys.argv[3], 'w'), indent=1)
