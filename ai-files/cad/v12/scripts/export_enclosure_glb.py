"""Enclosure (all non-PCB solids + PCB stand-ins without a KiCad model) -> binary glTF for the web viewer.

Run: CAD_OUT=.../ai-files/cad/v12 WEB_OUT=.../website/desktopSpeaker-site/cad freecadcmd export_enclosure_glb.py
Reads CAD_OUT/work/meta.json + work/brep/*.brep (written by build_speaker_cad.py).
Writes WEB_OUT/enclosure.glb and CAD_OUT/work/enclosure_nodes.json (node list, bbox, explode vectors; merged into meta.json
by make_web_meta.py).

Frame: millimetres, glTF Y up. glTF (x, y, z) = CAD (X, Z, -Y): +x = speaker right, +y = up, +z = toward the front baffle
(CAD Y = 0 is the front outer face, so the front faces +z, the default three.js camera side).
Plain glTF 2.0: no extensions, no compression (three.js r128 GLTFLoader).
"""
import os, json, struct, math
import numpy as np
import Part, MeshPart

OUT = os.environ.get('CAD_OUT', '/home/chithi/Desktop/DesktopSpeaker/ai-files/cad/v12').rstrip('/') + '/'
WEB = os.environ.get('WEB_OUT', '/home/chithi/Desktop/DesktopSpeaker/ai-files/website/desktopSpeaker-site/cad').rstrip('/') + '/'
LIN = float(os.environ.get('GLB_LIN', '0.08'))      # mm
ANG = float(os.environ.get('GLB_ANG', '0.3'))       # rad
os.makedirs(WEB, exist_ok=True)
m = json.load(open(OUT + 'work/meta.json'))

def to_gl(a):          # CAD (X, Y, Z) -> glTF (X, Z, -Y); proper rotation, winding kept
    return np.stack([a[:, 0], a[:, 2], -a[:, 1]], 1)

def cad_vec_to_gl(v):
    return [v[0], v[2], -v[1]]

# ---------------------------------------------------------------- grouping, materials, explode vectors (CAD frame, mm)
GROUPS = [   # key, description, default explode (CAD frame)
    ('Shell', 'Printed main shell: front baffle, walls, driver pads, woofer ring pad, lid bosses, feet bosses, battery cradle, encoder knob dish', (0, 0, 0)),
    ('Lid', 'Printed rear lid 4 mm: USB-C, 2 jacks, SW100, rocker cutouts; gasket groove', (0, 80, 0)),
    ('WooferChamberInsert', 'Printed sealed woofer chamber insert (partition, walls, roof, PCB shelf, PCB screw bosses); bonded into the shell', (0, 0, 25)),
    ('Drivers_ND65', 'Two Dayton Audio ND65-4 full-range drivers (maker STEP)', (0, -40, 0)),
    ('Woofer', 'Tang Band W3-2052SC down-firing woofer (parametric stand-in, no maker drawing)', (0, 0, -70)),
    ('Battery_2P21700', '2P Samsung INR21700-50S pack + PCM board (cradle is printed in the shell)', (0, 0, -30)),
    ('Harness', 'Schematic cable runs: J5 to pack, J11 to woofer through the grommet', (0, 0, 0)),
    ('PCB_StandIns', 'Board parts without a KiCad 3D model (J5, J9-J11, SW100): courtyard-size stand-ins in the PCB frame', (0, 0, 60)),
    ('Hardware', 'Screws, heat-set inserts, hex spacers, feet, rubber discs, lid gasket, grommet', (0, 0, 0)),
    ('Knob_Rocker_Grille', 'Encoder knob stand-in, SW101 rocker stand-in, front and woofer perforated grilles', (0, 0, 0)),
]
GDESC = {k: (d, e) for k, d, e in GROUPS}

