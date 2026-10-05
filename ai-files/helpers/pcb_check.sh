#!/bin/sh
# DRC summary by type + PDF/PNG/SVG/3D renders of DesktopSpeaker.kicad_pcb into ai-files/pcb/
set -e
ROOT=/home/chithi/Desktop/DesktopSpeaker
export PATH=$ROOT/ai-files/helpers/bin:$PATH
B=$ROOT/DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb
O=$ROOT/ai-files/pcb
kicad-cli pcb drc --format json --severity-all --units mm -o $O/drc.json $B | tail -3
python3 - <<'PY'
import json, collections
d = json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/drc.json'))
for k in ('violations', 'unconnected_items', 'schematic_parity'):
    c = collections.Counter((x['type'], x['severity']) for x in d.get(k, []))
    print(k, len(d.get(k, [])), dict(c))
PY
kicad-cli pcb export pdf --layers F.Cu,F.SilkS,F.Mask,F.CrtYd,Edge.Cuts --black-and-white -o $O/layout-top.pdf $B >/dev/null
kicad-cli pcb export pdf --layers F.Cu,F.SilkS,F.Fab,Edge.Cuts -o $O/layout-top-colour.pdf $B >/dev/null
kicad-cli pcb export svg --layers F.Cu,F.SilkS,F.CrtYd,Edge.Cuts --page-size-mode 2 -o $O/layout-top.svg $B >/dev/null
pdftoppm -png -r 400 -singlefile $O/layout-top.pdf $O/layout-top-full
for side in top bottom; do
  kicad-cli pcb render --side $side --width 2400 --height 1800 --quality basic --background opaque -o $O/layout-3d-$side.png $B >/dev/null 2>&1 || echo "3D render $side failed"
done
