"""flatpak: route_r6d_islands.py BOARD : vias of other non-GND nets inside non-GND In2 island outlines, and non-power tracks on In2"""
import sys, pcbnew
b=pcbnew.LoadBoard(sys.argv[1]); MM=1e6
isl=[z for z in b.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.In2_Cu) and str(z.GetNetname()) not in ('GND','')]
n=0
for v in b.GetTracks():
    if v.GetClass()!='PCB_VIA': continue
    vn=str(v.GetNetname())
    if vn=='GND': continue
    for z in isl:
        if str(z.GetNetname())!=vn and z.Outline().Collide(v.GetPosition(), int(v.GetWidth(pcbnew.F_Cu)/2)):
            n+=1; print('via in island', z.GetZoneName(), vn, round(v.GetX()/MM,2), round(v.GetY()/MM,2))
print('foreign non-GND vias in In2 islands:', n)
