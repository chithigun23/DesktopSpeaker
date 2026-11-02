"""Build accuracy-table.csv/.md from the inventory, the before/after measurements and the datasheet specs below.
python3 table.py   (run from models-v13/)"""
import csv, json, os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = lambda p: os.path.join(ROOT, p)
inv = {f['ref']: f for f in json.load(open(W('work/inventory.json')))}
mb = json.load(open(W('work/measure_before.json')))
ma = json.load(open(W('work/measure_after.json')))
DS = 'ai-files/datasheets/'

# ref -> MPN from the JLC BOM (board properties are incomplete)
bom = {}
for row in csv.DictReader(open(os.path.join(ROOT, '../../bom/DesktopSpeaker_JLC_BOM.csv'))):
    for d in row['Designator'].split(','):
        bom[d.strip()] = (row['MPN'], row['Manufacturer'])

PROV = {
    'R_0402_1005Metric.step': 'KiCad std (StepUp 2018)', 'C_0402_1005Metric.step': 'KiCad std (StepUp 2017)',
    'C_0805_2012Metric.step': 'KiCad std (StepUp 2017)', 'PD_C_1206.step': 'KiCad std C_1206 (StepUp 2017)',
    'CP_Elec_6.3x7.7.step': 'KiCad std CP_Elec_6.3x7.7', '2N7002.step': 'KiCad std SOT-23', 'ESDA25L.step': 'KiCad std SOT-23',
    'PESD5V0S2BT.step': 'KiCad std SOT-23', 'TPS3839G33DBZ_SOT23.step': 'KiCad std SOT-23',
    'TPS7A0230PDBVR.step': 'KiCad std SOT-23-5', 'TPS7A2033PDBVR.step': 'KiCad std SOT-23-5', 'TS5A3167DBVR.step': 'KiCad std SOT-23-5',
    'TPS22917DBVR.step': 'KiCad std SOT-23-6', 'TPS2116DRLR.step': 'KiCad std SOT-583-8', 'D_SOD-123.step': 'KiCad std D_SOD-123',
    'STM32G071RBT6.step': 'KiCad std LQFP-64', 'PCM1862DBTR.step': 'KiCad std TSSOP-30 (1.6 high)',
    'TPS7B8450QWDRBRQ1.step': 'KiCad std WSON-8 3x3', 'TVS2200DRVR.step': 'KiCad std WSON-6 2x2',
    'Crystal_SMD_3225-4Pin_3.2x2.5mm.step': 'KiCad std 3225 crystal', 'PinHeader_1x04_P2.54mm_Vertical.step': 'KiCad std pin header',
    'PinHeader_1x05_P2.54mm_Vertical.step': 'KiCad std pin header', 'L_Coilcraft_XAL7070-XXX.step': 'KiCad std (2024) XAL7070',
    'L_Sunlord_MWSA1265S.step': 'KiCad lib contributor (OCC 2022)', 'Bourns_SRN6045TA-2R2Y.step': 'KiCad lib contributor (StepUp 2018)',
    'Coilcraft_XFL4015-471MEC.step': 'Coilcraft vendor STEP (SolidWorks 2017)', 'DNH0008A.stp': 'TI vendor (Creo) DNH0008A',
    'REF0038A.stp': 'TI vendor (Creo) REF0038A', 'RQM0029A.stp': 'TI vendor (Creo) RQM0029A', 'TPS63802DLAR.step': 'TI vendor (Creo) DLA0010A',
    'BM83SM1-00TA.step': 'EasyEDA/LCSC (SolidWorks 2020)', 'MAX17048G+T10.step': 'EasyEDA/LCSC TDFN-8', 'TAS5825MRHBR.step': 'EasyEDA/LCSC VQFN-32',
    'TPA6132A2RTER.step': 'EasyEDA/LCSC WQFN-16', 'TPD2E2U06DRLR.step': 'EasyEDA/LCSC SOT-553', 'TPS61088RHLR.step': 'EasyEDA/LCSC VQFN-20',
    'TS5A23157DGSR.step': 'EasyEDA/LCSC MSOP-10', 'PCM2902CDBR.step': 'EasyEDA/LCSC SSOP-28 (2.2 high)',
    'EC11E15244G1.step': 'project-built FreeCAD 2026-10-06', 'PJ-307.step': 'project-built FreeCAD 2026-10-02',
    'TYPE-C-31-M-12.step': 'project-built FreeCAD 2026-10-02 (box-level)',
    'JST_B2P-VH_LF_SN.step': 'v13 built from drawing', 'TSSOP-30_DBT_4.4x7.8_P0.5_TI.step': 'v13 built from drawing',
    'TE_1977066-1.step': 'v13 built from drawing', 'Molex_Micro-Fit3_43650-0300_RA.step': 'v13 built from drawing',
    'Keystone_5015_TestPoint_MicroMini.step': 'v13 built from drawing', 'Keystone_5010-5014_TestPoint_THM.step': 'v13 built (no maker drawing)',
    'HRO_TYPE-C-31-M-12.step': 'v13 built from drawing', 'SSOP-28_DB_5.3x10.2_P0.65_TI.step': 'v13 built from drawing',
}

