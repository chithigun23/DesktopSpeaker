from pathlib import Path
import sys, copy, uuid
sys.path.insert(0,'ai-files/vendor')
import sexpdata as sx
S=sx.Symbol

def k(a): return str(a[0]) if isinstance(a,list) and a else ''
def one(a,n): return next(z for z in a if k(z)==n)
def uid(): return str(uuid.uuid4())
def prop(name,val,x,y,hide=False):
    e=[S('effects'),[S('font'),[S('size'),1.27,1.27]]]
    if hide:e.append([S('hide'),S('yes')])
    return [S('property'),name,val,[S('at'),x,y,0],e]
def pin(name,num,typ,side,y,x=None):
    if x is None: x=-30.48 if side=='L' else (30.48 if side=='R' else 0)
    angle=0 if side=='L' else (180 if side=='R' else (270 if side=='T' else 90))
    # Keep both fields visible while lowering their font to remain legible at the
    # required 2.54 mm minimum pitch.
    return [S('pin'),S(typ),S('line'),[S('at'),x,y,angle],[S('length'),5.08],[S('name'),name,[S('effects'),[S('font'),[S('size'),0.50,0.50]]]],[S('number'),num,[S('effects'),[S('font'),[S('size'),0.50,0.50]]]]]

def tps_symbol():
    pins=[]
    def lp(name,val,i,x,y,hide=False):
        e=[S('effects'),[S('font'),[S('size'),1.27,1.27]]]
        if hide:e.append([S('hide'),S('yes')])
        return [S('property'),name,val,[S('id'),i],[S('at'),x,y,0],e]
    # Inputs and digital signals on left; y is local symbol (positive is upward on page).
    left=[('CC1','28','bidirectional',20.32),('CC2','29','bidirectional',15.24),('SDA','8','bidirectional',10.16),('SCL','9','bidirectional',5.08),('ADC1','2','input',0),('ADC2','3','input',-5.08),('ADC3','5','input',-10.16),('ADC4','7','input',-15.24),('FAULT','18','input',-20.32)]
    for n,num,t,y in left:pins.append(pin(n,num,t,'L',y))
    right=[('CAP_MIS','6','open_collector',20.32),('SINK_EN','19','open_collector',15.24),('EVENT','37','open_collector',10.16),('FLIP','13','open_collector',5.08),('DBG_ACC','10','open_collector',0),('RESERVED','[26-27]','passive',-5.08),('DRAIN','15','passive',-10.16),('DRAIN','30','passive',-15.24),('DRAIN','40','passive',-20.32)]
    for n,num,t,y in right:pins.append(pin(n,num,t,'R',y))
    # The datasheet identifies these pads as electrically common; native stacks retain physical pin numbers.
    top=[('VBUS_IN','[23-25]','power_in',-22.86),('VBUS','[32-33]','power_in',-13.97),('LDO_3V3','1','power_out',-5.08),('LDO_1V5','4','power_out',5.08),('VIN_3V3','38','power_in',13.97),('PPHV','[20-22]','power_out',22.86)]
    for n,num,t,x in top:pins.append(pin(n,num,t,'T',30.48,x))
    pins.append(pin('GND','[11-12,14,16-17,31,34-35,39]','power_in','B',-30.48,-22.86))
    pins.append(pin('RESERVED','36','passive','B',-30.48,-17.78))
    lib=[S('symbol'),'TPS25730DREFR',[S('pin_numbers')],[S('pin_names'),[S('offset'),1.27]],[S('in_bom'),S('yes')],[S('on_board'),S('yes')],
        lp('Reference','U',0,0,-27.94),lp('Value','TPS25730DREFR',1,0,-30.48),lp('Footprint','TPS25730D:Texas_REF0038A_WQFN-38-2EP_6x4mm_P0.4',2,0,0,True),lp('Datasheet','${KIPRJMOD}/../ai-files/datasheets/TPS25730.pdf',3,0,0,True),lp('Manufacturer','Texas Instruments',4,0,0,True),lp('MPN','TPS25730DREFR',5,0,0,True),lp('LCSC Part','C22438973',6,0,0,True),lp('Description','USB Type-C sink PD controller, integrated 7A path, WQFN-38 REF0038A',7,0,0,True),
        [S('symbol'),'TPS25730DREFR_0_1',[S('rectangle'),[S('start'),-25.4,25.4],[S('end'),25.4,-25.4],[S('stroke'),[S('width'),0.254],[S('type'),S('default')]],[S('fill'),[S('type'),S('background')]]]],
        [S('symbol'),'TPS25730DREFR_1_1',*pins],[S('embedded_fonts'),S('no')]]
    return lib

