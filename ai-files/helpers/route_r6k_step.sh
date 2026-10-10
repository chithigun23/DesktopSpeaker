#!/bin/sh
# route_r6k_step.sh IN_STEM OUT_STEM SPEC.json : hand edits (route_r6k_edit.py ops) with R6k rules (byte copy of R6j), then route_r6k_eval.sh OUT IN
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers; W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6
FP="flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp/claude-1000 --command=python3 org.kicad.KiCad"
cd $W; $FP $H/route_r6k_edit.py $1.kicad_pcb $2.kicad_pcb $3 2>&1 | grep -v -e '^$' -e Gtk
sh $H/route_r6k_eval.sh $2 $1