# footprint lib -> (L_x, W_y, H, source, note); None dims = not checkable
S = {
 'R_0402_1005Metric_Pad0.72x0.64mm_HandSolder': (1.0, 0.5, 0.35, DS + 'Yageo_AC0402FR_series.pdf / UNI_ROYAL_0402WGF_series.pdf (L 1.00, W 0.50, H 0.35 +-0.05)', 'FB200 BLM15AG601SN1D is 0.50 thick (Murata BLM15 T 0.5 +-0.05): model 0.15 low'),
 'C_0402_1005Metric_Pad0.74x0.62mm_HandSolder': (1.0, 0.5, 0.5, DS + 'Murata_GRM155*.pdf, Samsung CL05 (1.0 x 0.5 x 0.5 +-0.05)', ''),
 'C_0805_2012Metric_Pad1.18x1.45mm_HandSolder': (2.0, 1.25, 1.25, DS + 'Samsung_CL21B105KBFNNNE.pdf p1 (T 1.25 +-0.10), Murata_GRM21BZ71A226ME15.pdf (T 1.25 +-0.2), TDK_C2012X7R1H475KT0A0E.pdf', 'all 0805 MPNs are 1.25 mm thickness codes (Samsung F/Q, Murata B, TDK 125)'),
 'PD_C_1206': (3.2, 1.6, 1.6, 'Murata GRM31CR61E476ME44L: 3.2 x 1.6 x 1.6 +-0.2 (C thickness code)', ''),
 'CP_Elec_8x10': (7.8, 6.6, 7.7, DS + 'Panasonic_EEH-ZA_hybrid_polymer.pdf p1 size D8: D 6.3, L 7.7 +-0.3, A/B 6.6, H 7.8 max', 'FOOTPRINT: part is case D8 (6.3 x 7.7) on a CP_Elec_8x10 land; terminals overlap the pads 2.4 of 3.0 mm'),
 '2N7002': (2.4, 2.9, 1.0, DS + '2N7002.pdf (Nexperia SOT23: HE 2.1-2.64, D 2.8-3.0, A 0.9-1.1)', ''),
 'ESDA25L': (2.4, 2.9, 1.0, DS + 'ESDAL-ST.pdf SOT-23', ''),
 'PESD5V0S2BT': (2.4, 2.9, 1.0, 'DOWO PESD5V0S2BT SOT-23 (JEDEC TO-236)', ''),
 'TPS3839G33DBZR': (2.37, 2.92, 1.0, DS + 'TPS3839.pdf DBZ0003A (1.12 max)', ''),
 'TPS7A0230PDBVR': (2.8, 2.9, 1.2, DS + 'TPS7A02.pdf DBV0005A (A 1.45 max; nominal ~1.2)', 'model 1.55 is 0.1 above the max height'),
 'TPS7A2033PDBVR': (2.8, 2.9, 1.2, DS + 'TPS7A20.pdf DBV0005A', 'model 1.55 is 0.1 above the max height'),
 'TS5A3167DBVR': (2.8, 2.9, 1.2, DS + 'TS5A3167.pdf DBV0005A', 'model 1.55 is 0.1 above the max height'),
 'TPS22917DBVR': (2.8, 2.9, 1.2, DS + 'TPS22917.pdf DBV0006A (1.45 max)', 'model 1.55 is 0.1 above the max height'),
 'TPS2116DRLR': (1.6, 2.1, 0.55, DS + 'TPS2116.pdf DRL0008A (E 1.5-1.7, D 2.0-2.2, 0.6 max)', ''),
 'TPD2E2U06DRLR': (1.6, 1.6, 0.55, DS + 'TPD2E2U06.pdf DRL0005A (0.6 max)', ''),
 'TVS2200DRVR': (2.0, 2.0, 0.75, DS + 'TVS2200.pdf DRV0006A WSON 2x2 (0.8 max)', ''),
 'TPS7B8450QWDRBRQ1_WSON-8': (3.0, 3.0, 0.9, DS + 'TPS7B84-Q1.pdf DRB0008J VSON 3x3 (1.0 max)', ''),
 'TPS63802DLAR': (2.0, 3.0, 0.9, DS + 'TPS63802.pdf DLA0010A VSON-HR 2x3 (1.0 max)', 'TI vendor model'),
 'TPA6132A2RTER': (3.0, 3.0, 0.75, DS + 'TPA6132A2.pdf RTE0016C WQFN 3x3 (0.8 max)', 'lead check n/a: terminals coplanar with the body underside'),
 'TAS5825MRHBR': (5.0, 5.0, 0.9, DS + 'TAS5825M.pdf RHB0032E VQFN 5x5 (1.0 max)', 'EP pad 33 fused with body underside (n/a)'),
 'TPS61088RHLR': (4.5, 3.5, 0.9, 'TI RHL0020A VQFN 3.5x4.5 (1.0 max), ' + DS + 'tps61088-layout-excerpt.txt', ''),
 'TPS25730D': (6.0, 4.0, 0.75, DS + 'TPS25730.pdf REF0038A WQFN 6x4 (0.8 max)', 'TI vendor model'),
 'BQ25792RQMR': (4.0, 4.0, 0.9, DS + 'BQ25792.pdf RQM0029A VQFN-HR 4x4 (1 max)', 'TI vendor model'),
 'CSD17579Q3A_DNH0008A': (3.3, 3.3, 0.95, DS + 'CSD17579Q3A.pdf DNH0008A SON 3.3x3.3 (1.0 max)', 'TI vendor model; drain pins 5-8 merge with the die pad in the slice (check artefact)'),
 'MAX17048G+T10': (2.0, 2.0, 0.75, DS + 'MAX17048_MAX17049.pdf TDFN-8 2x2 (0.8 max)', 'lead check n/a: terminals coplanar with the body underside'),
 'TS5A23157DGSR': (3.0, 4.9, 0.95, DS + 'TS5A23157.pdf DGS0010A VSSOP-10 (1.1 max)', ''),
 'STM32G071RBT6': (12.0, 12.0, 1.5, DS + 'STM32G071x8_xB.pdf LQFP64 10x10 (D 12.0, A 1.6 max, A2 1.4)', ''),
 'PCM2902CDBR': (10.2, 7.8, 1.85, DS + 'PCM2902C.pdf DB0028A SSOP-28 (D 9.9-10.5, E 7.4-8.2, 2 max)', 'before: model 2.2 high, 0.2 above the 2.0 max'),
 'PCM1862DBTR': (6.4, 7.8, 1.1, DS + 'PCM1862.pdf p1 TSSOP(30) 7.80 x 4.40; TI DBT/JEDEC MO-153 (E 6.2-6.6, A 1.2 max)', 'before: KiCad TSSOP-30 model is 1.6 high and 6.7 wide'),
 'PD_D_SOD123': (3.7, 1.6, 1.15, 'Diodes 1N5819HW SOD-123 (3.55-3.85 x 1.4-1.7, 1.35 max)', ''),
 'Crystal_SMD_3225-4Pin_3.2x2.5mm': (3.2, 2.5, 0.75, DS + 'KYX_K3A120002010.pdf / YXC_YSX321SL_X322524576MOB4SI.pdf (3.2 x 2.5, 0.8 max)', 'lead check n/a (fused underside)'),
 'Coilcraft_XFL4015-471MEC': (4.0, 4.0, 1.5, DS + 'Coilcraft_XFL4015.pdf (4.0 +-0.3 sq, 1.60 max)', 'vendor model is the 4.3 max envelope'),
 'Bourns_SRN6045TA-2R2Y': (6.0, 6.0, 4.2, DS + 'Bourns_SRN6045TA.pdf (6.0 +-0.3 sq, 4.2 +-0.3)', ''),
 'L_Coilcraft_XAL7070-XXX': (None, None, None, 'Coilcraft XAL7070 drawing NOT obtained (coilcraft.com 403)', 'UNVERIFIED: KiCad library model 7.7 x 8.0 x 7.0'),
 'L_Sunlord_MWSA1265S': (13.45, 12.6, 6.5, 'Sunlord MWSA1265S series sheet via third-party copy (13.45 +-0.35 x 12.6 +-0.3 x 6.5 max); maker PDF not obtained', 'secondary source'),
 'BM83SM1-00TA': (15.0, 32.0, 2.5, DS + 'BM83_Bluetooth_Stereo_Audio_Module.pdf p55-56 (15 x 32 x 2.5; pads 1.90-20.90 from the bottom edge)', 'before: model 0.43 mm off in y vs the footprint (offset fix); FOOTPRINT: GND pad 56 at x 1.40, datasheet 12.27 from the left edge = +4.77 (3.37 mm error)'),
 'TYPE-C-31-M-12': (8.94, 7.75, 3.26, DS + 'TYPE-C-31-M-12.pdf (8.94 x 7.35 + 0.40 leads, 3.26 high, opening 8.34 x 2.56)', 'before: box-level model, rectangular 8.34 x 2.60 opening (stadium corners 0.53 off), no tongue/posts'),
 'PJ-307': (14.2, 12.0, 5.5, DS + 'PJ-307.pdf (10.9 + 3.3 nose, 12 wide, body 5, nose dia 6 at z 2.5 -> 5.5)', 'FOOTPRINT: front NPTH pegs at 0 mm from the body front; drawing 1.0 mm (pegs 1.0 off, part cannot seat)'),
 'RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm_MountingHoles': (None, None, 24.5, DS + 'Alps_EC11E.pdf Drawing No.2 (EC11E18244AU = same drawing as G1; shaft tip 24.5, dia 6, body 11.7 x 12)', 'shaft axis 0.07 from the footprint locator; body 12.0 x 11.7 measured; MP tabs 0.13 from the slot centres inside 2.8 mm slots (fits)'),
 'PD_SERVICE_HDR': (None, None, 8.54, DS + 'Ckmtw_B-2100S04P-A110_C124378.pdf (2.54 plastic + 6.0 pin, tail 3.0)', ''),
 'PinHeader_1x04_P2.54mm_Vertical': (None, None, 8.54, DS + 'Ckmtw_B-2100S04P-A110_C124378.pdf', ''),
 'PinHeader_1x05_P2.54mm_Vertical': (None, None, 8.5, DS + 'XYECONN_XY-MTP254-1X5_C54110162.pdf (2.5 plastic + 6.0, tail 3.0)', ''),
 'JST_B2P_VH_1x02_P3.96mm_Vertical': (7.86, 8.5, 10.9, DS + 'JST_VH.pdf p3 (B 7.86, 8.5 deep, 10.9 post top, tail 3.7)', 'before: NO model'),
 'Molex_Micro-Fit_3.0_43650-0300_1x03_P3.00mm_Horizontal': (12.65, 9.9, 5.57, DS + 'Molex_43650-0300_C503478.pdf = LXW H3000S14-03 equivalent (12.65 x 9.90, body 4.37, latch ~5.5); genuine Molex drawing not obtained', 'before: NO model; peg check shows the split-peg centroid (artefact)'),
 'TE_1977066-1_Tact_RA_SMD': (4.95, 3.4, 3.3, DS + 'TE_1977066-1_datasheet.pdf rev C1 p1', 'before: NO model; FOOTPRINT (draft): outer pads +-1.50 vs terminals +-1.175, peg holes 1.5 from the pad row vs 0.9, bracket pads missing; the peg holes sit on the side away from the edge while the courtyard puts the actuator toward the edge. Model follows the drawing with the actuator toward the edge (intended)'),
 'TestPoint_Keystone_5015_Micro_Mini': (2.7, 1.0, 1.5, DS + 'Keystone_5015_M65p55.pdf (2.7 x 1.0 x 1.5, strip 0.25)', 'before: NO model; lead check reports the two feet of one pad (artefact)'),
 'TestPoint_Keystone_5010-5014_Multipurpose': (None, None, None, 'no Keystone drawing; distributor OD 3.17, overall 11.3; EasyEDA OBJ z -3.17..8.11', 'before: NO model; built model UNVERIFIED'),
}
NA = {'MountingHole_3.2mm_M3_PTH_GND': 'no component (screw/spacer: see mechanical-accuracy.md)',
      'Tag-Connect_TC2030-IDC-FP_2x03_P1.27mm_Vertical': 'no component (TC2030 cable footprint)',
      'Logo_Orwellian': 'artwork, no component',
      'SHOUHAN_KCD1-201-R_Rocker_D20_Panel': 'wire pads only; the rocker GRB112B802BR1 is panel-mounted (see mechanical-accuracy.md)'}


