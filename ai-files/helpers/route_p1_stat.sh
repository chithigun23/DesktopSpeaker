#!/bin/sh
# route_p1_stat.sh STEM : open edges by class using the union-find oracle
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-p1; H=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers
flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp --command=python3 org.kicad.KiCad $H/route_p1_open.py $W/$1.kicad_pcb $W/$1.open.json >/dev/null 2>&1
python3 - $W/$1.open.json <<'P'
import json,collections,sys
cls=json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-p1/net-classes-p1.json'));o=json.load(open(sys.argv[1]))
c=collections.Counter();n=collections.Counter()
for k,v in o.items():
    if k.startswith('unconnected-'): continue
    c[cls.get(k)]+=v;n[cls.get(k)]+=1
print('edges',dict(c),'nets',sum(n.values()))
P
