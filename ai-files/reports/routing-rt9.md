# RT-9: PD I2C restore and remaining groups (2026-11-02)

Agent "RT-9 restore PD I2C and close remaining".
- **Input:** `ai-files/pcb/work-route8/RT-8.*` (227/283 connections, DRC 0, 56 unconnected).
- **Work folder:** `ai-files/pcb/work-route9/` only.
- **Result:** `ai-files/pcb/work-route9/RT-9.kicad_pcb/.kicad_pro/.kicad_dru`.
- **Untouched:** nothing in `DesktopSpeaker-kicad/`, the earlier work folders or `helpers/route_oct*.py` was edited.
- **Method:** all board edits are text edits (`scripts/edit.py`). Every build was refilled in a separate pcbnew process with the pristine `.kicad_pro`/`.kicad_dru` beside the board (`scripts/cycle.sh`).
- **Not done:** not committed, nothing published.

**Bottom line.**
- Unconnected went from **56 to 53**, with **DRC 0**, **no connection lost**, **no part moved** and the rule files identical to RT-8.
- **Closed:**
  - PDCTRL_SCL ×2: U3-43 to the U11/J4 group, and R15-2;
  - BT_SYS_CFG: U1-31 to J8-2.
- **Not closed:**
  - **PDCTRL_SDA (U3-44)** and **NRST to J7-3**. Both have a verified cause and a minimal proposal in `work-route9/schematic-patch.md` (P4, P5).
  - C215-C212 (task 3), I2S BCK (task 4) and most of task 6: analysed but not changed (sections 4-6).
- No release-todo file was written: 52 open connections that are not accepted remain.

## 1. Gates (all independent of the editing tools; `t/RT-9.gates.txt`)

| gate | RT-8 | RT-9 |
|---|---|---|
| kicad-cli DRC `--severity-all --all-track-errors` (project library) | 0 | **0** |
| DRC unconnected | 56 | **53** (CHG_INT accepted) |
| closed / lost vs RT-8 (per-net diff) | | PDCTRL_SCL 2→0, BT_SYS_CFG 1→0; **lost: none** |
| footprints moved / pad nets of 360 footprints (1194 pads) | | **none moved**; `pad_net_diff []` |
| rule files | dru ce43baa1…, pro aa88e8c9… | **byte-identical** (no exemption); sentinel **FIRES** (81) |
| locked copper | | 3336 of 3406 RT-8 items untouched, 70 removed or changed (all in the edit reports), 0 unexpected. SHA-256 `02b282fc75ac229b871f7a0b9faf8ef3114559eefa0289c17bce1c39f98a5234` |
| new copper exact 0/45/90 (gates4) | | **74 segments, 145.2 mm, 0 not exact**. Vias: 13 added, 14 removed |
| route_oct_check (11 touched nets) | | exact 100 %, joints < 90° 0, length ratio median 1.37, p95 2.02 (section 3) |
| r7 B.Cu over In2 void | 269.2 mm | **267.7 mm** (≤ 269; the 200 mm target is not reached) |
| r7 sensitive B.Cu over void | | unchanged, except **BT_AUDIO_R 3.9 → 4.3 mm** (section 3) |
| r7 joints < 80° / < 30° | 19 / 7 | **19 / 7** |
| r7 BM83 F.Cu inside module | GND 2.3, SYS_PWR 2.0 | **unchanged** (BM83 keep-out 0 mm new copper) |
| parcheck sensitive pairs / sensitive vias > 1.5 mm from GND | 0 / 0 | **0 / 0** |
| pour check (route_oct_pourcheck) | | **OK** (foreign unconnected 51 → 51) |
| HA8 failing pairs | 122 | **122** (no new pair, none tighter) |
| BAT_INT U4-22/23 → Q103 (6 A) | 2.889 mΩ | **2.889 mΩ** (104.0 mW) |
| silkscreen | | no part moved, so silk_tile was not run; RT-8 silk is unchanged |

## 2. Edits, task by task

The coordinates are in mm. The full per-item table (uuid, net, layer, width, both end points) is `work-route9/t/editlog.md`.

### 2.1 Task 2: north escape (PDCTRL, NRST)

**Option chosen: neither moving BT_AUDIO_L nor moving U3.** Measurement showed that BT_AUDIO_L is not what blocks pins 43/44:
- A y ≈ 62.5 path east of x 128.8 would run into the CHG_QON_SENSE via (129.6, 62.48), the PD_PLUG_EVENT via (128.9, 61.73), the BT_AUDIO_R via (133.63, 62.57) and the LDO_3V3 R15-1 → TP5 link.
- The straight diagonal would cross the TP5 pad.

