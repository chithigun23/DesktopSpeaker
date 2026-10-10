# Routing R6g (2026-10-09): U7 bundle on R6f-final, then stop at 28 open edges

Work copies only (`ai-files/pcb/work-r6/R6g-*`). The hand specs are in `work-r6/r6g/G1.json` and `G2.json`. A\* was used only for slow nets and is noted where used. `DesktopSpeaker-kicad/` was not touched. Nothing was committed.

- **Final board:** `work-r6/R6g-final.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru` (= R6f rules, unchanged), `.drc.json`, `.open2.json`, `.parity.json`).
- **Renders:** `ai-files/pcb/route-r6g-top.png` and `route-r6g-bottom.png`.
- **New helpers:** `route_r6g_step.sh` and `route_r6g_edit.py`. These are R6f's step and edit tools, pointed at the R6g rule files.
- **Clean-up:** I deleted the intermediate `R6f-t*/x*/b*` boards and the R6e/R6d experiment boards. Nothing references them. I kept every `*-final.*`, `R6d-0` (a report cites it) and the `R6x.kicad_pro/dru` rule files.

## Result

| | R6f-final | R6g-final |
|---|---|---|
| Open edges (fragment-aware, all nets) | 33 | **28** |
| Default / I2C / AUDIO / I2S_CLK | 16 / 6 / 8 / 3 | 14 / 5 / 8 / 1 |
| Power-class open edges | 0 | 0 (power connectivity unchanged) |
| DRC: clearance, shorts, dangling, isolated copper, track width | 0 | **0** |
| DRC: USB items | 3 skew, 1 uncoupled | same (pair untouched) |
| DRC: silk/lib items | 33 | 33 |
| Vias total (GND / signal) | 708 (244 / 464) | 716 (245 / 471) |
| Via centre in SMD pad (non-EP list) | 11 | 11, the same list |
| EP vias U6 / U7 / U25 | 16 / 16 / 8 | 16 / 16 / 8 |
| Antenna keep-out items | 1 (pre-existing) | 1 |
| Foreign non-GND vias in In2 islands | 24 | 24 (no signal on In2) |
| Schematic parity, net conflicts | 15 | 15 (all pre-existing) |

**Closed:**
- I2S_SDATA (U7), I2S_LRCK (U7 leg), Net-(U7-PDN), AMP_FAULT_N (U7 to U3 leg), AUD_SDA (U7 to U3 leg), AMP_BOOST_EN (A\*).
- AUD_SCL is re-routed and still complete. CHG_SYS_ENABLE and CTRL_SDA were ripped for the bundle and re-routed by A\*.

**New open edge (regression): MCU/ENC_A.**
- Its old B run along y 102.5 under the TP area is now taken by the BCK and SDATA jumpers.
- Every other crossing is full: north of H2 (ENC_B, ENC_SW, GAUGE), the SCL B diagonal, and the BAT_PACK In2 line, which keeps vias out of the space between them.

## Changes made

**3V3_AUDIO re-feed:**
- The old F diagonal (182.45,106.75)–(198.2,122.5) and its via were removed.
- The In2 track was extended (182.45,106.75) → (182.7,103.2) → (187.6,103.2) → (188.4,102.4) → (188.4,100.3) → (195.6,100.3). It stays outside BAT_PACK_IN2 and clear of H6.
- The new via is at 195.6,100.3.
- F then runs down the east side of H6: (195.8,100.5) → (195.8,108) → (198.2,110.4) → (198.2,122.5), onto the existing C293 feed.
- The via is east of H6, not at the briefed 188.6,103.8. That spot is now the SCL/SDA/FAULT corridor and is too close to H6.

**U7 bundle (hand, explicit waypoints):**
- **Fan-out:** the six top-row pins fan out by staggered 45° turns inside NECK_U7 (y 126.0–125.3). The spacing is set from the clearances: 0.4 mm I2S/I2C/Default to other nets and 0.2 mm I2S to I2S.
- **North run:** SCL 183.88, SDA 184.5, SDATA 185.35, BCK 185.8, LRCK 186.25 and FAULT 186.9 run north in parallel.
- **The I2S trio:**
  - It turns west at y 102.95 / 103.4 / 103.85 (LRCK / BCK / SDATA).
  - It runs straight west along the band to x 152.5, north of Q102/R111. The old x 178 channel is not used.
  - BCK's east leg and its 0-via diagonal were replaced.
- **SCL and SDA:**
  - Each takes one B jumper under the trio and FAULT, at y 105.0 and 106.2. The vias sit at y ≤ 106.2, outside BAT_PACK_IN2.
  - They come up east of FAULT, so the order at U3 is FAULT 25, SCL 30, SDA 31 with no other crossing.
