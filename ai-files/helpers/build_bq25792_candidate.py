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
# Preserve visible functional names and pin numbers, with a compact readable font.
for sub in allof(u4lib,'symbol'):
    if str(sub[1]).endswith('_1_1'):
        for pin in allof(sub,'pin'):
            number=str(one(pin,'number')[1])
            top_x={'[2-3]':-20.32,'8':-10.16,'9':0.0,'29':10.16,'5':20.32}.get(number)
            if top_x is not None:
                one(pin,'at')[1]=top_x
            name=one(pin,'name')
            short_names={}
            if name[1] in short_names: name[1]=short_names[name[1]]
            newpos={'1':(-27.94,12.7,0),'6':(-27.94,10.16,0),'7':(-27.94,7.62,0),'14':(-27.94,5.08,0),'15':(-27.94,2.54,0),
                    '13':(-27.94,0,0),'16':(-27.94,-2.54,0),'17':(-27.94,-5.08,0),'20':(-27.94,-7.62,0),'21':(-27.94,-10.16,0),'12':(-27.94,-12.7,0),
                    '18':(27.94,-12.7,180),'10':(-17.78,-17.78,90),'11':(-7.62,-17.78,90),'27':(-12.7,-17.78,90)}
            if number in newpos:
                one(pin,'at')[1:]=list(newpos[number])
                continue
            if str(one(pin,'number')[1]) in ('1','6','7','12','13','14','15','16','17','20','21','25','[22-23]','18','28','4','26','19','24','11','10'):
                one(pin,'at')[1]=(-27.94 if float(one(pin,'at')[1])<0 else 27.94)
    if str(sub[1]).endswith('_0_1'):
        rect=next((v for v in allof(sub,'rectangle')),None)
        if rect: one(rect,'start')[1:3]=[-25.4,15.24]; one(rect,'end')[1:3]=[25.4,-15.24]
        circ=next((v for v in allof(sub,'circle')),None)
        if circ: one(circ,'center')[1:3]=[-24.13,13.97]
    for pin in allof(sub,'pin'):
        for propname in ('name','number'):
            prop=one(pin,propname)
            size=one(one(prop,'effects'),'font')
            one(size,'size')[1:]=[0.75,0.75]
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
new_cap('C113','0.1uF / 50V',165,99,footprint='DesktopSpeaker:PD_C_0402')
path((165,95.19),(165,88.9)); label('VBUS_PD',165,88.9); path((165,102.81),(165,110)); gnd(165,110)
pmid=P('29')
for ref,x in [('C101',270),('C108',292)]:
    passive(ref,x,99,value='10uF / 35V',footprint='DesktopSpeaker:PD_C_1210')
    for p in allof(obj_by_ref[ref],'property'):
        if p[1] in ('MPN','LCSC Part','LCSC','Manufacturer','Datasheet'): p[2]=''
    path((x,95.19),(x,89.0)); label('PMID',x,89.0); path((x,102.81),(x,110)); gnd(x,110)
new_cap('C112','10uF / 35V',314,99,template='C103',footprint='DesktopSpeaker:PD_C_1210')
path((314,95.19),(314,89.0)); label('PMID',314,89.0); path((314,102.81),(314,110)); gnd(314,110)
new_cap('C114','0.1uF / 50V',336,99,footprint='DesktopSpeaker:PD_C_0402')
new_cap('C115','0.1uF / 50V',350,99,footprint='DesktopSpeaker:PD_C_0402')  # SYS bypass at U4 pin 25
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
    if p[1]=='MPN': p[2]='RC0603FR-074K7L'
    elif p[1] in ('LCSC Part','LCSC'): p[2]='C99782'
    elif p[1]=='Manufacturer': p[2]='YAGEO'
    elif p[1]=='Datasheet': p[2]='${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf'
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

note('Startup: keep HIZ clamped through POR; clear EN_EXTILIM, program/read back IINDPM and 1S limits before enabling SYS. Verify reset/watchdog recovery.',45,266,1.0)
note('Set REG14.SFET_PRESENT=1 before SDRV ship control. MCU reset/REG_RST requires reconfiguration. Pack 10k NTC curve and QON timing pending.',45,271,1.0)
note('R102 4.7k = 1S/750kHz; use 1A initial charge target. D+/D− stay raw for mux. SYS_RAW varies; qualify TPS2116 5.5V limit/transients.',45,276,1.0)
note('L1 2.2uH/6A and input MLCCs are provisional: qualify 20V surge/DC-bias, audio+charge current, ripple, efficiency and thermal limits.',45,281,1.0)

