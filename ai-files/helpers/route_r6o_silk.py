#!/usr/bin/env python3
"""route_r6o_silk.py IN.kicad_pcb OUT.kicad_pcb [--lib]  R6o silk cleanup + C275 6.3x7.7 outline (text edits).
--lib also applies the identical footprint edits to DesktopSpeaker-kicad/kicad-library/footprint (PJ-307, TYPE-C-31-M-12,
BM83SM1-00TA, Logo_Orwellian, CP_Elec_8x10). Pads are never touched."""
import re,sys,uuid
LIB='/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/kicad-library/footprint/'
LOGO_S=0.66; LOGO_AT=(173.2,55.15)
def match(s,st):
    d=0;j=st
    while True:
        c=s[j]
        if c=='(':d+=1
        elif c==')':
            d-=1
            if d==0:return j+1
        j+=1
def fpblk(s,ref):
    i=s.find('(property "Reference" "%s"'%ref); st=s.rfind('\n\t(footprint ',0,i)+1; return st,match(s,st)
def children(t,names):
    out=[];i=0
    while True:
        m=re.compile(r'\((%s)\b'%'|'.join(names)).search(t,i)
        if not m:break
        e=match(t,m.start()); out.append((m.start(),e)); i=e
    return out
def nums(t): return [float(x) for x in re.findall(r'\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)',re.sub(r'\s+',' ',t))[0]]
def setse(t,a,b,c,d): return re.sub(r'\(start [-\d.]+ [-\d.]+\)(\s*)\(end [-\d.]+ [-\d.]+\)',lambda m:'(start %g %g)%s(end %g %g)'%(a,b,m.group(1),c,d),t,count=1)
def edit_lines(t,rules,newuuid=True):
    """rules: list of ((x1,y1,x2,y2) on layer F.SilkS, [replacement segments] ) ; [] deletes"""
    hits=0
    for (key,reps) in rules:
        for a,b in reversed(children(t,['fp_line'])):
            seg=t[a:b]
            if 'F.SilkS' not in seg:continue
            try: v=nums(seg)
            except IndexError: continue
            if all(abs(p-q)<1e-3 for p,q in zip(v,key)):
                new=[]
                for k,r in enumerate(reps):
                    x=setse(seg,*r)
                    if k>0 or newuuid: x=re.sub(r'\(uuid "[^"]+"\)','(uuid "%s")'%uuid.uuid4(),x)
                    new.append(x)
                t=t[:a]+('\n\t\t'.join(new) if new else '')+t[b:]; hits+=1; break
    return t,hits
PJ=[((-7.33,4.5,-5.85,4.5),[(-7.33,4.5,-6.5,4.5)]),((-7.33,-4.5,-5.85,-4.5),[(-7.33,-4.5,-6.5,-4.5)]),((-5.85,-6,-5.85,6),[(-5.85,-4.2,-5.85,4.2)])]
J1=[((4.47,5.09,4.47,3.61),[]),((4.47,5.09,-4.47,5.09),[]),((-4.47,5.09,-4.47,3.61),[])]
U1=[((7.6,-21.56,7.6,-10.99),[(7.6,-21.56,7.6,-14.2),(7.6,-12.95,7.6,-10.99)]),((-7.6,-10.99,-7.6,-21.56),[(-7.6,-10.99,-7.6,-12.95),(-7.6,-14.2,-7.6,-21.56)])]
def gl(x1,y1,x2,y2,w,lay,ind):
    return ('(fp_line\n{i}\t(start {} {})\n{i}\t(end {} {})\n{i}\t(stroke\n{i}\t\t(width {})\n{i}\t\t(type solid)\n{i}\t)\n{i}\t(layer "{}")\n{i}\t(uuid "{}")\n{i})'
            .format(x1,y1,x2,y2,w,lay,uuid.uuid4(),i=ind))
