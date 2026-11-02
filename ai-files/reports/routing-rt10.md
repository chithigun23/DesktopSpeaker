# RT-10: In2 rule for slow nets, slow-net closures and B-over-void repair (2026-11-03)

Agent "RT-10 In2 for slow nets and audio re-placement".
- **Input:** `ai-files/pcb/work-route9p/RT-9p.*` (DRC 0, 50 unconnected, 233/283 connections).
- **Work folder:** `ai-files/pcb/work-route10/` only. Nothing in `DesktopSpeaker-kicad/`, earlier work folders or `helpers/route_oct*.py` was edited.
- **Result:** `ai-files/pcb/work-route10/RT-10.kicad_pcb` / `.kicad_pro` / `.kicad_dru`.
- **Method:** text-level board edits (`scripts/edit.py`). Each build was refilled in a separate pcbnew process with the pristine `base.kicad_pro` + `RT-10.kicad_dru` beside it (`scripts/cycle10.sh`). The board keeps its KiCad-10 net names.
- **Not done:** nothing committed or published. No release-todo file: 46 open connections remain that are not accepted.

## Bottom line

- Unconnected went from **50 to 47**: **3 closures**, **no connection lost**, **no part moved**. DRC has 0 violations.
- **Closed:**
  - **BT_RST_M**: on In2 under the new rule 21.
  - **CHG_ENABLE** (U3-38).
  - **CHG_SYS_ENABLE** (U3-42).

  The two charger lines leave U3 through its package body (section 2.2).
- **B.Cu over In2 void:** 269.5 → **266.9 mm**. This meets the ≤ 269 gate but not the ≤ 200 target.
- **Task 2 is largely not closed.** For most of its nets the lever was not In2. U3's own pins now escape. The blockers are the far ends: R262, R258, R237/U10, U9-5, R242, U4's bottom row and Q102-3. Each is sealed by local copper, a BKO area or an In2 island, so no via site exists (section 4).
- **Tasks 3 (audio re-placement) and 4 (I2S BCK):** analysed, not executed (sections 4 and 5).
  - Audio: no part was moved.
  - BCK: the lane RT-7 reserved for it is now crossed by ADC_INT.

## 1. Gates

All gates are independent of the editing tools; the full output is in `t/RT-10.gates.txt`.

| gate | RT-9p | RT-10 |
|---|---|---|
| kicad-cli DRC `--severity-all --all-track-errors` (project library, RT-10 rules) | 0 | **0** |
| DRC unconnected | 50 | **47** |
| closures | | BT_RST_M, CHG_ENABLE, CHG_SYS_ENABLE (1 → 0 each). **Lost: none** (`uncnet.py` per net) |
| other unconnected-pair changes | | Only end-point re-description, with the same count per net: HP_SEL_A, HP_EN, HP_OUTL, U14-FB, AUD_SDA |
| footprints moved / pad nets (360 fp, 1194 pads) | | **moved []**, **pad_net_diff []** |
| locked copper | | 3397 of 3432 RT-9p items untouched; 35 removed or changed (all in `t/RT-10.edit.json`); **0 unexpected**. SHA-256 `9dededefa53f6baa4c9f1450f5f46c98665f8f35e264044b63a68ceebda91b0c` |
| new copper exact 0/45/90 (gates4) | | **69 segments, 231.0 mm, 0 not exact** |
| rule file | ce43baa1… | `RT-10.kicad_dru` = RT-9p + rule 21 only (diff: 15 lines added, 0 removed), c47d6aed…; `.kicad_pro` unchanged, aa88e8c9… |
| route_oct sentinel | FIRES (81) | **FIRES (81)** |
| rule 21 sentinel (`scripts/sentinel21.sh`) | | **PASS**, see below |
| pour check (route_oct_pourcheck) | | **OK**, foreign unconnected 1 → 1 |
| islands per zone (`scripts/islands10.py`) | | See below |
| r7 B.Cu over In2 void | 269.5 | **266.9** (gate ≤ 269 met; target ≤ 200 not met) |
| r7 sensitive B over void | | Unchanged for every net (BT_AUDIO_R 4.3, AUD_SDA 3.1, …) |
| r7 BM83 F.Cu in module | GND 2.3, SYS_PWR 2.0 | **unchanged** |
| antenna keep-out | | DRC 0 (rf_keepout untouched) |
| parcheck sensitive pairs / sens. vias > 1.5 mm from GND | 1 (USB pair) / 1 | **1 / 1** (unchanged) |
| parcheck slow pairs < 0.4 mm over > 3 mm | 9 | **8** |
| HA8 failing pairs | 122 | **122** (no new pair, none tighter) |
| BAT_INT U4-22/23 → Q103 at 6 A | 2.889 mΩ | **2.889 mΩ** (104.0 mW) |
| route_oct_check (all nets) | | See below |
| silkscreen | | No part moved, so silk_tile was not run |

