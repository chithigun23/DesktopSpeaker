# Hardware and consumables buy list (one unit + second-unit column), 2026-10-12

Everything needed to build one complete DesktopSpeaker that is NOT on `bom/DesktopSpeaker_JLC_BOM.csv` (SW101 is excluded from that BOM and is listed here). Machine-readable copy: `bom/hardware-buy-list.csv` (same lines, plus category, price status and URL).

**All prices and stock figures are snapshots read on 2026-10-12 (some from search-result snippets of undated pages). They are not quotes. Re-check every line at order time. Shipping, GST/import duty and currency fees are not included.** Digi-Key, LCSC, Parts Express and Tag-Connect prices are USD; Australian stores are AUD (Core and Jaycar figures include GST). Overall totals convert USD at an ASSUMED 1.50 AUD/USD (rate not looked up).

Sources read: `cad/mechanical-bom.md`, `cad/README.md` (v11-v11.2), `reports/cad-v11-print-ready.md`, `reports/sourcing-2026-10-12.md`, `reports/battery-pack-rfq.md`, `bom/jlc-assembly-notes.md`, HANDOVER lines on J4-J11, SW101, drivers and pack.

Price status: **confirmed** = price read from the store page/listing; **estimate** = no AUD/quote read, figure is a guess; **TBD** = no source or quote.


## Drivers

