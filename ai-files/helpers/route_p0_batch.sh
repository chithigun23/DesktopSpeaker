#!/bin/sh
# usage: route_p0_batch.sh prep NAME INCLUDE_CLASSES MP   (exports DSN from work-p0/DesktopSpeaker-<prev>.kicad_pcb, filters, starts Freerouting in background, 25 min cap)
#        route_p0_batch.sh post NAME PREV                (imports SES, cleans, DRC, prunes violating autorouter items 3x -> DesktopSpeaker-<NAME>.kicad_pcb)
ROOT=/home/chithi/Desktop/DesktopSpeaker; W=$ROOT/ai-files/pcb/work-p0; export PATH=$ROOT/ai-files/helpers/bin:$PATH
FP="flatpak run --filesystem=$ROOT --filesystem=/tmp --command=python3 org.kicad.KiCad"
J=$HOME/Applications/freerouting/jre25/jdk-25.0.4.1+1-jre/bin/java
H=$ROOT/ai-files/helpers
q() { grep -v "swig\|Debug\|assert"; }
if [ "$1" = prep ]; then
  N=$2; INC=$3; MP=$4; PREV=${5:-zv}
  $FP $H/route_p0_dsn.py $W/DesktopSpeaker-$PREV.kicad_pcb $W/$N.in.dsn 2>&1 | q
  python3 $H/route_p0_dsn_filter.py $W/$N.in.dsn $W/$N.dsn $W/excl$N.json $INC
  nohup timeout 1500 $J -Djava.awt.headless=true -jar $HOME/Applications/freerouting/freerouting-2.5.0.jar -de $W/$N.dsn -do $W/$N.ses -mp $MP > $W/fr$N.log 2>&1 &
else
  N=$2; PREV=${3:-zv}
  $FP $H/route_p0_ses.py import $W/DesktopSpeaker-$PREV.kicad_pcb $W/$N.ses $W/imp$N.kicad_pcb 2>&1 | q
  $FP $H/route_p0_ses.py clean $W/imp$N.kicad_pcb $W/DesktopSpeaker-$N-0.kicad_pcb $W/excl$N.json $W/DesktopSpeaker-$PREV.kicad_pcb 2>&1 | q
  cur=$N-0
  for i in 1 2 3 4; do
    cp $W/DesktopSpeaker.kicad_pro $W/DesktopSpeaker-$cur.kicad_pro; cp $W/DesktopSpeaker.kicad_dru $W/DesktopSpeaker-$cur.kicad_dru
    kicad-cli pcb drc --format json --severity-all --units mm -o $W/drc-$cur.json $W/DesktopSpeaker-$cur.kicad_pcb >/dev/null
    python3 -c "
import json,collections;d=json.load(open('$W/drc-$cur.json'));print('$cur',dict(collections.Counter(x['type'] for x in d['violations'] if not x['type'].startswith('silk') and x['type'] not in('drill_out_of_range','hole_clearance'))),'unconnected',len(d['unconnected_items']))"
    [ $i = 4 ] && break
    $FP $H/route_p0_prune.py $W/DesktopSpeaker-$cur.kicad_pcb $W/drc-$cur.json $W/DesktopSpeaker-$PREV.kicad_pcb $W/DesktopSpeaker-$N-$i.kicad_pcb 2>&1 | grep pruned
    cur=$N-$i
  done
  cp $W/DesktopSpeaker-$cur.kicad_pcb $W/DesktopSpeaker-$N.kicad_pcb; cp $W/DesktopSpeaker.kicad_pro $W/DesktopSpeaker-$N.kicad_pro; cp $W/DesktopSpeaker.kicad_dru $W/DesktopSpeaker-$N.kicad_dru
fi
