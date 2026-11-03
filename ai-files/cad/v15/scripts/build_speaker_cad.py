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
CAD = ROOT + 'ai-files/cad/'                     # parts (ND65 STEP) stay here
OUT = os.environ.get('CAD_OUT', CAD + 'v15/').rstrip('/') + '/'
M13 = os.environ.get('M13_3D', CAD + 'models-v13/3d/').rstrip('/') + '/'      # v13: audited enclosure-level STEP models
ACC_CSV = os.environ.get('ACC_CSV', CAD + 'models-v13/accuracy-table.csv')
KL = ROOT + 'DesktopSpeaker-kicad/kicad-library/'
WORK = OUT + 'work/'
PRINT = OUT + 'print/'
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
        usb_cut=(12.0, 7.0, 2.0), jack_bore=8.5, jack_cb=(11.0, 2.0), sw100_bore=5.0, min_web=1.6,
        rocker_bore=20.2, rocker_panel=2.0, rocker_cb=28.0, rocker_x=63.0, rocker_z=80.0,   # CW Industries GRB112B802BR1: inside pocket to a 2.0 panel
        rocker_notch=(2.2, 1.0), rocker_flange=(25.0, 2.0), rocker_body=(19.8, 7.0), rocker_faston=(4.8, 0.8, 4.0, 6.0),
        lid_tr=(76.5, 94.0),       # top-right lid screw moved from (74, 92.5) to clear the rocker pocket
        ap_w=76.2, w_flange_od=82.55, w_depth=44.45,             # Parts Express W3-2052SC: cutout 76.2, flange 82.55, depth 44.45 (bolt circle 77 still assumed)
        cell_r=10.85, cell_l=70.2, cradle_gap=0.3,
    )
    # ---- v13 (2026-11-02): real-part geometry from ai-files/cad/models-v13/mechanical-accuracy.md
    P.update(
        # Tang Band W3-2052SC: SQUARE frame 82.55 (R4), 4 holes on a 96.52 circle = 68.25 square, frame block 13.3,
        # factory foam gasket 3.3 (front face), total 47.75 incl. gasket (model TangBand_W3-2052SC.step, origin = gasket front face)
        w_square=82.55, w_corner_r=4.0, w_bc=96.52, w_hole_sq=68.25, w_hole=3.4, w_frame_t=13.3, w_gasket=3.3, w_total=47.75,
        w_seat=0.0,              # gasket seats directly on the floor inner face (z 3.0): no ring pad, no flange recess (removed)
        ring_t=0.0, w_recess=0.0, ring_od=0.0,
        w_screw=20.0,            # ISO 4762 M3x20: head on the frame back, through frame 13.3 + gasket 3.3 into a Ruthex M3x5.7 insert
        w_boss_od=8.0, w_boss_skin=1.0,   # insert bosses under the floor (outside, teardrop toward the baffle for support-free printing)
        w_grille_d=86.0,         # woofer grille 90 -> 86 so it clears the four outside bosses
        w_front_air_d=73.7,      # gasket / frame opening: the air in front of the cone is outside air (excluded from the chamber volume)
        # cells: Samsung INR21700-50S max 21.25 x 70.62 (model at max); cradle/end stops/PCM laid out for 70.7
        cell_l=70.7,
        w_cy_off=1.5,
    )
    # v15 (2026-11-03): woofer-lead grommet moved from (x 40, z 40) to (x 50, z 47) so the J5 pack leads pass under its boss
    # and the J11 adapter pair reaches the PH junction in the free side band of the woofer chamber
    P.update(grom_x=50.0, grom_z=47.0)
    P.update(
        dish=True, dish_ref='SW102', dish_d=36.0, dish_wall=3.0, dish_floor_t=3.0, dish_expose=8.0, dish_hole=7.5 + 1.0,
        dish_leadin=2.0, dish_teardrop=True, knob_d=30.0, knob_h=14.0, knob_gap=0.75, knob_bore=6.0, knob_bore_l=10.0,
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
CH_NET_L = 0.525                              # woofer chamber NET volume target; gross = net + displaced
# v13: displaced volume measured by check_cad.py (square W3-2052SC frame + gasket + front-air correction); env CH_DISP_L overrides
CH_DISPLACED_L = float(os.environ.get('CH_DISP_L', '0.1224'))    # pass 1 (v12 value 0.056): 0.1024 displaced + 0.0199 front air
CH_LEN = (CH_NET_L + CH_DISPLACED_L) * 1e6 / ((2 * P['ch_x']) * (P['ch_top'] - t))
P['ch_y0'] = YB - t - CH_LEN
P['woof_cy'] = P['ch_y0'] + t + CH_LEN / 2.0 + P.get('w_cy_off', -2.0)     # v13: +1.5 (was -2.0) keeps the H2 PCB boss 2.9 mm off the magnet cup
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

# v15: detail module (wiring, crimps/housings, vendor-built 1S4P brick, strap, countersunk post-Torx screws), shares this namespace
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.environ.get('V15_SCRIPTS', '/home/chithi/Desktop/DesktopSpeaker/ai-files/cad/v15/scripts'), 'v15_detail.py')).read())

# ------------------------------------------------------------------ fastener sites (insert top point, axis INTO material, head underside offset from insert top)
sites = []   # dict(kind, name, p, axis, head_off, pilot, body)
dcx, dzc = P['drv_cx'], P['drv_zc']
for side, sx in (('L', -1), ('R', 1)):
    for i, (a, b) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        sites.append(dict(kind='drv', name='DrvScrew_%s%d' % (side, i + 1), p=V(sx * dcx + a * 23.4, P['drv_y_flange'], dzc + b * 23.4),
                          axis=V(0, -1, 0), head_off=0.75, pilot=10.0, body='shell', screw=10.0))
W_SEAT_Z = t + P['w_seat']          # v13: gasket front face (contact plane with the floor inner face)
W_BOSS_H = 0.0                      # outside boss height below the floor (set below from the pilot depth)
for i in range(4):
    ang = math.radians(45 + 90 * i)
    r = P['w_bc'] / 2               # 96.52 / 2 = 48.26: corner holes of the 68.25 square pattern
    zf = W_SEAT_Z
    pil = P['ins_l'] + 1.0          # insert 5.7 + 1 mm (as the PCB and lid pilots)
    W_BOSS_H = max(W_BOSS_H, pil + P['w_boss_skin'] - zf)
    sites.append(dict(kind='woof', name='WoofScrew_%d' % (i + 1), p=V(P['woof_cx'] + r * math.cos(ang), P['woof_cy'] + r * math.sin(ang), zf),
                      axis=V(0, 0, -1), head_off=P['w_frame_t'] + P['w_gasket'], pilot=pil, body='shell', screw=P['w_screw']))
for i, (hu, hv) in enumerate(P['pcb_holes']):
    sites.append(dict(kind='pcb', name='PcbScrew_%d_%s' % (i + 1, P['pcb_hole_names'][i]), p=V(P['pcb_cx'] + hu, P['pcb_cy'] + hv, RB + P['boss_h']),
                      axis=V(0, 0, -1), head_off=P['standoff'] + P['pcb_t'], pilot=P.get('pcb_pilot_l', 6.5), body='insert' if DETAIL else 'shell',
                      screw=16.0 if DETAIL else 12.0))
