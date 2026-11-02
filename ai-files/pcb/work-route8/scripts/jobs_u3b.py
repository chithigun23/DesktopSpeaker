#!/usr/bin/env python3
"""jobs_u3b.py GEO OUT_JOBS OUT_PLAN [--lb 0.8] [--only net,...] : RT-8 U3 escape-ordered jobs (hr8).
Each U3 job keeps the exit lanes of every U3 pin routed LATER free (F.Cu block + no-via box, rule: no route turns across an
unrouted pin's exit within LB mm of its pad tip). Order per side: pins whose target is behind the package first, then
left-turning pins by angle (most extreme first), right-turning likewise, straight ones last. Secondary pads afterwards."""
import sys, json, math
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from jobs_u3 import P1, P2, pc   # job lists (tgt_near) of the first attempt
a = sys.argv
geo, outj, outp = a[1:4]
LB = float(a[a.index('--lb') + 1]) if '--lb' in a else 0.8
CX, CY = 128.0, 76.5
TIP = 5.67 + 0.775


def side(p):
    x, y = pc[p][0] - CX, pc[p][1] - CY
    if x > 5: return 'E', (1, 0)
    if x < -5: return 'W', (-1, 0)
    if y > 5: return 'S', (0, 1)
    return 'N', (0, -1)


def lane(p):
    x, y = pc[p]; s, (nx, ny) = side(p)
    t0 = TIP; t1 = TIP + LB
    if nx: xa, xb = sorted([CX + nx * t0, CX + nx * t1]); return [xa, y - 0.15, xb, y + 0.15]
    ya, yb = sorted([CY + ny * t0, CY + ny * t1]); return [x - 0.15, ya, x + 0.15, yb]


u3j = [j for j in P1 + P2 if isinstance(j['from'], str) and j['from'].startswith('U3-')]
sec = [j for j in P1 + P2 if j not in u3j]
info = []
for j in u3j:
    p = j['from']; s, (nx, ny) = side(p); tx, ty = j['tgt_near'][:2]
    vx, vy = tx - pc[p][0], ty - pc[p][1]
    behind = (tx - CX) * nx + (ty - CY) * ny < 0
    # angle of the target relative to the outward normal, positive = clockwise (screen)
    th = math.degrees(math.atan2(nx * vy - ny * vx, nx * vx + ny * vy))
    info.append((j, s, behind, th))
order = []
for s in 'ESNW':
    S = [i for i in info if i[1] == s]
    nx, ny = side(S[0][0]['from'])[1]; lx, ly = ny, -nx
    pos = lambda i: -(pc[i[0]['from']][0] * lx + pc[i[0]['from']][1] * ly)      # from the left end
    F = sorted([i for i in S if not i[2]], key=pos)
    # longest non-decreasing run of target angle along the side = planar F.Cu fan; the rest cross -> via first
    n = len(F); best = [1] * n; prv = [-1] * n
    for b in range(n):
        for c in range(b):
            if F[c][3] <= F[b][3] and best[c] + 1 > best[b]: best[b] = best[c] + 1; prv[b] = c
    k = max(range(n), key=lambda b: best[b]) if n else -1; lis = set()
    while k >= 0: lis.add(id(F[k])); k = prv[k]
    cross = [i for i in F if id(i) not in lis]
    P = [i for i in F if id(i) in lis]
    left = [i for i in P if i[3] < -20]; right = [i for i in P if i[3] > 20][::-1]; straight = [i for i in P if abs(i[3]) <= 20]
    order += [i for i in S if i[2]] + cross + left + right + straight
    print(s, 'behind', [i[0]['from'] for i in S if i[2]], 'cross', [i[0]['from'] for i in cross], 'L', [i[0]['from'] for i in left], 'R', [i[0]['from'] for i in right], 'S', [i[0]['from'] for i in straight])
only = set(a[a.index('--only') + 1].split(',')) if '--only' in a else None
jobs = []
for k, (j, s, b, th) in enumerate(order):
    later = [o[0]['from'] for o in order[k + 1:] if o[0]['net'] != j['net']]
    j = dict(j)
    j['block'] = [lane(p) + ['F.Cu'] for p in later]
    j['noviabox'] = [[l[0] - 0.45, l[1] - 0.45, l[2] + 0.45, l[3] + 0.45] for l in (lane(p) for p in later)]
    j['_info'] = '%s %s %.0f' % (s, 'behind' if b else '', th)
    jobs.append(j)
jobs += sec
if only: jobs = [j for j in jobs if j['net'] in only]
json.dump(dict(geo=geo, out_plan=outp, jobs=jobs), open(outj, 'w'), indent=0)
for j in jobs: print(j['net'], j['from'], j.get('_info', ''))
