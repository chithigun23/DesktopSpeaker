# Routing R6e (2026-10-09): authorised placement moves and hand routing on R6d-final

Work copies only (`ai-files/pcb/work-r6/R6e-*`). Rules file `R6e.kicad_dru` is identical to `R6d.kicad_dru`; only the BKO_MUX rule-area outline changed (see Copper changes).

- **Final board:** `work-r6/R6e-final.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`, `.drc.json`, `.open2.json`).
- **Hand specs:** `work-r6/r6e/E1–E7.json`.
- **Renders:** `ai-files/pcb/route-r6e-top.png` (F.Cu) and `route-r6e-bottom.png` (B.Cu).
- **New helpers:**
  - `helpers/route_r6e_edit.py`: R6d edit ops plus footprint `move`/`moveby`.
  - `helpers/route_r6e_step.sh`: DRC, fragment-aware open edges, silk count.
  - `helpers/route_r6e_gndnear.py`: legal GND via spots near a point.

`DesktopSpeaker-kicad/` was not touched. Nothing was committed.

## Result

| | R6d-final | R6e-final |
|---|---|---|
| Open edges (fragment-aware, all nets) | 48 | **41** |
| Default / I2C / AUDIO / I2S_CLK / PWR_LOCAL | 26 / 9 / 9 / 3 / 1 | 21 / 9 / 8 / 3 / 0 |
| Power classes | 0 | 0 (power-net connectivity unchanged) |
| DRC clearance, shorts, dangling, isolated copper, track width, annular, courtyard | 0 | 0 |
| DRC USB items | 3 skew, 1 uncoupled | same (unchanged, see USB) |
| Silk/lib items | 33 | 33 |
| Vias 0.6/0.3 + 0.5/0.2 | 607 + 27 = 634 | 619 + 31 = 650 (GND 240, signal 410) |
| Via centre in an SMD pad | 11 | 11, same list (C215.1 still in it) |
| EP vias U6 / U7 / U25 | 16 / 16 / 8 | 16 / 16 / 8 |
| Antenna keep-out items | 1 (old GND track, 89.40,26.37) | 1 (same) |
| Foreign non-GND vias in In2 islands | 24 | 24 (no new ones; no signal on In2) |

**Closed (7):** Net-(U10-CPP), Net-(U25-FSW), Net-(U25-MODE), AMP_BOOST_EN at U25 (R255–U25.2), Net-(R18-Pad1), Net-(U9-NO2), PD_SINK_EN.

## Placement moves (all mm-scale; refdes and values kept, courtyards clean)

| Part | Move | Reason |
|---|---|---|
| C243 | (199.09,65.03) rot −90 → (199.50,64.15) rot 0 (0.97 mm) | CPP runs straight at y 65.03. GND goes to R236.2. |
| C245 | 0.30 mm south | Courtyard room for C243 |
| **R252** | (151.26,142.34) rot 180 → (150.30,146.55) rot −90 (**4.3 mm, > 1.5 mm**) | FSW resistor now sits in the pocket beside U25 pins 3/4. FSW stub is 1.2 mm; R252.2 lands on the SW pour. |
| C267 | (151.26,143.64) rot 0 → (150.55,143.20) rot 90 (0.84 mm) | Frees the column north of U25.2 for AMP_BOOST_EN. SW track and BOOT via are unchanged. |
| C314 / C270 / C290 | 0.10 / 0.06 / 0.06 mm east | Gap for MODE between U25.12 and C314.2 |

- These are 0402/0805 passives, so CAD fit is unaffected.
- Not done:
  - R230/R231 swap: their other pads (C234/C235-Pad2) would then cross over U9.
  - U9 rotation, R18 move, C201/C233/R258 relocation: see the open edges below.
  - C212/C215 north shift: XO track and the Y200 courtyard. C215.1 stays a via-in-pad, to be filled and capped (IPC-4761 VII).

## Copper changes

- **USB_VBUS:** via 135.75,49.50 removed. C184.1 keeps via 136.55,49.50. This opens the C184 pad gap for R18. USB_VBUS vias 22 → 21.
- **U3 top row:**
  - CTRL_SCL now leaves pin 60 north (x 184.2) to y 80.3, then NE to TP16.
  - BT_TX_IND via moved to 183.20,80.95 (0.5/0.2).
  - PD_SINK_EN escapes pin 63 west at y 81.55 to a 0.5/0.2 via at 181.30,81.00.
