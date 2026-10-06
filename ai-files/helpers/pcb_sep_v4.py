import pcbnew, json, math, re
import xml.etree.ElementTree as ET
bd = pcbnew.LoadBoard('/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb')
sheet = {c.get('ref'): (c.find('sheetpath').get('names').strip('/') if c.find('sheetpath') is not None else '') for c in ET.parse('/tmp/ds_net.xml').getroot().find('components')}
fp = {f.GetReference(): f for f in bd.GetFootprints()}
def bb(r):
    b = fp[r].GetBoundingBox(False); return (b.GetX() / 1e6, b.GetY() / 1e6, b.GetRight() / 1e6, b.GetBottom() / 1e6)
def gap(a, b):
    return math.hypot(max(a[0] - b[2], b[0] - a[2], 0), max(a[1] - b[3], b[1] - a[3], 0))
AS = ('Source_Select_ADC', 'Headphone_Aux', 'USB_Audio')
analog = [r for r in fp if sheet.get(r) in AS and not r.startswith('H')]
u1 = bb('U1')
bt = [r for r in analog if gap(bb(r), u1) < 8]
print('BT-audio coupling parts inside the BM83 cell (analogue sheet, <8 mm from U1):', bt)
analog2 = [r for r in analog if r not in bt]
def mn(A, B):
    best = (1e9, '', '')
    for a in A:
        for b in B:
            g = gap(bb(a), bb(b))
            if g < best[0]: best = (g, a, b)
    return '%.1f mm (%s - %s)' % best
classd = ['U6', 'U7'] + ['L%d' % i for i in range(201, 207)]
boost = ['U25', 'L200', 'C275']
sw = ['L1', 'L2', 'L3', 'U4', 'U14', 'U15', 'L200', 'U25', 'U6', 'U7'] + ['L%d' % i for i in range(201, 207)]
print('BM83 - analogue ICs/jacks/passives (excl. BT coupling parts):', mn(['U1'], analog2))
print('BM83 - analogue ICs/jacks only:', mn(['U1'], [r for r in analog2 if not r[0] in 'RC']))
print('BM83 - class-D/inductors:', mn(['U1'], classd), ' BM83 - boost:', mn(['U1'], boost), ' BM83 - L1/U4:', mn(['U1'], ['L1', 'U4']), ' BM83 - L2/U14:', mn(['U1'], ['L2', 'U14']), ' BM83 - U15/L3:', mn(['U1'], ['U15', 'L3']))
print('class-D - analogue ICs:', mn(classd, [r for r in analog2 if r[0] not in 'RC']), ' class-D - analogue ALL parts:', mn(classd, analog2))
print('boost - analogue ICs:', mn(boost, [r for r in analog2 if r[0] not in 'RC']), ' boost - analogue ALL:', mn(boost, analog2))
print('L2/U14 - analogue ALL:', mn(['L2', 'U14'], analog2), ' L1/U4 - analogue ALL:', mn(['L1', 'U4'], analog2), ' U15/L3 - analogue ALL:', mn(['U15', 'L3'], analog2))
