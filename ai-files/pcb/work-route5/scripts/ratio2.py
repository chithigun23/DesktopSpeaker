import json,sys,math
G=json.load(open(sys.argv[2])); pc={'%s-%s'%(p['ref'],p['num']):(p['x'],p['y']) for p in G['pads']}
for e in json.load(open(sys.argv[1])):
    if not e['ok']: continue
    J=e['job']; L=e['length']; nv=len(e['res']['vias'])
    if J['to']!='NET':
        a,b=pc[J['from']],pc[J['to']]; dx,dy=abs(a[0]-b[0]),abs(a[1]-b[1]); om=max(dx,dy)+0.4142*min(dx,dy)
    else: om=J['_d']
    bad = L > 1.5*om + 1.0
    print('%-30s %-8s %-8s L%6.2f min%6.2f r%5.2f v%d %s'%(J['net'][:30],J['from'],str(J['to'])[:8],L,om,L/max(om,.01),nv,'BAD' if bad else ''))
