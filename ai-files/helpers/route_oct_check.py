#!/usr/bin/env python3
"""route_oct_check.py BOARD.kicad_pcb GEO.json NETFILE [--drc DRC.json] [--manifest MAN.json] [--rules DRU PRO] [--json OUT]
Independent measurement of routed nets (does not import the router). Copper (segments, arcs, vias) is parsed from the saved
.kicad_pcb text; pad and zone-fill shapes come from GEO.json (route_oct_export.py run on the same refilled board).
Per net and in total:
  connectivity : own union-find over pads/segments/vias -> unconnected pad groups, shorts to foreign copper, dangling ends/vias
  angles       : exact share of length (|dx|=|dy| within 0.005 mm or one of them < 0.005 mm), max angle deviation, arcs
  joints       : interior angle < 90 deg, 90-degree joints away from pads/vias (GE3), T-junctions away from pads/vias (GE6)
  hygiene      : colinear splits, micro segments (< width; inside pad copper listed separately), bend spacing < max(0.4, 3w) (GE5),
                 pad exit straight run < 0.3 mm beyond the pad edge (GE7)
  length       : routed length / octilinear MST of pad centres (complete nets only), vias per net
  reference    : B.Cu length over In2 GND / non-GND island / void; F.Cu length over In1 void
  spacing      : near-parallel length (angle within 12 deg, overlap) at edge gap < 0.6 mm between an I2S_CLK/USB net and any other
                 signal track on the same layer (USB pair partner excluded); also the part outside NECK/courtyard relaxation areas
  drc          : violations by type and unconnected items, from the kicad-cli JSON
  lock         : stage copper hashes of the manifest recomputed on this board; rule file hashes vs the project
Plain python + numpy + shapely (venv)."""
import sys, re, json, math, collections, hashlib, os, argparse
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
from shapely.prepared import prep
from shapely.strtree import STRtree

TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')


def parse_copper(path):
    segs, vias, arcs = [], [], []
    txt = open(path, encoding='utf-8').read().split('\n'); i = 0
    while i < len(txt):
        m = re.match(r'^\t\((segment|arc|via)$', txt[i])
        if not m:
            i += 1; continue
        j = i + 1
        while txt[j] != '\t)':
            j += 1
        d = {}
        for b in txt[i + 1:j]:
            mm = re.match(r'^\t\t\((start|end|mid|at|width|size|drill|layer|layers|net) (.*)\)$', b)
            if mm:
                d[mm.group(1)] = mm.group(2)
        net = d.get('net', '').strip('"')
        if m.group(1) == 'segment':
            a = d['start'].split(); b = d['end'].split()
            segs.append(dict(x1=float(a[0]), y1=float(a[1]), x2=float(b[0]), y2=float(b[1]), w=float(d['width']), l=d['layer'].strip('"'), net=net,
                             sx1=a[0], sy1=a[1], sx2=b[0], sy2=b[1]))
        elif m.group(1) == 'via':
            a = d['at'].split(); vias.append(dict(x=float(a[0]), y=float(a[1]), d=float(d['size']), net=net))
        else:
            a = d['start'].split(); b = d['end'].split(); c = d['mid'].split()
            arcs.append(dict(net=net, pts=[(float(a[0]), float(a[1])), (float(c[0]), float(c[1])), (float(b[0]), float(b[1]))], w=float(d['width']), l=d['layer'].strip('"'),
                             sx1=a[0], sy1=a[1], sx2=b[0], sy2=b[1]))
        i = j + 1
    return segs, vias, arcs


def mkpoly(plist):
    out = []
    for rings in plist:
        if len(rings[0]) >= 3:
            p = Polygon(rings[0], [h for h in rings[1:] if len(h) >= 3])
            out.append(p if p.is_valid else p.buffer(0))
    return unary_union(out) if out else None


def octi(a, b):
    dx = abs(a[0] - b[0]); dy = abs(a[1] - b[1]); return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


def mst(pts):
    pts = list(set(pts))
    if len(pts) < 2:
        return 0.0
    d = [octi(pts[0], p) for p in pts]; inT = {0}; t = 0.0
    while len(inT) < len(pts):
        j = min((i for i in range(len(pts)) if i not in inT), key=lambda i: d[i]); t += d[j]; inT.add(j)
        for i in range(len(pts)):
            d[i] = min(d[i], octi(pts[i], pts[j]))
    return t


