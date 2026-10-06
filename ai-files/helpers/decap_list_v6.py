import json,re,sys
t=open('/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb').read()
fpn={}
for m in re.finditer(r'\(footprint "([^"]+)"(.*?)\(property "Reference" "([^"]+)"',t,re.S):
    fpn[m.group(3)]=m.group(1)
d=json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/dist-v6.json'))['ic']
th=float(sys.argv[1]) if len(sys.argv)>1 else 2.5
bad=[(ic,r,dist,net) for ic,v in d.items() for r,dist,pin,net in v['items'] if r[0]=='C' and '0402' in fpn.get(r,'') and dist>th]
print(len(bad)); 
for b in sorted(bad,key=lambda x:(x[0],-x[2])): print(b)
