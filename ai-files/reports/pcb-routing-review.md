# PCB routing review: work-p3/R5-final (2026-10-07)

This is a read-only critique of `ai-files/pcb/work-p3/R5-final.kicad_pcb` and its rules (`.kicad_dru`) against `pcb-layout-best-practices.md`, `pcb-layout-rules-audio.md` and `pcb-routing-plan.md`. No board was modified.

Scratch files are in `ai-files/pcb/work-review/`:
- copied board
- geometry dump `rv_dump.json` (`rv_dump.py`)
- analyses: `rv_analyse.py` producing `rv_analyse.txt`, plus `rv_more.py`, `rv_clear.py` and `rv_path.py`
- layer renders `rv-*.png` and crops `crop-*.png`

Coordinates are board mm. Power currents used: SYS_RAW and battery 8 A (boost input at a low pack voltage), USB_VBUS/VBUS_PD 3 A, SW1/SW2 5 A, PVDD 3 A, speaker outputs 3 A peak, and U25 SW 8.7 A peak (HANDOVER sec. Amplifiers).

**Verdict: not releasable. R5 is a connectivity draft.** Most blockers are placement-driven: missing or misplaced decoupling, inductor and crystal positions, regulator locations. Fix placement (v10) before any further routing passes, then re-route the power stages by hand with pours.

## BLOCKER

**B1. 67 unconnected items, many of them functional.** Without these connections the board does not work.
- Ground pins:
  - U4.27 BQ25792 power ground, between SW1 and SW2 (136.15, 97.78)
  - U14.3/U14.8 TPS63802 GND/PGND (88.5-90.0, 92.4)
  - U6.20, U7.5 and U7.20 TAS5825M ground pins
  - U24.7 PCM1862 AGND (197.9, 35.4)
  - U2.26, U11.31, U5.4, U9.3, R180.2, J7.5
  - U10.2/3/15/17 (EP)
- Buses and control: AUD_SCL/SDA to U3, U6, U7 and U24; CTRL_SCL to U4; PDCTRL_SDA to U11, U3 and J4; AMP_PDN, AMP_FAULT_N and AMP_BOOST_EN; U25 FSW and SS; CHG_INT, PROG, REGN and the Q103 gate (SDRV); SWDIO/SWCLK/NRST at J6/J7.
- I2S: BCK and SDATA to U6/U7.
- Supplies: 3V3_AUDIO to U6.6, U7.6 and U8/U9; AVDD of U6, U7 and U24; 3V8_BT from C190 to U15 (about 100 mm).
- USB: D+/D- (J1 to R171/R172) and CC2.
- Fix: the P3 report shows the remaining items are blocked by placement and 0.6 mm vias. Move parts first (see B3, B4 and the M items). For the GND pins hemmed in at 0.45-0.5 mm pitch:
  - U4.27: a stub under the package to tented vias, or a paid POFV via-in-pad.
  - U6/U7 GND pins: short F.Cu bridges to the exposed pad.

**B2. Thermal vias were stripped from the exposed pads.**
- Current via counts:
  - U6 EP (117.5, 136.1, 3.45 mm square): 1 via
  - U7 EP (179.3, 136.1): 1 via
  - U25 EP (175.3, 104.7): 0 vias in the pad centre. Only pins 11 and 20 have vias.
  - U11: 2 vias plus the 0.2 mm footprint vias.
- For comparison, P0 had 16/16/6, the plan asks for about 20 per TAS5825M and at least 9 on U25, and the datasheets require "thermal vias underneath". With one via, a TAS5825M at 12 V will hit thermal shutdown.
- The intended B.Cu heat-spreader under the amps is also cut by I2S_LRCK, a 55 mm B.Cu run at y 139.2 from x 122.4 to 177.0, and by other B.Cu tracks.
- Fix:
  - Restore the arrays: TAS5825M 4x4 or more at 0.3/0.6 mm with about 0.9-1.0 mm pitch, in radial columns; U25 at least 6 in pad 21.
  - Connect them solid (no relief) to In1 and B.Cu.
  - Keep at least 900 mm2 of B.Cu per amp free of signals.

