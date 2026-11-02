# RT-12: U3 nets, USB-C/PD/gauge locals, R262/R258 moves, B-over-void repair (2026-11-03)

Agent "RT-12 U3 nets, BCK, USB-PD and finish".
- **Input:** `ai-files/pcb/work-route11/RT-11.*` (DRC 0, 37 unconnected).
- **Work folder:** `ai-files/pcb/work-route12/` only. Nothing in `DesktopSpeaker-kicad/`, earlier work folders or `helpers/route_oct*.py` was edited. Nothing committed or published.
- **Result:** `ai-files/pcb/work-route12/RT-12.kicad_pcb` / `.kicad_pro` / `.kicad_dru`.
- **Method:** text-level edits (`scripts/edit.py` + `scripts/merge12.py` / `resolve.py`). Every build was refilled in a separate pcbnew process with the pristine `base.kicad_pro` + `RT-12.kicad_dru` beside it (`scripts/cycle12.sh`). Router `scripts/hr12.py` = hr11 with one change: it reads `RT-12.kicad_dru` (plus an optional rule-22 list, unused in the result).
- **Not reached:** 0 unconnected. So **no release material** was written (`proposed-project.kicad_dru`, `release-todo-2026-11-02.md`). Section 5 is the connection-by-connection to-do list instead.

## Bottom line

- Unconnected (kicad-cli DRC) **37 -> 26**: 11 closures, **no connection lost** (per-net counts: no net increased). DRC **0 violations**.
- Closed:
  - AMP_FAULT_N (U6-9 to R262)
  - GAUGE_ISO_N
  - HP_G0 (U3-16 to R237/U10)
  - HP_OUTL
  - PD_SINK_EN
  - R18 (U11-36)
  - U11-ADC4
  - U12-EN
  - U14-FB (R140-2)
  - U2-VOUTL
  - U7-PDN (R258-2 to U7-17)
- **Bookkeeping correction:** CHG_INT has no pads on the board since patch P1, so it is not in any DRC count. RT-11's "37 = 36 + CHG_INT" was wrong: all 37 were real, and all 26 now open are real.
- **Rule file:** RT-12.kicad_dru = RT-11 byte-identical (SHA-256 c47d6aed...); `.kicad_pro` unchanged (aa88e8c9...). No rule-21 extension was needed:
  - every In2 use is by rule-11 / rule-21 nets: PDCTRL_SDA, BT_FORCE_PWM, BT_RST_N, PD_SINK_EN, GAUGE_ISO_N, HP_G0;
  - a rule-22 draft (Net-(U11-FAULT)) was written and then withdrawn, because the final U11-FAULT route is F/B only.
- **B.Cu over In2 void: 268.7 -> 264.7 mm.** The gate (<= 269) is met; the target (<= 200) is not.
- **Still missed (honest):**
  - HP_R ratio (1.83) and ADC_INT 35.6 mm: unchanged.
  - The 20 cosmetic RT-11 route ends are not merged. Total dangling stays 63, with none new from RT-12.
  - Tasks 3 (BCK / AUD_SDA) and most of 5 were analysed, not executed (section 4).

## 1. Parts moved (task 1; both within the 6 mm allowance; HA8 checked)

| ref | RT-11 (x, y, rot) | RT-12 (x, y, rot) | moved | why |
|---|---|---|---|---|
| R262 | (116.000, 127.340, 90) | (111.505, 124.350, -90) | 5.40 mm | Its pocket was sealed (PVDD vias, C281/C282 GND via, L201). The new spot is the free area above U6 pins 9-11: pin 2 drops straight into U6-9, and pin 1 joins 3V3_AUDIO at C280-1 (F w0.4 at y 123.75). The old R262-1 3V3 stub was removed. |
| R258 | (183.200, 108.400, -90) | (185.600, 113.600, -90) | 5.73 mm | It left the I2S/AUD_SCL pocket for the free F area west of the AUD_SCL diagonal. U7-PDN runs on F to U7-17 (west pin column, clear of C296/GVDD), 15.0 mm, ratio 1.02. |

No other footprint moved: `gates4`, moved_not_allowed [].

**HA8:** 122 -> **121**. The L201-R262 pair (0.784 mm) is gone; no new pair, none tighter.

