#!/usr/bin/env python3
"""Print physical pin groups from a kicad sexpr netlist as JSON (names ignored)."""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'vendor'))
from sexpdata import load
def k(x): return str(x[0]) if isinstance(x,list) and x else ''
d=load(open(sys.argv[1])); nets=[v for v in d if k(v)=='nets'][0][1:]
groups={}
for n in nets:
    nodes=sorted(f"{[a for a in x if k(a)=='ref'][0][1]}.{[a for a in x if k(a)=='pin'][0][1]}" for x in n if k(x)=='node')
    nodes=[q for q in nodes if not q.startswith('#')]
    name=[a for a in n if k(a)=='name'][0][1]
    if nodes: groups[name]=nodes
json.dump(groups,open(sys.argv[2],'w'),indent=1,sort_keys=True)