if DETAIL:
    lid_pts = [(-74, 7.5, 'floor'), (74, 7.5, 'floor'), (-74, 92.5, 'top'), (P['lid_tr'][0], P['lid_tr'][1], 'top'), (0, 92.5, 'top'), (-50, 7.5, 'floor'), (50, 7.5, 'floor'),
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
if P['ring_t'] > 0:
    adds.append(cyl(P['ring_od'] / 2, P['ring_t'] + 0.01, V(P['woof_cx'], P['woof_cy'], t - 0.01)))      # (v12 round ring pad; v13: none)
def teardrop_z(cx, cy, r, z0, z1):
    """circle r in the X-Y plane + 45 deg point toward -Y (the bed when printed baffle-down), extruded z0..z1"""
    k = r * math.sqrt(0.5)
    tri = Part.Face(Part.makePolygon([V(cx - k, cy - k, z0), V(cx + k, cy - k, z0), V(cx, cy - r * math.sqrt(2), z0), V(cx - k, cy - k, z0)])).extrude(V(0, 0, z1 - z0))
    return cyl(r, z1 - z0, V(cx, cy, z0)).fuse(tri).removeSplitter()
WBOSS = []
for s_ in sites:          # v13 woofer insert bosses: outside, under the floor (the pilot needs 6.7 + 1 mm skin below the 3 mm floor)
    if s_['kind'] == 'woof':
        WBOSS.append(teardrop_z(s_['p'].x, s_['p'].y, P['w_boss_od'] / 2, -W_BOSS_H, 0.01))
adds.extend(WBOSS)
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

# battery: 2P 21700 (2 x Samsung 50S, max 21.25 x 70.62; cradle laid out for 21.7 x 70.7) + PCM; cradle (DETAIL) under the drivers
# v13p4 (2026-11-03, battery feasibility study): env BATT = 2P (v13 unchanged), 3P (3 flat rows, axis X, v13 cradle extended by one row),
# 4P (1S4P brick: 4 cells side by side in X, axes along Y, PCM at the rear end against the woofer-chamber partition)
BATT = os.environ.get('BATT', '4P')        # v15 (2026-11-03): owner decision 1S4P; 2P/3P remain selectable
NCELL = int(BATT[0])
AXIS = 'Y' if BATT == '4P' else 'X'
PITCH = 21.7                       # 2 x 10.85 (v13 cell pitch: bare cell max 21.25/21.55 + wrap)
bz = t + 1.0 + 10.85
by = 33.0 + (NCELL - 2) * 10.85 if AXIS == 'X' else 0.0        # pack centre Y (axis-X layouts: rows from y 11.3 as v13)
bx0 = -36.6
CELL_POS = []                      # (x, y) of the negative-end centre of each cell, and the axis
CRADLE = {}
if DETAIL and AXIS == 'Y':
    R = P['cell_r'] + P['cradle_gap']
    cl = P['cell_l']
    x0 = 0.0
    xcs = [x0 + (i - (NCELL - 1) / 2.0) * PITCH for i in range(NCELL)]
    y_pcm1 = P['ch_y0'] - 1.0                     # PCM rear face 1 mm in front of the partition (the partition is the rear stop)
    y_pcm0 = y_pcm1 - 3.0
    cy1 = y_pcm0                                  # cell positive ends (+ strip) on the PCM
    cy0 = cy1 - cl                                # cell negative ends
    CELL_POS = [(xc, cy0) for xc in xcs]
    s45 = math.sqrt(0.5)
    def xarc(xc, a0, a1, n=12):
        return [(xc + R * math.cos(math.radians(a)), bz + R * math.sin(math.radians(a))) for a in [a0 + (a1 - a0) * k / n for k in range(n + 1)]]
    av = math.degrees(math.acos((PITCH / 2) / R))          # valley angle offset from the horizontal
    xl, xr = xcs[0] - R - 3.0, xcs[-1] + R + 3.0             # 3 mm side lips to the cell centre height
    # v15: saddle profile for the WRAPPED brick (stadium section): the outer cell arcs plus a flat bottom between them
    # (v13p4 followed each cell; its inter-cell peaks would press into the heat-shrink that bridges the valleys)
    prof = [(xl, t - 0.01), (xl, bz), (xcs[0] - R, bz)] + xarc(xcs[0], 180.0, 270.0)[1:] + xarc(xcs[-1], 270.0, 360.0) + [(xr, bz), (xr, t - 0.01)]
    def lead_in(body, y0, H):
        """45 deg lead-in below a feature whose front (-Y) face is at y0 and which rises H above the floor (print: baffle down, +Y up)"""
        L = body.copy(); L.translate(V(0, -H, 0))
        L = fuse([L, body]).common(halfspace(V(0, y0 - H, ZB_IN), V(0, 1, -1)))
        return fuse([body, L])
    H = bz - ZB_IN
    # two 3 mm saddle ribs near the cell ends; their 45 deg lead-ins (H = 11.9 mm) leave y 22.5-67.3 free for the central strap
    # (pass 1 had a third, middle rib and two straps: the lead-ins ran into both 22 mm strap bands)
    ribs_y = [cy0 + 4.0, cy1 - 7.0]
    for yr_ in ribs_y:
        # rib + 45 deg lead-in: the profile extruded over the whole lead length, cut by the 45 deg plane
        # (pass 2 translated the 3 mm rib by H, which left the rib as an unsupported shelf: found by the overhang audit)
        rib = prism_xz(prof, yr_ - H, yr_ + 3.0).common(halfspace(V(0, yr_ - H, ZB_IN), V(0, 1, -1)))
        adds.append(rib)
    # front stop: 8 mm wide fingers on each cell axis, grown from the baffle, 1 mm from the cell negative ends (nickel strip)
    for xc in xcs:
        adds.append(box(xc - 4.0, xc + 4.0, t - 0.01, cy0 - 1.0, ZB_IN - 0.01, bz))
    # strap: one 20 mm hook-and-loop strap around the brick in the X-Z plane (as v13: one strap, lying in the 1 mm floor gap under
    # the cells); anchors with tunnels along X at both sides, centred between the two rib lead-ins
    strap_y = [round(((ribs_y[0] + 3.0) + (ribs_y[1] - H)) / 2.0, 2)]
    for ys in strap_y:
        for sx in (-1, 1):
            xa0 = (xl - 7.0) if sx < 0 else (xr + 1.0)
            blk = box(xa0, xa0 + 6.0, ys - 14.0, ys + 14.0, ZB_IN - 0.01, ZB_IN + 6.0)
            blk = lead_in(blk, ys - 14.0, 6.0)
            tun = box(xa0 - 1, xa0 + 7.0, ys - 11.0, ys + 11.0, ZB_IN - 0.5, ZB_IN + 2.5)
            adds.append(blk.cut(tun))
    CRADLE.update(layout='1S4P brick, axes along Y', cells_x=[round(v, 2) for v in xcs], cells_y=(round(cy0, 2), round(cy1, 2)),
                  pcm_y=(round(y_pcm0, 2), round(y_pcm1, 2)), ribs_y=[round(v, 2) for v in ribs_y], lips_x=(round(xl, 2), round(xr, 2)),
                  strap_y=[round(v, 2) for v in strap_y], strap_w=20, tunnel=(22, 3.0), rear_stop='woofer-chamber partition (1.0 mm gap to the PCM)',
                  front_stop='4 fingers 8 mm wide from the baffle, 1.0 mm from the negative ends')
    by = (cy0 + cy1) / 2.0
elif DETAIL and AXIS == 'X' and NCELL != 2:
    # 3P: the v13 rib profile generalised to N rows (front lip, falling arc to the bottom, 45 deg tangent up to the next arc)
    R = P['cell_r'] + P['cradle_gap']
    ycs = [by + (i - (NCELL - 1) / 2.0) * PITCH for i in range(NCELL)]
    s45 = math.sqrt(0.5)
    def arc(yc, a0, a1, n=18):
        return [(yc + R * math.cos(math.radians(a)), bz + R * math.sin(math.radians(a))) for a in [a0 + (a1 - a0) * k / n for k in range(n + 1)]]
    rib_prof = [(t - 0.01, t - 0.01), (t - 0.01, bz)] + arc(ycs[0], 180, 315)
    for yp, yn in zip(ycs[:-1], ycs[1:]):
        ty, tz = yp + R * s45, bz - R * s45
        c0 = tz - ty - bz
        A, B, C = 2.0, 2 * (c0 - yn), yn ** 2 + c0 ** 2 - R * R
        yi = (-B - math.sqrt(B * B - 4 * A * C)) / (2 * A)
        ai = math.degrees(math.atan2(yi + c0, yi - yn)) % 360
        rib_prof += [(yi, yi + c0 + bz)] + arc(yn, ai, 315)[1:]
    ty2, tz2 = ycs[-1] + R * s45, bz - R * s45
    yr = ty2 + (bz - tz2)
    rib_prof += [(yr, bz), (yr, t - 0.01)]
    CRADLE['rib_y1'] = yr
    for xr in (-31.0, 22.0):
        adds.append(prism_yz(rib_prof, xr - 1.5, xr + 1.5))
    for xe in (bx0 - 1.0 - 3.0, bx0 + P['cell_l'] + 3.0 + 1.0):
        adds.append(box(xe, xe + 3.0, t - 0.01, yr, ZB_IN - 0.01, bz))
    xs = -4.5
    fa = box(xs - 14, xs + 14, t - 0.01, t + 5, ZB_IN - 0.01, ZB_IN + 6)
    ra = prism_yz([(yr + 0.5 - 6, ZB_IN - 0.01), (yr + 0.5, ZB_IN + 6), (yr + 5.5, ZB_IN + 6), (yr + 5.5, ZB_IN - 0.01)], xs - 14, xs + 14)
    tun = box(xs - 11, xs + 11, 0, yr + 20, ZB_IN - 0.5, ZB_IN + 2.5)
    adds.append(fa.cut(tun)); adds.append(ra.cut(tun))
    CRADLE.update(layout='%dP rows, axes along X' % NCELL, rows_y=[round(v, 2) for v in ycs], xs=xs, strap_w=20, tunnel=(22, 2.5))
    CELL_POS = [(bx0, yc) for yc in ycs]
elif DETAIL:
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

# ------------------------------------------------------------------ board STEP (read once) + encoder knob dish in the top wall (DETAIL)
_board_step = []
zfix = {}
def board_step():
    if not _board_step:
        _board_step.append(Part.read(BOARD_STEP))
    return _board_step[0]
DISH = None
def dish_axis(ref):
    """shaft axis (CAD X, Y) and shaft top z from the board STEP solids inside the part courtyard"""
    q = LJ['parts'][ref]['rect']
    sols = [so for so in board_step().Solids if q[0] - 0.6 <= (so.BoundBox.XMin + so.BoundBox.XMax) / 2 <= q[2] + 0.6
            and q[1] - 0.6 <= (so.BoundBox.YMin + so.BoundBox.YMax) / 2 <= q[3] + 0.6 and so.BoundBox.XLength < 50]
    c = Part.makeCompound(sols)
    ztop = c.BoundBox.ZMax
    tip = c.common(Part.makeBox(400, 400, 1.0, V(-200, -200, ztop - 1.0)))      # top 1 mm = shaft tip
    sec = tip.BoundBox
    ax_ = [(f.Surface.Center.x, f.Surface.Center.y, f.Surface.Radius) for f in tip.Faces if isinstance(f.Surface, Part.Cylinder) and 2.0 < f.Surface.Radius < 4.0]
    ux, uy = (ax_[0][0], ax_[0][1]) if ax_ else ((sec.XMin + sec.XMax) / 2, (sec.YMin + sec.YMax) / 2)   # D-shaft: axis of the round face, not the bbox centre
    if not ax_ and abs(sec.XLength - sec.YLength) > 0.3:     # D flat: find the flat side (wide chord) and put the axis R from the round side
        R = max(sec.XLength, sec.YLength) / 2
        def chord(axis, v0, v1):
            b = tip.common(box(v0, v1, -500, 500, -500, 500) if axis == 'x' else box(-500, 500, v0, v1, -500, 500)).BoundBox
            return b.YLength if axis == 'x' else b.XLength
        if sec.XLength < sec.YLength:
            ux = sec.XMin + R if chord('x', sec.XMin, sec.XMin + 0.1) < chord('x', sec.XMax - 0.1, sec.XMax) else sec.XMax - R
            uy = (sec.YMin + sec.YMax) / 2
        else:
            uy = sec.YMin + R if chord('y', sec.YMin, sec.YMin + 0.1) < chord('y', sec.YMax - 0.1, sec.YMax) else sec.YMax - R
            ux = (sec.XMin + sec.XMax) / 2
        ax_ = ['D-flat']
    # v12: the tip-chord logic above picked the flat side on the EC11E model (axis 0.86 mm off). Prefer the centre of the first
    # full round section below the D-flat (square bbox, 5-7 mm wide); keep the tip result only as a fallback.
    for k in range(3, 25):
        zs = ztop - 0.5 * k
        sl = c.common(Part.makeBox(400, 400, 0.2, V(-200, -200, zs - 0.1)))
        if sl.Volume < 1e-6:
            continue
        b = sl.BoundBox
        if abs(b.XLength - b.YLength) < 0.05 and 5.0 < b.XLength < 7.0:
            ux, uy = (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2
            ax_ = ['round section %.1f mm below the tip' % (0.5 * k)]
            break
    return P['pcb_cx'] + ux, P['pcb_cy'] + uy, PCB_BOT + ztop, (round(sec.XLength, 2), round(sec.YLength, 2), (ax_[0] if isinstance(ax_[0], str) and ax_[0] != 'D-flat' else ('D-shaft round side' if ax_ == ['D-flat'] else 'cylinder axis')) if ax_ else 'bbox centre')
def dish_profile(r, cx, cy, z0, h, tip_front=True, tip_rear_cut=None):
    """circle r, extended to 45 deg points along -Y (front) and +Y (rear) so the well prints baffle-down (+Y up) without support;
    tip_rear_cut truncates the rear point at cy + tip_rear_cut (flat bridge)"""
    parts = [cyl(r, h, V(cx, cy, z0))]
    if P['dish_teardrop']:
        k = r * math.sqrt(0.5)
        for sgn, use in ((-1, tip_front), (1, True)):
            if not use:
                continue
            apex = cy + sgn * r * math.sqrt(2)
            tri = Part.Face(Part.makePolygon([V(cx - k, cy + sgn * k, z0), V(cx + k, cy + sgn * k, z0), V(cx, apex, z0), V(cx - k, cy + sgn * k, z0)])).extrude(V(0, 0, h))
            if sgn > 0 and tip_rear_cut is not None:
                tri = tri.common(box(cx - 2 * r, cx + 2 * r, cy - 2 * r, cy + tip_rear_cut, z0 - 1, z0 + h + 1))
            parts.append(tri)
    return fuse(parts)
if DETAIL and P['dish'] and LJ and P['dish_ref'] in LJ['parts'] and os.path.exists(BOARD_STEP):
    dx, dy, shaft_top, shaft_sec = dish_axis(P['dish_ref'])
    ri, ro = P['dish_d'] / 2, P['dish_d'] / 2 + P['dish_wall']
    zf_top = shaft_top - P['dish_expose']                 # dish floor top face
    zf_bot = zf_top - P['dish_floor_t']
    well_env = dish_profile(ro, dx, dy, zf_bot, ZT_IN - zf_bot + 0.01, tip_front=True)               # outer envelope (shell material + dish air)
    dish_in = dish_profile(ri, dx, dy, zf_top, Hd - zf_top + 1.0, tip_front=False, tip_rear_cut=ro)   # dish pocket (open to the top)
    DISH = dict(cx=round(dx, 2), cy=round(dy, 2), shaft_top=round(shaft_top, 2), shaft_section=shaft_sec, floor_top=round(zf_top, 2), floor_bot=round(zf_bot, 2),
                d=P['dish_d'], wall=P['dish_wall'], hole=P['dish_hole'], exposed_shaft=P['dish_expose'],
                envelope_cm3=round(well_env.Volume / 1000, 2), pocket_cm3=round(dish_in.common(box(-Wd, Wd, -10, Dd, zf_top, ZT_IN)).Volume / 1000, 2),
                fillet_merge=bool(abs(dx) + ro > Wd / 2 - t - P.get('fillet_in', 1.0) - 0.5 or dy - ro * math.sqrt(2) < t + 1.5 or dy + ro * math.sqrt(2) > YB - 0.5))
    adds.append(well_env)
    well_env.exportBrep(WORK + 'dish_envelope.brep')
shell = shell.fuse(fuse(adds)).removeSplitter()
cuts = []
if DETAIL and AXIS == 'Y':
    cuts.append(strap_channel_tool())          # v15: 0.6 mm channel under the hook-and-loop strap
for sx in (-1, 1):
    cuts.append(cyl(P['ap_drv'] / 2, P['pad_t'] + 2, V(sx * dcx, -1, dzc), V(0, 1, 0)))
    if DETAIL:   # 0.5 mm driver gasket recess on the pad rear face: 63 mm square inside the 64 mm flange, minus the aperture and 7 mm around each screw
        q = P['drv_gasket_sq'] / 2
        g = rrect_y(sx * dcx, dzc, 2 * q, 2 * q, 4.0, P['pad_t'] - P['drv_gasket'], P['pad_t'] + 1)
        g = g.cut(cyl(P['ap_drv'] / 2 + 0.01, 5, V(sx * dcx, P['pad_t'] - 2, dzc), V(0, 1, 0)))
        for a, b in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            g = g.cut(cyl(3.5, 5, V(sx * dcx + a * 23.4, P['pad_t'] - 2, dzc + b * 23.4), V(0, 1, 0)))
        cuts.append(g)
cuts.append(cyl(P['ap_w'] / 2, t + P['ring_t'] + 2, V(P['woof_cx'], P['woof_cy'], -1)))
if DETAIL:
    if P['w_recess'] > 0:
        cuts.append(cyl(P['w_recess_d'] / 2, P['w_recess'] + 1, V(P['woof_cx'], P['woof_cy'], t + P['ring_t'] - P['w_recess'])))
    # insert locating grooves in the floor (insert walls drop 1 mm into them, 0.2 mm clearance each side)
    gc, fg = P['groove_clr'], P['floor_groove']
    g_out = box(-chx - t - gc, chx + t + gc, P['ch_y0'] - gc, YB + 1, ZB_IN - fg, ZB_IN + 0.5)
    g_in = box(-chx + gc, chx - gc, P['ch_y0'] + t + gc, YB + 2, ZB_IN - fg - 1, ZB_IN + 1)
    cuts.append(g_out.cut(g_in))
for s in sites:
    if s['body'] == 'shell':
        cuts.append(cyl(P['pilot'] / 2, s['pilot'], s['p'], s['axis']))
if DISH:
    cuts.append(dish_in)
    cuts.append(cyl(P['dish_hole'] / 2, P['dish_floor_t'] + 2, V(DISH['cx'], DISH['cy'], zf_bot - 1)))
    try:     # 45 deg lead-in on the top rim (loft of the pocket outline to a 2 mm offset)
        f0 = [f for f in dish_profile(ri, dx, dy, Hd - P['dish_leadin'], 1.0, tip_front=False, tip_rear_cut=ro).Faces
              if abs(f.BoundBox.ZMin - (Hd - P['dish_leadin'])) < 1e-6 and abs(f.BoundBox.ZMax - (Hd - P['dish_leadin'])) < 1e-6]
        f0 = Part.Face(Part.Wire(Part.__sortEdges__(fuse(f0).Edges))) if len(f0) > 1 else f0[0]
        w0 = f0.OuterWire; w1 = f0.makeOffset2D(P['dish_leadin'] + 0.02).OuterWire; w1.translate(V(0, 0, P['dish_leadin'] + 0.02))
        cuts.append(Part.makeLoft([w0, w1], True))
    except Exception as ex:
        skipped.append('dish rim lead-in: %s' % str(ex)[:80])
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
ND65 = os.environ.get('ND65_STEP', CAD + 'parts/ND65_3D/ND65-4 and 8.step')
nd = Part.read(ND65)
for name, sx in (('Driver_FrontL_ND65-4', -1), ('Driver_FrontR_ND65-4', 1)):
    s = tr(nd, V(sx * dcx, P['drv_y_flange'] + 22.75, dzc), Rot(V(1, 0, 0), -90))     # raw front = -Z, flange plane z = -22.75
    add(name, 'drivers', s, (0.15, 0.15, 0.17))

# ------------------------------------------------------------------ woofer: Tang Band W3-2052SC, models-v13 model (square frame, factory gasket)
# model frame: origin on the gasket front face at the driver axis, +z = radiating side, body toward -z -> flipped (radiates down)
def m13(name):
    return Part.read(M13 + name + '.step')
wz0 = W_SEAT_Z                      # gasket front face on the floor inner face
wcx, wcy = P['woof_cx'], P['woof_cy']
WOOF = tr(m13('TangBand_W3-2052SC'), V(wcx, wcy, wz0), Rot(V(1, 0, 0), 180))
add('Woofer_W3-2052SC', 'woofer', WOOF, (0.12, 0.12, 0.14))
# air in front of the cone (gasket + frame opening down to the cone/surround) is outside air: exported for check_cad.py
FRONT_AIR = cyl(P['w_front_air_d'] / 2, P['w_gasket'] + 3.0 + 0.5, V(wcx, wcy, t)).cut(WOOF)
FRONT_AIR.exportBrep(WORK + 'woofer_front_air.brep')

# ------------------------------------------------------------------ battery cells (models-v13 Samsung INR21700-50S at max size) + PCM
# model frame: origin = centre of the negative end, +z toward the positive cap -> cell axis along +X from bx0 (PCM at the + end)
cellm = m13('Cell_Samsung_INR21700-50S')
if DETAIL and AXIS == 'Y':      # v15: vendor-built 1S4P brick + strap
    build_pack_4p(cellm)
    build_strap()
    CELL_POS_DONE = True
else:
    CELL_POS_DONE = False
if not CELL_POS:
    CELL_POS = [(bx0, by + dy) for dy in (-10.85, 10.85)]
for i, (cx_, cy_) in enumerate(CELL_POS if not CELL_POS_DONE else []):
    add('Battery_Cell%d_21700_50S' % (i + 1), 'battery', tr(cellm, V(cx_, cy_, bz), Rot(V(0, 0, 1), V(1, 0, 0) if AXIS == 'X' else V(0, 1, 0))), (0.2, 0.45, 0.8))
if CELL_POS_DONE:
    pass
elif AXIS == 'X':
    add('Battery_PCM_board', 'battery', box(bx0 + P['cell_l'], bx0 + P['cell_l'] + 3.0, by - NCELL * 10.85, by + NCELL * 10.85, bz - 9, bz + 9), (0.1, 0.5, 0.2))
else:      # 1S4P PCM placeholder 60 x 3 x 18 (a 1S 15-20 A board is typically 40-60 mm long; UNVERIFIED)
    add('Battery_PCM_board', 'battery', box(-30.0, 30.0, CRADLE['pcm_y'][0], CRADLE['pcm_y'][1], bz - 9, bz + 9), (0.1, 0.5, 0.2))

# ------------------------------------------------------------------ PCB + components from the routed-board STEP (layout frame: STEP x = u, y = v, z = 0 at the board bottom)
pcx, pcy = P['pcb_cx'], P['pcb_cy']
BU0, BU1 = (LJ['board']['u0'], LJ['board']['u1']) if LJ else (-P['pcb_w'] / 2, P['pcb_w'] / 2)
REAR_E = LJ['board']['rear_edge_cad_y'] if LJ else 156.5
placed = {}
standin_pcb = []
OBJREFS = {}          # v13: object name -> board references (accuracy lookup)
INDIV = re.compile(r'^(J\d+|U\d+|L\d+|SW\d+|Y\d+|Q\d+|C275)$')
def at_board(s):
    return tr(s, V(pcx, pcy, PCB_BOT))
use_step = os.path.exists(BOARD_STEP) and LJ is not None
if use_step:
    comp = board_step()
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
        # v11.1: no correction (library offsets fixed in 6052ec2); floating/sunk models are only reported
        if bb.ZMin > P['pcb_t'] + 0.3 or (bb.ZMax <= P['pcb_t'] + 0.6 and -0.05 <= bb.ZMin < P['pcb_t'] - 0.1):
            zfix[ref] = round(P['pcb_t'] - bb.ZMin, 3)
        c = at_board(c)
        placed[ref] = c
        if INDIV.match(ref):
            nm = {'J1': 'PCB_J1_USB-C', 'J2': 'PCB_J2_3.5mm_jack', 'J3': 'PCB_J3_3.5mm_jack'}.get(ref, 'PCB_%s' % ref)
            add(nm, 'pcb_parts', c, (0.1, 0.1, 0.1) if ref in ('J2', 'J3') else (0.55, 0.55, 0.6))
            OBJREFS[nm] = [ref]
        else:
            sh = (LJ.get('sheets', {}).get(ref) or 'root').replace(' ', '_')
            groups.setdefault(sh, []).extend(c.Solids)
            OBJREFS.setdefault('PCB_smallparts_%s' % sh, []).append(ref)
    for sh, sols in sorted(groups.items()):
        add('PCB_smallparts_%s' % sh, 'pcb_parts', Part.makeCompound(sols), (0.5, 0.45, 0.4))
else:
    raise SystemExit('board STEP %s or layout %s missing: export with kicad-cli (README)' % (BOARD_STEP, LAYOUT_JSON))

# parametric stand-ins (no STEP in the library): J5 Micro-Fit, J9-J11 JST VH 2-pos, SW100 tact switch
def slab_bb(shape, y0, y1):
    try:
        c = shape.common(box(-500, 500, y0, y1, -500, 500))
        if c.Volume > 1e-4:
            return c.BoundBox
    except Exception:
        pass
    return None
def sbox(ref, u, v, du, dv, dz, label, color):
    s = box(pcx + u - du / 2, pcx + u + du / 2, pcy + v - dv / 2, pcy + v + dv / 2, PCB_TOP, PCB_TOP + dz)
    placed[ref] = s; standin_pcb.append(ref)
    add('PCB_%s_%s' % (ref, label), 'pcb_parts', s, color)
    return s
def rdim(ref, dflt):
    r = PL(ref, 'rect')
    return (r[2] - r[0], r[3] - r[1]) if r else dflt
# v13: J5, J9-J11 and SW100 have models-v13 STEP models in the board export; stand-ins only if a model is missing
if 'J5' not in placed:
    sbox('J5', PL('J5', 'cy_u', 46.0), PL('J5', 'cy_v', 3.0), rdim('J5', (11.0, 13.66))[0], rdim('J5', (11.0, 13.66))[1], 9.0, 'MicroFit3_standin', (0.9, 0.9, 0.85))
for ref, v in (('J9', -27.0), ('J10', -17.5), ('J11', -8.0)):
    if ref not in placed:
        sbox(ref, PL(ref, 'cy_u', -38.0), PL(ref, 'cy_v', v), 9.27, 9.5, 10.9, 'JST_B2P-VH_standin', (0.95, 0.95, 0.9))
SW_U = PL('SW100', 'origin_u', 30.0)
SW100 = {}
if 'SW100' in placed:
    # TE 1977066-1 actuator (dia 2.0) = the last 0.6 mm of the model toward the rear edge
    swb = placed['SW100'].BoundBox
    act = slab_bb(placed['SW100'], swb.YMax - 0.6, swb.YMax + 1.0)
    SW_X, SW_Z = (act.XMin + act.XMax) / 2, (act.ZMin + act.ZMax) / 2
    SW100 = dict(axis_x=round(SW_X, 3), axis_z=round(SW_Z, 3), above_board_top=round(SW_Z - PCB_TOP, 3), act_section=(round(act.XLength, 2), round(act.ZLength, 2)),
                 tip_y=round(swb.YMax, 3), tip_past_board_edge=round(swb.YMax - REAR_E, 3), tip_to_lid_inner=round(YB - swb.YMax, 3),
                 tip_to_lid_outer=round(Dd - swb.YMax, 3))
    SW_SRC = 'PCB_SW100'
else:
    SW_X, SW_Z = pcx + SW_U, PCB_TOP + 1.75          # plunger axis height (v12 assumption)
    sbox('SW100', SW_U, PL('SW100', 'cy_v', 30.0), 4.6, 5.0, 3.5, 'tact_standin', (0.3, 0.3, 0.3))
    plunger = cyl(1.25, 2.5, V(SW_X, REAR_E, SW_Z), V(0, 1, 0))
    placed['SW100_plunger'] = plunger
    add('PCB_SW100_plunger', 'pcb_parts', plunger, (0.8, 0.1, 0.1))
    SW_SRC = 'PCB_SW100_plunger'

# ------------------------------------------------------------------ PCB screws/standoffs board holes already in the STEP board body
# ------------------------------------------------------------------ SW101 rocker (panel mount, stand-in) and harnesses (schematic tubes)
rx, rz = P['rocker_x'], P['rocker_z']
if DETAIL:    # GRB112B802BR1 stand-in: 25 mm flange outside, body behind the 2.0 mm panel, 3 fastons (body + tabs about 11 mm)
    yp = Dd - P['rocker_panel']
    bd, bl = P['rocker_body']; fw, ft, fl_, fp = P['rocker_faston']
    rk = [cyl(P['rocker_flange'][0] / 2, P['rocker_flange'][1], V(rx, Dd, rz), V(0, 1, 0)),
          cyl(P['rocker_bore'] / 2 - 0.2, P['rocker_panel'], V(rx, yp, rz), V(0, 1, 0)),
          cyl(bd / 2, bl, V(rx, yp - bl, rz), V(0, 1, 0))]
    for k in (-1, 0, 1):
        rk.append(box(rx + k * fp - ft / 2, rx + k * fp + ft / 2, yp - bl - fl_, yp - bl + 0.01, rz - fw / 2, rz + fw / 2))
    rocker = fuse(rk)
else:
    rocker = fuse([cyl(9.8, 22.0, V(rx, Dd - 22.0, rz), V(0, 1, 0)), cyl(11.5, 1.5, V(rx, Dd, rz), V(0, 1, 0))])
if DETAIL:    # v13: CW GRB112B802BR1 model (models-v13; origin = cutout centre on the panel front face, +z out of the panel = CAD +Y)
    rocker = tr(m13('CW_GRB112B802BR1_Rocker'), V(rx, Dd, rz), Rot(V(0, 0, 1), V(0, 1, 0)))
    add('SW101_rocker_GRB112B802BR1', 'hardware', rocker, (0.6, 0.1, 0.1))
else:
    add('SW101_rocker_D20_standin', 'hardware', rocker, (0.6, 0.1, 0.1))
if DISH:
    kz = DISH['floor_top'] + P['knob_gap']
    knob = cyl(P['knob_d'] / 2, P['knob_h'], V(DISH['cx'], DISH['cy'], kz)).cut(cyl(P['knob_bore'] / 2, P['knob_bore_l'], V(DISH['cx'], DISH['cy'], kz - 0.01)))
    add('Knob_D30x14_standin', 'hardware', knob, (0.1, 0.1, 0.12))
    DISH.update(knob_z=(round(kz, 2), round(kz + P['knob_h'], 2)), shaft_in_knob=round(DISH['shaft_top'] - kz, 2))
def tube(pts, r):
    hs = []
    for a, b in zip(pts[:-1], pts[1:]):
        d = V(b[0] - a[0], b[1] - a[1], b[2] - a[2])
        hs.append(cyl(r, d.Length, V(*a), d))
    for q in pts[1:-1]:
        hs.append(Part.makeSphere(r, V(*q)))
    return fuse(hs)
J5U, J5V = PL('J5', 'cy_u', 46.0), PL('J5', 'cy_v', 3.0)
V15_WIRING = DETAIL and AXIS == 'Y'
if V15_WIRING:       # v15: real wires, crimps and housings (replaces the schematic tubes and the grommet stand-in)
    HARNESS = build_wiring()
elif DETAIL:
    hx, hz = Wd / 2 - t - 8.5, bz + 3.0          # right side pocket (outside the woofer chamber), above the cradle end stop
    hp = [(pcx + PL('J5', 'rect')[2] + 1.0, pcy + J5V, PCB_TOP + 4.5), (hx, pcy + J5V, PCB_TOP + 4.5), (hx, pcy + J5V, hz), (hx, by, hz),
          (bx0 + P['cell_l'] + 3.0 + 2.4, by, hz)]
    if AXIS == 'Y':      # v13p4 4P: down the right side pocket to z 29 (above the cells), forward to the PCM, then over the PCM top edge
        hz = bz + 10.85 + 1.3 + 2.0
        ypc = CRADLE['pcm_y'][0] + 0.8
        hp = hp[:2] + [(hx, pcy + J5V, hz), (hx, ypc, hz), (28.0, ypc, hz)]
else:
    hz = bz
    hp = [(pcx + PL('J5', 'rect')[2] + 2.0, pcy + J5V, PCB_TOP + 4.5), (pcx + BU1 + 2.8, pcy + J5V, PCB_TOP + 4.5), (pcx + BU1 + 2.8, pcy + J5V, hz), (pcx + BU1 + 2.8, by, hz), (39.0, by, hz)]
if not V15_WIRING:
    add('Harness_J5_to_pack_schematic', 'harness', tube(hp, 2.0), (0.8, 0.5, 0.1))
    HARNESS = dict(j5=hp)
if DETAIL and not V15_WIRING:
    # woofer leads: J11 (WOOFER) plug -> down in front of the board edge -> grommet in the partition -> woofer terminals
    jx, jy = pcx + PL('J11', 'cy_u', 45.3), pcy + PL('J11', 'cy_v', -63.6)
    gy = P['ch_y0']
    wp = [(jx, jy, PCB_TOP + 12.5), (jx, jy, PCB_TOP + 16.0), (jx, pcy + P['pcb_d'] * -0.5 - 4.5, PCB_TOP + 16.0), (jx, pcy - P['pcb_d'] / 2 - 4.5, P['grom_z']),
          (P['grom_x'], pcy - P['pcb_d'] / 2 - 4.5, P['grom_z']), (P['grom_x'], gy + t + 6.0, P['grom_z']), (wcx + 38.0, wcy, 27.0)]   # v13: to the pigtail rib (+X)
    add('Harness_woofer_leads_schematic', 'harness', tube(wp, 1.5), (0.7, 0.1, 0.1))
    HARNESS['woofer'] = wp
    # grommet stand-in: 6 mm panel hole, 1.6 mm web, ID 3.4 (two 0.5 mm2 leads)
    gx, gz = P['grom_x'], P['grom_z']
    y_web = gy + t - P['grom_web']
    grom = fuse([cyl(3.0, P['grom_web'], V(gx, y_web, gz), V(0, 1, 0)), cyl(4.6, 1.0, V(gx, y_web - 1.0, gz), V(0, 1, 0)),
                 cyl(4.6, 1.0, V(gx, gy + t, gz), V(0, 1, 0))]).cut(cyl(1.7, 10, V(gx, y_web - 3, gz), V(0, 1, 0)))
    add('Grommet_6mm_standin', 'hardware', grom, (0.05, 0.05, 0.05))

# ------------------------------------------------------------------ rear lid: cutouts from the real connector geometry in the board STEP
cut_info = []
lcuts = []
for s in sites:
    if s['kind'] == 'lid':
        lcuts.append(cyl(1.7, LT + 2, V(s['p'].x, YB - 1, s['p'].z), V(0, 1, 0)))
        if DETAIL and AXIS == 'Y':
            lcuts.append(csk_tool(s['p'].x, s['p'].z, Dd, 1))        # v15: 6.0 x 90 deg countersink for the M3x10 countersunk T10 screws
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
lcuts.append(cyl(sd / 2, LT + 2, V(SW_X, YB - 1, SW_Z), V(0, 1, 0)))
_swb = (SW100['act_section'] if SW100 else (2.5, 2.5))
cut_info.append(dict(ref='SW100', kind=('tact actuator (TE 1977066-1 model)' if SW100 else 'tact plunger (stand-in)'), shape='circle', cx=SW_X, cz=SW_Z, d=sd, body=_swb,
                     body_ymax=round(placed['SW100' if SW100 else 'SW100_plunger'].BoundBox.YMax, 2), src=SW_SRC))
web_usb_sw = abs(SW_X - ucx) - uw / 2 - sd / 2          # lid web between the USB-C clearance and the SW100 bore
if DETAIL and web_usb_sw < P['min_web']:
    # web too thin to print (board places SW100 %.1f mm from J1): join both into one keyhole opening
    xa, xb = sorted((ucx + math.copysign(uw / 2 - 0.5, SW_X - ucx), SW_X))
    lcuts.append(box(xa, xb, YB - 1, Dd + 1, SW_Z - sd / 2, SW_Z + sd / 2))
    cut_info[-1]['joined'] = 'J1'
    skipped.append('lid web J1/SW100 %.2f mm < %.1f: openings joined (keyhole); no chamfer on the joining edges' % (web_usb_sw, P['min_web']))
rd = P.get('rocker_bore', 20.2)
lcuts.append(cyl(rd / 2, LT + 2, V(rx, YB - 1, rz), V(0, 1, 0)))
if DETAIL:
    lcuts.append(cyl(P['rocker_cb'] / 2, LT - P['rocker_panel'] + 1, V(rx, YB - 1, rz), V(0, 1, 0)))       # inside pocket, panel 2.0
    nw, nd = P['rocker_notch']
    lcuts.append(box(rx - nw / 2, rx + nw / 2, YB - 1, Dd + 1, rz + rd / 2 - 0.5, rz + rd / 2 + nd))         # key notch at the top
cut_info.append(dict(ref='SW101', kind='rocker panel hole (GRB112B802BR1)', shape='circle', cx=rx, cz=rz, d=rd, body=(rd - 0.4, rd - 0.4), body_ymax=None,
                     pocket=P.get('rocker_cb'), notch=P.get('rocker_notch')))
if DETAIL:   # pocket clearances (2D, lid plane)
    rp = P['rocker_cb'] / 2
    xo_in = Wd / 2 - t / 2 - P['groove_w'] / 2; zo_in = Hd - t / 2 - P['groove_w'] / 2
    bosses = [(s_['p'].x, s_['p'].z, s_['name']) for s_ in sites if s_['kind'] == 'lid']
    nb = min(bosses, key=lambda b: math.hypot(b[0] - rx, b[1] - rz))
    jk = [c for c in cut_info if c['ref'] in ('J2', 'J3')]
    nj = min(jk, key=lambda c: math.hypot(c['cx'] - rx, c['cz'] - rz))
    ROCKER = dict(centre=(rx, rz), pocket_d=2 * rp, panel=P['rocker_panel'], gap_groove_side=round(xo_in - (rx + rp), 2), gap_groove_top=round(zo_in - (rz + rp), 2),
                  nearest_lid_screw=nb[2], gap_lid_boss=round(math.hypot(nb[0] - rx, nb[1] - rz) - rp - P['boss_od'] / 2, 2),
                  nearest_jack=nj['ref'], gap_jack_cbore=round(math.hypot(nj['cx'] - rx, nj['cz'] - rz) - rp - P['jack_cb'][0] / 2 - P['cut_chamfer'], 2),
                  body_to_board_top=round(rocker.common(box(-500, 500, -10, YB, -500, 500)).BoundBox.ZMin - PCB_TOP, 2), body_depth_behind_panel=round(Dd - rocker.BoundBox.YMin, 2))
else:
    ROCKER = None
# woofer seat (v13, square frame): aperture vs holes vs frame edge, frame vs chamber walls, magnet vs roof, bosses vs grille
hs = P['w_square'] / 2
wb = WOOF.BoundBox
WRING = dict(seat='square frame 82.55 on the floor inner face (z %.2f), factory 3.3 mm foam gasket; no ring pad, no recess' % W_SEAT_Z,
             aperture_r=P['ap_w'] / 2, frame_half=hs, frame_opening_r=P['w_front_air_d'] / 2, bolt_r=round(P['w_bc'] / 2, 3), hole_sq=P['w_hole_sq'],
             hole_r=P['w_hole'] / 2, pilot_r=P['pilot'] / 2, boss_r=P['w_boss_od'] / 2, boss_below_floor=round(W_BOSS_H, 2),
             pilot_depth=P['ins_l'] + 1.0, pilot_skin=P['w_boss_skin'],
             seal_land_on_flats=round(hs - P['ap_w'] / 2, 3),
             pilot_edge_to_aperture=round(P['w_bc'] / 2 - P['pilot'] / 2 - P['ap_w'] / 2, 2),
             hole_edge_to_frame_edge=round(hs - P['w_hole_sq'] / 2 - P['w_hole'] / 2, 2),
             frame_to_partition=round((wcy - hs) - (P['ch_y0'] + t), 2), frame_to_lid=round(YB - (wcy + hs), 2), frame_to_side_wall=round(chx - hs, 2),
             magnet_top_z=round(wb.ZMax, 2), magnet_to_roof=round(P['ch_top'] - wb.ZMax, 2),
             grille_r=P['w_grille_d'] / 2, grille_to_boss=round(P['w_bc'] / 2 - P['w_boss_od'] / 2 - P['w_grille_d'] / 2, 2),
             screw='ISO 4762 M3x%g' % P['w_screw'], head_on='frame back z %.2f' % (W_SEAT_Z + P['w_frame_t'] + P['w_gasket']),
             engage_free_gasket=round(P['w_screw'] - P['w_frame_t'] - P['w_gasket'], 2),
             engage_gasket_1mm_compressed=round(P['w_screw'] - P['w_frame_t'] - P['w_gasket'] + 1.0, 2),
             tip_to_pilot_floor=round(P['ins_l'] + 1.0 - (P['w_screw'] - P['w_frame_t'] - P['w_gasket'] + 1.0), 2),
             front_air_cm3=round(FRONT_AIR.Volume / 1000, 2))
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
            if s['kind'] == 'lid' and not (DETAIL and AXIS == 'Y'):
                lcuts.append(chamfer_tool_circle(s['p'].x, s['p'].z, 1.7, cc))
        lcuts.append(chamfer_tool_rrect(ucx, ucz, uw, uh, ur, cc))
        for ci in cut_info:
            if ci['ref'] in ('J2', 'J3'):
                lcuts.append(chamfer_tool_circle(ci['cx'], ci['cz'], P['jack_cb'][0] / 2, cc))
        lcuts.append(chamfer_tool_circle(SW_X, SW_Z, sd / 2, cc))
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
add('Grille_woofer_dia%g' % P['w_grille_d'], 'grille', cyl(P['w_grille_d'] / 2, P['grille_t'], V(wcx, wcy, -P['grille_t'])).cut(Part.makeCompound(tools)), (0.1, 0.1, 0.1))

# ------------------------------------------------------------------ fasteners: inserts, screws, standoffs, feet (v13: models-v13 STEP models)
# frames (models-v13/gen/build_mech.py): screw origin = under-head bearing face, head +z, shank -z; insert origin = top face, body -z;
# spacer origin = bottom face, +z; stud origin = body bottom (stud root), body +z, male stud -z
def socket_cap(L):
    """ISO 4762 M3 x L as models-v13 build_mech.socket_cap (head 5.5 x 3.0, socket 2.5 AF x 1.3, shank 3.0 plain); for lengths not in models-v13"""
    rr = 2.5 / math.sqrt(3)
    hexs = Part.Face(Part.makePolygon([V(rr * math.cos(math.radians(a_)), rr * math.sin(math.radians(a_)), 3.0 - 1.3) for a_ in range(0, 420, 60)])).extrude(V(0, 0, 1.3))
    head = cyl(2.75, 3.0, V(0, 0, 0)).cut(hexs)
    try:
        head = head.makeChamfer(0.2, [e for e in head.Edges if abs(e.BoundBox.ZMin - 3.0) < 1e-6 and e.BoundBox.XLength > 5])
    except Exception:
        pass
    return head.fuse(cyl(1.5, L, V(0, 0, -L))).removeSplitter()
_fm = {}
def fmodel(key):
    if key not in _fm:
        files = {'M3x10': 'Screw_ISO4762_M3x10', 'M3x16': 'Screw_ISO4762_M3x16', 'insert': 'Insert_Ruthex_RX-M3x5.7',
                 'spacer': 'Spacer_Wurth_970100321_M3x10_FF', 'stud': 'Stud_Wurth_971120321_M3x12_MF'}
        if key in files:
            _fm[key] = m13(files[key])
        elif key.startswith('M3x'):
            _fm[key] = socket_cap(float(key[3:]))
    return _fm[key]
GENERATED_SCREWS = set()
nscrew = {}
for s in sites:
    p, ax = s['p'], s['axis']
    rot_in = Rot(V(0, 0, 1), ax * -1)           # model +z -> -axis (out of the material)
    add('Insert_M3x5.7_' + s['name'], 'hardware', tr(fmodel('insert'), p, rot_in), (0.85, 0.65, 0.2))
    if s['kind'] in ('lid', 'drv') and DETAIL and AXIS == 'Y':     # v15: M3x10 countersunk post-Torx T10 (Hobson) + cup washer on the ND65 flange
        hw = CUPW['h'] if s['kind'] == 'drv' else 0.0
        top = p - ax * (s['head_off'] + hw)              # head top (lid: flush with the outer face; driver: flush with the cup washer top)
        if s['kind'] == 'drv':
            add('Washer_cupM3_' + s['name'], 'hardware', tr(cup_washer(), p - ax * s['head_off'], rot_in), (0.72, 0.72, 0.75))
        if 'M3x10CSK' not in _fm:
            _fm['M3x10CSK'] = csk_screw(10.0)
        add('Screw_M3x10CSK_' + s['name'], 'hardware', tr(_fm['M3x10CSK'], top, rot_in), (0.62, 0.62, 0.66))
        nscrew['M3x10 CSK post-Torx T10'] = nscrew.get('M3x10 CSK post-Torx T10', 0) + 1
        s['engage'] = round(10.0 - CSK['k'] - (s['head_off'] + hw - CSK['k']) if False else 10.0 - (s['head_off'] + hw), 2)
        s['engage_note'] = 'thread below the %s: %.2f mm (insert 5.7)' % ('lid inner face' if s['kind'] == 'lid' else 'pad face', 10.0 - (s['head_off'] + hw))
    elif s['kind'] != 'foot':
        hu = p - ax * s['head_off']                    # head underside
        L = s['screw']
        key = 'M3x%g' % L
        if key not in ('M3x10', 'M3x16'):
            GENERATED_SCREWS.add(key)
        add('Screw_M3x%g_%s' % (L, s['name']), 'hardware', tr(fmodel(key), hu, rot_in), (0.55, 0.55, 0.6))
        nscrew[key] = nscrew.get(key, 0) + 1
        s['engage'] = round(L - s['head_off'], 2)
    else:
        add('Foot_standoff_Wurth971120321_' + s['name'], 'hardware', tr(fmodel('stud'), V(p.x, p.y, p.z), Rot(V(1, 0, 0), 180)), (0.75, 0.75, 0.78))
        add('Foot_rubber_disc_' + s['name'], 'hardware', cyl(6.0, 3.0, V(p.x, p.y, -15.0)), (0.05, 0.05, 0.05))     # not selected: parametric
    if s['kind'] == 'pcb':
        add('Standoff_M3_%gmm_%s' % (P['standoff'], s['name']), 'hardware', tr(fmodel('spacer'), V(p.x, p.y, p.z)), (0.75, 0.75, 0.78))

# ------------------------------------------------------------------ document, export
if os.environ.get('SKIP_EXPORT', '0') != '1':        # v13p4: FCStd/STEP export optional (SKIP_EXPORT=1 for the study variants)
    doc = App.newDocument('DesktopSpeaker_internal')
    feats = []
    for name, group, shape, color in objs:
        o = doc.addObject('Part::Feature', re.sub(r'[^A-Za-z0-9_]', '_', name))
        o.Label = name
        o.Shape = shape
        feats.append(o)
    doc.recompute()
    if os.path.exists(OUT + 'DesktopSpeaker_internal.FCStd'):
        os.remove(OUT + 'DesktopSpeaker_internal.FCStd')      # regenerated; avoids FreeCAD's .FCBak rotation (which deleted the tracked backup)
    doc.saveAs(OUT + 'DesktopSpeaker_internal.FCStd')
    try:
        import Import
        Import.export(feats, OUT + 'DesktopSpeaker_internal.step')
    except Exception as e:
        print('STEP export via Import failed', e)
        Part.export(feats, OUT + 'DesktopSpeaker_internal.step')

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
                                  ('lid', lid, 'outer_face_down', 'none (jack counterbore floors bridge 1.25 mm; chamfers on the bed side; rocker pocket on the top face)'),
                                  ('woofer_chamber_insert', INSERT, 'roof_down', 'none (shelf gussets and bosses grow from the roof)')):
        s = orient(shape, how)
        m = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.03, AngularDeflection=0.2, Relative=False)
        fn = PRINT + 'DesktopSpeaker_%s.stl' % name
        m.write(fn)
        bb = s.BoundBox
        prints.append(dict(name=name, file=os.path.relpath(fn, ROOT), orient=how, supports=sup, size=[round(bb.XLength, 1), round(bb.YLength, 1), round(bb.ZLength, 1)],
                           volume_cm3=round(shape.Volume / 1000, 1), facets=m.CountFacets, solids=len(shape.Solids), valid=shape.isValid()))

