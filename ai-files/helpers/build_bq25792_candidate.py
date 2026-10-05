#!/usr/bin/env python3
"""Build an isolated BQ25792 Battery_Charger candidate sheet for review."""
from __future__ import annotations
import copy, pathlib, sys, uuid
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'ai-files/vendor'))
from sexpdata import Symbol as S, load, dumps

SRC = ROOT / 'DesktopSpeaker-kicad/Battery_Charger.kicad_sch'
PART = ROOT / 'ai-files/candidates/BQ25792RQMR.kicad_sym'
OUT = ROOT / 'ai-files/candidates/Battery_Charger.kicad_sch'
SHEET_UUID = 'a7066d55-4393-49f1-9dcb-c2e9f1db9549'
ROOT_UUID = 'feda53ed-537d-4f88-9436-c6075776255b'
PATH = f'/{ROOT_UUID}/{SHEET_UUID}'

def k(x): return str(x[0]) if isinstance(x, list) and x else ''
def allof(x, key): return [v for v in x if k(v) == key]
def one(x, key): return allof(x, key)[0]
def uid(): return str(uuid.uuid4())
def find_prop(obj, name): return next(p for p in allof(obj, 'property') if p[1] == name)
def set_prop(obj, name, value): find_prop(obj, name)[2] = value
def grid(v): return round(round(float(v)/1.27)*1.27,4)
def xy(x,y): return [S('xy'),grid(x),grid(y)]
def at(x,y,a=0): return [S('at'),grid(x),grid(y),a]
def eff(size=1.0, just=None, hide=False):
    e=[S('effects'),[S('font'),[S('size'),size,size]]]
    if just: e.append([S('justify'),S(just)])
    if hide: e.append([S('hide'),S('yes')])
    return e

src=load(open(SRC)); source_lib=one(src,'lib_symbols')
part=load(open(PART)); u4lib=copy.deepcopy(one(part,'symbol')); u4lib[1]='BQ25792RQMR:BQ25792RQMR'
lib_symbols=[S('lib_symbols'),u4lib]
needed=('PD_R:PD_R','PD_C:PD_C','Device:L','Connector_Generic:Conn_01x03',
        '2N7002:2N7002','power:GND','Switch:SW_Push','Switch:SW_SPST')
for name in needed:
    lib_symbols.append(copy.deepcopy(next(v for v in allof(source_lib,'symbol') if v[1]==name)))
ship_part=load(open(ROOT/'ai-files/candidates/CSD17579Q3A.kicad_sym'))
shiplib=copy.deepcopy(one(ship_part,'symbol')); shiplib[1]='CSD17579Q3A:CSD17579Q3A'; lib_symbols.append(shiplib)

sch=[S('kicad_sch'),[S('version'),20260306],[S('generator'),'eeschema'],
     [S('generator_version'),'10.0'],[S('uuid'),uid()],[S('paper'),'A3'],
     [S('title_block'),[S('title'),'BQ25792 1S charger and power path candidate'],[S('rev'),'candidate-0.1']],lib_symbols]
obj_by_ref={find_prop(v,'Reference')[2]:v for v in allof(src,'symbol')}
inst_by_lib={v[1]:v for v in allof(lib_symbols,'symbol')}

def add(v): sch.append(v); return v
def path(*pts):
    for a,b in zip(pts,pts[1:]):
        if a==b: continue
        assert a[0]==b[0] or a[1]==b[1],(a,b)
        add([S('wire'),[S('pts'),xy(*a),xy(*b)],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),uid()]])
def junction(x,y): add([S('junction'),at(x,y)[:3],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),uid()]])
def label(name,x,y,justify='left'):
    add([S('label'),name,at(x,y),[S('effects'),[S('font'),[S('size'),1.0,1.0]],[S('justify'),S(justify),S('bottom')]],[S('uuid'),uid()]])
def port(name,x,y,shape='input',side='left'):
    add([S('hierarchical_label'),name,[S('shape'),S(shape)],at(x,y),[S('effects'),[S('font'),[S('size'),1.0,1.0]],[S('justify'),S(side),S('bottom')]],[S('uuid'),uid()]])
def note(txt,x,y,size=1.0):
    add([S('text'),txt,at(x,y),[S('effects'),[S('font'),[S('size'),size,size]],[S('justify'),S('left'),S('bottom')]],[S('uuid'),uid()]])
def nc(x,y): add([S('no_connect'),at(x,y)[:3],[S('uuid'),uid()]])

