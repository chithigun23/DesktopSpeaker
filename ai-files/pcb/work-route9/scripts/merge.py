#!/usr/bin/env python3
"""merge.py OUT.json P1.json P2.json ... : concatenate edit.py plans (lists appended, dicts updated; duplicate deletions removed)."""
import json, sys
out = dict(seg_del=[], seg_set={}, seg_add=[], via_del=[], via_set={}, via_add=[], fp_move={}, zone_pts={})
for f in sys.argv[2:]:
    p = json.load(open(f))
    for k, v in p.items():
        if k not in out: out[k] = v; continue
        if isinstance(out[k], list): out[k] += [x for x in v if not (k in ('seg_del', 'via_del') and x in out[k])]
        else: out[k].update(v)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
print('merged', {k: len(v) for k, v in out.items() if hasattr(v, '__len__')})
