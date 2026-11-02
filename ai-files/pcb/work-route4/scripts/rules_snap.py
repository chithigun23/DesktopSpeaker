"""route_oct_rules.py : clearance model for route_oct.py, transcribed by hand from DesktopSpeaker.kicad_dru (read only, rule AG1).

The transcription is bound to the rule file by SHA-256: if the .kicad_dru beside the board differs from the hash below,
route_oct.py refuses to run (re-transcribe and re-verify with DRC first). The router is stricter than DRC on purpose:
  * the class rules (audio_clear, vbus_clear, pvdd_clear, switch_*, clk_clear) are combined by max(), not by KiCad's
    'last matching rule wins', so the router never relies on rule order to get a smaller clearance;
  * inside the neck_ic relaxation areas (fine-pitch IC courtyards + NECK_<ref> areas) the router uses 0.2 mm like DRC,
    but keeps the switch-node clearances (1.0 mm / 2.0 mm) because the rulebook says a relaxation area never lowers an
    analog-to-switch clearance;
  * neck_u11 (0.15 mm) and fine_pitch (pad-pad) are not used.
Board setup (from .kicad_pro): min clearance 0.1, copper-edge 0.5, hole clearance 0.25, hole-to-hole 0.3, min track 0.2.
"""
import hashlib, re

DRU_SHA256 = '102fbee45eadf16bac9531882e79962ad7d4a876274cf4d090981bd5bd71e80d'
SIGCLS = {'SIGNAL', 'Default', 'I2C', 'AUDIO', 'I2S_CLK', 'USB'}
CRIT_NETS = {'Net-(U4-BATP)', 'Net-(U25-FB)', 'Net-(U25-COMP)', 'Net-(U25-ILIM)'}
EDGE = 0.5
HOLE_CLR = 0.25
HOLE_HOLE = 0.3
NECK_W = 0.2
# width-only relaxation areas (rule usb_u2_entry: USB width 0.2 inside NECK_U2_USB)
WIDTH_AREAS = {'NECK_U2_USB': {'USB'}}
# B.Cu keep-out exceptions of rule bko_tracks / bko_vias (net names)
BKO_EXEMPT_NETS = {'Net-(U7-BST_B+)', 'Net-(U25-BOOT)', 'Net-(U24-AVDD)', 'Net-(U2-VCCCI)', 'Net-(U2-VCCP1I)', 'Net-(U2-VCCP2I)',
                   'Net-(U24-LDO)', 'Net-(U8-COM1)', 'Net-(U8-COM2)'}
BKO_EXEMPT_CLS = {'GND', 'PVDD', 'POWER_HI', 'SPK_OUT', 'SWITCH', 'PWR_5V', 'PWR_3V'}


def check_dru(path):
    h = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    return h == DRU_SHA256, h


def neck_targets(path):
    """courtyard refs and NECK area names of rule neck_ic, read from the rule file"""
    t = open(path, encoding='utf-8').read()
    m = re.search(r'\(rule neck_ic\s*\(condition "([^"]*)"', t)
    c = m.group(1)
    return re.findall(r"intersectsCourtyard\('([^']+)'\)", c), re.findall(r"intersectsArea\('([^']+)'\)", c)


def clr_strict(our_cls, our_net, it_cls, it_type):
    """our item is a Track or Via of a signal net; it_type in Pad/Track/Via/Zone"""
    if our_cls == 'USB' and it_cls == 'USB':
        return 0.15                     # usb_pair_gap (placed after all other rules)
    c = 0.2
    np_ = it_type != 'Pad'
    if our_cls == 'AUDIO' and it_cls not in ('AUDIO', 'GND') and np_: c = max(c, 0.5)
    if it_cls == 'AUDIO' and our_cls not in ('AUDIO', 'GND') and np_: c = max(c, 0.5)
    if it_cls == 'POWER_HI' and np_: c = max(c, 0.4)
    if it_cls in ('PVDD', 'SPK_OUT') and np_: c = max(c, 0.3)
    if it_cls == 'SWITCH' and our_cls not in ('SWITCH', 'GND'): c = max(c, 0.3)
    if it_cls == 'SWITCH' and our_cls in SIGCLS: c = max(c, 1.0)
    if it_cls in ('SWITCH', 'BOOT') and our_net in CRIT_NETS: c = max(c, 2.0)
    if our_cls == 'I2S_CLK' and it_cls not in ('I2S_CLK', 'GND') and np_: c = max(c, 0.4)
    if it_cls == 'I2S_CLK' and our_cls not in ('I2S_CLK', 'GND') and np_: c = max(c, 0.4)
    return c


def clr_neck(our_cls, our_net, it_cls, it_type):
    if our_cls == 'USB' and it_cls == 'USB':
        return 0.15
    c = 0.2
    if it_cls == 'SWITCH' and our_cls in SIGCLS: c = 1.0
    if it_cls in ('SWITCH', 'BOOT') and our_net in CRIT_NETS: c = 2.0
    return c


def bko_applies(our_cls, our_net):
    return our_cls not in BKO_EXEMPT_CLS and our_net not in BKO_EXEMPT_NETS