**Rule 21 sentinel.** Three DRC runs on copies in `sentinel/`:
- **A** (RT-10 rules, In2 test tracks inside GND): `in2_power_only` fires for Net-(U14-FB) only.
- **B** (RT-9p rules, same tracks): it fires for both /HP_G0 and U14-FB. This proves that rule 21 is what allows the listed nets.
- **C** (a /HP_G0 track 0.20 mm wide): `rt10_in2_slow_width` fires.

**Islands per zone.**
- Every In2 power island keeps one island, with the same area as RT-9p: VBUS_PD, VBUS_PD_G (10 parts), USB_VBUS, SYS, BAT_INT, BAT_PACK, PVDD, PVDD_G.
- GND_IN2_BG: 52 → 51 islands, area −18 mm².
- GND_BCU: 4 → 5 islands. The new piece is 11.8 mm² at x 132.8-139.6, y 79.3-84.7, enclosed by the two CHG B hops and GAUGE_ALRT_N. It is connected through one GND via, like the three existing small pieces.

**route_oct_check, all nets (RT-9p → RT-10).**

| check | RT-9p | RT-10 |
|---|---|---|
| joints < 90° | 0 | 0 |
| T-junctions | 12 | 13 |
| bend spacing short | 26 | 27 |
| pad exits short | 10 | 11 |
| dangling (checker) | 43 | 43 (no new) |
| exact angles | 100 % | 100 % |
| In2 signal length | 205.0 mm | 227.5 mm |
| complete nets | 98 | 101 |

## 2. Edits

All coordinates are in mm. The full per-item table is in `t/editlog.md`.

### 2.1 Rule 21 (exact text, appended to the RT-9p rule file)
```
# 21. RT-10 (coordinator decision 2026-11-02; documented additive exemption, sentinel-tested): slow digital control / status /
#     enable / strap / UART / debug nets that rule 11 does not list may run on In2.Cu, in the In2 GND pour only.
#     Not for audio, I2S, USB data, clocks/crystals, switch nodes or analogue sense/feedback nets.
#     21a lifts rule 11 for these nets (a later matching rule takes precedence; severity ignore = allowed);
#     21b keeps them at >= 0.25 mm on In2. Clearance to In2 power islands stays 0.3 mm (rule 19, Default class).
(rule rt10_in2_slow
  (layer "In2.Cu")
  (condition "A.Type == 'Track' && (A.NetName == '/Bluetooth/BT_RST_M' || A.NetName == '/Bluetooth/BT_SYS_CFG' || A.NetName == '/HP_G0' || A.NetName == '/HP_G1' || A.NetName == '/Fuel_Gauge_Power/GAUGE_ISO_N' || A.NetName == 'Net-(U12-EN)' || A.NetName == 'Net-(Q101-G)')")
  (constraint disallow track)
  (severity ignore))
(rule rt10_in2_slow_width
  (layer "In2.Cu")
  (condition "A.Type == 'Track' && (A.NetName == '/Bluetooth/BT_RST_M' || A.NetName == '/Bluetooth/BT_SYS_CFG' || A.NetName == '/HP_G0' || A.NetName == '/HP_G1' || A.NetName == '/Fuel_Gauge_Power/GAUGE_ISO_N' || A.NetName == 'Net-(U12-EN)' || A.NetName == 'Net-(Q101-G)')")
  (constraint track_width (min 0.25mm)))
```

**How the override works.** A disallow rule cannot be undone by a later rule without a severity: KiCad ORs the disallow flags. So 21a matches the same items with `(severity ignore)`. As the later rule it takes precedence for the listed nets, and every other net still hits rule 11. This was verified with sentinels A and B.

**What the nets are.** All seven are static or event-rate GPIO, enable, strap or reset lines.
- The two TPS25730D strap nets (U11-ADC4, R18/RESERVED) were in a first draft and were removed: ADC4 is an analogue divider level.
- The project `.kicad_dru` still needs this rule and `rt5_sw100_te_land`; that update is the coordinator's.

