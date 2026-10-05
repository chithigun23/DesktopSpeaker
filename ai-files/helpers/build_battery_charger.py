#!/usr/bin/env python3
"""Build the BQ25895 charger child from the original U4 symbol instance.

The main-sheet owner moves U4 out of the root when integrating this sheet.
"""
from __future__ import annotations

import copy
import pathlib
import sys
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'vendor'))
from sexpdata import Symbol, dumps, load

S = Symbol
ROOT = pathlib.Path(__file__).resolve().parents[2]
SCH = ROOT / 'DesktopSpeaker-kicad/Battery_Charger.kicad_sch'
PARENT = ROOT / 'DesktopSpeaker-kicad/DesktopSpeaker.kicad_sch'
PD = ROOT / 'DesktopSpeaker-kicad/USB_PD.kicad_sch'
STD = pathlib.Path('/home/chithi/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Symbols/x86_64/beta/active/files/symbols')
SHEET_UUID = 'a7066d55-4393-49f1-9dcb-c2e9f1db9549'
ROOT_UUID = 'feda53ed-537d-4f88-9436-c6075776255b'
PROJ_PATH = f'/{ROOT_UUID}/{SHEET_UUID}'

def kind(x): return str(x[0]) if isinstance(x, list) and x else ''
def allof(x, name): return [v for v in x if kind(v) == name]
def one(x, name): return allof(x, name)[0]
def uid(): return str(uuid.uuid4())
def at(x, y, angle=0): return [S('at'), round(x, 4), round(y, 4), angle]
def xy(x, y): return [S('xy'), round(x, 4), round(y, 4)]
def eff(size=1.0, justify=None, hide=False):
    e=[S('effects'),[S('font'),[S('size'),size,size]]]
    if justify: e.append([S('justify'),S(justify)])
    if hide: e.append([S('hide'),S('yes')])
    return e

root=load(open(PARENT))
pd=load(open(PD))
source=root
if not any(one(v,'property')[2]=='U4' for v in allof(root,'symbol')):
    source=load(open(SCH))
u4=copy.deepcopy(next(v for v in allof(source,'symbol') if one(v,'property')[2]=='U4'))
u4lib=copy.deepcopy(next(v for v in allof(one(source,'lib_symbols'),'symbol') if v[1]=='BQ25895RTWR:BQ25895RTWR'))
base=pd[:7]
sch=[copy.deepcopy(v) for v in base if kind(v) not in ('lib_symbols','title_block','uuid')]
sch.insert(4,[S('uuid'),uid()])
sch.insert(6,[S('title_block'),[S('title'),'BQ25895 charger and 1S battery power path'],[S('rev'),'0.1']])
lib=[S('lib_symbols'),u4lib]
sch.append(lib)

def stdsym(filename, name, library):
    d=load(open(STD/filename))
    obj=copy.deepcopy(next(v for v in allof(d,'symbol') if v[1]==name))
    obj[1]=f'{library}:{name}'
    lib.append(obj)
    return obj

for n in ('PD_R:PD_R','PD_C:PD_C'):
    lib.append(copy.deepcopy(next(v for v in allof(one(pd,'lib_symbols'),'symbol') if v[1]==n)))
stdsym('Device.kicad_sym','L','Device')
stdsym('Connector_Generic.kicad_sym','Conn_01x03','Connector_Generic')
qfile=load(open(ROOT/'DesktopSpeaker-kicad/kicad-library/schematic/2N7002.kicad_sym'))
qdef=copy.deepcopy(one(qfile,'symbol'));qdef[1]='2N7002:2N7002';lib.append(qdef)
gndlib=stdsym('power.kicad_sym','GND','power')

def add(v): sch.append(v); return v
def path(*pts):
    for a,b in zip(pts,pts[1:]):
        if a==b: continue
        assert a[0]==b[0] or a[1]==b[1],(a,b)
        add([S('wire'),[S('pts'),xy(*a),xy(*b)],[S('stroke'),[S('width'),0],[S('type'),S('default')]], [S('uuid'),uid()]])
