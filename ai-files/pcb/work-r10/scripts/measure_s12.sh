#!/bin/sh
# measure_s12.sh SRC_STEM TAG : strip all signal nets of SRC_STEM.kicad_pcb (H0 procedure), refill, export, order,
# then route stage S1 and S2 once with the final route_oct parameters. Work dir: ai-files/pcb/work-r10. Nothing else added.
set -e
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r10; cd $W
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
V=/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/V/bin/python
K=~/Applications/kicad.AppImage
SRC=$1; T=$2
python3 $H/route_oct_strip.py $SRC.kicad_pcb $T-H0-raw.kicad_pcb --all-signals base.kicad_pro --list $T-H0.nets.txt
cp -f base.kicad_pro $T-H0-raw.kicad_pro; cp -f base.kicad_dru $T-H0-raw.kicad_dru
$K python3.11 $H/route_oct_refill.py $T-H0-raw.kicad_pcb $T-H0.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
cp -f base.kicad_pro $T-H0.kicad_pro; cp -f base.kicad_dru $T-H0.kicad_dru
$K python3.11 $H/route_oct_export.py $T-H0.kicad_pcb $T-H0.geo.json 2>&1 | grep -v "memory leak" | tail -1
$V $H/route_oct_order.py $T-H0.geo.json $T-H0.nets.txt $T-hard-nets.txt
export ROUTE_OCT_MANIFEST=$T-manifest.json; rm -f $ROUTE_OCT_MANIFEST
sh $H/route_oct_stage.sh $W $T-H0 S1 $T-1 $T-hard-nets.txt --via-cost 1.5 --pair-avoid 1 --hweight 1 --max-exp 3e7
sh $H/route_oct_stage.sh $W $T-1 S2 $T-2 $T-hard-nets.txt --via-cost 1.5 --pair-avoid 1 --hweight 1 --max-exp 3e7
echo DONE $T
