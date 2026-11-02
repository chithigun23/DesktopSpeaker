# RT-8: MCU escape redesign and remaining groups (2026-11-02)

Agent "RT-8 MCU escape redesign and remaining groups".
- **Input:** `ai-files/pcb/work-route7/RT-7.*` (220/283 connections, DRC 0, 64 unconnected).
- **Work folder:** `ai-files/pcb/work-route8/` only.
- **Result:** `ai-files/pcb/work-route8/RT-8.kicad_pcb/.kicad_pro/.kicad_dru`.
- **Untouched:** nothing in `DesktopSpeaker-kicad/`, earlier work folders or `helpers/route_oct*.py` was edited.
- **Method:** all board edits are text edits (`scripts/edit.py`, now also able to delete arcs). Every build was refilled in a separate pcbnew process with the pristine `.kicad_pro`/`.kicad_dru` beside the board (`scripts/cycle.sh`).
- **Not done:** not committed, nothing published.

**Bottom line.**
- Unconnected went from **64 to 56**, with **DRC 0** and every gate green.
- U3's escape was redesigned in place: 191 segments and 46 vias were ripped and re-escaped, with exit-lane protection and manual via fans.
- 11 connections were closed and 3 were lost (net 8). The 3 losses:
  - PDCTRL_SDA U3-44;
  - PDCTRL_SCL U3-43 → U11;
  - NRST U3 → J7-3.
- The two PDCTRL items disconnect the MCU from the TPS25730D status I2C. The PD sink still negotiates standalone; only status reads are lost. The cause is the north-escape capacity limit described in section 3.3.
- CHG_INT is moved to the accepted-unrouted list, with a schematic patch for the coordinator (`ai-files/pcb/work-route8/schematic-patch.md`).
- No release-todo file was written: 55 connections that are not accepted remain open.

## 1. Result and gates

| gate | RT-7 | RT-8 |
|---|---|---|
| kicad-cli DRC `--severity-all --all-track-errors` (RT-7 rules, project library) | 0 | **0** |
| DRC unconnected | 64 | **56** (1 accepted: CHG_INT; section 6) |
| closed vs RT-7 | | AMP_BOOST_EN, AUD_SCL (U24 side), BT_PWR_EN, CTRL_SDA (U13 side), HP_SEL_A (U3-13 → U8-5/R234), MCU/SWCLK (J6), MCU/SWDIO ×2 (J7, J6), MCU/NRST (J6), PD_PLUG_EVENT (U11-37), Q101-G (R110-2 → Q101-1): **11** |
| opened vs RT-7 | | PDCTRL_SCL U3-43 ↔ U11 group, PDCTRL_SDA U3-44 ↔ U11 group, NRST J7-3 ↔ U3-12: **3** (section 3.3) |
| footprints moved | | **R110 only**: rotated 180° in place, (176.59, 108.82) rot 90 → 270. All 359 others unchanged. |
| pad nets of 360 footprints / 1194 pads vs RT-7 | | **unchanged** (gates4 `pad_net_diff []`) |
| rule files | `.kicad_dru` ce43baa1…, `.kicad_pro` aa88e8c9… | **identical to RT-7**. No new rule, no exemption. |
| sentinel (I2S_CLK width ≥ 5 mm appended to a copy) | FIRES | **FIRES** (81 items) |
| locked copper (RT-7 items untouched) | | 2909 of 3173. 264 removed or changed, all listed in the edit reports, 0 unexpected. SHA-256 `af2890b9097cac38d2a044b6e5c8302e19c0aaef7dcfda2bdb8e278073366aa2` |
| new copper exactly 0/45/90 (gates4, own text parse) | | **376 segments, 1052.6 mm, 0 not exact**; 121 vias added |
| pour check (route_oct_pourcheck, RT-7 → RT-8) | | **OK** (foreign unconnected 43 → 43) |
| parcheck (< 0.4 mm over > 3 mm, touched nets) | sensitive 0, other 1 | sensitive **0** (only the intended USB pair). Other **9** slow pairs (section 5). |
| sensitive vias farther than 1.5 mm from GND | 0 | **0** (17 vias, worst 1.39 mm, AUD_SDA inherited) |
| r7 joints < 80° / < 30° | 19 / 7 | **19 / 7** (two 0° reversals created by the router at cut ends were removed in build KG7) |
| r7 BM83 F.Cu inside module | GND 2.3, SYS_PWR 2.0 | **unchanged**; 0 mm of new copper |
| HA8 failing pairs | 122 | **122** (no new pair, none tighter) |
| BAT_INT U4-22/23 → Q103 (6 A, 20 °C) | 2.889 mΩ | **2.889 mΩ** (104.0 mW, unchanged) |
| silkscreen (silk_tile copy `scripts/silk_tile8.py`, unchanged data, + gate) | ALL PASS | **G1-G6 ALL PASS** (`RT-8.silkgate.json`) |
| length (route_oct_check, 34 touched nets, 23 complete) | | median **1.27**, p95 **1.79**, max 2.09 (PD_PLUG_EVENT, slow, limit 3.5). Above 1.4: ADC_INT 1.61, BT_FORCE_PWM 1.42, CODEC_PWR_EN 1.79, HP_DET 1.76. ADC_INT is 35.6 mm against a 1.5× + 1 = 34.1 mm sense limit (section 5). |