# dump for the render / check scripts
# v13 per-object provenance and accuracy from the models-v13 audit (accuracy-table.csv for board parts, mechanical-accuracy.md for
# enclosure parts). '<0.5mm' only where the audit compared the model with a drawing / standard; 'estimated' = known deviation or
# placeholder for an unselected part; 'unverified' = no drawing could be compared.
STANDIN_SRC = {'J5': 'courtyard box (no STEP)', 'J9': 'courtyard-size box (no STEP)', 'J10': 'courtyard-size box (no STEP)', 'J11': 'courtyard-size box (no STEP)', 'SW100': 'parametric box + plunger (no STEP)'}
import csv
ACC = {r['ref']: r for r in csv.DictReader(open(ACC_CSV))}
FP_ERR = {'J2': 'footprint fixed in RT-14: front NPTH pegs at x -4.75 (PJ-307 drawing)',
          'J3': 'footprint fixed in RT-14: front NPTH pegs at x -4.75 (PJ-307 drawing)',
          'U1': 'footprint fixed in RT-14: GND pad 56 at +4.77 (DS70005402D Fig. 8-2); model offset y -0.427 applied',
          'SW100': 'footprint redrawn from TE 1977066-1 rev C1 in RT-14 (lands +-1.225 x 0.75, pegs 0.9 on the actuator side, bracket pads); actuator at the board edge',
          'C275': 'land CP_Elec_6.3x7.7 in RT-14 matches case D8 (EEHZA1E101XP)'}   # v14: RT-14 carries the four footprint fixes
