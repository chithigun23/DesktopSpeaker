"""flatpak: route_r6a_power.py IN.kicad_pcb OUT.kicad_pcb [blocks]
R6a phase 2/3 hand geometry: power copper shapes (zones), neck tracks and vias per block. All items locked.
Coordinates come from the v10d pad dump (see ai-files/reports/pcb-routing-r6a.md)."""
import sys, json
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
inp, outp = sys.argv[1:3]
SEL = sys.argv[3].split(',') if len(sys.argv) > 3 else None
b = pcbnew.LoadBoard(inp)
F, B2, BB = 'F', '2', 'B'
def T(n, pts, w, lay='F'): return trk(b, n, lay, pts, w)
ZCLR = {'POWER_HI': 0.4, 'PVDD': 0.3, 'SPK_OUT': 0.3, 'SWITCH': 0.3, 'GND': 0.4}
def Z(n, pts, prio, lay='F', clr=None, name='', **k):
    if clr is None: clr = max(0.2, ZCLR.get(ncls(full(n, b)), 0.25))
    return zone(b, n, lay, pts, prio=prio, clr=clr, name=name or ('%s_%s' % (n.split('/')[-1], lay)), **k)
LOG = {'via_fail': [], 'fields': {}}
def VIA(n, x, y, d=0.6, dr=0.3, force=False):
    if force: return via(b, n, x, y, d, dr)
    v = place_via(b, n, x, y, d, dr)
    if v is None: LOG['via_fail'].append((n, x, y))
    return v
def FIELD(n, pts, want, tag, d=0.6, dr=0.3):
    got = 0
    for x, y in pts:
        if got >= want: break
        if place_via(b, n, x, y, d, dr) is not None: got += 1
    LOG['fields'][tag] = got
    return got
def grid(x0, x1, y0, y1, p=0.8):
    out = []; y = y0
    while y <= y1 + 1e-6:
        x = x0
        while x <= x1 + 1e-6: out.append((round(x, 3), round(y, 3))); x += p
        y += p
    return out
BLOCKS = {}
def block(f): BLOCKS[f.__name__] = f; return f