## 2. U3 escape redesign (decision 1)

**Placement: U3 stays at (128.0, 76.5) at 90°. It was not moved or rotated, and its support parts did not move.** The pins are fixed by the schematic, so a rotation only permutes which side each pin faces. I counted, for every signal pin, how many have their nearest peer behind their own side:

| rotation (relative) | pins facing away | octilinear sum to peers |
|---|---|---|
| 0 (current) | 12 | 1447 mm |
| 90 | 13 | 1452 mm |
| 180 | 24 | 1552 mm |
| 270 | 24 | 1562 mm |

A move of up to 12 mm runs into hard edges on every side:
- east: the U24/ADC block and BKO_ADC (x 144-160);
- north: J7, U11 and the foreign BT_AUDIO_L/R pair;
- south-west: the H8 mounting hole at (117.2, 85.8);
- south: the cap row, TP19 and the 3V_AO bar.

Neither ND nor fit data changes, because U3, J7 and every support part keep their positions.

**Rip-up** (`scripts/ripwin.py`, plan `t/rip1.json`, build K0): every segment of the 39 U3 signal nets with an end inside x 116.5-140, y 64.5-89, and every via inside that box.
- 191 segments and 46 vias were removed.
- Floating fragments were removed; cut ends were kept as targets.
- GND, 3V_AO and all foreign copper are locked.

**Escape method** (router `scripts/hr8.py` = hr7 copy plus via end points, a `tgt_near` target filter and F.Cu restriction boxes; job builders `jobs_u3c.py` and `fix8.py`):
- **Via-first pins.** These are pins whose target is behind the package, or that cross a planar neighbour. They drop to B.Cu or In2 next to the pin. N-S nets under the body are biased to In2 and E-W nets to B.Cu. F.Cu is allowed only in the pin's escape box and near its target.
- **Planar F.Cu fan.** For the other pins on each side: left-turners from the left end, right-turners from the right end, straight pins last.
- **Exit lanes.** Every job keeps the exit lanes of the U3 pins routed later free: an F.Cu block 1.0 mm beyond the pad tip, plus a no-via box extended 0.8 mm (1.5 mm for long nets) and widened by via radius plus clearance.

**Manual escapes**, where the lattice search boxed itself in. Fine vias 0.5/0.2 inside NECK_U3:

| net | pin | F.Cu stub (w 0.25 unless noted) | via |
|---|---|---|---|
| AUD_SDA | U3-31 | (133.675, 73.25)-(135.7, 73.25)-(136.05, 72.9), w 0.3 | (136.05, 72.9) |
| BT_RST_N | U3-58 | (122.325, 77.25)-(121.0, 77.25)-(120.6, 77.65) | (120.6, 77.65) |
| BT_MFB | U3-57 | (122.325, 76.75)-(120.35, 76.75)-(119.8, 77.3) | (119.8, 77.3) |
| BT_TX_IND | U3-62 | (122.325, 79.25)-(120.5, 79.25)-(120.15, 79.6) | removed in cleanup KG2 (the route continues on F.Cu from that point) |
| PD_SINK_EN | U3-63 | (122.325, 79.75)-(121.3, 79.75)-(120.95, 80.1) | (120.95, 80.1) |

