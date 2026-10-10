#!/bin/sh
# route_r6l_verify2.sh STEM STATE.json : strict re-check of an overspec result: split every track into 1 mm pieces, DRC, revert widened
# items holding a violating piece (route_r6l_widen.py verify2), repeat until no item is reverted.
H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers; W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6; export PATH=$H/bin:$PATH
FP="flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp/claude-1000 --command=python3 org.kicad.KiCad"
cd $W; T=$1sp; cp R6l.kicad_pro $T.kicad_pro; cp R6l.kicad_dru $T.kicad_dru
for j in 1 2 3 4 5 6; do
 $FP $H/route_r6l_splitall.py $1.kicad_pcb $T.kicad_pcb 1.0 >/dev/null 2>&1
 kicad-cli pcb drc --all-track-errors --format json --severity-all --units mm -o $T.drc.json $T.kicad_pcb >/dev/null 2>&1
 r=$($FP $H/route_r6l_widen.py verify2 $1.kicad_pcb $1.kicad_pcb $2 $T.drc.json 2>&1 | grep verify2); echo "strict $j $r"
 case "$r" in *"reverted 0"*) break;; esac
done
python3 - $T.drc.json <<'P'
import json,sys,collections
d=json.load(open(sys.argv[1])); print(' strict DRC', dict(collections.Counter(x['type'] for x in d['violations'] if not x['type'].startswith('silk'))))
for x in d['violations']:
    if not x['type'].startswith('silk') and x['type'] not in ('lib_footprint_mismatch','skew_out_of_range','diff_pair_uncoupled_length_too_long'): print('  ',x['type'],x['description'][:70],[(i['description'][:40],i['pos']['x'],i['pos']['y']) for i in x['items']])
P
rm -f $T.kicad_pcb $T.kicad_pro $T.kicad_dru $T.drc.json $T.kicad_prl