@block
def charger():
    # --- pin necks (0.2 mm inside NECK_U4)
    T('SW1', [(151.12, 120.485), (151.12, 119.0), (150.97, 118.85), (150.97, 118.0)], 0.2)
    T('SW2', [(152.02, 120.485), (152.02, 119.0), (152.2, 118.82), (152.2, 118.3)], 0.2)
    T('PMID', [(150.67, 120.46), (150.67, 119.6), (150.2, 119.13)], 0.2)
    T('PMID', [(148.75, 118.0), (148.9, 118.375), (149.85, 118.375), (149.85, 118.9)], 0.35)   # C312 -> C101 link under SW1 lane
    T('GND', [(151.57, 120.485), (151.57, 116.6)], 0.2)
    T('SYS_RAW', [(152.47, 120.485), (152.47, 119.6), (152.98, 119.2)], 0.2)
    T('SYS_RAW', [(153.27, 118.95), (153.27, 118.4), (154.5, 118.4), (154.6, 117.9)], 0.25)  # C311 -> C104
    T('BAT_INT', [(153.47, 120.985), (153.47, 121.385)], 0.2)
    T('BAT_INT', [(153.55, 121.185), (156.3, 121.185)], 0.6)
    T('Net-(Q103-G)', [(153.433, 120.585), (153.8, 120.585), (154.2, 120.1), (155.55, 120.1)], 0.2); VIA('Net-(Q103-G)', 155.55, 120.1, 0.5, 0.2)
    T('Net-(Q103-G)', [(170.975, 111.71), (170.975, 112.55)], 0.25); VIA('Net-(Q103-G)', 170.975, 112.55)
    # Q103 gate drive (SDRV) jumper on B.Cu, clear of the SW2 bootstrap link; placed before the via fields
    pts = [(155.55, 120.1), (156.4, 119.15), (166.6, 119.15), (170.975, 114.8), (170.975, 112.55)]
    if all(track_legal(b, 'Net-(Q103-G)', a, c, 0.25, 'B') for a, c in zip(pts[:-1], pts[1:])): T('Net-(Q103-G)', pts, 0.25, 'B')
    else: LOG['via_fail'].append(('gate_jumper_illegal',))

    # VBUS_PD at U4 pins 2/3 and 8/9
    T('VBUS_PD', [(149.67, 121.385), (149.67, 120.985), (149.2, 120.985), (148.45, 120.7)], 0.2)
    T('BTST1', [(149.67, 121.785), (148.6, 121.785)], 0.2)
    T('REGN', [(149.67, 122.185), (149.2, 122.185), (148.85, 122.55), (148.45, 122.75)], 0.2)          # pin 5 -> C102.1
    T('REGN', [(147.45, 123.8), (146.7, 124.55), (146.7, 125.8)], 0.4)             # C102.1 -> C109.1, west of the VBUS_PD vias
    # REGN hub at TP11: R103.1 and R100.1 straight down, R108.1 by a short B.Cu jumper, so the TS_SENSE lane (pin 16 -> R100.2) stays open
    T('REGN', [(151.87, 127.578), (151.87, 130.6)], 0.5)
    T('REGN', [(152.77, 129.08), (152.77, 130.6)], 0.5)
    T('REGN', [(154.67, 127.38), (155.45, 127.6)], 0.4); VIA('REGN', 155.45, 127.6, force=True)
    T('REGN', [(155.45, 127.6), (155.45, 130.7)], 0.4, 'B'); VIA('REGN', 155.45, 130.7, force=True)
    T('REGN', [(155.45, 130.7), (154.6, 130.9)], 0.4)
    # BTST cap SW links on B.Cu (documented v10b exception), routed clear of the BATP via
    T('SW1', [(147.33, 121.65), (146.45, 121.75)], 0.4)
    T('SW1', [(146.45, 121.75), (146.45, 119.6), (147.1, 118.0), (150.1, 115.2)], 0.4, 'B')
    T('SW2', [(155.75, 125.57), (156.55, 125.57)], 0.4)
    T('SW2', [(156.55, 125.57), (156.4, 124.0), (155.9, 122.6), (154.5, 120.0), (153.0, 115.2)], 0.4, 'B')
    T('BTST2', [(153.43, 122.585), (155.75, 122.585), (155.75, 124.4)], 0.2)
    # --- copper shapes
    Z('SW1', [(150.3, 118.55), (151.07, 118.55), (151.07, 112.3), (148.3, 112.3), (148.3, 113.75), (149.2, 113.75), (149.2, 117.85), (150.3, 117.85)], 10)
    Z('SW2', [(151.9, 118.7), (152.75, 118.7), (152.75, 117.95), (154.05, 117.95), (154.05, 112.3), (151.9, 112.3)], 10)
    Z('GND', [(142.3, 113.55), (161.0, 113.55), (161.0, 116.3), (142.3, 116.3)], 5, name='GND_U4_TOP_F')
    Z('PMID', [(142.4, 116.75), (149.0, 116.75), (149.0, 118.2), (142.4, 118.2)], 8)
    Z('SYS_RAW', [(154.1, 116.75), (160.6, 116.75), (160.6, 115.9), (163.4, 115.9), (163.4, 119.4), (154.1, 119.4)], 8, name='SYS_U4CAP_F')
    Z('VBUS_PD', [(146.45, 119.3), (149.1, 119.3), (149.1, 120.95), (146.45, 120.95)], 8, name='VBUS_U4A_F')
    # BAT_INT F.Cu trunk C106 -> Q103 (>= 5 mm where room allows)
    Z('BAT_INT', [(156.0, 119.95), (167.2, 119.95), (167.2, 108.6), (170.68, 108.6), (170.68, 124.4), (161.0, 124.4), (161.0, 121.5), (156.0, 121.5)], 8, name='BAT_INT_F')

