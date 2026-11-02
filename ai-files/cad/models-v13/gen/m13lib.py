"""models-v13 builder helpers (run inside freecadcmd).
Frame: KiCad footprint-model convention: x right, y up (= -y of the footprint editor), z up from the board top,
origin = footprint origin, mm. Each model is a list of (solid, colour) pairs; save() writes a STEP whose
solids carry STYLED_ITEM colours (post-processed, because freecadcmd has no view providers)."""
import re
import Part
from FreeCAD import Vector, Matrix

V = Vector

# KiCad-like material colours (r, g, b in 0..1)
BLACK = (0.10, 0.10, 0.10)
DARK = (0.20, 0.20, 0.22)
GREY = (0.55, 0.55, 0.58)
METAL = (0.80, 0.80, 0.82)
TIN = (0.86, 0.86, 0.86)
GOLD = (0.85, 0.68, 0.25)
BRASS = (0.78, 0.62, 0.30)
COPPER = (0.80, 0.50, 0.30)
WHITE = (0.93, 0.92, 0.88)
IVORY = (0.95, 0.92, 0.80)
RED = (0.75, 0.10, 0.10)
BLUE = (0.15, 0.30, 0.65)
GREEN = (0.10, 0.45, 0.20)
NICKEL = (0.72, 0.73, 0.75)


def box(x0, y0, z0, x1, y1, z1):
    return Part.makeBox(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), V(min(x0, x1), min(y0, y1), min(z0, z1)))


def cbox(cx, cy, z0, lx, ly, h):
    return Part.makeBox(lx, ly, h, V(cx - lx / 2, cy - ly / 2, z0))


def cyl(r, h, x=0, y=0, z=0, d=V(0, 0, 1)):
    return Part.makeCylinder(r, h, V(x, y, z), d)


def cone(r1, r2, h, x=0, y=0, z=0, d=V(0, 0, 1)):
    return Part.makeCone(r1, r2, h, V(x, y, z), d)


def rbox(x0, y0, z0, x1, y1, z1, r):
    """box with vertical edges rounded by r"""
    b = box(x0, y0, z0, x1, y1, z1)
    if r <= 0:
        return b
    edges = [e for e in b.Edges if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > 1e-6]
    return b.makeFillet(r, edges)


def stadium(w, h, length, y0, zc, axis='y'):
    """stadium (slot) prism: width w (x), height h (z), extruded along +y from y0 by length, centred x=0, z=zc"""
    r = h / 2
    c = box(-w / 2 + r, y0, zc - r, w / 2 - r, y0 + length, zc + r)
    c = c.fuse(cyl(r, length, -w / 2 + r, y0, zc, V(0, 1, 0)))
    c = c.fuse(cyl(r, length, w / 2 - r, y0, zc, V(0, 1, 0)))
    return c.removeSplitter()


def rot(shape, axis, deg, centre=V(0, 0, 0)):
    s = shape.copy()
    s.rotate(centre, axis, deg)
    return s


def move(shape, dx, dy, dz):
    s = shape.copy()
    s.translate(V(dx, dy, dz))
    return s


def solids_of(parts):
    out = []
    for shp, col in parts:
        for so in (shp.Solids if shp.Solids else [shp]):
            out.append((so, col))
    return out


def save(parts, path, name='model'):
    """parts: list of (shape, rgb). Writes STEP with per-solid colours."""
    sol = solids_of(parts)
    comp = Part.makeCompound([s for s, _ in sol])
    comp.exportStep(path)
    txt = open(path).read()
    # item order of the shape representation = compound order
    flat = re.sub(r"\s+", " ", txt)
    breps, ctx = [], None
    for m in re.finditer(r"#(\d+) ?= ?(?:ADVANCED_BREP_SHAPE_REPRESENTATION|SHAPE_REPRESENTATION|MANIFOLD_SURFACE_SHAPE_REPRESENTATION) ?\( ?'[^']*' ?, ?\(([^)]*)\) ?, ?#(\d+) ?\)", flat):
        ids = [int(x.strip()[1:]) for x in m.group(2).split(',') if x.strip()]
        bb = [i for i in ids if re.search(r"#%d ?= ?(MANIFOLD_SOLID_BREP|BREP_WITH_VOIDS)" % i, flat)]
        if bb:
            breps += bb; ctx = int(m.group(3))
    if len(breps) != len(sol):
        raise RuntimeError('brep count %d != solids %d' % (len(breps), len(sol)))
    nid = max(int(x) for x in re.findall(r"#(\d+)\s*=", txt)) + 1
    lines = []
    styled = []
    cache = {}
    for (s, col), b in zip(sol, breps):
        key = tuple(round(c, 3) for c in col)
        if key not in cache:
            c0 = nid; nid += 7
            lines += ["#%d = COLOUR_RGB('',%.3f,%.3f,%.3f);" % (c0, *key),
                      "#%d = FILL_AREA_STYLE_COLOUR('',#%d);" % (c0 + 1, c0),
                      "#%d = FILL_AREA_STYLE('',(#%d));" % (c0 + 2, c0 + 1),
                      "#%d = SURFACE_STYLE_FILL_AREA(#%d);" % (c0 + 3, c0 + 2),
                      "#%d = SURFACE_SIDE_STYLE('',(#%d));" % (c0 + 4, c0 + 3),
                      "#%d = SURFACE_STYLE_USAGE(.BOTH.,#%d);" % (c0 + 5, c0 + 4),
                      "#%d = PRESENTATION_STYLE_ASSIGNMENT((#%d));" % (c0 + 6, c0 + 5)]
            cache[key] = c0 + 6
        lines.append("#%d = STYLED_ITEM('color',(#%d),#%d);" % (nid, cache[key], b))
        styled.append(nid); nid += 1
    lines.append("#%d = MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',(%s),#%d);"
                 % (nid, ','.join('#%d' % x for x in styled), ctx))
    txt = txt.replace('ENDSEC;\nEND-ISO-10303-21;', '\n'.join(lines) + '\nENDSEC;\nEND-ISO-10303-21;')
    if 'MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION' not in txt:
        # data section end may differ in whitespace
        i = txt.rfind('ENDSEC;')
        txt = txt[:i] + '\n'.join(lines) + '\n' + txt[i:]
    # product name
    txt = re.sub(r"PRODUCT\('[^']*','[^']*'", "PRODUCT('%s','%s'" % (name, name), txt, count=1)
    open(path, 'w').write(txt)
    return comp


def bbox(shape):
    try:
        b = shape.optimalBoundingBox(False, False)
    except Exception:
        b = shape.BoundBox
    return [round(v, 3) for v in (b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax)]
