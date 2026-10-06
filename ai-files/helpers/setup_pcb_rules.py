#!/usr/bin/env python3
"""Idempotent routing-rule setup: netclasses/patterns/teardrops/minima in DesktopSpeaker.kicad_pro, stackup in .kicad_pcb.
Netlist source: kicad-cli sch export netlist --format kicadxml -> /tmp/n.xml. No routing is created."""
import json, re, sys, fnmatch
ROOT='/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/'
nets=sorted(re.findall(r'<net code="\d+" name="([^"]*)"',open('/tmp/n.xml').read()))
# class -> (track_min_DRC, track_pref, planned clearance (enforced in .kicad_dru for non-pad items; netclass clearance stays 0.2 so pad pitch is not flagged), via_dia, via_drill, patterns)
CL={
'POWER_HI':(0.5,2.0,0.4,0.8,0.4,['/SYS_RAW','/Battery_Charger/BAT_INT','/Fuel_Gauge_Power/BAT_PACK','/Battery_Charger/PACK_RAW','/Battery_Charger/VBUS_PD','/USB_VBUS','/Battery_Charger/PMID']),
'PVDD':(0.5,2.0,0.3,0.8,0.4,['/Amplifiers/PVDD_AMP']),
'SPK_OUT':(0.5,2.0,0.3,0.8,0.4,['Net-(C30[2-7]-Pad1)']),
'SWITCH':(0.4,1.5,0.5,0.6,0.3,['/Battery_Charger/SW1','/Battery_Charger/SW2','Net-(U25-SW)','Net-(U14-L1)','Net-(U14-L2)','Net-(U15-L1)','Net-(U15-L2)','Net-(U6-OUT_*)','Net-(U7-OUT_*)']),
'BOOT':(0.25,0.3,0.3,0.6,0.3,['/Battery_Charger/BTST1','/Battery_Charger/BTST2','Net-(U25-BOOT)','Net-(U6-BST_*)','Net-(U7-BST_*)']),
'PWR_5V':(0.4,1.0,0.25,0.6,0.3,['/5V_LOGIC','/5V_CODEC','/Fuel_Gauge_Power/USB_AUX_5V','/Battery_Charger/REGN']),
'PWR_3V':(0.3,0.5,0.25,0.6,0.3,['/3V3_AUDIO','/3V8_BT','/3V_AO','/USB_PD/LDO_3V3','/USB_PD/LDO_1V5','Net-(U1-SYS_PWR)','Net-(U1-VDD_IO)']),
'PWR_LOCAL':(0.25,0.4,0.25,0.6,0.3,['Net-(U2-VBUS)','Net-(U2-VCC*)','Net-(U6-AVDD)','Net-(U6-GVDD)','Net-(U6-VR_DIG)','Net-(U7-AVDD)','Net-(U7-GVDD)','Net-(U7-VR_DIG)','Net-(U24-AVDD)','Net-(U24-LDO)','Net-(U25-VCC)','Net-(U10-HPVDD)','Net-(U10-HPVSS)','Net-(U10-CPN)','Net-(U10-CPP)','/USB_PD/VIN_LOW']),
'AUDIO':(0.25,0.3,0.3,0.6,0.3,['/AUX_L','/AUX_R','/BT_AUDIO_L','/BT_AUDIO_R','/USB_AUDIO_L','/USB_AUDIO_R','/Headphone_Aux/*','Net-(C20[0-5]-Pad2)','Net-(C23[0-5]-Pad2)','Net-(U10-IN[LR]-)','Net-(U24-VIN[LR][123])','Net-(U24-VREF)','Net-(U2-VOUT[LR])','Net-(U2-VCOM)','Net-(U1-AOHP[LR])','Net-(U8-*)','Net-(U9-*)']),
'I2S_CLK':(0.25,0.25,0.4,0.6,0.3,['/I2S_BCK','/I2S_LRCK','/I2S_SDATA','Net-(U24-BCK)','Net-(U24-LRCK)','Net-(U24-DOUT)','Net-(U24-XI)','Net-(U24-XO)','Net-(U2-XTI)','Net-(U2-XTO)']),
'USB':(0.25,0.25,0.4,0.6,0.3,['/USB_DP','/USB_DN','Net-(U2-D+)','Net-(U2-D-)']),
'I2C':(0.25,0.3,0.3,0.6,0.3,['/AUD_SCL','/AUD_SDA','/CTRL_SCL','/CTRL_SDA','/PDCTRL_SCL','/PDCTRL_SDA']),
'GND':(0.4,0.5,0.2,0.6,0.3,['GND']),
}
# SIGNAL = Default class catch-all (everything else incl. unconnected-*)
pro=json.load(open(ROOT+'DesktopSpeaker.kicad_pro'))
ns=pro['net_settings']
base=[c for c in ns['classes'] if c['name']=='Default'][0]
base.update(track_width=0.25,clearance=0.2,via_diameter=0.6,via_drill=0.3,diff_pair_width=0.25,diff_pair_gap=0.15,diff_pair_via_gap=0.25)
tmpl={k:v for k,v in base.items()}
classes=[base]; pats=[]
for name,(mn,pref,clr,vd,vdr,pl) in CL.items():
    c=dict(tmpl); c.update(name=name,track_width=pref,clearance=0.2,via_diameter=vd,via_drill=vdr,priority=len(classes))
    if name=='USB': c.update(diff_pair_width=0.25,diff_pair_gap=0.15)
    classes.append(c)
    for p in pl: pats.append({'netclass':name,'pattern':p})
