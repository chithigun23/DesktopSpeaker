#!/bin/sh
# route_r6j_clean.sh IN_STEM OUT_STEM : (R6j) remove DRC-reported dangling tracks/vias round by round (route_r6j_dangle.py);
# stops when nothing is dangling, and undoes the last round if the fragment-aware open-edge count grew.
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6; H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
FP="flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp/claude-1000 --command=python3 org.kicad.KiCad"
export PATH=$H/bin:$PATH
T=$(mktemp -d)
cd $W; cp $1.kicad_pcb $2.kicad_pcb; cp R6j.kicad_pro $2.kicad_pro; cp R6j.kicad_dru $2.kicad_dru
op() { $FP $H/route_p2_open2.py $1.kicad_pcb $T/op.json all >/dev/null 2>&1; python3 -c "import json;print(sum(json.load(open('$T/op.json')).values()))"; }
o0=$(op $2)
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
 kicad-cli pcb drc --format json --severity-all --units mm -o $2.drc.json $2.kicad_pcb >/dev/null 2>&1
 cp $2.kicad_pcb $T/prev.kicad_pcb
 r=$($FP $H/route_r6j_dangle.py $2.kicad_pcb $2.drc.json $2.kicad_pcb 2>/dev/null | grep removed | tail -1)
 [ "$r" = "removed 0" ] && { echo "clean after $i"; break; }
 o=$(op $2); echo "iter $i $r open $o (start $o0)"
 if [ "$o" -gt "$o0" ]; then cp $T/prev.kicad_pcb $2.kicad_pcb; echo "undo iter $i"; break; fi
done
rm -rf $T
