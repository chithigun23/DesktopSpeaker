# -*- coding: utf-8 -*-
"""Parametric internal CAD of the DesktopSpeaker enclosure (FreeCAD 1.0, headless).

Run:  freecadcmd ai-files/cad/build_speaker_cad.py        (from the project root)
Outputs (all under ai-files/cad/): DesktopSpeaker_internal.FCStd/.step, work/shapes.pkl-like brep dir,
interference.md, volumes.md, mechanical-bom.md, work/render_meta.json.
Axes: X = long side (left/right), Y = depth (0 = front outer face, +Y = rear), Z = up (0 = outer bottom).
All dimensions in mm.  Only the PCB size is an estimate (see pcb-size-estimate.md).
"""
import os, re, json, math, itertools
import FreeCAD as App
import Part
from FreeCAD import Vector as V, Rotation as Rot, Placement as Pl

ROOT = '/home/chithi/Desktop/DesktopSpeaker/'
CAD = ROOT + 'ai-files/cad/'
KL = ROOT + 'DesktopSpeaker-kicad/kicad-library/'
WORK = CAD + 'work/'
os.makedirs(WORK + 'brep', exist_ok=True)

# ------------------------------------------------------------------ parameters
P = dict(
    W=163.0, H=100.0, D=160.0, wall=3.0,
    pad_t=11.0,             # front baffle thickness at driver pads (3 wall + 8 raised): M3x10 through a 0.75 mm flange
    pad_w=70.0,
    drv_cx=41.0, drv_zc=61.55, drv_y_flange=11.0,
    ap_drv=59.5, cbore_d=0.0, cbore_h=0.0,
    ch_x=58.0, ch_y0=59.0, ch_top=54.0, roof=3.0,        # woofer chamber: inner x +-58, front wall y 59..62, inner top z 54
    woof_cx=0.0, woof_cy=109.5, ap_w=70.0, ring_od=86.0, ring_t=4.5, w_flange_od=82.6, w_flange_t=4.0,
    w_bc=77.0, w_hole=3.5, w_depth=44.5,
    boss_od=8.0, boss_h=4.5, pilot=4.6, ins_od=4.6, ins_id=3.0, ins_l=5.7,
    pcb_w=100.0, pcb_d=66.0, pcb_t=1.6, pcb_cx=0.0, pcb_cy=123.5, pcb_hole=(47.0, 29.5), standoff=5.0,
    grille_t=0.8, hole_d=2.0, hole_pitch=3.0,
)
Wd, Hd, Dd, t = P['W'], P['H'], P['D'], P['wall']
YB = Dd - t                                   # rear end of the shell (lid sits at YB..Dd)
ZB_IN, ZT_IN = t, Hd - t
RB = P['ch_top'] + P['roof']                  # roof top z
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

# ------------------------------------------------------------------ fastener sites (insert top point, axis INTO material, head underside offset from insert top)
sites = []   # dict(kind, name, p, axis, head_off, pilot)
dcx, dzc = P['drv_cx'], P['drv_zc']
for side, sx in (('L', -1), ('R', 1)):
    for i, (a, b) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        sites.append(dict(kind='drv', name='DrvScrew_%s%d' % (side, i + 1), p=V(sx * dcx + a * 23.4, P['drv_y_flange'], dzc + b * 23.4),
                          axis=V(0, -1, 0), head_off=0.75, pilot=10.0, stack='flange'))
for i in range(4):
    ang = math.radians(45 + 90 * i)
    r = P['w_bc'] / 2
    sites.append(dict(kind='woof', name='WoofScrew_%d' % (i + 1), p=V(P['woof_cx'] + r * math.cos(ang), P['woof_cy'] + r * math.sin(ang), t + P['ring_t']),
                      axis=V(0, 0, -1), head_off=P['w_flange_t'], pilot=6.5, stack='flange'))
hx, hy = P['pcb_hole']
for i, (a, b) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
    sites.append(dict(kind='pcb', name='PcbScrew_%d' % (i + 1), p=V(P['pcb_cx'] + a * hx, P['pcb_cy'] + b * hy, RB + P['boss_h']),
                      axis=V(0, 0, -1), head_off=P['standoff'] + P['pcb_t'], pilot=6.5, stack='pcb'))
