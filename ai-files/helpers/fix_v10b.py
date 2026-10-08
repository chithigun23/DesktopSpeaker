# -*- coding: utf-8 -*-
"""Placement v10b: local fixes from ai-files/reports/pcb-placement-v10-review.md (B1-B3, M1-M8, minors) applied to the v10b base board
(build_pcb_v10b.py output: v10 generator + PD/AO3V cell moves + H9 + silk border). Run in the KiCad python (build_pcb_v10b.sh does this):
    fix_v10b.py base.kicad_pcb out.kicad_pcb
Every move is a target position/rotation in board mm (KiCad sheet frame, y down). place() keeps the target when it is legal, otherwise takes the
nearest legal spot within r (courtyard + pad union clear of all other top-side parts, of the keep-out bands and of the board edge).
Placeholders (CPH*, TPG*) are NOT in the schematic: they reserve spots for the schematic gaps listed in pcb-placement-v10.md and the review.
Writes out.kicad_pcb, layout-v10b.json (CAD export updated for moved parts and new holes) and fix-v10b.log (moves, displacements)."""
import sys, os, json, math
import pcbnew

SRC, DST = sys.argv[1], sys.argv[2]
W = os.path.dirname(DST) + '/'
ROOT = '/home/chithi/Desktop/DesktopSpeaker/'
FPLIB = ROOT + 'DesktopSpeaker-kicad/kicad-library/footprint'
MM = 1e6
b = pcbnew.LoadBoard(SRC)
FP = {f.GetReference(): f for f in b.GetFootprints()}
eb = b.GetBoardEdgesBoundingBox()
EDGE = (eb.GetX() / MM, eb.GetY() / MM, eb.GetRight() / MM, eb.GetBottom() / MM)
LOG = []
MOVED = set()


def log(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s)


def net(name):
    for n, ni in b.GetNetsByName().items():
        n = str(n)
        if n == name or n.endswith('/' + name):
            return ni
    raise KeyError(name)


def V(x, y):
    return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))


def rect_of(f):
    try:
        f.BuildCourtyardCaches()
    except Exception:
        pass
    cy = f.GetCourtyard(pcbnew.F_CrtYd)
    r = None
    if cy.OutlineCount():
        bb = cy.BBox()
        r = [bb.GetX() / MM, bb.GetY() / MM, bb.GetRight() / MM, bb.GetBottom() / MM]
    for p in f.Pads():
        pb = p.GetBoundingBox()
        q = [pb.GetX() / MM, pb.GetY() / MM, pb.GetRight() / MM, pb.GetBottom() / MM]
        r = q if r is None else [min(r[0], q[0]), min(r[1], q[1]), max(r[2], q[2]), max(r[3], q[3])]
    return tuple(r) if r else None


def top(f):
    return f.GetLayer() == pcbnew.F_Cu and f.GetReference() != 'LOGO1'


RECT = {r: rect_of(f) for r, f in FP.items() if top(f)}
# every part this script moves is lifted first, so a target is only checked against parts that stay or are already re-placed
LIFT = """L1 C112 C108 C101 C104 C105 C107 C100 C103 C106 R102 C110 R108 R100 C111 C272 C274 C283 C284 C278 C287 R257 C296 C297 C291 C300 R258
C280 C282 C271 R261 C295 C301 C298 C2 R10 R11 R13 R17 C120 C126 C123 C214 C212 C215 Y200 C226 C227 C275 C270 C290 C277 C292 C279 R256 R253 R254
C269 R251 R250 C268 C262 C261 C264 R152 L3 C152 C153 C190 R150 C154 C142 C222 C238 C160 C161 C162 R173 TP13 TP12 TP14 TP10""".split()
for _r in LIFT:
    RECT.pop(_r, None)


def inter(a, c, g=0.0):
    return a[0] < c[2] + g and a[2] > c[0] - g and a[1] < c[3] + g and a[3] > c[1] - g


# keep-out bands (board mm): no courtyard of a placed/moved part may enter them
KEEP = {
    'U6 top escape band (B3)': (107.05, 123.3, 112.45, 126.26),
    'U7 top escape band (B3)': (189.85, 123.3, 195.25, 126.26),
    'U4 SW1/SW2 + PGND via channel (B1)': (149.3, 113.4, 153.85, 118.5),
    'U11 bottom escape band (M8)': (133.9, 58.3, 140.95, 59.6),
    'U3 left escape band (M8)': (178.95, 83.6, 179.95, 91.6),
}


