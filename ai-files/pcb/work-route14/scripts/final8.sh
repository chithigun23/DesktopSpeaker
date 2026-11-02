#!/bin/sh
# final8.sh PLAN : K0 + PLAN -> KF ; prune dangling copper (KP1, KP2, ...) until DRC reports none -> G1 (pre-silk)
set -e
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route9; cd $W
sh scripts/cycle.sh K0 $1 KF > t/KF.cycle.txt 2>&1
python3 scripts/drcsum.py KF.drc.json | head -1
prev=KF; k=1
while true; do
  n=$(python3 -c "import json;d=json.load(open('$prev.drc.json'));print(sum(1 for v in d['violations'] if v['type'] in ('track_dangling','via_dangling')))")
  [ "$n" = "0" ] && break
  python3 scripts/prune.py $prev.kicad_pcb $prev.drc.json t/prune$k.json
  sh scripts/cycle.sh $prev t/prune$k.json KP$k > t/KP$k.cycle.txt 2>&1
  python3 scripts/drcsum.py KP$k.drc.json | head -1
  prev=KP$k; k=$((k+1)); [ $k -gt 8 ] && break
done
echo FINAL $prev
