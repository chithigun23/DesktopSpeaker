# -*- coding: utf-8 -*-
"""Parametric internal CAD of the DesktopSpeaker enclosure (FreeCAD 1.0, headless).

Run (from the project root):
    freecadcmd ai-files/cad/build_speaker_cad.py              # v11 print-ready model (DETAIL=1, default)
    DETAIL=0 freecadcmd ai-files/cad/build_speaker_cad.py     # v11 refresh only (v10 enclosure logic, real board)
Inputs:  ai-files/pcb/layout.json (helpers/board_to_layout.py from the routed board),
         ai-files/cad/parts/DesktopSpeaker-board.step (kicad-cli export, origin = layout frame u/v = 0).
Outputs (ai-files/cad/): DesktopSpeaker_internal.FCStd/.step, work/brep + work/meta.json (for check_cad.py and
render_cad.py), print/*.stl (DETAIL=1; one per printable body, in print orientation).
Axes: X = long side (left/right), Y = depth (0 = front outer face, +Y = rear), Z = up (0 = outer bottom).  mm.
"""
import os, re, json, math
import FreeCAD as App
import Part
from FreeCAD import Vector as V, Rotation as Rot, Placement as Pl

ROOT = '/home/chithi/Desktop/DesktopSpeaker/'
CAD = ROOT + 'ai-files/cad/'
KL = ROOT + 'DesktopSpeaker-kicad/kicad-library/'
WORK = CAD + 'work/'
PRINT = CAD + 'print/'
BOARD_STEP = os.environ.get('BOARD_STEP', CAD + 'parts/DesktopSpeaker-board.step')
LAYOUT_JSON = os.environ.get('LAYOUT', ROOT + 'ai-files/pcb/layout.json')
DETAIL = os.environ.get('DETAIL', '1') != '0'
os.makedirs(WORK + 'brep', exist_ok=True)
for f in os.listdir(WORK + 'brep'):
    os.remove(WORK + 'brep/' + f)
skipped = []            # fillets/chamfers/booleans that failed and were skipped (reported)

# ------------------------------------------------------------------ parameters
P = dict(
    W=163.0, H=100.0, D=160.0, wall=3.0, lid_t=3.0,
    pad_t=11.0,             # front baffle thickness at driver pads (3 wall + 8 raised): M3x10 through a 0.75 mm flange
    pad_w=70.0,
    drv_cx=41.0, drv_zc=61.55, drv_y_flange=11.0,
    ap_drv=59.5, cbore_d=0.0, cbore_h=0.0,
    ch_x=58.0, ch_y0=59.0, ch_top=54.0, roof=3.0,        # woofer chamber: inner x +-58, inner top z 54
    woof_cx=0.0, woof_cy=109.5, ap_w=70.0, ring_od=86.0, ring_t=4.5, w_flange_od=82.6, w_flange_t=4.0,
    w_bc=77.0, w_hole=3.5, w_depth=44.5,
    boss_od=8.0, boss_h=4.5, pilot=4.6, ins_od=4.6, ins_id=3.0, ins_l=5.7,
    pcb_w=100.0, pcb_d=66.0, pcb_t=1.6, pcb_cx=-3.5, pcb_cy=123.5, standoff=5.0,
    grille_t=0.8, hole_d=2.0, hole_pitch=3.0,
    rocker_x=66.0, rocker_z=78.0,
)
if DETAIL:
    P.update(
        lid_t=4.0,             # 1.5 mm gasket groove leaves 2.5 mm
        pilot=4.0,             # real heat-set pilot for M3 x 5.7 inserts (insert OD 4.6 melts in: intended overlap)
        pcb_pilot_l=6.7,       # insert 5.7 + 1 mm
        standoff=10.0,         # flat insert roof (printed roof-down): 10 mm hex spacer instead of 4.5 mm boss + 5 mm spacer
        boss_h=0.0,
        ring_t=5.5, w_recess=1.0, w_recess_d=83.4,       # woofer ring pad 5.5 with a 1 mm flange locating recess
        drv_gasket=0.5, drv_gasket_sq=63.0,              # 0.5 mm gasket recess on the pad rear face (inside the 64 mm flange)
        groove_w=2.0, groove_d=1.5,                      # lid gasket groove for a 3 mm foam cord
        floor_groove=1.0, groove_clr=0.2,                # insert locating grooves in the shell floor
        shelf_y0=76.0,                                   # insert roof extended forward as a PCB shelf (front holes)
        grom_x=40.0, grom_z=40.0, grom_d=6.0, grom_boss_od=14.0, grom_web=1.6, grom_cb=10.0,
        fillet_out=2.0, fillet_in=1.0, cut_chamfer=0.5,
        usb_cut=(12.0, 7.0, 2.0), jack_bore=8.5, jack_cb=(11.0, 2.5), sw100_bore=5.0, min_web=1.6,
        rocker_bore=20.2, rocker_panel=2.0, rocker_cb=25.0, rocker_z=80.0,
        cell_r=10.85, cell_l=70.2, cradle_gap=0.3,
    )
LJ = None
if os.path.exists(LAYOUT_JSON):
    LJ = json.load(open(LAYOUT_JSON))
    P.update(pcb_w=LJ['board']['w'], pcb_d=LJ['board']['d'], pcb_cy=LJ['board']['centre_cad_y'])
    P['D'] = LJ['board']['rear_edge_cad_y'] + 0.5 + P['lid_t']      # board rear edge 0.5 mm in front of the lid inner face
P['pcb_holes'] = [(h['u'], h['v']) for h in LJ['holes']] if LJ else [(a * 47.0, b * 29.5) for a, b in ((1, 1), (1, -1), (-1, 1), (-1, -1))]
P['pcb_hole_names'] = [h['name'] for h in LJ['holes']] if LJ else ['H%d' % (i + 1) for i in range(4)]
def PL(ref, key, default=None):
    return LJ['parts'][ref][key] if LJ and ref in LJ['parts'] else default
Wd, Hd, Dd, t = P['W'], P['H'], P['D'], P['wall']
LT = P['lid_t']
YB = Dd - LT                                  # rear end of the shell = lid inner face
P['YB'] = YB
ZB_IN, ZT_IN = t, Hd - t
RB = P['ch_top'] + P['roof']                  # roof top z
CH_NET_L, CH_DISPLACED_L = 0.525, 0.056      # woofer chamber NET volume target; gross = net + displaced (estimate)
CH_LEN = (CH_NET_L + CH_DISPLACED_L) * 1e6 / ((2 * P['ch_x']) * (P['ch_top'] - t))
P['ch_y0'] = YB - t - CH_LEN
P['woof_cy'] = P['ch_y0'] + t + CH_LEN / 2.0 - 2.0
PCB_BOT = RB + P['boss_h'] + P['standoff']
PCB_TOP = PCB_BOT + P['pcb_t']

