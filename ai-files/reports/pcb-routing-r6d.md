# Routing R6d (2026-10-09): hand routing on R6c-final

Work copies only: `ai-files/pcb/work-r6/R6d-*`. Rules: `R6d.kicad_dru`. Hand specs: `work-r6/r6d/*.json`, applied with `helpers/route_r6d_edit.py` through `helpers/route_r6d_step.sh`. Final board: `work-r6/R6d-final.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`, `.drc.json`, `.open2.json`, `.metrics.json`). Renders: `ai-files/pcb/route-r6d-top.png` (F.Cu) and `route-r6d-bottom.png` (B.Cu). Nothing in `DesktopSpeaker-kicad/` was touched. No commit.

## Result

| | R6c-final | R6d-final |
|---|---|---|
| Open edges (fragment-aware, all nets) | 105 | **48** |
| Default / GND / AUDIO / I2C / USB / I2S_CLK / PWR_LOCAL | 37 / 26 / 16 / 10 / 9 / 4 / 3 | 26 / 0 / 9 / 9 / 0 / 3 / 1 |
| Power classes (PWR_5V, PWR_3V, POWER_HI, PVDD, SWITCH, BOOT, BAT) | 0 | 0 |
| DRC: clearance, shorts, dangling, isolated copper, track width, hole/annular | 0 | 0 |
| DRC: USB diff-pair items | 0 (no pair routed) | 3 skew + 1 uncoupled (see USB) |
| DRC: silk/lib items (unchanged) | 33 | 33 |
| Vias total (0.6/0.3, 0.5/0.2) | 594 (568, 26) | 634 (607, 27) |
| GND vias | 221 | 237 |
| EP vias U6 / U7 / U25 / U11 thermal | 16 / 16 / 8 / 8 | 16 / 16 / 8 / 8 |
| Via centre in an SMD pad | 11 | 11, same list (C215.1 not fixed, see below) |
| Antenna keep-out items | 1 (pre-existing GND track at 89.40,26.37) | 1 (same) |
| Non-GND vias of other nets inside In2 islands | 20 | 24 (+2 5V_LOGIC, +2 U24-LDO; all local power nets, no signal vias) |

## USB
- J1 to U2 is routed as a 0.25/0.15 coupled pair. DP is bridged north of the J1 pads. DN is bridged on B.Cu using 0.5/0.2 vias in NECK_J1.
- Both lines pass through their D1 pads, so there are no stubs. D+/D- enter U2 at 0.2 mm inside NECK_U2_USB.
- Skew:
  - A 5-bump DP serpentine (7.6 mm) on x 148.0 matches the end-to-end paths.
  - KiCad's net-length skew is −2.94 mm. It counts both J1 bridge branches: DP 51.59 mm vs DN 54.53 mm.
  - The −51.7 / −51.2 mm items are an artefact: KiCad groups the 2.8 / 3.3 mm U2-side nets (Net-(U2-D±), after R171/R172) with the connector nets.
- Uncoupled length is 17.6 mm, against a limit of 6 mm. It comes from the D1 pass-through U-loop and the J1 bridges.
- BT_MFB and USB_AUX_5V crossings moved to B.Cu with vias west of the reshaped USB_VBUS In2 island.

## I2S lengths (copper per leg)
| Leg | Length |
|---|---|
| BCK ADC (R207) to TP12 | ≈ 8 mm |
| BCK TP12 to U6 | ≈ 48 mm |
| BCK TP12 to U7 | ≈ 58 mm (total net 112.6 mm) |
| SDATA ADC to U6 | 62.1 mm, 3 vias |
| LRCK | only R208 to TP13 (3.3 mm) |

The LRCK legs and SDATA to U7 are open (see below). Every routed leg is under 70 mm.

