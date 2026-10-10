"""flatpak: route_r6b_gnd2.py IN OUT [win] : A* GND attach for isolated GND groups (after route_r6b_gnd.py).
F.Cu only, 0.3/0.25/0.2 mm. Target = main-group GND copper on F.Cu (pads, tracks, vias, F.Cu GND fills) or any cell
where a GND via is legal (not inside a non-GND In2 island, not in/over a pad, 0.5/0.2 only inside NECK_*). A new via is
placed at the end cell when the path ends on a via cell."""
import sys, json, math
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6b_route import *
from route_r6a_lib import place_via
inp, outp = sys.argv[1:3]; WIN = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
R = Router(inp); ctx = R.ctx; b = ctx.b; me = ctx.netid['GND']
R.cur = {'cls': 'GND', 'crit': False, 'bko': False, 'floor': 0.2, 'fine': True, 'cme': 0.2}
def main_idx(comps):
    for i, g in enumerate(comps):
        if any(x[0] == 'zone' and x[2] == pcbnew.In1_Cu for x in g): return i
    return 0
ok, fail = [], []
for rnd in range(3):
    comps = comps_of(ctx, 'GND'); mi = main_idx(comps); main = comps[mi]
    iso = [g for i, g in enumerate(comps) if i != mi]
    print('round', rnd, 'isolated groups', len(iso), flush=True)
    if not iso: break
    progress = 0
    for g in iso:
        pads = [x[1] for x in g if x[0] == 'pad']
        xs = [p.GetX() / MM for p in pads]; ys = [p.GetY() / MM for p in pads]
        x0 = max(int(ctx.cx(min(xs) - WIN)), 0); x1 = min(int(ctx.cx(max(xs) + WIN)), ctx.W)
        y0 = max(int(ctx.cy(min(ys) - WIN)), 0); y1 = min(int(ctx.cy(max(ys) + WIN)), ctx.H)
        win = (y0, y1, x0, x1); h, w = y1 - y0, x1 - x0
        wds = [0.3, 0.25, 0.2]
        code = np.zeros((3, h, w), np.uint8)
        for ti, wd in enumerate(wds):
            ok_ = ~ctx.obstacle(me, 0, y0, y1, x0, x1, wd, 0.2, gndc=0.2)
            code[0][ok_ & (code[0] == 0)] = ti + 1
        src = RC.raster_comp(ctx, g, win); src[1:] = 0
        tgt_main = RC.raster_comp(ctx, [it for it in main if not (it[0] == 'zone' and it[2] != pcbnew.F_Cu)], win); tgt_main[1:] = 0
        vb = ctx.via_obstacle(me, y0, y1, x0, x1, 0.6, 0.2)
        # no via on/over any F.Cu pad (own pads included): pad raster dilated by via radius + 0.15
        padm = ctx.R['pad'][0][y0:y1, x0:x1] != 0
        vb |= ctx.dilate(padm, (0.3 + 0.15) / G)
        vcell = (~vb) & (code[0] > 0)
        tgt = (tgt_main > 0).astype(np.uint8); tgt[0] |= vcell.astype(np.uint8)
        code[0][(code[0] == 0) & (src[0] > 0)] = 3
        srcm = (src > 0).astype(np.uint8)
        if not tgt.any() or not srcm.any(): fail.append([padkey(p) for p in pads]); continue
        sy, sx = np.nonzero(srcm[0]); ty_, tx_ = np.nonzero(tgt[0]); k = np.argmin((ty_ - sy.mean()) ** 2 + (tx_ - sx.mean()) ** 2)
        lay_ok = np.array([1, 0, 0], np.uint8); viaok = np.zeros((h, w), np.uint8); pen = np.zeros((3, h, w), np.uint8)
        sc = (ctypes.c_float * 5)(0, 1.0, 1.15, 1.6, 2.2); path = np.zeros((400000, 3), np.int32)
        code = np.ascontiguousarray(code); srcm = np.ascontiguousarray(srcm); tgt = np.ascontiguousarray(tgt)
        n = RC.lib.astar(3, h, w, code.ctypes.data_as(RC.P_), srcm.ctypes.data_as(RC.P_), tgt.ctypes.data_as(RC.P_), viaok.ctypes.data_as(RC.P_), lay_ok.ctypes.data_as(RC.P_),
                         pen.ctypes.data_as(RC.P_), sc, ctypes.c_float(1.0), ctypes.c_float(1.5), ctypes.c_float(1.0), int(ty_[k]), int(tx_[k]), path.ctypes.data_as(RC.P_), 400000, ctypes.c_int64(5_000_000))
        if n <= 0: fail.append([padkey(p) for p in pads]); continue
        pts = [(int(path[i, 0]), int(path[i, 1]), int(path[i, 2])) for i in range(n)][::-1]
        endc = pts[-1]; viaend = not tgt_main[0, endc[1], endc[2]]
        pl = [(l, y + y0, x + x0, wds[code[l, y, x] - 1] if code[l, y, x] else 0.2, bool(srcm[l, y, x]) or bool(tgt_main[l, y, x])) for (l, y, x) in pts]
        added = RC.emit(ctx, 'GND', pl, {'tiers': wds, 'dv': 0.6, 'drill': 0.3}, {}) if len(pl) > 1 else []
        if viaend:
            ex, ey = ctx.x0 + pl[-1][2] * G, ctx.y0 + pl[-1][1] * G
            v = None
            for d, dr in ((0.6, 0.3), (0.5, 0.2)):
                if d < 0.59 and not R.NECK[pl[-1][1], pl[-1][2]]: continue
                v = place_via(b, 'GND', ex, ey, d, dr, lock=False)
                if v is not None: break
            if v is None:
                for a in added: b.RemoveNative(a)
                ctx.rebuild(); fail.append([padkey(p) for p in pads] + ['via-illegal']); continue
            ctx.add_track(v); added.append(v)
        if added or len(pl) <= 1: ok.append([padkey(p) for p in pads]); progress += 1
    if not progress: break
refill(b); pcbnew.SaveBoard(outp, b)
json.dump({'ok': ok, 'fail': fail}, open(outp.replace('.kicad_pcb', '.gnd2.json'), 'w'), indent=0)
print('attached', len(ok), 'fail', len(fail), fail[:40])
