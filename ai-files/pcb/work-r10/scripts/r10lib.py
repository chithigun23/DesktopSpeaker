"""r10lib.py : shared model for the R10 placement pass (venv python: shapely).
Board(geo.json, dump.json, nets.txt): pads/courtyards/copper of one board; pose overrides per ref (x, y, rot);
 - exits(ref|pad list): outward escape probe (same rule as exitprobe.py)
 - legal(ref): courtyard HA8 tiers vs every neighbour (AG3: a failing pair may not be tighter than in the reference board),
   pads vs fixed foreign copper (tracks, vias, non-GND zone fills) at the router clearance, board outline.
Rotation convention: KiCad, y down, positive angle = counter-clockwise on screen."""
import sys, json, math, collections, copy
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r8/scripts')
import route_oct_rules as RR
import r8b_ha8 as HA
from shapely.geometry import Polygon, LineString, Point, box
from shapely.strtree import STRtree
from shapely.ops import unary_union
from shapely import affinity

L_EXIT, W_TRK = 1.0, 0.25
FIXED = {'J1', 'J2', 'J3', 'J5', 'J9', 'J10', 'J11', 'SW100', 'SW101', 'SW102', 'U1', 'U6', 'U7'}


def polys(pl):
    out = []
    for poly in pl:
        try:
            P = Polygon(poly[0], poly[1:]); P = P if P.is_valid else P.buffer(0)
            if not P.is_empty: out.append(P)
        except Exception: pass
    return out


def xf(px, py, f0, f1):
    """move point from footprint pose f0=(x,y,rot) to f1"""
    d = math.radians(f1[2] - f0[2]); dx, dy = px - f0[0], py - f0[1]
    c, s = math.cos(d), math.sin(d)
    return f1[0] + dx * c + dy * s, f1[1] - dx * s + dy * c


def xg(G, f0, f1):
    G = affinity.translate(G, -f0[0], -f0[1]); G = affinity.rotate(G, -(f1[2] - f0[2]), origin=(0, 0))
    return affinity.translate(G, f1[0], f1[1])


