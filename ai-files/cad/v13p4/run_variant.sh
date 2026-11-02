#!/usr/bin/env bash
# v13p4 battery study: build + check (+ render) one variant.  usage: run_variant.sh 2P|3P|4P [render]
set -euo pipefail
ROOT=/home/chithi/Desktop/DesktopSpeaker
SC=$ROOT/ai-files/cad/v13p4/scripts
export BATT=$1 CAD_OUT=$ROOT/ai-files/cad/v13p4/$1 SKIP_EXPORT=1
export BOARD_STEP=$ROOT/ai-files/pcb/work-cad13/board.step LAYOUT=$ROOT/ai-files/pcb/work-cad13/layout.json
mkdir -p "$CAD_OUT"
freecadcmd "$SC/build_speaker_cad.py" > "$CAD_OUT/build.log" 2>&1; grep -a "BUILD OK" "$CAD_OUT/build.log"
freecadcmd "$SC/check_cad.py" > "$CAD_OUT/check.log" 2>&1; grep -a "^unintended" "$CAD_OUT/check.log"; grep -a "^{" "$CAD_OUT/check.log"
[ "${2:-}" = render ] && freecadcmd "$SC/render_cad.py" > "$CAD_OUT/render.log" 2>&1
echo "done $1"
