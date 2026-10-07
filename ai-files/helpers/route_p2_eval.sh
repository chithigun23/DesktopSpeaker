#!/bin/sh
# route_p2_eval.sh STEM [norefill] : refill zones -> STEM-f.kicad_pcb, open edges by class (union-find), DRC counts
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-p2; H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers; export PATH=$H/bin:$PATH
FP="flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp --command=python3 org.kicad.KiCad"
cp $W/S0.kicad_pro $W/$1.kicad_pro 2>/dev/null; cp $W/S0.kicad_dru $W/$1.kicad_dru 2>/dev/null
if [ "$2" != "norefill" ]; then $FP $H/route_p1_post.py refill $W/$1.kicad_pcb $W/$1-f.kicad_pcb >/dev/null 2>&1; cp $W/S0.kicad_pro $W/$1-f.kicad_pro; cp $W/S0.kicad_dru $W/$1-f.kicad_dru; F=$1-f; else F=$1; fi
$FP $H/route_p1_open.py $W/$F.kicad_pcb $W/$F.open.json >/dev/null 2>&1
$FP $H/route_p2_open2.py $W/$F.kicad_pcb $W/$F.open2.json >/dev/null 2>&1
kicad-cli pcb drc --format json --severity-all --units mm -o $W/$F.drc.json $W/$F.kicad_pcb >/dev/null 2>&1
python3 - $W/$F <<'P'
import json,collections,sys,fnmatch
f=sys.argv[1];pro=json.load(open(f+'.kicad_pro'));pats=pro['net_settings']['netclass_patterns']
def cl(n):
    for p in pats:
        if fnmatch.fnmatchcase(n,p['pattern']): return p['netclass']
    return 'SIGNAL'
o=json.load(open(f+'.open.json'));c=collections.Counter();bn={}
for k,v in o.items():
    if k.startswith('unconnected-'): continue
    c[cl(k)]+=v
    if cl(k) in('SWITCH','POWER_HI','PVDD','SPK_OUT','BOOT'): bn[k]=v
d=json.load(open(f+'.drc.json'));t=collections.Counter(x['type'] for x in d['violations'])
print(f.split('/')[-1]);print(' open',dict(c));print(' target open nets',bn)
o2=json.load(open(f+'.open2.json'));print(' OPEN2 (fragment-aware) target',sum(o2.values()),o2);print(' drc',dict(t))
P
