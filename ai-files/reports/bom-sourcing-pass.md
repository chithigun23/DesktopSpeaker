# BOM sourcing pass, 2026-10-10 (review item B5)

Scope: `ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv` and `.xlsx` only. Schematic, PCB, footprints and libraries were not touched.
Method: public LCSC product-detail JSON (stock, price ladder) and the public JLCPCB parts list (basic/extended). No login, no orders.
All stock figures are lookup snapshots from 2026-10-10, not quotes and not reservations; re-check at order.

## Counts

| Measure | Before (CSV 2026-10-08) | After |
|---|---|---|
| BOM rows (one row per MPN group; incl. 2 test-point rows) | 99 | 101 (+2 J5 mating rows) |
| Rows with an LCSC code | 50 | 93 |
| Rows without an LCSC code | 49 | 8 (2 test-point rows excluded by design, 6 unresolved) |
| Rows verified (listing model equals MPN, value and package match) | 15 clean; 84 unlisted or flagged unverified/snapshot | 93 |
| of which stock below the order quantity | not checked | 11 |
| Rows unresolved | 49 without code | 6 |
| Rows priced | 36 | 93 |
| Fitted USD subtotal (priced rows) | 74.38 | 101.69 |
| In-stock order subtotal (USD, MOQ-consolidated) | 83.57 | 124.59 |

The subtotals are partial and are not a product cost. They exclude the pack/cells/PCM/harness, the 6 unresolved rows, test points, speakers and every row whose stock is below the order quantity (those contribute to the fitted subtotal but not the order subtotal). The rise from the old figures is mostly newly priced rows plus corrected prices on previously priced passives (the old 0402 resistor prices were stale or low).
`Availability` now carries the status text: "In stock", "OUT OF STOCK" or "UNRESOLVED", plus JLC basic or extended (6 basic rows, 86 extended; hand-soldering is the plan, so this only matters if JLC assembly is ever used). Where LCSC shows stock 0 but the JLC list shows a few pieces, both numbers are in the cell.

## BOM edits made

- Codes, MOQ, multiples, price tier (ladder at order quantity), stock, JLC type and source URL filled for 43 rows; the 50 rows that had codes were re-looked-up: all models match their MPN; prices, stock and MOQ refreshed.
- C242 added to the CL05A225KP5NNNC row (now 9 pcs: C200-C205, C242-C244; corrected below to C241, C7464343, X5R 10 V 0402, 2,000 in stock). BOM only. Note: X5R 10 V loses capacitance with bias; U10 VDD should be checked against the rail (about 1.8 V or 3.3 V).
- Value text corrected where the listing disagrees: GRM21BR61H106KE43L is X5R (text said X7R); CL05A105KO5NNNC is X5R 16 V (said X7R 10 V); FB200 text said BLM18AG601SN1D, MPN is BLM15AG601SN1D (0402).
- J4 (PD I2C service header): set to B-2100S04P-A110, C124378 (Ckmtw 1x4 2.54 mm straight THT, 52,690 in stock), the same part as J6. It matches the `PD_SERVICE_HDR` footprint (1x04, 2.54 mm). Selected by me to match the footprint; no user choice was recorded.
- New rows: J5 mating housing Molex 43645-0300 C259740 (5,705 in stock, qty 1) and 3 crimp contacts 43030-0001 C259786 (2.89 M in stock). Wire gauge for the pack leads (3 A charge, about 9 A discharge) is undecided; 43030-0001 is listed as 20-24 AWG, so confirm the contact variant before ordering.
- xlsx regenerated from the CSV (was 2026-10-06; C311-C316, TP26/27 rows now included; formulas for order qty/fitted/order USD re-pointed to rows 11-111 and recalculated in LibreOffice, matching the CSV). The "Open selections" sheet was not changed. `DesktopSpeaker_LCSC_Starter_BOM.xlsx.inspect.ndjson` is a stale old inspection dump and was left alone.

## Verified but not orderable today (stock below order quantity)

