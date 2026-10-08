#!/bin/sh
# Render the top side of a board to PNG (copper, silk, courtyards, fab text, outline), cropped to the board: v10_render.sh board.kicad_pcb out.png [dpi]
set -e
ROOT=/home/chithi/Desktop/DesktopSpeaker
export PATH=$ROOT/ai-files/helpers/bin:$PATH
B=$1; O=$2; DPI=${3:-300}
T=$(dirname $O)/.render_tmp
kicad-cli pcb export pdf --layers F.Cu,F.SilkS,F.Fab,F.CrtYd,Edge.Cuts --mode-single -o $T.pdf $B >/dev/null
BB=$(flatpak run --filesystem=$ROOT --command=python3 org.kicad.KiCad -c "
import pcbnew
b=pcbnew.LoadBoard('$B').GetBoardEdgesBoundingBox()
k=$DPI/25.4
print(int((b.GetX()/1e6-1)*k), int((b.GetY()/1e6-1)*k), int((b.GetWidth()/1e6+2)*k), int((b.GetHeight()/1e6+2)*k))" 2>/dev/null)
set -- $BB
pdftoppm -png -r $DPI -singlefile -x $1 -y $2 -W $3 -H $4 $T.pdf ${O%.png}
rm -f $T.pdf
echo "rendered $O"