def classify(name, group):
    """-> (top group, sub group or None, explode vector CAD frame, material key)"""
    n = name
    if group == 'shell': return 'Shell', None, (0, 0, 0), 'shell'
    if group == 'lid': return 'Lid', None, (0, 80, 0), 'lid'
    if group == 'insert': return 'WooferChamberInsert', None, (0, 0, 25), 'insert'
    if group == 'drivers': return 'Drivers_ND65', None, (0, -40, 0), 'driver'
    if group == 'woofer': return 'Woofer', None, (0, 0, -70), 'driver'
    if group == 'battery': return 'Battery_2P21700', None, (0, 0, -30), 'cell' if 'Cell' in n else 'pcm'
    if group == 'harness': return 'Harness', None, (0, 0, 0), 'harness_red' if 'woofer' in n else 'harness_orange'
    if group == 'pcb_parts': return 'PCB_StandIns', None, (0, 0, 60), 'plunger' if 'plunger' in n else 'standin'
    if group == 'grille':
        return 'Knob_Rocker_Grille', None, ((0, -80, 0) if 'front' in n else (0, 0, -70)), 'grille'
    if n.startswith('Knob'): return 'Knob_Rocker_Grille', None, (0, 0, 40), 'knob'
    if n.startswith('SW101'): return 'Knob_Rocker_Grille', None, (0, 80, 0), 'rocker'
    # hardware
    if n.startswith('Gasket'): return 'Hardware', 'Gaskets_Grommet', (0, 80, 0), 'rubber'
    if n.startswith('Grommet'): return 'Hardware', 'Gaskets_Grommet', (0, 0, 0), 'rubber'
    if n.startswith('Foot_rubber'): return 'Hardware', 'Feet', (0, 0, -25), 'rubber'
    if n.startswith('Foot_'): return 'Hardware', 'Feet', (0, 0, -25), 'steel'
    if n.startswith('Insert_'):
        return 'Hardware', 'Inserts', ((0, -40, 0) if '_Drv' in n else (0, 0, 25) if ('PcbScrew' in n or 'LidScrew_10' in n or 'LidScrew_11' in n) else (0, 0, 0)), 'brass'
    if n.startswith('Standoff_'): return 'Hardware', 'Standoffs', (0, 0, 60), 'steel'
    if n.startswith('Screw_'):
        e = (0, -40, 0) if 'Drv' in n else (0, 0, -70) if 'Woof' in n else (0, 0, 60) if 'Pcb' in n else (0, 80, 0) if 'Lid' in n else (0, 0, 0)
        return 'Hardware', 'Screws', e, 'screw'
    return 'Hardware', 'Other', (0, 0, 0), 'standin'

MATS = {   # name: (rgba, metallic, roughness)
    'shell': ((0.30, 0.32, 0.36, 1), 0.0, 0.75), 'lid': ((0.38, 0.40, 0.45, 1), 0.0, 0.75), 'insert': ((0.52, 0.42, 0.32, 1), 0.0, 0.8),
    'driver': ((0.10, 0.10, 0.11, 1), 0.3, 0.6), 'cell': ((0.22, 0.42, 0.78, 1), 0.1, 0.45), 'pcm': ((0.10, 0.45, 0.20, 1), 0.0, 0.6),
    'harness_red': ((0.75, 0.12, 0.10, 1), 0.0, 0.6), 'harness_orange': ((0.85, 0.50, 0.10, 1), 0.0, 0.6),
    'standin': ((0.92, 0.92, 0.86, 1), 0.0, 0.7), 'plunger': ((0.80, 0.10, 0.10, 1), 0.0, 0.6),
    'grille': ((0.08, 0.08, 0.09, 1), 0.6, 0.5), 'knob': ((0.12, 0.12, 0.13, 1), 0.2, 0.4), 'rocker': ((0.65, 0.10, 0.10, 1), 0.0, 0.5),
    'rubber': ((0.05, 0.05, 0.05, 1), 0.0, 0.95), 'steel': ((0.72, 0.72, 0.75, 1), 1.0, 0.35), 'brass': ((0.85, 0.65, 0.25, 1), 1.0, 0.35),
    'screw': ((0.20, 0.20, 0.22, 1), 0.9, 0.4),
}
MKEYS = list(MATS)