## Power copper changes
- **USB_VBUS_IN2:** the outline was reshaped (west/south notch for the signal vias). Two USB_VBUS vias were removed (USB_VBUS vias 24 → 22). C182.2/C183.2 now share a GND link.
- **5V_LOGIC:** the In2 hop was re-made. It now runs 140.60,61.50 → B.Cu → an F.Cu hop 144.95–146.40 over the PDCTRL_SCL branch → via 149.95,62.25 → In2. Its vias at 144.95 and 146.40 lie in VBUS_PD_IN2, as power-net precedent allows.
- **3V3_AUDIO:**
  - B.Cu/In2 hop via moved to 152.20,76.60.
  - Lower via moved to 150.30,90.50, with the In2 feed re-routed. The old 1.5 mm In2 bar was removed.
  - The U10 feed now runs through B.Cu (194.24,62.14 → 197.30,61.30).
- **Net-(U24-AVDD):** via moved to 152.45,78.30.
- **VCCP2I:** 0.25 mm via B.Cu. **USB_AUX_5V:** reworked around U20. **BT_PWR_EN:** loop widened at R152.
- **U24-LDO:** B.Cu jumper 148.70,81.35 → 144.30,78.00. Both vias lie in VBUS_PD_IN2.
- **SYS_RAW at U14:**
  - The F.Cu loop that enclosed U14 pin 1 was removed.
  - Pin 2 and C140.1 now go through a new via at 91.85,99.95 and a 0.6 mm In2 stub to the 2 mm SYS In2 track. SYS_RAW vias 52 → 53.
  - SYS_RAW stays connected.
- **PVDD_AMP:** the second C271.1 via (116.00,124.85) was removed to pass AMP_FAULT_N. C271.1 keeps one via (116.80,124.85). PVDD vias 20 → 19.
- **Width floors:** no power track is below its plan minimum. Power-net connectivity is unchanged: every power class has 0 open edges in open2.

## Rule changes (R6d.kicad_dru)
- `usb_pair_gap`: 0.15 mm USB-to-USB clearance (the coupled-pair gap).
- `usb_u2_entry`: 0.2 mm USB width, inside rule area NECK_U2_USB only.
- `usb_diff` uncoupled limit raised from 3 to 6 mm.
- `bko_tracks` / `bko_vias`: Net-(U24-LDO) added to the local-power exceptions.
- **Keep-out trims:**
  - **BKO_ADC:** lower edge raised to y 89.4 for x 145.5–152.0 (U24 digital side only).
  - **BKO_MUX:** a notch at x 186.6–193.85, y 62.3–66.7, between the U9 and U10 bodies (passives only). It carries the HP_L, INL- and INR- jumpers.

## Progress log
| Step | Open edges | Work |
|---|---|---|
| R6d-0 (= R6c-final) | 105 | |
| u1–u7 | 80 | USB VBUS island, BT_MFB / USB_AUX_5V / CC1 / CC2, USB pair and serpentine, PDCTRL_SCL / R15, 5V_LOGIC hop, SEL0, C200-Pad2, U2 top side (VCCP2I, VOUTL/R, XTO), U11 GND, PD_SINK_EN U11 side |
| g1/g2 | 66 | All GND leftovers, each with a via beside the pad |
| a1/a2 | 57 | U24 VIN fan-out, AVDD / 3V3_AUDIO via moves, BCK, AUD_SCL to R209, ADC_INT pin side, LDO jumper |
| m1 | 56 | U20-PR1, USB_AUX_5V around U20 |
| m3 | 54 | U8 NO2 outer route, U8 pin 3 GND, HP_SEL_A U8.5, R235.2 GND, HP_SEL_B R235.1 to U9.1 |
| m4 | 51 | U10 INL- and INR- (B.Cu jumpers in the BKO_MUX notch, GND via 192.35,65.07 between them), HP_L (B.Cu jumper north of U9) |
| m5 | 50 | 5V_LOGIC_EN R142 to U14.1 |
| m6 | 49 | AMP_FAULT_N R262.2 to the U6 pin track |
| m7 | 48 | U16-NC, B.Cu U5.7 to U16.1. U17-NC via moved to 101.0,86.3 to free U5.7 |
| m8 = final | 48 | GND vias 182.60,61.00 and 190.20,63.40 beside the new HP_L / INL- / INR- jumpers |

## Open edges (48) and reasons

### Blocked locally: smallest placement change proposed

