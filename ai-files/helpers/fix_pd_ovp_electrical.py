#!/usr/bin/env python3
import copy,pathlib,sys,uuid
sys.path.insert(0,'ai-files/vendor')
from sexpdata import load,dumps,Symbol as S
p=pathlib.Path('DesktopSpeaker-kicad/USB_PD.kicad_sch');s=load(open(p))
def k(v):return str(v[0]) if isinstance(v,list) and v else ''
def sub(v,n):return next(x for x in v if k(x)==n)
def ref(v):return next((x[2] for x in v if k(x)=='property' and x[1]=='Reference'),None)
def ends(v):return tuple(tuple(x[1:]) for x in sub(v,'pts')[1:3])
def wire(a,b):return [S('wire'),[S('pts'),[S('xy'),*a],[S('xy'),*b]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),str(uuid.uuid4())]]
def j(x,y):return [S('junction'),[S('at'),x,y],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),str(uuid.uuid4())]]
def gnd(x,y,name):
 v=copy.deepcopy(next(v for v in s if k(v)=='symbol' and ref(v)=='#PWR23'))
 ox,oy=sub(v,'at')[1:3];sub(v,'at')[1:3]=[x,y];sub(v,'uuid')[1]=str(uuid.uuid4())
 for q in v:
  if k(q)=='property':
   if q[1]=='Reference':q[2]=name
   a=sub(q,'at');a[1]+=x-ox;a[2]+=y-oy
  if k(q)=='pin':sub(q,'uuid')[1]=str(uuid.uuid4())
 sub(v,'instances')[1][2][2][1]=name;s.append(v)
# SHDN uses its specified internal low-voltage pull-up. No raw 21V on this 0-4V pin.
for v in list(s):
 if k(v)=='wire' and ends(v) in (((322.58,63.5),(322.58,78.74)),((322.58,78.74),(328.93,78.74))):s.remove(v)
s.append(wire((322.58,63.5),(322.58,73.66)))
s.append([S('no_connect'),[S('at'),328.93,78.74],[S('uuid'),str(uuid.uuid4())]])
# 1uF 50V local eFuse input capacitor; exact MPN/DC-bias remains a selection item.
c=copy.deepcopy(next(v for v in s if k(v)=='symbol' and ref(v)=='C4'))
oldx,oldy=sub(c,'at')[1:3];newx,newy=293.37,60.96;sub(c,'at')[1:3]=[newx,newy];sub(c,'uuid')[1]=str(uuid.uuid4())
for q in c:
 if k(q)=='property':
  if q[1]=='Reference':q[2]='C180'
  if q[1]=='Value':q[2]='1uF X7R 50V'
  if q[1]=='Datasheet':q[2]=''
  a=sub(q,'at');a[1]+=newx-oldx;a[2]+=newy-oldy
 if k(q)=='pin':sub(q,'uuid')[1]=str(uuid.uuid4())
sub(c,'instances')[1][2][2][1]='C180';s.append(c)
s.extend([wire((293.37,39.37),(293.37,57.15)),wire((293.37,64.77),(293.37,73.66)),j(293.37,39.37)])
gnd(293.37,73.66,'#PWR24')
p.write_text(dumps(s)+'\n')