def legal(ref, rc, gap=0.03, keep=True):
    if rc[0] < EDGE[0] + 0.5 or rc[2] > EDGE[2] - 0.5 or rc[1] < EDGE[1] + 0.5 or rc[3] > EDGE[3] - 0.5:
        return False
    for o, q in RECT.items():
        if o != ref and q and inter(rc, q, gap):
            return False
    if keep:
        for k in KEEP.values():
            if inter(rc, k):
                return False
    return True


def setpos(f, x, y, rot):
    f.SetOrientationDegrees(rot)
    f.SetPosition(V(x, y))


def place(ref, x, y, rot, r=1.5, keep=True, fab=True):
    """move ref to (x, y, rot) or the nearest legal spot within r (0.05 mm grid rings)"""
    f = FP[ref]
    x0, y0 = f.GetPosition().x / MM, f.GetPosition().y / MM
    setpos(f, 0.0, 0.0, rot)
    r0 = rect_of(f)
    best = None
    n = int(round(r / 0.05))
    for ring in range(0, n + 1):
        if ring == 0:
            cand = [(0, 0)]
        else:
            cand = [(i, s * ring) for i in range(-ring, ring + 1) for s in (-1, 1)] + [(s * ring, j) for j in range(-ring + 1, ring) for s in (-1, 1)]
        for i, j in cand:
            dx, dy = i * 0.05, j * 0.05
            rc = (r0[0] + x + dx, r0[1] + y + dy, r0[2] + x + dx, r0[3] + y + dy)
            if legal(ref, rc, keep=keep):
                d = math.hypot(dx, dy)
                if best is None or d < best[0]:
                    best = (d, x + dx, y + dy)
        if best is not None and best[0] <= ring * 0.05:
            break
    if best is None:
        setpos(f, x, y, rot)
        RECT[ref] = rect_of(f)
        hits = [o for o, q in RECT.items() if o != ref and q and inter(RECT[ref], q, 0.0)]
        log('WARN %s: no legal spot within %.2f mm of (%.2f, %.2f); placed at target, overlaps %s' % (ref, r, x, y, hits))
    else:
        setpos(f, best[1], best[2], rot)
        RECT[ref] = rect_of(f)
        log('move %-6s (%.2f, %.2f) -> (%.2f, %.2f) rot %d%s' % (ref, x0, y0, best[1], best[2], rot, '' if best[0] < 1e-6 else '  [nudged %.2f from target]' % best[0]))
    MOVED.add(ref)
    if fab and ref[0] in 'RCLYD' and not ref.startswith('CPH'):
        f.Reference().SetLayer(pcbnew.F_Fab)
        f.Reference().SetVisible(False)
    return f


def shift(ref, dx, dy, r=1.0):
    f = FP[ref]
    return place(ref, f.GetPosition().x / MM + dx, f.GetPosition().y / MM + dy, f.GetOrientationDegrees(), r)


def pin(ref, num):
    for p in FP[ref].Pads():
        if p.GetNumber() == num:
            return p.GetPosition().x / MM, p.GetPosition().y / MM
    raise KeyError((ref, num))


def add_fp(ref, fpname, value, nets, x, y, rot, r=1.0, note='PLACEHOLDER: not in the schematic'):
    f = pcbnew.FootprintLoad(FPLIB, fpname)
    f.SetReference(ref)
    f.SetValue(value)
    f.SetFPID(pcbnew.LIB_ID('DesktopSpeaker', fpname))
    for p in f.Pads():
        if p.GetNumber() in nets:
            p.SetNet(net(nets[p.GetNumber()]))
    b.Add(f)
    FP[ref] = f
    f.Reference().SetLayer(pcbnew.F_Fab)
    f.Reference().SetTextSize(pcbnew.VECTOR2I(int(0.4 * MM), int(0.4 * MM)))
    f.Reference().SetTextThickness(int(0.06 * MM))
    f.Reference().SetVisible(True)
    f.Value().SetLayer(pcbnew.F_Fab)
    f.Value().SetVisible(False)
    f.SetField('Note', note)
    fld = [q for q in f.GetFields() if q.GetName() == 'Note'][0]
    fld.SetLayer(pcbnew.F_Fab)
    fld.SetVisible(False)
    setpos(f, x, y, rot)
    RECT[ref] = rect_of(f)
    place(ref, x, y, rot, r, fab=False)
    log('  new %s %s %s nets %s' % (ref, fpname, value, nets))
    return f


VIAS = []