| Ref | MPN | Code | Issue and alternatives |
|---|---|---|---|
| C2, C5 | C2012X7R1H475K125AC | C2174853 | Stock 0, $1.30 each. Alternatives, same 0805 4.7 uF 50 V X7R: TDK C2012X7R1H475KT0A0E C5159426 (231 in stock, $0.199); Murata GRM21BR61H475KE51L C162420 (X5R, 117,805, $0.114) |
| C177, C178 | GRM1555C1H330JA01D | C76964 | Stock 0 (33 pF C0G 0402) |
| R100 | RC0402FR-075K23L | C477746 | LCSC stock 0 (JLC list 12), below the 100 MOQ |
| R101 | RC0402FR-0730K1L | C138009 | LCSC stock 0 (JLC list 746) |
| R150, R151 | RC0402FR-07604KL / -0791KL | C327334, C327323 | LCSC stock 0 (JLC list 8 and 6) |
| R254 | RC0402FR-0782KL | C137932 | LCSC stock 0 (JLC list 5,186) |
| Y170 | X322512MSB4SI | C9002 | LCSC stock 0 (JLC list 119,585) |
| Y200 | L327S240P11L | C5261154 | LCSC stock 0 (JLC list 22) |
| SW101 | KCD1-201-R | C5884429 | LCSC stock 0 |
| SW102 | EC11E15244G1 | C370970 | Stock 0. In-stock Alps variants differ (EC11E18244A5 C255515, 697; EC11E18244AU C202365, 401): check detent/shaft/switch suffix against the footprint before any swap |

The 0-stock resistors are odd values (5.23k, 30.1k, 604k, 91k, 82k). Options needing your approval: move to nearest in-stock E96/E24 values only where the circuit tolerates it (feedback dividers need an engineering check), or buy elsewhere.

## Unresolved rows (6)

| Row | Reason | Candidates (not applied) |
|---|---|---|
| C103, C110, C266 GRM155R71H473KA12D | MPN not listed at LCSC/JLC | GRM155R71H473KE14D C117757 (47 nF 50 V X7R 0402, 28,566, $0.0119) |
| C268 GRM155R71H682KA01D | MPN not listed | CL05B682KB5NNNC C318580 (Samsung 6.8 nF 50 V X7R 0402, 18,635, $0.0094) |
| C206-C211 GRM1555C1H103JA01D | MPN not listed | GRM1555C1H103JE01D C22400107 (10 nF 50 V C0G, 63,616, $0.0966 each) |
| C285-C288, C298-C301 CL05B474KO5NNNC | MPN not listed | CL05B474KP5NNNC C2895720 (470 nF 10 V X7R, 8,047, $0.0403; 10 V vs rail needs checking); CGA0402X7R474K160GT C22435970 (HRE 16 V, 1,914, $0.0117) |
| C275 EEH-ZA1E101P | MPN not listed; footprint is `CP_Elec_8x10` | Panasonic EEHZA1E101XP C264047 (100 uF 25 V, D6.3x7.7, 2,184, $0.80) or EEHZA1E101XV C454667 (D6.3x8, 1,675, $0.67): both smaller than the 8x10 footprint and the XP/XV suffix is not the intended P part; the listed ripple of the XP (300 mA) looks too low for a bass reservoir, so prefer XV (2 A at 100 kHz) after datasheet check |
| PACK | No LCSC stock items for cells, PCM or harness (INR21700 searches returned nothing) | NTC: Murata NCP15XH103F03RC C77131 (10 k 0402, B3380, 10,406); MF52A103F3950 C13879 (10 k B3950, 170,230); MF52A103F3435 C84036 (10 k B3435, 31,810). The curve must match the BQ25792 TS table. Pack/PCM purchase remains your decision |

## Inductors

L201-L206: Sunlord MWSA1265S-220MT is at LCSC as C7245133 (22 uH, 36 mohm, listing "6 A / 7.5 A", 13.5x12.6 mm, matches the MWSA1265S footprint). Only 54 in stock for 6 required; the LCSC detail API returned no data for this code, so price ($0.7183) and stock come from the JLC list only. The listing's current ratings contradict the earlier 5.0 A note; confirm Isat from the Sunlord datasheet (peak current 2.8 A at 11.1 V into 4 ohm, OCP about 7.5 A).

L200 (2.2 uH boost, Isat >= 12 A): correction to the earlier note, XAL7070-222MEC is at LCSC: C3911470, 2.2 uH, 19.6 A / 17.8 A, 6.33 mohm, 7.2x7.5 mm, 262 in stock, $8.1549. It is a drop-in with the existing footprint; the BOM now carries it (verified, low stock). Substitutes, for approval only (nothing changed):

| Option | Part | Isat / Irms (per listing) | DCR | Size | Stock, price | Fits current footprint? |
|---|---|---|---|---|---|---|
| 1 (recommended) | Coilcraft XAL7070-222MEC C3911470 | 19.6 / 17.8 A | 6.33 mohm | 7.2x7.5 | 262, $8.15 | Yes (is the footprint part) |
| 2 | Bourns SRP7050TA-2R2M C2045424 | 14 A and 10 A (order of Isat/Irms not stated) | 11.2 mohm | 7.3x6.6 | 0, $1.13 | Body is near the XAL7070 size, but pads differ; verify against the Bourns land pattern. Not orderable (stock 0) |
| 3 | KOHER MDA1050-2R2M C2847559 | 20 / 19.5 A | 5.1 mohm | 11x10 | 563, $1.08 | No: needs a new footprint and about 4 mm more board each way |
| 4 | Bourns SRP1265A-2R2M C2831487 | 37 / 22 A (order not stated) | 4.2 mohm | 13.5x12.5 | 698, $1.39 | No: needs a new footprint (same body as the L201-L206 parts) |
| not usable | Bourns SRP6540-2R2M C2041814 | 9 A | 15.5 mohm | 7.2x6.5 | 19 | Isat below 12 A |
| not usable | KOHER MDA7050-2R2M C2847539 | 10 A | 10 mohm | 7.3x6.6 | 261 | Isat below 12 A |
| not at LCSC | Cyntec PIMB104T-2R2MS | | | | | No hit |

