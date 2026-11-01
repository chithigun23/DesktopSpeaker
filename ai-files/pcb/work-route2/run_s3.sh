#!/bin/sh
# run_s3.sh BASE RUN [router args] : re-run stage S3 only on BASE-2 (S0-S2 locked through BASE-manifest.json), output RUN-3.
set -e
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route2; cd $W
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
B=$1; R=$2; shift 2
python3 -c "import json;M=json.load(open('$B-manifest.json'));M['stages'].pop('S3',None);M['base_run']='$B';json.dump(M,open('$R-manifest.json','w'),indent=1)"
export ROUTE_OCT_MANIFEST=$R-manifest.json
date +"%T start S3 on $B-2"
sh $H/route_oct_stage.sh $W $B-2 S3 $R-3 hard-nets.txt --via-cost 1.5 --pair-avoid 1 --hweight 1 --max-exp 3e7 "$@"
date +"%T DONE $R"
