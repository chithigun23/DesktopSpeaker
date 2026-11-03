#!/usr/bin/env python3
"""Validate enclosure.glb / pcb.glb for the web viewer and check that they overlay in one frame.

  python -I validate_glb.py SITE_CAD_DIR CAD_OUT_DIR  -> CAD_OUT/work/glb_validation.json (+ printout)
Checks: GLB header/chunks, JSON parse, no extensions, accessor ranges inside buffer views, node names,
world-space bounding boxes (node TRS/matrix applied), PCB board body vs the CAD board, PCB hole walls vs the
standoff axes from meta.json, component bboxes in pcb.glb vs the FreeCAD board-STEP placement (fit.json)."""
import json, struct, sys
import numpy as np

CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
NC = {'SCALAR': 1, 'VEC3': 3, 'VEC2': 2, 'VEC4': 4}


def load(path):
    f = open(path, 'rb').read()
    mg, ver, ln = struct.unpack('<III', f[:12])
    assert mg == 0x46546C67 and ver == 2 and ln == len(f), 'bad header'
    cl, ct = struct.unpack('<II', f[12:20]); assert ct == 0x4E4F534A
    j = json.loads(f[20:20 + cl])
    bl, bt = struct.unpack('<II', f[20 + cl:28 + cl]); assert bt == 0x004E4942
    b = f[28 + cl:28 + cl + bl]
    assert j['buffers'][0]['byteLength'] <= len(b)
    for a in j['accessors']:
        bv = j['bufferViews'][a['bufferView']]
        need = a.get('byteOffset', 0) + a['count'] * np.dtype(CT[a['componentType']]).itemsize * NC[a['type']]
        assert need <= bv['byteLength'] or bv.get('byteStride'), 'accessor overruns view'
        assert bv['byteOffset'] + bv['byteLength'] <= len(b)
    return j, b


def acc(j, b, i):
    a = j['accessors'][i]; bv = j['bufferViews'][a['bufferView']]
    dt = CT[a['componentType']]; n = NC[a['type']]
    st = bv.get('byteStride', 0)
    off = bv['byteOffset'] + a.get('byteOffset', 0)
    if st and st != np.dtype(dt).itemsize * n:
        raw = np.frombuffer(b, np.uint8, st * (a['count'] - 1) + np.dtype(dt).itemsize * n, off)
        return np.lib.stride_tricks.as_strided(raw, (a['count'], np.dtype(dt).itemsize * n), (st, 1)).copy().view(dt).reshape(a['count'], n)
    return np.frombuffer(b, dt, a['count'] * n, off).reshape(a['count'], n)


def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def local(n):
    M = np.eye(4)
    if 'matrix' in n:
        return np.array(n['matrix']).reshape(4, 4).T
    S = np.diag(n.get('scale', [1, 1, 1]) + [1])
    R = np.eye(4); R[:3, :3] = qmat(n.get('rotation', [0, 0, 0, 1]))
    T = np.eye(4); T[:3, 3] = n.get('translation', [0, 0, 0])
    return T @ R @ S


def world_points(j, b):
    """-> {node index: (world matrix)}, per-named-node world vertices (cached per mesh)"""
    out = {}
    def walk(i, M, path):
        n = j['nodes'][i]; W = M @ local(n)
        out[i] = (W, path + [n.get('name', str(i))])
        for c in n.get('children', []):
            walk(c, W, path + [n.get('name', str(i))])
    for r in j['scenes'][j.get('scene', 0)]['nodes']:
        walk(r, np.eye(4), [])
    return out


def node_bbox(j, b, W, i, cache, collect=None):
    """world bbox of node i and its subtree"""
    lo = np.full(3, np.inf); hi = np.full(3, -np.inf)
    def rec(k):
        nonlocal lo, hi
        n = j['nodes'][k]
        if 'mesh' in n:
            if n['mesh'] not in cache:
                cache[n['mesh']] = np.concatenate([acc(j, b, p['attributes']['POSITION']) for p in j['meshes'][n['mesh']]['primitives']]).astype(float)
            P = cache[n['mesh']] @ W[k][0][:3, :3].T + W[k][0][:3, 3]
            lo = np.minimum(lo, P.min(0)); hi = np.maximum(hi, P.max(0))
            if collect is not None:
                collect.append(P)
        for c in n.get('children', []):
            rec(c)
    rec(i)
    return lo, hi


