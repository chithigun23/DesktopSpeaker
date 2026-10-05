"""Activate reviewed TI ship-FET assets; no schematic placement."""
from pathlib import Path
import sys,hashlib,shutil,json
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ai-files/vendor'))
from sexpdata import load,dumps,Symbol as S
def k(a):return str(a[0]) if isinstance(a,list) and a else ''
def one(a,n):return next(v for v in a if k(v)==n)
c=ROOT/'ai-files/candidates';lib=ROOT/'DesktopSpeaker-kicad/kicad-library'
sym=load(open(c/'CSD17579Q3A.kicad_sym'));fp=load(open(c/'CSD17579Q3A_DNH0008A.kicad_mod'))
pins={one(p,'number')[1]:one(p,'name')[1] for sub in one(sym,'symbol') if k(sub)=='symbol' for p in sub if k(p)=='pin'}
assert pins=={'4':'G','[1-3]':'S','[5-9]':'D'}
pads=[p for p in fp if k(p)=='pad'];assert sorted(p[1] for p in pads if p[1])==list('123456789')
windows=[p for p in pads if not p[1]]
assert {tuple(one(p,'at')[1:3]) for p in windows}=={(x,y) for x in [-.208,.697] for y in [-.6625,.6625]}
assert all(one(p,'size')[1:]==[.705,1.125] for p in windows)
ep=next(p for p in pads if p[1]=='9');assert one(ep,'at')[1:3]==[.3275,0] and one(ep,'size')[1:]==[1.775,2.45]
step=c/'DNH0008A.stp';assert hashlib.sha256(step.read_bytes()).hexdigest()=='26822bbb4a4b1874481c18de404dd194dce4554cd319bc6ab12b4c227540200d'
for p in one(sym,'symbol'):
 if k(p)=='property' and p[1]=='Footprint':p[2]='DesktopSpeaker:CSD17579Q3A_DNH0008A'
 if k(p)=='property' and p[1]=='Datasheet':p[2]='${KIPRJMOD}/../ai-files/datasheets/CSD17579Q3A.pdf'
for p in list(fp):
 if k(p)=='model':fp.remove(p)
fp.append([S('model'),'${KIPRJMOD}/kicad-library/3d/DNH0008A.stp',[S('offset'),[S('xyz'),0,0,0]],[S('scale'),[S('xyz'),1,1,1]],[S('rotate'),[S('xyz'),0,0,0]]])
(lib/'schematic/CSD17579Q3A.kicad_sym').write_text(dumps(sym)+'\n')
(lib/'footprint/CSD17579Q3A_DNH0008A.kicad_mod').write_text(dumps(fp)+'\n')
shutil.copy2(step,lib/'3d/DNH0008A.stp')
p=ROOT/'DesktopSpeaker-kicad/sym-lib-table';t=load(open(p))
if not any(k(a)=='lib' and one(a,'name')[1]=='CSD17579Q3A' for a in t):
 t.append([S('lib'),[S('name'),'CSD17579Q3A'],[S('type'),'KiCad'],[S('uri'),'${KIPRJMOD}/kicad-library/schematic/CSD17579Q3A.kicad_sym'],[S('options'),''],[S('descr'),'External charger ship FET, TI DNH0008A']])
p.write_text('(sym_lib_table\n'+''.join('  '+dumps(a)+'\n' for a in t[1:])+')\n')
report={'native_pin_stacks_verified':pins,'pads_1_to_9_verified':True,'TI_copper_anchor_verified':True,'TI_stencil_windows_verified':True,'TI_STEP_hash_verified':True,'model_alignment_evidence':'csd17579-step-parts.json','active_placement':False}
(ROOT/'ai-files/reports/ship-fet-library-activation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
