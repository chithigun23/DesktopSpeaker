#!/usr/bin/env python3
"""stencil_check.py PASTE.json OUT_PREFIX [THICKNESS_MM]   (venv python with shapely; run with -I)
Hand-assembly stencil check of the F.Paste layer dumped by paste_dump.py (one stainless stencil, default 0.10 mm,
laser cut, electropolished). Rules (ai-files/reports/hand-assembly-research-2026-11-01.md, section 1):
  area ratio AR = opening area / wall area = A / (P * T)  >= 0.66   (electropolished foil releases down to about 0.60)
  aspect ratio  = smallest opening width / T              >= 1.5
  thermal / exposed pads (IC/transistor/TVS SMD pad >= 0.8 mm2 and >= 2.5x the median pad of its part): paste coverage 50-75 % as window panes, web between panes >= 0.25 mm, pane side >= 0.5 mm,
  no paste over an open via hole.
Writes OUT_PREFIX.json and OUT_PREFIX.md; prints a one-line summary 'STENCIL fail N warn M'."""
import json, sys, collections, math
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

src, prefix = sys.argv[1], sys.argv[2]
T = float(sys.argv[3]) if len(sys.argv) > 3 else 0.10
AR_MIN, ASP_MIN, AR_EP = 0.66, 1.5, 0.60
d = json.load(open(src))

def mkpoly(pp):
    out = []
    for outer, holes in pp:
        if len(outer) >= 3:
            g = Polygon(outer, [h for h in holes if len(h) >= 3]).buffer(0)
            if not g.is_empty: out.append(g)
    return unary_union(out) if out else None

def comps(g):
    if g is None or g.is_empty: return []
    return list(g.geoms) if hasattr(g, 'geoms') else [g]

def minwidth(g):
    r = g.minimum_rotated_rectangle
    c = list(r.exterior.coords)
    e = [math.dist(c[i], c[i + 1]) for i in range(4)]
    return min(e), max(e)

# paste geometry: pads on F.Paste (copper outline grown by the paste margin) + footprint graphics on F.Paste
items = []   # (geom, ref, num)
for p in d['pads']:
    if not p['paste']: continue
    g = mkpoly(p['poly'])
    if g is None: continue
    mx, my = p['margin']
    if abs(mx) > 1e-6: g = g.buffer(mx, join_style=2)
    items.append((g, p['ref'], p['num']))
for s in d['shapes']:
    g = mkpoly(s['poly'])
    if g is not None: items.append((g, s['ref'], '(shape)'))
union = unary_union([g for g, _, _ in items])
aps = comps(union)

# owners of each aperture (reference designators) by intersection with the items
from shapely.strtree import STRtree
tree = STRtree([g for g, _, _ in items])
copper = [(mkpoly(p['poly']), p) for p in d['pads'] if p.get('fcu', True)]
copper = [(g, p) for g, p in copper if g is not None]
ctree = STRtree([g for g, _ in copper])

rows = []
for a in aps:
    owners = sorted({(items[i][1], items[i][2]) for i in tree.query(a) if items[i][0].intersects(a)})
    A = a.area; P = a.length; w, l = minwidth(a)
    ar = A / (P * T); asp = w / T
    rows.append({'refs': sorted({o[0] for o in owners}), 'pads': ['%s.%s' % o for o in owners], 'w': round(w, 3), 'l': round(l, 3),
                 'area': round(A, 4), 'perim': round(P, 3), 'ar': round(ar, 3), 'aspect': round(asp, 2),
                 'cx': round(a.centroid.x, 3), 'cy': round(a.centroid.y, 3)})

def ref_prefix(r): return ''.join(ch for ch in r if ch.isalpha())
fails = [r for r in rows if r['ar'] < AR_MIN or r['aspect'] < ASP_MIN]