def instance_from_template(ref,x,y,angle=0,value=None,footprint=None,newref=None):
    base=copy.deepcopy(obj_by_ref[ref]); oldref=ref
    if newref: ref=newref
    instat=one(base,'at'); instat[1:]=[grid(x),grid(y),angle]
    rootid=one(base,'uuid'); rootid[1]=uid() if newref else rootid[1]
    set_prop(base,'Reference',ref)
    if value is not None: set_prop(base,'Value',value)
    if footprint is not None: set_prop(base,'Footprint',footprint)
    # Place visible identifiers consistently; hidden purchasing fields stay hidden.
    is_ic=ref=='U4'; is_passive=ref[:1] in ('C','R','L')
    for p in allof(base,'property'):
        name=p[1]
        if name=='Reference': p[3]=at(x,y+18.5,0) if is_ic else at(x+5.08 if is_passive else x+8.89,y-1.27,0)
        elif name=='Value': p[3]=at(x, y+21.0, 0) if is_ic else at(x+5.08 if is_passive else x+8.89,y+1.27,0)
        elif name in ('MPN','LCSC Part','LCSC','Manufacturer','Datasheet','Description') and len(p)>3:
            p[3]=at(x,y,0)
    if newref:
        for pp in allof(base,'pin'): pp[2][1]=uid()
        pi=one(one(base,'instances'),'project')
        pth=one(pi,'path'); pth[1]=PATH; one(pth,'reference')[1]=ref
    else:
        pi=one(one(base,'instances'),'project'); pth=one(pi,'path'); pth[1]=PATH; one(pth,'reference')[1]=ref
    return add(base)

def new_cap(ref,value,x,y,template='C103',footprint=None,mpn=None,lcsc=None,angle=0):
    v=instance_from_template(template,x,y,angle,value=value,footprint=footprint or 'DesktopSpeaker:PD_C_0603',newref=ref)
    for key in ('MPN','LCSC Part','LCSC','Manufacturer','Datasheet'):
        for p in allof(v,'property'):
            if p[1]==key: p[2]=mpn if key=='MPN' and mpn else (lcsc if key in ('LCSC Part','LCSC') and lcsc else ('Texas Instruments' if key=='Manufacturer' and mpn else ''))
    return v
def new_res(ref,value,x,y,template='R102',footprint='DesktopSpeaker:PD_R_0603',mpn=None,lcsc=None,angle=0):
    v=instance_from_template(template,x,y,angle,value=value,footprint=footprint,newref=ref)
    for p in allof(v,'property'):
        if p[1]=='MPN': p[2]=mpn or ''
        elif p[1] in ('LCSC','LCSC Part'): p[2]=lcsc or ''
        elif p[1]=='Manufacturer': p[2]='YAGEO' if mpn else ''
        elif p[1]=='Datasheet': p[2]=''
    return v

def make_generic(libid,ref,val,x,y,footprint='',pins=None):
    sym=inst_by_lib[libid]; inst=[S('symbol'),[S('lib_id'),libid],at(x,y),[S('unit'),1],
        [S('exclude_from_sim'),S('no')],[S('in_bom'),S('yes')],[S('on_board'),S('yes')],[S('dnp'),S('no')],[S('uuid'),uid()]]
    is_gnd=ref.startswith('#PWR'); offset=0 if is_gnd else (8.89 if ref.startswith('Q') else 5.08)
    inst += [[S('property'),'Reference',ref,at(x,y+3.81),eff(1.0,None,True) if is_gnd else eff(1.27,'left')],
             [S('property'),'Value',val,at(x,y+5.08) if is_gnd else at(x+offset,y+1.27),eff(1.0,'center') if is_gnd else eff(1.27,'left')],
             [S('property'),'Footprint',footprint,at(x,y),eff(hide=True)]]
    if pins is None:
        for sub in allof(sym,'symbol'):
            for p in allof(sub,'pin'): inst.append([S('pin'),one(p,'number')[1],[S('uuid'),uid()]])
    else:
        inst.extend([[S('pin'),p, [S('uuid'),uid()]] for p in pins])
    inst.append([S('instances'),[S('project'),'DesktopSpeaker',[S('path'),PATH,[S('reference'),ref],[S('unit'),1]]]])
    return add(inst)

gnd_count=0
def gnd(x,y):
    global gnd_count
    gnd_count+=1; ref=f'#PWR{gnd_count:03d}'
    # Power symbols need KiCad's standard no-BOM/no-board instance flags and
    # full property formatting. Clone a valid child-sheet instance instead of
    # synthesizing one; generic yes/yes GND instances fail KiCad 10 loading.
    base=copy.deepcopy(next(v for v in allof(src,'symbol')
                            if find_prop(v,'Reference')[2].startswith('#PWR')))
    one(base,'at')[1:]=[grid(x),grid(y),0]
    one(base,'uuid')[1]=uid()
    set_prop(base,'Reference',ref)
    find_prop(base,'Reference')[3]=at(x+5.08,y-1.27,0)
    find_prop(base,'Value')[3]=at(x,y+5.08,0)
    ve=one(find_prop(base,'Value'),'effects'); ve[:]=[e for e in ve if k(e)!='justify']
    for pin in allof(base,'pin'): one(pin,'uuid')[1]=uid()
    pi=one(one(base,'instances'),'project'); pth=one(pi,'path'); pth[1]=PATH; one(pth,'reference')[1]=ref
    return add(base)
