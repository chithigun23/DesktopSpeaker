# Routing R6k (2026-10-09): Fable R6j review fixes on R6j-final, corner hits 49 → 7

Work copies only (`ai-files/pcb/work-r6/`). `DesktopSpeaker-kicad/` was not touched, nothing was committed, no process was killed, no sub-agents were used, `route_r6i_route.py` was not needed (no router runs, so no prune risk).

- **Final board:** `work-r6/R6k-final.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`, `.drc.json`, `.open2.json`, `.isl.json`, `.bends.json`). `R6k-0.*` is the R6j-final baseline copy.
- **Rules:** `R6k.kicad_pro` / `R6k.kicad_dru` are byte copies of the R6j files (checked with `cmp`). No DRC rule, rule area or netclass was added, relaxed or moved.
- **Renders:** `ai-files/pcb/route-r6k-top.png`, `route-r6k-bottom.png`, `route-r6k-in2.png`.
- **Specs, logs, measurements:** `work-r6/r6k/` (`k1`–`k11` edit and via plans, `arc8*.json` arc logs, `final.gates.txt`, `capacity.txt`, `usb_coupling.txt`, `powervias.txt`, `audio_gnd.txt`). Intermediate boards were deleted.

## Gates (R6j-final → R6k-final)

| Gate | R6j-final | R6k-final |
|---|---|---|
| Open edges (fragment-aware, all nets) | 2 (J7 NRST/SWCLK) | **2**, the same two |
| Power-class open edges | 0 | 0 |
| DRC clearance / shorts / dangling / isolated copper / track width | 0 | **0** |
| DRC USB items | 3 skew, 1 uncoupled 17.34 mm | 3 skew, 1 uncoupled **17.34 mm** (unchanged, see M4) |
| DRC silk/lib | 37 | 37 |
| Island continuity (`route_r6h_isl.py` vs R6k-0) | – | every island 1 outline; area changes only where intended (below) |
| Foreign non-GND vias in In2 islands | 32 | 32 (Q103-G via moved 0.6 mm inside the same SYS column) |
| In2 slow signals to island outline | ≥ 0.32 mm | ≥ 0.32 mm (none < 0.3) |
| AUDIO / I2S / USB / clock copper on In2 | none | none |
| Via centre in SMD pad (non-EP) | 7 | **3** |
| Bend-rule hits (`route_r6i_bends.py`) | 49 | **7** |
| Vias total (GND / signal) | 921 (268 / 653) | 955 (265 / 690) |
| POWER_HI + PVDD vias 0.8/0.4 | 0 of 170 | **179 of 207** |

Island area changes (all deliberate): BAT_INT_IN2 183.7 → 152.7 mm² (west part given to SYS), SYS_IN2 465.3 → 502.9, SYS_BOOST_F 308 → 318, SYS_U4CAP_F 25.4 → 21.4 (bottom edge raised for the BAT strip), SW1_F/SW2_F −0.6/−0.7 (idle corners trimmed), VBUS_U4A_F 4.1 → 4.5. New pours (1 outline each): SYS_U4PIN_F, BAT_U4PIN_F, PMID_U4PIN_F, VBUS_U4B_F, PVDD_C271_F, PVDD_C272_F, SYS_COL_B (B.Cu). B.Cu GND_BCU went from 4 to 5 fill pieces: a 20 mm² piece between the SW2 B jumper and SYS_COL_B, stitched by the C311 and C106 GND vias.

Current ratings below are IPC-2221 at the accepted 15 K rise (outer 1 oz k 0.048, inner 0.5 oz k 0.024), the same basis as the review. "Cut" = narrowest total copper cross-section, with all parallel lanes summed (`route_r6k_cut.py`). "Widest" = widest single path (`route_r6k_neck.py`, 0.1 mm grid).

## BLOCKER B1: SYS_RAW out of U4 pin 25

