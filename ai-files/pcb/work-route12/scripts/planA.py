#!/usr/bin/env python3
"""planA.py BOARD OUT.json : RT-6 task 1 (U4 east): REGN pocket section -> west hook, compact SW2 bootstrap loop
(leg hugging the U4 east pin row, V1 at U4-26, V2 at C110-2), C110/R102 nudges, BTST2/PROG/BATP fan-out, Q103-G and
BATP/TS_SENSE B.Cu routes, BAT_INT via field thinned (5 of 22), SYS stitching row y 128.2 -> 129.8, REGN via moved."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mkplan import P

B, OUT = sys.argv[1:3]
p = P(B)
REGN, SW2, BT, PROG, GND = '/Battery_Charger/REGN', '/Battery_Charger/SW2', '/Battery_Charger/BTST2', '/Battery_Charger/PROG', 'GND'
BATP, QG, TS, SYS, BAT = 'Net-(U4-BATP)', 'Net-(Q103-G)', '/Battery_Charger/TS_SENSE', '/SYS_RAW', '/Battery_Charger/BAT_INT'

# --- REGN: delete the pocket section (152.19,115.62) .. via (155.45,127.6); new west hook to the U4-5 REGN track
for a in [(152.19, 115.619, 152.795, 117.609), (152.795, 117.609, 153.4, 119.6), (153.4, 119.6, 153.0, 120.0), (153.0, 120.0, 153.0, 123.067),
          (153.0, 123.067, 153.567, 123.633), (153.567, 123.633, 153.65, 125.65), (153.65, 125.65, 155.25, 127.4)]:
    p.seg_del_at(REGN, *a)
p.seg('B.Cu', REGN, 0.4, (152.19, 115.62), (149.5, 118.31), (149.5, 121.87), (148.8, 122.57))
p.via(REGN, 148.8, 122.57)
# REGN via of R108-1 moved south out of the new lanes; F.Cu feed redrawn
p.via_set_at(REGN, 155.45, 127.6, 155.45, 128.9)
p.seg_set_at(REGN, 155.45, 127.6, 155.45, 130.7, (155.45, 128.9, 155.45, 130.7))
p.seg_del_at(REGN, 155.33, 127.48, 155.45, 127.6)
p.seg_set_at(REGN, 154.27, 127.48, 155.33, 127.48, (154.27, 127.48, 154.83, 127.48))
p.seg('F.Cu', REGN, 0.6, (154.83, 127.48), (155.45, 128.1), (155.45, 128.9))

# --- SW2 bootstrap loop: old B.Cu leg, its two vias and the C110-2 stub removed
p.seg_del_at(SW2, 153.0, 115.2, 156.3, 118.5)
p.seg_del_at(SW2, 156.3, 118.5, 156.3, 124.63)
p.seg_del_at(SW2, 156.3, 124.63, 155.13, 125.8)
p.seg_del_at(SW2, 154.73, 124.8475, 154.73, 125.4)
p.seg_del_at(SW2, 154.73, 125.4, 155.13, 125.8)
p.via_del_at(SW2, 155.13, 125.8)
p.via_del_at(SW2, 153.0, 115.2)
p.via(SW2, 151.9, 119.45, 0.5, 0.2)                              # V1 on the U4-26 SW2 stub
p.seg('B.Cu', SW2, 0.3, (151.9, 119.45), (151.9, 120.1), (152.87, 121.07), (152.87, 122.7), (155.6, 122.7), (155.6, 126.2))
p.via(SW2, 155.6, 126.2)                                         # V2 below C110-2
p.move('C110', 155.6, 124.75, -90)
p.seg('F.Cu', SW2, 0.4, (155.6, 125.317), (155.6, 126.2))

# --- BTST2 / PROG / BATP fan-out at the U4 east toe
p.seg_del_at(BT, 153.43, 122.585, 154.07, 122.585)
p.seg_del_at(BT, 154.07, 122.585, 154.73, 123.245)
p.seg_del_at(BT, 154.73, 123.245, 154.73, 123.7125)
p.seg('F.Cu', BT, 0.2, (153.43, 122.585), (154.655, 122.585), (155.6, 123.53), (155.6, 124.182))
p.seg_del_at(PROG, 153.47, 122.185, 154.305, 122.185)
p.seg_del_at(PROG, 154.305, 122.185, 156.05, 123.93)
p.move('R102', 156.95, 124.457, -90)
p.move('C106', 158.85, 122.84)
p.move('TP2', 159.97, 126.485)
p.seg('F.Cu', PROG, 0.2, (153.47, 122.185), (154.845, 122.185), (156.52, 123.86), (156.95, 123.86))
# R102 / C106 GND: shared via moved to (157.4,125.25)
p.seg_del_at(GND, 156.05, 124.8975, 157.0, 124.8975)
p.seg_del_at(GND, 157.9, 123.9975, 157.0, 124.8975)
p.via_del_at(GND, 157.0, 124.8975)
p.seg_del_at(GND, 157.9, 123.877, 157.9, 123.9975)
p.via(GND, 156.95, 125.95)
p.seg('F.Cu', GND, 0.3, (156.95, 125.054), (156.95, 125.95))
p.seg('F.Cu', GND, 0.4, (158.85, 123.977), (158.85, 124.254), (158.05, 125.054), (156.95, 125.054))

# --- BATP (Kelvin sense, U4-18 -> R112-2)
p.seg('F.Cu', BATP, 0.2, (153.445, 122.985), (154.275, 122.985), (154.64, 123.35))
p.via(BATP, 154.64, 123.35, 0.5, 0.2)
p.seg('B.Cu', BATP, 0.25, (154.64, 123.35), (154.64, 126.6), (154.99, 126.95), (162.05, 126.95), (164.0, 125.0), (164.0, 115.9),
      (170.47, 115.9), (170.47, 115.2))
p.via(BATP, 170.47, 115.2)
p.seg('F.Cu', BATP, 0.25, (170.47, 115.2), (170.47, 114.21))

# --- Q103-G (U4-24 -> Q103-4)
p.seg('F.Cu', QG, 0.2, (153.695, 120.585), (154.12, 120.16))
p.via(QG, 154.12, 120.16, 0.5, 0.2)
p.seg('B.Cu', QG, 0.25, (154.12, 120.16), (154.12, 115.45), (154.47, 115.1), (163.1, 115.1), (163.85, 114.35), (170.625, 114.35),
      (170.975, 114.0), (170.975, 112.75))
p.via(QG, 170.975, 112.75)
p.seg('F.Cu', QG, 0.25, (170.975, 112.75), (170.975, 111.71))

# --- TS_SENSE (U4 side via (153.17,127.485) -> J5-2 B.Cu pad)
p.seg('B.Cu', TS, 0.25, (153.17, 127.485), (153.31, 127.625), (162.075, 127.625), (164.5, 125.2), (164.5, 116.4), (172.4, 116.4), (172.4, 108.35),
      (199.0, 108.35), (202.745, 104.605), (204.285, 104.605))

# --- BAT_INT via field thinned: 5 of 22 removed (lane x 163.8-164.8)
for x, y in [(164.3, 120.6), (165.1, 120.6), (164.4, 121.7), (164.4, 122.8), (164.4, 123.9)]:
    p.via_del_at(BAT, x, y)
# --- SYS_RAW stitching row y 128.2 moved to y 129.8 (same 7 vias, same x)
for x in (156.9, 157.7, 158.5, 159.3, 160.1, 160.9, 161.7):
    p.via_set_at(SYS, x, 128.2, x, 129.8)
p.save(OUT)
