# Passive repackage to hand-solder footprints (2026-10-06)

Policy: all resistors and capacitors use hand-solder KiCad footprints, 0402 by default, 0805 only for large or high-voltage capacitors. Footprints `R_0402_1005Metric_Pad0.72x0.64mm_HandSolder`, `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder`, `C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` were copied (one file each) into `kicad-library/footprint`; STEP models `R_0402_1005Metric.step`, `C_0402_1005Metric.step`, `C_0805_2012Metric.step` are in `kicad-library/3d` (project-relative paths). Old `PD_*` footprints stay in the library, unused except where flagged. Helpers: `helpers/repackage_passives.py`, `helpers/repackage_passives_bom.mjs` (map: `reports/passive-repackage-map.json`).

Result: 104 R + 98 C on 0402, 59 C on 0805 (of which 16 are unchanged-MPN 22 uF/10 uF parts); FB200 on 0402. Only C275 (polymer 8x10) is not a chip part. Netlist: all 312 pin groups identical; ERC 19 (unchanged); all footprint and 3D paths resolve. LCSC codes: C60491, C60490, C29266 (and carried-over codes) were seen in search results; every other new MPN comes from family knowledge and is UNVERIFIED (code, price and stock open; partial BOM subtotal reduced to US$74.53 fitted / US$84.50 order because those rows are unpriced).

