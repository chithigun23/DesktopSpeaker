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
    right=[('CAP_MIS','6','open_collector',20.32),('SINK_EN','19','open_collector',15.24),('EVENT','37','open_collector',10.16),('FLIP','13','open_collector',5.08),('DBG_ACC','10','open_collector',0),('RESERVED','[26-27,36]','passive',-5.08),('DRAIN','15','passive',-10.16),('DRAIN','30','passive',-15.24),('DRAIN','40','passive',-20.32)]
    for n,num,t,y in right:pins.append(pin(n,num,t,'R',y))
    # The datasheet identifies these pads as electrically common; native stacks retain physical pin numbers.
    top=[('VBUS_IN','[23-25]','power_in',-22.86),('VBUS','[32-33]','power_in',-13.97),('LDO_3V3','1','power_out',-5.08),('LDO_1V5','4','power_out',5.08),('VIN_3V3','38','power_in',13.97),('PPHV','[20-22]','power_out',22.86)]
    for n,num,t,x in top:pins.append(pin(n,num,t,'T',30.48,x))
    pins.append(pin('GND','[11-12,14,16-17,31,34-35,39]','power_in','B',-30.48,-22.86))
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
    return a
def text(s,x,y,size=1.27):return [S('text'),s,[S('at'),x,y,0],[S('effects'),[S('font'),[S('size'),size,size]],[S('justify'),S('left'),S('bottom')]],[S('uuid'),uid()]]

base=sx.loads(Path('DesktopSpeaker-kicad/USB_PD.kicad_sch').read_text())
oldlibs=one(base,'lib_symbols')
need=['PD_C:PD_C','PD_R:PD_R','PD_SERVICE_HDR:PD_SERVICE_HDR','TVS2200DRVR:TVS2200DRVR','ESDA25L:ESDA25L','TPS7B8450QWDRBRQ1:TPS7B8450QWDRBRQ1','power:GND']
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
 ('C2','1uF X7R 50V CVBUS',198.12,82.55,'DesktopSpeaker:PD_C_1210'),
 ('C6','10uF X7R 10V',215.90,82.55,'DesktopSpeaker:PD_C_0805'),
 ('C181','10uF X7R 10V',226.06,82.55,'DesktopSpeaker:PD_C_0805'),
 ('C185','10uF X7R 10V CVIN_3V3',234.95,82.55,'DesktopSpeaker:PD_C_0805'),
 ('C182','330pF C0G CC1 filter',166.37,123.19,'DesktopSpeaker:PD_C_0603'),
 ('C183','330pF C0G CC2 filter',186.69,125.73,'DesktopSpeaker:PD_C_0603'),
 ('C184','1uF X7R 50V',91.44,208.28,'DesktopSpeaker:PD_C_0805'),
 ('C5','4.7uF X7R 50V',134.62,208.28,'DesktopSpeaker:PD_C_1206')]:add('PD_C:PD_C',ref,val,x,y,fp)
for ref,val,x,y in [('R10','200k 1%',149.86,129.54),('R11','10k 1%',149.86,142.24),('R12','100k 1%',265.43,95.25),('R13','10k 1%',182.88,151.13)]:add('PD_R:PD_R',ref,val,x,y,'DesktopSpeaker:PD_R_0603')
# Populate only exact known purchasing matches; leave R10 unselected (200k has no
# matching BOM record). Capacitor curves still need effective-value qualification.
def purchasing(ref, manufacturer, mpn, lcsc, datasheet=''):
    inst=next(i for i in items if any(k(p)=='property' and p[1]=='Reference' and p[2]==ref for p in i))
    at=one(inst,'at')
    for n,v in [('Manufacturer',manufacturer),('MPN',mpn),('LCSC Part',lcsc),('LCSC',lcsc)]: inst.append(prop(n,v,at[1],at[2],True))
    if datasheet: inst.append(prop('Datasheet',datasheet,at[1],at[2],True))
