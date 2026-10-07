#!/bin/sh
# route_p1_cycle.sh IN_STEM OUT_STEM : fix (from IN_STEM.drc.json) -> refill -> DRC -> OUT_STEM.drc.json ; removed nets in OUT_STEM-removed.json
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-p1; H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers; export PATH=$H/bin:$PATH
FP="flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp --command=python3 org.kicad.KiCad"
$FP $H/route_p1_fix.py $W/$1.kicad_pcb $W/$1.drc.json $W/$2-nr.kicad_pcb $W/$2-removed.json >/dev/null 2>&1
cp $W/DesktopSpeaker.kicad_pro $W/$2-nr.kicad_pro
$FP $H/route_p1_post.py refill $W/$2-nr.kicad_pcb $W/$2.kicad_pcb >/dev/null 2>&1
cp $W/DesktopSpeaker.kicad_pro $W/$2.kicad_pro; cp $W/DesktopSpeaker.kicad_dru $W/$2.kicad_dru
kicad-cli pcb drc --format json --severity-all --units mm -o $W/$2.drc.json $W/$2.kicad_pcb >/dev/null
python3 - $W/$2 <<'P'
import json,collections,sys
f=sys.argv[1];d=json.load(open(f+'.drc.json'));c=collections.Counter(x['type'] for x in d['violations'])
print(f.split('/')[-1],{k:c[k] for k in('clearance','shorting_items','track_dangling','via_dangling','track_width','hole_to_hole','holes_co_located')},'removed nets',len(json.load(open(f+'-removed.json'))))
P