def main(site, cadout):
    res = {}
    E, Eb = load(site + '/enclosure.glb'); Pj, Pb = load(site + '/pcb.glb')
    for nm, j in (('enclosure', E), ('pcb', Pj)):
        res[nm] = dict(extensionsUsed=j.get('extensionsUsed', []), extensionsRequired=j.get('extensionsRequired', []), nodes=len(j['nodes']), meshes=len(j['meshes']),
                       materials=len(j['materials']), accessors=len(j['accessors']),
                       triangles=int(sum(j['accessors'][p['indices']]['count'] // 3 for m in j['meshes'] for p in m['primitives'])))
    meta = json.load(open(cadout + '/work/meta.json')); fit = json.load(open(cadout + '/work/fit.json'))
    WE = world_points(E, Eb); WP = world_points(Pj, Pb)
    ce, cp = {}, {}
    # enclosure top groups
    eb = {}
    for i, (W, path) in WE.items():
        if len(path) == 2:
            lo, hi = node_bbox(E, Eb, WE, i, ce); eb[path[-1]] = [lo.round(2).tolist(), hi.round(2).tolist()]
    lo, hi = node_bbox(E, Eb, WE, E['scenes'][0]['nodes'][0], ce)
    res['enclosure']['bbox_mm'] = [lo.round(2).tolist(), hi.round(2).tolist()]; res['enclosure']['group_bbox_mm'] = eb
    lo, hi = node_bbox(Pj, Pb, WP, Pj['scenes'][0]['nodes'][0], cp)
    res['pcb']['bbox_mm'] = [lo.round(2).tolist(), hi.round(2).tolist()]
    # board body vs CAD board
    bidx = [i for i, (W, p) in WP.items() if p[-1] == 'Board_body'][0]
    pts = []
    lo, hi = node_bbox(Pj, Pb, WP, bidx, cp, pts)
    bp = np.concatenate(pts)
    B = meta['pcb']; Lb = meta['params']
    exp_lo = [B['cx'] + (-61.0), B['bot'], -(B['rear_edge'])]
    exp_hi = [B['cx'] + 66.5, B['top'], -(B['rear_edge'] - Lb['pcb_d'])]
    res['board_body'] = dict(glb_lo=lo.round(3).tolist(), glb_hi=hi.round(3).tolist(), expected_lo=exp_lo, expected_hi=exp_hi,
                             max_err_mm=round(float(max(np.abs(lo - exp_lo).max(), np.abs(hi - exp_hi).max())), 3))
    # hole walls vs standoff axes (CAD site p -> glTF (x, -y))
    holes = []
    stand = {n['name'] for n in E['nodes']}
    for s in meta['sites']:
        if s['kind'] != 'pcb':
            continue
        ax = np.array([s['p'][0], -s['p'][1]])
        d = np.hypot(bp[:, 0] - ax[0], bp[:, 2] - ax[1])
        ring = d[(d < 2.6)]
        # standoff node centre in enclosure.glb
        sn = [i for i, (W, p) in WE.items() if p[-1].startswith('Standoff_') and p[-1].endswith(s['name'].split('_')[-1]) and ('_%s' % s['name'].split('_')[-1]) in p[-1]]
        sc = None
        if sn:
            l2, h2 = node_bbox(E, Eb, WE, sn[0], ce); sc = ((l2 + h2) / 2).round(3).tolist(); stop = round(float(h2[1]), 3)
        holes.append(dict(hole=s['name'], axis_xz=ax.round(3).tolist(), board_vertices_within_2p6=int(len(ring)),
                          hole_wall_radius_min=round(float(ring.min()), 3) if len(ring) else None,
                          standoff_centre=sc, standoff_top_y=stop if sn else None,
                          standoff_centre_err=round(float(np.hypot(sc[0] - ax[0], sc[2] - ax[1])), 3) if sc else None))
    res['holes'] = holes
    # components: pcb.glb node bbox vs FreeCAD placement (fit.json bbox, CAD frame)
    fb = {r['ref']: r['bbox'] for r in fit['rows']}
    comp = []
    for ref in ('J1', 'J2', 'J3', 'SW102', 'U1', 'U3', 'L201', 'C275', 'J4', 'J5', 'J9', 'J11', 'SW100', 'U2', 'U24', 'TP1', 'TP23'):
        idx = [i for i, (W, p) in WP.items() if p[-1] == ref and 'mesh' not in Pj['nodes'][i]]
        if not idx or ref not in fb:
            continue
        lo, hi = node_bbox(Pj, Pb, WP, idx[0], cp)
        q = fb[ref]; elo = np.array([q[0], q[2], -q[4]]); ehi = np.array([q[3], q[5], -q[1]])
        comp.append(dict(ref=ref, max_err_mm=round(float(max(np.abs(lo - elo).max(), np.abs(hi - ehi).max())), 3)))
    res['components_vs_cad'] = comp
    json.dump(res, open(cadout + '/work/glb_validation.json', 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ('holes',)}, indent=1))
    for h in holes:
        print(h)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
