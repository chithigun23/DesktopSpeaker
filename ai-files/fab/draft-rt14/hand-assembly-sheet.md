# Hand-assembly placement sheet (DRAFT, RT-14)

DRAFT for the routed board RT-14; part positions do not change in the remaining GUI copper work, so the order holds for the final board (regenerate with `scripts/make_ha_sheet.py` after `regen_final.sh` to be sure). Process (owner, 2026-11-01): one 0.10 mm stainless stencil (laser cut, electropolished), leaded paste (assume SnPb, liquidus about 183 C), tweezers, large hotplate, iron/hot air for rework. All SMD parts are on F.Cu; B.Cu carries no parts, so the board lies flat on the plate.

Heights are the 3D-model heights from `ai-files/cad/models-v13/accuracy-table.csv` (datasheet-checked unless marked there as unverified).

## 0. Before printing

- Stencil check result (`stencil/stencil-report.md`): 1085 apertures, 0 fail area ratio 0.66 / aspect 1.5 at 0.10 mm. Exposed pads outside the windowing rules: U6.33 (coverage 100 % outside 50-75 %; 16 open via holes under paste), D6.7 (coverage 87 % outside 50-75 %; web 0.20 mm < 0.25), Q103.9 (coverage 76 % outside 50-75 %; web 0.20 mm < 0.25; pane side 0.30 mm < 0.5), U11.39 (web 0.20 mm < 0.25), U11.40 (coverage 79 % outside 50-75 %; web 0.21 mm < 0.25), U10.17 (coverage 100 % outside 50-75 %), U5.9 (coverage 100 % outside 50-75 %), U25.21 (coverage 100 % outside 50-75 %; 8 open via holes under paste), U7.33 (coverage 100 % outside 50-75 %; 16 open via holes under paste), U1.56 (coverage 100 % outside 50-75 %).
- The stencil as exported prints full paste on the U6/U7 (16 open vias each) and U25 (8 open vias) exposed pads: expect solder to wick into the vias and some voiding. Either order the stencil after a paste-only footprint fix (windowed panes between the vias, 50-75 %, no copper change) or reduce by hand: cover part of those three apertures with Kapton before printing.
- 22 test points TP1-TP22 (Keystone 5015 SMD loops) are not populated, but their 3.4 x 1.8 mm pads get paste: harmless solder bumps, or tape their apertures.
- Print once on a spare board and check registration through the openings (pad edges visible = misaligned).

## 1. Tight pairs first (courtyard gap < 0.20 mm)

Place these before their neighbours close them in. **C215 and C212 (0.14 mm apart) go first, before U24 and Y200.**

| pair | courtyard gap (mm) | tier need (mm) | note |
|---|---|---|---|
| U10 - C243 | 0.000 | 0.25 | U10 first (step 2.2), then the passive from its free side |
| C190 - R151 | 0.100 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| C314 - C270 | 0.110 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| U15 - C190 | 0.115 | 0.25 | U15 first (step 2.2), then the passive from its free side |
| L201 - C271 | 0.124 | 1.50 | passive first, then L201 (later step); check the gap before reflow |
| R252 - U25 | 0.125 | 0.25 | U25 first (step 2.2), then the passive from its free side |
| C274 - C291 | 0.130 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| U22 - C222 | 0.138 | 0.25 | passive first, then U22 (later step); check the gap before reflow |
| C215 - U24 | 0.138 | 0.25 | C215 and C212 first (step 2.1), then U24 and Y200 |
| C280 - C271 | 0.140 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| U4 - C103 | 0.140 | 0.25 | U4 first (step 2.2), then the passive from its free side |
| C284 - C283 | 0.140 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| C277 - C292 | 0.140 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| C215 - C212 | 0.140 | 0.40 | C215 and C212 first (step 2.1), then U24 and Y200 |
| C190 - C154 | 0.140 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| C270 - C290 | 0.140 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| R140 - C142 | 0.140 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| C316 - U19 | 0.150 | 0.25 | U19 first (step 2.2), then the passive from its free side |
| C284 - C278 | 0.150 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| C152 - C190 | 0.150 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| C100 - C103 | 0.150 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| C103 - C102 | 0.155 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| C173 - U2 | 0.156 | 0.25 | U2 first (step 2.2), then the passive from its free side |
| R151 - R150 | 0.160 | 0.25 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| U15 - C152 | 0.165 | 0.25 | U15 first (step 2.2), then the passive from its free side |
| C120 - U5 | 0.165 | 0.25 | U5 first (step 2.2), then the passive from its free side |
| C191 - U1 | 0.170 | 0.25 | passive first, then U1 (later step); check the gap before reflow |
| C182 - U11 | 0.170 | 0.25 | U11 first (step 2.2), then the passive from its free side |
| C193 - U1 | 0.170 | 0.25 | passive first, then U1 (later step); check the gap before reflow |
| U11 - C183 | 0.170 | 0.25 | U11 first (step 2.2), then the passive from its free side |
| C190 - R150 | 0.170 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| C192 - U1 | 0.170 | 0.25 | passive first, then U1 (later step); check the gap before reflow |
| C269 - R251 | 0.180 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| R152 - L3 | 0.180 | 0.40 | passive first, then L3 (later step); check the gap before reflow |
| C262 - L200 | 0.185 | 1.50 | passive first, then L200 (later step); check the gap before reflow |
| C172 - U2 | 0.186 | 0.25 | U2 first (step 2.2), then the passive from its free side |
| C100 - C312 | 0.190 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| C226 - C213 | 0.190 | 0.40 | passive pair: place both in one sitting, push apart with tweezers before reflow |
| C171 - U2 | 0.196 | 0.25 | U2 first (step 2.2), then the passive from its free side |
| U2 - C170 | 0.196 | 0.25 | U2 first (step 2.2), then the passive from its free side |