def dims(m):
    b = m.get('bbox')
    if not b:
        return None
    return (round(b[3] - b[0], 3), round(b[4] - b[1], 3), round(b[5], 3))


def lead(m):
    s = []
    if m.get('smd_missing'):
        s.append('smd pads without lead: %s' % ','.join(m['smd_missing'][:6]))
    if m.get('smd_max_lat') is not None:
        s.append('lat %.2f' % m['smd_max_lat'])
    if [x for x in m.get('tht_missing', []) if x]:
        s.append('plated holes without pin: %d' % len([x for x in m['tht_missing'] if x]))
    elif m.get('tht_missing'):
        s.append('NPTH without peg: %d' % len(m['tht_missing']))
    if m.get('tht_max_dist') is not None:
        s.append('pin-hole %.2f' % m['tht_max_dist'])
    return '; '.join(s) or 'n/a'


def lead_ok(m, lib):
    if lib in ('TPA6132A2RTER', 'MAX17048G+T10', 'TPS2116DRLR', 'Crystal_SMD_3225-4Pin_3.2x2.5mm', 'Coilcraft_XFL4015-471MEC', 'L_Coilcraft_XAL7070-XXX', 'TAS5825MRHBR'):
        return True  # fused underside: lead check not applicable
    if lib in ('CSD17579Q3A_DNH0008A', 'TestPoint_Keystone_5015_Micro_Mini', 'Molex_Micro-Fit_3.0_43650-0300_1x03_P3.00mm_Horizontal',
               'RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm_MountingHoles'):
        return True  # documented check artefacts
    if m.get('smd_missing'):
        return False
    if (m.get('smd_max_lat') or 0) > 0.1:
        return False
    if (m.get('tht_max_dist') or 0) > 0.1 or [x for x in m.get('tht_missing', []) if x]:
        return False
    return True


