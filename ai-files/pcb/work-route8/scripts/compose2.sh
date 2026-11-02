#!/bin/sh
# compose2.sh WLOG NLOG OUT : RT-8 phase-A plan = v4 - (E, W, N re-routed jobs) + manual escapes + E/W/N fix logs + Q2 (R110)
cd /home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route8
python3 scripts/planminus.py t/pA2_4.json t/pA2_4.hrlog.json t/_c1.json /AUD_SDA:U3-31 /BT_TX_IND:U3-62 /PD_SINK_EN:U3-63 /BT_RST_N:U3-58 /MCU/ENC_B:U3-49 /BT_FORCE_PWM:U3-54 /BT_UART_TX:U3-55 /CTRL_SCL:U3-60 /PDCTRL_SDA:U3-44 /CODEC_PWR_EN:U3-39 /PDCTRL_SCL:115.35,63.7,F.Cu
python3 - <<'PY'
import json
p=json.load(open('t/_c1.json'))
def poly(net,pts,w=0.25):
    for a,b in zip(pts,pts[1:]): p['seg_add'].append(['F.Cu',net,w,a[0],a[1],b[0],b[1]])
poly('/AUD_SDA',[(133.675,73.25),(135.7,73.25),(136.05,72.9)],0.3); p['via_add'].append(['/AUD_SDA',136.05,72.9,0.5,0.2])
poly('/BT_RST_N',[(122.325,77.25),(121.0,77.25),(120.6,77.65)]); p['via_add'].append(['/BT_RST_N',120.6,77.65,0.5,0.2])
poly('/BT_MFB',[(122.325,76.75),(120.35,76.75),(119.8,77.3)]); p['via_add'].append(['/BT_MFB',119.8,77.3,0.5,0.2])
poly('/BT_TX_IND',[(122.325,79.25),(120.5,79.25),(120.15,79.6)]); p['via_add'].append(['/BT_TX_IND',120.15,79.6,0.5,0.2])
poly('/PD_SINK_EN',[(122.325,79.75),(121.3,79.75),(120.95,80.1)]); p['via_add'].append(['/PD_SINK_EN',120.95,80.1,0.5,0.2])
q=json.load(open('t/planQ2.json'))
for k in ('seg_del','arc_del','via_del','via_del_xy'): p[k]=p.get(k,[])+q.get(k,[])
p['fp_move']=dict(p.get('fp_move',{}),**q.get('fp_move',{}))
p['seg_add']+=q['seg_add']; p['via_add']+=q.get('via_add',[])
json.dump(p,open('t/_c2.json','w'),indent=1)
PY
python3 scripts/planplus.py t/_c2.json $3 t/pLE.hrlog.json $1 $2
