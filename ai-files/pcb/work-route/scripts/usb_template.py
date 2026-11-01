"""usb_template.py OUT_PLAN.json : scripted exact-octilinear USB template (J1 -> D1 -> R173/R171/R172 -> U2), stage S1.
Waypoints are listed per net; every segment is checked to be exactly 0/45/90 deg before the plan is written."""
import json, sys, math
DP, DN, UP, UM, GND = '/USB_DP', '/USB_DN', 'Net-(U2-D+)', 'Net-(U2-D-)', 'GND'
segs, vias = [], []
def path(layer, net, w, pts):
    for a, b in zip(pts, pts[1:]):
        dx, dy = round(b[0] - a[0], 6), round(b[1] - a[1], 6)
        assert dx == 0 or dy == 0 or abs(abs(dx) - abs(dy)) < 1e-9, (net, a, b)
        segs.append([layer, net, w, a[0], a[1], b[0], b[1]])
# --- J1 escape (inside NECK_J1: 0.2 mm width, 0.45/0.2 vias) ---
# J1 stubs: all four exits 0.25 (A6 0.3) so every parallel DP/DN pair of exits has a 0.225-0.25 mm gap (diff_pair_gap rule)
path('F.Cu', DP, 0.25, [(148.23, 26.355), (148.23, 27.84)])           # B6 stub
path('F.Cu', DP, 0.3, [(149.23, 26.355), (149.23, 27.35)])            # A6 stub (pad width)
vias += [[DP, 148.23, 27.84, 0.5, 0.2], [DP, 149.23, 27.35, 0.5, 0.2]]
path('B.Cu', DP, 0.25, [(149.23, 27.35), (148.74, 27.84), (148.23, 27.84)])   # B.Cu jumper A6 -> B6
path('B.Cu', DP, 0.25, [(148.23, 27.84), (148.23, 29.06)])            # B.Cu down to the return via
vias += [[DP, 148.23, 29.06, 0.6, 0.3]]                               # DP back to F.Cu
for x0 in (148.705, 149.755):                                         # A7 / B7 branches of the DN Y junction
    path('F.Cu', DN, 0.25, [(x0, 26.355), (x0, 27.57), (149.23, 28.095)])
vias += [[GND, 149.3, 29.4, 0.6, 0.3], [GND, 149.95, 28.55, 0.6, 0.3]]                                # return-current GND via for the B.Cu jumper
# --- J1 -> D1 -> trunk, DN west / DP east ---
path('F.Cu', DN, 0.25, [(149.23, 28.095), (148.96, 28.365), (145.62, 28.365), (145.2, 28.785), (145.2, 29.84)])
path('F.Cu', DN, 0.25, [(145.2, 29.84), (144.6, 29.84)])            # tap into D1-5 (DN)
path('F.Cu', DN, 0.25, [(145.2, 29.84), (145.2, 31.0), (144.28, 31.92), (144.28, 39.0), (147.95, 42.67),
                        (147.95, 61.0), (148.7, 61.75)])              # trunk -> R172-1
path('F.Cu', DP, 0.25, [(148.23, 29.06), (147.935, 28.765), (146.6, 28.765)])
path('F.Cu', DP, 0.25, [(146.6, 28.765), (146.0, 28.765)])              # tap into D1-3 (DP)
c = 145.2 + 31.0 + 0.4 * math.sqrt(2)                                # DP diagonal 0.4 mm (centre) beside the DN diagonal
c = round(c, 4)
y1 = round(c - 146.6, 4); y2 = round(c - 144.68, 4)
cse = round(144.28 - 39.0 + 0.4 * math.sqrt(2), 4)                    # x - y of the DP south-east jog
y3 = round(144.68 - cse, 4); y4 = round(148.35 - cse, 4)
path('F.Cu', DP, 0.25, [(146.6, 28.765), (146.6, y1), (144.68, y2), (144.68, y3), (148.35, y4), (148.35, 57.43), (148.8, 57.88)])
path('F.Cu', DP, 0.25, [(149.05, 57.83), (149.05, 59.1325)])         # R173-1 -> R171-1
# --- R171-2 -> U2-1 (D+), inner entry; R172-2 -> U2-2 (D-), outer entry ---
path('F.Cu', UP, 0.25, [(149.05, 60.3275), (149.855, 60.3275), (150.655, 61.1275), (150.655, 62.0)])
path('F.Cu', UM, 0.25, [(148.9, 62.9775), (148.9, 63.67), (149.675, 64.445), (150.765, 64.445), (151.305, 63.905), (151.305, 63.3)])
plan = {'seg_add': segs, 'via_add': vias, 'seg_del': ['cddb4150'],   # cddb: 0.05 mm LDO_3V3 overlap left by the A1 R10 fix
       
        'via_set': {'d3c5ebf1': [146.58, 27.6]}, 'seg_set': {'02a1aa4a': [146.58, 26.8, 146.58, 27.6]}}
json.dump(plan, open(sys.argv[1], 'w'), indent=0)
print('segments', len(segs), 'vias', len(vias), 'DP diag c', c, y1, y2, 'SE jog', y3, y4)