objs = []       # (name, group, shape, color)
def add(name, group, shape, color=(0.7, 0.7, 0.7)):
    objs.append((name, group, shape, color))
    return shape

def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def cyl(r, h, p, d=V(0, 0, 1)):
    return Part.makeCylinder(r, h, p, d)
def hexprism(af, h, p):
    r = af / math.sqrt(3)
    pts = [V(p.x + r * math.cos(math.radians(60 * i)), p.y + r * math.sin(math.radians(60 * i)), p.z) for i in range(7)]
    return Part.Face(Part.makePolygon(pts)).extrude(V(0, 0, h))
def fuse(lst):
    s = lst[0]
    return s.multiFuse(lst[1:]).removeSplitter() if len(lst) > 1 else s
def cut(a, lst):
    return a.cut(fuse(lst)) if lst else a
def tr(shape, pos, rot=Rot(0, 0, 0)):
    s = shape.copy(); s.Placement = Pl(pos, rot).multiply(s.Placement); return s
def halfspace(pt, n):
    """solid half-space {p: (p - pt) . n >= 0} (a 2 m cube)"""
    b = Part.makeBox(2000, 2000, 1000, V(-1000, -1000, 0))
    b.Placement = Pl(pt, Rot(V(0, 0, 1), n))
    return b
def prism_yz(pts, x0, x1):
    """polygon in the Y-Z plane (list of (y, z)) extruded from x0 to x1"""
    w = Part.makePolygon([V(x0, y, z) for y, z in pts] + [V(x0, pts[0][0], pts[0][1])])
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))
def prism_xz(pts, y0, y1):
    w = Part.makePolygon([V(x, y0, z) for x, z in pts] + [V(pts[0][0], y0, pts[0][1])])
    return Part.Face(w).extrude(V(0, y1 - y0, 0))
def rrect_y(cx, cz, w, h, r, y0, y1):
    """rounded rectangle (X-Z) extruded along Y"""
    b = box(cx - w / 2, cx + w / 2, y0, y1, cz - h / 2, cz + h / 2)
    if r > 0:
        try:
            b = b.makeFillet(r, [e for e in b.Edges if e.BoundBox.XLength < 1e-6 and e.BoundBox.ZLength < 1e-6])
        except Exception as ex:
            skipped.append('rounded rect fillet r%.1f (%s)' % (r, ex))
    return b
def try_fillet(shape, r, edges, label):
    if not edges:
        return shape
    try:
        s = shape.makeFillet(r, edges)
        if s.isValid():
            return s
        skipped.append('%s: invalid result' % label)
    except Exception as ex:
        skipped.append('%s: %s' % (label, str(ex)[:60]))
    return shape
def try_chamfer(shape, d, edges, label):
    if not edges:
        return shape
    try:
        s = shape.makeChamfer(d, edges)
        if s.isValid():
            return s
        skipped.append('%s: invalid result' % label)
    except Exception as ex:
        skipped.append('%s: %s' % (label, str(ex)[:60]))
    return shape

# ------------------------------------------------------------------ fastener sites (insert top point, axis INTO material, head underside offset from insert top)
sites = []   # dict(kind, name, p, axis, head_off, pilot, body)
dcx, dzc = P['drv_cx'], P['drv_zc']
for side, sx in (('L', -1), ('R', 1)):
    for i, (a, b) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        sites.append(dict(kind='drv', name='DrvScrew_%s%d' % (side, i + 1), p=V(sx * dcx + a * 23.4, P['drv_y_flange'], dzc + b * 23.4),
                          axis=V(0, -1, 0), head_off=0.75, pilot=10.0, body='shell', screw=10.0))
for i in range(4):
    ang = math.radians(45 + 90 * i)
    r = P['w_bc'] / 2
    zf = t + P['ring_t'] - P.get('w_recess', 0.0)       # flange seat
    sites.append(dict(kind='woof', name='WoofScrew_%d' % (i + 1), p=V(P['woof_cx'] + r * math.cos(ang), P['woof_cy'] + r * math.sin(ang), zf),
                      axis=V(0, 0, -1), head_off=P['w_flange_t'], pilot=zf - 1.0, body='shell', screw=10.0))
for i, (hu, hv) in enumerate(P['pcb_holes']):
    sites.append(dict(kind='pcb', name='PcbScrew_%d_%s' % (i + 1, P['pcb_hole_names'][i]), p=V(P['pcb_cx'] + hu, P['pcb_cy'] + hv, RB + P['boss_h']),
                      axis=V(0, 0, -1), head_off=P['standoff'] + P['pcb_t'], pilot=P.get('pcb_pilot_l', 6.5), body='insert' if DETAIL else 'shell',
                      screw=16.0 if DETAIL else 12.0))
if DETAIL:
    lid_pts = [(-74, 7.5, 'floor'), (74, 7.5, 'floor'), (-74, 92.5, 'top'), (74, 92.5, 'top'), (0, 92.5, 'top'), (-50, 7.5, 'floor'), (50, 7.5, 'floor'),
               (-70, 45.0, 'left'), (70, 45.0, 'right'), (-30, 50.0, 'roof'), (30, 50.0, 'roof')]
else:
    lid_pts = [(-74, 7.5, 'floor'), (74, 7.5, 'floor'), (-74, 92.5, 'top'), (74, 92.5, 'top'), (0, 92.5, 'top'), (-50, 7.5, 'floor'), (50, 7.5, 'floor')]
for i, (x, z, anc) in enumerate(lid_pts):
    sites.append(dict(kind='lid', name='LidScrew_%d' % (i + 1), p=V(x, YB, z), axis=V(0, -1, 0), head_off=LT, pilot=8.0, anchor=anc,
                      body='insert' if anc == 'roof' else 'shell', screw=10.0))
feet_pts = [(-68, 25), (68, 25), (-68, 135), (68, 135)]
for i, (x, y) in enumerate(feet_pts):
    sites.append(dict(kind='foot', name='Foot_%d' % (i + 1), p=V(x, y, 0), axis=V(0, 0, 1), head_off=0, pilot=6.5, body='shell'))

