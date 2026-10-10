"""flatpak: route_r6d_view.py BOARD OUT.png X0 Y0 W H [PXMM] [LAYERS] [NET,NET..] : net-aware raster view of a board region.
LAYERS: string of F,B,2 (default FB). F.Cu items red/brown, B.Cu blue, In2 fills faint green; GND copper grey; highlighted nets in bright colours (legend printed).
Zones: only F.Cu non-GND fills drawn solid, GND fills drawn faint. Grid: 1 mm light, 5 mm dark (labels printed as origin)."""
import sys, zlib, struct, numpy as np, pcbnew
MM = 1e6
a = sys.argv
b = pcbnew.LoadBoard(a[1]); out = a[2]; X0, Y0, W, H = map(float, a[3:7])
S = float(a[7]) if len(a) > 7 else 30.0
LS = a[8] if len(a) > 8 else 'FB'
HL = a[9].split(',') if len(a) > 9 and a[9] else []
nw, nh = int(W * S), int(H * S)
img = np.full((nh, nw, 3), 255, np.uint8)
ys = (np.arange(nh) + 0.5) / S + Y0; xs = (np.arange(nw) + 0.5) / S + X0
PAL = [(255, 200, 0), (0, 200, 0), (255, 0, 255), (0, 220, 220), (255, 120, 0), (120, 0, 255), (0, 120, 0), (200, 0, 80), (120, 80, 0), (0, 80, 200)]
def full(n):
    if b.FindNet(n) is not None: return n
    for k in b.GetNetsByName().keys():
        if str(k).endswith('/' + n): return str(k)
    return n
HL = [full(n) for n in HL]
for i, n in enumerate(HL): print('colour', PAL[i % len(PAL)], n)
def col(net, base):
    if net in HL: return PAL[HL.index(net) % len(PAL)]
    if net == 'GND': return {'F': (150, 150, 150), 'B': (150, 170, 210), '2': (200, 230, 200)}[base]
    return {'F': (200, 40, 40), 'B': (40, 70, 220), '2': (120, 200, 120)}[base]
def blend(mask, c, alpha=1.0):
    if mask is None: return
    if isinstance(mask, tuple):
        r0, c0, m = mask; sub = img[r0:r0 + m.shape[0], c0:c0 + m.shape[1]]
    else: sub, m = img, mask
    if alpha >= 1: sub[m] = c
    else: sub[m] = (sub[m] * (1 - alpha) + np.array(c) * alpha).astype(np.uint8)
def fill_poly(rings):
    """even-odd fill of a list of rings (list of (x,y) mm) -> (r0,c0,mask) or None"""
    E = []
    for ring in rings:
        a_ = np.array(ring, float)
        if len(a_) < 3: continue
        E.append(np.hstack([a_, np.roll(a_, -1, 0)]))
    if not E: return None
    E = np.vstack(E)
    if E[:, 0].max() < X0 or E[:, 0].min() > X0 + W or E[:, 1].max() < Y0 or E[:, 1].min() > Y0 + H: return None
    E = E[(np.maximum(E[:, 1], E[:, 3]) >= Y0) & (np.minimum(E[:, 1], E[:, 3]) <= Y0 + H)]
    r0 = max(int((E[:, 1:4:2].min() - Y0) * S) - 1, 0); r1 = min(int((E[:, 1:4:2].max() - Y0) * S) + 2, nh)
    m = np.zeros((nh, nw), bool)
    for r in range(r0, r1):
        y = ys[r]; y1, y2 = E[:, 1], E[:, 3]
        sel = (y1 <= y) != (y2 <= y)
        if not sel.any(): continue
        e = E[sel]; xc = np.sort(e[:, 0] + (y - e[:, 1]) * (e[:, 2] - e[:, 0]) / (e[:, 3] - e[:, 1]))
        for k in range(0, len(xc) - 1, 2):
            c0 = max(int(np.ceil((xc[k] - X0) * S - 0.5)), 0); c1 = min(int(np.floor((xc[k + 1] - X0) * S - 0.5)) + 1, nw)
            if c1 > c0: m[r, c0:c1] = True
    return m
