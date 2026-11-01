#!/usr/bin/env python3
"""r7_metrics.py BOARD.kicad_pcb [--json OUT]
Independent routing-quality metrics used by the R7 routing run (see ai-files/reports/routing-review-r6q.md).
Pure Python + shapely + numpy (not the KiCad python). Create a venv: python3 -m venv V && V/bin/pip install shapely numpy
Metrics (all in mm):
  ref   : B.Cu signal length by what lies beneath on In2 (GND / other island / void), total and for sensitive nets;
          F.Cu signal length over In1 GND vs In1 void
  par   : near-parallel runs between different signal nets on the same layer (edge gap <= 0.30 mm, angle diff <= 12 deg)
  ang   : length of segments >= 5 mm by angle class (exact grid / 0.6-5 / 5-15 / 15-22.5 deg off); joints sharper than 80 deg
  gvia  : distance from each sensitive-net via to the nearest GND via / GND through-hole pad
  sw    : closest same-layer distance of selected sensitive nets to switch-node copper
  bm83  : F.Cu track length inside the BM83 pad rectangle (shrunk 1 mm)
Signal = net not GND and track width <= 0.35 mm.
"""
import sys, re, math, json, collections
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely.prepared import prep
from shapely.strtree import STRtree

TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')
def parse(path):
    st = [[]]
    for m in TOK.finditer(open(path, encoding='utf-8').read()):
        t = m.group(0)
        if t == '(': st.append([])
        elif t == ')': x = st.pop(); st[-1].append(x)
        else: st[-1].append(t[1:-1] if t[0] == '"' else t)
    return st[0][0]
def kids(n, k): return [c for c in n if isinstance(c, list) and c and c[0] == k]
def kid(n, k):
    r = kids(n, k); return r[0] if r else None
def NN(n):
    if not n or len(n) < 2: return ''
    return n[-1] if len(n) > 2 else n[1]
f = float

def load(path):
    B = parse(path); segs = []; vias = []; zones = []; fps = []
    for s in kids(B, 'segment'):
        a = kid(s, 'start'); b = kid(s, 'end')
        segs.append(dict(x1=f(a[1]), y1=f(a[2]), x2=f(b[1]), y2=f(b[2]), w=f(kid(s, 'width')[1]), l=kid(s, 'layer')[1], net=NN(kid(s, 'net'))))
    for s in kids(B, 'via'):
        a = kid(s, 'at'); vias.append(dict(x=f(a[1]), y=f(a[2]), net=NN(kid(s, 'net'))))
    for z in kids(B, 'zone'):
        td = kid(z, 'attr'); ist = bool(td and kid(td, 'teardrop'))
        nn = kid(z, 'net_name') or kid(z, 'net')
        fl = []
        for p in kids(z, 'filled_polygon'):
            pts = [(f(q[1]), f(q[2])) for q in kid(p, 'pts') if isinstance(q, list) and q[0] == 'xy']
            fl.append((kid(p, 'layer')[1], pts))
        zones.append(dict(net=NN(nn) if nn else '', fills=fl, td=ist))
    for fp in kids(B, 'footprint'):
        ref = None
        for p in kids(fp, 'property'):
            if p[1] == 'Reference': ref = p[2]
        at = kid(fp, 'at'); x, y = f(at[1]), f(at[2]); rot = f(at[3]) if len(at) > 3 else 0.0
        c, s_ = math.cos(math.radians(rot)), math.sin(math.radians(rot)); pads = []
        for p in kids(fp, 'pad'):
            pa = kid(p, 'at'); px, py = f(pa[1]), f(pa[2])
            pads.append(dict(x=x + px * c + py * s_, y=y - px * s_ + py * c, net=NN(kid(p, 'net')), type=p[2]))
        fps.append(dict(ref=ref, x=x, y=y, pads=pads))
    return dict(segs=segs, vias=vias, zones=zones, fps=fps)

