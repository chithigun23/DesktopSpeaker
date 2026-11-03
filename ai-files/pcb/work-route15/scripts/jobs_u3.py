#!/usr/bin/env python3
"""jobs_u3.py GEO OUT_JOBS OUT_PLAN [phase...] : RT-8 U3 re-route jobs (hr8 format). Phases: 1 local restore, 2 long nets."""
import sys, json
if __name__ == '__main__': geo, outj, outp = sys.argv[1:4]
else: geo = sys.argv[1]
ph = set(sys.argv[4:]) if __name__ == '__main__' else set()
D = json.load(open(geo)); pc = {'%s-%s' % (p['ref'], p['num']): (p['x'], p['y']) for p in D['pads']}
def J(net, fr, near, r=0.6, **kw):
    if isinstance(near, str): x, y = pc[near]; near = (x, y)
    j = dict(net=net, **{'from': fr}, to='NET', tgt_radius=150.0, tgt_near=[near[0], near[1], r], neck_drc=True, fine_via=True,
             island_via=True, layers='FBI', via_cost=1.2, max_exp=3e6, max_cells=4000000, margin=4)
    j.update(kw); return j
P1 = [
 J('/AUD_SDA', 'U3-31', 'R210-2', 0.3), J('/AUD_SDA', 'R210-2', (136.2, 89.15)),
 J('/AUD_SCL', 'U3-30', (158.62, 71.75)), J('/AUD_SCL', 'TP18-1', 'U3-30', 14.0),
 J('/ADC_INT', 'U3-26', (138.03, 90.45)),
 J('/MCU/NRST', 'U3-12', 'C162-1', 0.3), J('/MCU/NRST', 'TP19-1', 'C162-1', 5.0), J('/MCU/NRST', [126.25, 64.38, 'B.Cu'], 'U3-12', 4.0),
 J('/MCU/SWCLK', 'U3-46', 'J7-4', 0.3), J('/MCU/SWCLK', 'R160-1', 'U3-46', 6.0),
 J('/MCU/SWDIO', 'U3-45', 'J7-2', 0.3),
 J('/CHG_QON_SENSE', 'U3-3', (129.6, 62.48)), J('/PD_PLUG_EVENT', 'U3-4', (128.9, 61.73)), J('/PD_SINK_EN', 'U3-63', (137.12, 62.4)),
 J('/GAUGE_ALRT_N', 'U3-17', (115.88, 80.65)), J('/MCU/ENC_A', 'U3-48', (115.75, 79.83)), J('/5V_LOGIC_EN', 'U3-18', (124.33, 89.4)),
 J('/CTRL_SCL', 'U3-60', (115.15, 78.9)), J('/CTRL_SCL', [128.75, 89.25, 'via'], 'U3-60', 6.0),
 J('/CTRL_SDA', 'U3-61', (129.6, 89.1)),
 J('/PDCTRL_SCL', 'U3-43', (115.35, 63.7)), J('/PDCTRL_SCL', [135.5, 61.1, 'B.Cu'], 'U3-43', 12.0), J('/PDCTRL_SCL', 'R15-2', 'U3-43', 12.0),
 J('/PDCTRL_SDA', 'U3-44', (130.3, 61.98)),
 J('/CODEC_PWR_EN', 'U3-39', (128.2, 61.02)), J('/HP_DET', 'U3-28', (134.62, 63.95)), J('/HP_G1', 'U3-21', (151.03, 76.0)),
 J('/AMP_PDN', 'U3-23', 'R259-1', 0.3), J('/AMP_PDN', [118.85, 98.15, 'F.Cu'], 'U3-23', 8.0),
 J('/CHG_INT', 'U3-5', 'R106-2', 0.3),
 J('/MCU/ENC_B', 'U3-49', (113.66, 80.58)), J('/MCU/ENC_SW', 'U3-64', (125.28, 92.65)),
 J('/BT_FORCE_PWM', 'U3-54', (116.07, 67.51)), J('/BT_UART_TX', 'U3-55', 'TP21-1', 0.3), J('/BT_UART_RX', 'U3-56', (115.38, 71.95)),
 J('/BT_MFB', 'U3-57', (116.78, 64.0)), J('/BT_RST_N', 'U3-58', (118.38, 61.85)), J('/BT_TX_IND', 'U3-62', (117.53, 60.55)),
]
P2 = [
 J('/MCU/SWDIO', 'J6-1', 'U3-45', 25.0), J('/MCU/SWCLK', 'J6-2', 'U3-46', 25.0), J('/MCU/NRST', 'J6-3', 'U3-12', 25.0),
 J('/HP_SEL_A', 'U3-13', 'U8-1', 0.3), J('/HP_SEL_A', 'U8-5', 'U8-1', 4.0), J('/HP_SEL_B', 'U3-51', 'U9-1', 0.3), J('/HP_SEL_B', 'U9-5', 'U9-1', 4.0),
 J('/HP_G0', 'U3-16', 'U10-6', 0.3), J('/HP_G0', 'R237-1', 'U10-6', 4.0), J('/HP_EN', 'U3-47', 'U10-13', 0.3),
 J('/AUX_DET', 'U3-29', 'R242-2', 0.3),
 J('/CHG_ENABLE', 'U3-38', 'R107-1', 2.0), J('/CHG_SYS_ENABLE', 'U3-42', 'R111-1', 2.0),
 J('/AMP_BOOST_EN', 'U3-24', 'R255-1', 2.0), J('/AMP_FAULT_N', 'U3-25', 'R262-2', 0.3),
 J('/BT_PWR_EN', 'U3-36', 'R152-1', 2.0), J('/PD_PLUG_EVENT', 'U11-37', 'U3-4', 30.0), J('/PD_SINK_EN', 'U11-19', 'R17-2', 6.0),
 J('/AMP_PDN', 'R258-1', 'U3-23', 70.0), J('/5V_LOGIC_EN', 'R142-1', 'U14-1', 6.0), J('/CTRL_SDA', 'U13-2', 'U3-61', 30.0),
 J('/CTRL_SCL', 'U4-14', 'U4-15', 8.0), J('/AUD_SDA', 'U24-23', 'U24-24', 8.0),
]
if __name__ == '__main__':
  jobs = (P1 if '1' in ph else []) + (P2 if '2' in ph else [])
  json.dump(dict(geo=geo, out_plan=outp, jobs=jobs), open(outj, 'w'), indent=0)
  print(len(jobs), 'jobs')
