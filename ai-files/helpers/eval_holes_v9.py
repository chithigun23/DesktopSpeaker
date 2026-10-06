"""Plate-model preview of a raw v8 floorplan: python3 eval_holes_v8.py floorplan.json (writes /tmp layout + runs plate_v7)."""
import json, sys, subprocess
ROOT = '/home/chithi/Desktop/DesktopSpeaker/ai-files/'
C = json.load(open(ROOT + 'pcb/cells-v9.json')); f = json.load(open(sys.argv[1]))
MG, MT, HOLE = 0.5, 2.3, 7.8
W, H = f['W'], f['H']; ab = f['abs']
u0, v0 = -W / 2, -H / 2
def uv(x, y): return u0 + x, v0 + H - y          # tile coords (x right, y down from the rear) -> board centred frame, v up
holes = [uv(ab[n][0] + HOLE / 2, ab[n][1] + HOLE / 2) for n in ab if n.startswith('H')]
for cn, l in C['cellholes'].items():
    for du, dv in l: holes.append(uv(ab[cn][0] + MG + du, ab[cn][1] + MT + dv))
parts = {}
for r, (cn, du, dv) in C['heavy'].items():
    cx, cy = uv(ab[cn][0] + MG + du, ab[cn][1] + MT + dv); parts[r] = dict(rect=[cx - 3, cy - 3, cx + 3, cy + 3])
json.dump(dict(board=dict(w=W, d=H, u0=u0, v0=v0), holes=[dict(name='H', u=a, v=b) for a, b in holes], parts=parts), open('/tmp/lay_v8.json', 'w'))
print(sys.argv[1].split('/')[-1], 'W %.1f H %.1f area %.0f' % (W, H, W * H), 'holes', len(holes))