# ---------------------------------------------------------------- tessellation (per B-rep face: smooth within a face, sharp across edges)
def mesh_shape(shape):
    P, N, I = [], [], []
    base = 0
    flips = 0
    for f in shape.Faces:
        try:
            mm = MeshPart.meshFromShape(Shape=f, LinearDeflection=LIN, AngularDeflection=ANG, Relative=False)
        except Exception:
            continue
        pts = np.array([[p.x, p.y, p.z] for p in mm.Points], float)
        if len(pts) == 0 or mm.CountFacets == 0:
            continue
        tri = np.array([fa.PointIndices for fa in mm.Facets], int)
        t3 = pts[tri]
        fn = np.cross(t3[:, 1] - t3[:, 0], t3[:, 2] - t3[:, 0])
        # orientation: compare with the B-rep face normal at the largest triangle centroid
        k = int(np.argmax(np.linalg.norm(fn, axis=1)))
        c = t3[k].mean(0)
        try:
            uv = f.Surface.parameter(App_V(*c))
            nref = f.normalAt(*uv)
            if f.Orientation == 'Reversed':
                pass   # Face.normalAt already accounts for the orientation
            if np.dot(fn[k], [nref.x, nref.y, nref.z]) < 0:
                tri = tri[:, [0, 2, 1]]; fn = -fn; flips += 1
        except Exception:
            pass
        vn = np.zeros_like(pts)
        for j in range(3):
            np.add.at(vn, tri[:, j], fn)
        ln = np.linalg.norm(vn, axis=1); ln[ln == 0] = 1
        vn /= ln[:, None]
        P.append(pts); N.append(vn); I.append(tri + base); base += len(pts)
    if not P:
        return None
    P = np.concatenate(P); N = np.concatenate(N); I = np.concatenate(I)
    # signed volume (outward normals -> positive for closed solids)
    t3 = P[I]
    vol = float(np.einsum('ij,ij->i', t3[:, 0], np.cross(t3[:, 1], t3[:, 2])).sum() / 6.0)
    return P, N, I, vol, flips

from FreeCAD import Vector as App_V

# ---------------------------------------------------------------- build glTF
chunks = []; accessors = []; meshes = []; nodes = []
def add_view(arr, target):
    chunks.append((np.ascontiguousarray(arr).tobytes(), target)); return len(chunks) - 1
def add_acc(arr, ctype, typ, target, mm=False):
    d = dict(bufferView=add_view(arr, target), componentType=ctype, count=int(arr.shape[0]), type=typ)
    if mm:
        d['min'] = [float(x) for x in arr.min(0)]; d['max'] = [float(x) for x in arr.max(0)]
    accessors.append(d); return len(accessors) - 1

