import re
s=open('DesktopSpeaker-kicad/Logic_Audio_Power.kicad_sch').read()
toks=re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',s)
i=0
def parse():
 global i
 x=toks[i];i+=1
 if x=='(':
  a=[]
  while toks[i]!=')':a.append(parse())
  i+=1;return a
 if x.startswith('"'):return bytes(x[1:-1],'utf8').decode('unicode_escape')
 return x
root=parse()
def head(x): return x[0] if isinstance(x,list) and x else None
for x in root:
 if head(x)=='lib_symbols':
  for sym in x:
   if head(sym)=='symbol' and sym[1] in ('TPS61023DRLT:TPS61023DRLT','TPS63802DLAR:TPS63802DLAR'):
    print('LIB',sym[1]); print(sym)
for x in root:
 if head(x)=='symbol':
  ref=next((q[2] for q in x if head(q)=='property' and q[1]=='Reference'),None)
  if ref in ['U14','L2','R140','R141','R142']:
   print('\nINST',ref, x)
for x in root:
 if head(x) in ['wire','junction','no_connect','label','global_label','symbol']:
  txt=repr(x)
  if any(z in txt for z in [' 139.7',' 152.4',' 127',' 69.85','U14']): print('GEOM',x)