| | Before | After |
|---|---|---|
| Pin 25 escape | 0.2 mm tracks, 2.8 mm to the cap pour | SYS_U4PIN_F pour on the pad end. The first 0.2 mm is 0.30 mm wide, set by the pin pitch (SW2 pad 0.25 mm away, Q103-G corner pad 0.25 mm away). After that the path is ≥ 0.95 mm wide (widest path) to C104.1 and the cap row. |
| C311 → C104 passage | 0.3 mm (between SW2_F and C311.2) | ≈ 1 mm. SW2_F's idle lower-right corner was raised 0.65 mm; the SW node path (0.85 mm strip from pin 26) is unchanged. |
| SYS F → In2/B transitions at the caps | 8 × 0.6/0.3 | **14 × 0.8/0.4** in SYS_U4CAP_F (the field was upsized, plus 4 vias in the cap band and 2 between the caps), plus 1 fine 0.5/0.2 via beside pin 25 |
| SYS_IN2 column x 154–163 | cut 2.46 mm, widest 0.9 mm (0.7 A) | **cut 8.76 mm (3.8 A), widest 5.1 mm** |
| Parallel B.Cu SYS (new SYS_COL_B, x 157.2–163.4, y 115.9–124.4) | – | cut 6.2 mm (**10.7 A**), widest 3.9 mm; 6 × 0.8/0.4 vias at its south end into the SYS_BOOST_F extension |
| SYS_BOOST_F field (y 128–129) | 14 × 0.6/0.3 | 14 × 0.8/0.4; SYS_BOOST_F grown north to y 121.95 (x 160.3–163.5) |
| SYS field 2 → boost | In2 5.9 / F 4.9 mm | In2 5.9 / F 4.7 mm (unchanged path, 8.8 A on F) |

**How it was done**
- The BAT_INT_IN2 west part (x 157.6–163.9) was given to SYS_IN2, so the SYS column is x 153.9–163.5.
- The 14 BAT vias that sat in that column were removed. A 0.8/0.4 BAT array (4 + 18 vias) went into the BAT_INT_F block, now at x 163.9–170.7.
- The C106/R102 GND vias left the column centre: 2 vias at x 158.1 became 1 via at 157.25,123.85, with R102.2 re-routed to C106.2.
- The Q103-G B track was re-routed north of the new B pour, along y 115.3 with two arcs.
- To clear the BAT neck, the Q103-G via moved 155.55 → 154.95,120.1, and the SW2 B jumper bend moved 0.35 mm west inside NECK_U4.

**Why (c) went on B.Cu and not on F.Cu:** the review asked for F.Cu SYS from SYS_U4CAP_F down to SYS_BOOST_F at x 157–163, y 119–128. That area is the BAT_INT_F strip, which is BAT's only F path from pins 22/23 to Q103. SYS (cap row north, boost south) and BAT (pins east, Q103 north-east) cross there whatever is drawn. So SYS crosses on In2 + B.Cu and BAT crosses on F.Cu. B.Cu already carries a power pour (BAT_PACK_B), and In1 stays solid GND under it.

**Capacity at 15 K**
- From the cap row on, SYS has ≥ 14 A in parallel (In2 3.8 + B 10.7) and 8.8 A on F to the boost. Via capacity is ≥ 25 A at both ends (0.8/0.4 ≈ 1.5–2 A each).
- **Open:** the first ≈ 1.5 mm from pin 25 is single-layer F at 0.95 mm (2.8 A on the long-trace formula). The single 0.2 mm SYS pad and the 0.45 mm pin pitch set it.
  - The only further widening would be moving C311 (100 nF SYS). Its vertical orientation was tried, but it overlaps the U4 and C104 courtyards, so it stays.
  - This is a short neck between copper masses, not a long trace, but at 6–8 A it remains the limit of this footprint.

## MAJOR M1: U4 power-pad escapes

| Pad | Before | After |
|---|---|---|
| PMID 29 | 0.2 mm × 1.5 mm then 0.35 mm track | PMID_U4PIN_F pour: 0.30 mm × 0.2 mm at the pad end (pitch-limited, as for SYS), then ≥ 0.8 mm over C312.1 into C101.1 / PMID_F. SW1_F's idle lower-left corner was raised 0.55 mm. |
| VBUS_PD 2/3 | four 0.2 mm escapes | VBUS_U4A_F extended onto the pad ends: **0.6 mm neck** (pads 2 + 3 together), zone clearance 0.2 |
| VBUS_PD 8/9 | 0.2 mm track to C313/C111/vias | New VBUS_U4B_F pour: **0.6 mm neck** at the pad ends, ≥ 1.3 mm to C313.1, C111.1 and 5 vias (2 × 0.8/0.4 + 3 × 0.6/0.3) |
| BAT_INT 22/23 | 0.6 mm × 2.75 mm track (2.0 A) | BAT_U4PIN_F pour: **0.6 mm neck** at the pad ends, then ≥ 1.3 mm (3.5 A) to C106.1. The BAT_INT_F strip was widened from 1.3 to 1.9 mm (4.6 A) and its local clearance set to 0.2; the POWER_HI 0.4 rule still applies to tracks and vias. |

