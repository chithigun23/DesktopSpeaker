#!/bin/sh
# verify.sh STEM [MANIFEST] : independent checks of a routed board STEM.kicad_pcb (S0..S3 net file hard-nets.txt):
# route_oct_check, route_oct_parcheck, r7_metrics, sentinel, footprint/pad-net/non-routed-copper diff vs RT-1, DRC summary.
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route2; cd $W
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
V=/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/V/bin/python
K=~/Applications/kicad.AppImage
R=$1; M=${2:-}
[ -f $R.drc.json ] || $K kicad-cli pcb drc --severity-all --format json --all-track-errors -o $R.drc.json $R.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
$K python3.11 $H/route_oct_export.py $R.kicad_pcb $R.geo.json 2>&1 | grep -v "memory leak" | tail -1
$V $H/route_oct_check.py $R.kicad_pcb $R.geo.json hard-nets.txt --drc $R.drc.json ${M:+--manifest $M} --rules $R.kicad_dru $R.kicad_pro --json $R.check.json > $R.check.txt 2>&1
sh $H/route_oct_sentinel.sh $W $R > $R.sentinel.txt 2>&1
$V $H/r7_metrics.py $R.kicad_pcb --json $R.r7.json > $R.r7.txt 2>&1
$V $H/route_oct_parcheck.py $R.kicad_pcb $R.geo.json hard-nets.txt --json $R.par.json > $R.par.txt 2>&1
python3 fpdiff.py RT-1.kicad_pcb $R.kicad_pcb hard-nets.txt --json $R.fpdiff.json > $R.fpdiff.txt
sha256sum $R.kicad_dru $R.kicad_pro base.kicad_dru base.kicad_pro > $R.rulehash.txt
echo VERIFY DONE $R