def passive(ref,x,y,value=None,angle=0,footprint=None):
    if ref in obj_by_ref:
        return instance_from_template(ref,x,y,angle,value=value,footprint=footprint)
    if ref.startswith('C'):
        return new_cap(ref,value or '',x,y,angle=angle,footprint=footprint)
    if ref.startswith('R'):
        return new_res(ref,value or '',x,y,angle=angle,footprint=footprint or 'DesktopSpeaker:PD_R_0603')
    raise KeyError(ref)

# Preserve U4 UUID and reference; replace only its device definition/value/footprint/pin instances.
U4_X,U4_Y=229.87,129.54
u4=copy.deepcopy(obj_by_ref['U4']); u4_uuid=one(u4,'uuid')[1]
one(u4,'lib_id')[1]='BQ25792RQMR:BQ25792RQMR'
one(u4,'at')[1:]=[U4_X,U4_Y,0]
set_prop(u4,'Value','BQ25792RQMR'); set_prop(u4,'Footprint','DesktopSpeaker:BQ25792RQMR')
set_prop(u4,'Datasheet','../ai-files/datasheets/BQ25792.pdf')
set_prop(u4,'MPN','BQ25792RQMR'); set_prop(u4,'LCSC Part','C2862876'); set_prop(u4,'Manufacturer','Texas Instruments')
find_prop(u4,'Reference')[3]=at(U4_X,151.0,0); find_prop(u4,'Value')[3]=at(U4_X,153.5,0)
for pin in allof(u4,'pin'): u4.remove(pin)
for sub in allof(u4lib,'symbol'):
    for p in allof(sub,'pin'): u4.append([S('pin'),one(p,'number')[1],[S('uuid'),uid()]])
pi=one(one(u4,'instances'),'project'); pth=one(pi,'path'); pth[1]=PATH
add(u4)

# Pin positions generated from the candidate symbol definition (KiCad local y is inverted on sheet).
pinpos={}
for sub in allof(u4lib,'symbol'):
    for p in allof(sub,'pin'):
        num=one(p,'number')[1]; local=one(p,'at')
        pinpos[str(num)]=(grid(U4_X+float(local[1])),grid(U4_Y-float(local[2])))
def P(n): return pinpos[str(n)]

# Incoming VBUS; single-input topology ties VAC1/2 to VBUS, with ACDRV1/2 grounded.
vbus=P('[2-3]'); port('VBUS_PD',38,93,'input'); path((38,93),(70,93)); label('VBUS_PD',70,93)
path(vbus,(vbus[0],vbus[1]-5.08)); label('VBUS_PD',vbus[0],vbus[1]-5.08)
for n in ('8','9'):
    p=P(n); path(p,(p[0],p[1]-5.08)); label('VBUS_PD',p[0],p[1]-5.08)
for n in ('10','11'):
    p=P(n); path(p,(p[0]+6.35,p[1])); path((p[0]+6.35,p[1]),(p[0]+6.35,p[1]+5.08)); gnd(p[0]+6.35,p[1]+5.08)
nc(*P('1')) # STAT unused; charge state is available on I2C/INT.

# BQ25792 TI single-input bank: 2x10uF VBUS; 3x10uF PMID; 0.1uF at each.
# This is the charger share of the coordinated PD sink capacitance budget, not an added bulk bank.
for ref,x,val in [('C100',115,'10uF / 50V')]:
    passive(ref,x,99,value=val,footprint='DesktopSpeaker:PD_C_1210')
    for p in allof(obj_by_ref[ref],'property'):
        if p[1] in ('MPN','LCSC Part','LCSC','Manufacturer','Datasheet'): p[2]=''
    path((x,95.19),(x,88.9)); label('VBUS_PD',x,88.9); path((x,102.81),(x,110)); gnd(x,110)
new_cap('C111','10uF / 50V',140,99,template='C103',footprint='DesktopSpeaker:PD_C_1210')
path((140,95.19),(140,88.9)); label('VBUS_PD',140,88.9); path((140,102.81),(140,110)); gnd(140,110)
new_cap('C113','0.1uF / 50V',165,99,footprint='DesktopSpeaker:PD_C_0603')
path((165,95.19),(165,88.9)); label('VBUS_PD',165,88.9); path((165,102.81),(165,110)); gnd(165,110)
pmid=P('29')
for ref,x in [('C101',270),('C108',292)]:
    passive(ref,x,99,value='10uF / 35V',footprint='DesktopSpeaker:PD_C_1210')
    for p in allof(obj_by_ref[ref],'property'):
        if p[1] in ('MPN','LCSC Part','LCSC','Manufacturer','Datasheet'): p[2]=''
    path((x,95.19),(x,89.0)); label('PMID',x,89.0); path((x,102.81),(x,110)); gnd(x,110)
