"""flatpak: route_r6c_dbg.py BOARD NET X0 Y0 X1 Y1 OUT.png [W] : A* obstacle map (F.Cu left, B.Cu right) for NET at track width W (default 0.25); blue = free, dark = blocked, red/green = net pads/copper, yellow = via-legal"""
import sys, zlib, struct
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6c_route import *
board, net, x0, y0, x1, y1, out = sys.argv[1:8]; W = float(sys.argv[8]) if len(sys.argv) > 8 else 0.25
R = Router(board); ctx = R.ctx; net = full(net, ctx.b); c = ctx.cls.get(net, 'Default'); P = dict(PRM.get(c, PRM['Default']))
R.cur = {'cls': c, 'crit': net in CRIT, 'bko': c not in BKO_EXEMPT_CLS and net not in BKO_EXTRA, 'floor': P['floor'], 'fine': False, 'cme': P['cme']}
me = ctx.netid[net]
gx0, gx1 = int(ctx.cx(float(x0))), int(ctx.cx(float(x1))); gy0, gy1 = int(ctx.cy(float(y0))), int(ctx.cy(float(y1)))
import os; S = int(os.environ.get("DBG_S", "4")); h, w = gy1 - gy0, gx1 - gx0
layers = []
for li in (0, 2):
    bl = ctx.obstacle(me, li, gy0, gy1, gx0, gx1, W, P['cme'], gndc=0.2)
    layers.append(bl)
vb = ctx.via_obstacle(me, gy0, gy1, gx0, gx1, 0.6, P['cme'], gndc=0.2)
own = np.zeros((h, w), bool)
for f in ctx.b.GetFootprints():
    for p in f.Pads():
        if str(p.GetNetname()) == net:
            ctx.circ_fill  # noqa
            cx_ = ctx.cx(p.GetX() / MM) - gx0; cy_ = ctx.cy(p.GetY() / MM) - gy0
            own[max(int(cy_) - 6, 0):max(int(cy_) + 6, 0), max(int(cx_) - 6, 0):max(int(cx_) + 6, 0)] = True
img = np.zeros((h, 2 * w + 4, 3), np.uint8)
for k, bl in enumerate(layers):
    a = np.zeros((h, w, 3), np.uint8); a[:] = (200, 220, 255); a[bl] = (40, 40, 60); a[~vb & ~bl] = (255, 255, 120); a[own] = (230, 60, 60)
    img[:, k * (w + 4):k * (w + 4) + w] = a
DS = int(os.environ.get('DBG_DS', '1'))
if DS > 1:
    hh, ww = img.shape[0] // DS * DS, img.shape[1] // DS * DS
    img = img[:hh:DS, :ww:DS]
img = np.kron(img, np.ones((S, S, 1), np.uint8))
H_, W_ = img.shape[:2]
raw = b''.join(b'\x00' + img[i].tobytes() for i in range(H_))
def ch(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
open(out, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', W_, H_, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b''))
print('wrote', out, W_, H_, 'origin', x0, y0, 'px/mm', S / G)