lid_pts = [(-74, 7.5), (74, 7.5), (-74, 92.5), (74, 92.5), (0, 92.5), (-50, 7.5), (50, 7.5)]
for i, (x, z) in enumerate(lid_pts):
    sites.append(dict(kind='lid', name='LidScrew_%d' % (i + 1), p=V(x, YB, z), axis=V(0, -1, 0), head_off=t, pilot=8.0, stack='lid'))
feet_pts = [(-68, 25), (68, 25), (-68, 135), (68, 135)]
for i, (x, y) in enumerate(feet_pts):
    sites.append(dict(kind='foot', name='Foot_%d' % (i + 1), p=V(x, y, 0), axis=V(0, 0, 1), head_off=0, pilot=6.5, stack='foot'))

# ------------------------------------------------------------------ main shell (box): front baffle + 4 walls + woofer chamber + bosses
outer = box(-Wd / 2, Wd / 2, 0, YB, 0, Hd)
cav = box(-Wd / 2 + t, Wd / 2 - t, t, YB, ZB_IN, ZT_IN)
shell = outer.cut(cav)
adds = []
for sx in (-1, 1):                                    # raised driver mounting pads (flat front face stays 3 mm baffle plus pad)
    adds.append(box(sx * dcx - P['pad_w'] / 2, sx * dcx + P['pad_w'] / 2, t, P['pad_t'], dzc - P['pad_w'] / 2, dzc + P['pad_w'] / 2))
chx = P['ch_x']
chamber_out = box(-chx - t, chx + t, P['ch_y0'], YB, ZB_IN, RB)
chamber_in = box(-chx, chx, P['ch_y0'] + t, YB, ZB_IN, P['ch_top'])
adds.append(chamber_out.cut(chamber_in))
adds.append(cyl(P['ring_od'] / 2, P['ring_t'], V(P['woof_cx'], P['woof_cy'], t)))      # woofer mounting ring pad
for s in sites:
    p = s['p']
    if s['kind'] == 'pcb':
        adds.append(cyl(P['boss_od'] / 2, P['boss_h'], V(p.x, p.y, RB)))
    elif s['kind'] == 'lid':
        adds.append(cyl(P['boss_od'] / 2, 10.0, V(p.x, p.y - 10.0, p.z), V(0, 1, 0)))
    elif s['kind'] == 'foot':
        adds.append(cyl(P['boss_od'] / 2, P['boss_h'], V(p.x, p.y, t)))
shell = shell.fuse(fuse(adds)).removeSplitter()
cuts = []
for sx in (-1, 1):
    cuts.append(cyl(P['ap_drv'] / 2, P['pad_t'] + 2, V(sx * dcx, -1, dzc), V(0, 1, 0)))
cuts.append(cyl(P['ap_w'] / 2, t + P['ring_t'] + 1, V(P['woof_cx'], P['woof_cy'], -1)))
for s in sites:
    cuts.append(cyl(P['pilot'] / 2, s['pilot'], s['p'], s['axis']))       # pilot holes for heat-set inserts (dia = insert OD in the model)
shell = shell.cut(fuse(cuts)).removeSplitter()
add('Shell_Box', 'shell', shell, (0.28, 0.30, 0.34))

# ------------------------------------------------------------------ STEP loader helpers
_cache = {}
def load_step(path):
    if path not in _cache:
        _cache[path] = Part.read(path)
    return _cache[path].copy()

def fp_model(fpname):
    """(step path, offset, scale, rotate) from a .kicad_mod, or None."""
    f = KL + 'footprint/' + fpname.split(':')[-1] + '.kicad_mod'
    if not os.path.exists(f):
        return None
    txt = open(f).read()
    i = txt.find('(model "')
    if i < 0:
        return None
    depth, j = 0, i
    while True:
        c = txt[j]
        depth += (c == '(') - (c == ')')
        j += 1
        if depth == 0: break
    blk = txt[i:j]
    path = re.search(r'\(model "([^"]+)"', blk).group(1).replace('${KIPRJMOD}', ROOT + 'DesktopSpeaker-kicad')
    g = lambda key, d: [float(x) for x in re.search(r'\(%s\s*\(xyz ([-\d. ]+)\)' % key, blk).group(1).split()] if re.search(r'\(%s\s*\(xyz ([-\d. ]+)\)' % key, blk) else d
    return path, g('offset', [0, 0, 0]), g('scale', [1, 1, 1]), g('rotate', [0, 0, 0])