The real limits are:
- the In2 5V_LOGIC trunk (w 2.0 / 1.0 / 0.4), which leaves no via site within about 1.2 mm of pins 40-48;
- the SWDIO/SWCLK fan around the J7 NPTH holes.

Moving U3 together with its decoupling parts would mean re-escaping about 50 routed pins. The lower-risk option was therefore to redesign the corridor in place, leaving BT_AUDIO_L and U3 where they are.

| build | edit |
|---|---|
| K1 | **PDCTRL_SCL dead loop removed**: F (122.2, 58.2)-(119.9, 58.2), B (119.9, 58.2)…(115.35, 60.55), F (115.35, 60.55)-(115.35, 61.75), In2 (115.35, 61.75)-(118.9, 58.2), and vias (119.9, 58.2), (115.35, 60.55), (115.35, 61.75). The In2 trunk now starts at the existing via (122.2, 58.2). About 13 mm and 3 vias saved; J4 ↔ U11 stays connected. |
| K1 | **R15-2 tie**: F 0.3 (131.97, 60.652)-(130.3, 60.652), via 0.6/0.3 (130.3, 60.652), In2 0.3 (130.3, 60.652)-(130.3, 57.0) onto the trunk diagonal. Closes R15-2. |
| K1 | SWDIO J6 via moved from (126.715, 69.045) to (126.2975, 68.6275), and its F stub removed (later superseded). |
| K2-K4 | Corridor ripped (U3 side only, far copper kept): CODEC_PWR_EN (pin 39 → via 128.2, 61.025), BT_PWR_EN (pin 36 → via 127.35, 58.575), CHG_QON_SENSE (via 131.05, 68.725 → vias at x 129.6), PD_PLUG_EVENT north branch, SWDIO/SWCLK pin escapes and J7 branches. 50 segments and 8 vias. |
| K5 | **Routed (hr8, order S-D-w-K-b-c-Q-P, exit lanes 2.6 mm):** see the routes table below. |
| K5 | Manual: SWCLK J7 branch straight down the 0.8 mm gap between the J7 holes. B (122.95, 65.525)-(123.05, 65.625)-(123.05, 67.425)-(123.75, 68.125); this replaces RT-8's 9 mm detour east of the hole. R160 branch: F (123.2475, 69.75)-(124.311, 68.686). SWDIO J7 branch: F (123.35, 64.975)-(125.3, 64.975)-(126.25, 65.925)-(126.25, 68.975)-(126.1, 69.125). |
| K5 | **BT_SYS_CFG** (task 6): BT_RST_N run moved 0.59 mm north. F (99.8975, 24.36)-(110.465, 24.36)-(110.675, 24.15) replaces the y 24.95 run and its jog, opening U1-31. Then hr8 routed J8-2 → U1-31, 40.3 mm, 2 vias. |
| K6/K7 | Cleanup: SWCLK via (123.4, 69.625) and QON via (129.6, 61.225), both connected on one layer only, removed. PD_PLUG_EVENT In2 ends at the existing via (128.9, 61.725), so the via (128.9, 58.575) and one In2 crossing under BT_AUDIO_R are removed. |
| K8 | Overlapping SWDIO pin stub removed (a 0° joint in r7). BT_SYS_CFG B run re-spaced around the 3V8_BT vias, x 112.6 / 112.8925 / 112.155. The 0.24 mm gaps to BT_RXD_M and BT_TXD_M became ≥ 0.40 mm, or < 3 mm long. |

Routes found by hr8 in K5:

| net | route | length | vias |
|---|---|---|---|
| PDCTRL_SCL | F (126.75, 70.825)-(126.75, 67.825)-(128.75, 65.825), via, B -(130.3, 64.275)-(130.3, 60.875) into the R15-2 tie via | 11.4 mm | 1 |
| SWDIO pin | F to via (126.1, 69.125), then B to the J6 run | 6.1 mm | 1 |
| SWCLK pin / J6 | F to via (123.75, 68.125), then B -(125.3, 69.675)-(126.5, 69.675)-(129.0, 72.175) | 10.3 mm | 1 |
| BT_PWR_EN | B and In2 | 13.4 mm | 2 new (RT-8 used 3 fine vias) |
| CODEC_PWR_EN | In2 x 128.2 → F | 10.5 mm | 1 new (RT-8: 1) |
| CHG_QON_SENSE | B, west of the corridor | 13.9 mm | 0 new; −2 vias vs RT-8 |
| PD_PLUG_EVENT | F, In2 x 129.45/128.9 | 14.5 mm | 2 new |