def mk_cache(src,libid):
    a=copy.deepcopy(next(x for x in src if k(x)=='symbol' and x[1]==libid))
    return a

def mk_instance(cache,libid,ref,value,x,y,rotation=0,fp='',datasheet='',mfr='',mpn='',lcsc='',root=''):
    sym=next(z for z in cache if k(z)=='symbol' and z[1].endswith('_1_1'))
    nums=[]
    for p in sym:
        if k(p)=='pin': nums.append(one(p,'number')[1])
    item=[S('symbol'),[S('lib_id'),libid],[S('at'),x,y,rotation],[S('unit'),1],[S('exclude_from_sim'),S('no')],[S('in_bom'),S('yes')],[S('on_board'),S('yes')],[S('dnp'),S('no')],[S('uuid'),uid()],
       prop('Reference',ref,x,y-4.0),prop('Value',value,x,y-1.5),prop('Footprint',fp,x,y,True),prop('Datasheet',datasheet,x,y,True)]
    if mfr:item.append(prop('Manufacturer',mfr,x,y,True))
    if mpn:item.append(prop('MPN',mpn,x,y,True))
    if lcsc:item.append(prop('LCSC Part',lcsc,x,y,True))
    for n in nums:item.append([S('pin'),n,[S('uuid'),uid()]])
    item.append([S('instances'),[S('project'),'DesktopSpeaker',[S('path'),'/'+root,[S('reference'),ref],[S('unit'),1]]]])
    return item

def wire(a,b): return [S('wire'),[S('pts'),[S('xy'),a[0],a[1]],[S('xy'),b[0],b[1]]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),uid()]]
def hlabel(name,x,y,shape,justify='left'): return [S('hierarchical_label'),name,[S('shape'),S(shape)],[S('at'),x,y,0],[S('effects'),[S('font'),[S('size'),1,1]],[S('justify'),S(justify),S('bottom')]],[S('uuid'),uid()]]
def local_label(name,x,y,justify='left'):return [S('label'),name,[S('at'),x,y,0],[S('effects'),[S('font'),[S('size'),1,1]],[S('justify'),S(justify),S('bottom')]],[S('uuid'),uid()]]
ground_count=0
def ground(x,y,ref=None):
    global ground_count
    ground_count+=1
    g=next(z for z in oldlibs if k(z)=='symbol' and z[1]=='power:GND')
    a=mk_instance(g,'power:GND',f'#PWR{ground_count:02d}','GND',x,y,0,'','','','','',root)
    for p in a:
        if k(p)=='property' and p[1]=='Reference':one(p,'effects').append([S('hide'),S('yes')])
        if k(p)=='in_bom':p[1]=S('no')
        if k(p)=='on_board':p[1]=S('no')
        if k(p)=='property' and p[1]=='Value': one(p,'at')[1:3]=[x,round(y+3.81,2)]
    return a
def text(s,x,y,size=1.27):return [S('text'),s,[S('at'),x,y,0],[S('effects'),[S('font'),[S('size'),size,size]],[S('justify'),S('left'),S('bottom')]],[S('uuid'),uid()]]

