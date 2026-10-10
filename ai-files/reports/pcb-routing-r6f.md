# Routing R6f (2026-10-09): schematic pin swaps and U3 re-escape on R6e-final

Work copies only (`ai-files/pcb/work-r6/R6f-*`). Hand specs are `work-r6/r6f/F0–F13.json`. `DesktopSpeaker-kicad/` was not touched. Nothing was committed. The stray `r6e/try5.*` files were deleted.

- **Final board:** `work-r6/R6f-final.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru` (= R6e rules, unchanged), `.drc.json`, `.open2.json`, `.parity.json`).
- **Renders:** `ai-files/pcb/route-r6f-top.png` (F.Cu) and `route-r6f-bottom.png` (B.Cu).
- **New helpers:**
  - `route_r6f_netdiff.py`: compares the netlist with the board pads and applies the differences.
  - `route_r6f_parity.sh`: schematic-parity DRC against a copy of the schematic.
  - `route_r6f_edit.py`: R6e edit ops plus `ripnet`, `ripbox` and `setw`.
  - `route_r6f_step.sh`: one edit-and-gate step.
  - `route_r6f_prune.py`: removes dangling copper.
  - `route_r6f_why.py`: lists what makes a candidate track or via illegal.
  - `route_r6f_dbg.py`: A\* obstacle map with a scale argument.

## Result

| | R6e-final | after pin swap | R6f-final |
|---|---|---|---|
| Open edges (fragment-aware, all nets) | 41 | 44 | **33** |
| Default / I2C / AUDIO / I2S_CLK | 21 / 9 / 8 / 3 | 22 / 9 / 8 / 5 | 16 / 6 / 8 / 3 |
| Power-class open edges | 0 | 0 | 0 (power connectivity unchanged) |
| DRC: clearance, shorts, dangling, isolated copper, track width | 0 | – | 0 |
| DRC: USB items | 3 skew, 1 uncoupled | | same |
| DRC: silk/lib items | 33 | | 33 |
| Vias total (GND / signal) | 650 (240 / 410) | | 708 (244 / 464) |
| Via centre in SMD pad (non-EP list) | 11 | | 11, the same list. A new one on R153.1 from A\* was moved off the pad. |
| EP vias U6 / U7 / U25 | 16 / 16 / 8 | | 16 / 16 / 8 |
| Antenna keep-out items | 1 | | 1 (pre-existing) |
| Foreign vias in In2 islands | 24 | | 24 (no signal on In2) |
| Schematic parity, net conflicts | 29 | | 15. All 15 are pre-existing: 9 `{slash}` name escapes and 6 stacked-pin items. |

**Closed:**
- BT_UART_RX, BT_FORCE_PWM, BT_UART_TX U3–TP21 leg, HP_SEL_B U3 leg.
- I2S_SDATA TP13, I2S_LRCK R208–TP14.
- AUD_SCL U6 leg.
- 5V_LOGIC_EN, CTRL_SDA (all 3 edges), TS_SENSE.

## Step 1: schematic sync

- The netlist was exported with kicad-cli 10.0.6 to `r6f/netlist.net`.
- There are 14 pad-net differences, exactly the `pin-swaps.json` set: 12 U3 pads plus TP13/TP14. They were applied to the board copy. CHG_QON_SENSE stays on U3.3.
- The netlist also shows 9 `{slash}` differences (U1, U24, R187 auto-names). These are only how the netlist escapes `/`, so they were left as is.
- Netclasses are unchanged. The moved nets keep their names, and the new `unconnected-(U3-…)` nets fall into Default.
- Only the conflicting copper of the affected nets was ripped:
  - the BT_UART_TX loop to old U3.19 (15 items);
  - the SDATA stub onto TP14;
  - the LRCK stub R208–TP13.
- Parity DRC afterwards shows no U3/TP13/TP14 conflicts.

## Step 2: moves and copper changes

**Placement:**
- R103 moved 0.4 mm east and C313 moved 0.1 mm west, both for the U4 bay. R103's CE_N and REGN stubs were re-centred.
- No other parts moved.

**Zones:**
- **SYS_IN2 bay** at x 149.7–153.9, y 124.5–129.6. It now holds the CTRL_SDA via at 152.45,125.2.
- **PVDD_IN2 notch** at x 147.2–148.6, y 140–141.1, for the AMP_BOOST_EN via at 147.9,140.4. It is unused in the final board: AMP_BOOST_EN routes only at the cost of AMP_PDN (see below).
- **BKO_MUX south notch** at x 184.9–189.0, y 68.6–69.5, for the HP_SEL_B B leg.

