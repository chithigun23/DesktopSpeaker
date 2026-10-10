#!/bin/sh
# route_r6l_widen2.sh IN_STEM OUT_STEM [N] : R6l overspec track pass with the strict oracle. init (env R6L_SPLIT, R6L_STEAL, R6L_STEAL0,
# R6L_ONLY), then per round: apply N items, DRC on a copy split into 1 mm pieces (route_r6l_splitall.py), judgepos; then merge the
# collinear pieces back and re-check strictly (route_r6l_verify2.sh) until clean.
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers; W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6; export PATH=$H/bin:$PATH
FP="flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp/claude-1000 --command=python3 org.kicad.KiCad"
cd $W; T=$2w; P=$2p; N=${3:-60}; for s in $2 $T $P; do cp R6l.kicad_pro $s.kicad_pro; cp R6l.kicad_dru $s.kicad_dru; done
flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp/claude-1000 --env=R6L_ONLY="$R6L_ONLY" --env=R6L_STEAL="${R6L_STEAL:-0.4}" --env=R6L_STEAL0="$R6L_STEAL0" --env=R6L_SPLIT="${R6L_SPLIT:-0}" --command=python3 org.kicad.KiCad $H/route_r6l_widen.py init $1.kicad_pcb $T.kicad_pcb r6l/$2.widen.json 2>&1 | grep init
i=0; while [ $i -lt 300 ]; do i=$((i+1))
 $FP $H/route_r6l_widen.py apply $T.kicad_pcb $T.kicad_pcb r6l/$2.widen.json $N >/dev/null 2>&1
 $FP $H/route_r6l_splitall.py $T.kicad_pcb $P.kicad_pcb 1.0 >/dev/null 2>&1
 kicad-cli pcb drc --all-track-errors --format json --severity-all --units mm -o $P.drc.json $P.kicad_pcb >/dev/null 2>&1
 r=$($FP $H/route_r6l_widen.py judgepos $T.kicad_pcb $T.kicad_pcb r6l/$2.widen.json $P.drc.json 2>&1 | grep judge); echo "round $i $r"
 case "$r" in *"pending 0"*) break;; esac
done
$FP $H/route_r6l_widen.py merge $T.kicad_pcb $T.kicad_pcb r6l/$2.widen.json 2>&1 | grep merged
cp $T.kicad_pcb $2.kicad_pcb; rm -f $T.kicad_pcb $T.kicad_pro $T.kicad_dru $T.kicad_prl $P.kicad_pcb $P.kicad_pro $P.kicad_dru $P.drc.json $P.kicad_prl
sh $H/route_r6l_verify2.sh $2 r6l/$2.widen.json
