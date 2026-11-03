#!/usr/bin/env python3
"""Repack a KiCad `pcb export glb` file for the web viewer (plain three.js GLTFLoader, no extensions).

  python glb_repack.py IN.glb OUT.glb --scale 1000 --translate X Y Z --root-name NAME [--names names.json]

* merges all primitives of a mesh that share a material into one primitive (KiCad writes one primitive per
  B-rep face: about 120k accessors and an 18 MB JSON chunk for this board),
* uint16 indices where possible, drops unused data,
* wraps the scene in one root node with the given scale/translation (KiCad: metres, Y up, gltf z = -board y),
* renames the anonymous top-level copper/mask/silk nodes from their material colour if --names is given.
Needs numpy (scratch venv)."""
import json, struct, sys, argparse
import numpy as np

CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def read_glb(path):
    f = open(path, 'rb').read()
    assert f[:4] == b'glTF'
    cl = struct.unpack('<I', f[12:16])[0]
    j = json.loads(f[20:20 + cl])
    off = 20 + cl
    bl = struct.unpack('<I', f[off:off + 4])[0]
    binc = f[off + 8:off + 8 + bl]
    return j, binc


def accessor(j, binc, i):
    a = j['accessors'][i]
    bv = j['bufferViews'][a['bufferView']]
    dt = np.dtype(CT[a['componentType']])
    n = NC[a['type']]
    start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', 0) or dt.itemsize * n
    if stride == dt.itemsize * n:
        arr = np.frombuffer(binc, dtype=dt, count=a['count'] * n, offset=start).reshape(a['count'], n)
    else:
        raw = np.frombuffer(binc, dtype=np.uint8, count=stride * (a['count'] - 1) + dt.itemsize * n, offset=start)
        arr = np.lib.stride_tricks.as_strided(raw, shape=(a['count'], dt.itemsize * n), strides=(stride, 1)).copy().view(dt).reshape(a['count'], n)
    return arr


def write_glb(path, j, chunks):
    """chunks: list of (bytes, target or None); builds bufferViews in order"""
    blob = bytearray()
    j['bufferViews'] = []
    for data, target in chunks:
        while len(blob) % 4:
            blob += b'\0'
        bv = dict(buffer=0, byteOffset=len(blob), byteLength=len(data))
        if target:
            bv['target'] = target
        j['bufferViews'].append(bv)
        blob += data
    while len(blob) % 4:
        blob += b'\0'
    j['buffers'] = [dict(byteLength=len(blob))]
    js = json.dumps(j, separators=(',', ':')).encode()
    js += b' ' * ((4 - len(js) % 4) % 4)
    total = 12 + 8 + len(js) + 8 + len(blob)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, total))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)
    return total