**Open: BAT on F.** BAT stays F-only from the pins to the BAT block (x 164) because the In2 crossing now belongs to SYS. That gives ≈ 3.5–4.6 A at 15 K against the plan's 9 A. It was 2.0 A before. The 0.6 mm pin pitch and the PROG/BTST2 escapes bound it.

## MAJOR M2: VBUS_PD_IN2

- **Where the neck really was:** the 1.5 mm neck reported at 147.4,122.4 is not there; that location is an artefact of the widest-path walk. Re-measured with a fixed walk, the neck was the row of six PMID-cap GND vias at y 114.3 across the strip. Widest single gap: 1.5 mm at x 141.7. Copper cut: 2.68 mm.
- **Fix:** those six vias were replaced by a column of three at x 142.0, against the strip's west edge. The GND pour was extended to x 141.4.
- **Result:** cut 2.68 → **7.24 mm** (3.3 A at 15 K for the 3 A input), widest path 1.5 → 2.3 mm. The 2.3 mm is the lane west of the C100 GND vias; parallel lanes are summed in the cut.
- **SW1 jumper via** (146.45,121.75): it does not form a neck (the strip is 4.9 mm wide beside it). It cannot leave the strip anyway, because C103.2 itself sits at x 147.3 inside it.
- **Trade-off:** C101/C108's own GND vias are now 2.8–5 mm away. The PMID HF loop is held by C312 (100 nF), which keeps its GND via beside the pad.
- No signal via was added in x 141–149, y 118–127.

## MAJOR M3: PVDD_AMP via feeds

| Pour / cap | Before | After |
|---|---|---|
| PVDD_U6L_F (U6 21/22) | 2 × 0.6/0.3 | 2 × **0.8/0.4**. The pour is boxed by AVDD/C284 above and the OUT_B+ switch node below, so a third via does not fit. 2 × 0.8/0.4 ≈ 3–4 A against 1–2 A per channel. |
| PVDD_U6R_F (U6 3/4) | 2 × 0.6/0.3 | 3 × 0.8/0.4 |
| PVDD_U7L_F (U7 21/22) | 0 in the pour (1 via beside C274) | 2 × 0.8/0.4 + 1 × 0.6/0.3, plus the C274 via |
| PVDD_U7R_F (U7 3/4) | 0 in the pour (2 at C273) | 3 × 0.8/0.4, plus the 2 C273 vias (now 0.8/0.4) |
| C272 (U6 22 µF) | 2 × 0.6/0.3 | new PVDD_C272_F pour, 4 × 0.8/0.4 + 2 × 0.6/0.3 |
| C271 (U6 22 µF) | 1 × 0.6/0.3 | 1 × 0.6/0.3. **Open:** there is no room. The AMP_FAULT_N diagonal runs 0.5 mm off the pad, and 0.8/0.4 at that via breaks the 0.3 mm switch clearance to L201. |
| PVDD_BOOST_F (boost output) | 8 × 0.6/0.3 | **16 × 0.8/0.4** (a second and third row at x 160.9–163.1) |

## MAJOR M4: USB pair (not fixable to 6 mm; waiver recommended)

**Deleting the DP bumps does not work.** It was tried (`r6k/ux.json`):
- physical skew goes from 0.2 mm to **7.37 mm** (DP 43.99 vs DN 51.36 mm);
- uncoupled length only drops from 17.34 to **14.90 mm** (DRC).

The bumps compensate 7.4 mm, not 0.2 mm. DN is longer for three reasons:
- **The D1 loop:** DN's pin (D1.5) sits on the east column while DN is the west lane, so DN has to loop round the top of D1 (≈ 4.4 mm).
- **The resistor end:** R172 sits 2.6 mm below R171.
- **The J1 bridge.**

**Uncoupled length without any tuning is ≈ 14–15 mm per net** (`r6k/usb_coupling.txt`):
- J1 interleave and bridges: ≈ 2.8 mm;
- D1 pin split and loop: ≈ 5.9 mm on DN;
- R171/R172/R173 stagger: ≈ 5 mm.

So ≤ 6 mm needs placement changes: D1 rotated so the DN pin faces the DN lane, and R172 beside R171. Even then the J1 bridges alone take ≈ 2.8 mm.

**DN's two fine vias at J1 cannot be removed.** The receptacle row is DP-DN-DP-DN (B6, A7, A6, B7), so one of the two bridges must change layer:
- DP's bridge runs on F behind the pads;
- a DN bridge on F would have to cross DP's A6 exit.
- Exiting DP from B6 instead would reverse the lane order, which must have DP on the east side to reach R173/R171 without crossing.