materials = [dict(name=k, pbrMetallicRoughness=dict(baseColorFactor=list(v[0]), metallicFactor=v[1], roughnessFactor=v[2]), doubleSided=True) for k, v in MATS.items()]
tree = {}       # top -> sub -> [node idx]
info = []
for o in m['objs']:
    if o['group'] == 'pcb' or (o['group'] == 'pcb_parts' and 'standin' not in o['name'] and 'plunger' not in o['name']):
        continue                     # in pcb.glb (KiCad export with the real models)
    shape = Part.read(OUT + 'work/brep/' + o['file'])
    r = mesh_shape(shape)
    if r is None:
        print('EMPTY', o['name']); continue
    P, N, I, vol, flips = r
    top, sub, ex, mk = classify(o['name'], o['group'])
    Pg, Ng = to_gl(P).astype(np.float32), to_gl(N).astype(np.float32)
    ia = add_acc(I.reshape(-1).astype(np.uint16 if len(P) < 65535 else np.uint32), 5123 if len(P) < 65535 else 5125, 'SCALAR', 34963)
    pa = add_acc(Pg, 5126, 'VEC3', 34962, True); na = add_acc(Ng, 5126, 'VEC3', 34962)
    meshes.append(dict(name=o['name'], primitives=[dict(attributes=dict(POSITION=pa, NORMAL=na), indices=ia, material=MKEYS.index(mk), mode=4)]))
    bbg = [[float(x) for x in Pg.min(0)], [float(x) for x in Pg.max(0)]]
    exg = cad_vec_to_gl(ex)
    nodes.append(dict(name=o['name'], mesh=len(meshes) - 1,
                      extras=dict(group=top, sub=sub, explode_mm=exg, model_source=o.get('model_source'), accuracy=o.get('accuracy'), cad_group=o['group'])))
    tree.setdefault(top, {}).setdefault(sub, []).append(len(nodes) - 1)
    bb = shape.BoundBox
    info.append(dict(name=o['name'], group=top, sub=sub, material=mk, color=list(MATS[mk][0][:3]), explode_mm=exg,
                     bbox_gl=bbg, bbox_cad=[round(bb.XMin, 2), round(bb.YMin, 2), round(bb.ZMin, 2), round(bb.XMax, 2), round(bb.YMax, 2), round(bb.ZMax, 2)],
                     triangles=int(len(I)), mesh_signed_volume_mm3=round(vol, 1), brep_volume_mm3=round(shape.Volume, 1), face_flips=flips,
                     model_source=o.get('model_source'), accuracy=o.get('accuracy')))
    print('%-45s %-20s tris %7d  vol mesh/brep %.3f' % (o['name'], top, len(I), vol / shape.Volume if shape.Volume else 0))
top_nodes = []
order = [g[0] for g in GROUPS]
for top in order:
    if top not in tree: continue
    kids = []
    for sub, idx in tree[top].items():
        if sub is None:
            kids += idx
        else:
            nodes.append(dict(name='%s_%s' % (top, sub), children=idx, extras=dict(group=top, sub=sub))); kids.append(len(nodes) - 1)
    nodes.append(dict(name=top, children=kids, extras=dict(group=top, description=GDESC[top][0], explode_mm=cad_vec_to_gl(GDESC[top][1]))))
    top_nodes.append(len(nodes) - 1)
nodes.append(dict(name='DesktopSpeaker_enclosure', children=top_nodes, extras=dict(units='mm', up='+Y', frame='glTF (x, y, z) = CAD (X, Z, -Y)')))
gltf = dict(asset=dict(version='2.0', generator='DesktopSpeaker export_enclosure_glb.py (FreeCAD %s)' % '.'.join(__import__('FreeCAD').Version()[:3]),
                       extras=dict(units='mm', up='+Y', frame='glTF (x, y, z) = CAD (X, Z, -Y); CAD X right, Y rear, Z up; front baffle faces +z',
                                   tessellation=dict(linear_mm=LIN, angular_rad=ANG))),
            scene=0, scenes=[dict(name='enclosure', nodes=[len(nodes) - 1])], nodes=nodes, meshes=meshes, materials=materials, accessors=accessors)
blob = bytearray(); views = []
for data, target in chunks:
    while len(blob) % 4: blob += b'\0'
    views.append(dict(buffer=0, byteOffset=len(blob), byteLength=len(data), target=target)); blob += data
while len(blob) % 4: blob += b'\0'
gltf['bufferViews'] = views; gltf['buffers'] = [dict(byteLength=len(blob))]
js = json.dumps(gltf, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
with open(WEB + 'enclosure.glb', 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob)))
    f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
    f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)
json.dump(dict(nodes=info, groups=[dict(key=k, description=d, explode_mm=cad_vec_to_gl(e)) for k, d, e in GROUPS if k in tree],
               tessellation=dict(linear_mm=LIN, angular_rad=ANG)), open(OUT + 'work/enclosure_nodes.json', 'w'), indent=1)
print('WROTE enclosure.glb %.2f MB, %d mesh nodes, %d triangles' % (os.path.getsize(WEB + 'enclosure.glb') / 1e6, len(meshes), sum(i['triangles'] for i in info)))