**Re-assignments inside the same nets:**
- CTRL_SDA U3-61 now goes west on F.Cu into the U13/R121 branch, which closes RT-7's open item. The TP15/U4 branch rejoins from the TP15 via.
- PDCTRL_SCL: R15-2 has been boxed since RT-7. U3-43 was aimed at the U11-9 branch, but the final state links U3-43 only to the J4 branch (section 3.3).

**Phase B, the long nets.** These were routed sequentially in three orders and as single parallel jobs, then merged with DRC as referee. Routed:

| net | from | length | vias |
|---|---|---|---|
| MCU/NRST | J6-3 | 49.9 mm | 5 |
| MCU/SWDIO | J6-1 | 57.8 mm | |
| MCU/SWCLK | J6-2 | 55.1 mm | |
| BT_PWR_EN | | 45.0 mm | |
| PD_PLUG_EVENT | U11-37 | 30.7 mm | |
| HP_SEL_A | U3-13 | 53.2 mm, ratio 1.13 | |
| AMP_BOOST_EN | | 89.3 mm (net ratio 1.27) | 8 |

**Cleanup:**
- **KG1** (`scripts/prune2.py`): dead copper at cut ends removed without breaking connections. Free ends are trimmed back along their own line, so angles do not change.
- **KG2-KG6:** five single-layer vias handled by hand. Three were deleted, because their segments already met at the via centre. Two were replaced by 45° links: ENC_SW (125.175, 92.45)-(125.275, 92.55)-(125.275, 92.65) on F.Cu, and HP_DET (134.725, 64.15)-(134.625, 64.05)-(134.625, 63.95) on B.Cu. Dead stub chains on NRST (J7 side) and PDCTRL_SDA (U11 side) were removed.
- **KG7:** the two 0° reversals were removed: AUD_SCL at TP18 (132.2-134.25, y 102.0) and PDCTRL_SCL at J4 (x 115.35, y 61.75-63.7).
- The plan I tried first, `scripts/prune.py` (delete what DRC calls dangling), broke 4 nets in build KP1-KP8. It was discarded; the KP boards are kept only as evidence.

**Iterations (AG13).** Three iterations, each run as several parallel order variants. All logs are in `t/`.
1. Ordered single run (`jA`). 29 of 38 OK.
2. Exit-lane and no-via-box variants v1-v15. Best 28-30 of 38. EXT 2.5 was worse.
3. Side fix-ups:
   - E: `jLE`, 3/3.
   - W: 20 orders. The manual via fan in `jMi` routes all 11.
   - N: 12 orders. Always one of CODEC_PWR_EN, PDCTRL_SCL and PDCTRL_SDA fails.
   - Phase B: `PB`/`PC`/`PD`/`PL`, `Q6_*`, `Q7_*`, `R*`, `W*`, `Z*`.

## 3. U3 group: what is still open and why

### 3.1 Long nets whose pin exit is boxed or whose search ran out
| net | pins | result | cause |
|---|---|---|---|
| HP_EN | U3-47 | exp 171 | Under-package B/In2 is fully used by the via-first nets. The pin lane is protected, but its via has no exit. |
| HP_SEL_B ×2 | U3-51 | exp 198 | West side: the BT via fan and ENC_A/ENC_B occupy the vias next to pin 51. |
| AUX_DET | U3-29 | exp 19 | East side: the AUD_SDA via (136.05, 72.9) and the AUD_SCL straight lane enclose pin 29. |
| CHG_ENABLE | U3-38 | 62.8 mm found on KA6, lost after the N-side PDCTRL routes and PD_SINK_EN were added | north corridor |
| CHG_SYS_ENABLE | U3-42 | exp 167 / 4-8M | north corridor, then the Q102/R111 pocket (section 4.1) |
| AMP_FAULT_N ×4 | U3-25, U6-9, R262-2, TP20, U7-9 | 8M nodes without a path | R262-2/U6-9 pocket (RT-7 3.2) plus the 80 mm path |
| HP_G0 ×2 | U3-16, R237/U10-6 | 8M nodes | path along the south side then east, through the mux block |
| AMP_PDN | R258-1 | no path | R258 between the AUD_SCL detour and the SDATA diagonal |

