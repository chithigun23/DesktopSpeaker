#!/bin/sh
# route_r6f_step.sh IN_STEM OUT_STEM SPEC.json : apply hand spec (route_r6c_hand.py), then DRC + fragment-aware open edges; prints non-silk DRC items and the open list diff
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6; H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers; export PATH=$H/bin:$PATH
FP="flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp/claude-1000 --command=python3 org.kicad.KiCad"
cd $W
$FP $H/route_r6f_edit.py $1.kicad_pcb $2.kicad_pcb $3 2>&1 | grep -v -e '^$' -e Gtk
cp R6f.kicad_pro $2.kicad_pro; cp R6f.kicad_dru $2.kicad_dru
$FP $H/route_p2_open2.py $2.kicad_pcb $2.open2.json all >/dev/null 2>&1
kicad-cli pcb drc --format json --severity-all --units mm -o $2.drc.json $2.kicad_pcb >/dev/null 2>&1
python3 - $1 $2 <<'P'
import json,collections,sys,fnmatch
a,f=sys.argv[1:3];pro=json.load(open(f+'.kicad_pro'));pats=pro['net_settings']['netclass_patterns']
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
print(f,'OPEN',sum(o.values()),dict(c));print(' DRC',dict(t),'silk/lib',sum(s.values()),dict(s))
for x in d['violations']:
    if not x['type'].startswith('silk') and x['type'] not in ('lib_footprint_mismatch','skew_out_of_range','diff_pair_uncoupled_length_too_long'): print('  ',x['type'],x['description'][:90],[(i['description'][:50],i['pos']['x'],i['pos']['y']) for i in x['items']])
for k in sorted(set(o)|set(o0)):
    if o.get(k,0)!=o0.get(k,0): print('  delta',k,o0.get(k,0),'->',o.get(k,0))
P
