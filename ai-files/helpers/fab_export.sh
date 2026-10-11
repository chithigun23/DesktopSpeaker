#!/usr/bin/env bash
# Fab outputs for JLCPCB from a KiCad 10 board (Flatpak kicad-cli).
# Usage: fab_export.sh BOARD.kicad_pcb OUT_DIR [TAG]
# Produces: OUT_DIR/gerbers/*.g* (+ drill, map), OUT_DIR/<TAG>-gerbers.zip,
#           OUT_DIR/<TAG>-pos-jlc.csv (JLC CPL format, mm, both sides),
#           OUT_DIR/<TAG>-pos-kicad.csv, OUT_DIR/<TAG>-drill-report.txt
# The board is copied beside the project .kicad_pro/.kicad_dru/fp-lib-table and a
# kicad-library symlink so project rules, footprints and variables resolve.
set -euo pipefail
BOARD=$(readlink -f "$1"); OUT=$(readlink -f -m "$2"); TAG=${3:-$(basename "$BOARD" .kicad_pcb)}
PROJ=/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad
K="flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp --command=kicad-cli org.kicad.KiCad"
WORK=$(mktemp -d /tmp/fabexp.XXXX)
cp "$BOARD" "$WORK/DesktopSpeaker.kicad_pcb"
cp "$PROJ/DesktopSpeaker.kicad_pro" "$PROJ/DesktopSpeaker.kicad_dru" "$PROJ/fp-lib-table" "$WORK/"
[ -f "$PROJ/sym-lib-table" ] && cp "$PROJ/sym-lib-table" "$WORK/"
ln -s "$PROJ/kicad-library" "$WORK/kicad-library"
B="$WORK/DesktopSpeaker.kicad_pcb"
mkdir -p "$OUT/gerbers"; rm -f "$OUT"/gerbers/*
LAYERS="F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
$K pcb export gerbers --output "$OUT/gerbers/" --layers "$LAYERS" --no-x2 --no-netlist \
   --subtract-soldermask --use-drill-file-origin --check-zones --precision 6 "$B"
$K pcb export drill --output "$OUT/gerbers/" --format excellon --drill-origin plot \
   --excellon-zeros-format decimal --excellon-units mm --excellon-separate-th \
   --generate-map --map-format gerberx2 --generate-report --report-path "$OUT/$TAG-drill-report.txt" "$B"
$K pcb export pos --output "$OUT/$TAG-pos-kicad.csv" --format csv --units mm --side both \
   --use-drill-file-origin --exclude-dnp "$B"
# JLC CPL: Designator,Mid X,Mid Y,Layer,Rotation
python3 - "$OUT/$TAG-pos-kicad.csv" "$OUT/$TAG-pos-jlc.csv" <<'PY'
import csv,sys
rows=list(csv.DictReader(open(sys.argv[1])))
with open(sys.argv[2],'w',newline='') as f:
    w=csv.writer(f); w.writerow(["Designator","Mid X","Mid Y","Layer","Rotation"])
    for r in rows:
        w.writerow([r["Ref"],f'{float(r["PosX"]):.4f}mm',f'{float(r["PosY"]):.4f}mm',
                    "Top" if r["Side"]=="top" else "Bottom",f'{float(r["Rot"]):.2f}'])
print(len(rows),"placements")
PY
python3 -c "import sys,zipfile,os; z=zipfile.ZipFile(sys.argv[1],'w',zipfile.ZIP_DEFLATED); [z.write(os.path.join(sys.argv[2],f),f) for f in sorted(os.listdir(sys.argv[2]))]; z.close()" "$OUT/$TAG-gerbers.zip" "$OUT/gerbers"
ls -1 "$OUT/gerbers" | sed 's/^/  /'; ls -l "$OUT/$TAG-gerbers.zip"
rm -rf "$WORK"
