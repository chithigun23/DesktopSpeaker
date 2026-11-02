# CAD sourcing log (v13), 2026-11-02

Scope: download and dimension extraction only. No project files changed except this folder and five new PDFs copied flat into `ai-files/datasheets/`.

HEADLINE: NO real STEP file was obtainable from any source. All manufacturer STEP routes were blocked (TE, Coilcraft, Bourns, Microchip, Keystone: HTTP 403 bot walls; Molex: no response; JST: download is form-gated; Wurth: 403). The EasyEDA endpoint `modules.easyeda.com/3dmodel/<uuid>` returns Wavefront OBJ (mm), not STEP; the STEP endpoint (`.../qAxj6KHrDKw4blvomvyg/<uuid>`) now returns 404 NoSuchKey. OBJ bounding boxes are given below (vertex min/max, mm, from the OBJ file, not freecadcmd). freecadcmd was used only on the project's existing STEP files (section C).

## (a) Attempts table

| Part | Source | URL | Result | Saved |
|---|---|---|---|---|
| Woofer | tb-speaker.com | /product/w3-2052sc/ | 200 but "page has moved" (73 B) | none |
| Woofer | tb-speaker.com | /products/list/24, /30, /31 (/38 timed out) | 200, no W3-2052SC entry | none |
| Woofer | parts-express.com | /Tang-Band-W3-2052SC-3-Full-Range-Driver-299-572 | 200, JS-only SPA, empty | none |
| Woofer | parts-express.com | /Tang-Band-W3-2052SC-3-RBM-Neodymium-Subwoofer-4-Ohm-299-572 (real URL) | 200, JS-only SPA | none |
| Woofer | parts-express.com | /api/items?fieldset=details&url=...299-572 (the shop's own JSON) | 200 with specs | tangband_W3-2052SC/parts-express_299-572_api_items.json |
| Woofer | parts-express.com | product images 299-572_{HR_0.default,ALT_0,ALT_1,ALT_2}.jpg | 200 x4 | tangband_W3-2052SC/img_*.jpg |
| Woofer | parts-express.com | /pedocs/specs/299-572--...spec-sheet.pdf (guessed) | 200, 0 bytes | none (deleted) |
| Woofer | WebSearch x3 | maker drawing / spec | no maker drawing exists online | none |
| CW rocker | switches-connectors-custom.cwind.com | /Asset/GRB112B802BR1.pdf | 404 | none |
| CW rocker | cwind.com | /product/GRB112B802BR1 | 404 | none |
| CW rocker | cwind.com | /sites/cwind/files/grb112b802br1.pdf (link from DigiKey page via WebFetch) | 200, 1-page maker drawing | cw_GRB112B802BR1/grb112b802br1.pdf (copy: datasheets/CW_GRB112B802BR1.pdf) |
| CW rocker | digikey.com | product page 2349683 via WebFetch | 200; no STEP listed, cutout 20.20 mm | none |
| Molex 43650-0300 | molex.com | /en-us/products/part-detail/436500300 (curl, then WebFetch) | curl 000 no response; WebFetch timeout | none |
| Molex | EasyEDA API C503478 + 3dmodel aca6fa2f... | 200 / 200 (OBJ) | easyeda_C503478/ |
| JST B2P-VH | jst-mfg.com | /product/detail_e.php?series=278 (WebFetch) | 200, XH series page, no VH | none |
| JST | jst-mfg.com | series=124,123,125 (guesses) | 200 stub pages, no CAD links | none |
| JST | jst-mfg.com | /product/pdf/eng/eVH.pdf | 200, identical to local datasheets/JST_VH.pdf (cmp) | jst_B2P-VH/eVH.pdf |
| JST | EasyEDA API C160315 + 3dmodel 0122b456... | 200 / 200 (OBJ) | easyeda_C160315/ |
| TE 1977066-1 | te.com | DDEController?...DocFormat=STEP | 403 Akamai Access Denied (not circumvented) | none |
| TE | te.com | /en/product-1977066-1.html | 403 | none |
| TE | EasyEDA API C2972219 + 3dmodel 4c08b1da... | 200 / 200 (OBJ) | easyeda_C2972219/ |
| Keystone 5015 | keyelco.com | /product.cfm/product_id/918 | 403 Cloudflare challenge (not circumvented) | none |
| Keystone 5015 | keyelco.com | /userAssets/file/M65p55.pdf (URL from search) | 200, 1 page (5015 and 5017 drawing) | keystone_5015/M65p55.pdf (copy: datasheets/Keystone_5015_M65p55.pdf) |
| Keystone 5010-5014 | WebSearch | no keyelco THT datasheet URL found; no keyelco STEP found | n/a | none |
| Keystone 5014 | EasyEDA API C238128 + 3dmodel 0d00f52e... | 200 / 200 (OBJ) | easyeda_C238128/ |
| Alps EC11E18244AU | tech.alps.com | /docs/datasheet/EC11E18244AU.pdf | 000 no response | none (local Alps_EC11E.pdf used, covers the series incl. both parts) |
| Alps | EasyEDA API C202365 + 3dmodel 98040a81... | 200 / 200 (OBJ) | easyeda_C202365/ |
| TYPE-C-31-M-12 | EasyEDA API C165948 + 3dmodel 617b05f9... | 200 / 200 (OBJ) | easyeda_C165948/ |
| PJ-307 | EasyEDA API C2939173 + 3dmodel fbf8285e... | 200 / 200 (OBJ) | easyeda_C2939173/ |
| EEHZA1E101XP | EasyEDA API C264047 + 3dmodel 6cb1ec57... | 200 / 200 (OBJ) | easyeda_C264047/ |
| EasyEDA STEP endpoint | modules.easyeda.com/qAxj6KHrDKw4blvomvyg/<uuid>, 8 uuids; also `.step` suffix and `?type=step` variants on one uuid | 404 NoSuchKey (the `?type=step` variant returned the same OBJ, 200) | `*.step-endpoint-404.xml` stubs |
| Panasonic | panasonic.com | not attempted; local Panasonic_EEH-ZA PDF used | n/a |
| Coilcraft XAL7070 | coilcraft.com | /en-us/products/.../xal7070-222/ and /en-us/models/mechanical/ | 403 both | none |
| XAL7070 | EasyEDA API C3911470 (BOM LCSC id) | 200 but record has no 3D model | none |
| Sunlord MWSA1265S | sunlordinc.com/ | 200 homepage only, no PDF path found | none |
| Sunlord | lcsc.com/product-detail/C7245133.html and wmsc.lcsc.com detail | 200 HTML with no datasheet link; API result null | none |
| Sunlord | EasyEDA API C7245133 + 3dmodel cf9d2492... | 200 / 200 (OBJ), but the model is for a different part (`125CDMCCDS-4R7MC`) | easyeda_C7245133/ |
| Bourns SRN6045TA | bourns.com series page | 403 | none |
| Bourns | EasyEDA API C1332316 (SRN6045TA-2R2Y) + 3dmodel 45a643b4... | 200 / 200 (OBJ) | easyeda_C1332316/ |
| Microchip BM83 | microchip.com/en-us/product/BM83 | 403 | none |
| Headers | EasyEDA API C54110162 | 200 `{"success":false,"code":404}` (not in EasyEDA) | none |
| Headers | wmsc.lcsc.com product detail C124378, C54110162 (gave pdfUrl) | 200 x2 | JSON only (scratchpad) |
| Headers | datasheet.lcsc.com PDFs | 200 x2 | lcsc_pin_headers/*.pdf (copies in datasheets/) |
| Headers | EasyEDA API C124378 + 3dmodel 62d1dd00... | 200 / 200 (OBJ) | easyeda_C124378/ |
| Molicel P45B | molicel.com/wp-content/uploads/INR21700P45B-V4-80091.pdf (guess) | 404 | none (deleted) |
| Molicel | molicel.com/wp-content/uploads/INR21700P45B_1.2_Product-Data-Sheet-of-INR-21700-P45B-80109.pdf (from search) | 200, 1 page | molicel_P45B/INR21700P45B_1.2_datasheet.pdf (copy: datasheets/Molicel_INR21700-P45B_v1.2.pdf) |
| Samsung 50S | local datasheets/Samsung_INR21700-50S_SDI_introduction_2021.pdf | read | n/a |
| Ruthex RX-M3x5.7 | WebSearch only (3djake spec table); ruthex.de not fetched | snippet only | none |
| Wurth 970100321, 971120321 | we-online.com/components/products/datasheet/<mpn>.pdf | 403 x2 | none (error stubs deleted) |
| Wurth | WebSearch (element14, RS, Digikey, Buerklin listings) | spec text only | none |
| LCSC C5884429 (KCD1 rocker) | EasyEDA API | 200 `{"code":404}` | none |

## (b) Dimension blocks

### 1. Tang Band W3-2052SC (Parts Express 299-572, "RBM neodymium subwoofer, 4 ohm", brand "Factory Buyouts")
No maker drawing, spec sheet or STEP exists online (the Tang Band site does not list the part; the Parts Express spec PDF URL returns empty). Numbers below are from the Parts Express item JSON (`parts-express_299-572_api_items.json`) and from four product photos (`img_*.jpg`; photo values are rough, plus or minus 1.5 mm, perspective not corrected).

| Item | Value | Basis |
|---|---|---|
| Mounting holes | 4 | PE JSON `custitem_pe_no_mounting_holes` |
| Bolt circle diameter | 3.8 in = 96.52 mm | PE JSON `custitem_pe_bolt_circle_diameter` |
| Overall outside "diameter" | 3.25 in = 82.55 mm | PE JSON; **the flange is a SQUARE with rounded corners, 82.55 mm across, not a round flange** (photos ALT_1, HR_0). 4 holes sit in the corners. For a square flange the 96.52 bolt circle gives hole centres 68.25 mm apart on x and y |
| Baffle cutout | 3.0 in = 76.2 mm | PE JSON `baffle_cutout_diameter` |
| Overall depth | 1.75 in = 44.45 mm | PE JSON `custitem_pe_depth` (baseline unknown: probably front face to back of magnet) |
| Hole diameter | about 3.0-3.5 mm | photo estimate only (inner bore about 50-60 px at 16.2 px/mm). UNVERIFIED |
| Flange/frame block | square box about 82.55 mm wide, about 17 mm tall including a black foam gasket of about 3-4 mm on the front face | photo ALT_2 side view (16.1 px/mm). UNVERIFIED |
| Frame below box | open ribbed basket, about 74-75 mm wide, windows between ribs | photo ALT_2 |
| Magnet/motor cup | cylinder, about 37-38 mm diameter, about 16 mm tall, flat closed back with a small centre vent hole; 3 mm black cup | photo ALT_2, ALT_0. UNVERIFIED |
| Terminals | no solder terminals on the frame: a 2-pin white JST-PH-style plug on a twisted red/black pigtail (about 100 mm, length unverified) soldered to a tinsel pad on one frame rib | photos |
| Cone aperture | circular, about 65 mm (surround outer edge) | photo ALT_1 |
| Other | Xmax 5 mm, VC dia 1.0 in, Fs 59 Hz, Qts 0.49, Vas 0.021 ft3, Sd 28.8 cm2, 0.55 lb | PE JSON |
| Stock note | PE shows `isinstock` true, qty 257, but the out-of-stock message says "no longer available" (factory buyout); verify before ordering | PE JSON |

CRITICAL NUMBERS: 4 holes, bolt circle 96.52 mm, flange 82.55 mm square, cutout 76.2 mm, depth 44.45 mm are published by the seller. Hole diameter, flange thickness and magnet diameter are NOT published; only photo estimates exist. The old assumption "77 mm bolt circle" in the handover is contradicted by the seller's 3.8 in = 96.5 mm.

### 2. CW Industries GRB112B802BR1 (drawing `cw_GRB112B802BR1/grb112b802br1.pdf`, page 1, unit mm, general tolerance +-0.3)
| Item | Value | Tolerance |
|---|---|---|
| Panel cutout | round Ø20.2 | +0.2 / -0.1 |
| Anti-rotation notch (variant 1) | width 2.2, reaching 11.0 from the cutout centre (check the arrow on the drawing before cutting) | +0.1 / 0 |
| Variant 2 cutout | Ø20.2 with a flat to 19.0 (+0 / -0.2), 4.2 offset | |
| Panel thickness | 1.5 to 2.5 (variant 1); 0.7 to 2.5 (variant 2) | |
| Bezel / flange diameter | Ø25.00 | +-1.00 |
| Rocker diameter | Ø19.8 | +-0.3 |
| Skirt diameter above panel | Ø19.00 | +-0.3 |
| Height above panel | 10.7 +-0.2 (flat), 11.5 +-1.0 (rocked) | |
| Depth behind flange | 22.4 total to terminal tips (+-1); terminals protrude 8.3 +-0.5 below body | |
| Terminals | 3 quick-connect tabs, 4.8 +-0.1 wide, 0.8 +-0.03 thick, Ø2.2 +-0.2 hole, pitch 7.1 +-0.3, order 3-2-1 | |
| Ratings | 16 A 125 VAC, 10 A 250 VAC, 20 A 14 VDC, IP65, 3P SPST, red LED w/ resistor 12-14 VDC | |
Reading caveat: the 11.5 / 10.7 / 22.4 / 8.3 vertical dimension lines are ambiguous on the scan; render page 1 at 170 dpi and confirm which end each arrow touches. No STEP.

### 3. Molex 43650-0300 (LCSC C503478)
The local `datasheets/Molex_43650-0300_C503478.pdf` is NOT a Molex drawing: it is an LXWCONN generic drawing "H3000S14-XX, 3.0 mm right angle header" (units mm, tolerance X.XX +-0.25, 2 pages, 3-circuit PCB layout). Values for 3 circuits (page 1): pin pitch 3.00; DIM A (first to last pin) 6.00; DIM B (housing length) 12.65; housing height 9.90; pin 0.64 square; depth 4.37 (rear block); pin shoulder to pin tip 4.32 / 3.20 tail; PCB signal holes Ø1.02, post holes Ø3.00 at 4.32 mm from the pin row, outer posts 2.15 from the end (3P). EasyEDA model title "CONN-TH_3P-436500300". No Molex STEP.

### 4. JST B2P-VH(LF)(SN) (`datasheets/JST_VH.pdf`, page 3)
Pitch 3.96; B = 7.86 mm housing length; A = 3.96 pin span; housing height 8.5; depth 10.9 (from the rear edge to the mating front), post tail below board 3.7. No JST STEP (JST download page is form-gated).

### 5. TE 1977066-1 (`datasheets/TE_1977066-1_datasheet.pdf`, page 1, mm)
Body 4.50 x ~3.4 deep (side view 3.40 total / 0.85 + 2.55), body height 3.30, plunger Ø2.00 centred 1.70 above the pad plane, plunger overall (0.85 forward); terminals 2-0.65 + centre 0.50 wide, 3.00 pitch; two locating pegs Ø0.9; peg-to-peg 4.25 wide; land layout 5.00 x 3.20 (pad 1.20 x 0.90 outer, 1.80 x 0.60 inner). Tape pocket K0 4.2 (page 2). Actuation 160 +-50 gf, travel 0.20 +-0.10. Rating 50 mA 12 VDC. No TE STEP (403).

### 6. Keystone test points
- 5015 (page 1 of `keystone_5015/M65p55.pdf`, mm): 2.7 L x 1.0 W x 1.5 H, flat wire 0.25 thick, phosphor bronze silver plate; pad layout 3.4 x 1.8 (outer), pad 1.0. 1000/reel, 8 mm tape, 4 mm pitch.
- 5010-5014 THT multipurpose: no keyelco drawing downloaded. Distributor listing and EasyEDA record give OD 0.125 in = 3.17 mm, length 0.445 in = 11.3 mm, pin about 1.0-1.6 mm. See OBJ for 5014 below (model "TEST-TH_BD3.17-P1.87").

### 7. Alps EC11E18244AU (`datasheets/Alps_EC11E.pdf`, page 2 "Drawing No.2", unit mm)
EC11E18244AU and EC11E15244G1 are both Drawing No.2 in the product list (page 1): vertical, flat (D-cut) actuator, actuator length 20, detent torque 10 +-7 mN m, push switch with 0.5 mm travel. **Shaft length and type are identical.** They differ only in detents/pulses (36/18 vs 30/15). The project's `EC11E15244G1.step` shaft tip is at z = 24.49 (matches 24.5 on the drawing).
Drawing No.2: shaft tip 24.5 above the mounting plane (bushing 4.5 + 20 actuator), shaft Ø6 (+0 / -0.05), flat length 10 starting 7 from the bushing end, chamfer C1; body width 11.7, body height 7.5 max; pin pitch 5 (A, C, B), pin row 7.5 from centre; 3.5 pin length below board; switch pins D, E; PCB holes 5 x Ø1 at 12.5 +-0.05 pin-to-tab spacing, mounting tab slots 1.5 x 2.6 (+0.1/0), tolerance +-0.1.

### 8. Korean Hroparts TYPE-C-31-M-12 (C165948) and HOOYA PJ-307 (C2939173)
EasyEDA OBJ bounding boxes (section C) vs the project STEP: Type-C OBJ x +-4.47 (8.94), y -5.3..2.6 (7.9), z -0.85..3.25 (4.10) against project STEP 9.105 x 7.9 x 4.215; PJ-307 OBJ 14.2 x 12.01 x 8.5 against project 14.2 x 12.01 x 8.5 (identical size, origin differs: OBJ x -2.8..11.4, project x -9.05..5.15).

### 9. Panasonic EEHZA1E101XP (`datasheets/Panasonic_EEH-ZA_hybrid_polymer.pdf`, page 1 table)
Size code D8: D 6.3, L 7.7 +-0.3, A and B 6.6, H 7.8 max, I 2.6, W 0.65 +-0.1, P 1.8, K 0.35 +0.20/-0.15 (unit mm). EasyEDA OBJ: 7.8 x 6.6 x 7.75. No Panasonic STEP downloaded.

### 10. Inductors
- Coilcraft XAL7070-222MEC: page and STEP blocked (403). Search snippet only: 2.2 uH, DCR 6.3 mohm max, Isat 19.6 A, Irms 17.8 A. Project model height 7.0 (z 0..7), footprint 7.7 x 8.0 (UNVERIFIED against Coilcraft drawing). Not at LCSC (EasyEDA C3911470 has no 3D).
- Sunlord MWSA1265S-220MT: only a search snippet of a third-party copy of the series datasheet (13.45 +-0.35 x 12.6 +-0.3, 6.5 max). Not downloaded from Sunlord. Project STEP is 13.46 x 12.6 x 6.5. EasyEDA's model for C7245133 is a different part; do not use it.
- Bourns SRN6045TA: local PDF gives 6.0 +-0.3 square; project STEP height 4.2, EasyEDA OBJ 6.0 x 6.02 x 4.52 (2R2Y listed max 4.5 on the Bourns table; check the project model height, 4.2 vs 4.5 max).
- Microchip BM83SM1-00TA: page blocked (403). Project STEP: 15.0 x 32.0 x 2.51.

### 11. Pin headers
| Item | Ckmtw B-2100S04P-A110 (C124378) | XYECONN XY-MTP254-1X5 (C54110162) |
|---|---|---|
| Drawing | `lcsc_pin_headers/C124378_B-2100S04P-A110.pdf` p1 (drawing 210S-1*XP, 6.0/2.54/3.0) | `lcsc_pin_headers/C54110162_XY-MTP254-1X5.pdf` p1 |
| Pitch | 2.54 | 2.54 +-0.1 |
| Plastic height | 2.54 (nominal; implied 11.6 - 6.0 - 3.0 = 2.6) | 2.50 |
| Pin above plastic (mating) | 6.0 | 6.00 +-0.2 |
| Tail below board | 3.0 | 3.00 +-0.2 |
| Total pin length | 11.6 (ref) | 11.5 |
| Pin | 0.64 square +-0.02 | 0.64 square |
| Tolerance | X.X +-0.20; .XX +-0.10 | .X +-0.3 ... .XXX +-0.1 |
| PCB hole | n/a | Ø1.02, PCB tolerance +-0.05 |
| Dimension A/B table | n/a | 1x5: A 10.16, B 12.70 |

### 12. Cells and hardware
- Molicel INR21700-P45B (`molicel_P45B/...datasheet.pdf`, page 1, version 1.2): diameter 21.55 max, height 70.15 max, weight 70 g max. The datasheet has NO cap, vent or button dimensions. The product page (per search) says 21.6 x 70.2 max (older). One third-party copy says 21.40 +-0.15 x 70.00 +-0.15 (unverified, not downloaded).
- Samsung INR21700-50S (local PDF, page 2): diameter 21.25 max, height 70.62 max. Cap size not given.
- Ruthex RX-M3x5.7 (EAN 4260528721146, GE-M3x57-001): from a 3djake spec table (snippet, not a maker drawing): D1 4.6 (outside diameter at knurl), D2 3.9, D3 4.0 (installation hole), L 5.7, S min 1.6. Column mapping unconfirmed. Existing BOM says OD 4.6, hole 4.0, which matches.
- Wurth spacer, M3, 10 mm, F/F, 5.5 AF: MPN **970100321** (WA-SSTII, steel zinc; DigiKey 6174761; element14 2884518; RS 1768403/1768102). Wurth datasheet 403.
- Wurth stud, M3 M/F, 12 mm body, 6 mm male stud, 5.5 AF: **971120321** (WA-SSTIE; RS 1768061; DigiKey 6174625); RS "176-8061" is the stock number the brief called "1768061". Datasheet 403.
- ISO 4762 M3: standard values head Ø5.5, head height 3.0, hex 2.5 (not downloaded; standard).

## (c) EasyEDA OBJ bounding boxes and the project STEP boxes

OBJ values: vertex min/max in the file (mm). Origins are the EasyEDA component origin (pin 1 or body centre); z is up. All OBJ, none STEP, solid count not measurable (OBJ groups by material only).

| Part | OBJ file (under `easyeda_<id>/`) | x | y | z | Apparent origin |
|---|---|---|---|---|---|
| Molex 436500300 (C503478) | model_aca6fa2f...obj | -6.325..6.325 | -8.92..0.98 | -3.3..5.57 | centred on x, y 0 at pin row, body extends -y; posts to z -3.3 |
| JST B2P-VH (C160315) | model_0122b456...obj | -1.98..5.94 | -0.75..7.95 | -6.45..7.35 | pin 1 near x 0; axes differ from the project convention (OBJ is rotated, z-span 13.8 = 10.9 + 3.7 - 0.8) |
| TE 1977066-1 (C2972219) | model_4c08b1da...obj | -2.25..2.25 | -0.85..2.71 | -2.501..1.599 | centred on x; axis order differs (plunger along y); height 4.1 |
| Alps EC11E (C202365) | model_98040a81...obj | -6.289..6.289 | -7.6..7.1 | -3.5..24.5 | centred on shaft, pins to z -3.5, shaft tip z 24.5 |
| TYPE-C-31-M-12 (C165948) | model_617b05f9...obj | -4.47..4.47 | -5.3..2.6 | -0.85..3.251 | centred on x, shell towards -y |
| PJ-307 (C2939173) | model_fbf8285e...obj | -2.8..11.4 | -6.01..6.0 | -5.5..3.0 | x 0 at pin; body extends +x |
| EEHZA1E101XP (C264047) | model_6cb1ec57...obj | -3.9..3.9 | -3.3..3.3 | -0.05..7.7 | body centre, z 0 at seating plane |
| Ckmtw 1x4 (C124378) | model_62d1dd00...obj | -5.08..5.08 | -1.33..1.33 | -3.0..8.54 | centred on the row, z 0 at plastic bottom, tail to -3.0 |
| Keystone 5014 (C238128) | model_0d00f52e...obj | -1.585..1.585 | -1.58..1.58 | -3.17..8.111 | centred; OD 3.17, z span 11.28 |
| Bourns SRN6045TA-2R2Y (C1332316) | model_45a643b4...obj | -3.0..3.0 | -3.01..3.01 | -0.01..4.51 | centred, z 0 at seating plane |
| Sunlord C7245133 (wrong part) | model_cf9d2492...obj | -6.75..6.75 | -6.31..6.3 | -0.02..5.0 | do not use |

Project STEP files measured with freecadcmd 1.0 (`Part.read`, BoundBox, from `kicad-library/3d`):
| File | solids | x | y | z |
|---|---|---|---|---|
| EC11E15244G1.step | 1 | -0.869..15.571 | -9.139..4.139 | -3.855..24.492 |
| PJ-307.step | 1 | -9.05..5.15 | -6.005..6.005 | -3.0..5.5 |
| TYPE-C-31-M-12.step | 14 | -4.552..4.552 | -2.8..5.1 | -0.883..3.332 |
| JST_B3P-VH.step | 1 | -4.8..3.7 | -1.95..9.87 | -3.7..10.9 |
| L_Coilcraft_XAL7070-XXX.step | 1 | -3.85..3.85 | -4.0..4.0 | 0..7.0 |
| L_Sunlord_MWSA1265S.step | 3 | -6.73..6.73 | -6.3..6.3 | 0..6.5 |
| Bourns_SRN6045TA-2R2Y.step | 1 | -3.0..3.0 | -3.0..3.0 | 0..4.2 |
| BM83SM1-00TA.step | 77 | -7.5..7.5 | -10.013..21.987 | 5.407..7.917 |
Note: BM83 z range 5.4..7.9 means the project model floats 5.4 mm above z=0 (not at the seating plane); check against the footprint 3D offset.

## (d) UNFOUND
- Tang Band W3-2052SC: any maker drawing, spec sheet, STEP; hole diameter, flange thickness, magnet cup diameter and height, pigtail length/connector part (only seller specs and photo estimates).
- STEP for: Molex 43650-0300, JST B2P-VH(LF)(SN), TE 1977066-1, Keystone 5015 and 5010-5014, Alps EC11E18244AU, Hroparts TYPE-C-31-M-12, HOOYA PJ-307, Panasonic EEHZA1E101XP, Coilcraft XAL7070-222MEC, Sunlord MWSA1265S-220MT, Bourns SRN6045TA, Microchip BM83SM1-00TA, CW GRB112B802BR1, headers, Ruthex insert, Wurth spacers. (EasyEDA OBJ obtained for 10 of these; none for CW rocker, Keystone 5015, Coilcraft, Microchip, XYECONN header, Ruthex, Wurth.)
- Keystone 5010-5014 maker drawing (the 5015 page was found).
- Molex 43650-0300 genuine Molex drawing (local PDF is an LXWCONN equivalent; Molex site unreachable).
- Coilcraft XAL7070 datasheet drawing; Sunlord MWSA1265S-220MT datasheet from sunlordinc.com; Microchip BM83 mechanical drawing (local BM83 PDF not rechecked).
- Molicel P45B: cap/vent/button dimensions (not in the datasheet); Samsung 50S cap dimensions.
- Ruthex maker drawing (OD/hole/knurl column mapping unconfirmed); Wurth datasheets (403).
- CW GRB112B802BR1 STEP; clarity of the notch dimension and the vertical dimension arrows (see block 2).
