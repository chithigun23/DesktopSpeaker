# Routing R6j (2026-10-09): 8 of 10 open edges closed on R6i-final, bend hits 123 → 49

Work copies only (`ai-files/pcb/work-r6/`). `DesktopSpeaker-kicad/` was not touched. Nothing was committed. All background jobs ran to completion (none had to be stopped). No sub-agents were used.

- **Final board:** `work-r6/R6j-final.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`, `.drc.json`, `.open2.json`, `.isl.json`, `.bends.json`, `.len.txt`). `R6j-0.*` is the R6i-final baseline copy.
- **Rules:** `R6j.kicad_dru` / `R6j.kicad_pro` are byte copies of the R6i files. No DRC rule was added or relaxed.
- **Renders:** `ai-files/pcb/route-r6j-top.png`, `route-r6j-bottom.png`, `route-r6j-in2.png` (`route_p1_view.sh`).
- **Specs and logs:** `work-r6/r6j/` (hand specs `*.json` for `route_r6g_edit.py`, router plans and logs, `final.gates.txt`). All intermediate boards were deleted.

## Result

| | R6i-final | R6j-final |
|---|---|---|
| Open edges (fragment-aware, all nets) | 10 | **2** (MCU/NRST, MCU/SWCLK, both only at J7) |
| Power-class open edges | 0 | 0 |
| DRC: clearance, shorts, dangling, isolated copper, track width | 0 | **0** |
| DRC: USB items | 3 skew, 1 uncoupled (17.63 mm) | 3 skew (same values), 1 uncoupled (**17.34 mm**) |
| DRC: silk/lib items | 37 | 37 |
| Via centre in SMD pad (non-EP list) | 7 | 7, the same list |
| EP vias U6 / U7 / U25 | 16 / 16 / 8 | 16 / 16 / 8 |
| Antenna keep-out items | 1 | 1 |
| Foreign non-GND vias in In2 islands | 32 | 32 (no new island via) |
| Island continuity (`route_r6h_isl.py` vs R6j-0) | – | every outline count and area identical |
| In2 signals to island outline | ≥ 0.33 mm | ≥ 0.32 mm (PD_PLUG_EVENT, smoother chamfer; rule is 0.3) |
| AUDIO / I2S / USB / clock copper on In2 | none | none |
| USB DP / DN length | 51.59 / 51.36 mm | 51.59 / 51.36 mm |
| Vias total (GND / signal) | 880 (267 / 613) | 921 (268 / 653) |
| Bend-rule hits (`route_r6i_bends.py`) | 123 | **49** (USB_DP 11 → 2) |

**Closed (8):** AUD_SDA ×2 (U6.15, U24.23), I2S_LRCK (U6 leg), CHG_QON_SENSE, Net-(U8-COM2), BT_UART_TX, HP_EN, HP_SEL_B.

## How each edge was closed (in order)

1. **AUD_SDA at U6.15** (`r6j/a1.json`). The U6 SCL diagonal was redrawn 0.47 mm further NW, so SDA has its own lane between SCL and SDATA (0.4 / 0.625 mm). SDA leaves BKO_U6 to a new via at 120.9,113.45 and runs on B to the existing SDA via.
2. **I2S_LRCK at U6.12** (`r6j/a2.json`, generator `route_r6j_u6fan.py 60 118.6 0.68 0.44`).
   - The U6 SCL / SDA / SDATA / BCK fan-out was redrawn as a 60° fan. BCK's bend now sits 0.47 mm NW of its old line and rejoins the old diagonal at x 124.
   - LRCK gets a new 0.47 mm-offset lane SE of BCK, from the pin to via 140.2,103.9. It passes the C280 GND pad corner at 0.37 mm.
   - The lane needed four small via nudges and one via removal (see exceptions). C280 and C271 were **not** moved.