base=sx.loads(Path('DesktopSpeaker-kicad/USB_PD.kicad_sch').read_text())
oldlibs=one(base,'lib_symbols')
need=['PD_C:PD_C','PD_R:PD_R','PD_DIODE:PD_DIODE','PD_SERVICE_HDR:PD_SERVICE_HDR','TVS2200DRVR:TVS2200DRVR','ESDA25L:ESDA25L','TPS7B8450QWDRBRQ1:TPS7B8450QWDRBRQ1','power:GND']
cache=[mk_cache(oldlibs,n) for n in need]
tps=tps_symbol(); tps[1]='TPS25730DREFR:TPS25730DREFR'
# Add all cached symbols by their instance lib ids and the newly designed IC.
libsyms=[S('lib_symbols'),tps,*cache]
root=uid()
sch=[S('kicad_sch'),[S('version'),20260306],[S('generator'),'eeschema'],[S('generator_version'),'10.0'],[S('uuid'),root],[S('paper'),'A4'],[S('title_block'),[S('title'),'USB-C PD 5–20 V SPR — TPS25730D candidate'],[S('rev'),'prototype review'] ],libsyms]
# Candidate duplicates the existing child UUID and U11 symbol UUID so integration can be swapped in place.
root='feda53ed-537d-4f88-9436-c6075776255b/f38b7023-3d53-43ea-b3db-e2c826d87b35'
# Update the sheet UUID and project path while preserving the existing hierarchy path.
sch[4]=[S('uuid'),'f38b7023-3d53-43ea-b3db-e2c826d87b35']
# Compact functional candidate layout on the 1.27mm schematic grid.
items=[]
items.append(mk_instance(tps,'TPS25730DREFR:TPS25730DREFR','U11','TPS25730DREFR',220.98,129.54,0,'TPS25730D:Texas_REF0038A_WQFN-38-2EP_6x4mm_P0.4','${KIPRJMOD}/../ai-files/datasheets/TPS25730.pdf','Texas Instruments','TPS25730DREFR','C22438973',root))
one(items[0],'uuid')[1]='ecd93b6c-1e07-45ba-9154-e32777f2a513'
ldoc=next(x for x in oldlibs if k(x)=='symbol' and x[1]=='TPS7B8450QWDRBRQ1:TPS7B8450QWDRBRQ1')
items.append(mk_instance(ldoc,'TPS7B8450QWDRBRQ1:TPS7B8450QWDRBRQ1','U19','TPS7B8450QWDRBRQ1',110.49,208.28,0,'DesktopSpeaker:TPS7B8450QWDRBRQ1_WSON-8','../ai-files/datasheets/TPS7B84-Q1.pdf','Texas Instruments','TPS7B8450QWDRBRQ1','C3751394',root))
one(items[-1],'uuid')[1]='db29242f-3c91-45e6-8bd2-39f0825252c0'
items[-1].append(prop('Description','Fixed 5.0 V, 150 mA automotive LDO, WSON-8 DRB with exposed thermal pad',110.49,208.28,True))
def add(libid,ref,val,x,y,fp='',datasheet='',mfr='',mpn='',lcsc=''):
    lib=next(z for z in oldlibs if k(z)=='symbol' and z[1]==libid)
    i=mk_instance(lib,libid,ref,val,x,y,0,fp,datasheet,mfr,mpn,lcsc,root);items.append(i);return i
add('TVS2200DRVR:TVS2200DRVR','D6','TVS2200DRVR',110.49,100.33,'DesktopSpeaker:TVS2200DRVR','${KIPRJMOD}/../ai-files/datasheets/TVS2200.pdf','Texas Instruments','TVS2200')
add('ESDA25L:ESDA25L','D5','ESDA25L',139.70,121.92,'DesktopSpeaker:ESDA25L','${KIPRJMOD}/../ai-files/datasheets/ESDAL-ST.pdf','STMicroelectronics','ESDA25L','C95343')
for ref,val,x,y,fp in [
 ('C2','4.7uF X7R 50V',198.12,82.55,'DesktopSpeaker:PD_C_1210'),
 ('C6','22uF X7R 10V',215.90,82.55,'DesktopSpeaker:PD_C_0805'),
 ('C181','10uF X7R 10V',226.06,82.55,'DesktopSpeaker:PD_C_0805'),
 ('C185','10uF X7R 10V CVIN_3V3',234.95,82.55,'DesktopSpeaker:PD_C_0805'),
 ('C182','330pF C0G CC1 filter',166.37,123.19,'DesktopSpeaker:PD_C_0603'),
 ('C183','330pF C0G CC2 filter',186.69,125.73,'DesktopSpeaker:PD_C_0603'),
 ('C184','1uF X7R 50V',91.44,208.28,'DesktopSpeaker:PD_C_0805'),
 ('C5','4.7uF X7R 50V',134.62,208.28,'DesktopSpeaker:PD_C_1206')]:add('PD_C:PD_C',ref,val,x,y,fp)
