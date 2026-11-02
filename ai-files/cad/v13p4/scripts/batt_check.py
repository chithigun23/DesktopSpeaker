"""v13p4 battery study: pack clearances, envelope vs the PCB footprint, cradle/shell deltas, mass and centre of mass, print overhang audit.
Run (per variant, after build + check):  CAD_OUT=ai-files/cad/v13p4/4P freecadcmd ai-files/cad/v13p4/scripts/batt_check.py
Writes CAD_OUT/work/batt.json.  Masses are ESTIMATES (make_web_meta.py conventions + pack items below)."""
import os, json, math, struct
import Part
from FreeCAD import Vector as V
import numpy as np
OUT = os.environ['CAD_OUT'].rstrip('/') + '/'
W = OUT + 'work/'
m = json.load(open(W + 'meta.json')); P = m['params']
S = {o['name']: (o, Part.read(W + 'brep/' + o['file'])) for o in m['objs']}
batt = sorted(n for n in S if n.startswith('Battery_'))
cells = [n for n in batt if 'Cell' in n]
NC = len(cells)
res = dict(variant=os.path.basename(OUT.rstrip('/')), n_cells=NC, cradle=m.get('cradle'))

# ---- pack envelope (cells + PCM) and the PCB footprint
bb = None
for n in batt:
    b = S[n][1].BoundBox
    bb = b if bb is None else bb.united(b)
# OCC bounding boxes of B-spline cells are loose: use the exact cell envelope from the placement instead
pcb = m['pcb']; LW, LD = P['pcb_w'], P['pcb_d']
pcb_rect = (pcb['cx'] - LW / 2, pcb['cy'] - LD / 2, pcb['cx'] + LW / 2, pcb['cy'] + LD / 2)
def tight(shape):
    c = shape.common(Part.makeBox(400, 400, 400, V(-200, -200, -100)))
    pts = [v.Point for v in c.Vertexes]
    # sample faces for curved extents
    xs, ys, zs = [], [], []
    for f in c.Faces:
        u0, u1, v0, v1 = f.ParameterRange
        for i in range(9):
            for j in range(9):
                p = f.valueAt(u0 + (u1 - u0) * i / 8, v0 + (v1 - v0) * j / 8)
                xs.append(p.x); ys.append(p.y); zs.append(p.z)
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))
env = [tight(S[n][1]) for n in batt]
E = (min(e[0] for e in env), max(e[1] for e in env), min(e[2] for e in env), max(e[3] for e in env), min(e[4] for e in env), max(e[5] for e in env))
res['pack_envelope_mm'] = dict(x=(round(E[0], 2), round(E[1], 2)), y=(round(E[2], 2), round(E[3], 2)), z=(round(E[4], 2), round(E[5], 2)),
                               size=(round(E[1] - E[0], 2), round(E[3] - E[2], 2), round(E[5] - E[4], 2)))
ox = max(0.0, min(E[1], pcb_rect[2]) - max(E[0], pcb_rect[0])); oy = max(0.0, min(E[3], pcb_rect[3]) - max(E[2], pcb_rect[1]))
res['pcb_footprint'] = dict(rect_xy=[round(v, 2) for v in pcb_rect], pack_area_mm2=round((E[1] - E[0]) * (E[3] - E[2])),
                            overlap_area_mm2=round(ox * oy), overlap_fraction=round(ox * oy / ((E[1] - E[0]) * (E[3] - E[2])), 3),
                            vertical_gap_to_pcb_bottom=round(pcb['bot'] - E[5], 2))

# ---- clearances: every battery object vs every non-battery object (nearest 12) + named targets
groups = {}
for n, (o, s) in S.items():
    groups[n] = o['group']
def dmin(a, b):
    try:
        return a.distToShape(b)[0]
    except Exception:
        return None
near = {}
for n in batt:
    sb = S[n][1]
    box_ = sb.BoundBox; box_.enlarge(30)
    lst = []
    for k, (o, s) in S.items():
        if k in batt or not box_.intersect(s.BoundBox):
            continue
        d = dmin(sb, s)
        if d is not None:
            lst.append((round(d, 2), k))
    lst.sort()
    near[n] = lst[:12]
res['nearest'] = near
def grp_min(pred):
    best = None
    for n in batt:
        for d, k in near[n]:
            if pred(k) and (best is None or d < best[0]):
                best = (d, n, k)
    if best is None:     # not within 30 mm of any battery object: compute directly
        for n in batt:
            for k in S:
                if pred(k):
                    d = dmin(S[n][1], S[k][1])
                    if best is None or d < best[0]:
                        best = (round(d, 2), n, k)
    return best