def via(x, y, netname, why):
    if os.environ.get('NOVIA'):
        return
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(V(x, y))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetDrill(int(0.3 * MM))
    try:
        v.SetWidth(int(0.6 * MM))
    except TypeError:
        v.SetWidth(pcbnew.F_Cu, int(0.6 * MM))
    b.Add(v)
    v.SetNetCode(net(netname).GetNetCode())
    VIAS.append((round(x, 2), round(y, 2), netname, why))


def tp_move(ref, x, y, rot=None, r=3.0, side=None):
    """move a test point together with its net-name label (front silk text next to it)"""
    f = FP[ref]
    x0, y0 = f.GetPosition().x / MM, f.GetPosition().y / MM
    lab = None
    for d in b.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == f.GetValue() and d.GetLayer() == pcbnew.F_SilkS:
            q = d.GetPosition()
            dd = math.hypot(q.x / MM - x0, q.y / MM - y0)
            if dd < 7.0 and (lab is None or dd < lab[0]):
                lab = (dd, d)
    place(ref, x, y, f.GetOrientationDegrees() if rot is None else rot, r, fab=False)
    dx, dy = f.GetPosition().x / MM - x0, f.GetPosition().y / MM - y0
    if lab and side:
        b.Remove(lab[1])
        tp_label(f, f.GetValue(), side)
    elif lab:
        lab[1].Move(V(dx, dy))


def tp_label(f, text, side='R'):
    rc = rect_of(f)
    t = pcbnew.PCB_TEXT(b)
    t.SetText(text)
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(int(0.7 * MM), int(0.7 * MM)))
    t.SetTextThickness(int(0.1 * MM))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT if side == 'R' else pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    t.SetPosition(V(rc[2] + 0.25 if side == 'R' else rc[0] - 0.25, (rc[1] + rc[3]) / 2))
    b.Add(t)


def text_move(txt, near, to):
    for d in b.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == txt and math.hypot(d.GetPosition().x / MM - near[0], d.GetPosition().y / MM - near[1]) < 2.0:
            d.SetPosition(V(*to))
            return
    log('WARN text %s not found near %s' % (txt, near))


def ref_to(ref, x, y):
    FP[ref].Reference().SetPosition(V(x, y))


# =====================================================================================================================================
# B1 / B2: U4 BQ25792 ring. PMID row 1.4 mm left, SYS row 1.4 mm right, both rows and L1 up 1.0 mm -> 5.3 mm copper channel for
# SW1 | PGND via column (pin 27) | SW2. 0.1 uF placeholders between the rows and the pins; C103/C110 next to BTST1/BTST2 with SW via pairs.
# C106 vertical, BAT pad at pins 22/23; CHG_INT/PROG escape under C106, BTST2 down to C110, BATP via, ILIM/TS down to R108/R100.
# =====================================================================================================================================
place('L1', 151.57, 110.03, 0, 0.6, keep=False)
for ref, x in (('C112', 143.42), ('C108', 145.82), ('C101', 148.22), ('C104', 154.92), ('C105', 157.32), ('C107', 159.72)):
    place(ref, x, 116.53, 90, 0.3, keep=False)
place('C100', 146.15, 120.07, 180, 0.3)
place('C103', 147.90, 121.60, 180, 0.3)
add_fp('CPH2', 'C_0402_1005Metric_Pad0.74x0.62mm_HandSolder', '100nF PH (U4 PMID HF)', {'1': 'PMID', '2': 'GND'}, 149.30, 119.07, 180, 0.3)
add_fp('CPH1', 'C_0402_1005Metric_Pad0.74x0.62mm_HandSolder', '100nF PH (U4 SYS HF)', {'1': 'SYS_RAW', '2': 'GND'}, 153.84, 119.07, 0, 0.3)
place('C106', 156.80, 121.90, 270, 0.4)
place('R102', 159.10, 122.00, 0, 0.6)
place('C110', 155.75, 125.00, 270, 0.4)
place('R108', 154.67, 126.78, 90, 0.4)
place('R100', 153.37, 129.08, 0, 0.4)
place('C111', 149.57, 128.03, 270, 0.4)
add_fp('CPH3', 'C_0402_1005Metric_Pad0.74x0.62mm_HandSolder', '100nF PH (U4 VBUS HF)', {'1': 'VBUS_PD', '2': 'GND'}, 150.15, 125.30, 0, 0.3)
for y in (116.6, 117.5, 118.4):
    via(151.57, y, 'GND', 'U4 pin 27 PGND via column (B1)')