for ref in ('C6','C181','C185'):
    purchasing(ref,'Samsung Electro-Mechanics','CL21B106KPQNNNE','C32635','${KIPRJMOD}/../ai-files/datasheets/Samsung_CL21B106KPQNNNE.pdf')
purchasing('C184','Samsung Electro-Mechanics','CL21B105KBFNNNE','C28323','https://www.lcsc.com/datasheet/C28323.pdf')
purchasing('R11','YAGEO','RC0603FR-0710KL','C98220','${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf')
purchasing('R12','YAGEO','RC0603FR-07100KL','C14675','${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf')
purchasing('R13','YAGEO','RC0603FR-0710KL','C98220','${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf')
add('PD_SERVICE_HDR:PD_SERVICE_HDR','J4','I2C service',64.77,246.38,'DesktopSpeaker:PD_SERVICE_HDR')
def locate(i,refxy,valxy):
    for a in i:
        if k(a)=='property' and a[1] in ('Reference','Value'):one(a,'at')[1:3]=refxy if a[1]=='Reference' else valxy
locate(items[0],(220.98,165.10),(220.98,167.64));locate(items[1],(110.49,218.44),(110.49,220.98))
for i in items[2:]:
    ref=next((a[2] for a in i if k(a)=='property' and a[1]=='Reference'),'');at=one(i,'at')
    if ref in ('C2','C6','C181','C185'):
        dx={'C2':(5.08,-7.62),'C6':(-1.27,-10.16),'C181':(3.81,10.16),'C185':(7.62,-7.62)}[ref]
        locate(i,(at[1]+dx[0],at[2]+dx[1]),(at[1]+dx[0],at[2]+dx[1]+2.54))
    elif ref=='J4':locate(i,(72.39,241.3),(72.39,243.84))
    else:locate(i,(at[1]+6.35,at[2]-1.27),(at[1]+6.35,at[2]+1.27))
sch.extend(items)
def stub(x1,y1,x2,y2,name,shape=None):
    sch.append(wire((x1,y1),(x2,y2)));just='right' if x2<x1 else 'left'
    sch.append(hlabel(name,x2,y2,shape,just) if shape else local_label(name,x2,y2,just))
def junc(x,y):sch.append([S('junction'),[S('at'),x,y],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),uid()]])
# Raw VBUS input rail to D6, C2 and the two raw controller pin groups.
stub(110.49,95.25,74.93,95.25,'USB_VBUS','input')
sch.append(wire((110.49,96.52),(110.49,95.25)));sch.append(wire((110.49,95.25),(198.12,95.25)))
sch.append(wire((198.12,109.22),(198.12,95.25)));sch.append(wire((207.01,109.22),(207.01,95.25)));sch.append(wire((198.12,95.25),(207.01,95.25)))
sch.append(wire((198.12,78.74),(198.12,95.25)));sch.append(wire((198.12,86.36),(198.12,90.17)));sch.append(ground(198.12,90.17))
# D6 ground stack plus the exposed pad, all joined at the local ground point.
sch.append(wire((113.03,104.14),(110.49,104.14)));sch.append(ground(110.49,104.14))
# Direct bypass from each upper functional supply pin. VIN_3V3 is deliberately held low.
for x in (215.90,226.06,234.95):sch.append(wire((x,109.22),(x,78.74)))
for x in (215.90,226.06,234.95):
    sch.append(wire((x,86.36),(x,90.17)));sch.append(ground(x,90.17))