**B3. U7 has no PVDD and no DVDD (3V3_AUDIO) decoupling at all.**
- Every PVDD cap is around U6 or C275: C270-C274, C276-C279, C289-C292, all 3.6-16 mm from U6 and 55-69 mm from U7. Every 3V3 cap (C280, C281, C293, C294) is also at U6.
- HANDOVER says the design is "PVDD 2 x (22 uF + 0.1 uF) per device". The TAS5825M datasheet (sec. 12.1.2) warns that output ringing without close PVDD caps can exceed abs-max and damage the device.
- U6 also has C289 (100 nF PVDD) connected through a via, against the datasheet.
- Fix (placement): give U7 its own set at pins 3/4 and 21/22 (0.1 uF within 1.5 mm with no via, 22 uF within 6 mm), plus 4.7 uF and 0.1 uF at pin 6. Rebalance the eight 22 uF caps between U6, U7 and U25 (see B4).

**B4. The TPS61088 output hot loop has no ceramic capacitor.**
- VOUT pins 14-16 (177.0, 104.4-105.4) feed C275 (100 uF electrolytic, + at 185.5, 104.7) through a **0.2 mm x 3.4 mm** trace, (177.45, 104.45) to (180.81, 104.24), then 1.0 mm.
- No 22 uF ceramic or 0.1 uF sits at VOUT/PGND. The bottleneck from U25.15 to C275, U6 and U7 is 0.2 mm on every path.
- SLVA773 and the datasheet both put the output ceramics first: the pulsed current of up to 8.7 A peak creates SW overshoot and ringing (it can trip the 12.7 V OVP or overstress SW) and EMI.
- Fix:
  - Place 3 x 22 uF 25 V 1210 plus 0.1 uF 0402 within 2 mm of pins 14-16. Their GND goes on F.Cu to pins 11/12 and the EP.
  - Make VOUT a pour at least 3 mm wide, joined to the PVDD trunk with at least 4 x 0.4 mm vias.
  - Leave C275 as bulk.

**B5. Power-path widths and via counts are far below the design current.** IPC-2221 widths at a 20 K rise; inner layers are 0.5 oz (15.2 um, per the stackup).
- SW1 (5 A): pin 28 -> 0.2 mm F.Cu -> **one 0.3 mm via** at (135.7, 98.7) under the U4 body -> B.Cu 1.5 mm -> a via in the L1 pad at (134.2, 91.4). This breaks the datasheet rule on SW layer and copper area, and the single via is about 1 A capable.
- SW2 (5 A): a 0.2 mm x 1.45 mm neck at (136.3, 96.55-95.1). The total SW2 copper runs 19.4 mm because of the BTST2 detour.
- USB_VBUS (3 A, J1 to U11):
  - F.Cu 0.6 mm x 3 mm at (135.0, 32-35)
  - In2 1.5 mm x 25 mm from (116.9, 55.0) to (134.6, 37.4), plus 2.0 x 16.5 mm
  - single 0.4 mm vias at each layer change; the TPS25730 datasheet asks for at least 6, and 15 at VBUS_IN
- VBUS_PD (U11.20 to U4): bottleneck 0.2 mm.
- BAT_INT (8 A, Q103 to U4.22/23): In2 1.5 mm x 10 mm at (137.4, 85.8-96.0) with single vias.
- BAT_PACK (8 A, SW101 to Q103): bottleneck 2.0 mm over about 110 mm. That is about 27 mOhm, about 0.2 V and roughly a 50 K rise at 8 A.
- SYS_RAW to the boost (8.4 A input): a single 2 mm F.Cu trace, 18.5 mm, from (144.4, 101.8) to (162.9, 101.8). Several 1.0 mm B.Cu branches.
- PVDD to U7: one 0.6/0.3 via at (176.95, 135.6) and 0.2 mm tracks (181.7-186.6, 134-137.6). The U6 feed includes a 0.2 mm x 7 mm B.Cu track from (118.65, 132.6) to (116.4, 139.25).
- Fix: build the plan's pours:
  - SYS 8 mm and BAT 12 mm on L1 + L3 with 12-18 via arrays
  - VBUS at least 3.5 mm with at least 6 vias, 15 at VBUS_IN/PPHV
  - PVDD at least 6 mm
  - SW1/SW2 as short F.Cu polygons that flare straight from the pins to the L1 pads, with no vias
  - order 1 oz inner copper (and set it in the stackup) if inner layers must carry current

