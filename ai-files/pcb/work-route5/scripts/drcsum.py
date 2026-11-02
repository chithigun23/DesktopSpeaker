import json, sys, collections, re
d = json.load(open(sys.argv[1]))
v = d['violations']; u = d['unconnected_items']
print('DRC violations', len(v), dict(collections.Counter(x['type'] for x in v)), 'unconnected', len(u))
for x in v[:30]:
    print('  ', x['type'], '|', x['description'][:90], '|', ' ; '.join('%s @(%.3f,%.3f)' % (i['description'][:60], i['pos']['x'], i['pos']['y']) for i in x['items']))
