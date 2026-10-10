#!/bin/sh
# route_r6c_eval.sh STEM : in work-r6; uses R6c.kicad_pro/.kicad_dru; DRC counts + fragment-aware open edges (all nets) by class
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6; H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers; export PATH=$H/bin:$PATH
FP="flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --command=python3 org.kicad.KiCad"
cd $W; cp R6c.kicad_pro $1.kicad_pro; cp R6c.kicad_dru $1.kicad_dru
$FP $H/route_p2_open2.py $1.kicad_pcb $1.open2.json all >/dev/null 2>&1
kicad-cli pcb drc --format json --severity-all --units mm -o $1.drc.json $1.kicad_pcb >/dev/null 2>&1
python3 - $1 <<'P'
import json,collections,sys,fnmatch
f=sys.argv[1];pro=json.load(open(f+'.kicad_pro'));pats=pro['net_settings']['netclass_patterns']
def cl(n):
    for p in pats:
        if fnmatch.fnmatchcase(n,p['pattern']): return p['netclass']
    return 'Default'
o=json.load(open(f+'.open2.json'));c=collections.Counter()
for k,v in o.items(): c[cl(k)]+=v
d=json.load(open(f+'.drc.json'));t=collections.Counter(x['type'] for x in d['violations'])
print(f,'OPEN',sum(o.values()),dict(c));print(' DRC',dict(t),'unconn',len(d.get('unconnected_items',[])))
P