## 2. SMD placement order (one reflow)

| step | group | parts |
|---|---|---|
| 2.1 | tight pair at U24/Y200 | C215, C212 |
| 2.2 | fine-pitch and exposed-pad ICs (align under magnification; pin 1 as on the silk) | D1, D6, Q103, U2, U3, U4, U5, U6, U7, U8, U9, U10, U11, U14, U15, U19, U20, U24, U25 |
| 2.3 | 0402 passives (196), region by region | C103, C110, C120, C122, C123, C124, C125, C126, C130, C131, C132, C160, C162, C170, C171, C172, C173, C174, C177, C178, C182, C183, C191, C192, C193, C200, C201, C202, C203, C204, C205, C206, C207, C208, C209, C210, C211, C213, C217, C219, C220, C221, C222, C224, C225, C226, C227, C230, C231, C232, C233, C234, C235, C237, C238, C239, C240, C241, C243, C244, C245, C246, C260, C266, C267, C268, C269, C276, C278, C281, C282, C283, C284, C285, C286, C287, C288, C289, C291, C294, C295, C296, C297, C298, C299, C300, C301, C308, C309, C310, C311, C312, C313, C314, FB200, R10, R11, R12, R13, R14, R15, R16, R17, R18, R100, R101, R102, R103, R106, R107, R108, R109, R110, R111, R112, R113, R120, R121, R122, R124, R125, R126, R127, R140, R141, R142, R150, R151, R152, R153, R154, R160, R170, R171, R172, R173, R174, R175, R176, R180, R181, R182, R183, R184, R185, R186, R187, R200, R201, R202, R203, R204, R205, R206, R207, R208, R209, R210, R211, R212, R220, R221, R222, R223, R224, R225, R226, R227, R228, R229, R230, R231, R232, R233, R234, R235, R236, R237, R238, R239, R240, R241, R242, R243, R244, R250, R251, R252, R253, R254, R255, R257, R258, R259, R261, R262 |
| 2.4 | 0805/1206 passives (59) | C2, C5, C6, C100, C101, C102, C104, C105, C106, C107, C108, C109, C111, C112, C140, C141, C142, C150, C152, C153, C154, C161, C175, C176, C181, C184, C186, C187, C190, C194, C195, C214, C216, C218, C223, C236, C261, C262, C263, C264, C265, C270, C271, C272, C273, C274, C277, C279, C280, C290, C292, C293, C302, C303, C304, C305, C306, C307, C316 |
| 2.5 | small discretes, crystals, SOT/SOD/SC-70 and other low parts | D5, D7, D200, D201, Q100, Q101, Q102, Q104, U21, Y170, Y200 |
| 2.6 | medium-height parts (1.4-3 mm) | C315 (1.6), L2 (1.6), L3 (1.6), U1 (2.5), U12 (1.6), U13 (1.6), U16 (1.6), U17 (1.6), U22 (1.6), U23 (1.6) |
| 2.7 | tall SMD last (>= 3 mm) | J1 (3.3), SW100 (3.4), L1 (4.2), L201 (6.5), L202 (6.5), L203 (6.5), L204 (6.5), L205 (6.5), L206 (6.5), L200 (7.0), C275 (7.7) |