## Changes
| Refs | Old pkg | Old MPN | New pkg | New MPN | LCSC |
|---|---|---|---|---|---|
| C2 | C_1210 | CL32B475KBUYNNE | C_0805 | C2012X7R1H475K125AC | open |
| C5 | C_1206 | (none) | C_0805 | C2012X7R1H475K125AC | open |
| C6, C104, C105, C106, C107, C140, C141, C142 (+8) | C_0805 | GRM21BZ71A226ME15L | C_0805 | GRM21BZ71A226ME15L | C907991 |
| C100, C101, C108, C111, C112 | C_1210 | CL32B106KBJNNNE | C_0805 | GRM21BR61H106KE43L | open |
| C102, C109, C175, C176, C181, C185, C190, C214 (+3) | C_0805 | CL21B106KPQNNNE | C_0805 | CL21B106KPQNNNE | C32635 |
| C103, C110, C266 | C_0603 | CC0603KRX7R9BB473 | C_0402 | GRM155R71H473KA12D | open |
| C113, C114, C115 | C_0402 | GRM155R71H104KE14D | C_0402 | GRM155R71H104KE14D | C77020 |
| C120, C121, C126, C130, C131, C132, C143, C151 (+20) | C_0603 | CL10B104KB8NNNC | C_0402 | GRM155R71H104KE14D | C77020 |
| C122, C123, C124, C125 | C_0603 | LMK107B7105KA-T | C_0402 | CL05A105KO5NNNC | C29266 |
| C161, C280, C293 | C_0603 | CL10A475KO8NNNC | C_0805 | CL21A475KAQNNNE | open |
| C164 | C_0603 | CL10A105KB8NNNC | C_0402 | CL05A105KO5NNNC | C29266 |
| C170, C171, C172, C173, C174, C192, C193, C212 (+21) | C_0805 | CL21B105KBFNNNE | C_0402 | CL05A105KO5NNNC | C29266 |
| C177, C178 | C_0603 | CL10C330JB8NNNC | C_0402 | GRM1555C1H330JA01D | open |
| C182, C183 | C_0603 | CL10C331JB8NNNC | C_0402 | GRM1555C1H331JA01D | open |
| C184, C270 | C_0805 | CL21B105KBFNNNE | C_0805 | CL21B105KBFNNNE | C28323 |
| C186, C187, C194, C195, C236 | C_1206 | CL31B475KBHNNNE | C_0805 | CL21A475KAQNNNE | open |
| C200, C201, C202, C203, C204, C205, C243, C244 | C_0805 | CL21B225KAFNNNE | C_0402 | CL05A225KP5NNNC | open |
| C206, C207, C208, C209, C210, C211 | C_0603 | GRM1885C1H103JA01D | C_0402 | GRM1555C1H103JA01D | open |
| C226, C227 | C_0603 | CL10C220JB8NNNC | C_0402 | GRM1555C1H220JA01D | open |
| C265 | C_0805 | CL21B225KAFNNNE | C_0805 | CL21B225KAFNNNE | C19110 |
| C268 | C_0603 | CL10B682KB8NNNC | C_0402 | GRM155R71H682KA01D | open |
| C269 | C_0603 | CL10C470JB8NNNC | C_0402 | GRM1555C1H470JA01D | open |
| C271, C272, C273, C274, C277, C279, C290, C292 | C_1210 | CL32B226KAJNNNE | C_0805 | CL21A226MAQNNNE | open |
| C285, C286, C287, C288, C298, C299, C300, C301 | C_0603 | CL10B474KA8NNNC | C_0402 | CL05B474KO5NNNC | open |
| C302, C303, C304, C305, C306, C307 | C_0805 | CL21B684KBFVPNE | C_0805 | CL21B684KBFVPNE | C472832 |
| FB200 | R_0603 | BLM18AG601SN1D | R_0402 | BLM15AG601SN1D | open |
| R10 | R_0603 | RC0603FR-07200KL | R_0402 | RC0402FR-07200KL | open |
| R11, R13, R14, R15, R18, R106, R182, R183 (+4) | R_0603 | RC0603FR-0710KL | R_0402 | RC0402FR-0710KL | C60490 |
| R12, R16, R17, R103, R107, R109, R110, R111 (+28) | R_0603 | RC0603FR-07100KL | R_0402 | RC0402FR-07100KL | C60491 |
| R100 | R_0603 | 1RC0603F5231 | R_0402 | RC0402FR-075K23L | open |
| R101 | R_0603 | 1RC0603F3012 | R_0402 | RC0402FR-0730K1L | open |
| R102, R120, R121 | R_0603 | RC0603FR-074K7L | R_0402 | RC0402FR-074K7L | open |
| R108, R124 | R_0603 | RC0603FR-07180KL | R_0402 | RC0402FR-07180KL | open |
| R112, R200, R201, R202, R203, R204, R205 | R_0603 | RC0603FR-07100RL | R_0402 | RC0402FR-07100RL | open |
| R122, R232, R233 | R_0603 | RC0603FR-0747KL | R_0402 | RC0402FR-0747KL | open |
| R126, R127, R174, R241 | R_0603 | RC0603FR-071ML | R_0402 | RC0402FR-071ML | open |
| R140 | R_0603 | 1RC0603F7872 | R_0402 | RC0402FR-0778K7L | open |
| R141 | R_0603 | RC0603FR-079K1L | R_0402 | RC0402FR-079K1L | open |
| R150 | R_0603 | FRC0603F6043TS | R_0402 | RC0402FR-07604KL | open |
| R151 | R_0603 | AC0603FR-0791KL | R_0402 | RC0402FR-0791KL | open |
| R170 | R_0603 | RC0603FR-072R2L | R_0402 | RC0402FR-072R2L | open |
| R171, R172 | R_0603 | RC0603FR-0722RL | R_0402 | RC0402FR-0722RL | open |
| R173 | R_0603 | RC0603FR-071K5L | R_0402 | RC0402FR-071K5L | C114759 |
| R185, R186, R187, R226, R227, R228, R229, R230 (+5) | R_0603 | RC0603FR-071KL | R_0402 | RC0402FR-071KL | open |
| R206, R207, R208 | R_0603 | RC0603FR-0733RL | R_0402 | RC0402FR-0733RL | open |
| R209, R210 | R_0603 | RC0603FR-072K2L | R_0402 | RC0402FR-072K2L | open |
| R250 | R_0603 | RC0603FR-07499KL | R_0402 | RC0402FR-07499KL | open |
| R251 | R_0603 | RC0603FR-0756KL | R_0402 | RC0402FR-0756KL | open |
| R252 | R_0603 | RC0603FR-07301KL | R_0402 | RC0402FR-07301KL | open |
| R253 | R_0603 | RC0603FR-07150KL | R_0402 | RC0402FR-07150KL | open |
| R254 | R_0603 | RC0603FR-0782KL | R_0402 | RC0402FR-0782KL | open |
| R256, R260 | R_0603 | RC0603FR-070RL | R_0402 | RC0402FR-070RL | open |

