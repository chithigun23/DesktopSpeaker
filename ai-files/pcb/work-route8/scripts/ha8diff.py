"""ha8diff.py BASE.ha8.json NEW.ha8.json : HA8 failing pairs new / gone / tighter (gap smaller by > 1 um)"""
import json, sys
a = {tuple(sorted(f[:2])): f for f in json.load(open(sys.argv[1]))['fails']}
b = {tuple(sorted(f[:2])): f for f in json.load(open(sys.argv[2]))['fails']}
print('pairs', len(a), '->', len(b))
print('new', [b[k] for k in b if k not in a]); print('gone', [a[k] for k in a if k not in b])
print('tighter', [(a[k][2], b[k]) for k in b if k in a and b[k][2] < a[k][2] - 1e-3])