# ---------------------------------------------------------------------------
# Readable redraw (2026-10-05). All wires/labels/ports/junctions/ground symbols
# and notes from the first draft are discarded and rebuilt from pin coordinates.
# Layout: VBUS/PMID/REGN across the top, buck-boost power stage and SYS to the
# right, battery/ship-FET/pack row below it, host and configuration to the left.
# ---------------------------------------------------------------------------
sch[:]=[v for v in sch if k(v) not in ('wire','label','hierarchical_label','junction','no_connect','text')]
sch[:]=[v for v in sch if not (k(v)=='symbol' and find_prop(v,'Reference')[2].startswith('#PWR'))]
def getinst(ref):
    return next(v for v in allof(sch,'symbol') if find_prop(v,'Reference')[2]==ref)
def point_for(ref,pinno):
    inst=getinst(ref); libid=one(inst,'lib_id')[1]; lib=next(v for v in allof(lib_symbols,'symbol') if v[1]==libid)
    atv=one(inst,'at'); cx,cy,ang=float(atv[1]),float(atv[2]),int(atv[3])
    mir=[str(m[1]) for m in allof(inst,'mirror')]
    pp=next(p for sub in allof(lib,'symbol') for p in allof(sub,'pin') if str(one(p,'number')[1])==str(pinno))
    local=one(pp,'at'); lx,ly=float(local[1]),float(local[2])
    if 'x' in mir: ly=-ly
    if 'y' in mir: lx=-lx
    if ang==0: dx,dy=lx,-ly
    elif ang==90: dx,dy=-ly,-lx
    elif ang==180: dx,dy=-lx,ly
    else: dx,dy=ly,lx
    return grid(cx+dx),grid(cy+dy),cx,cy
def set_text(inst,ref_xy,val_xy,just,tang=0):
    for p in allof(inst,'property'):
        if p[1] in ('Reference','Value'):
            xy_=ref_xy if p[1]=='Reference' else val_xy
            p[3]=at(*xy_,tang)
            e=one(p,'effects'); e[:]=[v for v in e if k(v) not in ('justify','hide')]
            if just!='center': e.append([S('justify'),S(just)])
def place(ref,x,y,ang=0,mirror=None,txt='right',ox=5.08):
    inst=getinst(ref); a=one(inst,'at'); a[1:]=[grid(x),grid(y),ang]
    for m in allof(inst,'mirror'): inst.remove(m)
    if mirror: inst.insert(inst.index(a)+1,[S('mirror'),S(mirror)])
    for p in allof(inst,'property'):
        if p[1] not in ('Reference','Value') and len(p)>3: p[3]=at(x,y,0)
    if txt=='right': set_text(inst,(x+ox,y-1.27),(x+ox,y+1.27),'left')
    elif txt=='below': set_text(inst,(x,y+4.0),(x,y+6.5),'center',ang if ang in (90,270) else 0)
    return inst
def stub(x,y,dx,dy,name,just):
    ex,ey=grid(x+dx),grid(y+dy); path((x,y),(ex,ey)); label(name,ex,ey,just)
def hrail(y,xs):
    xs=sorted(xs)
    for a,b in zip(xs,xs[1:]): path((a,y),(b,y))
def P4(n): return point_for('U4',n)[:2]
def pin(ref,n): return point_for(ref,n)[:2]

# ---- U4 body and text -------------------------------------------------------
u4_now=getinst('U4'); set_text(u4_now,(U4_X,U4_Y+17.78),(U4_X,U4_Y+20.32),'center')

# ---- VBUS input rail: VBUS, VAC1, VAC2 (no ACFET installed) ---------------------
RY=101.6
vb,v2,v1=P4('[2-3]'),P4('8'),P4('9')
port('VBUS_PD',38.1,RY,'input')
bank=[('C100',147.32),('C111',167.64),('C113',187.96)]
hrail(RY,[38.1]+[x for _,x in bank]+[vb[0],v2[0],v1[0]])
for p in (vb,v2,v1): path(p,(p[0],RY))
for x in [x for _,x in bank]+[vb[0],v2[0]]: junction(x,RY)
for ref,x in bank:
    place(ref,x,RY+3.81); gnd(*pin(ref,'2'))
note('VBUS input: VAC1/VAC2 tied to VBUS (no ACFETs); ACDRV1/2 to GND',127.0,RY-3.81,1.0)

