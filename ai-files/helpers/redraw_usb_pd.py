#!/usr/bin/env python3
"""Rebuild the USB PD sheet from its existing instances and pin mapping."""
from __future__ import annotations

import copy
import pathlib
import sys
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'vendor'))
from sexpdata import Symbol, dumps, load

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCH = ROOT / 'DesktopSpeaker-kicad/USB_PD.kicad_sch'
MOS = ROOT / 'DesktopSpeaker-kicad/kicad-library/schematic/STL9P3LLH6.kicad_sym'
FET = pathlib.Path('/home/chithi/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Symbols/x86_64/beta/active/files/symbols/Transistor_FET.kicad_sym')
POWER = pathlib.Path('/home/chithi/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Symbols/x86_64/beta/active/files/symbols/power.kicad_sym')

S = Symbol
def kind(x): return str(x[0]) if isinstance(x, list) and x else ''
def allof(x, name): return [v for v in x if kind(v) == name]
def one(x, name): return allof(x, name)[0]
def uid(): return str(uuid.uuid4())
def A(x, y, angle=0): return [S('at'), round(x, 4), round(y, 4), angle]
def xy(x, y): return [S('xy'), round(x, 4), round(y, 4)]

sch = load(open(SCH))
lib = one(sch, 'lib_symbols')
instances = {one(v, 'property')[2]: v for v in allof(sch, 'symbol')}
for embedded in list(allof(lib, 'symbol')):
    if embedded[1] == 'power:GND': lib.remove(embedded)

# Adopt the installed KiCad 10 PMOS outline (including its body diode),
# with physical pads stacked at their visible S and D terminals.
fetlib = load(open(FET))
standard = next(v for v in allof(fetlib, 'symbol') if v[1] == 'Q_PMOS_GSD')
oldlib = next(v for v in allof(lib, 'symbol') if v[1] == 'STL9P3LLH6:STL9P3LLH6')
graphic = copy.deepcopy(one(standard, 'symbol'))
graphic[1] = 'STL9P3LLH6_0_1'
terminals = copy.deepcopy(allof(standard, 'symbol')[1])
terminals[1] = 'STL9P3LLH6_1_1'
pins = allof(terminals, 'pin')
pins[0][1] = S('input')
one(pins[0], 'number')[1] = '4'
one(pins[1], 'number')[1] = '[1-3]'
one(pins[2], 'number')[1] = '[5-8]'
for sub in list(allof(oldlib, 'symbol')):
    oldlib.remove(sub)
oldlib.extend((graphic, terminals))

# The library file stays a single component and carries the same footprint,
# model and supplier fields as the original symbol.
moslib = load(open(MOS))
standalone = one(moslib, 'symbol')
for sub in list(allof(standalone, 'symbol')):
    standalone.remove(sub)
standalone.extend((copy.deepcopy(graphic), copy.deepcopy(terminals)))

# Standard KiCad ground symbol from the installed library.
powerlib = load(open(POWER))
gndlib = copy.deepcopy(next(v for v in allof(powerlib, 'symbol') if v[1] == 'GND'))
gndlib[1] = 'power:GND'
lib.append(gndlib)

def move(ref, x, y, angle=0, mirror=None, prop_above=7.62):
    inst = instances[ref]
    at = one(inst, 'at')
    ox, oy = at[1:3]
    at[1:] = [x, y, angle]
    for p in allof(inst, 'property'):
        pa = one(p, 'at')
        if p[1] == 'Reference': pa[1:] = [x, round(y-prop_above, 4), 0]
        elif p[1] == 'Value': pa[1:] = [x, round(y-prop_above+2.54, 4), 0]
        else:
            pa[1] = round(pa[1] + x - ox, 4)
            pa[2] = round(pa[2] + y - oy, 4)
            pa[3] = 0
    for old_mirror in list(allof(inst, 'mirror')): inst.remove(old_mirror)
    if mirror:
        inst.insert(4, [S('mirror'), S(mirror)])
    return inst

