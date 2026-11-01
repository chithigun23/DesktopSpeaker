"""probe.py STEM [--detail REF ...] : whole-board exit probe (same model as work-r10 r10lib.Board.exits / exitprobe.py).
Needs STEM.geo.json (route_oct_export) and STEM.dump.json (work-r8 dump.py). Net list nets.txt (the 140 signal nets of I3-H0)."""
import sys, os, json
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r10/scripts')
from r10lib import Board
W = '/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route'
st = sys.argv[1]
B = Board(f'{W}/{st}.geo.json', f'{W}/{st}.dump.json', f'{W}/nets.txt', f'{W}/base.kicad_dru')
bad = B.exits(list(B.pads))
print(len(bad))
for b in bad: print(b)
if '--detail' in sys.argv:
    import route_oct_rules as RR
    from shapely.geometry import LineString, Point
    refs = sys.argv[sys.argv.index('--detail') + 1:]
    for r in refs:
        po = B.all_pad_obs(B.pose[r][:2], 9.0)
        for q in B.sigpads(r):
            for (dx, dy), h in B.dirs(r, q):
                a = (q['x'] + dx * h, q['y'] + dy * h); b = (a[0] + dx * 1.0, a[1] + dy * 1.0)
                w = RR.NECK_W if B.NECK.contains(Point(q['x'], q['y'])) else 0.25
                tr = LineString([a, b]).buffer(w / 2, cap_style=2); hits = []
                cands = [B.cop[i] for i in B.coptree.query(tr.buffer(2.1))] + [o for o in po if o[0].distance(tr) < 2.1]
                for g, net, cls, typ, name in cands:
                    if net and net == q['net']: continue
                    inneck = B.NECK.intersects(g.buffer(0.01)) and B.NECK.intersects(tr)
                    c = (RR.clr_neck if inneck else RR.clr_strict)(q['cls'], q['net'], cls, typ)
                    d = g.distance(tr)
                    if d < c - 1e-6: hits.append((round(c - d, 3), name, round(d, 3), c, [round(v, 3) for v in g.bounds]))
                print(r, q['num'], q['net'], 'pad', round(q['x'], 3), round(q['y'], 3), 'dir', (round(dx, 2), round(dy, 2)), 'w', w, 'OK' if not hits else hits)
