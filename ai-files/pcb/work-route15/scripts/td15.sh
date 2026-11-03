#!/bin/sh
# td15.sh : teardrop regeneration on a COPY of RT-15 (release to-do step 1.4, headless):
#   td_enable_vias.py, then kicad-cli pcb drc --refill-zones --save-board (pristine base.kicad_pro + RT-15.kicad_dru beside).
#   Run twice on fresh copies; the two results must be byte-identical. Result: RT-15-td.kicad_pcb (+ .kicad_pro/.kicad_dru).
set -e
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route15; cd $W
F=/home/chithi/Desktop/DesktopSpeaker/ai-files/fab/draft-rt14/scripts
K=~/Applications/kicad.AppImage
for r in 1 2; do
  D=td/run$r; mkdir -p $D; cp -f fp-lib-table $D/; [ -e $D/kicad-library ] || ln -s ../../kicad-library $D/kicad-library
  python3 $F/td_enable_vias.py RT-15.kicad_pcb $D/RT-15-td.kicad_pcb
  cp -f base.kicad_pro $D/RT-15-td.kicad_pro; cp -f RT-15.kicad_dru $D/RT-15-td.kicad_dru
  $K kicad-cli pcb drc --refill-zones --save-board --format json -o $D/pass.drc.json $D/RT-15-td.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
  rm -f $D/*.kicad_prl
  echo "run $r teardrop zones: $(grep -A3 '(teardrop$' $D/RT-15-td.kicad_pcb | grep -c 'type padvia')  (input: $(grep -A3 '(teardrop$' RT-15.kicad_pcb | grep -c 'type padvia'))"
  sha256sum $D/RT-15-td.kicad_pcb
done
cmp td/run1/RT-15-td.kicad_pcb td/run2/RT-15-td.kicad_pcb && echo "TEARDROP RE-RUN BYTE-IDENTICAL"
cp -f td/run1/RT-15-td.kicad_pcb RT-15-td.kicad_pcb; cp -f base.kicad_pro RT-15-td.kicad_pro; cp -f RT-15.kicad_dru RT-15-td.kicad_dru
$K kicad-cli pcb drc --severity-all --format json --all-track-errors -o RT-15-td.drc.json RT-15-td.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
cp -f RT-15-td.kicad_pcb libpf/RT-15-td.kicad_pcb; cp -f base.kicad_pro libpf/RT-15-td.kicad_pro; cp -f RT-15.kicad_dru libpf/RT-15-td.kicad_dru
$K kicad-cli pcb drc --severity-all --format json --all-track-errors -o libpf/RT-15-td.drc.json libpf/RT-15-td.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
rm -f *.kicad_prl libpf/*.kicad_prl
for s in RT-15-td libpf/RT-15-td; do echo "$s:"; python3 scripts/drcsum.py $s.drc.json | head -3; done
