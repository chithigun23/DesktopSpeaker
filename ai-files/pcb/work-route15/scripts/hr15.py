#!/usr/bin/env python3
"""hr.py : scripted hand-route helper for RT-4 (venv python: numpy + shapely). Not the router: a local, single-connection,
exact-octilinear lattice search used to draft each hand edit; every result is gated by kicad-cli DRC and the independent checks.

  hr.py JOBS.json  -> writes the plan (seg_add / via_add, edit.py format) named in JOBS['out_plan'] and a log.

JOBS = {"geo": BOARD.geo.json, "out_plan": PLAN.json, "base_plan": optional plan to merge (deletions etc.),
        "jobs": [ {net, from, to, layers 'F'|'B'|'FB', w, wn (neck width), dirs_from, dirs_to ('E','NE',.. or '*'),
                   margin, via_cost, turn, run (bend spacing mm), sp3 (mm, 0=off), halo (0.6), stitch (1.5), fine_via (bool),
                   tol_own (cells inside own pads always passable), allow_gnd_pour (bool, default true)} ]}
  from / to : "REF-NUM" (pad) or [x, y, "F.Cu"] (a point on own copper) ; to may be a list.
Geometry: lattice pitch 0.05 mm anchored at the start point; moves are the 8 lattice directions; only 45-degree bends; after
every bend or via the next run is at least `run` mm (falls back to 0.4 mm if `run` fails); pad exits/entries straight >= 0.3 mm
beyond the pad edge. Clearances: route_oct_rules snapshot (strict class max) outside neck regions, neck values inside;
hole 0.25, edge 0.5; BKO_* / module / antenna / J7 keep-outs; halo 0.6 for AUDIO/I2S/USB/AUD I2C; sensitive B.Cu only over In2 GND.
Each routed connection is added to the in-memory board so later jobs in the same file see it."""
import sys, os, json, math, heapq, time, collections
import numpy as np
import shapely
from shapely.geometry import Polygon, MultiPolygon, LineString, Point, box
from shapely.ops import unary_union
from shapely.strtree import STRtree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules_snap as RU
import re as _re
_DRU = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'RT-15.kicad_dru')).read()  # RT-10: rule 11 + rule 21
_m = _re.search(r'\(rule in2_power_only.*?\(condition "([^"]*)"', _DRU, _re.S)
IN2_NETS = set(_re.findall(r"A.NetName != '([^']+)'", _m.group(1)))
_m21 = _re.search(r'\(rule rt10_in2_slow\b.*?\(condition "([^"]*)"', _DRU, _re.S)
IN2_NETS |= set(_re.findall(r"A.NetName == '([^']+)'", _m21.group(1)))
_m22 = _re.search(r'\(rule rt12_in2_slow\b.*?\(condition "([^"]*)"', _DRU, _re.S)     # RT-12: rule 22 additions
if _m22: IN2_NETS |= set(_re.findall(r"A.NetName == '([^']+)'", _m22.group(1)))
IN2_CLS = {'POWER_HI', 'PVDD', 'PWR_5V', 'PWR_3V', 'GND'}

G = 0.05
M = 0.036            # sweep margin for diagonal steps
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
DNAME = {'E': 0, 'SE': 1, 'S': 2, 'SW': 3, 'W': 4, 'NW': 5, 'N': 6, 'NE': 7}
SENS_CLS = {'USB', 'I2S_CLK', 'AUDIO'}
SENS_NETS = {'/AUD_SDA', '/AUD_SCL'}
FORBID_ISLAND_CLS = {'POWER_HI', 'PVDD', 'SPK_OUT'}
SWCLS = {'SWITCH', 'BOOT'}
NECK_REFS = ['U4', 'U6', 'U7', 'U8', 'U9', 'U11', 'U14', 'U15', 'U19', 'U24', 'U25', 'U3', 'U5', 'U10', 'U20', 'J1']
CLASS_W = {'Default': 0.25, 'SIGNAL': 0.25, 'I2C': 0.3, 'AUDIO': 0.3, 'I2S_CLK': 0.25, 'USB': 0.25, 'BOOT': 0.3, 'PWR_LOCAL': 0.4, 'PWR_3V': 0.5, 'GND': 0.5}


def mk(plist):
    out = []
    for rings in plist:
        if len(rings[0]) < 3: continue
        p = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 3])
        if not p.is_valid: p = p.buffer(0)
        if not p.is_empty: out.append(p)
    if not out: return None
    return out[0] if len(out) == 1 else unary_union(out)


class Item:
    __slots__ = ('geom', 'net', 'cls', 'typ', 'layer', 'name', 'hole')

    def __init__(s, geom, net, cls, typ, layer, name='', hole=None):
        s.geom, s.net, s.cls, s.typ, s.layer, s.name, s.hole = geom, net, cls, typ, layer, name, hole


