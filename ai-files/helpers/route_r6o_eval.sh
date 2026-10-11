#!/bin/sh
# route_r6o_eval.sh STEM [PREV_STEM] [full] : R6o gates = route_r6n_eval.sh with R6o rules (R6n rules + usb_fs_waiver, rule 6b) and the route_r6l_eval.sh logic inlined;
# 'full' adds route_r6c_gates (via-in-pad, lengths), island continuity vs ISLREF (default R6o-0), strict DRC (every track split into 1 mm pieces,
# --all-track-errors), corner rule vs ISLREF (default R6o-0) (BOARD.bends.json), narrow-copper scan of all zone fills (STEM.sliver.json), pour areas, union, GND fill.
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6; H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers; export PATH=$H/bin:$PATH
FP="flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp/claude-1000 --command=python3 org.kicad.KiCad"
cd $W; cmp -s R6o.kicad_pro R6n.kicad_pro || echo "WARNING R6o project differs from R6n"
cp R6o.kicad_pro $1.kicad_pro; cp R6o.kicad_dru $1.kicad_dru
$FP $H/route_p2_open2.py $1.kicad_pcb $1.open2.json all >/dev/null 2>&1
kicad-cli pcb drc --format json --severity-all --units mm -o $1.drc.json $1.kicad_pcb >/dev/null 2>&1
python3 - $1 ${2:-none} <<'P'
import json,collections,sys,fnmatch
f,a=sys.argv[1:3];pro=json.load(open(f+'.kicad_pro'));pats=pro['net_settings']['netclass_patterns']
def cl(n):
    for p in pats:
        if fnmatch.fnmatchcase(n,p['pattern']): return p['netclass']
    return 'Default'
o=json.load(open(f+'.open2.json'));c=collections.Counter()
for k,v in o.items(): c[cl(k)]+=v
try: o0=json.load(open(a+'.open2.json'))
except Exception: o0={}
d=json.load(open(f+'.drc.json'));t=collections.Counter(x['type'] for x in d['violations'] if not x['type'].startswith('silk') and x['type']!='lib_footprint_mismatch')
s=collections.Counter(x['type'] for x in d['violations'] if x['type'].startswith('silk') or x['type']=='lib_footprint_mismatch')
print(f,'OPEN',sum(o.values()),dict(c));print(' DRC',dict(t),'silk/lib',sum(s.values()))
for x in d['violations']:
    if not x['type'].startswith('silk') and x['type'] not in ('lib_footprint_mismatch','skew_out_of_range','diff_pair_uncoupled_length_too_long'): print('  ',x['type'],x['description'][:90],[(i['description'][:50],i['pos']['x'],i['pos']['y']) for i in x['items']])
for k in sorted(set(o)|set(o0)):
    if o.get(k,0)!=o0.get(k,0): print('  delta',k,o0.get(k,0),'->',o.get(k,0))
P
if [ "$3" = full ]; then
 $FP $H/route_r6c_gates.py $1.kicad_pcb 2>&1 | grep -v -e Gtk -e '^$' -e swig
 $FP $H/route_r6h_isl.py $1.kicad_pcb ${ISLREF:-R6o-0}.isl.json 2>&1 | grep -v -e Gtk -e '^$' -e swig
 T=$1sp; cp R6o.kicad_pro $T.kicad_pro; cp R6o.kicad_dru $T.kicad_dru
 $FP $H/route_r6l_splitall.py $1.kicad_pcb $T.kicad_pcb 1.0 2>&1 | grep split
 kicad-cli pcb drc --all-track-errors --format json --severity-all --units mm -o $1.strict.json $T.kicad_pcb >/dev/null 2>&1
 python3 - $1.strict.json <<'P'
import json,sys,collections
d=json.load(open(sys.argv[1])); print(' strict DRC', dict(collections.Counter(x['type'] for x in d['violations'] if not x['type'].startswith('silk') and x['type']!='lib_footprint_mismatch')))
for x in d['violations']:
    if not x['type'].startswith('silk') and x['type'] not in ('lib_footprint_mismatch','skew_out_of_range','diff_pair_uncoupled_length_too_long'): print('  ',x['type'],x['description'][:70],[(i['description'][:40],i['pos']['x'],i['pos']['y']) for i in x['items']])
P
 rm -f $T.kicad_pcb $T.kicad_pro $T.kicad_dru $T.kicad_prl
 $FP $H/route_r6i_bends.py $1.kicad_pcb ${ISLREF:-R6o-0}.kicad_pcb --json $1.bends.json 2>&1 | grep -v -e Gtk -e '^$' -e swig -e Debug | tail -12
 $FP $H/route_r6m_sliver.py $1.kicad_pcb $1.sliver.json 2>&1 | grep -A3 NARROW | grep -v -e Gtk
 $FP $H/route_r6l_pourarea.py $1.kicad_pcb $1.pour.json 2>&1 | grep -v -e Gtk -e '^$' -e swig
 $FP $H/route_r6l_union.py $1.kicad_pcb 2>&1 | grep -v -e Gtk -e '^$' -e swig
 $FP $H/route_r6l_gndfill.py $1.kicad_pcb 2>&1 | grep 'GND layer'
fi