new_cap('C112','10uF / 35V',314,99,template='C103',footprint='DesktopSpeaker:PD_C_1210')
path((314,95.19),(314,89.0)); label('PMID',314,89.0); path((314,102.81),(314,110)); gnd(314,110)
new_cap('C114','0.1uF / 50V',336,99,footprint='DesktopSpeaker:PD_C_0603')
path((336,95.19),(336,89.0)); label('PMID',336,89.0); path((336,102.81),(336,110)); gnd(336,110)
path(pmid,(260,pmid[1])); label('PMID',260,pmid[1])

# REGN decoupling and 2-rail bootstraps (C103 retained, C110 added).
regn=P('5')
for ref,x in [('C102',358),('C109',380)]:
    passive(ref,x,99,value='10uF / 10V'); path((x,95.19),(x,89.0)); label('REGN',x,89.0); path((x,102.81),(x,110)); gnd(x,110)
path(regn,(304,regn[1])); label('REGN',304,regn[1])
for n,cap,x in [('4','C103',278),('19','C110',302)]:
    p=P(n); sw=P('28' if n=='4' else '26')
    passive(cap,x,178,value='47nF / 50V',footprint='DesktopSpeaker:PD_C_0603')
    # Discrete local labels avoid crossing the bridge pins/inductor node.
    path(p,(p[0]+3.81,p[1])); label('BTST1' if n=='4' else 'BTST2',p[0]+3.81,p[1])
    path(sw,(sw[0]+3.81,sw[1])); label('SW1' if n=='4' else 'SW2',sw[0]+3.81,sw[1])
    ctop=(x,174.19); cbot=(x,181.81)
    path(ctop,(x,171)); label('BTST1' if n=='4' else 'BTST2',x,171)
    path(cbot,(x,185)); label('SW1' if n=='4' else 'SW2',x,185)

# Two switching nodes and the 2.2uH 750kHz power inductor.
sw1=P('28'); sw2=P('26')
instance_from_template('L1',304,145,angle=90,value='2.2uH',footprint='DesktopSpeaker:SRN6045TA-2R2Y')
path(sw1,(sw1[0]+6.35,sw1[1])); label('SW1',sw1[0]+6.35,sw1[1])
path(sw2,(sw2[0]+6.35,sw2[1])); label('SW2',sw2[0]+6.35,sw2[1])
path((300.19,145),(294,145)); label('SW1',294,145)
path((307.81,145),(314,145)); label('SW2',314,145)

# SYS regulated output rail and decoupling.
sys=P('25'); port('SYS_RAW',390,sys[1],'output','right')
path(sys,(390,sys[1])); label('SYS_RAW',365,sys[1])
for ref,x in [('C104',330),('C105',350),('C107',370)]:
    passive(ref,x,178,value='22uF / 10V'); path((x,174.19),(x,sys[1])); path((x,181.81),(x,188.0)); gnd(x,188.0)
    if ref!='C104': junction(x,sys[1])

# Charger ground and battery-internal rail decoupling. BAT and BAT_PACK remain isolated pending Q103.
g=P('27'); path(g,(g[0],g[1]+5.08)); gnd(g[0],g[1]+5.08)
bat=P('[22-23]'); path(bat,(bat[0]+5.08,bat[1])); label('BAT_INT',bat[0]+5.08,bat[1])
passive('C106',325,211,value='22uF / 10V'); path((325,207.19),(325,201)); label('BAT_INT',325,201); path((325,214.81),(325,221.16)); gnd(325,221.16)
instance_from_template('J5',375,245,value='1S_PACK_3PIN',footprint='DesktopSpeaker:JST_B3P_VH_1x03_P3.96mm_Vertical')
# Pin endpoints of Conn_01x03 at angle 0: pins 1,2,3 are vertically ordered.
j1=(369.92,242.46); j2=(369.92,245.0); j3=(369.92,247.54)
instance_from_template('SW101',360,242.46,value='BAT_DISCONNECT')
path(j1,(365.08,242.46)); label('PACK_RAW',365.08,242.46)
path((354.92,242.46),(320,242.46)); label('BAT_PACK',320,242.46)
path(j2,(365,j2[1])); label('TS_SENSE',365,j2[1])
path(j3,(365,j3[1]),(365,262)); gnd(365,262)
port('BAT_PACK',390,242.46,'bidirectional','right'); path((320,242.46),(390,242.46))