for ref in ('C112', 'C108', 'C101', 'C104', 'C105', 'C107'):
    x = FP[ref].GetPosition().x / MM
    for dx in (-0.4, 0.4):
        via(x + dx, 114.3, 'GND', '%s GND pad, 2 vias to In1 (B1)' % ref)
via(143.85, 119.60, 'GND', 'C100 GND pad (B1)'); via(143.85, 120.55, 'GND', 'C100 GND pad (B1)')
via(149.10, 130.10, 'GND', 'C111 GND pad (B1)'); via(150.05, 130.10, 'GND', 'C111 GND pad (B1)')
via(158.10, 123.20, 'GND', 'C106 GND pad'); via(158.10, 124.05, 'GND', 'C106 GND pad')
via(157.90, 120.40, 'BAT_INT', 'C106 BAT pad to the In2 BAT_INT pour (B2 layer plan)'); via(158.70, 120.40, 'BAT_INT', 'C106 BAT pad to In2 (B2)')
via(146.45, 121.75, 'SW1', 'C103 SW1 pad via pair (B2)'); via(150.10, 115.20, 'SW1', 'C103 SW1 via pair, channel end (B2)')
via(156.55, 125.57, 'SW2', 'C110 SW2 pad via pair (B2)'); via(153.00, 115.20, 'SW2', 'C110 SW2 via pair, channel end (B2)')
via(155.00, 123.00, 'Net-(U4-BATP)', 'BATP escape via (pin 18 -> R112 on an inner/bottom layer)')

# =====================================================================================================================================
# B3: U6 / U7 top pin row (9-16) clear to 3 mm. Left side re-stacked so PDN, GVDD and AVDD escape without crossings:
# PDN goes up beside the pins to R257/R258, GVDD/AVDD caps horizontal in line with pins 18/19, PVDD 0.1 uF horizontal in line with pins 21/22
# (PVDD pad 0.35 mm from the pin tips, GND pad via to In1), BST_B cap below the OUT_B+ corridor. Right side: VR_DIG cap below DVDD 100 nF row,
# DVDD 4.7 uF and the PVDD 22 uF above it, outside the band.
# =====================================================================================================================================
for dx, ic in ((0.0, 'U6'), (82.79, 'U7')):
    L = dict(U6=dict(bulk='C272', gv='C283', av='C284', hf='C278', bst='C287', pdn='R257'),
             U7=dict(bulk='C274', gv='C296', av='C297', hf='C291', bst='C300', pdn='R258'))[ic]
    if ic == 'U6':
        place('C272', 103.50, 124.20, 90, 0.3)
    else:
        place('C274', 184.44, 128.75, 180, 0.3)
    place(L['gv'], 104.90 + dx, 127.25, 180, 0.2)
    place(L['av'], 104.90 + dx, 128.30, 180, 0.2)
    place(L['hf'], 105.75 + dx, 129.31, 180, 0.2)
    place(L['bst'], 104.00 + dx, 132.25, 180, 0.4)
    place(L['pdn'], 106.70 + dx, 121.80 if ic == 'U6' else 122.30, 270, 0.4)
    for y in (127.25, 128.30):
        via(103.30 + dx, y, 'GND', '%s GVDD/AVDD cap GND pad' % ic)
    via(104.20 + dx, 129.35, 'GND', '%s PVDD 0.1 uF GND pad to In1' % ic)
    if ic == 'U6':
        via(103.40, 129.35, 'GND', 'U6 PVDD 0.1 uF GND pad to In1')
# U6 right
place('C280', 114.06, 122.20, 90, 0.3)
place('C282', 114.06, 125.25, 0, 0.3)
place('C271', 116.15, 122.60, 90, 0.3)
# U7 right + bottom BST caps (PBTL)
place('R261', 196.86, 124.00, 180, 0.4)
place('C295', 196.86, 125.25, 0, 0.3)
place('C301', 191.95, 132.80, 90, 0.3)
place('C298', 192.95, 132.80, 270, 0.3)

# =====================================================================================================================================
# M1 / M8: PD cell (moved by the generator under J1). C2 to the top-right (pins 32/23), PPHV 47 uF placeholder at the pin-20 exit,
# U11 bottom resistors 1.5 mm below the pin row, U19 input cap placeholder.
# =====================================================================================================================================
place('C2', 142.30, 53.40, 90, 0.6)
for ref in ('R10', 'R11', 'R13', 'R17'):
    shift(ref, 0.0, 1.2, 0.6)