## FLAGS
1. **Effective capacitance, VBUS/PMID (C100, C101, C108, C111, C112)**: 10 uF 50 V X7R 1210 became GRM21BR61H106KE43L (50 V X5R 0805). At 20 V bias X5R 0805 keeps roughly 20-30 % (about 2-3 uF each) versus roughly 40-50 % for the 1210; total VBUS 2 x and PMID 3 x remain, but the margin is lower. Not silently accepted: add 1-2 further 10 uF/50 V (or 4.7 uF) parallel parts at layout, or return PMID to 1210. No parts were added now (netlist kept identical).
2. **C2 (TPS25730D CVBUS) and C5 (USB_AUX_5V)**: 4.7 uF 50 V X7R 1210/1206 became TDK C2012X7R1H475K125AC (0805, 50 V X7R, MPN unverified). Effective capacitance at 20 V falls to about 1.5 uF (was about 2-2.5 uF); still inside the 1-10 uF CVBUS window.
3. **PVDD_AMP (C271-274, C277, C279, C290, C292)**: 22 uF 25 V X7R 1210 became CL21A226MAQNNNE (25 V X5R 0805). At 12 V bias roughly 8-10 uF effective each (was roughly 12-13 uF). Total drops about 30 %; 100 uF polymer C275 (unchanged) and 0.1 uF/1 uF remain. Add parallel 22 uF at layout if the TAS5825M PVDD ripple test fails. Rating 25 V is about 2x the 12 V rail (OVP 12.7 V); no 35 V 22 uF 0805 exists.
4. **Caps kept at 0805 on purpose**: all 10 uF/22 uF/4.7 uF parts, C184 and C270 (1 uF 50 V X7R: USB_VBUS and PVDD_AMP 12 V bias), C265 (2.2 uF on TPS61088 VCC, about 6 V; a 10 V 0402 part would lose over half), C302-C307 (0.68 uF 50 V output filter caps; no 0402 part, high swing).
5. **4.7 uF (C161, C280, C293, C186, C187, C194, C195, C236)**: 0603/1206 became CL21A475KAQNNNE (0805, 25 V X5R), more capacitance at bias than before. C186/C187/C194/C195 are signal-path AC couplings (X5R, level-dependent; previously also class-II).
6. **1 uF 0402 (CL05A105KO5NNNC, 16 V X5R, 34 pcs)** replaces 50 V/10 V X7R parts: at 5 V (C124, C221, C224, C225 on 5 V rails) effective is about 0.5-0.6 uF; at 3.3 V about 0.7 uF. Dielectric text of C122-C125 changed from X7R 10 V to X5R 16 V. Audio coupling caps (C230-C235, C239/C240) are X5R, higher distortion/microphonics than before (same class as the X7R parts); consider film/C0G if THD measures poorly.
7. **2.2 uF 0402 (CL05A225KP5NNNC, 10 V X5R)**: C200-C205 (signal couplings, low bias) and C243/C244 (HPVDD/HPVSS about +/-1.8 V, about 20 % loss) - acceptable; HPVDD/HPVSS were not enlarged. C265 stays 0805 (flag 4).
8. **0.47 uF BST (C285-288, C298-301)**: now 16 V X7R 0402 (was 25 V X7R 0603); bootstrap voltage is GVDD (about 7 V), derating about 25 %; Table 66 value 0.47 uF still met at about 0.35 uF effective. Moderate margin.
9. **High-voltage nodes**: every capacitor on VBUS (C2, C5, C100, C101, C108, C111, C112, C113, C114, C103/C110 BTST at VBUS+5 V, C182/C183 CC filters, C184) is rated >= 50 V; PVDD caps are 25 V or 50 V. Nothing below 35 V sits above 12 V.
10. **Resistor power**: highest dissipation is R112 (100R, BAT_PACK sense, uW), R170 (2.2 R in 5 V codec supply, about 1.4 mW at 25 mA), R171/R172 (22 R), R250 (499 k at 12 V, 0.3 mW), R252 (301 k at the SW node), R10/R12/R17 on VBUS dividers (under 5 mW at 22 V). All are below 12 mW (< half of 62.5 mW); no resistor stays at 0603. Voltage rating 50 V covers the 22 V maximum.
11. **FB200**: BLM18AG601SN1D (0603) became BLM15AG601SN1D (0402, 600 ohm at 100 MHz, rated current about 300 mA vs about 30 mA codec AVDD); displayed value text updated. LCSC code open; rating from family knowledge, check the datasheet.
12. **Resistor MPNs changed brand**: R100, R101, R140, R150, R151 (Uniroyal/FOJAN/Yageo AC series) became Yageo RC0402FR-07xxxL E96 values (5.23 k, 30.1 k, 78.7 k, 604 k, 91 k); verify stock of RC0402FR-0730K1L, -075K23L, -0778K7L, -07604KL.
13. **C0G**: crystal caps C177/C178 (33 pF), C226/C227 (22 pF), CC filters C182/C183 (330 pF), anti-alias C206-C211 (10 nF) and COMP C269 (47 pF) are all Murata GRM1555 C0G 50 V; 6.8 nF COMP C268 is X7R as before. Crystal load effective values are unchanged.
14. **Value text** such as "100nF 10V X7R" was left as drawn; the fitted part is 50 V X7R (C77020 family). Displayed values and references are otherwise unchanged.
15. **Unverified**: every MPN above except those with an LCSC code in the table (and the carried-over CL21B*/GRM21BZ rows) was chosen from family knowledge and not stock-checked (Murata GRM155/GRM21BR, Samsung CL05/CL21A, TDK C2012). Replace any that fail at order.
16. **Hand-solder reality**: 0402 is hand-solderable but small; the Pad 0.72x0.64 / 0.74x0.62 land patterns are KiCad stock. Unused: `PD_R_0603`, `PD_C_0603`, `PD_C_1206/1210`, `PD_R_1206` (PD_C_0402 and PD_C_0805 remain too). BOM pre-existing notes: J7 has no BOM row, PACK is a placeholder row, R256 DNP is listed inside the R260 row.
