"""flatpak: route_r6k_usbcpl.py BOARD [A B] : per-net uncoupled sections of a differential pair (default /USB_DP /USB_DN, F.Cu):
a point of A is coupled when the nearest B track centreline on the same layer is 0.40-0.50 mm away (0.25 tracks, gap 0.15-0.25).
Prints coupled / uncoupled length per net and the uncoupled runs (start, end, length)."""
import sys, math, pcbnew
MM = 1e6; b = pcbnew.LoadBoard(sys.argv[1]); A, B = (sys.argv[2], sys.argv[3]) if len(sys.argv) > 3 else ('/USB_DP', '/USB_DN')
def segs(n): return [(t.GetLayer(), t.GetStart().x / MM, t.GetStart().y / MM, t.GetEnd().x / MM, t.GetEnd().y / MM, t.GetWidth() / MM) for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and str(t.GetNetname()) == n]
def dseg(px, py, s):
    _, x0, y0, x1, y1, _ = s; dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy
    u = 0 if L2 == 0 else max(0, min(1, ((px - x0) * dx + (py - y0) * dy) / L2)); return math.hypot(px - x0 - u * dx, py - y0 - u * dy)
for X, Y in ((A, B), (B, A)):
    sx, sy = segs(X), segs(Y); cp = un = 0.0; runs = []; cur = None
    for s in sx:
        L = math.hypot(s[3] - s[1], s[4] - s[2]); n = max(1, int(L / 0.05))
        for k in range(n):
            u = (k + 0.5) / n; px, py = s[1] + u * (s[3] - s[1]), s[2] + u * (s[4] - s[2])
            d = min([dseg(px, py, t) for t in sy if t[0] == s[0]] or [9])
            ok = 0.395 <= d <= 0.505
            if ok: cp += L / n
            else: un += L / n
            if not ok:
                if cur is None: cur = [px, py, px, py, 0.0]
                cur[2], cur[3] = px, py; cur[4] += L / n
            elif cur is not None: runs.append(cur); cur = None
        if cur is not None: runs.append(cur); cur = None
    print(X, 'coupled %.2f uncoupled %.2f' % (cp, un))
    for r in runs:
        if r[4] > 0.2: print('   uncoupled %.2f mm from (%.2f,%.2f) to (%.2f,%.2f)' % (r[4], r[0], r[1], r[2], r[3]))
