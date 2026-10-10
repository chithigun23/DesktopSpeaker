# Routing R6h (2026-10-09): In2 slow-net corridors on R6g-final, stopped at 25 open edges

Work copies only (`ai-files/pcb/work-r6/R6h-*`). Hand specs are in `work-r6/r6h/`:
- `b1`–`b3`: PD_SINK_EN and CTRL_SDA rip-up and the dangling-via fix;
- `m1`: COM1;
- `u0`, `u1`, `i1`: rejected U4 trials.

A\* was run for the In2 routes. Intermediate boards were deleted. `DesktopSpeaker-kicad/` was not touched. Nothing was committed.

- **Final board:** `work-r6/R6h-final.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`, `.drc.json`, `.open2.json`, `.isl.json`). `R6h-0.*` is the R6g-final baseline copy.
- **Renders:** `ai-files/pcb/route-r6h-top.png`, `route-r6h-bottom.png`, `route-r6h-in2.png`.
- **Rules (`R6h.kicad_dru`, written by `helpers/route_r6h_dru.py`):** R6g rules plus:
  - rule 11 (In2 power-only) now exempts the 42 slow nets in `helpers/route_r6h_slow.json`;
  - new rule 19: slow In2 tracks keep 0.3 mm from every non-GND In2 zone;
  - rule 16 (BKO) exempts `Net-(U8-COM1)` and `Net-(U8-COM2)`.
- **New helpers:**
  - `route_r6h_route.py`: A\* router with the `--in2` slow-net layer, the 0.3 mm island mask, and `R6H_VIAISL` (U4 nets may put vias in the listed islands).
  - `route_r6h_chk.py`: pre-checks a hand spec against the R6 rules, including neck relaxation, SW 1 mm, BATP 2 mm and In2 islands.
  - `route_r6h_view.py`: three-panel region render with a 1 mm grid.
  - `route_r6h_dbg.py`: A\* obstacle map for F, In2 and B.
  - `route_r6h_isl.py`: island continuity, In2 signal list, and foreign vias in islands.
  - `route_r6h_eval.sh` and `route_r6h_step.sh`: the gates.

## Result

| | R6g-final | R6h-final |
|---|---|---|
| Open edges (fragment-aware, all nets) | 28 | **25** |
| Default / I2C / AUDIO / I2S_CLK | 14 / 5 / 8 / 1 | 12 / 5 / 7 / 1 |
| Power-class open edges | 0 | 0 (power connectivity unchanged) |
| DRC: clearance, shorts, dangling, isolated copper, track width | 0 | **0** |
| DRC: USB items (pair untouched) | 3 skew, 1 uncoupled | same |
| DRC: silk/lib items | 33 | 33 |
| Vias total (GND / signal) | 716 (245 / 471) | 727 (246 / 481) |
| Via centre in SMD pad (non-EP) | 11 | 11, the same list |
| EP vias U6 / U7 / U25 | 16 / 16 / 8 | 16 / 16 / 8 |
| Antenna keep-out items | 1 (pre-existing) | 1 |
| Foreign non-GND vias in In2 islands | 24 | 24 (the island-via exception ended up unused) |

**Island continuity:**
- Every power pour and island is still one fill outline.
- Areas are identical to a no-op refill of R6g-final. That check board was not kept.
- The only deltas against R6g-final's stored fill (for example PVDD_U6L/U7L/U7R, USB_VBUS_U11_F, VBUS_PD_U11_F, VBUS_U4A_F) come from the refill itself. They appear with zero edits.
- The new In2 signal tracks cut two small In2 GND-background islands, which island removal deletes:
  - x 121–127, y 106–114;
  - x 154–172, y 90–101.
- In1 stays solid GND.

**Closed:**
- MCU/ENC_A (the R6g regression, restored through In2).
- ADC_INT (In2).
- Net-(U8-COM1) (AUDIO B jumper, exception 3).

