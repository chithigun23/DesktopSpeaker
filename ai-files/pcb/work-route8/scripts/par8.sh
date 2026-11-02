#!/bin/sh
# par8.sh JOBS.json TAG : run every job of JOBS.json as its own hr8 process (same geo + base_plan), in parallel.
# Outputs t/TAG_k.json (job), t/TAG_k_plan.json (+ .hrlog.json), t/TAG_k.log
cd /home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route8
V=/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/V/bin/python
N=$(python3 -c "import json,sys;print(len(json.load(open('$1'))['jobs']))")
k=0
while [ $k -lt $N ]; do
  python3 -c "
import json; d=json.load(open('$1')); j=d['jobs'][$k]; d['jobs']=[j]; d['out_plan']='t/$2_$k''_plan.json'; json.dump(d,open('t/$2_$k.json','w'))"
  ( timeout 2400 $V scripts/hr8.py t/$2_$k.json > t/$2_$k.log 2>&1 ) &
  k=$((k+1))
done
wait
grep -h "^OK\|^FAIL" t/$2_*.log