chx = P['ch_x']
# ------------------------------------------------------------------ lid boss (shell walls): circle + web to the anchor wall(s), 45 deg lead-in for baffle-down printing
def lid_boss(x, z, anc, L=10.0):
    r = P['boss_od'] / 2
    y0 = YB - L
    prof = [cyl(r, L, V(x, y0, z), V(0, 1, 0))]
    if anc == 'floor':
        prof.append(box(x - r, x + r, y0, YB, ZB_IN - 0.01, z))
        if abs(x) > Wd / 2 - t - 2 * r:
            sx = 1 if x > 0 else -1
            prof.append(box(min(x, sx * (Wd / 2 - t + 0.01)), max(x, sx * (Wd / 2 - t + 0.01)), y0, YB, z - r, z + r))
        dist, n, pt = z + r - ZB_IN, V(0, 1, -1), lambda y1: V(0, y1, ZB_IN)
    elif anc == 'top':
        prof.append(box(x - r, x + r, y0, YB, z, ZT_IN + 0.01))
        if abs(x) > Wd / 2 - t - 2 * r:
            sx = 1 if x > 0 else -1
            prof.append(box(min(x, sx * (Wd / 2 - t + 0.01)), max(x, sx * (Wd / 2 - t + 0.01)), y0, YB, z - r, z + r))
        dist, n, pt = ZT_IN - (z - r), V(0, 1, 1), lambda y1: V(0, y1, ZT_IN)
    elif anc in ('left', 'right'):
        sx = 1 if anc == 'right' else -1
        wx = sx * (Wd / 2 - t + 0.01)
        prof.append(box(min(x, wx), max(x, wx), y0, YB, z - r, z + r))
        dist = (Wd / 2 - t) - (abs(x) - r)
        n, pt = V(sx, 1, 0), lambda y1: V(sx * (Wd / 2 - t), y1, 0)
    else:
        raise ValueError(anc)
    body = fuse(prof)
    if not DETAIL:
        return cyl(r, L, V(x, y0, z), V(0, 1, 0))
    lead = body.copy(); lead.translate(V(0, -dist, 0))
    lead = lead.common(halfspace(pt(y0 - dist), n))
    return fuse([body, lead])

# ------------------------------------------------------------------ main shell: front baffle + 4 walls + bosses (+ woofer chamber when DETAIL=0)
outer = box(-Wd / 2, Wd / 2, 0, YB, 0, Hd)
cav = box(-Wd / 2 + t, Wd / 2 - t, t, YB + 1.0, ZB_IN, ZT_IN)
if DETAIL:
    outer = try_fillet(outer, P['fillet_out'], [e for e in outer.Edges if e.BoundBox.XLength < 1e-6 and e.BoundBox.YLength < 1e-6 and abs(e.BoundBox.YMin) < 1e-6],
                       'shell outer front vertical edges r2')
    cav = try_fillet(cav, P['fillet_in'], [e for e in cav.Edges if not (abs(e.BoundBox.YMin - (YB + 1)) < 1e-6 and abs(e.BoundBox.YMax - (YB + 1)) < 1e-6)],
                     'shell cavity inner edges r1')
shell = outer.cut(cav)
adds = []
for sx in (-1, 1):                                    # raised driver mounting pads
    adds.append(box(sx * dcx - P['pad_w'] / 2, sx * dcx + P['pad_w'] / 2, t - 0.01, P['pad_t'], dzc - P['pad_w'] / 2, dzc + P['pad_w'] / 2))
if not DETAIL:
    chamber_out = box(-chx - t, chx + t, P['ch_y0'], YB, ZB_IN, RB)
    chamber_in = box(-chx, chx, P['ch_y0'] + t, YB, ZB_IN, P['ch_top'])
    adds.append(chamber_out.cut(chamber_in))
adds.append(cyl(P['ring_od'] / 2, P['ring_t'] + 0.01, V(P['woof_cx'], P['woof_cy'], t - 0.01)))      # woofer mounting ring pad
for s in sites:
    p = s['p']
    if s['kind'] == 'pcb' and not DETAIL:
        if abs(p.x) > chx + t - 1.0 or p.y < P['ch_y0'] + 1.0:      # hole not over the chamber roof -> 8 mm post from the main floor
            adds.append(cyl(P['boss_od'] / 2, RB + P['boss_h'] - t, V(p.x, p.y, t)))
            s['post'] = True
        adds.append(cyl(P['boss_od'] / 2, P['boss_h'], V(p.x, p.y, RB)))
    elif s['kind'] == 'lid' and s['body'] == 'shell':
        adds.append(lid_boss(p.x, p.z, s['anchor']))
    elif s['kind'] == 'foot':
        adds.append(cyl(P['boss_od'] / 2, P['boss_h'] if not DETAIL else 4.5, V(p.x, p.y, t - 0.01)))

# battery: 2P 21700 (2 x Samsung 50S, 21.7 x 70.2) + PCM; cradle (DETAIL) under the drivers
bz = t + 1.0 + 10.85
by = 33.0
bx0 = -36.6
CRADLE = {}
if DETAIL:
    R = P['cell_r'] + P['cradle_gap']
    yc1, yc2 = by - 10.85, by + 10.85
    s45 = math.sqrt(0.5)
    def arc(yc, a0, a1, n=18):        # circle points, angle from +Y axis measured in the Y-Z plane (deg)
        return [(yc + R * math.cos(math.radians(a)), bz + R * math.sin(math.radians(a))) for a in [a0 + (a1 - a0) * k / n for k in range(n + 1)]]
    # front lip at the cell centre height, falling arc to the bottom, rising part only up to 45 deg then a 45 deg tangent line (prints along +Y)
    p1 = [(t - 0.01, t - 0.01), (t - 0.01, bz)] + arc(yc1, 180, 315)
    # 45 deg line from the cell-1 tangent point up to cell-2 arc
    ty, tz = yc1 + R * s45, bz - R * s45
    # intersection of z = tz + (y - ty) with circle 2 (falling side)
    c0 = tz - ty - bz      # z - bz = y + c0
    A, B, C = 2.0, 2 * (c0 - yc2), yc2 ** 2 + c0 ** 2 - R * R
    yi = (-B - math.sqrt(B * B - 4 * A * C)) / (2 * A)
    ai = math.degrees(math.atan2(yi + c0, yi - yc2)) % 360
    p2 = [(yi, yi + c0 + bz)] + arc(yc2, ai, 315)[1:]
    ty2, tz2 = yc2 + R * s45, bz - R * s45
    yr = ty2 + (bz - tz2)
    rib_prof = p1 + p2 + [(yr, bz), (yr, t - 0.01)]
    CRADLE['rib_y1'] = yr
    for xr in (-31.0, 22.0):
        adds.append(prism_yz(rib_prof, xr - 1.5, xr + 1.5))
    for xe in (bx0 - 1.0 - 3.0, bx0 + P['cell_l'] + 3.0 + 1.0):        # end stops (1 mm from the cells / the PCM)
        adds.append(box(xe, xe + 3.0, t - 0.01, yr, ZB_IN - 0.01, bz))
    # strap anchors (20 mm hook-and-loop strap): tunnels along Y, front block on the baffle, rear block with 45 deg lead-in
    xs = -4.5
    fa = box(xs - 14, xs + 14, t - 0.01, t + 5, ZB_IN - 0.01, ZB_IN + 6)
    ra = prism_yz([(yr + 0.5 - 6, ZB_IN - 0.01), (yr + 0.5, ZB_IN + 6), (yr + 5.5, ZB_IN + 6), (yr + 5.5, ZB_IN - 0.01)], xs - 14, xs + 14)
    tun = box(xs - 11, xs + 11, 0, yr + 20, ZB_IN - 0.5, ZB_IN + 2.5)
    adds.append(fa.cut(tun)); adds.append(ra.cut(tun))
    CRADLE.update(xs=xs, strap_w=20, tunnel=(22, 2.5))