| Net (edges) | Blocker | Proposal |
|---|---|---|
| Net-(U10-CPP) (1, PWR_LOCAL) | C243 (HPVDD cap) straddles the U10.11 → C245.1 line. The gap between its pads is 0.41 mm. B.Cu is BKO_MUX, or the B.Cu verticals AUX_DET/HP_DET/BT_TX_IND/BT_RST_N at 0.65 mm pitch east of it. | Rotate C243 horizontal north of the pin-12 row, ≈(199.5,64.1), with its GND to a via. CPP then runs straight at y 65.05. |
| Net-(U25-FSW), AMP_BOOST_EN U25 side (2) | U25 NW corner is closed by the SW arc L200 → R252.2 → C267.2, C267 and the VCC stub to C265. | Shift C265 about 0.6 mm east and move C267, or re-route VCC. |
| Net-(U25-MODE) (1) | Boxed by C314 (156.1,147.08/148.22) and pins 12/14. | Shift C314 about 0.3 mm east. |
| Net-(U7-PDN) (1) | R258 (189.49,122.1) sits north of the AUD_SCL wrap and the I2S approach. BKO_U7 and the PVDD/BAT_PACK In2 islands leave no via spot. | Relocate R258 next to U7.17, or re-route AUD_SCL from the north. |
| Net-(U9-NO2) (1) | R230/R231 are swapped relative to U9 pins 2/4 under BKO_MUX. | Swap R230/R231. |
| Net-(R18-Pad1) (1) | Needs to go east past the VIN_LOW 0.5 mm track and the PD_PLUG_EVENT / VIN_LOW pin stubs. The only gap, C184.2–C184.1, needs 0.4 mm VBUS clearance and is closed by the VBUS vias 135.75 / 136.55,49.50. | Move R18 to the east side of C184, or drop one VBUS via. |
| Net-(U8-COM1/COM2) (2), HP_SEL_B U9.5 (1 of 2) | All F.Cu exits of U9 pins 5/7/9 are closed: the 3V3_AUDIO pin-8 riser (audio_clear 0.5), the NO1 track over pins 3–5, the pin-3 GND hook and HP_OUTR at y 69.3. B.Cu is BKO_MUX. | Rotate U9 180°, or extend the BKO_MUX notch over U8–U9, and feed U9.8 3V3 from C237 on B.Cu. |
| USB_AUDIO_R (1) | C201.1 is enclosed by C200-Pad2 and must cross USB_AUDIO_L / VOUTR at C187. Both USB_AUDIO_R and C200-Pad2 already use their single B.Cu jumper. | Mirror the L channel: place C201 beside C200 near C187, or give USB_AUDIO_L a B.Cu hop at x 164.5. |
| BT_AUDIO_R C233–C203 (1 of 2) | C203.1 is enclosed by C202 and the C233-Pad2 wrap. A B.Cu jumper would cross PDCTRL_SDA B.Cu. | Move C233 to the east of R223, or route PDCTRL_SDA B.Cu around the C202/C203 column. |
| /MCU/SWCLK, /MCU/NRST at J7 (2) | TC2030 pads are boxed by the leg holes, the SWDIO via and B.Cu, J7.5 GND and its via, AUD_SCL F.Cu and the ENC_A B.Cu wall. | Add NECK_J7 (0.5/0.2 vias at the pad-quad centres 170.13 / 171.40,95.31), re-route SWDIO B.Cu north through the hole gap, and move the J7.5 GND via. Alternatively, J7 duplicates J6 (same SWD nets), so J6 can serve alone. |
| Net-(U4-QON) (1), CE_N / CTRL_SCL / CTRL_SDA at U4 | U4 sits wholly inside SYS_IN2 (x 149.7–157.2, y 106–133.4), so no signal via fits within about 10 mm of the bottom row. The bottom-row 0.4 mm pitch, the C313 GND pad and R103 leave room for at most two dog-bones. | Notch SYS_IN2 at x 151.6–153.75, y 124.5–129.3 for the CTRL_SCL / CTRL_SDA / CE_N vias, and move R103 0.4 mm east for QON. QON's far end (140.6,24.05) is 100 mm away. Consider moving the QON button / test point near U4. |
| C215.1 via-in-pad (pre-existing, not an open edge) | C215.1 is boxed by the C215.2–C212.2 GND link, the XO track, C212.1 and the U24 pins. There is no 0.45 mm via spot beside the pad. | Move C212/C215 0.6 mm north, or accept a filled and capped via-in-pad (IPC-4761 type VII). |