Not closed:
- **PDCTRL_SDA**: P4 pin swap, verified route.
- **NRST J7-3**: P5.

The causes are in `schematic-patch.md`.

**Iterations (AG13, 3 used):**
1. RT-8-state board K1, 2 orders: both PDCTRL fail (pins boxed).
2. K2/K3 rips, 24 + 24 orders: SDA, SWDIO J7 and BT_PWR_EN always fail.
3. K4 rip of the SWD escapes:
   - 40 random orders, best 8/11;
   - then 24 lane-length variants: `SDwKbcQP` with exit lanes 2.6 mm routes everything except SDA. This one was chosen.
   - Follow-ups on the final board: NRST 3 runs, SDA 3 runs, SDA pin probes on pins 33/34/35/37/40/41.

The logs are `t/jN*_*.log`, `t/jN[123].log`, `t/jD[123].log` and `t/jSDA*.log`.

### 2.2 Task 3: C215-C212 (0.14 mm), not changed
The courtyards of these two 0402s must be 0.4 mm apart; they share only GND. Every move fails a hard rule:
- **C212 east:** VINR1 runs at x 152.745 with 0.21 mm to the C212 pad. It cannot turn earlier without crossing VINL1 (pin 3).
- **C212 north** (≥ 2.4 mm for courtyard separation in y): runs into the AVDD feed F (153.15, 75.9)-(152.45, 78.3) and its via.
- **C215 west:** XO leaves pin 9 at x 150.245, 0.37 mm from the C215 pad. Narrowing XO to 0.2 mm and VINR1 to 0.2 mm (allowed in NECK_U24) gives a total of 0.415 mm. But C215 would then approach Y200 (already 0.32, failing) and the U24 courtyard (0.138), which would make those pairs tighter. That breaks the HA8 "none tighter" gate.
- **Moving the crystal group 1-4 mm:** does not help, because XO must still leave pin 9 beside C215. C215 would have to move about 2.7 mm north, which breaks the 3 mm AVDD decoupling rule.

**Recommendation:** accept this pair as a documented hand-assembly item (place C215 and C212 first, before U24 and Y200), or change the U24 decoupling footprints (0201 VREF cap) at schematic level.

### 2.3 Task 4: I2S BCK, not attempted (budget)
The RT-8 analysis stands: four crossings of LRCK/SDATA, and the hub column is VBUS_PD on In2.

The geometry for the next run:
- TP12 (146.35, 95.4) is boxed by LRCK x 142.895 on the west, TP14 at y 97.6-99.4 on the south, and SDATA x 148.55 on the east.
- The U6 fan lane x + y = 232.19 is reserved.

No In2 island was reshaped in RT-9.

### 2.4 Task 5: quality
| item | RT-8 | RT-9 | note |
|---|---|---|---|
| B.Cu over In2 void (all) | 269.2 mm | 267.7 mm | −1.5 mm, from the corridor rip (QON on B instead of In2). Not ≤ 200 mm: most of the void length is outside the touched area. |
| BT_AUDIO_R B.Cu over void | 3.9 mm | 4.3 mm | **regression.** The SCL tie In2 x 130.3 crosses under BT_AUDIO_R's B.Cu y 59.565. It is the only crossing left: B.Cu is closed by the HP_DET and BT_AUDIO_R B diagonals, and F.Cu by the QON F x 129.6 and HP_DET B x 130.675 pair, with no via site. The PD_PLUG_EVENT crossing was removed in K7 to compensate in part. |
| slow parallel pairs < 0.4 mm over > 3 mm (touched nets) | 9 listed | 6 | 5 are inherited RT-8 copper: QON/PD_PLUG In2 under U3, SWCLK/SWDIO J6 B under U3, HP_G1/SWCLK, BT_RST_N/BT_UART_RX, BT_RST_N/BT_TX_IND. 1 is changed: SWDIO/PD_PLUG F 3.79 mm. The two new BT_SYS_CFG pairs were removed in K8. |
| via count on corridor nets | BT_PWR_EN 3 fine + 1 | 2 + 1 | QON −2, PD_PLUG −1 |
| ADC_INT 35.6 / 34.1 mm | | unchanged | Shortening needs TP26 (GND PTH, 141.0, 90.9) moved about 2 mm south to drop the y 92.7 detour. TP26's PTH would then cut the In2 VBUS_PD island, so it was not done. |

