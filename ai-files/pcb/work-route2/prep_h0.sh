#!/bin/sh
# prep_h0.sh : H0 for the S1-S3 run on RT-1. Strip every signal net (--all-signals list) EXCEPT the S0b/USB template nets
# (kept.txt), refill, export, DRC, OR1/OR2 order, then prepend the kept nets as stage S0 and lock their copper in the manifest.
set -e
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route2; cd $W
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
V=/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/V/bin/python
K=~/Applications/kicad.AppImage
printf '/USB_DP\n/USB_DN\nNet-(U2-D+)\nNet-(U2-D-)\nNet-(U2-XTO)\n' > kept.txt
# 1. list of all signal nets on RT-1 (the stripped output of this call is discarded)
python3 $H/route_oct_strip.py RT-1.kicad_pcb _all.kicad_pcb --all-signals base.kicad_pro --list all-signals.txt; rm -f _all.kicad_pcb
grep -vxF -f kept.txt all-signals.txt > H0.nets.txt
echo "all-signals $(wc -l < all-signals.txt), kept $(grep -cxF -f kept.txt all-signals.txt), to route $(wc -l < H0.nets.txt)"
# 2. strip the explicit list
python3 $H/route_oct_strip.py RT-1.kicad_pcb H0-raw.kicad_pcb --nets H0.nets.txt
cp -f base.kicad_pro H0-raw.kicad_pro; cp -f base.kicad_dru H0-raw.kicad_dru
$K python3.11 $H/route_oct_refill.py H0-raw.kicad_pcb H0.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
cp -f base.kicad_pro H0.kicad_pro; cp -f base.kicad_dru H0.kicad_dru
$K python3.11 $H/route_oct_export.py H0.kicad_pcb H0.geo.json 2>&1 | grep -v "memory leak" | tail -1
$K kicad-cli pcb drc --severity-all --format json --all-track-errors -o H0.drc.json H0.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
$V $H/route_oct_order.py H0.geo.json H0.nets.txt order.txt
# 3. net file: S0 (kept, locked, not routed) + S1..S3
{ echo '# S0 = copper kept from RT-1 (USB pair template, XTO template); locked, not routed'
  echo 'S0 /USB_DP bcu=gnd'; echo 'S0 /USB_DN bcu=gnd pair=/USB_DP'; echo 'S0 Net-(U2-D+) bcu=gnd'; echo 'S0 Net-(U2-D-) bcu=gnd pair=Net-(U2-D+)'; echo 'S0 Net-(U2-XTO)'
  cat order.txt; } > hard-nets.txt
echo PREP DONE