**Shortened:**
- PD_SINK_EN: 149.8 → 70.5 mm.
- CTRL_SDA: 223.3 → 163.4 mm (the U13 leg was re-routed).

## Exceptions used (net, location)

**1. In2 corridors (slow nets only).** All are more than 0.3 mm from the islands (DRC rule 19 and `route_r6h_isl.py`). No audio, I2S, USB or clock net is on In2.

| Net | In2 length | Route |
|---|---|---|
| /MCU/ENC_A | 36.3 mm | (189.5,84.95)→(178.9,95.5) and west under the U3/TP band |
| /ADC_INT | 33.0 mm | U3.26 to U24/R211 across x 150–186, y 89–95 |
| /PD_SINK_EN | 28.2 mm | (179.8,77.3)→(164.85,70.25) and (139.8,58.85)→(134.75,64.0) near U11 |
| /CTRL_SDA | 7.0 mm | U13-leg hop near x 121–140, y 106–113 |

**3. AUDIO jumper inside BKO_MUX:** Net-(U8-COM1).
- From U8.10, an F stub runs to via 170.85,61.85 (0.6/0.3, just outside BKO_MUX).
- B runs (171.6,62.6)→(174.6,62.6)→(176.6,64.6)→(183.8,64.6).
- It reaches via 183.8,64.6 (0.5/0.2, inside the U9 body), then an F stub to U9.9. B length 17 mm, 2 vias.
- GND via 170.05,61.85 sits beside the first via. The second via's nearest GND via is the existing 183.04,65.95, 1.55 mm away.

**Not used:**
- Island vias for U4: no complete route exists (see below).
- The BAT_INT_F slot.
- U9 rotation.

**Briefed moves checked and not applied:**
- **SW2 via 1 mm east:** the via lands on the C104.2 GND pad (154.92,115.49) and shorts. 0.5 mm east gives no extra lane.
- **R100/R103/R108 out of the bay:** does not create via room. There are 7 escapes at 0.4 mm pitch, and a via needs about 1.15 mm between the neighbouring tracks.
- **3V_AO dog-leg:** a shift of the whole diagonal hits 7 vias. A shift big enough for HP_SEL_B, at 1.5 mm or more, was not attempted.
- **C280 NE:** lands on BCK/SDATA.
- **R182 1 mm east:** pad 1 lands on the PWR(MFB) loop.
- **Audio cap re-placements:** no corridor exists to make use of them (see below).

## Open edges (25) and the blocker for each

### Default (12)

**U4 group: CE_N, Net-(U4-QON), ILIM_HIZ, Net-(U4-BATP), CHG_INT (5, plus CTRL_SCL ×2 below).**

The island-via exception removes the In2 objection, but the copper around U4 still blocks every exit:

- **F, south bay:** 7 pin escapes at 0.4 mm pitch, plus R103/R108/R100/C313 and the CTRL_SDA via 152.45,125.2. No second via fits.
- **F, east side:** a stack of BAT_INT 0.6, PROG, BTST2 (BOOT, 2 mm from BATP) and ILIM.
- **Under the body:** room for about 4 fine vias (x 150.4–152.6, y 121.4–123.3). But on B the U4 area is fenced:
  - SW1 jumper to the west, and SW2 jumper to the east (1 mm rule).
  - **North gap:** between the SW vias at 150.1 and 153.0 (y 115.2) only 0.03 mm of centreline space remains, because of the PGND via column at 151.57, y 116.6–118.4.
  - **West gap:** used up by CTRL_SDA. At x 146.45, y ≥ 123.15 is needed and y ≤ 122.9 is available.
  - **South:** leads only west. The targets' side is closed by SW2 (via 156.55,125.57) and the REGN B diagonal (155.45,127.6)→(176.35,106.75). That centreline gap is 1.27 mm, and 1.3 mm is needed.
- **A\* attempts** (VIAISL, 0.5 mm fine vias, margin 0.012): all U4 nets fail.
  - **ILIM:** a hand bay via at 154.67,125.1 is legal, but a 15-minute search from it found no route.