- **Old AUD_SCL copper removed:** the AUD_SCL loop round the south of U7 and its y 95 run under the U3 bottom row. That run was the cap on the bottom-row escapes.
- **West end** (the topological reversal needs only one new jumper):
  - The SDATA U7 leg branches from SDATA's existing B run at (150.9,100.55) and comes up at via 151.0,103.55, south of LRCK.
  - LRCK leaves TP14 at y 102.55, clear of the BAT_PACK via at 150,101.65.
  - BCK takes one B jumper under LRCK: vias at 152.9,101.0 and 152.4,103.3.
- **GND vias beside the I2S vias:**
  - 153.69,101.14 for BCK via 1 (0.8 mm away).
  - 150.33,104.1 for the SDATA via (0.85 mm away).
  - BCK via 2 has no legal GND spot within 2 mm (BAT_PACK In2 line, SCL B and the lanes). Its nearest GND via is the SDATA one, 2.1 mm away. This is the one deviation from "GND via beside each".
- **PDN:**
  - U7.17 → (189.55,127.06) → diagonal → x 183.45 north → R258.2.
  - AMP_PDN runs from R258.1 to the existing via 180.55,106.75.
- **R109:** rotated −90° about its pin 1, so the PDN, SCL and SDA lanes pass the Q101/R109 row. Its GND via moved to 182.76,112.75.

**A\* (slow nets, after the hand work):**

| Net | Result |
|---|---|
| AUD_SCL west link | (171.85,91) → y 95 west of pin 17 → B under the trio to the SCL lane. 166.8 mm, 7 vias (was 220.7 / 4). |
| AMP_BOOST_EN | 98.7 mm, 4 vias. Down the freed x 178 channel, then B to U25. |
| CHG_SYS_ENABLE | 24.3 mm, 4 vias |
| CTRL_SDA | 223.3 mm, 9 vias (was 260.5 / 15) |

**Placement moves:**

| Part | Move |
|---|---|
| R258 | (189.49,122.1) → (183.2,108.4), rot −90. **15 mm (> 1.5 mm).** It now sits SW of the bundle, inside the trio corner. |
| R109 | (183.36,110.74) rot 0 → (182.76,111.34) rot −90 (0.85 mm) |

- No other parts moved. The other briefed moves were checked and not applied, because none of them closes an edge on its own (see below).

## Open edges (28) by class, with the blocker

### Default (14)

- **U4 group: CE_N, Net-(U4-QON), ILIM_HIZ, Net-(U4-BATP), CHG_INT** (5, and both CTRL_SCL edges below).
  - **Structural:** U4 sits in SYS_IN2. Every target is inside an In2 island:
    - Q100.3 and R112.2 are in BAT_INT_IN2.
    - Q101.3 is in BAT_PACK_IN2.
  - So no signal via is legal at either end.
  - On F, U4's east side is walled by the BAT_INT_F pour.
  - The B route north from the bay is one track wide even after moving the SW2 via 1 mm east. The U4 GND-pin vias at x 151.57 (y 116.6–118.4) and the SW1/SW2 B jumpers (1 mm rule) set that width.
  - Moving R100/R103/R108 out of the bay adds bay via spots. It does not change the island problem at the far ends, so it was not applied.
- **QON far end:** SW100 (WAKE_QON) is the right-angle panel tact switch at the board edge (138.6–141.6, 25.2), not a test point. It cannot move near U4. This is mechanical, not a schematic issue.
- **ADC_INT (U3.26):** its only F escape lies between the FAULT and SCL lanes. Going west, it would cross every SW-going B escape under U3 (GAUGE, 5V_LOGIC_EN, AMP_PDN, CHG_ENABLE, CHG_SYS, SCL link) or the AMP_PDN/BOOST_EN F escapes. A\* fails.
- **AMP_FAULT_N U6 leg:** the U3/U7 part is east of the trio. The U6 part (120.2,120.8) is west, past the trio corner, which is full on B (AMP_PDN, BOOST_EN, SCL and CHG_SYS B, Q101-G, REGN). A\* timed out after 240 s.
- **HP_SEL_B (U9.1–U9.5):**
  - The 3V_AO dog-leg was checked. It allows a GND via south of U9.3.
  - But the pin 1 to pin 5 link must then pass that via. HP_OUTR, AUDIO at 0.5 mm, lies 1 mm below.
  - Under the body there is no room (NO1 via, NO2 track, GND via 183.04,65.95).
  - Needs a U9 180° rotation (all 10 pins re-routed) or a BKO_MUX south-notch extension for a B leg from pin 1.
