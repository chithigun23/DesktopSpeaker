#!/bin/sh
# final13.sh PRE EDITS MOVES : silk tiling of PRE -> RT-13, DRC + geo, silk gate, independent gates vs RT-12, rule-21 sentinel.
set -e
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route15; cd $W
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
K=~/Applications/kicad.AppImage
P=$1; EDJ=$2; AM=$3
python3 scripts/silk_tile13.py $P.kicad_pcb RT-15.kicad_pcb --report t/RT-15.silk.json | tail -1
cp -f base.kicad_pro RT-15.kicad_pro
rm -f RT-15.drc.json RT-15.geo.json
$K kicad-cli pcb drc --severity-all --format json --all-track-errors -o RT-15.drc.json RT-15.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
$K python3.11 $H/route_oct_export.py RT-15.kicad_pcb RT-15.geo.json 2>&1 | grep -v "memory leak" | tail -1
rm -f RT-15.kicad_prl
$K python3.11 $H/silk_tile_gate.py $P.kicad_pcb RT-15.kicad_pcb --drc-base $P.drc.json --drc-new RT-15.drc.json --json t/RT-15.silkgate.json 2>&1 | grep -v "memory leak" | tail -8
sh scripts/gates15.sh RT-15 $EDJ $AM > t/RT-15.gates.txt 2>&1 || true
sh scripts/sentinel21_15.sh RT-15 2>&1 | tail -4 >> t/RT-15.gates.txt
tail -5 t/RT-15.gates.txt
