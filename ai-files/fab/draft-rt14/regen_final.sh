#!/usr/bin/env bash
# regen_final.sh BOARD.kicad_pcb OUTDIR [--tag TAG] [--draft] [--teardrops] [--no-step]
# Env: HA8=<routing gate ha8.json> also writes OUTDIR/hand-assembly-sheet.md; PYVENV=python with shapely (stencil, via-in-pad).
#
# One-command release regeneration for the DesktopSpeaker board (KiCad 10.0.7 AppImage, headless).
# Given the final board (after the owner's GUI routing; teardrops either done in the GUI or with --teardrops):
#   0  work copy in OUTDIR/work beside the PRISTINE project .kicad_pro, the proposed project rules
#      (draft-rt14/proposed-project.kicad_dru = project rules + rules 20/21), fp-lib-table, sym-lib-table,
#      all schematic sheets and a kicad-library symlink (never inside DesktopSpeaker-kicad/)
#   1  teardrops: --teardrops = give every via without a teardrop block the R6q block (td_enable_vias.py) and let
#      kicad-cli regenerate all pad/via teardrops (drc --refill-zones --save-board; KiCad 10.0.7 does this headless);
#      without --teardrops the input's teardrops are compared with a headless regeneration on a scratch copy (gate)
#   2  zone fill: refill in a SEPARATE pcbnew process (helpers/route_oct_refill.py); the zone-fill signature of the
#      input is compared with the refill; if it differs the refilled board is used (and reported)
#   3  DRC with schematic parity (gates: 0 violations, 0 unconnected, 0 lib_footprint_mismatch, 0 new parity issues
#      vs the inherited set in draft-rt14/parity-baseline.json)
#   4  rule sentinels (3 DRC runs on copies): rule file is read (I2S_CLK 5 mm width rule fires), rule 21 allows only
#      its nets on In2 and enforces 0.25 mm, rule 20 is what clears the SW100 peg holes
#   5  exports: gerbers (11 layers, Protel names), Excellon PTH/NPTH + gerber drill maps + drill report, KiCad and JLC
#      position files, BOM from the schematic (kicad-cli + helpers/jlc_bom.py grouping), board STEP
#   6  helpers/fab_check.py on the outputs, CPL/BOM/board cross-checks, stencil check (0.10 mm foil) of the paste layer
#   7  SHA256SUMS, SUMMARY.txt; exit 0 only if no gate FAILs
# OUTDIR must be new or empty. Nothing outside OUTDIR is written.
set -uo pipefail
ROOT=/home/chithi/Desktop/DesktopSpeaker
HERE=$(dirname "$(realpath "$0")")
SC=$HERE/scripts
PROJ=$ROOT/DesktopSpeaker-kicad
H=$ROOT/ai-files/helpers
K=~/Applications/kicad.AppImage
PRO=${PRO:-$PROJ/DesktopSpeaker.kicad_pro}
DRU=${DRU:-$HERE/proposed-project.kicad_dru}
BASELINE=${BASELINE:-$HERE/parity-baseline.json}
REFBOM=${REFBOM:-$ROOT/ai-files/bom/DesktopSpeaker_JLC_BOM.csv}
PYVENV=${PYVENV:-/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/V/bin/python}
STENCIL_T=${STENCIL_T:-0.10}

[ $# -ge 2 ] || { sed -n '2,3p' "$0"; exit 2; }
BOARD=$(realpath "$1"); OUT=$(realpath -m "$2"); shift 2
TAG=""; DRAFT=0; TD=0; STEP=1
while [ $# -gt 0 ]; do case "$1" in
  --tag) TAG=$2; shift 2;; --draft) DRAFT=1; shift;; --teardrops) TD=1; shift;; --no-step) STEP=0; shift;;
  *) echo "unknown option $1" >&2; exit 2;; esac; done