@block
def boost():
    # SW node: bar from L200.2 to pins 4-7 (pad width ~1.85 mm), links to R252.2 (FSW resistor) and C267.2 (BOOT cap)
    Z('Net-(U25-SW)', rect(147.2, 146.27, 151.6, 148.12), 10, name='U25_SW_F')
    T('Net-(U25-SW)', [(151.458, 146.445), (151.458, 147.945)], 0.24)
    T('Net-(U25-SW)', [(148.3, 143.6), (149.0, 142.9), (150.4, 142.5)], 0.4)
    T('Net-(U25-SW)', [(150.662, 142.34), (151.28, 143.0), (151.827, 143.64)], 0.25)
    # BOOT: pin 8 -> via -> B.Cu -> via -> C267.1
    T('Net-(U25-BOOT)', [(151.3, 148.445), (150.3, 148.445), (149.6, 148.9)], 0.25)
    VIA('Net-(U25-BOOT)', 149.6, 148.9); VIA('Net-(U25-BOOT)', 149.75, 143.64)
    T('Net-(U25-BOOT)', [(149.6, 148.9), (149.75, 143.64)], 0.3, 'B')
    T('Net-(U25-BOOT)', [(149.75, 143.64), (150.692, 143.64)], 0.25)
    # SYS input: pin 9 -> C260.1, pour to L200.1 / C26x / via field
    T('SYS_RAW', [(151.3, 148.945), (150.6, 149.65), (150.45, 150.5)], 0.25)
    T('Net-(U25-SS)', [(152.435, 149.6), (152.0, 150.25), (151.64, 150.6)], 0.2)
    Z('SYS_RAW', [(156.4, 124.85), (162.4, 124.85), (162.4, 139.4), (144.25, 139.4), (144.25, 150.25), (154.15, 150.25), (154.15, 156.95),
                  (139.6, 156.95), (139.6, 134.0), (156.4, 134.0)], 8, name='SYS_BOOST_F')   # boost input pour + trunk from TP2 (>= 5.4 mm)
    # PVDD out: pins 14-16 -> C314/C270/C290 -> C279 / C275 / C277 / C292 + via fields
    T('PVDD_AMP', [(154.912, 146.945), (154.912, 147.945)], 0.24)
    Z('PVDD_AMP', [(154.6, 146.85), (160.75, 146.85), (160.75, 143.9), (163.6, 143.9), (163.6, 149.6), (165.5, 149.6), (165.5, 156.15),
                   (156.6, 156.15), (156.6, 153.1), (160.6, 153.1), (160.6, 148.6), (154.6, 148.6)], 9, name='PVDD_BOOST_F')
    T('PVDD_AMP', [(161.25, 144.3), (161.25, 142.3), (160.45, 142.3)], 0.5)
    T('PVDD_AMP', [(160.3, 148.1), (162.5, 148.1), (162.5, 150.9)], 0.6)   # output band -> C275 / via column below C279.2
    # power-stage GND (output caps -> PGND pins 11/12/EP), own vias for caps inside the SYS pour
    T('GND', [(156.1, 148.218), (156.1, 148.95)], 0.3)
    Z('GND', [(153.65, 148.75), (160.55, 148.75), (160.55, 152.95), (156.4, 152.95), (156.4, 156.4), (154.55, 156.4), (154.55, 150.0), (153.65, 150.0)], 7, name='GND_BOOST_F')
    VIA('GND', 158.72, 150.95); VIA('GND', 155.5, 153.74)
    T('GND', [(142.8, 154.04), (142.8, 155.25)], 0.4); VIA('GND', 142.8, 155.25)
    T('GND', [(150.36, 151.907), (149.4, 151.9)], 0.4); VIA('GND', 149.4, 151.9)
    T('GND', [(151.64, 151.947), (150.36, 151.907)], 0.3)
    T('GND', [(151.06, 155.787), (149.5, 155.8)], 0.4); VIA('GND', 149.5, 155.8)

