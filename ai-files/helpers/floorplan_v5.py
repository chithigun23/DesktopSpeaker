"""Tiled floorplan for placement v5. layout(sizes, spec, MG, MT) -> dict(board, cells{n:{u0,v0,+edge keys}}, tiles{n:[u0,v0,u1,v1]}, holes, title).
spec: W, ul, rows [ [item,...] ] (rear row first). item: cell name | {"col": [name|{"hole":[name,corner]}...]} | {"space": w}.
Rows abut (shared edges); free width is shared by the tiles of the row; row height = tallest column; tiles of a column share the extra height.
spec["edge"][cell] = {"rear":[ref, ovh]} etc.; spec["valign"][cell] in t/c/b; spec["title_bottom"] list of cells (title at the bottom of the tile)."""
HOLE = 8.0


def layout_abs(sizes, spec, MG, MT):
    W, H, ul = spec['W'], spec['H'], spec['ul']
    ab = spec['abs']
    T = {n: (sizes[n][0] + 2 * MG - (spec.get('ovh', {}).get(n, 0)), sizes[n][1] + MG + MT) for n in ab if n in sizes}
    tiles, cells, holes = {}, {}, []
    for n, (x, y) in ab.items():
        if n in T:
            w, h = T[n]
            R = [x, y, x + w, y + h]
            right = [ab[m][0] for m in T if m != n and ab[m][0] >= x + w - 0.01 and ab[m][1] < y + h - 0.01 and ab[m][1] + T[m][1] > y + 0.01]
            R[2] = min(right) if right and min(right) - (x + w) <= 10 else (ul + W if W - (x + w) <= 10 and not right else x + w)
            down = [ab[m][1] for m in T if m != n and ab[m][1] >= y + h - 0.01 and ab[m][0] < x + w - 0.01 and ab[m][0] + T[m][0] > x + 0.01]
            R[3] = min(down) if down and min(down) - (y + h) <= 10 else (H if H - (y + h) <= 10 and not down else y + h)
            if R[2] < x + w: R[2] = x + w
            tiles[n] = [ul + R[0], -R[3], ul + R[2], -R[1]]
            cells[n] = dict(u0=ul + x + (w - (sizes[n][0] + 2 * MG - spec.get('ovh', {}).get(n, 0))) / 2 + MG, v0=-(y + (MG if n in spec.get('title_bottom', []) else MT)) - sizes[n][1])
            for k, v in spec.get('edge', {}).get(n, {}).items():
                cells[n][k] = v
        else:
            holes.append([n, ul + x + 4.0, -(y + 4.0)])
    return dict(board=dict(ul=ul, ur=ul + W, vf=-H, vr=0.0), cells=cells, tiles=tiles, holes=holes, title=spec.get('title', [ul + 20, -H + 5]), title_bottom={n: True for n in spec.get('title_bottom', [])})


def layout(sizes, spec, MG=0.9, MT=2.4):
    if 'abs' in spec:
        return layout_abs(sizes, spec, MG, MT)
    W, ul = spec['W'], spec['ul']
    rows = spec['rows']
    tiles, cells, holes = {}, {}, []
    tb = set(spec.get('title_bottom', []))
    edge = spec.get('edge', {})
    valign = spec.get('valign', {})
    t = 0.0                       # distance from the rear edge
    rowinfo = []
    for row in rows:
        items = []
        for it in row:
            if isinstance(it, str): it = {'col': [it]}
            if 'space' in it:
                items.append(dict(kind='space', w=it['space'], h=0, ents=[])); continue
            ents = [e if isinstance(e, str) else e for e in it['col']]
            w = max([sizes[e][0] + 2 * MG if isinstance(e, str) else HOLE for e in ents])
            h = sum([sizes[e][1] + MG + MT if isinstance(e, str) else HOLE for e in ents])
            items.append(dict(kind='col', w=w, h=h, ents=ents))
        fixed = sum(i['w'] for i in items if i['kind'] == 'space')
        ncol = sum(1 for i in items if i['kind'] == 'col')
        slack = W - fixed - sum(i['w'] for i in items if i['kind'] == 'col')
        rh = max(i['h'] for i in items)
        rowinfo.append((items, slack / ncol, rh))
        if slack < -0.01:
            print('ROW TOO WIDE by %.1f: %s' % (-slack, [e for i in items for e in i['ents']]))
    x_h = 0.0
    for (items, extra, rh), row in zip(rowinfo, rows):
        x = ul
        for i in items:
            if i['kind'] == 'space':
                x += i['w']; continue
            cw = i['w'] + extra
            nfix = sum(1 for e in i['ents'] if isinstance(e, str))
            extra_h = (rh - i['h']) / max(nfix, 1)
            y = t
            for e in i['ents']:
                if not isinstance(e, str):
                    nm, corner = e['hole']
                    hu = x + (HOLE / 2 if 'l' in corner else cw - HOLE / 2)
                    hv_t = y + (HOLE / 2 if 't' in corner else HOLE / 2)
                    holes.append([nm, hu, -hv_t]); y += HOLE; continue
                th = sizes[e][1] + MG + MT + extra_h
                tiles[e] = [x, -(y + th), x + cw, -y]       # u0, v0, u1, v1 (v up, rear edge = 0)
                va = valign.get(e, 'c')
                if e in tb:
                    cv1 = -(y + th) + MG + sizes[e][1] + (th - sizes[e][1] - MG - MT) * (0 if va == 'b' else 1 if va == 't' else 0.5)
                    cv0 = cv1 - sizes[e][1]
                else:
                    top = -(y + MT)
                    free = th - MG - MT - sizes[e][1]
                    cv1 = top - free * (0 if va == 't' else 1 if va == 'b' else 0.5)
                    cv0 = cv1 - sizes[e][1]
                cu0 = x + (cw - sizes[e][0]) / 2
                cells[e] = dict(u0=cu0, v0=cv0)
                for k, v in edge.get(e, {}).items():
                    cells[e][k] = v
                y += th
            x += cw
        t += rh
    H = t
    board = dict(ul=ul, ur=ul + W, vf=-H, vr=0.0)
    return dict(board=board, cells=cells, tiles=tiles, holes=holes, title=spec.get('title', [ul + 12, -H + 5]), title_bottom=dict.fromkeys(tb, True))
