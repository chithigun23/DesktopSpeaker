"""Activate coordinator-reviewed BQ25792 library assets; no schematic wiring."""
from pathlib import Path
import sys, copy, re, json, hashlib, shutil
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ai-files/vendor'))
from sexpdata import load, dumps, Symbol as S

def k(x): return str(x[0]) if isinstance(x,list) and x else ''
def one(x,n): return next(a for a in x if k(a)==n)
def expanded(n):
    out=[]
    for item in str(n).strip('[]').split(','):
        if '-' in item:
            a,b=map(int,item.split('-'));out.extend(range(a,b+1))
        else:out.append(int(item))
    return out
cand=ROOT/'ai-files/candidates'; lib=ROOT/'DesktopSpeaker-kicad/kicad-library'
sym=load(open(cand/'BQ25792RQMR.kicad_sym'))
fp=load(open(cand/'BQ25792RQMR.kicad_mod'))
expected={1:'STAT',2:'VBUS',3:'VBUS',4:'BTST1',5:'REGN',6:'D+',7:'D−',8:'VAC2',9:'VAC1',10:'ACDRV2',11:'ACDRV1',12:'QON',13:'CE',14:'SCL',15:'SDA',16:'TS',17:'ILIM_HIZ',18:'BATP',19:'BTST2',20:'PROG',21:'INT',22:'BAT',23:'BAT',24:'SDRV',25:'SYS',26:'SW2',27:'GND',28:'SW1',29:'PMID'}
actual={}
for sub in one(sym,'symbol'):
 if k(sub)=='symbol':
  for pin in sub:
   if k(pin)=='pin':
    name=one(pin,'name')[1].replace('~{','').replace('}','')
    for number in expanded(one(pin,'number')[1]):
     assert number not in actual,number
     actual[number]=name
assert actual==expected,(actual,expected)
pads=[a for a in fp if k(a)=='pad']
assert sorted(int(a[1]) for a in pads)==list(range(1,30))
std=Path('/home/chithi/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Footprints/x86_64/beta/active/files/footprints/Package_DFN_QFN.pretty/Texas_RQM0029A_VQFN-29_4x4mm_P0.4mm.kicad_mod')
stdpads=[a for a in load(open(std)) if k(a)=='pad']
assert pads==stdpads,'Footprint pad geometry differs from reviewed installed standard'
step=cand/'RQM0029A.stp'
assert hashlib.sha256(step.read_bytes()).hexdigest()=='2b506f614e8de3b8d4fd691a864bbf33dfe113a3ca635bd76cc83714a26860be'
for p in one(sym,'symbol'):
 if k(p)=='property' and p[1]=='Datasheet':p[2]='${KIPRJMOD}/../ai-files/datasheets/BQ25792.pdf'
for model in [a for a in fp if k(a)=='model']: fp.remove(model)
fp.append([S('model'),'${KIPRJMOD}/kicad-library/3d/RQM0029A.stp',[S('offset'),[S('xyz'),0,0,0]],[S('scale'),[S('xyz'),1,1,1]],[S('rotate'),[S('xyz'),0,0,0]]])
(lib/'schematic/BQ25792RQMR.kicad_sym').write_text(dumps(sym)+'\n')
(lib/'footprint/BQ25792RQMR.kicad_mod').write_text(dumps(fp)+'\n')
shutil.copy2(step,lib/'3d/RQM0029A.stp')
tablepath=ROOT/'DesktopSpeaker-kicad/sym-lib-table';table=load(open(tablepath))
if not any(k(a)=='lib' and one(a,'name')[1]=='BQ25792RQMR' for a in table):
 table.append([S('lib'),[S('name'),'BQ25792RQMR'],[S('type'),'KiCad'],[S('uri'),'${KIPRJMOD}/kicad-library/schematic/BQ25792RQMR.kicad_sym'],[S('options'),''],[S('descr'),'5-20V capable 1S buck-boost charger']])
 tablepath.write_text('(sym_lib_table\n'+''.join('  '+dumps(a)+'\n' for a in table[1:])+')\n')
report={'pin_map_checked':True,'all_29_numbered_pads_checked':True,'pads_equal_installed_standard':True,'TI_STEP_hash_checked':True,'STEP_origin_alignment_evidence':'bq25792-step-parts.json','model_link_resolves':(lib/'3d/RQM0029A.stp').exists(),'schematic_wiring_changed':False}
(ROOT/'ai-files/reports/bq25792-library-activation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
