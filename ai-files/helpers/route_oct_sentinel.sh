#!/bin/sh
# route_oct_sentinel.sh WORKDIR STEM : prove the custom DRC rule file is read for STEM.kicad_pcb.
# Copies the board to sentinel/STEM_sentinel.* with the frozen rule file plus ONE extra rule appended
# (I2S_CLK tracks must be >= 5 mm wide) and runs kicad-cli DRC; the sentinel must fire. The real rule files are not changed.
set -e
cd $1; mkdir -p sentinel
cp -f $2.kicad_pcb sentinel/$2_sentinel.kicad_pcb; cp -f $2.kicad_pro sentinel/$2_sentinel.kicad_pro
cp -f $2.kicad_dru sentinel/$2_sentinel.kicad_dru
printf '\n(rule sentinel_route_oct\n  (condition "A.NetClass == '"'"'I2S_CLK'"'"'")\n  (constraint track_width (min 5mm)))\n' >> sentinel/$2_sentinel.kicad_dru
cp -f fp-lib-table sentinel/ 2>/dev/null || true; [ -e sentinel/kicad-library ] || ln -s ../kicad-library sentinel/kicad-library
~/Applications/kicad.AppImage kicad-cli pcb drc --severity-all --format json -o sentinel/$2_sentinel.drc.json sentinel/$2_sentinel.kicad_pcb 2>&1 | grep -v "memory leak" | tail -1
python3 -c "
import json,collections; d=json.load(open('sentinel/$2_sentinel.drc.json')); c=collections.Counter(v['type'] for v in d['violations'])
s=sum(1 for v in d['violations'] if 'sentinel_route_oct' in v.get('description',''))
print('sentinel violations:', s, dict(c)); print('SENTINEL', 'FIRES' if s>0 else 'DOES NOT FIRE')"