def ref_accuracy(ref):
    r = ACC.get(ref)
    if r is None:
        return 'unverified', 'not in the models-v13 accuracy table'
    v = r['verdict_after']
    note = FP_ERR.get(ref, '')
    if v.startswith('OK'):
        return '<0.5mm', note or ('dev %s mm vs %s' % (r['dev_after'], (r['evidence'] or '')[:80]))
    if v.startswith('UNVERIFIED'):
        return 'unverified', (r['notes'] or 'no maker drawing')[:160]
    return 'unverified', v
def model_source(name, group):
    if group in ('shell', 'lid', 'insert'):
        return 'parametric design master (build_speaker_cad.py v15)', '<0.5mm', 'design master: the print is made from this model'
    if group == 'drivers':
        return ('maker STEP: Dayton Audio ND65-4 3D files (daytonaudio.com, 2025-11-20) ' + os.path.basename(ND65), 'estimated',
                'audited (mechanical-accuracy.md): depth 48.0 exact, holes 0.12/0.3 off spec, but the scan-derived flange is 0.9 mm wider in y and '
                'the hole pattern is 0.35 mm off the cone axis')
    if group == 'woofer':
        return ('models-v13 TangBand_W3-2052SC.step (Parts Express item data: square 82.55, bolt circle 96.52, cutout 76.2, depth 44.45; '
                'photo estimates for gasket 3.3, frame 13.3, holes, magnet, basket)', 'estimated',
                'seller numbers exact; photo-derived details +-1.5 mm UNVERIFIED (caliper checklist in mechanical-accuracy.md)')
    if group == 'battery' and AXIS == 'Y' and 'Cell' not in name:
        return ('parametric vendor-built brick part (%s): wrap 0.25, nickel 0.15, fish paper 0.25, PCM 60 x 18 x 1.6 + parts, NTC 103AT dia 2.4' % name.split('_', 1)[1],
                'estimated', 'placeholder: the real pack outline, PCM and holder come from the vendor (RFQ)')
    if group == 'battery':
        if 'Cell' in name:
            return ('models-v13 Cell_Samsung_INR21700-50S.step (Samsung SDI introduction 2021 p.2, modelled at max 21.25 x 70.62)', '<0.5mm',
                    'envelope = datasheet max; cap/button geometry assumed')
        if AXIS == 'Y':
            return 'parametric box 60 x 3 x 18 on the + end (1S4P PCM / holder not sourced; RFQ battery-pack-rfq.md)', 'estimated', 'placeholder (part not selected; real PCM size UNVERIFIED)'
        return 'parametric box 3 x %.1f x 18, PCM board not sourced' % (NCELL * 21.7), 'estimated', 'placeholder (part not selected)'
    if group == 'pcb':
        return 'KiCad board STEP (kicad-cli export of %s)' % os.path.basename(BOARD_STEP), '<0.5mm', 'board outline and holes from the KiCad board'
    if group == 'pcb_parts':
        for r, src in STANDIN_SRC.items():
            if name.startswith('PCB_%s_' % r) and 'standin' in name:
                return src, 'estimated', 'stand-in'
        refs = OBJREFS.get(name, [])
        accs = [(r_, ref_accuracy(r_)) for r_ in refs]
        bad = [r_ for r_, a_ in accs if a_[0] != '<0.5mm']
        if len(refs) == 1:
            r0 = ACC.get(refs[0], {})
            return ('board STEP via KiCad: %s (%s)' % (r0.get('model_after', '?'), r0.get('source_after', '?')), accs[0][1][0], accs[0][1][1])
        if not bad:
            return 'board STEP via KiCad: %d parts, all audited' % len(refs), '<0.5mm', 'all %d parts verified in accuracy-table.csv' % len(refs)
        return ('board STEP via KiCad: %d parts' % len(refs), 'unverified',
                '%d of %d parts verified; unverified: %s' % (len(refs) - len(bad), len(refs), ' '.join(sorted(bad))))
    if group == 'grille':
        return 'parametric (0.8 mm perforated sheet, custom, made to the CAD; not sourced)', '<0.5mm', 'design master (custom part made to the CAD)'
    if group == 'harness':
        return 'schematic tube', 'estimated', 'route only, wire not modelled'
    if group == 'wiring':
        w_ = [x for x in WIRING if x['name'] == name]
        if w_:
            w_ = w_[0]
            return ('parametric swept wire: %s, %s, length %.0f mm (bend radius min %.1f mm = %.1f x OD)' % (w_['gauge'], w_['colour'], w_['length_mm'], w_['min_bend_radius_mm'], w_['bend_ratio'])
                    if w_['min_bend_radius_mm'] < 1e8 else 'parametric straight wire: %s, %s, %.0f mm' % (w_['gauge'], w_['colour'], w_['length_mm'])), 'estimated', 'route designed in CAD; OD typical for the gauge (UNVERIFIED for the bought wire)'
        if 'VHR-2N' in name:
            return 'parametric JST VHR-2N from the JST VH datasheet (datasheets/JST_VH.pdf: B 7.86, depth 10.5, height 13.3, mated height 16.5)', '<0.5mm', 'outer envelope from the datasheet; latch and cavity detail simplified'
        if 'PHR-2' in name and name.startswith('Housing'):
            return 'parametric JST PHR-2 from the JST PH datasheet (ePH.pdf: B 5.8, depth 4.5, height 6.0)', '<0.5mm', 'outer envelope from the datasheet; cavities simplified'
        if '43645' in name:
            return 'parametric Molex 43645-0300 receptacle: towers fitted to the audited 43650-0300 header holes; body 9.9 x 5.2 x 5.0 ESTIMATED', 'estimated', 'Molex drawing not obtained (download refused); check against the part'
        if 'PH_male' in name:
            return 'parametric inline JST-PH-compatible 2-pin male plug (B2B-PH-style shroud, non-JST hobby part), 6.4 x 4.9 x 6.5 ESTIMATED', 'estimated', 'no drawing'
        if name.startswith('Crimp_'):
            return 'parametric crimp terminal (%s), simplified box + barrels inside the housing cavity' % name.split('_')[-2], 'estimated', 'dimensions estimated; wire ranges from the JST/Molex data'
        if name.startswith(('Sleeve_', 'Solder_')):
            return 'parametric heat-shrink / solder joint', 'estimated', ''
    if name.startswith('Screw_M3x10CSK'):
        return 'parametric M3x10 countersunk post-Torx T10 (Hobson Engineering via boltandnut.com.au: head 5.90, height 2.00, 90 deg)', 'estimated', 'vendor page values; head modelled as 0.55 cylinder + 90 deg cone, T10 six-lobe recess with centre pin'
    if name.startswith('Washer_cup'):
        return CUPW['src'], 'estimated', 'not sourced: owner to pick a stainless M3 cup (finishing) washer about 8 x 1.6'
    if name.startswith('Strap_'):
        return 'parametric 20 x 1.2 hook-and-loop strap on its tensioned path', 'estimated', 'width and thickness UNVERIFIED'
    if name.startswith('Grommet_Heyco'):
        return 'parametric Heyco 2000 snap bushing (ID 3.56, 6.35 hole, panel 1.57)', 'estimated', 'CAD hole is 6.0 (ream to 6.35, known finding)'
    if name.startswith('SW101'):
        return ('models-v13 CW_GRB112B802BR1_Rocker.step (CW drawing R13-112B8-02-BRR-L1 rev 3)', '<0.5mm',
                'audit: main dimensions within 0.4 mm of the drawing (tolerance +-0.3/+-1); bezel thickness, clips and low side scaled from the drawing')
    if name.startswith('Knob'):
        return 'parametric stand-in D30 x 14 (knob not selected; models-v13 stand-in has the same envelope)', 'estimated', 'placeholder (part not selected)'
    if name.startswith('Screw_'):
        L = name.split('_')[1]
        if L in GENERATED_SCREWS:
            return ('ISO 4762 %s nominal, generated with the models-v13 socket_cap geometry (M3x10/M3x16 audited)' % L, '<0.5mm', 'standard nominal dimensions')
        return 'models-v13 Screw_ISO4762_%s.step (ISO 4762 nominal)' % L, '<0.5mm', 'standard nominal dimensions'
    if name.startswith('Insert_'):
        return 'models-v13 Insert_Ruthex_RX-M3x5.7.step (retailer table: OD 4.6, L 5.7)', '<0.5mm', 'audit OK vs the retailer table; maker drawing not obtained'
    if name.startswith('Standoff_'):
        return 'models-v13 Spacer_Wurth_970100321_M3x10_FF.step (distributor data, 5.5 AF x 10)', '<0.5mm', 'audit OK; Wurth datasheet blocked (403)'
    if name.startswith('Foot_standoff'):
        return 'models-v13 Stud_Wurth_971120321_M3x12_MF.step (5.5 AF, 12 + 6)', '<0.5mm', 'audit OK; distributor data'
    if name.startswith('Foot_rubber'):
        return 'parametric disc 12 x 3 (rubber foot not selected)', 'estimated', 'placeholder (part not selected)'
    if name.startswith(('Gasket_', 'Grommet_')):
        return 'parametric (material/part not selected)', 'estimated', 'placeholder'
    return 'parametric stand-in', 'estimated', ''

