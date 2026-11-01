#!/usr/bin/env python3
"""route_oct.py : exact-octilinear staged A* router for the DesktopSpeaker board (headless, works on a COPY of a board).

Usage (venv python with numpy + shapely; the C core is compiled into --workdir on first use):
  route_oct.py --board IN.kicad_pcb --geo IN.geo.json --nets NETS.txt --stage S1 --out OUT.kicad_pcb \
               --manifest MANIFEST.json [--log LOG.json] [--via-cost 25] [--turn-cost 2] [--bcu-cost 1.6] ...
  IN.geo.json comes from route_oct_export.py (KiCad python) run on IN.kicad_pcb (zones refilled).
  NETS.txt lines:  STAGE NETNAME [key=value ...]   e.g.  'S1 /USB_DN pair=/USB_DP bcu=gnd'
     keys: pair=<net routed earlier, DN hugs it at the diff-pair gap>, bcu=no|gnd|yes (B.Cu use), width=<mm>
  Stages are routed one per call in file order of their nets; earlier stages must already be in IN (locked, hash checked).

Geometry guarantees (by construction, re-measured by route_oct_check.py):
  * every routed cell is a node of the global 0.05 mm lattice and moves are the 8 lattice directions, so all
    segments are exactly 0/45/90 degrees; pad stubs are computed in integer nanometres and are exactly axial or 45 degrees
  * only 45-degree bends; the segment between two bends is >= max(0.4 mm, 3 x width) (forced run after each turn)
  * every pad is left along its axis for at least 0.3 mm beyond the pad edge (stub), fine-pitch IC pads only outward
  * no T-junction except at a pad stub; post-pass merges colinear segments and never shortcuts
Rules: clearances from route_oct_rules.py (transcription of the frozen .kicad_dru, SHA-256 checked), edge 0.5 mm,
keep-outs (antenna, BKO_* on B.Cu, J7 no-via), no In1/In2 routing, SP1 halo 0.6 mm for I2S_CLK and USB classes.
"""
import sys, os, json, math, time, argparse, hashlib, uuid, ctypes, itertools, collections, re, subprocess
import numpy as np
import shapely
from shapely.geometry import Polygon, MultiPolygon, LineString, Point, box
from shapely.ops import unary_union
from shapely.prepared import prep

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import route_oct_rules as RU
import route_oct_lock as LK

G = 0.05              # lattice pitch mm
GN = 50000            # lattice pitch nm
M = 0.04              # sweep margin (>= half diagonal cell 0.0354)
TOL = 2.5e-4          # exact checks: pad polygons are exported 0.2 um outside the true shape; KiCad accepts equality
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
RL = ['F.Cu', 'B.Cu']                    # routing layers
ALLCU = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
SENSITIVE_CLS = {'USB', 'I2S_CLK', 'AUDIO'}
SENSITIVE_NETS = {'/AUD_SDA', '/AUD_SCL'}
SPACE = {'I2S_CLK': 0.6, 'USB': 0.6}   # SP1 edge gap to other signal tracks (halo), applied outside neck areas
FORBID_ISLAND_CLS = {'POWER_HI', 'PVDD', 'SPK_OUT'}
VIA_D, VIA_DR = 0.6, 0.3


def dang(a, b):
    d = abs(a - b) % 8
    return min(d, 8 - d)


# ---------------------------------------------------------------- C core
def load_core(workdir):
    src = os.path.join(HERE, 'route_oct_core.c'); so = os.path.join(workdir, 'route_oct_core.so')
    if not os.path.exists(so) or os.path.getmtime(so) < os.path.getmtime(src):
        subprocess.check_call(['gcc', '-O2', '-shared', '-fPIC', '-o', so, src, '-lm'])
    L = ctypes.CDLL(so)
    P = ctypes.c_void_p
    L.oct_astar.restype = ctypes.c_int
    L.oct_astar.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, P, P, P, P, P, ctypes.c_int, P, P, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                            ctypes.c_float, ctypes.c_float, ctypes.c_float, P, ctypes.c_int64, P, ctypes.c_int, P]
    L.fill_poly.restype = None
    L.fill_poly.argtypes = [P, ctypes.c_int, ctypes.c_int, P, P, ctypes.c_int, ctypes.c_uint8]
    return L


def ptr(a):
    return a.ctypes.data_as(ctypes.c_void_p)


# ---------------------------------------------------------------- geometry helpers
def mkpolys(plist):
    out = []
    for rings in plist:
        if len(rings[0]) < 3:
            continue
        p = Polygon(rings[0], [h for h in rings[1:] if len(h) >= 3])
        if not p.is_valid:
            p = p.buffer(0)
        if not p.is_empty:
            out.append(p)
    if not out:
        return None
    return out[0] if len(out) == 1 else unary_union(out)


def geom_rings(g):
    """shapely (Multi)Polygon -> list of (xy float64 Nx2 array, ring_start int32 array)"""
    out = []
    if g is None or g.is_empty:
        return out
    parts = [g] if g.geom_type == 'Polygon' else [p for p in getattr(g, 'geoms', []) if p.geom_type == 'Polygon']
    for p in parts:
        rings = [np.asarray(p.exterior.coords)[:-1]] + [np.asarray(r.coords)[:-1] for r in p.interiors]
        rings = [r for r in rings if len(r) >= 3]
        if not rings:
            continue
        rs = np.zeros(len(rings) + 1, np.int32)
        for i, r in enumerate(rings):
            rs[i + 1] = rs[i] + len(r)
        out.append((np.ascontiguousarray(np.vstack(rings), dtype=np.float64), rs))
    return out


class Item:
    __slots__ = ('id', 'kind', 'typ', 'net', 'cls', 'layer', 'geom', 'bounds', 'smd', 'dyn', 'sig', 'owner', 'w')

    def __init__(self, id, kind, typ, net, cls, layer, geom, smd=False, dyn=False, sig=False, owner=None, w=0.0):
        self.id = id; self.kind = kind; self.typ = typ; self.net = net; self.cls = cls; self.layer = layer; self.geom = geom
        self.bounds = geom.bounds; self.smd = smd; self.dyn = dyn; self.sig = sig; self.owner = owner; self.w = w


class Index:
    """bucket spatial index per layer, supports insert/remove"""

    def __init__(self, cell=2.0):
        self.c = cell; self.b = collections.defaultdict(set); self.items = {}

    def _keys(self, bd):
        c = self.c
        for i in range(int(math.floor(bd[0] / c)), int(math.floor(bd[2] / c)) + 1):
            for j in range(int(math.floor(bd[1] / c)), int(math.floor(bd[3] / c)) + 1):
                yield (i, j)

    def add(self, it):
        self.items[it.id] = it
        for k in self._keys(it.bounds):
            self.b[k].add(it.id)

    def remove(self, it):
        self.items.pop(it.id, None)
        for k in self._keys(it.bounds):
            self.b[k].discard(it.id)

    def query(self, bd):
        s = set()
        for k in self._keys(bd):
            s |= self.b.get(k, set())
        return [self.items[i] for i in s if i in self.items and self.items[i].bounds[0] <= bd[2] and self.items[i].bounds[2] >= bd[0]
                and self.items[i].bounds[1] <= bd[3] and self.items[i].bounds[3] >= bd[1]]


