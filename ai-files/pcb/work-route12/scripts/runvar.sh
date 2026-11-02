#!/bin/sh
# runvar.sh TAG CHGPLAN : RT-10 candidate build = final10 composition with the CHG routes of CHGPLAN -> hr10 jobs -> snap10 -> cycle10 -> void
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route11; cd $W
V=/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/V/bin/python
T=$1
python3 scripts/final10.py $2 t/j$T.json > /dev/null
$V scripts/hr10.py t/j$T.json 2>&1 | grep -E "^FAIL" 
python3 scripts/snap10.py R1.kicad_pcb t/p$T.json t/p${T}s.json > t/p${T}s.snap.txt
sh scripts/cycle10.sh R1 t/p${T}s.json $T 2>&1 | grep -E "^DRC"
python3 scripts/uncnet.py R1.drc.json $T.drc.json | head -1
$V scripts/voidmap.py $T.kicad_pcb --top 300 > t/void_$T.txt; head -1 t/void_$T.txt; grep -E "CHG_(SYS_)?ENABLE +[0-9]" t/void_$T.txt