- **PD_SINK_EN route (A\*):** about 150 mm, 13 vias. It goes north-east round BKO_MUX (x 202), then west at y 59–60 and along F.Cu y 43–47 to U11. It is legal but long. It is the first candidate for re-routing if U3 pins are reassigned.
- **U9:**
  - NO1 now uses a 2.1 mm B.Cu jumper under the U9 body (0.5/0.2 vias at 183.80,65.95 and 185.90,66.20).
  - NO2 runs on F.Cu under the body at y 65.3 into pin 4.
  - BKO_MUX notch widened west to x 183.4 and down to y 66.75 to allow that jumper.
  - GND vias added at 183.04,65.95 and 186.10,67.33.
- **Older jumper GND vias:**
  - SDATA: added at 150.84,100.70.
  - VMID_HP (189.95,38.40) and C234-Pad2 (191.09,37.67): no legal spot within 1.5 mm.

## USB and I2S lengths (unchanged from R6d)

**USB:**
- Copper per net: DP 51.59 mm and DN 51.36 mm (0.23 mm apart, both bridge branches included).
- KiCad skew: −2.94 mm. It counts both J1 bridge branches.
- The −51.7 / −51.2 mm items are the known U2-side net-grouping artefact.
- Uncoupled length: 17.6 mm. This is not cheap to fix: it is the D1 pass-through U-loop plus the J1 bridges and needs a D1 placement or pad-entry change.

**I2S:**
| Net | Length | Vias |
|---|---|---|
| BCK | 112.6 mm | 0 |
| SDATA (ADC to U6) | 62.1 mm | 3 |
| LRCK (R208 to TP13 only) | 3.3 mm | 0 |

## Open edges (41) and why

A\* (route_r6c_route, F+B, all classes) was run on all 32 open nets after the moves. All 32 failed: unreachable pad or exhausted search. Each failure is a structural enclosure rather than a corridor-length problem.

**Default (21)**

- **U3 legs (5V_LOGIC_EN, ADC_INT, AMP_BOOST_EN U3.24, AMP_FAULT_N U3.25, BT_UART_RX U3.20, BT_FORCE_PWM U3.37, CHG_QON_SENSE U3.3, HP_EN U3.15, HP_SEL_B U3.14):** the pin assignment fights the geometry.
  - Bottom-row pins 20/24/25/26 are capped by the AUD_SCL F run at y 95.0. That run is AUD_SCL's only link to R209/U24.
  - Left pins 14/15 are boxed by the NRST riser (x 179.1), the HP_SEL_A via (181.55,90.55) and the HP_G0 diagonal.
  - Pin 3 is wrapped by PD_PLUG_EVENT.
  - Pin 37 is capped by the BT_PWR_EN via at 193.10,90.05 and the CHG_ENABLE stub.
  - Top-row pin 59 is boxed on F by the CTRL_SDA/CTRL_SCL risers and on B by BT_TX_IND/BT_MFB. An escape via at 184.77,81.15 was tried; A\* found no path and it was removed.
  - The north-row free pins (PD0–PD6) are capped by the BT_RST_N run (pin 58 to 189.6,80.6).
- **U4 (CE_N, ILIM_HIZ, TS_SENSE, BATP, QON, CHG_INT, and the U4 end of CTRL_SCL/SDA):**
  - No signal via is legal around U4: it sits in SYS_IN2/VBUS_PD_IN2, with BAT_INT_IN2 to the east.
  - The F.Cu exits run into the BAT_INT_F / SYS_BOOST_F / SYS_U4CAP_F pours. The only pocket (x 156–161, y 121.5–124.85) is a dead end.
  - The B.Cu exit north is walled by AMP_PDN B (y 105.6–110, x 127–170, inside the island zone) and the SW1/SW2 B tracks (1 mm rule).
  - A SYS_IN2 bay at x 149.7–153.9, y 124.5–129.6, plus R103 moved 0.4 mm east and C313 moved 0.1 mm west, would give QON/CE_N/CTRL vias. Their B legs still hit the AMP_PDN wall, so AMP_PDN B must also move north of y 104 (x 140–170). Not applied, because it gains nothing on its own.
- **AMP_FAULT_N U7.9, Net-(U7-PDN):**
  - AUD_SCL reaches U7.16 by a loop round the south of U7 that encloses pin 17.
  - Everything south-west of BCK at U7 is unreachable. BCK takes the only channel (x 178, between the Q103 pour and Q101/Q102), and the lower corridor lies in BAT_PACK_IN2 and BKO_U7.
