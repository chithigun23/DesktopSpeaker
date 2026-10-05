#!/usr/bin/env python3
"""Parse a kicad-cli sexpr netlist into {netname: set((ref,pin))}; CLI prints a net or compares two files."""
import re, sys
def parse(txt):
    toks = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', txt)
    st = [[]]
    for t in toks:
        if t == '(': st.append([])
        elif t == ')':
            x = st.pop(); st[-1].append(x)
        else: st[-1].append(t.strip('"') if t.startswith('"') else t)
    return st[0][0]
def nets(path):
    root = parse(open(path).read())
    out = {}
    for sec in root:
        if isinstance(sec, list) and sec and sec[0] == 'nets':
            for n in sec[1:]:
                if isinstance(n, list) and n[0] == 'net':
                    name = [x for x in n if isinstance(x, list) and x[0] == 'name'][0][1]
                    nodes = set()
                    for x in n:
                        if isinstance(x, list) and x[0] == 'node':
                            d = {y[0]: y[1] for y in x[1:] if isinstance(y, list) and len(y) > 1}
                            if not d['ref'].startswith('#'): nodes.add((d['ref'], d['pin']))
                    out[name] = nodes
    return out
if __name__ == '__main__':
    n = nets(sys.argv[1])
    for k, v in n.items():
        if any(a in k for a in sys.argv[2:]) or any(r in [x[0] for x in v] for r in sys.argv[2:]): print(k, sorted(v))