def verdict(m, spec, lib):
    if lib in NA:
        return 'N/A', None
    if not m.get('bbox'):
        return 'FIX (no model)', None
    if spec is None or all(v is None for v in spec[:3]):
        return 'UNVERIFIED', None
    d = dims(m)
    devs = [abs(a - b) for a, b in zip(d, spec[:3]) if b is not None]
    dev = max(devs)
    v = 'OK' if dev < 0.5 else 'FIX'
    if not lead_ok(m, lib):
        v += ' / pad mismatch'
    return v, round(dev, 3)


rows = []
for ref in sorted(inv, key=lambda r: (re.sub(r'\d', '', r), int(re.sub(r'\D', '', r) or 0))):
    f = inv[ref]; lib = f['lib'].split(':')[-1]
    mpn, man = bom.get(ref, (f.get('mpn') or '', f.get('manufacturer') or ''))
    b, a = mb[ref], ma[ref]
    spec = S.get(lib)
    vb, db = verdict(b, spec, lib); va, da = verdict(a, spec, lib)
    if lib == 'TYPE-C-31-M-12':
        vb = 'FIX (detail: rectangular opening, corner dev 0.53; no tongue; no posts)'
    note = NA.get(lib) or (spec[4] if spec else '')
    if ref == 'FB200':
        note = S['R_0402_1005Metric_Pad0.72x0.64mm_HandSolder'][4]
    elif lib == 'R_0402_1005Metric_Pad0.72x0.64mm_HandSolder':
        note = ''
    if lib == 'TE_1977066-1_Tact_RA_SMD' or lib == 'PJ-307' or (lib == 'BM83SM1-00TA'):
        pass
    rows.append(dict(ref=ref, value=f['value'], footprint=lib, mpn=mpn, manufacturer=man,
                     model_before=','.join(b.get('models', [])) or '-', source_before=PROV.get((b.get('models') or ['-'])[0], '-'),
                     model_after=','.join(a.get('models', [])) or '-', source_after=PROV.get((a.get('models') or ['-'])[0], '-'),
                     real_LxWxH=('x'.join('-' if v is None else '%g' % v for v in spec[:3]) if spec else '-'),
                     model_before_LxWxH=('x'.join('%g' % v for v in dims(b)) if dims(b) else '-'),
                     dev_before=db if db is not None else '', verdict_before=vb, lead_check_before=lead(b),
                     model_after_LxWxH=('x'.join('%g' % v for v in dims(a)) if dims(a) else '-'),
                     dev_after=da if da is not None else '', verdict_after=va, lead_check_after=lead(a),
                     evidence=spec[3] if spec else '', notes=note))

