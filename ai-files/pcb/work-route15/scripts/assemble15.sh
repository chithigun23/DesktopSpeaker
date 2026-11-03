#!/bin/sh
# assemble15.sh PLAN.json MOVES : RT-14 + merged group plan (incl. LDO stub fix ops) -> refill (separate pcbnew, pristine
#   base.kicad_pro + RT-15.kicad_dru beside) -> RT-15P (copper final) -> silk tiling -> paste_fix.py -> RT-15.kicad_pcb
#   -> DRC (project library) + DRC (paste-patched library copy) + geo; then gates15.sh on the pre-paste copper board.
set -e
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route15; cd $W
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
F=/home/chithi/Desktop/DesktopSpeaker/ai-files/fab/draft-rt14
K=~/Applications/kicad.AppImage
PLAN=$1; AM=${2:-none}
python3 scripts/edit.py RT-14.kicad_pcb $PLAN RT-15R-raw.kicad_pcb t/RT-15.edit.json
cp -f base.kicad_pro RT-15R-raw.kicad_pro; cp -f RT-15.kicad_dru RT-15R-raw.kicad_dru
$K python3.11 $H/route_oct_refill.py RT-15R-raw.kicad_pcb RT-15P.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
rm -f RT-15R-raw.*
cp -f base.kicad_pro RT-15P.kicad_pro; cp -f RT-15.kicad_dru RT-15P.kicad_dru
python3 scripts/silk_tile13.py RT-15P.kicad_pcb RT-15S.kicad_pcb --report t/RT-15.silk.json | tail -1
python3 $F/paste_fix.py RT-15S.kicad_pcb -o RT-15.kicad_pcb --report t/RT-15.pastefix.json | tail -3
python3 $F/ldo_stub_fix.py RT-15.kicad_pcb --dry-run | tail -2
cp -f base.kicad_pro RT-15.kicad_pro; cp -f base.kicad_pro RT-15S.kicad_pro; cp -f RT-15.kicad_dru RT-15S.kicad_dru
rm -f RT-15P.drc.json RT-15P.geo.json RT-15S.drc.json RT-15.drc.json RT-15.geo.json
$K kicad-cli pcb drc --severity-all --format json --all-track-errors -o RT-15P.drc.json RT-15P.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
$K kicad-cli pcb drc --severity-all --format json --all-track-errors -o RT-15S.drc.json RT-15S.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
$K kicad-cli pcb drc --severity-all --format json --all-track-errors -o RT-15.drc.json RT-15.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
# DRC against a paste-patched COPY of the project footprint library (what the library looks like after paste_fix.py --lib)
mkdir -p libpf/kicad-library; rm -rf libpf/kicad-library/footprint; mkdir -p libpf/kicad-library/footprint
cp /home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/kicad-library/footprint/*.kicad_mod libpf/kicad-library/footprint/
[ -e libpf/kicad-library/3d ] || ln -s /home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/kicad-library/3d libpf/kicad-library/3d
python3 $F/paste_fix.py RT-15S.kicad_pcb -o libpf/tmp.kicad_pcb --lib libpf/kicad-library/footprint | tail -1; rm -f libpf/tmp.kicad_pcb
cp -f RT-15.kicad_pcb libpf/RT-15.kicad_pcb; cp -f base.kicad_pro libpf/RT-15.kicad_pro; cp -f RT-15.kicad_dru libpf/RT-15.kicad_dru; cp -f fp-lib-table libpf/
$K kicad-cli pcb drc --severity-all --format json --all-track-errors -o libpf/RT-15.drc.json libpf/RT-15.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
$K python3.11 $H/route_oct_export.py RT-15.kicad_pcb RT-15.geo.json 2>&1 | grep -v "memory leak" | tail -1
$K python3.11 $H/route_oct_export.py RT-15S.kicad_pcb RT-15S.geo.json 2>&1 | grep -v "memory leak" | tail -1
rm -f *.kicad_prl libpf/*.kicad_prl
for s in RT-15P RT-15S RT-15 libpf/RT-15; do echo "$s:"; python3 scripts/drcsum.py $s.drc.json | head -2; done
$K python3.11 $H/silk_tile_gate.py RT-15P.kicad_pcb RT-15S.kicad_pcb --drc-base RT-15P.drc.json --drc-new RT-15S.drc.json --json t/RT-15.silkgate.json 2>&1 | grep -v "memory leak" | tail -8