class Board:
    def __init__(self, geo):
        D = json.load(open(geo)); self.D = D
        self.netcls = D['netclass']
        self.items = collections.defaultdict(list)          # layer -> [Item]
        self.holes = []                                      # (Point geom buffered to drill/2, net, plated)
        self.pads = {}
        for p in D['pads']:
            key = '%s-%s' % (p['ref'], p['num'])
            for L, pl in p['poly'].items():
                g = mk(pl)
                if g is None: continue
                self.items[L].append(Item(g, p['net'], p['cls'], 'Pad', L, key))
                self.pads.setdefault(key, {})[L] = g
            self.pads.setdefault(key, {})['_c'] = (p['x'], p['y']); self.pads[key]['_net'] = p['net']
            if p['drill']:
                self.holes.append((Point(p['x'], p['y']).buffer(max(p['drill']) / 2, 16), p['net'], p['attr'] != 'NPTH'))
        for t in D['tracks']:
            g = mk(t['poly']) if t['arc'] and t['poly'] else LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]).buffer(t['w'] / 2, 16)
            if g.is_empty: g = Point(t['x1'], t['y1']).buffer(t['w'] / 2, 16)
            self.items[t['layer']].append(Item(g, t['net'], t['cls'], 'Track', t['layer'], t['uuid']))
        for v in D['vias']:
            g = Point(v['x'], v['y']).buffer(v['d'] / 2, 16)
            for L in ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'):
                self.items[L].append(Item(g, v['net'], v['cls'], 'Via', L))
            self.holes.append((Point(v['x'], v['y']).buffer(v['drill'] / 2, 16), v['net'], True))
        self.zfill = collections.defaultdict(list)
        for z in D['zones']:
            for L, pl in z['fills'].items():
                g = mk(pl)
                if g is None: continue
                self.items[L].append(Item(g, z['net'], z['cls'] or self.netcls.get(z['net'], ''), 'Zone', L, z['name'] or ('TD' if z['teardrop'] else '')))
                self.zfill[L].append((z['net'], g))
        self.outline = mk(D['outline'])
        self.edge = self.outline.exterior
        self.areas = D['areas']
        neck = [mk(a['outline']) for a in D['areas'] if a['name'].startswith('NECK_') and a['name'] != 'NECK_U2_USB']
        for r in NECK_REFS:
            c = D['courtyard'].get(r)
            if c and c['poly'].get('F'): neck.append(mk(c['poly']['F']))
        self.neck = unary_union([g for g in neck if g is not None])
        self.in2gnd = unary_union([g for n, g in self.zfill['In2.Cu'] if n == 'GND'])
        self.in1gnd = unary_union([g for n, g in self.zfill['In1.Cu'] if n == 'GND'])
        self.in2forbid = unary_union([g for n, g in self.zfill['In2.Cu'] if self.netcls.get(n) in FORBID_ISLAND_CLS])
        self.gnd12 = self.in1gnd.intersection(self.in2gnd).buffer(-0.31)
        # BM83 module keep-out (U1 pad rectangle shrunk 0.5, own pads +0.15 cut out)
        pp = [g for k, d in self.pads.items() if k.startswith('U1-') and 'F.Cu' in d for g in [d['F.Cu']]]
        bd = unary_union(pp).bounds
        self.modko = box(bd[0] + 0.5, bd[1] + 0.5, bd[2] - 0.5, bd[3] - 0.5).difference(unary_union([q.buffer(0.15) for q in pp]))
        # IC body keep-out (F.Cu, vias): convex hull of each U-part's pad centres shrunk 0.45 mm (no copper under a package body)
        from shapely.geometry import MultiPoint
        ub = []; self.icb = {}
        refs = sorted({k.split('-')[0] for k in self.pads if k.startswith('U') and k.split('-')[0] != 'U1'})
        for r in refs:
            cs = [d['_c'] for k, d in self.pads.items() if k.split('-')[0] == r and 'F.Cu' in d]
            if len(cs) >= 6:
                h = MultiPoint(cs).convex_hull.buffer(-0.45)
                if not h.is_empty: ub.append(h); self.icb[r] = h
        self.icbody = unary_union(ub) if ub else None
        self.rebuild()

    def rebuild(self):
        self.tree = {L: STRtree([it.geom for it in its]) for L, its in self.items.items()}
        self.htree = STRtree([h[0] for h in self.holes])

    def query(self, L, g):
        its = self.items[L]
        return [its[i] for i in self.tree[L].query(g)]

    def add_track(self, L, net, w, a, b):
        g = LineString([a, b]).buffer(w / 2, 16)
        self.items[L].append(Item(g, net, self.netcls.get(net, ''), 'Track', L, 'new'))

    def add_via(self, net, x, y, d, dr):
        g = Point(x, y).buffer(d / 2, 16)
        for L in ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'):
            self.items[L].append(Item(g, net, self.netcls.get(net, ''), 'Via', L))
        self.holes.append((Point(x, y).buffer(dr / 2, 16), net, True))


def contains_grid(geom, X, Y):
    if geom is None or geom.is_empty: return np.zeros(X.shape, bool)
    return shapely.contains_xy(geom, X, Y) | shapely.intersects_xy(geom.boundary, X, Y)


