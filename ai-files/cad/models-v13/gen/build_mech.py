"""models-v13 mechanical models (enclosure-level items). Run: freecadcmd build_mech.py
Frames (mm): each model's origin is its mounting reference, documented per model. Writes ../3d/<name>.step."""
import os, sys, json, math
sys.path.insert(0, os.environ['M13_GEN'])
from m13lib import *
import Part

OUT = os.path.join(os.environ['M13_ROOT'], '3d')
ONLY = set(os.environ.get('M13_ONLY', '').split(',')) - {''}
report = {}


def emit(name, parts):
    if ONLY and name not in ONLY:
        return
    p = os.path.join(OUT, name + '.step')
    comp = save(parts, p, name)
    report[name] = dict(bbox=bbox(comp), solids=len(comp.Solids))


def hexprism(af, h, z0=0.0):
    r = af / math.sqrt(3)
    pts = [V(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), z0) for a in range(0, 360, 60)]
    pts.append(pts[0])
    return Part.Face(Part.makePolygon(pts)).extrude(V(0, 0, h))


# ------------------------------------------------------------- Tang Band W3-2052SC (Parts Express 299-572)
def woofer():
    """Origin: driver axis on the front face of the factory foam gasket (= contact plane with the baffle), +z = radiating
    side, body toward -z. Seller data (PE item JSON): square frame 82.55 across, 4 holes on a 96.52 bolt circle
    (= 68.25 square), cutout 76.2, depth 44.45 (frame front to magnet back). Photo estimates (+-1.5 mm, UNVERIFIED):
    gasket 3.3, frame block 13.3, corner radius 4, holes 3.4 with 7.3 counterbore, opening 73.7, cone 54, basket 72
    wide x 16.6, magnet cup 35.5 x 14.5."""
    P = []
    g = 3.3
    gas = rbox(-41.275, -41.275, -g, 41.275, 41.275, 0, 4.0).cut(cyl(73.7 / 2, g + 1, 0, 0, -g - 0.5))
    frame = rbox(-41.275, -41.275, -g - 13.3, 41.275, 41.275, -g, 4.0)
    frame = frame.cut(cyl(73.7 / 2, 3.0, 0, 0, -g - 3.0))          # front recess for cone/surround
    frame = frame.cut(cyl(64.0 / 2, 13.3, 0, 0, -g - 13.3))         # throat
    hp = 96.52 / 2 / math.sqrt(2)
    for sx in (-1, 1):
        for sy in (-1, 1):
            frame = frame.cut(cyl(1.7, 20, sx * hp, sy * hp, -g - 15))
            frame = frame.cut(cyl(3.65, 2.0, sx * hp, sy * hp, -g - 2.0))
            gas = gas.cut(cyl(3.65, g + 1, sx * hp, sy * hp, -g - 0.5))
    P.append((gas, (0.15, 0.15, 0.15)))
    P.append((frame.removeSplitter(), BLACK))
    zb0 = -g - 13.3; zb1 = -g - 44.45 + 14.5
    bask = cyl(36.0, zb0 - zb1, 0, 0, zb1).cut(cyl(33.5, zb0 - zb1 + 1, 0, 0, zb1 - 0.5))
    for k in range(8):
        a = k * 45 + 22.5
        w = box(-5, 30, zb1 + 2.5, 5, 40, zb0 - 2.5)
        w.rotate(V(0, 0, 0), V(0, 0, 1), a)
        bask = bask.cut(w)
    bask = bask.fuse(cyl(36.0, 2.0, 0, 0, zb1)).cut(cyl(17.0, 3, 0, 0, zb1 - 0.5))  # rear ring/motor seat
    P.append((bask.removeSplitter(), DARK))
    cup = cyl(35.5 / 2, 14.5, 0, 0, -g - 44.45).cut(cyl(1.0, 2, 0, 0, -g - 44.45 - 0.5))
    P.append((cup, BLACK))
    cone_ = Part.makeCone(54 / 2, 25.0 / 2, 9.0, V(0, 0, -g - 3.0), V(0, 0, -1))
    cone_ = cone_.fuse(Part.makeSphere(20.0, V(0, 0, -g - 3.0 - 17.0)).common(cyl(14, 4, 0, 0, -g - 3.5)))  # dust cap / centre
    sur = Part.makeTorus((73.7 / 2 + 54 / 2) / 2, (73.7 / 2 - 54 / 2) / 2, V(0, 0, -g - 3.0), V(0, 0, 1)).common(cyl(40, 4, 0, 0, -g - 3.0))
    P.append((cone_.fuse(sur).removeSplitter(), (0.18, 0.18, 0.2)))
    tab = box(29.5, -2, zb1 + 6, 33.5, 2, zb1 + 12)
    P.append((tab, RED))
    return P


