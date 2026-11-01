"""exitprobe.py GEO.json NETLIST.txt [REF ...] : outward escape probe on F.Cu.
For every pad on a stripped signal net of the listed parts: a straight 0.25 mm track from the pad edge outward for 1.0 mm
(0.2 mm when the pad lies in a neck area, as the router necks; fine-pitch pads: outward along the long axis only, rule FO1; elongated pads: both ends of the long axis; square-ish: 4 directions)
must clear every foreign pad, track, via and non-GND F.Cu zone fill by the router's clearance (route_oct_rules.clr_strict,
clr_neck inside the neck_ic courtyards/NECK areas). GND fills are ignored (they refill). Pass = at least one direction is free.
Prints per part: tested pads, failing pads (with the blocking item)."""
import sys, json, math, collections
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import route_oct_rules as RR
from shapely.geometry import Polygon, LineString, Point, MultiPolygon
from shapely.strtree import STRtree
from shapely.ops import unary_union
G = json.load(open(sys.argv[1])); NETS = {l.split('#')[0].strip() for l in open(sys.argv[2]) if l.split('#')[0].strip()}
REFS = sys.argv[3:] or ['U9', 'U2', 'U11', 'U4', 'U8', 'J7', 'U20', 'C207', 'R225', 'R226', 'R108', 'C182']
L, W = 1.0, 0.25
import os; DETAIL = bool(os.environ.get('DETAIL'))
def polys(pl):
    out = []
    for poly in pl:
        try:
            P = Polygon(poly[0], poly[1:]);  P = P if P.is_valid else P.buffer(0)
            if not P.is_empty: out.append(P)
        except Exception: pass
    return out
dru = sys.argv[1].replace('.geo.json', '.kicad_dru')
try: neck_refs, neck_areas = RR.neck_targets(dru)
except Exception: neck_refs, neck_areas = [], []
NECK = []
for r in neck_refs:
    c = G['courtyard'].get(r)
    if c and 'F' in c['poly']: NECK += polys(c['poly']['F'])
for a in G['areas']:
    if a['name'] in neck_areas: NECK += polys(a['outline'])
NECK = unary_union(NECK) if NECK else None
obs = []   # (geom, net, cls, type)
for p in G['pads']:
    if 'F.Cu' in p['poly']:
        for P in polys(p['poly']['F.Cu']): obs.append((P, p['net'], p['cls'], 'Pad', p['ref'] + '-' + p['num']))
for t in G['tracks']:
    if t['layer'] == 'F.Cu':
        obs.append((LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]).buffer(t['w'] / 2), t['net'], t['cls'], 'Track', 'trk ' + t['net']))
for v in G['vias']:
    obs.append((Point(v['x'], v['y']).buffer(v['d'] / 2), v['net'], v['cls'], 'Via', 'via ' + v['net']))
for z in G['zones']:
    if z['cls'] == 'GND' or z['teardrop'] or 'F.Cu' not in z['fills']: continue
    for P in polys(z['fills']['F.Cu']): obs.append((P, z['net'], z['cls'], 'Zone', 'zone ' + (z['name'] or z['net'])))
tree = STRtree([o[0] for o in obs])
npads = collections.Counter(p['ref'] for p in G['pads'])
cent = {r: (c['x'], c['y']) for r, c in G['courtyard'].items()}
def dirs(p):
    sx, sy = p['sx'], p['sy']; r = math.radians(p['rot'])
    # pad long axis in board coords (y down; KiCad rotation CCW on screen)
    ax = (math.cos(r), -math.sin(r)) if sx >= sy else (math.sin(r), math.cos(r))
    long_, short = max(sx, sy), min(sx, sy)
    fine = npads[p['ref']] >= 8 and short <= 0.45
    if fine:
        cx, cy = cent[p['ref']]; s = 1 if (p['x'] - cx) * ax[0] + (p['y'] - cy) * ax[1] >= 0 else -1
        return [((s * ax[0], s * ax[1]), long_ / 2)]
    if long_ > 1.3 * short:
        return [(ax, long_ / 2), ((-ax[0], -ax[1]), long_ / 2)]
    perp = (-ax[1], ax[0])
    return [(ax, long_ / 2), ((-ax[0], -ax[1]), long_ / 2), (perp, short / 2), ((-perp[0], -perp[1]), short / 2)]
def probe(p):
    res = []
    for (dx, dy), h in dirs(p):
        a = (p['x'] + dx * h, p['y'] + dy * h); b = (a[0] + dx * L, a[1] + dy * L)
        w = RR.NECK_W if (NECK is not None and NECK.contains(Point(p['x'], p['y']))) else W
        seg = LineString([a, b]); tr = seg.buffer(w / 2, cap_style=2)
        worst = None
        for i in tree.query(tr.buffer(2.1)):
            g, net, cls, typ, name = obs[i]
            if net == p['net'] and net: continue
            inneck = NECK is not None and NECK.intersects(g.buffer(0.01)) and NECK.intersects(tr)
            c = (RR.clr_neck if inneck else RR.clr_strict)(p['cls'], p['net'], cls, typ)
            d = g.distance(tr)
            if d < c - 1e-6 and (worst is None or c - d > worst[0]): worst = (round(c - d, 3), name, round(d, 3), c)
        res.append(((round(dx, 2), round(dy, 2)), worst))
        if DETAIL and worst: print('     ', p['ref'], p['num'], (round(dx, 2), round(dy, 2)), worst)
    return res
tot = {}
for ref in REFS:
    ps = [p for p in G['pads'] if p['ref'] == ref and p['net'] in NETS and not p['net'].startswith('unconnected')]
    bad = []
    for p in ps:
        r = probe(p)
        if all(w for _, w in r): bad.append((p['num'], p['net'].split('/')[-1], min((w for _, w in r), key=lambda w: w[0])))
    tot[ref] = (len(ps), bad)
    print('%-5s signal pads %2d  no-exit %2d  %s' % (ref, len(ps), len(bad), '; '.join('%s %s [%s short %.3f]' % (n, net, w[1], w[0]) for n, net, w in bad)))
print('TOTAL no-exit pads', sum(len(b) for _, b in tot.values()), 'of', sum(n for n, _ in tot.values()))
