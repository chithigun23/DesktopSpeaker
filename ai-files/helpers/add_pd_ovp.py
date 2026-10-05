#!/usr/bin/env python3
"""One-shot USB_PD 20 V DC tolerance capture. Do not rerun over later edits."""
import copy, pathlib, shutil, sys, uuid
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'vendor'))
from sexpdata import Symbol as S, load, dumps
root=pathlib.Path(__file__).resolve().parents[2]
pr=root/'DesktopSpeaker-kicad'; schpath=pr/'USB_PD.kicad_sch'
syms=pr/'kicad-library/schematic'; fps=pr/'kicad-library/footprint'; models=pr/'kicad-library/3d'
srcfp=next(pathlib.Path('/home/chithi/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Footprints').rglob('Package_SO.pretty/HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3x3mm.kicad_mod')).parent.parent
src3d=next(pathlib.Path('/home/chithi/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Packages3D').rglob('Diode_SMD.3dshapes/D_SMA.step')).parent.parent
def k(v):return str(v[0]) if isinstance(v,list) and v else ''
def sub(v,n):return next(x for x in v if k(x)==n)
def uid():return str(uuid.uuid4())
def eff(h=False,j=None):
 v=[S('effects'),[S('font'),[S('size'),1.27,1.27]]]
 if j:v.append([S('justify'),S(j)])
 if h:v.append([S('hide'),S('yes')])
 return v
def prop(n,v,x,y,h=False,j=None):return [S('property'),n,v,[S('at'),x,y,0],eff(h,j)]
def pin(n,num,x,y,a,t='passive'):
 return [S('pin'),S(t),S('line'),[S('at'),x,y,a],[S('length'),2.54],[S('name'),n,eff()],[S('number'),num,eff()]]
def line(a,b):return [S('wire'),[S('pts'),[S('xy'),*a],[S('xy'),*b]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),uid()]]
def junction(x,y):return [S('junction'),[S('at'),x,y],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),uid()]]
def label(n,x,y):return [S('label'),n,[S('at'),x,y,0],[S('effects'),[S('font'),[S('size'),1,1]],[S('justify'),S('right'),S('bottom')]],[S('uuid'),uid()]]
def symbol_lib(n,body,pins,fp,ds):
 v=[S('symbol'),n,[S('in_bom'),S('yes')],[S('on_board'),S('yes')],prop('Reference',n[0],0,20.32),prop('Value',n,0,-20.32),prop('Footprint','DesktopSpeaker:'+fp,0,0,True),prop('Datasheet',ds,0,0,True),[S('symbol'),n+'_0_1',*body],[S('symbol'),n+'_1_1',*pins],[S('embedded_fonts'),S('no')]]
 (syms/(n+'.kicad_sym')).write_text(dumps([S('kicad_symbol_lib'),[S('version'),20231120],[S('generator'),S('kicad_symbol_editor')],v])+'\n')
 e=copy.deepcopy(v);e[1]=n+':'+n;lib.append(e)
 return v
def rect(x1,y1,x2,y2):return [S('rectangle'),[S('start'),x1,y1],[S('end'),x2,y2],[S('stroke'),[S('width'),0.254],[S('type'),S('default')]],[S('fill'),[S('type'),S('background')]]]
def inst(n,ref,x,y,value,fp,ds,mpn,lcsc,coords,pins,ic=False):
 v=[S('symbol'),[S('lib_id'),n+':'+n],[S('at'),x,y,0],[S('unit'),1],[S('exclude_from_sim'),S('no')],[S('in_bom'),S('yes')],[S('on_board'),S('yes')],[S('dnp'),S('no')],[S('uuid'),uid()],prop('Reference',ref,*coords[0],j='left' if not ic else None),prop('Value',value,*coords[1],j='left' if not ic else None),prop('Footprint','DesktopSpeaker:'+fp,x,y,True),prop('Datasheet',ds,x,y,True),prop('MPN',mpn,x,y,True),prop('LCSC Part',lcsc,x,y,True),*[[S('pin'),p,[S('uuid'),uid()]] for p in pins],[S('instances'),[S('project'),'DesktopSpeaker',[S('path'),path,[S('reference'),ref],[S('unit'),1]]]]]
 sch.append(v);return v
def gnd(x,y,ref):
 v=copy.deepcopy(gnd_template); ox,oy=sub(v,'at')[1:3]; sub(v,'at')[1:3]=[x,y];sub(v,'uuid')[1]=uid()
 for p in v:
  if k(p)=='property':
   if p[1]=='Reference':p[2]=ref
   at=sub(p,'at');at[1]+=x-ox;at[2]+=y-oy
  if k(p)=='pin':sub(p,'uuid')[1]=uid()
 sub(v,'instances')[1][2][2][1]=ref;sch.append(v)
