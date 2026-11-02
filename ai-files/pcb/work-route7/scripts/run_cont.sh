#!/bin/sh
# run_cont.sh IN R [router args] : continuation S1..S3 on IN (refilled board; project .kicad_pro/.kicad_dru copied beside it,
# the router checks the project rule hash). Output R-1..R-3, manifest R-manifest.json. Work folder work-route7.
set -e
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route7; cd $W
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
K=~/Applications/kicad.AppImage
IN0=$1; R=$2; shift 2
cp -f base.kicad_pro $IN0.kicad_pro; cp -f base.kicad_dru $IN0.kicad_dru
[ -f $IN0.pdrc.json ] || $K kicad-cli pcb drc --severity-all --format json --all-track-errors -o $IN0.pdrc.json $IN0.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
cp -f $IN0.pdrc.json $IN0.drc.json
export ROUTE_OCT_MANIFEST=$R-manifest.json; rm -f $ROUTE_OCT_MANIFEST
IN=$IN0
for S in 1 2 3; do
  date +"%T start S$S"
  FR=""; [ $S = 3 ] && FR="--first-refs U1,J8"
  sh $H/route_oct_stage.sh $W $IN S$S $R-$S cont-nets.txt --cont-drc $W/$IN.drc.json --via-cost 1.5 --pair-avoid 1 --hweight 1 --max-exp 3e7 --detour 2.5 $FR "$@"
  IN=$R-$S
done
date +"%T DONE $R"