**Silk:** `scripts/silk_tile12.py` is identical to RT-11's `silk_tile11.py` (no data change). `silk_tile_gate` G1-G6 all PASS (`t/RT-12.silkgate.json`).

## 2. Edits (build chain RT-11 -> B1 -> B2 -> B3 -> B4 -> V1 -> C1 -> H1 -> F1 -> RT-12)

Edit reports: `t/<stem>.edit.json`. Plans: `t/b1`, `t/b2`, `t/b3`, `t/b4`, `t/v1`, `t/c1`, `t/b5`, `t/f1` (each `base.py` documents its edits).

**B1: USB-C/PD and gauge locals (task 4).**
- **PDCTRL_SDA**
  - The redundant second SDA branch was removed: R14 via (134.32, 57.50) -> B x 134.32/135.22 -> via (134.57, 48.65) -> F -> J4-3 formed a loop with the B trunk at x 133.6. The R14 via was re-linked to the trunk by a 0.42 mm B stub.
  - The U11-8 escape now goes straight down to a fine via (135.5, 58.75), then B to the trunk and In2 south (rule-11 net).
- **PD_PLUG_EVENT:** the pin-37 loop over pin 36 was replaced by a fine via (135.2, 52.9) plus B.
- **R18:** hand F route U11-36 -> R18-1, 7.0 mm, ratio 1.19.
- **U11-ADC4:** router, B hop under the LDO_3V3 wall.
- **PD_SINK_EN:** router, F + B around R17.
- **U11-FAULT:** its B detour was ripped and re-routed by hand: F, fine via, B x 139.1 west of PD_PLUG_EVENT, F into R13-2.
- **GAUGE_ISO_N:**
  - The In2 SYS_RAW trunk (w 2.0, x ~94.2) lies under U17-4, so the escape via sits west of it at (92.6, 84.71).
  - U17-NC was re-routed from the U17-4 pocket wall to a via at U17-1, then B to its U5 side.
- **U14-FB:** router, R140-2 -> FB stub (B y 103.02).
- **HP_OUTL:** router, 45.8 mm whole net, ratio 1.07, 4 vias with GND stitches. B only over In2 GND (BKO_MUX notch used).

**B2: U2-VOUTL and U12-EN.**
- **U2-VOUTL** (audio, F only inside BKO_CODEC):
  - The C178-1 -> Y170-3 XTO link was lowered 0.227 mm inside both pads, which opens a 0.5 mm audio lane under C173-2.
  - The VCCP2I via stub was shortened inside C173-1.
  - VOUTL: 6.3 mm, ratio 1.47 (audio limit 1.5 x + 1 mm met).
- **U12-EN:** router from the U12 via, F/B, 24 mm.

**B3: R262 move**, plus AMP_FAULT_N U6-9 link.

**B4: R258 move**, plus U7-PDN route.

**V1: B-over-void repair (task 6).** Via-to-via B runs of slow rule-11/21 nets that lay over In2 void were found with `scripts/bchains.py` and re-routed on F/In2:
- BT_FORCE_PWM (In2);
- BT_RST_N (F + In2);
- GAUGE_ISO_N (In2);
- BT_TX_IND: U3-62 detour (F west, In2 loop, B chain) replaced by 10.2 mm F under the U3 body (LQFP, no exposed pad, as in RT-10);
- PD_SINK_EN: U3-63 F/B/F/B loop south of U3 replaced by F + In2;
- U11-ADC4 re-routed with a high void cost.

Failed and left unchanged: BT_MFB, ENC_B, BT_PWR_EN, PD_PLUG_EVENT (In2 crowded), and U12-EN (F/In2).

**C1: clean-up of RT-12's own ends.**
- 7 route ends snapped onto centre lines or pad centres.
- HP_OUTL now ends on its via from the north.
- The U12-EN 45-degree joint at the U12 via was removed: the C122-1 link became vertical + horizontal.

**H1: HP_G0.** Router, 86.7 mm whole net, ratio 1.17, 9 vias, F/B/In2 (rule-21 net). A router In2 spiral at (137, 71.5) was replaced by a 2-segment link, and the U3-16 entry was squared off.

**F1: final snaps.**
- In2 conversion ends snapped onto via centres.
- The HP_G0 start at R237-1 now joins the RT-11 U10-6 stub at 90 degrees.