### Long nets not attempted (router and hand attempts found no escapes)
- **U3 MCU legs:** BT_UART_RX/TX, BT_FORCE_PWM, CHG_QON_SENSE, 5V_LOGIC_EN (U3.59 leg), PD_SINK_EN (U3 leg), HP_EN, HP_SEL_B (U3 leg), ADC_INT (U3 leg), AMP_FAULT_N (U3 and U7 legs), AMP_BOOST_EN (U3 leg), CHG_INT. These are 25–100 mm cross-board.
- **U3 escapes are the limiting factor:**
  - The NRST F.Cu riser at x 179.10 (y 90.05–94.40) blocks the left-column pins 13–16 at 0.34 mm.
  - The 3V_AO via 178.40,93.30 blocks the move-west option.
  - AUD_SCL F.Cu at y 95.1 runs under the bottom row.
  - B.Cu diagonals fan out from under U3.
- **Proposal for U3:** reassign the plain GPIOs to free pins. Free pins are PD0–PD6 (50–56, top row), PB12–PB15 (32–35), PA1/PA5/PB0 (18/22/27), PD8/PD9 (40/41), PA15 (47) and PC11/PC12 (1/2). Move the NRST riser east of C162 / R106, with 3V_AO via to 176.6,93.6.
- **Charger:**
  - CE_N, ILIM_HIZ, TS_SENSE and BATP are blocked by SYS_IN2 / VBUS_PD_IN2 around U4, as above.
  - The SW2 B.Cu wall (needs 1.0 mm) and the REGN B.Cu diagonal meet the BAT_INT via field at x ≈ 165, which closes the B.Cu corridor to Q100.
  - BATP is critical: it needs 2 mm from SW / BOOT.
- **I2C:** CTRL_SCL/SDA (U4 to U3 and to the U16 / U12 area), AUD_SDA (U24, U3, U6, U7, R210), AUD_SCL (U6 leg).
- **I2S:** LRCK U6 and U7 legs, SDATA U7 leg.
  - The pin order at U6 (SDATA, BCK, LRCK, west to east) is the reverse of the TP order (LRCK, BCK, SDATA, north to south). LRCK must therefore cross both BCK and SDATA.
  - The only B.Cu crossing outside BKO_U6 lies in the pocket between BCK and the AMP_FAULT_N / 3V3_AUDIO / C280 wall.
  - **Proposal:** swap TP13 and TP14 (test-point order only), or pin-swap LRCK / SDATA in the schematic net labels at TP level.
- **Audio:** BT_AUDIO_L/R BM83 legs (≈80 mm F.Cu across the board, one jumper each). C205-Pad2 (R205 (156.95,89.28) to C205 (192.49,41.97), ≈60 mm). BT_AUDIO_L C202 to C232.

## Gates (R6d-final)
- **DRC:** clearance 0, shorts 0, dangling 0, isolated copper 0, track width 0. Remaining: USB skew ×3 and uncoupled ×1 (explained above), plus 33 unchanged silk/lib items.
- **Via-in-pad:** the list is identical to R6c (11 entries, incl. C215.1). No new via in a pad. All new GND vias are beside their pads.
- **EP/via fields** unchanged. **Antenna keep-out** unchanged (1 pre-existing GND item).
- **No signal on In2.** Audio is on F.Cu with at most one B.Cu jumper per net.
- **GND vias at the new jumpers:**
  - Within 1.1 mm of the U10-end vias of INL- and INR-, and of the HP_L west via.
  - The west ends of INL- and INR- and the HP_L east via have their nearest GND via 1.8–2.8 mm away. The C239/C240 pocket has no legal GND via spot.
  - The B.Cu there sits over In2 GND background.
- **Older jumpers with a GND via more than 1.2 mm away (from R6a–R6c):** I2S_SDATA 150.00,100.55; VMID_HP 189.95,38.40; C234-Pad2 191.09,37.67.
