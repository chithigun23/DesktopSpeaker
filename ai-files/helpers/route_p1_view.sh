#!/bin/sh
# route_p1_view.sh BOARD OUT.png LAYERS FX FY FW FH   (fractions of board bbox; colour theme)
export PATH=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/bin:$PATH
T=$(mktemp -d); kicad-cli pcb export svg --layers "$3,Edge.Cuts" --mode-single --page-size-mode 2 --exclude-drawing-sheet -o $T/a.svg "$1" >/dev/null 2>&1
node /home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/route_p1_png.mjs $T/a.svg "$2" 1600 $4 $5 $6 $7
