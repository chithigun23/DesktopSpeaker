import sys, json; sys.path.insert(0,'scripts')
from mkplan import P
p=P('D0.kicad_pcb')
SDA='/CTRL_SDA'; SCL='/CTRL_SCL'; CE='/Battery_Charger/CE_N'
old=json.load(open('t/planD_u4.json'))
for s in old['seg_add']:
    if s[1]==SDA: p.seg_del_at(SDA,*s[3:7])
for v in old['via_add']:
    if v[0]==SDA: p.via_del_at(SDA,v[1],v[2])
# CE_N: straight down from U4-13, then east into R103-2 (frees the column below pin 14)
p.seg_del_at(CE,151.77,124.085,151.77,125.635); p.seg_del_at(CE,151.77,125.635,152.37,126.235)
p.seg('F.Cu',CE,0.2,(151.77,124.085),(151.77,126.38),(152.27,126.38))
# SDA (U4-15) and SCL (U4-14): short stubs to fine vias below the pins
p.seg('F.Cu',SDA,0.2,(152.57,124.085),(152.57,124.6),(152.82,124.85)); p.via(SDA,152.82,124.85,0.5,0.2)
p.seg('F.Cu',SCL,0.2,(152.17,124.085),(152.17,125.22),(152.45,125.5)); p.via(SCL,152.45,125.5,0.5,0.2)
p.save('t/planE1.json')
