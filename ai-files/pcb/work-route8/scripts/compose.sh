#!/bin/sh
# compose.sh WLOG NLOG OUT : phase-A plan = v4 - (E,W,N jobs) + manual SDA escape + E/W/N fix logs
cd /home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route8
python3 scripts/planminus.py t/pA2_4.json t/pA2_4.hrlog.json t/_c1.json /AUD_SDA:U3-31 /BT_TX_IND:U3-62 /PD_SINK_EN:U3-63 /BT_RST_N:U3-58 /MCU/ENC_B:U3-49 /BT_FORCE_PWM:U3-54 /BT_UART_TX:U3-55 /CTRL_SCL:U3-60 /PDCTRL_SDA:U3-44 /CODEC_PWR_EN:U3-39
python3 - <<'PY'
import json
p=json.load(open('t/_c1.json'))
for a,b in [((133.675,73.25),(135.0,73.25)),((135.0,73.25),(135.35,72.9))]: p['seg_add'].append(['F.Cu','/AUD_SDA',0.3,a[0],a[1],b[0],b[1]])
p['via_add'].append(['/AUD_SDA',135.35,72.9,0.5,0.2])
json.dump(p,open('t/_c1.json','w'),indent=1)
PY
python3 scripts/planplus.py t/_c1.json $3 t/pFE.hrlog.json $1 $2
