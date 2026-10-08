#!/bin/sh
# Placement v10: generate ai-files/pcb/work-v10/DesktopSpeaker-v10.kicad_pcb (placement only). Never touches the project board/project file.
# The work copy gets the project rules (.kicad_pro netclasses, .kicad_dru, stackup) copied in for DRC; setup_pcb_rules.py is NOT run.
set -e
ROOT=/home/chithi/Desktop/DesktopSpeaker
W=$ROOT/ai-files/pcb/work-v10
P=$ROOT/DesktopSpeaker-kicad
export PATH=$ROOT/ai-files/helpers/bin:$PATH
mkdir -p $W
kicad-cli sch export netlist --format kicadxml -o $W/ds_net.xml $P/DesktopSpeaker.kicad_sch
cp $P/DesktopSpeaker.kicad_pro $W/DesktopSpeaker-v10.kicad_pro
cp $P/DesktopSpeaker.kicad_dru $W/DesktopSpeaker-v10.kicad_dru
sed "s#\${KIPRJMOD}/kicad-library#$P/kicad-library#g" $P/fp-lib-table > $W/fp-lib-table
flatpak run --env=PYTHONHASHSEED=0 --env=FLOOR=${FLOOR:-$ROOT/ai-files/pcb/floorplan-v10.json} --filesystem=$ROOT --filesystem=/tmp --command=python3 org.kicad.KiCad $ROOT/ai-files/helpers/build_pcb_v10.py
sed -i 's/"min_text_height": 0.8/"min_text_height": 0.6/' $W/DesktopSpeaker-v10.kicad_pro   # pcbnew SaveBoard resets it
python3 $ROOT/ai-files/helpers/v10_stackup.py $P/DesktopSpeaker.kicad_pcb $W/DesktopSpeaker-v10.kicad_pcb
