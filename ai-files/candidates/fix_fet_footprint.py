from pathlib import Path
import re,uuid
p=Path('ai-files/candidates/CSD17579Q3A_DNH0008A.kicad_mod')
s=p.read_text()
# Extract every top-level footprint pad expression.
starts=[m.start() for m in re.finditer(r'\t\(pad ',s)]
blocks=[]
for st in starts:
 level=0;quote=False;esc=False
 for i in range(st,len(s)):
  c=s[i]
  if quote:
   if esc:esc=False
   elif c=='\\':esc=True
   elif c=='"':quote=False
   continue
  if c=='"':quote=True
  elif c=='(':level+=1
  elif c==')':
   level-=1
   if level==0:blocks.append((st,i+1,s[st:i+1]));break
# Correct terminal paste openings: numbered side lands provide 0.6 x 0.3 apertures.
kept=[]
for st,en,b in blocks:
 if '(pad "9" smd custom' in b:
  poly='''\t(pad "9" smd custom
\t\t(at 0.3275 0)
\t\t(size 1.775 2.45)
\t\t(layers "F.Cu" "F.Mask")
\t\t(thermal_bridge_angle 45)
\t\t(options (clearance outline) (anchor rect))
\t\t(primitives
\t\t\t(gr_poly
\t\t\t\t(pts
\t\t\t\t\t(xy -0.8875 -1.225) (xy 0.8875 -1.225)
\t\t\t\t\t(xy 0.8875 -1.125) (xy 1.2225 -1.125) (xy 1.2225 -0.825) (xy 0.8875 -0.825)
\t\t\t\t\t(xy 0.8875 -0.475) (xy 1.2225 -0.475) (xy 1.2225 -0.175) (xy 0.8875 -0.175)
\t\t\t\t\t(xy 0.8875 0.175) (xy 1.2225 0.175) (xy 1.2225 0.475) (xy 0.8875 0.475)
\t\t\t\t\t(xy 0.8875 0.825) (xy 1.2225 0.825) (xy 1.2225 1.125) (xy 0.8875 1.125)
\t\t\t\t\t(xy 0.8875 1.225) (xy -0.8875 1.225)
\t\t\t\t)
\t\t\t\t(width 0) (fill yes)
\t\t\t)
\t\t)
\t\t(uuid "'''+str(uuid.uuid4())+'''”)
\t)'''.replace('”','"')
  kept.append((st,en,poly))
 elif '(pad "" smd rect' in b:
  m=re.search(r'\(at ([^ ]+) ([^ )]+)\)',b); x,y=map(float,m.groups())
  # Four TI stencil windows: 0.705 x 1.125 mm; columns 0.905 mm apart and rows 1.325 mm apart.
  if abs(x-(-.09))<.01 or abs(x-.86)<.01:
   ix= -.125 if x<0 else .78
   iy= -.6625 if y<0 else .6625
   b=re.sub(r'\(at [^ )]+ [^ )]+\)',f'(at {ix} {iy})',b,count=1)
   b=re.sub(r'\(size [^ )]+ [^ )]+\)', '(size 0.705 1.125)',b,count=1)
   b=re.sub(r'\(uuid "[^"]+"\)',f'(uuid "{uuid.uuid4()}")',b,count=1)
   kept.append((st,en,b))
  else:
   # obsolete four separate terminal apertures, now supplied by pads5–8
   pass
 elif '(pad "" smd roundrect' in b:
  # obsolete overlapping 0.63 x0.5 mm drain terminal paste helpers
  pass
 else: kept.append((st,en,b))
# Replace from end to start to preserve non-pad text.
for st,en,b in reversed(kept):s=s[:st]+b+s[en:]
# Remove discarded pad expressions left in the original by reconstructing between pads from filtered source positions is tricky;
# Repeat a top-level expression pass and drop obsolete unnamed pads.
starts=[m.start() for m in re.finditer(r'\t\(pad ',s)]; out=[]; pos=0
for st in starts:
 out.append(s[pos:st]);level=0;quote=False;esc=False
 for i in range(st,len(s)):
  c=s[i]
  if quote:
   if esc:esc=False
   elif c=='\\':esc=True
   elif c=='"':quote=False
   continue
  if c=='"':quote=True
  elif c=='(':level+=1
  elif c==')':
   level-=1
   if level==0:en=i+1;break
 b=s[st:en]
 if not ('(pad "" smd roundrect' in b):out.append(b)
 pos=en
out.append(s[pos:]); s=''.join(out)
# add four newly distinct drain terminal pads
pads=''
for n,y in [(8,-.975),(7,-.325),(6,.325),(5,.975)]:
 pads+=f'''\t(pad "{n}" smd roundrect
\t\t(at 1.55 {y:.3f})
\t\t(size 0.6 0.3)
\t\t(layers "F.Cu" "F.Mask" "F.Paste")
\t\t(roundrect_rratio 0.16)
\t\t(uuid "{uuid.uuid4()}")
\t)
'''
s=s.replace('\t(embedded_fonts no)',pads+'\t(embedded_fonts no)')
p.write_text(s)
