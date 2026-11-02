#!/bin/sh
# render.sh STEM OUTPREFIX : F.Cu and B.Cu (each with Edge.Cuts) of STEM.kicad_pcb as SVG (kicad-cli) and PNG (headless chrome), top view (B.Cu not mirrored).
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route8; cd $W; mkdir -p evidence
K=~/Applications/kicad.AppImage
for L in F B; do
  $K kicad-cli pcb export svg --mode-single --layers "$L.Cu,Edge.Cuts" --page-size-mode 2 --exclude-drawing-sheet --drill-shape-opt 1 -o evidence/$2-$L.svg $1.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
  printf '<html><body style="margin:0;background:#0b1a12"><img src="%s" style="width:1600px;display:block"></body></html>\n' $2-$L.svg > evidence/$2-$L.html
  WH=$(python3 -c "import re;s=open('evidence/$2-$L.svg').read(2000);m=re.search(r'width=\"([\d.]+)mm\" height=\"([\d.]+)mm\"',s);print(int(1600*float(m.group(2))/float(m.group(1)))+2)")
  google-chrome --headless=new --disable-gpu --no-sandbox --hide-scrollbars --screenshot=$W/evidence/$2-$L.png --window-size=1600,$WH file://$W/evidence/$2-$L.html >/dev/null 2>&1
  rm -f evidence/$2-$L.html
done
ls -la evidence/$2-*