# External electronic ship switch. Pin stack [1-3] is charger-side BAT; [5-9]
# is battery-side pack positive, matching the body-diode direction in TI Fig. 9-14.
make_generic('CSD17579Q3A:CSD17579Q3A','Q103','CSD17579Q3A',330,235,
             'DesktopSpeaker:CSD17579Q3A_DNH0008A',pins=['4','[1-3]','[5-9]'])
set_prop(one(sch[-1],'symbol') if False else sch[-1], 'Footprint', 'DesktopSpeaker:CSD17579Q3A_DNH0008A')
for key,val in [('MPN','CSD17579Q3A'),('LCSC Part','C97376'),('Manufacturer','Texas Instruments'),('Datasheet','https://www.ti.com/lit/ds/symlink/csd17579q3a.pdf')]:
    sch[-1].insert(next(i for i,v in enumerate(sch[-1]) if k(v)=='pin'),[S('property'),key,val,at(330,235),eff(hide=True)])
q103_s=(332.54,240.08); q103_d=(332.54,229.92); q103_g=(324.92,235)
path(q103_s,(320,240.08),(320,242.46)); label('BAT_INT',320,240.08)
path(q103_d,(340,229.92),(340,225)); label('BAT_PACK',340,225)
path(q103_g,(315,235)); label('SDRV',315,235)

# BATP sense is isolated from the external battery terminal by the TI 100-ohm series resistor.
batp=P('18'); path(batp,(batp[0]+5.08,batp[1])); label('BATP_SENSE',batp[0]+5.08,batp[1])
passive('R112',348,212,angle=90,value='100R'); path((344.19,212),(335,212)); label('BAT_PACK',335,212)
path((351.81,212),(356,212)); label('BATP_SENSE',356,212)

# 1S PROG setup; R102 repurposed from the retired old-charger ILIM resistor.
prog=P('20'); passive('R102',164,214,value='4.7k')
for p in allof(obj_by_ref['R102'],'property'):
    if p[1] in ('MPN','LCSC Part','LCSC','Manufacturer','Datasheet'): p[2]=''
path(prog,(prog[0]-14,prog[1]),(150,prog[1]),(150,210.19),(164,210.19)); path((164,217.81),(164,225)); gnd(164,225)

# TS network preserves the pack NTC port plus provisional fixed bias resistors.
ts=P('16'); path(ts,(ts[0]-5.08,ts[1])); label('TS_SENSE',ts[0]-5.08,ts[1])
passive('R100',188,199,value='5.23k'); path((188,195.19),(188,184)); label('REGN',188,184); path((188,202.81),(188,208)); label('TS_SENSE',188,208)
passive('R101',212,236,value='30.1k'); path((212,232.19),(212,227)); label('TS_SENSE',212,227); path((212,239.81),(212,246)); gnd(212,246)

# Default-off SYS converter gate: Q101 clamps ILIM_HIZ low until Q102 is enabled.
# REGN-fed divider is deliberately about 0.8–1.1A across 4.6–5.2V, not a fixed-6V assumption.
ilim=P('17'); path(ilim,(186,ilim[1])); label('ILIM_HIZ',186,ilim[1])
passive('R108',173,180,value='180k'); passive('R109',190,197,value='100k')
path((173,176.19),(173,168),(185,168)); label('REGN',185,168)
path((173,183.81),(173,ilim[1]),(186,ilim[1])); path((190,193.19),(190,ilim[1]),(173,ilim[1])); junction(173,ilim[1]); path((190,200.81),(190,207)); gnd(190,207)
make_generic('2N7002:2N7002','Q101','2N7002',222,215,'DesktopSpeaker:2N7002')
# Q101 drain to ILIM_HIZ, source GND, gate held at REGN through R110 (default clamp ON).
q1gate=(216.92,215); q1drain=(224.54,209.92); q1source=(224.54,220.08)
path(q1drain,(230,209.92),(230,ilim[1]),(186,ilim[1])); path(q1source,(224.54,226)); gnd(224.54,226)
passive('R110',205,203,value='100k'); path((205,199.19),(205,168),(185,168)); label('REGN',185,168); path((205,206.81),(205,215),(216.92,215)); junction(205,215)
make_generic('2N7002:2N7002','Q102','2N7002',257,233,'DesktopSpeaker:2N7002')
q2gate=(251.92,233); q2drain=(259.54,227.92); q2source=(259.54,238.08)
port('CHG_SYS_ENABLE',38,233,'input'); path((38,233),(80,233),q2gate)
path(q2drain,(259.54,215),(216.92,215)); junction(216.92,215); path(q2source,(259.54,244)); gnd(259.54,244)
passive('R111',275,247,value='100k'); path((275,243.19),(275,233),(259.54,233)); junction(259.54,233); path((275,250.81),(275,257)); gnd(275,257)

