"""Row data for buylist_review_fixes_20261103.py (2026-11-03 fastener schedule + CAD completeness review fixes).

UPDATES: {data row number (= # in hardware-buy-list.md): (expected item prefix, {column: new value or function})}
NEW_ROWS: appended in order as rows 43+.
Sourcing evidence for rows 47-65: reports/review-fixes-2026-11-03.md section 4 (agent "Review-fix parts sourcing").
"""
D = '2026-11-03'
BN_CSK = 'https://www.boltandnut.com.au/m3-x-0-50p-coarse-stainless-a2-70-g304-countersunk-post-torx-t10-machine-screws'
BN_BTN = 'https://www.boltandnut.com.au/security-fasteners/machine-screws/m3-x-0-50p-coarse-stainless-a2-70-g304-button-post-torx-t10-machine-screws'


def pre(text):
    return lambda old: text + ' Was: ' + old


def app(text):
    return lambda old: (old + ' ' + text).strip()


SUP = {'Line price': lambda old: (old.split()[0] + ' 0.00') if old and old[:3] in ('AUD', 'USD', 'EUR') else old,
       'Price status': 'superseded'}


def sup(qty, note):
    d = dict(SUP)
    d['Qty'] = qty
    d['Notes'] = pre(note)
    return d


UPDATES = {
    2: ('Woofer Tang Band W3-2052SC', {'Notes': pre(
        f'{D}: CAD v13+ geometry: square 82.55 frame (R4), 4 x 3.4 holes on a 96.52 mm bolt circle (68.25 mm square), frame block 13.3, '
        'factory 3.3 mm foam gasket, seated directly on the floor (no ring, no recess); screws button post-Torx M3x20 (row 44). '
        'All are photo estimates (+-1.5): caliper the sample before printing; check its termination (PHR-2 pigtail in the photo, UNVERIFIED).')}),
    3: ('Acoustic stuffing Acousta-Stuf', {'Spec': pre(
        f'polyester fill; {D}: 6-8 g per unit in the woofer chamber only, loose, 10 mm off the magnet and the cone back (Qtc about 0.70); '
        'the main chamber gets the 10 mm foam lining (row 54).')}),
    4: ('Acoustic grille cloth, black', {'Notes': app(
        f'{D}: also backs the woofer grille against debris (review S13); the yard covers both plates.')}),
    12: ('Speaker wire 20 AWG figure-8', {'Notes': app(
        f'{D} (review S9 slack for the assembly order): cut J9 about 110 mm, J10 modelled + 40 (about 336 / 292 mm), J11 adapter modelled + 40 '
        '(about 235 mm): about 0.7 m of pair; 1 m still covers.')}),
    13: ('Silicone wire 18 AWG', {'Qty': '1 pack (optional)', 'Qty 2nd unit': '0 (optional)', 'Price status': 'confirmed (optional, excluded)',
                                  'Notes': pre(f'{D}: optional alternative for the rocker leads (more flexible; insulation OD not stated, too thick '
                                               'for Micro-Fit crimps). Default is the thin-wall 18 AWG wire of row 57 for both the rocker leads and a '
                                               'J5 service lead.')}),
    14: ('Encoder knob (SW102)', sup('0 (superseded 2026-11-03)', f'{D}: superseded by row 64 (true 6 mm bore; the 6.35 bore sits 0.35 mm off-centre on the 6 mm shaft).')),
    15: ('Heat-set insert M3 x 5.7', {'Spec': f'brass, 46 per unit ({D}: lid 11, drivers 8, woofer 4, PCB 11, feet 4, knob cup 4, woofer-chamber insert 4); 51 with 10 % spares',
                                      'Qty 2nd unit': '0 (51 + 46 = 97 of 100)'}),
    16: ('Socket cap screw M3 x 10', {'Price status': 'superseded', 'Notes': pre(f'{D}: superseded everywhere (lid, drivers, knob cup, insert: row 40; woofer: row 44).')}),
    17: ('Socket cap screw M3 x 16', sup('0 (superseded 2026-11-03)', f'{D}: superseded by button post-Torx M3x10 (row 43) on Wurth 971100321 M/F standoffs (row 46); ball-end hex keys are not used any more.')),
    19: ('Hex spacer M3 F/F 10 mm', sup('0 (superseded 2026-11-03)', f'{D}: superseded by the M/F standoff Wurth 971100321 (row 46, steel) and a nylon standoff at H9 (row 47).')),
    21: ('Rubber foot disc 12.7 dia', sup('0 (superseded 2026-11-03)', f'{D}: a glued bumper on the 5.5 AF stud end shears off when the speaker is slid (review S12): superseded by screw-in rubber feet (row 63).')),
    22: ('Nylon flat washer M3', sup('0 (removed 2026-11-03, superseded)', f'{D}: removed: a flat washer cannot sit under the flush countersunk lid screws. The 4 lid screws inside the woofer-chamber loop get foam washers cut from the 1.5 mm sheet in boss counterbores (CAD v16) or a non-curing butyl dab.')),
    23: ('Snap bushing / grommet', {'Notes': pre(f'{D}: CAD v16 sets the hole to 6.35 mm and the web to 1.5 mm (inside the 1.57 rating); no reaming. Re-checked on Digi-Key AU 2026-11-03: A$0.15 ex GST, 221,582 in stock, lead time 3 weeks. ID: Digi-Key 3.56 mm (0.140 in) but a GlobalSpec datasheet copy says 0.125 in (3.18): the J11 pair (2 x OD 1.75 = 3.5 x 1.75) needs the 3.56 figure: confirm on the part.')}),
    25: ('Lid gasket cord, closed-cell EPDM sponge 3 mm', sup('0 (superseded 2026-11-03)', f'{D}: 3 mm cord fills the 2.0 x 1.5 groove 235 % (review S4): superseded by 2 mm cord (row 50).')),
    26: ('Driver/woofer gasket, closed-cell foam sheet', {**SUP, 'Qty': '0 (superseded 2026-11-03)', 'Notes': pre(f'{D}: superseded by the sourced foam sheets rows 51-53 (3 mm for the driver gaskets per the coordinator; woofer ring only if the factory gasket is missing).')}),
    27: ('PU sealant/adhesive Sikaflex-11FC', {'Spec': pre(f'{D}: grille plates and grommet leads only; the woofer-chamber insert is now screwed on a 1.5 mm foam gasket (removable), not bonded.')}),
    30: ('Filament PETG 1.75 mm', {'Notes': app(f'{D}: add the knob cup, 3 SW100 plungers and the tie bridges (small; volumes from CAD v16). One roll is tight: a second roll for reprints is advisable.')}),
    31: ('1S4P 21700, 20 Ah', {
        'Item': lambda old: old.replace('max 87.0 x 75.0 x 23.0 mm including wrap and PCM', 'max 87.0 x 75.0 x 22.3 mm including wrap, PCM, fuse and TCO, 15 A PACK+ fuse, about 85 C thermal cut-off').replace('lead about 180 mm', 'thin-wall 18 AWG leads (OD <= 1.7) about 180 mm'),
        'Notes': app(f'{D} review fixes: the RFQ adds a 15 A fuse in PACK+ and an about 85 C thermal cut-off (rows 60-61) and limits the thickness to 22.3 mm (cradle usable thickness; 23.0 superseded).')}),
    40: ('Countersunk post-Torx (T10 security) machine screw M3 x 10', {
        'Qty': '30', 'Qty 2nd unit': '27',
        'Spec': 'M3 x 0.5, 90 deg countersunk, head 5.90 x 2.00, T10 post (pin) Torx, length 10 overall incl. head; 27 per unit: 11 lid + 8 drivers (on cup washers, row 42) + 4 knob cup + 4 woofer-chamber insert; 30 with 10 % spares',
        'Part number': '22CPTS310 (maker MPN YCXSA2M3X10)', 'Unit price': 'AUD 0.63', 'Line price': 'AUD 18.90',
        'Stock/date': '29,590 (page JSON 2026-11-03)',
        'Notes': f'{D} fastener schedule: tiers per piece 10+ 1.00, 20+ 0.75, 30+ 0.63, 50+ 0.42 (50 cost AUD 21.00 and cover a second unit). Lid thread 6.0 below the lid, driver about 7.5 engaged (5.7 insert full). Was: qty 19, price not read.',
        'Price status': 'confirmed', 'URL': BN_CSK}),
    41: ('T10 x 25 mm post-Torx', {
        'Qty': '2', 'Qty 2nd unit': '0', 'Spec': '1/4 in hex insert bit, T10 with centre hole for the post; Alpha TXSE1025; one + spare',
        'Part number': '11PT1025A (Alpha TXSE1025)', 'Unit price': 'AUD 7.00', 'Line price': 'AUD 14.00', 'Stock/date': 'In stock (page 2026-11-03)',
        'Notes': f'{D}: standalone price 9.00, 2+ 7.00; the screw pages offer it as a bundle at AUD 3.00 (quantity rule not verified). A plain T10 bit does not fit the post. Was: qty 1, bundle AUD 3.00.',
        'Price status': 'confirmed', 'URL': 'https://www.boltandnut.com.au/t10-x-25mm-alpha-post-torx-insert-security-standard-driver-bit'}),
    42: ('Countersunk (cup / finishing) washer M3', {
        'Item': 'Cup washer 6g (3.5 mm) G304 stainless, OD 11.0-11.4, ID 4.1-4.5, cup 2.1-2.3, 90 deg',
        'Qty': '10', 'Qty 2nd unit': '8', 'Spec': 'under the countersunk M3 post-Torx heads on the 0.75 mm ND65 flanges (8 per unit) + 2 spares',
        'Source': 'Bolt and Nut Australia (Hobson Engineering)', 'Part number': '71CS6', 'Unit price': 'AUD 0.64', 'Line price': 'AUD 6.40',
        'Stock/date': 'In stock (page 2026-11-03)',
        'Notes': f'{D}: replaces the unsourced 8 x 1.6 countersunk washer (same row). 10+ tier; 10 cost less than 9. Fit of the 5.90 head in the 6g cup calculated from geometry, not tested; CAD v16 checks the 11.4 OD against the ND65 basket ribs.',
        'Price status': 'confirmed', 'URL': 'https://www.boltandnut.com.au/washers/cup-washers/6g-3-5mm-g304-stainless-cup-washers'}),
}

