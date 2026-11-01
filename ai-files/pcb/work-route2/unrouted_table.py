"""unrouted_table.py RUN : markdown table of the unrouted connections of RUN (from RUN.analyze.json), grouped by cause.
'no exit' is split with the router's own exit model (evidence/exitprobe-H0.txt, -A1-2.txt): pad-bound already on H0 /
sealed by S1-S2 copper / sealed inside S3 or same-pad topology. Remedies: hand-written per part from the probe blockers and the
RT-1 report (pad-bound list), see routing-s1-s3-run.md section 5."""
import json, sys, re, collections
R = sys.argv[1]
U = json.load(open(R + '.analyze.json'))['unrouted']
def blocked(path):
    out = {}
    for L in open(path):
        m = re.match(r'^(\S+)\s+\S+\s+exits (\d+)\s*(.*)$', L.strip())
        if m:
            out[m.group(1)] = (int(m.group(2)), m.group(3))
    return out
H0 = blocked('evidence/exitprobe-H0.txt'); S2 = blocked('evidence/exitprobe-A1-2.txt')
REM = [  # (regex on 'net a b', remedy)
    (r'/I2S_(BCK|LRCK)', 'hand template: stitched B.Cu hops through the TP12/TP13/TP14 + R206-R208 hub (BKO_U6/U7 forbid B.Cu at the IC legs); or placement: swap TP12/TP14 order'),
    (r'U24-XO', 'placement nudge: C226 about 0.3 mm off the Y200-1 centre line (Y200-1 pad-bound in RT-1)'),
    (r'/AUD_SDA|/AUD_SCL', 'hand template: AUD I2C crossing at U6/TP17/TP18 with one stitched B.Cu hop; U24-23/24 pocket is the 3V3_AUDIO feed'),
    (r'HP_OUTL', 'hand route J2-5 -> U10-16 (one stitched hop), corridor taken by S2 audio nets'),
    (r'U8-COM|U8-NC|U9-9|U9-7', 'copper edit of the 3V3_AUDIO feed under U8/U9 (RT-1 sec.3 "copper-fixable"), or nudge R226 0.5 mm north'),
    (r'C239', 'nudge C239 about 0.5 mm east or reroute the 3V3_AUDIO track along its pads'),
    (r'U24-VIN|U24-VREF', 'placement nudge: C210 / C212 (pad-bound at U24-30 / U24-4 in RT-1) and hand fan-out of the U24 west pins'),
    (r'BT_AUDIO|USB_AUDIO|C204-Pad2|C205-Pad2|C231-Pad2|C233-Pad2|C235-Pad2|/AUX_L', 'hand route the coupling-cap block C200-C205/C230-C235 (dense, 0.5 mm audio clearance + 0.6 mm halo); or spread the block by 0.5-1 mm'),
    (r'U2-VOUT', 'placement nudge: C173 out of the U2-15/16 escape (RT-1 pad-bound list); VCCP1I/2I copper at the pins'),
    (r'U1-AOHPL', 'hand template for AOHPL/AOHPR at BM83 pins 8/9 (S2 stitch via and AOHPR via took the only outward exit)'),
    (r'AMP_FAULT_N|U6-~\{PDN\}|U7-~\{PDN\}|AMP_PDN', 'hand escapes inside BKO_U6/U7 (F.Cu only); placement nudge C283 / C296 (RT-1 pad-bound U6-17 / U7-17)'),
    (r'SW100-1 SW100-1|U11-40 U11-40', 'not a routing problem: two pads with the same number (pin stack); join under the part by hand or treat as internally connected'),
    (r'HP_SEL', 'S2 tracks of U8-NO1/NO2, U9-NO1/NO2 took the reserved escape (reservation order defect); hand reroute those 4 short nets (ratios 3.4-4.1) clear of U8/U9 pins 1 and 5'),
    (r'J7-', 'hand template: J7 (TC2030) pads are boxed by pad pitch and NPTH holes (0.5 mm edge rule); router has axial exits only. Rule question: NPTH clearance at J7'),
    (r'5V_LOGIC_EN', 'U14-1 rule-bound (SYS_RAW, POWER_HI 0.4 mm); placement nudge R142 / hand neck; R142 -> U3-18 sequential blocking'),
    (r'USB_CC', 'hand template: CC1/CC2 B.Cu hop right at J1 (S0b report open problem 3); J1-B5 pad-bound by VBUS'),
    (r'U12-EN|U20-PR1', 'placement nudge C124/C125 (RT-1 pad-bound U20-2/4/7); USB_AUX_5V / SYS_RAW copper at the pins'),
    (r'Q103-G|U4-BATP|/PROG|Q101-G|U11-FAULT', 'pour/power copper edits from RT-1 sec.3 (BAT_INT notch, REGN reroute, VBUS_PD pour corner); U4-18 is rule-bound (switch_critical 2.0 mm to BTST2): rule question'),
    (r'U14-FB', 'placement nudge C141/C142 off R140-2 (RT-1)'),
    (r'R18-Pad1', 'footprint-bound (U11-36 vs U11-34): hand neck escape'),
    (r'U7-ADR', 'placement nudge C294 (RT-1 pad-bound U7-8)'),
    (r'U25-', 'U25 switch-node copper and switch_critical rules: placement nudge R252 / C314 (RT-1), hand template for FB/COMP/ILIM/SS/MODE'),
    (r'AMP_BOOST_EN', 'U25-2 rule-bound (U25-SW pour); placement nudge R255/R252 and hand neck'),
    (r'AUX_DET', 'R242-2 sealed by S2 VMID_HP track and AUX_TIPSW pad: hand reroute of the VMID_HP leg'),
    (r'/Bluetooth/BT_|BT_UART_RX|CE_N', 'BM83 side: placement nudge R182/TP22 (sec.9 open problem 4); pour-island rejects need one added GND via to anchor the GND_BCU piece; route the J8/BM83 nets first inside S3'),
]
def remedy(u):
    key = '%s %s %s' % (u['net'], u['a'], u['b'])
    if u['cause'] == 'no exit':
        p = u['status'].split('no exit at ')[1]
        key += ' ' + p
    for rx, txt in REM:
        if re.search(rx, key):
            return txt
    return 'sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented)'