**U3 top row:** a hand fan-out of 0.5/0.2 vias at y 80.3–81.0 for pins 54/55/56/58/62/63/51. Then:
- Six BT/PD nets run as a planned bundle: B legs to transition vias at (181.6–187.55, 71.65–74.9), then F horizontals across the HP_G0/HP_G1/AUX_DET/HP_DET fan.
- Next comes a 6-via staircase at x 201.07 (y 68.45–73.2), between VMID_HP (0.5 mm audio clearance) and CODEC_PWR_EN.
- From there the routes go north along the east corridor; the far ends were routed with A\*.
- Old routes ripped for this: PD_SINK_EN, BT_TX_IND and BT_RST_N (U3 sides).

**HP_SEL_B:**
- U3.51 to a via at 188.15,80.5, then a B leg to a via at 185.40,69.0, then F to U9.5.
- HP_OUTR was moved from y 69.3 to y 70.2 under U9 to make room. It stays audio-to-audio 0.45 mm from VMID_HP and 0.775 mm from the new via.
- The U9.3 GND hook now goes west to via 182.70,68.70.

**I2S at the test points:**
- BCK now runs from R207 down the west side into TP12.
- SDATA has a stub into TP13.
- LRCK R208–TP14 was routed by A\* with two short B jumpers under BCK and the SDATA B run (4 vias, GND via within 0.85 mm of each).

**A\* routes:**
- AUD_SCL U6 leg (B under the I2S run).
- AMP_PDN west end (F, with B hops).
- 5V_LOGIC_EN, CTRL_SDA, TS_SENSE.

**Clean-up:** the A\* via inside R153.1 was moved to 117.37,31.46. The BT_UART_TX funnel stub was trimmed, which keeps the U3–TP21 link.

## Lengths and vias (final)

**USB:**
- DP 51.59 mm and DN 51.36 mm (unchanged). KiCad skew is −2.94 mm and the uncoupled length 17.6 mm.
- The D1 pad-entry change was not attempted. The 17.6 mm comes from the D1 pass-through U-loop plus the J1 bridges, so it needs a D1 placement or pad change, which is not cheap. It is left as is.

**I2S:**

| Net | Length | Vias | Status |
|---|---|---|---|
| BCK | 115.1 mm | 0 | complete |
| SDATA | 62.2 mm | 2 | U7 leg open |
| LRCK | 24.5 mm | 4 | U6 and U7 legs open |

**Long Default/I2C routes (legal, but long):**

| Net | Length | Vias |
|---|---|---|
| PD_SINK_EN | 149.8 mm | 12 |
| BT_TX_IND | 161.0 mm | 8 |
| BT_RST_N | 161.5 mm | 4 |
| BT_UART_RX | 142.0 mm | 10 |
| BT_FORCE_PWM | 154.5 mm | 8 |
| CTRL_SDA | 260.5 mm | 15 |
| AUD_SCL | 220.7 mm | 4 |
| TS_SENSE | 112.5 mm | 2 |
| 5V_LOGIC_EN | 101.4 mm | 8 |

- PD_SINK_EN is not shorter than before. The direct NW path from U3 is closed by the C204-Pad2 B wall (x 163–166, y 54–84), BKO_CODEC and BKO_MUX. All BM83/U11 nets therefore take the east corridor.

## Open edges (33) and the smallest change for each

### Default (16)

**AMP_FAULT_N ×2, ADC_INT, AMP_BOOST_EN, Net-(U7-PDN):** U3 bottom-row and U7 band.
- Bottom-row escapes are walled on B by the SW fan under U3 (CHG_SYS_ENABLE, CHG_ENABLE, ENC_A, SWDIO, GAUGE_ALRT_N, AMP_PDN). On F they are capped by the AUD_SCL run at y 95.
- PDN's R258 sits NE of the BCK diagonal, while U7.17 is SW of it.
- Rip-up search on the same nets: 4 net orderings (19 nets ripped in a box) plus 4 smaller variants. All were worse, 19–20 against 18 for the same set. AMP_BOOST_EN routes (B under the islands to the PVDD notch via) only if AMP_PDN loses 2 edges.
- **Change:**
  1. Extend the 3V3_AUDIO In2 track from 182.45,106.75 to a via near 188.6,103.8 and re-run the 3V3 F diagonal NE.
  2. Move R258 SW of the BCK diagonal.
  3. Then route the U7 bundle SCL/SDA/SDATA/BCK/LRCK/FAULT, with B jumpers for SCL/SDA north of y 107.2.

