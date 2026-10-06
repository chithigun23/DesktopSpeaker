#!/bin/sh
R=/home/chithi/Desktop/DesktopSpeaker
flatpak run --filesystem=$R --command=python3 org.kicad.KiCad $R/ai-files/helpers/pcb_dist_check.py $R/DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb $R/ai-files/pcb/dist-v5.json
