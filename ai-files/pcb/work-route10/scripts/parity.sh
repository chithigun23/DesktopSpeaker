#!/bin/sh
# parity.sh BOARD.kicad_pcb OUTDIR : DRC with --schematic-parity against the project schematic (copied beside a board copy in OUTDIR)
set -e
B=$1; O=$2; D=${3:-/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad}; W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route9p
st=$(basename $B .kicad_pcb); mkdir -p $O; rm -f $O/*.kicad_sch
cp $B $O/P.kicad_pcb; cp $W/base.kicad_pro $O/P.kicad_pro; cp $W/base6.kicad_dru $O/P.kicad_dru; cp $W/fp-lib-table $O/
[ -e $O/kicad-library ] || ln -s $W/kicad-library $O/kicad-library
for f in $D/*.kicad_sch; do cp $f $O/; done; mv $O/DesktopSpeaker.kicad_sch $O/P.kicad_sch
[ -f $D/sym-lib-table ] && cp $D/sym-lib-table $O/ || true
~/Applications/kicad.AppImage kicad-cli pcb drc --schematic-parity --severity-all --format json --all-track-errors -o $O/$st.parity.json $O/P.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
python3 - $O/$st.parity.json <<'P'
import json,sys,collections
d=json.load(open(sys.argv[1]))
print('violations',len(d['violations']),'unconnected',len(d['unconnected_items']),'parity',len(d.get('schematic_parity',[])))
print(collections.Counter(x['type'] for x in d.get('schematic_parity',[])))
for x in d.get('schematic_parity',[])[:40]: print(' ',x['type'],'|',x['description'][:80],'|',[i['description'][:70] for i in x['items']])
P
