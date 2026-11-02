#!/bin/sh
# sentinel21.sh STEM : prove rule 21 works and is narrow. Three DRC runs on copies of STEM.kicad_pcb in sentinel/ with test tracks on In2
# inside the In2 GND pour (171-175, 40.5-42.5), real rule files unchanged:
#  A: RT-10 rules; /HP_G0 (rule-21 net) 0.25 + Net-(U14-FB) (not listed) 0.25 -> in2_power_only must fire for U14-FB only
#  B: RT-9p rules (no rule 21), same tracks -> in2_power_only must fire for both (rule 21 is what allows HP_G0)
#  C: RT-10 rules; /HP_G0 at 0.20 mm -> rt10_in2_slow_width must fire
set -e
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route10; cd $W; S=$1; D=sentinel; mkdir -p $D
[ -e $D/kicad-library ] || ln -s ../kicad-library $D/kicad-library; cp -f fp-lib-table $D/
printf '{"seg_add": [["In2.Cu", "/HP_G0", 0.25, 171.0, 41.0, 175.0, 41.0], ["In2.Cu", "Net-(U14-FB)", 0.25, 171.0, 42.5, 175.0, 42.5]]}' > $D/s21ab.json
printf '{"seg_add": [["In2.Cu", "/HP_G0", 0.2, 171.0, 41.0, 175.0, 41.0]]}' > $D/s21c.json
python3 scripts/edit.py $S.kicad_pcb $D/s21ab.json $D/S21A.kicad_pcb $D/S21A.edit.json
cp $D/S21A.kicad_pcb $D/S21B.kicad_pcb
python3 scripts/edit.py $S.kicad_pcb $D/s21c.json $D/S21C.kicad_pcb $D/S21C.edit.json
for t in A B C; do cp -f base.kicad_pro $D/S21$t.kicad_pro; cp -f RT-10.kicad_dru $D/S21$t.kicad_dru; done
cp -f /home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route9p/RT-9p.kicad_dru $D/S21B.kicad_dru
for t in A B C; do ~/Applications/kicad.AppImage kicad-cli pcb drc --severity-all --format json -o $D/S21$t.drc.json $D/S21$t.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1; rm -f $D/S21$t.kicad_prl; done
python3 - <<'P'
import json
def f(t):
    d = json.load(open('sentinel/S21%s.drc.json' % t)); out = []
    for v in d['violations']:
        if any('In2.Cu' in i['description'] and ('HP_G0' in i['description'] or 'U14-FB' in i['description']) for i in v['items']):
            out.append((v['type'], v['description'].split("rule '")[1].split("'")[0] if "rule '" in v['description'] else v['description'][:40], [i['description'][:40] for i in v['items']][0]))
    return out
A, B, C = f('A'), f('B'), f('C')
for t, r in (('A', A), ('B', B), ('C', C)): print(t, r)
okA = any(x[1] == 'in2_power_only' and 'U14-FB' in x[2] for x in A) and not any(x[1] == 'in2_power_only' and 'HP_G0' in x[2] for x in A)
okB = any(x[1] == 'in2_power_only' and 'HP_G0' in x[2] for x in B) and any(x[1] == 'in2_power_only' and 'U14-FB' in x[2] for x in B)
okC = any(x[1] == 'rt10_in2_slow_width' for x in C)
print('RULE21 SENTINEL', 'PASS' if okA and okB and okC else 'FAIL', okA, okB, okC)
P
