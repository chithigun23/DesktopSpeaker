#!/bin/sh
# ha8.sh STEM : HA8 failing pairs of STEM.kicad_pcb (work-r8 dump.py + r8b_ha8.py), diff against RT-5 (t/RT-5.ha8.json)
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route6; cd $W
S=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r8/scripts
V=/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/V/bin/python
~/Applications/kicad.AppImage python3.11 $S/dump.py $1.kicad_pcb t/$1.dump.json 2>&1 | grep -v "memory leak" | tail -1
$V $S/r8b_ha8.py t/$1.dump.json t/$1.ha8.json | head -1
[ -f t/RT-5.ha8.json ] && python3 scripts/ha8diff.py t/RT-5.ha8.json t/$1.ha8.json
