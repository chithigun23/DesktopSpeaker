"""flatpak: route_r6a_final.py IN OUT : OUT_x widening pours (U6/U7 -> L202/L204/L205/L206), lock every copper item, refill"""
import sys
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
b = pcbnew.LoadBoard(sys.argv[1])
def Z(n, pts, name, prio=11): zone(b, n, 'F', pts, prio=prio, clr=0.3, name=name)
dx = 82.79
Z('Net-(U6-OUT_A-)', [(110.0, 132.95), (111.6, 132.95), (114.6, 135.9), (117.85, 135.9), (117.85, 137.2), (114.4, 137.2), (111.2, 134.4), (110.0, 134.4)], 'OUT_A-_U6_F')
Z('Net-(U6-OUT_B-)', [(108.9, 134.2), (108.9, 135.2), (106.2, 137.4), (101.7, 137.4), (101.7, 136.0), (105.4, 136.0), (107.6, 134.2)], 'OUT_B-_U6_F')
Z('Net-(U7-OUT_A+)', [(110.0 + dx, 132.95), (111.6 + dx, 132.95), (114.6 + dx, 135.9), (117.85 + dx, 135.9), (117.85 + dx, 137.2), (114.4 + dx, 137.2), (111.2 + dx, 134.4), (110.0 + dx, 134.4)], 'OUT_A+_U7_F')
Z('Net-(U7-OUT_A+)', [(196.25, 132.0), (197.0, 132.0), (198.2, 133.6), (198.2, 136.9), (197.3, 136.9), (197.3, 134.6), (196.25, 133.4)], 'OUT_A+_U7b_F', 12)
Z('Net-(U7-OUT_B+)', [(108.9 + dx, 134.2), (108.9 + dx, 135.2), (106.2 + dx, 137.4), (101.7 + dx, 137.4), (101.7 + dx, 136.0), (105.4 + dx, 136.0), (107.6 + dx, 134.2)], 'OUT_B+_U7_F')
# TPS63802 L1 switch nodes (U14 -> L2.1, U15 -> L3.1): 1.0-1.3 mm pours beyond the pin neck
Z('Net-(U14-L1)', rect(95.6, 99.9, 97.9, 101.25), 'U14_L1_F')
Z('Net-(U15-L1)', rect(118.55, 35.55, 120.8, 36.55), 'U15_L1_F')
n = 0
for t in b.Tracks(): t.SetLocked(True); n += 1
for z in b.Zones(): z.SetLocked(True)
refill(b); pcbnew.SaveBoard(sys.argv[2], b); print('locked items', n)