### 3.2 Re-routed restores that held: all except three
All U3 connections that RT-7 had closed are closed again, except the three in 3.3. This covers:
- GAUGE_ALRT_N, 5V_LOGIC_EN (U14 side), AUD_SDA/AUD_SCL, ADC_INT, HP_DET, HP_G1;
- CHG_QON_SENSE, PD_PLUG_EVENT (R16), ENC_A/B/SW, CODEC_PWR_EN, BT bundle ×6;
- CTRL_SCL/CTRL_SDA, SWDIO/SWCLK (J7), NRST (C162/TP19), CHG_INT pull-up (U3-5 → R106-2), AMP_PDN (R259, R257), PD_SINK_EN (U3 → R17 side).

### 3.3 The north-escape limit (PDCTRL_SCL, PDCTRL_SDA, NRST J7)
The foreign BT_AUDIO_L runs as an F.Cu diagonal x − y = 64.5 from (128.77, 64.42) to (134.27, 69.92), only 0.2-2.5 mm from U3's north pin row. Its B.Cu partner BT_AUDIO_R runs at y 59.6-62.6. Every north-bound U3 net must hop this audio pair, inside a 5 mm corridor that also carries:
- SWDIO/SWCLK to J7;
- the via escapes of CODEC_PWR_EN, CHG_QON_SENSE and PD_PLUG_EVENT;
- the long-net lanes of pins 36/38/42/47.

In 12 N-side orders only two of CODEC_PWR_EN, PDCTRL_SCL and PDCTRL_SDA fit. With BT_PWR_EN and PD_PLUG_EVENT (U11-37) also routed through the corridor, both PDCTRL lines to U11 fail. I kept BT_PWR_EN, PD_PLUG_EVENT and CODEC_PWR_EN and lost the U11 status I2C:
- the firmware spec uses that I2C only as "rare, low-rate status traffic" on a software bus;
- the TPS25730D negotiates standalone.

The J7 NRST branch would have to cross the saturated under-package B/In2 from the north row to pin 12 on the south row.

**Remedies** (one per bullet; either first one frees about 2 mm):
- (a) Re-route BT_AUDIO_L along y ≈ 62.5 east of x 128.8, so it no longer dives to (134.27, 69.92). This is an audio net; the length change is under 1 mm. It needs coordinator approval, because it is foreign copper.
- (b) Move U3, C160-C162, R106, R160 and R259 1.5 mm south. Check the H8 clearance first.
- (c) J7-3 NRST: a 25 mm B.Cu lane west of J7 into the NRST copper of the J6 branch.

## 4. Other groups (decision 3)

### 4.1 U4 group
- **Q101-G: 2 open → 1 open.** R110 is rotated 180° in place, so REGN (R110-1) is on top at (176.59, 108.2225) and Q101-G (R110-2) at the bottom at (176.59, 109.4175).
  - Removed: REGN segments 053c1e0a (176.59, 109.4175)-(177.034, 109.000) and 9afe631e (177.075, 107.511)-(176.35, 106.75), and the REGN arc 8568558e.
  - Added: REGN F.Cu 0.4 (176.35, 106.75)-(176.35, 107.9825)-(176.59, 108.2225), from via e13b26f7.
  - Added: Q101-G F.Cu 0.25 (176.59, 109.4175)-(178.67, 109.4175)-(178.85, 109.5975) into Q101-1.
  - Q102-3 stays open. It is north of the AUD_SCL detour (y 106-108.7), which separates it from Q101-1.
  - Tried and rejected: AUD_SCL north of Q102. The corridor exists (y 104.13-104.28 between LRCK at y 103.25 and the Q102 pads), but the descent to (183.6, 109.8) is blocked on both sides:
    - East of R111: the I2S_SDATA diagonal x − y = 78.4 leaves 0.73 mm where 0.9 mm is needed.
    - West of R111: the descent would cut the CHG_SYS_ENABLE Q102-1 → R111-1 stub.
  - Remedy: move R111 to the west side of Q102-1, then run AUD_SCL down at x 180.86.
- **CHG_INT: accepted unrouted (decision 2).** An escape search from U4-21 with F/B/In2, fine vias and island vias (`t/jCI.log`) gives **exp 0**: no legal first step. U3-5 → R106-2 is routed. The proposal is `work-route8/schematic-patch.md` P1:
  - firmware polls REG1B-REG27 (status, fault and flag registers) over I2C every 250 ms while a source is attached;
  - U4-21 gets a no-connect flag;
  - the hierarchical CHG_INT chain is removed;
  - U3 PC15 keeps R106 as a pulled-up spare.