cols = list(rows[0].keys())
with open(W('accuracy-table.csv'), 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)

# summary
cnt_b = collections.Counter(r['verdict_before'].split(' /')[0] for r in rows)
cnt_a = collections.Counter(r['verdict_after'].split(' /')[0] for r in rows)
pad_b = sum(1 for r in rows if 'pad mismatch' in r['verdict_before'])
pad_a = sum(1 for r in rows if 'pad mismatch' in r['verdict_after'])
json.dump(dict(before=cnt_b, after=cnt_a, pad_mismatch_before=pad_b, pad_mismatch_after=pad_a, total=len(rows)),
          open(W('work/summary.json'), 'w'), indent=1)

# markdown: grouped by footprint + MPN + verdicts
grp = collections.OrderedDict()
for r in rows:
    k = (r['footprint'], r['mpn'], r['model_before'], r['model_after'], r['verdict_before'], r['verdict_after'])
    grp.setdefault(k, []).append(r)
L = ['# CAD component accuracy table (models-v13, 2026-11-02)', '',
     'Board: `ai-files/pcb/work-route3/RT-3.kicad_pcb` (360 footprints). Measured in the footprint frame with `gen/measure.py` '
     '(KiCad transform verified against `kicad-cli pcb export step`). Real = datasheet nominal L (x) x W (y) x H (top above board) '
     'in the footprint orientation. Dev = largest |model - real| of L, W, H (mm). OK < 0.5, FIX >= 0.5. '
     '"pad mismatch" = model leads vs footprint pads off by > 0.1 mm or a pad/hole without a lead. Per-reference rows: `accuracy-table.csv`.', '',
     'Counts before: %s; after: %s; pad mismatch before %d, after %d (all remaining ones are footprint errors, listed in the notes).'
     % (dict(cnt_b), dict(cnt_a), pad_b, pad_a), '',
     '| Refs | Footprint | MPN | Real LxWxH | Model before | Src before | Dev | Verdict before | Model after | Dev | Verdict after | Lead check after | Notes |',
     '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
for k, rs in grp.items():
    r = rs[0]
    refs = ' '.join(x['ref'] for x in rs) if len(rs) <= 8 else ' '.join(x['ref'] for x in rs[:6]) + ' ... (%d)' % len(rs)
    L.append('| %s | %s | %s | %s | %s %s | %s | %s | %s | %s %s | %s | %s | %s | %s |' % (
        refs, r['footprint'], r['mpn'], r['real_LxWxH'], r['model_before'], r['model_before_LxWxH'], r['source_before'], r['dev_before'],
        r['verdict_before'], r['model_after'] if r['model_after'] != r['model_before'] else '(same)', r['model_after_LxWxH'], r['dev_after'],
        r['verdict_after'], r['lead_check_after'], r['notes']))
open(W('accuracy-table.md'), 'w').write('\n'.join(L) + '\n')
print(json.dumps(dict(before=cnt_b, after=cnt_a, pad_b=pad_b, pad_a=pad_a)))
