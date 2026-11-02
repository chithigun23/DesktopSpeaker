"""Measure every footprint's 3D model in the footprint-local KiCad 3D frame (x right, y up = -y_fp, z up from
the board top surface, mm). Run with freecadcmd:
  freecadcmd measure.py   (reads env M13_INV, M13_LIB3D, M13_OUT, optional M13_OVERRIDE json, M13_REFS)
KiCad transform (verified against kicad-cli STEP export, see verify_transform in MODELS.md):
  p = offset + Rz(-rz) * Ry(-ry) * Rx(-rx) * (scale * p_model)
Outputs per ref: bbox of the placed model, slice-based lead/pad check (SMD slice just above z 0, THT slice at
z -0.8 inside the board), per-solid bboxes for the largest solids."""
import os, json, math
import FreeCAD, Part
from FreeCAD import Vector, Matrix

INV = os.environ['M13_INV']
LIB = os.environ['M13_LIB3D']
OUT = os.environ['M13_OUT']
OVR = json.load(open(os.environ['M13_OVERRIDE'])) if os.environ.get('M13_OVERRIDE') else {}
REFS = set(os.environ['M13_REFS'].split(',')) if os.environ.get('M13_REFS') else None

inv = json.load(open(INV))
cache = {}


def load(path):
    p = path.replace('${KIPRJMOD}/kicad-library/3d', LIB).replace('${KIPRJMOD}', os.path.dirname(LIB))
    if p not in cache:
        if not os.path.exists(p):
            cache[p] = None
        else:
            s = Part.Shape(); s.read(p); cache[p] = s
    return cache[p], p


def kicad_matrix(off, scl, rot):
    m = Matrix()
    m.scale(Vector(*scl))
    rx, ry, rz = [math.radians(-a) for a in rot]
    r = Matrix(); r.rotateX(rx); m = r.multiply(m)
    r = Matrix(); r.rotateY(ry); m = r.multiply(m)
    r = Matrix(); r.rotateZ(rz); m = r.multiply(m)
    t = Matrix(); t.move(Vector(*off)); m = t.multiply(m)
    return m


def obb(sh):
    try:
        return sh.optimalBoundingBox(False, False)
    except Exception:
        return sh.BoundBox


def bb(b):
    return [round(b.XMin, 3), round(b.YMin, 3), round(b.ZMin, 3), round(b.XMax, 3), round(b.YMax, 3), round(b.ZMax, 3)]


def pad_rect(p, fprot):
    a = (p['rot'] - fprot) % 180
    w, h = p['size'][0], p['size'][1] if len(p['size']) > 1 else p['size'][0]
    if abs(a - 90) < 1:
        w, h = h, w
    cx, cy = p['at'][0], -p['at'][1]
    return cx, cy, w, h


def regions(shape, z):
    out = []
    try:
        wires = shape.slice(Vector(0, 0, 1), z)
    except Exception:
        return out
    for w in wires:
        if not w.isClosed():
            continue
        b = w.BoundBox
        try:
            f = Part.Face(w); a = f.Area; c = f.CenterOfMass
        except Exception:
            a = b.XLength * b.YLength; c = b.Center
        out.append(dict(c=[c.x, c.y], bb=[b.XMin, b.YMin, b.XMax, b.YMax], area=a))
    return out