- **HP_EN:** U3.47's east exit is boxed by two parallel risers, SWCLK at x 192.9 and CODEC_PWR_EN at x 193.3. Moving R160 frees only the first. The BKO strip alone gives no B path, so neither was applied.
- **BT_UART_TX:** the whole ~150 mm leg from U3 to R182 is missing, not only the R182 pad. R182.1 is wrapped by the PWR(MFB) loop. Moving R182 1 mm east lands it on BT_FORCE_PWM and the GND via at 114.72,31.5, so it was not applied.
- **CHG_QON_SENSE:** U3.3 is boxed (as in R6e/R6f). The far end is R113 beside SW100.
- **MCU/NRST, MCU/SWCLK at J7:** duplicate SWD pads, left minimal as before.
- **MCU/ENC_A:** the new regression, described in the Result section.

### I2C (5)

- **AUD_SDA ×3:**
  - The U3/U7 group still needs its link to U24.23, which is enclosed by R209/R211.
  - R210 and the U6.15 leg remain open.
- **CTRL_SCL ×2:** U4 group (above).

### AUDIO (8)

- **BT_AUDIO_L ×2, BT_AUDIO_R ×2:**
  - The C202/C203 pad-1 side faces east into the C233-Pad2/R223 loop. North of it is the C200-Pad2 wall that runs to C200 at y 47.
  - Even with C233 rotated and R223 shifted, each net needs a B jumper west of x 162.3 at y 66–68, then about 70 mm of F to the BM83.
  - Not attempted this round.
- **USB_AUDIO_R, C205-Pad2, U8 COM1/COM2:** unchanged from R6f. COM1/COM2 need an AUDIO jumper exception inside BKO_MUX, which is not authorised.

### I2S_CLK (1)

- **LRCK U6 leg:**
  - Moving C280 1 mm NE pushes it onto the BCK/SDATA diagonals.
  - To the south or east, C271, C282 and the FAULT stub block it.
  - The LRCK lane needs C280.2 about 0.5 mm further from the BCK line than any legal position allows.

## Long nets and lengths (final)

**Long slow nets:**

| Net | Length | Vias | Note |
|---|---|---|---|
| PD_SINK_EN | 149.8 mm | 12 | unchanged; the NW path is still closed |
| CTRL_SDA | 223.3 mm | 9 | was 260.5 / 15 |
| TS_SENSE | 112.5 mm | 2 | unchanged; a shorter path would cross the U7 bundle |
| 5V_LOGIC_EN | 101.4 mm | 8 | unchanged; already close to the Manhattan distance |
| AUD_SCL | 166.8 mm | 7 | |
| AMP_BOOST_EN | 98.7 mm | 4 | |
| AMP_PDN | 106.7 mm | 8 | |

- The BT bundle (BT_TX_IND, BT_RST_N, BT_UART_RX, BT_FORCE_PWM) is unchanged at 142–162 mm.

**USB:** DP 51.59 mm, DN 51.36 mm (untouched). Skew −2.94 mm, uncoupled 17.6 mm.

**I2S:**

| Net | Length | Vias |
|---|---|---|
| BCK | 125.3 mm | 2 (one jumper under LRCK) |
| SDATA | 125.7 mm | 3 (existing jumper, plus the U7-leg branch via) |
| LRCK | 88.9 mm | 4 (unchanged R6f weave; U6 leg open) |

## Gates

The following were run after each batch:
- DRC
- Fragment-aware open edges (`route_p2_open2.py all`)
- `route_r6c_gates.py` (via-in-pad, EP, antenna, lengths)
- `route_r6d_islands.py`
- Schematic parity (final)

All were 0 or unchanged at the final board, as tabled above.

## Structural blocker (why this round stops at 28 open edges, more than 10)

1. **In2 power islands with no foreign vias (the U4 group, 7 edges).**
   - U4 and all its targets sit inside SYS_IN2, BAT_INT_IN2 and BAT_PACK_IN2.
   - Letting slow signals use In2 corridors *outside* the islands would not help here: there is no GND-background In2 near U4.
   - What would unlock them is allowing signal vias (with antipads) through the power islands for slow nets, or one short F slot through BAT_INT_F for BATP.
2. **The U3 bottom/south fan (ADC_INT, FAULT U6 leg, ENC_A, plus the HP_EN/HP_SEL_B pockets).**
   - Every slow net from U3 to the west or south now crosses the I2S trio and the other U3 escapes on B, in the same 10 mm band. B is saturated there.
   - This band (x 150–196, y 90–107) is GND background on In2, apart from the BAT_PACK, 3V3_AUDIO, 3V_AO and 5V_CODEC lines.
   - Letting slow Default/I2C nets use In2 corridors there **would** unlock ENC_A, ADC_INT and the FAULT U6 leg, and probably HP_EN. It would also make PD_SINK_EN, CTRL_SDA and AUD_SCL much shorter.
3. **The audio block (8).** This needs a planned BM83-to-ADC F corridor with one jumper per net, plus a decision on an AUDIO jumper exception inside BKO_MUX for COM1/COM2. It is placement and rule work, not hand-routing.
