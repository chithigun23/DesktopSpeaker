"""flatpak: route_r6h_view.py BOARD X0 Y0 X1 Y1 OUT.png [PXMM=20] [NET,NET..|''] [PANELS=FB2]
Region view, three panels F.Cu | B.Cu | In2.Cu side by side, 1 mm grid (5 mm darker, 10 mm black ticks).
Colours: pour fills light, tracks dark, pads medium, vias white ring with black hole; GND copper grey;
listed nets highlighted yellow (tracks/pads/vias). Rule areas BKO/NECK outlined (B panel BKO magenta, NECK cyan)."""
import sys, zlib, struct, math
import numpy as np, pcbnew
MM = 1e6
a = sys.argv; b = pcbnew.LoadBoard(a[1]); X0, Y0, X1, Y1 = map(float, a[2:6]); out = a[6]
S = float(a[7]) if len(a) > 7 else 20.0
HL = set()
for n in (a[8].split(',') if len(a) > 8 and a[8] else []):
    if b.FindNet(n) is not None: HL.add(n)
    else:
        for k in b.GetNetsByName().keys():
            if str(k).endswith('/' + n): HL.add(str(k))
W = int((X1 - X0) * S); H = int((Y1 - Y0) * S)
X = (np.arange(W) + 0.5) / S + X0; Y = (np.arange(H) + 0.5) / S + Y0
LY = [(pcbnew.F_Cu, (200, 40, 40)), (pcbnew.B_Cu, (40, 80, 210)), (pcbnew.In2_Cu, (30, 150, 60))]
PN = a[9] if len(a) > 9 else 'FB2'
LY = [x for x, k in zip(LY, 'FB2') if k in PN]
def seg(img, p, q, w, col):
    r = w / 2; xs = (min(p[0], q[0]) - r, max(p[0], q[0]) + r); ys = (min(p[1], q[1]) - r, max(p[1], q[1]) + r)
    i0 = max(int((xs[0] - X0) * S) - 1, 0); i1 = min(int((xs[1] - X0) * S) + 2, W); j0 = max(int((ys[0] - Y0) * S) - 1, 0); j1 = min(int((ys[1] - Y0) * S) + 2, H)
    if i1 <= i0 or j1 <= j0: return
    xx = X[None, i0:i1]; yy = Y[j0:j1, None]; dx = q[0] - p[0]; dy = q[1] - p[1]; L2 = dx * dx + dy * dy
    t = np.clip(((xx - p[0]) * dx + (yy - p[1]) * dy) / L2, 0, 1) if L2 > 0 else np.zeros_like(xx * yy)
    m = (xx - (p[0] + t * dx)) ** 2 + (yy - (p[1] + t * dy)) ** 2 <= r * r
    img[j0:j1, i0:i1][m] = col
def poly(img, rings, col):
    xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
    i0 = max(int((min(xs) - X0) * S) - 1, 0); i1 = min(int((max(xs) - X0) * S) + 2, W); j0 = max(int((min(ys) - Y0) * S) - 1, 0); j1 = min(int((max(ys) - Y0) * S) + 2, H)
    if i1 <= i0 or j1 <= j0: return
    xx = X[None, i0:i1]; yy = Y[j0:j1, None]; ins = np.zeros((j1 - j0, i1 - i0), bool)
    for ring in rings:
        n = len(ring)
        for k in range(n):
            xa, ya = ring[k]; xb, yb = ring[(k + 1) % n]
            if ya == yb: continue
            c = (ya > yy) != (yb > yy); xi = xa + (yy - ya) * (xb - xa) / (yb - ya); ins ^= c & (xx < xi)
    img[j0:j1, i0:i1][ins] = col
def ringpts(o): return [(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())]
def outline(img, ring, col, w=0.08):
    for k in range(len(ring)): seg(img, ring[k], ring[(k + 1) % len(ring)], w, col)
