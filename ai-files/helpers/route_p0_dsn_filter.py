#!/usr/bin/env python3
"""Freerouting input filter: drop critical nets from the DSN network (they stay as pad obstacles), protect existing wiring.
usage: route_p0_dsn_filter.py IN.dsn OUT.dsn EXCLUDED_NETS.json   (writes the excluded list as json)"""
import sys, re, json
src, dst, exj = sys.argv[1:4]
cls = json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/net-classes-p0.json'))
txt = open(src).read()
EXC_CLASS = {'AUDIO', 'I2S_CLK', 'USB', 'SWITCH', 'BOOT', 'SPK_OUT', 'POWER_HI', 'PVDD'}
excl = {n for n, c in cls.items() if c in EXC_CLASS}
# network block
i = txt.index('  (network')
head, net = txt[:i], txt[i:]
# split top-level (net ...) blocks and (class ...) blocks by paren depth
def blocks(s):
    out = []; depth = 0; start = None; instr = False
    for k, ch in enumerate(s):
        if ch == '"': instr = not instr
        if instr: continue
        if ch == '(':
            if depth == 1: start = k
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 1: out.append((start, k+1))
    return out
bl = blocks(net)
# 1. find nets touching U1/U6/U7 (except GND)
def netname(b):
    m = re.match(r'\(net\s+("[^"]*"|\S+)', b); return m.group(1).strip('"') if m else None
for a, c in bl:
    b = net[a:c]
    nm = netname(b)
    if nm and nm != 'GND' and re.search(r'\b(U1|U6|U7)-', b): excl.add(nm)
for k in list(excl):
    if k.startswith('unconnected-'): excl.discard(k)
keep = []
pos = 0
res = net[:bl[0][0]]
for idx, (a, c) in enumerate(bl):
    b = net[a:c]; between = net[pos if idx == 0 else bl[idx-1][1]:a] if idx else ''
    if idx: res += net[bl[idx-1][1]:a]
    if b.startswith('(net '):
        if netname(b) in excl: continue
        res += b
    elif b.startswith('(class '):
        m = re.search(r'\(circuit|\(rule', b)
        hdr, rest = b[:m.start()], b[m.start():]
        toks = re.findall(r'"[^"]*"|[^\s]+', hdr)
        t2 = [toks[0], toks[1]] + [t for t in toks[2:] if t.strip('"') not in excl]
        res += '(' + ' '.join(t[1:] if j == 0 and t.startswith('(') else t for j, t in enumerate(t2[:1])) + ' ' + ' '.join(t2[1:]) + '\n      ' + rest
    else:
        res += b
res += net[bl[-1][1]:]
out = head + res
out = out.replace('(type route)', '(type protect)')
open(dst, 'w').write(out)
json.dump(sorted(excl), open(exj, 'w'), indent=0)
print('excluded nets', len(excl))