# ---------------------------------------------------------------- board model
class Board:
    def __init__(self, geo, dru, pro, core):
        self.L = core
        D = json.load(open(geo))
        ok, h = RU.check_dru(dru)
        if not ok:
            raise SystemExit('route_oct: rule file %s hash %s differs from the transcribed rules; refusing to route' % (dru, h))
        self.pro = json.load(open(pro))
        self.cls_w = {c['name']: c['track_width'] for c in self.pro['net_settings']['classes']}
        self.netcls = D['netclass']
        self.idx = {l: Index() for l in ALLCU}
        self.nid = 0
        self.pads = []
        ol = mkpolys(D['outline'])
        self.outline = ol
        self.outline_b = ol.boundary
        self.edge_cache = {}
        cy_refs, neck_areas = RU.neck_targets(dru)
        neck = []
        for ref in cy_refs:
            c = D['courtyard'].get(ref)
            if c:
                for side in ('F', 'B'):
                    if side in c['poly']:
                        g = mkpolys(c['poly'][side])
                        if g is not None:
                            neck.append(g)
        self.keepouts = []
        for a in D['areas']:
            g = mkpolys(a['outline'])
            if g is None:
                continue
            if a['name'] in neck_areas:
                neck.append(g)
            self.keepouts.append(dict(name=a['name'] or ('fp:' + a['ref']), layers=a['layers'], no_tracks=a['no_tracks'], no_vias=a['no_vias'], geom=g))
        self.neck = unary_union(neck) if neck else Polygon()
        self.neck_p = prep(self.neck)
        # pads
        for p in D['pads']:
            for l, pl in p['poly'].items():
                g = mkpolys(pl)
                if g is None:
                    continue
                self._add(Item(self._id(), 'pad', 'Pad', p['net'], p['cls'] if p['net'] else '', l, g, smd=p['attr'] in ('SMD', 'CONN')))
            if p['drill'] and p['drill'][0] > 0:
                r = max(p['drill']) / 2.0
                g = Point(p['x'], p['y']).buffer(r, 16)
                for l in ALLCU:
                    self._add(Item(self._id(), 'hole', 'NPTH' if p['attr'] == 'NPTH' else 'Hole', p['net'] if p['attr'] != 'NPTH' else '', '', l, g))
            fpc = D['courtyard'].get(p['ref'], {})
            self.pads.append(dict(p, fpx=fpc.get('x', p['x']), fpy=fpc.get('y', p['y']), fpn=fpc.get('npads', 0)))
        for t in D['tracks']:
            if t['arc'] and t['poly']:
                g = mkpolys(t['poly'])
            else:
                g = LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]).buffer(t['w'] / 2, 16) if (t['x1'], t['y1']) != (t['x2'], t['y2']) else Point(t['x1'], t['y1']).buffer(t['w'] / 2, 16)
            if g is None:
                continue
            self._add(Item(self._id(), 'track', 'Track', t['net'], t['cls'], t['layer'], g, sig=(t['net'] != 'GND' and t['w'] <= 0.35), w=t['w']))
        for v in D['vias']:
            g = Point(v['x'], v['y']).buffer(v['d'] / 2, 16); gh = Point(v['x'], v['y']).buffer(v['drill'] / 2, 16)
            for l in ALLCU:
                self._add(Item(self._id(), 'via', 'Via', v['net'], v['cls'], l, g))
                self._add(Item(self._id(), 'hole', 'Hole', v['net'], v['cls'], l, gh))
        self.zfill = collections.defaultdict(list)   # (layer) -> [(net, cls, geom)]
        for z in D['zones']:
            for l, pl in z['fills'].items():
                g = mkpolys(pl)
                if g is None:
                    continue
                self.zfill[l].append((z['net'], z['cls'], g, z['teardrop']))
                if z['net'] == 'GND' and not z['teardrop']:
                    continue          # GND pours yield to new copper on refill
                self._add(Item(self._id(), 'zone', 'Zone', z['net'], z['cls'], l, g))
        # global lattice
        bx = ol.bounds
        self.gx0 = int(math.floor(bx[0] / G)) - 2; self.gy0 = int(math.floor(bx[1] / G)) - 2
        self.GW = int(math.ceil(bx[2] / G)) + 3 - self.gx0; self.GH = int(math.ceil(bx[3] / G)) + 3 - self.gy0
        t0 = time.time()
        self.R_neck = self.raster_full([self.neck])
        self.R_in1g = self.raster_full([g for n, c, g, td in self.zfill['In1.Cu'] if n == 'GND'])
        self.R_in2g = self.raster_full([g for n, c, g, td in self.zfill['In2.Cu'] if n == 'GND'])
        self.R_in2o = self.raster_full([g for n, c, g, td in self.zfill['In2.Cu'] if n != 'GND'])
        self.R_in2f = self.raster_full([g for n, c, g, td in self.zfill['In2.Cu'] if c in FORBID_ISLAND_CLS])
        self.buf_cache = {}
        print('board model: %d items, lattice %dx%d, rasters %.1fs' % (self.nid, self.GW, self.GH, time.time() - t0), flush=True)

    def _id(self):
        self.nid += 1
        return self.nid

    def _add(self, it):
        self.idx[it.layer].add(it)

    def raster_full(self, geoms):
        R = np.zeros((self.GH, self.GW), np.uint8)
        for g in geoms:
            self.fill(R, g, self.gx0, self.gy0, 1)
        return R

    def fill(self, R, g, x0i, y0i, val, off=(0.0, 0.0)):
        H, W = R.shape
        for xy, rs in geom_rings(g):
            c = np.empty_like(xy); c[:, 0] = (xy[:, 0] - off[0]) / G - x0i; c[:, 1] = (xy[:, 1] - off[1]) / G - y0i
            if c[:, 0].max() < -1 or c[:, 0].min() > W + 1 or c[:, 1].max() < -1 or c[:, 1].min() > H + 1:
                continue
            c = np.ascontiguousarray(c)
            self.L.fill_poly(ptr(R), W, H, ptr(c), ptr(rs), len(rs) - 1, val)

    def buffered(self, it, r):
        k = (it.id, round(r, 4))
        g = self.buf_cache.get(k)
        if g is None:
            g = it.geom.buffer(r, 8)
            self.buf_cache[k] = g
        return g

    def edge_inner(self, r):
        k = round(r, 4)
        if k not in self.edge_cache:
            self.edge_cache[k] = self.outline.buffer(-r, 8)
        return self.edge_cache[k]


