#!/usr/bin/env python3
"""One-shot (guarded): repackage all R/C/FB to hand-solder 0402 (0805 for large caps). Run from project root.
Writes ai-files/reports/passive-repackage-map.json (ref -> old/new) used by the BOM helper."""
import re, json, shutil, pathlib, sys
ROOT = pathlib.Path('.')
SCH = sorted((ROOT/'DesktopSpeaker-kicad').glob('*.kicad_sch'))
FPD = ROOT/'DesktopSpeaker-kicad/kicad-library/footprint'; M3 = ROOT/'DesktopSpeaker-kicad/kicad-library/3d'
FPL = pathlib.Path('/home/chithi/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Footprints/x86_64/beta/active/files/footprints')
P3 = next(pathlib.Path('/home/chithi/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Packages3D').rglob('3dmodels')) 
R402 = 'R_0402_1005Metric_Pad0.72x0.64mm_HandSolder'; C402 = 'C_0402_1005Metric_Pad0.74x0.62mm_HandSolder'; C805 = 'C_0805_2012Metric_Pad1.18x1.45mm_HandSolder'
for lib, name, step, sub in [('Resistor_SMD',R402,'R_0402_1005Metric','Resistor_SMD'),('Capacitor_SMD',C402,'C_0402_1005Metric','Capacitor_SMD'),('Capacitor_SMD',C805,'C_0805_2012Metric','Capacitor_SMD')]:
    t = (FPL/(lib+'.pretty')/(name+'.kicad_mod')).read_text()
    t, n = re.subn(r'\$\{KICAD\d*_3DMODEL_DIR\}/[^"]*/([^/"]+\.step)', r'${KIPRJMOD}/kicad-library/3d/\1', t); assert n == 1
    (FPD/(name+'.kicad_mod')).write_text(t)
    shutil.copy(P3/(sub+'.3dshapes')/(step+'.step'), M3/(step+'.step'))
SAM, MUR, YAG, TDK = 'Samsung Electro-Mechanics', 'Murata', 'Yageo', 'TDK'
def cap(m, mpn, lcsc, fp): return dict(fp=fp, mfr=m, mpn=mpn, lcsc=lcsc)
C = {
 '100n': cap(MUR,'GRM155R71H104KE14D','C77020',C402),
 '47n': cap(MUR,'GRM155R71H473KA12D','',C402),
 '10nC0G': cap(MUR,'GRM1555C1H103JA01D','',C402),
 '330pC0G': cap(MUR,'GRM1555C1H331JA01D','',C402),
 '33pC0G': cap(MUR,'GRM1555C1H330JA01D','',C402),
 '22pC0G': cap(MUR,'GRM1555C1H220JA01D','',C402),
 '47pC0G': cap(MUR,'GRM1555C1H470JA01D','',C402),
 '6n8': cap(MUR,'GRM155R71H682KA01D','',C402),
 '0u47': cap(SAM,'CL05B474KO5NNNC','',C402),
 '1u': cap(SAM,'CL05A105KO5NNNC','C29266',C402),
 '2u2s': cap(SAM,'CL05A225KP5NNNC','',C402),
 '4u7': cap(SAM,'CL21A475KAQNNNE','',C805),
 '4u7_50': cap(TDK,'C2012X7R1H475K125AC','',C805),
 '10u50': cap(MUR,'GRM21BR61H106KE43L','',C805),
 '22u25': cap(SAM,'CL21A226MAQNNNE','',C805),
 '1u50': cap(SAM,'CL21B105KBFNNNE','C28323',C805),
 '2u2_805': cap(SAM,'CL21B225KAFNNNE','C19110',C805),
 '10u10': cap(SAM,'CL21B106KPQNNNE','C32635',C805),
 '22u10': cap(MUR,'GRM21BZ71A226ME15L','C907991',C805),
 '0u68': cap(SAM,'CL21B684KBFVPNE','C472832',C805),
}
OLD2NEW = {'GRM155R71H104KE14D':'100n','CL10B104KB8NNNC':'100n','CC0603KRX7R9BB473':'47n','GRM1885C1H103JA01D':'10nC0G','CL10C331JB8NNNC':'330pC0G',
 'CL10C330JB8NNNC':'33pC0G','CL10C220JB8NNNC':'22pC0G','CL10C470JB8NNNC':'47pC0G','CL10B682KB8NNNC':'6n8','CL10B474KA8NNNC':'0u47',
 'LMK107B7105KA-T':'1u','CL10A105KB8NNNC':'1u','CL10A475KO8NNNC':'4u7','CL31B475KBHNNNE':'4u7','CL32B106KBJNNNE':'10u50','CL32B226KAJNNNE':'22u25',
 'CL21B105KBFNNNE':'1u','CL21B225KAFNNNE':'2u2s','CL21B106KPQNNNE':'10u10','GRM21BZ71A226ME15L':'22u10','CL21B684KBFVPNE':'0u68'}
