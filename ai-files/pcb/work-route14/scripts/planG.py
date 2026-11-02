#!/usr/bin/env python3
"""planG.py BOARD OUT.json : RT-6 task-1 iteration 3 (hygiene + parcheck): exact REGN hook joints, V1 moved to the SW2 stub end
(F stub 0.2 mm), VINL2 link onto the exact node, Q103-G/BATP/TS_SENSE redrawn with >= 0.75 mm mitres, BATP/TS_SENSE separated
to >= 0.4 mm edge gap (column x 164.0 / 164.9, lane y 126.95 / 127.785), BAT_INT field: 4 more vias moved out of the lane
(165.5 column, 165.9@120.6) and 3 added on row y 120.6 (net count 22 -> 16)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mkplan import P

B, OUT = sys.argv[1:3]
p = P(B)
REGN, SW2, BATP, QG, TS, BAT = '/Battery_Charger/REGN', '/Battery_Charger/SW2', 'Net-(U4-BATP)', 'Net-(Q103-G)', '/Battery_Charger/TS_SENSE', '/Battery_Charger/BAT_INT'
VL2 = 'Net-(U24-VINL2)'


def dels(net, pts):
    for a, b in zip(pts, pts[1:]):
        p.seg_del_at(net, a[0], a[1], b[0], b[1])


# REGN hook: exact joints at the existing trunk end and on the U4-5 REGN track node
dels(REGN, [(152.19, 115.62), (149.5, 118.31), (149.5, 121.87), (148.8, 122.57)])
p.via_del_at(REGN, 148.8, 122.57)
p.seg('B.Cu', REGN, 0.4, (152.1905, 115.6187), (149.5, 118.3092), (149.5, 121.872), (148.794, 122.578))
p.via(REGN, 148.794, 122.578)
# (SW2 V1 move to (151.75,119.3) rolled back: its clearance cut the U4-28 SW1 stub off SW1_F; A2 V1 kept)
# VINL2 link onto the exact node
dels(VL2, [(154.24, 82.56), (154.24, 81.61), (155.37, 81.61)])
p.seg('F.Cu', VL2, 0.25, (154.245, 82.555), (154.245, 81.63), (155.3825, 81.63))
# Q103-G longer mitres
dels(QG, [(154.12, 120.16), (154.12, 115.45), (154.47, 115.1), (163.1, 115.1)])
dels(QG, [(163.85, 114.35), (170.625, 114.35), (170.975, 114.0), (170.975, 112.75)])
p.seg('B.Cu', QG, 0.25, (154.12, 120.16), (154.12, 115.65), (154.67, 115.1), (163.1, 115.1))
p.seg('B.Cu', QG, 0.25, (163.85, 114.35), (170.425, 114.35), (170.975, 113.8), (170.975, 112.75))
# BATP B.Cu
dels(BATP, [(154.64, 123.35), (154.64, 126.6), (154.99, 126.95), (162.05, 126.95), (164.0, 125.0), (164.0, 115.9), (170.47, 115.9), (170.47, 115.2)])
p.seg('B.Cu', BATP, 0.25, (154.64, 123.35), (154.64, 126.4), (155.19, 126.95), (162.0, 126.95), (164.0, 124.95), (164.0, 116.45), (164.55, 115.9),
      (169.77, 115.9), (170.47, 115.2))
# TS_SENSE B.Cu
dels(TS, [(153.17, 127.485), (153.31, 127.625), (162.075, 127.625), (164.5, 125.2), (164.5, 116.4), (172.4, 116.4), (172.4, 108.35), (199.0, 108.35),
          (202.745, 104.605), (204.285, 104.605)])
p.seg('B.Cu', TS, 0.25, (153.17, 127.485), (153.47, 127.785), (162.115, 127.785), (164.9, 125.0), (164.9, 117.15), (165.45, 116.6), (171.85, 116.6),
      (172.4, 116.05), (172.4, 108.9), (172.95, 108.35), (199.0, 108.35), (202.745, 104.605), (204.285, 104.605))
# BAT_INT field: lane x 163.8-166.2
for x, y in [(165.5, 121.7), (165.5, 122.8), (165.5, 123.9), (165.9, 120.6)]:
    p.via_del_at(BAT, x, y)
for x in (167.7, 168.8, 169.9):
    p.via(BAT, x, 120.6, 0.8, 0.4)
p.save(OUT)