# ---------------------------------------------------------------- router
class Router:
    def __init__(self, B, args, netopts):
        self.B = B; self.a = args; self.opts = netopts
        self.out_segs = []; self.out_vias = []
        self.log = []
        self.reserved = collections.defaultdict(list)   # pad key -> items
        self.used = {}      # pad key -> list of dict(node, layer, sdir, arrive)
        self.netcopper = collections.defaultdict(list)  # net -> dynamic items
        self.pending = set()                             # nets of this and later stages not yet routed
        self.off = (0, 0)                                # lattice origin (nm) of the current connection
        self.soft = set()                                # nets treated as passable-with-penalty (conflict search)
        self.recs = {}
        self.rrr_log = []

    # ---- per net profile
    def prof(self, net):
        cls = self.B.netcls.get(net, 'Default')
        o = self.opts.get(net, {})
        w = float(o.get('width', self.B.cls_w.get(cls, 0.25)))
        sens = cls in SENSITIVE_CLS or net in SENSITIVE_NETS
        bcu = o.get('bcu', 'no' if sens else 'yes')
        Lmm = max(0.4, 3 * w)
        return dict(net=net, cls=cls, w=w, sens=sens, bcu=bcu, space=SPACE.get(cls), pair=o.get('pair'),
                    Lo=int(math.ceil(Lmm / G - 1e-9)), Ld=int(math.ceil(Lmm / (G * math.sqrt(2)) - 1e-9)))

    # ---- exact checks
    def seg_ok(self, pts, w, layer, pf, mode='intersects'):
        """exact clearance check of a polyline of width w on layer against all foreign copper (DRC semantics for the neck areas)"""
        B = self.B
        line = LineString(pts) if len(pts) > 1 and pts[0] != pts[-1] else Point(pts[0])
        inneck = B.neck.intersects(line) if mode == 'intersects' else B.neck_p.contains(line)
        bd = line.bounds; R = 2.6
        for it in B.idx[layer].query((bd[0] - R, bd[1] - R, bd[2] + R, bd[3] + R)):
            if it.net == pf['net'] and it.net:
                continue
            if it.net == 'GND' and it.kind == 'zone':
                continue
            if it.dyn and it.net in self.soft:
                continue
            if it.kind == 'hole':
                c = RU.EDGE if it.typ == 'NPTH' else RU.HOLE_CLR
            else:
                c = (RU.clr_neck if inneck else RU.clr_strict)(pf['cls'], pf['net'], it.cls, it.typ)
            if line.distance(it.geom) < c + w / 2 - TOL:
                return False, it
        if B.outline_b.distance(line) < RU.EDGE + w / 2 + 1e-3 or not B.outline.contains(line):
            return False, 'edge'
        for k in B.keepouts:
            if layer not in k['layers']:
                continue
            bko = k['name'].startswith('BKO_') and layer == 'B.Cu' and RU.bko_applies(pf['cls'], pf['net'])
            if (k['no_tracks'] or bko) and k['geom'].distance(line) < w / 2 + 1e-3:
                return False, 'keepout ' + k['name']
        return True, None

    def via_ok_exact(self, x, y, pf):
        B = self.B; p = Point(x, y); r = VIA_D / 2
        for l in ALLCU:
            for it in B.idx[l].query((x - 2.6, y - 2.6, x + 2.6, y + 2.6)):
                if it.kind == 'zone' and it.net == 'GND':
                    continue
                if it.dyn and it.net in self.soft:
                    continue
                if it.kind == 'hole':
                    need = max(RU.HOLE_HOLE + VIA_DR / 2, (RU.EDGE if it.typ == 'NPTH' else RU.HOLE_CLR) + r)
                    if it.net == pf['net']:
                        need = RU.HOLE_HOLE + VIA_DR / 2
                elif it.kind == 'pad' and it.smd:
                    need = r + max(0.25, RU.clr_strict(pf['cls'], pf['net'], it.cls, it.typ) if it.net != pf['net'] else 0.25)
                elif it.net == pf['net']:
                    continue
                else:
                    need = r + RU.clr_strict(pf['cls'], pf['net'], it.cls, it.typ)
                if p.distance(it.geom) < need - TOL:
                    return False
        if B.outline_b.distance(p) < RU.EDGE + r + 1e-3:
            return False
        for k in B.keepouts:
            bko = k['name'].startswith('BKO_') and RU.bko_applies(pf['cls'], pf['net'])
            if (k['no_vias'] or bko or (k['no_tracks'] and k['name'] == 'BM83_ANTENNA_KEEPOUT')) and k['geom'].distance(p) < r + 1e-3:
                return False
        return True

    # ---- pad exits
    def pad_key(self, p):
        return (p['ref'], p['num'])

    def exits(self, pad, pf):
        """candidate exits of a pad: list of dict(layer, pts_nm, width, node(ix,iy), sdir, arr(list of (dir, bits)), cost)"""
        out = []
        P = (int(round(pad['x'] * 1e6)), int(round(pad['y'] * 1e6)))
        layers = [l for l in RL if l in pad['poly'] and (l == 'F.Cu' or pf['bcu'] != 'no')]
        # pad extents per layer from its polygon
        for l in layers:
            dirs, ext, bd = self.pad_dirs(pad, l)
            single = len(dirs) == 1
            for d in dirs:
                ux, uy = DIRS[d]
                F0 = int(round((ext[d] + 0.3) * 1e6))
                for var in ('A', 'B+', 'B-'):
                    e = self._mk_exit(P, d, F0, var, pf, nodog=self.pad_key(pad) in self.used)
                    if e is None:
                        continue
                    pts_mm = [(x / 1e6, y / 1e6) for x, y in e['pts']]
                    okw = None
                    for w in ([pf['w']] + ([RU.NECK_W] if pf['w'] > RU.NECK_W + 1e-9 else [])):
                        if w < pf['w'] and not self.B.neck_p.contains(LineString(pts_mm)) and not any(
                                k['name'] in RU.WIDTH_AREAS and pf['cls'] in RU.WIDTH_AREAS[k['name']] and k['geom'].contains(LineString(pts_mm)) for k in self.B.keepouts):
                            continue
                        ok, why = self.seg_ok(pts_mm, w, l, pf, mode='contains')
                        if ok:
                            okw = w; break
                    if okw is None:
                        continue
                    e.update(layer=l, width=okw, pad=pad, single=single, d=d,
                             cost=sum(math.hypot(pts_mm[i + 1][0] - pts_mm[i][0], pts_mm[i + 1][1] - pts_mm[i][1]) for i in range(len(pts_mm) - 1)) / G + (0 if var == 'A' else 3) + (0 if okw == pf['w'] else 2))
                    out.append(e)
        return out

    def pad_dirs(self, pad, l):
        """allowed exit directions of a pad on layer l (fine-pitch IC pads: outward along the long axis only), pad extents, bounds"""
        k = (pad['ref'], pad['num'], l)
        if not hasattr(self, '_pdc'):
            self._pdc = {}
        if k in self._pdc:
            return self._pdc[k]
        g = mkpolys(pad['poly'][l]); bd = g.bounds
        ext = {0: bd[2] - pad['x'], 4: pad['x'] - bd[0], 2: bd[3] - pad['y'], 6: pad['y'] - bd[1]}
        wx, wy = bd[2] - bd[0], bd[3] - bd[1]
        asp = max(wx, wy) / max(1e-6, min(wx, wy))
        dirs = [0, 2, 4, 6]
        if asp >= 1.3 and pad['fpn'] >= 3:
            ax = 0 if wx > wy else 2
            off = (pad['x'] - pad['fpx']) if ax == 0 else (pad['y'] - pad['fpy'])
            fine = pad['fpn'] >= 8 and min(wx, wy) <= 0.45      # QFN/QFP/SSOP/connector rows: rule FO1, outward escape only
            dirs = [ax if off > 0 else ax + 4] if (fine and abs(off) > 0.05) else [ax, ax + 4]
        self._pdc[k] = (dirs, ext, bd)
        return self._pdc[k]

    def direct(self, pf, A, B_):
        """rule LE5: two pads that face each other on a common horizontal or vertical line are joined by one straight segment
        (endpoints inside the pads, exact 0/90 degrees); returns (segs, dirA, dirB, layer) or None"""
        kA, kB = self.pad_key(A), self.pad_key(B_)
        usedA = {(u['layer'], u['d']) for u in self.used.get(kA, [])}; usedB = {(u['layer'], u['d']) for u in self.used.get(kB, [])}
        for l in RL:
            if l not in A['poly'] or l not in B_['poly'] or (l == 'B.Cu' and pf['bcu'] == 'no'):
                continue
            dA, eA, bA = self.pad_dirs(A, l); dB, eB, bB = self.pad_dirs(B_, l)
            for horiz in (True, False):
                if horiz:
                    da = 0 if B_['x'] > A['x'] else 4
                    lo, hi = max(bA[1], bB[1]), min(bA[3], bB[3]); ca, cb = A['y'], B_['y']
                else:
                    da = 2 if B_['y'] > A['y'] else 6
                    lo, hi = max(bA[0], bB[0]), min(bA[2], bB[2]); ca, cb = A['x'], B_['x']
                db = (da + 4) % 8
                if da not in dA or db not in dB or (l, da) in usedA or (l, db) in usedB:
                    continue
                cands = [c for c in (ca, cb, (ca + cb) / 2) if lo + 1e-4 <= c <= hi - 1e-4]
                for c in cands:
                    c = round(c, 6)
                    if horiz:
                        pa, pb = (A['x'], c), (B_['x'], c)
                    else:
                        pa, pb = (c, A['y']), (c, B_['y'])
                    for w in [pf['w']] + ([RU.NECK_W] if pf['w'] > RU.NECK_W + 1e-9 and self.B.neck_p.contains(LineString([pa, pb])) else []):
                        if self.seg_ok([pa, pb], w, l, pf)[0]:
                            seg = [l, (int(round(pa[0] * 1e6)), int(round(pa[1] * 1e6))), (int(round(pb[0] * 1e6)), int(round(pb[1] * 1e6))), w]
                            return [seg], da, db, l
        return None

    def _mk_exit(self, P, d, F0, var, pf, nodog=False):
        e = self._mk_exit0((P[0] - self.off[0], P[1] - self.off[1]), d, F0, var, pf, nodog)
        e['pts'] = [(x + self.off[0], y + self.off[1]) for x, y in e['pts']]
        e['off'] = self.off
        return e

    def _mk_exit0(self, P, d, F0, var, pf, nodog=False):
        ux, uy = DIRS[d]; px, py = P
        if var == 'A':
            if ux != 0:      # horizontal exit, lateral = y
                gy = int(round(py / GN)) * GN; b = gy - py
                fx = px + ux * F0
                sx = (-((-fx) // GN) * GN) if ux > 0 else (fx // GN) * GN
                pts = ([(px, gy)] if nodog else [P] + ([(px + ux * abs(b), gy)] if b else [])) + [(sx, gy)]
                node = (sx // GN, gy // GN)
            else:
                gx = int(round(px / GN)) * GN; b = gx - px
                fy = py + uy * F0
                sy = (-((-fy) // GN) * GN) if uy > 0 else (fy // GN) * GN
                pts = ([(gx, py)] if nodog else [P] + ([(gx, py + uy * abs(b))] if b else [])) + [(gx, sy)]
                node = (gx // GN, sy // GN)
            return dict(pts=pts, node=node, sdir=d, arr=self._arrmask((d + 4) % 8), var='A')
        t = 1 if var == 'B+' else -1
        v = (d + t) % 8; vx, vy = DIRS[v]
        Ld = pf['Ld']
        if ux != 0:
            s0 = (-py * vy) % GN
            L0 = (-px * ux - s0) % GN
            L = L0 + max(0, -((-(F0 - L0)) // GN)) * GN
            S1 = (px + ux * L, py)
        else:
            s0 = (-px * vx) % GN
            L0 = (-py * uy - s0) % GN
            L = L0 + max(0, -((-(F0 - L0)) // GN)) * GN
            S1 = (px, py + uy * L)
        k = s0 + Ld * GN
        S2 = (S1[0] + vx * k, S1[1] + vy * k)
        assert S2[0] % GN == 0 and S2[1] % GN == 0, (P, d, var, S2)
        return dict(pts=[P, S1, S2], node=(S2[0] // GN, S2[1] // GN), sdir=v, arr=self._arrmask((v + 4) % 8), var=var)

    @staticmethod
    def _arrmask(a):
        """target arrival bits: straight arrival a (also inside a forced run) and 45-degree arrivals a+-1"""
        return [(a, 1 | 2), ((a + 1) % 8, 1), ((a + 7) % 8, 1)]

    # ---- reservations of pad escapes (fine-pitch pads of nets still to route)
    def reserve(self, nets):
        n = 0
        for net in nets:
            pf = self.prof(net)
            for p in self.B.pads:
                if p['net'] != net:
                    continue
                k = self.pad_key(p)
                if k in self.used or k in self.reserved:
                    continue
                self.off = (int(round(p['x'] * 1e6)) % GN, int(round(p['y'] * 1e6)) % GN)
                ex = self.exits(p, pf)
                if ex and all(e['single'] for e in ex):
                    e = min(ex, key=lambda e: e['cost'])
                    pts = [(x / 1e6, y / 1e6) for x, y in e['pts'][:2 if e['var'] != 'A' else len(e['pts'])]]
                    if e['var'] == 'A':     # keep the forced straight run after the stub free as well
                        dx, dy = DIRS[e['sdir']]; L = pf['Lo'] * G
                        pts.append((pts[-1][0] + dx * L, pts[-1][1] + dy * L))
                    g = LineString(pts).buffer(e['width'] / 2, 8)
                    it = Item(self.B._id(), 'track', 'Track', net, pf['cls'], e['layer'], g, dyn=True, sig=True, owner=k, w=e['width'])
                    self.B._add(it); self.reserved[k].append(it); n += 1
        return n

    def unreserve(self, k):
        for it in self.reserved.pop(k, []):
            self.B.idx[it.layer].remove(it)

    # ---- window rasters
    def window(self, pf, bbox, discs_own, discs_halo):
        B = self.B; w = pf['w']; ox, oy = self.off[0] / 1e6, self.off[1] / 1e6; OFF = (ox, oy)
        x0i = max(B.gx0, int(math.floor((bbox[0] - ox) / G))); y0i = max(B.gy0, int(math.floor((bbox[1] - oy) / G)))
        x1i = min(B.gx0 + B.GW - 2, int(math.ceil((bbox[2] - ox) / G))); y1i = min(B.gy0 + B.GH - 2, int(math.ceil((bbox[3] - oy) / G)))
        W = x1i - x0i + 1; H = y1i - y0i + 1
        wb = (x0i * G + ox, y0i * G + oy, x1i * G + ox, y1i * G + oy)
        sl = (slice(y0i - B.gy0, y0i - B.gy0 + H), slice(x0i - B.gx0, x0i - B.gx0 + W))
        neck = B.R_neck[sl].astype(bool)
        yy, xx = np.mgrid[0:H, 0:W]
        X = (xx + x0i) * G + ox; Y = (yy + y0i) * G + oy

        def discmask(discs):
            m = np.zeros((H, W), bool)
            for (cx, cy, r) in discs:
                a = int(max(0, math.floor((cy - r) / G) - y0i)); b_ = int(min(H, math.ceil((cy + r) / G) - y0i + 1))
                c = int(max(0, math.floor((cx - r) / G) - x0i)); d = int(min(W, math.ceil((cx + r) / G) - x0i + 1))
                if a < b_ and c < d:
                    m[a:b_, c:d] |= (X[a:b_, c:d] - cx) ** 2 + (Y[a:b_, c:d] - cy) ** 2 <= r * r
            return m
        down = discmask(discs_own); dhalo = discmask(discs_halo)
        free = np.zeros((2, H, W), np.uint8); cost = np.ones((2, H, W), np.float32)
        Rq = 2.6
        q = (wb[0] - Rq, wb[1] - Rq, wb[2] + Rq, wb[3] + Rq)
        for li, l in enumerate(RL):
            OB2 = np.zeros((H, W), np.uint8)  # soft keep-away around pads of nets still to route
            OB = np.zeros((H, W), np.uint8)   # bit1 strict, bit2 neck, bit4 halo, bit8 own, bit16 keepout
            for it in B.idx[l].query(q):
                if it.kind == 'zone' and it.net == 'GND':
                    continue
                if it.net == pf['net'] and it.net:
                    if it.dyn and it.kind in ('track', 'via'):
                        B.fill(OB, B.buffered(it, 0.2 + w / 2 + M), x0i, y0i, 8, OFF)
                    continue
                if it.kind == 'pad' and it.net in self.pending and it.net != pf['net'] and self.a.pad_pen > 0:
                    B.fill(OB2, B.buffered(it, self.a.pad_halo + w / 2), x0i, y0i, 1, OFF)
                if it.dyn and it.net in self.soft:
                    if it.kind != 'hole':
                        B.fill(OB, B.buffered(it, RU.clr_strict(pf['cls'], pf['net'], it.cls, it.typ) + w / 2 + M), x0i, y0i, 32, OFF)
                    continue
                if it.kind == 'hole':
                    r = (RU.EDGE if it.typ == 'NPTH' else RU.HOLE_CLR) + w / 2 + M
                    B.fill(OB, B.buffered(it, r), x0i, y0i, 3, OFF)
                    continue
                cs = RU.clr_strict(pf['cls'], pf['net'], it.cls, it.typ); cn = RU.clr_neck(pf['cls'], pf['net'], it.cls, it.typ)
                if abs(cs - cn) < 1e-9:
                    B.fill(OB, B.buffered(it, cs + w / 2 + M), x0i, y0i, 3, OFF)
                else:
                    B.fill(OB, B.buffered(it, cs + w / 2 + M), x0i, y0i, 1, OFF)
                    B.fill(OB, B.buffered(it, cn + w / 2 + M), x0i, y0i, 2, OFF)
                if it.kind == 'track' and it.sig and it.net != pf['pair'] and (pf['space'] or SPACE.get(it.cls)):
                    sp = max(pf['space'] or 0, SPACE.get(it.cls) or 0)
                    B.fill(OB, B.buffered(it, sp + w / 2 + M), x0i, y0i, 4, OFF)
            for k in B.keepouts:
                if l not in k['layers']:
                    continue
                bko = k['name'].startswith('BKO_') and l == 'B.Cu' and RU.bko_applies(pf['cls'], pf['net'])
                if k['no_tracks'] or bko:
                    B.fill(OB, k['geom'].buffer(w / 2 + M, 8), x0i, y0i, 16, OFF)
            inner = np.zeros((H, W), np.uint8)
            B.fill(inner, B.edge_inner(RU.EDGE + w / 2 + M), x0i, y0i, 1, OFF)
            blocked = ((OB & 1).astype(bool) & ~neck) | ((OB & 2).astype(bool) & neck) | ((OB & 4).astype(bool) & ~neck & ~dhalo) \
                | ((OB & 8).astype(bool) & ~down) | (OB & 16).astype(bool) | ~inner.astype(bool)
            fr = ~blocked
            if l == 'F.Cu':
                cost[li] = 1.0 + self.a.f_void * (1 - B.R_in1g[sl])
            else:
                g2 = B.R_in2g[sl].astype(bool); o2 = B.R_in2o[sl].astype(bool) & ~g2
                cost[li] = self.a.bcu_cost * np.where(g2, 1.0, np.where(o2, self.a.b_island, self.a.b_void))
                fr &= ~B.R_in2f[sl].astype(bool) | g2
                if pf['bcu'] == 'no':
                    fr[:] = False
                elif pf['bcu'] == 'gnd':
                    fr &= g2
            free[li] = fr
            if self.a.pad_pen > 0:
                cost[li][OB2.astype(bool)] += self.a.pad_pen
            if self.soft:
                cost[li][(OB & 32).astype(bool)] += self.a.soft_pen
        # attraction to the pair partner
        hmin = 1.0
        if pf['pair'] and self.netcopper.get(pf['pair']):
            for li, l in enumerate(RL):
                A = np.zeros((H, W), np.uint8)
                for it in self.netcopper[pf['pair']]:
                    if it.layer != l or it.kind != 'track':
                        continue
                    B.fill(A, it.geom.buffer(0.15 + w / 2 + 0.095, 8), x0i, y0i, 1, OFF)
                    B.fill(A, it.geom.buffer(0.15 + w / 2 + M - 1e-3, 8), x0i, y0i, 2, OFF)
                band = (A == 1)
                E = np.zeros((H, W), np.uint8)
                for it in self.netcopper[pf['pair']]:
                    if it.layer == l and it.kind == 'track':
                        B.fill(E, it.geom.buffer(0.15 + w / 2 + 0.55, 8), x0i, y0i, 1, OFF)
                cost[li][(E == 1) & (A == 0)] *= self.a.pair_avoid   # near-parallel outside the 0.15-0.25 mm gap band
                cost[li][band] *= self.a.pair_attract
            hmin = self.a.pair_attract
        # via sites
        viaok = np.zeros((H, W), np.uint8)
        if pf['bcu'] != 'no':
            VB = np.zeros((H, W), np.uint8); r = VIA_D / 2
            for l in ALLCU:
                for it in B.idx[l].query(q):
                    if it.kind == 'zone' and it.net == 'GND':
                        continue
                    if it.dyn and it.net in self.soft:
                        continue
                    if it.kind == 'hole':
                        need = RU.HOLE_HOLE + VIA_DR / 2 if it.net == pf['net'] else max(RU.HOLE_HOLE + VIA_DR / 2, (RU.EDGE if it.typ == 'NPTH' else RU.HOLE_CLR) + r)
                    elif it.kind == 'pad' and it.smd:
                        need = r + (0.25 if it.net == pf['net'] else max(0.25, RU.clr_strict(pf['cls'], pf['net'], it.cls, it.typ)))
                    elif it.net == pf['net']:
                        continue
                    else:
                        need = r + RU.clr_strict(pf['cls'], pf['net'], it.cls, it.typ)
                    B.fill(VB, B.buffered(it, need + 0.005), x0i, y0i, 1, OFF)
            for k in B.keepouts:
                bko = k['name'].startswith('BKO_') and RU.bko_applies(pf['cls'], pf['net'])
                if k['no_vias'] or bko or (k['no_tracks'] and k['name'] == 'BM83_ANTENNA_KEEPOUT'):
                    B.fill(VB, k['geom'].buffer(r + 0.005, 8), x0i, y0i, 1, OFF)
            inner = np.zeros((H, W), np.uint8)
            B.fill(inner, B.edge_inner(RU.EDGE + r + 0.005), x0i, y0i, 1, OFF)
            viaok = ((VB == 0) & (inner == 1) & free[0].astype(bool) & free[1].astype(bool)).astype(np.uint8)
        return dict(off=self.off, x0i=x0i, y0i=y0i, W=W, H=H, free=np.ascontiguousarray(free), cost=np.ascontiguousarray(cost), viaok=np.ascontiguousarray(viaok), hmin=hmin)

    def open_corridors(self, pf, win, node, layer, dirs):
        """cells along straight runs of Lmin from a stub node, checked exactly (seg_ok), are marked free in the window raster;
        the conservative raster margin otherwise blocks nodes that sit next to neighbouring pads"""
        li = RL.index(layer); x0i, y0i, W, H = win['x0i'], win['y0i'], win['W'], win['H']
        for d in dirs:
            L = pf['Ld'] if d & 1 else pf['Lo']; dx, dy = DIRS[d]
            for k in (L, L // 2, 2):
                ox, oy = win['off'][0] / 1e6, win['off'][1] / 1e6
                p1 = (node[0] * G + ox, node[1] * G + oy); p2 = ((node[0] + dx * k) * G + ox, (node[1] + dy * k) * G + oy)
                ok, _ = self.seg_ok([p1, p2], pf['w'], layer, pf)
                if ok:
                    for j in range(0, k + 1):
                        x = node[0] + dx * j - x0i; y = node[1] + dy * j - y0i
                        if 0 <= x < W and 0 <= y < H:
                            win['free'][li, y, x] = 1
                    break

    # ---- A*
    def astar(self, pf, win, starts, targets):
        """starts: list of (layer_index, ix, iy, dir, g0); targets: list of (layer_index, ix, iy, [(dir,bits)])"""
        W, H = win['W'], win['H']; x0i, y0i = win['x0i'], win['y0i']
        tgt = np.zeros((2, H, W), np.uint16)
        hp = []
        for li, ix, iy, arr in targets:
            x, y = ix - x0i, iy - y0i
            if not (0 <= x < W and 0 <= y < H):
                continue
            for d, bits in arr:
                if bits & 1:
                    tgt[li, y, x] |= (1 << d)
                if bits & 2:
                    tgt[li, y, x] |= (1 << (8 + d))
            hp.append((y, x))
        st = []; sg = []
        for li, ix, iy, d, g0 in starts:
            x, y = ix - x0i, iy - y0i
            if 0 <= x < W and 0 <= y < H:
                st.append((li, y, x, d)); sg.append(g0)
        if not st or not hp:
            return None, 'no start/target in window'
        st = np.ascontiguousarray(np.array(st, np.int32)); sg = np.ascontiguousarray(np.array(sg, np.float32))
        hp = np.ascontiguousarray(np.array(hp, np.int32))
        dp = self.a.dir_pen
        dcF = [1, 1 + dp / 2, 1 + dp, 1 + dp / 2, 1, 1 + dp / 2, 1 + dp, 1 + dp / 2]
        dcB = [1 + dp, 1 + dp / 2, 1, 1 + dp / 2, 1 + dp, 1 + dp / 2, 1, 1 + dp / 2]
        dc = np.ascontiguousarray(np.array(dcF + dcB, np.float32))
        maxout = 200000; out = np.zeros(maxout * 4, np.int32); oc = np.zeros(1, np.float32)
        free = win['free']
        n = self.B.L.oct_astar(W, H, 2, ptr(free), ptr(win['cost']), ptr(win['viaok']), ptr(tgt), ptr(st), len(st), ptr(sg), ptr(hp), len(hp),
                               pf['Lo'], pf['Ld'], float(self.a.turn_cost), float(self.a.via_cost / G),
                               float(win['hmin'] * (self.a.hweight if W * H > self.a.hweight_cells else 1.0)), ptr(dc),
                               int(self.a.max_exp), ptr(out), maxout, ptr(oc))
        if n < 0:
            return None, {-1: 'no path', -2: 'out of memory', -3: 'expansion limit', -4: 'path too long'}.get(n, str(n))
        S = out[:4 * n].reshape(n, 4)
        return [(int(l), int(x) + x0i, int(y) + y0i, int(d)) for l, y, x, d in S], float(oc[0])

    # ---- connection
    def start_options(self, pad, pf, exits):
        """A* start states from a pad: fresh exits, plus T-branches at the stub node of a pad already used by this net"""
        k = self.pad_key(pad); opts = []
        used_dirs = {(u['layer'], u['d']) for u in self.used.get(k, [])}
        for e in exits:
            if (e['layer'], e['d']) not in used_dirs:
                opts.append(('fresh', e))
        for u in self.used.get(k, []):
            if not u['single'] or u.get('off') != self.off:
                continue
            ub = (u['sdir'] + 4) % 8  # stub direction from node towards the pad
            back = u['back']         # direction from node along the arriving route
            for l in range(8):
                if dang(l, ub) >= 2 and dang(l, back) >= 2:
                    opts.append(('branch', dict(u, sdir=l)))
        return opts

    def offsets(self, A, B_):
        """lattice origins to try: put A's / B's centre on lattice lines (only coordinate differences matter for exact angles)"""
        def c(p): return (int(round(p['x'] * 1e6)) % GN, int(round(p['y'] * 1e6)) % GN)
        a, b = c(A), c(B_)
        out = [u['off'] for u in self.used.get(self.pad_key(A), []) if u.get('single') and u.get('off') is not None]
        for o in (a, b, (a[0], b[1]), (b[0], a[1])):
            if o not in out:
                out.append(o)
        return out

    def route_conn(self, pf, A, B_, log):
        cands = []
        for off in self.offsets(A, B_):
            self.off = off
            exA = self.exits(A, pf); exB = self.exits(B_, pf); soA = self.start_options(A, pf, exA)
            score = (bool(soA) and bool(exB), sum(1 for k, e in soA if k == 'branch') + sum(1 for k, e in soA if e.get('var') == 'A') + sum(1 for e in exB if e['var'] == 'A'))
            cands.append((score, off))
        cands.sort(key=lambda t: t[0], reverse=True)
        err = None
        for score, off in cands[:self.a.max_offsets]:
            if not score[0] and err is not None:
                break
            self.off = off
            res, err = self.route_conn_off(pf, A, B_, log)
            if res is not None:
                return res, None
        return None, err

    def route_conn_off(self, pf, A, B_, log):
        exA = self.exits(A, pf); exB = self.exits(B_, pf)
        kA, kB = self.pad_key(A), self.pad_key(B_)
        # prefer unused pads' own reservation; exits of pads not yet used
        soA = self.start_options(A, pf, exA)
        if not soA or not exB:
            return None, 'no exit at %s' % ('%s-%s' % kA if not soA else '%s-%s' % kB)
        Lo, Ld = pf['Lo'], pf['Ld']
        starts = []; smeta = []
        for kind, e in soA:
            li = RL.index(e['layer'])
            if kind == 'fresh':
                starts.append((li, e['node'][0], e['node'][1], e['sdir'], e['cost'])); smeta.append((kind, e, None))
            else:
                L = Ld if e['sdir'] & 1 else Lo; dx, dy = DIRS[e['sdir']]
                n2 = (e['node'][0] + dx * L, e['node'][1] + dy * L)
                starts.append((li, n2[0], n2[1], e['sdir'], L * (1.414 if e['sdir'] & 1 else 1) + 4)); smeta.append((kind, e, n2))
        targets = [(RL.index(e['layer']), e['node'][0], e['node'][1], e['arr']) for e in exB]
        ox, oy = self.off
        def mm(ix, iy): return ((ix * GN + ox) / 1e6, (iy * GN + oy) / 1e6)
        pts = [mm(s[1], s[2]) for s in starts] + [mm(t[1], t[2]) for t in targets]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        discs_own = [mm(s[1], s[2]) + (0.75,) for s in starts] + [mm(*e['node']) + (0.75,) for k_, e, n2 in smeta if k_ == 'branch'] \
            + [mm(t[1], t[2]) + (0.75,) for t in targets]
        discs_halo = [(A['x'], A['y'], 1.2), (B_['x'], B_['y'], 1.2)]
        res = None
        for margin in self.a.margins:
            bbox = (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)
            win = self.window(pf, bbox, discs_own, discs_halo)
            for kind, e, n2 in smeta:
                if kind == 'fresh':
                    self.open_corridors(pf, win, e['node'], e['layer'], [e['sdir'], (e['sdir'] + 1) % 8, (e['sdir'] + 7) % 8])
            for e in exB:
                self.open_corridors(pf, win, e['node'], e['layer'], [(a + 4) % 8 for a, b in e['arr']])
            # branch starts: forced run must be free
            st2 = []
            for s, (kind, e, n2) in zip(starts, smeta):
                if kind == 'branch':
                    li = s[0]; dx, dy = DIRS[e['sdir']]; L = Ld if e['sdir'] & 1 else Lo; okr = True
                    for j in range(1, L + 1):
                        x = e['node'][0] + dx * j - win['x0i']; y = e['node'][1] + dy * j - win['y0i']
                        if not (0 <= x < win['W'] and 0 <= y < win['H']) or not win['free'][li, y, x]:
                            okr = False; break
                    if not okr:
                        st2.append(None); continue
                st2.append(s)
            sts = [s for s in st2 if s is not None]
            t0 = time.time()
            path, info = self.astar(pf, win, sts, targets)
            log.append(dict(margin=margin, W=win['W'], H=win['H'], t=round(time.time() - t0, 2), ok=path is not None, info=info if path is None else round(info, 1)))
            if path is not None:
                # identify start and target used
                s0 = path[0]; i0 = next(i for i, s in enumerate(st2) if s is not None and (s[0], s[1], s[2], s[3]) == (s0[0], s0[1], s0[2], s0[3]))
                tl = path[-1]
                eB = next(e for e in exB if RL.index(e['layer']) == tl[0] and e['node'] == (tl[1], tl[2]) and any(d == tl[3] for d, b in e['arr']))
                res = (path, smeta[i0], eB)
                break
        if res is None:
            if getattr(self.a, 'debug_png', None):
                self.dump_png(win, sts, targets, '%s/%s_%s-%s_%s-%s.png' % (self.a.debug_png, pf['net'].strip('/').replace('/', '_'), A['ref'], A['num'], B_['ref'], B_['num']))
                if sts:
                    self.dump_png(win, sts, targets, '%s/%s_%s-%s_start.png' % (self.a.debug_png, pf['net'].strip('/').replace('/', '_'), A['ref'], A['num']), crop=(sts[0][2] - win['y0i'], sts[0][1] - win['x0i']))
                t0 = targets[0]
                self.dump_png(win, sts, targets, '%s/%s_%s-%s_tgt.png' % (self.a.debug_png, pf['net'].strip('/').replace('/', '_'), B_['ref'], B_['num']), crop=(t0[2] - win['y0i'], t0[1] - win['x0i']))
            return None, 'no path'
        return res, None

    def dump_png(self, win, sts, targets, path, crop=None):
        import zlib, struct
        fr = win['free']; H, W = win['H'], win['W']
        rgb = np.zeros((H, 2 * W + 4, 3), np.uint8)
        for li in range(2):
            o = li * (W + 4)
            rgb[:, o:o + W][fr[li].astype(bool)] = (40, 140, 40)
            rgb[:, o:o + W][~fr[li].astype(bool)] = (30, 30, 30)
            rgb[:, o:o + W][(win['viaok'] > 0) & fr[li].astype(bool)] = (150, 150, 40)
            rgb[:, o:o + W][(win['cost'][li] < 1)] = (60, 200, 200)
        for col, lst in (((255, 0, 0), [(s[0], s[1] - win['x0i'], s[2] - win['y0i']) for s in sts]), ((80, 140, 255), [(t[0], t[1] - win['x0i'], t[2] - win['y0i']) for t in targets])):
            for li, x, y in lst:
                o = li * (W + 4)
                rgb[max(0, y - 2):y + 3, o + max(0, x - 2):o + x + 3] = col
        if crop:
            ys, xs = crop
            rgb = np.ascontiguousarray(np.repeat(np.repeat(rgb[max(0, ys - 60):ys + 60, max(0, xs - 60):xs + 60], 4, 0), 4, 1)); H = rgb.shape[0]
        raw = b''.join(b'\x00' + rgb[y].tobytes() for y in range(H))
        def ch(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
        open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', rgb.shape[1], H, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 6)) + ch(b'IEND', b''))

    # ---- copper from a path
    def build_copper(self, pf, path, sm, eB):
        kind, eA, n2 = sm
        w = pf['w']; ox, oy = self.off
        pieces = []        # (layer, [(x_nm,y_nm), ...], width)
        vias = []
        if kind == 'fresh':
            pieces.append((eA['layer'], list(eA['pts']), eA['width']))
        else:
            pieces.append((eA['layer'], [(eA['node'][0] * GN + ox, eA['node'][1] * GN + oy)], w))
        cur_l = RL[path[0][0]]
        route = [(path[0][1] * GN + ox, path[0][2] * GN + oy)]
        if kind == 'branch':
            route = [(eA['node'][0] * GN + ox, eA['node'][1] * GN + oy), (path[0][1] * GN + ox, path[0][2] * GN + oy)]
        segs_route = []
        for s in path[1:]:
            l = RL[s[0]]; p = (s[1] * GN + ox, s[2] * GN + oy)
            if l != cur_l:
                vias.append(route[-1]); segs_route.append((cur_l, route, w)); route = [route[-1]]; cur_l = l
            route.append(p)
        segs_route.append((cur_l, route, w))
        pieces += segs_route
        tp = list(reversed(eB['pts']))
        pieces.append((eB['layer'], tp, eB['width']))
        # flatten into segments, merge colinear consecutive with same layer and width
        segs = []
        for l, pts, wd in pieces:
            for i in range(len(pts) - 1):
                if pts[i] != pts[i + 1]:
                    segs.append([l, pts[i], pts[i + 1], wd])
        merged = []
        for s in segs:
            if merged:
                m = merged[-1]
                if m[0] == s[0] and abs(m[3] - s[3]) < 1e-9 and m[2] == s[1]:
                    d1 = (m[2][0] - m[1][0], m[2][1] - m[1][1]); d2 = (s[2][0] - s[1][0], s[2][1] - s[1][1])
                    if d1[0] * d2[1] - d1[1] * d2[0] == 0 and d1[0] * d2[0] + d1[1] * d2[1] > 0:
                        m[2] = s[2]; continue
            merged.append(s)
        return merged, vias

    def verify(self, pf, segs, vias):
        # self-consistency of the new path: holes of its own vias >= hole-to-hole apart, and no two non-adjacent
        # segments of the path closer than the clearance on one layer (A* has no self-avoidance)
        for i in range(len(vias)):
            for j in range(i + 1, len(vias)):
                if math.hypot(vias[i][0] - vias[j][0], vias[i][1] - vias[j][1]) / 1e6 < RU.HOLE_HOLE + VIA_DR - TOL:
                    return False, 'own vias too close'
        geo = [(l, LineString([(a[0] / 1e6, a[1] / 1e6), (b[0] / 1e6, b[1] / 1e6)]), w, a, b) for l, a, b, w in segs]
        for i in range(len(geo)):
            for j in range(i + 1, len(geo)):
                li, gi, wi, ai, bi = geo[i]; lj, gj, wj, aj, bj = geo[j]
                if li != lj or {ai, bi} & {aj, bj}:
                    continue
                if gi.distance(gj) < 0.2 + (wi + wj) / 2 - TOL:
                    return False, 'path touches itself'
        for l, a, b, w in segs:
            ok, why = self.seg_ok([(a[0] / 1e6, a[1] / 1e6), (b[0] / 1e6, b[1] / 1e6)], w, l, pf)
            if not ok:
                return False, 'segment %s (%.3f,%.3f)-(%.3f,%.3f): %s' % (l, a[0] / 1e6, a[1] / 1e6, b[0] / 1e6, b[1] / 1e6,
                                                                       why if isinstance(why, str) else '%s %s %s' % (why.kind, why.net, why.cls))
        for v in vias:
            if not self.via_ok_exact(v[0] / 1e6, v[1] / 1e6, pf):
                return False, 'via (%.3f,%.3f)' % (v[0] / 1e6, v[1] / 1e6)
        return True, None

    def commit(self, pf, segs, vias):
        for l, a, b, w in segs:
            pa = (a[0] / 1e6, a[1] / 1e6); pb = (b[0] / 1e6, b[1] / 1e6)
            g = LineString([pa, pb]).buffer(w / 2, 16)
            it = Item(self.B._id(), 'track', 'Track', pf['net'], pf['cls'], l, g, dyn=True, sig=True, w=w)
            self.B._add(it); self.netcopper[pf['net']].append(it)
            self.out_segs.append(dict(layer=l, a=a, b=b, w=w, net=pf['net']))
        for v in vias:
            p = (v[0] / 1e6, v[1] / 1e6)
            for l in ALLCU:
                it = Item(self.B._id(), 'via', 'Via', pf['net'], pf['cls'], l, Point(p).buffer(VIA_D / 2, 16), dyn=True)
                self.B._add(it); self.netcopper[pf['net']].append(it)
                ih = Item(self.B._id(), 'hole', 'Hole', pf['net'], pf['cls'], l, Point(p).buffer(VIA_DR / 2, 16), dyn=True)
                self.B._add(ih)
            self.out_vias.append(dict(a=v, net=pf['net']))

    # ---- chain order
    def chain(self, pads, single):
        n = len(pads)
        def dist(i, j):
            dx = abs(pads[i]['x'] - pads[j]['x']); dy = abs(pads[i]['y'] - pads[j]['y'])
            return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)
        def cost(order):
            c = sum(dist(order[i], order[i + 1]) for i in range(n - 1))
            c += sum(50.0 for i in order[1:-1] if single[i])
            return c
        if n <= 2:
            return list(range(n))
        if n <= 7:
            best = min(itertools.permutations(range(n)), key=cost)
            return list(best)
        best = None
        for s in range(n):
            order = [s]; rest = set(range(n)) - {s}
            while rest:
                j = min(rest, key=lambda j: dist(order[-1], j)); order.append(j); rest.remove(j)
            improved = True
            while improved:
                improved = False
                for i in range(1, n - 1):
                    for j in range(i + 1, n):
                        o2 = order[:i] + order[i:j + 1][::-1] + order[j + 1:]
                        if cost(o2) < cost(order) - 1e-9:
                            order = o2; improved = True
            if best is None or cost(order) < cost(best):
                best = order
        return best

    # ---- net
    def route_net(self, net):
        pf = self.prof(net)
        pads = [p for p in self.B.pads if p['net'] == net and any(l in p['poly'] for l in RL)]
        rec = dict(net=net, cls=pf['cls'], w=pf['w'], pads=len(pads), conns=[], status='')
        t0 = time.time()
        if len(pads) < 2:
            rec['status'] = 'skip (<2 pads)'; return rec
        for p in pads:
            self.unreserve(self.pad_key(p))
        single = []
        for p in pads:
            self.off = (int(round(p['x'] * 1e6)) % GN, int(round(p['y'] * 1e6)) % GN)
            ex = self.exits(p, pf)
            single.append(bool(ex) and all(e['single'] for e in ex))
        order = self.chain(pads, single)
        okc = 0
        for i in range(len(order) - 1):
            A, B_ = pads[order[i]], pads[order[i + 1]]
            clog = dict(a='%s-%s' % self.pad_key(A), b='%s-%s' % self.pad_key(B_), tries=[])
            dr = self.direct(pf, A, B_)
            if dr is not None:
                segs, da, db, l = dr
                self.commit(pf, segs, [])
                self.used.setdefault(self.pad_key(A), []).append(dict(layer=l, d=da, sdir=da, single=False, node=None, back=da))
                self.used.setdefault(self.pad_key(B_), []).append(dict(layer=l, d=db, sdir=db, single=False, node=None, back=db))
                clog['status'] = 'ok'; clog['direct'] = True; clog['segs'] = 1; clog['vias'] = 0
                clog['len'] = round(math.hypot(segs[0][2][0] - segs[0][1][0], segs[0][2][1] - segs[0][1][1]) / 1e6, 3)
                okc += 1; rec['conns'].append(clog)
                continue
            res, err = self.route_conn(pf, A, B_, clog['tries'])
            if res is not None:
                path, sm, eB = res
                segs, vias = self.build_copper(pf, path, sm, eB)
                ok, why = self.verify(pf, segs, vias)
                if not ok:
                    clog['status'] = 'verify failed: ' + why
                else:
                    self.commit(pf, segs, vias)
                    kind, eA, n2 = sm
                    if kind == 'fresh':
                        self.used.setdefault(self.pad_key(A), []).append(dict(eA, back=path[1][3] if len(path) > 1 else eA['sdir']))
                    # arrival direction into B's node: direction of the last move; back = opposite
                    self.used.setdefault(self.pad_key(B_), []).append(dict(eB, back=(path[-1][3] + 4) % 8))
                    clog['status'] = 'ok'; clog['segs'] = len(segs); clog['vias'] = len(vias)
                    clog['len'] = round(sum(math.hypot(b[0] - a[0], b[1] - a[1]) for l, a, b, w in segs) / 1e6, 3)
                    okc += 1
            else:
                clog['status'] = err
            rec['conns'].append(clog)
        rec['status'] = 'complete' if okc == len(order) - 1 else 'PARTIAL %d/%d' % (okc, len(order) - 1)
        rec['t'] = round(time.time() - t0, 2)
        return rec


    # ---- rip-up and reroute (transactional)
    def net_pads(self, net):
        return [self.pad_key(p) for p in self.B.pads if p['net'] == net]

    def snapshot(self, nets):
        return {n: dict(items=list(self.netcopper.get(n, [])), segs=[s for s in self.out_segs if s['net'] == n], vias=[v for v in self.out_vias if v['net'] == n],
                        used={k: list(self.used[k]) for k in self.net_pads(n) if k in self.used}, rec=self.recs.get(n)) for n in nets}

    def ripup(self, net):
        for it in self.netcopper.pop(net, []):
            self.B.idx[it.layer].remove(it)
        self.out_segs = [s for s in self.out_segs if s['net'] != net]
        self.out_vias = [v for v in self.out_vias if v['net'] != net]
        holes = [it for l in ALLCU for it in list(self.B.idx[l].items.values()) if it.dyn and it.kind == 'hole' and it.net == net]
        for it in holes:
            self.B.idx[it.layer].remove(it)
        for k in self.net_pads(net):
            self.used.pop(k, None)

    def restore(self, snap):
        for n, S in snap.items():
            self.ripup(n)
            for it in S['items']:
                self.B._add(it)
                if it.kind == 'via':
                    self.B._add(Item(self.B._id(), 'hole', 'Hole', it.net, it.cls, it.layer, it.geom.centroid.buffer(VIA_DR / 2, 16), dyn=True))
            self.netcopper[n] = list(S['items']); self.out_segs += S['segs']; self.out_vias += S['vias']
            self.used.update({k: list(v) for k, v in S['used'].items()})
            if S['rec'] is not None:
                self.recs[n] = S['rec']

    @staticmethod
    def nok(rec):
        return 0 if rec is None else sum(1 for c in rec['conns'] if c['status'] == 'ok')

    def conflicts(self, net, A, B_, candidates):
        """route the failed connection with the copper of `candidates` passable at a penalty; return the nets it would cross"""
        pf = self.prof(net)
        self.soft = set(candidates)
        try:
            res, err = self.route_conn(pf, A, B_, [])
            if res is None:
                return None
            segs, vias = self.build_copper(pf, *res)
        finally:
            self.soft = set()
        hit = set()
        for l, a, b, w in segs:
            line = LineString([(a[0] / 1e6, a[1] / 1e6), (b[0] / 1e6, b[1] / 1e6)]) if a != b else Point(a[0] / 1e6, a[1] / 1e6)
            for n in candidates:
                if n in hit:
                    continue
                for it in self.netcopper.get(n, []):
                    if it.layer != l:
                        continue
                    c = RU.clr_strict(pf['cls'], net, it.cls, it.typ)
                    if it.kind == 'track' and (pf['space'] or SPACE.get(it.cls)):
                        c = max(c, pf['space'] or 0, SPACE.get(it.cls) or 0)
                    if line.distance(it.geom) < c + w / 2:
                        hit.add(n); break
        for v in vias:
            p = Point(v[0] / 1e6, v[1] / 1e6)
            for n in candidates:
                if n not in hit and any(p.distance(it.geom) < VIA_D / 2 + 0.3 for it in self.netcopper.get(n, [])):
                    hit.add(n)
        return hit

    def route_stage(self, nets):
        for net in nets:
            self.pending.discard(net)
            self.recs[net] = self.route_net(net)
            r = self.recs[net]
            print('%-28s %-8s %-14s %s' % (net, r['cls'], r['status'], ' '.join('%s>%s:%s' % (c['a'], c['b'], c['status'][:20]) for c in r['conns'] if c['status'] != 'ok')), flush=True)
        if self.a.ripup <= 0:
            return
        rips = collections.Counter(); T0 = time.time()
        for rnd in range(self.a.ripup):
            improved = False
            for net in nets:
                if time.time() - T0 > self.a.rrr_time:
                    break
                r = self.recs[net]
                if r['status'] == 'complete' or r['status'].startswith('skip'):
                    continue
                fc = next((c for c in r['conns'] if c['status'] != 'ok'), None)
                pads = {'%s-%s' % self.pad_key(p): p for p in self.B.pads if p['net'] == net}
                cands = [n for n in nets if n != net and self.netcopper.get(n) and rips[n] < self.a.ripup]
                hit = self.conflicts(net, pads[fc['a']], pads[fc['b']], cands)
                entry = dict(round=rnd, net=net, conn='%s>%s' % (fc['a'], fc['b']), conflicts=sorted(hit) if hit is not None else None)
                if not hit or len(hit) > self.a.rrr_max:
                    entry['result'] = 'no candidate set'; self.rrr_log.append(entry); continue
                group = [net] + sorted(hit)
                before = sum(self.nok(self.recs.get(n)) for n in group)
                snap = self.snapshot(group)
                for n in group:
                    self.ripup(n)
                for n in group:
                    self.recs[n] = self.route_net(n)
                after = sum(self.nok(self.recs.get(n)) for n in group)
                if after > before:
                    entry['result'] = 'kept %d -> %d' % (before, after); improved = True
                    for n in hit:
                        rips[n] += 1
                else:
                    entry['result'] = 'rolled back %d -> %d' % (before, after)
                    self.restore(snap)
                self.rrr_log.append(entry)
                print('  RRR', entry, flush=True)
            if not improved:
                break


# ---------------------------------------------------------------- output
def fmt(v_nm):
    s = '%d.%06d' % (abs(v_nm) // 1000000, abs(v_nm) % 1000000)
    s = s.rstrip('0').rstrip('.')
    return ('-' if v_nm < 0 else '') + s


def write_board(src, dst, segs, vias):
    txt = open(src, encoding='utf-8').read().split('\n')
    k = next((i for i, L in enumerate(txt) if L == '\t(zone'), None)
    if k is None:
        k = max(i for i, L in enumerate(txt) if L == ')')
    add = []
    for s in segs:
        add += ['\t(segment', '\t\t(start %s %s)' % (fmt(s['a'][0]), fmt(s['a'][1])), '\t\t(end %s %s)' % (fmt(s['b'][0]), fmt(s['b'][1])),
                '\t\t(width %s)' % fmt(int(round(s['w'] * 1e6))), '\t\t(layer "%s")' % s['layer'], '\t\t(net "%s")' % s['net'],
                '\t\t(uuid "%s")' % uuid.uuid4(), '\t)']
    for v in vias:
        add += ['\t(via', '\t\t(at %s %s)' % (fmt(v['a'][0]), fmt(v['a'][1])), '\t\t(size %s)' % fmt(int(VIA_D * 1e6)), '\t\t(drill %s)' % fmt(int(VIA_DR * 1e6)),
                '\t\t(layers "F.Cu" "B.Cu")', '\t\t(net "%s")' % v['net'], '\t\t(uuid "%s")' % uuid.uuid4(), '\t)']
    out = txt[:k] + add + txt[k:]
    open(dst, 'w', encoding='utf-8').write('\n'.join(out))


def read_nets(path):
    stages = collections.OrderedDict(); opts = {}
    for L in open(path, encoding='utf-8'):
        L = L.split('#', 1)[0].strip()
        if not L:
            continue
        t = L.replace(':', ' ', 1).split() if re.match(r'^S\d+:', L) else L.split()
        st, net = t[0], t[1]
        stages.setdefault(st, []).append(net)
        opts[net] = dict(kv.split('=', 1) for kv in t[2:])
    return stages, opts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--board', required=True); ap.add_argument('--geo', required=True); ap.add_argument('--nets', required=True)
    ap.add_argument('--stage', required=True); ap.add_argument('--out', required=True); ap.add_argument('--manifest', required=True)
    ap.add_argument('--log'); ap.add_argument('--workdir', default=None)
    ap.add_argument('--dru'); ap.add_argument('--pro')
    ap.add_argument('--via-cost', type=float, default=4.0, help='via cost in mm of track')
    ap.add_argument('--turn-cost', type=float, default=1.0, help='cost per 45-degree bend in cells')
    ap.add_argument('--dir-pen', type=float, default=0.10, help='extra cost factor for steps against the layer preferred direction')
    ap.add_argument('--bcu-cost', type=float, default=1.3, help='B.Cu step factor over In2 GND')
    ap.add_argument('--b-island', type=float, default=3.0, help='extra B.Cu factor over a non-GND In2 island')
    ap.add_argument('--b-void', type=float, default=3.0, help='extra B.Cu factor over no In2 copper')
    ap.add_argument('--f-void', type=float, default=2.0, help='F.Cu penalty over In1 void')
    ap.add_argument('--pair-avoid', type=float, default=4.0, help='cost factor 0.25-0.8 mm from the partner (outside the pair band)')
    ap.add_argument('--pair-attract', type=float, default=0.6, help='cost factor on the diff-pair rail next to the partner')
    ap.add_argument('--margins', default='4,12,40')
    ap.add_argument('--max-exp', type=float, default=6e7)
    ap.add_argument('--no-reserve', action='store_true')
    ap.add_argument('--pad-pen', type=float, default=2.0, help='extra cost per cell near pads of nets still to route (0 = off)')
    ap.add_argument('--pad-halo', type=float, default=0.6, help='edge distance of that soft keep-away, mm')
    ap.add_argument('--hweight', type=float, default=1.3, help='heuristic weight (weighted A*) for windows larger than --hweight-cells')
    ap.add_argument('--hweight-cells', type=float, default=1.5e6)
    ap.add_argument('--max-offsets', type=int, default=2, help='lattice origins tried per connection')
    ap.add_argument('--ripup', type=int, default=3, help='rip-up-and-reroute rounds (0 = off)')
    ap.add_argument('--rrr-max', type=int, default=3, help='max nets ripped for one failed connection')
    ap.add_argument('--rrr-time', type=float, default=900, help='time budget of rip-up rounds per stage, s')
    ap.add_argument('--soft-pen', type=float, default=20.0, help='cost per cell crossing ripable copper in the conflict search')
    ap.add_argument('--debug-png', default=None, help='directory for PNG dumps of failed connection windows (last margin)')
    a = ap.parse_args()
    a.margins = [float(x) for x in a.margins.split(',')]
    stem = os.path.splitext(a.board)[0]
    a.dru = a.dru or stem + '.kicad_dru'; a.pro = a.pro or stem + '.kicad_pro'
    workdir = a.workdir or os.path.dirname(os.path.abspath(a.out))
    T0 = time.time()
    stages, opts = read_nets(a.nets)
    if a.stage not in stages:
        raise SystemExit('stage %s not in %s' % (a.stage, a.nets))
    man = json.load(open(a.manifest)) if os.path.exists(a.manifest) else dict(stages={})
    # lock check of earlier stages
    names = list(stages)
    for st in names[:names.index(a.stage)]:
        if st not in man['stages']:
            raise SystemExit('earlier stage %s not in manifest; route it first' % st)
        h, n = LK.copper_hash(a.board, stages[st])
        if h != man['stages'][st]['copper_sha256']:
            raise SystemExit('LOCK VIOLATION: copper of stage %s changed (hash %s != %s)' % (st, h, man['stages'][st]['copper_sha256']))
        print('lock ok', st, n, 'items', flush=True)
    core = load_core(workdir)
    B = Board(a.geo, a.dru, a.pro, core)
    R = Router(B, a, opts)
    later = [n for st in names[names.index(a.stage):] for n in stages[st]]
    if not a.no_reserve:
        print('reserved escapes:', R.reserve(later), flush=True)
    R.pending = set(later)
    R.route_stage(stages[a.stage])
    recs = [R.recs[n] for n in stages[a.stage]]
    for r in recs:
        if not r['status'].startswith('complete'):
            print('  final %-28s %s' % (r['net'], r['status']), flush=True)
    write_board(a.board, a.out, R.out_segs, R.out_vias)
    h, n = LK.copper_hash(a.out, stages[a.stage])
    nconn = sum(len(r['conns']) for r in recs); okc = sum(1 for r in recs for c in r['conns'] if c['status'] == 'ok')
    summ = dict(stage=a.stage, nets=stages[a.stage], complete_nets=sum(1 for r in recs if r['status'] == 'complete'), conns=nconn, conns_ok=okc,
                segments=len(R.out_segs), vias=len(R.out_vias), runtime_s=round(time.time() - T0, 1),
                params={k: getattr(a, k) for k in ('via_cost', 'turn_cost', 'dir_pen', 'bcu_cost', 'b_island', 'b_void', 'f_void', 'pair_attract', 'pair_avoid', 'margins', 'max_exp', 'no_reserve', 'pad_pen', 'pad_halo', 'max_offsets', 'hweight', 'hweight_cells', 'ripup', 'rrr_max', 'rrr_time', 'soft_pen')})
    man['stages'][a.stage] = dict(summ, input_board=os.path.abspath(a.board), output_board=os.path.abspath(a.out),
                                  output_sha256=hashlib.sha256(open(a.out, 'rb').read()).hexdigest(), copper_sha256=h, copper_items=n,
                                  dru_sha256=RU.check_dru(a.dru)[1], pro_sha256=hashlib.sha256(open(a.pro, 'rb').read()).hexdigest())
    json.dump(man, open(a.manifest, 'w'), indent=1)
    if a.log:
        json.dump(dict(summary=summ, nets=recs, rrr=R.rrr_log), open(a.log, 'w'), indent=1)
    print('STAGE %s: nets complete %d/%d, connections %d/%d, %d segments, %d vias, %.1f s%s' % (
        a.stage, summ['complete_nets'], len(stages[a.stage]), okc, nconn, len(R.out_segs), len(R.out_vias), summ['runtime_s'],
        '' if okc == nconn else '  PARTIAL'), flush=True)


if __name__ == '__main__':
    main()