**RT-12 = F1 + silk tiling.**

**New copper:** 141 segments, 290.9 mm, **0 not exact 0/45/90** (`gates4`). All new vias are 0.6/0.3, or 0.5/0.2 inside neck areas. The router rejects via lands within 0.06 mm of any pad. Hand vias were checked by DRC and the hole-to-pad review in the plans.

## 3. Gates (independent of the editing tools; `t/RT-12.gates.txt`)

| gate | RT-11 | RT-12 |
|---|---|---|
| kicad-cli DRC (project library, RT-12 = RT-11 rules) | 0 / 37 unconnected | **0 / 26** |
| connections lost | - | **none** (per-net: only decreases) |
| footprints / pad nets (360 fp, 1194 pads) | - | R262, R258 moved only / **pad_net_diff []** |
| locked copper | - | 3424 of 3505 RT-11 items untouched; 81 removed/changed, all in the edit reports (0 unexpected). SHA-256 `a5f7dab1b39e575e96347d0b0e42cad2f030836b79ad05ce6e4c5c5d39eecab2` (`t/RT-12.gates.json`) |
| new copper exact 0/45/90 | - | 141 seg, 290.9 mm, 0 not exact |
| route_oct_check | joints < 90: 0, dangling 63, T 14, bend-short 34 | joints < 90: **0**, dangling **63** (no new), T 21, bend-short 43, pad-exit-short 14, exact 100 % |
| r7 B.Cu over In2 void | 268.7 | **264.7** (gate <= 269 met; target 200 not met) |
| r7 sensitive B over void | HP_OUTL 1.9, AUD_SDA 3.1 | HP_OUTL 3.6 (via antipads of the new run), AUD_SDA 3.5; others unchanged |
| r7 BM83 F.Cu in module | GND 2.3, SYS_PWR 2.0 | unchanged; antenna keep-out DRC 0 |
| parcheck (sensitive / slow pairs) | 1 / 8 | **1 / 7** |
| pour check | OK | OK. No non-GND island changed: VBUS_PD, SYS_RAW, BAT_PACK, BAT_INT and PVDD counts and areas are equal. |
| GND islands | | GND_IN2_BG 51 -> 54 and GND_BCU 5 -> 6 (`scripts/islanddiff.py`). Each new piece holds 1-3 GND vias (largest new: 22 mm2 at (137.6, 73.3)). No floating copper. |
| HA8 | 122 | **121** (0 new, 0 tighter) |
| BAT_INT 6 A | 17.3 mV / 104.0 mW | **unchanged** |
| route_oct sentinel / rule-21 sentinel | fires | **fires (81)** / **PASS** (`scripts/sentinel21_12.sh`) |
| silk_tile_gate | | **ALL PASS** |

**Length report (route_oct_check; whole net; ratio = length / octilinear minimum):**

| net | mm | ratio | vias | note |
|---|---|---|---|---|
| R18 (U11-36) | 7.0 | 1.19 | 0 | |
| U11-ADC4 | 9.8 | 2.22 | 2 | analogue strap; B hop under the LDO_3V3 wall |
| U11-FAULT | 8.2 | 2.89 | 2 | |
| PD_SINK_EN | 37.1 | 1.27 | 6 | |
| GAUGE_ISO_N | 42.5 | 1.61 | 4 | |
| U17-NC | 12.9 | 1.05 | 2 | |
| U14-FB | 18.9 | 2.33 | 4 | feedback: R140 link 6 mm, B y 103.0 south of U14 |
| HP_OUTL | 45.8 | 1.07 | 5 | |
| U2-VOUTL | 6.3 | 1.47 | 0 | audio, within 1.5 x + 1 mm |
| U12-EN | 31.0 | 1.30 | 4 | |
| U7-PDN | 15.0 | 1.02 | 0 | |
| HP_G0 | 86.7 | 1.17 | 9 | |
| BT_TX_IND / BT_RST_N / BT_FORCE_PWM | 81.9 / 86.8 / 62.8 | 1.23 / 1.40 / 1.35 | 4 / 10 / 8 | |
| HP_R | 13.7 | 1.83 | 2 | unchanged |
| ADC_INT | 35.6 | 1.61 | 2 | unchanged |

