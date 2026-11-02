#!/bin/sh
# refill_drc.sh STEM : STEM-raw.kicad_pcb -> refill in a separate pcbnew process (pristine pro/dru beside) -> STEM.kicad_pcb -> DRC json + parity DRC json
set -e
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route9p; cd $W
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
K=~/Applications/kicad.AppImage
O=$1
cp -f base.kicad_pro $O-raw.kicad_pro; cp -f base6.kicad_dru $O-raw.kicad_dru
$K python3.11 $H/route_oct_refill.py $O-raw.kicad_pcb $O.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
cp -f base.kicad_pro $O.kicad_pro; cp -f base6.kicad_dru $O.kicad_dru
rm -f $O-raw.kicad_pro $O-raw.kicad_dru $O-raw.kicad_prl $O.kicad_prl
$K kicad-cli pcb drc --severity-all --format json --all-track-errors -o $O.drc.json $O.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
rm -f $O.kicad_prl
python3 ../work-route9/scripts/drcsum.py $O.drc.json
python3 ../work-route9/scripts/uncdiff.py ../work-route9/RT-9.drc.json $O.drc.json