STEM=$(basename "$BOARD" .kicad_pcb)
[ -n "$TAG" ] || { [ $DRAFT = 1 ] && TAG="DRAFT-$STEM" || TAG="DesktopSpeaker-$STEM"; }
case "$OUT" in "$PROJ"*) echo "OUTDIR must not be inside DesktopSpeaker-kicad/" >&2; exit 2;; esac
[ -f "$BOARD" ] || { echo "no board $BOARD" >&2; exit 2; }
if [ -d "$OUT" ] && [ -n "$(ls -A "$OUT")" ]; then echo "OUTDIR $OUT is not empty: choose a new folder" >&2; exit 2; fi
mkdir -p "$OUT"/{work,checks,gerbers,bom,stencil,board}
W=$OUT/work; C=$OUT/checks; LOG=$OUT/regen.log; GATES=$C/gates.txt; : > "$GATES"
kc() { "$K" kicad-cli "$@" 2>&1 | grep -v -e "memory leak" -e "Debug:" ; }
kp() { "$K" python3.11 "$@" 2>&1 | grep -v -e "memory leak" -e "Debug:" ; }
say() { echo "== $*" | tee -a "$LOG"; }
g() { tee -a "$GATES" | tee -a "$LOG"; }   # pipe GATE lines through g
gate() { echo "GATE $1 $2 ${3:-}" | g; }

say "regen_final $(date -Is)  board $BOARD  tag $TAG  draft $DRAFT  teardrops $TD"
echo "kicad-cli $("$K" kicad-cli version 2>/dev/null | tail -1); git $(git -C "$ROOT" rev-parse --short HEAD)" | tee -a "$LOG"
sha256sum "$BOARD" | tee "$C/input.sha256" | tee -a "$LOG"
if [ $DRAFT = 1 ]; then
  printf 'DRAFT - NOT FOR ORDERING.\nGenerated %s from %s (%s).\nThe board is not finished (see checks/gates.txt); regenerate with regen_final.sh on the final board.\n' \
    "$(date -Is)" "$BOARD" "$(cut -c1-16 "$C/input.sha256")" > "$OUT/DRAFT-NOT-FOR-ORDERING.txt"
fi