@block
def charger2():
    # extra BAT_INT transition vias (C106 side / Q103 side)
    FIELD('BAT_INT', grid(161.1, 166.7, 120.6, 123.8), 10, 'BAT_INT_C106_extra')
    FIELD('BAT_INT', grid(167.6, 170.0, 111.7, 123.9), 9, 'BAT_INT_Q103_extra')
    # VBUS_PD lower group at U4 (pins 8/9 -> C313 -> C111 + reservation vias)
    T('VBUS_PD', [(149.67, 123.385), (149.67, 124.3), (149.58, 125.1)], 0.2)
    T('VBUS_PD', [(149.58, 125.5), (149.57, 126.6)], 0.5)
    T('VBUS_PD', [(147.65, 124.6), (148.55, 125.0), (149.3, 125.2)], 0.4)
    T('VBUS_PD', [(148.25, 127.0), (148.95, 127.0)], 0.5)
    T('VBUS_PD', [(148.3, 128.0), (148.95, 127.5)], 0.5)
    # SYS F.Cu trunk TP2 -> boost (>= 5.4 mm), stitched to the In2 SYS island
    FIELD('SYS_RAW', grid(156.9, 161.9, 128.2, 133.0), 14, 'SYS_trunk_vertical')
    FIELD('SYS_RAW', grid(141.5, 155.5, 135.4, 138.6), 18, 'SYS_trunk_west')

@block
def battery():
    # Q103 source side: F.Cu pad pour + 18 vias to the In2 / B.Cu BAT_PACK bands
    Z('BAT_PACK', [(171.75, 108.9), (175.7, 108.9), (175.7, 110.3), (177.4, 110.3), (177.4, 114.6), (171.0, 114.6), (171.0, 113.4), (171.75, 113.4)], 8, name='BAT_PACK_Q103_F')
    FIELD('BAT_PACK', grid(175.0, 177.0, 109.3, 114.1), 18, 'BAT_PACK_Q103')
    band = [(173.0, 112.8), (201.0, 112.8), (201.0, 91.0), (212.0, 91.0), (212.0, 96.4), (196.0, 96.4), (196.0, 119.0), (173.0, 119.0)]
    Z('BAT_PACK', band, 6, lay='B', name='BAT_PACK_B')
    # PACK_RAW: J5.1 -> SW101.2 on F.Cu (5.3 mm)
    Z('PACK_RAW', [(203.3, 85.0), (211.9, 85.0), (211.9, 88.6), (208.75, 88.6), (208.75, 102.4), (203.3, 102.4)], 8, name='PACK_RAW_F')

@block
def vbus():
    # J1 cluster: VBUS pads straight to In2 (USB pair and CC lines pass between)
    T('USB_VBUS', [(146.58, 26.8), (146.58, 27.85)], 0.5); VIA('USB_VBUS', 146.58, 27.85)
    T('USB_VBUS', [(151.38, 26.8), (151.38, 27.85), (152.2, 28.4)], 0.5); VIA('USB_VBUS', 151.38, 27.85); VIA('USB_VBUS', 152.2, 28.4)
    T('USB_VBUS', [(147.75, 31.88), (150.03, 31.88)], 0.5); VIA('USB_VBUS', 147.75, 31.88)
    T('USB_VBUS', [(147.75, 31.88), (147.75, 32.75)], 0.5); VIA('USB_VBUS', 147.75, 32.75)
    T('USB_VBUS', [(150.38, 37.0), (151.6, 37.0)], 0.5)
    T('USB_VBUS', [(150.38, 36.753), (150.38, 37.253)], 0.24)
    T('USB_VBUS', [(151.6, 36.5), (151.6, 35.45)], 0.5); T('USB_VBUS', [(152.4, 36.5), (152.4, 35.45)], 0.5)
    VIA('USB_VBUS', 151.6, 35.45); VIA('USB_VBUS', 152.4, 35.45)
    # U11 cluster: pour TP1 / C2 / U11.23 + 14 vias; U11.32 -> C184
    Z('USB_VBUS', [(140.05, 47.7), (144.3, 47.7), (144.3, 55.35), (140.05, 55.35)], 8, name='USB_VBUS_U11_F')
    T('USB_VBUS', [(137.2, 53.875), (137.2, 52.0), (136.6, 51.4)], 0.3)
    FIELD('USB_VBUS', [(x, y) for y in (50.62, 51.25) for x in (140.5, 141.3, 142.1, 142.9, 143.7)] + [(143.85, y) for y in (52.3, 53.1, 53.9, 54.7)] + [(140.4, 47.4), (141.2, 47.4)], 15, 'USB_VBUS_U11')
    T('GND', [(142.3, 52.362), (140.9, 52.4)], 0.4); VIA('GND', 140.9, 52.4)
    T('USB_VBUS', [(136.55, 49.5), (136.55, 50.4)], 0.5); VIA('USB_VBUS', 135.75, 49.5); T('USB_VBUS', [(135.75, 49.5), (136.55, 49.5)], 0.5)
    T('USB_VBUS', [(146.325, 57.2), (146.3, 54.9), (144.0, 54.9)], 0.5)
    # VBUS_PD at U11: pin 20 -> C315 + 15 vias
    Z('VBUS_PD', [(140.3, 55.75), (145.2, 55.75), (145.2, 60.6), (140.3, 60.6)], 8, name='VBUS_PD_U11_F')
    FIELD('VBUS_PD', [(141.2, 57.9)] + grid(141.4, 144.6, 58.8, 60.4), 11, 'VBUS_PD_U11_extra')