# ---- PMID rail and REGN rail -----------------------------------------------------
PY=83.82
pm=P4('29'); pcx=[264.16,284.48,304.8,325.12]
path(pm,(pm[0],PY)); hrail(PY,[pm[0]]+pcx); label('PMID',251.46,PY)
for x in pcx[:-1]: junction(x,PY)
for ref,x in zip(('C101','C108','C112','C114'),pcx):
    place(ref,x,PY+3.81); gnd(*pin(ref,'2'))
rg=P4('5'); rcx=[264.16,284.48]
path(rg,(rg[0],RY)); hrail(RY,[rg[0]]+rcx); label('REGN',254.0,RY); junction(rcx[0],RY)
for ref,x in zip(('C102','C109'),rcx):
    place(ref,x,RY+3.81); gnd(*pin(ref,'2'))

# ---- Buck-boost switch nodes, inductor and bootstrap capacitors ---------------------
place('L1',299.72,116.84,ang=90,txt=None)
set_text(getinst('L1'),(306.07,115.57),(306.07,118.11),'left',90)
l1a,l1b=pin('L1','1'),pin('L1','2')
sw1,sw2=P4('28'),P4('26')
path(sw1,l1a); label('SW1',273.05,sw1[1])
path(sw2,(l1b[0],sw2[1]),l1b); label('SW2',273.05,sw2[1])
stub(*P4('4'),2.54,0,'BTST1','left'); stub(*P4('19'),2.54,0,'BTST2','left')
for cap,x,bt,sw in (('C103',335.28,'BTST1','SW1'),('C110',355.6,'BTST2','SW2')):
    place(cap,x,111.76)
    t,b=pin(cap,'1'),pin(cap,'2')
    stub(t[0],t[1],0,-2.54,bt,'left'); stub(b[0],b[1],0,2.54,sw,'left')

# ---- SYS output ------------------------------------------------------------------------
SYS_Y=P4('25')[1]; scx=[325.12,345.44,365.76,386.08]
sy=P4('25'); hrail(SYS_Y,[sy[0]]+scx+[398.78])
for x in scx: junction(x,SYS_Y)
for ref,x in zip(('C115','C104','C105','C107'),scx):
    place(ref,x,SYS_Y+3.81); gnd(*pin(ref,'2'))
port("SYS_RAW",398.78,SYS_Y,'output','right')

# ---- Battery path: BAT -> external ship FET Q103 (source on BAT, drain to pack) -------------
place('Q103',271.78,137.16,mirror='x',txt=None)
set_text(getinst('Q103'),(280.67,134.62),(280.67,137.16),'left')
bt=P4('[22-23]'); qs=pin('Q103','[1-3]'); qg=pin('Q103','4'); qd=pin('Q103','[5-9]')
path(bt,qs); junction(*qs); path(qs,(304.8,qs[1])); label('BAT_INT',281.94,qs[1])
place('C106',304.8,qs[1]+3.81); gnd(*pin('C106','2'))
path(P4('24'),qg)                       # SDRV straight to ship FET gate
# BATP Kelvin sense through R112 (100R) from the pack-side node (Q103 drain)
place('R112',265.43,P4('18')[1],ang=270,txt='below')
r112a,r112b=pin('R112','2'),pin('R112','1')
path(P4('18'),r112a); path(r112b,qd); junction(*qd)
BPY=152.4
path(qd,(qd[0],BPY),(284.48,BPY)); junction(284.48,BPY)
place('SW101',307.34,BPY,txt='below')
sw101a,sw101b=pin('SW101','1'),pin('SW101','2')
path((284.48,BPY),sw101a)
place('J5',345.44,BPY+2.54)
j1,j2,j3=pin('J5','1'),pin('J5','2'),pin('J5','3')
path(sw101b,j1); label('PACK_RAW',325.12,BPY)
stub(j2[0],j2[1],-2.54,0,'TS_SENSE','right'); gnd(*j3)
path((284.48,BPY),(284.48,167.64),(391.16,167.64)); port('BAT_PACK',391.16,167.64,'bidirectional','right')

# ---- Ground cluster (GND, ACDRV1, ACDRV2) ------------------------------------------------
g,a1,a2=P4('27'),P4('11'),P4('10'); GY=g[1]+5.08
for p in (g,a1,a2): path(p,(p[0],GY))
hrail(GY,[a2[0],g[0],a1[0]]); junction(g[0],GY); gnd(g[0],GY)
nc(*P4('1'))                         # STAT unused