def c275_items(ind):
    L=[]
    # silk (0.11 outside the 6.6 base plate), polarity + unchanged at (-5,-2.51)
    for a in [(-5.5,-2.51,-4.5,-2.51),(-5,-3.01,-5,-2.01),(-3.41,-2.345563,-3.41,-1.51),(-3.41,-2.345563,-2.345563,-3.41),(-3.41,2.345563,-3.41,1.51),
              (-3.41,2.345563,-2.345563,3.41),(-2.345563,-3.41,3.41,-3.41),(-2.345563,3.41,3.41,3.41),(3.41,-3.41,3.41,-1.51),(3.41,3.41,3.41,1.51)]:
        L.append(gl(*a,0.12,'F.SilkS',ind))
    # courtyard: base plate + 0.25, pads (+-5.0 x +-1.25) + 0.25
    P=[(-5.25,-1.5),(-5.25,1.5),(-3.55,1.5),(-3.55,2.4),(-2.4,3.55),(3.55,3.55),(3.55,1.5),(5.25,1.5),(5.25,-1.5),(3.55,-1.5),(3.55,-3.55),(-2.4,-3.55),(-3.55,-2.4),(-3.55,-1.5),(-5.25,-1.5)]
    for p,q in zip(P,P[1:]): L.append(gl(p[0],p[1],q[0],q[1],0.05,'F.CrtYd',ind))
    # fab: 6.6 base plate with 1.0 chamfers, 6.3 can circle, + mark
    for a in [(-3.3,-2.3,-3.3,2.3),(-3.3,-2.3,-2.3,-3.3),(-3.3,2.3,-2.3,3.3),(-2.3,-3.3,3.3,-3.3),(-2.3,3.3,3.3,3.3),(3.3,-3.3,3.3,3.3),(-2.9,-1.5,-2.1,-1.5),(-2.5,-1.9,-2.5,-1.1)]:
        L.append(gl(*a,0.1,'F.Fab',ind))
    L.append(('(fp_circle\n{i}\t(center 0 0)\n{i}\t(end 3.15 0)\n{i}\t(stroke\n{i}\t\t(width 0.1)\n{i}\t\t(type solid)\n{i}\t)\n{i}\t(fill no)\n{i}\t(layer "F.Fab")\n{i}\t(uuid "{}")\n{i})').format(uuid.uuid4(),i=ind))
    return L
def c275(t,ind):
    ch=[(a,b) for a,b in children(t,['fp_line','fp_circle']) if re.search(r'\(layer "F\.(SilkS|CrtYd|Fab)"\)',t[a:b])]
    first=ch[0][0]
    for a,b in reversed(ch): t=t[:a]+t[b:]
    t=re.sub(r'\n\s*\n','\n',t)
    first=t.find('(fp_text user') if '(fp_text user' in t else t.find('(pad')
    return t[:first]+('\n'+ind).join(c275_items(ind))+'\n'+ind+t[first:]
DESC=('57.4 x 63.2 mm (scale 2.95','%.1f x %.1f mm (scale %.2f'%(57.35*LOGO_S,63.18*LOGO_S,2.95*LOGO_S))
def logo(t):
    t=re.sub(r'\(xy ([-\d.]+) ([-\d.]+)\)',lambda m:'(xy %.4f %.4f)'%(float(m.group(1))*LOGO_S,float(m.group(2))*LOGO_S),t)
    return t.replace(*DESC)
