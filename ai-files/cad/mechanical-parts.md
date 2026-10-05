# Mechanical parts for the CAD model (2026-10-06)
Sources: web snapshots 2026-10-06; "UNVERIFIED" = not confirmed from a maker drawing. Only the PCB is estimated.

## 1. Front full-range drivers (x2) - Dayton Audio ND65-4 (Parts Express 290-204)
| Item | Value |
|---|---|
| Maker/MPN | Dayton Audio ND65-4, 2.5 in aluminium cone, 4 ohm; list US$31.99 (page gave no stock) |
| Drawing/datasheet | https://www.daytonaudio.com/images/resources/290-204-dayton-audio-nd65-4-specifications.pdf (saved in parts/) |
| Flange | 64 x 64 mm square (rounded corners), flange thickness about 5 mm (48 total - 43 behind flange) |
| Mounting | 4 holes dia 4.2 mm on 66 mm bolt circle at 45 deg (= 46.7 mm square pattern); baffle cutout dia 52 mm |
| Depth | 48 mm overall incl. terminals (43 mm behind flange face to terminal tops); magnet cup dia 52 mm. EXCEEDS the 35 mm hint; accept, or move the cabinet inner wall |
| Mass | about 0.18 kg (0.4 lb) |
| Electrical | Re 3.5, Le 0.44 mH, 15 W RMS / 30 W max, 83 dB, VC dia 19 mm |
| T/S | Fs 89.5 Hz, Qts 0.61, Vas 0.53 L, Sd 15.6 cm2, Xmax 3.5 mm |
| 3D | REAL STEP: parts/ND65_3D/ND65-4 and 8.step (also .stl .dwg). Origin: https://www.daytonaudio.com/images/resources/3D-Scans/ND65-4_and_8_3D_Files.zip, maker file dated 2025-11-20. FreeCAD check: 1 solid, 64.0 x 64.9 mm, Z -26..+22 (48 mm); front face at Z=+22, origin at driver axis |
Two side by side need 2 x 64 = 128 mm of width; fits in 163 mm. Needs a small sealed back volume each (Vas 0.53 L, so a 0.1-0.2 L chamber is acceptable for >150 Hz crossover).