**Recommendation:** record a full-speed USB waiver (12 Mb/s, ≥ 4 ns edges, total pair 51 mm), or schedule the D1/R172 placement change. A symmetric option is to bridge DP on B as well (+2 vias), which would only balance the DRC via-height skew. No USB copper was changed in R6k.

## MAJOR M5: vias in SMD pads (7 → 3)

**Dogboned (4):**

| Pad | Via moved to | Distance | Note |
|---|---|---|---|
| C234.2 | 193.0,39.993 | 0.8 mm | GND via 193.45,39.3 stays 0.8 mm away; the B links were rebuilt cleanly |
| J7.2 (SWDIO) | 169.7,93.95 | 0.4 mm | |
| TP19.1 (NRST) | 177.4,95.636 | 1.65 mm | the B corner was then arced |
| R185.2 | 98.58,23.77 | 0.7 mm | |

**Remaining (3):**
- **R10.2** (U11 ADC4 divider): every spot within 3.5 mm that clears F (LDO_3V3 tracks), In2 (PDCTRL_SCL, PD_SINK_EN, LDO_3V3 1 mm) and B (PDCTRL_SDA) is taken. The best spot, 135.4,60.88, shorts PDCTRL_SCL on In2.
- **R224.1** (AUX coupling): the only adjacent spot, 191.75,37.55, is 0.61 mm from the AUX_DET In2 diagonal, which needs 0.93 mm. AUX_DET is the outer track of a three-track In2 bus (BT_PWR_EN, BT_UART_RX), so it cannot step away.
- **C215.1** (U24 AVDD 100 nF): boxed by the XO crystal track (0.4 mm clock clearance), C212 0.43 mm away, the C215.2 GND pad and the U24 pins. It needs C215/C212 moved or a filled and capped via (POFV).

## m6: acute acid-trap wedges (all 5 fixed)

All five listed wedges were fixed by merging the short stub into the junction: the trunk is cut 0.5–1.0 mm before the bend and re-aimed at the stub's via or pad, so no inside angle stays below 90°.

| Wedge | Change |
|---|---|
| 5V_LOGIC In2 171.0,54.5 | cut d = 0.75 |
| 5V_LOGIC In2 96.3,95.8 | cut d = 1.0 |
| SYS_RAW In2 94.95,74.05 | trunk re-aimed at the via (95.44,73.91) |
| LDO_3V3 In2 130.85,57.15 | cut d = 0.75 |
| HP_SEL_A F 171.15,67.0 | cut d = 0.5, ending in the U8 pin |

The same treatment fixed the other acutes:
- 5V_LOGIC 184.05,50.9;
- 5V_CODEC 161.55,88.9 and 150.55,66.15;
- 3V_AO 188.4,39.0.

Three acutes became tangent arcs: 3V3_AUDIO 182.45,106.75 (R 1.65), 3V3_AUDIO 173.5,59.1 (R 0.4) and 3V_AO 177.7,93.3 (R 0.6). USB_AUX_5V 93.05,75.15 now leaves the U20.5 pad directly.

## m4: GND vias beside audio vias (1 of 9 added)

- **Added:** one GND via at 184.6,64.6 for COM1 183.8,64.6.
- **Searched without a legal spot:** a 0.1 mm grid within 1.2 mm of the other eight, checked against every layer:
  - VMID_HP 189.95,38.4; C234-Pad2 191.09,37.67; COM2 173.55,62.22 and 184.85,62.0; HP_L 187.3,62.45; U10-INL- 188.0,61.6; U10-INR- 188.35,62.7;
  - the I2S BCK via 152.4,103.3.
- **Why:** these sit in the U8/U9/U10 mux area, where the 3V3_AUDIO In2 trunk and the slow In2 nets fill the gaps the F audio tracks leave. One example: 188.4,60.9 is free on F and B but hits 3V3_AUDIO on In2.
- **What it would take:** moving the 3V3_AUDIO In2 trunk 0.5 mm. That was not done in this pass.

## MAJOR M6: power vias 0.8/0.4

- **Method:** every POWER_HI/PVDD via was upsized to 0.8/0.4. Each one DRC then flagged was reverted (`route_r6k_upsize.sh`, 2 rounds), and new arrays were added where room allowed.
- **Result:** 179 of 207 power vias are 0.8/0.4.