def board(s):
    rep={}
    for ref in ('J2','J3'):
        a,b=fpblk(s,ref); t,h=edit_lines(s[a:b],PJ); assert h==3,(ref,h); s=s[:a]+t+s[b:]
    a,b=fpblk(s,'J1'); t,h=edit_lines(s[a:b],J1); assert h==3; s=s[:a]+t+s[b:]
    a,b=fpblk(s,'U1'); t,h=edit_lines(s[a:b],U1); assert h==2; s=s[:a]+t+s[b:]
    a,b=fpblk(s,'C275'); s=s[:a]+c275(s[a:b],'\t\t')+s[b:]
    a,b=fpblk(s,'LOGO1'); t=logo(s[a:b]); t=t.replace('(at 118.95 114 180)','(at %g %g 180)'%LOGO_AT,1); s=s[:a]+t+s[b:]
    a,b=fpblk(s,'SW101'); t=s[a:b]; t=t.replace('(property "Reference" "SW101"\n\t\t\t(at 10.565 0 0)','(property "Reference" "SW101"\n\t\t\t(at 9.505 0 0)',1); assert t!=s[a:b]; s=s[:a]+t+s[b:]
    # board-level silk
    def gr(s,u,reps):
        i=s.find('(uuid "%s'%u); st=s.rfind('\n\t(gr_',0,i)+1; e=match(s,st); seg=s[st:e]
        new=[setse(seg,*r) if k==0 else re.sub(r'\(uuid "[^"]+"\)','(uuid "%s")'%uuid.uuid4(),setse(seg,*r)) for k,r in enumerate(reps)]
        return s[:st]+'\n\t'.join(new)+s[e:]
    s=gr(s,'a61bbfd8',[(206.855,97.25,212.75,97.25)])      # SW101 frame bottom, was to 214.145 (past the edge)
    s=gr(s,'cbfae435',[(212.75,76.36,206.855,76.36)])      # SW101 frame top
    s=gr(s,'6bd7ab16',[(212.75,97.25,212.75,76.36)])       # SW101 frame right side moved onto the 1 mm border line
    s=gr(s,'7664d2ea',[])                                   # border corner arc under J10
    s=gr(s,'9aa64136',[(165.95,101.1,188.7,101.1),(195.6,101.1,196.65,101.1)])   # divider across H6
    s=gr(s,'b15105f5',[(165.95,73.5,171.4,73.5),(173.2,73.5,196.65,73.5)])        # dividers across R222
    s=gr(s,'c6b8896c',[(170.25,73.5,171.4,73.5),(173.2,73.5,204.55,73.5)])
    s=s.replace('(gr_text "J10 Front Right"\n\t\t(at 91.755 146.785 0)','(gr_text "J10 Front Right"\n\t\t(at %s 0)'%J10AT,1)
    return s
J10AT='101.6 148.75'
def lib():
    p=LIB+'PJ-307.kicad_mod'; t=open(p).read()
    for a,b in [('(start -7.33 4.50) (end -5.85 4.50)','(start -7.33 4.50) (end -6.50 4.50)'),('(start -7.33 -4.50) (end -5.85 -4.50)','(start -7.33 -4.50) (end -6.50 -4.50)'),('(start -5.85 -6.00) (end -5.85 6.00)','(start -5.85 -4.20) (end -5.85 4.20)')]:
        assert a in t; t=t.replace(a,b)
    open(p,'w').write(t)
    p=LIB+'TYPE-C-31-M-12.kicad_mod'; t=open(p).read()
    for a in ['\t(fp_line (start 4.47 5.09) (end -4.47 5.09) (layer F.SilkS) (width 0.25))\n','\t(fp_line (start -4.47 5.09) (end -4.47 3.61) (layer F.SilkS) (width 0.25))\n','\t(fp_line (start 4.47 5.09) (end 4.47 3.61) (layer F.SilkS) (width 0.25))\n']:
        assert a in t; t=t.replace(a,'')
    open(p,'w').write(t)
    p=LIB+'BM83SM1-00TA.kicad_mod'; t=open(p).read()
    for a,b in [('(start -7.60 -10.99) (end -7.60 -21.56) (layer F.SilkS) (width 0.25))','(start -7.60 -10.99) (end -7.60 -12.95) (layer F.SilkS) (width 0.25))\n\t(fp_line (start -7.60 -14.20) (end -7.60 -21.56) (layer F.SilkS) (width 0.25))'),
                ('(start 7.60 -21.56) (end 7.60 -10.99) (layer F.SilkS) (width 0.25))','(start 7.60 -21.56) (end 7.60 -14.20) (layer F.SilkS) (width 0.25))\n\t(fp_line (start 7.60 -12.95) (end 7.60 -10.99) (layer F.SilkS) (width 0.25))')]:
        assert a in t; t=t.replace(a,b)
    open(p,'w').write(t)
    p=LIB+'Logo_Orwellian.kicad_mod'; t=open(p).read(); assert DESC[0] in t; open(p,'w').write(logo(t))
    p=LIB+'CP_Elec_8x10.kicad_mod'; t=open(p).read(); open(p,'w').write(c275(t,'\t'))
if __name__=='__main__':
    if len(sys.argv)>3 and sys.argv[3].startswith('--j10='): J10AT=sys.argv[3][6:]
    s=open(sys.argv[1]).read(); s=board(s); open(sys.argv[2],'w').write(s)
    if '--lib' in sys.argv: lib(); print('library edited')
    print('board written',sys.argv[2])