BYREF = {'C2':'4u7_50','C5':'4u7_50','C184':'1u50','C270':'1u50','C265':'2u2_805'}
def res(v):
    v = v.replace(' 1%','').replace(' DNP','').replace('R DNP','R')
    if v=='0R': pass
    m = {'0R':'070RL','2.2':'072R2L','22':'0722RL','33':'0733RL','100':'07100RL','100R':'07100RL','1k':'071KL','1.5k':'071K5L','2.2k':'072K2L','4.7k':'074K7L',
     '5.23k':'075K23L','9.1k':'079K1L','10k':'0710KL','30.1k':'0730K1L','47k':'0747KL','56k':'0756KL','78.7k':'0778K7L','82k':'0782KL','91k':'0791KL',
     '100k':'07100KL','150k':'07150KL','180k':'07180KL','200k':'07200KL','301k':'07301KL','499k':'07499KL','604k':'07604KL','1M':'071ML'}[v]
    lc = {'07100KL':'C60491','0710KL':'C60490','071K5L':'C114759'}.get(m,'')
    return dict(fp=R402, mfr=YAG, mpn='RC0402FR-'+m, lcsc=lc)
def prop(line, name):
    m = re.search(r'\(property "%s" "([^"]*)"' % re.escape(name), line); return m.group(1) if m else None
def setp(line, name, val):
    if prop(line, name) is not None:
        return re.sub(r'(\(property "%s" )"[^"]*"' % re.escape(name), lambda m: m.group(1)+'"'+val+'"', line, count=1)
    m = re.search(r'\(property "Footprint" "[^"]*" \(at ([^)]*)\)', line); at = m.group(1)
    ins = ' (property "%s" "%s" (at %s) (hide yes) (effects (font (size 1 1))))' % (name, val, at)
    i = m.start(); d = 0
    while True:
        c = line[i]; d += (c == '(') - (c == ')'); i += 1
        if d == 0: break
    return line[:i] + ins + line[i:]
mp = {}; seen = set()
for f in SCH:
    out = []
    for line in re.split(r'(?=\(symbol \(lib_id)', f.read_text()):
        if line.startswith('(symbol (lib_id') and '"power:' not in line[:40]:
            ref = prop(line, 'Reference')
            if ref and (re.fullmatch(r'[RC]\d+', ref) or ref == 'FB200'):
                fp = prop(line, 'Footprint'); old = prop(line, 'MPN'); val = prop(line, 'Value')
                if fp and 'CP_Elec' not in fp:
                    if ref == 'FB200':
                        new = dict(fp=R402, mfr=MUR, mpn='BLM15AG601SN1D', lcsc='')
                        line = line.replace('"Value" "BLM18AG601SN1D"', '"Value" "BLM15AG601SN1D"')
                    elif ref in BYREF: new = C[BYREF[ref]]
                    elif ref[0] == 'R': new = res(val)
                    else: new = C[OLD2NEW[old]]
                    if ref in ('C122','C123','C124','C125'): line = line.replace('"1uF X7R 10V"','"1uF X5R 16V"')
                    line = setp(line, 'Footprint', 'DesktopSpeaker:'+new['fp'])
                    line = setp(line, 'MPN', new['mpn']); line = setp(line, 'Manufacturer', new['mfr'])
                    line = setp(line, 'LCSC', new['lcsc'])
                    if prop(line, 'LCSC Part') is not None: line = setp(line, 'LCSC Part', new['lcsc'])
                    mp[ref] = dict(old_fp=fp.split(':')[1], old_mpn=old, value=val, **new); seen.add(ref)
        out.append(line)
    f.write_text(''.join(out))
json.dump(mp, open('ai-files/reports/passive-repackage-map.json','w'), indent=1)
print(len(mp), 'passives updated')