# ---- Left host interface ports (straight) ------------------------------------------------------
nc(*P4('6')); nc(*P4('7'))            # D+/D- unconnected; AUTO_INDET_EN=0
for name,n,shape in (('CHG_SCL','14','bidirectional'),('CHG_SDA','15','bidirectional')):
    p=P4(n); port(name,38.1,p[1],shape); path((38.1,p[1]),p)
LX=198.12
for n,name in (('13','CE_N'),('16','TS_SENSE'),('17','ILIM_HIZ'),('20','PROG'),('21','CHG_INT')):
    p=P4(n); path(p,(LX,p[1])); label(name,LX,p[1],'right')
# QON wake button directly on the QON pin
place('SW100',190.5,P4('12')[1],ang=180,txt=None)
set_text(getinst('SW100'),(189.23,151.13),(189.23,153.67),'left')
path(P4('12'),pin('SW100','1')); gnd(*pin('SW100','2'))

# ---- PROG strap and TS network ----------------------------------------------------------------------
place('R102',160.02,170.18); r=pin('R102','1'); stub(r[0],r[1],0,-2.54,'PROG','left'); gnd(*pin('R102','2'))
place('R100',182.88,170.18); r=pin('R100','1'); stub(r[0],r[1],0,-2.54,'REGN','left')
place('R101',182.88,181.61); gnd(*pin('R101','2'))
path(pin('R100','2'),pin('R101','1')); label('TS_SENSE',182.88,175.26,'right')

# ---- ILIM_HIZ default-off gate -----------------------------------------------------------------------------
place('R108',111.76,170.18); r=pin('R108','1'); stub(r[0],r[1],0,-2.54,'REGN','left')
place('R109',111.76,181.61); gnd(*pin('R109','2'))
place('Q101',129.54,180.34,mirror='y',ox=10.16)
q1d,q1s,q1g=pin('Q101','3'),pin('Q101','2'),pin('Q101','1')
r8b,r9t=pin('R108','2'),pin('R109','1')
path(r8b,(r8b[0],175.26)); path((r8b[0],175.26),r9t); junction(r8b[0],175.26)
path((r8b[0],175.26),q1d); label('ILIM_HIZ',118.11,175.26); gnd(*q1s)
XG=137.16
place('R110',XG,173.99); r=pin('R110','1'); stub(r[0],r[1],0,-2.54,'REGN','left')
path(q1g,(XG,q1g[1])); junction(XG,q1g[1]); path(pin('R110','2'),(XG,q1g[1]))
place('Q102',134.62,208.28)
q2d,q2s,q2g=pin('Q102','3'),pin('Q102','2'),pin('Q102','1')
path((XG,q1g[1]),q2d); gnd(*q2s)
place('R111',121.92,212.09); port('CHG_SYS_ENABLE',38.1,q2g[1],'input')
path((38.1,q2g[1]),q2g); junction(121.92,q2g[1]); path(pin('R111','1'),(121.92,q2g[1])); gnd(*pin('R111','2'))

# ---- CE default-off (charge disabled unless CHG_ENABLE is driven high) ---------------------------------
set_prop(getinst('R103'),'Value','100k'); place('R103',87.63,170.18); r=pin('R103','1'); stub(r[0],r[1],0,-2.54,'REGN','left')
place('Q100',85.09,187.96)
q0d,q0s,q0g=pin('Q100','3'),pin('Q100','2'),pin('Q100','1')
path(pin('R103','2'),q0d); label('CE_N',87.63,177.8,'right'); gnd(*q0s)
place('R107',64.77,191.77); port('CHG_ENABLE',38.1,q0g[1],'input')
path((38.1,q0g[1]),q0g); junction(64.77,q0g[1]); path(pin('R107','1'),(64.77,q0g[1])); gnd(*pin('R107','2'))

# ---- INT pull-up (10k to the logic rail) and interrupt output -------------------------------------------------
place('R106',50.8,170.18)
vio=pin('R106','1'); port('CHG_VIO_3V0',38.1,vio[1],'input'); path((38.1,vio[1]),vio)
r=pin('R106','2'); stub(r[0],r[1],0,2.54,'CHG_INT','left')
path((381.0,180.34),(391.16,180.34)); label('CHG_INT',381.0,180.34,'right'); port('CHG_INT',391.16,180.34,'output','right')

