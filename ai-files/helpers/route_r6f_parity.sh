#!/bin/sh
# route_r6f_parity.sh STEM : schematic-parity DRC of work-r6/STEM.kicad_pcb against a copy of the current schematic (work-r6/r6f/parity), prints parity item counts
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6; P=$W/r6f/parity; export PATH=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/bin:$PATH
cp $W/$1.kicad_pcb $P/DesktopSpeaker.kicad_pcb; cp $W/R6f.kicad_pro $P/DesktopSpeaker.kicad_pro; cp $W/R6f.kicad_dru $P/DesktopSpeaker.kicad_dru
kicad-cli pcb drc --schematic-parity --format json --severity-all --units mm -o $P/parity.json $P/DesktopSpeaker.kicad_pcb >/dev/null 2>&1
python3 - $P/parity.json <<'P'
import json,sys,collections
d=json.load(open(sys.argv[1])); s=d.get('schematic_parity',[])
print('parity items',len(s),dict(collections.Counter(x['type'] for x in s)))
for x in s[:30]: print('  ',x['type'],x['description'][:100],[i['description'][:60] for i in x['items']])
P