# --------------------------------------------------------------------------- new rows (43+)
def row(item, qty, qty2, spec, source, pn, unit, line, stock, notes, cat, status, url):
    return {'Item': item, 'Qty': qty, 'Qty 2nd unit': qty2, 'Spec': spec, 'Source': source, 'Part number': pn, 'Unit price': unit,
            'Line price': line, 'Stock/date': stock, 'Notes': notes, 'Category': cat, 'Price status': status, 'URL': url}


NEW_ROWS = [
    row('Button post-Torx (T10 security) machine screw M3 x 10, A2-70 (304) stainless', '12', '10',
        'M3 x 0.5, button head 5.11-5.70 x 1.60-1.80, length 10 under the head; PCB H1-H8, HA1, HA2 into the Wurth 971100321 standoffs (8.4 mm in the steel thread); 10 per unit + 10 % + 1 so H9 can fall back to steel',
        'Bolt and Nut Australia (Hobson Engineering)', '22BPTS310', 'AUD 1.00', 'AUD 12.00', '20,345 (page JSON 2026-11-03)',
        f'{D} fastener schedule; replaces row 17 (M3x16 socket). Tiers 10+ 1.00, 20+ 0.70. H9 uses a nylon screw (row 48).', 'Mechanical', 'confirmed', BN_BTN),
    row('Button post-Torx (T10 security) machine screw M3 x 20, A2-70 (304) stainless', '5', '4',
        'M3 x 0.5, button head 5.11-5.70 x 1.60-1.80, length 20 under the head; woofer W3-2052SC (frame 13.3 + factory gasket 3.3)',
        'Bolt and Nut Australia (Hobson Engineering)', '22BPTS320', 'AUD 1.60', 'AUD 8.00', '29,639 (page JSON 2026-11-03)',
        f'{D}: replaces the never-listed ISO 4762 M3x20 (review 3.2 #1). Engagement 3.4 mm free / 4.4 mm compressed (marginal); 5.4-5.7 with the optional 2 mm floor-boss tweak after calipering. 20 is the longest M3 button post-Torx at Bolt and Nut.',
        'Mechanical', 'confirmed', BN_BTN),
    row('T10 post-Torx L-key 90 mm, short arm 19 mm', '2', '0',
        'Hobson ISKPT10, alloy tool steel; one for the PCB and woofer screws, one to cut to about 8 mm short arm for H8 (fallback once the knob cup is removable)',
        'Bolt and Nut Australia', '11PTK10H (Hobson ISKPT10)', 'AUD 6.00', 'AUD 12.00', 'In stock (page 2026-11-03)',
        f'{D}: standalone 9.00, 2+ 6.00; bundle price 5.00 on the screw pages (quantity rule not verified). Ball-end keys do not fit post-Torx. HA1/HA2 are about 120 mm deep: check the reach with the real key.',
        'Tools', 'confirmed', 'https://www.boltandnut.com.au/t10-x-90mm-hobson-post-torx-security-allen-key'),
    row('Hex standoff M3 M/F, 10 mm body + 6 mm stud, 5.5 AF, steel zinc', '12', '10',
        'PCB H1-H8, HA1, HA2: stud into the roof insert, button M3x10 into the female end; 10 per unit + 10 % + 1 for an H9 steel fallback',
        'Digi-Key', 'Wurth 971100321 (DK 732-10398-ND)', 'USD 0.33', 'USD 3.96', '32,433 (DK 2026-11-03)',
        f'{D}: replaces row 19 (F/F 970100321 + M3x16). Female thread depth UNVERIFIED (RS listing: hole depth 10); if < 8.5 mm use button M3x8 (Bolt and Nut 22BPTS38).',
        'Mechanical', 'confirmed', 'https://www.digikey.com/en/products/result?keywords=971100321'),
    # ---- 47-65: sourced 2026-11-03 by agent "Review-fix parts sourcing" (Digi-Key AU prices ex GST; AU store prices inc GST)
    row('Nylon (polyamide) hex standoff M3 M/F, 10 mm body + 8 mm stud, 6 mm hex, black (H9)', '2', '1',
        'H9 only (nearest metal to the BM83 antenna, 16.3 mm): stud into the roof insert, nylon screw into the female end. **Trim the 8 mm stud to 6 mm** (pilot floor is 6.7 below the insert top) or add a nylon washer',
        'Digi-Key AU', 'Wurth 971100365 (DK 732-13056-ND)', 'AUD 1.33', 'AUD 2.66', '4,877 (DK AU 2026-11-03)',
        f'{D}: VERIFIED. Wurth nylon M/F appears to come only with an 8 mm stud. Fallback Wurth 970100365 nylon F/F 10 mm (AUD 1.27, 2,424) is not usable here (no screw can enter the roof insert from below). Price ex GST (assumed; not labelled).',
        'Mechanical', 'confirmed', 'https://www.digikey.com.au/en/products/detail/w%C3%BCrth-elektronik/971100365/9488760'),
    row('Nylon (PA66) machine screw M3 x 10, pan head Phillips (H9)', '2', '1',
        'M3, 10 under the head, pan head 5.5 mm; through the PCB (1.6) into the nylon standoff (about 8.4 mm engaged)',
        'Digi-Key AU', 'Wurth 97791003111 (DK 732-13706-ND)', 'AUD 0.38', 'AUD 0.76', '14,984 (DK AU 2026-11-03)',
        f'{D}: VERIFIED. Not tamper-resistant (Phillips), acceptable inside the sealed box. Bolt and Nut showed no nylon M3 screw or standoff (partial read of the pan-head list; nylon washers only).',
        'Mechanical', 'confirmed', 'https://www.digikey.com.au/en/products/detail/w%C3%BCrth-elektronik/97791003111/10056389'),
    row('1/4 in hex magnetic bit holder / extension 300 mm', '1', '0',
        'for the 8 driver screws driven through the empty shell (about 190 mm deep); takes 25 mm insert bits',
        'Bunnings (AU)', 'Kango 300 mm HyperTorque impact magnetic bit holder (Bunnings I/N 0727956)', 'AUD 19.99', 'AUD 19.99', 'store stock only (page 2026-11-03)',
        f'{D}: VERIFIED page. Check that the post-Torx bit sits fully in the holder. Fallback Wera 05160981001 300 mm (UNVERIFIED for AU).',
        'Tools', 'confirmed', 'https://www.bunnings.com.au/kango-300mm-hypertorque-impact-magnetic-bit-holder_p0727956'),
    row('Lid gasket cord, EPDM sponge 2 mm round', '2 m', '0 (covers)',
        'lid groove 2.0 x 1.5: outer loop 0.51 + chamber U 0.23 = 0.75 m per unit; 2 m covers spares and one refit. Also usable for the woofer-chamber insert floor groove if CAD v16 cuts one',
        'Polymax (UK)', 'Polymax 2004200', 'GBP 3.55', 'GBP 7.10', 'In stock (page 2026-11-03)',
        f'{D}: price VERIFIED (inc VAT, per metre); **closed-cell not stated on the page** (EPDM sponge cord normally is: confirm); 2.0 +-0.5 mm, 45 Shore A; AU freight not checked. No AU retail 2 mm source found (Associated Gaskets lists EPDM sponge cord from 3 mm). Replaces row 25.',
        'Seal', 'estimate', 'https://www.polymax.co.uk/epdm-sponge-cord-2mm'),
    row('Closed-cell foam sheet 2 mm, adhesive one side (connector-face seals)', 'about 150 x 100 mm', '0 (covers)',
        'lid inner face around J1 (cut-out 8.6 x 2.9), J2/J3 (holes 5.0 or the v16 bore), SW100 (5.0): one die-cut piece or four pads; about 25 % compression against the connector faces',
        'NOT SOURCED (Clark Rubber store cut suggested)', '-', 'TBD', 'TBD', '-',
        f'{D}: UNVERIFIED: no A4-size adhesive 2 mm closed-cell sheet verified at an AU retailer (RS AU blocked fetches). Options: Clark Rubber or Foam Sales store cut; craft EVA self-adhesive A4 sheet (Spotlight/Officeworks, not verified, EVA is closed-cell).',
        'Seal', 'TBD', '-'),
    row('Closed-cell neoprene self-adhesive tape 12 mm x 3 mm (driver gaskets, encoder washer)', '2 m', '0 (covers)',
        'driver gaskets: 63 mm square frame of strips (ring width 1.75 mm at the flats, cut from the 12 mm strip), 2 drivers about 0.5 m; encoder washer ID 7 / **OD 12** (the strip is 12 mm wide; review asked OD 14) x 3 mm; woofer ring only if the sample has no factory gasket',
        'Clark Rubber (AU)', 'Clark Rubber 15471P neoprene (CR) self-adhesive tape 3 mm', 'AUD 5.50', 'AUD 11.00', 'not shown (buy online or in store, 2026-11-03)',
        f'{D}: price VERIFIED ("from" A$5.50 per metre on the category page; range stated closed-cell). Softer alternative Clark Rubber 15496P EPDM414 supersoft 12 x 3 mm from A$3.95/m. Replaces row 26. 3 mm is the coordinator choice: CAD v16 sets the driver recess for it.',
        'Seal', 'confirmed', 'https://www.clarkrubber.com.au/products/15471p-neoprene-cr-self-adhesive-tape-3mm-black'),
    row('Closed-cell foam sheet 1.5 mm, adhesive one side (woofer-chamber insert gasket, knob-cup ring, lid screw washers)', '1 piece about 200 x 150 mm', '0 (covers)',
        'woofer-chamber insert floor gasket (removable insert), knob-cup flange ring (46 mm), 4 lid-screw washers ID 3.2 / OD 7.5 if CAD v16 adds the boss counterbores',
        'RS Components AU (or Clark Rubber store cut)', 'RS PRO 733-6731 closed-cell neoprene sponge 1.5 mm, 1 x 2 m (adhesive backing unconfirmed)', 'TBD', 'TBD', 'not read (RS AU returned 403)',
        f'{D}: UNVERIFIED (listings conflict on adhesive backing; 1 x 2 m is far more than needed). Alternatives: Inseal 3259 closed-cell PVC tape 1.5 x 30 mm x 50 m A$87.40 + GST (PB Tech, UNVERIFIED); a 2 mm cord in a groove instead of the flat gasket if CAD v16 chooses it.',
        'Seal', 'TBD', 'https://hkcn.rs-online.com/web/p/rubber-sheets/7336753'),
    row('Acoustic lining for the main chamber, about 10 mm (wadding or open-cell foam)', '1 sheet', '0 (covers)',
        'about 0.04 m2: top wall over the drivers (not under the cable path) and the side walls in front of the insert; keeps fibres off the PCB, encoder and jacks',
        'Jaycar (AU)', 'Jaycar AX3694 650 gsm acrylic speaker dampening material', 'TBD', 'TBD', 'not read (Jaycar returned 403)',
        f'{D}: UNVERIFIED (price, size and thickness not read; 650 gsm wadding is usually thicker than 10 mm uncompressed: trim or compress). Fallback Monacor MDM-3002 open-cell PU foam 480 x 378 x 10 mm, GBP 13.35 ex VAT (Rapid Online UK, UNVERIFIED).',
        'Acoustic', 'TBD', 'https://www.jaycar.com.au/650gsm-acrylic-speaker-dampening-material/p/AX3694'),
    row('Nylon cable ties 2.5 x 100 mm, black UV-stabilised, pack of 100', '1 pack', '0 (covers)',
        '9 anchor points (review M4) + driver lead ties; pack covers many units',
        'Altronics (AU)', 'Altronics H4031A', 'AUD 4.55', 'AUD 4.55', 'stock not shown (page 2026-11-03)',
        f'{D}: VERIFIED price. Natural colour H4012A same price. Jaycar HP1203 is 2.0 mm wide.',
        'Consumables', 'confirmed', 'https://www.altronics.com.au/product/h4031a-100mm-black-uv-resistant-cable-ties-pk-100'),
    row('Adhesive cable-tie mounts 21 x 21 mm, pack of 25', '1 pack', '0 (covers)',
        'where CAD v16 does not print a tie bridge; add a dab of CA glue on PETG',
        'Altronics (AU)', 'Altronics H4110A', 'AUD 9.15', 'AUD 9.15', 'In stock (page 2026-11-03)',
        f'{D}: VERIFIED. Maximum tie width not stated (this size normally takes 2.5-4.8 mm). Needs a 21 mm flat land: check against the wall curvature in CAD v16.',
        'Consumables', 'confirmed', 'https://www.altronics.com.au/p/h4110a-21mm-adhesive-cable-tie-mounts-pk-25/'),
    row('Thin-wall hook-up wire 18 AWG ETFE, OD 1.52 mm, 2 ft red + 2 ft black', '4 ft (2 + 2)', '4 ft',
        'TE Raychem Spec 55, 19/30 tinned copper, 600 V, -65..150 C. Rocker SW101 leads 2 x about 150 mm with a 60-80 mm service loop; J5 service/spare lead (fits the Micro-Fit 43030-0038, insulation max 1.85)',
        'Digi-Key AU', 'TE 55A0111-18-0 black (A$2.67/ft) + 55A0111-18-2 red (A$2.53/ft)', 'AUD 2.60', 'AUD 10.40', '2,217 ft black / 3,256 ft red (DK AU 2026-11-03)',
        f'{D}: VERIFIED. Unit price is the mean of the two colours per foot (line = 2 x 2.67 + 2 x 2.53). 18 AWG kept for the rocker (pack current path, up to about 9 A); the 20 AWG 55A0111-20-x (OD 1.27, A$1.93/ft) was not chosen. Row 13 silicone becomes optional.',
        'Wire', 'confirmed', 'https://www.digikey.com.au/en/products/detail/te-connectivity-raychem-cable-protection/55A0111-18-0/2399856'),
    row('Heat-shrink assortment 2:1 black, 160 pcs x 100 mm (1.6-9.5 mm)', '1 pack', '0 (covers)',
        'J11 splice sleeves in the woofer chamber, rocker and J5 service-lead joints, lamp-tab insulation backup',
        'Altronics (AU)', 'Altronics W0886', 'AUD 22.95', 'AUD 22.95', 'In stock (page 2026-11-03)',
        f'{D}: VERIFIED. Count per size not stated. Review 3.2 #11 (heat-shrink absent).',
        'Consumables', 'confirmed', 'https://www.altronics.com.au/p/w0886-160pc-100mm-black-heatshrink-pack/'),
    row('Polyimide (Kapton) tape 12 mm x 33 m', '1 roll', '0 (covers)',
        'insulation where leads cross metal (driver baskets, PCM edge, splices); 60 um, 260 C',
        'Altronics (AU)', 'Altronics T2972A', 'AUD 14.50', 'AUD 14.50', 'In stock (page 2026-11-03)',
        f'{D}: VERIFIED. Review 3.2 #11 (Kapton absent).',
        'Consumables', 'confirmed', 'https://www.altronics.com.au/p/t2972a-12mm-x-33m-high-temperature-polyimide-tape/'),
    row('PACK+ fuse 15 A (fitted by the pack vendor; RFQ item 2)', '1 (in the pack)', '1 (in the pack)',
        'secondary protection at the PCM output: carries 10 A continuous and 20 A for 1 s; interrupting rating at 5 V DC above the pack short-circuit current. Example proposed to the vendor: Littelfuse NANO2 0453015.MR (15 A, 65 V, 6.1 x 2.7 x 2.7 mm SMD)',
        'Pack vendor (RFQ)', 'example Littelfuse 0453015.MR (DK F3142CT-ND, A$5.02 ex GST, 7,141 in stock)', 'TBD', 'TBD', 'vendor to state',
        f'{D}: part of the pack quote, not a separate purchase (placeholder outside every subtotal). The 0453015 listing is VERIFIED; its 50 A breaking rating (at rated voltage) is UNVERIFIED as adequate for a 4P short (hundreds of A): the vendor must state the interrupting rating. There is no 15 A part in the Littelfuse 456 series (it starts at 20 A).',
        'Battery', 'TBD', 'https://www.digikey.com.au/en/products/detail/littelfuse-inc/0453015-MR/552266'),
    row('Thermal cut-off about 85 C (fitted by the pack vendor; RFQ item 2)', '1 (in the pack)', '1 (in the pack)',
        'in thermal contact with the cells, in series with PACK+; >= 15 A DC breaking; hold current >= 10 A at 45 C. Example proposed: Bourns (Komatsulite) NR85AB0 mini-breaker, 85 +-5 C trip, 40 C reset, 5 mOhm, breaks 60 A at 5 V DC',
        'Pack vendor (RFQ)', 'example Bourns NR85AB0 (DK NR85AB0-ND, A$2.54 ex GST, 19,995 in stock)', 'TBD', 'TBD', 'vendor to state',
        f'{D}: part of the pack quote (placeholder outside every subtotal). Datasheet https://www.bourns.com/docs/Product-Datasheets/nr.pdf read by the sourcing agent: the A-type also trips on self-heating, about 13 A at room temperature and less when warm, so the hold current at 45 C must be confirmed against the 8.5 A amplifier peaks. Tabs must be welded, not reflowed. Vendor-only alternative Bourns AC85ABD (35 A / 28 V, MOQ 3000).',
        'Battery', 'TBD', 'https://www.digikey.com.au/en/products/result?keywords=NR85AB0'),
    row('Inline mini-blade fuse holder + 15 A mini blade fuse (OPTIONAL fallback)', '0 (1 if the vendor declines the fuse)', '0',
        'in the PACK+ lead between the pack and J5 if the pack vendor cannot fit the 15 A fuse (the 180 mm lead has about 49 mm of slack); confirm the holder leads take 16-18 AWG',
        'Altronics / Jaycar (AU)', 'Altronics S6035 holder (A$7.95, in stock) + Jaycar SF1915 15 A mini blade (A$1.30, snippet)', 'AUD 9.25', 'AUD 0.00', 'holder in stock; fuse stock not read (2026-11-03)',
        f'{D}: holder VERIFIED, fuse UNVERIFIED (Altronics S5919 15 A out of stock; S5485 low-profile A$1.15 snippet). Excluded from subtotals. CAD would need to model the holder.',
        'Battery', 'confirmed (optional, excluded)', 'https://www.altronics.com.au/p/s6035-30a-in-line-mount-mini-blade-fuse-holder/'),
    row('Screw-in rubber foot, M3 x 6 male stud, 8 mm dia x 8 mm (into the stud female end)', '5', '4',
        'screws into the female end of the Wurth 971120321 foot stud (row 20); floor gap becomes 12 + 8 = 20 mm (CAD v16 updates the woofer gap and tipping). 4 + 1 spare',
        'RS Components AU', 'RS PRO 196-1356 (M3 x 6 male buffer, 8 x 8 mm, 45 Shore A)', 'TBD', 'TBD', 'not read (RS AU returned 403)',
        f'{D}: UNVERIFIED. No 12-16 mm diameter buffer with an M3 stud was found anywhere (catalogue M3 buffers are 8 mm). Options: (a) this 8 x 8 M3 buffer on the stud (keeps the stud, small contact patch; a 12.7 mm Bumpon can be stuck on its face); (b) Ruland VMS8-8-M3-55-SSNR/10PK 8 x 8 (UNVERIFIED stock); (c) change the 4 foot inserts to M4 and drop the stud: Small Parts and Bearings CMB01513040MR60 15 x 13 mm M4 buffer (gap 13 mm; UNVERIFIED, site 429). Owner/CAD decision. Replaces row 21.',
        'Mechanical', 'TBD', '-'),
    row('Encoder knob, knurled aluminium, 6.00 mm bore, 2 set screws, 31.75 mm skirt x 15.88 mm (SW102)', '1', '1',
        'Kilo International DDS-90-4-7, black matte, skirted, arrow on the skirt; knurled body 23.5 mm. For the Alps EC11E18244AU 6 mm flat (D) shaft, 20 mm actuator (Alps product list: flat shaft, 20 mm) [the 6 mm diameter is from the CAD stand-in / EC11 family, D]. Tighten one set screw on the flat',
        'Digi-Key AU', 'Kilo DDS-90-4-7 (DK 305224)', 'AUD 26.82', 'AUD 26.82', '26 (DK AU 2026-11-03); maker lead time 12 weeks after stock',
        f'{D}: VERIFIED (ex GST; A$29.50 inc). Replaces row 14 (6.35 bore). In the 36 mm cup: about 2.1 mm radial gap at the skirt; the knurled body above the skirt gives the grip the review S6 asked for; 15.88 tall vs the 14 mm stand-in, so CAD v16 must re-check the top height. No finger dimple. Fallbacks: Kilo DDS-75-3-7 (25.4 skirt, A$25.84, 37); Same Sky SAK-002 (28.9 x 12, 6 mm D bore: ideal, but MOQ 2268, not orderable); Altronics H6224 29 x 14 (A$5.05) has the 6.35 bore problem.',
        'Mechanical', 'confirmed', 'https://www.digikey.com.au/en/products/detail/kilo-international/DDS-90-4-7/305224'),
    row('PCB drill bit set 0.3-1.2 mm, 10 pcs (0.5 mm for the vents)', '1 set', '0',
        'two 0.5 mm pressure-equalisation holes through the printed lid (woofer zone and main chamber), in a pin vice or drill stand',
        'Altronics (AU)', 'Altronics T2329', 'AUD 16.95', 'AUD 16.95', 'In stock (page 2026-11-03)',
        f'{D}: price/stock VERIFIED; carbide and 1/8 in shank not stated on the page. Carbide bits are brittle: use a stand. Cover each hole inside with a dot of grille cloth (row 4) or felt.',
        'Tools', 'confirmed', 'https://www.altronics.com.au/product/t2329-pcb-drill-set-10pk'),
    # ---- 66-71: no purchase (cut or printed)
    row('Encoder foam washer ID 7 / OD 12 x 3 mm (cut from row 52)', '2 (1 + spare)', '1',
        'on the SW102 bushing top under the knob-cup floor, compresses to about 2.1 mm; closes the 1.25 mm radial shaft gap (review S1b, 28.5 mm2)',
        'cut from row 52', '-', '-', '-', '-', f'{D}: no purchase.', 'Seal', 'cut (no purchase)', '-'),
    row('Printed main shell (PETG), incl. printed cable-tie bridges', '1', '1',
        'CAD v16 (`ai-files/cad/v16/`): knob-cup opening and insert bosses, floor screw holes for the removable insert, tie bridges, cradle re-cut from the vendor drawing', 'printed (row 30)', 'CAD v16 STL', '-', '-', '-',
        f'{D}: do not print before CAD v16 passes its insertion-path and tool-access check and the woofer has been calipered.', 'Print', 'printed (no purchase)', '-'),
    row('Printed rear lid 4 mm (PETG)', '1', '1',
        'CAD v16: SW100 counterbore 7.4 x 1.0, gasket groove 2.0 x 1.5, 11 countersinks; vents drilled after printing (row 65)', 'printed (row 30)', 'CAD v16 STL', '-', '-', '-',
        f'{D}: outer face on the bed; labels (if added in v16) print mirrored.', 'Print', 'printed (no purchase)', '-'),
    row('Printed woofer-chamber insert (PETG), removable', '1', '1',
        'CAD v16: 4 boss feet with inserts for the floor screws, foam gasket land, grommet hole 6.35 / web 1.5', 'printed (row 30)', 'CAD v16 STL', '-', '-', '-',
        f'{D}: roof down, no supports (as v15).', 'Print', 'printed (no purchase)', '-'),
    row('Printed knob cup (PETG), new', '1', '1',
        'CAD v16: 36 mm dish, 3 mm wall and floor, 8.5 shaft hole, 46 mm flange, 4 countersunk screw holes', 'printed (row 30)', 'CAD v16 STL', '-', '-', '-',
        f'{D}: new part (review M1 option b).', 'Print', 'printed (no purchase)', '-'),
    row('Printed SW100 plunger (PETG), 3 variants', '3 (fit 1)', '3',
        'nub lengths 0.4 / 0.6 / 0.8 mm; shank 4.6, flange 7.0 x 0.8, nub 1.8 dia', 'printed (row 30)', 'CAD v16 STL', '-', '-', '-',
        f'{D}: keep the variant that clicks without preload (TE travel unknown, about 0.25 mm assumed).', 'Print', 'printed (no purchase)', '-'),
]