@block
def inner():
    """In2 power islands (final shapes, power only)"""
    Z('USB_VBUS', rect(135.5, 27.35, 153.5, 54.6), 20, lay='2', clr=0.4, name='USB_VBUS_IN2')
    Z('VBUS_PD', rect(141.0, 55.2, 149.3, 129.0), 20, lay='2', clr=0.4, name='VBUS_PD_IN2')
    Z('SYS_RAW', [(149.7, 106.0), (163.5, 106.0), (163.5, 119.3), (157.2, 119.3), (157.2, 125.4), (163.0, 125.4), (163.0, 139.6),
                  (141.6, 139.6), (141.6, 149.6), (139.5, 149.6), (139.5, 133.4), (149.7, 133.4)], 21, lay='2', clr=0.4, name='SYS_IN2')   # incl. strip to the L200 via field
    Z('BAT_INT', [(157.6, 119.7), (163.9, 119.7), (163.9, 106.0), (172.6, 106.0), (172.6, 125.0), (157.6, 125.0)], 20, lay='2', clr=0.4, name='BAT_INT_IN2')
    Z('BAT_PACK', [(173.0, 107.5), (196.2, 107.5), (196.2, 90.5), (208.9, 90.5), (208.9, 91.0), (212.0, 91.0), (212.0, 96.4),
                   (208.9, 96.4), (208.9, 120.5), (173.0, 120.5)], 20, lay='2', clr=0.4, name='BAT_PACK_IN2')
    Z('PVDD_AMP', [(101.5, 123.4), (119.0, 123.4), (119.0, 140.0), (163.4, 140.0), (163.4, 132.0), (184.0, 132.0), (184.0, 123.4),
                   (201.5, 123.4), (201.5, 132.0), (213.3, 132.0), (213.3, 157.2), (105.0, 157.2), (105.0, 140.5), (101.5, 140.5)],
      20, lay='2', clr=0.3, name='PVDD_IN2')

def amp(dx, right_to_L, extra):
    """TAS5825M fan-out (U6 dx=0, U7 dx=82.79): PVDD lanes, OUT/BST necks, GND pin bridges to the EP"""
    u = 'U6' if dx == 0 else 'U7'
    X = lambda x: x + dx
    N = lambda s: 'Net-(%s-%s)' % (u, s)
    # GND pins -> EP bridges
    T('GND', [(X(112.165), 128.555), (X(111.3), 128.555)], 0.2)
    if u == 'U6': T('GND', [(X(112.165), 127.055), (X(111.3), 127.055)], 0.2)
    T('GND', [(X(107.345), 128.555), (X(108.2), 128.555)], 0.2)
    for x in (108.005, 108.505, 111.005, 111.505): T('GND', [(X(x), 131.215), (X(x), 130.4)], 0.2)
    # PVDD necks + lanes (right pins 3/4, left pins 21/22)
    T('PVDD_AMP', [(X(112.165), 129.055), (X(112.165), 129.555)], 0.24)
    T('PVDD_AMP', [(X(107.345), 129.055), (X(107.345), 129.555)], 0.24)
    # bottom row: OUT_B-/BST_B-/BST_A-/OUT_A- (U7: OUT_B+/BST_B-/BST_A-/OUT_A+)
    o27 = N('OUT_B-') if u == 'U6' else N('OUT_B+'); o30 = N('OUT_A-') if u == 'U6' else N('OUT_A+')
    T(o27, [(X(109.005), 131.4), (X(109.005), 131.85), (X(108.05), 131.85), (X(108.05), 134.61), (X(109.0), 134.61)], 0.2)
    T(N('BST_B-'), [(X(109.505), 131.4), (X(109.505), 132.25), (X(108.45), 132.25), (X(108.45), 133.96), (X(110.267), 133.96), (X(110.267), 134.4)], 0.2)
    T(N('BST_A-'), [(X(110.005), 131.4), (X(110.005), 132.45), (X(109.4), 133.05)], 0.2)
    T(o30, [(X(110.505), 131.4), (X(110.505), 133.1)], 0.2)
    extra()

