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
keep-outs (antenna, BKO_* on B.Cu, J7 no-via), no In1/In2 routing.
Router-side rules added 2026-11-02 (section 9 of routing-toolchain-oct-2026-11-01.md; stricter than DRC, no rule file change):
  * module keep-out (--module-keepout U1:0.5): no F.Cu track or via inside the BM83 pad rectangle shrunk by 0.5 mm;
    the module's own pads (+0.15 mm) are cut out so their stubs can leave outward
  * SP1/GE9 halo (--halo 0.6): tracks of classes AUDIO, I2S_CLK, USB and /AUD_SDA, /AUD_SCL keep a 0.6 mm edge gap to every
    other signal track and vice versa, outside neck areas and outside 1.2 mm of the connection's own pads
  * near-parallel cost (--par-gap 0.4 --par-pen): extra cost per cell within 0.4 mm of another signal net's track
  * LA2/LA5: sensitive nets may use B.Cu only over In2 GND (--sens-bcu gnd); every via of a sensitive net gets a GND
    stitching via within --stitch 1.5 mm (placed legally; via sites without a legal stitch spot are pruned before A*)
  * SP3 (--sp3 2.0): FB/COMP/ILIM/PROG/TS/EN/CE nets of switching ICs keep 2.0 mm to SWITCH/BOOT copper (beyond 0.75 mm of
    the stub nodes; the stubs themselves use the DRC value)
  * pour guard: a connection that would cut a via-anchored F/B.Cu GND fill piece into an un-anchored part is rejected
  * self-avoidance: a path that touches itself, or whose via has no stitch spot, is re-searched with that part blocked
Router fixes 2026-11-02 (section 10 of the report; every one can be switched off):
  1 escape reservations: all fine-pitch pads of this and every later stage are reserved before the stage, with the neck
    clearance between reservations and stubs (so a later-stage pad next to an earlier-stage pad keeps its lane); a pad left
    unrouted gets its reservation back (released only when its own net uses it)
  2 pad identity (ref, number, index): same-number pads of one part on one net are one electrical pin (no routing between
    them; a connection goes to the nearest member)
  3 continuation mode (--cont-drc DRC.json): route only the open connections (DRC unconnected_items) of an already routed
    board; all existing copper is a locked obstacle (manifest C0 + per-stage added items); a connection may end on existing
    copper of its own net at a pad, a via, or a segment tap (stub node: cheap; T in a segment: --tap-pen-mid, flagged)
  4 rip-up (--rrr-mode new): only same-stage nets of this run that are not complete-and-short (ratio <= --rrr-keep-ratio);
    kept only if connections increase and the group length ratio does not worsen
  5 detour limit (--detour 2.5): longer paths are re-searched with a cheap via hop and with the other layer preferred; the
    shortest is kept, still-long ones are accepted (no alternative) and listed in the stage summary (detours)
  6 GND stitching along sensitive B.Cu runs (--run-stitch 6 --run-stitch-dist 1.5)
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
HALO_CLS = {'I2S_CLK', 'USB', 'AUDIO'}   # SP1/GE9 edge gap to other signal tracks (halo), applied outside neck areas
HALO_NETS = {'/AUD_SDA', '/AUD_SCL'}
HALO = [0.6]                             # set from --halo
FORBID_ISLAND_CLS = {'POWER_HI', 'PVDD', 'SPK_OUT'}
VIA_D, VIA_DR = 0.6, 0.3
SW_CLS = ('SWITCH', 'BOOT')
SP3_TOK = re.compile(r'(?<![A-Z0-9])(FB|COMP|ILIM|PROG|TS|EN|CE)(?![A-Z0-9])')
STITCH_RE = re.compile(r'I2S|AUD_S|BT_AUDIO|HP_OUT|VMID|USB_D|USB_AUDIO|AUX|U24-VIN|XI\)?$|XO\)?$')   # r7_metrics gvia set


def space_of(net, cls):
    return HALO[0] if (cls in HALO_CLS or net in HALO_NETS) and HALO[0] > 0 else None


def octi_xy(x1, y1, x2, y2):
    dx = abs(x1 - x2); dy = abs(y1 - y2)
    return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


