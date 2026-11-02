#!/usr/bin/env python3
"""Assemble meta.json and cad_status.json for the website CAD viewer (plain python3, no numpy).

  python3 make_web_meta.py CAD_OUT WEB_OUT BOARD.kicad_pcb
Inputs: CAD_OUT/work/{meta,check,fit,enclosure_nodes,glb_validation}.json, the board (3D model links per footprint),
CAD_OUT/fit_findings.json (hand-written enclosure-fit findings for this board revision; optional).
Outputs: WEB_OUT/meta.json, WEB_OUT/cad_status.json, CAD_OUT/meta.json (copy)."""
import json, os, re, sys, hashlib, datetime

CAD, WEB, BOARD = [a.rstrip('/') for a in sys.argv[1:4]]
W = CAD + '/work/'
m = json.load(open(W + 'meta.json')); chk = json.load(open(W + 'check.json')); fit = json.load(open(W + 'fit.json'))
enc = json.load(open(W + 'enclosure_nodes.json')); val = json.load(open(W + 'glb_validation.json'))
findings = json.load(open(CAD + '/fit_findings.json')) if os.path.exists(CAD + '/fit_findings.json') else {}
P = m['params']
sha = hashlib.sha256(open(BOARD, 'rb').read()).hexdigest()

# ---- 3D model link per footprint (pcb.glb component nodes are named by reference)
txt = open(BOARD).read()
models = {}
for blk in re.split(r'\n\t\(footprint ', txt)[1:]:
    ref = re.search(r'\(property "Reference" "([^"]+)"', blk)
    if not ref:
        continue
    fp = blk.split('"')[1]
    mod = re.findall(r'\(model "([^"]+)"', blk)
    models[ref.group(1)] = dict(footprint=fp, model=[os.path.basename(x) for x in mod])
pcb_nodes = []
for ref, d in sorted(models.items()):
    if not d['model']:
        continue
    pcb_nodes.append(dict(ref=ref, footprint=d['footprint'], model_source='KiCad library STEP %s' % ','.join(d['model']), accuracy='unverified'))
no_model = sorted(r for r, d in models.items() if not d['model'] and not re.match(r'^(HA?\d+|TP\d+|G\d+|LOGO|REF\*\*)', r))

# ---- masses (estimated): printed bodies PETG 1.27 g/cm3 at 100 % infill, metal parts from modelled volume; drivers/woofer/cells from maker data
dens = dict(shell=1.27, lid=1.27, insert=1.27)
mass = {}
vol = {o['name']: o['vol'] for o in m['objs']}
grp = {o['name']: o['group'] for o in m['objs']}
mass['Shell (PETG, 100 % infill)'] = vol['Shell_Box'] / 1000 * 1.27
mass['Lid (PETG)'] = vol['Lid_rear'] / 1000 * 1.27
mass['Woofer chamber insert (PETG)'] = vol['Insert_woofer_chamber'] / 1000 * 1.27
mass['ND65-4 x2 (Dayton spec 0.18 kg each)'] = 360.0
mass['W3-2052SC (Parts Express 0.25 kg)'] = 250.0
mass['2 x INR21700-50S (about 69 g each, unverified)'] = 138.0
mass['PCB + components (estimate: FR4 1.85 g/cm3 + 30 g parts)'] = P['pcb_w'] * P['pcb_d'] * 1.6 / 1000 * 1.85 + 30.0
hw = sum(v / 1000 * (8.5 if n.startswith('Insert_') else 7.85) for n, v in vol.items() if n.startswith(('Insert_M3', 'Screw_', 'Standoff_', 'Foot_standoff')))
mass['Screws, inserts, spacers, feet (steel/brass, modelled volume)'] = hw
mass['Grilles 0.8 mm (steel, modelled volume)'] = sum(v / 1000 * 7.85 for n, v in vol.items() if n.startswith('Grille_'))
mass = {k: round(v) for k, v in mass.items()}

groups = []
for g in enc['groups']:
    nn = [n for n in enc['nodes'] if n['group'] == g['key']]
    lo = [min(n['bbox_gl'][0][i] for n in nn) for i in range(3)]; hi = [max(n['bbox_gl'][1][i] for n in nn) for i in range(3)]
    groups.append(dict(key=g['key'], description=g['description'], explode_mm=g['explode_mm'], nodes=[n['name'] for n in nn],
                       bbox_mm=[[round(x, 2) for x in lo], [round(x, 2) for x in hi]], color=nn[0]['color'] if nn else None))
lidc = chk['lid_cutouts']
inter = dict(solids=len(m['objs']), threshold_mm3=0.5, unintended=len(chk['overlaps']), intended=len(chk['intended']),
             unintended_pairs=[dict(a=a, b=b, mm3=v) for a, b, v, _ in chk['overlaps']],
             intended_by_reason={})
