#!/bin/sh
# route_r6k_upsize.sh IN_STEM OUT_STEM CLASSES : upsize power vias to 0.8/0.4, then revert every via DRC flags, until DRC has no new item
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers; W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6; export PATH=$H/bin:$PATH
FP="flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp/claude-1000 --command=python3 org.kicad.KiCad"
cd $W; for s in $2 $2u; do cp R6k.kicad_pro $s.kicad_pro; cp R6k.kicad_dru $s.kicad_dru; done
$FP $H/route_r6k_vsz.py $1.kicad_pcb $2u.kicad_pcb up $3 2>&1 | grep -v Gtk
for i in 1 2 3 4 5 6; do
 kicad-cli pcb drc --format json --severity-all --units mm -o $2u.drc.json $2u.kicad_pcb >/dev/null 2>&1
 r=$($FP $H/route_r6k_vsz.py $2u.kicad_pcb $2u.kicad_pcb revert $2u.drc.json 2>&1 | grep reverted); echo "iter $i $r"
 case "$r" in "reverted 0 "*) break;; esac
done
cp $2u.kicad_pcb $2.kicad_pcb; cp $2u.vsz.json $2.vsz.json; rm -f $2u.kicad_pcb $2u.kicad_pro $2u.kicad_dru $2u.drc.json $2u.vsz.json $2u.kicad_prl
