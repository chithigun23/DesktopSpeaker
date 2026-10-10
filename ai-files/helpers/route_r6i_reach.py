"""flatpak: route_r6i_reach.py BOARD NET X0 Y0 X1 Y1 OUT.png [W=0.2] [VIAISL]   env: R6I_LAYERS=0,2  R6I_DV=0.6  R6I_S=1 (scale)  R6I_SRC=REF.PAD (source component)
Reachability map for the R6i router (route_r6h patches + R6i via-in-pad/NPTH masks): flood fill from NET's first
copper component over free cells of the listed layers (0 F, 1 In2, 2 B), changing layer at via-legal cells.
Panels per layer: dark = blocked, light blue = free not reachable, green = reachable, yellow = reachable + via-legal,
red = own pads/copper of the source component, magenta = other components of NET. 1 mm grid ticks every 5 mm."""
import sys, os, zlib, struct
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
a = sys.argv
if len(a) > 9 and a[9]: os.environ['R6H_VIAISL'] = a[9]
import route_r6h_route as H
H.VIAISL = os.environ.get('R6H_VIAISL', '')
import route_r6c_route as RR
from route_r6c_route import *
import numpy as np
board, net = a[1], a[2]; X0, Y0, X1, Y1 = map(float, a[3:7]); out = a[7]
W = float(a[8]) if len(a) > 8 else 0.2
LS = [int(x) for x in (os.environ.get('R6I_LAYERS', '0,2')).split(',')]
DV = float(os.environ.get('R6I_DV', '0.6'))
R = RR.Router(board); ctx = R.ctx; b = ctx.b; net = full(net, b); c = ctx.cls.get(net, 'Default'); P = dict(PRM.get(c, PRM['Default']))
PADM = np.zeros((ctx.H, ctx.W), bool)
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetDrillSizeX() > 0: continue
        for L in (pcbnew.F_Cu, pcbnew.B_Cu):
            if p.IsOnLayer(L):
                for ring in ctx.pad_poly(p, L):
                    if len(ring) >= 3: ctx.poly_fill(PADM, [ring], True)
R.cur = {'cls': c, 'crit': net in CRIT, 'bko': c not in BKO_EXEMPT_CLS and net not in BKO_EXTRA, 'floor': P['floor'], 'fine': DV < 0.55, 'cme': P['cme']}
me = ctx.netid[net]
gx0, gx1 = int(ctx.cx(X0)), int(ctx.cx(X1)); gy0, gy1 = int(ctx.cy(Y0)), int(ctx.cy(Y1)); h, w = gy1 - gy0, gx1 - gx0
comps = comps_of(ctx, net); win = (gy0, gy1, gx0, gx1)
si = 0
if os.environ.get('R6I_SRC'):   # source = component holding this pad (REF.PAD)
    for k, cc in enumerate(comps):
        if any(it[0] == 'pad' and it[1].GetParentFootprint().GetReference() + '.' + str(it[1].GetNumber()) == os.environ['R6I_SRC'] for it in cc): si = k
src = raster_comp(ctx, comps[si], win) > 0
oth = np.zeros_like(src)
for k, cc in enumerate(comps):
    if k != si: oth |= raster_comp(ctx, cc, win) > 0
free = np.zeros((3, h, w), bool)
for li in LS: free[li] = ~ctx.obstacle(me, li, gy0, gy1, gx0, gx1, W, P['cme'], gndc=0.2) | src[li] | oth[li]
vok = ~ctx.via_obstacle(me, gy0, gy1, gx0, gx1, DV, P['cme'], gndc=0.2) & ~PADM[gy0:gy1, gx0:gx1]
rea = src & free
for it in range(20000):
    old = rea.sum()
    for li in LS:
        r = rea[li]; n = r.copy()
        n[1:] |= r[:-1]; n[:-1] |= r[1:]; n[:, 1:] |= r[:, :-1]; n[:, :-1] |= r[:, 1:]
        rea[li] = n & free[li]
    anyv = np.zeros((h, w), bool)
    for li in LS: anyv |= rea[li] & vok
    for li in LS: rea[li] |= anyv & free[li]
    if rea.sum() == old: break
hit = bool((rea & oth).any())
img = np.zeros((h, (w + 6) * len(LS), 3), np.uint8)
for k, li in enumerate(LS):
    A = np.zeros((h, w, 3), np.uint8); A[:] = (40, 40, 60); A[free[li]] = (200, 220, 255); A[rea[li]] = (120, 210, 120)
    A[rea[li] & vok] = (250, 240, 90); A[src[li]] = (230, 40, 40); A[oth[li]] = (220, 0, 220)
    for mm in range(int(X0) + 1, int(X1) + 1):
        i = int(ctx.cx(mm)) - gx0
        if 0 <= i < w: A[:, i] = A[:, i] * (0.4 if mm % 5 == 0 else 0.8)
    for mm in range(int(Y0) + 1, int(Y1) + 1):
        j = int(ctx.cy(mm)) - gy0
        if 0 <= j < h: A[j, :] = A[j, :] * (0.4 if mm % 5 == 0 else 0.8)
    img[:, k * (w + 6):k * (w + 6) + w] = A
S = int(os.environ.get('R6I_S', '1'))
if S > 1: img = np.kron(img, np.ones((S, S, 1), np.uint8))
Hh, Ww = img.shape[:2]
raw = b''.join(b'\x00' + img[i].tobytes() for i in range(Hh))
def ch(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
open(out, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', Ww, Hh, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b''))
print('wrote', out, Ww, Hh, 'px/mm', S / G, 'layers', LS, 'reaches other component:', hit, 'comps', len(comps))