shell = shell.fuse(fuse(adds)).removeSplitter()
cuts = []
for sx in (-1, 1):
    cuts.append(cyl(P['ap_drv'] / 2, P['pad_t'] + 2, V(sx * dcx, -1, dzc), V(0, 1, 0)))
    if DETAIL:   # 0.5 mm driver gasket recess on the pad rear face: 63 mm square inside the 64 mm flange, minus the aperture and 7 mm around each screw
        q = P['drv_gasket_sq'] / 2
        g = rrect_y(sx * dcx, dzc, 2 * q, 2 * q, 4.0, P['pad_t'] - P['drv_gasket'], P['pad_t'] + 1)
        g = g.cut(cyl(P['ap_drv'] / 2 + 0.01, 5, V(sx * dcx, P['pad_t'] - 2, dzc), V(0, 1, 0)))
        for a, b in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            g = g.cut(cyl(3.5, 5, V(sx * dcx + a * 23.4, P['pad_t'] - 2, dzc + b * 23.4), V(0, 1, 0)))
        cuts.append(g)
cuts.append(cyl(P['ap_w'] / 2, t + P['ring_t'] + 1, V(P['woof_cx'], P['woof_cy'], -1)))
if DETAIL:
    cuts.append(cyl(P['w_recess_d'] / 2, P['w_recess'] + 1, V(P['woof_cx'], P['woof_cy'], t + P['ring_t'] - P['w_recess'])))
    # insert locating grooves in the floor (insert walls drop 1 mm into them, 0.2 mm clearance each side)
    gc, fg = P['groove_clr'], P['floor_groove']
    g_out = box(-chx - t - gc, chx + t + gc, P['ch_y0'] - gc, YB + 1, ZB_IN - fg, ZB_IN + 0.5)
    g_in = box(-chx + gc, chx - gc, P['ch_y0'] + t + gc, YB + 2, ZB_IN - fg - 1, ZB_IN + 1)
    cuts.append(g_out.cut(g_in))
for s in sites:
    if s['body'] == 'shell':
        cuts.append(cyl(P['pilot'] / 2, s['pilot'], s['p'], s['axis']))
shell = shell.cut(fuse(cuts)).removeSplitter()
add('Shell_Box', 'shell', shell, (0.28, 0.30, 0.34))

# ------------------------------------------------------------------ woofer chamber insert (DETAIL): partition + side walls + roof + forward PCB shelf, printed roof-down
INSERT = None
if DETAIL:
    fg = P['floor_groove']
    ins_out = box(-chx - t, chx + t, P['ch_y0'], YB, ZB_IN - fg, RB)
    ins_in = box(-chx, chx, P['ch_y0'] + t, YB + 1, ZB_IN - fg - 1, P['ch_top'])
    ins = ins_out.cut(ins_in)
    ia = [box(-chx - t, chx + t, P['shelf_y0'], P['ch_y0'] + 0.01, P['ch_top'], RB)]       # shelf
    sl = P['ch_y0'] - P['shelf_y0'] - 2.0
    for xg in (-28.0, 0.0, 28.0):                                                            # 45 deg shelf gussets
        ia.append(prism_yz([(P['shelf_y0'] + 2.0, P['ch_top'] + 0.01), (P['ch_y0'] + 0.01, P['ch_top'] + 0.01), (P['ch_y0'] + 0.01, P['ch_top'] - sl)], xg - 1.5, xg + 1.5))
    clip = box(-chx - t, chx + t, P['shelf_y0'], YB, -10, RB)
    for s in sites:
        p = s['p']
        if s['kind'] == 'pcb':
            if not (P['shelf_y0'] + 4.0 <= p.y <= YB - 4.0 and abs(p.x) <= chx + t):
                skipped.append('PCB hole %s outside the insert roof/shelf (no support)' % s['name'])
                continue
            zb = p.z - s['pilot'] - 1.0
            ia.append(cyl(P['boss_od'] / 2, P['ch_top'] - zb + 0.01, V(p.x, p.y, zb)).common(clip))
        elif s['kind'] == 'lid' and s['body'] == 'insert':
            r = P['boss_od'] / 2
            ia.append(cyl(r, 10.0, V(p.x, YB - 10.0, p.z), V(0, 1, 0)))
            ia.append(box(p.x - r, p.x + r, YB - 10.0, YB, p.z, P['ch_top'] + 0.01))
    # grommet boss on the partition front face (woofer leads main chamber -> woofer chamber)
    gx, gz = P['grom_x'], P['grom_z']
    ia.append(cyl(P['grom_boss_od'] / 2, 3.01, V(gx, P['ch_y0'] - 3.0, gz), V(0, 1, 0)))
    ins = ins.fuse(fuse(ia)).removeSplitter()
    ic = [cyl(P['grom_d'] / 2, 10, V(gx, P['ch_y0'] - 4, gz), V(0, 1, 0)),
          cyl(P['grom_cb'] / 2, 6.0 - P['grom_web'] + 1.0, V(gx, P['ch_y0'] - 4, gz), V(0, 1, 0))]
    for s in sites:
        if s['body'] == 'insert':
            ic.append(cyl(P['pilot'] / 2, s['pilot'], s['p'], s['axis']))
    ins = ins.cut(fuse(ic)).removeSplitter()
    INSERT = add('Insert_woofer_chamber', 'insert', ins, (0.36, 0.30, 0.26))

# ------------------------------------------------------------------ front drivers (real maker STEP)
ND65 = CAD + 'parts/ND65_3D/ND65-4 and 8.step'
nd = Part.read(ND65)
for name, sx in (('Driver_FrontL_ND65-4', -1), ('Driver_FrontR_ND65-4', 1)):
    s = tr(nd, V(sx * dcx, P['drv_y_flange'] + 22.75, dzc), Rot(V(1, 0, 0), -90))     # raw front = -Z, flange plane z = -22.75
    add(name, 'drivers', s, (0.15, 0.15, 0.17))

