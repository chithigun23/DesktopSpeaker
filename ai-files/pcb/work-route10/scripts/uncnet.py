"""uncnet.py A.drc.json B.drc.json : unconnected count per net (A vs B), prints the differing nets"""
import json, sys, re, collections
def C(f):
    c = collections.Counter()
    for u in json.load(open(f))['unconnected_items']:
        c[re.search(r'\[(.*?)\]', u['items'][0]['description']).group(1)] += 1
    return c
a, b = C(sys.argv[1]), C(sys.argv[2])
print('total', sum(a.values()), '->', sum(b.values()))
for n in sorted(set(a) | set(b)):
    if a[n] != b[n]: print('  %-40s %d -> %d' % (n, a[n], b[n]))