pats.append({'netclass':'SIGNAL','pattern':'*'})
sig=dict(tmpl); sig.update(name='SIGNAL',priority=len(classes)); classes.append(sig)
ns['classes']=classes; ns['netclass_patterns']=pats
# verify every net classified
asg={}
for n in nets:
    got='SIGNAL'
    for p in pats[:-1]:
        if fnmatch.fnmatchcase(n,p['pattern']) :
            got=p['netclass']; break
    asg[n]=got
json.dump(asg,open('/tmp/w/net_class.json','w'),indent=0)
d=pro['board']['design_settings']
d['rules'].update(min_clearance=0.1,min_track_width=0.2,min_via_annular_width=0.15,min_hole_to_hole=0.3,min_via_diameter=0.5,min_through_hole_diameter=0.3)
d['track_widths']=[0,0.25,0.3,0.4,0.5,1.0,1.5,2.0,3.0]
d['via_dimensions']=[{'diameter':0,'drill':0},{'diameter':0.6,'drill':0.3},{'diameter':0.8,'drill':0.4}]
d['diff_pair_dimensions']=[{'gap':0,'via_gap':0,'width':0},{'gap':0.15,'via_gap':0.25,'width':0.25}]
d['teardrop_options']=[{'td_onpthpad':True,'td_onroundshapesonly':False,'td_onsmdpad':True,'td_ontrackend':True,'td_onvia':True}]
for t in d['teardrop_parameters']:
    t.update(td_curve_segcount=5,td_length_ratio=0.5,td_maxlen=1.0,td_height_ratio=1.0,td_maxheight=2.0,td_on_pad_in_zone=False,td_allow_use_two_tracks=True)
d['teardrop_parameters']=[t for t in d['teardrop_parameters']]
json.dump(pro,open(ROOT+'DesktopSpeaker.kicad_pro','w'),indent=2)
# stackup
pcb=open(ROOT+'DesktopSpeaker.kicad_pcb').read()
st='''		(stackup
			(layer "F.SilkS" (type "Top Silk Screen"))
			(layer "F.Paste" (type "Top Solder Paste"))
			(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01) (material "Solder Mask") (epsilon_r 3.8) (loss_tangent 0))
			(layer "F.Cu" (type "copper") (thickness 0.035))
			(layer "dielectric 1" (type "prepreg") (thickness 0.2104) (material "7628") (epsilon_r 4.4) (loss_tangent 0.02))
			(layer "In1.Cu" (type "copper") (thickness 0.0152))
			(layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4 core") (epsilon_r 4.6) (loss_tangent 0.02))
			(layer "In2.Cu" (type "copper") (thickness 0.0152))
			(layer "dielectric 3" (type "prepreg") (thickness 0.2104) (material "7628") (epsilon_r 4.4) (loss_tangent 0.02))
			(layer "B.Cu" (type "copper") (thickness 0.035))
			(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01) (material "Solder Mask") (epsilon_r 3.8) (loss_tangent 0))
			(layer "B.Paste" (type "Bottom Solder Paste"))
			(layer "B.SilkS" (type "Bottom Silk Screen"))
			(copper_finish "ENIG")
			(dielectric_constraints no)
		)
'''
if '(stackup' not in pcb:
    pcb=pcb.replace('\t(setup\n','\t(setup\n'+st,1)
    open(ROOT+'DesktopSpeaker.kicad_pcb','w').write(pcb)
from collections import Counter
print(Counter(asg.values()),len(nets))