def cause(u):
    c = u['cause']
    if c == 'no exit':
        p = u['status'].split('no exit at ')[1]
        if H0.get(p, (1,))[0] == 0:
            return 'no exit: pad-bound on H0 (%s)' % H0[p][1].split(';')[0].split(':', 1)[-1].strip()[:40]
        if S2.get(p, (1,))[0] == 0:
            return 'no exit: sealed by S1-S2 copper (%s)' % S2[p][1].split(';')[0].split(':', 1)[-1].strip()[:40]
        return 'no exit: same-pad / sealed in S3'
    return c
G = collections.defaultdict(list)
for u in U:
    c = cause(u); grp = c.split(':')[0].split(' (')[0]
    G[grp].append((u, c))
order = ['no exit', 'keep-out', 'pour island', 'topology/pin order', 'no path']
print('| # | stage | net | connection | cause (detail) | proposed remedy |'); print('|---|---|---|---|---|---|')
i = 0; cnt = collections.Counter()
for g in order:
    for u, c in sorted([x for k, v in G.items() if k == g for x in v], key=lambda x: (x[0]['stage'], x[0]['net'])):
        i += 1; cnt[g] += 1
        print('| %d | %s | %s | %s - %s | %s | %s |' % (i, u['stage'], u['net'].replace('|', '/'), u['a'], u['b'], c, remedy(u)))
print(); print('counts', dict(cnt), 'total', i, file=sys.stderr)
sub = collections.Counter(cause(u).split(' (')[0] for u in U)
print('sub-causes', dict(sub), file=sys.stderr)
