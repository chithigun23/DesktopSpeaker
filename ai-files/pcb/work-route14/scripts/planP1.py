import sys; sys.path.insert(0,'scripts')
from mkplan import P
p=P('R0.kicad_pcb')
AO='/3V_AO'
# U3 VDD pins 6-8 joined at the pad tips, pin 8 straight down into C160-1
p.seg('F.Cu',AO,0.25,(126.75,82.85),(127.75,82.85))
p.seg('F.Cu',AO,0.25,(127.75,82.175),(127.75,84.65))
# C160-1 -> C161-1 -> R106-1 (below the PD_PLUG_EVENT and CHG_INT vias)
p.seg('F.Cu',AO,0.3,(127.432,84.65),(127.432,84.85),(126.982,85.3),(125.6,85.3))
p.seg('F.Cu',AO,0.3,(124.9,85.2),(122.4,85.2))
# U3-9 GND straight down into C160-2
p.seg('F.Cu','GND',0.25,(128.25,82.175),(128.25,84.0),(128.567,84.317),(128.567,84.65))
# LDO_3V3: C6/via cluster -> U11-1
p.seg('F.Cu','/USB_PD/LDO_3V3',0.25,(132.03,54.8),(134.2141,54.8))
p.save('t/planP1.json')
for ref,c,v in [('C160-2',(128.5675,84.65),(128.5675,85.35)),('C162-2',(131.7675,84.65),(131.7675,83.95)),('R259-2',(136.0,83.5975),(135.3,83.5975)),
                ('C161-2',(124.9,87.1375),(124.9,86.1875)),('R160-2',(120.1025,70.3),(121.5167,68.8858)),('J7-5',(120.83,63.415),(120.2997,63.9453))]:
    p.seg('F.Cu','GND',0.3,c,v); p.via('GND',v[0],v[1])
p.save('t/planP1.json')