res = {}
memo = {}
for fp in inv:
    ref = fp['ref']
    if REFS and ref not in REFS:
        continue
    models = [m for m in fp['models'] if not m.get('hide')]
    if ref in OVR:
        models = OVR[ref]
    key = json.dumps([fp['lib'], models, fp['pads'], fp['rot'] % 360 if False else 0], sort_keys=True)
    if key in memo:
        res[ref] = memo[key]; continue
    r = dict(lib=fp['lib'], models=[m['path'].split('/')[-1] for m in models])
    shapes = []
    for m in models:
        s, p = load(m['path'])
        if s is None:
            r.setdefault('missing', []).append(p); continue
        s = s.copy(); s.transformShape(kicad_matrix(m['offset'], m['scale'], m['rotate']))
        shapes.append(s)
    if not shapes:
        res[ref] = r; continue
    comp = Part.makeCompound(shapes)
    B = obb(comp)
    r['bbox'] = bb(B)
    r['n_solids'] = len(comp.Solids)
    sol = sorted(comp.Solids, key=lambda s: -s.Volume)[:6]
    r['solids'] = [dict(bbox=bb(obb(s)), vol=round(s.Volume, 3)) for s in sol]
    tht = any(p['type'] in ('thru_hole',) for p in fp['pads'])
    smd_pads = [p for p in fp['pads'] if p['type'] == 'smd' and p['num'] and ('F.Cu' in p.get('layers', ['F.Cu'])) and p['shape'] != 'custom']
    checks = []
    # SMD check: slice at board level
    if smd_pads:
        z = max(B.ZMin, 0.0) + 0.03
        regs = regions(comp, z) + regions(comp, z + 0.07) + regions(comp, z + 0.17)
        pcx = sum(p['at'][0] for p in smd_pads) / len(smd_pads)
        pcy = sum(-p['at'][1] for p in smd_pads) / len(smd_pads)
        r['slice_regions'] = len(regs)
        for p in smd_pads:
            cx, cy, w, h = pad_rect(p, fp['rot'])
            # lateral axis: across the pad's short axis; for square-ish pads across the radial direction
            if min(w, h) / max(w, h) <= 0.8:
                radial_x = w >= h
            else:
                radial_x = abs(cx - pcx) >= abs(cy - pcy)
            central = math.hypot(cx - pcx, cy - pcy) < 0.3 and min(w, h) / max(w, h) > 0.8
            best = None
            for g in regs:
                gx, gy = g['c']
                if abs(gx - cx) <= w / 2 + 0.3 and abs(gy - cy) <= h / 2 + 0.3:
                    gw = g['bb'][2] - g['bb'][0]; gh = g['bb'][3] - g['bb'][1]
                    if gw > w + 1.0 and gh > h + 1.0:
                        continue  # body bottom, not a lead
                    if central:
                        lat = max(abs(gx - cx), abs(gy - cy)); lon = 0.0
                    elif radial_x:
                        lat, lon = abs(gy - cy), abs(gx - cx)
                    else:
                        lat, lon = abs(gx - cx), abs(gy - cy)
                    if best is None or lat < best[0]:
                        best = (lat, lon)
            checks.append(dict(pad=p['num'], kind='smd', lat=None if best is None else round(best[0], 3),
                               lon=None if best is None else round(best[1], 3)))
        r['slice_z_smd'] = round(z, 3)
    tht_pads = [p for p in fp['pads'] if p['type'] in ('thru_hole', 'np_thru_hole') and p.get('drill')]
    if tht_pads and B.ZMin < -0.5:
        regs = regions(comp, -0.8)
        for p in tht_pads:
            cx, cy = p['at'][0], -p['at'][1]
            d = [x for x in p['drill'] if isinstance(x, str) and x.replace('.', '', 1).replace('-', '', 1).isdigit()]
            dmax = max(float(x) for x in d) if d else 1.0
            best = None
            for g in regs:
                gx, gy = g['c']
                dd = math.hypot(gx - cx, gy - cy)
                if dd < dmax and (best is None or dd < best):
                    best = dd
            checks.append(dict(pad=p['num'], kind=p['type'], dist=None if best is None else round(best, 3)))
    r['pad_checks'] = checks
    cu = [p for p in fp['pads'] if p['num'] and 'F.Cu' in p.get('layers', ['F.Cu']) or p['type'] == 'thru_hole']
    if cu:
        px = sum(p['at'][0] for p in cu) / len(cu); py = sum(-p['at'][1] for p in cu) / len(cu)
        r['pad_centroid'] = [round(px, 3), round(py, 3)]
        r['bbox_centre_minus_pads'] = [round((B.XMin + B.XMax) / 2 - px, 3), round((B.YMin + B.YMax) / 2 - py, 3)]
    smd = [c for c in checks if c['kind'] == 'smd']
    th = [c for c in checks if c['kind'] != 'smd']
    r['smd_missing'] = [c['pad'] for c in smd if c['lat'] is None]
    r['smd_max_lat'] = max([c['lat'] for c in smd if c['lat'] is not None], default=None)
    r['tht_missing'] = [c['pad'] for c in th if c['dist'] is None]
    r['tht_max_dist'] = max([c['dist'] for c in th if c['dist'] is not None], default=None)
    res[ref] = r; memo[key] = r
json.dump(res, open(OUT, 'w'), indent=1)
print('measured', len(res))
