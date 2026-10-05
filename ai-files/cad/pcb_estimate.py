"""PCB area estimate: netlist (work/net.xml) + footprint courtyards -> work/pcb_estimate.json"""
import re, json, os, collections
import xml.etree.ElementTree as ET
R='/home/chithi/Desktop/DesktopSpeaker/'
FP=R+'DesktopSpeaker-kicad/kicad-library/footprint/'
def bbox(name):
    p=FP+name+'.kicad_mod'
    if not os.path.exists(p): return None
    t=open(p).read()
    def pts(layer):
        xs=[];ys=[]
        for blk in re.findall(r'\((?:fp_line|fp_rect|fp_poly|fp_circle|fp_arc)\b.*?\)\s*\n?\s*\(?(?:layer|stroke|width)[^\n]*',t,re.S):
            pass
        # simple: per-element scan
        for m in re.finditer(r'\(fp_(line|rect|poly|circle)\b(.*?)\(layer "?%s"?\)'%layer,t,re.S):
            body=m.group(2)
            if m.group(1)=='circle':
                c=re.search(r'\(center ([-\d.]+) ([-\d.]+)\)',body);e=re.search(r'\(end ([-\d.]+) ([-\d.]+)\)',body)
                if c and e:
                    cx,cy,ex,ey=map(float,c.groups()+e.groups());r=((cx-ex)**2+(cy-ey)**2)**.5
                    xs+= [cx-r,cx+r];ys+=[cy-r,cy+r]
                continue
            for x,y in re.findall(r'\((?:start|end|xy) ([-\d.]+) ([-\d.]+)\)',body):
                xs.append(float(x));ys.append(float(y))
        return (min(xs),min(ys),max(xs),max(ys)) if xs else None
    b=pts('F.CrtYd') or pts('B.CrtYd')
    src='courtyard'
    if not b:
        xs=[];ys=[]
        for m in re.finditer(r'\(pad .*?\(at ([-\d.]+) ([-\d.]+)(?: [-\d.]+)?\).*?\(size ([-\d.]+) ([-\d.]+)\)',t,re.S):
            x,y,w,h=map(float,m.groups());xs+=[x-w/2,x+w/2];ys+=[y-h/2,y+h/2]
        if not xs: return None
        b=(min(xs),min(ys),max(xs),max(ys));src='pads+0'
    return b,src
root=ET.parse(R+'ai-files/cad/work/net.xml').getroot()
rows=[];missing=[]
for c in root.find('components'):
    ref=c.get('ref');fp=(c.findtext('footprint') or '')
    if ref.startswith('#') or ref.startswith('PWR'): continue
    if not fp:
        missing.append(ref);continue
    r=bbox(fp.split(':')[-1])
    if r is None:
        missing.append(ref+'('+fp+')');continue
    (x0,y0,x1,y1),src=r
    w,h=x1-x0,y1-y0
    if src=='pads+0': w+=0.5;h+=0.5
    rows.append(dict(ref=ref,fp=fp,w=round(w,2),h=round(h,2),a=round(w*h,2),src=src))
tot=sum(r['a'] for r in rows)
json.dump(dict(rows=rows,missing=missing,total=tot),open(R+'ai-files/cad/work/pcb_estimate.json','w'),indent=1)
print(len(rows),'parts, sum area mm2',round(tot),'missing',missing)
cnt=collections.Counter(r['src'] for r in rows);print(cnt)
for r in sorted(rows,key=lambda r:-r['a'])[:15]:print(r)