| # | Item | Qty (unit 1) | 2nd unit | Spec | Source / part number | Unit price | Line price | Stock / date | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Full-range driver Dayton Audio ND65-4 | 2 | 2 | 2.5 in aluminium cone, 4 ohm, 64 mm flange | [Parts Express (US)](https://www.parts-express.com/Dayton-Audio-ND65-4-2-1-2-Aluminum-Cone-Full-Range-Driver-290-204): 290-204 | USD 23.98 | USD 47.96 | 395 in stock (PE page via search, undated) | confirmed | Rear-mounted; needs 59.5 mm aperture (CAD has it). Solder tabs: no connectors needed at the driver. |
| 2 | Woofer Tang Band W3-2052SC | 1 | 1 | 3 in, 4 ohm, flange 82.55, cutout 76.2 | [Parts Express (US)](https://www.parts-express.com/Tang-Band-W3-2052SC-3-RBM-Neodymium-Subwoofer-4-Ohm-299-572): 299-572 | USD 29.98 | USD 29.98 | In stock, ships next business day (PE page 2026-10-12) | confirmed | Bolt circle/hole size UNVERIFIED; measure before fixing screws (CAD v11.2 conflict, clamp-ring fallback). |

## Acoustic

| # | Item | Qty (unit 1) | 2nd unit | Spec | Source / part number | Unit price | Line price | Stock / date | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 3 | Acoustic stuffing Acousta-Stuf polyfill | 1 bag (454 g) | 0 (bag covers) | polyester fill; about 30 g per unit (about 10 g woofer chamber, about 20 g main chamber, ASSUMED) | [Parts Express (US)](https://parts-express.com/Acousta-Stuf-Polyfill-1-lb.-Bag-260-317): 260-317 | USD 15.98 | USD 15.98 | In stock on product page; back-ordered on category page (conflicting snapshots) | confirmed | Tune by ear/measurement; one bag serves many units. |
| 4 | Acoustic grille cloth, black | 1 yd (70 in wide) | 0 (covers) | polyester, not flame retardant | [Parts Express (US)](https://www.parts-express.com/Speaker-Grill-Cloth-Black-Yard-70-Wide-260-335): 260-335 | USD 9.98 | USD 9.98 | Listed (category page 2026-10-12) | confirmed | Backs the front grille plate; Mellotone 260-332 is the flame-retardant option (USD 26.80/yd). |

## Switch

| # | Item | Qty (unit 1) | 2nd unit | Spec | Source / part number | Unit price | Line price | Stock / date | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 5 | Battery rocker SW101 CW Industries GRB112B802BR1 | 1 | 1 | SPST 20 A/14 VDC, 20.2 mm hole + key, 0.187 in fastons, panel 1.5-2.5 | [Digi-Key](https://www.digikey.com/en/products/detail/cw-industries/GRB112B802BR1/2349683): GRB112B802BR1 (DK 2349683) | USD 5.09 | USD 5.09 | 7,073 (reports/sourcing-2026-10-12.md) | confirmed | Not on the JLC BOM (panel part). LED unused on the 1S rail. |

## Connectors

| # | Item | Qty (unit 1) | 2nd unit | Spec | Source / part number | Unit price | Line price | Stock / date | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 6 | Faston receptacle 0.187 in, fully insulated, 22-18 AWG | 3 | 3 | tab 0.187 x 0.032 in (4.75 x 0.8), red | [Digi-Key](https://www.digikey.com/en/products/result?keywords=2-520194-2): TE 2-520194-2 (DK A27806-ND) | USD 0.35 | USD 1.05 | 58,881 (DK 2026-10-12) | confirmed | 2 used (in/out), 1 to insulate the unused lamp tab. Tab thickness 0.032 assumed from the CAD stand-in (4.8 x 0.8). Note 2-520184-2 is the 0.250 in size (wrong). |
| 7 | J5 mating housing Molex Micro-Fit 3.0 receptacle 3-way | 1 | 1 | 43645-0300, 3.0 mm pitch | [Digi-Key](https://www.digikey.com/en/products/result?keywords=0436450300): Molex 43645-0300 (DK WM1846-ND) | USD 0.42 | USD 0.42 | 115,485 (DK 2026-10-12) | confirmed | Pack RFQ asks the vendor to fit this housing; then this line is a spare/service lead. |
| 8 | Micro-Fit female crimp, 18 AWG, tin (PACK+/PACK-) | 1 strip of 100 | 0 (covers) | 43030-0038, 18 AWG, insulation OD <= 1.85 | [Digi-Key](https://www.digikey.com/en/products/detail/molex/0430300038/6098601): Molex 43030-0038 (DK WM13070CT-ND) | USD 8.19 | USD 8.19 | 583,204 (DK 2026-10-12); cut tape min 100 | confirmed | 43030-0007 does NOT take 18 AWG (20-24 AWG only). Check silicone wire OD against 1.85 mm (FIT0585 OD not stated). |
| 9 | Micro-Fit female crimp, 20-24 AWG, tin (NTC pin) | 2 | 1 | 43030-0007 | [Digi-Key](https://www.digikey.com/en/products/result?keywords=0430300007): Molex 43030-0007 (DK WM1837-ND) | USD 0.2 | USD 0.40 | 701,377 (DK 2026-10-12) | confirmed | For the 24 AWG NTC lead; a 26 AWG lead needs a 26-30 AWG terminal instead. |
| 10 | J9-J11 mating housing JST VHR-2N | 3 (MOQ 20) | 0 (MOQ covers) | VH 3.96 mm, 2-way | [LCSC](https://datasheet.lcsc.com/lcsc/2304140030_JST-VHR-2N_C157900.pdf): JST VHR-2N (LCSC C157900) | USD 0.031 | USD 0.62 | about 249,600 (LCSC listing via search 2026-10-12) | confirmed | Order with the JLC/LCSC batch. Digi-Key alternative 455-VHR-2N-ND USD 0.11 (90,067). |
| 11 | JST VH crimp SVH-21T-P1.1 | 6 (MOQ 100) | 0 (MOQ covers) | 18-22 AWG | [LCSC](https://www.lcsc.com/product-detail/C160349.html): JST SVH-21T-P1.1 (LCSC C160349) | USD 0.0282 | USD 2.82 | 247,900 (LCSC 2026-10-12) | confirmed | Digi-Key sells it on full reels only. |

## Wire

| # | Item | Qty (unit 1) | 2nd unit | Spec | Source / part number | Unit price | Line price | Stock / date | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 12 | Speaker wire 20 AWG figure-8 | 1 m | 1 m | 2 x 20/0.18; drivers 2 x about 0.25 m + woofer about 0.15 m (J11 lead through the grommet) | [Core Electronics (AU)](https://core-electronics.com.au/20-awg-figure-8-speaker-cable-per-metre.html): AW2116 | AUD 1.7 | AUD 1.70 | 127 (Core 2026-10-12) | confirmed | Jaycar WB1704 (21 AWG, A$0.80/m) is an alternative. |
| 13 | Silicone wire 18 AWG, 1 m red + 1 m black | 1 pack | 1 pack | 0.75 mm2 tinned, 22 A, -60..200 C | [Core Electronics (AU)](https://core-electronics.com.au/high-temperature-resistant-silicone-wire-18awg-0-75mm2-1m-red-black.html): DFRobot FIT0585 | AUD 5.28 | AUD 5.28 | 17 (Core 2026-10-12) | confirmed | Rocker leads (2 x about 0.12 m) and a spare/DIY pack lead. RFQ lead is 150 mm but the CAD harness route is about 230 mm: align before ordering the pack. |

## Mechanical

| # | Item | Qty (unit 1) | 2nd unit | Spec | Source / part number | Unit price | Line price | Stock / date | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 14 | Encoder knob (SW102) | 1 | 1 | 29 x 14 mm solid aluminium, grub screw, 1/4 in (6.35) bore | [Jaycar (AU)](https://www.jaycar.com.au/29mm-black-anodised-knob/p/HK7011): HK7011 | AUD 10.95 | AUD 10.95 | Available for delivery (Jaycar category page 2026-10-12) | confirmed | ASSUMED fit: 6.35 bore on the 6 mm D shaft with the grub screw on the flat (0.35 mm offset). 29 mm in the 36 mm dish (3.5 mm radial gap). No 30 mm 6 mm-D knob found in AU stock; UK alternative Cliff CL172989 (30 x 13, 6 mm set screw, GBP 7.01, Maplin Pro). |
| 15 | Heat-set insert M3 x 5.7, OD 4.6, hole 4.0 | 1 bag of 100 | 0 (38+38 = 76) | brass, 38 per unit (34 screws + 4 feet) | [RS Australia](https://ie.rs-online.com/web/p/products/2040616): RS PRO 204-0616 | AUD 30 | AUD 30.00 | AUD price/stock NOT read (RS AU blocks fetch); IE price EUR 17.39 ex VAT per 100 | estimate | AUD figure is an estimate. Confirmed but expensive fallback: Amazon AU ruthex GE-M3x57-001 A$76.59 in stock (2026-10-12); 3DJake EUR 7.49 + EUR 40.49 DHL to AU. |
| 16 | Socket cap screw M3 x 10, 316 stainless | 1 pack of 50 | 0 (23+23 = 46) | ISO 4762 type; 23 per unit (8 drivers + 4 woofer + 11 lid) | [Miniature Bearings Australia](https://miniaturebearings.com.au/collections/screws-socket-cap-stainless): SC030M-010-C-SK-S6 | AUD 8.77 | AUD 8.77 | Available (store JSON 2026-10-12) | confirmed | Woofer screws may change (bolt circle unverified; M2.5 or clamp-ring fallback). |
| 17 | Socket cap screw M3 x 16, 304 stainless | 1 pack of 50 | 0 (covers) | 11 per unit (PCB H1-H9, HA1, HA2) | [Miniature Bearings Australia](https://miniaturebearings.com.au/collections/screws-socket-cap-stainless): SC030M-016-C-SK-S4 | AUD 7.68 | AUD 7.68 | Available (store JSON 2026-10-12) | confirmed | H8 sits under the knob dish floor: drive with a 2.5 mm ball-end key before the lid goes on. |
| 18 | Socket cap screw M3 x 6, 304 stainless (OPTIONAL) | 0 (8 if pads removed) | 0 | only if the 11 mm driver pads are removed (3 mm baffle) | [Miniature Bearings Australia](https://miniaturebearings.com.au/collections/screws-socket-cap-stainless): SC030M-006-C-SK-S4 (pack 100) | AUD 9.59 | AUD 0.00 | Available (store JSON 2026-10-12) | confirmed (optional, excluded) | Not needed for the v11.2 CAD (pads present). Excluded from subtotals. |
| 19 | Hex spacer M3 F/F 10 mm, 5.5 AF | 11 | 11 | steel zinc, WA-SSTII | [Digi-Key](https://www.digikey.com/en/products/result?keywords=970100321): Wurth 970100321 (DK 732-10541-ND) | USD 0.29 | USD 3.19 | 26,262 (DK 2026-10-12) | confirmed | PCB stack: roof z 57 -> 10 mm spacer -> PCB -> M3x16. |
| 20 | Feet stud M3 M/F, 12 mm body, 6 mm male | 4 | 4 | steel; = RS 176-8061 | [Digi-Key](https://www.digikey.com/en/products/result?keywords=1768061): Wurth 971120321 (DK, page search) | USD 0.48 | USD 1.92 | 3,120 (DK 2026-10-12) | confirmed | The brief's "Wurth 1768061" is the RS stock number 176-8061; the Wurth MPN is 971120321. |
| 21 | Rubber foot disc 12.7 dia x 3.5 | 4 | 4 | 3M Bumpon SJ5312 clear PU dome, adhesive | [element14 AU](https://my.element14.com/3m/sj-5312-clear/feet-protective-bumper-pu-3-5mm/dp/2674622): 3M SJ-5312 CLEAR (e14 2674622) | AUD 0.35 | AUD 1.40 | AUD not read; Farnell IE EUR 0.19, 2,270-2,763 in stock | estimate | 12.7 x 3.5 vs CAD 12 x 3: feet gap 15.5 instead of 15. Glue to the stud end (5.5 AF face is small; add CA/epoxy). |
| 22 | Nylon flat washer M3 (lid screw seal) | 11 | 11 | 3.2 x 8.0 x 0.8 nylon | [Digi-Key](https://www.digikey.com/en/products/result?keywords=nylon%20washer%20M3%20flat): Essentra 16M03080080 | USD 0.1 | USD 1.10 | 30,563 (DK 2026-10-12) | confirmed | Plain nylon washer, not a bonded sealing washer (none found in AU stock); add a dab of sealant if the lid leaks. |
| 23 | Snap bushing / grommet, woofer leads | 2 | 1 | Heyco 2000: 0.250 in (6.35) hole, panel <= 0.062 in (1.57), ID 0.140 in (3.56), PA66 black | [Digi-Key](https://azcus.digikey.com/en/products/detail/heyco-products-corporation/2000/15906424): Heyco 2000 (DK 3720-2000-ND) | USD 0.1 | USD 0.20 | 265,521 (DK via search 2026-10-12) | confirmed | CAD hole is 6.0: ream to 6.35 or change the CAD to 6.35. Web is 1.6 (0.03 over the 1.57 rating, check fit). Seal leads with Sikaflex. |
| 24 | Hook-and-loop strap (battery) | 1 | 1 | 300 mm (210 loop + 60 hook); width NOT stated | [Core Electronics (AU)](https://core-electronics.com.au/hook-and-loop-strap-with-buckle.html): CE09642 | AUD 0.39 | AUD 0.39 | 399 (Core 2026-10-12) | confirmed | Cradle tunnels are 22 x 2.5 for a 20 mm strap: width and buckle thickness UNVERIFIED. Alternative VELCRO ONE-WRAP 20 mm roll (element14 3499736). |

## Seal

| # | Item | Qty (unit 1) | 2nd unit | Spec | Source / part number | Unit price | Line price | Stock / date | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 25 | Lid gasket cord, closed-cell EPDM sponge 3 mm | 1 roll of 10 m | 0 (covers) | 0.75 m per unit (outer loop 0.51 + chamber U 0.23); allow 1 m | [Essentra Components AU](https://ecompreprod.essentracomponents.com/en-au/p/round-cord-gasket/551809): 551809 | AUD 9.52 | AUD 9.52 | Price from a search snippet of the Essentra AU preprod site; stock not read | estimate | Verify on essentracomponents.com/en-au. Groove is 2 x 1.5: 3 mm sponge compresses about 50 %. |
| 26 | Driver/woofer gasket, closed-cell foam sheet 0.5-1 mm | 1 sheet about 200 x 200 | 0 (covers) | 2 x 63 mm square rings (aperture 59.5) + 1 ring 83 OD/76.2 ID | NOT SOURCED: - | TBD | TBD | - | TBD | No source confirmed. PE gasket tape 260-542 is 3.2 mm thick and 12.7 wide: too thick/wide for the 0.5 mm recess. Use 0.5-1 mm neoprene/EPDM/PE foam sheet with adhesive. |
| 27 | PU sealant/adhesive Sikaflex-11FC, black 300 ml | 1 | 0 (covers) | chamber insert to shell grooves, grille plates, grommet leads | [Bunnings (AU)](https://www.bunnings.com.au/sika-300ml-black-sikaflex-11fc-purform_p0628964): Sika 11FC black 300 ml (Bunnings p0628964) | AUD 27 | AUD 27.00 | Listed A$27 (Bunnings via search, undated) | confirmed | One PU product replaces separate epoxy/silicone. Needs a caulking gun. |

## Grille

| # | Item | Qty (unit 1) | 2nd unit | Spec | Source / part number | Unit price | Line price | Stock / date | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 28 | Front grille plate 163 x 100, 0.8 mm, 2 x 56 dia perforated zones (2.0 holes / 3.0 pitch) | 1 order (5 pcs) | 0 (5 pcs) | SPEC CHANGE PROPOSED: 0.8 mm black FR4 with NPTH holes instead of aluminium | [JLCPCB (quote)](https://jlcpcb.com): own Gerber (to be drawn) | USD 15 | USD 15.00 | Not quoted | estimate | Estimate only. Metal option: Metal Mesh (Sefar AU) 1 mm aluminium 2.0/3.5 pitch, custom quote; RS PRO 202-7877 0.6 mm sheet is A$189/3 sheets with 1.5 mm holes (rejected). |
| 29 | Woofer grille disc 90 dia, 0.8 mm, holes to 64 dia | 1 order (5 pcs) | 0 (5 pcs) | same process as the front plate | [JLCPCB (quote)](https://jlcpcb.com): own Gerber (to be drawn) | USD 10 | USD 10.00 | Not quoted | estimate | Estimate only. |

## Print

| # | Item | Qty (unit 1) | 2nd unit | Spec | Source / part number | Unit price | Line price | Stock / date | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 30 | Filament PETG 1.75 mm, black, 1 kg | 1 | 1 | (384 + 101 + 60) cm3 x 1.27 g/cm3 = 692 g, +20 % = 831 g | [Jaycar (AU)](https://jaycar-prod.australia-southeast1.gcp.storefrontcloud.io/1-75mm-black-esun-petg-filament-1kg-roll/p/TL4465): eSUN PETG TL4465 | AUD 39.95 | AUD 39.95 | Listed A$39.95 (Jaycar via search, undated) | confirmed | STL volumes treated as solid (conservative). 831 g leaves little margin for a failed print. ASA is the heat/UV alternative. |

## Battery

| # | Item | Qty (unit 1) | 2nd unit | Spec | Source / part number | Unit price | Line price | Stock / date | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 31 | 1S2P 21700 pack, 10 Ah, PCM >= 10 A, 10k NTC (B 3435), Micro-Fit 43645-0300 lead | 1 | 1 | max 73 x 44 x 22 mm; see reports/battery-pack-rfq.md | [RFQ: Keeppower / CM Batteries](https://cmbatteries.com/project/1s2p-battery-pack/): quote | TBD | TBD | No price; quote needed | TBD | PLACEHOLDER: not in any subtotal. UN38.3 shipping to AU not confirmed. |
| 32 | Spare NTC 103AT-2 (10k, B 3435) | 1 | 1 | Semitec 103AT-2 | [Digi-Key](https://www.digikey.com/en/products/result?keywords=103AT-2): 4316-103AT-2-ND | USD 0.68 | USD 0.68 | 5,077 (DK 2026-10-12) | confirmed | For bench testing of the TS network or a DIY pack. |

## Tools

| # | Item | Qty (unit 1) | 2nd unit | Spec | Source / part number | Unit price | Line price | Stock / date | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 33 | ST-LINK/V3 MINIE debugger | 1 | 0 | STDC14 output, USB-C | [Digi-Key](https://www.digikey.com/en/products/result?keywords=STLINK-V3MINIE): STLINK-V3MINIE (DK 497-STLINK-V3MINIE-ND) | USD 25.51 | USD 25.51 | 3,490 (DK 2026-10-12) | confirmed | One per workbench, not per unit. |
| 34 | Tag-Connect cable for J7 (legged), STDC14 | 1 | 0 | TC2030 6-pin legged to 14-pin STDC14 (SWD + SWO) | [Tag-Connect (direct)](https://www.tag-connect.com/product/tc2030-ctx-stdc14-for-use-with-stm32-processors-with-stlink-v3): TC2030-CTX-STDC14 | USD 43 | USD 43.00 | Price from tag-connect.com via search; stock not read | confirmed | Replaces the brief's TC2030-IDC-NL: J7 is the legged footprint and the IDC cable would need a separate adapter to the V3MINIE. Digi-Key search found no TC2030-IDC-NL. |
| 35 | USB-I2C/UART adapter, 3.3 V (J4 STUSB4500 NVM, J8 BM83 UART) | 1 | 0 | Adafruit MCP2221A breakout, USB-C | [Core Electronics (AU)](https://core-electronics.com.au/adafruit-mcp2221a-breakout-general-purpose-usb-to-gpio-adc-i2c-stemma-qt-qwiic.html): ADA4471 | AUD 12.3 | AUD 12.30 | OUT OF STOCK on the product page (2026-10-12) | confirmed | UNVERIFIED that MCP2221A UART speed suits isUpdate/Config Tool; a CP2102 3.3 V module is the fallback for J8. |
| 36 | Female-female jumper wires 20 cm, 40 pcs | 1 | 0 | 2.54 mm Dupont for J4/J6/J8 | [Core Electronics (AU)](https://core-electronics.com.au/solderless-breadboard-jumper-cable-wires-female-female-40-pieces.html): CE05098 | AUD 3.95 | AUD 3.95 | Listed (Core via search 2026-10-12) | confirmed |  |
| 37 | USB-C PD tester (PDO/contract readout, up to 240 W EPR) | 1 | 0 | FNIRSI FNB-C2 | [Core Electronics (AU)](https://core-electronics.com.au/test-equipment/usb-meters.html): CE11101 | AUD 58.49 | AUD 58.49 | Listed A$58.49 (Core via search, stock not read) | confirmed | Cheaper V/I-only option: Adafruit ADA6271 A$28.05. |
| 38 | Heat-set insert tip, Hakko T18 (OPTIONAL) | 0 | 0 | M3 / #4-40 | [Core Electronics (AU)](https://core-electronics.com.au/heat-set-insert-for-soldering-irons-4-40-m3-inserts.html): ADA4239 | AUD 22.2 | AUD 0.00 | Listed (Core via search) | confirmed (optional, excluded) | Only if the iron takes Hakko T18 tips. Excluded from subtotals. |
| 39 | Crimp tool for Micro-Fit and VH open-barrel (OPTIONAL) | 0 | 0 | open-barrel ratchet crimper, 18-24 AWG | user choice: - | TBD | TBD | - | TBD (optional, excluded) | Not priced. Avoid by having the pack vendor terminate J5 and by soldering/ordering pre-crimped VH leads. |

## Subtotals per source (unit 1 order; second-unit extra)

| Source | Currency | Confirmed, unit 1 | Confirmed, 2nd-unit extra | Estimate, unit 1 | Estimate, 2nd-unit extra |
|---|---|---|---|---|---|
| Parts Express (US) | USD | 103.90 | 77.94 | 0.00 | 0.00 |
| Digi-Key | USD | 47.75 | 13.75 | 0.00 | 0.00 |
| LCSC | USD | 3.44 | 0.00 | 0.00 | 0.00 |
| Core Electronics (AU) | AUD | 82.11 | 7.37 | 0.00 | 0.00 |
| Jaycar (AU) | AUD | 50.90 | 50.90 | 0.00 | 0.00 |
| RS Australia | AUD | 0.00 | 0.00 | 30.00 | 0.00 |
| Miniature Bearings Australia | AUD | 16.45 | 0.00 | 0.00 | 0.00 |
| element14 AU | AUD | 0.00 | 0.00 | 1.40 | 1.40 |
| Essentra Components AU | AUD | 0.00 | 0.00 | 9.52 | 0.00 |
| Bunnings (AU) | AUD | 27.00 | 0.00 | 0.00 | 0.00 |
| JLCPCB (quote) | USD | 0.00 | 0.00 | 25.00 | 0.00 |
| Tag-Connect (direct) | USD | 43.00 | 0.00 | 0.00 | 0.00 |

- **Overall, unit 1, confirmed prices: about A$473.59** (A$296.09 build parts + A$177.50 one-off tools: ST-Link, Tag-Connect cable, USB adapter, jumpers, PD tester).
- Plus estimates (inserts, rubber feet, gasket cord, two grille orders): about A$78.42. **Unit 1 total including estimates: about A$552.01.**
- Second unit extra (drivers, rocker, knob, filament, small parts not covered by packs): about A$197.20.
- **Not included anywhere:** the battery pack (RFQ, no price), the driver/woofer gasket foam sheet (no source; guess A$10), optional lines (M3x6, insert tip, crimp tool), shipping (Parts Express and Tag-Connect ship from the US; Digi-Key/LCSC international shipping thresholds not checked), and the JLC PCB assembly itself. This is a partial cost, not a complete product cost.

## Lines without a confirmed source or price

- Heat-set insert M3 x 5.7, OD 4.6, hole 4.0: estimate (AUD figure is an estimate. Confirmed but expensive fallback: Amazon AU ruthex GE-M3x57-001 A$76.59 in stock (2026-10-12); 3DJake EUR 7.49 + EUR 40.49 DHL to AU.)
- Rubber foot disc 12.7 dia x 3.5: estimate (12.7 x 3.5 vs CAD 12 x 3: feet gap 15.5 instead of 15. Glue to the stud end (5.5 AF face is small; add CA/epoxy).)
- Lid gasket cord, closed-cell EPDM sponge 3 mm: estimate (Verify on essentracomponents.com/en-au. Groove is 2 x 1.5: 3 mm sponge compresses about 50 %.)
- Driver/woofer gasket, closed-cell foam sheet 0.5-1 mm: TBD (No source confirmed. PE gasket tape 260-542 is 3.2 mm thick and 12.7 wide: too thick/wide for the 0.5 mm recess. Use 0.5-1 mm neoprene/EPDM/PE foam sheet with adhesive.)
- Front grille plate 163 x 100, 0.8 mm, 2 x 56 dia perforated zones (2.0 holes / 3.0 pitch): estimate (Estimate only. Metal option: Metal Mesh (Sefar AU) 1 mm aluminium 2.0/3.5 pitch, custom quote; RS PRO 202-7877 0.6 mm sheet is A$189/3 sheets with 1.5 mm holes (rejected).)
- Woofer grille disc 90 dia, 0.8 mm, holes to 64 dia: estimate (Estimate only.)
- 1S2P 21700 pack, 10 Ah, PCM >= 10 A, 10k NTC (B 3435), Micro-Fit 43645-0300 lead: TBD (PLACEHOLDER: not in any subtotal. UN38.3 shipping to AU not confirmed.)
- Out of stock at the chosen store: MCP2221A breakout (Core ADA4471).

## Assumptions and design points found while sourcing

- Knob: no 30 mm knob with a 6 mm D bore found in AU stock. Chosen Jaycar HK7011 (29 x 14, grub screw, 6.35 bore) on the 6 mm D shaft with the screw on the flat. Height 14 matches the CAD stand-in. UK option Cliff CL172989 (30 x 13, 6 mm grub screw).
- Grommet: Heyco 2000 needs a 6.35 mm (1/4 in) hole and a panel up to 1.57 mm. The CAD hole is 6.0 mm and the web 1.6 mm: change the CAD hole to 6.35 or ream it.
- Micro-Fit crimps: 43030-0007 is 20-24 AWG only. PACK+/PACK- 18 AWG needs 43030-0038 (cut tape, minimum 100). Pin 2 (NTC, 24 AWG) can use 43030-0007.
- Pack lead length: the RFQ asks for 150 mm leads, but `mechanical-bom.md` routes the J5 harness about 230 mm (side pocket, along the floor). Align the RFQ before sending.
- Tag-Connect: J7 is the legged TC2030 footprint and the STLINK-V3MINIE has an STDC14 connector, so TC2030-CTX-STDC14 plugs straight in. TC2030-IDC-NL would need an adapter and was not found at Digi-Key.
- J4 (STUSB4500 NVM, I2C) and J8 (BM83 UART test mode) need a 3.3 V USB adapter. MCP2221A covers I2C and UART. Its UART speed for isUpdate/Config Tool is unverified.
- Front/woofer grilles: proposed as 0.8 mm black FR4 boards with NPTH holes from JLCPCB (same order as the PCB). This replaces the aluminium/steel spec. A metal option needs a laser-cut quote (Metal Mesh/Sefar AU has 1 mm aluminium with 2.0 mm holes on a 3.5 mm pitch). The RS PRO 0.6 mm sheet was rejected (A$189 for 3, 1.5 mm holes).
- Driver gasket recesses are 0.5 mm deep and only about 1.75 mm wide at the flats. Speaker gasket tape (3.2 mm) does not fit, so a 0.5-1 mm foam sheet cut to shape is needed.
- Filament: 545 cm3 x 1.27 g/cm3 = 692 g, +20 % = 831 g, so one 1 kg roll per unit. Solid-volume basis (conservative).
- Stuffing: about 30 g per unit is assumed. Tune it by measurement.
- Feet: "Wurth 1768061" is RS stock number 176-8061 = Wurth 971120321 (M3 M/F, 12 mm body, 6 mm stud). Bumpon SJ5312 is 12.7 x 3.5 against the 12 x 3 spec, so the gap becomes 15.5 mm.
- Lid screw washers: plain nylon 3.2 x 8 x 0.8 mm. No bonded M3 sealing washer was found in stock.
- Rocker fastons: TE 2-520194-2, 0.187 x 0.032 in tab assumed from the CAD stand-in (4.8 x 0.8).
- Wire: 20 AWG figure-8 for the J9-J11 speaker leads (VH crimp 18-22 AWG). 18 AWG silicone for the rocker leads. The silicone wire OD must be <= 1.85 mm for Micro-Fit 18 AWG crimps (not stated).