def fp_oriented(fpname, ignore_rotz=False):
    m = fp_model(fpname)
    if not m or not os.path.exists(m[0]):
        return None
    path, off, sc, rt = m
    s = load_step(path)
    rz = 0 if ignore_rotz else rt[2]
    s = tr(s, V(off[0], off[1], off[2]), Rot(rz, rt[1], rt[0]))
    return s

# ------------------------------------------------------------------ front drivers (real maker STEP)
ND65 = CAD + 'parts/ND65_3D/ND65-4 and 8.step'
nd = Part.read(ND65)
for name, sx in (('Driver_FrontL_ND65-4', -1), ('Driver_FrontR_ND65-4', 1)):
    # maker model: front = -Z, flange plane z=-22.75, magnet rear z=+22.  Map raw (x,y,z)->(x, z, -y): rotate about X by -90
    s = tr(nd, V(sx * dcx, P['drv_y_flange'] + 22.75, dzc), Rot(V(1, 0, 0), -90))
    add(name, 'drivers', s, (0.15, 0.15, 0.17))

# ------------------------------------------------------------------ woofer: Tang Band W3-2052SC parametric stand-in (no maker STEP, dims from Parts Express listing)
wz0 = t + P['ring_t']                       # flange front face z (sits on the ring pad)
wcx, wcy = P['woof_cx'], P['woof_cy']
fl = cyl(P['w_flange_od'] / 2, P['w_flange_t'], V(wcx, wcy, wz0)).cut(cyl(31.0, P['w_flange_t'] + 1, V(wcx, wcy, wz0 - 0.5)))
for s in sites:
    if s['kind'] == 'woof':
        fl = fl.cut(cyl(P['w_hole'] / 2 + 0.05, 6, V(s['p'].x, s['p'].y, wz0 - 1)))
bas_h = 24.5 - P['w_flange_t'] + P['w_flange_t']      # cone+basket frustum from front face up
outer_c = Part.makeCone(31.0, 20.0, 24.5, V(wcx, wcy, wz0), V(0, 0, 1))
inner_c = Part.makeCone(28.0, 17.0, 24.5, V(wcx, wcy, wz0 - 0.0), V(0, 0, 1))
shellcone = outer_c.cut(inner_c)
mag = cyl(20.0, P['w_depth'] - 24.5, V(wcx, wcy, wz0 + 24.5))
woofer = fuse([fl, shellcone, mag])
add('Woofer_W3-2052SC_standin', 'woofer', woofer, (0.12, 0.12, 0.14))

# ------------------------------------------------------------------ battery: 2P 21700 (2 x Samsung 50S 5 Ah, 21.7 dia x 70.2) + PCM board + NTC
bz = t + 1.0 + 10.85
by = 33.0
bx0 = -36.6
for i, dy in enumerate((-10.85, 10.85)):
    add('Battery_Cell%d_21700_50S' % (i + 1), 'battery', cyl(10.85, 70.2, V(bx0, by + dy, bz), V(1, 0, 0)), (0.2, 0.45, 0.8))
add('Battery_PCM_board', 'battery', box(bx0 + 70.2, bx0 + 73.2, by - 21.7, by + 21.7, bz - 9, bz + 9), (0.1, 0.5, 0.2))

# ------------------------------------------------------------------ PCB
import xml.etree.ElementTree as ET
nl = {c.get('ref'): (c.findtext('footprint') or '') for c in ET.parse(WORK + 'net.xml').getroot().find('components')}
pcx, pcy = P['pcb_cx'], P['pcb_cy']        # board rear edge = 123.5+33 = 156.5 (0.5 mm clear of the lid)
P['pcb_cy'] = pcy
for s in sites:
    if s['kind'] == 'pcb':
        pass