meta = []
for name, group, shape, color in objs:
    fn = re.sub(r'[^A-Za-z0-9_.-]', '_', name) + '.brep'
    shape.exportBrep(WORK + 'brep/' + fn)
    src, acc, note = model_source(name, group)
    meta.append(dict(name=name, group=group, color=color, file=fn, vol=shape.Volume, model_source=src, accuracy=acc, accuracy_note=note,
                     refs=OBJREFS.get(name)))
json.dump(dict(objs=meta, params={k: v for k, v in P.items()}, detail=DETAIL, standins=standin_pcb, zfix=zfix, skipped=skipped, prints=prints,
               lid_cutouts=cut_info, batt=BATT, n_cells=NCELL, cradle=CRADLE, pack=PACKD, wiring=WIRING, csk=CSK, cup_washer=CUPW, dish=DISH, rocker=ROCKER, woofer_ring=WRING, sw100=SW100, ch_disp_L=CH_DISPLACED_L, ch_len=CH_LEN, harness=HARNESS, screws=nscrew, board_step=os.path.relpath(BOARD_STEP, ROOT),
               pcb=dict(top=PCB_TOP, bot=PCB_BOT, cx=pcx, cy=pcy, rear_edge=REAR_E),
               sites=[dict(name=s['name'], kind=s['kind'], body=s['body'], p=[round(s['p'].x, 2), round(s['p'].y, 2), round(s['p'].z, 2)],
                           engage=s.get('engage'), engage_note=s.get('engage_note'), post=s.get('post', False)) for s in sites]),
          open(WORK + 'meta.json', 'w'), indent=1)
print('BUILD OK detail=%s objects=%d standins=%s zfix=%s skipped=%s' % (DETAIL, len(objs), standin_pcb, zfix, skipped))
print('D=%.1f YB=%.1f ch_y0=%.2f woof_cy=%.2f PCB_BOT=%.2f prints=%s' % (Dd, YB, P['ch_y0'], P['woof_cy'], PCB_BOT, json.dumps(prints)))