class Job:
    def __init__(self, B, J):
        self.B, self.J = B, J
        self.net = J['net']; self.cls = B.netcls.get(self.net, 'Default')
        self.w = J.get('w', CLASS_W.get(self.cls, 0.25))
        self.wn = J.get('wn', 0.25 if self.cls in SENS_CLS else 0.2)
        self.sens = self.cls in SENS_CLS or self.net in SENS_NETS
        self.layers = [{'F': 'F.Cu', 'B': 'B.Cu', 'I': 'In2.Cu'}[c] for c in J.get('layers', 'FB')]
        if 'In2.Cu' in self.layers and not (self.net in IN2_NETS or self.cls in IN2_CLS): self.layers.remove('In2.Cu')
        self.softbox = unary_union([box(*b) for b in J['soft_box']]) if J.get('soft_box') else None
        # RT-10: 'ic_allow' = refs whose package body may carry F.Cu tracks / vias (U3 LQFP-64 has no exposed pad)
        al = set(J.get('ic_allow', []))
        self.icbody = unary_union([g for r, g in B.icb.items() if r not in al]) if al else B.icbody

    def net_targets(self, S):
        """own-net copper (pads, tracks, vias on F/B) not connected to the start item -> target endpoints"""
        B = self.B; its = []
        for L in ('F.Cu', 'B.Cu'):
            for it in B.items[L]:
                if it.net == self.net and it.typ in ('Pad', 'Track', 'Via'):
                    its.append((L, it))
        n = len(its); adj = [[] for _ in range(n)]
        tr = STRtree([it.geom for L, it in its])
        for a, (La, ia) in enumerate(its):
            for b in tr.query(ia.geom.buffer(0.001)):
                Lb, ib = its[b]
                if b != a and (La == Lb or (ia.typ == 'Via' and ib.typ == 'Via' and ia.geom.equals(ib.geom)) or (ia.typ == 'Pad' and ib.typ == 'Pad' and ia.name == ib.name)) and ia.geom.intersects(ib.geom):
                    adj[a].append(b)
        seed = [k for k, (L, it) in enumerate(its) if L in S['reg'] and it.geom.intersects(S['reg'][L])]
        seen = set(seed); st = list(seed)
        while st:
            a = st.pop()
            for b in adj[a]:
                if b not in seen: seen.add(b); st.append(b)
        out = []
        for k, (L, it) in enumerate(its):
            if k in seen: continue
            if it.typ == 'Pad':
                out.append(dict(key=it.name, c=B.pads[it.name]['_c'], reg={L: it.geom}))
            else:
                c = it.geom.centroid
                out.append(dict(key=None, c=(c.x, c.y), reg={L: it.geom.buffer(-0.05) if it.geom.area > 0.05 else it.geom}))
        return out

    def cneck(self, it):
        if self.J.get('neck_drc'):      # rule-file value inside neck areas (neck_ic is the last matching rule): 0.2, USB pair 0.15
            return 0.15 if (self.cls == 'USB' and it.cls == 'USB') else self.J.get('neck_val', 0.2)
        return RU.clr_neck(self.cls, self.net, it.cls, it.typ)

    def endpoint(self, spec):
        """-> dict(c=(x,y), layer list, region geom per layer, pad key or None)"""
        if isinstance(spec, str):
            d = self.B.pads[spec]
            return dict(key=spec, c=d['_c'], reg={L: d[L] for L in ('F.Cu', 'B.Cu') if L in d})
        x, y, L = spec[0], spec[1], spec[2]
        r = spec[3] if len(spec) > 3 else 0.08
        if L == 'via':      # RT-8: start/end on an existing via (all routing layers of the job)
            return dict(key=None, c=(x, y), reg={LL: Point(x, y).buffer(r, 16) for LL in self.layers})
        return dict(key=None, c=(x, y), reg={L: Point(x, y).buffer(r, 16)})

    def run(self):
        B, J = self.B, self.J
        S = self.endpoint(J['from'])
        if J['to'] == 'NET':
            Ts = self.net_targets(S)
            R = J.get('tgt_radius', 12.0)
            Ts = [t for t in Ts if math.dist(t['c'], S['c']) <= R or (t['key'] and t['key'] in J.get('tgt_keys', []))]
            if J.get('tgt_near'):     # RT-8: only targets with copper within r of (x, y)
                tx, ty, tr = J['tgt_near']
                Ts = [t for t in Ts if any(g.distance(Point(tx, ty)) <= tr for g in t['reg'].values())]
            if not Ts: return None
        else:
            Ts = [self.endpoint(t) for t in (J['to'] if isinstance(J['to'], list) and not isinstance(J['to'][0], (int, float)) else [J['to']])]
        sx, sy = S['c']
        pts = [S['c']] + [t['c'] for t in Ts]
        mg = J.get('margin', 3.0)
        x0 = min(p[0] for p in pts) - mg; x1 = max(p[0] for p in pts) + mg
        y0 = min(p[1] for p in pts) - mg; y1 = max(p[1] for p in pts) + mg
        if 'box' in J: x0, y0, x1, y1 = J['box']
        i0 = int(math.floor((x0 - sx) / G)); i1 = int(math.ceil((x1 - sx) / G))
        j0 = int(math.floor((y0 - sy) / G)); j1 = int(math.ceil((y1 - sy) / G))
        self.i0, self.j0 = i0, j0
        NX, NY = i1 - i0 + 1, j1 - j0 + 1
        if NX * NY > J.get('max_cells', 900000):
            print('   window too large %dx%d' % (NX, NY), flush=True); return None
        xs = sx + G * np.arange(i0, i1 + 1); ys = sy + G * np.arange(j0, j1 + 1)
        X, Y = np.meshgrid(xs, ys, indexing='ij')
        self.X, self.Y, self.NX, self.NY = X, Y, NX, NY
        win = box(xs[0] - 3, ys[0] - 3, xs[-1] + 3, ys[-1] + 3)
        inneck = contains_grid(B.neck, X, Y) if J.get('neck', True) else np.zeros(X.shape, bool)
        self.inneck = inneck
        own_pad_reg = unary_union([g for k, d in B.pads.items() if d['_net'] == self.net for L, g in d.items() if L in ('F.Cu', 'B.Cu')])
        near_own = contains_grid(own_pad_reg.buffer(1.2), X, Y)
        near_own75 = contains_grid(own_pad_reg.buffer(0.75), X, Y)
        P = {}; CF = {}
        for L in self.layers:
            P[L] = self.passable(L, win, X, Y, inneck, near_own, near_own75)
            # own endpoint pads always passable well inside the pad
            for E in [S] + Ts:
                if L in E['reg']:
                    inner = E['reg'][L].buffer(-min(self.wn, self.w) / 2 + 0.01) if E['key'] else E['reg'][L]
                    P[L] |= contains_grid(inner, X, Y) & ~self.blk_np[L]
            cf = np.ones(X.shape)
            if L == 'In2.Cu':
                cf *= J.get('in2_cost', 1.6)
                # RT-10: an In2 signal track cuts the In2 GND under B.Cu signal tracks (B over void): cost under them
                bsh = [it.geom for it in B.query('B.Cu', win) if it.typ == 'Track' and it.net != self.net and it.net != 'GND' and it.geom.area < 50]
                if bsh: cf *= np.where(contains_grid(unary_union(bsh).buffer(self.w / 2 + 0.3, 8), X, Y), J.get('in2_bshadow', 4.0), 1.0)
            elif L == 'B.Cu':
                cf *= J.get('bcu_cost', 1.3)
                if not self.sens:
                    cf *= np.where(contains_grid(B.in2gnd, X, Y), 1.0, J.get('void_cost', 3.0))
            else:
                cf *= np.where(contains_grid(B.in1gnd, X, Y), 1.0, 2.0)
            CF[L] = cf
        VOK = self.via_ok(win, X, Y, inneck) if len(self.layers) >= 2 else np.zeros(X.shape, bool)
        self.P, self.CF, self.VOK = P, CF, VOK
        # targets
        TG = {L: np.zeros(X.shape, bool) for L in self.layers}
        for T in Ts:
            for L, g in T['reg'].items():
                if L in TG:
                    TG[L] |= contains_grid(g.buffer(-0.02) if T['key'] else g, X, Y)
        self.TG = TG
        Lix = {L: k for k, L in enumerate(self.layers)}
        res = None
        for run_mm in [J.get('run', 0.75), 0.4] if J.get('run', 0.75) > 0.4 else [0.4]:
            res = self.astar(S, Ts, Lix, run_mm, J)
            if res: break
        if J.get('dbg'):
            self.dump(J['dbg'])
        if not res:
            return None
        return self.emit(res, S, Ts)

    def dump(self, path):
        import zlib, struct
        H, W = self.NY, self.NX
        img = np.zeros((H, W, 3), np.uint8)
        L = self.layers
        if 'F.Cu' in L: img[..., 0] = np.where(self.P['F.Cu'].T, 200, 40)
        if 'B.Cu' in L: img[..., 2] = np.where(self.P['B.Cu'].T, 200, 40)
        img[..., 1] = np.where(self.VOK.T, 160, 0)
        for (i, j) in getattr(self, 'visited', []):
            img[j, i] = (255, 255, 0)
        raw = b''.join(b'\x00' + img[r].tobytes() for r in range(H))
        def ch(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
        open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b''))
        print('dbg', path, 'origin', self.X[0, 0], self.Y[0, 0], 'px=0.05mm', flush=True)

    def passable(self, L, win, X, Y, inneck, near_own, near_own75):
        B, J = self.B, self.J
        w, wn = self.w, self.wn
        gs = collections.defaultdict(list); gn = collections.defaultdict(list); gp = collections.defaultdict(list)
        for it in B.query(L, win):
            if it.net == self.net and self.net: continue
            if it.typ == 'Zone' and it.net == 'GND' and J.get('allow_gnd_pour', True): continue
            if it.typ == 'Zone' and L in ('F.Cu', 'B.Cu') and J.get('zone_soft', 0) > 0:   # RT-10: F/B pours refill around new copper
                g2 = it.geom.buffer(-J['zone_soft'])
                if g2.is_empty: continue
                it = Item(g2, it.net, it.cls, it.typ, it.layer)
            if it.typ == 'Zone' and self.softbox is not None:
                g2 = it.geom.difference(self.softbox)
                if g2.is_empty: continue
                it = Item(g2, it.net, it.cls, it.typ, it.layer)
            cs = RU.clr_strict(self.cls, self.net, it.cls, it.typ); cn = self.cneck(it)
            if L == 'In2.Cu' and it.typ == 'Zone' and it.net != 'GND': cs = max(cs, 0.3); cn = max(cn, 0.3)
            gs[round(cs + w / 2 + M, 4)].append(it.geom); gn[round(cn + wn / 2 + self.J.get("neck_margin", -0.0005), 4)].append(it.geom)
            if it.typ != 'Pad': gp[(round(cs + w / 2 + M, 4), round(cn + wn / 2 - 0.0005, 4))].append(it.geom)
        blk_s = np.zeros(X.shape, bool); blk_n = np.zeros(X.shape, bool)
        for d, gl in gs.items(): blk_s |= contains_grid(unary_union(gl).buffer(d, 8), X, Y)
        for d, gl in gn.items(): blk_n |= contains_grid(unary_union(gl).buffer(d, 8), X, Y)
        blk = np.where(inneck, blk_n, blk_s)
        bs2 = np.zeros(X.shape, bool); bn2 = np.zeros(X.shape, bool)
        for (d1, d2), gl in gp.items():
            u = unary_union(gl); bs2 |= contains_grid(u.buffer(d1, 8), X, Y); bn2 |= contains_grid(u.buffer(d2, 8), X, Y)
        self.blk_np = getattr(self, 'blk_np', {}); self.blk_np[L] = np.where(inneck, bn2, bs2)
        # holes (copper to hole 0.25) of other nets (and NPTH)
        hs = [B.holes[i] for i in B.htree.query(win)]
        hg = [h[0] for h in hs if h[1] != self.net or not h[2]]
        if hg: blk |= contains_grid(unary_union(hg).buffer(0.25 + w / 2 + M, 8), X, Y)
        blk |= contains_grid(B.edge.buffer(0.5 + w / 2 + M, 8), X, Y) | ~contains_grid(B.outline, X, Y)
        for a in B.areas:
            if L not in a['layers']: continue
            nm = a['name']
            g = mk(a['outline'])
            if a['no_tracks']: blk |= contains_grid(g.buffer(w / 2 + M), X, Y)
            if nm.startswith('BKO_') and L == 'B.Cu' and RU.bko_applies(self.cls, self.net): blk |= contains_grid(g.buffer(w / 2 + M), X, Y)
        if L == 'F.Cu' and self.icbody is not None and J.get('no_under_ic', True): blk |= contains_grid(self.icbody.buffer(w / 2), X, Y)
        if L == 'F.Cu': blk |= contains_grid(B.modko.buffer(w / 2), X, Y) if self.net not in [d['_net'] for k, d in B.pads.items() if k.startswith('U1-')] else contains_grid(B.modko, X, Y)
        # halo
        hal = J.get('halo', 0.6)
        if hal > 0 and self.cls in RU.SIGCLS | {'I2S_CLK'} :
            hl = []
            for it in B.query(L, win):
                if it.typ != 'Track' or it.net == self.net: continue
                other_sens = it.cls in SENS_CLS or it.net in SENS_NETS
                if (self.sens and it.cls in RU.SIGCLS) or (not self.sens and other_sens):
                    hl.append(it.geom)
            if hl:
                hb = contains_grid(unary_union(hl).buffer(hal + w / 2, 8), X, Y)
                blk |= hb & ~inneck & ~near_own
        # SP3: control nets of switchers keep sp3 mm to SWITCH/BOOT copper beyond 0.75 mm of own pads
        sp3 = J.get('sp3', 0.0)
        if sp3 > 0:
            sl = [it.geom for it in B.query(L, win) if it.cls in SWCLS and it.net != self.net]
            if sl: blk |= contains_grid(unary_union(sl).buffer(sp3 + w / 2, 8), X, Y) & ~near_own75
        # sensitive nets: B.Cu only over In2 GND
        if L == 'B.Cu' and self.sens and J.get('sens_bcu', 'gnd') == 'gnd':
            blk |= ~contains_grid(B.in2gnd.buffer(-w / 2), X, Y)
        for k in J.get('block', []):           # extra manual block boxes [x0,y0,x1,y1,'F.Cu']
            if k[4] == L: blk |= contains_grid(box(*k[:4]), X, Y)
        if L == 'F.Cu' and J.get('fblock'):     # RT-8: F.Cu forbidden inside fblock boxes except inside fallow boxes
            fb = contains_grid(unary_union([box(*k) for k in J['fblock']]), X, Y)
            if J.get('fallow'): fb &= ~contains_grid(unary_union([box(*k) for k in J['fallow']]), X, Y)
            blk |= fb
        return ~blk

    def via_ok(self, win, X, Y, inneck):
        B, J = self.B, self.J
        fine = J.get('fine_via', False)
        r = 0.3; rn = 0.25 if fine else 0.3
        ok = np.ones(X.shape, bool)
        for L in ('F.Cu', 'B.Cu', 'In1.Cu', 'In2.Cu'):
            gs = collections.defaultdict(list); gn = collections.defaultdict(list)
            for it in B.query(L, win):
                if it.net == self.net and self.net: continue
                if it.typ == 'Zone' and (L in ('In1.Cu', 'In2.Cu') or it.net == 'GND'): continue
                if it.typ == 'Zone' and J.get('zone_soft', 0) > 0:
                    g2 = it.geom.buffer(-J['zone_soft'])
                    if g2.is_empty: continue
                    it = Item(g2, it.net, it.cls, it.typ, it.layer)
                if it.typ == 'Zone' and self.softbox is not None:
                    g2 = it.geom.difference(self.softbox)
                    if g2.is_empty: continue
                    it = Item(g2, it.net, it.cls, it.typ, it.layer)
                cs = RU.clr_strict(self.cls, self.net, it.cls, 'Via' if it.typ == 'Via' else it.typ)
                cn = self.cneck(it)
                gs[round(cs + r + M, 4)].append(it.geom); gn[round(cn + rn + M, 4)].append(it.geom)
            bs = np.zeros(X.shape, bool); bn = np.zeros(X.shape, bool)
            for d, gl in gs.items(): bs |= contains_grid(unary_union(gl).buffer(d, 8), X, Y)
            for d, gl in gn.items(): bn |= contains_grid(unary_union(gl).buffer(d, 8), X, Y)
            ok &= ~np.where(inneck, bn, bs)
        if J.get('island_via'):
            fb = unary_union([g for n, g in B.zfill['In2.Cu'] if n in J.get('island_forbid', ['/Battery_Charger/BAT_INT'])])
            if not fb.is_empty: ok &= ~contains_grid(fb.buffer(0.4 + r), X, Y)
        else:
            ok &= ~contains_grid(B.in2forbid.buffer(0.4 + r), X, Y)
        hs = [B.holes[i] for i in B.htree.query(win)]
        if hs:
            ok &= ~contains_grid(unary_union([h[0] for h in hs]).buffer(0.3 + 0.15 + M, 8), X, Y)
            hg = [h[0] for h in hs if h[1] != self.net or not h[2]]
            if hg: ok &= ~contains_grid(unary_union(hg).buffer(0.25 + r + M, 8), X, Y)
        ok &= ~contains_grid(B.edge.buffer(0.5 + r + M, 8), X, Y) & contains_grid(B.outline, X, Y)
        for a in B.areas:
            g = mk(a['outline'])
            if a['no_vias'] or (a['name'].startswith('BKO_') and RU.bko_applies(self.cls, self.net)):
                ok &= ~contains_grid(g.buffer(r + M), X, Y)
        ok &= ~contains_grid(B.modko.buffer(r), X, Y)
        # RT-11: no via land touching any pad (own net included): hand assembly, no via in pad
        pp = [g for k, d in B.pads.items() for L, g in d.items() if L in ('F.Cu', 'B.Cu') and g.intersects(win)]
        if pp: ok &= ~contains_grid(unary_union(pp).buffer(r + 0.06), X, Y)
        if self.icbody is not None and J.get('no_under_ic', True): ok &= ~contains_grid(self.icbody.buffer(r), X, Y)
        if self.sens and J.get('sens_bcu', 'gnd') == 'gnd':
            ok &= contains_grid(B.in2gnd.buffer(0.6), X, Y)     # via land inside / next to In2 GND
        for k in J.get('noviabox', []):
            ok &= ~contains_grid(box(*k), X, Y)
        return ok

    def astar(self, S, Ts, Lix, run_mm, J):
        NX, NY = self.NX, self.NY
        P = [self.P[L] for L in self.layers]; CF = [self.CF[L] for L in self.layers]; TG = [self.TG[L] for L in self.layers]
        VOK = self.VOK
        via_cost = J.get('via_cost', 1.5); turn = J.get('turn', 0.3)
        K = [max(1, int(math.ceil(run_mm / (G * (1.41421356 if d % 2 else 1.0)) - 1e-9))) for d in range(8)]
        st = [math.sqrt(2) * G if d % 2 else G for d in range(8)]
        ci0, cj0 = -self.i0, -self.j0            # start cell
        tcs = [((t['c'][0] - self.X[0, 0]) / G, (t['c'][1] - self.Y[0, 0]) / G) for t in Ts]

        def h(i, j):
            best = 1e9
            for ti, tj in tcs:
                dx, dy = abs(i - ti), abs(j - tj)
                best = min(best, (max(dx, dy) + 0.41421356 * min(dx, dy)) * G)
            return best

        def inb(i, j): return 0 <= i < NX and 0 <= j < NY
        dirs_from = J.get('dirs_from', '*')
        dlist = range(8) if dirs_from == '*' else [DNAME[x] for x in dirs_from.split(',')]
        g = {}; par = {}; pq = []
        Lstart = [l for l, L in enumerate(self.layers) if L in S['reg']]
        sreg = {L: S['reg'][L] for L in S['reg']}
        for l in Lstart:
            L = self.layers[l]
            for d in dlist:
                dx, dy = DIRS[d]; i, j = ci0, cj0; n = 0; okp = True
                # walk out of own pad then 0.3 mm
                while True:
                    i += dx; j += dy; n += 1
                    if not inb(i, j) or not P[l][i, j]: okp = False; break
                    if not shapely.intersects_xy(sreg[L], self.X[i, j], self.Y[i, j]) or n > 200: break
                if not okp: continue
                extra = (int(math.ceil(0.3 / st[d] - 1e-9)) if S['key'] else K[d] - 1)
                for _ in range(extra):
                    i += dx; j += dy; n += 1
                    if not inb(i, j) or not P[l][i, j]: okp = False; break
                if not okp: continue
                s = (i, j, l, d); c = n * st[d]
                if c < g.get(s, 1e18):
                    g[s] = c; par[s] = ('start', d, n); heapq.heappush(pq, (c + h(i, j), c, s))
        tend = J.get('dirs_to', '*'); tset = None if tend == '*' else {DNAME[x] for x in tend.split(',')}
        exp = 0; maxexp = J.get('max_exp', 3e6); self.exp = 0; self.visited = set()
        while pq:
            f, c, s = heapq.heappop(pq)
            if c > g.get(s, 1e18) + 1e-12: continue
            exp += 1
            if exp > maxexp: break
            i, j, l, d = s
            if J.get('dbg'): self.visited.add((i, j))
            if d < 8 and TG[l][i, j] and (tset is None or d in tset):
                # straight approach >= 0.3 mm outside the target pad
                total = 0; k = s
                while True:
                    p = par[k]
                    if p[0] == 'start':
                        total += p[2]; break
                    prev, how = p
                    if how[0] != 'step' or how[1] != d: break
                    total += how[2]; k = prev
                    if total * st[d] > 2.0: break
                inside = 0; ii, jj = i, j
                while inb(ii, jj) and TG[l][ii, jj] and inside <= total:
                    inside += 1; ii -= DIRS[d][0]; jj -= DIRS[d][1]
                if (total - inside + 1) * st[d] >= 0.3 - 1e-9 or not any(T['key'] for T in Ts):
                    return self.trace(s, par)
            nb = []
            if d < 8:
                dx, dy = DIRS[d]
                if inb(i + dx, j + dy) and P[l][i + dx, j + dy]:
                    nb.append(((i + dx, j + dy, l, d), st[d] * CF[l][i + dx, j + dy], ('step', d, 1)))
                for nd in ((d + 1) % 8, (d - 1) % 8):
                    r = self.jump(P[l], CF[l], i, j, nd, K[nd], st[nd])
                    if r: nb.append(((r[0], r[1], l, nd), r[2] + turn, ('step', nd, K[nd])))
                if len(self.layers) >= 2 and VOK[i, j]:
                    for l2 in range(len(self.layers)):
                        if l2 != l: nb.append(((i, j, l2, 8), via_cost, ('via', 8, 0)))
            else:
                for nd in range(8):
                    r = self.jump(P[l], CF[l], i, j, nd, K[nd], st[nd])
                    if r: nb.append(((r[0], r[1], l, nd), r[2], ('step', nd, K[nd])))
            for s2, dc, how in nb:
                c2 = c + dc
                if c2 < g.get(s2, 1e18) - 1e-12:
                    g[s2] = c2; par[s2] = (s, how); heapq.heappush(pq, (c2 + h(s2[0], s2[1]), c2, s2))
        self.exp = exp
        return None

    def jump(self, P, CF, i, j, d, k, stp):
        dx, dy = DIRS[d]; c = 0.0
        for n in range(1, k + 1):
            a, b = i + dx * n, j + dy * n
            if not (0 <= a < self.NX and 0 <= b < self.NY) or not P[a, b]: return None
            c += stp * CF[a, b]
        return (i + dx * k, j + dy * k, c)

    def trace(self, s, par):
        path = []
        while True:
            p = par[s]
            if p[0] == 'start':
                path.append((s, 'start', p[1], p[2])); break
            prev, how = p
            path.append((s, how[0], how[1], how[2])); s = prev
        return list(reversed(path))

    def emit(self, path, S, Ts):
        """-> list of segments (layer, w, (x1,y1), (x2,y2)) and vias; cells -> polyline per layer"""
        X0, Y0 = self.X[0, 0], self.Y[0, 0]
        P = lambda i, j: (round(X0 + i * G, 6), round(Y0 + j * G, 6))
        sx, sy = S['c']
        polys = []; cur = [(sx, sy)]; curL = self.layers[path[0][0][2]]; vias = []
        cells = []      # (x, y, layer)
        for s, how, d, n in path:
            i, j, l, _ = s
            L = self.layers[l]
            if how == 'via':
                polys.append((curL, cur)); vias.append(P(i, j)); cur = [P(i, j)]; curL = L; continue
            cur.append(P(i, j))
        polys.append((curL, cur))
        # extend into the end pad toward its centre along the last direction
        segs = []
        for L, pl in polys:
            q = [pl[0]]
            for p in pl[1:]:
                if len(q) >= 2:
                    a, b = q[-2], q[-1]
                    d1 = (np.sign(round(b[0] - a[0], 6)), np.sign(round(b[1] - a[1], 6)))
                    d2 = (np.sign(round(p[0] - b[0], 6)), np.sign(round(p[1] - b[1], 6)))
                    if d1 == d2: q[-1] = p; continue
                if p != q[-1]: q.append(p)
            for a, b in zip(q[:-1], q[1:]):
                segs.append([L, a, b])
        # final extension inside the target pad toward the projection of its centre
        if segs:
            L, a, b = segs[-1]
            T = None
            for t in Ts:
                if L in t['reg'] and t['reg'][L].buffer(0.01).contains(Point(b)): T = t
            if T is not None and T['key']:
                dx, dy = np.sign(round(b[0] - a[0], 6)), np.sign(round(b[1] - a[1], 6))
                best = b; bd = math.hypot(b[0] - T['c'][0], b[1] - T['c'][1])
                for k in range(1, 60):
                    p = (round(b[0] + dx * G * k, 6), round(b[1] + dy * G * k, 6))
                    if not T['reg'][L].buffer(-0.01).contains(Point(p)): break
                    dd = math.hypot(p[0] - T['c'][0], p[1] - T['c'][1])
                    if dd < bd: best, bd = p, dd
                segs[-1][2] = best
        # widths: neck width where a segment lies (partly) in the neck region and the class width does not fit
        out = []
        for L, a, b in segs:
            ln = LineString([a, b])
            w = self.w
            if self.wn < self.w and ln.intersects(self.B.neck):
                # split at the neck boundary only if needed: test class width clearance along the segment cells
                w = self.wn if self.needs_neck(L, a, b) else self.w
            out.append(dict(layer=L, w=w, a=a, b=b))
        return dict(net=self.net, segs=out, vias=vias)

    def needs_neck(self, L, a, b):
        """True if a class-width track on a-b would violate the strict/neck clearance raster (sampled)"""
        ln = LineString([a, b]); n = max(2, int(ln.length / 0.02))
        for k in range(n + 1):
            p = ln.interpolate(k / n, normalized=True)
            g = p.buffer(self.w / 2 - self.wn / 2 + 1e-4)
            for it in self.B.query(L, g.buffer(1.5)):
                if it.net == self.net: continue
                if it.typ == 'Zone' and it.net == 'GND': continue
                c = RU.clr_neck(self.cls, self.net, it.cls, it.typ) if self.B.neck.contains(p) else RU.clr_strict(self.cls, self.net, it.cls, it.typ)
                if it.geom.distance(p) < c + self.w / 2 - 1e-4: return True
        return False