| Field | Vias now | Note |
|---|---|---|
| U4 VBUS | VBUS_U4A 2 + VBUS_U4B 2 (0.8/0.4) + 3 × 0.6/0.3 | two-row arrays at U4 VBUS do not fit: VBUS_U4A_F is 4.5 mm² between C100, C312 and BTST1 |
| SYS | 14 + 18 (0.8/0.4) | U4 cap field + SYS_COL_B ends |
| BAT block | 22 (0.8/0.4) | |
| Boost output | 16 (0.8/0.4) | |
| VBUS_PD (all) | 16 × 0.8/0.4 + 4 × 0.6/0.3 | no new vias at U11 (plan 15 at VBUS_IN/PPHV unchanged) |

**Vias that must stay 0.6/0.3** (an upsize broke clearance), plus one fine via:

| Net | Vias (x,y) |
|---|---|
| BAT_INT | 168.0,109.3 |
| BAT_PACK | 100.46,91.37; 140.25,101.65; 150.0,101.65 |
| PVDD_AMP | 102.7,126.3; 103.5,126.3; 116.8,124.85 (L201 SW pad); 186.09,128.3; 188.7,129.15 |
| SYS_RAW | 95.44,73.91; 117.05,35.45; 140.05,106.0; 150.0,106.0 |
| USB_VBUS | 140.4,47.4; the 8-via field 141.3–143.7 × 50.62/51.25 (0.8 pitch, neighbours); 143.85,54.7 |
| VBUS_PD | 144.6,60.4; 147.65,124.6; 148.3,128.0; 148.6,125.8 (new) |
| SYS_RAW fine via | 152.62,119.4 (0.5/0.2, NECK_U4) |

## Corner-rule cleanup (coordinator extra scope): 49 → 7

**Method:** `route_r6k_arcfix.py`, a new helper, replaced the hits with 30 true tangent arcs and 9 stub merges; one more (USB_AUX_5V) was fixed by a direct pad exit. Every new piece passed the R6j smoother legality checks; DRC, open edges, islands and via-in-pad were re-run after each pass.
- **Arc radius:** all 30 arcs are ≥ 2 × w, except:
  - SYS_RAW In2 jog 112.0,107.0: R 2.8 mm = 1.4 w;
  - 3V3_AUDIO F 146.05,80.45: R 0.75 mm = 1.9 w;
  - the two acute-wedge arcs: 3V_AO R 0.6 mm = 0.6 w and 3V3_AUDIO R 0.4 mm = 1.3 w.
- **Stub merges:** 9 acutes were removed by merging the stub into the junction.
- **Hits created and fixed in this pass:** NRST B (from the TP19 dogbone) and the two Q103-G B corners (from the new route).
- **Rejected:** an R 0.4 arc at the USB_DP J1 jog. It was DRC-legal, but it raised the DRC uncoupled length 17.34 → 17.58 mm, so it was reverted.

**Remaining 7:**

| Hit | Middle / limit | Reason it stays |
|---|---|---|
| 3V_AO In2 corner 167.55,99.95 | 1.87 / 3.0 mm | 1.0 mm In2 trunk double chamfer round a via cluster, already ≈ 2.3 mm equivalent radius; arcs ≥ 1.0 mm hit the island outline (0.3 mm) or vias |
| 3V_AO In2 corner 172.2,99.95 | 2.12 / 3.0 mm | same S-shape, same obstacles |
| USB_DP corner 148.025,57.4 | 0.61 / 0.75 mm | DP peels off the pair to R173.1/R171.1; an arc ≥ 0.4 mm collides with DN at the 0.15 mm pair gap or with the R173 pad; tied to the M4 placement change |
| USB_DP jog 149.23,27.05 | 0.27 / 0.75 mm | J1 A6 pad exit; the only legal arc raised the DRC uncoupled length (above); genuine pin escape |
| Net-(U2-D-) corner 151.1,63.905 | 0.29 / 0.6 mm | U2 pin escape inside NECK_U2_USB (0.2 mm area); an arc leaves a 0.2 mm remnant outside the area (width_audio DRC); genuine pin escape |
| Net-(U24-AVDD) B corner 152.75,78.9 | 0.70 / 1.2 mm | B jumper to the C215 in-pad via, squeezed round the C215/C212 GND via 151.85,79.0 inside BKO_ADC; clears only with the C215 placement change (M5) |
| Net-(U7-OUT_B+) F corner 188.6,130.055 | 0.21 / 1.2 mm | U7 pin-23 escape between the PVDD_U7L pour and the BST_B+ vias; genuine pin escape |