def u6_extra():
    Z('PVDD_AMP', rect(111.95, 128.88, 116.65, 129.75), 12, name='PVDD_U6R_F')
    Z('PVDD_AMP', rect(104.1, 128.88, 107.55, 129.75), 12, name='PVDD_U6L_F')
    # right side: OUT_A+ over BST_A+, to C285.2 and up to L201.1
    T('Net-(U6-OUT_A+)', [(112.165, 130.055), (112.6, 130.12), (113.4, 130.12), (113.85, 130.4)], 0.2)
    T('Net-(U6-OUT_A+)', [(113.85, 130.4), (114.77, 130.4), (114.77, 131.0)], 0.4)
    T('Net-(U6-BST_A+)', [(112.165, 130.555), (113.3, 130.555), (113.632, 130.95)], 0.2)
    Z('Net-(U6-OUT_A+)', [(114.35, 130.35), (116.85, 130.35), (116.85, 128.1), (120.7, 128.1), (120.7, 131.75), (114.35, 131.75)], 11, name='OUT_A+_U6_F')
    # left side: OUT_B+ bar under the lane to C287.2 and L203.1; BST_B+ below it to C287.1
    T('Net-(U6-OUT_B+)', [(107.345, 130.055), (105.8, 130.055), (105.55, 130.25)], 0.2)
    T('Net-(U6-OUT_B+)', [(105.55, 130.25), (101.8, 130.25), (101.8, 128.0)], 0.4)
    T('Net-(U6-OUT_B+)', [(103.43, 130.25), (103.43, 132.1)], 0.4)
    T('Net-(U6-BST_B+)', [(107.345, 130.555), (106.6, 130.555), (106.2, 130.95), (104.57, 130.95), (104.57, 132.0)], 0.2)
    Z('Net-(U6-OUT_B+)', [(98.8, 128.0), (102.05, 128.0), (102.05, 130.0), (103.85, 130.0), (103.85, 132.6), (102.95, 132.6), (102.95, 131.4), (98.8, 131.4)], 11, name='OUT_B+_U6_F')

