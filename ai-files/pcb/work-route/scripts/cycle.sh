#!/bin/sh
# cycle.sh IN_STEM PLAN OUT_STEM : text edit -> refill (separate pcbnew process, pristine pro/dru) -> DRC -> export -> dump -> probe
set -e
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route; cd $W
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
V=/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/V/bin/python
K=~/Applications/kicad.AppImage
IN=$1; PLAN=$2; OUT=$3
python3 scripts/edit.py $IN.kicad_pcb $PLAN $OUT-raw.kicad_pcb $OUT.edit.json
cp -f base.kicad_pro $OUT-raw.kicad_pro; cp -f base.kicad_dru $OUT-raw.kicad_dru
$K python3.11 $H/route_oct_refill.py $OUT-raw.kicad_pcb $OUT.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
cp -f base.kicad_pro $OUT.kicad_pro; cp -f base.kicad_dru $OUT.kicad_dru
rm -f $OUT-raw.kicad_pro $OUT-raw.kicad_dru $OUT-raw.kicad_prl $OUT.kicad_prl
( $K kicad-cli pcb drc --severity-all --format json --all-track-errors -o $OUT.drc.json $OUT.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1 ) &
( $K python3.11 $H/route_oct_export.py $OUT.kicad_pcb $OUT.geo.json 2>&1 | grep -v "memory leak" | tail -1 ) &
( $K python3.11 ../work-r8/scripts/dump.py $OUT.kicad_pcb $OUT.dump.json 2>&1 | grep -v "memory leak" | tail -1 ) &
wait
rm -f $OUT.kicad_prl
$V scripts/probe.py $OUT > $OUT.allexits.txt; echo "probe failing: $(head -1 $OUT.allexits.txt)"
python3 scripts/drcsum.py $OUT.drc.json