class Board:
    def __init__(self, geo, dump, netfile, dru):
        self.G = json.load(open(geo)); self.D = HA.json.load(open(dump)) if False else json.load(open(dump))
        self.D['F'] = {f['ref']: f for f in self.D['fps']}
        self.NETS = {l.split('#')[0].strip() for l in open(netfile) if l.split('#')[0].strip()}
        self.pose0 = {f['ref']: (f['x'], f['y'], f['rot']) for f in self.D['fps']}
        self.pose = dict(self.pose0)
        self.npads = collections.Counter(p['ref'] for p in self.G['pads'])
        self.pads = collections.defaultdict(list)
        for p in self.G['pads']: self.pads[p['ref']].append(p)
        nr, na = RR.neck_targets(dru); N = []
        for r in nr:
            c = self.G['courtyard'].get(r)
            if c and 'F' in c['poly']: N += polys(c['poly']['F'])
        for a in self.G['areas']:
            if a['name'] in na: N += polys(a['outline'])
        self.NECK = unary_union(N)
        self.outline = Polygon(self.G['outline'][0][0])
        cop = []
        for t in self.G['tracks']:
            if t['layer'] == 'F.Cu':
                cop.append((LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]).buffer(t['w'] / 2), t['net'], t['cls'], 'Track', 'trk ' + t['net']))
        for v in self.G['vias']:
            cop.append((Point(v['x'], v['y']).buffer(v['d'] / 2), v['net'], v['cls'], 'Via', 'via ' + v['net']))
        for z in self.G['zones']:
            if z['cls'] == 'GND' or z['teardrop'] or 'F.Cu' not in z['fills']: continue
            for P in polys(z['fills']['F.Cu']): cop.append((P, z['net'], z['cls'], 'Zone', 'zone ' + (z['name'] or z['net'])))
        self.cop = cop; self.coptree = STRtree([c[0] for c in cop])
        self.CY0 = HA.courtyards(self.D)          # strict courtyards at reference poses
        import os
        sk = []
        sp = os.path.join(os.path.dirname(os.path.abspath(dump)), 'silk-r9.json')
        for o in json.load(open(sp)):
            if o['kind'] in ('gr_line', 'gr_arc') and o['start'] and o['end']:
                sk.append(LineString([o['start'], o['end']]).buffer(o['w'] / 2))
            elif o['kind'] == 'gr_text' and o['at'] and o['size']:
                w = 0.8 * o['size'][0] * max(1, len(o['text'] or '')); h = o['size'][1] * 1.2
                sk.append(box(o['at'][0] - w / 2, o['at'][1] - h / 2, o['at'][0] + w / 2, o['at'][1] + h / 2))
        self.silk = unary_union(sk)
        self.base_gap = {}; self._pg0 = {}
        st = []
        for ref in self.pads:
            for q in self.padgeoms(ref):
                for P in q['P']: st.append((P, q['net'], q['cls'], 'Pad', ref + '-' + q['num'], ref))
        self.spad = st; self.spadtree = STRtree([o[0] for o in st])

    # ---------- geometry under overrides
    def padgeoms(self, ref):
        f0, f1 = self.pose0[ref], self.pose[ref]; out = []
        if f0 == f1 and ref in self._pg0: return self._pg0[ref]
        for p in self.pads[ref]:
            q = dict(p); q['x'], q['y'] = xf(p['x'], p['y'], f0, f1); q['rot'] = (p['rot'] + f1[2] - f0[2]) % 360
            q['P'] = [xg(P, f0, f1) for P in polys(p['poly'].get('F.Cu', []))] if 'F.Cu' in p['poly'] else []
            out.append(q)
        if f0 == f1: self._pg0[ref] = out
        return out

    def cy(self, ref):
        P = self.CY0[ref][0]
        return P if self.pose[ref] == self.pose0[ref] else xg(P, self.pose0[ref], self.pose[ref])

    def all_pad_obs(self, near, rad=4.0):
        """pad obstacles (current poses) within rad of point near"""
        moved = {r for r in self.pose if self.pose[r] != self.pose0[r]}
        q0 = box(near[0] - rad, near[1] - rad, near[0] + rad, near[1] + rad)
        out = [self.spad[i][:5] for i in self.spadtree.query(q0) if self.spad[i][5] not in moved]
        for ref in moved:
            for q in self.padgeoms(ref):
                for P in q['P']:
                    if P.intersects(q0): out.append((P, q['net'], q['cls'], 'Pad', ref + '-' + q['num']))
        return out

    # ---------- exit probe
    def dirs(self, ref, p):
        sx, sy = p['sx'], p['sy']; r = math.radians(p['rot'])
        ax = (math.cos(r), -math.sin(r)) if sx >= sy else (math.sin(r), math.cos(r))
        lo, sh = max(sx, sy), min(sx, sy)
        if self.npads[ref] >= 8 and sh <= 0.45:
            cx, cy = self.pose[ref][:2]
            s = 1 if (p['x'] - cx) * ax[0] + (p['y'] - cy) * ax[1] >= 0 else -1
            return [((s * ax[0], s * ax[1]), lo / 2)]
        if lo > 1.3 * sh: return [(ax, lo / 2), ((-ax[0], -ax[1]), lo / 2)]
        pp = (-ax[1], ax[0])
        return [(ax, lo / 2), ((-ax[0], -ax[1]), lo / 2), (pp, sh / 2), ((-pp[0], -pp[1]), sh / 2)]

    def exit_ok(self, ref, p, padobs=None):
        padobs = padobs if padobs is not None else self.all_pad_obs((p['x'], p['y']))
        best = None
        for (dx, dy), h in self.dirs(ref, p):
            a = (p['x'] + dx * h, p['y'] + dy * h); b = (a[0] + dx * L_EXIT, a[1] + dy * L_EXIT)
            w = RR.NECK_W if self.NECK.contains(Point(p['x'], p['y'])) else W_TRK
            tr = LineString([a, b]).buffer(w / 2, cap_style=2); worst = None
            cands = [self.cop[i] for i in self.coptree.query(tr.buffer(2.1))] + [o for o in padobs if o[0].distance(tr) < 2.1]
            for g, net, cls, typ, name in cands:
                if net and net == p['net']: continue
                inneck = self.NECK.intersects(g.buffer(0.01)) and self.NECK.intersects(tr)
                c = (RR.clr_neck if inneck else RR.clr_strict)(p['cls'], p['net'], cls, typ)
                d = g.distance(tr)
                if d < c - 1e-6 and (worst is None or c - d > worst[0]): worst = (round(c - d, 3), name)
            if worst is None: return True, None
            best = worst if best is None or worst[0] < best[0] else best
        return False, best

    def sigpads(self, ref):
        return [q for q in self.padgeoms(ref) if q['net'] in self.NETS and not q['net'].startswith('unconnected')]

    def exits(self, refs):
        bad = []
        for r in refs:
            po = None
            for q in self.sigpads(r):
                if po is None: po = self.all_pad_obs(self.pose[r][:2], 9.0)
                ok, w = self.exit_ok(r, q, po)
                if not ok: bad.append((r, q['num'], q['net'], w))
        return bad

    # ---------- legality of one part at its current override
    def legal(self, ref, verbose=False):
        why = []
        P = self.cy(ref)
        if not self.outline.buffer(-0.3).contains(P): why.append('outline')
        if P.intersects(self.silk) and not self.CY0[ref][0].intersects(self.silk): why.append('silk')
        F = self.D['F']
        for o, (Q0, _) in self.CY0.items():
            if o == ref: continue
            Q = self.cy(o)
            if Q.distance(P) > 1.6: continue
            g = P.distance(Q); rq, t = HA.req(F[ref], F[o])
            if g < rq - 1e-6:
                g0 = self.CY0[ref][0].distance(self.CY0[o][0])
                if g < g0 - 1e-3 or g0 >= rq - 1e-6: why.append('ha8 %s %.3f<%.2f (R9 %.3f)' % (o, g, rq, g0))
        for q in self.padgeoms(ref):
            for Pq in q['P']:
                for i in self.coptree.query(Pq.buffer(1.1)):
                    g, net, cls, typ, name = self.cop[i]
                    if net and net == q['net']: continue
                    c = RR.clr_strict(cls if cls else 'Default', net, q['cls'], 'Pad')
                    c = max(c, 0.2)
                    if g.distance(Pq) < c - 1e-6: why.append('cu %s-%s vs %s %.3f<%.2f' % (ref, q['num'], name, g.distance(Pq), c))
        # HA6: pad edge >= 0.5 mm from a via that does not belong to it (or no closer than on the reference board)
        p0 = {q['num']: q for q in self.padgeoms_at(ref, self.pose0[ref])}
        for q in self.padgeoms(ref):
            for Pq in q['P']:
                for v in self.G['vias']:
                    if abs(v['x'] - q['x']) > 2 or abs(v['y'] - q['y']) > 2: continue
                    d = Point(v['x'], v['y']).buffer(v['d'] / 2).distance(Pq)
                    if d < 0.5 - 1e-6:
                        d0 = min(Point(v['x'], v['y']).buffer(v['d'] / 2).distance(P) for P in p0[q['num']]['P'])
                        if d < d0 - 1e-3: why.append('ha6 %s-%s via %s %.3f (R9 %.3f)' % (ref, q['num'], v['net'], d, d0))
        return (not why), why

    def padgeoms_at(self, ref, pose):
        keep = self.pose[ref]; self.pose[ref] = pose
        try: return self.padgeoms(ref)
        finally: self.pose[ref] = keep


def octd(a, b):
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1]); return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


def mst(P):
    if len(P) < 2: return 0.0
    inT = {0}; d = [octd(P[0], q) for q in P]; t = 0.0
    while len(inT) < len(P):
        j = min((i for i in range(len(P)) if i not in inT), key=lambda i: d[i]); t += d[j]; inT.add(j)
        for i in range(len(P)): d[i] = min(d[i], octd(P[i], P[j]))
    return t


def net_mst(B, nets):
    pts = collections.defaultdict(list)
    for ref in B.pads:
        for q in B.padgeoms(ref) if B.pose[ref] != B.pose0[ref] else B.pads[ref]:
            if q['net'] in nets: pts[q['net']].append((q['x'], q['y']))
    return {n: mst(v) for n, v in pts.items()}
