#!/bin/sh
# route_r6h_eval.sh STEM [PREV_STEM] [full] : R6h rules; DRC + fragment-aware open edges (diff vs PREV); 'full' adds via-in-pad/EP/antenna/lengths + island continuity vs R6h-0
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6; H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers; export PATH=$H/bin:$PATH
FP="flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp/claude-1000 --command=python3 org.kicad.KiCad"
cd $W; cp R6h.kicad_pro $1.kicad_pro; cp R6h.kicad_dru $1.kicad_dru
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
 $FP $H/route_r6c_gates.py $1.kicad_pcb 2>&1 | grep -v -e Gtk -e '^$'
 $FP $H/route_r6h_isl.py $1.kicad_pcb R6h-0.isl.json 2>&1 | grep -v -e Gtk -e '^$'
fi