def junction(x,y): add([S('junction'),at(x,y)[:3],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),uid()]])
def label(name,x,y,justify='left'):
    add([S('label'),name,at(x,y),[S('effects'),[S('font'),[S('size'),1.0,1.0]],[S('justify'),S(justify),S('bottom')]],[S('uuid'),uid()]])
def port(name,x,y,shape='input',side='left'):
    add([S('hierarchical_label'),name,[S('shape'),S(shape)],at(x,y),[S('effects'),[S('font'),[S('size'),1.0,1.0]],[S('justify'),S(side),S('bottom')]],[S('uuid'),uid()]])
def note(txt,x,y,size=1.27):
    add([S('text'),txt,at(x,y),[S('effects'),[S('font'),[S('size'),size,size]],[S('justify'),S('left'),S('bottom')]],[S('uuid'),uid()]])
def nc(x,y): add([S('no_connect'),at(x,y)[:3],[S('uuid'),uid()]])

def instance(lid,ref,value,x,y,angle=0,footprint='',right=False,ic=False):
    inst=[S('symbol'),[S('lib_id'),lid],at(x,y,angle),[S('unit'),1],[S('exclude_from_sim'),S('no')],
          [S('in_bom'),S('no' if ref.startswith('#') else 'yes')],[S('on_board'),S('no' if ref.startswith('#') else 'yes')],
          [S('dnp'),S('no')],[S('uuid'),uid()]]
    offset=8.89 if ref.startswith('Q') else 5.08
    if ref=='L1':
        rpos=at(x+8.89,y-3.81,90);vpos=at(x+8.89,y-1.27,90)
    else:
        rpos=at(x+offset,y-1.27);vpos=at(x+offset,y+1.27)
    inst += [[S('property'),'Reference',ref,rpos,eff(1.27,'left',ref.startswith('#'))],
             [S('property'),'Value',value,vpos,eff(1.27,'left')],
             [S('property'),'Footprint',footprint,at(x,y),eff(hide=True)]]
    source=next(v for v in lib[1:] if v[1]==lid)
    for sub in allof(source,'symbol'):
        for p in allof(sub,'pin'):
            inst.append([S('pin'),one(p,'number')[1],[S('uuid'),uid()]])
    inst.append([S('instances'),[S('project'),'DesktopSpeaker',[S('path'),PROJ_PATH,[S('reference'),ref],[S('unit'),1]]]])
    return add(inst)

def gnd(x,y,hide_value=False):
    idx=1+sum(1 for v in allof(sch,'symbol') if one(v,'lib_id')[1]=='power:GND')
    obj=instance('power:GND',f'#PWR2{idx:02d}','GND',x,y)
    if hide_value:
        one(next(p for p in allof(obj,'property') if p[1]=='Value'),'effects').append([S('hide'),S('yes')])

def passive(kind,ref,value,x,y,footprint):
    return instance(f'PD_{kind}:PD_{kind}',ref,value,x,y,footprint=footprint,right=True)

# U4 keeps its original reference, value, UUID, location, and purchasing fields.
one(one(one(u4,'instances'),'project'),'path')[1]=PROJ_PATH
# Its original identifiers collided with the bottom pin fanout; relocate only
# the two displayed text fields, keeping the body at its original coordinate.
for p in allof(u4,'property'):
    if p[1]=='Reference': one(p,'at')[1:]=[219.1,226.06,0]
    if p[1]=='Value': one(p,'at')[1:]=[219.1,228.6,0]
add(u4)

# Power input, regulated system path and charger local capacitors.
port('VBUS_PD',35.56,100.33)
path((35.56,100.33),(148.59,100.33),(175.26,100.33),(175.26,177.48),(197.51,177.48))
passive('C','C100','2.2uF / 25V',148.59,122.555,'DesktopSpeaker:PD_C_0805')
path((148.59,100.33),(148.59,118.745))
path((148.59,126.365),(148.59,132.08));gnd(148.59,132.08);junction(148.59,100.33)