Approval needed: confirm whether to keep XAL7070-222MEC at about $8 each (stock 262) or accept a footprint change for options 3 or 4. Isat/Irms order in the LCSC text is ambiguous for options 2-4; confirm against the manufacturer datasheets before choosing.

## Other observations

- C315 47 uF 25 V 1206 (GRM31CR61E476ME44L C403725, 92 k in stock) and C316 (CL21B105KBFNNNE C28323, JLC basic): verified. LCSC stock for C28323 shows only 10 at LCSC against 1.89 M at JLC.
- Lookups reproducible with the public endpoints `wmsc.lcsc.com/ftps/wm/product/detail?productCode=` and the JLCPCB `selectSmtComponentList` search; scripts were kept in the scratchpad, not the project.
- Not committed.

## Coordinator-approved substitutions (2026-10-10)

Rules applied (BOM only; schematic, PCB and libraries untouched): same value, same package/footprint, voltage rating >= original, dielectric and tolerance equal or better, in stock at LCSC (public LCSC product JSON, no login, no order). Stock figures are lookups, not reservations. Order quantities follow the sheet convention (multiple = MOQ). Each applied line is also recorded in the Notes column of the BOM row.

| Ref | Old part | New part | Reason |
|---|---|---|---|
| U10 VDD cap | row listed C242 | ref C241 | C242 does not exist; C241 (net 3V3_AUDIO) moved from the CL05A105KO5NNNC 1 uF row (33 to 32 pcs) to the CL05A225KP5NNNC 2.2 uF row (still 9 pcs: C200-C205, C241, C243, C244) |
| C103, C110, C266 | GRM155R71H473KA12D (not listed) | Murata GRM155R71H473KE14D C117757 | 47 nF X7R 50 V +/-10% 0402; 28,550 in stock, $0.012 |
| C268 | GRM155R71H682KA01D (not listed) | Samsung CL05B682KB5NNNC C318580 | 6.8 nF X7R 50 V +/-10% 0402; 18,600, $0.0095 |
| C206-C211 | GRM1555C1H103JA01D (not listed) | Murata GRM1555C1H103JE01D C22400107 | 10 nF C0G 50 V +/-5% 0402; 59,625, $0.0972 |
| C285-C288, C298-C301 | CL05B474KO5NNNC 16 V (not listed) | HRE CGA0402X7R474K160GT C22435970 | 470 nF X7R 16 V +/-10% 0402; 1,900, $0.0118. These are TAS5825M bootstrap caps (BST to OUT nets); the 10 V CL05B474KP5NNNC C2895720 was rejected because 10 V is below the original 16 V and close to the bootstrap voltage |
| C275 | EEH-ZA1E101P (not listed) | Panasonic EEHZA1E101XP C264047 | 100 uF 25 V +/-20% hybrid polymer, standard (P) product of the same EEH-ZA series, 1,708 in stock, $0.8096. Pad fit vs `CP_Elec_8x10`: pads at +/-3.25 mm, 3.5 x 2.5 mm; datasheet size D8 terminals span about +/-1.1 to +/-3.5 mm (P 2.2, I 2.4, W 0.65), so they sit on the pads; the 6.3 mm body is inside the 8x10 courtyard. Datasheet ripple is 2000 mA rms (the 300 mA in the LCSC text is wrong). The 3D model is the 8x10 one (cosmetic). Fit OK, so applied; the 6.3 mm part is much smaller than the footprint, so a dedicated footprint would be tidier later |
| C2, C5 | TDK C2012X7R1H475K125AC C2174853 (stock 0) | TDK C2012X7R1H475KT0A0E C5159426 | 4.7 uF X7R 50 V 0805; 175 in stock, $0.201. C2 is on USB_VBUS (up to 20 V) and C5 on USB_AUX_5V, both DC-bias critical, so Murata X5R C162420 was not used |
| C177, C178 | Murata GRM1555C1H330JA01D C76964 (stock 0) | FOJAN FCC0402N330J500AT C5137486 | 33 pF C0G 50 V +/-5% 0402; 3.58 M, $0.0031 (Samsung CL05C330JB5NNNC C70465 also stock 0) |
| R100 | RC0402FR-075K23L C477746 | UNI-ROYAL 0402WGF5231TCE C25907 | 5.23 k 1% 0402 50 V, 62.5 mW, 100 ppm; 3,700 |
| R101 | RC0402FR-0730K1L C138009 | Yageo AC0402FR-0730K1L C226982 | 30.1 k 1% 0402 (automotive-grade Yageo series); 15,500 |
| R150 | RC0402FR-07604KL C327334 | UNI-ROYAL 0402WGF6043TCE C27013 | 604 k 1% 0402; 1,800 |
| R151 | RC0402FR-0791KL C327323 | Yageo AC0402FR-0791KL C144733 | 91 k 1% 0402; 30,300 |
| R254 | RC0402FR-0782KL C137932 | Yageo AC0402FR-0782KL C144735 | 82 k 1% 0402; 35,600 |
| Y170 | YXC X322512MSB4SI C9002 (LCSC stock 0) | KYX K3A120002010 C368730 | 12 MHz, CL 20 pF, +/-10 ppm, +/-20 ppm stability, ESR 80 ohm, 3225-4P; 67,070, $0.0593 |
| Y200 | Lucki L327S240P11L C5261154 (stock 0) | JYJE 3TJ424576UYFBC C2149067 | 24.576 MHz, CL 15 pF, +/-10 ppm, +/-30 ppm stability, ESR 60 ohm, 3225-4P; 135 in stock (low), $0.1237. The old LCSC listing says 24 MHz, so the original code may have been the wrong frequency for the PCM1862 (24.576 MHz); recheck pad usage 1/3 on the replacement |