### 2.5 Task 6: remaining groups
- Closed: **BT_SYS_CFG** (above).
- U14-FB was analysed. R140-2 is fenced on all sides:
  - the L2 switch track is within 1.0 mm (switch_sensitive);
  - the B.Cu 5V_LOGIC trunk lies on the west;
  - C142 lies on the south.
  - RT-8's plan (FB via at (98.47, 105.3) after moving R140 1.8 mm east) overlaps the C142-2 pad (y 105.33).
  - Not done.
- The other groups are unchanged from RT-8 section 6.

## 3. Length report (route_oct_check, 11 touched nets, 9 complete)
- Median ratio 1.37, p95 2.02, max 2.02. All 731.4 mm of the touched nets is exactly on the 0/45/90 grid.
- Ratios above 1.4, all slow control lines and all within 3.5×:

  | net | ratio | why |
  |---|---|---|
  | PDCTRL_SCL | 1.86 | J4 + U11 + R15 tree |
  | CODEC_PWR_EN | 1.79 | inherited north run |
  | PD_PLUG_EVENT | 2.02 | three branches |
  | BT_SYS_CFG | 1.57 | around the BM83 east side |

- Hygiene on the touched nets:
  - T-junctions 2;
  - bend spacing < max(0.4, 3w) 12 (pin fans);
  - pad exits < 0.3 mm 1;
  - micro-segments 3 (2 inside pads).

  DRC reports no dangling copper.
- Teardrops: edit.py removed 1 teardrop zone next to edited copper (K5). Regenerating it is a GUI step.

## 4. Remaining open connections (53)
| group | conns | cause / proposal |
|---|---|---|
| CHG_INT | 1 | **accepted unrouted** (P1) |
| PDCTRL_SDA U3-44 | 1 | corridor capacity; **P4** pin swap to PB13 (route verified, 14.8 mm) |
| NRST J7-3 | 1 | closed pocket; **P5** J7-3 no-connect (NRST stays on J6) |
| U3 long nets | 13 | as RT-8 3.1 |
| U4 charger | 4 | CTRL_SCL, QON, ILIM_HIZ, Q101-G (RT-8 4.1) |
| I2S / AUD I2C / amp control | 5 | RT-8 4.2/4.3; section 2.3 |
| U24 inputs / USB audio | 9 | RT-8 4.4 |
| headphone mux | 8 | RT-8 4.4 |
| USB-C / PD / regulators / gauge | 9 | RT-8 4.6; U14-FB section 2.5 |
| BT / debug | 1 | BT_RST_M (RT-8: 4 M nodes without a path) |
| power | 1 | 3V_AO to R241 (P2) |

## 5. Files (`ai-files/pcb/work-route9/`)
- **Result:** `RT-9.kicad_pcb/.kicad_pro/.kicad_dru`.
  - Build chain: RT-8 → K1 → K2 → K3 → K4 → K5 → K6 → K7 → K8 = RT-9.
  - Plans: `t/p1.json`, `t/rip2.json`, `t/rip3.json`, `t/rip4.json`, `t/p5.json` (merged from `t/pN_4SDwKbcQP_2.6.json`, `t/pSWD.json`, `t/pBT.json`, `t/pSYS.json`), `t/p6.json`, `t/p7.json`, `t/p8.json`.
- **Gate files:**
  - `t/RT-9.gates.txt`, `RT-9.drc.json`, `RT-9.gates.json`;
  - `RT-9.check.json/.txt`, `RT-9.r7.json/.txt`, `RT-9.par.json/.txt`;
  - `RT-9.rulehash.txt`, `t/RT-9.ha8.json`, `t/RT-9.cp.json`;
  - `sentinel/RT-9_sentinel.*`.
- **Edit log:** `t/editlog.md`.
- **Evidence:** `evidence/rt9-F.png`, `evidence/rt9-B.png`, `evidence/rt9-north.png` (corridor), `evidence/rt9-syscfg.png`.
- **Proposals:** `schematic-patch.md` (P4, P5).
- **New scripts:** `scripts/freemap.py` (free-space map per layer), `scripts/fu.py` (uuid lookup), `scripts/mkN.py` (corridor jobs), `scripts/gates9.sh` (gates8 rebased on RT-8).
- **Size:** intermediate boards K*/KB are about 0.25 GB; do not commit them.
