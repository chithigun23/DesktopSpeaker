#!/bin/sh
# gates9p.sh STEM : independent gates of STEM.kicad_pcb (refilled; pristine pro/dru beside) against RT-9 (work-route9).
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route9p; cd $W
R=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route9
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
X=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r8/scripts
V=/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/V/bin/python
K=~/Applications/kicad.AppImage
S=$1; EDJ=${2:-t/$1.edit.json}
[ -f $S.drc.json ] || $K kicad-cli pcb drc --severity-all --format json --all-track-errors -o $S.drc.json $S.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
[ -f $S.geo.json ] || $K python3.11 $H/route_oct_export.py $S.kicad_pcb $S.geo.json 2>&1 | grep -v "memory leak" | tail -1
rm -f $S.kicad_prl
echo "== DRC"; python3 $R/scripts/drcsum.py $S.drc.json | head -3
echo "== unconnected per net (RT-9 -> $S)"; python3 $R/scripts/uncnet.py $R/RT-9.drc.json $S.drc.json
echo "== gates4 RT-9 -> $S (pad nets; copper incl. the 5 renamed CHG_INT items)"; python3 $R/scripts/gates4.py $R/RT-9.kicad_pcb $S.kicad_pcb t/$S.gates_rt9.json | grep -v "^unexpected_removed \[\]"
echo "== gates4 S1-raw (RT-9 + net sync, no geometry change) -> $S"; python3 $R/scripts/gates4.py S1-raw.kicad_pcb $S.kicad_pcb t/$S.gates.json --edits $EDJ
echo "== text diff RT-9 -> S1-raw (net lines only)"; diff $R/RT-9.kicad_pcb S1-raw.kicad_pcb | grep -c '^>' 
echo "== route_oct_check"; $V $H/route_oct_check.py $S.kicad_pcb $S.geo.json $R/cont-nets.txt --drc $S.drc.json --rules $S.kicad_dru $S.kicad_pro --json t/$S.check.json > t/$S.check.txt 2>&1; tail -25 t/$S.check.txt
echo "== r7"; $V $H/r7_metrics.py $S.kicad_pcb --json t/$S.r7.json > t/$S.r7.txt 2>&1; tail -15 t/$S.r7.txt
echo "== parcheck"; $V $H/route_oct_parcheck.py $S.kicad_pcb $S.geo.json $R/cont-nets.txt --json t/$S.par.json > t/$S.par.txt 2>&1; tail -12 t/$S.par.txt
echo "== pour check"; $V $H/route_oct_pourcheck.py $R/RT-9.drc.json $S.drc.json $R/cont-nets.txt 2>&1 | tail -2
echo "== sentinel"; cp -f fp-lib-table sentinel/ 2>/dev/null; sh $H/route_oct_sentinel.sh $W $S 2>&1 | tail -2
echo "== rule hashes"; sha256sum $S.kicad_dru $S.kicad_pro $R/RT-9.kicad_dru $R/RT-9.kicad_pro | tee t/$S.rulehash.txt
echo "== HA8"; $K python3.11 $X/dump.py $S.kicad_pcb t/$S.dump.json 2>&1 | grep -v "memory leak" | tail -1
$V $X/r8b_ha8.py t/$S.dump.json t/$S.ha8.json | head -1; python3 $R/scripts/ha8diff.py $R/t/RT-9.ha8.json t/$S.ha8.json
echo "== BAT_INT"; $K python3.11 $H/copper_path_export.py $S.kicad_pcb t/$S.cp.json "/Battery_Charger/BAT_INT" 2>&1 | grep -v "memory leak" | tail -1
(cd t && $V $H/copper_path_solve.py $S.cp.json /Battery_Charger/BAT_INT "U4:22,U4:23" "Q103:1,Q103:2,Q103:3" 148,104,178,128 0.05 6.0 20 $S 2>&1 | sed -n 3,4p)