def stitch(B, net, vias, segs, rmax=1.5):
    """GND stitching via within rmax of every via: existing GND via / plated GND hole, else a legal new spot"""
    add = []
    for (x, y) in vias:
        have = any(Point(x, y).distance(h[0].centroid) <= rmax for h in B.holes if h[1] == 'GND' and h[2])
        if have: continue
        best = None
        for rr in np.arange(0.8, rmax + 1e-9, 0.05):
            for k in range(48):
                a = 2 * math.pi * k / 48
                px, py = round(x + rr * math.cos(a), 3), round(y + rr * math.sin(a), 3)
                if site_ok_gnd(B, px, py, segs): best = (px, py); break
            if best: break
        add.append(best)
    return add


def site_ok_gnd(B, x, y, segs):
    p = Point(x, y); r = 0.3
    if not B.gnd12.contains(p): return False
    if not B.outline.buffer(-0.8).contains(p): return False
    g = p.buffer(r + 0.2 + 0.01)
    for L in ('F.Cu', 'B.Cu', 'In1.Cu', 'In2.Cu'):
        for it in B.query(L, g.buffer(0.5)):
            if it.net == 'GND' or (it.typ == 'Zone'): continue
            c = RU.clr_strict('GND', 'GND', it.cls, it.typ)
            if it.geom.distance(p) < r + c + 0.01: return False
    for h in B.holes:
        if h[0].distance(p) < 0.15 + 0.3 + 0.01: return False
    for a in B.areas:
        if a['no_vias'] and mk(a['outline']).buffer(r).contains(p): return False
    if B.modko.buffer(r).contains(p): return False
    for k, d in B.pads.items():                     # RT-11: no stitch via touching any pad
        for L, g in d.items():
            if L in ('F.Cu', 'B.Cu') and g.distance(p) < r + 0.06: return False
    for s in segs:
        if LineString([s['a'], s['b']]).distance(p) < s['w'] / 2 + 0.2 + r + 0.01: return False
    return True