- **MCU/NRST, MCU/SWCLK at J7:**
  - The TC2030 pads are boxed by the NPTH holes, the SWDIO via-in-pad and its B run, AUD_SCL F and ENC_A B.
  - J7 duplicates J6 (same SWD nets), so J6 serves alone. J7 is left with SWDIO, 3V_AO and GND only.

**I2C (9):** AUD_SDA ×4 (U24.23, R210, U6.15, U7.15), AUD_SCL U6.16, CTRL_SCL/SDA ×4.
- AUD_SDA cannot reach U24.23 from the south-west past R209/R211/GAUGE.
- The U6 and U7 legs need the same planned bundle as I2S (below).
- The CTRL legs start at TP15/TP16 and U4 and hit the U3 west walls and the U4 enclosure.

**I2S_CLK (3): LRCK ×2, SDATA to U7.**
- LRCK needs two crossings: the BCK/SDATA risers from R207/R206 (U7 leg) and BCK's U6 leg (U6 pin order SDATA/BCK/LRCK). That breaks the one-jumper rule.
- SDATA to U7 must sit south-west of BCK, which the x 178 channel cannot hold.

**AUDIO (8):**
- **BT_AUDIO_L/R (×4):** about 80 mm from BM83 to the ADC cap column. C202.1 and C203.1 are enclosed by the C233-Pad2 / R223 wrap.
- **USB_AUDIO_R:** C201.1 is enclosed by C200-Pad2, and both nets have used their jumper. C201 cannot reach the area north near C187: the C176/C174 pads and the BT_PWR_EN / PD_PLUG_EVENT / PDCTRL_SCL F hops close the x 161–164 strip.
- **C205-Pad2:** about 60 mm, same corridors.
- **U8 COM1/COM2:**
  - With the BKO extension, COM1 alone could take a 12.5 mm B jumper under U8–U9 (U9 via 183.8,64.6 to U8 via 171.3,64.6).
  - COM2 cannot also get one: at U9 it must pass COM1's via, and at U8 pin 6 is wrapped by NC2. The under-body space at U9 is now used by NO1/NO2.

## Smallest changes to close the rest

**1. Schematic: MCU GPIO reassignment (plain GPIOs only; AFs checked in the STM32G071 datasheet LQFP64 table).**

| Net | From | To |
|---|---|---|
| BT_UART_TX | PA2 (19) | PD5 (55), USART2_TX AF |
| BT_UART_RX | PA3 (20) | PD6 (56), USART2_RX AF |
| BT_FORCE_PWM | pin 37 | PD4 (54) |
| CHG_QON_SENSE | pin 3 | PD3 (53) |
| HP_SEL_B | pin 14 | PD1 (51) |
| HP_EN | pin 15 | PA15 (47) |
| 5V_LOGIC_EN | pin 59 | PA1 (18) |

The top-row targets also need BT_RST_N to leave pin 58 straight to B.Cu, which frees the area north of pins 50–56.

**2. Schematic: TP13/TP14 swap** (or LRCK/SDATA order at TP level). LRCK then needs only one crossing (its U6 leg).

**3. PCB, one planned re-route of the south-of-U3 band** (x 140–200, y 88–126), instead of net-by-net:
- Move AMP_PDN B north of y 104 and re-route BT_UART_TX's U3-to-TP21 loop.
- Make the CHG_SYS_ENABLE / AMP_PDN junction near Q102 local.
- BCK takes its single B jumper under the Q101/Q102 cluster (y < 107.5). This frees the x 178 channel for SDATA.
- Run U7 as one bundle, south-west to north-east: PDN (R258), SCL, SDA, SDATA, BCK, LRCK, FAULT. SCL/SDA/FAULT cross the I2S pair on B north of y 107.5.
- Drop the AUD_SCL loop round U7.
- Add the SYS_IN2 bay under U4 (item above) and a PVDD_IN2 notch at x 147.2–148.6, y 140–141.1 for the AMP_BOOST_EN via at 147.9,140.4.

**4. Audio:**
- Rotate C233 (−90) and move R223 about 0.7 mm east to open a 1.2 mm channel east of the cap column for BT_AUDIO_L/R.
- Move C201 near C187 so that C201-Pad2 crosses C200-Pad2 where C200-Pad2 is on B (y 49.4–55.3). This needs C176 moved about 0.3 mm west.

**5. U8/U9:** rotate U9 180° (all 10 pins re-routed), or let COM1 and COM2 each take a long B jumper under U8–U9 with NC2 re-routed under U8. Either is a rule exception for AUDIO jumper length.

## Gates run per batch

The following were run after every spec: DRC, open2, via-in-pad, EP counts, islands, antenna keep-out, and power-class open edges (0).
