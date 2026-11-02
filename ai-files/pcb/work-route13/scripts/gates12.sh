#!/bin/sh
# gates11.sh STEM EDITS [ALLOWMOVE] : independent gates of STEM.kicad_pcb (refilled; base.kicad_pro + RT-11.kicad_dru beside) against RT-11.
# EDITS = comma list of the edit reports of the build chain RT-10 -> STEM. RT-11 copy of work-route10/scripts/gates10.sh.
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route12; cd $W
R=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route9
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
X=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r8/scripts
V=/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/V/bin/python
K=~/Applications/kicad.AppImage
S=$1; EDJ=$2; AM=${3:-none}
[ -f $S.drc.json ] || $K kicad-cli pcb drc --severity-all --format json --all-track-errors -o $S.drc.json $S.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
[ -f $S.geo.json ] || $K python3.11 $H/route_oct_export.py $S.kicad_pcb $S.geo.json 2>&1 | grep -v "memory leak" | tail -1
rm -f $S.kicad_prl
echo "== DRC (kicad-cli, project footprint library, RT-12 rules)"; python3 scripts/drcsum.py $S.drc.json | head -3
echo "== unconnected per net (RT-11 -> $S)"; python3 scripts/uncnet.py RT-11.drc.json $S.drc.json
echo "== unconnected pairs (RT-11 -> $S)"; python3 scripts/uncdiff.py RT-11.drc.json $S.drc.json
echo "== gates4 RT-11 -> $S"; python3 scripts/gates4.py RT-11.kicad_pcb $S.kicad_pcb t/$S.gates.json --edits $EDJ --allow-move $AM
echo "== route_oct_check"; $V $H/route_oct_check.py $S.kicad_pcb $S.geo.json $R/cont-nets.txt --drc $S.drc.json --rules $S.kicad_dru $S.kicad_pro --json t/$S.check.json > t/$S.check.txt 2>&1; tail -3 t/$S.check.txt
echo "== r7"; $V $H/r7_metrics.py $S.kicad_pcb --json t/$S.r7.json > t/$S.r7.txt 2>&1; python3 -c "import json;d=json.load(open('t/$S.r7.json'));print('Bcu_total',d['ref']['Bcu_total'],'Fcu',d['ref']['Fcu_over_In1']);print('sens void',{k:v.get('void',0) for k,v in d['ref']['Bcu_sensitive'].items()});print('bm83',d['bm83'])"
echo "== parcheck"; $V $H/route_oct_parcheck.py $S.kicad_pcb $S.geo.json $R/cont-nets.txt --json t/$S.par.json > t/$S.par.txt 2>&1; tail -4 t/$S.par.txt
echo "== pour check"; $V $H/route_oct_pourcheck.py RT-11.drc.json $S.drc.json $R/cont-nets.txt 2>&1 | tail -2
echo "== islands"; $V scripts/islands10.py RT-11.kicad_pcb $S.kicad_pcb | tail -25
echo "== sentinel"; sh $H/route_oct_sentinel.sh $W $S 2>&1 | tail -2
echo "== rule hashes"; sha256sum $S.kicad_dru $S.kicad_pro RT-11.kicad_dru RT-11.kicad_pro | tee t/$S.rulehash.txt
echo "== rule diff RT-11 -> $S"; diff RT-11.kicad_dru $S.kicad_dru | grep -c '^>'; diff RT-11.kicad_dru $S.kicad_dru | grep '^<' | wc -l
echo "== HA8"; $K python3.11 $X/dump.py $S.kicad_pcb t/$S.dump.json 2>&1 | grep -v "memory leak" | tail -1
$V $X/r8b_ha8.py t/$S.dump.json t/$S.ha8.json | head -1; python3 scripts/ha8diff.py t/RT-11.ha8.json t/$S.ha8.json
echo "== BAT_INT"; $K python3.11 $H/copper_path_export.py $S.kicad_pcb t/$S.cp.json "/Battery_Charger/BAT_INT" 2>&1 | grep -v "memory leak" | tail -1
(cd t && $V $H/copper_path_solve.py $S.cp.json /Battery_Charger/BAT_INT "U4:22,U4:23" "Q103:1,Q103:2,Q103:3" 148,104,178,128 0.05 6.0 20 $S 2>&1 | sed -n 3,4p)
