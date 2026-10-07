#!/usr/bin/env python3
"""route_p1_unc.py DRC.json [CLASSES.json] : unconnected items per netclass and per net (nets listed for --nets)"""
import sys, json, re, collections
d = json.load(open(sys.argv[1]))
cls = json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/net-classes-p0.json'))
bycls = collections.Counter(); bynet = collections.Counter()
for u in d['unconnected_items']:
    m = re.search(r'\[([^\]]*)\]', u['items'][0]['description'])
    n = m.group(1) if m else '?'
    bynet[n] += 1; bycls[cls.get(n, '?')] += 1
print('total', sum(bycls.values()), dict(bycls.most_common()))
if '--nets' in sys.argv:
    for c in sys.argv[sys.argv.index('--nets')+1:]:
        print(c, [(n, k) for n, k in bynet.most_common() if cls.get(n) == c])
json.dump(bynet, open(sys.argv[1] + '.unc.json', 'w'))