- **CTRL_SCL (U4-14), QON, ILIM_HIZ: unchanged.** At 0.4 mm pitch, an SCL via between CE_N (x 151.77) and the SDA via (152.57, 125.28) misses clearance by 0.15 mm.
  - Remedy: move R103 1 mm south-west and drop CE_N to B.Cu at pin 13. That frees x 151.4-151.9 for the QON via, and SCL takes a second-row via at (152.17, 125.95).
  - This needs the REGN via (148.79, 122.58) moved 0.6 mm north for the B.Cu lane. ILIM_HIZ as RT-7.

### 4.2 I2S BCK hub (2 open): not changed; topology analysed
The hub order is L, B, S (R208/R207/R206, set by the U24 pinout). Both amplifier fans need S, B, L in the direction of travel. So BCK must cross LRCK and SDATA once on the U6 path and once on the U7 path: 4 crossings.

Each crossing must sit over In2 GND, but the whole hub column x 138.84-149.46 (y 92-104) is VBUS_PD on In2. The U7 fan also has no lane: the SDATA and LRCK diagonals are 0.92 mm apart, and U7-13 sits under the SDATA vertical (x 192.345).

Remedy (needs a power-zone edit):
1. Shrink VBUS_PD_IN2 to x ≥ 144.6 for y 90-106. That is about 1.3 mΩ for 3 A.
2. Move TP14 west.
3. Hop BCK under LRCK and SDATA with GND stitches into the reserved U6 lane x + y = 232.19.
4. Re-fan U7 pins 12-14 at 1.3 mm spacing.

### 4.3 AUD I2C and amplifier control (U6/U7)
Unchanged as RT-7 section 3.2: AUD_SDA U24-23 and U7-15, U7-PDN and AMP_FAULT_N. The remedy is the R262 move plus the AUD_SCL re-route from 4.1.

### 4.4 U24 input block, USB audio, headphone mux (17 open): unchanged
RT-7's remedies stand:
- re-place R225/R229/C235 and R226/R227/R231/R234/R235 next to their pins;
- feed U9-8 from In2;
- an NO/NC fan alternating north/south.

BKO_MUX forbids B.Cu signals under the mux. HP_SEL_A is now routed from U3 to U8-5/R234; U8-1 is boxed by the U8-2 NO1 escape.

### 4.5 C215-C212 tweezers gap (HA8 0.14 mm): not fixed, trade-off for the owner
- Moving C212 east by 0.26 mm puts its pad on VINR1 (x 152.745), so the RT-7 VINR1 closure would be lost.
- Moving C215 west needs XO (x 150.245) 0.15 mm west, which is impossible: XI runs straight up at x 149.7675 with a 0.228 mm gap today.
- Moving either cap in y breaks the 3 mm HF-decoupling rule (C215-1 to U24-8 would be 4.0 mm).

The only legal fix gives up VINR1. RT-8 keeps VINR1; the owner should choose.

### 4.6 USB-C/PD/regulators/gauge, BT/debug, 3V_AO: unchanged
- **U14-FB:** the R140 2 mm move plan needs R140-1's 5V_LOGIC link rebuilt; not attempted. The analysis is in my notes: FB via at (98.47, 105.3) after R140 moves 1.8 mm east, then B.Cu west at y 105.8.
- **5V_LOGIC_EN R142, U12-EN, GAUGE_ISO_N, U11-ADC4, R18, PD_SINK_EN (U11-19 ↔ R17), USB_CC1/CC2:** as RT-7. The single-job searches on RT-8 end with exp 7-31, so the pins are boxed.
- **BT_SYS_CFG:** U1-31 has no first step (exp 0). The BT_RST_N F.Cu run along y 24.95 passes 0.34 mm above the pad. Remedy: move that run 0.6 mm north.
- **BT_RST_M:** 4M nodes without a path.
- **3V_AO R241:** two legs tried. Leg 1 exhausted 6M nodes; leg 2's start point is not routable (exp 0). The In2 VBUS/USB_VBUS islands wall x 135-153 from y 27 to 130. Proposal in schematic-patch.md P2: a dedicated B.Cu lane at y 56-58 under the codec (PWR_3V is exempt from BKO_CODEC).