board = box(pcx - P['pcb_w'] / 2, pcx + P['pcb_w'] / 2, pcy - P['pcb_d'] / 2, pcy + P['pcb_d'] / 2, PCB_BOT, PCB_TOP)
for s in sites:
    if s['kind'] == 'pcb':
        board = board.cut(cyl(1.6, 3, V(s['p'].x, s['p'].y, PCB_BOT - 1)))
add('PCB_estimated_100x66x1.6', 'pcb', board, (0.05, 0.35, 0.15))

YF_USB, YF_JACK = 158.5, 156.6
placed = {}
def put(ref, shape, u, v, yaw=0.0, center=True, zfix=True, origin_y=None):
    s = shape
    if center:
        bb = s.BoundBox
        s = tr(s, V(-(bb.XMin + bb.XMax) / 2, -(bb.YMin + bb.YMax) / 2, 0))
        bb = s.BoundBox
        if zfix and bb.ZMin > 0.3:
            s = tr(s, V(0, 0, -bb.ZMin))
    s = tr(s, V(0, 0, 0), Rot(yaw, 0, 0))
    pos = V(pcx + u, pcy + v, PCB_TOP)
    s = tr(s, pos)
    placed[ref] = s
    return s

# (ref, u, v, yaw) ; centred placement for ICs / inductors / caps / headers
LAYOUT = [
    ('U1', -42.0, 16.0, 90.0), ('U3', -8.0, 12.0, 0.0), ('U2', 10.0, 14.0, 0.0), ('U24', -20.0, 8.0, 0.0),
    ('U6', -8.0, 0.0, 0.0), ('U7', 8.0, 0.0, 0.0), ('U25', 28.0, -26.0, 0.0), ('L200', 40.0, -26.0, 0.0), ('C275', 36.0, -12.0, 0.0),
    ('L201', -15.0, -24.5, 0.0), ('L202', 0.0, -24.5, 0.0), ('L203', 15.0, -24.5, 0.0),
    ('L204', -15.0, -11.5, 0.0), ('L205', 0.0, -11.5, 0.0), ('L206', 15.0, -11.5, 0.0),
    ('L1', 26.0, -5.0, 0.0), ('L2', 26.0, 6.0, 0.0), ('L3', 33.0, 6.0, 0.0), ('U4', 26.0, 14.0, 0.0), ('U11', 33.0, 14.0, 0.0),
    ('J4', 40.0, 17.0, 0.0), ('J6', 45.5, 17.0, 0.0), ('J8', 36.0, 25.0, 0.0),
]
standin_pcb = []
for ref, u, v, yaw in LAYOUT:
    fp = nl.get(ref, '')
    s = fp_oriented(fp)
    if s is None:
        standin_pcb.append(ref)
        courtyard = {'U4': (5.3, 4.9, 0.9), 'U11': (6.9, 4.9, 1.0)}.get(ref, (5, 5, 1))
        s = box(-courtyard[0] / 2, courtyard[0] / 2, -courtyard[1] / 2, courtyard[1] / 2, 0, courtyard[2])
    s = put(ref, s, u, v, yaw)
    add('PCB_%s' % ref, 'pcb_parts', s, (0.55, 0.55, 0.6))

# connectors with raw-origin placement (pads/edge assumptions documented in README)
j1 = fp_oriented(nl['J1'], ignore_rotz=True)
j1 = tr(j1, V(pcx - 18.0, YF_USB - 5.1, PCB_TOP)); placed['J1'] = j1
add('PCB_J1_USB-C', 'pcb_parts', j1, (0.7, 0.7, 0.75))
for ref, u in (('J2', -2.0), ('J3', 14.0)):
    j = fp_oriented(nl[ref], ignore_rotz=True)
    j = tr(j, V(0, 0, 0), Rot(-90, 0, 0))                    # raw -X (jack bore side) -> +Y (rear)
    j = tr(j, V(pcx + u, YF_JACK - 9.1, PCB_TOP)); placed[ref] = j
    add('PCB_%s_3.5mm_jack' % ref, 'pcb_parts', j, (0.1, 0.1, 0.1))