3. **CHG_QON_SENSE** (`q1.json`, router `q2.json`).
   - The 3V_AO In2 trunk's south end was bent up to 1.25 mm east (178.3,86.8)→(180.0,86.6)→(181.39,77.0), still 1.0 mm wide.
   - A via at 179.05,84.55 now fits beside U3.3 (U3.1/U3.2 are NC).
   - The A\* router routed it to R113 at 135 mm (In2 89 mm).
4. **Net-(U8-COM2)** (`c2.json`, `c5.json`).
   - The COM1 B jumper was moved under the U8 body (y 64.6), and the HP_L B jumper north to y 60.95.
   - COM2 now has a fine-via B jumper: 0.5/0.2 at 173.55,62.22 (U8 side) and 184.85,62.0 (U9 side). The B lane runs at y 62.82.
   - Making room for it needed these moves:
     - USB_AUDIO_R via 173.95,61.95 → 174.2,61.8 (its B and F ends re-pointed);
     - its GND companion via 174.55,61.35 → 174.62,60.92;
     - the U8.8 3V3_AUDIO escape reshaped to (172.35,62.15)→(173.85,60.95)→(173.8,59.95).
5. **BT_UART_TX** (`t1.json`, router `t2.json`).
   - R182 was relocated from 112.82,32.36 to 109.6,46.0 (180°). Its pad 2 now sits on the existing BT_RXD_M track to J8.3, and the old RXD_M stub was removed.
   - BT_UART_TX was routed from R182.1 to the MCU side over In2.
   - The PWR(MFB) loop that wrapped the old R182.1 was then straightened (`h4.json`).
6. **HP_EN** (`e1.json`, router `e2.json`).
   - A new F stub from U10.13 runs north to a via at 198.1,61.4, just outside BKO_MUX. This avoids the R236 GND hook.
   - The via sat on the BT_RST_N In2 vertical (x 197.9), so BT_RST_N was ripped. HP_EN was routed first (35 mm), then BT_RST_N was re-routed (162 → 187 mm).
7. **AUD_SDA at U24.23** (`s1.json`, `s2.json`, router `s3.json`).
   - R209 was moved 1.9 mm, from (151.05,91.28) 0° to (152.9,92.0) 90°. Its 3V3 pad gets a new via at 153.4,92.3 and a 0.86 mm In2 stub to the 3V3_AUDIO In2 diagonal. The old R209.1 F stub was removed.
   - The 3V3 junction via 150.3,90.5 stays; SDA passes 0.22 mm east of it.
   - SDA drops through the pocket to a via at 150.92,91.5 and runs on B across the VBUS_PD strip, inside the BKO_ADC notch and then y > 92, to a via at 140.45,93.75. The router closed the last 6 mm.
   - This took the old CTRL_SDA strip lane. CTRL_SDA, ENC_A and ENC_SW were ripped locally and re-routed in five orders (`p_*.json`). Only two of the three fit through the strip again, so ENC_SW was routed the long way (`s11.json`). See long nets.
8. **HP_SEL_B** (`b1.json`, cleanup `f1.json`).
   - The U9.3 GND hook was removed, and U9.3 gets its own fine via 0.5/0.2 at 184.3,68.55 (NECK_U9). That frees a lane south of the pins, U9.1 → (183.32,68.75) → (183.77,69.2) → (185.1,69.2) → the existing via 185.4,69.0, at ≥ 0.54 mm from HP_OUTR.
   - The via needed the 3V_AO trunk off pin 3. The U9 section (181.39,77.0)→(188.4,54.75) was re-planned with a grid A\* (`route_r6j_trunkplan.py`) to (183.54,69.05)→(183.57,67.25)→(186.47,64.35)→(186.52,56.6)→(188.4,54.75).
   - That section is now **0.6 mm wide instead of 1.0 mm** (exception 3). The largest lateral move is 1.1 mm.

## Every exception used