add_fp('CPH5', 'PD_C_1206', '47uF PH (U11 PPHV, CPPHV)', {'1': 'VBUS_PD', '2': 'GND'}, 143.20, 59.00, 90, 1.5)
x8, y8 = pin('U19', '8')
add_fp('CPH6', 'C_0402_1005Metric_Pad0.74x0.62mm_HandSolder', '1uF PH (U19 USB_VBUS input)', {'1': 'USB_VBUS', '2': 'GND'}, x8 + 1.25, y8 + 0.57, 270, 1.0)

# =====================================================================================================================================
# M2 gauge / supervisor bypass at the ICs; M3 3V_AO output cap on U12 pin 5 (U12/C122 moved by the generator)
# =====================================================================================================================================
place('C120', 100.60, 90.75, 0, 0.6)
place('C126', 102.60, 81.70, 90, 0.6)
x5, y5 = pin('U12', '5')
place('C123', x5 + 0.57 + 0.1, y5 - 1.45, 0, 0.8)

# =====================================================================================================================================
# M4 U24: VREF/AVDD 0402s on pins 6/8, crystal to the left with its load caps, LDO cap moved 0.6 mm left
# =====================================================================================================================================
place('C214', 145.40, 76.95, 90, 0.3)
place('C212', 152.15, 80.35, 90, 0.3)
place('C215', 151.05, 80.35, 90, 0.3)
place('Y200', 148.60, 77.20, 0, 0.6)
place('C226', 147.60, 79.75, 180, 0.6)
place('C227', 149.90, 74.60, 0, 0.6)

# =====================================================================================================================================
# M5 U25: 0.1 uF placeholder at pins 14-16, C270 1 uF next, 2x2 22 uF block (C290/C277/C292 + C279 beside), FB/COMP/ILIM column top-right,
# MODE resistor at pin 13, C275 bulk lower right (>= 12 mm from U25), m7: one SYS 22 uF at the L200 input pad
# =====================================================================================================================================
place('C275', 166.70, 152.10, 0, 0.8, keep=False)
add_fp('CPH4', 'C_0402_1005Metric_Pad0.74x0.62mm_HandSolder', '100nF PH (U25 VOUT HF)', {'1': 'PVDD_AMP', '2': 'GND'}, 156.05, 147.65, 270, 0.3)
place('C270', 157.63, 148.95, 270, 0.3)
place('C290', 159.72, 148.95, 270, 0.3)
place('C277', 157.63, 152.95, 90, 0.4)
place('C292', 159.72, 152.95, 90, 0.4)
place('C279', 161.96, 145.70, 270, 0.4)
place('C261', 154.46, 152.54, 0, 0.2)
place('C264', 154.46, 154.94, 0, 0.2)
place('R256', 156.05, 150.35, 270, 0.3)       # MODE 0R at pin 13; CPH4 GND reaches the C270 GND pad between C270 PVDD and R256
for ref, x, rot in (('R253', 155.95, 90), ('R254', 157.05, 90), ('C269', 158.15, 90), ('R251', 159.25, 90), ('R250', 160.35, 270)):
    place(ref, x, 142.90, rot, 0.3)
place('C268', 157.05, 140.60, 90, 0.4)
place('C262', 142.80, 153.00, 270, 0.6)

# =====================================================================================================================================
# M6 U15 / U14: output caps at VOUT pin 6, L3 up 1 mm, FB divider left, C154 at the U1 pin 23 end; U14 C142 next to C141
# =====================================================================================================================================
place('R152', 119.37, 32.96, 90, 0.3)
place('L3', 122.31, 36.06, 0, 0.3, keep=False)
place('C152', 117.55, 40.40, 270, 0.3)
place('C153', 119.65, 40.40, 270, 0.3)
place('C190', 115.45, 40.40, 270, 0.3)
place('R150', 113.25, 40.05, 0, 0.6)
place('C154', 113.41, 42.96, 90, 1.0)
via(117.55, 42.40, 'GND', 'C152 GND pad'); via(119.65, 42.40, 'GND', 'C153 GND pad')
place('C142', 97.90, 105.20, 0, 1.5)

# =====================================================================================================================================
# M7: U22 output cap on pin 5; U8 V+ cap (C238 from U10) and a placeholder for U9 V+ (schematic has 2 x 0.1 uF for 3 needs)
# =====================================================================================================================================
x5, y5 = pin('U22', '5')
place('C222', x5 + 1.45, y5 + 0.4, 270, 1.0)
x8, y8 = pin('U8', '8')
place('C238', x8, y8 - 2.35, 90, 2.5)
x8, y8 = pin('U9', '8')
add_fp('CPH7', 'C_0402_1005Metric_Pad0.74x0.62mm_HandSolder', '100nF PH (U9 V+)', {'1': '3V3_AUDIO', '2': 'GND'}, x8, y8 - 2.35, 90, 1.0)