# CE remains a separate charge-only enable, pulled high at reset and sunk by the preserved Q100.
ce=P('13');
port('CHG_ENABLE',38,230,'input'); path((38,230),(135,230),(167,230)); label('CHG_ENABLE',135,230)
make_generic('2N7002:2N7002','Q100','2N7002',172,244,'DesktopSpeaker:2N7002')
qg=(166.92,244); qd=(174.54,238.92); qs=(174.54,249.08)
path(ce,(ce[0]-10,ce[1]),(ce[0]-10,238.92),(174.54,238.92)); path(qd,(174.54,238.92)); path(qs,(174.54,255)); gnd(174.54,255)
passive('R103',192,228,value='10k'); path((192,224.19),(192,214),(205,214)); label('REGN',205,214); path((192,231.81),(192,238.92),(174.54,238.92)); junction(174.54,238.92)
path((167,230),(qg[0],230),qg)
passive('R107',146,247,value='100k'); path((146,243.19),(146,230)); junction(146,230); path((146,250.81),(146,257)); gnd(146,257)

# Host/control interfaces; D+/D− remain explicit left-side ports for later source-selection muxing.
for n,pn,py in [('CHG_DP_RAW','6',104),('CHG_DM_RAW','7',109),('CHG_SCL','14',154),('CHG_SDA','15',159)]:
    p=P(pn); port(n,38,py,'bidirectional' if 'SCL' in n or 'SDA' in n else 'input'); path((38,py),(185,py),(185,p[1]),p)
for n,pn in [('CHG_INT','21')]:
    p=P(pn); path(p,(p[0]-7.62,p[1])); label(n,p[0]-7.62,p[1])
port('CHG_INT',390,209,'output','right'); path((382.38,209),(390,209)); label('CHG_INT',382.38,209)
vio=(175,195); port('CHG_VIO_3V0',*vio,'input'); passive('R106',190,222,value='10k')
path((190,218.19),(190,195),(175,195)); path((190,225.81),(190,233)); label('CHG_INT',190,233)

# Keep the QON button, separate mechanical pack switch, and open notes reviewable.
qon=P('12');
make_generic('Switch:SW_Push','SW100','WAKE_QON',298,214,'')
path(qon,(270,qon[1]),(270,214),(292.92,214)); path((303.08,214),(311,214)); gnd(311,214)

note('1S Li-ion; PROG 4.7k = 750kHz. Charge target 1A is firmware-only; POR 2A must remain disabled.',34,42,1.15)
note('ILIM_HIZ low keeps switching off; POR sample below1.08V caches100mA. EN_EXTILIM/watchdog policy unresolved.',34,48,1.0)
note('Do not release CHG_SYS_ENABLE before source-specific IINDPM. Prove REG_RST/watchdog behavior in firmware.',34,53,1.0)
note('DP/DM left ports require a source-selection mux; do not tie to codec. SYS_RAW is variable NVDC, not 5V.',34,58,1.0)
note('L1 2.2uH/6A is provisional: total SYS + charge current and ripple need product-load/thermal review.',34,63,1.0)
note('Pack and 10k NTC profile pending. QON wake defaults to ~1s low (15ms if configured); verify button hold.',34,68,1.0)
note('TPS2116 SYS max5.5V; 1S default4.27–4.55V at BAT4.2; SYSMIN 3.5–4.1V; qualify SYSOVP/transients.',34,73,1.0)
note('PMID follows high input path: 35V caps shown; verify effective capacitance, derating and surge.',274,84,1.0)
note('50uF nominal BQ bank counts in PD bulk budget; keep shared nominal bank <=100uF.',274,89,1.0)

# Tighten the functional grouping around U4 before laying wires.
positions={'C101':(268,96),'C108':(288,96),'C112':(308,96),'C114':(328,96),
 'C102':(228,96),'C109':(246,96),'C103':(260,119.38),'C110':(260,124.46),
 'L1':(286,124),'C104':(286,165),'C105':(307,165),'C107':(328,165),'C106':(258,166),
 'Q103':(267,145),'R112':(300,195),'J5':(365,189.23),'SW101':(345,186.69),'SW100':(258,190),
 'R102':(160,165),'R100':(167,178),'R101':(185,178),'R108':(165,145),'R109':(181,156),
 'R110':(198,156),'Q101':(213,166),'Q102':(240,180),'R111':(256,186),
 'Q100':(145,185),'R103':(162,190),'R107':(130,195),'R106':(185,197)}
for ref,(nx,ny) in positions.items():
    inst=getinst(ref) if 'getinst' in globals() else next(v for v in allof(sch,'symbol') if find_prop(v,'Reference')[2]==ref)
    old=one(inst,'at'); dx,dy=grid(nx)-float(old[1]),grid(ny)-float(old[2]); old[1:]=[grid(nx),grid(ny),90 if ref in ('C103','C110') else old[3]]
    for prop in allof(inst,'property'):
        atp=allof(prop,'at')
        if atp: atp[0][1:]=[grid(float(atp[0][1])+dx),grid(float(atp[0][2])+dy),atp[0][3]]
