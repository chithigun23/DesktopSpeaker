#!/bin/sh
# Regenerate DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb (placement only). Run from anywhere.
set -e
ROOT=/home/chithi/Desktop/DesktopSpeaker
export PATH=$ROOT/ai-files/helpers/bin:$PATH
kicad-cli sch export netlist --format kicadxml -o /tmp/ds_net.xml $ROOT/DesktopSpeaker-kicad/DesktopSpeaker.kicad_sch
flatpak run --env=PYTHONHASHSEED=0 --filesystem=$ROOT --filesystem=/tmp --command=python3 org.kicad.KiCad $ROOT/ai-files/helpers/build_pcb_v8.py
sed -i 's/"min_text_height": 0.8/"min_text_height": 0.6/' $ROOT/DesktopSpeaker-kicad/DesktopSpeaker.kicad_pro   # pcbnew SaveBoard resets it
