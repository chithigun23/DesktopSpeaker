#!/usr/bin/env bash
# Website PCB model + realistic board textures + hero renders from a board file (default: the current RT-15H).
#
#   ai-files/helpers/make_pcb_textures.sh [BOARD.kicad_pcb] [WORKDIR]
#
# WORKDIR (default: a fresh folder under /tmp) gets a COPY of the board with its .kicad_pro/.kicad_dru/fp-lib-table and
# a kicad-library link; never point it inside DesktopSpeaker-kicad/. Writes into ai-files/website/desktopSpeaker-site/cad/:
#   pcb_<tag>.glb, pcb_copper_<tag>.glb   kicad-cli glb export repacked like CAD v15 (same user origin and placement)
#   pcb_textures/                          {top,bottom}_albedo.jpg, *_rmb.jpg, top_albedo_2k.jpg, textures.json
#   renders/pcb_real_{top,bottom,iso}.png  kicad-cli pcb render --quality high
# The viewer (app.js) reads cad/pcb_textures/textures.json; its "glb"/"copper_glb" keys replace the pcb files of meta.json.
# Env: PYVENV = python with numpy, pillow, cairosvg (default: the session scratch venv); TAG (default RT15H).
# Placement: PCB_T = "x y z" translation of the board in the enclosure frame (CAD v15: -3.5 67.0 -133.3, from
# ai-files/cad/v15/work/meta.json pcb.cx / pcb.bot / -pcb.cy); the outline centre must stay at 147.25 x 88.8 mm.
set -euo pipefail
ROOT=/home/chithi/Desktop/DesktopSpeaker
BOARD=$(realpath "${1:-$ROOT/ai-files/pcb/gui-finish/DesktopSpeaker-RT15H.kicad_pcb}")
WD=$(realpath -m "${2:-$(mktemp -d)}")
case "$WD" in "$ROOT/DesktopSpeaker-kicad"*) echo "WORKDIR must not be inside DesktopSpeaker-kicad" >&2; exit 1;; esac
K=~/Applications/kicad.AppImage           # kicad-cli and python3.11 only; NEVER "python3" (opens the GUI)
PY=${PYVENV:-/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/V/bin/python}
TAG=${TAG:-RT15H}; tag=$(echo "$TAG" | tr 'A-Z' 'a-z')
read -r TX TY TZ <<< "${PCB_T:--3.5 67.0 -133.3}"
SITE=$ROOT/ai-files/website/desktopSpeaker-site/cad
SC=$ROOT/ai-files/cad/v15/scripts
H=$(dirname "$(realpath "$0")")
mkdir -p "$WD" "$SITE/pcb_textures" "$SITE/renders"
B=$(basename "$BOARD" .kicad_pcb); D=$(dirname "$BOARD")
cp "$BOARD" "$WD/"; for e in kicad_pro kicad_dru; do [ -f "$D/$B.$e" ] && cp "$D/$B.$e" "$WD/"; done
cp "$D/fp-lib-table" "$WD/" 2>/dev/null || cp "$ROOT/DesktopSpeaker-kicad/fp-lib-table" "$WD/"
ln -sfn "$ROOT/DesktopSpeaker-kicad/kicad-library" "$WD/kicad-library"
P="$WD/$B.kicad_pcb"
python3 "$ROOT/ai-files/cad/models-v13/apply.py" --board "$P"          # models-v13 links (idempotent)
echo "== glb"
$K kicad-cli pcb export glb --force --subst-models --include-pads --include-soldermask --include-silkscreen --user-origin 147.25x88.8mm -o "$WD/pcb_raw.glb" "$P"
$K kicad-cli pcb export glb --force --subst-models --no-components --no-board-body --include-tracks --include-zones --user-origin 147.25x88.8mm -o "$WD/copper_raw.glb" "$P"
"$PY" -I "$SC/glb_repack.py" "$WD/pcb_raw.glb" "$SITE/pcb_$tag.glb" --scale 1000 --translate $TX $TY $TZ --root-name "PCB_$TAG" --auto-names
"$PY" -I "$SC/glb_repack.py" "$WD/copper_raw.glb" "$SITE/pcb_copper_$tag.glb" --scale 1000 --translate $TX $TY $TZ --root-name "PCB_${TAG}_copper" --auto-names
echo "== textures"
$K python3.11 "$H/make_pcb_textures.py" dump "$P" "$WD/dump.json"
SHA=$(sha256sum "$BOARD" | cut -c1-64)
TEX_EXTRA=$(printf '{"board": "%s", "glb": "pcb_%s.glb", "copper_glb": "pcb_copper_%s.glb", "glb_bytes": %d, "copper_bytes": %d, "origin_mm": [147.25, 88.8], "board_name": "%s", "board_sha256": "%s", "placement_mm": [%s, %s, %s], "renders": ["renders/pcb_real_iso.png", "renders/pcb_real_top.png", "renders/pcb_real_bottom.png"], "generated": "%s", "tool": "ai-files/helpers/make_pcb_textures.sh"}' \
  "${BOARD#$ROOT/}" "$tag" "$tag" "$(stat -c %s "$SITE/pcb_$tag.glb")" "$(stat -c %s "$SITE/pcb_copper_$tag.glb")" "$B" "$SHA" "$TX" "$TY" "$TZ" "$(date +%F)") \
  "$PY" -I "$H/make_pcb_textures.py" build "$P" "$WD/dump.json" "$SITE/pcb_textures"
echo "== hero renders"
$K kicad-cli pcb render --side top --quality high --width 2000 --height 2000 -o "$WD/pcb_real_top.png" "$P"
$K kicad-cli pcb render --side bottom --quality high --width 2000 --height 2000 -o "$WD/pcb_real_bottom.png" "$P"
$K kicad-cli pcb render --side top --quality high --floor --perspective --rotate '-45,0,30' --zoom 0.72 --width 2400 --height 1600 --background opaque -o "$WD/pcb_real_iso.png" "$P"
"$PY" -I -c "
import sys
from PIL import Image
for n in ('top', 'bottom', 'iso'):
    im = Image.open(sys.argv[1] + '/pcb_real_%s.png' % n)
    im.thumbnail((1600, 1600), Image.LANCZOS)
    im.save(sys.argv[2] + '/pcb_real_%s.png' % n, optimize=True)
" "$WD" "$SITE/renders"
ls -la "$SITE/pcb_textures" "$SITE"/renders/pcb_real_*.png "$SITE/pcb_$tag.glb" "$SITE/pcb_copper_$tag.glb"