**B6. Charger U4 power-stage rules are broken** (BQ25792 DS sec. 12 priority list):
- The SYS caps C104, C105 and C107 (22 uF) reach SYS pin 25 only through vias (not F.Cu-connected), and C105 has a 0.4 mm via in its pad.
- There is no 0.1 uF HF cap on SYS, PMID or VBUS. This is a schematic gap: add three 0402s.
- The PMID cap C101's GND via is 2.4 mm away, and the PGND pin is open (B1).
- BATP sense (Net-(U4-BATP)) runs on B.Cu **0.31 mm** from SW1. ILIM_HIZ is 0.31 mm from SW2 and CTRL_SDA 0.82 mm from SW1.
- REGN caps C102 and C109 sit 12.1 and 7.5 mm from pin 5, and REGN is still open.
- Fix: re-place the U4 ring in the datasheet order, keep all loops on F.Cu, and keep BATP and the other signals at least 2 mm from SW.

## MAJOR

**M1. Via-in-pad: 178 vias in ordinary SMD pads.** They are spread over 94 caps, 55 resistors and 15 IC pins:
- IC pins: U25.11 and U25.20 (0.24 mm pads), U6.25, U4.16, U11.20, U19.8, U22, U12, U16, U21
- power caps C104 and C105 (SYS 0.4 mm), C150, C154, C190
- crystal pads Y200.1 and Y200.4
- the L1 SW1 pad and the L203 pad
- most decap GND pads, which have the via centred in the pad (gndvia 0.0-0.1 in `rv_analyse.txt` sec. 7)

The pads are untented, and 0402s are hand-soldered. Solder wicks into the vias, which causes opens and tombstoning, and POFV is a paid option on 4 layers at JLC. Fix: move each via beside its pad on a 0.3 mm dogbone, about 0.25 mm from the pad edge. Alternatively, order POFV and record it in the fab notes; that is required for any QFN-pin via kept.

**M2. Class-D pre-filter switch nodes are 14-36 mm long and partly on B.Cu (plan: at most 3 mm).**
- Lengths: U6 OUT_A+ 36.1 mm, 5.8 mm of it on B.Cu with vias at (111.3, 133.7) and (116.0, 131.7). U6 OUT_B+ 22.9 mm, 20.3 mm on B.Cu with vias at (122.4, 135.2) and (138.2, 124.2). U6 OUT_A-/OUT_B- 14 mm. U7 OUT_A+/OUT_B+ 20 mm.
- Widths: U6 OUT_A+/OUT_A- are 0.4 mm over 8.6-9.3 mm, at 3 A peak.
- Cause: the inductor row L201-L206 at y 121.6 sits 15-28 mm from the OUT pins at y 133.7-134.9 (L201 at x 89.6 against U6 at x 117.5).
- Fix: move each inductor next to its OUT pin pair, route on F.Cu at least 1.5 mm wide with no vias, and keep the filter cap within 3 mm of the inductor, grounded at that amp.

**M3. I2S topology and routing.**
- I2S_LRCK is 181 mm long with 3 vias:
  - B.Cu 55 mm under both amps (y 139.2)
  - B.Cu 17 mm along x 175.3 at the L205 edge (overlapping switch copper in plan view at (175.4, 121.5))
  - F.Cu diagonal from (177.4, 117.5) to (214.8, 66.8), passing the C275/U25 boost output
  - 28 mm along the board edge at x 214.8 to TP13