- **QON far end:** SW100 sits at the board edge, about 100 mm away.
- **Unlock (re-plan, not hand-routing):**
  1. Move one PGND via (151.57,116.6) or the whole column. This opens 1 north lane.
  2. Re-escape CTRL_SDA through an inner via. This turns the west gap into 3 lanes.
  3. Re-route REGN→R110 off the B diagonal.
  4. Then route a planned U4 bundle: inner vias for CHG_INT/BATP/QON/SCL, bay vias for CE_N/ILIM, a west column at x 140.7–142.4, and an east run at y 109–113.8 (BATP ≤ 112.8, 2 mm from the SW vias).

**AMP_FAULT_N (U6 leg):**
- U6 lies under BKO_U6 and PVDD_IN2, so F is the only layer there.
- In2 cannot cross x 141–149.3 anywhere: VBUS_PD_IN2 covers y 55–129, with SYS/PVDD below it.
- The F/B crossing of that strip at y 95–125 is full (BCK/SDATA/AMP_PDN/AUD_SCL/CTRL_SDA). A\* with In2 fails.

**HP_SEL_B (U9.1–U9.5):**
- The U9.3 GND hook (F, y 68.65) blocks the pin-1 stub.
- A replacement GND via, or an HP_SEL_B via south of the pins, hits the 3V_AO In2 trunk (1.0 mm, x 183.4–184.4 at y 69) and the GND via at 182.7,68.7.
- The R235.1 side is boxed by the HP_OUTR and C235-Pad2 audio diagonals (0.5 mm).
- Needs a U9 180° rotation (all 10 pins re-routed) or a 3V_AO trunk move of 1.5 mm or more.

**HP_EN:** unchanged from R6g (the SWCLK and CODEC_PWR_EN risers). A\* with In2 fails.

**BT_UART_TX:**
- **F:** R182.1 is enclosed on the N, E and S sides by the PWR(MFB) loop (R183.2→U1.26).
- **B:** BT_RST_M runs underneath at x 113.45, so no via fits.
- MFB and RXD_M cross topologically (U1.26/29 against R183/R182), so one of them has to loop.
- **Needs:** R182 relocated a few mm, for example onto the RXD_M→J8 path. That is not a briefed move.
- The ~150 mm leg is not routed; without an end point it closes nothing.

**CHG_QON_SENSE (U3.3):**
- **Outward:** blocked by the CHG_INT F diagonal (177.7,84.35)→(179.5,86.6), with 0.115 mm clearance.
- **Vias in front of U3.2–U3.6:** any via there hits the 3V_AO In2 trunk (x ≈ 178.7).
- **Inward:** blocked by the PD_PLUG_EVENT hook (181.5,85.65)→(181.45,84.25) and the PDCTRL_SCL B diagonal.
- **Fix:** re-route the last CHG_INT leg (part of the U4 group), or the PD_PLUG_EVENT hook.

**MCU/NRST, MCU/SWCLK at J7:** duplicate SWD pads; J6 carries SWD. A\* (NRST with In2) fails.

### I2C (5)

- **AUD_SDA ×3:**
  - U24.23 is enclosed by R209/R211.
  - The R210 and U6.15 legs cross AMP_PDN/AUD_SCL.
  - A\* with In2 fails.
- **CTRL_SCL ×2:** part of the U4 group.

### AUDIO (7)

**BT_AUDIO_L ×2, BT_AUDIO_R ×2, USB_AUDIO_R, Net-(C205-Pad2):**
- The C201/C202/C203 pad-1 sides are boxed by:
  - the C200-Pad2 F wall (x 162.0–162.65, y 61.65–78.3);
  - the C233-Pad2 loop to R223 and the via 170.15,72.55.