# ------------------------------------------------------------------ woofer: Tang Band W3-2052SC parametric stand-in
wz0 = t + P['ring_t'] - P.get('w_recess', 0.0)       # flange front face
wcx, wcy = P['woof_cx'], P['woof_cy']
fl = cyl(P['w_flange_od'] / 2, P['w_flange_t'], V(wcx, wcy, wz0)).cut(cyl(31.0, P['w_flange_t'] + 1, V(wcx, wcy, wz0 - 0.5)))
for s in sites:
    if s['kind'] == 'woof':
        fl = fl.cut(cyl(P['w_hole'] / 2 + 0.05, 6, V(s['p'].x, s['p'].y, wz0 - 1)))
outer_c = Part.makeCone(31.0, 20.0, 24.5, V(wcx, wcy, wz0), V(0, 0, 1))
inner_c = Part.makeCone(28.0, 17.0, 24.5, V(wcx, wcy, wz0), V(0, 0, 1))
mag = cyl(20.0, P['w_depth'] - 24.5, V(wcx, wcy, wz0 + 24.5))
add('Woofer_W3-2052SC_standin', 'woofer', fuse([fl, outer_c.cut(inner_c), mag]), (0.12, 0.12, 0.14))

# ------------------------------------------------------------------ battery cells + PCM
for i, dy in enumerate((-10.85, 10.85)):
    add('Battery_Cell%d_21700_50S' % (i + 1), 'battery', cyl(10.85, 70.2, V(bx0, by + dy, bz), V(1, 0, 0)), (0.2, 0.45, 0.8))
add('Battery_PCM_board', 'battery', box(bx0 + 70.2, bx0 + 73.2, by - 21.7, by + 21.7, bz - 9, bz + 9), (0.1, 0.5, 0.2))

# ------------------------------------------------------------------ PCB + components from the routed-board STEP (layout frame: STEP x = u, y = v, z = 0 at the board bottom)
pcx, pcy = P['pcb_cx'], P['pcb_cy']
BU0, BU1 = (LJ['board']['u0'], LJ['board']['u1']) if LJ else (-P['pcb_w'] / 2, P['pcb_w'] / 2)
REAR_E = LJ['board']['rear_edge_cad_y'] if LJ else 156.5
placed = {}
standin_pcb = []
zfix = {}
INDIV = re.compile(r'^(J\d+|U\d+|L\d+|SW\d+|Y\d+|Q\d+|C275)$')
def at_board(s):
    return tr(s, V(pcx, pcy, PCB_BOT))
use_step = os.path.exists(BOARD_STEP) and LJ is not None
if use_step:
    comp = Part.read(BOARD_STEP)
    board, own = None, {}
    rects = [(r, p['rect']) for r, p in LJ['parts'].items()]
    for so in comp.Solids:
        bb = so.BoundBox
        if bb.XLength > 0.8 * P['pcb_w'] and bb.YLength > 0.8 * P['pcb_d']:
            board = so if board is None or so.Volume > board.Volume else board
            continue
        cu, cv = (bb.XMin + bb.XMax) / 2, (bb.YMin + bb.YMax) / 2
        best = None
        for r, q in rects:
            if q[0] - 0.6 <= cu <= q[2] + 0.6 and q[1] - 0.6 <= cv <= q[3] + 0.6:
                a = (q[2] - q[0]) * (q[3] - q[1])
                if best is None or a < best[0]:
                    best = (a, r)
        own.setdefault(best[1] if best else 'UNASSIGNED', []).append(so)
    add('PCB_%gx%gx1.6' % (P['pcb_w'], P['pcb_d']), 'pcb', at_board(board), (0.05, 0.35, 0.15))
    groups = {}
    for ref, sols in own.items():
        c = Part.makeCompound(sols)
        bb = c.BoundBox
        if bb.ZMin > P['pcb_t'] + 0.3:                                   # floating model (BM83 STEP origin 5.4 mm high)
            zfix[ref] = round(P['pcb_t'] - bb.ZMin, 3); c.translate(V(0, 0, P['pcb_t'] - bb.ZMin))
        elif bb.ZMax <= P['pcb_t'] + 0.6 and -0.05 <= bb.ZMin < P['pcb_t'] - 0.1:   # SMD model sunk into the board (XFL4015 rotate about the wrong pivot)
            zfix[ref] = round(P['pcb_t'] - bb.ZMin, 3); c.translate(V(0, 0, P['pcb_t'] - bb.ZMin))
        c = at_board(c)
        placed[ref] = c
        if INDIV.match(ref):
            nm = {'J1': 'PCB_J1_USB-C', 'J2': 'PCB_J2_3.5mm_jack', 'J3': 'PCB_J3_3.5mm_jack'}.get(ref, 'PCB_%s' % ref)
            add(nm, 'pcb_parts', c, (0.1, 0.1, 0.1) if ref in ('J2', 'J3') else (0.55, 0.55, 0.6))
        else:
            sh = (LJ.get('sheets', {}).get(ref) or 'root').replace(' ', '_')
            groups.setdefault(sh, []).extend(c.Solids)
    for sh, sols in sorted(groups.items()):
        add('PCB_smallparts_%s' % sh, 'pcb_parts', Part.makeCompound(sols), (0.5, 0.45, 0.4))
else:
    raise SystemExit('board STEP %s or layout %s missing: export with kicad-cli (README)' % (BOARD_STEP, LAYOUT_JSON))

# parametric stand-ins (no STEP in the library): J5 Micro-Fit, J9-J11 JST VH 2-pos, SW100 tact switch
def sbox(ref, u, v, du, dv, dz, label, color):
    s = box(pcx + u - du / 2, pcx + u + du / 2, pcy + v - dv / 2, pcy + v + dv / 2, PCB_TOP, PCB_TOP + dz)
    placed[ref] = s; standin_pcb.append(ref)
    add('PCB_%s_%s' % (ref, label), 'pcb_parts', s, color)
    return s
def rdim(ref, dflt):
    r = PL(ref, 'rect')
    return (r[2] - r[0], r[3] - r[1]) if r else dflt
sbox('J5', PL('J5', 'cy_u', 46.0), PL('J5', 'cy_v', 3.0), rdim('J5', (11.0, 13.66))[0], rdim('J5', (11.0, 13.66))[1], 9.0, 'MicroFit3_standin', (0.9, 0.9, 0.85))
for ref, v in (('J9', -27.0), ('J10', -17.5), ('J11', -8.0)):
    sbox(ref, PL(ref, 'cy_u', -38.0), PL(ref, 'cy_v', v), 9.27, 9.5, 10.9, 'JST_B2P-VH_standin', (0.95, 0.95, 0.9))
