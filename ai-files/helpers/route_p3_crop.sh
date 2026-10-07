#!/bin/sh
# route_p3_crop.sh BOARD OUT.png LAYERS X0 Y0 X1 Y1 (mm)  ; board bbox 81.55..215.45 x 20..147.8
python3 - "$@" <<'P' > /tmp/claude-1000/crop.args
import sys
a=sys.argv; x0,y0,x1,y1=map(float,a[4:8]); X=81.55;Y=20;W=133.9;H=127.8
print((x0-X)/W,(y0-Y)/H,(x1-x0)/W,(y1-y0)/H)
P
/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/route_p1_view.sh "$1" "$2" "$3" $(cat /tmp/claude-1000/crop.args)