for ref,val,x,y in [('R10','200k 1%',149.86,129.54),('R11','10k 1%',149.86,142.24),('R12','100k 1%',265.43,95.25),('R13','10k 1%',182.88,151.13),('R14','10k 1%',62.23,139.7),('R15','10k 1%',80.01,139.7),('R16','100k 1%',222.25,99.06),('R17','100k 1%',212.09,78.74),('R18','10k 1%',152.4,139.7)]:add('PD_R:PD_R',ref,val,x,y,'DesktopSpeaker:PD_R_0603')
# Populate only exact known purchasing matches; leave R10 unselected (200k has no
# matching BOM record). Capacitor curves still need effective-value qualification.
def purchasing(ref, manufacturer, mpn, lcsc, datasheet=''):
    inst=next(i for i in items if any(k(p)=='property' and p[1]=='Reference' and p[2]==ref for p in i))
    at=one(inst,'at')
    for n,v in [('Manufacturer',manufacturer),('MPN',mpn),('LCSC Part',lcsc),('LCSC',lcsc)]: inst.append(prop(n,v,at[1],at[2],True))
    if datasheet: inst.append(prop('Datasheet',datasheet,at[1],at[2],True))
for ref in ('C181','C185'):
    purchasing(ref,'Samsung Electro-Mechanics','CL21B106KPQNNNE','C32635','${KIPRJMOD}/../ai-files/datasheets/Samsung_CL21B106KPQNNNE.pdf')
purchasing('C2','Samsung Electro-Mechanics','CL32B475KBUYNNE','C170099','https://product.samsungsem.com/mlcc/CL32B475KBUYNN.do')
purchasing('C6','Murata','GRM21BZ71A226ME15L','C907991')
for r in ('R14','R15','R18'): purchasing(r,'YAGEO','RC0603FR-0710KL','C98220','${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf')
for r in ('R16','R17'): purchasing(r,'YAGEO','RC0603FR-07100KL','C14675','${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf')
purchasing('C184','Samsung Electro-Mechanics','CL21B105KBFNNNE','C28323','https://www.lcsc.com/datasheet/C28323.pdf')
purchasing('R11','YAGEO','RC0603FR-0710KL','C98220','${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf')
purchasing('R12','YAGEO','RC0603FR-07100KL','C14675','${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf')
purchasing('R13','YAGEO','RC0603FR-0710KL','C98220','${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf')
add('PD_DIODE:PD_DIODE','D7','1N5819HW',134.62,66.04,'DesktopSpeaker:PD_D_SOD123','','Diodes Incorporated','1N5819HW-7-F','C82544')
add('PD_SERVICE_HDR:PD_SERVICE_HDR','J4','I2C service',64.77,246.38,'DesktopSpeaker:PD_SERVICE_HDR')

# ---- Readable redraw: explicit placement on the 1.27 mm grid, no net crossings. ----
def bykey(ref):
    return next(i for i in items if any(k(p)=='property' and p[1]=='Reference' and p[2]==ref for p in i))
def setprop(i,name,x,y,just=None):
    for p in i:
        if k(p)=='property' and p[1]==name:
            one(p,'at')[1:3]=[round(x,2),round(y,2)]
            if just:
                eff=one(p,'effects')
                eff.append([S('justify'),S(just)])
def place(ref,x,y,rot=0,ref_at=None,val_at=None,just='left'):
    i=bykey(ref); at=one(i,'at'); at[1:4]=[x,y,rot]
    ref_at=ref_at or (x+3.81,y-1.27); val_at=val_at or (x+3.81,y+1.27)
    setprop(i,'Reference',*ref_at,just); setprop(i,'Value',*val_at,just)
    for p in i:
        if k(p)=='property' and p[1] not in ('Reference','Value'): one(p,'at')[1:3]=[x,y]
# ICs: ref/value centred below the body. Passives/diodes/connector: text to the right.
place('U11',170.18,101.6,ref_at=(170.18,129.54),val_at=(170.18,132.08),just=None)
place('U19',96.52,165.1,ref_at=(96.52,189.23),val_at=(96.52,191.77),just=None)
place('D6',88.9,68.58,ref_at=(95.25,67.31),val_at=(95.25,69.85))
place('D7',134.62,66.04,270,ref_at=(138.43,64.77),val_at=(138.43,67.31))
for pp in bykey('D7'):
    if k(pp)=='property' and pp[1] in ('Reference','Value'): one(pp,'at')[3]=90  # symbol rotated 270; keep text horizontal
place('D5',91.44,116.84,ref_at=(97.79,115.57),val_at=(97.79,118.11))
for r,(x,y) in {'C2':(114.3,67.31),'C6':(170.18,54.61),'C181':(195.58,54.61),'C185':(220.98,54.61),'R12':(255.27,54.61),
                'C182':(50.8,110.49),'C183':(50.8,123.19),'C184':(71.12,173.99),'C5':(124.46,161.29),
                'R10':(116.84,113.03),'R11':(116.84,120.65)}.items(): place(r,x,y)