passive('C','C101','22uF / 25V',190.5,122.555,'DesktopSpeaker:PD_C_1210')
path((215.29,162.24),(215.29,100.33),(190.5,100.33),(190.5,118.745))
path((190.5,126.365),(190.5,132.08));gnd(190.5,132.08)
note('VBUS 3.9-14 V; PMID >=8.2uF effective (OTG unused)',42,85.09,1.15)

passive('C','C102','10uF / 10V',156.21,145.415,'DesktopSpeaker:PD_C_0805')
path((156.21,141.605),(156.21,137.16));label('REGN',156.21,137.16)
path((156.21,149.225),(156.21,154.94));gnd(156.21,154.94)
path((217.83,162.24),(217.83,143.51));label('REGN',217.83,143.51)

# Bootstrap 47 nF from BTST to SW; both SW pads feed the power inductor.
passive('C','C103','47nF / 25V',247.65,140.97,'DesktopSpeaker:PD_C_0603')
path((220.37,162.24),(220.37,146.05),(236.22,146.05),(236.22,137.16),(247.65,137.16))
path((247.65,144.78),(247.65,153.67),(233.68,153.67),(233.68,162.24))
path((222.91,162.24),(225.45,162.24),(233.68,162.24),(260.35,162.24),(260.35,121.92),(281.94,121.92))
junction(225.45,162.24);junction(233.68,162.24)
instance('Device:L','L1','2.2uH',285.75,121.92,angle=90,footprint='')
path((289.56,121.92),(309.88,121.92),(335.28,121.92),(389.89,121.92))
junction(309.88,121.92);junction(335.28,121.92)
port('SYS_RAW',389.89,121.92,'output','right')
for ref,x in (('C104',309.88),('C105',335.28)):
    passive('C',ref,'22uF / 10V',x,143.51,'DesktopSpeaker:PD_C_0805')
    path((x,121.92),(x,139.7));path((x,147.32),(x,154.94));gnd(x,154.94)

# Two SYS, two BAT, and two PGND pads retain separate physical endpoints.
path((240.69,182.56),(264.16,182.56),(264.16,185.1),(240.69,185.1))
path((264.16,185.1),(276.86,185.1));label('SYS_RAW',276.86,185.1)
junction(264.16,185.1)
path((240.69,177.48),(252.73,177.48),(252.73,180.02),(240.69,180.02))
path((252.73,180.02),(257.81,180.02));gnd(257.81,180.02);junction(252.73,180.02)
path((240.69,195.26),(252.73,195.26));gnd(252.73,195.26)

path((240.69,187.64),(271.78,187.64),(271.78,190.18),(240.69,190.18))
path((271.78,190.18),(309.88,190.18),(335.28,190.18))
junction(271.78,190.18);junction(309.88,190.18)
passive('C','C106','22uF / 10V',309.88,209.23,'DesktopSpeaker:PD_C_0805')
path((309.88,190.18),(309.88,205.42));path((309.88,213.04),(309.88,218.44));gnd(309.88,218.44)
port('BAT_PACK',389.89,173.99,'bidirectional','right')
path((335.28,190.18),(335.28,173.99),(389.89,173.99));junction(335.28,190.18)

# Provisional three-contact protected 1S battery pack: +, 103AT-2 NTC, -.
instance('Connector_Generic:Conn_01x03','J5','1S_PACK_3PIN',355.6,198.12,footprint='DesktopSpeaker:JST_B3P_VH_1x03_P3.96mm_Vertical')
path((335.28,190.18),(335.28,195.58),(350.52,195.58))
path((350.52,198.12),(342.9,198.12));label('TS_SENSE',342.9,198.12,'right')
path((350.52,200.66),(342.9,200.66),(342.9,215.9));gnd(342.9,215.9)
note('J5: protected 1S pack + / 103AT-2 NTC / -; key and rating pending',320,223.52,1.0)

# REGN-to-TS divider with the specified 103AT-2 NTC in the pack.
passive('R','R100','5.23k',283.21,210.82,'DesktopSpeaker:PD_R_0603')
passive('R','R101','30.1k',309.88,232.41,'DesktopSpeaker:PD_R_0603')
path((283.21,207.01),(283.21,201.93));label('REGN',283.21,201.93)
path((283.21,214.63),(283.21,220.98),(309.88,220.98),(335.28,220.98))
path((309.88,220.98),(309.88,228.60));junction(309.88,220.98)
path((309.88,236.22),(309.88,242.57));gnd(309.88,242.57)
label('TS_SENSE',335.28,220.98)
path((222.91,205.42),(222.91,201.93),(236.22,201.93));label('TS_SENSE',236.22,201.93)

