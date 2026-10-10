"""python3 route_r6c_drc.py STEM : print non-silk DRC violations"""
import json,sys
d=json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/%s.drc.json'%sys.argv[1]))
for v in d['violations']:
    if not v['type'].startswith('silk'): print(v['type'],v['description'][:110],[(i['description'][:42],i['pos']['x'],i['pos']['y']) for i in v['items']])