- BCK and SDATA are still open, and each will be over 100 mm from U24 (around y 39) to U6/U7 (y 138.5). The plan limit is 60 mm.
- Fix: decide the topology first (source near the amps, or a buffered or series-terminated star). Then route on F.Cu over solid In1, outside the class-D and boost area, with a GND guard and an in-line TP (no 28 mm edge detour).

**M4. Audio is routed on B.Cu, against the plan (L1 only, no vias).**
- 579 mm of AUDIO on B.Cu with 40 vias: BT_AUDIO_L 140 mm, USB_AUDIO_R 128 mm, BT_AUDIO_R 107 mm, HP_OUTR, the VIN and coupling nets.
- They cross 34 In2 tracks: USB_VBUS, the I2C lines, BT UART, LDO_3V3, among others.
- Their reference is the fragmented B.Cu pour or In2 (rarely GND), not In1.
- Fix: re-route on F.Cu over In1. If one crossing is unavoidable, use a single short B.Cu jumper with GND vias on both sides and nothing on In2 above it.

**M5. Crystals are far from their ICs and coupled into audio.**
- Y200 (PCM1862): XI is 22.8 mm with 4 vias and 7 B.Cu segments. XO is 14.6 mm, of which 12.2 mm runs within 1 mm of AUDIO next to the PCM1862 analog pins. XO and XI are 0.3 mm from AVDD/LDO.
- Y170 (PCM2902C): XTI/XTO are 13-15 mm, about 4 mm of it within 1 mm of AUDIO.
- Fix: move each crystal within 3-5 mm of the pins, use F.Cu only with no vias, add a GND guard ring, and keep nothing else under it.

**M6. USB D+/D- and CC routing.**
- The pair is not coupled. USB_DP takes vias to B.Cu at J1, (132.1, 25.15) to (129.45, 27.8). USB_DN loops around the J1 shell, (131.6, 23.5) to (127.05, 25.35) to (129.4, 31.1).
- The full J1-to-U2 path will be about 85 mm across the board. DRC reports skew -4.6 mm and 22.9 mm uncoupled.
- USB_CC1 is 92 mm long with In2/B.Cu vias. The CC caps C182/C183 sit at J1, 62-67 mm from the U11 CC pins; the datasheet wants them close to the IC with the via after the cap.
- Fix:
  - Route the pair 0.25/0.15 mm on F.Cu, J1 -> D1 -> R171/R172 -> U2, with no vias and GND stitching on both sides.
  - Bridge A6/B6 and A7/B7 at the connector.
  - Preferably place U11 next to J1 (this also shortens VBUS, B5). Otherwise put C182/C183 at U11 and the ESD at J1.

**M7. BM83 (U1).**
- The 3V8_BT regulator U15 is at (208.6, 92.6), about 120 mm of route from the module (105.6, 36.4), so its switching ripple travels across the board.
- C190 and C193 sit 3.8 and 3.2 mm from the supply pins.
- There are F.Cu tracks under the module body (3V8_BT, BT_RST_M, BT_RXD_M, BT_SYS_CFG). The datasheet (sec. 7.2) says no top-layer routing under the module.
- Only 7 GND vias are within 3 mm of the module.
- The antenna end overhangs the board edge: module x runs 73.6-105.6 and the edge is at 81.5. The keep-out (81.55-84.16) is empty, which is good, but the overhang needs a mechanical check.
- Fix: move U15 and L3 next to the BM83, route supply and control from the pad side outward, and add a via fence at a pitch of 3 mm or less.

**M8. TPS63802 buck-boost hot loops (U14, U15).**
- U14: PGND (pin 8) and GND (pin 3) are open (B1). C141/C142 reach 5V_LOGIC through vias, 2.9 and 6.1 mm away.
- U15: input cap C150 is not on F.Cu. Output caps are 8.4 mm (C152) and 6.1 mm (C154) away.
- In a buck-boost both the input and output caps are in hot loops. Fix: within 1.5 mm, on F.Cu.

