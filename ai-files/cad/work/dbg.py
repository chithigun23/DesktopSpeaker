import json,Part
W='/home/chithi/Desktop/DesktopSpeaker/ai-files/cad/work/'
m=json.load(open(W+'meta.json'));S={o['name']:Part.read(W+'brep/'+o['file']) for o in m['objs']}
import sys
for a,b in [('Shell_Box','Driver_FrontL_ND65-4'),('Shell_Box','Lid_rear'),('PCB_U1','Screw_M3x10_PcbScrew_3')]:
    c=S[a].common(S[b]);bb=c.BoundBox;print("DBG",a,b,round(c.Volume,1),[round(x,1) for x in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
