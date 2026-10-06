#!/bin/sh
# v7 pipeline: cells -> pack (several W x seeds in parallel) -> spec -> board. Usage: WS="129 131" SEEDS="1 2" TRIALS=300 run_v7.sh
R=/home/chithi/Desktop/DesktopSpeaker
export PATH=$R/ai-files/helpers/bin:$PATH
KP="flatpak run --filesystem=$R --command=python3 org.kicad.KiCad"
cd $R/ai-files
if [ -z "$SKIPCELLS" ]; then rm -f pcb/floorplan-v7.json pcb/floorplan-v7-raw*.json; sh helpers/build_pcb_v7.sh | grep -E "WARN|FAIL|placed"; fi
for w in ${WS:-129 131 133}; do for sd in ${SEEDS:-1 2 3}; do $KP helpers/fp_pack_v7.py ${HMIN:-95} 150 ${TRIALS:-200} $w $sd 2>&1 | grep -E "^(W|H .* ok|fails)" & done; done; wait
$KP helpers/fp_spec_v7.py
sh helpers/build_pcb_v7.sh | grep -E "WARN|FAIL|placed"