**M9. Decouplers connected through a via** (the PCM1862 and TAS5825M datasheets forbid this).
- U24: C212 (VREF), C214 and C215/C216 (LDO/AVDD), C218/C219.
- U6: C289 (PVDD), C281/C294 (3V3).
- U2: C173, C174, C175.
- U25: C260 (VIN).
- Fix: connect each on F.Cu directly, with the cap pad on the path before the pin.

**M10. In2 and B.Cu return paths, and power islands.**
- 1.6 m of signal is routed on In2. About 250 mm of it runs inside other-net power-island outlines, for example HP_SEL_B 24 mm in L3_BAT_PACK_0, BT_PWR_EN 27 mm in L3_BAT_PACK_1, BT_RXD_M 19.6 mm in L3_3V8_BT_0, HP_DET/AUX_DET 13.5 mm in L3_3V_AO_1.
- These cuts split the islands: L3_BAT_PACK_0 and L3_3V_AO_1 have 3 fill fragments each, and L1_PVDD_AMP_1 has 5, one of them floating (DRC).
- The B.Cu GND pour is cut into 19 fragments, largest 11,412 mm2, others 1,439/600/289/251 mm2 down to 0.4 mm2. In2 and B.Cu signals therefore lose a close reference.
- The planned L3 planes (BAT 15 mm, SYS 8 mm) were never built: the islands are 3-8 mm rectangles.
- Fix: keep slow signals out of the island areas, or move them to F.Cu. Draw real L3 power planes for SYS/BAT/PVDD/VBUS. Re-check B.Cu pour continuity under the amps and the BM83.

**M11. Rule relaxations.**
- `switch_clear` 0.3 mm: acceptable as a voltage clearance (22 V maximum; IPC-2221B allows 0.1 mm). It is not acceptable as a noise rule. The 554 segment pairs under 1.0 mm are mostly same-stage pairs (BST/OUT, SW-PMID/SYS), which is harmless. The sensitive pairs fail: SW1-BATP 0.31, SW2-ILIM_HIZ 0.31, SW1-CTRL_SDA 0.82. Add a narrow rule: `A.NetClass=='SWITCH' && B.NetClass in {SIGNAL, I2C, AUDIO, I2S_CLK, USB}` with min 1.0 mm, plus 2 mm for BATP and FB/COMP by area.
- `neck_exempt`: its condition `A.Width < 0.26mm || B.Width < 0.26mm` is board-wide. Every 0.25 mm AUDIO/I2S/USB/SIGNAL track (526 segments) and every 0.2 mm track (605) qualifies, so it turns off `audio_clear` (0.5) and `clk_clear` (0.4) for track pairs anywhere. Actual damage is small: 8 audio pairs (e.g. U9 NO1/NO2 to HP_SEL_B at 0.25 mm, (152.2, 56.6)), 2 crystal pairs and 2 USB pairs. Restrict it to `A.intersectsCourtyard()` of the fine-pitch ICs (U3, U4, U6, U7, U11, U25, J1).
- The 199 `track_width` errors are not all harmless necks. They include PVDD 0.2 x 3.4 mm (B4), PVDD 0.2 x 7 mm (B5), SW2 0.2 x 1.45 mm and VBUS_PD 0.2 mm. Add a script check that limits floor-violating segments to 1 mm or less from their own pad.

**M12. GND stitching and pours.**
- There are only 216 GND vias, and 344 of about 675 10 x 10 mm windows contain none (`rv_analyse.txt` sec. 11).
- There is no F.Cu GND pour and no audio or amp guard fence, although the plan calls for L1/L4 GND pours, a fence and stitching at 4-5 mm (3 mm or less near the BM83 and edges).
- Fix: after the power rework, add stitching on a 5 mm grid (3 mm near the BM83), a fence between the amp/boost block and the audio block, and F.Cu GND fill in free areas, never in the antenna keep-out.

