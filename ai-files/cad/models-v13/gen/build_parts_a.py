"""Build models-v13 parametric models (tier a, board parts). Run: freecadcmd build_parts_a.py
Writes ../3d/<name>.step and prints a JSON line per model with its bbox."""
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.environ['M13_GEN'])
from m13lib import *
import Part

OUT = os.path.join(os.environ.get('M13_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '3d')
ONLY = set(os.environ.get('M13_ONLY', '').split(',')) - {''}
report = {}


def emit(name, parts):
    if ONLY and name not in ONLY:
        return
    p = os.path.join(OUT, name + '.step')
    comp = save(parts, p, name)
    report[name] = dict(bbox=bbox(comp), solids=len(comp.Solids), file=p)


# ---------------------------------------------------------------- JST B2P-VH (J9-J11)
def jst_vh(n=2):
    """JST VH top-entry header B<n>P-VH, drawing JST eVH.pdf p.3 (ai-files/datasheets/JST_VH.pdf):
    B = 3.96*(n-1)+3.9 housing length, depth 8.5 incl. latch, post top 10.9 above board, tail 3.7,
    base 3.2 high (scaled from side view), rear wall/lock 1.7 thick, 9.4 high, inset 1.2 per end.
    Origin pin 1, posts along +x, wall at +y (KiCad Fab: body y 2.0..-4.8, wall 2.0..3.7)."""
    p = 3.96
    x0, x1 = -1.95, p * (n - 1) + 1.95
    parts = []
    base = rbox(x0, -4.8, 0.0, x1, 2.0, 3.2, 0.3)
    # underside relief channel and post bosses: simple stand-off pads 0.3 high
    base = base.cut(box(x0 + 0.6, -4.2, 0.0, x1 - 0.6, 1.4, 0.3))
    wall = box(x0 + 1.2, 2.0, 0.0, x1 - 1.2, 3.3, 9.4)
    # lock ramp on the outer wall face (latch), 0.4 proud, z 7.4..9.4
    ramp = Part.makePolygon([V(0, 3.3, 7.4), V(0, 3.7, 8.6), V(0, 3.7, 9.4), V(0, 3.3, 9.4), V(0, 3.3, 7.4)])
    ramp = Part.Face(ramp).extrude(V(min(2.6, x1 - x0 - 3.4), 0, 0))
    ramp.translate(V((x0 + x1) / 2 - min(2.6, x1 - x0 - 3.4) / 2, 0, 0))
    housing = base.fuse(wall).fuse(ramp).removeSplitter()
    parts.append((housing, IVORY))
    t = 1.14
    for i in range(n):
        x = i * p
        post = cbox(x, 0, -3.7 + 0.4, t, t, 10.9 - 0.4 - (-3.7 + 0.4))
        tip = Part.makeLoft([Part.makePolygon([V(x - t / 2, -t / 2, 10.5), V(x + t / 2, -t / 2, 10.5), V(x + t / 2, t / 2, 10.5), V(x - t / 2, t / 2, 10.5), V(x - t / 2, -t / 2, 10.5)]),
                             Part.makePolygon([V(x - 0.3, -0.3, 10.9), V(x + 0.3, -0.3, 10.9), V(x + 0.3, 0.3, 10.9), V(x - 0.3, 0.3, 10.9), V(x - 0.3, -0.3, 10.9)])], True)
        tail = Part.makeLoft([Part.makePolygon([V(x - 0.3, -0.3, -3.7), V(x + 0.3, -0.3, -3.7), V(x + 0.3, 0.3, -3.7), V(x - 0.3, 0.3, -3.7), V(x - 0.3, -0.3, -3.7)]),
                              Part.makePolygon([V(x - t / 2, -t / 2, -3.3), V(x + t / 2, -t / 2, -3.3), V(x + t / 2, t / 2, -3.3), V(x - t / 2, t / 2, -3.3), V(x - t / 2, -t / 2, -3.3)])], True)
        parts.append((post.fuse(tip).fuse(tail).removeSplitter(), TIN))
    return parts


emit('JST_B2P-VH_LF_SN', jst_vh(2))


# ---------------------------------------------------------------- gull-wing SOP generator
def gullwing(D, E1, E, A, A1, e, n_side, b, c, L, name_axis='y', pin1_mark=True):
    """Leads on the +-x sides, rows along y (pin 1 at top-left, KiCad TSSOP orientation).
    D body length (y), E1 body width (x), E lead tip span (x), A max height, A1 standoff, e pitch,
    b lead width, c lead thickness, L foot length."""
    parts = []
    body_h0 = A1
    body = box(-E1 / 2, -D / 2, body_h0, E1 / 2, D / 2, A)
    # draft-like chamfer on the top edges
    try:
        top = [ed for ed in body.Edges if abs(ed.Vertexes[0].Point.z - A) < 1e-6 and abs(ed.Vertexes[1].Point.z - A) < 1e-6]
        body = body.makeChamfer(min(0.1, (A - A1) / 4), top)
    except Exception:
        pass
    if pin1_mark:
        dim = cyl(0.25, 0.05, -E1 / 2 + 0.6, D / 2 - 0.6, A - 0.05)
        body = body.cut(dim)
    parts.append((body, BLACK))
    zc = A1 + (A - A1) * 0.45  # lead exit height
    xe = E1 / 2
    xt = E / 2
    xf = xt - L
    for side in (-1, 1):
        for i in range(n_side):
            y = (n_side - 1) / 2 * e - i * e
            pts = [V(xe - 0.05, 0, zc + c / 2), V(xf - 0.25, 0, zc + c / 2), V(xf, 0, c), V(xt, 0, c), V(xt, 0, 0),
                   V(xf - c * 0.6, 0, 0), V(xf - 0.25 - c * 0.6, 0, zc - c / 2), V(xe - 0.05, 0, zc - c / 2), V(xe - 0.05, 0, zc + c / 2)]
            f = Part.Face(Part.makePolygon(pts)).extrude(V(0, b, 0))
            f.translate(V(0, y - b / 2, 0))
            if side < 0:
                f.rotate(V(0, y, 0), V(0, 0, 1), 180)
            parts.append((f, TIN))
    return parts


# PCM1862DBTR, TI DBT (TSSOP-30, 0.5 mm pitch): JEDEC MO-153 / TI DBT0030A: D 7.8 (7.7-7.9), E1 4.4 (4.3-4.5),
# E 6.4 (6.2-6.6), A 1.2 max (body top modelled at 1.10 nominal), A1 0.10 (0.05-0.15), b 0.22 (0.17-0.27),
# c 0.15 (0.09-0.20), L 0.60 (0.45-0.75). PCM1862 datasheet SLASEB2 p.1: "TSSOP (30) 7.80 mm x 4.40 mm".
emit('TSSOP-30_DBT_4.4x7.8_P0.5_TI', gullwing(D=7.8, E1=4.4, E=6.4, A=1.10, A1=0.10, e=0.5, n_side=15, b=0.22, c=0.15, L=0.60))


# ---------------------------------------------------------------- TE 1977066-1 (SW100)
def te_1977066():
    """TE 1977066-1 R/A SMT tact switch, TE customer drawing 1977066 rev C1 p.1 (ai-files/datasheets/TE_1977066-1_datasheet.pdf):
    body 4.00 (case) / 4.50 over the bracket, depth 2.55, height 3.30, actuator dia 2.00 at z 1.70, 0.85 proud of the
    body front; pegs dia 0.70, 0.45 below the board, 4.25 apart, 2.05 behind the actuator tip; terminals 0.65/0.50/0.65
    wide, outer edges 3.00 apart (centres +-1.175); land pattern: terminal pads 1.80 long with the peg-hole centre line
    on their front edge, bracket pads 1.2 x 1.3 at x +-1.2..2.5 starting 0.3 in front of the hole line.
    Built with the actuator toward -y, then rotated 180 deg about z at emit: final actuator toward +y (3D),
    origin = terminal pad-row centre. NOTE the project footprint puts the peg holes 1.5 from the pads on the
    side AWAY from the actuator (drawing: 0.9, actuator side)."""
    P = []
    tip = -2.95; front = tip + 0.85; rear = front + 2.55
    case = box(-2.0, front, 0.15, 2.0, rear, 3.30)
    case = case.cut(box(-1.2, front - 0.01, 0.15, 1.2, front + 0.4, 0.6))  # front relief under the actuator
    P.append((case, BLACK))
    act = cyl(1.0, 0.85 + 0.6, 0, front + 0.6, 1.70, V(0, -1, 0))
    P.append((act, IVORY))
    # steel bracket: side plates + top strap + front solder tabs
    br = box(-2.25, front + 0.2, 0.0, -2.0, rear - 0.2, 3.2).fuse(box(2.0, front + 0.2, 0.0, 2.25, rear - 0.2, 3.2))
    br = br.fuse(box(-2.25, front + 0.2, 3.2, 2.25, front + 1.0, 3.35))
    for sx in (-1, 1):
        br = br.fuse(box(sx * 1.4, -2.1, 0.0, sx * 2.25, -1.5, 0.15))
    P.append((br.removeSplitter(), TIN))
    for sx in (-1, 1):
        peg = cyl(0.35, 0.45 + 0.15, sx * 2.125, -0.9, -0.45 + 0.35).fuse(Part.makeSphere(0.35, V(sx * 2.125, -0.9, -0.1)))
        P.append((peg, BLACK))
    for x, w in ((-1.175, 0.65), (0.0, 0.50), (1.175, 0.65)):
        t = box(x - w / 2, rear - 0.15, 0.0, x + w / 2, rear, 1.2).fuse(box(x - w / 2, -0.3, 0.0, x + w / 2, rear + 0.05, 0.15))
        P.append((t.removeSplitter(), TIN))
    return P


# Final orientation: actuator toward +y (3D) = KiCad -y = toward the board edge, as the footprint courtyard/Fab intend.
# The current draft footprint has its peg holes on the opposite side (+1.5 KiCad y): see MODELS.md / report.
emit('TE_1977066-1', [(rot(sh, V(0, 0, 1), 180), c) for sh, c in te_1977066()])


# ---------------------------------------------------------------- Molex Micro-Fit 3.0 R/A 43650-0300 (J5)
def microfit_ra(n=3):
    """Micro-Fit 3.0 right-angle header, 1 row, n circuits. Dims from the LXW H3000S14-03 drawing supplied as
    ai-files/datasheets/Molex_43650-0300_C503478.pdf (Micro-Fit compatible; genuine Molex drawing not obtained):
    housing 3.00*n+3.65 (12.65) long, 9.90 deep (pins 0.98 from the rear face), body 4.37 high, latch to 5.57,
    cavities on 3.00 pitch at z 2.4, pins 0.64 sq, tails 3.20 below board, peg dia 3.0 at 4.32 toward the mating
    face. Frame = KiCad footprint (pin 1 at origin, pins along +x, mating face at y +8.92 (3D))."""
    P = []
    p = 3.0
    x0 = -3.325; x1 = p * (n - 1) + 3.325
    y_rear = -0.98; y_face = 8.92
    h = box(x0, y_rear, 0.6, x1, y_face, 4.37)
    # feet/standoffs at the ends
    h = h.fuse(box(x0, y_rear, 0.0, x0 + 1.0, y_face, 0.6)).fuse(box(x1 - 1.0, y_rear, 0.0, x1, y_face, 0.6))
    for i in range(n):
        x = i * p
        h = h.cut(box(x - 1.3, 1.6, 1.1, x + 1.3, y_face + 0.1, 3.7))
    # latch ramp on top near the mating face
    xc = (x0 + x1) / 2
    lat = Part.Face(Part.makePolygon([V(0, y_face - 3.0, 4.37), V(0, y_face, 4.37), V(0, y_face, 5.57), V(0, y_face - 1.4, 5.57), V(0, y_face - 3.0, 4.37)])).extrude(V(2.6, 0, 0))
    lat.translate(V(xc - 1.3, 0, 0))
    h = h.fuse(lat).removeSplitter()
    P.append((h, BLACK))
    for i in range(n):
        x = i * p
        mp = cbox(x, 0, 0, 0.64, 0.64, 1).copy()
        pin = box(x - 0.32, -0.32, -3.2 + 0.3, x + 0.32, 0.32, 2.72)      # vertical leg
        pin = pin.fuse(box(x - 0.32, -0.32, 2.08, x + 0.32, y_face - 1.5, 2.72))  # horizontal mating pin
        pin = pin.fuse(Part.makeLoft([Part.makePolygon([V(x - 0.32, -0.32, -2.9), V(x + 0.32, -0.32, -2.9), V(x + 0.32, 0.32, -2.9), V(x - 0.32, 0.32, -2.9), V(x - 0.32, -0.32, -2.9)]),
                                       Part.makePolygon([V(x - 0.15, -0.15, -3.2), V(x + 0.15, -0.15, -3.2), V(x + 0.15, 0.15, -3.2), V(x - 0.15, 0.15, -3.2), V(x - 0.15, -0.15, -3.2)])], True))
        P.append((pin.removeSplitter(), TIN))
    peg = cyl(1.5, 0.6 + 2.0, p * (n - 1) / 2, 4.32, -2.0)
    peg = peg.cut(box(p * (n - 1) / 2 - 0.25, 2.5, -2.01, p * (n - 1) / 2 + 0.25, 6.2, -0.3))  # split peg
    P.append((peg, BLACK))
    return P


emit('Molex_Micro-Fit3_43650-0300_RA', microfit_ra(3))


# ---------------------------------------------------------------- Keystone 5015 micro-mini SMT test point
def keystone_5015():
    """Keystone 5015 (catalog M65 p.55, ai-files/datasheets/Keystone_5015_M65p55.pdf): flat phosphor-bronze strip
    0.25 thick, 1.0 wide, trapezoid loop 2.7 long at the base, 1.0 flat top, 1.5 high, silver plated. Origin = pad centre."""
    t = 0.25
    outer = [V(-1.35, 0, 0), V(1.35, 0, 0), V(0.5, 0, 1.5), V(-0.5, 0, 1.5), V(-1.35, 0, 0)]
    # inner offset (approximate parallel offset of the slanted legs)
    ang = math.atan2(1.5, 0.85)
    dx = t / math.sin(ang)
    inner = [V(-1.35 + dx + t / math.tan(ang), 0, t), V(1.35 - dx - t / math.tan(ang), 0, t), V(0.5 - dx + t / math.tan(ang) * 0, 0, 1.5 - t), V(-0.5 + dx - 0, 0, 1.5 - t)]
    inner.append(inner[0])
    f = Part.Face(Part.makePolygon(outer)).cut(Part.Face(Part.makePolygon(inner)))
    s = f.extrude(V(0, 1.0, 0)); s.translate(V(0, -0.5, 0))
    # split the base in the middle (strip ends meet at the centre of the base)
    s = s.cut(box(-0.15, -0.6, -0.01, 0.15, 0.6, t + 0.01))
    return [(s, NICKEL)]


emit('Keystone_5015_TestPoint_MicroMini', keystone_5015())


# ---------------------------------------------------------------- Keystone 5010-5014 THM multipurpose test point
def keystone_5010(color=RED):
    """Keystone 5010-5014 THM multipurpose test point: NO maker drawing obtained. Envelope from distributor data
    (OD 0.125 in = 3.17, overall 0.445 in = 11.3) and the LCSC/EasyEDA OBJ for 5014 (z -3.17..8.11, centred):
    moulded coloured body dia 3.17, wire loop on top, pin dia 1.0 through the board. UNVERIFIED detail."""
    P = []
    body = cyl(1.585, 4.6, 0, 0, 0.0).fuse(cone(1.585, 1.0, 0.8, 0, 0, 4.6))
    P.append((body, color))
    loop = Part.makeTorus(1.1, 0.25, V(0, 0, 6.85), V(0, 1, 0))
    loop = loop.cut(box(-2, -1, 5.2, 2, 1, 5.75))
    stem = cyl(0.25, 0.9, -1.1, 0, 5.4).fuse(cyl(0.25, 0.9, 1.1, 0, 5.4))
    P.append((loop.fuse(stem).removeSplitter(), NICKEL))
    pin = cyl(0.5, 3.17 + 0.5, 0, 0, -3.17)
    P.append((pin, NICKEL))
    return P


emit('Keystone_5010-5014_TestPoint_THM', keystone_5010())


# ---------------------------------------------------------------- HRO TYPE-C-31-M-12 (J1), detailed
def typec_31m12():
    """Korean Hroparts TYPE-C-31-M-12, drawing (ai-files/datasheets/TYPE-C-31-M-12.pdf, 2020-12-08): shell 8.94 wide,
    7.35 long, top 3.26 above the board, receptacle opening 8.34 x 2.56 (USB Type-C spec; shell 0.30), tongue 0.70,
    THT legs 0.80 (front) / 1.10 (rear) wide, 1.01 below the seating plane, front legs 2.60 behind the mating face,
    rear legs 4.18 behind them; SMD leads protrude 0.40 behind the shell. Frame = project footprint frame
    (model rotate z 180 in the footprint as before is NOT needed: this model is built directly in the footprint
    frame: mating face toward -y (3D), legs at x +-4.33, y -2.47 / +1.71)."""
    P = []
    yf = -2.47 - 2.60; yr = yf + 7.35
    z0 = 0.10; zt = 3.26; zc = (z0 + zt) / 2
    outer = stadium(8.94, zt - z0, yr - yf, yf, zc)
    inner = stadium(8.34, 2.56, yr - yf - 0.3, yf - 0.01, zc)
    shell = outer.cut(inner)
    for sx in (-1, 1):
        for (yl, w) in ((-2.47, 0.80), (1.71, 1.10)):
            leg = box(sx * 4.17, yl - w / 2, -1.0, sx * 4.47, yl + w / 2, zc)
            shell = shell.fuse(leg)
    P.append((shell.removeSplitter(), METAL))
    for sx in (-1, 1):  # 2 x dia 0.50 plastic locating posts (front view '2-0.50'), footprint NPTH 0.6 at (+-2.9, 1.21)
        P.append((cyl(0.25, z0 + 0.9, sx * 2.9, 1.21, -0.9), BLACK))
    tongue = box(-6.69 / 2, yf + 0.9, zc - 0.35, 6.69 / 2, yr - 0.3, zc + 0.35)
    tongue = tongue.fuse(stadium(8.34 - 0.02, 2.56 - 0.02, 1.2, yr - 1.5, zc))  # rear insulator plug
    P.append((tongue.removeSplitter(), BLACK))
    xs = [-2.75 + 0.5 * i for i in range(12)]
    for x in xs:
        for zz in (zc + 0.35, zc - 0.35 - 0.02):
            P.append((box(x - 0.125, yf + 1.2, zz, x + 0.125, yf + 4.0, zz + 0.02), GOLD))
    for x, w in ((-3.2, 0.4), (-2.4, 0.4), (-1.75, 0.2), (-1.25, 0.2), (-0.75, 0.2), (-0.25, 0.2),
                 (0.25, 0.2), (0.75, 0.2), (1.25, 0.2), (1.75, 0.2), (2.4, 0.4), (3.2, 0.4)):
        P.append((box(x - w / 2, yr - 0.6, 0.0, x + w / 2, yr + 0.40, 0.12).fuse(box(x - w / 2, yr - 0.6, 0.0, x + w / 2, yr - 0.45, z0 + 0.5)).removeSplitter(), GOLD))
    return P


emit('HRO_TYPE-C-31-M-12', typec_31m12())


# PCM2902CDBR, TI DB0028A (SSOP-28, 0.65 mm pitch), PCM2902C datasheet package outline (SLES230, DB0028A 4214853/B):
# D 10.2 (9.9-10.5), E1 5.3 (5.0-5.6), E 7.8 (7.4-8.2), A 2 max (body top at 1.85 = MO-150 A2 1.75 + A1 0.1),
# b 0.30 (0.22-0.38), c 0.15 (0.09-0.25), L 0.75 (0.55-0.95). Built leads-on-x; footprint uses rotate z -90.
emit('SSOP-28_DB_5.3x10.2_P0.65_TI', gullwing(D=10.2, E1=5.3, E=7.8, A=1.85, A1=0.10, e=0.65, n_side=14, b=0.30, c=0.15, L=0.75))

json.dump(report, sys.stdout, indent=1)
print()
