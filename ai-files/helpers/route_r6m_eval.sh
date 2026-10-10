#!/bin/sh
# route_r6m_eval.sh STEM [PREV_STEM] [full] : R6m gates. R6m rules (byte copies of R6l/R6k) -> route_r6l_eval.sh logic (DRC + open edges diff vs PREV);
# 'full' adds route_r6c_gates (via-in-pad, lengths), island continuity vs R6l-final, strict DRC (every track split into 1 mm pieces,
# --all-track-errors), corner rule vs R6l-final (BOARD.bends.json), narrow-copper scan of all zone fills (STEM.sliver.json), pour areas, union, GND fill.
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6; H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers; export PATH=$H/bin:$PATH
FP="flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp/claude-1000 --command=python3 org.kicad.KiCad"
cd $W; cmp -s R6m.kicad_pro R6l.kicad_pro && cmp -s R6m.kicad_dru R6l.kicad_dru || echo 'WARNING R6m rules differ from R6l'
sh $H/route_r6l_eval.sh $1 ${2:-none} | grep -v 'zone change\|zone area'
cp R6m.kicad_pro $1.kicad_pro; cp R6m.kicad_dru $1.kicad_dru
if [ "$3" = full ]; then
 $FP $H/route_r6c_gates.py $1.kicad_pcb 2>&1 | grep -v -e Gtk -e '^$' -e swig
 $FP $H/route_r6h_isl.py $1.kicad_pcb R6l-final.isl.json 2>&1 | grep -v -e Gtk -e '^$' -e swig
 T=$1sp; cp R6m.kicad_pro $T.kicad_pro; cp R6m.kicad_dru $T.kicad_dru
 $FP $H/route_r6l_splitall.py $1.kicad_pcb $T.kicad_pcb 1.0 2>&1 | grep split
 kicad-cli pcb drc --all-track-errors --format json --severity-all --units mm -o $1.strict.json $T.kicad_pcb >/dev/null 2>&1
 python3 - $1.strict.json <<'P'
import json,sys,collections
d=json.load(open(sys.argv[1])); print(' strict DRC', dict(collections.Counter(x['type'] for x in d['violations'] if not x['type'].startswith('silk') and x['type']!='lib_footprint_mismatch')))
for x in d['violations']:
    if not x['type'].startswith('silk') and x['type'] not in ('lib_footprint_mismatch','skew_out_of_range','diff_pair_uncoupled_length_too_long'): print('  ',x['type'],x['description'][:70],[(i['description'][:40],i['pos']['x'],i['pos']['y']) for i in x['items']])
P
 rm -f $T.kicad_pcb $T.kicad_pro $T.kicad_dru $T.kicad_prl
 $FP $H/route_r6i_bends.py $1.kicad_pcb R6l-final.kicad_pcb --json $1.bends.json 2>&1 | grep -v -e Gtk -e '^$' -e swig -e Debug | tail -12
 $FP $H/route_r6m_sliver.py $1.kicad_pcb $1.sliver.json 2>&1 | grep -A3 NARROW | grep -v -e Gtk
 $FP $H/route_r6l_pourarea.py $1.kicad_pcb $1.pour.json 2>&1 | grep -v -e Gtk -e '^$' -e swig
 $FP $H/route_r6l_union.py $1.kicad_pcb 2>&1 | grep -v -e Gtk -e '^$' -e swig
 $FP $H/route_r6l_gndfill.py $1.kicad_pcb 2>&1 | grep 'GND layer'
fi
