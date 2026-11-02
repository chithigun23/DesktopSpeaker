#!/usr/bin/env python3
"""editlog.py E1.edit.json ... : markdown edit tables (net, layer, coordinates) from edit.py reports."""
import json, sys
f4 = lambda v: '%.4f' % v
for fn in sys.argv[1:]:
    E = json.load(open(fn)); stem = fn.split('/')[-1].replace('.edit.json', '')
    print('\n### %s (%s)\n' % (stem, E.get('plan', '')))
    print('| op | net | layer | w / size | geometry |\n|---|---|---|---|---|')
    for s in E['seg_del']: print('| seg del %s | %s | %s | %s | (%s, %s)-(%s, %s) |' % (s[0][:8], s[1], s[2], s[3], *map(f4, s[4:8])))
    for s in E['seg_set']: print('| seg set %s | %s | %s | %s | (%s, %s)-(%s, %s) -> (%s, %s)-(%s, %s) |' % (s[0][:8], s[1], s[2], s[3], *map(f4, s[4]), *map(f4, s[5])))
    for v in E['via_del']: print('| via del %s | %s | F-B | %s/%s | (%s, %s) |' % (v[0][:8], v[1], v[4], v[5], f4(v[2]), f4(v[3])))
    for v in E['via_set']: print('| via move %s | %s | F-B | - | (%s, %s) -> (%s, %s) |' % (v[0][:8], v[1], *map(f4, v[2]), *map(f4, v[3])))
    for m in E.get('fp_move', []): print('| footprint move %s | - | F | - | (%s, %s) -> %s |' % (m[0], m[1][0], m[1][1], tuple(m[2])))
    for s in E['seg_add']: print('| seg add | %s | %s | %s | (%s, %s)-(%s, %s) |' % (s[2], s[1], s[3], *map(f4, s[4:8])))
    for v in E['via_add']: print('| via add | %s | F-B | %s/%s | (%s, %s) |' % (v[1], v[4], v[5], f4(v[2]), f4(v[3])))
    print('| teardrops removed near edits | | | | %d |' % len(E['td_removed']))
