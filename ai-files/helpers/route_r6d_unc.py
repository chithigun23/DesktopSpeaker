"""python3 route_r6d_unc.py STEM [filter] : list DRC unconnected item pairs (net, positions)"""
import json,sys,re
d=json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/%s.drc.json'%sys.argv[1]))
flt=sys.argv[2] if len(sys.argv)>2 else ''
for u in d['unconnected_items']:
    it=u['items']; n=re.search(r'\[([^\]]*)\]',it[0]['description']).group(1)
    if flt and flt not in n: continue
    print('%-28s'%n[:28],' | '.join('%s (%.2f,%.2f)'%(re.sub(r'\s*\[[^\]]*\]','',i['description'])[:34],i['pos']['x'],i['pos']['y']) for i in it))