## 2. Downward woofer - Tang Band W3-2052SC (Parts Express 299-572)
| Item | Value |
|---|---|
| Maker/MPN | Tang Band (Taiwan) W3-2052SC, 3 in RBM neodymium sub, 4 ohm; US$29.98 sale (MSRP 69.99), "in stock" at Parts Express |
| Drawing | NOT FOUND (no Tang Band PDF reachable). Dimensions below are from the Parts Express listing. Request the drawing from Tang Band/Parts Express before cutting |
| Flange | OD 3.25 in = 82.6 mm, round, 4 mounting holes (diameter/pattern UNVERIFIED; assume 4 x dia 3.5 on about 73 mm bolt circle until confirmed) |
| Cutout | listed as 3 in (76.2 mm). UNVERIFIED, plausible values are 70-76 mm |
| Depth | 1.75 in = 44.5 mm (meets <=45 mm). Magnet dia UNVERIFIED, assume about 40 mm neodymium |
| Mass | 0.55 lb = 0.25 kg |
| Electrical | 15 W RMS / 30 W max (below the 20 W target, but boost-limited ~15 W anyway: acceptable); 78.3 dB; 50-800 Hz |
| T/S | Fs 59 Hz, Qts 0.49, Vas 0.021 ft3 = 0.59 L, Xmax 5 mm, Sd 28.8 cm2. Suited to 0.4-0.6 L sealed |
| 3D | NO maker STEP found. A GrabCAD model of the sibling Tang Band W3-1876S exists (https://grabcad.com, not downloaded). Build PARAMETRIC stand-in: dia 82.6 flange x ~4 mm, cone/surround dia 70, basket dia 70 x 20, magnet dia 40 x 20, total depth 44.5 |
Alternative with real STEP: use a second ND65-4 pair is not recommended; the Dayton ND90-4 (3.5 in, Vas 1.06 L, Qts 0.63, Xmax 4 mm, cutout 85 mm) is 61 mm deep, too deep.

## 3. Passive radiator
SKIPPED. The 0.4-0.6 L sealed volume matches the W3-2052SC Vas; a radiator would add depth and area without clear gain.

## 4. Battery pack - LP1260100 (LiPol 10000 mAh 1S1P with PCM)
| Item | Value |
|---|---|
| Part | LP1260100, 3.7 V, 10 000 mAh min (10 050 typ), 37 Wh, about 200 g; resellers Soldered, Electrokit, Videotronics (price/stock UNVERIFIED, about US$25-45) |
| Size | 12 x 60 x 110 mm nominal (T x W x L). Cells of this type usually swell +0.5..1 mm and tolerance is typically +-0.5 T, +-1 W, +-2 L (UNVERIFIED): model 12.5 x 61 x 112 with 1 mm foam each side |
| Leads/connector | JST PHR-3 (PH 2.0 mm, 3 pos), lead position/length UNVERIFIED (assume 60-80 mm leads from a 60 mm end, PCM at that end, about 3 mm extra thickness) |
| NTC | 10 kohm 1% B3435 |
| FINDING (from a search-result datasheet extract) | Max continuous discharge 3 A, standard 1.5 A, PCM overcurrent trip 4-4.5 A (8-16 ms); max charge 2 A. A 4-ohm 15 W amp on 3.7 V draws about 5-8 A from the pack on peaks, so this pack will trip. Prefer a higher-rate pack or the 2P 21700 option (pack-switch report option C); for the CAD keep the same 12x60x110 envelope as placeholder |
| 3D | PARAMETRIC box (no STEP): 12 x 60 x 110 with 1 mm corner radius, plus lead stub and PHR-3 plug (10 x 6 x 7 mm) |

## 5. Hardware
| Item | Value | 3D |
|---|---|---|
| M3x10 socket cap, ISO 4762 | head dia 5.5, head height 3.0, hex 2.5, fully threaded (L=10, thread dia 3.0) | parametric |
| (alternative) ISO 7380 button M3x10 | head dia 5.7, height 1.65, hex 2.0 | parametric |
| M3 brass heat-set insert, e.g. Ruthex RX-M3x5.7 (MPN family unverified in this pass) | OD 4.6 (knurled, 5.0 max), length 5.7, ID M3, pilot hole dia 4.0-4.2 x 6.5 deep in the part; M3x10 screw leaves 10-5.7 = 4.3 mm for clamped plate thickness (clamp up to 4 mm incl. PCB 1.6) | parametric |
| M3 PCB standoff F/F brass hex, Wurth WA-SBRII family (M3, hex SW 5.5 typ, UNVERIFIED), lengths 5/6/8/10 mm | with M3x10 screws: PCB (1.6) + standoff 6 mm fits through-screw 10 mm with 2.4 mm thread in the far end; use 6 mm or 5 mm for screw-from-top, avoid 8-10 mm | parametric hex dia 5.5 x L, bore dia 3 |
| Feet gap 12 mm | Wurth 1768061 (RS stock, M3 male/female steel spacer stud, 12 mm body) with a 12 mm dia adhesive rubber disc 3 mm thick on the lower end; the stack is 12 mm of standoff + 3 mm pad = 15 mm gap. Rubber disc maker UNVERIFIED (3M Bumpon family) | parametric |
| Grille | perforated stainless or aluminium sheet 0.8 mm, 2.0 mm holes, 3.0 mm pitch staggered, about 40% open; paint black, backed by acoustic cloth. Cutout dia 52 each driver (front); woofer: cover with grille dia 90 in the base | parametric |

## 6. Existing KiCad 3D models (DesktopSpeaker-kicad/kicad-library/3d)
| Ref | Part | 3D present |
|---|---|---|
| J1 | USB-C TYPE-C-31-M-12 | YES TYPE-C-31-M-12.step |
| J2, J3 | PJ-307 3.5 mm jack | YES PJ-307.step |
| J5 | Molex 43650-0300 Micro-Fit | NO (footprint only; plan.md says no STEP) |
| J9, J10, J11 | JST B2P-VH (2 pos) | NO (only JST_B3P-VH.step for the 3-pos; build 2-pos parametric, pitch 3.96) |
| J4 | PD_SERVICE_HDR | NO (PinHeader 1x04 STEP is similar) |
Present: all ICs, caps, inductors (XFL4015, XAL7070, MWSA1265S, SRN6045), crystal, STM32G071RB, TAS5825M, TPS61088, etc. Missing: J5, J9-J11, SW100/SW101, PD_C_0402.

## Real STEP vs parametric summary
Real: ND65-4 (maker STEP), KiCad boards' USB-C, PJ-307 jacks, all ICs. Parametric: W3-2052SC woofer, battery pack, M3 hardware, standoffs/feet, grille, J5/J9-J11, PCB (estimated outline).
Downloaded files: parts/ND65_3D/*, parts/ND65-4_and_8_3D_Files.zip, parts/290-204-dayton-audio-nd65-4-specifications.pdf (plus nd65pg-1.png render).