for r,(x,y) in {'R14':(62.23,139.7),'R15':(80.01,139.7),'R16':(222.25,99.06),'R17':(212.09,78.74),'R18':(152.4,139.7)}.items(): place(r,x,y)
place('R13',129.54,125.73,180,ref_at=(133.35,124.46),val_at=(133.35,127.0),just='right')
place('J4',48.26,182.88,ref_at=(52.07,180.34),val_at=(52.07,182.88))
for i in items[:]:pass
sch.extend(items)
def W(*pts):
    for a,b in zip(pts,pts[1:]):sch.append(wire(a,b))
def J(x,y):junc(x,y)
def G(x,y):sch.append(ground(x,y))
def LBL(n,x,y,j='left'):sch.append(local_label(n,x,y,j))
def HL(n,x,y,shape,j):sch.append(hlabel(n,x,y,shape,j))
def NC(x,y):sch.append([S('no_connect'),[S('at'),x,y],[S('uuid'),uid()]])
def junc(x,y):sch.append([S('junction'),[S('at'),x,y],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),uid()]])
# Raw USB rail: input port -> D6, C2, VBUS_IN drop, VBUS drop (one port label for the whole section).
HL('USB_VBUS',40.64,60.96,'input','right')
W((40.64,60.96),(88.9,60.96),(114.3,60.96),(147.32,60.96),(156.21,60.96),(156.21,71.12))
W((147.32,60.96),(147.32,71.12)); W((88.9,60.96),(88.9,64.77)); W((114.3,60.96),(114.3,63.5))
J(88.9,60.96);J(114.3,60.96);J(147.32,60.96);J(134.62,60.96)
W((134.62,60.96),(134.62,62.23)); G(134.62,69.85)
G(114.3,71.12); G(88.9,72.39); W((88.9,72.39),(91.44,72.39))
# Left-hand interface ports (inputs/bidirectional).
for n,y,sh in [('USB_CC1',81.28,'input'),('USB_CC2',86.36,'input'),('PDCTRL_SDA',91.44,'bidirectional'),('PDCTRL_SCL',96.52,'bidirectional')]:
    W((110.49,y),(139.7,y)); HL(n,110.49,y,sh,'right')
# ADC straps: ADCIN1/3 to GND (code 0), ADCIN2 to LDO_3V3 (code 7), ADCIN4 via 200k/10k divider (code 1).
G(139.7,101.6); G(139.7,111.76)
W((139.7,106.68),(134.62,106.68)); LBL('LDO_3V3',134.62,106.68,'right')
W((139.7,116.84),(116.84,116.84)); J(116.84,116.84)
W((116.84,109.22),(116.84,104.14)); LBL('LDO_3V3',116.84,104.14,'left'); G(116.84,124.46)
# FAULT_IN pull-up (R13 rotated: pin 2 on FAULT_IN, pin 1 to LDO_3V3).
W((139.7,121.92),(129.54,121.92)); W((129.54,129.54),(129.54,132.08)); LBL('LDO_3V3',129.54,132.08,'left')
# Top supply pins: bypass sections are remote and share the label with the pin stub.
for x,n in [(165.1,'LDO_3V3'),(175.26,'LDO_1V5'),(184.15,'VIN_LOW')]:
    W((x,71.12),(x,68.58)); LBL(n,x,68.58,'left')
W((193.04,71.12),(193.04,68.58),(234.95,68.58)); HL('VBUS_PD',234.95,68.58,'output','left')
for x,n in [(170.18,'LDO_3V3'),(195.58,'LDO_1V5')]:
    W((x,50.8),(x,48.26)); LBL(n,x,48.26,'left'); G(x,58.42)
W((220.98,50.8),(220.98,48.26)); LBL('VIN_LOW',220.98,48.26,'left'); G(220.98,58.42)
W((220.98,50.8),(255.27,50.8)); J(220.98,50.8); G(255.27,58.42)
# Right-hand status outputs, reserved pins grounded, drains intentionally no-connect.
for n,y in [('PD_SINK_EN',86.36),('PD_PLUG_EVENT',91.44)]:
    W((200.66,y),(234.95,y)); HL(n,234.95,y,'output','left')
