import sys; sys.path.insert(0,'scripts')
from mkplan import P
p=P(sys.argv[1] if len(sys.argv)>1 else 'B1.kicad_pcb')
VL1='Net-(U24-VINL1)'; VR1='Net-(U24-VINR1)'; XO='Net-(U24-XO)'
# C212 (VREF decoupling) 0.35 mm west; its GND via moved off the VINR1 column; VREF entry shortened
p.move('C212',152.1,80.199999,90)
p.plan['seg_del'] += ['f7137758','988dbb35','6e839ebe','439aea75']
p.via_set_at('GND',151.85,79.0,151.75,78.75)
p.seg('F.Cu','GND',0.3,(151.75,78.75),(151.75,79.4))
p.seg('F.Cu','Net-(U24-VREF)',0.3,(151.745,81.505),(152.095,81.155))
# VINL1 diagonal moved 0.13 mm SE (c 233.72) so VINR1 fits beside it
p.plan['seg_del'] += ['a5ad4dbe','ef0f7fb8']
p.seg_del_at(VL1,153.25,80.3,153.25,82.56)
p.seg('F.Cu',VL1,0.25,(153.25,82.56),(153.25,80.47),(155.37,78.35))
# VINR1: U24-4 north, 45 deg NE, joins the R201-2/C207-1 node at (155.38,77.7)
p.seg('F.Cu',VR1,0.25,(152.745,82.555),(152.745,79.845),(154.89,77.7),(155.38,77.7))
# XO: Y200-2 GND via/stub removed (Y200-2 keeps its GND track), U24-9 -> Y200-3 east of the crystal
p.plan['seg_del'] += ['2ded5bca']
p.via_del_at('GND',150.9,78.05)
p.seg('F.Cu',XO,0.25,(150.245,82.555),(150.245,79.3),(150.9,78.645),(150.9,77.1),(150.45,76.65),(150.2,76.65))
p.save('t/planU24.json')
p.seg_set_at('GND',151.05,79.7825,152.3,79.7825,(151.05,79.7825,152.1,79.7825))
p.plan['seg_del'] += ['1d7259f2','b8b0f8cb']
p.seg('F.Cu','Net-(U24-AVDD)',0.3,(150.745,82.555),(150.745,81.6),(151.05,81.295))
p.save('t/planU24.json')
# Y200-2/Y200-4 GND chain lost its via: tie Y200-4 to C214-2 (GND, via-connected)
p.seg('F.Cu','GND',0.3,(147.55,76.35),(146.2,76.35),(145.45,75.6))
p.save('t/planU24.json')
# HA8 compensation: R209 0.02 mm north (H2-R209 was 0.399 of 0.4 mm)
p.move('R209',152.95,91.93,90)
p.save('t/planU24.json')
