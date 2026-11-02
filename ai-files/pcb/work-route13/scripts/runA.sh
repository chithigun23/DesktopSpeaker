#!/bin/sh
# runA.sh : task A chain RT-4 -> A0 (fpfix) -> A1 (copper plan t/planA.json, refill, DRC) -> A2 (v13 models applied, DRC)
set -e
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route5; cd $W; K=~/Applications/kicad.AppImage; M=../../cad/models-v13
python3 scripts/fpfix.py RT-4.kicad_pcb A0.kicad_pcb t/A0.fpfix.json
cp RT-4.drc.json A0.drc.json
sh scripts/cycle.sh A0 t/planA.json A1
cp A1.kicad_pcb A2.kicad_pcb
python3 $M/apply.py --map $M/apply-map.json --board A2.kicad_pcb | head -1
cp base.kicad_pro A2.kicad_pro; cp base5.kicad_dru A2.kicad_dru
$K kicad-cli pcb drc --severity-all --format json --all-track-errors -o A2.drc.json A2.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
$K python3.11 ../../helpers/route_oct_export.py A2.kicad_pcb A2.geo.json 2>&1 | grep -v "memory leak" | tail -1
rm -f A2.kicad_prl
python3 scripts/drcsum.py A2.drc.json
