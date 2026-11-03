#!/usr/bin/env python3
"""planC.py BOARD OUT.json : RT-6 task 3 (I2S hub): TP12 (BCK) <-> TP14 (LRCK) position swap; BCK tail shortened to the new TP12
(top); LRCK stub from its existing corner (142.895,97.047) to the new TP14 (middle)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mkplan import P

B, OUT = sys.argv[1:3]
p = P(B)
BCK, LRCK = '/I2S_BCK', '/I2S_LRCK'
p.move('TP12', 146.35, 95.4)
p.move('TP14', 146.35, 98.5)
for a in [(144.5, 93.75, 147.15, 93.75), (143.8, 94.45, 144.5, 93.75), (143.8, 97.95, 143.8, 94.45), (144.35, 98.5, 143.8, 97.95),
          (146.35, 98.5, 144.35, 98.5)]:
    p.seg_del_at(BCK, *a)
p.seg('F.Cu', BCK, 0.25, (147.15, 93.75), (147.15, 94.65))
p.seg('F.Cu', LRCK, 0.25, (142.895, 97.047), (143.6, 97.752), (144.8, 97.752))
p.save(OUT)