**Nets on In2 in RT-10:**
- **New under rule 21:** /Bluetooth/BT_RST_M, In2 0.25 (98.795, 24.365)-(98.795, 46.865), 22.5 mm.
- **Rule-11 nets with new In2 copper:** none. CHG_ENABLE and CHG_SYS_ENABLE use F/B only.

### 2.2 Router copy (`scripts/hr10.py`, copied from work-route9 hr8.py)

Changes from hr8:
- The In2 net list is read from `RT-10.kicad_dru`: rule 11 plus rule 21.
- In2 cells under B.Cu signal tracks cost 4× (`in2_bshadow`), so an In2 run does not open void under existing B copper.
- New options:
  - `void_cost`: cost of B over In2 non-GND;
  - `zone_soft`: F/B pours eroded 0.2 mm in the model, because they refill around new copper;
  - `ic_allow`: package bodies that may carry F tracks and vias.
- **Policy change, for the coordinator to accept:** `ic_allow: ["U3"]`.
  - U3 is the LQFP-64 with no exposed pad. Its body was empty on F.Cu only because of hr7's IC-body keep-out. That keep-out is an RT-7 tool choice, not a rule in the routing standard or in `.kicad_dru`.
  - CHG_ENABLE and CHG_SYS_ENABLE now leave pins 38 and 42 inward under the body, on F.Cu, to the SE corner. Their first vias are fine 0.5/0.2 vias inside NECK_U3: (135.30, 81.825) and (133.85, 83.325). Both are tented and outside every pad.
  - For stencil, tweezers and hotplate assembly this is harmless: no pad, mask over copper.

New helper scripts:
- `snap10.py`: extends a route end along its own direction onto the target copper, so angles stay exact.
- `voidjobs.py` / `voideval.py`: B-over-void repair jobs.
- `final10.py`: final composition.
- `gates10.sh`, `sentinel21.sh`, `islands10.py`, `voidmap.py`, `whyblk.py`, `pngscale.py`, `mkj10.py`, `mkdru.py`, `cycle10.sh`, `runvar.sh`.

### 2.3 Closures

**BT_RST_M** (U1-43 → J8-1). 32.1 mm against an octilinear minimum of 30.3 (ratio 1.06), 2 vias.
- The RT-8 escape stub end (98.6975, 24.365) is lengthened to (98.795, 24.365): seg set 1656e077; micro segment 12447eb0 deleted.
- Via (98.795, 24.365).
- **In2** (98.795, 24.365)-(98.795, 46.865).
- Via, then F (98.795, 46.865)-(102.795, 50.865) into J8-1.
- The In2 run passes 2 layers below the BM83 module. F.Cu inside the module is unchanged and In1 GND under the module is intact.

**CHG_ENABLE** (U3-38 → the RT-8 stub near (162.09, 107.59)). 69.0 mm against 53.4 (ratio 1.29), 4 vias.
- F (129.25, 70.825)-(129.25, 77.275)-(133.80, 81.825)-(135.30, 81.825).
- Via 0.5/0.2, then B (136.35, 82.875)-(136.35, 85.575)-(137.45, 86.675).
- Via, then F (137.45, 86.675)-(137.45, 92.025).
- Via, then B (138.80, 93.375)-(154.55, 93.375)-(164.55, 103.375)-(164.55, 104.125).
- Via, then F (162.50, 106.175)-(162.50, 107.585), T-joining the stub.

**CHG_SYS_ENABLE** (U3-42 → Q102-1). 80.5 mm against 68.9 (ratio 1.17), **6 vias**. This exceeds the ≤ 4 preference. The only 4-via CHG_SYS_ENABLE variant (Wa, 74.4 mm) pushed CHG_ENABLE to 8 vias and the void to 270.0 mm, so it was dropped (see AG13).
- F (127.25, 70.825)-(127.25, 76.325)-(132.55, 81.625)-(132.55, 82.775)-(133.10, 83.325)-(133.85, 83.325).
- Via, B to (133.85, 88.975); via, F to (135.30, 91.175).
- Via, B (138.35, 94.225)-(150.55, 94.225).
- Via, F (150.55, 95.275)-(149.95, 95.875)-(149.95, 98.625)-(153.30, 101.975)-(165.25, 101.975).
- Via, B (165.80, 101.425)-(167.25, 101.425)-(169.95, 104.125).
- Via, F (178.80, 104.125)-(180.05, 105.375) into Q102-1.