- The F/B field at x 130–176, y 50–90 is dense with digital nets: PD_PLUG_EVENT, PD_SINK_EN, BT_PWR_EN, BT_MFB, ENC_B/SW, SWD, HP_SEL_A.
- A\* fails at once. The F free-space map shows no BM83→ADC corridor.
- **Unlock:** move those slow nets onto In2 (now allowed) to clear a 70–80 mm F corridor, then re-place C202/C203/C233/R223.

**Net-(U8-COM2):**
- U8.6 is wrapped by the NC2 hook inside the U8 body (going to the resistor at 174.59,63.17).
- 3V3_AUDIO lies to the north (0.5 mm audio clearance).
- **Needs:** NC2 re-routed. Its end pad sits between U8.6 and C231-Pad2, so no hook fits.

### I2S_CLK (1)

**LRCK U6 leg:**
- The corner beside BCK lies 0.155 mm from the C280 GND pad (0.2 mm needed).
- C280's GND via at 114.49,120.12 leaves 0.225 mm beside BCK; 0.65 mm is needed.
- **Options:**
  - Move that via. This first needs FAULT's north detour at x 115.1 moved.
  - Move C280. NE lands it on BCK/SDATA.

## Long nets (final)

| Net | R6g | R6h | Vias | In2 |
|---|---|---|---|---|
| PD_SINK_EN | 149.8 | **70.5** | 8 | 28.2 |
| CTRL_SDA | 223.3 | **163.4** | 10 | 7.0 |
| TS_SENSE | 112.5 | 112.5 | 2 | – |
| 5V_LOGIC_EN | 101.4 | 101.4 | 8 | – |
| AUD_SCL | 166.8 | 166.8 | 7 | – |
| AMP_BOOST_EN / AMP_PDN | 98.7 / 106.7 | same | 4 / 8 | – |
| MCU/ENC_A | 36.9 (open) | 101.8 | 6 | 36.3 |
| ADC_INT | 3.6 (open) | 47.9 | 6 | 33.0 |
| BT_TX_IND / RST_N / UART_RX / FORCE_PWM | 161.0 / 161.5 / 142.0 / 154.5 | same | | – |

Lengths in mm.

- **CTRL_SDA and AUD_SCL** stay above 120 mm because of their spread: U4/U3/U13 and U6/U7/U24/U3. Their Steiner minimum is about 160 mm.
- **TS_SENSE and 5V_LOGIC_EN** are already at 120 mm or less.

**USB:** DP 51.59 mm, DN 51.36 mm (unchanged).

**I2S:** BCK 125.3 mm / 2 vias, SDATA 125.7 mm / 3 vias, LRCK 88.9 mm / 4 vias (unchanged).

## Gates (run after every batch)

- DRC: 0 clearance, shorts, dangling, isolated copper and track width.
- Fragment-aware open edges.
- `route_r6c_gates.py`: via-in-pad, EP, antenna, lengths.
- `route_r6h_isl.py`: island continuity, In2 signals at 0.3 mm or more, foreign vias in islands.
- Power-class open edges: 0.

## Why this round stops at 25 open edges (more than 8)

The remaining edges are not hand-routing gaps. Each sits behind copper that has to be re-planned first:

1. **The U4 B fence** (7 edges): the PGND via column, the CTRL_SDA west escape and the REGN diagonal.
2. **The audio field** (7 edges): it needs the slow digital nets moved to In2, and then the caps re-placed.
3. **Single local knots** (11 edges):
   - CHG_QON_SENSE and BT_UART_TX: R182 placement.
   - HP_SEL_B: U9 rotation or the 3V_AO trunk.
   - LRCK: C280 and the FAULT detour.
   - AUD_SDA ×3: U24.23 and the R210/U6.15 legs.
   - FAULT: the VBUS_PD strip crossing.
   - HP_EN, NRST, SWCLK.

Even a full U4 bundle would leave 18 edges. The next step is a coordinated re-plan of these areas (U4 bundle, then an audio-field In2 migration), not more hand-routing on this base.
