#!/usr/bin/env python3
"""Assemble meta.json and cad_status.json for the website CAD viewer (plain python3, no numpy).

  python3 make_web_meta.py CAD_OUT WEB_OUT BOARD.kicad_pcb
Inputs: CAD_OUT/work/{meta,check,fit,enclosure_nodes,glb_validation}.json, the board (3D model links per footprint),
CAD_OUT/fit_findings.json (hand-written enclosure-fit findings for this board revision; optional).
Outputs: WEB_OUT/meta.json, WEB_OUT/cad_status.json, CAD_OUT/meta.json (copy)."""
import json, os, re, sys, hashlib, datetime, csv

CAD, WEB, BOARD = [a.rstrip('/') for a in sys.argv[1:4]]
W = CAD + '/work/'
m = json.load(open(W + 'meta.json')); chk = json.load(open(W + 'check.json')); fit = json.load(open(W + 'fit.json'))
enc = json.load(open(W + 'enclosure_nodes.json')); val = json.load(open(W + 'glb_validation.json'))
findings = json.load(open(CAD + '/fit_findings.json')) if os.path.exists(CAD + '/fit_findings.json') else {}
batt = json.load(open(W + 'batt.json')) if os.path.exists(W + 'batt.json') else {}      # v15: batt_check.py (pack clearances, mass/CoM, overhang audit)
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
# v13/v14: accuracy per reference from the models-v13 audit (accuracy-table.csv); footprint errors listed separately
ACC = {r['ref']: r for r in csv.DictReader(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/cad/models-v13/accuracy-table.csv'))}
# v14: the four footprint errors found by the models-v13 audit are fixed on RT-14 (checked on the board file: J2/J3 front NPTH x -4.75,
# U1 pad 56 at +4.77, SW100 redrawn from the TE drawing with the actuator tip at the board edge, C275 on CP_Elec_6.3x7.7)
FOOTPRINT_ERRORS = []
FOOTPRINT_FIXES = [
    dict(refs=['J2', 'J3'], footprint='PJ-307', was='front NPTH locating pegs at x -5.75 (1.0 mm off)', now='front NPTH at x -4.75 as the HOOYA drawing', source='datasheets/PJ-307.pdf'),
    dict(refs=['U1'], footprint='BM83SM1-00TA', was='GND pad 56 at local x +1.40 (3.37 mm off)', now='pad 56 at (+4.77, -0.03)', source='DS70005402D p.56 Fig. 8-2'),
    dict(refs=['SW100'], footprint='TE_1977066-1_Tact_RA_SMD', was='DRAFT (pads +-1.50, pegs on the wrong side, no bracket pads; actuator 2.30 mm inside the board edge)',
         now='redrawn from TE rev C1: lands +-1.225 x 0.75, pegs 0.9 on the actuator side, bracket pads; actuator tip at the board edge (CAD: 0.00 mm)', source='TE 1977066-1 rev C1 p.1'),
    dict(refs=['C275'], footprint='CP_Elec_6.3x7.7', was='CP_Elec_8x10 land for a case D8 part', now='CP_Elec_6.3x7.7 land and model', source='Panasonic EEH-ZA case D8'),
]
FPF = {r: e for e in FOOTPRINT_FIXES for r in e['refs']}
FPE = {r: e for e in FOOTPRINT_ERRORS for r in e['refs']}
def acc_of(ref):
    r = ACC.get(ref)
    if r is None:
        return 'unverified', 'not in the audit table'
    v = r['verdict_after']
    if v.startswith('OK'):
        return '<0.5mm', 'dev %s mm (L x W x H vs datasheet %s)' % (r['dev_after'], r['real_LxWxH'])
    return 'unverified', (r['notes'] or v)[:160]
pcb_nodes = []
for ref, d in sorted(models.items()):
    if not d['model']:
        continue
    a, note = acc_of(ref)
    r = ACC.get(ref, {})
    nd = dict(ref=ref, footprint=d['footprint'], model_source='%s (%s)' % (','.join(d['model']), r.get('source_after', 'KiCad library')), accuracy=a, accuracy_note=note,
              lead_check=r.get('lead_check_after'))
    if ref in FPE:
        nd['footprint_error'] = FPE[ref]['error']
    if ref in FPF:
        nd['footprint_fixed'] = 'RT-14: ' + FPF[ref]['now']
    pcb_nodes.append(nd)
cnt = {}
for r in ACC.values():
    k = r['verdict_after'].split(' ')[0]
    cnt[k] = cnt.get(k, 0) + 1
unv = sorted([r for r, x in ACC.items() if x['verdict_after'].startswith('UNVERIFIED')], key=lambda x: (re.sub(r'\d', '', x), int(re.sub(r'\D', '', x) or 0)))
AUDIT = dict(source='ai-files/cad/models-v13/ (accuracy-table.csv, accuracy-table.md, mechanical-accuracy.md, MODELS.md); report ai-files/reports/cad-accuracy-2026-11-02.md',
             footprints=len(ACC), physical_parts=len(ACC) - cnt.get('N/A', 0), not_applicable=cnt.get('N/A', 0),
             within_0p5mm=cnt.get('OK', 0), unverified=cnt.get('UNVERIFIED', 0), unverified_refs=unv,
             unverified_why={'L200': 'XAL7070 KiCad library model; Coilcraft drawing blocked', 'TP23-TP27': 'Keystone 5010-5014: envelope from distributor data, no maker drawing'},
             coverage_pct=round(100.0 * cnt.get('OK', 0) / (len(ACC) - cnt.get('N/A', 0)), 1),
             summary='%d of %d physical board parts have a model within 0.5 mm of the datasheet; %d unverified (%s)' % (cnt.get('OK', 0), len(ACC) - cnt.get('N/A', 0), cnt.get('UNVERIFIED', 0), ', '.join(unv)),
             verified_means='passives at class level (thickness codes from MPN/family datasheets); IC body envelopes vs the maker package drawing (nominal); leads sliced at board level vs pads (0.1 mm)',
             footprint_errors=FOOTPRINT_ERRORS, footprint_fixes_rt14=FOOTPRINT_FIXES,
             footprint_errors_note='v14: the four footprint errors of the v13 audit (J2/J3, U1 pad 56, SW100, C275) are fixed on RT-14; none open.')
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
NCELL = m.get('n_cells', 2)
mass['%d x INR21700-50S (about 69 g each, unverified)' % NCELL] = 69.0 * NCELL
mass['Pack PCM, nickel, wrap, leads (estimate 8 g + 3 g per cell)'] = 8.0 + 3.0 * NCELL
mass['PCB + components (estimate: FR4 1.85 g/cm3 + 30 g parts)'] = P['pcb_w'] * P['pcb_d'] * 1.6 / 1000 * 1.85 + 30.0
hw = sum(v / 1000 * (8.5 if n.startswith('Insert_') else 7.85) for n, v in vol.items() if n.startswith(('Insert_M3', 'Screw_', 'Standoff_', 'Foot_standoff')))
mass['Screws, inserts, spacers, feet (steel/brass, modelled volume)'] = hw
mass['Grilles 0.8 mm (steel, modelled volume)'] = sum(v / 1000 * 7.85 for n, v in vol.items() if n.startswith('Grille_'))
mass = {k: round(v) for k, v in mass.items()}

# ---- v15: battery pack section (owner decision 2026-11-03: 1S4P, ai-files/reports/battery-4p-feasibility-2026-11-03.md)
CR = m.get('cradle', {}); BC = batt.get('clearance', {}); BM = batt.get('mass', {}); OV = batt.get('print_overhang', {})
def bcl(k):
    c = BC.get(k); return c['mm'] if c else None
PACK = dict(
    configuration='1S%dP' % NCELL, cells=NCELL, cell='Samsung INR21700-50S (models-v13 model at datasheet max 21.25 x 70.62)',
    capacity_Ah_nominal=5.0 * NCELL, energy_Wh_nominal=round(5.0 * NCELL * 3.6, 1),
    brick_mm=list(m.get('pack', {}).get('brick_mm') or [86.8, 73.7, 21.7]),
    brick_note='modelled vendor brick incl. 0.25 mm heat-shrink, nickel, fish paper and PCM (CAD v15); feasibility estimate was 86.8 x 73.7 x 21.7; RFQ maximum 87.0 x 75.0 x 23.0 (ai-files/reports/battery-pack-rfq.md)',
    construction=m.get('pack'),
    envelope_mm_measured=batt.get('pack_envelope_mm'), layout=CR.get('layout'), cradle=CR,
    pcm=dict(position='positive (rear) end, wrapped with the cells; the woofer-chamber partition is the rear stop (%s mm gap)' % m.get('pack', {}).get('rear_gap_to_partition'),
             placeholder_mm=[60, 1.6, 18], lead='J5 leads from the PCM top-edge pads through a wrap slit; modelled lead length %s mm (RFQ about 180 mm)' % max([w['length_mm'] for w in m.get('wiring', []) if w['name'].startswith('Wire_J5')] or [batt.get('j5_harness_route_mm')])),
    clearances_mm=dict(pcm_to_partition=bcl('woofer chamber insert (partition)'), j5_wires_to_cells=bcl('J5 wires'), cells_to_nd65=bcl('drivers ND65 (L/R)'),
                       cells_to_driver_screws=bcl('driver screws/inserts'), pack_to_pcb_bottom=bcl('PCB board'), pack_to_pcb_parts=bcl('PCB components'),
                       cells_to_shell_cradle=batt.get('cells_to_shell_mm')),
    mass_estimated=BM,
    print=dict(shell_overhang_mm2=OV.get('shell', {}).get('overhang_area_mm2'), lid_overhang_mm2=OV.get('lid', {}).get('overhang_area_mm2'),
               insert_overhang_mm2=OV.get('woofer_chamber_insert', {}).get('overhang_area_mm2'), supports='none (v14 2P shell baseline 978 mm2; 4P adds two 2.5 mm strap-tunnel ceiling bridges; the strap-channel chamfer and the lid countersinks are exactly 45 deg and counted at the limit)'),
    assumptions=['PCM and cell holder/wrap are placeholders (PCM 60 x 3 x 18 slab; real pack outline from the vendor, RFQ max 87.0 x 75.0 x 23.0)',
                 'Samsung 50S mass 69 g per cell UNVERIFIED (P45B 70 g max per its datasheet); pack overhead 8 + 3 g per cell estimated',
                 'Cells at the 50S maximum size on a 21.7 pitch; one 20 mm hook-and-loop strap (width UNVERIFIED), loop about 330 mm',
                 'The woofer-chamber insert partition is the rear stop; drop loads on it are not analysed',
                 'Wires: typical insulation OD per gauge (UNVERIFIED for the bought wire); routes designed in CAD'],
    sources=['ai-files/reports/battery-4p-feasibility-2026-11-03.md', 'ai-files/cad/v15/work/batt.json', 'ai-files/bom/battery-pack-rfq.md'],
)
PACK_SPEC = [dict(k='Battery pack (CAD)', v='%s, %d x INR21700-50S, %g Ah / %g Wh nominal; brick %s mm; PCM at the rear against the partition' % (
    PACK['configuration'], NCELL, PACK['capacity_Ah_nominal'], PACK['energy_Wh_nominal'], ' x '.join('%g' % v for v in (PACK['brick_mm'] or [])) or 'n/a'))]

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
    version='v15', date=datetime.date.today().isoformat(),
    title='CAD v15 (RT-14 draft, 1S4P pack)',
    description='DesktopSpeaker internal CAD v15: board RT-14 routing draft + models-v13 accurate models; enclosure with the 1S4P battery cradle (owner decision 2026-11-03)',
    spec=PACK_SPEC,
    source=dict(board=os.path.relpath(BOARD, '/home/chithi/Desktop/DesktopSpeaker'), board_sha256=sha, cad_scripts='ai-files/cad/v15/scripts/', models='ai-files/cad/models-v13/3d/ (board models via the project library, enclosure models read directly)',
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
                        content='tracks + zones (outer layers) of the RT-14 routing draft (12 connections still open), same frame; optional layer: load on demand (not counted in the 40 MB budget)'),
        renders=sorted('renders/' + f for f in os.listdir(WEB + '/renders')),
        downloads=sorted('downloads/' + f for f in os.listdir(WEB + '/downloads')) if os.path.isdir(WEB + '/downloads') else []),
    viewer_notes=['Plain glTF 2.0, no extensions (three.js r128 GLTFLoader).', 'Materials are doubleSided so clipped sections show inner faces.',
                  'Explode: add node.userData.explode_mm (mesh nodes in enclosure.glb) to node.position; move the pcb.glb root by [0, 60, 0].',
                  'Per-node provenance is in node extras (userData): model_source, accuracy (<0.5mm = compared with a drawing/standard in the models-v13 audit | estimated = known deviation or placeholder for an unselected part | unverified = no drawing), accuracy_note.',
                  'Soldermask and silkscreen materials are translucent (alpha 0.83 / 0.9, alphaMode BLEND).'],
    groups=groups,
    pcb_group=dict(key='PCB', description='Board RT-14 routing draft (12 unconnected, DRC 0) with the models-v13 corrected library models (J1, J5, J9-J11, SW100, TP1-TP27, U1 offset, U2, U24) and the RT-14 footprint fixes (J2/J3, U1 pad 56, SW100, C275)', explode_mm=[0, 60, 0],
                   bbox_mm=val['pcb']['bbox_mm'], components_with_model=len(pcb_nodes), components_without_model=no_model),
    nodes=[dict(name=n['name'], group=n['group'], sub=n['sub'], color=n['color'], bbox_mm=n['bbox_gl'], explode_mm=n['explode_mm'],
                model_source=n['model_source'], accuracy=n['accuracy'], accuracy_note=n.get('accuracy_note')) for n in enc['nodes']],
    accuracy_audit=AUDIT,
    pcb_nodes=pcb_nodes,
    section_planes=[
        dict(name='x = 0: woofer chamber, PCB stack, knob', normal=[-1, 0, 0], constant=0.0, keeps='x < 0'),
        dict(name='x = -41: left ND65 and battery', normal=[-1, 0, 0], constant=-41.0, keeps='x < -41'),
        dict(name='x = -33.82: encoder shaft and knob dish', normal=[-1, 0, 0], constant=-33.82, keeps='x < -33.82'),
        dict(name='height 75: components above the PCB, connectors at the lid', normal=[0, -1, 0], constant=75.0, keeps='y < 75'),
        dict(name='height 15: battery pack, harness, woofer ring', normal=[0, -1, 0], constant=15.0, keeps='y < 15'),
        dict(name='height 96.5: top wall removed (open top)', normal=[0, -1, 0], constant=96.5, keeps='y < 96.5'),
        dict(name='depth 121.16: knob dish across', normal=[0, 0, 1], constant=121.16, keeps='z > -121.16'),
        dict(name='depth %.2f: woofer axis (square frame, outside bosses)' % P['woof_cy'], normal=[0, 0, 1], constant=round(P['woof_cy'], 2), keeps='z > -%.2f' % P['woof_cy']),
        dict(name='x = %.2f: woofer screws (frame, gasket, insert, outside boss)' % (P['w_hole_sq'] / 2), normal=[-1, 0, 0], constant=round(P['w_hole_sq'] / 2, 3), keeps='x < %.3f' % (P['w_hole_sq'] / 2)),
    ],
    key_dimensions=dict(outer_W_H_D_mm=[P['W'], P['H'], P['D']], depth_note='D includes the 4 mm lid', height_with_feet_mm=P['H'] + 15,
                        wall_mm=P['wall'], lid_mm=P['lid_t'], board_mm=[P['pcb_w'], P['pcb_d'], 1.6], pcb_bottom_z=m['pcb']['bot'],
                        external_volume_L=round(P['W'] * P['H'] * P['D'] / 1e6, 3), internal_cavity_L=round(chk['total_internal'] / 1e6, 3),
                        woofer_chamber_L=dict(gross=round(chk['woof_gross'] / 1e6, 3), net=round(chk['woof_net'] / 1e6, 3), target='0.45-0.60'),
                        main_chamber_L=dict(gross=round(chk['main_gross'] / 1e6, 3), net=round(chk['main_net'] / 1e6, 3), target='>= 0.80'),
                        print_bodies=m['prints'], masses_g_estimated=mass, mass_total_g_estimated=sum(mass.values())),
    interference=inter,
    clearances=chk['clearances'], lid_cutouts=lidc, dish=m['dish'], rocker=m['rocker'], woofer_ring=m['woofer_ring'], woofer_seat=m['woofer_ring'], sw100=m.get('sw100'),
    screw_table=findings.get('screw_table', []), changes_vs_v14=findings.get('changes_vs_v14', []), parameter_changes=findings.get('parameter_changes', []),
    tallest_parts=[dict(ref=r['ref'], top_z=r['top_z'], gap_to_top_wall=r['gap_top_wall']) for r in tall],
    closest_parts_to_enclosure=[dict(ref=r['ref'], nearest=r['nearest'][0][1], mm=r['nearest'][0][0]) for r in near],
    glb_validation=dict(board_body_max_err_mm=val['board_body']['max_err_mm'], holes=[dict(hole=h['hole'], standoff_axis_err_mm=h['standoff_centre_err'],
                        hole_wall_r=h['hole_wall_radius_min']) for h in val['holes']], components_vs_cad=val['components_vs_cad']),
    pack=PACK,
    wiring=dict(note='Cut list from CAD v15: modelled centreline length; cut length = modelled + 8 mm strip/crimp allowance, rounded up to 5 mm. Ends, gauge, colour, bend radius per wire.',
                wires=m.get('wiring', []), clearance=json.load(open(W + 'wires.json')) if os.path.exists(W + 'wires.json') else None,
                screws=dict(csk=m.get('csk'), cup_washer=m.get('cup_washer'), counts=m.get('screws'))),
    fit_findings=findings.get('findings', []),
    assumptions=findings.get('assumptions', []), open_items=findings.get('open_items', []),
    zfix=m['zfix'], skipped_operations=m['skipped'],
)
json.dump(meta, open(WEB + '/meta.json', 'w'), indent=1)
json.dump(meta, open(CAD + '/meta.json', 'w'), indent=1)
status = dict(
    version='v15', title=meta['title'], date=meta['date'], board='RT-14 (routing draft) + models-v13 model links', board_sha256=sha[:16],
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
    pcb_models=dict(with_model=len(pcb_nodes), accuracy_counts={k: sum(1 for n in pcb_nodes if n['accuracy'] == k) for k in ('<0.5mm', 'unverified', 'estimated')}),
    accuracy_audit=dict(physical_parts=AUDIT['physical_parts'], within_0p5mm=AUDIT['within_0p5mm'], unverified=AUDIT['unverified'], unverified_refs=AUDIT['unverified_refs'],
                        coverage_pct=AUDIT['coverage_pct'], footprint_errors=[dict(refs=e['refs'], error=e['error']) for e in FOOTPRINT_ERRORS],
                        footprint_fixes_rt14=[dict(refs=e['refs'], now=e['now']) for e in FOOTPRINT_FIXES]),
    checks=findings.get('checks', []),
    problems=[f['title'] for f in findings.get('findings', []) if f.get('severity') in ('problem', 'decision')],
    open_items=len(meta['open_items']),
    pack=dict(configuration=PACK['configuration'], cells=PACK['cells'], brick_mm=PACK['brick_mm'], pcm=PACK['pcm']['position'],
              tightest_mm=PACK['clearances_mm'], print_overhang_shell_mm2=PACK['print']['shell_overhang_mm2'], supports=PACK['print']['supports']),
)
json.dump(status, open(WEB + '/cad_status.json', 'w'), indent=1)
print(json.dumps(status, indent=1))