# parametric stand-ins (no STEP in library): J5 Micro-Fit, J9-J11 JST VH 2-pos, SW100 tact switch
def sbox(ref, u, v, du, dv, dz, label, color):
    s = box(pcx + u - du / 2, pcx + u + du / 2, pcy + v - dv / 2, pcy + v + dv / 2, PCB_TOP, PCB_TOP + dz)
    placed[ref] = s; standin_pcb.append(ref)
    add('PCB_%s_%s' % (ref, label), 'pcb_parts', s, color)
    return s
sbox('J5', 46.0, 3.0, 11.0, 13.66, 9.0, 'MicroFit3_standin', (0.9, 0.9, 0.85))
for ref, v in (('J9', -27.0), ('J10', -17.5), ('J11', -8.0)):
    sbox(ref, -38.0, v, 9.27, 9.5, 10.9, 'JST_B2P-VH_standin', (0.95, 0.95, 0.9))
sbox('SW100', 30.0, 30.0, 4.6, 5.0, 3.5, 'tact_standin', (0.3, 0.3, 0.3))
plunger = cyl(1.25, 159.0 - 156.5 + 0.0, V(pcx + 30.0, 156.5, PCB_TOP + 1.75), V(0, 1, 0))
add('PCB_SW100_plunger', 'pcb_parts', plunger, (0.8, 0.1, 0.1))

# ------------------------------------------------------------------ SW101 rocker (panel mount, stand-in) and speaker-wire/battery harness (schematic)
rx, rz = 66.0, 75.0
rocker = fuse([cyl(9.8, 22.0, V(rx, YB - 19.0 + 0.0, rz), V(0, 1, 0)).cut(Part.makeBox(1, 1, 1)) if False else cyl(9.8, 22.0, V(rx, Dd - 22.0, rz), V(0, 1, 0)),
               cyl(11.5, 1.5, V(rx, Dd, rz), V(0, 1, 0))])
add('SW101_rocker_D20_standin', 'hardware', rocker, (0.6, 0.1, 0.1))
hz = bz
hp = [(pcx + 53.0, pcy + 3.0, PCB_TOP + 4.5), (66.0, pcy + 3.0, PCB_TOP + 4.5), (66.0, pcy + 3.0, hz), (66.0, by, hz), (39.0, by, hz)]
hs = []
for a, b in zip(hp[:-1], hp[1:]):
    d = V(b[0] - a[0], b[1] - a[1], b[2] - a[2]); L = d.Length
    hs.append(cyl(2.0, L, V(*a), d)); hs.append(Part.makeSphere(2.0, V(*b)))
add('Harness_J5_to_pack_schematic', 'battery', fuse(hs), (0.8, 0.5, 0.1))

# ------------------------------------------------------------------ lid with cutouts
lcuts = []
for s in sites:
    if s['kind'] == 'lid':
        lcuts.append(cyl(1.7, t + 2, V(s['p'].x, YB - 1, s['p'].z), V(0, 1, 0)))
bb = j1.BoundBox
lcuts.append(box((bb.XMin + bb.XMax) / 2 - 5.1, (bb.XMin + bb.XMax) / 2 + 5.1, YB - 1, Dd + 1, (bb.ZMin + bb.ZMax) / 2 - 2.5, (bb.ZMin + bb.ZMax) / 2 + 2.5))
for ref in ('J2', 'J3'):
    bb = placed[ref].BoundBox
    lcuts.append(cyl(4.2, t + 2, V((bb.XMin + bb.XMax) / 2, YB - 1, PCB_TOP + 2.5), V(0, 1, 0)))
lcuts.append(cyl(2.5, t + 2, V(pcx + 30.0, YB - 1, PCB_TOP + 1.75), V(0, 1, 0)))
lcuts.append(cyl(10.1, t + 2, V(rx, YB - 1, rz), V(0, 1, 0)))
lid = box(-Wd / 2, Wd / 2, YB, Dd, 0, Hd).cut(fuse(lcuts))
add('Lid_rear', 'lid', lid, (0.35, 0.37, 0.42))

# ------------------------------------------------------------------ perforated grilles (0.8 mm, 2.0 mm holes, 3.0 mm staggered pitch)
def hexholes(cx, cz, r, plane):
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
    for a, b in hexholes(sx * dcx, dzc, 28.0, 'front'):
        tools.append(cyl(P['hole_d'] / 2, P['grille_t'] + 2, V(a, -P['grille_t'] - 1, b), V(0, 1, 0)))
