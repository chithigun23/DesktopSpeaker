import sys; sys.path.insert(0,'scripts')
from mkplan import P
p=P('B1.kicad_pcb')
TS='/Battery_Charger/TS_SENSE'
# TS_SENSE: via straight below pin 16 (frees the column below pins 12-15)
p.seg_del_at(TS,152.87,125.285,153.42,124.735)
p.via_del_at(TS,152.87,125.285)
p.seg_del_at(TS,152.32,125.835,152.87,125.285); p.seg_del_at(TS,152.32,126.635,152.32,125.835); p.seg_del_at(TS,153.17,127.485,152.32,126.635)
p.seg('F.Cu',TS,0.2,(153.42,124.735),(153.42,125.6))
p.via(TS,153.42,125.6,0.6,0.3)
p.seg('B.Cu',TS,0.25,(153.42,125.6),(153.42,127.235),(153.17,127.485))
# GND: remove the off-grid duplicate stubs between U4-10/11 and C313-2 (one straight 0.3 track and the via remain)
import json
for u in ['0094abd4','33147aa2','d14e8d86','abaa9043']: p.plan['seg_del'].append(u)
p.save('t/planU4S.json')
