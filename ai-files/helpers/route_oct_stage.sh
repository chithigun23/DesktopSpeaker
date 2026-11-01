#!/bin/sh
# route_oct_stage.sh WORKDIR IN_STEM STAGE OUT_STEM NETFILE [router args...]
# One locked stage: export geometry of IN (already refilled) -> route -> refill -> DRC. Files live in WORKDIR.
# IN_STEM.kicad_pcb must have IN_STEM.kicad_pro / .kicad_dru beside it (copies of the frozen project files).
set -e
W=$1; IN=$2; ST=$3; OUT=$4; NETS=$5; shift 5
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
PY=${ROUTE_OCT_PY:-/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/V/bin/python}
K=~/Applications/kicad.AppImage
cd $W
$K python3.11 $H/route_oct_export.py $IN.kicad_pcb $IN.geo.json 2>&1 | grep -v "memory leak" | tail -1
$PY $H/route_oct.py --board $IN.kicad_pcb --geo $IN.geo.json --nets $NETS --stage $ST --out $OUT-raw.kicad_pcb \
   --dru $IN.kicad_dru --pro $IN.kicad_pro --manifest ${ROUTE_OCT_MANIFEST:-manifest.json} --log $OUT.route.json --workdir $W "$@"
cp -f $W/base.kicad_pro $OUT-raw.kicad_pro; cp -f $W/base.kicad_dru $OUT-raw.kicad_dru
$K python3.11 $H/route_oct_refill.py $OUT-raw.kicad_pcb $OUT.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
cp -f $W/base.kicad_pro $OUT.kicad_pro; cp -f $W/base.kicad_dru $OUT.kicad_dru   # pristine project copies (pcbnew SaveBoard rewrites the .kicad_pro)
$K kicad-cli pcb drc --severity-all --format json --all-track-errors -o $OUT.drc.json $OUT.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
