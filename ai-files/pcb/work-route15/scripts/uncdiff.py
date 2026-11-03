import json, sys
def S(f):
    d = json.load(open(f)); out = set()
    for u in d['unconnected_items']:
        out.add(' | '.join(sorted(('%s' % i['description']).split(' on ')[0] if 'Pad' in i['description'] else i['description'].split(',')[0] for i in u['items'])))
    return out
a, b = S(sys.argv[1]), S(sys.argv[2])
print('only before:', len(a - b)); [print('  -', x) for x in sorted(a - b)]
print('only after:', len(b - a)); [print('  +', x) for x in sorted(b - a)]
