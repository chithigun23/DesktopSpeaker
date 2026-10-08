#!/bin/sh
# Placement v10b: v10 generator (same floorplan, unchanged tables) -> work-v10b/DesktopSpeaker-v10b-base.kicad_pcb, then the local review fixes
# (v10_fix_v10b.py: B1-B3, M1-M8, minors) -> work-v10b/DesktopSpeaker-v10b.kicad_pcb. Never touches the project board/project file.
set -e
ROOT=/home/chithi/Desktop/DesktopSpeaker
W=$ROOT/ai-files/pcb/work-v10b
P=$ROOT/DesktopSpeaker-kicad
export PATH=$ROOT/ai-files/helpers/bin:$PATH
mkdir -p $W
kicad-cli sch export netlist --format kicadxml -o $W/ds_net.xml $P/DesktopSpeaker.kicad_sch
if [ "${SKIPBASE:-0}" != 1 ]; then
  flatpak run --env=PYTHONHASHSEED=0 --env=FLOOR=${FLOOR:-$ROOT/ai-files/pcb/floorplan-v10b.json} --filesystem=$ROOT --filesystem=/tmp --command=python3 org.kicad.KiCad $ROOT/ai-files/helpers/build_pcb_v10b.py
fi
flatpak run --env=PYTHONHASHSEED=0 --filesystem=$ROOT --command=python3 org.kicad.KiCad $ROOT/ai-files/helpers/fix_v10b.py $W/DesktopSpeaker-v10b-base.kicad_pcb $W/DesktopSpeaker-v10b.kicad_pcb
for e in kicad_pro kicad_dru; do cp $P/DesktopSpeaker.$e $W/DesktopSpeaker-v10b.$e; done
sed -i 's/"min_text_height": 0.8/"min_text_height": 0.6/' $W/DesktopSpeaker-v10b.kicad_pro
sed "s#\${KIPRJMOD}/kicad-library#$P/kicad-library#g" $P/fp-lib-table > $W/fp-lib-table
python3 $ROOT/ai-files/helpers/v10_stackup.py $P/DesktopSpeaker.kicad_pcb $W/DesktopSpeaker-v10b.kicad_pcb