**Constraints on the CHG routes.**
- Both routes were run with a block on the RT-7 BCK lane x + y = 232.19 (F) and on B.Cu x 139-150.6 / y 94.4-99.6 (the BCK hop window, section 5).
- **Note for task 4:** CHG_SYS_ENABLE's F run x 149.95, y 95.9-98.6 sits in the hub's east exit, which the U7 BCK path would need. Move it about 1 mm east when BCK is done.

### 2.4 B-over-void repairs (task 5)

Method: each slow B chain carrying ≥ 1 mm of void was ripped and re-routed end to end with a high void cost (`voidjobs.py`, 52 + 58 jobs). A result was accepted only if it:
- gained ≥ 0.3-0.8 mm,
- added no via (GAUGE_ISO_N excepted: via count unchanged),
- grew no more than 15 % + 1 mm in length,
- and left the slow-pair count < 0.4 mm unchanged.

| net | change | void (mm) | length (mm) |
|---|---|---|---|
| GAUGE_ALRT_N | The B run y 78.35 under U3 (117.03-135.28) moves south. New path: B (115.925, 80.45)-(115.925, 81.45)-(116.875, 82.40)-(119.925, 82.40)-(120.475, 82.95)-(122.575, 82.95)-(123.325, 82.20)-(129.275, 82.20)-(132.825, 78.65)-(135.575, 78.65)-(136.175, 79.25) | 11.2 → 8.8 | 22.1 → 23.8 |
| GAUGE_ISO_N | The B vertical x 111.46 over the In2 3V_AO trunk (and its two vias) is replaced. New path: via (109.61, 75.1775), B to (109.61, 79.3275)-(110.16, 79.8775)-(110.16, 81.0775)-(110.96, 81.8775), via, F west to the existing diagonal at (109.96, 81.8775). Vias stay at 2; the GAUGE_ISO_N / ENC_B 6.3 mm pair at 0.265 is gone. | 3.4 → 1.5 | |
| CODEC_PWR_EN | The F → B → F loop between R212-1 and U23-3 (2 vias) becomes one F segment (184.2075, 54.29)-(184.2075, 52.79). | 2.9 → 0 | |
| SWDIO | B (129.365, 71.695)-(130.615, 71.695)-(132.465, 69.845)-(133.215, 69.845)-(134.165, 68.895) | 2.3 → 0.4 | |
| PDCTRL_SDA | The J4-3 B hop becomes F (138.58, 42.525)-(137.40, 42.525); the via is removed. | 1.2 → 0 | |
| CHG_QON_SENSE | B (131.05, 68.725)-(127.55, 68.725)-(126.25, 67.425)-(126.25, 62.875)-(127.05, 62.075)-(128.05, 62.075)-(128.60, 62.625)-(129.35, 62.625) | 9.1 → 8.5 | |
| HP_SEL_A | B (130.80, 83.825)-(130.80, 82.925)-(132.80, 80.925)-(133.70, 80.925) | 1.6 → 1.3 | |

**Rejected repairs:**
- **BT_TX_IND** (−2.4 mm) and **BT_MFB** (−1.2 mm): each created a new slow pair under 0.4 mm (ENC_A 5.7 mm at 0.37; BT_TXD_M 4.5 mm at 0.26).
- **BT_FORCE_PWM** (−0.3 mm): its end could not be made coincident.
- **SWCLK east** (−0.8 mm, +1 via, plus an F-only variant at 29 mm with 5 vias).
- **AUX_L closure** (B hop, 2 vias): no legal GND stitch within 1.5 mm of via (190.64, 38.50); the nearest GND via is 2.74 mm away. This breaks the audio rule, so the closure was removed.

**Other task 5 items.**

| item | RT-9p | RT-10 | note |
|---|---|---|---|
| BT_AUDIO_R B over void | 4.3 mm | 4.3 mm | Unchanged. Its only void is the RT-9 SCL tie In2 x 130.3 crossing (RT-9 2.4). |
| ADC_INT | 35.6 / 34.1 mm | unchanged | TP26 is a PTH that would cut VBUS_PD_IN2_G; not changed. |
| slow pairs < 0.4 mm over > 3 mm | 9 | 8 | GAUGE_ISO_N/ENC_B removed; SWCLK/SWDIO B 6.7 → 5.0 mm |
| C215-C212 0.14 mm | | unchanged | Accepted as a hand-assembly item (decision 6): place C215 and C212 first, before U24 and Y200. |