# Hard current ceiling: 220 ohm gives ~1.45–1.77 A over the specified
# 320–390 A*ohm ILIM coefficient. Firmware sets a lower source-aware IINLIM.
passive('R','R102','220R',255.27,240.03,'DesktopSpeaker:PD_R_0603')
path((220.37,205.42),(220.37,219.71),(246.38,219.71));label('ILIM_CTL',246.38,219.71)
path((255.27,236.22),(255.27,231.14));label('ILIM_CTL',255.27,231.14)
path((255.27,243.84),(255.27,248.92));gnd(255.27,248.92)

# Keep boost disabled and charging off at reset. A 2N7002 separates the
# REGN pulled /CE node from the 3 V MCU domain.
path((215.29,205.42),(215.29,210.82));gnd(215.29,210.82,hide_value=True)
passive('R','R103','10k',181.61,207.01,'DesktopSpeaker:PD_R_0603')
path((181.61,203.2),(181.61,198.12));label('REGN',181.61,198.12)
path((181.61,210.82),(181.61,217.17),(217.83,217.17),(217.83,205.42))
instance('2N7002:2N7002','Q100','2N7002',173.99,232.41,
         footprint='DesktopSpeaker:2N7002',right=True)
path((176.53,227.33),(176.53,217.17),(181.61,217.17));junction(181.61,217.17)
path((176.53,237.49),(176.53,242.57));gnd(176.53,242.57)
port('CHG_ENABLE',35.56,232.41,'input')
path((35.56,232.41),(142.24,232.41),(168.91,232.41));junction(142.24,232.41)
passive('R','R107','100k',142.24,246.38,'DesktopSpeaker:PD_R_0603')
path((142.24,232.41),(142.24,242.57))
path((142.24,250.19),(142.24,256.54));gnd(142.24,256.54)
nc(225.45,205.42) # QON internal pull-up

# Device data pins are isolated from the USB codec's D+/D- pair.
for p in ((197.51,180.02),(197.51,182.56),(212.75,162.24),(197.51,185.10)):
    nc(*p) # D+, D-, DSEL, STAT

port('CHG_SCL',35.56,187.64,'bidirectional')
port('CHG_SDA',35.56,190.18,'bidirectional')
path((35.56,187.64),(197.51,187.64))
path((35.56,190.18),(197.51,190.18))
path((212.75,205.42),(212.75,212.09),(199.39,212.09));label('CHG_INT',199.39,212.09,'right')
port('CHG_INT',389.89,245.11,'output','right')
path((377.19,245.11),(389.89,245.11));label('CHG_INT',377.19,245.11,'right')

# Supply pull-ups from a future always-on MCU logic domain. The same domain
# must remain live whenever this bus is active, including battery-only mode.
port('CHG_VIO_3V0',35.56,241.3,'input')
path((35.56,241.3),(129.54,241.3),(129.54,251.46))
passive('R','R106','10k',129.54,255.27,'DesktopSpeaker:PD_R_0603')
path((129.54,259.08),(129.54,265.43));label('CHG_INT',129.54,265.43)
note('Charge disabled until MCU validates pack/source and sets IINLIM, VREG, ICHG, watchdog.',42,60.96,1.1)
note('D+/D- unused; disable AUTO_DPDM. SYS_RAW is not a regulated 5 V rail.',42,67.31,1.1)

add([S('sheet_instances'),[S('path'),'/',[S('page'),'1']]])
add([S('embedded_fonts'),S('no')])

SCH.write_text('('+' '.join(dumps(v) for v in sch[:1])+'\n'+'\n'.join(dumps(v) for v in sch[1:])+')\n')
print(f'Wrote {SCH} with child sheet UUID {SHEET_UUID}')