**CE_N, QON, ILIM_HIZ, BATP, CHG_INT (U4):**
- The bay fits only one signal via beside R103/R100/R108.
- The B corridor north is closed by the SW1/SW2 vias at 150.1/153.0,115.2: 2.9 mm apart under the 1 mm switch rule.
- East exits run into the BAT_INT/SYS_RAW F pours and islands, which allow no via near Q100/R112/Q101.
- **Change:** move R100/R103/R108 about 1.5 mm south out of the bay, and move the SW2 via 1 mm east. QON's far end (140.6,24) is 100 mm away; move the QON test point or button near U4.

**HP_SEL_B (U9.1–U9.5):**
- The U9.3 GND stub lies between the two pins.
- A GND via south of U9.3 is blocked by the 3V_AO In2 1.0 mm trunk, which needs 1.0 mm.
- **Change:** dog-leg the 3V_AO In2 trunk about 0.7 mm west at y 66–72, or rotate U9 180°.

**HP_EN:**
- U10 is enclosed by the VMID_HP audio loop, CODEC_PWR_EN and BKO_MUX.
- U3.47 is boxed by the SWCLK riser to R160.
- A legal entry via exists at 198.15,61.65 (north of R236), but no B path leads from it to U3.
- **Change:** a BKO_MUX exception between the HP_G0/HP_G1 stubs (x 193.5–196, y 66.75–69.5), plus moving R160 so pin 47 can exit east.

**BT_UART_TX at R182.1:**
- The pad is wrapped by the Net-(U1-PWR(MFB)) F loop (R183.2 → U1.26) and sits over the BT_RST_M B track.
- The U3–TP21 part is routed, and a free funnel slot at y 72.25 is kept for it.
- **Change:** move R182 about 1 mm east, outside the loop, and re-route BT_RXD_M.

**CHG_QON_SENSE:** U3.3 is boxed (NRST riser, HP_SEL_A via, HP_G0). Same as in R6e.

**/MCU/NRST, /MCU/SWCLK at J7:** left minimal as briefed; J6 carries SWD.

### I2C (6)

**AUD_SDA ×4:**
- U24.23 is enclosed by R209/R211.
- The U6.15 leg is crossed by the AMP_PDN/AUD_SCL west routes.
- The U3 and U7 legs belong to the U7 bundle above.

**CTRL_SCL ×2:** the only bay via spot is used by CTRL_SDA. This needs the bay change above.

### AUDIO (8)

**BT_AUDIO_L ×2, BT_AUDIO_R ×2:**
- These are F-only routes of about 80 mm to the BM83.
- The channel east of the C201–C203 column is 1.15 mm, because the C200-Pad2 F track crosses it at y 78–79. The two tracks do not fit even after the briefed C233 rotation and the 0.7 mm R223 shift, so those moves were not applied.
- **Change:** re-place C202/C203 (and C233) west of the column or nearer the BM83.

**USB_AUDIO_R, C205-Pad2:** F-only A\* fails. These need the C201/C176 moves together with re-routing C200-Pad2, not the small shifts alone.

**U8 COM1/COM2:**
- COM1 can take a B jumper (vias at 183.8,64.6 inside U9 and at U8) if BKO_MUX is extended.
- COM2 at U8.6 is wrapped by NC2 inside the U8 body.
- **Change:** re-route NC2 or rotate U9 180°, with an AUDIO B-jumper exception for COM1/COM2.

### I2S_CLK (3)

**LRCK U6 leg:**
- The hand path (140.2,103.9) → (113.9,120.5) → U6.12 is legal except at C280 (U6 3V3 decoupling) and its GND via 114.49,120.12, which close the gap between the BCK approach and the AMP_FAULT_N detour.
- **Change:** move C280 about 1 mm NE, or route AMP_FAULT_N around the south of C271.

**LRCK and SDATA U7 legs:** part of the U7 bundle change above. They need 2 I2S jumpers for the TP-order reversal.

## Gates (every batch)

Every batch was gated with:
- DRC (clearance, shorts, dangling, isolated copper and track width all 0 at the final).
- Fragment-aware open edges (`route_p2_open2.py`).
- Via-in-pad and EP counts (`route_r6c_gates.py`).
- In2 islands (`route_r6d_islands.py`).
- Power-class open edges (0).
- Schematic-parity DRC (on n0 and on the final).
