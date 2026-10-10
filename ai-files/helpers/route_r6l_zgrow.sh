#!/bin/sh
# route_r6l_zgrow.sh IN_STEM OUT_STEM [STEP] [ROUNDS] : R6l pour growth (route_r6l_zgrow.py), STEP mm per round (default 0.5), ROUNDS (default 4)
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers; W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6; export PATH=$H/bin:$PATH
FP="flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp/claude-1000 --command=python3 org.kicad.KiCad"
cd $W; T=$2z; D=${3:-0.5}; R=${4:-4}; for s in $2 $T; do cp R6l.kicad_pro $s.kicad_pro; cp R6l.kicad_dru $s.kicad_dru; done
cp $1.kicad_pcb $T.kicad_pcb; rm -f r6l/$2.zgrow.json; c=""
i=0; while [ $i -lt $R ]; do i=$((i+1))
 $FP $H/route_r6l_zgrow.py grow $T.kicad_pcb $T.kicad_pcb r6l/$2.zgrow.json $D $c 2>&1 | grep grow; c=cont
 kicad-cli pcb drc --all-track-errors --format json --severity-all --units mm -o $T.drc.json $T.kicad_pcb >/dev/null 2>&1
 $FP $H/route_r6l_zgrow.py judge $T.kicad_pcb $T.kicad_pcb r6l/$2.zgrow.json $T.drc.json 2>&1 | grep judge
done
cp $T.kicad_pcb $2.kicad_pcb; rm -f $T.kicad_pcb $T.kicad_pro $T.kicad_dru $T.drc.json $T.kicad_prl