positions = {
    'U11': (151.13, 190.5, 0, None, 33.02),
    'Q1': (226.06, 78.74, 0, None, 12.7),
    'Q2': (281.94, 78.74, 0, 'y', 12.7),
    'R1': (82.55, 91.44, 0, None, 7.62),
    'D4': (111.76, 97.79, 0, None, 8.89),
    'C4': (64.77, 116.84, 0, None, 8.89),
    'R4': (128.27, 116.84, 0, None, 8.89),
    'R10': (246.38, 113.03, 0, None, 7.62),
    'R11': (270.51, 143.51, 0, None, 7.62),
    'R13': (316.23, 135.89, 0, None, 8.89),
    'C10': (340.36, 143.51, 0, None, 8.89),
    'R2': (363.22, 172.72, 0, None, 7.62),
    'R55': (96.52, 218.44, 0, None, 8.89),
    'C3': (210.82, 160.02, 0, None, 8.89),
    'C1': (210.82, 210.82, 0, None, 8.89),
    'C2': (219.71, 226.06, 0, None, 8.89),
    'C5': (242.57, 226.06, 0, None, 8.89),
    'C6': (265.43, 226.06, 0, None, 8.89),
    'R6': (285.75, 218.44, 0, None, 8.89),
    'R9': (306.07, 218.44, 0, None, 8.89),
    'J4': (350.52, 228.6, 0, None, 10.16),
    '#FLG01': (78.74, 39.37, 0, None, 6.35),
    '#FLG02': (44.45, 63.5, 0, None, 6.35),
}
for ref, args in positions.items(): move(ref, *args)

# KiCad 10 native pin stacks are single pins whose numbers are bracketed
# ranges. Keep each placed MOS pin UUID associated with the corresponding
# visible gate, source or drain terminal.
for ref in ('Q1', 'Q2'):
    inst = instances[ref]
    for p in list(allof(inst, 'pin')):
        if p[1] in ('2', '3', '6', '7', '8'): inst.remove(p)
        elif p[1] == '1': p[1] = '[1-3]'
        elif p[1] == '5': p[1] = '[5-8]'

# Move the seven original intentional no-connect marks with U11.
old_u = (139.7, 144.78)
new_u = (151.13, 190.5)
no_connects = allof(sch, 'no_connect')
for n in no_connects:
    at = one(n, 'at')
    if at[1] in (119.38, 139.7, 160.02):
        at[1] = round(at[1] + new_u[0] - old_u[0], 4)
        at[2] = round(at[2] + new_u[1] - old_u[1], 4)

# Keep only reusable project metadata, embedded symbols, moved instances,
# no-connects and fixed hierarchy port objects. Rebuild all graphic wiring.
discard = {'wire', 'label', 'junction', 'text'}
sch[:] = [v for v in sch if kind(v) not in discard and not (kind(v) == 'symbol' and one(v,'lib_id')[1] == 'power:GND')]

def add(expr): sch.insert(-2, expr)
def wire(a, b):
    if a == b: return
    if a[0] != b[0] and a[1] != b[1]: raise ValueError(('diagonal', a, b))
    add([S('wire'), [S('pts'), xy(*a), xy(*b)], [S('stroke'), [S('width'), 0], [S('type'), S('default')]], [S('uuid'), uid()]])
def path(*pts):
    for a, b in zip(pts, pts[1:]): wire(a,b)
def junc(x,y): add([S('junction'), A(x,y)[:3], [S('diameter'),0], [S('color'),0,0,0,0], [S('uuid'),uid()]])
def label(name,x,y,justify='left'):
    add([S('label'),name,A(x,y),[S('effects'),[S('font'),[S('size'),1.0,1.0]],[S('justify'),S(justify),S('bottom')]],[S('uuid'),uid()]])
def note(content,x,y,size=1.25):
    add([S('text'),content,A(x,y),[S('effects'),[S('font'),[S('size'),size,size]],[S('justify'),S('left'),S('bottom')]],[S('uuid'),uid()]])
