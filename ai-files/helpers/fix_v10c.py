# -*- coding: utf-8 -*-
"""Placement v10c: local fixes applied to the v10c base board (build_pcb_v10c.py output: v10 generator + PD/AO3V cell moves + H9 + silk border,
schematic parts C311-C316/TP26/TP27 on reserved spots). Two layers of fixes:
  - v10b: ai-files/reports/pcb-placement-v10-review.md (B1-B3, M1-M8, minors), as in fix_v10b.py, with the placeholders replaced by the real parts
    (CPH1->C311, CPH2->C312, CPH3->C313, CPH4->C314, CPH5->C315, CPH6->C316, TPG1->TP26, TPG2->TP27; CPH7 dropped, C237 moved to U9 V+);
  - v10c: ai-files/reports/pcb-placement-v10b-review.md (B1-B3, M1-M5, minors m1/m3-m6), marked "v10c".
Run in the KiCad python (build_pcb_v10c.sh does this):
    fix_v10c.py base.kicad_pcb out.kicad_pcb
Every move is a target position/rotation in board mm (KiCad sheet frame, y down). place() keeps the target when it is legal, otherwise takes the
nearest legal spot within r (courtyard + pad union clear of all other top-side parts, of the keep-out bands and of the board edge).
Writes out.kicad_pcb, layout-v10c.json (CAD export updated for moved parts and new holes), fix-v10c.json (vias) and fix-v10c.log (moves, displacements)."""
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
C269 R251 R250 C268 C262 C261 C264 R152 L3 C152 C153 C190 R150 C154 C142 C222 C238 C160 C161 C162 R173 TP13 TP12 TP14 TP10
C311 C312 C313 C314 C315 C316 TP26 TP27
C299 C285 C276 C289 C293 C183 C182 C184 R12 R18 C216 C207 C206 C209 C208 R201 R200 R203 R202 C201 C203 C202 R223 C233
R226 C230 C237 R106 C140 R211""".split()   # v10c: 2nd/3rd lines = real parts of the v10b placeholders, parts moved for pcb-placement-v10b-review.md
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
    if fab and ref[0] in 'RCLYD':
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
place('C312', 149.30, 119.07, 180, 0.3)      # 0.1 uF PMID HF (v10b placeholder CPH2)
place('C311', 153.84, 119.07, 0, 0.3)        # 0.1 uF SYS HF (CPH1)
place('C106', 156.80, 121.90, 270, 0.4)
place('R102', 159.10, 122.00, 0, 0.6)
place('C110', 155.75, 125.00, 270, 0.4)
place('R108', 154.67, 126.78, 90, 0.4)
place('R100', 153.37, 129.08, 0, 0.4)
place('C111', 149.57, 128.03, 270, 0.4)
place('C313', 150.15, 125.30, 0, 0.3)        # 0.1 uF VBUS HF (CPH3)
for y in (116.6, 117.5, 118.4):
    via(151.57, y, 'GND', 'U4 pin 27 PGND via column (B1)')
for ref in ('C112', 'C108', 'C101', 'C104', 'C105', 'C107'):
    x = FP[ref].GetPosition().x / MM
    for dx in (-0.4, 0.4):
        via(x + dx, 114.3, 'GND', '%s GND pad, 2 vias to In1 (B1)' % ref)
via(143.85, 119.60, 'GND', 'C100 GND pad (B1)'); via(143.85, 120.55, 'GND', 'C100 GND pad (B1)')
via(149.10, 130.10, 'GND', 'C111 GND pad (B1)'); via(150.05, 130.10, 'GND', 'C111 GND pad (B1)')
via(158.10, 123.20, 'GND', 'C106 GND pad'); via(158.10, 124.05, 'GND', 'C106 GND pad')
# v10c M2: BAT_INT (5-8 A) gets an 8-via field at the C106 BAT pad (was 2) and a 9-via field at Q103 pins 1-3 (below)
for x in (157.90, 158.70, 159.50, 160.30):
    for y in (120.25, 121.05):
        via(x, y, 'BAT_INT', 'C106 BAT pad / U4 pins 22-23 to the In2 BAT_INT pour, 8-via field (v10c M2)')
via(146.45, 121.75, 'SW1', 'C103 SW1 pad via pair (B2)'); via(150.10, 115.20, 'SW1', 'C103 SW1 via pair, channel end (B2)')
via(156.55, 125.57, 'SW2', 'C110 SW2 pad via pair (B2)'); via(153.00, 115.20, 'SW2', 'C110 SW2 via pair, channel end (B2)')
via(155.10, 123.35, 'Net-(U4-BATP)', 'BATP escape via (pin 18 -> R112 on an inner/bottom layer); v10c M3: 0.35 mm down so BTST2 passes over it')

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
    via(104.20 + dx, 129.35 if ic == 'U6' else 128.95, 'GND', '%s PVDD 0.1 uF GND pad to In1 (U7: v10c m3, 0.4 mm up to widen OUT_B+)' % ic)
    if ic == 'U6':
        via(102.60, 128.85, 'GND', 'U6 PVDD 0.1 uF GND pad to In1 (v10c m3: outer via up/left, OUT_B+ neck wider)')
# U6 right
place('C280', 114.06, 122.20, 90, 0.3)
place('C282', 114.06, 125.25, 0, 0.3)
place('C271', 116.15, 122.60, 90, 0.3)
# U7 right + bottom BST caps (PBTL)
place('R261', 196.86, 124.00, 180, 0.4)
place('C295', 196.86, 125.25, 0, 0.3)
# v10c B1: U7 PBTL bottom row = U6 stack (C286/C288): C299 at 1.45 mm under pins 29/30, C301 below it, C298 in the bottom-right OUT_A+ corner
place('C299', 192.60, 133.31, 180, 0.2)       # OUT_A+ pad 193.17 under pin 30, BST_A- pad 192.03
place('C301', 192.50, 134.61, 0, 0.2)         # OUT_B+ pad 191.93, BST_B- pad 193.07 (reached through the slot, as C288 on U6)
place('C298', 196.00, 132.00, 0, 0.3)         # BST_A+ pad 195.43 near pin 1, OUT_A+ pad 196.57 toward the trunk

# =====================================================================================================================================
# M1 / M8: PD cell (moved by the generator under J1). C2 to the top-right (pins 32/23), PPHV 47 uF placeholder at the pin-20 exit,
# U11 bottom resistors 1.5 mm below the pin row, U19 input cap placeholder.
# =====================================================================================================================================
place('C2', 142.30, 53.40, 90, 0.6)
for ref in ('R10', 'R11', 'R13', 'R17'):
    shift(ref, 0.0, 1.2, 0.6)
place('C315', 143.20, 59.00, 270, 1.5)       # 47 uF PPHV (CPH5); v10c M2: r270, VBUS pad up toward pin 20, GND pad away from it
x8, y8 = pin('U19', '8')
place('C316', x8 + 1.62, y8 + 1.04, 270, 1.0)   # 1 uF 0805 U19 input (CPH6 was 0402): VBUS pad in line with pin 8, courtyard clear of U19

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
place('C212', 152.10, 80.35, 90, 0.3)           # v10c: 0.05 mm left (pin-4 riser clearance)
place('C215', 151.05, 80.35, 90, 0.3)
place('Y200', 148.60, 77.20, 0, 0.6)
place('C226', 147.60, 79.75, 180, 0.6)
place('C227', 149.90, 74.60, 0, 0.6)

# =====================================================================================================================================
# M5 U25: 0.1 uF placeholder at pins 14-16, C270 1 uF next, 2x2 22 uF block (C290/C277/C292 + C279 beside), FB/COMP/ILIM column top-right,
# MODE resistor at pin 13, C275 bulk lower right (>= 12 mm from U25), m7: one SYS 22 uF at the L200 input pad
# =====================================================================================================================================
place('C275', 166.70, 152.10, 0, 0.8, keep=False)
place('C314', 156.05, 147.65, 270, 0.3)      # 0.1 uF VOUT HF (CPH4)
place('C270', 157.63, 148.95, 270, 0.3)
place('C290', 159.72, 148.95, 270, 0.3)
place('C277', 157.63, 152.95, 90, 0.4)
place('C292', 159.72, 152.95, 90, 0.4)
place('C279', 161.96, 145.70, 270, 0.4)
place('C261', 154.46, 152.54, 0, 0.2)
place('C264', 154.46, 154.94, 0, 0.2)
place('R256', 156.05, 150.35, 270, 0.3)       # MODE 0R (DNP) at pin 13; C314 GND reaches the C270 GND pad between C270 PVDD and R256 (v10b review m2: schematic item)
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
place('C238', 173.29, 58.70, 90, 0.5)         # v10c M5: U8 V+ cap ~1 mm up with R226/C230 (v10b spot 173.29, 59.77)
x8, y8 = pin('U9', '8')
place('C237', x8, y8 - 3.35, 90, 1.0)         # v10c: C237 (was at U10) is the U9 V+ cap (CPH7 dropped); M5: 1 mm further up than the v10b spot

# =====================================================================================================================================
# v10c: fixes from ai-files/reports/pcb-placement-v10b-review.md
# =====================================================================================================================================
# B2 U6 right side: PVDD 0.1 uF horizontal under pins 3/4 (GND pad outward, via to In1), BST_A+ cap below the OUT_A+ trunk -> pins 5-8 free
place('C276', 113.75, 129.30, 0, 0.2)          # PVDD pad 113.18 (0.31 mm from the pin tips), GND pad 114.32
via(114.90, 128.40, 'GND', 'C276 GND pad to In1 (v10c B2)')
place('C285', 114.20, 131.20, 0, 0.2)          # BST_A+ pad 113.63 by pin 1, OUT_A+ pad 114.77 below the trunk
# B2 U7 mirror: C289 horizontal, C293 0.9 mm right (courtyard + GND via room)
place('C293', 199.86, 128.45, 0, 0.3)
place('C289', 196.53, 129.30, 0, 0.2)          # PVDD pad 195.96, GND pad 197.10
via(197.69, 128.40, 'GND', 'C289 GND pad to In1 (v10c B2)')

# B3 U11 top row: CC caps vertical in pin order directly above pins 29/28 (CC pad down, GND via up); corner GND pins 26/27 to a via right;
# C184 (USB_VBUS 1 uF) 1.2 mm up with its VBUS pad 0.4 mm right of the review spot (CC2 rises between C184 and C183), USB_VBUS fed by a via;
# R12/R18 in the free area left-up so pins 36-38 go up through the 1.4 mm channel between C6 and C184 in pin order (38 R12, 37 via, 36 R18)
place('C183', 138.40, 52.10, 90, 0.15)          # CC2 pad over pin 29
place('C182', 139.50, 52.10, 90, 0.15)          # CC1 pad over pin 28/27; pin 28 rises at x 139.0 into its left edge
via(138.40, 50.55, 'GND', 'C183 GND pad (v10c B3)'); via(139.50, 50.55, 'GND', 'C182 GND pad (v10c B3)')
via(140.70, 53.45, 'GND', 'U11 corner GND pins 26/27 (v10c B3)')
place('C184', 135.50, 50.90, 180, 0.3)
via(136.55, 49.50, '/USB_VBUS', 'C184 VBUS pad feed from the B.Cu/In2 USB_VBUS copper (v10c B3)')
via(134.45, 49.45, 'GND', 'C184 GND pad (v10c B3)')
place('R12', 132.10, 48.30, 90, 0.4)            # VIN_LOW pull-down, pin 38
place('R18', 133.60, 48.30, 90, 0.4)            # pin 36 resistor
via(131.45, 47.70, 'GND', 'R12 GND pad (v10c B3)'); via(134.25, 47.70, 'GND', 'R18 GND pad (v10c B3)')
via(132.85, 46.60, 'PD_PLUG_EVENT', 'U11 pin 37 PD_PLUG_EVENT to R16/U3 on an inner/bottom layer (v10c B3)')

# M1 U4: VBUS_PD entry vias beside C100 and the CPH3/C111 column; HF-cap GND vias (m1)
for x, y in ((148.45, 120.00), (148.45, 120.70), (148.55, 125.00), (148.25, 127.00)):
    via(x, y, 'VBUS_PD', 'U4 VBUS_PD pins 2/3/8/9 to the In2 VBUS_PD island (v10c M1)')
via(147.85, 118.75, 'GND', 'C312 (PMID 0.1 uF) GND pad (v10c m1)'); via(155.40, 119.10, 'GND', 'C311 (SYS 0.1 uF) GND pad (v10c m1)')

# M2 power via fields (reservations)
for x in (168.00, 168.80, 169.60):
    for y in (109.30, 110.10, 110.90):
        via(x, y, 'BAT_INT', 'Q103 pins 1-3 BAT_INT 9-via field (v10c M2)')
for x, y in ((161.2, 116.4), (162.0, 116.4), (162.8, 116.4), (161.2, 117.2), (162.0, 117.2), (162.8, 117.2), (161.2, 118.0), (162.0, 118.0)):
    via(x, y, 'SYS_RAW', 'SYS_RAW field at C104-C107 to the In2/B.Cu SYS pour (v10c M2)')
for y in (144.2, 145.0, 145.8, 146.6, 147.4, 148.2, 149.0):
    via(140.35, y, 'SYS_RAW', 'SYS_RAW field beside the L200 pad 1 (v10c M2)')
for x in (157.20, 158.00, 158.80, 159.60, 160.40):
    via(x, 155.35, 'PVDD_AMP', 'U25 output block (C277/C292 PVDD pads) to the PVDD pour (v10c M2)')
for y in (151.30, 152.10, 152.90):
    via(161.10, y, 'PVDD_AMP', 'C275 PVDD pad to the PVDD pour (v10c M2)')
via(116.00, 124.85, 'PVDD_AMP', 'C271 PVDD pad (v10c M2)'); via(116.80, 124.85, 'PVDD_AMP', 'C271 PVDD pad (v10c M2)')
via(102.70, 126.30, 'PVDD_AMP', 'C272 PVDD pad (v10c M2)'); via(103.50, 126.30, 'PVDD_AMP', 'C272 PVDD pad (v10c M2)')
via(199.20, 132.30, 'PVDD_AMP', 'C273 PVDD pad (v10c M2)'); via(200.00, 132.30, 'PVDD_AMP', 'C273 PVDD pad (v10c M2)')
for y in (56.50, 57.30, 58.10, 58.90):
    via(144.75, y, 'VBUS_PD', 'C315 VBUS pad / U11 pin 20 to the VBUS_PD trunk (v10c M2)')

# M4 U24: VIN filter re-sorted in pin order. Rows (pitch 1.3 mm) top->bottom pin 4, 3, 2, 1: shunt cap (node pad left) | GND via |
# series R (node pad left, 0.65 mm lower: the 0.25 mm AUDIO node track passes under the GND pad and via at >= 0.2 mm) | coupling cap.
# C216 (AVDD 10 uF) moves above the rows; C212 (VREF) 0.05 mm left so the pin-4 riser keeps 0.2 mm.
place('C216', 156.00, 75.20, 0, 0.6)
for ref, rr, cc, y in (('C207', 'R201', 'C201', 77.05), ('C206', 'R200', None, 78.35), ('C209', 'R203', 'C203', 79.65), ('C208', 'R202', 'C202', 80.95)):
    place(ref, 155.95, y, 0, 0.15)
    via(157.40, y, 'GND', '%s GND pad (v10c M4)' % ref)
    place(rr, 159.00, y + 0.65, 180, 0.15)
    if cc:
        place(cc, 161.30, y + 0.65, 180, 0.6)
place('R223', 162.05, 79.71, 90, 2.5)              # re-placed after the coupling caps (VMID_HP bias of the HP path)
place('C233', 160.75, 82.18, 90, 2.5)

# M5 U8/U9: top-row band of >= 1.6 mm (R226/C230 1 mm up, C238/C237 above), GND vias, audio vias for the crossing nets
place('R226', 172.49, 60.40, 180, 0.3)          # top band 1.64 mm above U8 pins 6-10
place('C230', 171.59, 59.10, 0, 0.3)
via(173.29, 57.25, 'GND', 'C238 GND pad (v10c M5)'); via(184.29, 58.30, 'GND', 'C237 GND pad (v10c M5)')
via(170.50, 61.90, 'Net-(U8-COM1)', 'U8 COM1 (pin 10) to U9 pin 9 on B.Cu (v10c M5)')
via(182.60, 61.85, 'HP_L', 'U9 HP_L (pin 10) to C239 on B.Cu (v10c M5)')
shift('C239', 0.25, -0.4, 0.3)                # HP_L coupling cap 0.25 mm right, 0.4 mm up: room for the COM2 via and the HP_R exit
via(184.95, 61.35, 'Net-(U8-COM2)', 'U9 COM2 (pin 7) from U8 on B.Cu, beside V+ (v10c M5)')

# minors: m4 R106 below C162 (CHG_INT clear of C160), m5 C140 0.5 mm left, m6 R211 right of U24 pin 21 below R209
place('R106', 177.54, 92.90, 90, 1.5)
shift('C140', -0.5, 0.0, 0.3)
place('R211', 150.60, 92.45, 0, 0.6)

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
for ref, (x, y) in (('TP26', (141.0, 90.9)), ('TP27', (146.0, 132.0))):     # GND test points (TPG1/TPG2 in v10b; TP26 0.7 mm up: the 5010 silk circle is larger)
    f = place(ref, x, y, 0, 4.0, fab=False)
    f.Reference().SetLayer(pcbnew.F_Fab)
    tp_label(f, 'GND', 'L' if ref == 'TP26' else 'R')
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
LJ = json.load(open(W + 'layout-v10c-base.json'))
B = LJ['board']
X0 = 150.0 - (B['u0'] + B['u1']) / 2
VC = B['v_design_offset']
VR = VC + B['d'] / 2
Y0 = 20.0 + VR if VR < 500 else 100.0
for ref in MOVED:
    if ref in LJ['parts'] or ref in ('TP26', 'TP27', 'C315'):      # v10c: late schematic parts that the CAD models (test points, 47 uF 1206)
        f = FP[ref]
        x, y = f.GetPosition().x / MM, f.GetPosition().y / MM
        rc = rect_of(f)
        rc = (rc[0] - 0.2, rc[1] - 0.2, rc[2] + 0.2, rc[3] + 0.2)
        u0, u1, v0, v1 = rc[0] - X0, rc[2] - X0, Y0 - rc[3], Y0 - rc[1]
        LJ['parts'][ref] = dict(origin_u=round(x - X0, 3), origin_v=round(Y0 - y - VC, 3), rot=round(f.GetOrientationDegrees()) % 360,
                                cy_u=round((u0 + u1) / 2, 3), cy_v=round((v0 + v1) / 2 - VC, 3), rect=[round(u0, 3), round(v0 - VC, 3), round(u1, 3), round(v1 - VC, 3)])
        log('cad part updated', ref)
json.dump(LJ, open(W + 'layout-v10c.json', 'w'), indent=1)
json.dump(dict(vias=VIAS, moved=sorted(MOVED)), open(W + 'fix-v10c.json', 'w'), indent=1)
open(W + 'fix-v10c.log', 'w').write('\n'.join(LOG) + '\n')
print('saved', DST)