def octi(a, b):
    return octi_xy(a['x'], a['y'], b['x'], b['y'])


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
    def __init__(self, geo, dru, pro, core, args=None):
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
        # pads; identity = (ref, number, idx): pin stacks (SW100 "1" x2, U11 "40" x2) share ref+number (fix 2, 2026-11-02)
        self.D = D
        stk = collections.Counter((p['ref'], p['num']) for p in D['pads'])
        seen = collections.Counter()
        for p in D['pads']:
            p['idx'] = seen[(p['ref'], p['num'])]; seen[(p['ref'], p['num'])] += 1; p['nst'] = stk[(p['ref'], p['num'])]
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
        # ---- module keep-out (BM83: no top-layer routing under the module), own pads cut out for their outward stubs
        self.mod_ko = []
        for spec in (args.module_keepout.split(',') if args and args.module_keepout else []):
            ref, sh = spec.split(':'); sh = float(sh)
            pp = [mkpolys(p['poly']['F.Cu']) for p in D['pads'] if p['ref'] == ref and 'F.Cu' in p['poly']]
            pp = [g for g in pp if g is not None]
            if not pp:
                continue
            bd = unary_union(pp).bounds
            rect = box(bd[0] + sh, bd[1] + sh, bd[2] - sh, bd[3] - sh)
            g = rect.difference(unary_union([q.buffer(0.15, 8) for q in pp]))
            self.keepouts.append(dict(name='MODULE_KO_' + ref, layers=['F.Cu'], no_tracks=True, no_vias=True, geom=g))
            self.mod_ko.append((ref, rect.bounds))
            print('module keep-out %s: F.Cu rect %.3f,%.3f - %.3f,%.3f (pad rectangle shrunk %.2f mm), own pads cut out' % ((ref,) + rect.bounds + (sh,)), flush=True)
        # ---- SP3 victim nets: FB/COMP/ILIM/PROG/TS/EN/CE nets that touch a switching IC (part with a SWITCH/BOOT pad)
        swrefs = {p['ref'] for p in D['pads'] if p['cls'] in SW_CLS and p['ref'][:1] == 'U'}
        npads = collections.defaultdict(set)
        for p in D['pads']:
            if p['net']:
                npads[p['net']].add(p['ref'])
        self.sp3 = sorted(n for n, refs in npads.items() if SP3_TOK.search(n.upper()) and refs & swrefs and n not in RU.CRIT_NETS
                          and self.netcls.get(n) in RU.SIGCLS)
        print('SP3 nets (switch-node distance %.1f mm, router side): %s' % (args.sp3 if args else 0, ' '.join(self.sp3)), flush=True)
        # ---- legal GND stitching via centres need In1 GND and In2 GND copper around the whole via pad
        g1 = unary_union([g for n, c, g, td in self.zfill['In1.Cu'] if n == 'GND']); g2 = unary_union([g for n, c, g, td in self.zfill['In2.Cu'] if n == 'GND'])
        self.gnd12 = g1.intersection(g2).buffer(-VIA_D / 2 - 0.01, 8) if (not g1.is_empty and not g2.is_empty) else Polygon()
        self.gnd12_p = prep(self.gnd12)
        self.R_gnd12 = self.raster_full([self.gnd12])
        # ---- pour guard: F/B.Cu GND fill pieces anchored by a GND via or plated GND hole
        anch = [it.geom for l in ('F.Cu',) for it in self.idx[l].items.values() if it.kind == 'via' and it.net == 'GND'] + \
               [it.geom for it in self.idx['F.Cu'].items.values() if it.kind == 'hole' and it.net == 'GND' and it.typ == 'Hole']
        self.anchor0 = unary_union(anch) if anch else Polygon()
        self.gpieces = []
        for l in ('F.Cu', 'B.Cu'):
            gp = [it.geom for it in self.idx[l].items.values() if it.kind == 'pad' and it.net == 'GND']
            for z in D['zones']:
                if z['net'] != 'GND' or z['teardrop'] or l not in z['fills']:
                    continue
                g = mkpolys(z['fills'][l])
                if g is None:
                    continue
                for pc in (g.geoms if hasattr(g, 'geoms') else [g]):
                    if pc.area < 0.05 or not pc.intersects(self.anchor0):
                        continue
                    self.gpieces.append(dict(layer=l, name=z['name'] or 'GND zone', geom=pc, bounds=pc.bounds,
                                             pads=unary_union([q for q in gp if q.intersects(pc)]) if gp else Polygon()))
        print('board model: %d items, lattice %dx%d, rasters %.1fs, %d anchored GND F/B pieces' % (self.nid, self.GW, self.GH, time.time() - t0, len(self.gpieces)), flush=True)

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
        self.sp3set = set(B.sp3) if args.sp3 > 0 else set()
        self.xblock = []                                 # per-connection retry blocks: (layer, geom) for tracks
        self.xnovia = []                                 # per-connection retry blocks: via sites (x, y) mm
        self.stats = collections.Counter()
        self.cont = False                                # continuation mode (fix 3): route only the open connections
        self.layer_mul = [1.0, 1.0]                      # per-layer cost factor (detour alternatives, fix 5)
        self.conn_terms = {}                             # (net, conn index) -> (terminals A, terminals B) for rip-up
        self.detours = []                                # connections accepted above --detour x octilinear minimum
        self.base_used = {}                              # continuation: pad exits used by existing copper
        self.viaused = collections.defaultdict(lambda: collections.defaultdict(set))   # net -> (x_nm, y_nm) -> {(layer, dir)}
        self.base_viaused = {}

    # ---- per net profile
    def prof(self, net):
        cls = self.B.netcls.get(net, 'Default')
        o = self.opts.get(net, {})
        w = float(o.get('width', self.B.cls_w.get(cls, 0.25)))
        sens = cls in SENSITIVE_CLS or net in SENSITIVE_NETS
        bcu = o.get('bcu', self.a.sens_bcu if sens else 'yes')
        Lmm = max(0.4, 3 * w)
        return dict(net=net, cls=cls, w=w, sens=sens, bcu=bcu, space=space_of(net, cls), pair=o.get('pair'),
                    sp3=net in self.sp3set, stitch=self.a.stitch > 0 and (sens or bool(STITCH_RE.search(net))),
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
            elif it.dyn and isinstance(it.owner, tuple):
                # escape reservation of another pad (not copper): neck clearance between reservations and stubs (fix 1);
                # the A* window still keeps the strict clearance to reservations for the body of a route
                c = RU.clr_neck(pf['cls'], pf['net'], it.cls, it.typ)
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

    # ---- GND stitching vias (LA5)
    PFG = dict(cls='GND', net='GND')

    def gnd_pts(self, x, y, R):
        """centres of GND vias and plated GND holes within R of (x, y)"""
        out = []
        for it in self.B.idx['F.Cu'].query((x - R, y - R, x + R, y + R)):
            if it.kind == 'hole' and it.net == 'GND' and it.typ == 'Hole':
                c = it.geom.centroid; out.append((c.x, c.y))
        return out

    def stitchable(self, pf, x0i, y0i, W, H, OFF, sl, q):
        """bool raster of via sites that have a GND via / plated GND hole within --stitch mm, or a legal free GND via spot in the
        annulus [0.8 mm, --stitch] (legality as via_ok_exact for net GND, plus In1 and In2 GND copper around the via pad)"""
        B = self.B; R = self.a.stitch; r = VIA_D / 2
        GB = np.zeros((H, W), np.uint8)
        for l in ALLCU:
            for it in B.idx[l].query(q):
                if it.kind == 'zone' and it.net == 'GND':
                    continue
                if it.dyn and it.net in self.soft:
                    continue
                if it.kind == 'hole':
                    need = RU.HOLE_HOLE + VIA_DR / 2 if it.net == 'GND' else max(RU.HOLE_HOLE + VIA_DR / 2, (RU.EDGE if it.typ == 'NPTH' else RU.HOLE_CLR) + r)
                elif it.kind == 'pad' and it.smd:
                    need = r + (0.25 if it.net == 'GND' else max(0.25, RU.clr_strict('GND', 'GND', it.cls, it.typ)))
                elif it.net == 'GND':
                    continue
                else:
                    need = r + RU.clr_strict('GND', 'GND', it.cls, it.typ)
                B.fill(GB, B.buffered(it, need + 0.01), x0i, y0i, 1, OFF)
        for k in B.keepouts:
            if k['no_vias'] or (k['no_tracks'] and k['name'] == 'BM83_ANTENNA_KEEPOUT'):
                B.fill(GB, k['geom'].buffer(r + 0.01, 8), x0i, y0i, 1, OFF)
        inner = np.zeros((H, W), np.uint8)
        B.fill(inner, B.edge_inner(RU.EDGE + r + 0.01), x0i, y0i, 1, OFF)
        g12 = np.zeros((H, W), np.uint8)
        B.fill(g12, B.gnd12, x0i, y0i, 1, OFF)
        GV = (GB == 0) & (inner == 1) & (g12 == 1)
        Rc = int(math.ceil(R / G))
        yy, xx = np.mgrid[-Rc:Rc + 1, -Rc:Rc + 1]; d = np.hypot(xx, yy) * G
        out = np.zeros((H, W), bool)
        if GV.any():
            K = ((d >= VIA_D + 0.2 + 0.02) & (d <= R - 0.02)).astype(np.float32)
            s = (H + 2 * Rc, W + 2 * Rc)
            C = np.fft.irfft2(np.fft.rfft2(GV.astype(np.float32), s=s) * np.fft.rfft2(K, s=s), s=s)[Rc:Rc + H, Rc:Rc + W]
            out |= C > 0.5
        # existing GND vias / plated GND holes
        ox, oy = OFF
        bx = (x0i * G + ox, y0i * G + oy, (x0i + W) * G + ox, (y0i + H) * G + oy)
        disc = (d <= R - 0.02)
        for (cx, cy) in self.gnd_pts((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2, max(bx[2] - bx[0], bx[3] - bx[1]) / 2 + R):
            ix = int(round((cx - ox) / G)) - x0i; iy = int(round((cy - oy) / G)) - y0i
            a0, a1, b0, b1 = iy - Rc, iy + Rc + 1, ix - Rc, ix + Rc + 1
            c0, c1, e0, e1 = max(0, a0), min(H, a1), max(0, b0), min(W, b1)
            if c0 < c1 and e0 < e1:
                out[c0:c1, e0:e1] |= disc[c0 - a0:c1 - a0, e0 - b0:e1 - b0]
        return out

    def gnd_via_ok(self, x, y, pf, segs, vias, placed):
        if not self.B.gnd12_p.contains(Point(x, y)):
            return False
        if not self.via_ok_exact(x, y, self.PFG):
            return False
        p = Point(x, y); r = VIA_D / 2
        for l, a, b, w in segs:
            ln = LineString([(a[0] / 1e6, a[1] / 1e6), (b[0] / 1e6, b[1] / 1e6)]) if a != b else Point(a[0] / 1e6, a[1] / 1e6)
            if p.distance(ln) < r + w / 2 + RU.clr_strict('GND', 'GND', pf['cls'], 'Track') - TOL:
                return False
        for v in vias:
            if math.hypot(x - v[0] / 1e6, y - v[1] / 1e6) < max(VIA_D + RU.clr_strict('GND', 'GND', pf['cls'], 'Via'), RU.HOLE_HOLE + VIA_DR) - TOL:
                return False
        for (qx, qy) in placed:
            if math.hypot(x - qx, y - qy) < RU.HOLE_HOLE + VIA_DR + 0.05:
                return False
        return True

    def place_stitches(self, pf, segs, vias):
        """GND via within --stitch mm of every via of a stitched net; returns (list of (x, y) mm, None) or (None, failing via)"""
        if not pf['stitch'] or not vias:
            return [], None
        R = self.a.stitch; placed = []
        for v in vias:
            vx, vy = v[0] / 1e6, v[1] / 1e6
            if any(math.hypot(vx - x, vy - y) <= R for x, y in self.gnd_pts(vx, vy, R + 0.1) + placed):
                continue
            ok = False
            for rr in np.arange(VIA_D + 0.25, R + 1e-9, 0.05):
                n = max(16, int(2 * math.pi * rr / 0.1))
                for k in range(n):
                    t = 2 * math.pi * k / n
                    x = round(vx + rr * math.cos(t), 4); y = round(vy + rr * math.sin(t), 4)
                    if self.gnd_via_ok(x, y, pf, segs, vias, placed):
                        placed.append((x, y)); ok = True; break
                if ok:
                    break
            if not ok:
                return None, (vx, vy)
        return placed, None

    # ---- pour guard
    def pour_ok(self, pf, segs, vias, stitches):
        """reject copper that cuts a via-anchored F/B.Cu GND fill piece so that a part holding a GND pad (or > 0.3 mm2) loses
        every via anchor; fill model: zone clearance 0.2 mm + half width around new copper, 0.2 mm minimum width"""
        B = self.B
        if not B.gpieces or not self.a.pour_guard:
            return True, None
        for l in ('F.Cu', 'B.Cu'):
            new = [LineString([(a[0] / 1e6, a[1] / 1e6), (b[0] / 1e6, b[1] / 1e6)]).buffer(w / 2 + 0.2, 8) for ll, a, b, w in segs if ll == l and a != b]
            new += [Point(v[0] / 1e6, v[1] / 1e6).buffer(VIA_D / 2 + 0.2, 8) for v in vias]
            if not new:
                continue
            nu = unary_union(new); nb = nu.bounds
            for pc in B.gpieces:
                if pc['layer'] != l:
                    continue
                b = pc['bounds']
                if b[0] > nb[2] or b[2] < nb[0] or b[1] > nb[3] or b[3] < nb[1] or not pc['geom'].intersects(nu):
                    continue
                old = [it.geom.buffer(0.2, 8) for it in B.idx[l].query(b) if it.dyn and it.kind in ('track', 'via') and it.net != 'GND' and not isinstance(it.owner, tuple)]
                cut = unary_union(old + [nu])
                after = pc['geom'].difference(cut).buffer(-0.1, 8).buffer(0.1, 8)
                anch = [B.anchor0] + [Point(x, y).buffer(VIA_D / 2) for x, y in stitches] + \
                       [it.geom for it in B.idx[l].query(b) if it.dyn and it.kind == 'via' and it.net == 'GND']
                an = unary_union(anch)
                for c in (after.geoms if hasattr(after, 'geoms') else [after]):
                    if c.is_empty or c.intersects(an):
                        continue
                    if c.area > 0.3 or (not pc['pads'].is_empty and c.intersects(pc['pads'])):
                        return False, ('%s %.2f,%.2f' % (pc['name'], c.centroid.x, c.centroid.y), l, pc['geom'])
        return True, None

    # ---- pad exits
    def pad_key(self, p):
        return (p['ref'], p['num'], p.get('idx', 0))

    @staticmethod
    def pname(p):
        return '%s-%s' % (p['ref'], p['num']) + ('#%d' % p['idx'] if p.get('nst', 1) > 1 else '')

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
        k = (pad['ref'], pad['num'], pad.get('idx', 0), l)
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
    def reserve(self, nets, only=None):
        """fix 1: called once before the stage with the nets of this AND every later stage (stage order = priority); a pad's
        exit is checked against earlier reservations with the neck clearance (seg_ok), so a later-stage pad next to an
        earlier-stage pad keeps its lane; `only` = set of pad keys (re-reservation of pads left unrouted)"""
        n = 0
        for net in nets:
            pf = self.prof(net)
            for p in self.B.pads:
                if p['net'] != net:
                    continue
                k = self.pad_key(p)
                if only is not None and k not in only:
                    continue
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
            OB3 = np.zeros((H, W), np.uint8)  # near-parallel band of other signal nets' tracks (cost)
            OB = np.zeros((H, W), np.uint8)   # bit1 strict, bit2 neck, bit4 halo, bit8 own, bit16 keepout, bit32 soft, bit64 SP3, bit128 retry block
            for it in B.idx[l].query(q):
                if it.kind == 'zone' and it.net == 'GND':
                    continue
                if it.net == pf['net'] and it.net:
                    # own copper of this run; in continuation mode also the locked existing copper of the net (joinable only at taps)
                    if (it.dyn or self.cont) and it.kind in ('track', 'via') and not (it.dyn and isinstance(it.owner, tuple)):
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
                if it.kind == 'track' and it.sig and it.net != pf['pair']:
                    sp = max(pf['space'] or 0, space_of(it.net, it.cls) or 0)
                    if sp > 0:
                        B.fill(OB, B.buffered(it, sp + w / 2 + M), x0i, y0i, 4, OFF)
                    if self.a.par_pen > 0 and self.a.par_gap > 0:
                        B.fill(OB3, B.buffered(it, self.a.par_gap + w / 2), x0i, y0i, 1, OFF)
                if pf['sp3'] and it.cls in SW_CLS:
                    B.fill(OB, B.buffered(it, self.a.sp3 + w / 2 + M), x0i, y0i, 64, OFF)
            for xl, g in self.xblock:
                if xl == l:
                    B.fill(OB, g.buffer(w / 2 + M, 8), x0i, y0i, 128, OFF)
            for k in B.keepouts:
                if l not in k['layers']:
                    continue
                bko = k['name'].startswith('BKO_') and l == 'B.Cu' and RU.bko_applies(pf['cls'], pf['net'])
                if k['no_tracks'] or bko:
                    B.fill(OB, k['geom'].buffer(w / 2 + M, 8), x0i, y0i, 16, OFF)
            inner = np.zeros((H, W), np.uint8)
            B.fill(inner, B.edge_inner(RU.EDGE + w / 2 + M), x0i, y0i, 1, OFF)
            blocked = ((OB & 1).astype(bool) & ~neck) | ((OB & 2).astype(bool) & neck) | ((OB & 4).astype(bool) & ~neck & ~dhalo) \
                | ((OB & 8).astype(bool) & ~down) | (OB & 16).astype(bool) | ~inner.astype(bool) \
                | ((OB & 64).astype(bool) & ~down) | ((OB & 128).astype(bool) & ~down)
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
            if self.a.par_pen > 0:
                cost[li][OB3.astype(bool) & ~dhalo] += self.a.par_pen
            if self.soft:
                cost[li][(OB & 32).astype(bool)] += self.a.soft_pen
            if self.layer_mul[li] != 1.0:          # detour alternative: bias towards the other layer (fix 5)
                cost[li] *= self.layer_mul[li]
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
            for (vx, vy) in self.xnovia:
                B.fill(VB, Point(vx, vy).buffer(0.12, 8), x0i, y0i, 1, OFF)
            viaok = ((VB == 0) & (inner == 1) & free[0].astype(bool) & free[1].astype(bool))
            if pf['stitch'] and viaok.any():
                viaok &= self.stitchable(pf, x0i, y0i, W, H, OFF, sl, q)
            viaok = viaok.astype(np.uint8)
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

    # ---- terminals (2026-11-02): a connection runs from any terminal of side A to any terminal of side B.
    #   pad : a pad (fresh exit, or branch at its own stub node as before)
    #   via : an existing via of the net (continuation mode); start/arrival at >= 90 deg to the tracks already on it
    #   seg : a lattice node on an existing straight track of the net (continuation mode); perpendicular branch only,
    #         class 'stub' near a pad (stub node) or 'mid' (T-junction in a segment: high start cost, flagged)
    def term_pad(self, p):
        return dict(kind='pad', pad=p, x=p['x'], y=p['y'], name=self.pname(p))

    def lattice_node(self, xn, yn):
        ox, oy = self.off
        if (xn - ox) % GN or (yn - oy) % GN:
            return None
        return ((xn - ox) // GN, (yn - oy) // GN)

    def seg_nodes(self, t):
        """lattice nodes (current origin) on the existing segment t with their perpendicular branch directions"""
        ax, ay = t['a']; bx, by = t['b']; ux, uy = DIRS[t['d']]; ox, oy = self.off
        Ln = max(abs(bx - ax), abs(by - ay))
        if ux == 0:
            if (ax - ox) % GN:
                return []
            t0 = ((oy - ay) * uy) % GN
        elif uy == 0:
            if (ay - oy) % GN:
                return []
            t0 = ((ox - ax) * ux) % GN
        else:
            tx = ((ox - ax) * ux) % GN; ty = ((oy - ay) * uy) % GN
            if tx != ty:
                return []
            t0 = tx
        nx, ny = t['near']; out = []
        for tt in range(t0, Ln + 1, GN):
            if tt * (1.414 if t['d'] & 1 else 1) < 300000 or (Ln - tt) * (1.414 if t['d'] & 1 else 1) < 300000:
                continue
            x = ax + ux * tt; y = ay + uy * tt; xm, ym = x / 1e6, y / 1e6
            dn = math.hypot(xm - nx, ym - ny)
            if dn > self.a.tap_radius:
                continue
            pt = Point(xm, ym)
            if any(g.distance(pt) < 0.05 for g, c in t['pads']):
                continue
            stub = any(g.distance(pt) <= 0.3 + 0.75 for g, c in t['pads'])
            out.append((dn, ((x - ox) // GN, (y - oy) // GN), 'stub' if stub else 'mid'))
        out.sort()
        return [(n, c) for d, n, c in out[:self.a.tap_nodes]]

    def term_starts(self, pf, t, starts, smeta):
        Lo, Ld = pf['Lo'], pf['Ld']
        if t['kind'] == 'pad':
            ex = self.exits(t['pad'], pf)
            for kind, e in self.start_options(t['pad'], pf, ex):
                li = RL.index(e['layer'])
                if kind == 'fresh':
                    starts.append((li, e['node'][0], e['node'][1], e['sdir'], e['cost'])); smeta.append((kind, e, None, t))
                else:
                    L = Ld if e['sdir'] & 1 else Lo; dx, dy = DIRS[e['sdir']]
                    n2 = (e['node'][0] + dx * L, e['node'][1] + dy * L)
                    starts.append((li, n2[0], n2[1], e['sdir'], L * (1.414 if e['sdir'] & 1 else 1) + 4)); smeta.append((kind, e, n2, t))
            return
        if t['kind'] == 'via':
            node = self.lattice_node(t['xn'], t['yn'])
            if node is None:
                return
            used = self.viaused[t['net']][(t['xn'], t['yn'])]
            nodes = [(node, None, [(l, [d for d in range(8) if all(dang(d, u) >= 2 for ll, u in used if ll == l)]) for l in RL])]
            pen = 0.0
        else:
            nodes = [(n, c, [(t['layer'], [(t['d'] + 2) % 8, (t['d'] + 6) % 8])]) for n, c in self.seg_nodes(t)]
        for node, tcls, lds in nodes:
            pen = 0.0 if tcls is None else (self.a.tap_pen_stub if tcls == 'stub' else self.a.tap_pen_mid)
            for l, ds in lds:
                if l == 'B.Cu' and pf['bcu'] == 'no':
                    continue
                li = RL.index(l)
                for d in ds:
                    L = Ld if d & 1 else Lo; dx, dy = DIRS[d]
                    n2 = (node[0] + dx * L, node[1] + dy * L)
                    e = dict(node=node, sdir=d, layer=l, tcls=tcls or 'via')
                    starts.append((li, n2[0], n2[1], d, L * (1.414 if d & 1 else 1) + 4 + pen)); smeta.append(('tap', e, n2, t))

    def term_targets(self, pf, t, targets, tmeta):
        if t['kind'] == 'pad':
            ex = self.exits(t['pad'], pf)
            if self.cont:
                ud = {(u['layer'], u['d']) for u in self.used.get(self.pad_key(t['pad']), [])}
                ex = [e for e in ex if (e['layer'], e['d']) not in ud]
            for e in ex:
                targets.append((RL.index(e['layer']), e['node'][0], e['node'][1], e['arr'])); tmeta.append(('pad', e, t))
            return
        if t['kind'] == 'via':
            node = self.lattice_node(t['xn'], t['yn'])
            if node is None:
                return
            used = self.viaused[t['net']][(t['xn'], t['yn'])]
            for l in RL:
                if l == 'B.Cu' and pf['bcu'] == 'no':
                    continue
                arr = [(a, 1 | 2) for a in range(8) if all(dang((a + 4) % 8, u) >= 2 for ll, u in used if ll == l)]
                if arr:
                    targets.append((RL.index(l), node[0], node[1], arr))
                    tmeta.append(('tap', dict(node=node, layer=l, arr=arr, tcls='via'), t))
            return
        if t['layer'] == 'B.Cu' and pf['bcu'] == 'no':
            return
        for node, tcls in self.seg_nodes(t):
            arr = [((t['d'] + 6) % 8, 1), ((t['d'] + 2) % 8, 1)]
            targets.append((RL.index(t['layer']), node[0], node[1], arr)); tmeta.append(('tap', dict(node=node, layer=t['layer'], arr=arr, tcls=tcls), t))

    def start_options(self, pad, pf, exits):
        """A* start states from a pad: fresh exits, plus T-branches at the stub node of a pad already used by this net"""
        k = self.pad_key(pad); opts = []
        used_dirs = {(u['layer'], u['d']) for u in self.used.get(k, [])}
        for e in exits:
            if (e['layer'], e['d']) not in used_dirs:
                opts.append(('fresh', e))
        nofresh = not opts      # every legal exit direction of the pad is used (e.g. module pads whose inward side is kept out)
        for u in self.used.get(k, []):
            if not (u['single'] or (nofresh and u.get('node') is not None)) or u.get('off') != self.off:
                continue
            ub = (u['sdir'] + 4) % 8  # stub direction from node towards the pad
            back = u['back']         # direction from node along the arriving route
            for l in range(8):
                if dang(l, ub) >= 2 and dang(l, back) >= 2:
                    opts.append(('branch', dict(u, sdir=l)))
        return opts

    def offsets_terms(self, TA, TB):
        """lattice origins to try: put a terminal centre on lattice lines (only coordinate differences matter for exact angles);
        for one pad on each side this is the original order (used origin of A, A, B, mixed)"""
        def c(t): return (int(round(t['x'] * 1e6)) % GN, int(round(t['y'] * 1e6)) % GN)
        out = []
        for t in TA:
            if t['kind'] == 'pad':
                for u in self.used.get(self.pad_key(t['pad']), []):
                    if u.get('single') and u.get('off') is not None and u['off'] not in out:
                        out.append(u['off'])
        ca = [c(t) for t in TA][:2]; cb = [c(t) for t in TB][:2]
        for a in ca:
            for b in cb:
                for o in (a, b, (a[0], b[1]), (b[0], a[1])):
                    if o not in out:
                        out.append(o)
        out = out[:8]
        # continuation: origins that put an existing via centre or segment end of a terminal on the lattice (taps)
        for t in TA + TB:
            o = (t['xn'] % GN, t['yn'] % GN) if t['kind'] == 'via' else (t['a'][0] % GN, t['a'][1] % GN) if t['kind'] == 'seg' else None
            if o is not None and o not in out:
                out.append(o)
        return out[:14]

    def route_terms(self, pf, TA, TB, log):
        cands = []
        for off in self.offsets_terms(TA, TB):
            self.off = off
            st, sm, tg, tm = [], [], [], []
            for t in TA:
                self.term_starts(pf, t, st, sm)
            for t in TB:
                self.term_targets(pf, t, tg, tm)
            score = (bool(st) and bool(tg), sum(int(k != 'fresh') + int(e.get('var') == 'A') for k, e, n2, t in sm) + sum(1 for k, e, t in tm if k != 'pad' or e['var'] == 'A'))
            cands.append((score, off))
        cands.sort(key=lambda t: t[0], reverse=True)
        err = None
        for score, off in cands[:self.a.max_offsets]:
            if not score[0] and err is not None:
                break
            self.off = off
            res, err = self.route_terms_off(pf, TA, TB, log)
            if res is not None:
                return res, None
        return None, err

    def route_terms_off(self, pf, TA, TB, log):
        starts, smeta, targets, tmeta = [], [], [], []
        for t in TA:
            self.term_starts(pf, t, starts, smeta)
        for t in TB:
            self.term_targets(pf, t, targets, tmeta)
        if not starts or not targets:
            return None, 'no exit at %s' % ('/'.join(t['name'] for t in TA) if not starts else '/'.join(t['name'] for t in TB))
        Lo, Ld = pf['Lo'], pf['Ld']
        ox, oy = self.off
        def mm(ix, iy): return ((ix * GN + ox) / 1e6, (iy * GN + oy) / 1e6)
        pts = [mm(s[1], s[2]) for s in starts] + [mm(t[1], t[2]) for t in targets]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        discs_own = [mm(s[1], s[2]) + (0.75,) for s in starts] + [mm(*e['node']) + (0.75,) for k_, e, n2, t in smeta if k_ != 'fresh'] \
            + [mm(t[1], t[2]) + (0.75,) for t in targets]
        discs_halo = [(t['x'], t['y'], 1.2) for t in TA + TB if t['kind'] in ('pad', 'via')]
        res = None
        for margin in self.a.margins:
            bbox = (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)
            win = self.window(pf, bbox, discs_own, discs_halo)
            for kind, e, n2, t in smeta:
                if kind == 'fresh':
                    self.open_corridors(pf, win, e['node'], e['layer'], [e['sdir'], (e['sdir'] + 1) % 8, (e['sdir'] + 7) % 8])
            for k_, e, t in tmeta:
                if k_ == 'pad':
                    self.open_corridors(pf, win, e['node'], e['layer'], [(a + 4) % 8 for a, b in e['arr']])
            # branch / tap starts: forced run must be free
            st2 = []
            for s, (kind, e, n2, t) in zip(starts, smeta):
                if kind != 'fresh':
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
                s0 = path[0]; i0 = next(i for i, s in enumerate(st2) if s is not None and (s[0], s[1], s[2], s[3]) == (s0[0], s0[1], s0[2], s0[3]))
                tl = path[-1]
                j0 = next(j for j, (k_, e, t) in enumerate(tmeta) if RL.index(e['layer']) == tl[0] and e['node'] == (tl[1], tl[2]) and any(d == tl[3] for d, b in e['arr']))
                res = (path, smeta[i0], tmeta[j0])
                break
        if res is None:
            if getattr(self.a, 'debug_png', None):
                nm = pf['net'].strip('/').replace('/', '_')
                self.dump_png(win, sts, targets, '%s/%s_%s-%s.png' % (self.a.debug_png, nm, TA[0]['name'], TB[0]['name']))
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
    def build_copper(self, pf, path, sm, tm):
        kind, eA, n2, tA = sm
        w = pf['w']; ox, oy = self.off
        pieces = []        # (layer, [(x_nm,y_nm), ...], width)
        vias = []
        if kind == 'fresh':
            pieces.append((eA['layer'], list(eA['pts']), eA['width']))
        else:
            pieces.append((eA['layer'], [(eA['node'][0] * GN + ox, eA['node'][1] * GN + oy)], w))
        cur_l = RL[path[0][0]]
        route = [(path[0][1] * GN + ox, path[0][2] * GN + oy)]
        if kind != 'fresh':
            route = [(eA['node'][0] * GN + ox, eA['node'][1] * GN + oy), (path[0][1] * GN + ox, path[0][2] * GN + oy)]
        segs_route = []
        for s in path[1:]:
            l = RL[s[0]]; p = (s[1] * GN + ox, s[2] * GN + oy)
            if l != cur_l:
                vias.append(route[-1]); segs_route.append((cur_l, route, w)); route = [route[-1]]; cur_l = l
            route.append(p)
        segs_route.append((cur_l, route, w))
        pieces += segs_route
        tkind, eB, tB = tm
        if tkind == 'pad':
            pieces.append((eB['layer'], list(reversed(eB['pts'])), eB['width']))
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

    def verify(self, pf, segs, vias, terms=()):
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
                    self._touch = (lj, gj.buffer(0.2 + wj / 2, 8))
                    return False, 'path touches itself'
        for l, a, b, w in segs:
            ok, why = self.seg_ok([(a[0] / 1e6, a[1] / 1e6), (b[0] / 1e6, b[1] / 1e6)], w, l, pf)
            if not ok:
                return False, 'segment %s (%.3f,%.3f)-(%.3f,%.3f): %s' % (l, a[0] / 1e6, a[1] / 1e6, b[0] / 1e6, b[1] / 1e6,
                                                                       why if isinstance(why, str) else '%s %s %s' % (why.kind, why.net, why.cls))
        for v in vias:
            if not self.via_ok_exact(v[0] / 1e6, v[1] / 1e6, pf):
                return False, 'via (%.3f,%.3f)' % (v[0] / 1e6, v[1] / 1e6)
        if self.cont:
            ok, why = self.verify_own(pf, segs, vias, terms)
            if not ok:
                return False, why
        return True, None

    def verify_own(self, pf, segs, vias, terms):
        """continuation mode: new copper may touch existing copper of its own net only at its two ends (the taps):
        inside a terminal pad (+0.3 mm), within 0.6 mm of a terminal via, or within 0.45 mm of a segment tap node"""
        if not segs and not vias:
            return True, None
        allow = []
        for t in terms:
            if t['kind'] == 'pad':
                allow += [mkpolys(pl).buffer(0.3, 8) for l, pl in t['pad']['poly'].items() if mkpolys(pl) is not None]
            elif t['kind'] == 'via':
                allow.append(Point(t['x'], t['y']).buffer(VIA_D / 2 + 0.3, 8))
        if segs:
            for p in (segs[0][1], segs[-1][2]):
                allow.append(Point(p[0] / 1e6, p[1] / 1e6).buffer(0.45, 8))
        A = unary_union(allow) if allow else Polygon()
        net = pf['net']
        new = [(l, LineString([(a[0] / 1e6, a[1] / 1e6), (b[0] / 1e6, b[1] / 1e6)]).buffer(w / 2 + 0.1, 8) if a != b else Point(a[0] / 1e6, a[1] / 1e6).buffer(w / 2 + 0.1, 8)) for l, a, b, w in segs]
        new += [(l, Point(v[0] / 1e6, v[1] / 1e6).buffer(VIA_D / 2 + 0.1, 8)) for v in vias for l in RL]
        for l, g in new:
            for it in self.B.idx[l].query(g.bounds):
                if it.net != net or it.kind not in ('track', 'via') or (it.dyn and isinstance(it.owner, tuple)):
                    continue
                if it.dyn and it.owner == net:
                    continue      # own stitching vias are GND (not this net); safety
                inter = g.intersection(it.geom)
                if inter.is_empty or inter.area < 1e-9:
                    continue
                if not A.buffer(1e-6).contains(inter):
                    c = inter.centroid
                    return False, 'touches own copper at (%.3f,%.3f)' % (c.x, c.y)
        return True, None

    # ---- GND stitching along sensitive B.Cu runs (fix 6, section 14.1)
    def place_run_stitches(self, pf, segs, vias, placed):
        """every point of a stitched net's B.Cu run within --run-stitch/2 (along the run) of a GND via that lies within
        --run-stitch-dist of the track; missing stations are added as GND vias (legality as for via stitches)"""
        if not pf['stitch'] or self.a.run_stitch <= 0:
            return placed, None
        half = self.a.run_stitch / 2.0; Rd = self.a.run_stitch_dist
        placed = list(placed)
        runs = []; cur = None
        for l, a, b, w in segs:
            if l != 'B.Cu':
                cur = None; continue
            pa = (a[0] / 1e6, a[1] / 1e6); pb = (b[0] / 1e6, b[1] / 1e6)
            if cur is not None and cur[-1] == pa:
                cur.append(pb)
            else:
                cur = [pa, pb]; runs.append(cur)
        for run in runs:
            line = LineString(run); Lr = line.length
            if Lr < 1e-6:
                continue
            for it in range(40):
                bd = line.bounds
                c = ((bd[0] + bd[2]) / 2, (bd[1] + bd[3]) / 2); Rq = max(bd[2] - bd[0], bd[3] - bd[1]) / 2 + Rd + 0.1
                gp = self.gnd_pts(c[0], c[1], Rq) + placed
                pos = sorted(line.project(Point(q)) for q in gp if line.distance(Point(q)) <= Rd + 1e-6)
                covered = 0.0; u = None
                for p in pos:
                    if p - half > covered + 1e-6:
                        break
                    covered = max(covered, p + half)
                if covered >= Lr - 1e-6:
                    u = None
                else:
                    u = covered
                if u is None:
                    break
                ok = False
                for tt in np.arange(min(Lr, u + half), max(0.0, u - half) - 1e-9, -0.25):
                    p0 = line.interpolate(max(0.0, tt - 0.05)); p1 = line.interpolate(min(Lr, tt + 0.05)); pt = line.interpolate(tt)
                    dx, dy = p1.x - p0.x, p1.y - p0.y; nn = math.hypot(dx, dy)
                    if nn < 1e-9:
                        continue
                    nx, ny = -dy / nn, dx / nn
                    for dd in (1.0, 1.15, 1.3, 1.45):
                        for sgn in (1, -1):
                            x = round(pt.x + sgn * dd * nx, 4); y = round(pt.y + sgn * dd * ny, 4)
                            if line.distance(Point(x, y)) > Rd + 1e-6:
                                continue
                            if self.gnd_via_ok(x, y, pf, segs, vias, placed):
                                placed.append((x, y)); ok = True; break
                        if ok:
                            break
                    if ok:
                        break
                if not ok:
                    q = line.interpolate(min(Lr, u + 0.5))
                    return None, (q.x, q.y)
                self.stats['run_stitch_vias'] += 1
        return placed, None

    def commit(self, pf, segs, vias, stitches=()):
        for (x, y) in stitches:
            p = (x, y); a = (int(round(x * 1e6)), int(round(y * 1e6)))
            for l in ALLCU:
                it = Item(self.B._id(), 'via', 'Via', 'GND', 'GND', l, Point(p).buffer(VIA_D / 2, 16), dyn=True, owner=pf['net'])
                self.B._add(it); self.netcopper[pf['net']].append(it)
                ih = Item(self.B._id(), 'hole', 'Hole', 'GND', 'GND', l, Point(p).buffer(VIA_DR / 2, 16), dyn=True, owner=pf['net'])
                self.B._add(ih)
            self.out_vias.append(dict(a=a, net='GND', owner=pf['net']))
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

    # ---- one connection: search + exact checks + stitching + pour guard, with re-searches (no commit)
    def route_one(self, pf, TA, TB, clog):
        res, err = self.route_terms(pf, TA, TB, clog['tries'])
        attempt = 0; stitches = []; ok = False; why = err; segs = vias = None
        while res is not None:
            path, sm, tm = res
            segs, vias = self.build_copper(pf, path, sm, tm)
            ok, why = self.verify(pf, segs, vias, (sm[3], tm[2]))
            if ok:
                stitches, bad = self.place_stitches(pf, segs, vias)
                if stitches is None:
                    ok = False; why = 'no GND stitch spot for via (%.3f,%.3f)' % bad; self.xnovia.append(bad); self.stats['stitch_fail'] += 1
            if ok:
                st2, bad = self.place_run_stitches(pf, segs, vias, stitches)
                if st2 is None:
                    ok = False; why = 'no GND stitch spot along B.Cu run at (%.3f,%.3f)' % bad
                    self.xblock.append(('B.Cu', Point(bad).buffer(1.5, 8))); self.stats['run_stitch_fail'] += 1
                else:
                    stitches = st2
            if ok:
                okp, info = self.pour_ok(pf, segs, vias, stitches)
                if not okp:
                    ok = False; why = 'would isolate GND pour ' + info[0]; self.xblock.append((info[1], info[2])); self.stats['pour_reject'] += 1
            elif why == 'path touches itself':
                self.xblock.append(self._touch); self.stats['self_touch'] += 1
            if ok or attempt >= self.a.retries or not (why.startswith('no GND stitch') or why.startswith('would isolate') or why == 'path touches itself'):
                break
            attempt += 1
            clog.setdefault('retries', []).append(why)
            res, err = self.route_terms(pf, TA, TB, clog['tries'])
            if res is None:
                why = 'retry: ' + str(err)
        self.xblock = []; self.xnovia = []
        if res is not None or attempt:
            if not ok:
                return None, 'verify failed: ' + why
            if attempt:
                self.stats['retry_ok'] += 1
            path, sm, tm = res
            L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for l, a, b, w in segs) / 1e6
            p0, p1 = segs[0][1], segs[-1][2]
            om = octi_xy(p0[0] / 1e6, p0[1] / 1e6, p1[0] / 1e6, p1[1] / 1e6)
            return dict(path=path, sm=sm, tm=tm, segs=segs, vias=vias, stitches=stitches, len=L, omin=om, ratio=L / om if om > 1e-6 else 1.0), None
        return None, err

    def route_conn_full(self, pf, TA, TB, clog):
        """fix 5: a path longer than --detour x the octilinear minimum between its ends is re-searched with a cheap via hop and
        with the other layer preferred; the shortest is kept, and if it is still a detour it is accepted (no alternative) and reported"""
        r, err = self.route_one(pf, TA, TB, clog)
        if r is None or self.a.detour <= 0 or r['ratio'] <= self.a.detour:
            return r, err
        alts = [('base', r)]
        if pf['bcu'] != 'no':
            vc = self.a.via_cost
            for var in ('via', 'layer'):
                if var == 'via':
                    self.a.via_cost = min(vc, 0.3)
                else:
                    lf = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for l, a, b, w in r['segs'] if l == 'F.Cu'); lb = r['len'] * 1e6 - lf
                    self.layer_mul = [3.0, 1.0] if lf >= lb else [1.0, 3.0]
                try:
                    r2, e2 = self.route_one(pf, TA, TB, dict(tries=[]))
                finally:
                    self.a.via_cost = vc; self.layer_mul = [1.0, 1.0]
                if r2 is not None:
                    alts.append((var, r2))
                    if r2['ratio'] <= self.a.detour:
                        break
        var, best = min(alts, key=lambda t: t[1]['ratio'])
        clog['detour_alts'] = [(v, round(x['ratio'], 3)) for v, x in alts]
        if best['ratio'] > self.a.detour:
            clog['detour'] = round(best['ratio'], 3); self.stats['detour_accepted'] += 1
            self.detours.append(dict(net=pf['net'], a=clog['a'], b=clog['b'], ratio=round(best['ratio'], 3), len=round(best['len'], 3), omin=round(best['omin'], 3), alts=clog['detour_alts']))
        else:
            clog['detour_fixed'] = var; self.stats['detour_fixed'] += 1
        return best, None

    def commit_conn(self, pf, r, clog):
        self.commit(pf, r['segs'], r['vias'], r['stitches'])
        path = r['path']; kind, eA, n2, tA = r['sm']; tk, eB, tB = r['tm']; net = pf['net']
        if kind == 'fresh':
            self.used.setdefault(self.pad_key(tA['pad']), []).append(dict(eA, back=path[1][3] if len(path) > 1 else eA['sdir']))
        elif kind == 'tap':
            if tA['kind'] == 'via':
                self.viaused[net][(tA['xn'], tA['yn'])].add((eA['layer'], eA['sdir']))
            else:
                self.stats['tap_' + eA['tcls']] += 1; clog['tap_a'] = eA['tcls']
        if tk == 'pad':
            self.used.setdefault(self.pad_key(tB['pad']), []).append(dict(eB, back=(path[-1][3] + 4) % 8))
        elif tB['kind'] == 'via':
            self.viaused[net][(tB['xn'], tB['yn'])].add((eB['layer'], (path[-1][3] + 4) % 8))
        else:
            self.stats['tap_' + eB['tcls']] += 1; clog['tap_b'] = eB['tcls']
        clog['stitch'] = len(r['stitches'])
        clog['status'] = 'ok'; clog['segs'] = len(r['segs']); clog['vias'] = len(r['vias'])
        clog['len'] = round(r['len'], 3); clog['omin'] = round(r['omin'], 3); clog['ratio'] = round(r['ratio'], 3)
        clog['from'] = tA['name']; clog['to'] = tB['name']

    def commit_direct(self, pf, dr, A, B_, clog):
        segs, da, db, l = dr
        self.commit(pf, segs, [])
        self.used.setdefault(self.pad_key(A), []).append(dict(layer=l, d=da, sdir=da, single=False, node=None, back=da))
        self.used.setdefault(self.pad_key(B_), []).append(dict(layer=l, d=db, sdir=db, single=False, node=None, back=db))
        clog['status'] = 'ok'; clog['direct'] = True; clog['segs'] = 1; clog['vias'] = 0
        L = math.hypot(segs[0][2][0] - segs[0][1][0], segs[0][2][1] - segs[0][1][1]) / 1e6
        clog['len'] = round(L, 3); clog['omin'] = round(octi(A, B_), 3); clog['ratio'] = round(L / max(1e-6, octi(A, B_)), 3)

    # ---- chain order
    def chain(self, n, dist, single):
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

    def rereserve(self, net, pads):
        """fix 1: a pad whose connection failed keeps (gets back) its escape reservation; it is released only when its net uses it"""
        if self.a.no_reserve:
            return
        keys = {self.pad_key(p) for p in pads if self.pad_key(p) not in self.used}
        if keys:
            self.reserve([net], only=keys)

    # ---- net
    def route_net(self, net):
        if self.cont:
            return self.route_net_cont(net)
        pf = self.prof(net)
        pads = [p for p in self.B.pads if p['net'] == net and any(l in p['poly'] for l in RL)]
        rec = dict(net=net, cls=pf['cls'], w=pf['w'], pads=len(pads), conns=[], status='', pinstack=0)
        t0 = time.time()
        if len(pads) < 2:
            rec['status'] = 'skip (<2 pads)'; return rec
        for p in pads:
            self.unreserve(self.pad_key(p))
        grp = collections.OrderedDict()
        for p in pads:
            grp.setdefault((p['ref'], p['num']), []).append(p)      # fix 2: same-number pads of one part = one electrical pin
        G = list(grp.values()); rec['pinstack'] = len(pads) - len(G)
        if len(G) < 2:
            rec['status'] = 'skip (pin stack only)'; return rec
        single = []
        for g in G:
            s_all = True
            for p in g:
                self.off = (int(round(p['x'] * 1e6)) % GN, int(round(p['y'] * 1e6)) % GN)
                ex = self.exits(p, pf)
                s_all = s_all and bool(ex) and (all(e['single'] for e in ex) or len({(e['layer'], e['d']) for e in ex}) == 1)
            single.append(s_all)
        order = self.chain(len(G), lambda i, j: min(octi(p, q) for p in G[i] for q in G[j]), single)
        okc = 0
        for i in range(len(order) - 1):
            GA, GB = G[order[i]], G[order[i + 1]]
            clog = dict(a='%s-%s' % (GA[0]['ref'], GA[0]['num']), b='%s-%s' % (GB[0]['ref'], GB[0]['num']), tries=[])
            sa = sorted(GA, key=lambda p: min(octi(p, q) for q in GB)); sb = sorted(GB, key=lambda q: min(octi(p, q) for p in GA))
            TA = [self.term_pad(p) for p in sa]; TB = [self.term_pad(p) for p in sb]
            self.conn_terms[(net, len(rec['conns']))] = (TA, TB)
            dr = None
            for A, B_ in sorted(((p, q) for p in sa for q in sb), key=lambda ab: octi(ab[0], ab[1]))[:4]:
                dr = self.direct(pf, A, B_)
                if dr is not None:
                    break
            if dr is not None:
                self.commit_direct(pf, dr, A, B_, clog); okc += 1; rec['conns'].append(clog)
                continue
            r, err = self.route_conn_full(pf, TA, TB, clog)
            if r is not None:
                self.commit_conn(pf, r, clog); okc += 1
            else:
                clog['status'] = err
            rec['conns'].append(clog)
        rec['status'] = 'complete' if okc == len(order) - 1 else 'PARTIAL %d/%d' % (okc, len(order) - 1)
        rec['t'] = round(time.time() - t0, 2)
        self.rereserve(net, pads)
        return rec

    # ---- continuation mode (fix 3): open connections of an already routed board
    def cont_init(self, drc_path, nets):
        """per net: items (pads, tracks, vias, zone fills) and their connected groups (own union-find; pins with the same
        number of one part are one group, fix 2); exits and via directions used by the existing copper; the open
        connections = DRC unconnected_items of these nets, mapped to (group A, group B)"""
        D = self.B.D; NS = set(nets)
        self.cbase = {}; self.cedges = collections.defaultdict(list)
        items = collections.defaultdict(list)
        for p in self.B.pads:
            if p['net'] in NS:
                lg = {l: mkpolys(pl) for l, pl in p['poly'].items()}
                items[p['net']].append(dict(kind='pad', pad=p, lg={l: g for l, g in lg.items() if g is not None}, x=p['x'], y=p['y']))
        for t in D['tracks']:
            if t['net'] in NS:
                if t['arc'] and t['poly']:
                    g = mkpolys(t['poly'])
                else:
                    g = LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]).buffer(t['w'] / 2, 8) if (t['x1'], t['y1']) != (t['x2'], t['y2']) else Point(t['x1'], t['y1']).buffer(t['w'] / 2, 8)
                if g is not None:
                    items[t['net']].append(dict(kind='track', t=t, lg={t['layer']: g}, x=(t['x1'] + t['x2']) / 2, y=(t['y1'] + t['y2']) / 2, uuid=t.get('uuid')))
        for v in D['vias']:
            if v['net'] in NS:
                g = Point(v['x'], v['y']).buffer(v['d'] / 2, 16)
                items[v['net']].append(dict(kind='via', v=v, lg={l: g for l in ALLCU}, x=v['x'], y=v['y']))
        for z in D['zones']:
            if z['net'] in NS:
                lg = {l: mkpolys(pl) for l, pl in z['fills'].items()}
                lg = {l: g for l, g in lg.items() if g is not None}
                if lg:
                    items[z['net']].append(dict(kind='zone', lg=lg, x=0, y=0))
        for net in NS:
            its = items.get(net, [])
            par = list(range(len(its)))
            def f(i):
                while par[i] != i:
                    par[i] = par[par[i]]; i = par[i]
                return i
            for i in range(len(its)):
                for j in range(i + 1, len(its)):
                    a, b = its[i], its[j]
                    if any(l in b['lg'] and a['lg'][l].intersects(b['lg'][l]) for l in a['lg']):
                        par[f(i)] = f(j)
            stk = {}
            for i, it in enumerate(its):
                if it['kind'] == 'pad':
                    k = (it['pad']['ref'], it['pad']['num'])
                    if k in stk:
                        par[f(i)] = f(stk[k])
                    else:
                        stk[k] = i
            par = [f(i) for i in range(len(its))]
            self.cbase[net] = dict(items=its, parent=par)
            # exits used by existing copper (direction of the track leaving the pad), and track directions at existing vias
            trs = [it for it in its if it['kind'] == 'track' and not it['t']['arc']]
            for it in its:
                if it['kind'] == 'pad':
                    p = it['pad']; k = self.pad_key(p)
                    for tr in trs:
                        t = tr['t']; l = t['layer']
                        if l not in it['lg']:
                            continue
                        g = it['lg'][l]; e1 = g.intersects(Point(t['x1'], t['y1'])); e2 = g.intersects(Point(t['x2'], t['y2']))
                        if e1 == e2:
                            continue
                        dx, dy = (t['x2'] - t['x1'], t['y2'] - t['y1']) if e1 else (t['x1'] - t['x2'], t['y1'] - t['y2'])
                        d8 = int(round(math.atan2(dy, dx) / (math.pi / 4))) % 8
                        for dd in ([d8] if d8 % 2 == 0 else [(d8 + 7) % 8, (d8 + 1) % 8]):
                            self.base_used.setdefault(k, []).append(dict(layer=l, d=dd, sdir=dd, single=False, node=None, back=dd, existing=True))
                elif it['kind'] == 'via':
                    v = it['v']; xn, yn = int(round(v['x'] * 1e6)), int(round(v['y'] * 1e6))
                    s = self.viaused[net][(xn, yn)]
                    for tr in trs:
                        t = tr['t']
                        for (x1, y1, x2, y2) in ((t['x1'], t['y1'], t['x2'], t['y2']), (t['x2'], t['y2'], t['x1'], t['y1'])):
                            if abs(x1 - v['x']) < 1e-4 and abs(y1 - v['y']) < 1e-4 and (x1, y1) != (x2, y2):
                                s.add((t['layer'], int(round(math.atan2(y2 - y1, x2 - x1) / (math.pi / 4))) % 8))
        for k, lst in self.base_used.items():
            self.used[k] = [dict(u) for u in lst]
        self.base_viaused = {n: {k: set(v) for k, v in d.items()} for n, d in self.viaused.items()}
        # open connections from the DRC report
        DR = json.load(open(drc_path))
        rx_pad = re.compile(r'^(?:\S+ )?[Pp]ad (\S+) \[(.+)\] of (\S+) on'); rx_net = re.compile(r'\[(.+)\]')
        nskip = collections.Counter()
        for u in DR.get('unconnected_items', []):
            its2 = u.get('items', [])
            if len(its2) != 2:
                continue
            m = rx_net.search(its2[0]['description']); net = m.group(1) if m else None
            if net not in NS:
                nskip['foreign'] += 1; continue
            ends = []
            for di in its2:
                ends.append(self.cont_locate(net, di, rx_pad))
            ia, ib = ends
            P = self.cbase[net]['parent']
            e = dict(ia=ia, ib=ib, pa=(its2[0]['pos']['x'], its2[0]['pos']['y']), pb=(its2[1]['pos']['x'], its2[1]['pos']['y']),
                     na=self.cont_iname(net, ia), nb=self.cont_iname(net, ib), pinstack=P[ia] == P[ib])
            self.cedges[net].append(e)
        for net in self.cedges:
            self.cedges[net].sort(key=lambda e: math.hypot(e['pa'][0] - e['pb'][0], e['pa'][1] - e['pb'][1]))
        n = sum(len(v) for v in self.cedges.values()); npin = sum(1 for v in self.cedges.values() for e in v if e['pinstack'])
        print('continuation: %d open connections in %d nets (%d pin-stack internal, no routing); %d DRC items of other nets ignored; '
              '%d pads with exits used by existing copper' % (n, len(self.cedges), npin, nskip['foreign'], len(self.base_used)), flush=True)

    def cont_locate(self, net, di, rx_pad):
        its = self.cbase[net]['items']; desc = di['description']; px, py = di['pos']['x'], di['pos']['y']
        m = rx_pad.match(desc)
        if m:
            c = [i for i, it in enumerate(its) if it['kind'] == 'pad' and it['pad']['ref'] == m.group(3) and it['pad']['num'] == m.group(1)]
            if c:
                return min(c, key=lambda i: math.hypot(its[i]['x'] - px, its[i]['y'] - py))
        if desc.startswith('Track') or desc.startswith('Arc'):
            c = [i for i, it in enumerate(its) if it['kind'] == 'track' and it.get('uuid') == di.get('uuid')]
            if c:
                return c[0]
        if desc.startswith('Via'):
            c = [i for i, it in enumerate(its) if it['kind'] == 'via']
            if c:
                return min(c, key=lambda i: math.hypot(its[i]['x'] - px, its[i]['y'] - py))
        pt = Point(px, py)
        return min(range(len(its)), key=lambda i: min(g.distance(pt) for g in its[i]['lg'].values()))

    def cont_iname(self, net, i):
        it = self.cbase[net]['items'][i]
        if it['kind'] == 'pad':
            return self.pname(it['pad'])
        return '%s@%.2f,%.2f' % (it['kind'], it['x'], it['y'])

    def cont_terms(self, net, par, g, near):
        """terminals of group g (existing copper of the net) for a connection towards `near`: nearest pads, vias, segment taps"""
        its = self.cbase[net]['items']; nx, ny = near; pt = Point(nx, ny)
        mem = [it for i, it in enumerate(its) if par(i) == g]
        def dist(it):
            if it['kind'] in ('pad', 'via'):
                return math.hypot(it['x'] - nx, it['y'] - ny)
            return min(gg.distance(pt) for gg in it['lg'].values())
        cand = [(dist(it), it) for it in mem if it['kind'] != 'zone' and (it['kind'] != 'pad' or any(l in it['pad']['poly'] for l in RL))]
        if not cand:
            return []
        dmin = min(d for d, it in cand); K = self.a.cont_terms
        pads = sorted([(d, it) for d, it in cand if it['kind'] == 'pad' and d <= dmin + 3.0], key=lambda t: t[0])[:K]
        vias = sorted([(d, it) for d, it in cand if it['kind'] == 'via' and d <= dmin + 3.0], key=lambda t: t[0])[:2]
        segs = []
        padg = [(it['lg'][l], (it['x'], it['y'])) for it in mem if it['kind'] == 'pad' for l in it['lg']]
        for d, it in sorted([(d, it) for d, it in cand if it['kind'] == 'track' and d <= dmin + 2.0], key=lambda t: t[0]):
            t = it['t']
            if t['arc'] or t['w'] > 0.35 or t['layer'] not in RL:
                continue
            a = (int(round(t['x1'] * 1e6)), int(round(t['y1'] * 1e6))); b = (int(round(t['x2'] * 1e6)), int(round(t['y2'] * 1e6)))
            dx, dy = b[0] - a[0], b[1] - a[1]
            if a == b or not (dx == 0 or dy == 0 or abs(abs(dx) - abs(dy)) <= 0):
                continue
            dd = DIRS.index(((dx > 0) - (dx < 0), (dy > 0) - (dy < 0)))
            ls = LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]); q = ls.interpolate(ls.project(pt))
            segs.append(dict(kind='seg', layer=t['layer'], a=a, b=b, d=dd, x=q.x, y=q.y, near=(nx, ny), net=net,
                             pads=[(gg, c) for gg, c in padg], name='seg@%.2f,%.2f' % (q.x, q.y)))
            if len(segs) >= 3:
                break
        out = [self.term_pad(it['pad']) for d, it in pads]
        for d, it in vias:
            v = it['v']
            out.append(dict(kind='via', x=v['x'], y=v['y'], xn=int(round(v['x'] * 1e6)), yn=int(round(v['y'] * 1e6)), net=net, name='via@%.2f,%.2f' % (v['x'], v['y'])))
        return out + segs

    def route_net_cont(self, net):
        pf = self.prof(net)
        cb = self.cbase.get(net); E = self.cedges.get(net, [])
        pads = [it['pad'] for it in cb['items'] if it['kind'] == 'pad'] if cb else []
        rec = dict(net=net, cls=pf['cls'], w=pf['w'], pads=len(pads), conns=[], status='', pinstack=0, pinstack_conns=[])
        t0 = time.time()
        for p in pads:
            self.unreserve(self.pad_key(p))
        par = list(cb['parent'])
        def f(i):
            while par[i] != i:
                par[i] = par[par[i]]; i = par[i]
            return i
        okc = 0; nconn = 0
        for e in E:
            clog = dict(a=e['na'], b=e['nb'], tries=[])
            if e['pinstack']:
                clog['status'] = 'pin stack (same-number pads of one part: internal, no routing)'
                rec['pinstack'] += 1; rec['pinstack_conns'].append(clog); continue
            nconn += 1
            ga, gb = f(e['ia']), f(e['ib'])
            if ga == gb:
                clog['status'] = 'ok'; clog['merged'] = True; clog['len'] = 0.0; clog['omin'] = 0.0; okc += 1; rec['conns'].append(clog); continue
            TA = self.cont_terms(net, f, ga, e['pb']); TB = self.cont_terms(net, f, gb, e['pa'])
            self.conn_terms[(net, len(rec['conns']))] = (TA, TB)
            if not TA or not TB:
                clog['status'] = 'no terminal'; rec['conns'].append(clog); continue
            dr = None
            for A in [t['pad'] for t in TA if t['kind'] == 'pad'][:2]:
                for B_ in [t['pad'] for t in TB if t['kind'] == 'pad'][:2]:
                    dr = self.direct(pf, A, B_)
                    if dr is not None and not self.verify_own(pf, dr[0], [], [self.term_pad(A), self.term_pad(B_)])[0]:
                        dr = None
                    if dr is not None:
                        break
                if dr is not None:
                    break
            if dr is not None:
                self.commit_direct(pf, dr, A, B_, clog); okc += 1; par[ga] = gb; rec['conns'].append(clog)
                continue
            r, err = self.route_conn_full(pf, TA, TB, clog)
            if r is not None:
                self.commit_conn(pf, r, clog); okc += 1; par[ga] = gb
            else:
                clog['status'] = err
            rec['conns'].append(clog)
        rec['status'] = 'complete' if okc == nconn else 'PARTIAL %d/%d' % (okc, nconn)
        if nconn == 0:
            rec['status'] = 'skip (pin stack only)'
        rec['t'] = round(time.time() - t0, 2)
        self.rereserve(net, pads)
        return rec

    # ---- rip-up and reroute (transactional)
    def net_pads(self, net):
        return [self.pad_key(p) for p in self.B.pads if p['net'] == net]

    def snapshot(self, nets):
        return {n: dict(items=list(self.netcopper.get(n, [])), segs=[s for s in self.out_segs if s['net'] == n], vias=[v for v in self.out_vias if v['net'] == n or v.get('owner') == n],
                        used={k: list(self.used[k]) for k in self.net_pads(n) if k in self.used}, rec=self.recs.get(n),
                        viaused={k: set(v) for k, v in self.viaused.get(n, {}).items()},
                        resv={k: list(self.reserved[k]) for k in self.net_pads(n) if k in self.reserved}) for n in nets}

    def ripup(self, net):
        for it in self.netcopper.pop(net, []):
            self.B.idx[it.layer].remove(it)
        self.out_segs = [s for s in self.out_segs if s['net'] != net]
        self.out_vias = [v for v in self.out_vias if v['net'] != net and v.get('owner') != net]
        holes = [it for l in ALLCU for it in list(self.B.idx[l].items.values()) if it.dyn and it.kind == 'hole' and (it.net == net or it.owner == net)]
        for it in holes:
            self.B.idx[it.layer].remove(it)
        for k in self.net_pads(net):
            self.used.pop(k, None)
            if k in self.base_used:                          # continuation: exits of the locked existing copper stay used
                self.used[k] = [dict(u) for u in self.base_used[k]]
        if net in self.viaused:
            self.viaused[net] = collections.defaultdict(set, {k: set(v) for k, v in self.base_viaused.get(net, {}).items()})

    def restore(self, snap):
        for n, S in snap.items():
            self.ripup(n)
            for it in S['items']:
                self.B._add(it)
                if it.kind == 'via':
                    self.B._add(Item(self.B._id(), 'hole', 'Hole', it.net, it.cls, it.layer, it.geom.centroid.buffer(VIA_DR / 2, 16), dyn=True, owner=it.owner))
            self.netcopper[n] = list(S['items']); self.out_segs += S['segs']; self.out_vias += S['vias']
            self.used.update({k: list(v) for k, v in S['used'].items()})
            self.viaused[n] = collections.defaultdict(set, {k: set(v) for k, v in S['viaused'].items()})
            for k in self.net_pads(n):
                self.unreserve(k)
            for k, its in S['resv'].items():
                for it in its:
                    self.B._add(it)
                self.reserved[k] = list(its)
            if S['rec'] is not None:
                self.recs[n] = S['rec']

    @staticmethod
    def nok(rec):
        return 0 if rec is None else sum(1 for c in rec['conns'] if c['status'] == 'ok')

    @staticmethod
    def lensum(rec):
        if rec is None:
            return 0.0, 0.0
        return (sum(c.get('len', 0.0) for c in rec['conns'] if c['status'] == 'ok'),
                sum(c.get('omin', 0.0) for c in rec['conns'] if c['status'] == 'ok'))

    def complete_short(self, n):
        r = self.recs.get(n)
        if r is None or r['status'] != 'complete':
            return False
        L, O = self.lensum(r)
        return O <= 1e-9 or L / O <= self.a.rrr_keep_ratio

    def conflicts(self, net, TA, TB, candidates):
        """route the failed connection with the copper of `candidates` passable at a penalty; return the nets it would cross"""
        pf = self.prof(net)
        self.soft = set(candidates)
        try:
            res, err = self.route_terms(pf, TA, TB, [])
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
                    if it.kind == 'track' and (pf['space'] or space_of(it.net, it.cls)):
                        c = max(c, pf['space'] or 0, space_of(it.net, it.cls) or 0)
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
        rips = collections.Counter(); T0 = time.time(); new = self.a.rrr_mode == 'new'
        for rnd in range(self.a.ripup):
            improved = False
            for net in nets:
                if time.time() - T0 > self.a.rrr_time:
                    break
                r = self.recs[net]
                if r['status'] == 'complete' or r['status'].startswith('skip'):
                    continue
                fi = next((i for i, c in enumerate(r['conns']) if c['status'] != 'ok'), None)
                if fi is None or (net, fi) not in self.conn_terms:
                    continue
                fc = r['conns'][fi]; TA, TB = self.conn_terms[(net, fi)]
                if not TA or not TB:
                    continue
                cands = [n for n in nets if n != net and self.netcopper.get(n) and rips[n] < self.a.ripup and not (new and self.complete_short(n))]
                hit = self.conflicts(net, TA, TB, cands)
                entry = dict(round=rnd, net=net, conn='%s>%s' % (fc['a'], fc['b']), conflicts=sorted(hit) if hit is not None else None)
                if not hit or len(hit) > self.a.rrr_max:
                    entry['result'] = 'no candidate set'; self.rrr_log.append(entry); self.stats['rrr_no_set'] += 1; continue
                group = [net] + sorted(hit)
                before = sum(self.nok(self.recs.get(n)) for n in group)
                lb = [self.lensum(self.recs.get(n)) for n in group]; rb = sum(x for x, y in lb) / max(1e-9, sum(y for x, y in lb))
                snap = self.snapshot(group)
                for n in group:
                    self.ripup(n)
                for n in group:
                    self.recs[n] = self.route_net(n)
                after = sum(self.nok(self.recs.get(n)) for n in group)
                la = [self.lensum(self.recs.get(n)) for n in group]; ra = sum(x for x, y in la) / max(1e-9, sum(y for x, y in la))
                entry.update(ratio_before=round(rb, 3), ratio_after=round(ra, 3))
                keep = after > before and (not new or sum(y for x, y in lb) <= 1e-9 or ra <= rb + self.a.rrr_ratio_tol)
                if keep:
                    entry['result'] = 'kept %d -> %d' % (before, after); improved = True; self.stats['rrr_kept'] += 1
                    for n in hit:
                        rips[n] += 1
                else:
                    entry['result'] = 'rolled back %d -> %d' % (before, after); self.stats['rrr_rolled_back'] += 1
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
    ap.add_argument('--module-keepout', default='U1:0.5', help='REF:shrink[,..] no F.Cu track/via inside the pad rectangle of REF shrunk by shrink mm ("" = off)')
    ap.add_argument('--halo', type=float, default=0.6, help='edge gap of AUDIO/I2S_CLK/USB/AUD I2C tracks to other signal tracks outside neck areas (0 = off)')
    ap.add_argument('--par-gap', type=float, default=0.4, help='near-parallel band: edge gap to another signal net track that costs extra')
    ap.add_argument('--par-pen', type=float, default=0.5, help='extra cost per cell inside the near-parallel band (0 = off)')
    ap.add_argument('--sens-bcu', default='gnd', choices=['no', 'gnd', 'yes'], help='B.Cu policy of sensitive nets without an explicit bcu= (gnd = LA2)')
    ap.add_argument('--stitch', type=float, default=1.5, help='GND stitching via within this distance of every sensitive-net via (0 = off)')
    ap.add_argument('--sp3', type=float, default=2.0, help='SP3 distance of FB/COMP/ILIM/PROG/TS/EN/CE nets of switchers to SWITCH/BOOT copper (0 = off)')
    ap.add_argument('--pour-guard', type=int, default=1, help='reject connections that cut an anchored F/B.Cu GND fill piece (0 = off)')
    ap.add_argument('--retries', type=int, default=2, help='re-searches per connection after self-touch / no stitch spot / pour cut')
    ap.add_argument('--allow-pour-flag', action='store_true', help='route on top of an earlier stage flagged by route_oct_pourcheck.py')
    ap.add_argument('--rrr-mode', default='new', choices=['new', 'old'], help='new (fix 4): rip only same-stage nets that are not complete-and-short; keep only if connections increase and the length ratio does not worsen')
    ap.add_argument('--rrr-keep-ratio', type=float, default=1.2, help='a complete net with routed length / octilinear minimum <= this is never ripped (rrr-mode new)')
    ap.add_argument('--rrr-ratio-tol', type=float, default=0.0, help='allowed increase of the ripped group length ratio (rrr-mode new)')
    ap.add_argument('--detour', type=float, default=2.5, help='fix 5: path length limit as a multiple of the octilinear minimum between its ends; longer paths are re-searched (via hop, other layer) and reported (0 = off)')
    ap.add_argument('--run-stitch', type=float, default=6.0, help='fix 6: max spacing of GND vias along B.Cu runs of stitched nets (0 = off)')
    ap.add_argument('--run-stitch-dist', type=float, default=1.5, help='fix 6: such a GND via lies within this distance of the track')
    ap.add_argument('--cont-drc', default=None, help='continuation mode (fix 3): DRC JSON of the input board; only its unconnected items of the net file nets are routed, all copper stays')
    ap.add_argument('--first-refs', default='', help='REF[,REF]: inside the stage, nets with a pad on these parts first (owner decision: U1,J8 in S3)')
    ap.add_argument('--cont-terms', type=int, default=3, help='continuation: max pad terminals per side')
    ap.add_argument('--tap-pen-stub', type=float, default=10.0, help='continuation: start cost (cells) of a branch at a stub node of existing copper')
    ap.add_argument('--tap-pen-mid', type=float, default=200.0, help='continuation: start cost (cells) of a T-junction in the middle of an existing segment (flagged)')
    ap.add_argument('--tap-radius', type=float, default=3.0, help='continuation: segment taps within this distance of the DRC anchor, mm')
    ap.add_argument('--tap-nodes', type=int, default=16, help='continuation: max tap nodes per segment')
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
    names = list(stages)
    if a.cont_drc:
        # continuation (fix 3): C0 = every copper item of the first input board (locked); each stage records the items it added
        if 'C0' not in man['stages']:
            if man['stages']:
                raise SystemExit('manifest %s is not a continuation manifest' % a.manifest)
            hh, nn = LK.hash_strings(list(LK.item_strings(a.board).elements()))
            man = dict(mode='continue', stages=dict(C0=dict(stage='C0', note='all copper of the continuation input board (locked)', input_board=os.path.abspath(a.board),
                                                            copper_sha256=hh, copper_items=nn, stitch_vias=[])))
            print('continuation lock C0 created:', nn, 'items', flush=True)
        for st in names[names.index(a.stage):]:
            man['stages'].pop(st, None)                      # re-run of this stage: later entries are stale
        lk = LK.cont_lock(a.board, man)
        bad = [k for k, v in lk.items() if not v['ok']]
        if bad:
            raise SystemExit('LOCK VIOLATION (continuation): %s' % lk)
        print('lock ok (continuation):', lk, flush=True)
        for st, info in man['stages'].items():
            pc = info.get('pour_check')
            if pc and not pc.get('ok', True) and not a.allow_pour_flag:
                raise SystemExit('stage %s is flagged by the pour check (%s); fix it or pass --allow-pour-flag' % (st, '; '.join(pc.get('new', [])[:3])))
    else:
        # lock check of earlier stages
        for st in names[:names.index(a.stage)]:
            if st not in man['stages']:
                raise SystemExit('earlier stage %s not in manifest; route it first' % st)
            h, n = LK.copper_hash(a.board, stages[st])
            if h != man['stages'][st]['copper_sha256']:
                raise SystemExit('LOCK VIOLATION: copper of stage %s changed (hash %s != %s)' % (st, h, man['stages'][st]['copper_sha256']))
            print('lock ok', st, n, 'items', flush=True)
            sv = man['stages'][st].get('stitch_vias', [])
            if sv:
                have = {t[2] for t in LK.copper_items(a.board, ['GND']) if t[0] == 'via'}
                miss = [x for x in sv if x not in have]
                if miss:
                    raise SystemExit('LOCK VIOLATION: %d GND stitching vias of stage %s missing, e.g. %s' % (len(miss), st, miss[0]))
                print('lock ok', st, len(sv), 'stitching vias', flush=True)
            pc = man['stages'][st].get('pour_check')
            if pc and not pc.get('ok', True) and not a.allow_pour_flag:
                raise SystemExit('stage %s is flagged by the pour check (%s); fix it or pass --allow-pour-flag' % (st, '; '.join(pc.get('new', [])[:3])))
    core = load_core(workdir)
    HALO[0] = a.halo
    B = Board(a.geo, a.dru, a.pro, core, a)
    R = Router(B, a, opts)
    later = [n for st in names[names.index(a.stage):] for n in stages[st]]
    stage_nets = list(stages[a.stage])
    if a.cont_drc:
        R.cont = True
        R.cont_init(a.cont_drc, later)
        later = [n for n in later if R.cedges.get(n)]
        stage_nets = [n for n in stage_nets if R.cedges.get(n)]
    if a.first_refs:
        fr = set(a.first_refs.split(','))
        hasref = {n for n in stage_nets if any(p['net'] == n and p['ref'] in fr for p in B.pads)}
        stage_nets = [n for n in stage_nets if n in hasref] + [n for n in stage_nets if n not in hasref]
        print('first inside the stage (pads on %s): %s' % (a.first_refs, ' '.join(n for n in stage_nets if n in hasref)), flush=True)
    if not a.no_reserve:
        print('reserved escapes:', R.reserve(later), flush=True)
    R.pending = set(later)
    R.route_stage(stage_nets)
    recs = [R.recs[n] for n in stage_nets]
    for r in recs:
        if not r['status'].startswith('complete'):
            print('  final %-28s %s' % (r['net'], r['status']), flush=True)
    write_board(a.board, a.out, R.out_segs, R.out_vias)
    # detours of the final copper (R.detours also lists attempts that a rip-up later rolled back)
    R.detours = [dict(net=r['net'], a=c['a'], b=c['b'], ratio=c['detour'], len=c.get('len'), omin=c.get('omin'), alts=c.get('detour_alts'))
                 for r in recs for c in r['conns'] if c['status'] == 'ok' and c.get('detour')]
    nconn = sum(len(r['conns']) for r in recs); okc = sum(1 for r in recs for c in r['conns'] if c['status'] == 'ok')
    stv = ['%.6f %.6f' % (v['a'][0] / 1e6, v['a'][1] / 1e6) for v in R.out_vias if v.get('owner')]
    lens = [c['ratio'] for r in recs for c in r['conns'] if c['status'] == 'ok' and c.get('ratio')]
    summ = dict(stage=a.stage, mode='continue' if a.cont_drc else 'stage', nets=stage_nets, complete_nets=sum(1 for r in recs if r['status'] == 'complete'),
                conns=nconn, conns_ok=okc, pinstack=sum(r.get('pinstack', 0) for r in recs),
                segments=len(R.out_segs), vias=len(R.out_vias) - len(stv), stitch_vias=len(stv), runtime_s=round(time.time() - T0, 1),
                stats=dict(R.stats), detours=R.detours, conn_ratio_max=max(lens) if lens else None, sp3_nets=B.sp3, module_keepout=B.mod_ko,
                params={k: getattr(a, k) for k in ('via_cost', 'turn_cost', 'dir_pen', 'bcu_cost', 'b_island', 'b_void', 'f_void', 'pair_attract', 'pair_avoid', 'margins', 'max_exp', 'no_reserve', 'pad_pen', 'pad_halo', 'max_offsets', 'hweight', 'hweight_cells', 'ripup', 'rrr_max', 'rrr_time', 'soft_pen', 'module_keepout', 'halo', 'par_gap', 'par_pen', 'sens_bcu', 'stitch', 'sp3', 'pour_guard', 'retries',
                                                 'rrr_mode', 'rrr_keep_ratio', 'rrr_ratio_tol', 'detour', 'run_stitch', 'run_stitch_dist', 'cont_drc', 'first_refs', 'cont_terms', 'tap_pen_stub', 'tap_pen_mid', 'tap_radius', 'tap_nodes')})
    ent = dict(summ, input_board=os.path.abspath(a.board), output_board=os.path.abspath(a.out),
               output_sha256=hashlib.sha256(open(a.out, 'rb').read()).hexdigest(), stitch_vias=stv, dru_sha256=RU.check_dru(a.dru)[1],
               pro_sha256=hashlib.sha256(open(a.pro, 'rb').read()).hexdigest())
    if a.cont_drc:
        added = LK.item_strings(a.out) - LK.item_strings(a.board)
        ent['added_items'] = sorted(added.elements()); ent['copper_sha256'], ent['copper_items'] = LK.hash_strings(ent['added_items'])
    else:
        ent['copper_sha256'], ent['copper_items'] = LK.copper_hash(a.out, stages[a.stage])
    man['stages'][a.stage] = ent
    json.dump(man, open(a.manifest, 'w'), indent=1)
    if a.log:
        json.dump(dict(summary=summ, nets=recs, rrr=R.rrr_log), open(a.log, 'w'), indent=1)
    print('STAGE %s: nets complete %d/%d, connections %d/%d (+%d pin-stack internal), %d segments, %d vias (+%d GND stitching), %d detours > %.1fx accepted, %.1f s%s' % (
        a.stage, summ['complete_nets'], len(stage_nets), okc, nconn, summ['pinstack'], len(R.out_segs), summ['vias'], len(stv), len(R.detours), a.detour, summ['runtime_s'],
        '' if okc == nconn else '  PARTIAL'), flush=True)


if __name__ == '__main__':
    main()