for y in (81.28,96.52,101.6): NC(200.66,y)  # CAP_MIS, FLIP, DBG_ACC unused
# 100k open-drain pull-ups to LDO_3V3
W((212.09,86.36),(212.09,82.55)); J(212.09,86.36); W((212.09,74.93),(212.09,72.39)); LBL('LDO_3V3',212.09,72.39,'left')
W((222.25,91.44),(222.25,95.25)); J(222.25,91.44); W((222.25,102.87),(222.25,105.41)); LBL('LDO_3V3',222.25,105.41,'left')
# I2C pull-ups (remote sections share the port net names) and RESERVED pin 36 via 10k
for x,n in ((62.23,'PDCTRL_SDA'),(80.01,'PDCTRL_SCL')):
    W((x,135.89),(x,133.35)); LBL('LDO_3V3',x,133.35,'left'); W((x,143.51),(x,146.05)); LBL(n,x,146.05,'left')
W((152.4,132.08),(152.4,135.89)); G(152.4,143.51)
W((200.66,106.68),(203.2,106.68)); G(203.2,106.68)
for y in (111.76,116.84,121.92):NC(200.66,y)
G(147.32,132.08)
# CC clamp/filter block (remote sections share USB_CC1/USB_CC2 labels).
G(91.44,124.46)
W((86.36,114.3),(80.01,114.3),(80.01,106.68),(50.8,106.68),(45.72,106.68)); J(50.8,106.68); LBL('USB_CC1',45.72,106.68,'right'); G(50.8,114.3)
W((86.36,119.38),(50.8,119.38),(45.72,119.38)); J(50.8,119.38); LBL('USB_CC2',45.72,119.38,'right'); G(50.8,127.0)
# U19 raw-VBUS auxiliary LDO.
W((83.82,160.02),(71.12,160.02),(66.04,160.02)); LBL('USB_VBUS',66.04,160.02,'right')
W((71.12,160.02),(71.12,170.18),(83.82,170.18)); J(71.12,160.02); J(71.12,170.18); G(71.12,177.8)
W((109.22,157.48),(124.46,157.48),(139.7,157.48)); J(124.46,157.48); HL('USB_AUX_5V',139.7,157.48,'output','left'); G(124.46,165.1)
for y in (162.56,167.64,170.18,172.72):NC(109.22,y)
W((91.44,180.34),(91.44,182.88),(96.52,182.88),(101.6,182.88),(101.6,180.34)); J(96.52,182.88); G(96.52,182.88)
# Service header.
for y,n in [(180.34,'LDO_3V3'),(182.88,'PDCTRL_SCL'),(185.42,'PDCTRL_SDA')]:
    W((43.18,y),(38.1,y)); LBL(n,38.1,y,'right')
W((43.18,187.96),(40.64,187.96)); G(40.64,187.96)
notes=[
'5-20V SPR; ADCIN2=7 selects maximum per TI EVM Guide.',
'Read accepted PDO/RDO before raising charger/load limits; 5V default is not 2A permission.',
'Enforce 100mA SDP attach policy; implement USB suspend separately.',
'TVS2200 clamp max exceeds 28V abs max; qualify controller-pin transients.',
'Validate shared ~50uF bank bias and ramps; details: ai-files/reports/5-20v-pd-front-end-review.md.']
for i,n in enumerate(notes):sch.append(text(n,160.0,156.0+i*3.8,1.0))

# Add candidate metadata while preserving the original USB_PD child sheet UUID and U11 symbol UUID.
Path('ai-files/candidates/TPS25730D_USB_PD_candidate.kicad_sch').write_text('('+sx.dumps(sch[0])+'\n'+'\n'.join(sx.dumps(a) for a in sch[1:])+')\n')
Path('ai-files/candidates/TPS25730D.kicad_sym').write_text(sx.dumps([S('kicad_symbol_lib'),[S('version'),20250120],[S('generator'),'kicad_symbol_editor'],tps])+'\n')
Path('ai-files/candidates/fp-lib-table').write_text('(fp_lib_table\n  (version 7)\n  (lib (name "TPS25730D") (type "KiCad") (uri "${KIPRJMOD}/TPS25730D.pretty") (options "") (descr "TI REF0038A WQFN-38 two exposed pads"))\n)\n')
print('Wrote candidate schematic; C180 retired, retained U11/U19 identities; active files not touched.')
