"""Record physical connectivity review for the auxiliary mux milestone."""
from pathlib import Path
import xml.etree.ElementTree as E
import json
ROOT=Path(__file__).resolve().parents[2]
REPORTS=ROOT/'ai-files/reports'
def groups(p):
 return {frozenset((a.attrib['ref'],a.attrib['pin']) for a in n.findall('node')) for n in E.parse(p).findall('.//nets/net')}
before=groups(REPORTS/'before-5-20v-integration.xml')
after=groups(REPORTS/'usb-aux-logic-integrated.xml')
added={'U20','C124','C125','R124','R125'}
changed={('U12','1'),('U12','3'),('C122','1')}
def retained(gs):
 return {frozenset(v for v in g if v[0] not in added and v not in changed) for g in gs}-{frozenset()}
assert retained(after)==retained(before)
def net(pin):return next(g for g in after if pin in g)
assert net(('U20','3'))==frozenset({('U20','3'),('U20','5'),('C124','1'),('R124','1'),('C5','1'),('U19','1'),('U11','24')})
assert ('U4','15') in net(('U20','6')) and ('U19','1') not in net(('U20','6'))
assert net(('U20','2'))==frozenset({('U20','2'),('U20','7'),('C122','1'),('U12','1'),('U12','3')})
assert net(('U20','4'))==frozenset({('U20','4'),('R124','2'),('R125','1')})
assert len({net(p) for p in [('U20','3'),('U20','6'),('U20','2'),('U20','4'),('U12','5'),('U19','8')]})==6
report={'retained_physical_pin_groups_match':True,'intended_U12_input_change':['U12.1','U12.3','C122.1'],
 'aux_sys_output_ao_raw_isolation':True,'mux_physical_stack_correct':[2,7],'active_pd_range':'5/9 V only',
 'erc':{s['path']:len(s['violations']) for s in json.load(open(REPORTS/'usb-aux-logic-erc.json'))['sheets']},
 'runtime_hardware_qualification_pending':True}
(REPORTS/'usb-aux-logic-integration.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
