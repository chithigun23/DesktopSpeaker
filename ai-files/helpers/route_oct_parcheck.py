#!/usr/bin/env python3
"""route_oct_parcheck.py BOARD.kicad_pcb GEO.json NETFILE [--gap 0.4] [--min-len 3] [--json OUT]
Independent near-parallel and stitching check (does not import the router; parses the saved board with r7_metrics.load).
  par   : per pair of different signal nets on one layer (at least one of them in NETFILE), the length of track running
          parallel (angle difference <= 12 deg) at an edge gap < --gap; pairs over --min-len are listed, split into pairs with
          a sensitive net (classes AUDIO, I2S_CLK, USB, /AUD_SDA, /AUD_SCL) and others; inside neck areas is not excluded
  gvia  : distance of every via of a NETFILE net in the sensitive set to the nearest GND via / plated GND hole
  bm83  : F.Cu track length of NETFILE nets inside the BM83 (U1) pad rectangle shrunk by 0.5 mm, outside the module's pad
          copper (own-pad stubs excepted), and vias inside the rectangle
Signal = net not GND and track width <= 0.35 mm (as r7_metrics).
"""
import sys, os, json, math, collections, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r7_metrics as R7
from shapely.geometry import LineString, Point, box, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

SENS_CLS = {'AUDIO', 'I2S_CLK', 'USB'}; SENS_NETS = {'/AUD_SDA', '/AUD_SCL'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board'); ap.add_argument('geo'); ap.add_argument('nets')
    ap.add_argument('--gap', type=float, default=0.4); ap.add_argument('--min-len', type=float, default=3.0); ap.add_argument('--json')
    a = ap.parse_args()
    D = R7.load(a.board); G = json.load(open(a.geo)); cls = G['netclass']
    nets = {l.split('#', 1)[0].split()[1] for l in open(a.nets) if len(l.split('#', 1)[0].split()) >= 2}
    sens = lambda n: cls.get(n) in SENS_CLS or n in SENS_NETS
    sg = [s for s in D['segs'] if R7.sig(s)]
    lines = [LineString([(s['x1'], s['y1']), (s['x2'], s['y2'])]) for s in sg]; tree = STRtree(lines)
    par = collections.defaultdict(float); mg = {}; mx = collections.defaultdict(float)
    for i, s in enumerate(sg):
        for j in tree.query(lines[i].buffer(a.gap + 0.5)):
            if j <= i:
                continue
            t = sg[j]
            if t['l'] != s['l'] or t['net'] == s['net'] or not ({s['net'], t['net']} & nets):
                continue
            a1 = math.atan2(s['y2'] - s['y1'], s['x2'] - s['x1']); a2 = math.atan2(t['y2'] - t['y1'], t['x2'] - t['x1'])
            if abs((a1 - a2 + math.pi / 2) % math.pi - math.pi / 2) > math.radians(12):
                continue
            ov = lines[i].intersection(lines[j].buffer(a.gap + (s['w'] + t['w']) / 2 - 1e-6, cap_style='flat'))
            if ov.length < 0.05:
                continue
            k = tuple(sorted((s['net'], t['net'])) + [s['l']]); par[k] += ov.length; mx[k] = max(mx[k], ov.length)
            mg[k] = min(mg.get(k, 9), lines[i].distance(lines[j]) - (s['w'] + t['w']) / 2)
    rows = [dict(a=k[0], b=k[1], layer=k[2], mm=round(v, 2), longest=round(mx[k], 2), min_gap=round(mg[k], 3), sensitive=sens(k[0]) or sens(k[1]))
            for k, v in sorted(par.items(), key=lambda x: -x[1]) if v > a.min_len]
    # stitching
    gp = [(v['x'], v['y']) for v in D['vias'] if v['net'] == 'GND'] + [(p['x'], p['y']) for fp in D['fps'] for p in fp['pads'] if p['net'] == 'GND' and p['type'] == 'thru_hole']
    gv = sorted(((round(min(math.hypot(v['x'] - x, v['y'] - y) for x, y in gp), 3), v['net'], round(v['x'], 3), round(v['y'], 3))
                 for v in D['vias'] if v['net'] in nets and sens(v['net'])), reverse=True)
    # BM83
    u1 = [p for p in G['pads'] if p['ref'] == 'U1' and 'F.Cu' in p['poly']]
    bd = unary_union([Polygon(r[0]) for p in u1 for r in p['poly']['F.Cu']]).bounds
    rect = box(bd[0] + 0.5, bd[1] + 0.5, bd[2] - 0.5, bd[3] - 0.5)
    rect_np = rect.difference(unary_union([Polygon(r[0]) for p in u1 for r in p['poly']['F.Cu']]))   # module pad copper excepted
    bm = collections.defaultdict(float)
    for s in D['segs']:
        if s['l'] == 'F.Cu' and s['net'] in nets:
            L = LineString([(s['x1'], s['y1']), (s['x2'], s['y2'])]).intersection(rect_np).length
            if L > 0:
                bm[s['net']] += L
    bmv = [(v['net'], v['x'], v['y']) for v in D['vias'] if rect.contains(Point(v['x'], v['y'])) and (v['net'] in nets or v['net'] == 'GND')]
    R = dict(gap=a.gap, min_len=a.min_len,
             par_sensitive=[r for r in rows if r['sensitive']], par_other=[r for r in rows if not r['sensitive']],
             gvia=dict(n=len(gv), over_1p5=sum(1 for g in gv if g[0] > 1.5), worst=gv[:10]),
             bm83=dict(rect=[round(x, 3) for x in rect.bounds], fcu_mm={k: round(v, 3) for k, v in bm.items()}, vias_inside=bmv))
    print(json.dumps(R, indent=1))
    if a.json:
        json.dump(R, open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