SW_U = PL('SW100', 'origin_u', 30.0)
SW_Z = PCB_TOP + 1.75          # plunger axis height (assumed: TE 1977066-1 body 3.5 mm, plunger centred)
sbox('SW100', SW_U, PL('SW100', 'cy_v', 30.0), 4.6, 5.0, 3.5, 'tact_standin', (0.3, 0.3, 0.3))
plunger = cyl(1.25, 2.5, V(pcx + SW_U, REAR_E, SW_Z), V(0, 1, 0))
placed['SW100_plunger'] = plunger
add('PCB_SW100_plunger', 'pcb_parts', plunger, (0.8, 0.1, 0.1))

# ------------------------------------------------------------------ PCB screws/standoffs board holes already in the STEP board body
# ------------------------------------------------------------------ SW101 rocker (panel mount, stand-in) and harnesses (schematic tubes)
rx, rz = P['rocker_x'], P['rocker_z']
rocker = fuse([cyl(9.8, 22.0, V(rx, Dd - 22.0, rz), V(0, 1, 0)), cyl(11.5, 1.5, V(rx, Dd, rz), V(0, 1, 0))])
add('SW101_rocker_D20_standin', 'hardware', rocker, (0.6, 0.1, 0.1))
def tube(pts, r):
    hs = []
    for a, b in zip(pts[:-1], pts[1:]):
        d = V(b[0] - a[0], b[1] - a[1], b[2] - a[2])
        hs.append(cyl(r, d.Length, V(*a), d))
    for q in pts[1:-1]:
        hs.append(Part.makeSphere(r, V(*q)))
    return fuse(hs)
J5U, J5V = PL('J5', 'cy_u', 46.0), PL('J5', 'cy_v', 3.0)
if DETAIL:
    hx, hz = Wd / 2 - t - 8.5, bz + 3.0          # right side pocket (outside the woofer chamber), above the cradle end stop
    hp = [(pcx + PL('J5', 'rect')[2] + 1.0, pcy + J5V, PCB_TOP + 4.5), (hx, pcy + J5V, PCB_TOP + 4.5), (hx, pcy + J5V, hz), (hx, by, hz),
          (bx0 + 70.2 + 3.0 + 2.4, by, hz)]
else:
    hz = bz
    hp = [(pcx + PL('J5', 'rect')[2] + 2.0, pcy + J5V, PCB_TOP + 4.5), (pcx + BU1 + 2.8, pcy + J5V, PCB_TOP + 4.5), (pcx + BU1 + 2.8, pcy + J5V, hz), (pcx + BU1 + 2.8, by, hz), (39.0, by, hz)]
add('Harness_J5_to_pack_schematic', 'harness', tube(hp, 2.0), (0.8, 0.5, 0.1))
HARNESS = dict(j5=hp)
if DETAIL:
    # woofer leads: J11 (WOOFER) plug -> down in front of the board edge -> grommet in the partition -> woofer terminals
    jx, jy = pcx + PL('J11', 'cy_u', 45.3), pcy + PL('J11', 'cy_v', -63.6)
    gy = P['ch_y0']
    wp = [(jx, jy, PCB_TOP + 12.5), (jx, jy, PCB_TOP + 16.0), (jx, pcy + P['pcb_d'] * -0.5 - 4.5, PCB_TOP + 16.0), (jx, pcy - P['pcb_d'] / 2 - 4.5, P['grom_z']),
          (P['grom_x'], pcy - P['pcb_d'] / 2 - 4.5, P['grom_z']), (P['grom_x'], gy + t + 6.0, P['grom_z']), (30.0, wcy - 31.5, 25.0)]
    add('Harness_woofer_leads_schematic', 'harness', tube(wp, 1.5), (0.7, 0.1, 0.1))
    HARNESS['woofer'] = wp
    # grommet stand-in: 6 mm panel hole, 1.6 mm web, ID 3.4 (two 0.5 mm2 leads)
    gx, gz = P['grom_x'], P['grom_z']
    y_web = gy + t - P['grom_web']
    grom = fuse([cyl(3.0, P['grom_web'], V(gx, y_web, gz), V(0, 1, 0)), cyl(4.6, 1.0, V(gx, y_web - 1.0, gz), V(0, 1, 0)),
                 cyl(4.6, 1.0, V(gx, gy + t, gz), V(0, 1, 0))]).cut(cyl(1.7, 10, V(gx, y_web - 3, gz), V(0, 1, 0)))
    add('Grommet_6mm_standin', 'hardware', grom, (0.05, 0.05, 0.05))

# ------------------------------------------------------------------ rear lid: cutouts from the real connector geometry in the board STEP
def slab_bb(shape, y0, y1):
    try:
        c = shape.common(box(-500, 500, y0, y1, -500, 500))
        if c.Volume > 1e-4:
            return c.BoundBox
    except Exception:
        pass
    return None
cut_info = []
lcuts = []
for s in sites:
    if s['kind'] == 'lid':
        lcuts.append(cyl(1.7, LT + 2, V(s['p'].x, YB - 1, s['p'].z), V(0, 1, 0)))
# USB-C: the receptacle opening = J1 section behind the board edge
bbj = slab_bb(placed['J1'], REAR_E - 0.3, REAR_E + 10) or placed['J1'].BoundBox
ucx, ucz = (bbj.XMin + bbj.XMax) / 2, (bbj.ZMin + bbj.ZMax) / 2
uw, uh, ur = P.get('usb_cut', (10.2, 5.0, 0.0))
lcuts.append(rrect_y(ucx, ucz, uw, uh, ur, YB - 1, Dd + 1))
cut_info.append(dict(ref='J1', kind='USB-C plug clearance', shape='rrect', cx=ucx, cz=ucz, w=uw, h=uh, r=ur,
                     body=(round(bbj.XLength, 2), round(bbj.ZLength, 2)), body_ymax=round(placed['J1'].BoundBox.YMax, 2)))
for ref in ('J2', 'J3'):
    bbn = placed[ref].BoundBox
    bbs = slab_bb(placed[ref], bbn.YMax - 1.0, bbn.YMax + 1) or bbn
    jcx, jcz = (bbs.XMin + bbs.XMax) / 2, (bbs.ZMin + bbs.ZMax) / 2
    jd = P.get('jack_bore', 8.4)
    lcuts.append(cyl(jd / 2, LT + 2, V(jcx, YB - 1, jcz), V(0, 1, 0)))
    if DETAIL:
        cbd, cbt = P['jack_cb']
        lcuts.append(cyl(cbd / 2, cbt + 1, V(jcx, Dd - cbt, jcz), V(0, 1, 0)))
    cut_info.append(dict(ref=ref, kind='3.5 mm jack bore', shape='circle', cx=jcx, cz=jcz, d=jd, cb=P.get('jack_cb'),
                         body=(round(bbs.XLength, 2), round(bbs.ZLength, 2)), body_ymax=round(bbn.YMax, 2)))
