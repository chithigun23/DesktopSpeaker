#!/bin/sh
# v6 pipeline: cells -> pack -> spec -> board (placement only). Usage: run_v6.sh [seeds...]
R=/home/chithi/Desktop/DesktopSpeaker
export PATH=$R/ai-files/helpers/bin:$PATH
KP="flatpak run --filesystem=$R --command=python3 org.kicad.KiCad"
cd $R/ai-files
rm -f pcb/floorplan-v6.json pcb/floorplan-v6-raw*.json
sh helpers/build_pcb_v6.sh | grep -E "WARN|FAIL|placed" 
for sd in ${@:-1 2 3 4}; do $KP helpers/fp_pack_v6.py ${HMIN:-100} 170 ${TRIALS:-150} ${WID:-116} $sd 2>&1 | grep -E "^(W|H .* ok)" & done; wait
$KP helpers/fp_spec_v6.py
sh helpers/build_pcb_v6.sh | grep -E "WARN|FAIL|placed"