# =====================================================================================================================================
# M8 U3: decoupling 1 mm further from the left pin row
# =====================================================================================================================================
shift('C160', -0.34, 0.0, 0.3)          # R106 sits 1 mm further left: 0.34 mm keeps C160 >= 1.2 mm from the pin tips
for ref in ('C161', 'C162'):
    shift(ref, -1.0, 0.0, 0.5)

# =====================================================================================================================================
# minors: m1 D+ pull-up next to R171; m2 I2S test points in line below R206-R208, GND test loops at the ADC/charger and the boost,
# TP10 clear of the HA1 screw head
# =====================================================================================================================================
x, y = pin('R171', '1')
place('R173', x, y - 1.75, 90, 1.5)
tp_move('TP13', 147.0, 95.5, 0, 1.0, 'L')         # I2S test points in a column under the source resistors, labels on the left (H2 on the right)
tp_move('TP12', 147.0, 98.5, 0, 1.0, 'L')
tp_move('TP14', 147.0, 101.5, 0, 1.0, 'L')
for ref, (x, y) in (('TPG1', (141.0, 91.6)), ('TPG2', (146.0, 132.0))):
    f = add_fp(ref, 'TestPoint_Keystone_5015_Micro_Mini', 'GND', {'1': 'GND'}, x, y, 0, 4.0, note='PLACEHOLDER: GND test loop, not in the schematic')
    tp_label(f, 'GND')
tp_move('TP10', FP['TP10'].GetPosition().x / MM, FP['TP10'].GetPosition().y / MM + 2.25, None, 1.0)
# reference / label texts displaced by the moves (silk over pads)
ref_to('U7', 189.6, 132.6)
ref_to('U4', 151.57, 122.19)          # inside the body outline (no centre pad on U4)
ref_to('U5', 100.11, 92.05)
ref_to('U15', 121.75, 40.45)
text_move('BAT_PACK', (103.5, 90.8), (103.55, 84.45))

# =====================================================================================================================================
# checks and outputs
# =====================================================================================================================================
bad = []
refs = [r for r in RECT if RECT[r]]
for i, a in enumerate(refs):
    for c in refs[i + 1:]:
        if (a in MOVED or c in MOVED) and inter(RECT[a], RECT[c]):
            bad.append((a, c))
log('rect overlaps involving moved/new parts:', bad)
for k, q in KEEP.items():
    log('keep-out %s: %s' % (k, [r for r in refs if inter(RECT[r], q) and not r.startswith('U')]))
log('vias added:', len(VIAS))
pcbnew.SaveBoard(DST, b)

# CAD export: base layout json with the moved parts/holes updated (same frame as build_pcb_v10b.py)
LJ = json.load(open(W + 'layout-v10b-base.json'))
B = LJ['board']
X0 = 150.0 - (B['u0'] + B['u1']) / 2
VC = B['v_design_offset']
VR = VC + B['d'] / 2
Y0 = 20.0 + VR if VR < 500 else 100.0
for ref in MOVED:
    if ref in LJ['parts']:
        f = FP[ref]
        x, y = f.GetPosition().x / MM, f.GetPosition().y / MM
        rc = rect_of(f)
        rc = (rc[0] - 0.2, rc[1] - 0.2, rc[2] + 0.2, rc[3] + 0.2)
        u0, u1, v0, v1 = rc[0] - X0, rc[2] - X0, Y0 - rc[3], Y0 - rc[1]
        LJ['parts'][ref] = dict(origin_u=round(x - X0, 3), origin_v=round(Y0 - y - VC, 3), rot=round(f.GetOrientationDegrees()) % 360,
                                cy_u=round((u0 + u1) / 2, 3), cy_v=round((v0 + v1) / 2 - VC, 3), rect=[round(u0, 3), round(v0 - VC, 3), round(u1, 3), round(v1 - VC, 3)])
        log('cad part updated', ref)
json.dump(LJ, open(W + 'layout-v10b.json', 'w'), indent=1)
json.dump(dict(vias=VIAS, moved=sorted(MOVED)), open(W + 'fix-v10b.json', 'w'), indent=1)
open(W + 'fix-v10b.log', 'w').write('\n'.join(LOG) + '\n')
print('saved', DST)