**B-over-void per net** (`scripts/voidnet.py RT-11 RT-12`):
- Up (RT-12 new copper):
  - HP_G0 +7.8, U12-EN +4.8, U17-NC +2.3, HP_OUTL +1.7, ADC4 +1.6, U14-FB +0.9, U11-FAULT +0.8;
  - side effects of new In2 copper under existing B runs: 5V_LOGIC_EN +0.8, AUD_SDA +0.4, HP_SEL_A +0.4.
- Down (repairs): BT_RST_N -7.1, BT_TX_IND -6.4, BT_FORCE_PWM -5.7, PD_SINK_EN -4.3, BT_MFB -0.9, PDCTRL_SDA -0.7, GAUGE_ALRT_N -0.4.

## 4. AG13 iteration log (max 3 per task group)

**Task 4 (USB-C/PD/gauge), 3 iterations.**
1. B1a: GAUGE escape via landed on In2 SYS_RAW (short). Re-planned west of the trunk, with U17-NC moved to B.
2. B1b: the U17-NC via was left dangling. The redundant B stub was removed: DRC 0, 6 closures.
3. B2: 5V_LOGIC_EN.
   - R142-1 is enclosed by the U14-FB F loop.
   - The only FB via site outside In2 SYS_RAW is the loop's own via (91.875, 96.475); `freevia.py` finds 0 sites between R141 and R142.
   - A via NE of R142 shorted SYS_RAW, so it was reverted.
   - VOUTL needed the XTO shift and the VCCP2I stub trim (2 DRC rounds).

  Not done in this group:
  - **CC1/CC2:** In2 USB_VBUS island (x 136-153.5, y 46.5-54.5, plus a column x 146.5-153.5 up to y 30.5) forbids vias near the caps and D5. The F path north (x 137.6 / 139-140) is feasible, but crossing the USB DP/DN pair needs a B hop at y 32-38.5, x 143.5-146.2, and the D5 side is boxed by D6/C5/U19.
  - **Q101-G:** AUD_SCL (F, y 108.7) separates Q102-3 from Q101-1/R110-2. In2 under Q101 is BAT_PACK (no via) and TS_SENSE runs on B at y 108.35, so it needs an AUD_SCL reroute or a Q101 move (not allowed).

**Task 1 (R262/R258, AMP_FAULT_N/AMP_PDN), 2 iterations.**
- B3 and B4: 2 closures.
- Long probes, 8 M nodes each (`t/L/j_*.log`):
  - AMP_FAULT_N U7-9 -> U3-25: exhausted.
  - AMP_PDN R258-1 (old position): exp 37 k, sealed. At the new position it is west of AUD_SCL, but the AMP_PDN copper is 50 mm away.
  - TP20: not attempted. It sits south of BKO_U6, the In2 there is PVDD, and U6-9 is inside BKO_U6 (no via).

**Task 2 (long U3 nets), 3 iterations** (all with ic_allow U3, F/B/In2, up to 8 M nodes):
1. Probe B2:
   - HP_G0 and HP_SEL_B found from the mux side (83 / 81 mm), using the same B corridor y 68-70.5.
   - From U3-16 and U3-51 the search fails (exp 2 / 1.05 M).
   - HP_EN fails from both ends (0.37 M / 5.1 M).
   - AUX_DET: R242-2 sealed (exp 6); the U3 side failed at 0.25 M.
2. V1 with void cost 10: HP_SEL_B failed (5.6 M); HP_G0 OK and integrated (H1).
3. HP_SEL_B on C1 and H1: failed (4.3-5.6 M). The B2 path ended under U3 to U3-51, a lane now used by the BT_TX_IND repair, and the void gate needs that repair. The B2 route is kept as a reference plan: `t/L/p_selbR.json`.

**Task 3 (BCK x2, AUD_SDA x2):** analysed, no copper (budget).

**Task 5 (U4 charger, 3V_AO, jack audio):** probes only (`t/probe/*.log`).
- CTRL_SCL U4-14: exp 5.
- QON U4-12: exp 30.
- ILIM_HIZ: exp 0.
- 3V_AO: 8 M exhausted.
- C204/C205: exp 33/41 at the C end.
- C235: exp 4 / 1.0 M.
- USB_AUDIO_L/R: exp 226 / 9.9 k.
- AUX_L: one B-hop route exists, but its only via site (190.59, 38.48) has no GND stitch site within 1.5 mm (`freevia.py`: 0), so it was not applied.

