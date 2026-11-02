"""Inventory every footprint of a board: ref, lib id, position, side, pads, 3D models.
Usage: python3 inventory.py BOARD.kicad_pcb OUT.json"""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse, find, findall, nums

board = parse(open(sys.argv[1]).read())
out = []
for fp in findall(board, 'footprint'):
    lib = fp[1]
    at = nums(find(fp, 'at'))
    x, y = at[0], at[1]
    rot = at[2] if len(at) > 2 else 0.0
    layer = find(fp, 'layer')[1]
    props = {}
    for p in findall(fp, 'property'):
        props[p[1]] = p[2]
    pads = []
    for p in findall(fp, 'pad'):
        pat = nums(find(p, 'at'))
        sz = nums(find(p, 'size'))
        dr = find(p, 'drill')
        drill = None
        if dr:
            drill = [v for v in dr[1:] if not isinstance(v, list)]
        pads.append(dict(num=p[1], type=p[2], shape=p[3], at=pat[:2], rot=pat[2] if len(pat) > 2 else 0.0,
                         size=sz, drill=drill, layers=[v for v in (find(p, 'layers') or [])[1:]]))
    models = []
    for m in findall(fp, 'model'):
        def v(k):
            n = find(m, k)
            return nums(find(n, 'xyz')) if n else None
        hide = 'hide' in m or (find(m, 'hide') is not None)
        models.append(dict(path=m[1], offset=v('offset'), scale=v('scale'), rotate=v('rotate'), hide=hide))
    crt = None
    xs, ys = [], []
    for g in findall(fp, 'fp_rect') + findall(fp, 'fp_line') + findall(fp, 'fp_poly'):
        L = find(g, 'layer')
        if L and L[1].endswith('CrtYd'):
            for k in ('start', 'end'):
                n = find(g, k)
                if n:
                    a = nums(n); xs.append(a[0]); ys.append(a[1])
            pts = find(g, 'pts')
            if pts:
                for xy in findall(pts, 'xy'):
                    a = nums(xy); xs.append(a[0]); ys.append(a[1])
    if xs:
        crt = [min(xs), min(ys), max(xs), max(ys)]
    out.append(dict(ref=props.get('Reference'), value=props.get('Value'), lib=lib, x=x, y=y, rot=rot, layer=layer,
                    mpn=props.get('MPN') or props.get('Manufacturer Part Number') or props.get('MPN ') or '',
                    manufacturer=props.get('Manufacturer', ''), lcsc=props.get('LCSC', props.get('LCSC Part #', '')),
                    props={k: v for k, v in props.items() if k not in ('Reference', 'Value', 'Footprint', 'Datasheet', 'Description')},
                    pads=pads, models=models, courtyard=crt))
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print(len(out), 'footprints')
