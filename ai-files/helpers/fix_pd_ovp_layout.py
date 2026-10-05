#!/usr/bin/env python3
import pathlib,sys,uuid
sys.path.insert(0,'ai-files/vendor')
from sexpdata import load,dumps,Symbol as S
p=pathlib.Path('DesktopSpeaker-kicad/USB_PD.kicad_sch');s=load(open(p))
def k(v):return str(v[0]) if isinstance(v,list) and v else ''
def sub(v,n):return next(x for x in v if k(x)==n)
def wire(a,b):return [S('wire'),[S('pts'),[S('xy'),*a],[S('xy'),*b]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),str(uuid.uuid4())]]
def ends(v):return tuple(tuple(x[1:]) for x in sub(v,'pts')[1:3])
def ref(v):return next((x[2] for x in v if k(x)=='property' and x[1]=='Reference'),None)
# Remove bypass around U18, reconnect discharge branch by a local label.
for v in list(s):
 if k(v)=='wire' and ends(v) in (((350.52,147.32),(350.52,39.37)),((350.52,39.37),(350.52,143.51))):s.remove(v)
s.append(wire((350.52,143.51),(350.52,147.32)))
s.append([S('label'),'VBUS_PD',[S('at'),350.52,143.51,0],[S('effects'),[S('font'),[S('size'),1,1]],[S('justify'),S('right'),S('bottom')]],[S('uuid'),str(uuid.uuid4())]])
# Remove D7 old short wires, move it next to Q1 with dedicated direct source/gate wires.
for v in list(s):
 if k(v)=='wire' and ends(v) in (((260.35,106.68),(260.35,101.6)),((260.35,101.6),(279.4,101.6)),((260.35,114.3),(260.35,123.19))):s.remove(v)
 if k(v)=='junction' and sub(v,'at')[1:3] in ([260.35,101.6],[260.35,123.19]):s.remove(v)
d7=next(v for v in s if k(v)=='symbol' and ref(v)=='D7')
sub(d7,'at')[1]=228.6
for x in d7:
 if k(x)=='property':sub(x,'at')[1]-=31.75
s.extend([wire((228.6,106.68),(228.6,101.6)),wire((228.6,114.3),(228.6,123.19))])
s.extend([[S('junction'),[S('at'),228.6,101.6],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),str(uuid.uuid4())]],[S('junction'),[S('at'),228.6,123.19],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),str(uuid.uuid4())]]])
# IC identifier centered below pad/ground runs.
u=next(v for v in s if k(v)=='symbol' and ref(v)=='U18')
for x in u:
 if k(x)=='property' and x[1]=='Reference':sub(x,'at')[2]=118.11
 if k(x)=='property' and x[1]=='Value':sub(x,'at')[2]=120.65
p.write_text(dumps(s)+'\n')
