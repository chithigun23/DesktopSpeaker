#!/bin/sh
# route_p2_cycle.sh IN OUT : DRC-driven removal (IN-f.drc.json) -> reroute queue -> OUT.kicad_pcb ; then eval OUT
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-p3; H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
FP="flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp --command=python3 org.kicad.KiCad"
cp $W/S0.kicad_pro $W/$1.kicad_pro; cp $W/S0.kicad_pro $W/$2-x.kicad_pro; cp $W/S0.kicad_pro $W/$2.kicad_pro
$FP $H/route_p2_drcfix.py $W/$1.kicad_pcb $W/$1-f.drc.json $W/$2-x.kicad_pcb $W/$2-q.json 2>&1 | grep -v -E "assert|swig"
P3CLASSES=AUDIO,USB,I2S_CLK,I2C,PWR_5V,PWR_3V,PWR_LOCAL,SIGNAL,SWITCH,BOOT,SPK_OUT,POWER_HI,PVDD $FP $H/route_p3_run.py $W/$2-x.kicad_pcb $W/$2.kicad_pcb ALL --only $W/$2-q.json 2>&1 | grep -v -E "assert|swig" > $W/$2.log
tail -1 $W/$2.log
$H/route_p3_eval.sh $2