sch.append(local_label('PD_LDO_3V3',215.90,100.33))
sch.append(wire((234.95,95.25),(265.43,95.25)));junc(265.43,95.25);sch.append(local_label('VIN_3V3_LOW',234.95,95.25))
sch.append(wire((265.43,91.44),(265.43,95.25)));sch.append(local_label('VIN_3V3_LOW',265.43,91.44));sch.append(wire((265.43,99.06),(265.43,102.87)));sch.append(ground(265.43,102.87))
# Managed power output and common grounds.
stub(243.84,109.22,285.75,109.22,'VBUS_PD','output')
sch.append(wire((198.12,152.40),(198.12,158.75)));sch.append(ground(198.12,158.75))
# Connector-to-controller CC wires pass directly through the protected region; D5 is a shunt clamp.
stub(104.14,119.38,73.66,119.38,'USB_CC1','input');sch.append(wire((104.14,119.38),(195.58,119.38)))
stub(104.14,121.92,73.66,121.92,'USB_CC2','input');sch.append(wire((104.14,121.92),(195.58,121.92)))
# D5 pin1 lands on CC1; pin2 rises to CC2. Filter capacitor tops land on each trace.
sch.append(wire((134.62,124.46),(134.62,121.92)));junc(134.62,119.38);junc(134.62,121.92)
junc(166.37,119.38);sch.append(wire((166.37,127.0),(166.37,130.81)));sch.append(ground(166.37,130.81))
junc(186.69,121.92);sch.append(wire((186.69,129.54),(186.69,133.35)));sch.append(ground(186.69,133.35))
sch.append(ground(139.70,129.54))
# Type-C control, ADC straps and adjacent divider.
stub(195.58,124.46,151.13,124.46,'PDCTRL_SDA','bidirectional');stub(195.58,127.0,151.13,127.0,'PDCTRL_SCL','bidirectional')
stub(195.58,132.08,180.34,132.08,'PD_LDO_3V3')
sch.append(wire((195.58,137.16),(160.02,137.16)));sch.append(wire((160.02,137.16),(160.02,138.43)));sch.append(wire((160.02,138.43),(149.86,138.43)))
sch.append(wire((149.86,133.35),(149.86,138.43)));sch.append(local_label('PD_LDO_3V3',149.86,125.73));sch.append(wire((149.86,146.05),(149.86,149.86)));sch.append(ground(149.86,149.86))
# FAULT_IN gets a 10k pullup to controller LDO_3V3; status outputs face right.
stub(195.58,139.70,184.15,139.70,'PD_FAULT_IN');sch.append(local_label('PD_LDO_3V3',182.88,147.32));sch.append(wire((182.88,154.94),(182.88,158.75)));sch.append(local_label('PD_FAULT_IN',182.88,158.75))
# U19 is raw-connector auxiliary 5V only; both bypasses are wired at its pins.
stub(97.79,203.20,82.55,203.20,'USB_VBUS');stub(97.79,213.36,82.55,213.36,'USB_VBUS')
sch.append(wire((123.19,200.66),(138.43,200.66)));sch.append(hlabel('USB_AUX_5V',138.43,200.66,'output','left'))
sch.append(wire((91.44,204.47),(91.44,203.20)));sch.append(wire((91.44,203.20),(97.79,203.20)));sch.append(wire((91.44,212.09),(91.44,215.90)));sch.append(ground(91.44,215.90))
sch.append(wire((134.62,204.47),(134.62,200.66)));sch.append(wire((134.62,212.09),(134.62,215.90)));sch.append(ground(134.62,215.90));junc(134.62,200.66)
sch.append(wire((105.41,223.52),(105.41,229.87)));sch.append(wire((105.41,229.87),(93.98,229.87)));sch.append(wire((93.98,229.87),(93.98,237.49)));sch.append(ground(93.98,237.49))
sch.append(wire((115.57,223.52),(115.57,229.87)));sch.append(wire((115.57,229.87),(125.73,229.87)));sch.append(wire((125.73,229.87),(125.73,237.49)));sch.append(ground(125.73,237.49))
for y,n in [(243.84,'3V_AO'),(246.38,'PDCTRL_SCL'),(248.92,'PDCTRL_SDA')]:stub(59.69,y,49.53,y,n)
sch.append(wire((59.69,251.46),(52.07,251.46)));sch.append(ground(52.07,251.46))
# Five concise open gates; details and primary evidence are in the candidate review report.
notes=[
'5–20V SPR; ADCIN2=7 selects maximum per TI EVM Guide.',
'Read accepted PDO/RDO before raising charger/load limits; 5V default is not 2A permission.',
'Enforce 100mA SDP attach policy; implement USB suspend separately.',
'TVS2200 clamp max exceeds 28V abs max; qualify controller-pin transients.',
'Validate shared ~50uF bank bias and ramps; details: ai-files/reports/5-20v-pd-front-end-review.md.'
]
for i,n in enumerate(notes):sch.append(text(n,145.0,126.0+i*4.2,1.0))