Notes:
- U1 (BM83 module, 2.5 mm) floats on paste: place it after the 0402s around it, press lightly, check castellation alignment after reflow and touch up with the iron and flux.
- J1 (USB-C, hybrid): the SMD signal pads reflow on paste; the 4 shell legs are PTH and are soldered with the iron after reflow.
- C275 (Panasonic EEH-ZA hybrid polymer, 7.7 mm) is an SMD reflow part on paste; confirm the reflow limit in its datasheet (the plate peak for SnPb paste is far below 260 C). It is the tallest SMD: place it last so the tweezers can still reach its neighbours.
- SW100 (TE 1977066-1): the two locating pegs sit 0.075 mm from the terminal lands by the TE land pattern (rule 20); JLC may nick the pad corners. Check the pad shapes on delivery; if nicked, the joint still forms (or trim the outer pads to 0.65 mm in the footprint before ordering, 0.175 mm gap).
- Via-in-pad on RT-14 (`via_in_pad.py`): via centre inside a non-exposed pad: C215.1, R185.2; via hole touching or within 0.15 mm of a same-net pad: U16.4, C274.1 (touching), R209.1, U2.10, U4.10, C102.1, C130.2, R153.2. Vias are tented, but inside a pad opening the hole is open: solder may wick; inspect these joints (or move the vias 0.2-0.3 mm in the GUI).

## 3. Reflow, inspect

- Hotplate: ramp <= 2 C/s, soak, peak about 205-225 C for SnPb, watch the paste go shiny, then off the plate onto a heat-safe surface (hand-assembly research section 2).
- Inspect fine-pitch ICs for bridges (U4 0.4 mm pitch, U11, U6/U7, U3, U24, U2), tombstones on 0402s, and the C215/C212 pair.

## 4. Through-hole parts by iron (low to tall)

| part | height (mm) | note |
|---|---|---|
| J2 PJ-307 | 5.5 | audio jack, plastic |
| J3 PJ-307 | 5.5 | audio jack, plastic |
| J5 Molex_Micro-Fit_3.0_43650-0300_1x03_P3.0 | 5.6 | Micro-Fit pack connector |
| J4 PD_SERVICE_HDR | 8.5 |  |
| J6 PinHeader_1x04_P2.54mm_Vertical | 8.5 |  |
| J8 PinHeader_1x05_P2.54mm_Vertical | 8.5 |  |
| J9 JST_B2P_VH_1x02_P3.96mm_Vertical | 10.9 | speaker VH |
| J10 JST_B2P_VH_1x02_P3.96mm_Vertical | 10.9 | speaker VH |
| J11 JST_B2P_VH_1x02_P3.96mm_Vertical | 10.9 | woofer VH |
| SW102 RotaryEncoder_Alps_EC11E-Switch_Vertical | 24.5 | encoder: iron only, plastic body; shaft must point up |
| J1 shell legs | - | after reflow |
| TP23, TP24, TP25, TP26, TP27 | 8.2 | Keystone 5010-5014 THT test points: optional, fit if wanted (height unverified) |

## 5. Not fitted on the board

- R256: DNP (fit a 0R at the bench only for forced PWM on U25)
- J7: Tag-Connect TC2030 footprint, no part
- SW101: panel rocker CW GRB112B802BR1, wired at enclosure assembly
- TP1, TP2, TP3, TP4, TP5, TP6, TP7, TP8, TP9, TP10, TP11, TP12, TP13, TP14, TP15, TP16, TP17, TP18, TP19, TP20, TP21, TP22: SMD test-point loops, not populated by default (see 0).
- Mounting holes H1-H9, HA1, HA2 and LOGO1 have no part.

Counts: 308 SMD placements (19 fine-pitch/EP ICs, 198 0402, 59 0805/1206, 11 other low, 10 medium, 11 tall), 10 THT parts by iron.
