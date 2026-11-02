"""Per-reference enclosure fit check (v13).  Run: CAD_OUT=... BOARD_STEP=... LAYOUT=... [OLD_STEP=... OLD_LAYOUT=...] freecadcmd fit_check.py
For every footprint with a 3D model in the board STEP: top z, gap to the top wall, min distance to the enclosure bodies
(shell, insert, lid, screws, spacers, inserts, knob/dish, rocker, gasket, harness, drivers, woofer, battery). Writes work/fit.json."""
import os, json, math, Part
from FreeCAD import Vector as V
OUT = os.environ.get('CAD_OUT', '/home/chithi/Desktop/DesktopSpeaker/ai-files/cad/v13/').rstrip('/') + '/'
W = OUT + 'work/'
m = json.load(open(W + 'meta.json')); P = m['params']
pcx, pcy, zb = m['pcb']['cx'], m['pcb']['cy'], m['pcb']['bot']
def refsolids(step, layout):
    LJ = json.load(open(layout)); comp = Part.read(step)
    rects = [(r, p['rect']) for r, p in LJ['parts'].items()]
    own = {}
    for so in comp.Solids:
        bb = so.BoundBox
        if bb.XLength > 0.8 * LJ['board']['w'] and bb.YLength > 0.8 * LJ['board']['d']:
            continue
        cu, cv = (bb.XMin + bb.XMax) / 2, (bb.YMin + bb.YMax) / 2
        best = None
        for r, q in rects:
            if q[0] - 0.6 <= cu <= q[2] + 0.6 and q[1] - 0.6 <= cv <= q[3] + 0.6:
                a = (q[2] - q[0]) * (q[3] - q[1])
                if best is None or a < best[0]: best = (a, r)
        own.setdefault(best[1] if best else 'UNASSIGNED', []).append(so)
    res = {}
    for r, sols in own.items():
        c = Part.makeCompound(sols); c.translate(V(pcx, pcy, zb)); res[r] = c
    return res, LJ
new, LJ = refsolids(os.environ['BOARD_STEP'], os.environ['LAYOUT'])
ENC = {}
for o in m['objs']:
    if o['group'] in ('pcb', 'pcb_parts'): continue
    ENC[o['name']] = Part.read(W + 'brep/' + o['file'])
# split the shell into named zones only by distance reporting (one solid)
ZT_IN = P['H'] - P['wall']
rows = []
ARTEFACTS = []
for r, c in sorted(new.items()):
    bb = c.BoundBox
    near = []
    for n, s in ENC.items():
        b2 = s.BoundBox; b3 = V(0, 0, 0)
        bbx = bb.__class__(bb); bbx.enlarge(6.0)
        if not bbx.intersect(b2): continue
        try:
            cand = [so for so in (s.Solids or [s]) if bbx.intersect(so.BoundBox)] or [s]
            d = min(c.distToShape(so)[0] for so in cand)
            if d < 0.05:      # v13: guard against BRepExtrema artefacts (0.0 reported for disjoint solids)
                if max(c.common(so).Volume for so in cand) < 1e-6:
                    d_alt = min(so.distToShape(Part.Vertex(v_.Point))[0] for so in cand for v_ in c.Vertexes)
                    if d_alt > 1.0:
                        ARTEFACTS.append((r, n, round(d_alt, 2)))
                        d = d_alt
        except Exception as e:
            d = -1
        near.append((round(d, 2), n))
    near.sort()
    rows.append(dict(ref=r, top_z=round(bb.ZMax, 2), height_above_pcb=round(bb.ZMax - zb - P['pcb_t'], 2), gap_top_wall=round(ZT_IN - bb.ZMax, 2),
                     bbox=[round(x, 2) for x in (bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax)], nearest=near[:4]))
old = {}
if os.environ.get('OLD_STEP'):
    o, OLJ = refsolids(os.environ['OLD_STEP'], os.environ['OLD_LAYOUT'])
    for r, c in o.items():
        b = c.BoundBox; old[r] = [(b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, b.ZMax]
for row in rows:
    if row['ref'] in old:
        b = row['bbox']; q = old[row['ref']]
        row['moved_mm'] = round(math.hypot((b[0] + b[3]) / 2 - q[0], (b[1] + b[4]) / 2 - q[1]), 2)
    else:
        row['moved_mm'] = None
json.dump(dict(rows=rows, zt_in=ZT_IN, pcb_top=zb + P['pcb_t'], dist_artefacts=ARTEFACTS), open(W + 'fit.json', 'w'), indent=1)
print('refs', len(rows))
for row in sorted(rows, key=lambda r: r['nearest'][0][0] if r['nearest'] else 99)[:40]:
    print(row['ref'], 'top', row['top_z'], 'gapTop', row['gap_top_wall'], 'moved', row['moved_mm'], row['nearest'])
print('--- tallest')
for row in sorted(rows, key=lambda r: r['gap_top_wall'])[:12]:
    print(row['ref'], row['top_z'], row['gap_top_wall'])
print('--- moved > 1 mm')
for row in rows:
    if row['moved_mm'] is None or row['moved_mm'] > 1.0:
        print(row['ref'], row['moved_mm'], row['gap_top_wall'], row['nearest'][:2])