def auto_name(j):
    """KiCad leaves the board body, pads, copper, mask and silk nodes unnamed ('=>[0:1:1:n]'): name them by
    material colour (green = mask, white translucent = silk, gold = copper, grey = pads, other = board) and side (y sign)."""
    nodes = j['nodes']
    used = {}
    tops = []
    for r in j['scenes'][j.get('scene', 0)]['nodes']:
        tops += [r] + nodes[r].get('children', [])          # scene roots and their direct children only (not component sub-nodes)
    for n in [nodes[i] for i in tops]:
        nm = n.get('name', '')
        if not nm.startswith('=>') or 'mesh' not in n and not n.get('children'):
            continue
        ms = [n['mesh']] if 'mesh' in n else [nodes[c]['mesh'] for c in n.get('children', []) if 'mesh' in nodes[c]]
        if not ms:
            continue
        prims = [p for mi in ms for p in j['meshes'][mi]['primitives']]
        col = j['materials'][prims[0]['material']]['pbrMetallicRoughness'].get('baseColorFactor', [1, 1, 1, 1]) if 'material' in prims[0] else [1, 1, 1, 1]
        ymin = min(j['accessors'][p['attributes']['POSITION']]['min'][1] for p in prims)
        ymax = max(j['accessors'][p['attributes']['POSITION']]['max'][1] for p in prims)
        side = 'F' if ymin > 0.0008 else 'B' if ymax < 0.0008 else 'FB'
        r, g, b = col[:3]
        if col[3] < 0.95 and g > r and g > b:
            k = 'Soldermask_' + side
        elif col[3] < 0.95 and min(r, g, b) > 0.8:
            k = 'Silkscreen_' + side
        elif r > 0.6 and b < 0.15:
            k = 'Copper_' + side
        elif abs(r - g) < 0.05 and abs(g - b) < 0.05 and side == 'FB' and ymax - ymin > 0.0015:
            k = 'Pads_and_holes'
        elif side == 'FB':
            k = 'Board_body'
        else:
            continue
        used[k] = used.get(k, 0) + 1
        n['name'] = k if used[k] == 1 else '%s_%d' % (k, used[k])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inp'); ap.add_argument('out')
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--translate', type=float, nargs=3, default=[0, 0, 0])
    ap.add_argument('--root-name', default='PCB')
    ap.add_argument('--names', default=None, help='json {node index or name: new name}')
    ap.add_argument('--auto-names', action='store_true', help='name anonymous KiCad layer nodes from material colour and height')
    a = ap.parse_args()
    j, binc = read_glb(a.inp)
    chunks, acc = [], []

    def add_acc(arr, ctype, typ, target, minmax=False):
        arr = np.ascontiguousarray(arr)
        chunks.append((arr.tobytes(), target))
        d = dict(bufferView=len(chunks) - 1, componentType=ctype, count=int(arr.shape[0]), type=typ)
        if minmax:
            d['min'] = [float(x) for x in arr.min(0)]; d['max'] = [float(x) for x in arr.max(0)]
        acc.append(d)
        return len(acc) - 1

    new_meshes = []
    nprim_in = 0
    for m in j['meshes']:
        groups = {}
        for p in m['primitives']:
            nprim_in += 1
            assert p.get('mode', 4) == 4, 'only triangle lists'
            groups.setdefault(p.get('material', -1), []).append(p)
        prims = []
        for mat, ps in groups.items():
            P, N, I, base = [], [], [], 0
            for p in ps:
                pos = accessor(j, binc, p['attributes']['POSITION'])
                nor = accessor(j, binc, p['attributes']['NORMAL']) if 'NORMAL' in p['attributes'] else None
                idx = accessor(j, binc, p['indices']).reshape(-1).astype(np.uint32) if 'indices' in p else np.arange(len(pos), dtype=np.uint32)
                P.append(pos.astype(np.float32)); I.append(idx + base); base += len(pos)
                N.append(nor.astype(np.float32) if nor is not None else np.zeros_like(pos, dtype=np.float32))
            P = np.concatenate(P); N = np.concatenate(N); I = np.concatenate(I)
            attrs = dict(POSITION=add_acc(P, 5126, 'VEC3', 34962, True), NORMAL=add_acc(N, 5126, 'VEC3', 34962))
            if base < 65535:
                ii = add_acc(I.astype(np.uint16), 5123, 'SCALAR', 34963)
            else:
                ii = add_acc(I, 5125, 'SCALAR', 34963)
            pr = dict(attributes=attrs, indices=ii, mode=4)
            if mat >= 0:
                pr['material'] = mat
            prims.append(pr)
        nm = dict(primitives=prims)
        if 'name' in m:
            nm['name'] = m['name']
        new_meshes.append(nm)
    j['meshes'] = new_meshes
    j['accessors'] = acc
    names = json.load(open(a.names)) if a.names else {}
    for i, n in enumerate(j['nodes']):
        k = names.get(str(i)) or names.get(n.get('name', ''))
        if k:
            n['name'] = k
    if a.auto_names:
        auto_name(j)
    # root transform
    sc = j.get('scene', 0)
    roots = j['scenes'][sc]['nodes']
    j['nodes'].append(dict(name=a.root_name, children=list(roots), scale=[a.scale] * 3, translation=list(a.translate)))
    j['scenes'][sc]['nodes'] = [len(j['nodes']) - 1]
    j['scene'] = sc
    j.setdefault('asset', {})['extras'] = dict(j['asset'].get('extras', {}), repacked_by='glb_repack.py', root_scale=a.scale, root_translation=a.translate)
    tot = write_glb(a.out, j, chunks)
    print('primitives %d -> %d, accessors %d, size %.2f MB' % (nprim_in, sum(len(m['primitives']) for m in new_meshes), len(acc), tot / 1e6))


if __name__ == '__main__':
    main()