def union(D, layer, pred):
    out = []
    for z in D['zones']:
        if z['td'] or not pred(z['net']): continue
        for l, pts in z['fills']:
            if l == layer and len(pts) >= 3:
                p = Polygon(pts); out.append(p if p.is_valid else p.buffer(0))
    return unary_union(out) if out else Polygon()

SENS = re.compile(r'I2S|AUD_S|BT_AUDIO|HP_OUT|VMID|USB_D|USB_AUDIO|AUX|U24-VIN|XI$|XO$')
def sig(s): return s['net'] != 'GND' and s['w'] <= 0.35

def metrics(path):
    D = load(path); R = {}
    in1 = prep(union(D, 'In1.Cu', lambda n: n == 'GND'))
    in2g = prep(union(D, 'In2.Cu', lambda n: n == 'GND'))
    in2o = prep(union(D, 'In2.Cu', lambda n: n != 'GND'))
    ref = collections.defaultdict(float); sens = collections.defaultdict(lambda: collections.defaultdict(float)); fv = 0.0; fg = 0.0
    for s in D['segs']:
        if not sig(s): continue
        ln = math.hypot(s['x2'] - s['x1'], s['y2'] - s['y1']); n = max(1, int(ln / 0.4))
        for i in range(n):
            t = (i + .5) / n; p = Point(s['x1'] + (s['x2'] - s['x1']) * t, s['y1'] + (s['y2'] - s['y1']) * t); d = ln / n
            if s['l'] == 'F.Cu':
                if in1.contains(p): fg += d
                else: fv += d
            elif s['l'] == 'B.Cu':
                k = 'GND' if in2g.contains(p) else 'island' if in2o.contains(p) else 'void'
                ref[k] += d
                if SENS.search(s['net']): sens[s['net']][k] += d
    R['ref'] = dict(Bcu_total={k: round(v, 1) for k, v in ref.items()}, Fcu_over_In1={'GND': round(fg, 1), 'void': round(fv, 1)},
                    Bcu_sensitive={n: {k: round(v, 1) for k, v in c.items()} for n, c in sorted(sens.items())})
    # parallel runs
    sg = [s for s in D['segs'] if sig(s)]; lines = [LineString([(s['x1'], s['y1']), (s['x2'], s['y2'])]) for s in sg]; tree = STRtree(lines)
    par = collections.defaultdict(float); mg = {}
    for i, s in enumerate(sg):
        for j in tree.query(lines[i].buffer(0.8)):
            if j <= i: continue
            t = sg[j]
            if t['l'] != s['l'] or t['net'] == s['net']: continue
            a1 = math.atan2(s['y2'] - s['y1'], s['x2'] - s['x1']); a2 = math.atan2(t['y2'] - t['y1'], t['x2'] - t['x1'])
            if abs((a1 - a2 + math.pi / 2) % math.pi - math.pi / 2) > math.radians(12): continue
            ov = lines[i].intersection(lines[j].buffer(0.3 + (s['w'] + t['w']) / 2, cap_style='flat'))
            if ov.length < 0.5: continue
            k = tuple(sorted((s['net'], t['net'])) + [s['l']]); par[k] += ov.length
            mg[k] = min(mg.get(k, 9), lines[i].distance(lines[j]) - (s['w'] + t['w']) / 2)
    R['par'] = [dict(a=k[0], b=k[1], layer=k[2], mm=round(v, 1), min_gap=round(mg[k], 3)) for k, v in sorted(par.items(), key=lambda x: -x[1])[:25]]
    # angles
    h = collections.Counter()
    for s in D['segs']:
        L = math.hypot(s['x2'] - s['x1'], s['y2'] - s['y1'])
        if L < 5: continue
        a = math.degrees(math.atan2(s['y2'] - s['y1'], s['x2'] - s['x1'])) % 180; d = min(abs(a - x) for x in (0, 45, 90, 135, 180))
        h['exact' if d < .6 else '0.6-5' if d < 5 else '5-15' if d < 15 else '15-22.5'] += L
    ep = collections.defaultdict(list)
    for i, s in enumerate(D['segs']):
        ep[(s['l'], s['net'], round(s['x1'], 3), round(s['y1'], 3))].append((i, 0)); ep[(s['l'], s['net'], round(s['x2'], 3), round(s['y2'], 3))].append((i, 1))
    acute = []
    for k, v in ep.items():
        if len(v) != 2: continue
        (i1, e1), (i2, e2) = v; s1, s2 = D['segs'][i1], D['segs'][i2]
        d1 = (s1['x2'] - s1['x1'], s1['y2'] - s1['y1']) if e1 == 0 else (s1['x1'] - s1['x2'], s1['y1'] - s1['y2'])
        d2 = (s2['x2'] - s2['x1'], s2['y2'] - s2['y1']) if e2 == 0 else (s2['x1'] - s2['x2'], s2['y1'] - s2['y2'])
        n1 = math.hypot(*d1); n2 = math.hypot(*d2)
        if n1 < 1e-6 or n2 < 1e-6: continue
        a = math.degrees(math.acos(max(-1, min(1, (d1[0] * d2[0] + d1[1] * d2[1]) / (n1 * n2)))))
        if a < 80: acute.append(dict(deg=round(a), layer=k[0], net=k[1], x=k[2], y=k[3]))
    R['ang'] = dict(len_ge5mm_by_class={k: round(v) for k, v in h.items()}, joints_lt80=len(acute), joints_lt30=sum(1 for a in acute if a['deg'] < 30), acute=sorted(acute, key=lambda a: a['deg'])[:40])
    # ground vias
    gp = [(v['x'], v['y']) for v in D['vias'] if v['net'] == 'GND'] + [(p['x'], p['y']) for fp in D['fps'] for p in fp['pads'] if p['net'] == 'GND' and p['type'] == 'thru_hole']
    gv = []
    for v in D['vias']:
        if SENS.search(v['net']): gv.append((round(min(math.hypot(v['x'] - x, v['y'] - y) for x, y in gp), 1), v['net'], round(v['x'], 1), round(v['y'], 1)))
    gv.sort(reverse=True); R['gvia'] = dict(sensitive_vias=len(gv), worst=gv[:15])
    # switch proximity for ILIM_HIZ / FB nets
    swp = re.compile(r'/SW1$|/SW2$|U14-L|U15-L|U25-SW'); vic = re.compile(r'ILIM_HIZ|U14-FB|U15-FB|TS_SENSE|PROG')
    swg = [(s['net'], s['l'], LineString([(s['x1'], s['y1']), (s['x2'], s['y2'])]).buffer(s['w'] / 2)) for s in D['segs'] if swp.search(s['net'])]
    for z in D['zones']:
        if z['td'] or not swp.search(z['net']): continue
        for l, pts in z['fills']:
            if len(pts) >= 3: swg.append((z['net'], l, Polygon(pts).buffer(0)))
    best = {}
    for s in D['segs']:
        if not vic.search(s['net']): continue
        g = LineString([(s['x1'], s['y1']), (s['x2'], s['y2'])]).buffer(s['w'] / 2)
        for n2, l2, g2 in swg:
            if l2 != s['l']: continue
            d = g.distance(g2); k = (s['net'], n2, s['l'])
            if d < best.get(k, 9e9): best[k] = d
    R['sw'] = [dict(victim=k[0], sw=k[1], layer=k[2], mm=round(v, 2)) for k, v in sorted(best.items(), key=lambda x: x[1])[:10]]
    # BM83
    inner = box(90.4, 27.4, 109.3, 40.4); acc = collections.defaultdict(float)
    for s in D['segs']:
        if s['l'] == 'F.Cu': acc[s['net']] += LineString([(s['x1'], s['y1']), (s['x2'], s['y2'])]).intersection(inner).length
    R['bm83'] = {k: round(v, 1) for k, v in acc.items() if v > 0}
    return R

if __name__ == '__main__':
    r = metrics(sys.argv[1])
    if '--json' in sys.argv: json.dump(r, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
    print(json.dumps(r, indent=1))