**Task 6:**
- Void gate met (264.7). V1: 3 rounds: 1 of 11 chains on In2 only; then 6 with F/In2; then clean re-routes near U3.
- HP_R and ADC_INT were not changed.
- Own new dangling ends: 0. RT-11's 20 cosmetic ends were not merged.

## 5. Remaining open connections (26, all real) and suggested GUI actions

Owner routes by hand in 45-degree steps.
- **Audio:** 0.3 mm width, 0.5 mm clearance, B only over In2 GND, GND stitch within 1.5 mm.
- **I2S:** 0.6 mm spacing.
- **Slow nets:** may use In2 under rules 11/21.

| # | from | to | net | verified cause | suggested layer / corridor |
|---|---|---|---|---|---|
| 1 | TP12-1 (146.35, 95.40) | U6-13 (109.50, 126.39) | I2S_BCK | TP12 pocket boxed by LRCK (x 142.9 / y 97.75) and SDATA (x 148.5) on F. In2 under the hub is the VBUS_PD trunk (x 141.5-149) | Cut a GND window in VBUS_PD_IN2 at x 141-146.2, y 94.6-97.6. The trunk keeps x 146.2-149.3; the _G strip x 139-141 (necks >= 1.0 mm). B hop (144.0, 96.0) -> (141.6, 96.0) with GND stitches (144.0, 97.0), (141.6, 97.1). Move the ADC_INT F vertical (x 136.2) and TP15 off the x + y = 232.19 lane, then F parallel to LRCK to U6. Length-match LRCK/SDATA +-2 mm. |
| 2 | U7-13 (192.29, 126.39) | BCK track (147.15, 93.75) | I2S_BCK | U7 verticals SDATA x 192.345 / LRCK x 193.345 are 1.0 mm apart; diagonals 0.92 mm apart (BCK in between would give a 0.21-0.25 mm gap). B is forbidden in BKO_U7 and In2 is BAT_PACK there. | Re-space the bundle: verticals SDATA 192.0 / BCK 192.85 / LRCK 193.7; diagonals x - y = 78.4 / 79.6 / 80.8 (LRCK diagonal re-drawn from its B-hop via 182.145, 102.447). BCK F from the hub along SDATA's y 93.7 run. |
| 3 | U24-23 (150.75, 88.28) | AUD_SDA B (139.05, 83.10) | AUD_SDA | U24-23 pocket: DOUT/R206 west, AUD_SCL east, SDATA y 92.5 south. A via is legal only in the BKO_ADC notch (x 145.5-152, y 89.4-92). B west of x 149.3 is over the In2 VBUS_PD trunk (sensitive net). | F w0.2 down x 150.745 to a via at (150.75, 91.4) (In2 GND). B east/south over In2 GND (x >= 149.5); join AUD_SDA along AUD_SCL's route (F y ~72.35 parallel to AUD_SCL y 71.75, B x ~163.6 parallel to x 163.03), or after the VBUS_PD window of row 1, B west under the hub. |
| 4 | U7-15 (191.29, 126.39) | U24-23 | AUD_SDA | 60 mm I2C; corridor shared with rows 2/3 | F vertical x 191.2 between AUD_SCL (190.1) and SDATA (192.345), then the diagonal corridor (R258 moved out of it in RT-12). Pair with AUD_SCL; the AUD_SCL Q101/Q102 pocket must be avoided. |
| 5 | U3-25 (133.68, 76.25) | R262-2 (111.50, 124.95) | AMP_FAULT_N | 50 mm; In2 allowed; via-free inside BKO_U6 | F out of BKO_U6 north of y 114 from R262 (free area above U6 pins 9-11), via, In2 north-east (GND pour west of the VBUS_PD trunk) to U3's east column, parallel to AMP_PDN. |
| 6 | U7-9 (194.29, 126.39) | U3-25 | AMP_FAULT_N | 8 M nodes exhausted; In2 BAT_PACK/PVDD islands near U7 | F north from U7-9 east of LRCK (x >= 194.3) to y < 105, then In2 west (rule 11) over GND; cross the VBUS_PD trunk on F. |
| 7 | TP20-1 (110.16, 149.65) | AMP_FAULT_N (111.50, 124.95) | AMP_FAULT_N | TP20 south of BKO_U6; In2 under it is PVDD | F only around U6 (west of x 105) or move TP20 (not in the movable list). |
| 8 | R258-1 (185.60, 113.00) | AMP_PDN (137.47, 80.90) | AMP_PDN | 50 mm; In2 BAT_PACK under R258 | F north-west from R258 between AUD_SCL and the BAT_PACK vias to y < 107 (In2 GND), via, In2 west (rule 11), F across the VBUS_PD trunk. |
| 9 | U3-51 (122.33, 73.75) | R235-1 (183.40, 58.70) | HP_SEL_B | Router found 81 mm on B2 (`t/L/p_selbR.json`); its U3 entry lane (F under U3, x 123.85-127.75, y 73.8-77.7) is now used by BT_TX_IND | Reuse the reference path but enter U3-51 from the west side (pin faces west), F north of U3's top fan; the B corridor y 68-70.5 is shared with HP_G0 (keep 0.6 mm). |
| 10 | U3-47 (124.75, 70.83) | HP_EN (197.04, 63.78) / R236 | HP_EN | Both ends escape (0.37 M / 5.1 M nodes) but do not meet | As 9, parallel corridor; F north of the mux block along y 56-57 to R236. |
| 11 | U3-29 (133.68, 74.25) | R242-2 (189.82, 36.30) | AUX_DET | R242-2 sealed in the jack knot (exp 6) | Free R242-2 together with rows 17-21 (jack block); In2 north-east to y 45, F into R242. |
| 12 | U4-14 (152.17, 124.08) | CTRL_SCL (133.75, 96.25) | CTRL_SCL | U4 bottom-row 0.4 mm pitch: no via site (exp 5) | RT-8 4.1 remedy: R103 move (allowed nudge), then via south of pin 14, In2/B north-west. |
| 13 | U4-12 (151.37, 124.08) | QON (135.25, 25.00) / SW100 | U4-QON | as 12 (exp 30); 100 mm | as 12, then In2 (rule 11) north along the west of the VBUS_PD trunk to SW100. |
| 14 | U4-17 track (153.42, 123.39) | Q101-3 (180.96, 110.73) | ILIM_HIZ | Q101 sits over In2 BAT_PACK (no via); sense net | F only: east along y ~118-120 south of the BAT_INT island, then north into Q101-3 from the east (R109 side). |
| 15 | Q102-3 (179.09, 107.22) | Q101-G (176.59, 109.42) | Q101-G | AUD_SCL F y 108.7 between them; BAT_PACK In2 south (no via); TS_SENSE B y 108.35 | Re-route AUD_SCL locally north of Q102/R111 (needs R111 nudge <= 3 mm, allowed), then F Q102-3 -> Q101-1 straight down x 179.09. |
| 16 | R241-1 (188.42, 38.65) | 3V_AO (126.95, 64.48) | 3V_AO | 8 M exhausted | RT-10 lane: In2 y 56-58 to x 138.5, B over the VBUS_PD island x 138.5-150, B north of BKO_CODEC y 45-48. |
| 17 | C204-1 / C234-1 stub (191.14, 39.03) | D201-1 AUX_L (194.19, 36.59) | AUX_L | C234-Pad2 via (193.69, 37.49) and its F diagonal block the direct F path; the only B-hop via site (190.59, 38.48) has no GND stitch site within 1.5 mm | Move the C234-Pad2 via west of C234-2 or nudge C234 (<= 4 mm allowed), then F C234-1 -> D201-1 at x ~193.0 (no via). |
| 18 | R225-1 (189.74, 40.97) | R231-1 (184.80, 56.60) | C235-Pad2 | R225-1 enclosed by the VMID_HP F loop (x 188.44 + diagonal) | Re-route VMID to R225-2 from the north (x 187.6), then B hop from (187.5, 45) to below R225-1 over In2 GND, with a stitch. |
| 19 | C235-2 (195.26, 40.80) | R225-1 | C235-Pad2 | C235-2 enclosed by the AUX_R loop (C235-1 -> y 41.9 -> x 197.1) | Re-draw AUX_R around the south of C235, then F C235-2 -> R225-1 at y ~41.2 between the GND vias (190.9, 41.5) / (191.5, 41.1); move one of them. |
| 20 | R204-1 (156.35, 90.73) | C204-2 (191.14, 40.17) | C204-Pad2 | 60 mm audio; C end boxed (exp 33) | F north-east along y 50-55 between U24 and the mux, B hops only over In2 GND with stitches; free the C end with rows 17-19. |
| 21 | R205-1 (156.95, 89.28) | C205-2 (192.89, 42.37) | C205-Pad2 | as 20 (exp 41) | parallel to 20 at 0.6 mm |
| 22 | C200-1 (162.02, 79.00) | USB_AUDIO_L (174.55, 60.88) | USB_AUDIO_L | AUD_SCL F diagonal (157.6, 71.7)-(163.0, 76.1), its via and B x 163.0 wall the caps to the north-east (exp 226) | B hop east of C200 over In2 GND (check 5V_CODEC trunk), then F north-east to y 64 and on to the mux. |
| 23 | C201-1 (162.02, 77.65) | USB_AUDIO_R (168.75, 56.43) | USB_AUDIO_R | as 22 | parallel to 22 |
| 24 | C182-1 (139.50, 52.67) | D5-1 (152.79, 30.91) | USB_CC1 | In2 USB_VBUS island under the caps and D5 (no via); USB DP/DN pair between | F east of C182 (x 140.15), north-west of TP1 to x 139, north to y ~38.5. B hop under the DP/DN pair at y 32-38.5 (vias at x <= 143.5 and 145.2-146.2, In2 GND). F to D5 north of D6 (y < 31.3). |
| 25 | C183-1 (138.25, 52.67) | D5-2 (152.79, 32.80) | USB_CC2 | as 24 | F west of C183 at x 137.6 north to y 47 (clear of C184/VBUS by >= 0.4 mm), then as 24 |
| 26 | R142-1 (92.53, 97.42) | 5V_LOGIC_EN (98.72, 98.20) | 5V_LOGIC_EN | R142-1 enclosed by the U14-FB loop; In2 SYS_RAW leaves no other FB via site | Needs R142 or R141 moved >= 0.5 mm (not in the movable list): coordinator decision. |