def copyfp(srcname,dstname,category,modelname=None):
 src=srcfp/category/(srcname+'.kicad_mod'); t=src.read_text().replace('(footprint "'+srcname+'"','(footprint "'+dstname+'"',1)
 t=t.replace('${KICAD10_3DMODEL_DIR}/'+category.replace('.pretty','.3dshapes')+'/'+srcname+'.step', '${KIPRJMOD}/kicad-library/3d/'+dstname+'.step')
 if modelname is None:t='\n'.join(z for z in t.splitlines() if 'KICAD10_3DMODEL_DIR' not in z)
 (fps/(dstname+'.kicad_mod')).write_text(t)
 if modelname:shutil.copyfile(src3d/category.replace('.pretty','.3dshapes')/(modelname+'.step'),models/(dstname+'.step'))
sch=load(open(schpath));lib=sub(sch,'lib_symbols');gnd_template=next(v for v in sch if k(v)=='symbol' and sub(v,'lib_id')[1]=='power:GND');path=sub(next(v for v in sch if k(v)=='symbol'),'instances')[1][2][1]
assert not any(k(v)=='symbol' and any(k(p)=='property' and p[1]=='Reference' and p[2] in ('U18','D7','D8') for p in v) for v in sch)
shutil.copy2(schpath,root/'ai-files/backups/USB_PD-before-20v-ovp-2026-10-04.kicad_sch')

# D6 remains at its user-selected coordinates. Its package is replaced by a six-terminal TI DRV TVS.
d6=next(v for v in sch if k(v)=='symbol' and any(k(p)=='property' and p[1]=='Reference' and p[2]=='D6' for p in v))
sub(d6,'lib_id')[1]='TVS2200DRVR:TVS2200DRVR'
for p in d6:
 if k(p)=='property':
  if p[1]=='Value':p[2]='TVS2200DRVR'
  elif p[1]=='Footprint':p[2]='DesktopSpeaker:TVS2200DRVR'
  elif p[1]=='Datasheet':p[2]='https://www.ti.com/lit/ds/symlink/tvs2200.pdf'
  elif p[1]=='MPN':p[2]='TVS2200DRVR'
  elif p[1]=='LCSC Part':p[2]='C523793'
pins_d6=[p for p in d6 if k(p)=='pin']
for p in pins_d6:d6.remove(p)
for p in ('1','2','3','4','5','6','7'):d6.insert(-1,[S('pin'),p,[S('uuid'),uid()]])
tvspins=[pin('IN','[4-6]',0,3.81,270),pin('GND','[1-3]',0,-3.81,90),pin('EP','7',2.54,-3.81,90)]
symbol_lib('TVS2200DRVR',[rect(-3.81,1.27,3.81,-1.27)],tvspins,'TVS2200DRVR','https://www.ti.com/lit/ds/symlink/tvs2200.pdf')
# Existing D6 cathode/anode coordinates are unchanged. Tie EP7 to its ground section.
sch.append(line((71.12,72.39),(71.12,77.47)));sch.append(line((68.58,77.47),(71.12,77.47)));sch.append(junction(68.58,77.47))

zp=[pin('K/source','1',0,3.81,270),pin('A/gate','2',0,-3.81,90)]
symbol_lib('BZT52C12-7-F',[rect(-1.27,1.27,1.27,-1.27)],zp,'BZT52C12-7-F','https://www.diodes.com/assets/Datasheets/ds18001.pdf')
inst('BZT52C12-7-F','D7',260.35,110.49,'12V', 'BZT52C12-7-F','https://www.diodes.com/assets/Datasheets/ds18001.pdf','BZT52C12-7-F','C124196',((266.7,109.22),(266.7,111.76)),('1','2'))
sch.extend([line((260.35,106.68),(260.35,101.6)),line((260.35,101.6),(279.4,101.6)),junction(260.35,101.6),line((260.35,114.3),(260.35,123.19)),junction(260.35,123.19)])