def polyset_rings(ps):
    rings = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i); rings.append([(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())])
        for h in range(ps.HoleCount(i)):
            o = ps.Hole(i, h); rings.append([(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())])
    return rings
def seg_mask(x1, y1, x2, y2, w):
    r = w / 2
    c0 = max(int((min(x1, x2) - r - X0) * S) - 1, 0); c1 = min(int((max(x1, x2) + r - X0) * S) + 2, nw)
    r0 = max(int((min(y1, y2) - r - Y0) * S) - 1, 0); r1 = min(int((max(y1, y2) + r - Y0) * S) + 2, nh)
    if c1 <= c0 or r1 <= r0: return None
    X, Y = np.meshgrid(xs[c0:c1], ys[r0:r1]); dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy
    t = np.clip(((X - x1) * dx + (Y - y1) * dy) / L2, 0, 1) if L2 > 0 else 0
    return (r0, c0, (X - x1 - t * dx) ** 2 + (Y - y1 - t * dy) ** 2 <= r * r)
LID = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu, '2': pcbnew.In2_Cu}
# grid
for gx in range(int(X0), int(X0 + W) + 1):
    c = int((gx - X0) * S)
    if 0 <= c < nw: img[:, c] = (210, 210, 210) if gx % 5 else (120, 120, 120)
for gy in range(int(Y0), int(Y0 + H) + 1):
    r = int((gy - Y0) * S)
    if 0 <= r < nh: img[r, :] = (210, 210, 210) if gy % 5 else (120, 120, 120)
VIEW = pcbnew.BOX2I(pcbnew.VECTOR2I(int(X0 * MM), int(Y0 * MM)), pcbnew.VECTOR2I(int(W * MM), int(H * MM)))
order = [l for l in '2BF' if l in LS]
for l in order:
    L = LID[l]; al = 0.35 if l == '2' else (0.5 if l == 'B' and 'F' in LS else 1.0)
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(L) or not z.HasFilledPolysForLayer(L) or not VIEW.Intersects(z.GetBoundingBox()): continue
        n = str(z.GetNetname()); m = fill_poly(polyset_rings(z.GetFilledPolysList(L)))
        blend(m, col(n, l), 0.25 if n == 'GND' and n not in HL else 0.45 * al + 0.2)
    for t in b.GetTracks():
        if not VIEW.Intersects(t.GetBoundingBox()): continue
        n = str(t.GetNetname())
        if t.GetClass() == 'PCB_VIA':
            if l != 'F' and 'F' in LS: continue
            x, y = t.GetX() / MM, t.GetY() / MM; d = t.GetWidth(pcbnew.F_Cu) / MM
            blend(seg_mask(x, y, x, y, d), col(n, 'F') if n in HL else (60, 60, 60)); blend(seg_mask(x, y, x, y, t.GetDrillValue() / MM), (255, 255, 255))
        elif t.GetLayer() == L:
            s, e = t.GetStart(), t.GetEnd(); blend(seg_mask(s.x / MM, s.y / MM, e.x / MM, e.y / MM, t.GetWidth() / MM), col(n, l), al)
    for f in b.GetFootprints():
        if not VIEW.Intersects(f.GetBoundingBox()): continue
        for p in f.Pads():
            if not p.IsOnLayer(L): continue
            n = str(p.GetNetname()); m = fill_poly(polyset_rings(p.GetEffectivePolygon(L)))
            c = col(n, l); c = tuple(int(v * 0.75) for v in c) if n not in HL else c
            blend(m, c, al)
            if p.GetDrillSizeX() > 0: blend(seg_mask(p.GetX() / MM, p.GetY() / MM, p.GetX() / MM, p.GetY() / MM, p.GetDrillSizeX() / MM), (255, 255, 255))
H_, W_ = img.shape[:2]
raw = b''.join(b'\x00' + img[i].tobytes() for i in range(H_))
def ch(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
open(out, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', W_, H_, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b''))
print('wrote', out, W_, H_, 'origin', X0, Y0, 'px/mm', S)