emit('TangBand_W3-2052SC', woofer())


# ------------------------------------------------------------- 21700 cells
def cell(d, h, wrap):
    """Origin: centre of the negative (flat) end, +z toward the positive cap. Cap button dia 8 x 0.6 assumed."""
    c = cyl(d / 2, h - 0.6, 0, 0, 0)
    c = c.cut(Part.makeTorus(d / 2, 0.4, V(0, 0, h - 3.0), V(0, 0, 1)))   # crimp groove
    btn = cyl(4.0, 0.6, 0, 0, h - 0.6)
    neg = cyl(d / 2 - 0.6, 0.05, 0, 0, -0.05)
    return [(c, wrap), (btn, METAL), (neg, METAL)]


# Samsung INR21700-50S (SDI introduction 2021 p.2): dia 21.25 max, height 70.62 max -> modelled at max
emit('Cell_Samsung_INR21700-50S', cell(21.25, 70.62, (0.20, 0.35, 0.65)))
# Molicel INR21700-P45B (datasheet v1.2 p.1): dia 21.55 max, height 70.15 max -> modelled at max
emit('Cell_Molicel_INR21700-P45B', cell(21.55, 70.15, (0.25, 0.25, 0.28)))


# ------------------------------------------------------------- CW Industries GRB112B802BR1 rocker
def rocker():
    """Origin: cutout centre on the panel FRONT face, +z out of the panel. CW drawing R13-112B8-02-BRR-L1 rev 3
    (ai-files/datasheets/CW_GRB112B802BR1.pdf): bezel dia 25 (+-1), rocker dia 19.8, boot skirt dia 19.0, top 11.5
    (+-1) above the panel on the high side, 22.4 (+-1) from the panel to the terminal tips, terminals 4.8 x 0.8 at
    7.1 pitch, 8.3 long, hole dia 2.2. Body behind the panel: 17.5 square at the clips (scaled), panel 1.5-2.5.
    Bezel thickness 2.5 and the low-side height (9.0) scaled from the side view."""
    P = []
    bez = cyl(12.5, 2.5, 0, 0, 0)
    boot = cyl(9.5, 2.5, 0, 0, 2.5)
    # rocker cap: cylinder 19.8 cut by a tilted plane: 11.5 high side (+x), 9.0 low side (-x)
    cap = cyl(9.9, 9.0, 0, 0, 2.5)
    plane = box(-15, -15, 0, 15, 15, 20)
    plane.rotate(V(0, 0, 0), V(0, 1, 0), -math.degrees(math.atan2(2.5, 19.8)))
    plane.translate(V(0, 0, 10.25))
    cap = cap.cut(plane)
    P.append((bez.fuse(boot).removeSplitter(), BLACK))
    P.append((cap, RED))
    body = cyl(10.0, 2.2, 0, 0, -2.2).fuse(box(-8.75, -8.75, -14.1, 8.75, 8.75, -2.2))
    for sx in (-1, 1):
        clip = Part.Face(Part.makePolygon([V(sx * 8.75, -3, -3.0), V(sx * 10.6, -3, -3.0), V(sx * 8.75, -3, -11.0), V(sx * 8.75, -3, -3.0)])).extrude(V(0, 6, 0))
        body = body.fuse(clip)
    P.append((body.removeSplitter(), BLACK))
    for x in (-7.1, 0.0, 7.1):
        t = box(x - 0.4, -2.4, -22.4, x + 0.4, 2.4, -14.1).cut(cyl(1.1, 1, x - 0.5, 0, -20.5, V(1, 0, 0)))
        P.append((t, TIN))
    return P


emit('CW_GRB112B802BR1_Rocker', rocker())