# ---- Section titles and open items ------------------------------------------------------------------------------
note('Config and default-off gates',38.1,160.0,1.0)
for i,t in enumerate([
 'Startup: keep ILIM_HIZ clamped (Q101) through POR; clear EN_EXTILIM, program/read back IINDPM and 1S limits before enabling SYS. Verify reset/watchdog recovery.',
 'Set REG14.SFET_PRESENT=1 and read back before SDRV ship control; POR default 0 locks SDRV_CTRL. MCU reset/REG_RST requires reconfiguration.',
 'R102 4.7k = 1S/750kHz PROG. L1 2.2uH/6A and input MLCCs are provisional: qualify 20V surge/DC-bias, load current, ripple, efficiency and thermal limits.',
 'I2C pull-ups (10k to logic rail) and CHG_VIO_3V0 level are host-side; D+/D- unconnected (no-connect); set AUTO_INDET_EN=0, HVDCP_EN=0.']):
    note(t,38.1,232.0+5.08*i,1.0)

# Coordinator-approved provisional Samsung 10uF/50V 1210 for the five-cap
# VBUS/PMID bank; the small 100nF bypass MPNs remain unsourced.
for ref in ('C100','C111','C101','C108','C112'):
    cap=getinst(ref); set_prop(cap,'Value','10uF / 50V'); set_prop(cap,'Footprint','DesktopSpeaker:PD_C_1210')
    for p in allof(cap,'property'):
        if p[1]=='MPN':p[2]='CL32B106KBJNNNE'
        elif p[1] in ('LCSC Part','LCSC'):p[2]='C138687'
        elif p[1]=='Manufacturer':p[2]='Samsung Electro-Mechanics'
        elif p[1]=='Datasheet':p[2]='https://product.samsungsem.com/mlcc/CL32B106KBJNNN.do'

# Reuse already-selected passive mappings where the new candidate values match.
metadata={
 'C110':('YAGEO','CC0603KRX7R9BB473','C107093','https://www.yageo.com/upload/media/product/productspec/capacitor/CC0603KRX7R9BB473.pdf'),
 'C113':('Murata','GRM155R71H104KE14D','C77020','https://www.murata.com/en-us/products/productdetail?partno=GRM155R71H104KE14D%23'),
 'C114':('Murata','GRM155R71H104KE14D','C77020','https://www.murata.com/en-us/products/productdetail?partno=GRM155R71H104KE14D%23'),
 'C115':('Murata','GRM155R71H104KE14D','C77020','https://www.murata.com/en-us/products/productdetail?partno=GRM155R71H104KE14D%23'),
 'R103':('YAGEO','RC0603FR-07100KL','C14675','${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf'),
 'R108':('YAGEO','RC0603FR-07180KL','C123419','${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf'),
 'R109':('YAGEO','RC0603FR-07100KL','C14675','${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf'),
 'R110':('YAGEO','RC0603FR-07100KL','C14675','${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf'),
 'R111':('YAGEO','RC0603FR-07100KL','C14675','${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf'),
 'R112':('YAGEO','RC0603FR-07100RL','C105588','${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf'),
}
for ref,(manufacturer,mpn,lcsc,datasheet) in metadata.items():
    inst=getinst(ref)
    for p in allof(inst,'property'):
        if p[1]=='Manufacturer':p[2]=manufacturer
        elif p[1]=='MPN':p[2]=mpn
        elif p[1] in ('LCSC','LCSC Part'):p[2]=lcsc
        elif p[1]=='Datasheet':p[2]=datasheet
# Q101/Q102 reuse the already selected Q100 2N7002 mapping.
for ref in ('Q101','Q102'):
    inst=getinst(ref)
    for key,val in [('MPN','2N7002,215'),('LCSC Part','C65189'),('Manufacturer','Nexperia'),
                    ('Datasheet','https://assets.nexperia.com/documents/data-sheet/2N7002.pdf')]:
        inst.insert(next(i for i,v in enumerate(inst) if k(v)=='pin'),[S('property'),key,val,at(0,0),eff(hide=True)])
# Correct R102's stale 220-ohm purchasing identity for its retained 4.7-kohm value.
for p in allof(getinst('R102'),'property'):
    if p[1]=='MPN':p[2]='RC0603FR-074K7L'
    elif p[1] in ('LCSC','LCSC Part'):p[2]='C99782'
    elif p[1]=='Manufacturer':p[2]='YAGEO'
    elif p[1]=='Datasheet':p[2]='${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf'

add([S('sheet_instances'),[S('path'),'/',[S('page'),'1']]])
add([S('embedded_fonts'),S('no')])
OUT.write_text('('+' '.join(dumps(v) for v in sch[:1])+'\n'+'\n'.join(dumps(v) for v in sch[1:])+')\n')
print(OUT)