## MINOR

- **m1. Geometry hygiene.** There are 40 acute joints:
  - USB_VBUS 9 degrees at (109.96, 92.01)
  - U7 OUT_B+ 15 degrees at (182.91, 135.22)
  - SW1 36 degrees at (132.95, 98.17)
  - PVDD 42 degrees at (177.56, 105.45)
  - VBUS_PD 52 degrees at (113.09, 94.90)

  141 segments are shorter than 0.08 mm, including a raster staircase on USB_VBUS at (112.6-112.9, 88.85-89.15). 790 segments (2.9 m) are any-angle, off the 45-degree grid. Fix: clean up with a simplify and retrace pass.
- **m2. No teardrops.** The plan makes them mandatory. Generate them in the GUI after the final route.
- **m3. U11 thermal vias.** The footprint's 0.2 mm thermal vias have thermal-relief spokes; make them solid. There are 8 `drill_out_of_range` errors for these 0.2 mm vias. JLC builds 0.2 mm (minimum 0.15), so add a rule exception for U11 rather than ignoring the errors.
- **m4. Inherited DRC items.** SW100 `hole_clearance` is 0.175 mm (fix the footprint). There are 43 silk items. The 199 `lib_footprint_issues` come from the work copy lacking the fp-lib-table; this is an artifact of the copy.
- **m5. Test points.**
  - TP13 (I2S_LRCK) at the board edge (214.8, 38.4) forces a 28 mm detour.
  - TP12 and TP14 should be in line, with stubs of 2 mm or less.
  - TP9 is within 2.5 mm of R154, so probe access is tight.
  - All TPs are on top with the parts, which is fine for access.
- **m6. STM32G071 U3 decoupling.**
  - 3V_AO has only C160 (100 nF, 1.8 mm) and C161 (4.7 uF), whose GND via is 1.22 mm away.
  - The NRST cap C162's GND via is 1.9 mm away.
  - There is no separate VREF+ or VDDA 100 nF + 1 uF; check the schematic against AN5096.
- **m7. Small clearance items.**
  - U8/U9 mux control lines run 0.25-0.3 mm from the analog NO pins.
  - C204 is 0.47 mm from 3V_AO.
  - USB_DN is 0.3 mm from USB_CC1 at J1.
  - Net-(U2-D-) is 0.37 mm from U2 VBUS.
- **m8. Via under a package.** The SW1 via sits under the U4 body at (135.7, 98.7). It is tented, but it goes away with the B5 fix.

## What is good
- Clearance, short, dangling, isolated-copper and keep-out DRC are all 0.
- The antenna keep-out is empty on all four layers.
- In1 is one solid GND fill with no tracks.
- The speaker output trunks are 2.0 mm and on F.Cu.
- The U25 FB/COMP/ILIM traces are 3 mm or more from SW.
- Audio is 15 mm or more from all switch copper.
- The TAS5825M small PVDD caps on U6 (C276, C278, C291) are 1.2-1.6 mm away and F.Cu-connected.

## Recommended order
1. Placement v10:
   - U7 decoupling (B3)
   - U25 output ceramics (B4)
   - U4 ring with 0.1 uF caps added (B6)
   - inductors next to the OUT pins (M2)
   - crystals (M5)
   - U15 next to the BM83 (M7)
   - U11 near J1, or CC caps at U11 (M6)
   - an I2S topology decision (M3)
2. Hand-route the power stages and pours (B5), restore the EP via arrays (B2) and connect the GND pins (B1).
3. Fix the rules: a narrow `neck_exempt`, an added switch-to-sensitive rule and an inner copper decision (M11).
4. Re-run the signal router with AUDIO restricted to F.Cu and no In2 inside islands (M4, M10).
5. Then do stitching, teardrops and the DRC/width/loop scripts from plan sec. 7.
