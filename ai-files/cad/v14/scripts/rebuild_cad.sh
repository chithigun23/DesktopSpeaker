#!/usr/bin/env bash
# One-shot CAD rebuild from a board + a KiCad library (v14 = v13 pipeline on RT-14; applies the models-v13 map to the board COPY first).
#
#   ai-files/cad/v14/scripts/rebuild_cad.sh BOARD.kicad_pcb [LIBRARY_DIR] [CAD_OUT] [WEB_OUT] [WORKDIR]
#
# BOARD        board file (its .kicad_pro / .kicad_dru / fp-lib-table are copied if present beside it)
# LIBRARY_DIR  folder with footprint/ and 3d/ (default: DesktopSpeaker-kicad/kicad-library); linked as WORKDIR/kicad-library
#              so ${KIPRJMOD}/kicad-library/... model paths resolve. Never point WORKDIR inside DesktopSpeaker-kicad/.
# CAD_OUT      default ai-files/cad/v14      WEB_OUT  default ai-files/website/desktopSpeaker-site/cad
# WORKDIR      default ai-files/pcb/work-cad14
# Env (v14): OLD_STEP / OLD_LAYOUT = fit_check baseline (default: the v13 board, ai-files/pcb/work-cad13/board.step + layout.json, RT-3)
# Env (v13): CH_DISP_L (woofer chamber displacement incl. front air, default in the build script 0.1224 L), M13_3D (models-v13/3d)
# Env: ND65_STEP (driver STEP), PYVENV (python with numpy; default the session scratch venv), SKIP_RENDER=1, GLB_LIN/GLB_ANG.
# Tools: ~/Applications/kicad.AppImage (kicad-cli, python3.11 for pcbnew; NEVER pass python3 to the AppImage), /usr/bin/freecadcmd,
#        google-chrome (preview renders are made separately, see the report).
set -euo pipefail
ROOT=/home/chithi/Desktop/DesktopSpeaker
BOARD=$(realpath "$1")
LIB=$(realpath "${2:-$ROOT/DesktopSpeaker-kicad/kicad-library}")
CAD_OUT=$(realpath -m "${3:-$ROOT/ai-files/cad/v14}")
WEB_OUT=$(realpath -m "${4:-$ROOT/ai-files/website/desktopSpeaker-site/cad}")
WD=$(realpath -m "${5:-$ROOT/ai-files/pcb/work-cad14}")
K=~/Applications/kicad.AppImage
PY=${PYVENV:-/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/venv/bin/python}
SC=$(dirname "$(realpath "$0")")
case "$WD" in "$ROOT/DesktopSpeaker-kicad"*) echo "WORKDIR must not be inside DesktopSpeaker-kicad" >&2; exit 1;; esac
mkdir -p "$WD" "$CAD_OUT" "$WEB_OUT/renders" "$WEB_OUT/downloads"
B=$(basename "$BOARD" .kicad_pcb); D=$(dirname "$BOARD")
cp "$BOARD" "$WD/$B.kicad_pcb"
for e in kicad_pro kicad_dru; do [ -f "$D/$B.$e" ] && cp "$D/$B.$e" "$WD/"; done
[ -f "$D/fp-lib-table" ] && cp "$D/fp-lib-table" "$WD/" || cp "$ROOT/DesktopSpeaker-kicad/fp-lib-table" "$WD/"
ln -sfn "$LIB" "$WD/kicad-library"
PCB="$WD/$B.kicad_pcb"
echo "== 0 models-v13 model links + BM83 offset on the board copy (idempotent; library already holds the STEP files)"
python3 "$ROOT/ai-files/cad/models-v13/apply.py" --board "$PCB"
sha256sum "$PCB" | tee "$WD/board.sha256"
echo "== 1 layout frame (pcbnew)"
$K python3.11 "$ROOT/ai-files/helpers/board_to_layout.py" "$PCB" "$WD/layout.json" "$ROOT/ai-files/pcb/layout.json"
grep -q '"frame": "u = x - 147.25, v = 88.8000 - y' "$WD/layout.json" || { echo "outline centre moved: update --user-origin and the pcb.glb translation" >&2; exit 2; }
echo "== 2 board STEP + GLB (same user origin as v11: 147.25 x 88.8 mm = layout u/v 0)"
$K kicad-cli pcb export step --force --subst-models --user-origin 147.25x88.8mm -o "$WD/board.step" "$PCB"
$K kicad-cli pcb export glb --force --subst-models --include-pads --include-soldermask --include-silkscreen --user-origin 147.25x88.8mm -o "$WD/pcb_raw.glb" "$PCB"
$K kicad-cli pcb export glb --force --subst-models --no-components --no-board-body --include-tracks --include-zones --user-origin 147.25x88.8mm -o "$WD/copper_raw.glb" "$PCB"
export CAD_OUT WEB_OUT BOARD_STEP="$WD/board.step" LAYOUT="$WD/layout.json"
echo "== 3 FreeCAD model, checks, fit"
freecadcmd "$SC/build_speaker_cad.py" > "$WD/build.log" 2>&1; grep -a "BUILD OK" "$WD/build.log"
freecadcmd "$SC/check_cad.py" > "$WD/check.log" 2>&1; grep -a "^unintended" "$WD/check.log"; grep -a "^{" "$WD/check.log"   # woof_net must stay 0.525 +- 0.05: else set CH_DISP_L = woof_disp + woof_front_air and rerun
OLD_STEP="${OLD_STEP:-$ROOT/ai-files/pcb/work-cad13/board.step}" OLD_LAYOUT="${OLD_LAYOUT:-$ROOT/ai-files/pcb/work-cad13/layout.json}" freecadcmd "$SC/fit_check.py" > "$WD/fit.log" 2>&1
[ "${SKIP_RENDER:-0}" = 1 ] || freecadcmd "$SC/render_cad.py" > "$WD/render.log" 2>&1
echo "== 4 web export"
freecadcmd "$SC/export_enclosure_glb.py" > "$WD/encglb.log" 2>&1; grep -a WROTE "$WD/encglb.log"
PCBZ=$(python3 -c "import json;print(json.load(open('$CAD_OUT/work/meta.json'))['pcb']['bot'])")
PCX=$(python3 -c "import json;print(json.load(open('$CAD_OUT/work/meta.json'))['pcb']['cx'])")
PCY=$(python3 -c "import json;print(-json.load(open('$CAD_OUT/work/meta.json'))['pcb']['cy'])")
"$PY" -I "$SC/glb_repack.py" "$WD/pcb_raw.glb" "$WEB_OUT/pcb.glb" --scale 1000 --translate "$PCX" "$PCBZ" "$PCY" --root-name "PCB_$B" --auto-names
"$PY" -I "$SC/glb_repack.py" "$WD/copper_raw.glb" "$WEB_OUT/pcb_copper.glb" --scale 1000 --translate "$PCX" "$PCBZ" "$PCY" --root-name "PCB_${B}_copper" --auto-names
"$PY" -I "$SC/validate_glb.py" "$WEB_OUT" "$CAD_OUT" > "$WD/validate.log"
cp "$CAD_OUT"/print/*.stl "$CAD_OUT/DesktopSpeaker_internal.step" "$WEB_OUT/downloads/"
(cd "$WEB_OUT/downloads" && rm -f SHA256SUMS && sha256sum -- * > SHA256SUMS)
python3 "$SC/make_web_meta.py" "$CAD_OUT" "$WEB_OUT" "$PCB" > "$WD/meta.log"
echo "done: $CAD_OUT  $WEB_OUT  (fit_findings.json in CAD_OUT is hand-written: review it for a new board)"