**Hand-assembly note (unchanged):** C215-C212 are 0.14 mm apart. Place C215 and C212 first, before U24 and Y200.

## 6. Files (`ai-files/pcb/work-route12/`)

**Result:** `RT-12.kicad_pcb`, `RT-12.kicad_pro` (= base), `RT-12.kicad_dru` (= RT-11).

**Gates:**
- `t/RT-12.gates.txt` and `RT-12.drc.json`;
- `t/RT-12.gates.json` (locked manifest and new-copper list);
- `t/RT-12.check.json/.txt`, `t/RT-12.r7.json`, `t/RT-12.par.json`, `t/RT-12.ha8.json`, `t/RT-12.cp.json`, `t/RT-12.rulehash.txt`, `t/RT-12.silkgate.json`;
- `sentinel/RT-12_sentinel.*` and `sentinel/S21*`.

**Plans and logs:**
- `t/b1` ... `t/f1` (`base.py` per batch), `t/<stem>.edit.json`;
- probes in `t/probe/` and `t/L/`.

**Scripts (new):**
- `cycle12.sh`, `gates12.sh`, `hr12.py`, `merge12.py`, `resolve.py`, `mkjobs12.py`, `probe12.py`;
- `freevia.py`, `in2map.py`, `inbox.py`, `fppos.py`, `bchains.py`, `planvoid.py`, `voidall.py`, `islanddiff.py`;
- `silk_tile12.py`, `sentinel21_12.sh`, `render12.sh`.

**Evidence** (`evidence/`):
- full board: `rt12-F.png`, `rt12-B.png`;
- before/after: `rt11-` / `rt12-u11.png`, `-r262.png`, `-r258u7.png`;
- after only: `rt12-u17.png`, `rt12-u14.png`, `rt12-voutl.png`, `rt12-u3west.png`, `rt12-u12en.png`.

**Size:** about 0.2 GB of intermediate boards and geo exports. Do not commit them.