fg = box(-Wd / 2, Wd / 2, -P['grille_t'], 0, 0, Hd).cut(Part.makeCompound(tools))
add('Grille_front_perforated', 'grille', fg, (0.1, 0.1, 0.1))
tools = []
for a, b in hexholes(wcx, wcy, 32.0, 'bottom'):
    tools.append(cyl(P['hole_d'] / 2, P['grille_t'] + 2, V(a, b, -P['grille_t'] - 1)))
wg = cyl(45.0, P['grille_t'], V(wcx, wcy, -P['grille_t'])).cut(Part.makeCompound(tools))
add('Grille_woofer_dia90', 'grille', wg, (0.1, 0.1, 0.1))

# ------------------------------------------------------------------ fasteners: inserts, screws, standoffs, feet
for s in sites:
    p, ax = s['p'], s['axis']
    if s['kind'] != 'foot':
        ins = cyl(P['ins_od'] / 2, P['ins_l'], p, ax).cut(cyl(P['ins_id'] / 2, P['ins_l'] + 2, p - ax * 1, ax))
        add('Insert_M3x5.7_' + s['name'], 'hardware', ins, (0.85, 0.65, 0.2))
        hu = p - ax * s['head_off']                    # head underside
        head = cyl(2.75, 3.0, hu, ax * -1)
        shank = cyl(1.5, 10.0, hu, ax)
        scr = head.fuse(shank).removeSplitter()
        add('Screw_M3x10_' + s['name'], 'hardware', scr, (0.55, 0.55, 0.6))
    else:
        ins = cyl(P['ins_od'] / 2, P['ins_l'], p, ax).cut(cyl(P['ins_id'] / 2, P['ins_l'] + 2, p - ax * 1, ax))
        add('Insert_M3x5.7_' + s['name'], 'hardware', ins, (0.85, 0.65, 0.2))
        body = hexprism(5.5, 12.0, V(p.x, p.y, -12.0)).fuse(cyl(1.5, 6.0, p, ax)).removeSplitter()
        add('Foot_standoff_Wurth1768061_' + s['name'], 'hardware', body, (0.75, 0.75, 0.78))
        add('Foot_rubber_disc_' + s['name'], 'hardware', cyl(6.0, 3.0, V(p.x, p.y, -15.0)), (0.05, 0.05, 0.05))
    if s['kind'] == 'pcb':
        so = hexprism(5.5, P['standoff'], V(p.x, p.y, p.z)).cut(cyl(1.5, P['standoff'] + 2, V(p.x, p.y, p.z - 1)))
        add('Standoff_M3_5mm_' + s['name'], 'hardware', so, (0.75, 0.75, 0.78))

# ------------------------------------------------------------------ document, export
doc = App.newDocument('DesktopSpeaker_internal')
feats = []
for name, group, shape, color in objs:
    o = doc.addObject('Part::Feature', re.sub(r'[^A-Za-z0-9_]', '_', name))
    o.Label = name
    o.Shape = shape
    feats.append(o)
doc.recompute()
doc.saveAs(CAD + 'DesktopSpeaker_internal.FCStd')
try:
    import Import
    Import.export(feats, CAD + 'DesktopSpeaker_internal.step')
except Exception as e:
    print('STEP export via Import failed', e)
    Part.export(feats, CAD + 'DesktopSpeaker_internal.step')

# dump for the render / check scripts
meta = []
for name, group, shape, color in objs:
    fn = re.sub(r'[^A-Za-z0-9_.-]', '_', name) + '.brep'
    shape.exportBrep(WORK + 'brep/' + fn)
    meta.append(dict(name=name, group=group, color=color, file=fn, vol=shape.Volume))
json.dump(dict(objs=meta, params={k: v for k, v in P.items()}, standins=standin_pcb,
               pcb=dict(top=PCB_TOP, bot=PCB_BOT, cx=pcx, cy=pcy), sites=[dict(name=s['name'], kind=s['kind']) for s in sites]),
          open(WORK + 'meta.json', 'w'), indent=1)
print('BUILD OK objects=%d standins=%s' % (len(objs), standin_pcb))