## 5. Quality notes (new copper)
- **Angles:** all 376 new segments are exact 0/45/90. The touched nets show 98.3 % exact length, which is inherited copper of REGN, HP_G1 and others; none of it is new.
- **Via count is high on the slow nets:**

  | net | vias |
  |---|---|
  | CTRL_SDA | 12 |
  | BT_MFB | 11 |
  | PD_PLUG_EVENT | 10 |
  | BT_RST_N | 9 |
  | AUD_SCL | 9 |
  | BT_FORCE_PWM | 8 |
  | AMP_BOOST_EN | 8 |

  These are the price of the three-layer escape.
- **ADC_INT:** 35.6 mm against the 1.5× + 1 = 34.1 mm sense limit. It is an interrupt line; only accept.py's regex marks it as sense. Remedy: shorten its U3 stub (via (137.725, 77.3)) during the BT_AUDIO_L re-route.
- **B.Cu reference (r7):**
  - B.Cu over In2 void rose 171 → 269 mm, because slow In2 runs under U3 cut the In2 GND.
  - Sensitive B.Cu over void: AUD_SDA 1.4 → 3.1 mm, AUD_SCL 3.5 → 3.4 mm, and **BT_AUDIO_R 2.6 → 3.9 mm**. BT_AUDIO_R is a foreign audio net, so this is a regression caused by new In2 crossings near (124-134, 59-63).
  - Fix with the N-side remedy (3.3 a).
- **parcheck, non-sensitive pairs < 0.4 mm over > 3 mm:**

  | pair | layer | length | gap |
  |---|---|---|---|
  | CHG_QON_SENSE / PD_PLUG_EVENT | In2 | 8.1 mm | 0.386 |
  | AMP_BOOST_EN / HP_SEL_A | In2 | 7.3 mm | 0.325 |
  | SWCLK / SWDIO | B | 6.7 mm | 0.215 |
  | GAUGE_ISO_N / ENC_B | B | 6.3 mm | 0.265 |
  | HP_G1 / SWCLK | F | 5.2 mm | 0.265 |
  | BT_RST_N / BT_UART_RX (inherited) | B | 4.35 mm | 0.25 |
  | SWDIO / PD_PLUG_EVENT | F | 3.8 mm | |
  | BT_UART_RX / BT_UART_TX | F | 3.45 mm | |
  | BT_RST_N / BT_TX_IND | B | 3.3 mm | |

  All are slow control or debug nets.
- **Hygiene (route_oct_check, touched nets):**
  - T-junctions 6 (cut-end joins);
  - bend spacing < max(0.4, 3w) 22;
  - pad exits < 0.3 mm 8 (fine-pitch pins and the manual fans);
  - micro segments 13 (5 inside pads).

  DRC reports no dangling copper.
- **Teardrops:** edit.py removed the teardrop zones next to edited copper (listed per build in `t/editlog.md`). Regenerating them is a GUI step for the owner, as in RT-7.

## 6. Remaining open connections (56)

| group | conns | nets | cause / remedy |
|---|---|---|---|
| U3 long nets | 13 | AMP_FAULT_N ×4, HP_G0 ×2, HP_SEL_B ×2, HP_EN, AUX_DET, CHG_ENABLE, CHG_SYS_ENABLE, AMP_PDN (R258) | 3.1: pin vias boxed or search exhausted. Needs the N-corridor relief (3.3 a/b) and the R262 / R111 / mux re-place. |
| U3 north escape | 4 | PDCTRL_SCL ×2 (U3-43 ↔ U11 group, R15-2), PDCTRL_SDA, NRST (J7-3) | 3.3 |
| U4 charger | 5 | CHG_INT (**accepted**, schematic-patch P1), CTRL_SCL, QON, ILIM_HIZ, Q101-G (Q102-3) | 4.1 |
| I2S / AUD I2C / amp control | 5 | I2S_BCK ×2, AUD_SDA ×2 (U24, U7), U7-PDN | 4.2, 4.3 |
| U24 inputs / USB audio | 9 | C204/C205/C233-Pad2, C235-Pad2 ×2, USB_AUDIO_L, USB_AUDIO_R ×2, U2-VOUTL | 4.4 |
| headphone mux | 8 | U8-COM1/COM2/NC1/NC2, HP_L, HP_OUTL, AUX_L, HP_SEL_A (U8-1 ↔ U8-5) | 4.4 |
| USB-C / PD / regulators / gauge | 9 | U11-ADC4, R18, PD_SINK_EN (U11-19), USB_CC1, USB_CC2, U14-FB, 5V_LOGIC_EN (R142), U12-EN, GAUGE_ISO_N | 4.6 |
| BT / debug | 2 | BT_RST_M, BT_SYS_CFG | 4.6 |
| power | 1 | 3V_AO to R241 | 4.6, schematic-patch P2 |

