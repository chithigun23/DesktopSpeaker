"""Review complete physical pin groups in the isolated charger draft."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ai-files/vendor'))
from sexpdata import load
def k(a):return str(a[0]) if isinstance(a,list) and a else ''
def one(a,n):return next(v for v in a if k(v)==n)
d=load(open(ROOT/'ai-files/candidates/Battery_Charger-candidate.net'))
groups=[]
for net in one(d,'nets'):
 if k(net)=='net':
  groups.append({(str(one(n,'ref')[1]),str(one(n,'pin')[1])) for n in net if k(n)=='node' and not str(one(n,'ref')[1]).startswith('#')})
def pins(*values):return {(s.split('.')[0],s.split('.')[1]) for s in values}
expected={
 'VBUS':pins('U4.2','U4.3','U4.8','U4.9','C100.1','C111.1','C113.1'),
 'PMID':pins('U4.29','C101.1','C108.1','C112.1','C114.1'),
 'REGN':pins('U4.5','C102.1','C109.1','R100.1','R108.1','R110.1','R103.1'),
 'SYS':pins('U4.25','C104.1','C105.1','C107.1'),
 'BAT_INT':pins('U4.22','U4.23','Q103.1','Q103.2','Q103.3','C106.1'),
 'BAT_PACK':pins('Q103.5','Q103.6','Q103.7','Q103.8','Q103.9','SW101.1','R112.1'),
 'PACK_RAW':pins('SW101.2','J5.1'),
 'BATP':pins('U4.18','R112.2'),
 'SDRV':pins('U4.24','Q103.4'),
 'BTST1':pins('U4.4','C103.1'),
 'SW1':pins('U4.28','C103.2','L1.1'),
 'BTST2':pins('U4.19','C110.1'),
 'SW2':pins('U4.26','C110.2','L1.2'),
 'QON':pins('U4.12','SW100.1'),
 'CE':pins('U4.13','Q100.3','R103.2'),
 'SCL':pins('U4.14'),
 'SDA':pins('U4.15'),
 'DP':pins('U4.6'),
 'DM':pins('U4.7'),
 'STAT_NC':pins('U4.1'),
 'TS':pins('U4.16','R100.2','R101.1','J5.2'),
 'ILIM_HIZ':pins('U4.17','R108.2','R109.1','Q101.3'),
 'PROG':pins('U4.20','R102.1'),
 'INT':pins('U4.21','R106.2'),
 'VIO':pins('R106.1'),
 'CLAMP_GATE':pins('Q101.1','Q102.3','R110.2'),
 'SYS_ENABLE':pins('Q102.1','R111.1'),
 'CHG_ENABLE':pins('Q100.1','R107.1'),
}
caps=['C100','C101','C102','C104','C105','C106','C107','C108','C109','C111','C112','C113','C114']
expected['GND']=pins('U4.27','U4.10','U4.11','Q100.2','Q101.2','Q102.2','J5.3','SW100.2','R101.2','R102.2','R107.2','R109.2','R111.2',*(c+'.2' for c in caps))
findings=[]
for name,wanted in expected.items():
 matches=[g for g in groups if g&wanted]
 if len(matches)!=1 or matches[0]!=wanted:
  findings.append({'net':name,'expected':sorted(wanted),'actual_groups':[sorted(g) for g in matches]})
covered={p for g in expected.values() for p in g}
allphysical={p for g in groups for p in g}
uncovered=sorted(allphysical-covered)
missing=sorted(covered-allphysical)
u4coverage={p for r,p in covered if r=='U4'}
assert u4coverage=={str(i) for i in range(1,30)},u4coverage
report={'candidate_only':True,'all_29_U4_pins_reviewed':True,'expected_groups':len(expected),'findings':findings,'uncovered_physical_pins':uncovered,'missing_physical_pins':missing,'physical_connectivity_pass':not findings and not uncovered and not missing,'style_approved':False,'active_integration_approved':False}
(ROOT/'ai-files/reports/bq25792-candidate-full-pin-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