## 3. Length report

Measured by route_oct_check.

| net | length | octilinear min | ratio | vias |
|---|---|---|---|---|
| BT_RST_M | 32.1 | 30.3 | 1.06 | 2 |
| CHG_ENABLE | 69.0 | 53.4 | 1.29 | 4 |
| CHG_SYS_ENABLE | 80.5 | 68.9 | 1.17 | 6 |
| GAUGE_ALRT_N | 58.0 | | 1.26 → 1.30 | 4 |
| CODEC_PWR_EN | | | 1.79 → 1.73 | 4 → 2 |
| CHG_QON_SENSE | | | 1.21 → 1.20 | |
| SWDIO | 66.0 (unchanged) | | | |
| PDCTRL_SDA | | | | 8 → 7 |

- All-net median ratio 1.17, p95 2.95; all new copper is exactly on the 0/45/90 grid.
- No new joint is under 90°. One extra 90° joint, T-junction, bend-spacing and pad-exit item each comes from the CHG routes (U3 corner and the stub T-joins).
- Teardrops: none removed (0 near the edits). The new vias need GUI teardrops at release.

## 4. Remaining open connections (47) by cause

The CHG_INT connection already accepted under P1 is not counted in the 47.

| group | conns | nets | verified cause (RT-10 probes) | proposal |
|---|---|---|---|---|
| U3 long nets | 11 | AMP_FAULT_N ×4, HP_G0 ×2, HP_SEL_B ×2, HP_EN, AUX_DET, AMP_PDN (R258) | (a) | Mux-cluster re-place (decision 3) with a via row south of BKO_MUX; R262 0.8 mm south-west and R258 0.6 mm east (both outside the movable list) |
| U4 charger | 4 | CTRL_SCL (U4-14), QON (U4-12), ILIM_HIZ, Q101-G (Q102-3) | (b) | RT-8 4.1 remedy: R103 move; CE_N to B at pin 13; REGN via 0.6 mm north; R111 to the west of Q102-1 |
| I2S / AUD I2C / amp control | 5 | I2S_BCK ×2, AUD_SDA ×2, U7-PDN | (c) | Section 5 |
| U24 inputs / USB audio | 9 | C204/C205/C233-Pad2, C235-Pad2 ×2, USB_AUDIO_L, USB_AUDIO_R ×2, U2-VOUTL | (d) | Input-block re-place (RT-7 3.3) together with the mux re-place |
| headphone mux | 7 | U8-COM1/COM2/NC1/NC2, HP_L, HP_OUTL, HP_SEL_A (U8-1) | (e) | Re-place U8/U9/U10 with NO/NC fans alternating north/south (RT-7 3.4) |
| USB-C / PD / regulators / gauge | 9 | U11-ADC4, R18, PD_SINK_EN, USB_CC1, USB_CC2, U14-FB, 5V_LOGIC_EN, U12-EN, GAUGE_ISO_N | (f) | Manual lanes; U14-FB needs R140 + C142 re-placed |
| power | 1 | 3V_AO to R241 | (g) | Manual lane: In2 y 56-58 to x 138.5, B over the VBUS island x 138.5-150, then B north of BKO_CODEC at y 45-48 (`t/fm_3vao.png`) |

Causes:

- **(a) U3 long nets.** With the U3 body open, every U3-side search now expands 0.3-8.7 M nodes, so the U3 pins escape. The far ends are sealed:
  - **R262-2** (AMP_FAULT_N), exp 11. North: the PVDD_C271_F pour and the PVDD vias (116.2, 124.6) and (116.8, 124.85). West: GND via (115.24, 125.9) and C281/C282. East: L201 (SPK_OUT, 0.3 mm). BKO_U6 forbids a via. U6-9, U7-9 and TP20 can reach only R262.
  - **R237-1 / U10-6** (HP_G0) sit inside the HP_OUTR loop: U10-5 down to y 68, a diagonal to (194.0, 69.5), then west along y 69.5. BKO_MUX (x 169-199.5, y 62.3-69.5) forbids every via.
  - **U9-5** (HP_SEL_B), exp 0: boxed by the NO2 jog (184.79, 68.2)-(185.7, 69.3) and the GND vias (186.2, 67.4) and (186.1, 68.0).
  - **U10-13** (HP_EN): same cage; 3.6 M nodes, no path.
  - **R242-2** (AUX_DET): exp 6.
  - **R258-1** (AMP_PDN): enclosed by the LRCK via pair (180.34, 103.25)/(182.14, 102.45) with its 0.6 mm halo, the LRCK diagonal, and an In2 power island under the pocket. No via site (`t/dbg_pdnx.png`).
