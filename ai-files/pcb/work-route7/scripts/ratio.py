import json,re,sys
J={(j['net'],j['from'],str(j['to'])):j for j in json.load(open(sys.argv[1]))['jobs']}
for l in open(sys.argv[2]):
    m=re.match(r'OK\s+(\S+)\s+(\S+) -> (\S+)\s+([\d.]+) mm, (\d+) segs, (\d+) vias',l)
    if m:
        j=J[(m.group(1),m.group(2),m.group(3))]; L=float(m.group(4)); d=j['_d']
        r=L/max(d,0.01); flag='BAD' if (L-d>2.0 and r>1.6) else ''
        print('%-32s %-8s %-8s L%6.2f d%6.2f r%5.2f v%s %s'%(m.group(1)[:32],m.group(2),m.group(3)[:8],L,d,r,m.group(6),flag))
