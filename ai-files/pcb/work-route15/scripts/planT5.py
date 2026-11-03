import sys; sys.path.insert(0,'scripts')
from mkplan import P
p=P(sys.argv[1] if len(sys.argv)>1 else 'B1.kicad_pcb')
SW='/Battery_Charger/SW2'
# SW2 bootstrap via V2 0.57 mm NE, away from the BATP B.Cu lane (0.325 -> 0.83 mm)
p.seg_set_at(SW,155.6,125.317,155.6,126.2,(155.6,125.317,155.983,125.7))
p.via_set_at(SW,155.6,126.2,155.983,125.7)
p.seg_set_at(SW,155.6,122.7,155.6,126.2,(155.6,122.7,155.6,125.317))
p.seg('B.Cu',SW,0.3,(155.6,125.317),(155.983,125.7))
p.save('t/planT5.json')