def ground(x,y,angle=0):
    n = sum(1 for v in allof(sch,'symbol') if one(v,'lib_id')[1]=='power:GND') + 1
    ref = f'#PWR{n:02d}'
    u=uid()
    original=instances['U11']
    instance_path=copy.deepcopy(one(original,'instances'))
    one(one(one(instance_path,'project'),'path'),'reference')[1]=ref
    add([S('symbol'),[S('lib_id'),'power:GND'],A(x,y,angle),[S('unit'),1],[S('exclude_from_sim'),S('no')],[S('in_bom'),S('no')],[S('on_board'),S('no')],[S('dnp'),S('no')],[S('uuid'),u],
         [S('property'),'Reference',ref,A(x,y+3.81),[S('effects'),[S('font'),[S('size'),1.27,1.27]],[S('hide'),S('yes')]]],
         [S('property'),'Value','GND',A(x,y+5.08),[S('effects'),[S('font'),[S('size'),1.27,1.27]]]],
         [S('pin'),'1',[S('uuid'),uid()]],instance_path])

# Fixed ports. Input VBUS is a single readable rail across the upper sheet.
path((35.56,39.37),(78.74,39.37),(228.6,39.37),(228.6,73.66))
path((279.4,73.66),(279.4,39.37),(350.52,39.37),(389.89,39.37))
junc(78.74,39.37); junc(350.52,39.37)
path((35.56,63.5),(44.45,63.5)); ground(44.45,63.5)

# Controller CC pins, using the port names directly and short local branches.
path((35.56,48.26),(58.42,48.26),(58.42,177.8),(119.38,177.8),(130.81,177.8))
path((119.38,177.8),(119.38,180.34),(130.81,180.34)); junc(119.38,177.8)
path((35.56,55.88),(52.07,55.88),(52.07,185.42),(121.92,185.42),(130.81,185.42))
path((121.92,185.42),(121.92,187.96),(130.81,187.96)); junc(121.92,185.42)

# Fast VBUS sense: R1 and D4 feed C4/R4. Diode pad 2 is raw VBUS;
# pad 1 is the filtered node.
path((78.74,39.37),(78.74,78.74),(82.55,78.74),(82.55,87.63))
path((115.57,39.37),(115.57,97.79))
junc(115.57,39.37)
path((82.55,95.25),(82.55,105.41),(99.06,105.41),(128.27,105.41),(128.27,113.03))
path((107.95,97.79),(99.06,97.79),(99.06,105.41))
path((64.77,113.03),(64.77,105.41),(82.55,105.41))
junc(82.55,105.41); junc(99.06,105.41)
path((64.77,120.65),(64.77,125.73)); ground(64.77,125.73)
path((128.27,120.65),(128.27,129.54)); label('VBUS_VS_DISCH',128.27,129.54)

# Common-source reverse-current-blocking pair. Mirrored Q2 places both
# gate terminals on the outside of the power path.
path((228.6,83.82),(228.6,101.6),(246.38,101.6),(279.4,101.6),(279.4,83.82))
junc(246.38,101.6)
path((220.98,78.74),(213.36,78.74),(213.36,123.19),(246.38,123.19),(270.51,123.19),(287.02,123.19),(316.23,123.19),(316.23,132.08))
path((287.02,78.74),(287.02,123.19))
path((246.38,101.6),(246.38,109.22))
path((246.38,116.84),(246.38,123.19))
path((270.51,123.19),(270.51,139.7))
path((270.51,147.32),(270.51,153.67)); label('VBUS_EN_SNK',270.51,153.67)
path((316.23,139.7),(340.36,139.7))
path((340.36,147.32),(350.52,147.32),(350.52,39.37))
for pt in ((246.38,123.19),(270.51,123.19),(287.02,123.19),(350.52,147.32)):
    junc(*pt)