u4_now=next(v for v in allof(sch,'symbol') if find_prop(v,'Reference')[2]=='U4')
find_prop(u4_now,'Reference')[3]=at(U4_X,153.67,0); find_prop(u4_now,'Value')[3]=at(U4_X,156.21,0)

# Rebuild electrical geometry from pin coordinates. This discards the first
# draft's long crossing wires, then uses short local wires/labels between
# functional blocks. The bootstrap capacitors, ship FET, and pack disconnect
# keep their series/parallel electrical roles explicit in the pin map.
sch[:]=[v for v in sch if k(v) not in ('wire','label','hierarchical_label','junction','no_connect')]
# Retain one real ground symbol at U4 GND; old-draft ground symbols were
# placed on top of newly routed pins and can silently merge unrelated nets.
sch[:]=[v for v in sch if not (k(v)=='symbol' and find_prop(v,'Reference')[2].startswith('#PWR'))]
def getinst(ref):
    return next(v for v in allof(sch,'symbol') if find_prop(v,'Reference')[2]==ref)
def point_for(ref,pinno):
    inst=getinst(ref); libid=one(inst,'lib_id')[1]; lib=next(v for v in allof(lib_symbols,'symbol') if v[1]==libid)
    atv=one(inst,'at'); cx,cy,ang=float(atv[1]),float(atv[2]),int(atv[3])
    pp=next(p for sub in allof(lib,'symbol') for p in allof(sub,'pin') if str(one(p,'number')[1])==str(pinno))
    local=one(pp,'at'); lx,ly=float(local[1]),float(local[2])
    if ang==0: dx,dy=lx,-ly
    elif ang==90: dx,dy=-ly,-lx
    elif ang==180: dx,dy=-lx,ly
    else: dx,dy=ly,lx
    return grid(cx+dx),grid(cy+dy),cx,cy
def wirelabel(ref,pinno,name):
    x,y,cx,cy=point_for(ref,pinno); dx=x-cx; dy=y-cy
    if abs(dx)>=abs(dy):
        end=(grid(x+(2.54 if dx>0 else -2.54)),y)
        path((x,y),end); label(name,*end,'left' if dx>0 else 'right')
    else:
        end=(x,grid(y+(2.54 if dy>0 else -2.54)))
        path((x,y),end); label(name,*end,'left')

# Charger IC pins.
for n in ('[2-3]','8','9'): wirelabel('U4',n,'VBUS_PD')
for n,net in [('29','PMID'),('25','SYS_RAW'),('18','BATP_SENSE'),
              ('24','SDRV'),('13','CE_N'),('14','CHG_SCL'),('15','CHG_SDA'),
              ('6','CHG_DP_RAW'),('7','CHG_DM_RAW'),('12','QON_SW'),('16','TS_SENSE'),
              ('17','ILIM_HIZ'),('20','PROG'),('21','CHG_INT')]: wirelabel('U4',n,net)
nc(*P('1'))
for pinno in ('10','11','27'):
    gnd(*point_for('U4',pinno)[:2])
# Input and output hierarchical ports, each on a clear independent stub.
for name,y in [('VBUS_PD',93),('CHG_DP_RAW',108),('CHG_DM_RAW',118),('CHG_SCL',148),('CHG_SDA',158),
               ('CHG_ENABLE',218),('CHG_SYS_ENABLE',233),('CHG_VIO_3V0',248)]:
    port(name,38,y,'bidirectional' if name in ('CHG_SCL','CHG_SDA') else 'input'); path((38,y),(43.08,y))
for name,y in [('SYS_RAW',129.54),('CHG_INT',208),('BAT_PACK',242.46)]:
    port(name,390,y,'bidirectional' if name=='BAT_PACK' else 'output','right'); path((382.38,y),(390,y))

# Capacitor banks: input/PMID/REGN/SYS/BAT decoupling.
def rail_caps(refs,net,top,bottom):
    pts=[]
    for ref in refs:
        p1=point_for(ref,'1')[:2]; p2=point_for(ref,'2')[:2]; x=p1[0]
        path(p1,(x,top)); path(p2,(x,bottom)); pts.append(x)
    pts=sorted(pts); path((pts[0],top),(pts[-1],top)); path((pts[0],bottom),(pts[-1],bottom))
    for x in pts: junction(x,top); junction(x,bottom)
    label(net,pts[0],top); gnd(pts[-1],bottom)