def u7_extra():
    Z('PVDD_AMP', [(194.7, 128.88), (198.05, 128.88), (198.05, 129.35), (200.15, 129.35), (200.15, 131.6), (197.4, 131.6), (197.4, 129.75), (194.7, 129.75)], 12, name='PVDD_U7R_F')
    Z('PVDD_AMP', [(184.85, 128.85), (190.4, 128.85), (190.4, 129.75), (187.3, 129.75), (187.3, 130.3), (186.5, 130.3), (186.5, 129.75), (184.85, 129.75)], 12, name='PVDD_U7L_F')
    # right side: OUT_A+ (pin 2) to C298.2 then down to L205.1; BST_A+ to C298.1
    T('Net-(U7-OUT_A+)', [(194.955, 130.055), (195.6, 130.055), (195.9, 130.25), (196.567, 130.25), (196.567, 131.9)], 0.2)
    T('Net-(U7-BST_A+)', [(194.955, 130.555), (195.433, 130.555), (195.433, 131.9)], 0.2)
    T('Net-(U7-OUT_A+)', [(196.567, 132.3), (196.567, 133.2), (197.8, 134.5), (197.8, 137.0)], 0.5)
    # left side: OUT_B+ (pin 23) around C291 and under C300 to C300.2; BST_B+ jumps on B.Cu
    T('Net-(U7-OUT_B+)', [(190.135, 130.055), (188.6, 130.055)], 0.2)
    T('Net-(U7-OUT_B+)', [(188.6, 130.055), (188.45, 130.2), (188.45, 133.06), (186.22, 133.06), (186.22, 132.4)], 0.4)
    T('Net-(U7-OUT_B+)', [(186.22, 133.06), (186.22, 136.95)], 0.6)
    T('Net-(U7-BST_B+)', [(190.135, 130.555), (189.3, 131.05)], 0.2)
    VIA('Net-(U7-BST_B+)', 189.3, 131.05, 0.5, 0.2, force=True)
    T('Net-(U7-BST_B+)', [(189.3, 131.05), (187.75, 131.55)], 0.25, 'B')
    VIA('Net-(U7-BST_B+)', 187.75, 131.55, force=True)
    T('Net-(U7-BST_B+)', [(187.75, 131.55), (187.4, 132.0)], 0.25)

@block
def amps():
    amp(0, True, u6_extra)
    amp(82.79, False, u7_extra)

@block
def extras():
    # v10c review m2: U24 AGND/DGND pins 7/12/15/25/26 tied under the body to one GND patch with 2 vias
    for x in (147.245, 148.745, 151.245): T('GND', [(x, 83.0), (x, 83.95)], 0.2)
    for x in (151.745, 152.245): T('GND', [(x, 87.8), (x, 86.9)], 0.2)
    Z('GND', rect(147.0, 83.75, 154.1, 87.1), 9, clr=0.2, name='GND_U24_PATCH_F')
    VIA('GND', 149.5, 85.4, force=True); VIA('GND', 152.3, 85.4, force=True)

@block
def rails():
    # J7.1 (3V_AO) escape between the TC2030 locating holes to a via outside the J7 via keep-out
    T('3V_AO', [(169.495, 95.94), (169.813, 96.6), (169.813, 99.75)], 0.2); VIA('3V_AO', 169.813, 99.75)
    # TAS5825M DVDD / VR_DIG escapes (pin 6 -> C281/C294 outer, pin 7 -> C282/C295 inner), planar per v10b B2
    for dx, n7 in ((0.0, 'Net-(U6-VR_DIG)'), (82.79, 'Net-(U7-VR_DIG)')):
        T('3V3_AUDIO', [(112.165 + dx, 128.055), (113.49 + dx, 128.055), (113.49 + dx, 126.75)], 0.2)
        T(n7, [(112.165 + dx, 127.555), (112.8 + dx, 127.555), (112.8 + dx, 125.25), (113.3 + dx, 125.25)], 0.2)
    # U6 DVDD cluster (pin 6 / C281 / R262) is enclosed by the VR_DIG escape: rail feed through one fine via off the pin-6 stub
    VIA('3V3_AUDIO', 113.3, 127.9, 0.5, 0.2, force=True)
    # 3V_AO B.Cu crossing of the VBUS_PD column (seed for the scripted rail routing)
    T('3V_AO', [(139.8, 70.0), (150.4, 70.0)], 0.5, 'B'); VIA('3V_AO', 139.8, 70.0); VIA('3V_AO', 150.4, 70.0)

def run():
    for k, f in BLOCKS.items():
        if SEL is None or k in SEL: f()
    if SEL is None or 'stubs' in SEL:
        T('PVDD_AMP', [(109.67, 146.56), (109.67, 144.9)], 0.5); VIA('PVDD_AMP', 109.67, 144.9)   # TP10 to the In2 PVDD band
        LOG['stubs'] = stub_vias(b, log=LOG['via_fail'])
    refill(b)
    pcbnew.SaveBoard(outp, b)
    json.dump(LOG, open(outp.replace('.kicad_pcb', '.power.json'), 'w'), indent=1)
    print('fields', LOG['fields']); print('via_fail', LOG['via_fail'])
run()