Not substituted (flagged):

- SW101 KCD1-201-R C5884429: stock 0; no in-stock equal part found (all KCD1 variants stock 0). Marked 'no stock - alternatives' in Availability; the 3-terminal mapping and the 10 A/12 VDC rating issue remain open.
- SW102 EC11E15244G1 C370970: stock 0. EC11E18244A5 C255515 (437) and EC11E18244AU C202365 (401) have 36 detents / 18 pulses against 30 / 15, so they are not equal; not substituted. Marked 'no stock - alternatives'.
- L200 XAL7070-222MEC C3911470: kept (Isat 17.8-19.6 A >= 12 A required, 262 in stock, fits footprint).
- L201-L206 MWSA1265S-220MT C7245133: Sunlord catalog (MWSA series, page 10) gives 22 uH +/-20%, DCR 36 mohm max, Isat 7.5 A max (9.0 typ), Irms 6.0 A max (8.0 typ). The earlier 5.0 A note was wrong. Load: peak about 2.8 A at 11.1 V (about 3.2 A at 12.6 V) into 4 ohm, Irms about 2 A, so about 2.3x margin on Isat and 3x on Irms: OK. TAS5825M OCP at about 7.5 A equals the minimum Isat, so a hard short can briefly saturate the inductor (acceptable, current is OCP-limited). Stock is only 54 for 6 needed (price from JLC list only). BOM text updated from 5.0 A to 7.5 A.
- PACK (cells, PCM, harness, NTC): unresolved, user pack decision. NTC note: the BQ25792 datasheet recommends a 103AT-2 10 k thermistor and its JEITA thresholds are quoted for it (B about 3435 K), so MF52A103F3435 C84036 is the closest candidate of those listed; the TS divider and thresholds must be checked against the chosen curve.

### Counts after the coordinator pass

| Measure | Before this pass | After |
|---|---|---|
| BOM rows | 101 | 101 |
| Rows with an LCSC code | 93 | 98 |
| Rows without a code | 8 | 3 (PACK unresolved; 2 test-point rows excluded by design) |
| Rows unresolved | 6 | 1 (PACK) |
| Rows with stock below order qty | 11 | 2 (SW101, SW102) |
| Rows priced | 93 | 98 |
| Fitted USD subtotal (priced rows) | 101.69 | 101.23 |
| In-stock order subtotal (USD, MOQ-consolidated) | 124.59 | 133.11 |

The subtotals remain partial and are not a product cost: they exclude the pack/cells/PCM/harness, the unresolved PACK row, test points and speakers; the fitted figure includes SW101 and SW102 at listed prices while the order figure excludes them (stock 0). The order subtotal rose mainly because 13 rows that had no price or no stock are now orderable (MOQ-driven). The xlsx was regenerated by patching the data rows of `Selected BOM` from the CSV (formulas kept; LibreOffice recalculation reproduces 101.23 and 133.11); `Open selections` sheet unchanged. Not committed.