rail_caps(('C100','C111','C113'),'VBUS_PD',82.55,114.3)
rail_caps(('C101','C108','C112','C114'),'PMID',82.55,114.3)
rail_caps(('C102','C109'),'REGN',82.55,114.3)
rail_caps(('C104','C105','C107'),'SYS_RAW',151.13,183.0)
# BAT decoupling is local to the ship FET path; its single lower terminal has a downward ground symbol.
wirelabel('C106','1','BAT_INT'); gnd(*point_for('C106','2')[:2])
# One REGN ceramic runs directly from the pin to its local decoupling rail.
regpin=point_for('U4','5')[:2]; regcap=point_for('C102','1')[:2]
path(regpin,(regpin[0],88.9),(regcap[0],88.9),regcap)
# Two independent bootstrap pairs and the inductor.
def connect_bootstrap(bt_pin,sw_pin,cap,bt_name,sw_name):
    bx,by,_,_=point_for('U4',bt_pin); sx,sy,_,_=point_for('U4',sw_pin)
    c1x,c1y,_,_=point_for(cap,'1'); c2x,c2y,_,_=point_for(cap,'2')
    # Two distinct orthogonal lanes connect BTST to the top capacitor pin and
    # SW to the bottom pin without crossing at the 2.54 mm IC pitch.
    path((bx,by),(c1x,c1y))
    lane=grid(sx+13.97)
    path((sx,sy),(lane,sy),(lane,c2y),(c2x,c2y))
    label(sw_name,c2x,c2y)
connect_bootstrap('4','28','C103','BTST1','SW1')
connect_bootstrap('19','26','C110','BTST2','SW2')
wirelabel('L1','1','SW1'); wirelabel('L1','2','SW2')
# Pack connector, mechanical disconnect, and external SDRV ship FET in series.
j1=point_for('J5','1')[:2]; swb=point_for('SW101','2')[:2]; path(j1,swb)
wirelabel('J5','2','TS_SENSE'); gnd(*point_for('J5','3')[:2])
wirelabel('SW101','1','BAT_PACK')
batpin=P('[22-23]'); ssx,ssy,_,_=point_for('Q103','[1-3]')
path(batpin,(260.35,batpin[1]),(260.35,156.21),(ssx,156.21),(ssx,ssy)); label('BAT_INT',260.35,156.21)
wirelabel('Q103','[5-9]','BAT_PACK'); wirelabel('Q103','4','SDRV')
wirelabel('R112','1','BAT_PACK'); wirelabel('R112','2','BATP_SENSE')
# TS, 1S PROG, and default-off analog input-current ceiling.
for ref,a,b in [('R100','REGN','TS_SENSE'),('R101','TS_SENSE','GND'),('R102','PROG','GND'),
                ('R108','REGN','ILIM_HIZ'),('R109','ILIM_HIZ','GND'),('R110','REGN','Q101_GATE'),
                ('R111','CHG_SYS_ENABLE','GND'),('R103','REGN','CE_N'),('R107','CHG_ENABLE','GND'),
                ('R106','CHG_VIO_3V0','CHG_INT')]:
    (gnd(*point_for(ref,'1')[:2]) if a=='GND' else wirelabel(ref,'1',a))
    (gnd(*point_for(ref,'2')[:2]) if b=='GND' else wirelabel(ref,'2',b))
for ref,nets in [('Q101',('Q101_GATE','GND','ILIM_HIZ')),('Q102',('CHG_SYS_ENABLE','GND','Q101_GATE')),
                 ('Q100',('CHG_ENABLE','GND','CE_N'))]:
    for pn,net in zip(('1','2','3'),nets): (gnd(*point_for(ref,pn)[:2]) if net=='GND' else wirelabel(ref,pn,net))
wirelabel('SW100','1','QON_SW'); gnd(*point_for('SW100','2')[:2])

# Coordinator-approved provisional Samsung 10uF/50V 1210 for the five-cap
# VBUS/PMID bank; the small 100nF bypass MPNs remain unsourced.
for ref in ('C100','C111','C101','C108','C112'):
    cap=getinst(ref); set_prop(cap,'Value','10uF / 50V'); set_prop(cap,'Footprint','DesktopSpeaker:PD_C_1210')
    for p in allof(cap,'property'):
        if p[1]=='MPN':p[2]='CL32B106KBJNNNE'
        elif p[1] in ('LCSC Part','LCSC'):p[2]='C138687'
        elif p[1]=='Manufacturer':p[2]='Samsung Electro-Mechanics'
        elif p[1]=='Datasheet':p[2]='https://product.samsungsem.com/mlcc/CL32B106KBJNNN.do'

add([S('sheet_instances'),[S('path'),'/',[S('page'),'1']]])
add([S('embedded_fonts'),S('no')])
OUT.write_text('('+' '.join(dumps(v) for v in sch[:1])+'\n'+'\n'.join(dumps(v) for v in sch[1:])+')\n')
print(OUT)
