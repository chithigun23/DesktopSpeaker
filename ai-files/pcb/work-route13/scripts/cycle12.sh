#!/bin/sh
# cycle11.sh IN_STEM PLAN OUT_STEM : text edit (edit.py) -> refill (separate pcbnew process, pristine base.kicad_pro + RT-12.kicad_dru beside)
#   -> kicad-cli DRC -> geo export. RT-12 copy of work-route11 cycle11.sh.
set -e
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route12; cd $W
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
K=~/Applications/kicad.AppImage
IN=$1; PLAN=$2; OUT=$3
python3 scripts/edit.py $IN.kicad_pcb $PLAN $OUT-raw.kicad_pcb t/$OUT.edit.json
cp -f base.kicad_pro $OUT-raw.kicad_pro; cp -f RT-12.kicad_dru $OUT-raw.kicad_dru
$K python3.11 $H/route_oct_refill.py $OUT-raw.kicad_pcb $OUT.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
cp -f base.kicad_pro $OUT.kicad_pro; cp -f RT-12.kicad_dru $OUT.kicad_dru
rm -f $OUT-raw.kicad_pro $OUT-raw.kicad_dru $OUT-raw.kicad_prl $OUT.kicad_prl $OUT-raw.kicad_pcb
( $K kicad-cli pcb drc --severity-all --format json --all-track-errors -o $OUT.drc.json $OUT.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1 ) &
( $K python3.11 $H/route_oct_export.py $OUT.kicad_pcb $OUT.geo.json 2>&1 | grep -v "memory leak" | tail -1 ) &
wait
rm -f $OUT.kicad_prl
python3 scripts/drcsum.py $OUT.drc.json
python3 scripts/uncdiff.py $IN.drc.json $OUT.drc.json | head -3
