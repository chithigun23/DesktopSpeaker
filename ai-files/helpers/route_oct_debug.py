#!/usr/bin/env python3
"""route_oct_debug.py GEO DRU PRO NET PADA PADB OUT.png [layer] : render the A* window rasters of one connection
(green = free, dark = blocked, red = start nodes, blue = target nodes, yellow = via-ok) for diagnosis. No board is written."""
import sys, os, zlib, struct, types
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import route_oct as RO

def png(path, rgb):
    H, W, _ = rgb.shape
    raw = b''.join(b'\x00' + rgb[y].tobytes() for y in range(H))
    def ch(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 6)) + ch(b'IEND', b''))

geo, dru, pro, net, pa, pb, out = sys.argv[1:8]
li = int(sys.argv[8]) if len(sys.argv) > 8 else 0
a = types.SimpleNamespace(via_cost=1.5, turn_cost=1.0, dir_pen=0.1, bcu_cost=1.3, b_island=3.0, b_void=3.0, f_void=2.0, pair_attract=0.6, pair_avoid=1.0, margins=[4.0], max_exp=3e7, pad_pen=0.0, pad_halo=0.6, soft_pen=20.0, hweight=1.0, hweight_cells=1.5e6, max_offsets=2)
B = RO.Board(geo, dru, pro, RO.load_core(os.path.dirname(os.path.abspath(out))))
R = RO.Router(B, a, {})
pf = R.prof(net)
A = next(p for p in B.pads if '%s-%s' % (p['ref'], p['num']) == pa); Bp = next(p for p in B.pads if '%s-%s' % (p['ref'], p['num']) == pb)
exA = R.exits(A, pf); exB = R.exits(Bp, pf)
print('profile', pf); print('exits A', [(e['var'], e['d'], e['node'], e['width']) for e in exA]); print('exits B', [(e['var'], e['d'], e['node'], e['width']) for e in exB])
nodes = [e['node'] for e in exA + exB] + [(int(A['x'] / RO.G), int(A['y'] / RO.G)), (int(Bp['x'] / RO.G), int(Bp['y'] / RO.G))]
xs = [n[0] * RO.G for n in nodes]; ys = [n[1] * RO.G for n in nodes]
R.off = (int(round(A['x']*1e6)) % RO.GN, int(round(A['y']*1e6)) % RO.GN)
win = R.window(pf, (min(xs) - 4, min(ys) - 4, max(xs) + 4, max(ys) + 4), [], [(A['x'], A['y'], 1.2), (Bp['x'], Bp['y'], 1.2)])
fr = win['free'][li].astype(bool)
rgb = np.zeros((win['H'], win['W'], 3), np.uint8); rgb[fr] = (40, 140, 40); rgb[~fr] = (30, 30, 30)
rgb[win['viaok'].astype(bool)] = (160, 160, 40)
for col, ex in (((255, 0, 0), exA), ((60, 120, 255), exB)):
    for e in ex:
        x, y = e['node'][0] - win['x0i'], e['node'][1] - win['y0i']
        rgb[max(0, y - 2):y + 3, max(0, x - 2):x + 3] = col
for p, col in ((A, (255, 128, 128)), (Bp, (128, 180, 255))):
    x, y = int(round(p['x'] / RO.G)) - win['x0i'], int(round(p['y'] / RO.G)) - win['y0i']
    rgb[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = col
png(out, rgb); print('window', win['W'], win['H'], 'free share', fr.mean())
