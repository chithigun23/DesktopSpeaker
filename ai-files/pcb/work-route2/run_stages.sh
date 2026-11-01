#!/bin/sh
# run_stages.sh RUN [router args] : S1, S2, S3 in sequence on H0 (S0 = locked RT-1 template copper), final route_oct parameters (+ extra args).
# Each stage (helpers/route_oct_stage.sh): export -> route -> refill -> DRC -> pour check -> manifest; the router refuses a stage if earlier copper changed.
set -e
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route2; cd $W
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
V=/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/V/bin/python
R=$1; shift 1
export ROUTE_OCT_MANIFEST=$R-manifest.json; rm -f $ROUTE_OCT_MANIFEST
$V mk_s0.py $ROUTE_OCT_MANIFEST H0.kicad_pcb
IN=H0
for S in 1 2 3; do
  date +"%T start S$S"
  sh $H/route_oct_stage.sh $W $IN S$S $R-$S hard-nets.txt --via-cost 1.5 --pair-avoid 1 --hweight 1 --max-exp 3e7 "$@"
  IN=$R-$S
done
date +"%T DONE $R"