for a, b, v, why in chk['intended']:
    inter['intended_by_reason'][why] = inter['intended_by_reason'].get(why, 0) + 1
pt = m['pcb']['top']
tall = sorted(fit['rows'], key=lambda r: r['gap_top_wall'])[:10]
near = sorted([r for r in fit['rows'] if r['nearest']], key=lambda r: r['nearest'][0][0])
near = [r for r in near if not r['nearest'][0][1].startswith('Knob')][:12]

meta = dict(
    version='v12', date=datetime.date.today().isoformat(),
    title='DesktopSpeaker internal CAD v12 (board RT-3, placement R10)',
    source=dict(board=os.path.relpath(BOARD, '/home/chithi/Desktop/DesktopSpeaker'), board_sha256=sha, cad_scripts='ai-files/cad/v12/scripts/',
                freecad='1.0.0', kicad='10.0.7 (AppImage)'),
    units='mm', up_axis='+Y',
    frame=dict(gltf_from_cad='glTF (x, y, z) = CAD (X, Z, -Y)', cad='X right (long side), Y depth (0 = front outer face, + = rear), Z up (0 = outer bottom of the box)',
               front='+z in glTF (front baffle at z = 0, rear lid outer face at z = -206.6)', ground='feet bottoms at y = -15, box bottom at y = 0'),
    files=dict(
        enclosure=dict(file='enclosure.glb', bytes=os.path.getsize(WEB + '/enclosure.glb'), units='mm', transform=None,
                       triangles=val['enclosure']['triangles'], tessellation=enc['tessellation']),
        pcb=dict(file='pcb.glb', bytes=os.path.getsize(WEB + '/pcb.glb'), units='mm (root node PCB_<board> carries scale 1000 on the KiCad metre data)',
                 transform=dict(node='PCB_' + os.path.basename(BOARD)[:-10], scale=1000, translation=[m['pcb']['cx'], m['pcb']['bot'], -m['pcb']['cy']], note='already applied in the file: load both files unchanged and they overlay'),
                 triangles=val['pcb']['triangles'], content='kicad-cli pcb export glb --subst-models --include-pads --include-soldermask --include-silkscreen; components by reference designator',
                 layer_nodes=['Board_body', 'Pads_and_holes', 'Soldermask_F', 'Soldermask_B', 'Silkscreen_F', 'Silkscreen_B']),
        pcb_copper=dict(file='pcb_copper.glb', bytes=os.path.getsize(WEB + '/pcb_copper.glb'), optional=True,
                        content='tracks + zones (outer layers) of the partially routed RT-3 board, same frame; optional layer: load on demand (not counted in the 40 MB budget)'),
        renders=sorted('renders/' + f for f in os.listdir(WEB + '/renders')),
        downloads=sorted('downloads/' + f for f in os.listdir(WEB + '/downloads')) if os.path.isdir(WEB + '/downloads') else []),
    viewer_notes=['Plain glTF 2.0, no extensions (three.js r128 GLTFLoader).', 'Materials are doubleSided so clipped sections show inner faces.',
                  'Explode: add node.userData.explode_mm (mesh nodes in enclosure.glb) to node.position; move the pcb.glb root by [0, 60, 0].',
                  'Per-node provenance is in node extras (userData): model_source, accuracy (unverified | <0.5mm | estimated).',
                  'Soldermask and silkscreen materials are translucent (alpha 0.83 / 0.9, alphaMode BLEND).'],
    groups=groups,
    pcb_group=dict(key='PCB', description='Board RT-3 (placement R10, partial routing) with KiCad library STEP models', explode_mm=[0, 60, 0],
                   bbox_mm=val['pcb']['bbox_mm'], components_with_model=len(pcb_nodes), components_without_model=no_model),
    nodes=[dict(name=n['name'], group=n['group'], sub=n['sub'], color=n['color'], bbox_mm=n['bbox_gl'], explode_mm=n['explode_mm'],
                model_source=n['model_source'], accuracy=n['accuracy']) for n in enc['nodes']],
    pcb_nodes=pcb_nodes,
    section_planes=[
        dict(name='x = 0: woofer chamber, PCB stack, knob', normal=[-1, 0, 0], constant=0.0, keeps='x < 0'),
        dict(name='x = -41: left ND65 and battery', normal=[-1, 0, 0], constant=-41.0, keeps='x < -41'),
        dict(name='x = -33.82: encoder shaft and knob dish', normal=[-1, 0, 0], constant=-33.82, keeps='x < -33.82'),
        dict(name='height 75: components above the PCB, connectors at the lid', normal=[0, -1, 0], constant=75.0, keeps='y < 75'),
        dict(name='height 15: battery pack, harness, woofer ring', normal=[0, -1, 0], constant=15.0, keeps='y < 15'),
        dict(name='height 96.5: top wall removed (open top)', normal=[0, -1, 0], constant=96.5, keeps='y < 96.5'),
        dict(name='depth 121.16: knob dish across', normal=[0, 0, 1], constant=121.16, keeps='z > -121.16'),
    ],
    key_dimensions=dict(outer_W_H_D_mm=[P['W'], P['H'], P['D']], depth_note='D includes the 4 mm lid', height_with_feet_mm=P['H'] + 15,
                        wall_mm=P['wall'], lid_mm=P['lid_t'], board_mm=[P['pcb_w'], P['pcb_d'], 1.6], pcb_bottom_z=m['pcb']['bot'],
                        external_volume_L=round(P['W'] * P['H'] * P['D'] / 1e6, 3), internal_cavity_L=round(chk['total_internal'] / 1e6, 3),
                        woofer_chamber_L=dict(gross=round(chk['woof_gross'] / 1e6, 3), net=round(chk['woof_net'] / 1e6, 3), target='0.45-0.60'),
                        main_chamber_L=dict(gross=round(chk['main_gross'] / 1e6, 3), net=round(chk['main_net'] / 1e6, 3), target='>= 0.80'),
                        print_bodies=m['prints'], masses_g_estimated=mass, mass_total_g_estimated=sum(mass.values())),
    interference=inter,
    clearances=chk['clearances'], lid_cutouts=lidc, dish=m['dish'], rocker=m['rocker'], woofer_ring=m['woofer_ring'],
    tallest_parts=[dict(ref=r['ref'], top_z=r['top_z'], gap_to_top_wall=r['gap_top_wall']) for r in tall],
    closest_parts_to_enclosure=[dict(ref=r['ref'], nearest=r['nearest'][0][1], mm=r['nearest'][0][0]) for r in near],
    glb_validation=dict(board_body_max_err_mm=val['board_body']['max_err_mm'], holes=[dict(hole=h['hole'], standoff_axis_err_mm=h['standoff_centre_err'],
                        hole_wall_r=h['hole_wall_radius_min']) for h in val['holes']], components_vs_cad=val['components_vs_cad']),
    fit_findings=findings.get('findings', []),
    assumptions=findings.get('assumptions', []), open_items=findings.get('open_items', []),
    zfix=m['zfix'], skipped_operations=m['skipped'],
)
json.dump(meta, open(WEB + '/meta.json', 'w'), indent=1)
json.dump(meta, open(CAD + '/meta.json', 'w'), indent=1)
status = dict(
    version='v12', date=meta['date'], board='RT-3 (placement R10)', board_sha256=sha[:16],
    verdict=findings.get('verdict', ''),
    solids=len(m['objs']), unintended_overlaps=inter['unintended'], intended_overlaps=inter['intended'],
    woofer_net_L=meta['key_dimensions']['woofer_chamber_L']['net'], main_net_L=meta['key_dimensions']['main_chamber_L']['net'],
    outer_mm=[P['W'], P['H'], P['D']], mass_total_g_estimated=meta['key_dimensions']['mass_total_g_estimated'],
    lid_cutouts={c['ref']: dict(radial_margin_mm=c['radial_margin'], ok=c['ok']) for c in lidc},
    dish=dict(axis_x=m['dish']['cx'], axis_y=m['dish']['cy'], hole_radial_clearance_mm=round(P['dish_hole'] / 2 - 3.0, 2), exposed_shaft_mm=m['dish']['exposed_shaft']),
    min_part_to_enclosure_mm=near[0]['nearest'][0][0] if near else None, min_part_to_enclosure_ref=near[0]['ref'] if near else None,
    tallest_part_except_SW102_shaft=dict(ref=tall[1]['ref'], gap_to_top_wall_mm=tall[1]['gap_top_wall']) if len(tall) > 1 else None,
    pcb_overlay=dict(board_body_err_mm=val['board_body']['max_err_mm'], max_hole_to_standoff_err_mm=max(h['standoff_centre_err'] for h in val['holes'])),
    glb_bytes=dict(enclosure=meta['files']['enclosure']['bytes'], pcb=meta['files']['pcb']['bytes'], pcb_copper_optional=meta['files']['pcb_copper']['bytes']),
    triangles=dict(enclosure=val['enclosure']['triangles'], pcb=val['pcb']['triangles']),
    accuracy_counts={k: sum(1 for n in meta['nodes'] if n['accuracy'] == k) for k in ('<0.5mm', 'unverified', 'estimated')},
    pcb_models=dict(with_model=len(pcb_nodes), accuracy='unverified (v13 audit pending)'),
    problems=[f['title'] for f in findings.get('findings', []) if f.get('severity') in ('problem', 'decision')],
    open_items=len(meta['open_items']),
)
json.dump(status, open(WEB + '/cad_status.json', 'w'), indent=1)
print(json.dumps(status, indent=1))
