"""routesum.py ROUTE.json [...] : per-connection status, failure classes and 'no exit' count per part"""
import sys, json, collections
PARTS = ['U9', 'U2', 'U11', 'U4', 'U8', 'J7', 'U20', 'C207', 'R225', 'R226', 'R108', 'C182']
tot = collections.Counter(); noexit = collections.Counter(); fails = []
for f in sys.argv[1:]:
    d = json.load(open(f)); s = d['summary']; print(f, s['stage'], 'conns ok %d/%d' % (s['conns_ok'], s['conns']), 'complete nets', s['complete_nets'], 'vias', s['vias'])
    for n in d['nets']:
        for c in n['conns']:
            st = c['status']; cls = 'ok' if st == 'ok' or st.startswith('direct') else st.split(':')[0][:40]
            tot[cls] += 1
            if cls != 'ok':
                fails.append((n['net'], c['a'], c['b'], st[:90]))
                if 'exit' in st:
                    for p in (c['a'], c['b']):
                        noexit[p.split('-')[0]] += 1
print('status classes', dict(tot))
print('no-exit endpoints per part (listed parts):', {p: noexit.get(p, 0) for p in PARTS})
print('no-exit endpoints all:', dict(noexit.most_common(25)))
if '-v' in os.environ.get('RS', '') if (os := __import__('os')) else 0: pass
for x in fails:
    if any(k in x[0] for k in ('I2S', 'AUD_S', 'USB', 'U2-D')) or __import__('os').environ.get('ALL'): print('  FAIL', *x)