# ---- 0 work copy
B=$W/DesktopSpeaker.kicad_pcb
cp "$BOARD" "$B"; cp "$PRO" "$W/DesktopSpeaker.kicad_pro"; cp "$DRU" "$W/DesktopSpeaker.kicad_dru"
cp "$PROJ/fp-lib-table" "$PROJ/sym-lib-table" "$W/"; cp "$PROJ"/*.kicad_sch "$W/"
ln -sfn "$PROJ/kicad-library" "$W/kicad-library"
SIBPRO=$(dirname "$BOARD")/$STEM.kicad_pro
if [ -f "$SIBPRO" ]; then
  python3 - "$SIBPRO" "$PRO" > "$C/kicad_pro-diff.txt" <<'PY'
import json, sys
def flat(o, p=''):
    if isinstance(o, dict):
        for k, v in o.items(): yield from flat(v, p + '/' + k)
    elif isinstance(o, list):
        for i, v in enumerate(o): yield from flat(v, p + '[%d]' % i)
    else: yield p, o
a = dict(flat(json.load(open(sys.argv[1])))); b = dict(flat(json.load(open(sys.argv[2]))))
d = [(k, a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]
print('board-side .kicad_pro vs pristine project .kicad_pro: %d differing keys' % len(d))
for k, x, y in d: print('  %s: board %r  project %r' % (k, x, y))
PY
  n=$(head -1 "$C/kicad_pro-diff.txt" | grep -o '[0-9]* differing' | cut -d' ' -f1)
  gate kicad_pro_review "$([ "$n" = 0 ] && echo PASS || echo WARN)" "$n keys differ between $(basename "$SIBPRO") and the project .kicad_pro (exports use the project file; see checks/kicad_pro-diff.txt)"
fi
cmp -s "$DRU" "$HERE/proposed-project.kicad_dru" && gate rules_file PASS "proposed-project.kicad_dru $(sha256sum "$DRU" | cut -c1-12)" || gate rules_file WARN "custom DRU $DRU"

# ---- 1 teardrops
TD_IN=$(grep -A3 '(teardrop$' "$B" | grep -c 'type padvia')
if [ $TD = 1 ]; then
  say "1 teardrops: enable on all vias, regenerate headless (kicad-cli drc --refill-zones --save-board)"
  python3 "$SC/td_enable_vias.py" "$B" "$B.tmp" | tee -a "$LOG" && mv "$B.tmp" "$B"
  kc pcb drc --refill-zones --save-board --format json -o "$C/teardrop-pass.drc.json" "$B" | tail -1 | tee -a "$LOG"
  TD_OUT=$(grep -A3 '(teardrop$' "$B" | grep -c 'type padvia')
  gate teardrops INFO "regenerated headless: $TD_IN -> $TD_OUT teardrop zones (all pads and vias, curved, pads max 1.0 mm / vias max 0.6 mm, track-to-track none)"
else
  say "1 teardrops: compare the input's teardrops with a headless regeneration (scratch copy)"
  mkdir -p "$W/tdchk"; T=$W/tdchk/DesktopSpeaker.kicad_pcb
  cp "$W/DesktopSpeaker.kicad_pro" "$W/DesktopSpeaker.kicad_dru" "$W/fp-lib-table" "$W/tdchk/"; ln -sfn "$PROJ/kicad-library" "$W/tdchk/kicad-library"
  python3 "$SC/td_enable_vias.py" "$B" "$T" > /dev/null
  kc pcb drc --refill-zones --save-board --format json -o "$C/tdchk.drc.json" "$T" | tail -1 > /dev/null
  kp "$SC/fillsig.py" "$B" "$C/input.sig.json" | tee -a "$LOG"
  kp "$SC/fillsig.py" "$T" "$C/tdregen.sig.json" | tee -a "$LOG"
  python3 "$SC/regen_checks.py" tdcmp "$C/input.sig.json" "$C/tdregen.sig.json" | g
  rm -f "$T" "$W/tdchk/DesktopSpeaker.kicad_prl"
fi

# ---- 2 zone fill (separate pcbnew process, pristine pro/dru beside the copy)
say "2 refill in a separate pcbnew process and compare fills"
kp "$SC/fillsig.py" "$B" "$C/prefill.sig.json" | tee -a "$LOG"
kp "$H/route_oct_refill.py" "$B" "$W/refill.kicad_pcb" | tail -1 | tee -a "$LOG"
kp "$SC/fillsig.py" "$W/refill.kicad_pcb" "$C/refill.sig.json" | tee -a "$LOG"
if python3 "$SC/regen_checks.py" fillcmp "$C/prefill.sig.json" "$C/refill.sig.json" fill | tee -a "$LOG" | grep -q SAME; then
  gate zone_fill PASS "fill was current (refill gives the same zone areas); exporting the board as given"
  rm -f "$W/refill.kicad_pcb"
else
  gate zone_fill INFO "fill was stale: exporting the refilled board (board/DesktopSpeaker.kicad_pcb holds it for adoption)"
  mv "$W/refill.kicad_pcb" "$B"
fi
cp "$B" "$OUT/board/DesktopSpeaker.kicad_pcb"; sha256sum "$OUT/board/DesktopSpeaker.kicad_pcb" | tee -a "$LOG"
kp "$SC/fpdump.py" "$B" "$C/footprints.json" | tee -a "$LOG"
TDN=$(grep -A3 '(teardrop$' "$B" | grep -c 'type padvia')
gate teardrop_count INFO "$TDN teardrop zones on the exported board (old release board R6q/R9: 1825)"

# ---- 4 sentinels (start in background, 3 DRC runs)
say "4 rule sentinels (background)"
S=$W/sentinel; mkdir -p "$S"; cp "$W/fp-lib-table" "$S/"; ln -sfn "$PROJ/kicad-library" "$S/kicad-library"
python3 "$SC/regen_checks.py" segadd "$B" "$S/SA.kicad_pcb" "In2.Cu,/HP_G0,0.25,171.0,41.0,175.0,41.0" "In2.Cu,Net-(U14-FB),0.25,171.0,42.5,175.0,42.5" | tee -a "$LOG"
cp "$S/SA.kicad_pcb" "$S/SB.kicad_pcb"
python3 "$SC/regen_checks.py" segadd "$B" "$S/SC.kicad_pcb" "In2.Cu,/HP_G0,0.2,171.0,41.0,175.0,41.0" | tee -a "$LOG"
for t in SA SB SC; do cp "$W/DesktopSpeaker.kicad_pro" "$S/$t.kicad_pro"; done
python3 "$SC/regen_checks.py" druappend "$DRU" "$S/SA.kicad_dru"
python3 "$SC/regen_checks.py" drustrip "$DRU" "$S/SB.kicad_dru" rt5_sw100_te_land rt10_in2_slow rt10_in2_slow_width
cp "$DRU" "$S/SC.kicad_dru"
( for t in SA SB SC; do kc pcb drc --severity-all --format json -o "$C/sentinel-$t.drc.json" "$S/$t.kicad_pcb" > "$C/sentinel-$t.log" & done; wait ) &
SPID=$!

# ---- 3 DRC + parity
say "3 DRC with schematic parity"
kc pcb drc --schematic-parity --severity-all --all-track-errors --units mm --format json -o "$C/drc.json" "$B" | tail -3 | tee -a "$LOG"
kc pcb drc --schematic-parity --severity-all --all-track-errors --units mm --format report -o "$C/drc.rpt" "$B" > /dev/null
python3 "$SC/regen_checks.py" drc "$C/drc.json" "$BASELINE" | g

# ---- 5 exports (from a copy named after the tag, so every file carries the tag)
say "5 exports"
X=$W/exp; mkdir -p "$X"; XB=$X/$TAG.kicad_pcb
cp "$B" "$XB"; cp "$W/DesktopSpeaker.kicad_pro" "$X/$TAG.kicad_pro"; cp "$W/DesktopSpeaker.kicad_dru" "$X/$TAG.kicad_dru"
cp "$W/fp-lib-table" "$X/"; ln -sfn "$PROJ/kicad-library" "$X/kicad-library"
LAYERS="F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
kc pcb export gerbers --output "$OUT/gerbers/" --layers "$LAYERS" --no-x2 --no-netlist --subtract-soldermask \
   --use-drill-file-origin --check-zones --precision 6 "$XB" | tail -1 | tee -a "$LOG"
kc pcb export drill --output "$OUT/gerbers/" --format excellon --drill-origin plot --excellon-zeros-format decimal \
   --excellon-units mm --excellon-separate-th --generate-map --map-format gerberx2 --generate-report \
   --report-path "$OUT/$TAG-drill-report.txt" "$XB" | tail -1 | tee -a "$LOG"
kc pcb export pos --output "$OUT/$TAG-pos-kicad.csv" --format csv --units mm --side both --use-drill-file-origin --exclude-dnp "$XB" | tail -1 | tee -a "$LOG"
python3 "$SC/regen_checks.py" cpl "$OUT/$TAG-pos-kicad.csv" "$OUT/$TAG-pos-jlc.csv" "$C/footprints.json" | g
python3 -c "import sys,zipfile,os; z=zipfile.ZipFile(sys.argv[1],'w',zipfile.ZIP_DEFLATED); [z.write(os.path.join(sys.argv[2],f),f) for f in sorted(os.listdir(sys.argv[2]))]; z.close()" "$OUT/$TAG-gerbers.zip" "$OUT/gerbers"
# BOM from the schematic (per reference) + JLC grouping
kc sch export bom --fields 'Reference,Value,Footprint,MPN,Manufacturer,LCSC,LCSC Part,${DNP}' \
   --labels 'Reference,Value,Footprint,MPN,Manufacturer,LCSC,LCSC Part,DNP' --group-by '' --ref-range-delimiter '' \
   -o "$OUT/bom/$TAG-sch-bom.csv" "$W/DesktopSpeaker.kicad_sch" | tail -1 | tee -a "$LOG"
python3 "$H/jlc_bom.py" "$OUT/bom/$TAG-sch-bom.csv" "$OUT/bom/${TAG}_JLC_BOM.csv" | tee -a "$LOG"
python3 "$SC/regen_checks.py" bom "$OUT/bom/${TAG}_JLC_BOM.csv" "$REFBOM" "$C/footprints.json" "$OUT/$TAG-pos-jlc.csv" | g
# ERC (inherited 240 expected: 238 lib_symbol_issues, 1 power_pin_not_driven, 1 same_local_global_label)
kc sch erc --severity-all --format json -o "$C/erc.json" "$W/DesktopSpeaker.kicad_sch" | tail -1 | tee -a "$LOG"
python3 - "$C/erc.json" <<'PY' | g
import json, sys, collections
d = json.load(open(sys.argv[1])); v = [x for s in d['sheets'] for x in s['violations']]
c = collections.Counter(x['type'] for x in v)
ok = dict(c) == {'lib_symbol_issues': 238, 'power_pin_not_driven': 1, 'same_local_global_label': 1}
print('GATE erc %s %d %s (inherited set: 238 lib_symbol_issues, 1 power_pin_not_driven, 1 same_local_global_label)' % ('PASS' if ok else 'WARN', len(v), dict(c)))
PY
if [ $STEP = 1 ]; then
  kc pcb export step --force --subst-models -o "$OUT/$TAG-board.step" "$XB" | tail -1 | tee -a "$LOG"
  [ -s "$OUT/$TAG-board.step" ] && gate step PASS "$(du -h "$OUT/$TAG-board.step" | cut -f1) $TAG-board.step" || gate step FAIL "no STEP written"
fi

# ---- 6 fab_check, stencil
say "6 fab_check and stencil"
kp "$H/fab_check.py" "$OUT" "$B" > "$C/fab_check.txt"; cat "$C/fab_check.txt" >> "$LOG"
python3 "$SC/regen_checks.py" fabcheck "$C/fab_check.txt" | g
kp "$SC/paste_dump.py" "$B" "$C/paste.json" | tee -a "$LOG"
if [ -x "$PYVENV" ] && "$PYVENV" -c "import shapely" 2>/dev/null; then
  "$PYVENV" -I "$SC/stencil_check.py" "$C/paste.json" "$OUT/stencil/stencil-report" "$STENCIL_T" | tee -a "$LOG"
  python3 "$SC/regen_checks.py" stencil "$OUT/stencil/stencil-report.json" | g
  "$PYVENV" -I "$SC/via_in_pad.py" "$C/paste.json" "$C/via_in_pad.json" | tee -a "$LOG" | sed 's/^VIAPAD /GATE via_in_pad INFO /' | g
  if [ -n "${HA8:-}" ] && [ -f "$HA8" ]; then
    python3 "$SC/make_ha_sheet.py" "$C/footprints.json" "$HA8" "$OUT/stencil/stencil-report.json" \
      "$ROOT/ai-files/cad/models-v13/accuracy-table.csv" "$OUT/hand-assembly-sheet.md" "$TAG" | tee -a "$LOG"
  fi
else
  gate stencil_area_ratio WARN "no python with shapely at PYVENV=$PYVENV: stencil check skipped"
fi

# ---- sentinels result
wait $SPID
python3 "$SC/regen_checks.py" sentinel "$C/sentinel-SA.drc.json" "$C/sentinel-SB.drc.json" "$C/sentinel-SC.drc.json" | g
rm -f "$S"/S?.kicad_pcb "$S"/S?.kicad_prl "$X/$TAG.kicad_pcb" "$X/$TAG.kicad_prl" "$W/DesktopSpeaker.kicad_prl"

# ---- 7 checksums and summary
say "7 SHA256SUMS and summary"
( cd "$OUT" && find . -path ./work -prune -o -type f ! -name SHA256SUMS -print | sort | sed 's|^\./||' | xargs -d '\n' sha256sum > SHA256SUMS )
NF=$(grep -c ' FAIL ' "$GATES"); NW=$(grep -c ' WARN ' "$GATES")
{
  echo "regen_final $TAG  $(date -Is)"; echo "input  $(cat "$C/input.sha256")"
  echo "output $(sha256sum "$OUT/board/DesktopSpeaker.kicad_pcb" | cut -d' ' -f1)  board/DesktopSpeaker.kicad_pcb"
  [ $DRAFT = 1 ] && echo "DRAFT - NOT FOR ORDERING"
  echo; awk '/^GATE /{n=$2; r=$3; $1=$2=$3=""; sub(/^ +/, ""); printf "%-24s %-5s %s\n", n, r, $0; next} {print}' "$GATES"
  echo; [ "$NF" = 0 ] && echo "RESULT: PASS ($NW warnings)" || echo "RESULT: FAIL ($NF failing gates, $NW warnings)"
} > "$OUT/SUMMARY.txt"
cat "$OUT/SUMMARY.txt"
[ "$NF" = 0 ]