# Side-bank labels bridge the longer-spacing functional pinfield to the existing
# short, routed signal sections. Grounds and intentional drain N/Cs remain explicit.
for name,y in [('USB_CC1',109.22),('USB_CC2',114.30),('PDCTRL_SDA',119.38),('PDCTRL_SCL',124.46),('PD_LDO_3V3',134.62),('ADC4_DIV',144.78),('PD_FAULT_IN',149.86)]:
    sch.append(wire((190.50,y),(184.15,y)))
    sch.append(hlabel(name,184.15,y,'input' if name.startswith('USB_CC') else ('bidirectional' if name.startswith('PDCTRL_') else 'input'),'right'))
ground(190.50,129.54);ground(190.50,139.70)
for name,y in [('PD_CAP_MIS',109.22),('PD_SINK_EN',114.30),('PD_PLUG_EVENT',119.38),('PD_PLUG_FLIP',124.46),('PD_DBG_ACC',129.54)]:
    sch.append(wire((251.46,y),(257.81,y)))
    sch.append(hlabel(name,257.81,y,'output','left'))
ground(251.46,134.62)
for y in (139.70,144.78,149.86):sch.append([S('no_connect'),[S('at'),251.46,y],[S('uuid'),uid()]])
sch.append(wire((190.50,134.62),(184.15,134.62)));sch.append(local_label('PD_LDO_3V3',184.15,134.62,'right'))
sch.append(wire((190.50,144.78),(184.15,144.78)));sch.append(local_label('ADC4_DIV',184.15,144.78,'right'))
# Side stubs to the established traces are short and orthogonal where the nets
# were already routed. Top bypass and shared ground rows connect directly.
for x in (198.12,207.01,215.90,226.06,234.95,243.84):sch.append(wire((x,99.06),(x,109.22)))
sch.append(wire((198.12,158.75),(198.12,160.02)))

# Move the A4 landscape sheet down to fit the lower connector block.
def translate_sheet_y(node):
    if not isinstance(node,list): return
    if node and k(node)=='lib_symbols': return
    if k(node) in ('at','xy','start','end') and len(node)>=3 and isinstance(node[2],(int,float)):
        node[2]=round(node[2]-50,4)
    for child in node:translate_sheet_y(child)
translate_sheet_y(sch)

# Add candidate metadata while preserving the original USB_PD child sheet UUID and U11 symbol UUID.
Path('ai-files/candidates/TPS25730D_USB_PD_candidate.kicad_sch').write_text('('+sx.dumps(sch[0])+'\n'+'\n'.join(sx.dumps(a) for a in sch[1:])+')\n')
Path('ai-files/candidates/TPS25730D.kicad_sym').write_text(sx.dumps([S('kicad_symbol_lib'),[S('version'),20250120],[S('generator'),'kicad_symbol_editor'],tps])+'\n')
Path('ai-files/candidates/fp-lib-table').write_text('(fp_lib_table\n  (version 7)\n  (lib (name "TPS25730D") (type "KiCad") (uri "${KIPRJMOD}/TPS25730D.pretty") (options "") (descr "TI REF0038A WQFN-38 two exposed pads"))\n)\n')
print('Wrote candidate schematic; C180 retired, retained U11/U19 identities; active files not touched.')