def exact(s, tol=0.005):
    dx = abs(s['x2'] - s['x1']); dy = abs(s['y2'] - s['y1'])
    return dx < tol or dy < tol or abs(dx - dy) <= tol


def angdev(s):
    a = math.degrees(math.atan2(s['y2'] - s['y1'], s['x2'] - s['x1'])) % 180
    return min(abs(a - x) for x in (0, 45, 90, 135, 180))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board'); ap.add_argument('geo'); ap.add_argument('nets')
    ap.add_argument('--drc'); ap.add_argument('--manifest'); ap.add_argument('--rules', nargs=2); ap.add_argument('--json')
    ap.add_argument('--project-rules', nargs=2, default=['/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/DesktopSpeaker.kicad_dru',
                                                          '/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/DesktopSpeaker.kicad_pro'])
    a = ap.parse_args()
    nets = []; stage_of = {}
    for L in open(a.nets):
        L = L.split('#', 1)[0].split()
        if len(L) >= 2:
            nets.append(L[1]); stage_of[L[1]] = L[0]
    NS = set(nets)
    segs, vias, arcs = parse_copper(a.board)
    G = json.load(open(a.geo))
    cls = G['netclass']
    pads = collections.defaultdict(list)
    for p in G['pads']:
        if p['net'] in NS:
            for l, pl in p['poly'].items():
                g = mkpoly(pl)
                if g is not None:
                    pads[p['net']].append(dict(key='%s-%s' % (p['ref'], p['num']), l=l, g=g, x=p['x'], y=p['y'], pth=p['attr'] == 'PTH'))
    padcentres = collections.defaultdict(set)
    for p in G['pads']:
        if p['net'] in NS and any(l in p['poly'] for l in ('F.Cu', 'B.Cu')):
            padcentres[p['net']].add((round(p['x'], 4), round(p['y'], 4)))
    # foreign copper per layer for shorts
    foreign = collections.defaultdict(list)
    for p in G['pads']:
        for l, pl in p['poly'].items():
            g = mkpoly(pl)
            if g is not None:
                foreign[l].append((p['net'], g))
    for z in G['zones']:
        for l, pl in z['fills'].items():
            g = mkpoly(pl)
            if g is not None:
                foreign[l].append((z['net'], g))
    for s in segs:
        if s['net'] not in NS:
            g = LineString([(s['x1'], s['y1']), (s['x2'], s['y2'])]).buffer(s['w'] / 2) if (s['x1'], s['y1']) != (s['x2'], s['y2']) else Point(s['x1'], s['y1']).buffer(s['w'] / 2)
            foreign[s['l']].append((s['net'], g))
    for v in vias:
        if v['net'] not in NS:
            for l in ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'):
                foreign[l].append((v['net'], Point(v['x'], v['y']).buffer(v['d'] / 2)))
    ftree = {l: (STRtree([g for n, g in lst]), lst) for l, lst in foreign.items()}

    def union(D, layer, pred):
        out = []
        for z in D['zones']:
            if z['teardrop'] or not pred(z['net']):
                continue
            if layer in z['fills']:
                g = mkpoly(z['fills'][layer])
                if g is not None:
                    out.append(g)
        return prep(unary_union(out)) if out else None
    in1g = union(G, 'In1.Cu', lambda n: n == 'GND'); in2g = union(G, 'In2.Cu', lambda n: n == 'GND'); in2o = union(G, 'In2.Cu', lambda n: n != 'GND')
    neck = []
    for ar in G['areas']:
        if ar['name'].startswith('NECK_'):
            g = mkpoly(ar['outline'])
            if g is not None:
                neck.append(g)
    dru_txt = open(a.project_rules[0]).read()
    for ref in re.findall(r"intersectsCourtyard\('([^']+)'\)", dru_txt):
        c = G['courtyard'].get(ref)
        if c and 'F' in c['poly']:
            neck.append(mkpoly(c['poly']['F']))
    neck = prep(unary_union([g for g in neck if g is not None]))

    R = dict(nets={}, total={})
    T = collections.Counter(); ratios = []
    allsig = [s for s in segs if s['net'] != 'GND' and s['w'] <= 0.35 and (s['x1'], s['y1']) != (s['x2'], s['y2'])]
    sl = [LineString([(s['x1'], s['y1']), (s['x2'], s['y2'])]) for s in allsig]
    stree = STRtree(sl)
    for n in nets:
        S = [s for s in segs if s['net'] == n]; V = [v for v in vias if v['net'] == n]; P = pads.get(n, [])
        r = collections.OrderedDict(cls=cls.get(n, ''), stage=stage_of[n], segs=len(S), vias=len(V), arcs=sum(1 for x in arcs if x['net'] == n))
        L = sum(math.hypot(s['x2'] - s['x1'], s['y2'] - s['y1']) for s in S)
        Lx = sum(math.hypot(s['x2'] - s['x1'], s['y2'] - s['y1']) for s in S if exact(s))
        r['len'] = round(L, 3); r['exact_pct'] = round(100 * Lx / L, 3) if L else None
        r['max_dev_deg'] = round(max([angdev(s) for s in S if math.hypot(s['x2'] - s['x1'], s['y2'] - s['y1']) > 1e-9] or [0]), 4)
        # connectivity
        items = []
        for s in S:
            g = LineString([(s['x1'], s['y1']), (s['x2'], s['y2'])]).buffer(s['w'] / 2) if (s['x1'], s['y1']) != (s['x2'], s['y2']) else Point(s['x1'], s['y1']).buffer(s['w'] / 2)
            items.append(('s', {s['l']}, g, s))
        for v in V:
            items.append(('v', {'F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'}, Point(v['x'], v['y']).buffer(v['d'] / 2), v))
        for p in P:
            items.append(('p', {p['l']}, p['g'], p))
        for ar in arcs:
            if ar['net'] == n:
                items.append(('a', {ar['l']}, LineString(ar['pts']).buffer(ar['w'] / 2), ar))
        zl = []
        for z in G['zones']:
            if z['net'] == n:
                for l, pl in z['fills'].items():
                    g = mkpoly(pl)
                    if g is not None:
                        items.append(('z', {l}, g, None)); zl.append((l, g))
        par = list(range(len(items)))
        def f(i):
            while par[i] != i:
                par[i] = par[par[i]]; i = par[i]
            return i
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if items[i][1] & items[j][1] and items[i][2].intersects(items[j][2]):
                    par[f(i)] = f(j)
        padgroups = {}
        for i, it in enumerate(items):
            if it[0] == 'p':
                padgroups.setdefault(it[3]['key'], set()).add(f(i))
        # pads with copper on two layers are one item group
        comp = set()
        for k, gs in padgroups.items():
            g0 = min(gs)
            for g in gs:
                par[f(g)] = f(g0)
        comp = {f(min(gs)) for gs in padgroups.values()}
        r['pads'] = len(padgroups); r['unconnected'] = max(0, len(comp) - 1)
        r['complete'] = r['unconnected'] == 0 and r['pads'] >= 2
        # shorts
        sh = 0
        for kind, ls, g, o in items:
            if kind == 'p':
                continue
            for l in ls:
                if l not in ftree:
                    continue
                tr, lst = ftree[l]
                for j in tr.query(g):
                    nn, gg = lst[j]
                    if nn != n and nn and g.intersects(gg) and g.intersection(gg).area > 1e-6:
                        sh += 1
        r['shorts'] = sh
        # endpoints, joints
        ends = collections.defaultdict(list)
        for i, s in enumerate(S):
            ends[(s['l'], s['sx1'], s['sy1'])].append((i, 0)); ends[(s['l'], s['sx2'], s['sy2'])].append((i, 1))
        padp = collections.defaultdict(list)
        for p in P:
            padp[p['l']].append(p['g'])
        vpts = [Point(v['x'], v['y']).buffer(v['d'] / 2) for v in V]
        aend = collections.Counter()
        for ar in arcs:
            if ar['net'] == n:
                aend[(ar['l'], ar['sx1'], ar['sy1'])] += 1; aend[(ar['l'], ar['sx2'], ar['sy2'])] += 1
        def at_pad_or_via(l, x, y):
            pt = Point(x, y)
            return any(g.intersects(pt) for g in padp[l]) or any(g.intersects(pt) for g in vpts) or any(zz == l and g.buffer(1e-3).intersects(pt) for zz, g in zl)
        dangl = 0; acute = 0; j90 = 0; tj = 0; colin = 0; bendshort = 0; micro = 0; micro_in = 0; exitshort = 0
        def dvec(s, e):
            return (s['x2'] - s['x1'], s['y2'] - s['y1']) if e == 0 else (s['x1'] - s['x2'], s['y1'] - s['y2'])
        bendpts = set()
        for k, v in ends.items():
            l, x, y = k[0], float(k[1]), float(k[2])
            ap_ = at_pad_or_via(l, x, y)
            # also count other segments passing through this point (T on a body)
            body = sum(1 for i, s in enumerate(S) if s['l'] == l and (i, 0) not in v and (i, 1) not in v and
                       LineString([(s['x1'], s['y1']), (s['x2'], s['y2'])]).distance(Point(x, y)) < 1e-4)
            deg = len(v) + 2 * body + aend[k]
            if deg == 1 and not ap_:
                dangl += 1; R.setdefault('dangling_at', []).append((n, l, x, y))
            if deg >= 3 and not ap_:
                tj += 1
            if len(v) == 2 and body == 0:
                (i1, e1), (i2, e2) = v; d1 = dvec(S[i1], e1); d2 = dvec(S[i2], e2)
                n1 = math.hypot(*d1); n2 = math.hypot(*d2)
                if n1 < 1e-9 or n2 < 1e-9:
                    continue
                ang = math.degrees(math.acos(max(-1, min(1, (d1[0] * d2[0] + d1[1] * d2[1]) / (n1 * n2)))))
                if ang < 89.5:
                    acute += 1
                elif ang < 90.5 and not ap_:
                    j90 += 1
                if ang > 179.5 and abs(S[i1]['w'] - S[i2]['w']) < 1e-9 and not ap_:
                    colin += 1
                if ang < 179.5 and not ap_:
                    bendpts.add((l, k[1], k[2]))
        for v in V:
            c = sum(1 for s in S if (abs(s['x1'] - v['x']) < 1e-4 and abs(s['y1'] - v['y']) < 1e-4) or (abs(s['x2'] - v['x']) < 1e-4 and abs(s['y2'] - v['y']) < 1e-4))
            inpad = any(g.intersects(Point(v['x'], v['y'])) for l in ('F.Cu', 'B.Cu') for g in padp[l])
            if c + int(inpad) < 2:
                dangl += 1; R.setdefault('dangling_at', []).append((n, 'via', v['x'], v['y']))
        for s in S:
            ln = math.hypot(s['x2'] - s['x1'], s['y2'] - s['y1'])
            if ln < s['w']:
                g = LineString([(s['x1'], s['y1']), (s['x2'], s['y2'])]) if ln > 0 else Point(s['x1'], s['y1'])
                if any(pg.contains(g) for pg in padp[s['l']]):
                    micro_in += 1
                else:
                    micro += 1
            if (s['l'], s['sx1'], s['sy1']) in bendpts and (s['l'], s['sx2'], s['sy2']) in bendpts and ln < max(0.4, 3 * s['w']) - 1e-6:
                g = LineString([(s['x1'], s['y1']), (s['x2'], s['y2'])])
                if not any(pg.contains(g) for pg in padp[s['l']]):
                    bendshort += 1
        # pad exit: first segment(s) leaving each pad: straight length outside the pad before the first bend
        for p in P:
            for i, s in enumerate(S):
                if s['l'] != p['l']:
                    continue
                for e, (x, y) in enumerate(((s['x1'], s['y1']), (s['x2'], s['y2']))):
                    if not p['g'].intersects(Point(x, y)):
                        continue
                    g = LineString([(s['x1'], s['y1']), (s['x2'], s['y2'])]) if (s['x1'], s['y1']) != (s['x2'], s['y2']) else None
                    if g is None:
                        continue
                    if p['g'].contains(g):
                        # micro dogleg inside the pad: follow to the next segment
                        ox, oy = (s['x2'], s['y2']) if e == 0 else (s['x1'], s['y1'])
                        nxt = [t for t in S if t is not s and t['l'] == s['l'] and ((abs(t['x1'] - ox) < 1e-6 and abs(t['y1'] - oy) < 1e-6) or (abs(t['x2'] - ox) < 1e-6 and abs(t['y2'] - oy) < 1e-6))]
                        if len(nxt) != 1:
                            continue
                        t = nxt[0]; g = LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])])
                        far = (t['x2'], t['y2']) if abs(t['x1'] - ox) < 1e-6 and abs(t['y1'] - oy) < 1e-6 else (t['x1'], t['y1'])
                    else:
                        far = (s['x2'], s['y2']) if e == 0 else (s['x1'], s['y1'])
                    out_len = g.difference(p['g']).length
                    # a segment that ends in another pad of the net (direct pad-to-pad) is fine
                    if any(q['g'].intersects(Point(*far)) for q in P if q is not p and q['l'] == p['l']):
                        continue
                    if out_len < 0.3 - 1e-6:
                        exitshort += 1
        r.update(dangling=dangl, joints_lt90=acute, joints_90_away=j90, t_junctions=tj, colinear_splits=colin, micro_segs=micro,
                 micro_segs_in_pad=micro_in, bend_spacing_short=bendshort, pad_exit_short=exitshort)
        mn = mst(list(padcentres[n]))
        r['octi_min'] = round(mn, 3); r['ratio'] = round(L / mn, 3) if (mn and r['complete']) else None
        if r['ratio']:
            ratios.append(r['ratio'])
        # reference
        ref = collections.Counter()
        for s in S:
            ln = math.hypot(s['x2'] - s['x1'], s['y2'] - s['y1']); m = max(1, int(ln / 0.2))
            for k in range(m):
                t = (k + .5) / m; pt = Point(s['x1'] + (s['x2'] - s['x1']) * t, s['y1'] + (s['y2'] - s['y1']) * t)
                if s['l'] == 'B.Cu':
                    ref['B_over_In2_' + ('GND' if in2g and in2g.contains(pt) else 'island' if in2o and in2o.contains(pt) else 'void')] += ln / m
                elif s['l'] == 'F.Cu':
                    ref['F_over_In1_' + ('GND' if in1g and in1g.contains(pt) else 'void')] += ln / m
                else:
                    ref[s['l']] += ln / m
        r['ref'] = {k: round(v, 2) for k, v in ref.items()}
        # spacing
        par_all = 0.0; par_out = 0.0; mg = 9.0
        spc = cls.get(n) in ('I2S_CLK', 'USB')
        partner = {'/USB_DP': '/USB_DN', '/USB_DN': '/USB_DP', 'Net-(U2-D+)': 'Net-(U2-D-)', 'Net-(U2-D-)': 'Net-(U2-D+)'}.get(n)
        if spc:
            for s in S:
                if s['w'] > 0.35 or (s['x1'], s['y1']) == (s['x2'], s['y2']):
                    continue
                g = LineString([(s['x1'], s['y1']), (s['x2'], s['y2'])])
                for j in stree.query(g.buffer(1.0)):
                    t = allsig[j]
                    if t['l'] != s['l'] or t['net'] == n or t['net'] == partner:
                        continue
                    a1 = math.atan2(s['y2'] - s['y1'], s['x2'] - s['x1']); a2 = math.atan2(t['y2'] - t['y1'], t['x2'] - t['x1'])
                    if abs((a1 - a2 + math.pi / 2) % math.pi - math.pi / 2) > math.radians(12):
                        continue
                    ov = g.intersection(sl[j].buffer(0.6 + (s['w'] + t['w']) / 2, cap_style='flat'))
                    if ov.length < 1e-6:
                        continue
                    gap = g.distance(sl[j]) - (s['w'] + t['w']) / 2
                    mg = min(mg, gap); par_all += ov.length
                    m = max(1, int(ov.length / 0.1)); outn = 0
                    if ov.geom_type == 'LineString':
                        for k in range(m):
                            pt = ov.interpolate((k + .5) / m, normalized=True)
                            if not neck.contains(pt):
                                outn += 1
                        par_out += ov.length * outn / m
                    else:
                        par_out += ov.length
        r['par_lt0.6_mm'] = round(par_all, 2) if spc else None; r['par_lt0.6_outside_neck_mm'] = round(par_out, 2) if spc else None
        r['par_min_gap'] = round(mg, 3) if spc and mg < 9 else None
        R['nets'][n] = r
        for k in ('segs', 'vias', 'arcs', 'unconnected', 'shorts', 'dangling', 'joints_lt90', 'joints_90_away', 't_junctions', 'colinear_splits',
                  'micro_segs', 'micro_segs_in_pad', 'bend_spacing_short', 'pad_exit_short'):
            T[k] += r[k]
        T['len'] += L; T['len_exact'] += Lx; T['complete'] += int(r['complete']); T['pads'] += r['pads']
        for k, v in r['ref'].items():
            T[k] += v
        if spc:
            T['par_lt0.6_mm'] += par_all; T['par_lt0.6_outside_neck_mm'] += par_out
        sens = cls.get(n) in ('USB', 'I2S_CLK', 'AUDIO') or n in ('/AUD_SDA', '/AUD_SCL')
        if sens:
            T['sens_B_island_void_mm'] += r['ref'].get('B_over_In2_island', 0) + r['ref'].get('B_over_In2_void', 0)
            T['sens_B_total_mm'] += sum(v for k, v in r['ref'].items() if k.startswith('B_'))
    ratios.sort()
    def pct(q):
        return round(ratios[min(len(ratios) - 1, int(math.ceil(q * len(ratios))) - 1)], 3) if ratios else None
    R['total'] = dict({k: (round(v, 2) if isinstance(v, float) else v) for k, v in T.items()}, nets=len(nets),
                      exact_pct=round(100 * T['len_exact'] / T['len'], 4) if T['len'] else None,
                      max_dev_deg=max([r['max_dev_deg'] for r in R['nets'].values()] or [0]),
                      ratio_median=pct(0.5), ratio_p95=pct(0.95), ratio_max=ratios[-1] if ratios else None, ratio_n=len(ratios),
                      ratio_gt14=[(n, r['ratio']) for n, r in R['nets'].items() if r['ratio'] and r['ratio'] > 1.4],
                      vias_per_complete_net=round(sum(r['vias'] for r in R['nets'].values() if r['complete']) / max(1, T['complete']), 2))
    if a.drc:
        d = json.load(open(a.drc))
        vc = collections.Counter(v['type'] for v in d.get('violations', []))
        un = d.get('unconnected_items', [])
        unn = sum(1 for v in un if any(any('[%s]' % n in it['description'] for n in nets) for it in v['items']))
        R['drc'] = dict(violations=sum(vc.values()), by_type=dict(vc), unconnected_total=len(un), unconnected_these_nets=unn)
    if a.manifest:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import route_oct_lock as LK
        man = json.load(open(a.manifest)); st = collections.defaultdict(list)
        for n in nets:
            st[stage_of[n]].append(n)
        R['lock'] = {}
        if man.get('mode') == 'continue':      # continuation manifest: C0 = all input copper, later stages = their added items
            R['lock'] = {k: dict(ok=v['ok'], items=v['items']) for k, v in LK.cont_lock(a.board, man).items()}
        for s_, info in ([] if man.get('mode') == 'continue' else man['stages'].items()):
            h, k = LK.copper_hash(a.board, st[s_])
            R['lock'][s_] = dict(ok=h == info['copper_sha256'], items=k)
    if a.rules:
        R['rules'] = {os.path.basename(x): hashlib.sha256(open(x, 'rb').read()).hexdigest() == hashlib.sha256(open(y, 'rb').read()).hexdigest()
                      for x, y in zip(a.rules, a.project_rules)}
    if a.json:
        json.dump(R, open(a.json, 'w'), indent=1)
    t = R['total']
    print(json.dumps({k: v for k, v in t.items()}, indent=None))
    for k in ('drc', 'lock', 'rules'):
        if k in R:
            print(k, R[k])


if __name__ == '__main__':
    main()