sd = P.get('sw100_bore', 5.0)
lcuts.append(cyl(sd / 2, LT + 2, V(pcx + SW_U, YB - 1, SW_Z), V(0, 1, 0)))
cut_info.append(dict(ref='SW100', kind='tact plunger (stand-in)', shape='circle', cx=pcx + SW_U, cz=SW_Z, d=sd, body=(2.5, 2.5), body_ymax=round(plunger.BoundBox.YMax, 2)))
web_usb_sw = abs(pcx + SW_U - ucx) - uw / 2 - sd / 2          # lid web between the USB-C clearance and the SW100 bore
if DETAIL and web_usb_sw < P['min_web']:
    # web too thin to print (board places SW100 %.1f mm from J1): join both into one keyhole opening
    xa, xb = sorted((ucx + math.copysign(uw / 2 - 0.5, pcx + SW_U - ucx), pcx + SW_U))
    lcuts.append(box(xa, xb, YB - 1, Dd + 1, SW_Z - sd / 2, SW_Z + sd / 2))
    cut_info[-1]['joined'] = 'J1'
    skipped.append('lid web J1/SW100 %.2f mm < %.1f: openings joined (keyhole); no chamfer on the joining edges' % (web_usb_sw, P['min_web']))
rd = P.get('rocker_bore', 20.2)
lcuts.append(cyl(rd / 2, LT + 2, V(rx, YB - 1, rz), V(0, 1, 0)))
if DETAIL:
    lcuts.append(cyl(P['rocker_cb'] / 2, LT - P['rocker_panel'] + 1, V(rx, YB - 1, rz), V(0, 1, 0)))
cut_info.append(dict(ref='SW101', kind='rocker D20 panel hole', shape='circle', cx=rx, cz=rz, d=rd, body=(19.6, 19.6), body_ymax=None))
def chamfer_tool_circle(cx, cz, r, c):
    return Part.makeCone(r, r + c + 0.02, c + 0.02, V(cx, Dd - c, cz), V(0, 1, 0))
def chamfer_tool_rrect(cx, cz, w, h, r, c):
    f0 = rrect_y(cx, cz, w, h, r, Dd - c, Dd - c + 1).Faces
    f0 = [f for f in f0 if abs(f.BoundBox.YMax - (Dd - c)) < 1e-6 and abs(f.BoundBox.YMin - (Dd - c)) < 1e-6][0]
    w0 = f0.OuterWire
    w1 = f0.makeOffset2D(c + 0.02).OuterWire
    w1.translate(V(0, c + 0.02, 0))
    return Part.makeLoft([w0, w1], True)
if DETAIL:      # 0.5 mm x 45 deg chamfers on the outer-face rims of all lid cutouts (as cut tools; makeChamfer fails on this lid)
    cc = P['cut_chamfer']
    try:
        for s in sites:
            if s['kind'] == 'lid':
                lcuts.append(chamfer_tool_circle(s['p'].x, s['p'].z, 1.7, cc))
        lcuts.append(chamfer_tool_rrect(ucx, ucz, uw, uh, ur, cc))
        for ci in cut_info:
            if ci['ref'] in ('J2', 'J3'):
                lcuts.append(chamfer_tool_circle(ci['cx'], ci['cz'], P['jack_cb'][0] / 2, cc))
        lcuts.append(chamfer_tool_circle(pcx + SW_U, SW_Z, sd / 2, cc))
        lcuts.append(chamfer_tool_circle(rx, rz, rd / 2, cc))
    except Exception as ex:
        skipped.append('lid cutout chamfer tools: %s' % str(ex)[:80])
lid = box(-Wd / 2, Wd / 2, YB, Dd, 0, Hd)
if DETAIL:
    lid = try_fillet(lid, P['fillet_out'], [e for e in lid.Edges if e.BoundBox.XLength < 1e-6 and e.BoundBox.YLength < 1e-6 and abs(e.BoundBox.YMin - Dd) < 1e-6],
                     'lid outer vertical edges r2')
    # gasket groove: outer loop on the shell wall land + inverted U on the woofer chamber insert rim (joins the floor run)
    gw, gd = P['groove_w'], P['groove_d']
    xo, zo0, zo1 = Wd / 2 - t / 2, t / 2, Hd - t / 2
    ring = box(-xo - gw / 2, xo + gw / 2, YB - 1, YB + gd, zo0 - gw / 2, zo1 + gw / 2).cut(box(-xo + gw / 2, xo - gw / 2, YB - 2, YB + gd + 1, zo0 + gw / 2, zo1 - gw / 2))
    xc, zc = chx + t / 2, P['ch_top'] + P['roof'] / 2
    u_l = box(-xc - gw / 2, -xc + gw / 2, YB - 1, YB + gd, zo0, zc + gw / 2)
    u_r = box(xc - gw / 2, xc + gw / 2, YB - 1, YB + gd, zo0, zc + gw / 2)
    u_t = box(-xc - gw / 2, xc + gw / 2, YB - 1, YB + gd, zc - gw / 2, zc + gw / 2)
    groove = fuse([ring, u_l, u_r, u_t])
    lcuts.append(groove)
lid = lid.cut(fuse(lcuts)).removeSplitter()
if DETAIL:
    # foam gasket (fills the groove; compressed 3 mm cord)
    gasket = groove.common(box(-Wd, Wd, YB, YB + gd, -10, Hd + 10))
    add('Gasket_lid_foam_3mm', 'hardware', gasket, (0.1, 0.1, 0.1))
add('Lid_rear', 'lid', lid, (0.35, 0.37, 0.42))

# ------------------------------------------------------------------ perforated grilles (0.8 mm, 2.0 mm holes, 3.0 mm staggered pitch)
def hexholes(cx, cz, r):
    pts = []
    pitch = P['hole_pitch']; dy = pitch * math.sqrt(3) / 2
    n = int(r / pitch) + 2
    for j in range(-n, n + 1):
        for i in range(-n, n + 1):
            a = i * pitch + (pitch / 2 if j % 2 else 0); b = j * dy
            if a * a + b * b <= r * r:
                pts.append((cx + a, cz + b))
    return pts
tools = []
for sx in (-1, 1):
    for a, b in hexholes(sx * dcx, dzc, 28.0):
        tools.append(cyl(P['hole_d'] / 2, P['grille_t'] + 2, V(a, -P['grille_t'] - 1, b), V(0, 1, 0)))