1. **Part moves (all authorised):**
   - R182: 14 mm, to 109.6,46.0, sitting on the RXD_M line near J8. It is still a series 10 k between MCU TX and BM83 RXD; only its position along the line changed.
   - R209: 1.9 mm, rotated 90°.
   - Not moved: R211, C280, C271. U9 was not rotated.
2. **3V3_AUDIO:**
   - new via 153.4,92.3 plus a 0.86 mm In2 stub for R209.1; the R209.1 F stub at 150.3,90.5 was removed (the junction via itself is unchanged);
   - the U8.8 escape was reshaped (step 4).
3. **3V_AO In2 trunk:**
   - **Near U3:** south end bent ≤ 1.25 mm east; width kept at 1.0 mm.
   - **Under U9:** re-routed with lateral moves ≤ 1.1 mm and narrowed **1.0 → 0.6 mm over 24 mm**.
   - **Current check:** U12 (TPS7A02) is capable of 200 mA at most. 0.6 mm of 0.5 oz inner copper is well above that (my estimate is about 0.8 A at a 15 K rise). The width also stays above the PWR_3V 0.5 mm plan width.
   - **Continuity:** power stays connected (power-class open edges are 0). The junction at via 178.9,87.08 was simplified, removing an acute 148° stub.
4. **GND:**
   - C280 GND via nudged 114.49,120.12 → 114.55,120.2;
   - the U9.3 hook was replaced by a fine via at 184.3,68.55;
   - the USB_AUDIO_R companion GND via moved 174.55,61.35 → 174.62,60.92. Still within 1.0 mm.
5. **Foreign-net via nudges for the LRCK lane:**
   - AUD_SDA 125.65,113.25 → 125.9,113.75;
   - CTRL_SDA 126.55,113.1 → 126.6,113.18;
   - CTRL_SCL 135.5,107.2 removed with its 4.4 mm In2 piece (the B now starts at via 131.15,107.2);
   - 5V_LOGIC_EN 139.6,104.75 → 139.7,104.79.
6. **Fine vias 0.5/0.2 inside NECK areas:** COM2 ×2 and U9 GND ×1.
   - The U8-side COM2 via at 173.55,62.22 has its centre outside U8.6, but its ring overlaps the pad edge. The via-in-pad gate (centre in pad) is unchanged at 7.
7. **AUDIO B jumper in BKO_MUX:**
   - COM2 uses the existing R6h rule-16 exemption for Net-(U8-COM2);
   - COM1's B jumper was re-routed inside the same exemption;
   - the HP_L B jumper stays outside BKO_MUX (y < 62.3).
8. **In2 slow-net corridors (existing whitelist):**
   - new or longer In2 runs: CHG_QON_SENSE 89 mm, BT_UART_TX 75, HP_EN 22, BT_RST_N 162 (was 141), ENC_SW 124 (was 27);
   - every one keeps ≥ 0.3 mm to the islands.
9. **Re-drawn signal copper:**
   - **U6 I2S/I2C fan-out:** BCK 125.2 → 125.0 mm, SDATA 125.5 → 125.6, LRCK 88.7 → 127.6 (the new U6 leg).
   - **USB_DP length-tuning meander:** the 10-rung 0.5 mm square wave became two 1.67 mm bumps with 90° near-side corners and a V-shaped far side.
     - Equal length (DP 51.59 mm); skew is unchanged.
     - Uncoupled length went 17.63 → 17.34 mm.
     - A version with vertical far-side segments was rejected because it added `diff_pair_gap_out_of_range` items.
10. **Smoother edits:** `route_r6j_smooth.py` made 54 widened chamfers and 2 shortcuts, all DRC-clean. Hand fixes: the BCK acute at 153.15,100.75 (ends directly at its via now) and the PWR(MFB) loop straightened after R182 left.

Not used: any DRC rule change, any island via, U9 rotation, C280/C271 moves.

## Remaining open edges (2): J7 NRST and SWCLK

