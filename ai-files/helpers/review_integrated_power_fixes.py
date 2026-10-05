from pathlib import Path
import xml.etree.ElementTree as E,json,sys,shutil
sys.path.insert(0,'ai-files/vendor');import sexpdata as sx
old=Path('ai-files/reports/critical-power-current-netlist.xml');new=Path('ai-files/reports/power-fixes-after-cleanup.xml')
ignore={'D6','D7','D8','U13','U16','U17','U18','C130','C131','C132','C180','R180','R181','R182'}
def groups(p):
 out=[]
 for a in E.parse(p).findall('.//nets/net'):
  g=sorted((n.attrib['ref'],n.attrib['pin']) for n in a.findall('node') if not n.attrib['ref'].startswith('#') and n.attrib['ref'] not in ignore and not(n.attrib['ref']=='Q2' and n.attrib['pin'] in ['5','6','7','8']))
  if g:out.append(g)
 return sorted(out)
retained=groups(old)==groups(new)
r=E.parse(new);netsets=[set((n.attrib['ref'],n.attrib['pin']) for n in a.findall('node')) for a in r.findall('.//nets/net')]
def joined(*pairs):return any(set(pairs)<=n for n in netsets)
checks={
 'efuse_input':joined(('Q2','5'),('Q2','6'),('Q2','7'),('Q2','8'),('U18','1'),('U18','2'),('U18','3'),('C180','1'),('R180','1')),
 'efuse_output_charger':joined(('U18','15'),('U18','16'),('U4','1'),('D8','1'),('C100','1'),('R2','1')),
 'ovp_divider':joined(('U18','5'),('R180','2'),('R181','1')),
 'current_limit':joined(('U18','11'),('R182','1')),
 'gate_zener_cathode':joined(('D7','1'),('Q1','1'),('Q2','1')),
 'gate_zener_anode':joined(('D7','2'),('Q1','4'),('Q2','4')),
 'raw_tvs':joined(('D6','4'),('D6','5'),('D6','6'),('U11','24')),
 'gauge_sda':joined(('U5','8'),('U13','1')),
 'gauge_scl':joined(('U5','7'),('U16','1')),
 'gauge_alert':joined(('U5','5'),('U17','1')),
 'gauge_bat_supply':joined(('U5','3'),('U13','5'),('U16','5'),('U17','5'),('C130','1'),('C131','1'),('C132','1')),
 'ground_configuration':joined(('U18','6'),('U18','8'),('U18','9'),('U18','17'),('R181','2'),('R182','2'),('C180','2'),('D8','2'),('U13','3'),('U13','4'),('U16','3'),('U16','4'),('U17','3'),('U17','4'))}
checks['SHDN_intentionally_NC']=any(n=={('U18','7')} for n in netsets)
newparts=['TS5A3167DBVR','TVS2200DRVR','BZT52C12-7-F','SMA6J10A','TPS26600PWPR','PD_R_1206']
models={}
for name in newparts:
 p=Path('DesktopSpeaker-kicad/kicad-library/footprint')/(name+'.kicad_mod');x=sx.loads(p.read_text());paths=[a[1] for a in x if isinstance(a,list) and str(a[0])=='model']
 models[name]={'paths':paths,'files_present':all(Path(a.replace('${KIPRJMOD}','DesktopSpeaker-kicad')).exists() for a in paths),'has_model':bool(paths)}
report={'retained_pin_groups_preserved_excluding_intended_replacement_and_power_split':retained,'checks':checks,'model_links':models,'open_models':['TPS26600PWPR exact PWP0016A thermal-pad geometry'],'qualification_open':['PD transition/overshoot and raw TVS maximum-clamp margin','efuse cable-drop,thermal,inrush/effective-capacitance','gauge powered-off leakage and BAT brownout','final passive MPNs and BOM reconciliation'],'ERC_run':False}
Path('ai-files/reports/integrated-power-fixes-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));assert retained and all(checks.values())
shutil.copy2(new,'ai-files/reports/DesktopSpeaker-netlist.xml')