# System-side controlled discharge resistor.
path((350.52,39.37),(350.52,163.83),(363.22,163.83),(363.22,168.91))
path((363.22,176.53),(363.22,185.42)); label('DISCH',363.22,185.42)
junc(350.52,163.83)

# Controller local grounds, address and VSYS. Bring EP out above the body
# then terminate it at a downward-pointing ground beside the reference text.
path((151.13,172.72),(151.13,163.83),(173.99,163.83),(173.99,165.1)); ground(173.99,165.1)
for px,py,gx,gy in ((130.81,200.66,125.73,200.66),(130.81,205.74,125.73,205.74),
                    (171.45,205.74,177.8,205.74),(171.45,182.88,177.8,182.88)):
    path((px,py),(gx,gy)); ground(gx,gy)

# Reset pulldown and local digital interface labels.
path((130.81,190.5),(104.14,190.5),(104.14,210.82),(96.52,210.82),(96.52,214.63))
path((96.52,222.25),(96.52,228.6)); ground(96.52,228.6)
for net, yy in (('PD_SCL',193.04),('PD_SDA',195.58),('DISCH',198.12)):
    path((130.81,yy),(115.57,yy)); label(net,115.57,yy,'right')
for net, yy in (('USB_VBUS',177.8),('VBUS_VS_DISCH',193.04),('VBUS_EN_SNK',198.12)):
    path((171.45,yy),(181.61,yy)); label(net,181.61,yy)

# Regulator capacitors beside their controller pins.
path((171.45,180.34),(185.42,180.34),(185.42,156.21),(210.82,156.21))
path((210.82,163.83),(210.82,170.18)); ground(210.82,170.18)
path((171.45,185.42),(194.31,185.42),(194.31,207.01),(210.82,207.01))
path((210.82,214.63),(210.82,219.71)); ground(210.82,219.71)

# VDD bulk/high-frequency caps share one compact power bus.
path((219.71,222.25),(219.71,215.9),(242.57,215.9),(265.43,215.9),(265.43,222.25))
path((242.57,215.9),(242.57,222.25))
label('USB_VBUS',219.71,215.9)
junc(242.57,215.9)
for xx in (219.71,242.57,265.43):
    path((xx,229.87),(xx,234.95)); ground(xx,234.95)

# External 3.3 V programming supply, two pullups and header: one contiguous
# network for each I2C signal and the service supply.
path((285.75,214.63),(285.75,205.74),(306.07,205.74),(322.58,205.74),(322.58,226.06),(345.44,226.06))
path((306.07,205.74),(306.07,214.63))
path((306.07,222.25),(306.07,228.6),(345.44,228.6))
path((285.75,222.25),(285.75,231.14),(345.44,231.14))
path((345.44,233.68),(336.55,233.68)); ground(336.55,233.68)
label('PD_SERVICE_VIO',322.58,205.74)
label('PD_SCL',309.88,228.6)
label('PD_SDA',289.56,231.14)
junc(306.07,205.74)

note('USB-C INPUT / VBUS SENSE',39.37,31.75,1.65)
note('COMMON-SOURCE REVERSE-BLOCKING PMOS SWITCH',205.74,31.75,1.65)
note('PD CONTROLLER',115.57,145.415,1.55)
note('LOCAL REGULATOR AND VDD DECOUPLING',200.66,247.65,1.4)
note('USB-PRESENT I2C SERVICE',280.67,194.945,1.4)
note('Program and read back a 5 V / 9 V-only NVM profile before hardware use. Disable the factory 15 V and 20 V PDOs.',39.37,277.495,1.1)
note('J4 uses external 3.3 V logic power; disconnect the programmer when USB VBUS is absent.',280.67,245.11,1.0)

# One top-level expression per line keeps diffs usable while avoiding a
# formatter dependency. KiCad rewrites this in its normal pretty format.
def save(expr,path):
    path.write_text('(' + ' '.join(dumps(v) for v in expr[:1]) + '\n' + '\n'.join(dumps(v) for v in expr[1:]) + ')\n')
save(sch,SCH)
save(moslib,MOS)