- **Blocker:** the TC2030 middle pads J7.3 (NRST, 170.765,95.94) and J7.4 (SWCLK, 170.765,94.67) are enclosed:
  - pads 1/2 and 5/6 sit 0.48 mm away (a 0.2 mm track needs 0.6 mm);
  - the two Ø2.37 NPTH legs on each side leave 3.175 mm between centres, where 3.37 mm is needed with the 0.5 mm hole clearance.
  - The only connection is a via in each pad, which the via-in-pad gate forbids.
- **J6 (1×4 header) carries SWDIO / SWCLK / NRST / GND completely, and TP19 also carries NRST**, so SWD works without J7.
- **Recommendation:**
  - mark J7 as a test-only / do-not-route footprint, accepting these 2 open edges;
  - or, better, set it DNP or remove it in the schematic (coordinator decision; I did not edit the schematic);
  - if J7 must work, the alternative is 2 filled and capped via-in-pad (VIPPO) at J7.3/J7.4 as a listed fab exception.

## Long nets (mm, R6i-final → R6j-final)

| Net | R6i | R6j | Note |
|---|---|---|---|
| AMP_FAULT_N | 231.6 | 231.7 | Loop re-route experiment (`l3.json`, 46 min A\*) found the same 145.5 mm B path; kept |
| AUD_SDA | 232.6 | **278.0** | +45 mm = the two newly closed legs (U6 and U24). Loop re-route (`l2.json`) gave no gain |
| PD_SINK_EN | 134.0 | 134.2 | Unchanged; rip/re-route attempt in `h1.json` failed and restored |
| CTRL_SDA | 173.1 | 172.4 | Strip crossing kept short (25.8 mm local re-route) |
| CTRL_SCL | 141.6 | 141.4 | The In2 jumper piece was removed for the LRCK lane |
| Net-(U4-QON) | 136.0 | 136.0 | Untouched |
| **New / grown:** | | | |
| MCU/ENC_SW | 65.7 | **203.5** | Lost its strip lane to AUD_SDA/CTRL_SDA (see below) |
| BT_RST_N | 162.3 | 187.2 | Re-routed to free the HP_EN via |
| I2S_LRCK | 88.7 | 127.6 | New U6 leg |
| CHG_QON_SENSE | open | 135.0 | U3.3 → R113 (75 mm apart) |
| BT_UART_TX | 29.9 (open) | 146.3 | MCU → BM83 corner |

None of the six target nets reached 120 mm or less.

- **Where the length comes from:** the remaining length sits in two corridors:
  - the VBUS_PD_IN2 strip (In2 x 141–149.3, crossable only on F/B);
  - the U4/U25 power area. Its F/B space at y 95–150 is taken by the power pours and BKO_U7, which is why FAULT and AUD_SDA loop around the south edge.
- **The strip crossing near U24 (B, y 92–97) is now full:** 3V3_AUDIO, AUD_SDA, CTRL_SDA, ENC_A.
  - Of CTRL_SDA, ENC_A and ENC_SW, only two fit. I made ENC_SW (a debounced encoder input) the long one rather than the I2C bus: CTRL_SDA long = 276 mm.
- **Unlocking it:** shortening these needs a second crossing of the VBUS_PD strip. Options: a slot in VBUS_PD_IN2 for slow nets (island-via/slot exception), or moving the 3V3_AUDIO B link off the strip.

## Bend-rule hits (123 → 49)

- **Fixed (74):**
  - 56 by `route_r6j_smooth.py`: the R6i fixer plus asymmetric widened chamfers and 90° merges, accepted only with clearance-legal segments and fewer hits per net;
  - 9 by the USB_DP meander redraw;
  - single hand fixes: BCK, PWR(MFB), HP_EN at U3, the HP_SEL_B chamfer, the 3V_AO trunk junction.
