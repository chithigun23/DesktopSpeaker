#!/usr/bin/env python3
"""gndclean.py DRC.json POSES.json SRC.kicad_pcb : uuids of source-GND vias/tracks in DRC conflicts with pads of moved parts, plus
dangling GND items (source GND per uuid; the refill may re-net a via that overlaps a new pad)"""
import sys, json, re
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from pcbtext import items
d = json.load(open(sys.argv[1])); refs = set(json.load(open(sys.argv[2]))['poses'])
G = {x['uuid']: x for x in items(sys.argv[3]) if x['kind'] in ('via', 'segment') and x.get('net') in ('GND', '/3V3_AUDIO')}
seg, via = set(), set()
def add(i):
    if i['uuid'] in G: (via if G[i['uuid']]['kind'] == 'via' else seg).add(i['uuid'])
for v in d['violations']:
    its = v['items']
    if v['type'] in ('track_dangling', 'via_dangling'):
        for i in its: add(i)
        continue
    if any((lambda m: m and m.group(1) in refs)(re.search(r' of (\S+)', i['description'])) for i in its):
        for i in its: add(i)
print(json.dumps(dict(seg=sorted(seg), via=sorted(via))))