# Native KiCad 10 pin stacks map both IN and both OUT package terminals.
epins=[pin('IN','[1-2]',-15.24,12.7,0,'power_in'),pin('OUT','[15-16]',15.24,12.7,180,'power_out'),pin('OVP','5',-15.24,7.62,0,'input'),pin('UVLO','3',-15.24,2.54,0,'input'),pin('SHDN','7',-15.24,-2.54,0,'input'),pin('MODE','6',-15.24,-7.62,0,'input'),pin('ILIM','11',15.24,2.54,180,'input'),pin('FLT','14',15.24,-2.54,180,'open_collector'),pin('IMON','10',15.24,-7.62,180,'output'),pin('dVdT','12',15.24,-12.7,180,'input'),pin('RTN','8',-5.08,-20.32,90,'power_in'),pin('GND','9',0,-20.32,90,'power_in'),pin('EP','17',5.08,-20.32,90,'power_in'),pin('NC','4',-10.16,-20.32,90,'no_connect'),pin('NC','13',10.16,-20.32,90,'no_connect')]
symbol_lib('TPS26600PWPR',[rect(-12.7,17.78,12.7,-17.78)],epins,'TPS26600PWPR','https://www.ti.com/lit/ds/symlink/tps2660.pdf')
inst('TPS26600PWPR','U18',344.17,76.2,'TPS26600PWPR','TPS26600PWPR','https://www.ti.com/lit/ds/symlink/tps2660.pdf','TPS26600PWPR','C544399',((344.17,100.33),(344.17,102.87)),('1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17'),True)
# Split former Q2-to-port direct conductor. Branches at x350.52 retain downstream rail.
old=next(v for v in sch if k(v)=='wire' and sub(v,'pts')[1][1:]==[279.4,39.37] and sub(v,'pts')[2][1:]==[350.52,39.37]);sch.remove(old)
sch.extend([line((279.4,39.37),(322.58,39.37)),line((322.58,39.37),(322.58,63.5)),line((322.58,63.5),(328.93,63.5)),line((322.58,63.5),(322.58,78.74)),line((322.58,73.66),(328.93,73.66)),line((322.58,78.74),(328.93,78.74)),junction(322.58,63.5),junction(322.58,73.66),line((359.41,63.5),(375.92,63.5)),line((375.92,63.5),(375.92,39.37)),line((350.52,39.37),(375.92,39.37)),junction(375.92,39.37)])
# OVP divider, local input trace to top resistor and remote label to OVP input.
inst('PD_R','R180',307.34,68.58,'100k 1%','PD_R_0603','','','',((312.42,67.31),(312.42,69.85)),('1','2'))
inst('PD_R','R181',307.34,93.98,'12.1k 1%','PD_R_0603','','','',((312.42,92.71),(312.42,95.25)),('1','2'))
sch.extend([line((307.34,39.37),(307.34,64.77)),junction(307.34,39.37),line((307.34,72.39),(307.34,90.17)),line((307.34,97.79),(307.34,104.14)),line((307.34,83.82),(315.0,83.82)),label('OVP_11V',315.0,83.82),line((320.04,68.58),(328.93,68.58)),label('OVP_11V',320.04,68.58),junction(307.34,83.82)])
gnd(307.34,104.14,'#PWR17')
inst('PD_R','R182',381.0,85.09,'5.36k 1%','PD_R_0603','','','',((386.08,83.82),(386.08,86.36)),('1','2'))
sch.extend([line((359.41,73.66),(381.0,73.66)),line((381.0,73.66),(381.0,81.28)),line((381.0,88.9),(381.0,101.6))]);gnd(381.0,101.6,'#PWR18')
sch.extend([line((328.93,83.82),(317.5,83.82)),line((317.5,83.82),(317.5,109.22))]);gnd(317.5,109.22,'#PWR19')
for x,ref in ((339.09,'#PWR20'),(344.17,'#PWR21'),(349.25,'#PWR22')):sch.append(line((x,96.52),(x,109.22)));gnd(x,109.22,ref)
sch.extend([[S('no_connect'),[S('at'),359.41,78.74],[S('uuid'),uid()]],[S('no_connect'),[S('at'),359.41,83.82],[S('uuid'),uid()]],[S('no_connect'),[S('at'),359.41,88.9],[S('uuid'),uid()]]])

# 10 V output TVS protects active charger during eFuse's finite OVP delay.
symbol_lib('SMA6J10A',[rect(-1.27,1.27,1.27,-1.27)],[pin('K','1',0,3.81,270),pin('A','2',0,-3.81,90)],'SMA6J10A','https://www.littelfuse.com/assetdocs/tvs-diodes-sma6j-datasheet?assetguid=1bf347a3-17d1-4456-ac34-423c2a51943b')
inst('SMA6J10A','D8',394.97,75.565,'SMA6J10A','SMA6J10A','https://www.littelfuse.com/assetdocs/tvs-diodes-sma6j-datasheet?assetguid=1bf347a3-17d1-4456-ac34-423c2a51943b','SMA6J10A','',((400.05,74.295),(400.05,76.835)),('1','2'))
sch.extend([line((375.92,39.37),(394.97,39.37)),line((394.97,39.37),(394.97,71.755)),line((394.97,79.375),(394.97,88.265)),junction(394.97,39.37)]);gnd(394.97,88.265,'#PWR23')

# R4 discharge/sense current at a valid 21 V contract warrants a larger resistor.
r4=next(v for v in sch if k(v)=='symbol' and any(k(p)=='property' and p[1]=='Reference' and p[2]=='R4' for p in v))
for p in r4:
 if k(p)=='property' and p[1]=='Value':p[2]='3.3k'
 if k(p)=='property' and p[1]=='Footprint':p[2]='DesktopSpeaker:PD_R_1206'

# Local footprint/model assets. Native manufacturer DRV bottom view: IN 4-6, GND 1-3/EP7.
copyfp('WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm','TVS2200DRVR','Package_SON.pretty','WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm')
copyfp('D_SOD-123','BZT52C12-7-F','Diode_SMD.pretty','D_SOD-123')
copyfp('D_SMA','SMA6J10A','Diode_SMD.pretty','D_SMA')
copyfp('R_1206_3216Metric','PD_R_1206','Resistor_SMD.pretty',None)
copyfp('HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3x3mm','TPS26600PWPR','Package_SO.pretty',None)
schpath.write_text(dumps(sch)+'\n')