- **Remaining 49:** 47 on copper inherited from R6i, 2 changed by the smoother but still slightly short.
  - 3V3_AUDIO 146.20,80.20 (1.15 / 1.20);
  - SYS_RAW In2 112.0,107.0 jog.
- **Unfixable without a DRC or quality regression, by group:**
  - **USB_DP (2):**
    - the J1 jog at 149.23,27.05: straightening it raised the pair's uncoupled length by 0.54 mm (rejected);
    - the meander tail 148.03,57.4: lengthening it creates `diff_pair_gap_out_of_range` (rejected).
  - **Power In2 acutes / short corners (21):**
    - 3V_AO 188.4,39.0 / 177.7,93.3 / 167.55,99.95 / 172.2,99.95;
    - 5V_CODEC ×2, 5V_LOGIC ×3, SYS_RAW ×3, LDO_3V3 In2, 3V3_AUDIO In2 ×2.
    - These are wide tracks (1.0–2.0 mm) whose limit is 3–6 mm. Every widened chamfer or merge collides with island outlines or adjacent vias.
  - **Pin-escape corners at fine-pitch ICs (U3, U8, U24, U2, U1, Q104, U7), F.Cu, 13:**
    - AUD_SDA 189.6,95.15; SWCLK 192.65,85.5; NC2 ×2; U2-D- ×2; U24-XO; Q104-G ×2; U7-OUT_B+; LDO_3V3 F ×2; U1-SYS_PWR.
    - All candidates violate the 0.2 mm neck clearance to neighbouring pins or vias.
  - **Signal corners next to GND / audio vias (11):**
    - BT_AUDIO_R 164.4,77.3 (GND via at 0.225 mm leaves no room); PD_PLUG_EVENT F/In2; CTRL_SDA In2 126.3,103.5 (merge hits the CTRL_SCL via at 0.11 mm); PDCTRL_SDA In2; QON 127.85,104.8; C230-Pad2; HP_SEL_A acute; USB_AUX_5V acute; REGN ×2; PMID; U24-AVDD; switching nodes U14-L2 / U15-L2 / C305-Pad1 ×2 (wide SWITCH copper; 1.0 mm rule).
- Full list with coordinates: `work-r6/R6j-final.bends.json`.

## Helpers (new, `ai-files/helpers/`)

- `route_r6j_eval.sh` and `route_r6j_step.sh`: the R6i gates pointed at R6j rules and the R6j-0 island reference.
- `route_r6j_smooth.py`: the R6i smoother plus asymmetric chamfers and bend merging.
- `route_r6j_u6fan.py`: the U6 fan-out generator.
- `route_r6j_in2obs.py` and `route_r6j_trunkplan.py`: In2 obstacle export and a grid A\* for the 3V_AO trunk.
- `route_r6j_lens.py`: net-length table.
- `route_r6j_dangle.py` and `route_r6j_clean.sh`: DRC-driven dangling cleanup that undoes a round if open edges grow.
  - `route_r6i_route.py`'s own `prune` once removed live CTRL_SDA copper (29 items, a T-joined route). Plans that use it should pass `noprune` and clean up with this tool.

**Reproduction chain** (specs in `work-r6/r6j/`):
1. R6j-0 + a1, a2;
2. q1, q2 (router);
3. c2, c5;
4. t1, t2;
5. e1, e2;
6. s1, s2, s3, s4;
7. b1;
8. p_CAS (router, no prune), then s11, then g1;
9. `route_r6j_clean.sh`;
10. f3 (f1 + f2 + u1);
11. `route_r6j_smooth.py`;
12. h3, h4.

## Remaining blockers / next steps

1. **J7 NRST / SWCLK:** a schematic decision (test-only, DNP or VIPPO) is needed; see above.
2. **Long nets:** they need a second VBUS_PD strip crossing, plus a planned east–west corridor through the U4/U25 area.
   - ENC_SW (203 mm) is the first candidate to bring back once a strip lane exists.