box = pcbnew.BOX2I(pcbnew.VECTOR2I(int(X0 * MM), int(Y0 * MM)), pcbnew.VECTOR2I(int((X1 - X0) * MM), int((Y1 - Y0) * MM)))
panels = []
for L, col in LY:
    img = np.zeros((H, W, 3), np.uint8); img[:] = (250, 250, 250)
    light = tuple(int(255 - (255 - c) * 0.3) for c in col); dark = col; mid = tuple(int(255 - (255 - c) * 0.6) for c in col)
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(L) or not z.HasFilledPolysForLayer(L): continue
        if not box.Intersects(z.GetBoundingBox()): continue
        fp = z.GetFilledPolysList(L); g = str(z.GetNetname()) == 'GND'
        for i in range(fp.OutlineCount()):
            rings = [ringpts(fp.Outline(i))] + [ringpts(fp.Hole(i, h)) for h in range(fp.HoleCount(i))]
            poly(img, rings, (228, 228, 228) if g else light)
    for f in b.GetFootprints():
        if not box.Intersects(f.GetBoundingBox()): continue
        for p in f.Pads():
            if not p.IsOnLayer(L): continue
            n = str(p.GetNetname()); c = (255, 210, 0) if n in HL else ((150, 150, 150) if n == 'GND' else mid)
            sh = p.GetEffectivePolygon(L)
            for i in range(sh.OutlineCount()): poly(img, [ringpts(sh.Outline(i))], c)
            if p.GetDrillSizeX() > 0: seg(img, (p.GetX() / MM, p.GetY() / MM), (p.GetX() / MM, p.GetY() / MM), p.GetDrillSizeX() / MM, (0, 0, 0))
    for t in b.Tracks():
        if not box.Intersects(t.GetBoundingBox()): continue
        n = str(t.GetNetname())
        if t.GetClass() == 'PCB_VIA':
            c = (t.GetX() / MM, t.GetY() / MM)
            seg(img, c, c, t.GetWidth(pcbnew.F_Cu) / MM, (255, 210, 0) if n in HL else ((120, 120, 120) if n == 'GND' else (255, 255, 255)))
            seg(img, c, c, t.GetWidth(pcbnew.F_Cu) / MM - 0.12, (90, 90, 90) if n == 'GND' else dark)
            seg(img, c, c, t.GetDrillValue() / MM, (0, 0, 0))
        elif t.GetLayer() == L:
            seg(img, (t.GetStart().x / MM, t.GetStart().y / MM), (t.GetEnd().x / MM, t.GetEnd().y / MM), t.GetWidth() / MM, (230, 180, 0) if n in HL else ((110, 110, 110) if n == 'GND' else dark))
    for z in b.Zones():
        if not z.GetIsRuleArea() or not z.IsOnLayer(L) or not box.Intersects(z.GetBoundingBox()): continue
        nm = z.GetZoneName()
        if nm.startswith('BKO') or nm.startswith('NECK') or 'KEEPOUT' in nm: outline(img, ringpts(z.Outline().Outline(0)), (200, 0, 200) if not nm.startswith('NECK') else (0, 170, 200))
    # grid
    for k in range(int(math.ceil(X0)), int(X1) + 1):
        i = int((k - X0) * S)
        if 0 <= i < W: img[:, i] = img[:, i] * 0.75 if k % 5 else img[:, i] * 0.35
        if k % 10 == 0 and 0 <= i < W: img[:6, max(i - 1, 0):i + 2] = 0
    for k in range(int(math.ceil(Y0)), int(Y1) + 1):
        j = int((k - Y0) * S)
        if 0 <= j < H: img[j, :] = img[j, :] * 0.75 if k % 5 else img[j, :] * 0.35
        if k % 10 == 0 and 0 <= j < H: img[max(j - 1, 0):j + 2, :6] = 0
    panels.append(img)
sep = np.zeros((H, 6, 3), np.uint8)
img = panels[0]
for q in panels[1:]: img = np.concatenate([img, sep, q], axis=1)
Hh, Ww = img.shape[:2]
raw = b''.join(b'\x00' + img[i].tobytes() for i in range(Hh))
def ch(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
open(out, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', Ww, Hh, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 6)) + ch(b'IEND', b''))
print('wrote', out, Ww, Hh, 'panels F|B|In2, origin', X0, Y0, 'px/mm', S)
