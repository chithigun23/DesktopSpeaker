#!/bin/sh
# run11.sh BASE TAG : RT-11 block routing pipeline. Stage A (fans + COM jumpers) on the router-only grown-neck model, stage B on the real geometry.
set -e
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route11; cd $W
V=/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/V/bin/python
B=$1; T=$2
$V scripts/neckgeo.py $B.geo.json ${B}r.geo.json NECK_U8=1.0,NECK_U9=1.0,NECK_U10=0.6
python3 scripts/mkblock.py ${B}r.geo.json t/empty.json t/jA$T.json fan
$V scripts/hr11.py t/jA$T.json > t/jA$T.log 2>&1
sh scripts/cycle11.sh $B t/pA$T.json A$T > t/cA$T.log 2>&1
python3 scripts/mkblock.py A$T.geo.json t/empty.json t/jB$T.json aud,pwr,ctl
$V scripts/hr11.py t/jB$T.json > t/jB$T.log 2>&1
sh scripts/cycle11.sh A$T t/pB$T.json B$T > t/cB$T.log 2>&1
grep -hE "^(OK|FAIL)" t/jA$T.log t/jB$T.log | cut -c1-110
grep "DRC viol" t/cA$T.log t/cB$T.log
