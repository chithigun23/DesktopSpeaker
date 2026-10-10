"""route_p2_lib.py : raster multi-layer router for pcbnew (run in flatpak python). Grid G mm, layers F.Cu/In2.Cu/B.Cu."""
import sys, json, math, fnmatch, ctypes, collections
import numpy as np
import pcbnew
G = 0.05
MM = 1e6
LAYS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
ALL4 = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
lib = ctypes.CDLL('/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/route_p2_astar.so')
lib.astar.restype = ctypes.c_int
P = ctypes.c_void_p

class Ctx:
    def __init__(self, pcb, pro):
        self.b = pcbnew.LoadBoard(pcb)
        self.pcb = pcb
        d = json.load(open(pro))
        self.pats = d['net_settings']['netclass_patterns']
        bb = self.b.GetBoardEdgesBoundingBox()
        self.x0 = bb.GetLeft() / MM - 1; self.y0 = bb.GetTop() / MM - 1
        self.W = int((bb.GetRight() / MM + 1 - self.x0) / G) + 2
        self.H = int((bb.GetBottom() / MM + 1 - self.y0) / G) + 2
        self.netid = {}; self.netname = {}
        for i, n in enumerate(sorted(str(k) for k in self.b.GetNetsByName().keys())):
            self.netid[n] = i + 1; self.netname[i + 1] = n
        self.cls = {n: self.netclass(n) for n in self.netid}
        # label rasters per layer: pad, trk (normal), tka (AUDIO 0.5), tki (I2S/USB 0.4), edge
        sh = (self.H, self.W)
        self.R = {k: [np.zeros(sh, np.int16) for _ in LAYS] for k in ('pad', 'trk', 'tka', 'tki', 'tkg', 'tkh', 'tkp')}
        self.edge = np.zeros(sh, bool)
        self.build()
    def netclass(self, n):
        for p in self.pats:
            if fnmatch.fnmatchcase(n, p['pattern']): return p['netclass']
        return 'SIGNAL'
    # ---- geometry
    def cx(self, mm): return (mm - self.x0) / G
    def cy(self, mm): return (mm - self.y0) / G
    def poly_fill(self, arr, pts, val, grow=0.0):
        """even-odd fill of polygons list-of-rings (mm) into arr"""
        xs = [p[0] for r in pts for p in r]; ys = [p[1] for r in pts for p in r]
        gx0 = max(int(self.cx(min(xs) - grow)) - 1, 0); gx1 = min(int(self.cx(max(xs) + grow)) + 2, self.W)
        gy0 = max(int(self.cy(min(ys) - grow)) - 1, 0); gy1 = min(int(self.cy(max(ys) + grow)) + 2, self.H)
        if gx1 <= gx0 or gy1 <= gy0: return
        X = (np.arange(gx0, gx1) * G + self.x0)[None, :]; Y = (np.arange(gy0, gy1) * G + self.y0)[:, None]
        inside = np.zeros((gy1 - gy0, gx1 - gx0), bool)
        for ring in pts:
            n = len(ring)
            for i in range(n):
                xa, ya = ring[i]; xb, yb = ring[(i + 1) % n]
                if ya == yb: continue
                cond = ((ya > Y) != (yb > Y))
                xi = xa + (Y - ya) * (xb - xa) / (yb - ya)
                inside ^= (cond & (X < xi))
        sub = arr[gy0:gy1, gx0:gx1]; sub[inside] = val
        return (gy0, gy1, gx0, gx1, inside)
    def seg_fill(self, arr, a, b, w, val):
        r = w / 2
        gx0 = max(int(self.cx(min(a[0], b[0]) - r)) - 1, 0); gx1 = min(int(self.cx(max(a[0], b[0]) + r)) + 2, self.W)
        gy0 = max(int(self.cy(min(a[1], b[1]) - r)) - 1, 0); gy1 = min(int(self.cy(max(a[1], b[1]) + r)) + 2, self.H)
        X = (np.arange(gx0, gx1) * G + self.x0)[None, :]; Y = (np.arange(gy0, gy1) * G + self.y0)[:, None]
        dx = b[0] - a[0]; dy = b[1] - a[1]; L2 = dx * dx + dy * dy
        t = ((X - a[0]) * dx + (Y - a[1]) * dy) / L2 if L2 > 0 else np.zeros_like(X * Y)
        t = np.clip(t, 0, 1)
        d2 = (X - (a[0] + t * dx)) ** 2 + (Y - (a[1] + t * dy)) ** 2
        m = d2 <= r * r
        sub = arr[gy0:gy1, gx0:gx1]; sub[m] = val
        return (gy0, gy1, gx0, gx1, m)
    def circ_fill(self, arr, c, r, val): return self.seg_fill(arr, c, c, 2 * r, val)
    def pad_poly(self, p, L):
        ps = p.GetEffectivePolygon(L)
        out = []
        for i in range(ps.OutlineCount()):
            o = ps.Outline(i); out.append([(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())])
        return out
    def zone_polys(self, z, L):
        fp = z.GetFilledPolysList(L); res = []
        for i in range(fp.OutlineCount()):
            rings = []; o = fp.Outline(i); rings.append([(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())])
            for h in range(fp.HoleCount(i)):
                o = fp.Hole(i, h); rings.append([(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())])
            res.append(rings)
        return res
    def grp_of(self, cls):
        return 'tkh' if cls == 'POWER_HI' else ('tkp' if cls in ('PVDD', 'SPK_OUT', 'SWITCH') else 'tka' if cls == 'AUDIO' else ('tki' if cls in ('I2S_CLK', 'USB') else ('tkg' if cls == 'GND' else 'trk')))
    def add_pad(self, p, nid=None):
        n = str(p.GetNetname()); i = self.netid.get(n, 0)
        for li, L in enumerate(LAYS):
            if p.IsOnLayer(L):
                for ring in self.pad_poly(p, L):
                    if len(ring) >= 3: self.poly_fill(self.R['pad'][li], [ring], i if i else 30000)
        if p.GetDrillSizeX() > 0 and p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            c = (p.GetX() / MM, p.GetY() / MM)
            for li in range(3): self.circ_fill(self.R['pad'][li], c, p.GetDrillSizeX() / MM / 2 + 0.2, 30000)
    def add_track(self, t):
        n = str(t.GetNetname()); i = self.netid.get(n, 30000); g = self.grp_of(self.cls.get(n, 'SIGNAL'))
        if t.GetClass() == 'PCB_VIA':
            c = (t.GetPosition().x / MM, t.GetPosition().y / MM); r = t.GetWidth(pcbnew.F_Cu) / MM / 2
            for li in range(3): self.circ_fill(self.R[g][li], c, r, i)
        elif t.GetLayer() in LAYS:
            li = LAYS.index(t.GetLayer())
            self.seg_fill(self.R[g][li], (t.GetStart().x / MM, t.GetStart().y / MM), (t.GetEnd().x / MM, t.GetEnd().y / MM), t.GetWidth() / MM, i)
    def build(self):
        b = self.b
        for f in b.GetFootprints():
            for p in f.Pads(): self.add_pad(p)
        for t in b.Tracks(): self.add_track(t)
        for f in b.GetFootprints():
            for z in f.Zones():
                if z.GetIsRuleArea() and (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias()):
                    o = z.Outline().Outline(0); ring = [(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())]
                    self.poly_fill(self.edge, [ring], True, 0.3)
        for z in b.Zones():
            if z.GetIsRuleArea():
                if z.GetZoneName() == 'BM83_ANTENNA_KEEPOUT':
                    o = z.Outline().Outline(0); ring = [(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())]
                    self.poly_fill(self.edge, [ring], True)
                elif z.GetDoNotAllowTracks() or z.GetDoNotAllowVias():
                    o = z.Outline().Outline(0); ring = [(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())]
                    self.poly_fill(self.edge, [ring], True)
                continue
            n = str(z.GetNetname())
            if n == 'GND' or n == '': continue
            pass  # foreign pours are re-cut by the refill: not obstacles
        # board outline: mark outside
        ps = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ps, True)
        ring = [(ps.Outline(0).CPoint(k).x / MM, ps.Outline(0).CPoint(k).y / MM) for k in range(ps.Outline(0).PointCount())]
        inside = np.zeros((self.H, self.W), bool)
        self.poly_fill(inside, [ring], True)
        self.edge |= ~inside
        # 'edge' must be dilated by the edge clearance; keep the boundary band only: use as obstacle label as is
    # ---- dilation
    @staticmethod
    def dilate(m, R):
        """disk dilation radius R (cells, float) of bool array m"""
        if R < 0.5: return m.copy()
        Ri = int(math.floor(R)); out = np.zeros_like(m)
        cs = np.cumsum(m, axis=1, dtype=np.int32)
        cs = np.concatenate([np.zeros((m.shape[0], 1), np.int32), cs], axis=1)  # cs[:,k]=sum m[:, :k]
        Wd = m.shape[1]; hcache = {}
        x = np.arange(Wd)
        for dy in range(-Ri, Ri + 1):
            half = int(math.floor(math.sqrt(R * R - dy * dy)))
            if half not in hcache:
                hi = np.minimum(x + half + 1, Wd); lo = np.maximum(x - half, 0)
                hcache[half] = (cs[:, hi] - cs[:, lo]) > 0
            hm = hcache[half]
            if dy >= 0: out[dy:] |= hm[:m.shape[0] - dy] if dy else hm
            else: out[:dy] |= hm[-dy:]
        return out
    def obstacle(self, me, li, y0, y1, x0, x1, w, cme, cpad=0.2, extra=0.0, rip=None, gndc=0.2):
        """bool blocked map (window) for a track of width w on layer li for net id me"""
        s = (slice(y0, y1), slice(x0, x1)); m = getattr(self, 'MARGIN', 0.04)
        blocked = np.zeros((y1 - y0, x1 - x0), bool)
        def grp(name, c):
            a = self.R[name][li][s]
            mk = (a != 0) & (a != me)
            if rip and name != 'pad': mk &= ~np.isin(a, list(rip))
            return self.dilate(mk, (w / 2 + c + m) / G)
        blocked |= grp('pad', cpad)
        blocked |= grp('trk', cme)
        blocked |= grp('tka', max(cme, 0.5))
        blocked |= grp('tki', max(cme, 0.4))
        blocked |= grp('tkg', gndc)
        blocked |= grp('tkh', max(cme, 0.4))
        blocked |= grp('tkp', max(cme, 0.3))
        blocked |= self.dilate(self.edge[s], (w / 2 + 0.5 + m) / G)
        return blocked
    def via_obstacle(self, me, y0, y1, x0, x1, dv, cme, rip=None, gndc=0.2):
        blocked = np.zeros((y1 - y0, x1 - x0), bool)
        for li in range(3): blocked |= self.obstacle(me, li, y0, y1, x0, x1, dv, cme, cpad=0.26, rip=rip, gndc=gndc)
        return blocked
    def ripmask(self, me, li, y0, y1, x0, x1, w, c, rip):
        s = (slice(y0, y1), slice(x0, x1)); pen = np.zeros((y1 - y0, x1 - x0), np.uint8)
        byp = {}
        for nid, pv in rip.items(): byp.setdefault(pv, []).append(nid)
        for pv in sorted(byp):
            mk = np.zeros(pen.shape, bool)
            for name in ('trk', 'tka', 'tki', 'tkg', 'tkh', 'tkp'): mk |= np.isin(self.R[name][li][s], byp[pv])
            if mk.any(): pen[self.dilate(mk, (w / 2 + c) / G)] = pv
        return pen
    def rebuild(self):
        for k in self.R:
            for a in self.R[k]: a[:] = 0
        self.edge[:] = False
        self.build()