add('Grille_front_perforated', 'grille', box(-Wd / 2, Wd / 2, -P['grille_t'], 0, 0, Hd).cut(Part.makeCompound(tools)), (0.1, 0.1, 0.1))
tools = []
for a, b in hexholes(wcx, wcy, 32.0):
    tools.append(cyl(P['hole_d'] / 2, P['grille_t'] + 2, V(a, b, -P['grille_t'] - 1)))
add('Grille_woofer_dia90', 'grille', cyl(45.0, P['grille_t'], V(wcx, wcy, -P['grille_t'])).cut(Part.makeCompound(tools)), (0.1, 0.1, 0.1))

# ------------------------------------------------------------------ fasteners: inserts, screws, standoffs, feet
nscrew = {}
for s in sites:
    p, ax = s['p'], s['axis']
    ins = cyl(P['ins_od'] / 2, P['ins_l'], p, ax).cut(cyl(P['ins_id'] / 2, P['ins_l'] + 2, p - ax * 1, ax))
    add('Insert_M3x5.7_' + s['name'], 'hardware', ins, (0.85, 0.65, 0.2))
    if s['kind'] != 'foot':
        hu = p - ax * s['head_off']                    # head underside
        L = s['screw']
        scr = cyl(2.75, 3.0, hu, ax * -1).fuse(cyl(1.5, L, hu, ax)).removeSplitter()
        add('Screw_M3x%g_%s' % (L, s['name']), 'hardware', scr, (0.55, 0.55, 0.6))
        nscrew['M3x%g' % L] = nscrew.get('M3x%g' % L, 0) + 1
        s['engage'] = round(L - s['head_off'], 2)
    else:
        body = hexprism(5.5, 12.0, V(p.x, p.y, -12.0)).fuse(cyl(1.5, 6.0, p, ax)).removeSplitter()
        add('Foot_standoff_Wurth1768061_' + s['name'], 'hardware', body, (0.75, 0.75, 0.78))
        add('Foot_rubber_disc_' + s['name'], 'hardware', cyl(6.0, 3.0, V(p.x, p.y, -15.0)), (0.05, 0.05, 0.05))
    if s['kind'] == 'pcb':
        so = hexprism(5.5, P['standoff'], V(p.x, p.y, p.z)).cut(cyl(1.6, P['standoff'] + 2, V(p.x, p.y, p.z - 1)))
        add('Standoff_M3_%gmm_%s' % (P['standoff'], s['name']), 'hardware', so, (0.75, 0.75, 0.78))

# ------------------------------------------------------------------ document, export
doc = App.newDocument('DesktopSpeaker_internal')
feats = []
for name, group, shape, color in objs:
    o = doc.addObject('Part::Feature', re.sub(r'[^A-Za-z0-9_]', '_', name))
    o.Label = name
    o.Shape = shape
    feats.append(o)
doc.recompute()
if os.path.exists(CAD + 'DesktopSpeaker_internal.FCStd'):
    os.remove(CAD + 'DesktopSpeaker_internal.FCStd')      # regenerated; avoids FreeCAD's .FCBak rotation (which deleted the tracked backup)
doc.saveAs(CAD + 'DesktopSpeaker_internal.FCStd')
try:
    import Import
    Import.export(feats, CAD + 'DesktopSpeaker_internal.step')
except Exception as e:
    print('STEP export via Import failed', e)
    Part.export(feats, CAD + 'DesktopSpeaker_internal.step')

# ------------------------------------------------------------------ printable bodies: STL in print orientation (binary)
prints = []
if DETAIL:
    import Mesh, MeshPart
    os.makedirs(PRINT, exist_ok=True)
    def orient(shape, how):
        s = shape.copy()
        if how == 'baffle_down':      # front face on the bed, +Y -> +Z
            s.rotate(V(0, 0, 0), V(1, 0, 0), 90)
        elif how == 'outer_face_down':   # lid outer face (y = D) on the bed
            s.rotate(V(0, 0, 0), V(1, 0, 0), -90)
        elif how == 'roof_down':      # insert upside down, roof top on the bed
            s.rotate(V(0, 0, 0), V(1, 0, 0), 180)
        bb = s.BoundBox
        s.translate(V(-(bb.XMin + bb.XMax) / 2, -(bb.YMin + bb.YMax) / 2, -bb.ZMin))
        return s
    for name, shape, how, sup in (('shell', shell, 'baffle_down', 'none (cavity walls vertical; lid bosses have 45 deg lead-ins; cradle ribs start on the baffle)'),
                                  ('lid', lid, 'outer_face_down', 'none (jack counterbore floors bridge 1.25 mm; chamfers on the bed side)'),
                                  ('woofer_chamber_insert', INSERT, 'roof_down', 'none (shelf gussets and bosses grow from the roof)')):
        s = orient(shape, how)
        m = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.03, AngularDeflection=0.2, Relative=False)
        fn = PRINT + 'DesktopSpeaker_%s.stl' % name
        m.write(fn)
        bb = s.BoundBox
        prints.append(dict(name=name, file=os.path.relpath(fn, ROOT), orient=how, supports=sup, size=[round(bb.XLength, 1), round(bb.YLength, 1), round(bb.ZLength, 1)],
                           volume_cm3=round(shape.Volume / 1000, 1), facets=m.CountFacets, solids=len(shape.Solids), valid=shape.isValid()))

# dump for the render / check scripts
meta = []
for name, group, shape, color in objs:
    fn = re.sub(r'[^A-Za-z0-9_.-]', '_', name) + '.brep'
    shape.exportBrep(WORK + 'brep/' + fn)
    meta.append(dict(name=name, group=group, color=color, file=fn, vol=shape.Volume))
json.dump(dict(objs=meta, params={k: v for k, v in P.items()}, detail=DETAIL, standins=standin_pcb, zfix=zfix, skipped=skipped, prints=prints,
               lid_cutouts=cut_info, cradle=CRADLE, harness=HARNESS, screws=nscrew, board_step=os.path.relpath(BOARD_STEP, ROOT),
               pcb=dict(top=PCB_TOP, bot=PCB_BOT, cx=pcx, cy=pcy, rear_edge=REAR_E),
               sites=[dict(name=s['name'], kind=s['kind'], body=s['body'], p=[round(s['p'].x, 2), round(s['p'].y, 2), round(s['p'].z, 2)],
                           engage=s.get('engage'), post=s.get('post', False)) for s in sites]),
          open(WORK + 'meta.json', 'w'), indent=1)
print('BUILD OK detail=%s objects=%d standins=%s zfix=%s skipped=%s' % (DETAIL, len(objs), standin_pcb, zfix, skipped))
print('D=%.1f YB=%.1f ch_y0=%.2f woof_cy=%.2f PCB_BOT=%.2f prints=%s' % (Dd, YB, P['ch_y0'], P['woof_cy'], PCB_BOT, json.dumps(prints)))