- **(b) U4 charger.**
  - U4-14 (exp 5) and U4-12: the 0.4 mm-pitch bottom row has no via site between the CE_N run x 151.77, the GND via (150.77, 124.65) and the SDA via (152.57, 125.28).
  - Q102-3: AUD_SCL (y 108.7) lies between it and Q101-1. Under the pocket there is the BAT_PACK island plus the TS_SENSE B run at y 108.3, so no via site (`t/fm_q101.png`).
  - ILIM_HIZ: a sense net, so F/B only; exp 4 and 0.84 M.
- **(c) I2S / AUD I2C / amp control.** BCK: section 5. AUD_SDA: U24-23 side exp 2768 (U24 neck), B end exp 0. U7-PDN: R258-2 shares the R258 pocket.
- **(d) U24 inputs / USB audio.** All 18 probes fail:
  - R229-1 exp 23, R225-1 exp 15, C235-2 exp 4;
  - U2-16 exp 0 (inside BKO_CODEC, so F only);
  - C200/C201 0.6 M nodes.

  These are 45-60 mm audio runs at 0.5 mm clearance with B only over In2 GND. The ≤ 4 mm cap moves allowed by decision 3 do not change that.
- **(e) Headphone mux.** U9-7/9/10 and U8-7/9 exp 0: 0.5 mm-pitch pins whose exits are taken by the neighbouring NO/NC jogs, and BKO_MUX forbids B and vias. Not done for budget reasons. AUX_L was closed and then reverted (section 2.4).
- **(f) USB-C / PD / regulators / gauge.**
  - U11-7 and U11-36 exp 0; R18-1 exp 39, because of the PD_PLUG_EVENT F loop around pin 36.
  - CC1/CC2: exp 33/134 from C182/C183, 2 M nodes from D5.
  - 5V_LOGIC_EN: R142-1 is enclosed by the U14-FB F loop, which runs from via (91.875, 96.475) around to R141-1. Every via site west of U14 sits on the In2 SYS_RAW tracks (w 2.5/3.0) or beside the SYS_RAW via (91.85, 99.95). Tried as build E1: shorts, reverted.
  - U14-FB is fenced by L2 (1.0 mm switch rule).
  - U12-EN exp 1; GAUGE_ISO_N 0.9 M nodes.
- **(g) 3V_AO.** 8 M nodes exhausted. B.Cu at y 56-58 is crossed by verticals at x 123.8, 130.7, 133.6 and 135.3, and In2 is walled by VBUS_PD at x 139-149.3.

## 5. Tasks 3 and 4: analysed, not executed

**Task 3 (audio re-placement): no part moved.**
- The probes above show that the mux cage is set by the U9/U8 pin jogs and the HP_OUTR loop. The U24 input nets are long (45-60 mm) because the coupling capacitors sit at the AUX jack, about 50 mm from U24.
- The ≤ 4 mm cap moves allowed would not change the topology.
- A useful re-place of U8, U9 and U10 needs:
  1. a NO/NC fan alternating north/south;
  2. a south via row at y ≥ 69.85, outside BKO_MUX, for HP_SEL_A, HP_SEL_B, HP_G0 and HP_EN;
  3. R237 placed below U10-6, south of HP_OUTR.

  This was not started for budget reasons; it needs its own run.

**Task 4 (I2S BCK): no copper and no island edited.**
- **Hub geometry:**
  - TP12 (146.35, 95.4) is boxed by LRCK: x 142.895 for y 94.05-97.05, and y 97.75 for x 143.6-144.8.
  - On the east it is boxed by SDATA (x 148.55, y 95.6-99.3).
- **U6 side:** one crossing.
  - Via (144.0, 96.0) in the pocket, then B west under LRCK to via (141.6, 96.0).
  - GND stitches at (144.0, 97.0) and (141.6, 97.1).
  - Needs a GND window cut in VBUS_PD_IN2 at x 141-146.2, y 94.6-97.6. The trunk keeps x 146.2-149.3 (3.1 mm) plus the _G strip x 139-141, so both necks are ≥ 1.0 mm.