targets = {
    'drivers ND65 (L/R)': lambda k: k.startswith('Driver_'),
    'driver screws/inserts': lambda k: 'DrvScrew' in k,
    'woofer chamber insert (partition)': lambda k: k == 'Insert_woofer_chamber',
    'woofer W3-2052SC': lambda k: k.startswith('Woofer_'),
    'PCB board': lambda k: groups.get(k) == 'pcb',
    'PCB components': lambda k: groups.get(k) == 'pcb_parts',
    'PCB standoffs/screws/inserts': lambda k: 'PcbScrew' in k,
    'feet studs/inserts': lambda k: 'Foot' in k,
    'SW101 rocker': lambda k: k.startswith('SW101'),
    'J5 harness (tube)': lambda k: k == 'Harness_J5_to_pack_schematic',
    'woofer harness (tube)': lambda k: k == 'Harness_woofer_leads_schematic',
    'grommet': lambda k: k.startswith('Grommet'),
    'lid': lambda k: k == 'Lid_rear',
}
res['clearance'] = {t: (None if b is None else dict(mm=round(b[0], 2), battery_obj=b[1], other=b[2])) for t, b in ((t, grp_min(f)) for t, f in targets.items())}
# cells vs the shell (cradle saddles / lips / stops: design gap 0.3 radial, 1.0 at the ends)
res['cells_to_shell_mm'] = round(min(dmin(S[n][1], S['Shell_Box'][1]) for n in batt), 3)
# J5 harness: length of the schematic route, distance to cells/PCM and to the woofer chamber air (from check.json)
hp = m['harness']['j5']
res['j5_harness_route_mm'] = round(sum(math.dist(a, b) for a, b in zip(hp[:-1], hp[1:])), 1)
hd = min(dmin(S['Harness_J5_to_pack_schematic'][1], S[n][1]) for n in batt if 'Cell' in n)
res['j5_harness_to_cells_mm'] = round(hd, 2)

# ---- mass and centre of mass (ESTIMATES)
def com(shape):
    sols = shape.Solids or [shape]
    v = sum(s.Volume for s in sols)
    if v <= 0:
        b = shape.BoundBox; return V(b.Center), 0.0
    c = V(0, 0, 0)
    for s in sols:
        c = c + s.CenterOfMass * s.Volume
    return c * (1.0 / v), v
items = []
def addm(label, g, c):
    items.append((label, g, c))
for n, (o, s) in S.items():
    c, v = com(s)
    gname = o['group']
    if n in ('Shell_Box', 'Lid_rear', 'Insert_woofer_chamber'):
        addm(n, v / 1000 * 1.27, c)                                     # PETG 100 % infill (make_web_meta convention)
    elif gname == 'drivers':
        addm(n, 180.0, c)
    elif gname == 'woofer':
        addm(n, 250.0, c)
    elif 'Cell' in n:
        addm(n, 69.0, c)                                                # 50S about 69 g (UNVERIFIED); P45B 70 g max (datasheet)
    elif n == 'Battery_PCM_board':
        addm(n, 8.0 + 3.0 * NC, c)                                      # PCM + nickel + wrap + leads, ESTIMATE (CM 1S2P pack 152.8 g -> about 15 g over 2 cells)
    elif gname == 'pcb':
        addm(n, P['pcb_w'] * P['pcb_d'] * 1.6 / 1000 * 1.85 + 30.0, c)
    elif n.startswith(('Insert_M3', 'Screw_', 'Standoff_', 'Foot_standoff')):
        addm(n, v / 1000 * (8.5 if n.startswith('Insert_') else 7.85), c)
    elif n.startswith('Grille_'):
        addm(n, v / 1000 * 7.85, c)
tot = sum(g for _, g, _ in items)
C = V(0, 0, 0)
for _, g, c in items:
    C = C + c * g
C = C * (1.0 / tot)
pack_g = sum(g for l, g, _ in items if l.startswith('Battery_'))
res['mass'] = dict(total_g=round(tot), pack_g=round(pack_g), shell_g=round(S['Shell_Box'][1].Volume / 1000 * 1.27, 1),
                   com_xyz=(round(C.x, 2), round(C.y, 2), round(C.z, 2)), shell_cm3=round(S['Shell_Box'][1].Volume / 1000, 2),
                   note='estimates: PETG 100 % infill, drivers/woofer maker masses, 50S 69 g each (unverified), pack overhead 8 + 3 g per cell (estimate); PCB, hardware and grilles as make_web_meta.py')
# tipping: CoM height vs the feet footprint (feet at x +-68, y 25 / 135)
res['mass']['tip_margin_front_deg'] = round(math.degrees(math.atan2(C.y - 25.0, C.z + 15.0)), 1)

# ---- print overhang audit of the shell (print orientation STL: baffle down, +Y up): downward facets steeper than 45 deg, off the bed
def stl_tris(fn):
    d = open(fn, 'rb').read()
    n = struct.unpack('<I', d[80:84])[0]
    a = np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]), count=n)
    return a['v'].astype(float)
def overhang(fn, z_bed_tol=0.3):
    T = stl_tris(fn)
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); ar = np.linalg.norm(nrm, axis=1) / 2
    nz = nrm[:, 2] / np.maximum(np.linalg.norm(nrm, axis=1), 1e-12)
    zmin = T[:, :, 2].min(1)
    sel = (nz < -math.sqrt(0.5) - 1e-3) & (zmin > z_bed_tol)
    flat = sel & (nz < -0.999)
    return dict(overhang_area_mm2=round(float(ar[sel].sum()), 1), flat_bridge_area_mm2=round(float(ar[flat].sum()), 1), facets=int(sel.sum()),
                zones=sorted({round(float(z), 1) for z in zmin[sel]})[:40])
res['print_overhang'] = {p['name']: overhang(OUT + 'print/DesktopSpeaker_%s.stl' % p['name']) for p in m['prints']}
res['prints'] = m['prints']
json.dump(res, open(W + 'batt.json', 'w'), indent=1)
print('BATT', json.dumps({k: res[k] for k in ('variant', 'n_cells', 'pack_envelope_mm', 'pcb_footprint', 'clearance', 'cells_to_shell_mm', 'j5_harness_route_mm',
                                              'j5_harness_to_cells_mm', 'mass')}, indent=1))
print('OVH', json.dumps(res['print_overhang']))