# ------------------------------------------------------------- fasteners
def socket_cap(L):
    """ISO 4762 M3 x L: head dia 5.5, k 3.0, s 2.5 hex socket (t 1.3), thread dia 3.0 (modelled plain).
    Origin: under-head bearing face on the axis; head +z, shank -z."""
    head = cyl(2.75, 3.0, 0, 0, 0).cut(hexprism(2.5, 1.3, 3.0 - 1.3))
    try:
        head = head.makeChamfer(0.2, [e for e in head.Edges if abs(e.BoundBox.ZMin - 3.0) < 1e-6 and e.BoundBox.XLength > 5])
    except Exception:
        pass
    sh = cyl(1.5, L, 0, 0, -L)
    return [(head.fuse(sh).removeSplitter(), (0.15, 0.15, 0.15))]


emit('Screw_ISO4762_M3x10', socket_cap(10))
emit('Screw_ISO4762_M3x16', socket_cap(16))


def insert_ruthex():
    """Ruthex RX-M3x5.7 brass heat-set insert (retailer table, column mapping unconfirmed): OD 4.6 knurl, L 5.7,
    M3 thread (bore 2.5 modelled), 2 knurl bands with a waist dia 3.9. Origin: top face centre, body toward -z."""
    b = cyl(2.3, 5.7, 0, 0, -5.7).cut(Part.makeTorus(2.3, 0.35, V(0, 0, -2.85), V(0, 0, 1)))
    for k in range(18):
        f = box(2.05, -0.12, -5.6, 2.4, 0.12, -0.1)
        f.rotate(V(0, 0, 0), V(0, 0, 1), k * 20 + (10 if k % 2 else 0))
        b = b.cut(f)
    b = b.cut(cyl(1.25, 6.0, 0, 0, -5.85))
    return [(b, BRASS)]


emit('Insert_Ruthex_RX-M3x5.7', insert_ruthex())


def spacer_ff(L=10.0):
    """Wurth 970100321 WA-SSTII spacer M3, 5.5 AF, L 10, female/female through thread (bore 2.5 modelled).
    Origin: bottom face centre, +z."""
    s = hexprism(5.5, L).cut(cyl(1.25, L + 1, 0, 0, -0.5))
    return [(s, METAL)]


emit('Spacer_Wurth_970100321_M3x10_FF', spacer_ff())


def stud_mf():
    """Wurth 971120321 WA-SSTIE M/F stud M3, 5.5 AF, body 12, male thread 6. Origin: body bottom (stud root),
    body +z, male stud -z."""
    s = hexprism(5.5, 12.0).cut(cyl(1.25, 6.0, 0, 0, 6.01)).fuse(cyl(1.5, 6.0, 0, 0, -6.0))
    return [(s.removeSplitter(), METAL)]


emit('Stud_Wurth_971120321_M3x12_MF', stud_mf())


def foot():
    """Adhesive rubber disc 12 x 3 (maker not selected; 3M Bumpon family assumed). Origin: top (adhesive) face, -z."""
    f = cyl(6.0, 3.0, 0, 0, -3.0)
    try:
        f = f.makeFillet(0.8, [e for e in f.Edges if abs(e.BoundBox.ZMax + 3.0) < 1e-6])
    except Exception:
        pass
    return [(f, (0.12, 0.12, 0.12))]


emit('Foot_Rubber_12x3', foot())


def knob_standin():
    """Encoder knob NOT SELECTED: stand-in D30 x 14 with a 6 mm D bore (flat at 4.5), 8 deep, as used in CAD v11.1.
    Origin: knob underside on the axis, +z."""
    k = cyl(15.0, 14.0, 0, 0, 0)
    try:
        k = k.makeFillet(1.5, [e for e in k.Edges if abs(e.BoundBox.ZMin - 14.0) < 1e-6])
    except Exception:
        pass
    bore = cyl(3.0, 8.0, 0, 0, -0.01).common(box(-3, -3, -0.02, 1.5, 3, 8.0))
    k = k.cut(bore)
    k = k.cut(box(-0.4, 9, 13.6, 0.4, 14, 14.1))  # pointer line
    return [(k, (0.15, 0.15, 0.15))]


emit('Knob_StandIn_D30x14_6mmD', knob_standin())

json.dump(report, sys.stdout, indent=1)
print()