- **Blocker found in RT-10:** the reserved lane x + y = 232.19 is crossed at (136.2, 96.0) by the ADC_INT F vertical (x 136.2, y 85.8-107.6) and by TP15 (137.1-138.9 / 95.3-98.7).
  - So the U6 path also needs ADC_INT moved. That fits task 5's ADC_INT length item, which needs TP26 moved and the VBUS_PD_IN2_G island reshaped.
- **U7 side:** still 2 crossings plus the fan at U7 pins 12-14 (RT-8 4.2).
- **Length match:** LRCK and SDATA to U6 are 50-52 mm octilinear, so meeting ±2 mm needs about 2-4 mm of meander on BCK.

## 6. AG13 iteration log (max 3 per task group)

**Task 2 (slow nets).**
1. A0: 25 single jobs on R1, FBI, rule 21 active. 1 OK (BT_RST_M). The track-start parse bug (layer "F.Cu,") was fixed for the next round.
2. A1/A2: fixed starts plus reversed directions (24 jobs); U1/U2: 26 jobs with the U3 body opened. Closed CHG_ENABLE and CHG_SYS_ENABLE; everything else failed at the far end.
3. Further attempts:
   - S1/S2: 38 audio, short and charger jobs; 1 OK (AUX_L), later reverted.
   - pdn0/1: AMP_PDN at 25 M nodes.
   - ao1: 3V_AO at 8 M nodes.
   - E1: manual 5V_LOGIC_EN / U14-FB re-route, shorts, reverted.

**Composition.**
- B1, B2: CHG routes without, then with, the BCK blocks.
- Ha/Hb: full hub block; Hb rejected for +6 mm void.
- Va/Vb/Wa/Wb: void cost 12/25 in both orders; Va used.

**Task 5 (void).**
1. V1: 52 chains.
2. V2: 58 chains.
3. Final composition C1-C6 → F1/F2 → G1-G6, with snapping fixes and the GAUGE_ISO_N manual re-shape.

**Task 3 / task 4:** analysis only (0 builds).

**Logs:** `t/j_*.log`, plans `t/p_*.json`, variant builds `t/*.var.txt`.

## 7. Files (`ai-files/pcb/work-route10/`)

- **Result:** `RT-10.kicad_pcb`, `RT-10.kicad_pro` (= RT-9p), `RT-10.kicad_dru` (= RT-9p + rule 21); `rule21-nets.txt`.
- **Build chain:** RT-9p = R0 → R1 (refill only, RT-10 rules) → G6 (plan `t/RT-10.plan.json` = `t/pG6.json`) = RT-10.
- **Gates:**
  - `t/RT-10.gates.txt`, `RT-10.drc.json`, `t/RT-10.gates.json`;
  - `t/RT-10.check.json/.txt`, `t/RT-10.r7.json/.txt`, `t/RT-10.par.json/.txt`;
  - `t/RT-10.rulehash.txt`, `t/RT-10.ha8.json`, `t/RT-10.cp.json`;
  - `sentinel/RT-10_sentinel.*`, `sentinel/S21A/B/C.*`.
- **Edit log:** `t/editlog.md` (from `t/RT-10.edit.json`).
- **Evidence (PNG):**
  - `evidence/rt10-F.png`, `rt10-B.png`, `rt10-In2.png`;
  - `rt10-chg-west.png`, `rt10-chg-east.png`, `rt10-btrstm.png`, `rt10-gauge.png`;
  - cause crops `cause-i2s-hub.png`, `cause-mux.png`, `cause-r262.png`, `cause-q102-r258.png`, `cause-u4.png`, `cause-u14.png`.
- **Size:** about 0.3 GB of intermediate boards (R0, R1, B1a, C1-C6, F1-F2, G1-G6) and geo exports. Do not commit them.

## 8. Requests to the coordinator

1. Accept or reject the U3 package-body routing policy (section 2.2). If it is rejected, CHG_ENABLE and CHG_SYS_ENABLE must be re-escaped.
2. Copy rule 21 into the project `.kicad_dru`, together with `rt5_sw100_te_land`.
3. Add R262, R258 and R111 to the movable list for the next run. These small moves would unseal AMP_FAULT_N ×4, AMP_PDN, U7-PDN and Q101-G.
4. Order the mux and input-block re-place as its own run, since 16 audio connections depend on it. Pair it with the BCK run, which needs the ADC_INT/TP26 move and the VBUS_PD window.
