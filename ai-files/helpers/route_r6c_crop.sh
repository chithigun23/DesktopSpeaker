#!/bin/sh
# route_r6c_crop.sh BOARD LAYERS OUT.png X Y W H [DPI]  (mm region; LAYERS comma list)
export PATH=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/bin:$PATH
B=$1; L=$2; O=$3; X=$4; Y=$5; W=$6; Hh=$7; DPI=${8:-400}
T=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/.crop_$$
kicad-cli pcb export pdf --layers $L,Edge.Cuts --mode-single -o $T.pdf $B >/dev/null 2>&1
python3 - <<P > $T.txt
k=$DPI/25.4
print(int($X*k), int($Y*k), int($W*k), int($Hh*k))
P
set -- $(cat $T.txt)
pdftoppm -png -r $DPI -singlefile -x $1 -y $2 -W $3 -H $4 $T.pdf ${O%.png}
rm -f $T.pdf $T.txt