## 7. Part moves and records
| ref | old | new | reason |
|---|---|---|---|
| R110 | (176.59, 108.82) rot 90 | (176.59, 108.82) rot 270 | swap pads so Q101-G reaches Q101-1 below the AUD_SCL detour (4.1) |

No decoupling capacitor moved. Before fab, regenerate:
- the position/CPL file for R110;
- teardrops near the edits;
- Gerber/drill;
- the board STEP.

## 8. Edit log
The full table is in `ai-files/pcb/work-route8/t/editlog.md`, generated by `scripts/editlog.py` from the edit reports. It lists every deleted, changed and added segment, arc and via, with net, layer, width and coordinates, plus the footprint move and the removed teardrops per build.

Build chain:
1. RT-7 → **K0**: rip, `t/rip1.json`.
2. → **KF**: plan `t/planF3.json`. This is phase A (v4 minus re-routed jobs, plus the manual escapes and the E/W/N fix logs), the R110/REGN/Q101-G plan `t/planQ2.json`, phase B (`t/pQ6_2snap.json`, AMP_BOOST_EN `t/PL_3`, PD_SINK_EN and J4 `t/pWa`), and the GND via nudge (135.30, 83.597) → (135.31, 83.607). The nudge clears the AMP_PDN neck clearance: it was 0.1993 mm and is now ≥ 0.2.
3. → **KG1**: prune2.
4. → **KG2**: manual via and stub cleanup.
5. → **KG3-KG6**: dead stub chains.
6. → **KG7**: 0° reversals.
7. → **RT-8**: silk_tile.

## 9. Files (`ai-files/pcb/work-route8/`)
- **Result:** `RT-8.kicad_pcb/.kicad_pro/.kicad_dru` (pro and dru byte-identical to RT-7).
- **Gate files:** `RT-8.drc.json`, `RT-8.gates.json`, `t/RT-8.gates.txt`, `RT-8.check.json/.txt`, `RT-8.r7.json/.txt`, `RT-8.par.json/.txt`, `RT-8.rulehash.txt`, `RT-8.silkgate.json`, `t/RT-8.ha8.json`, `t/RT-8.cp.json`, and the sentinel in `sentinel/`.
- **Evidence:** `evidence/rt8-F.png`, `evidence/rt8-B.png` (+ .svg); crops `evidence/u3-F.png`, `evidence/u3-B-In2.png`, `evidence/q101.png`.
- **Schematic proposal for the coordinator:** `schematic-patch.md` (P1 CHG_INT, P2 3V_AO R241, P3 placement items).
- **Scripts:**
  - unchanged RT-7 tools: `edit.py` (+ arc_del), `gates4.py` (+ arc_del), `editlog.py` (+ arcs), `cycle.sh`, `gates8.sh` (RT-7 baseline);
  - new: `ripwin.py`, `hr8.py`, `jobs_u3*.py`, `fix8.py`, `jobs_B.py`, `par8.sh`, `mergepar.py`, `planplus.py`, `planminus.py`, `compose2.sh`, `prune2.py`, `final8.sh`, `silk_tile8.py`.
  - `prune.py` was superseded by `prune2.py` (see section 2).
- **Size:** the work folder is about 0.7 GB of intermediate boards (K*, KA*, KF*, KG*, KP*, Kv*, KW*) and geo exports; do not commit them.

## 10. Requested coordinator decisions
1. Apply schematic-patch P1 (CHG_INT not required, firmware polls the charger) or order a BAT_INT re-plan.
2. Allow re-routing the foreign BT_AUDIO_L north of U3 (3.3 a). This would restore both PDCTRL lines and the J7 NRST, and should open pins 36/38/42/47 for CHG_ENABLE, CHG_SYS_ENABLE and HP_EN.
3. C215-C212: keep the VINR1 closure (current) or give it back for the 0.4 mm tweezers gap.
4. I2S BCK: allow the VBUS_PD_IN2 cut (4.2).
