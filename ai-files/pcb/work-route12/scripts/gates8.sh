#!/bin/sh
# gates8.sh STEM NETFILE ALLOWMOVE EDITS : independent gates of STEM.kicad_pcb (refilled, STEM.kicad_pro/.kicad_dru beside)
# against RT-8: DRC (project library), unconnected diff, gates4 (poses, pad nets, locked copper, exact 0/45/90),
# route_oct_check, r7_metrics, parcheck, pour check, sentinel, rule hashes, HA8, BAT_INT resistance.
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route9; cd $W
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
V=/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/V/bin/python
K=~/Applications/kicad.AppImage
S=$1; NF=$2; AM=$3; ED=$4
[ -f $S.drc.json ] || $K kicad-cli pcb drc --severity-all --format json --all-track-errors -o $S.drc.json $S.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
[ -f $S.geo.json ] || $K python3.11 $H/route_oct_export.py $S.kicad_pcb $S.geo.json 2>&1 | grep -v "memory leak" | tail -1
echo "== DRC"; python3 scripts/drcsum.py $S.drc.json | head -3
echo "== unconnected per net (RT-8 -> $S)"; python3 scripts/uncnet.py RT-8.drc.json $S.drc.json
echo "== gates4"; python3 scripts/gates4.py RT-8.kicad_pcb $S.kicad_pcb $S.gates.json --allow-move $AM --edits $ED | grep -v "^unexpected_removed \[\]"
echo "== route_oct_check"; $V $H/route_oct_check.py $S.kicad_pcb $S.geo.json $NF --drc $S.drc.json --rules $S.kicad_dru $S.kicad_pro --json $S.check.json > $S.check.txt 2>&1; tail -25 $S.check.txt
echo "== r7"; $V $H/r7_metrics.py $S.kicad_pcb --json $S.r7.json > $S.r7.txt 2>&1; tail -15 $S.r7.txt
echo "== parcheck"; $V $H/route_oct_parcheck.py $S.kicad_pcb $S.geo.json $NF --json $S.par.json > $S.par.txt 2>&1; tail -12 $S.par.txt
echo "== pour check"; $V $H/route_oct_pourcheck.py RT-8.drc.json $S.drc.json $NF 2>&1 | tail -2
echo "== sentinel"; sh $H/route_oct_sentinel.sh $W $S 2>&1 | tail -2
echo "== rule hashes"; sha256sum $S.kicad_dru $S.kicad_pro RT-8.kicad_dru RT-8.kicad_pro | tee $S.rulehash.txt
echo "== HA8"; sh scripts/ha8.sh $S | tail -4
echo "== BAT_INT"; $K python3.11 $H/copper_path_export.py $S.kicad_pcb t/$S.cp.json "/Battery_Charger/BAT_INT" 2>&1 | grep -v "memory leak" | tail -1
(cd t && $V $H/copper_path_solve.py $S.cp.json /Battery_Charger/BAT_INT "U4:22,U4:23" "Q103:1,Q103:2,Q103:3" 148,104,178,128 0.05 6.0 20 $S 2>&1 | sed -n 3,4p)