# exposed / thermal pads: SMD pads >= 1.5 mm2 on ICs, transistors and D6 (TVS with EP); report coverage and panes
vias = [(Point(v['x'], v['y']).buffer(v['drill'] / 2, 16), v) for v in d['vias']]
ep = []
byfp = collections.defaultdict(list)
for g, p in copper: byfp[p['ref']].append(g.area)
def is_ep(g, p):
    a = sorted(byfp[p['ref']]); med = a[len(a) // 2]
    return p['attr'] == 1 and len(a) >= 5 and g.area >= 0.8 and g.area >= 2.5 * med and ref_prefix(p['ref']) in ('U', 'Q', 'D')
for g, p in copper:
    if not is_ep(g, p): continue
    panes = [c for c in comps(union.intersection(g.buffer(0.05)))]
    pa = sum(c.area for c in panes); cov = pa / g.area
    webs = []
    for i in range(len(panes)):
        for j in range(i + 1, len(panes)):
            webs.append(panes[i].distance(panes[j]))
    side = min((minwidth(c)[0] for c in panes), default=0)
    vin = [v for vg, v in vias if g.contains(Point(v['x'], v['y']))]
    vpaste = [v for vg, v in vias if g.contains(Point(v['x'], v['y'])) and vg.intersects(union)]
    probs = []
    if not (0.50 <= cov <= 0.75): probs.append('coverage %.0f %% outside 50-75 %%' % (cov * 100))
    if webs and min(webs) < 0.25: probs.append('web %.2f mm < 0.25' % min(webs))
    if panes and side < 0.5: probs.append('pane side %.2f mm < 0.5' % side)
    if vpaste: probs.append('%d open via holes under paste' % len(vpaste))
    ep.append({'pad': '%s.%s' % (p['ref'], p['num'] or '?'), 'net': p['net'], 'pad_mm2': round(g.area, 3), 'paste_mm2': round(pa, 3),
               'coverage_pct': round(cov * 100, 1), 'panes': len(panes), 'min_web': round(min(webs), 3) if webs else None,
               'min_pane_side': round(side, 3), 'vias_in_pad': len(vin), 'vias_under_paste': len(vpaste), 'problems': probs})

# grouped area-ratio table: by (rounded w x l)
grp = collections.OrderedDict()
for r in sorted(rows, key=lambda r: (r['ar'], r['w'], r['l'])):
    k = (round(r['w'], 2), round(r['l'], 2))
    gq = grp.setdefault(k, {'w': k[0], 'l': k[1], 'ar': r['ar'], 'aspect': r['aspect'], 'n': 0, 'refs': collections.Counter()})
    gq['n'] += 1
    for x in r['refs']: gq['refs'][x] += 1

warn_ar = [r for r in rows if AR_EP <= r['ar'] < AR_MIN]
summary = {'thickness_mm': T, 'apertures': len(rows), 'fail_ar_or_aspect': len(fails),
           'ar_between_0.60_0.66': len(warn_ar), 'ar_below_0.60': sum(1 for r in rows if r['ar'] < AR_EP),
           'aspect_below_1.5': sum(1 for r in rows if r['aspect'] < ASP_MIN),
           'thermal_pads': len(ep), 'thermal_pads_with_problems': sum(1 for e in ep if e['problems'])}
json.dump({'summary': summary, 'apertures': rows, 'fails': fails, 'thermal': ep,
           'groups': [{**g, 'refs': dict(g['refs'])} for g in grp.values()]}, open(prefix + '.json', 'w'), indent=1)

L = ['# Stencil aperture check (F.Paste, %.2f mm stainless, electropolished)' % T, '',
     'Generated by `stencil_check.py` from `%s`. Rules: area ratio >= 0.66 (electropolish releases to about 0.60), '
     'aspect (smallest width / thickness) >= 1.5; thermal pads 50-75 %% coverage in panes, web >= 0.25 mm, pane side >= 0.5 mm, '
     'no paste over open via holes (hand-assembly research 2026-11-01, section 1).' % src.split('/')[-1], '',
     '**Summary:** %(apertures)d apertures; %(fail_ar_or_aspect)d fail AR 0.66 or aspect 1.5 (AR 0.60-0.66: %(ar_between_0.60_0.66)d, '
     'AR < 0.60: %(ar_below_0.60)d, aspect < 1.5: %(aspect_below_1.5)d); thermal pads %(thermal_pads)d, with problems '
     '%(thermal_pads_with_problems)d.' % summary, '',
     '## Area-ratio table (apertures grouped by size, worst first)', '',
     '| opening w x l (mm) | area ratio | aspect | count | parts |', '|---|---|---|---|---|']
for g in grp.values():
    refs = sorted(g['refs'], key=lambda r: (ref_prefix(r), int(''.join(ch for ch in r if ch.isdigit()) or 0)))
    flag = ' **FAIL**' if (g['ar'] < AR_MIN or g['aspect'] < ASP_MIN) else ''
    L.append('| %.2f x %.2f | %.2f%s | %.2f | %d | %s |' % (g['w'], g['l'], g['ar'], flag, g['aspect'], g['n'],
             ', '.join(refs[:14]) + (' ... (+%d)' % (len(refs) - 14) if len(refs) > 14 else '')))
L += ['', '## Apertures failing AR 0.66 or aspect 1.5', '']
if fails:
    L += ['| pads | w x l (mm) | AR | aspect | centre (x, y) |', '|---|---|---|---|---|']
    for r in sorted(fails, key=lambda r: r['ar']):
        L.append('| %s | %.3f x %.3f | %.3f | %.2f | (%.2f, %.2f) |' % (', '.join(r['pads'][:6]), r['w'], r['l'], r['ar'], r['aspect'], r['cx'], r['cy']))
else:
    L.append('None.')
L += ['', '## Thermal / exposed pads (IC, transistor and TVS SMD pads >= 0.8 mm2 and >= 2.5x the median pad of the part)', '',
      '| pad | net | pad mm2 | paste mm2 | coverage | panes | min web | min pane side | vias in pad / under paste | verdict |',
      '|---|---|---|---|---|---|---|---|---|---|']
for e in sorted(ep, key=lambda e: e['pad']):
    L.append('| %s | %s | %.2f | %.2f | %.0f %% | %d | %s | %.2f | %d / %d | %s |' % (
        e['pad'], e['net'], e['pad_mm2'], e['paste_mm2'], e['coverage_pct'], e['panes'],
        '-' if e['min_web'] is None else '%.2f' % e['min_web'], e['min_pane_side'], e['vias_in_pad'], e['vias_under_paste'],
        'OK' if not e['problems'] else '; '.join(e['problems'])))
open(prefix + '.md', 'w').write('\n'.join(L) + '\n')
print('STENCIL fail %d warn %d thermal_problems %d apertures %d' % (len(fails), len(warn_ar), summary['thermal_pads_with_problems'], len(rows)))