def main():
    JS = json.load(open(sys.argv[1]))
    B = Board(JS['geo'])
    plan = json.load(open(JS['base_plan'])) if JS.get('base_plan') else {}
    plan.setdefault('seg_add', []); plan.setdefault('via_add', [])
    # copper deleted by the base plan is removed from the model
    dels = set(plan.get('seg_del', []))
    if dels:
        for L in list(B.items):
            B.items[L] = [it for it in B.items[L] if not (it.typ == 'Track' and any(it.name.startswith(u) for u in dels))]
    gone = [tuple(v) for v in plan.get('via_del_xy', [])] + [tuple(v[:2]) for v in plan.get('via_set_xy', [])]
    if gone:
        near = lambda g: any(abs(g.centroid.x - x) < 1e-3 and abs(g.centroid.y - y) < 1e-3 for x, y in gone)
        for L in list(B.items):
            B.items[L] = [it for it in B.items[L] if not (it.typ == 'Via' and near(it.geom))]
        B.holes = [h for h in B.holes if not near(h[0])]
    for v in plan.get('via_set_xy', []):
        B.add_via(v[4], v[2], v[3], v[5], v[6])
    for a in plan['seg_add']:
        B.add_track(a[0], a[1], a[2], (a[3], a[4]), (a[5], a[6]))
    for v in plan['via_add']:
        B.add_via(v[0], v[1], v[2], v[3], v[4])
    B.rebuild()
    log = []
    for J in JS['jobs']:
        t0 = time.time()
        jb = Job(B, J)
        try:
            r = jb.run()
        except Exception as e:
            import traceback; traceback.print_exc(); r = None
        def rlen(rr): return sum(math.dist(q['a'], q['b']) for q in rr['segs']) + 1.5 * len(rr['vias'])
        if isinstance(J['to'], str) and J['to'] != 'NET' and isinstance(J['from'], str):
            ca, cb = B.pads[J['from']]['_c'], B.pads[J['to']]['_c']
            dx, dy = abs(ca[0] - cb[0]), abs(ca[1] - cb[1]); omin = max(dx, dy) + 0.41421356 * min(dx, dy)
            if not r or rlen(r) > 1.5 * omin + 1.0:
                J2 = dict(J); J2['from'], J2['to'] = J['to'], J['from']
                if J2['from'].startswith('U11-'): J2.update(neck_val=0.15, wn=0.15)
                jb2 = Job(B, J2)
                try:
                    r2 = jb2.run()
                except Exception:
                    r2 = None
                if r2 and (not r or rlen(r2) < rlen(r)):
                    r, jb, J = r2, jb2, J2; print('   reverse direction used', flush=True)
        if not r:
            print('FAIL %-34s %s -> %s  (%.1fs, exp %s)' % (J['net'], J['from'], J['to'], time.time() - t0, getattr(jb, 'exp', '?')), flush=True)
            log.append(dict(job=J, ok=False)); continue
        L = 0
        for s in r['segs']:
            plan['seg_add'].append([s['layer'], J['net'], s['w'], s['a'][0], s['a'][1], s['b'][0], s['b'][1]])
            B.add_track(s['layer'], J['net'], s['w'], s['a'], s['b']); L += math.dist(s['a'], s['b'])
        r['vsz'] = []
        for (x, y) in r['vias']:
            vsz = (0.5, 0.2) if (J.get('fine_via') and B.neck.contains(Point(x, y))) else (0.6, 0.3)
            r['vsz'].append(vsz)
            plan['via_add'].append([J['net'], x, y, vsz[0], vsz[1]]); B.add_via(J['net'], x, y, *vsz)
        st = []
        if r['vias'] and (jb.sens or J.get('stitch_always')):
            B.rebuild()
            st = stitch(B, J['net'], r['vias'], r['segs'], J.get('stitch', 1.5))
            for p in st:
                if p is None: print('   WARN no stitch spot', flush=True); continue
                plan['via_add'].append(['GND', p[0], p[1], 0.6, 0.3]); B.add_via('GND', p[0], p[1], 0.6, 0.3)
        B.rebuild()
        print('OK   %-34s %s -> %s  %.2f mm, %d segs, %d vias, stitch %s (%.1fs)' % (J['net'], J['from'], J['to'], L, len(r['segs']), len(r['vias']), st, time.time() - t0), flush=True)
        for s in r['segs']:
            print('      %s w%.2f (%.3f,%.3f)-(%.3f,%.3f)' % (s['layer'], s['w'], *s['a'], *s['b']))
        log.append(dict(job=J, ok=True, res=r, stitch=st, length=L))
        json.dump(plan, open(JS['out_plan'], 'w'), indent=1)
    json.dump(plan, open(JS['out_plan'], 'w'), indent=1)
    json.dump(log, open(JS['out_plan'].replace('.json', '.hrlog.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