## Exceptions used

- **Part moves:** none (C311 was trialled and reverted; see B1).
- **Zone polygons and pours:**
  - Polygons changed: SW1_F/SW2_F trims, SYS_U4CAP_F, BAT_INT_F, SYS_BOOST_F, BAT_INT_IN2, SYS_IN2, VBUS_U4A_F, GND_U4_TOP_F (extended west 0.9 mm).
  - Local clearance set to 0.2 on BAT_INT_F and VBUS_U4A_F, and on the new pin pours, for pads only; the POWER_HI 0.4 rule still applies to tracks and vias.
  - New pours: as listed under Gates.
  - **B.Cu SYS pour (SYS_COL_B):** a power pour on B.Cu, like BAT_PACK_B.
- **Via moves:**
  - Q103-G via 155.55 → 154.95,120.1 (still in NECK_U4 and SYS_IN2; the same island-via count);
  - SW2 B jumper bend 0.35 mm west inside NECK_U4;
  - C106/R102 GND vias out of the column;
  - PMID-cap GND vias to x 142.0.
- **Q103-G B route:** now along y 115.3, with two arcs.
- **Arcs:** arcs are used on signal and power copper (see the corner section). KiCad teardrops (GUI) handle arcs.
- **Not used:** any DRC rule change, any new island via of a signal net, any In2 signal on an audio/I2S/USB/clock net.

## Left open (and why)

1. **SYS first 1.5 mm from pin 25 and BAT pins → x 164 on F only:** 2.8 A and 3.5–4.6 A IPC long-trace ratings against 6–9 A. Set by the U4 pad pitch and the SYS/BAT crossing. Next steps: a footprint/placement review of C311, C106, R102 and PROG, or accepting it as short-neck heating with a thermal check.
2. **USB uncoupled 17.3 mm (rule 6 mm) and DN's J1 vias:** needs D1 rotated and R172 moved; otherwise a full-speed waiver.
3. **Via in pad R10.2, R224.1, C215.1:** needs In2 slow-net re-routing (R10, R224) or a C215/C212 placement nudge, or POFV.
4. **Seven audio/I2S vias without a GND via within 1.2 mm:** needs the 3V3_AUDIO In2 trunk moved.
5. **J7 NRST/SWCLK:** unchanged; the coordinator's J7 decision is still pending.
6. **C271 single via:** see M3.

## Helpers (new, `ai-files/helpers/`)

| Helper | Purpose |
|---|---|
| `route_r6k_edit.py` | `route_r6g_edit.py` + `viasize`, `viabox`, `movevia`, `rmzone`, `zoneset` |
| `route_r6k_step.sh`, `route_r6k_eval.sh` | R6k rules, island reference R6k-0 |
| `route_r6k_neck.py` | widest path, zone unions, pads count as copper |
| `route_r6k_cut.py` | minimum copper cross-section |
| `route_r6k_dump.py` | items in a box |
| `route_r6k_addvias.py` | greedy legal via placement |
| `route_r6k_vsz.py`, `route_r6k_upsize.sh` | 0.8/0.4 upsizing with DRC-driven revert |
| `route_r6k_dogbone.py` | via-in-pad dogbone search |
| `route_r6k_arcfix.py` | tangent-arc and stub-merge corner fixer |
| `route_r6k_why.py` | legality verdict for one segment |
| `route_r6k_usbcpl.py` | per-section coupling of a pair |
| `route_r6k_audiogv.py` | audio vias versus nearest GND via |

**Intermediate boards need their `.kicad_pro`/`.kicad_dru` beside them before any pcbnew refill.** Without them the filler ignores the custom rules: this produced bad BAT_INT_F fills once, which were caught and redone.

**Reproduction chain** (specs in `work-r6/r6k/`):
1. R6k-0 + k1, k2, k3, k4 (`route_r6k_step.sh`);
2. k5 (edit) + k5v (`route_r6k_addvias.py`), then k5b;
3. `route_r6k_upsize.sh … POWER_HI,PVDD`, then k6a;
4. `route_r6k_dogbone.py` on the 7 pads, then k7c;
5. `route_r6k_arcfix.py` (`--skip 151.1,63.905`), then `--kinds acute --rmin 0.5` twice (arc then stub merge), then `--rmin 1.0`;
6. k8f;
7. addvias k9v;
8. k10 (USB_DP arc reverted);
9. addvias k11v.
