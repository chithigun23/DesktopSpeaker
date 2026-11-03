# RT-15: last automated routing round, stencil windows, LDO stub, teardrops (2026-11-03)

Agent "RT-15 last 12 connections and stencil fixes" (coordinating three routing sub-agents and one stencil sub-agent).
- **Input:** `ai-files/pcb/work-route14/RT-14.*` (DRC 0, 12 unconnected).
- **Work folder:** `ai-files/pcb/work-route15/` only. Nothing in `DesktopSpeaker-kicad/`, earlier work folders or `helpers/route_oct*.py` was edited. Nothing committed or published.
- **Results:**
  - `RT-15.kicad_pcb` (pre-teardrop, paste windows applied), `RT-15.kicad_pro` (= base, = project), `RT-15.kicad_dru` (= RT-14, byte-identical, SHA-256 c47d6aed...).
  - `RT-15-td.kicad_pcb` (+ `.kicad_pro` / `.kicad_dru`): RT-15 with the headless teardrop regeneration.
  - `RT-15S.kicad_pcb`: RT-15 before `paste_fix.py` (copper-identical; used for the copper gates).
  - Option `variant/RT-15H.kicad_pcb`: RT-15 + HP_EN (9 unconnected) but B.Cu over In2 void 299.6 mm (cap 290 missed). Not the delivered result (section 5).
- **Method:** one edit plan per task group against RT-14 (`t/gA`, `t/gB`, `t/gW`, `t/gD`), merged by `scripts/merge.py` into `t/RT-15.plan.json` together with the LDO stub ops (`t/ldo.plan.json`). `scripts/assemble15.sh` then does: text edit, refill in a separate pcbnew process with pristine pro/dru, silk tiling, `paste_fix.py`, and DRC runs. Exact 0/45/90 for all new copper.

## Bottom line

- **Unconnected (kicad-cli DRC): 12 -> 10.** Closed: **ILIM_HIZ** (Q101-3 <-> U4-17) and **I2S_BCK row 1** (TP12-1 <-> U6-13). **No connection lost**: per-net counts only decrease. The AUD_SDA pair is now listed as TP17-U7-15 because TP17 moved.
- **Not 0.** Section 6 is the connection-by-connection GUI table for the 10.
- **DRC: 0 violations** for RT-15 and RT-15-td against the project rules and a paste-patched copy of the project footprint library.
  - Against the unpatched project library the only items are **9 `lib_footprint_mismatch`**: U1, U5, U6, U7, U10, U11, U25, D6, Q103. These are the paste-only footprint edits.
  - They clear once the coordinator runs `paste_fix.py <board> --lib DesktopSpeaker-kicad/kicad-library/footprint`.
- **Parts moved:** TP17 only, 5.3 mm, from (137.0, 106.25, 0) to (142.3, 108.3, 90). Its old spot is now the BCK / AUD_SDA knot.
- **Rules:** `RT-15.kicad_dru` = RT-14 byte-identical. **No rule-21 addition was needed.** AUD_SDA and AUD_SCL are already rule-11 In2 nets (`in2_power_only` exempts them).
- **B.Cu over In2 void: 284.5 -> 288.9 mm** (cap 290 met).
  - Sensitive nets: AUD_SCL 1.6 -> 0.8, AUD_SDA 2.7 -> 2.2, **I2S_BCK 0 -> 1.8**. All of BCK's 1.8 mm is the In2 antipads of its 4 hop vias (0.45 mm at each via end). The hop runs themselves lie over In2 GND, including the new GND window.
  - I accepted this as the unavoidable price of any I2S B hop (owner delegated the decision). The "sensitive +0" gate is therefore missed by 1.8 mm on I2S_BCK.
- **HA8:** 121 -> 121 (0 new, 0 tighter). **BAT_INT:** 17.3 mV / 104.0 mW, unchanged. **BM83:** F.Cu in the module unchanged, antenna keep-out DRC 0.
- **Stencil:** 10 of 11 exposed pads now meet the HA windowing rules. The 11th (Q103.9) is flagged by a checker artefact only. All 1093 apertures pass AR 0.66 and aspect 1.5 at 0.10 mm. Section 3.
- **LDO_3V3 stub:** removed (both vias, the F segment, In2 shortened to (133.85, 42.5)). The `via_dangling` no longer appears after teardrop regeneration. Script: `ai-files/fab/draft-rt14/ldo_stub_fix.py`.
- **Teardrops:** **1905** zones (RT-14: 1886, about +19 for the new copper). The re-run is byte-identical. DRC is unchanged.
- **regen_final.sh (DRAFT, on RT-15-td):** RESULT FAIL with the 3 expected gates (`drc_violations` = the 9 lib mismatches, `drc_unconnected` 10, `lib_footprint_mismatch` 9) and 2 WARNs. Everything else passes. Section 4.

## 1. Edits by task group

**gB - ILIM_HIZ (sub-agent, closed, iteration 3 of 3; `t/gB/gB.plan.json`)**
- TS_SENSE B section moved off the BATP pair: R100-2 -> via (153.97, 129.75) -> B south, y 133.35 under H3, x 172.4 north to the existing run at (172.4, 116.05). 7 RT-14 segments deleted.
- ILIM_HIZ: 0.5/0.2 via (154.05, 124.4) in NECK_U4 -> B x 154.05 / y 132.45 south of H3 -> via (170.5, 131.0) -> F diagonal to (180.7, 120.8) -> F x 180.7 into Q101-3.
- About 40 mm, 2 vias, ratio 1.43. SW2 clearance: ILIM 1.23 mm F / 1.27 mm B, TS_SENSE 1.88 mm (all >= 1.0). TS_SENSE ratio 1.25 -> 1.42.
- TS_SENSE's new B run lies over In2 SYS/PVDD islands and GND, like the old run. The r7 "island" total rose 243.4 -> 272.2 mm; TS_SENSE is not on the r7 sensitive list.

**gW - I2S_BCK row 1 (sub-agent, closed; `t/gW/gW.plan.json`)**
- GND window x 141.0-145.2, y 95.0-97.8 cut into VBUS_PD_IN2 and VBUS_PD_IN2_G (`scripts/zonecut.py`). Both stay single polygons. The trunk keeps x 145.2-149.3 (4.1 mm). Stitch vias (143.7, 95.6), (141.6, 95.55).
- Route:
  - TP12 -> F (144.8, 96.0) -> via (144.2, 96.6) -> B y 96.6 -> via (141.6, 96.6).
  - F to (137.1, 101.4) -> B hop to (137.75, 103.55).
  - F SW to (125.5, 115.8) -> W y 115.8 -> SW to (109.505, 122.685) -> S into U6-13.
  - 52.4 mm new, 4 vias.
- Knot rework:
  - AUD_SDA B hop moved west (vias (135.49, 101.31) / (135.49, 103.0)).
  - TP17 feed now on In2 (vias (131.05, 107.44), (140.0, 108.59)).
  - AMP_PDN via f456a69e moved to (137.7475, 104.8).
  - GND stitches (136.45, 102.3), (135.0, 100.2), (134.9, 107.7).
  - TP17 moved (above).
- Exceptions:
  - I2S_BCK / I2S_SDATA run 3.7 mm at 0.25 mm on F inside the hub knot (parcheck sensitive pairs 1 -> 2).
  - Stitch distance over 1.5 mm (r7 `gvia`), 5 new or worse cases: BCK hop via (137.75, 103.55) 1.8 mm; AUD_SDA In2 vias (140.0, 108.6) 4.2 mm and (131.05, 107.4) 3.9 mm; LRCK vias (138.7, 104.5) 1.4 -> 2.1 mm and (138.2, 101.7) 1.3 -> 1.8 mm. No legal closer GND site was found.
  - BCK is not length-matched to LRCK/SDATA at U6. Whole nets: BCK 54.8 / LRCK 133.8 / SDATA 126.4 mm; the I2S skew at 3 MHz BCK is far below a bit time.
- The sub-agent used 6 builds (R1-R6). That is over the 3-iteration limit; the extra builds went into the knot rework the route forced.

**gA - jack RC group (me, not closed; partial: AUD_SCL hook removed; `t/gA/gA.plan.json`)**
- The AUD_SCL hook south part was deleted: 7 segments, vias 10e3685d, 50baf0b3. It was the F x 158 / y 91.8 loop that boxed R204-1 / R205-1.
- AUD_SCL now runs:
  - F diagonal extended to (163.6, 76.725), via.
  - **In2** (163.0, 77.3-80.2) -> (166.05, 83.2-87.8) -> diagonal x + y = 253.85 to the existing AUD_SCL via (159.2, 94.65).
- Dead end at (153.475, 91.15) trimmed into R209-2.
- AUD_SCL B over void 1.6 -> 0.8 mm. Board void +0.9 mm: slow SWCLK B now over the In2 AUD_SCL.
- R204-1 / R205-1 are now free to the east on F. The RC outputs and C204/C205 still did not route (section 2, group gA).

**gD - U3 long nets (sub-agent): HP_EN closed in a plan that is NOT in RT-15** (void +10.7 mm). See section 5.

**LDO stub:** `t/ldo.plan.json` (seg_del 8156dadd, via_del 0e5aa5c2 / 72c8d22a, In2 04fd585d end -> (133.85, 42.5)).
- `ai-files/fab/draft-rt14/ldo_stub_fix.py BOARD [-o OUT] [--dry-run]` does the same by net and coordinates. It is idempotent: a second run finds "already applied". On RT-15 it reports "already applied".

**New copper:** 46 segments, 191.2 mm, **0 not exact** (gates4). New vias 0.6/0.3; 0.5/0.2 only inside NECK_U4.

## 2. AG13 iteration log

- **gA jack RC (C204, C205, USB_AUDIO_L/R; 3 iterations):**
  1. RT-14 hook re-route rebuilt on the current board (the RT-14 plan collided with the QON via (157.65, 94.6)). New AUD_SCL B x 166 route OK. USB_R / USB_L / BT_R then FAIL with B over GND only: C200/C201 are boxed by the AUD_SCL via (163.025, 77.05) and its F stub.
  2. AUD_SCL fed from the west on In2: FAIL. There is no via site; the VBUS_PD In2 strip x 139-149.3 and BKO_ADC block it.
  3. AUD_SCL over the 5V_CODEC In2 trunk on F, then In2 (D2/D3: DRC 0). USB_R FAIL at 2.28 M nodes; C205 FAIL at 4.9 M nodes.
  - Kept: the hook removal and the In2 AUD_SCL (D3).
- **gB ILIM:** 3 iterations, closed (see 1).
- **gW BCK / AUD_SDA:**
  - Row 1: router FAIL at 130 k nodes, then hand routing, closed.
  - Row 2: router from U7-13 FAIL at 0 nodes, because pin 13 lies directly under the SDATA vertical x 192.345. The reverse probe was stopped.
  - Row 4: router FAIL (28 k nodes) with the In2 AUD_SCL corridor blocked.
  - Row 3: not attempted separately.
- **gD U3 trio:** 3 iterations.
  1. Probes FAIL (0.98 M nodes).
  2. HP_EN routed: 125.7 mm, ratio 1.70, 14 vias, BT_UART_RX re-routed.
  3. Void-aware re-run: same result. HP_SEL_B and AUX_DET analysis only.
- **Void repair (`void2in2r.py` on the full merge):** only 1.8 mm movable, of which 0.9 mm on BT_UART_TX (the RT-13-excluded chain). Not applied.

## 3. Stencil / paste (`ai-files/fab/draft-rt14/paste_fix.py`, report `ai-files/fab/draft-rt14/stencil-report-RT15.md`)

- **Script:** plain python3, text level, idempotent (byte-identical second run), `--dry-run`, `--report`.
  - `--lib DIR` writes the same layouts into the library `.kicad_mod` files.
  - The copper pad only loses `F.Paste`. The windows are unnumbered paste-only pads with deterministic uuids `a57ef1c0...`.
  - Paste is kept >= 0.10 mm from every drill edge. Webs >= 0.26 mm, panes >= 0.5 mm.
- **Coverage per pad:**

| pads | coverage |
|---|---|
| U6.33 / U7.33 | 55 % (3 strips, 0 of 16 vias under paste) |
| U25.21 | 51 % (0 of 8 vias) |
| U11.39 / U11.40 | 60 % |
| U1.56, D6.7, U5.9 | 60 % |
| U10.17 | 56 % |
| Q103.9 | 60 % (2 windows) |

- **Q103.9 flag:** the checker still prints "pane side 0.30" because it counts the drain-pin openings as panes. This is an artefact.
- No pad was skipped. U5.9 gets one 0.95 x 0.60 opening, because the pad is too small for two panes with a 0.25 mm web.
- **Checks:**
  - Pad copper, mask and nets are identical (`stencil/padcmp.py RT-15S RT-15`: paste-only pads 20 -> 34, all else identical).
  - Stencil checker at 0.10 mm: 1093 apertures, 0 below AR 0.66 / aspect 1.5.
- **Library note:** the U6/U7/U25 library layouts assume the board via grid, recorded under `holes_padframe` in the report JSON (`t/RT-15.pastefix.json`).

## 4. Gates (independent of the editing tools; `t/RT-15.gates.txt`, run on RT-15S = RT-15 copper)

| gate | RT-14 | RT-15 |
|---|---|---|
| kicad-cli DRC, project rules (RT-15S / RT-15 + patched lib / RT-15-td + patched lib) | 0 / 12 | **0 / 10** each; RT-15 and RT-15-td vs the unpatched library: 9 lib_footprint_mismatch only |
| connections lost | - | **none** (ILIM_HIZ 1 -> 0, I2S_BCK 2 -> 1, others equal) |
| footprints / pad nets (360 fp, 1194 pads) | - | TP17 moved only (allowed) / **pad_net_diff []** |
| locked copper | - | 3840 of 3875 RT-14 items untouched; 35 removed/changed, all in `t/RT-15.edit.json` (0 unexpected). SHA-256 `2975db7a225356217f0dfcbac0a668df2c0f604bb0797cd852995b2e29fb2778` (`t/RT-15S.gates.json`) |
| new copper exact 0/45/90 | - | 46 seg, 191.2 mm, **0 not exact** |
| route_oct_check | joints < 90: 0, dangling 63, T 25 | joints < 90 **0**, dangling **63**, T 25, exact **100 %** |
| r7 B.Cu over In2 void | 284.5 | **288.9** (cap 290) |
| r7 sensitive B over void | see RT-14 | AUD_SCL 0.8 (-0.8), AUD_SDA 2.2 (-0.5), **I2S_BCK 1.8 (+1.8, via antipads)**, others identical |
| parcheck sensitive / slow pairs | 1 / 11 | **2** / 11 (new: I2S_BCK / I2S_SDATA 3.7 mm at 0.25 mm in the hub knot) |
| GND stitch > 1.5 mm from a sensitive via (r7 gvia) | 4 (USB_AUX_5V 6.3 / 4.9, AUX_L 2.8, USB_DP 1.9) | 9 (+ AUD_SDA 4.2 / 3.9, LRCK 2.1 / 1.8, BCK 1.8) |
| pour check | OK | **OK**; island counts unchanged; VBUS_PD_IN2 590.7 -> 579.3 mm2 (window, trunk neck 4.1 mm), VBUS_PD_IN2_G 81.0 -> 79.0, SYS_IN2 503.7 -> 502.5; GND In2 62 islands (unchanged count) |
| HA8 | 121 | **121** (0 new, 0 tighter) |
| BAT_INT 6 A | 17.3 mV / 104.0 mW | **unchanged** |
| route_oct sentinel / rule-21 sentinel | fires / PASS | **fires (91)** / **PASS** |
| silk_tile_gate (RT-15P -> RT-15S) | - | **ALL PASS** (G1-G6) |
| teardrops (`scripts/td15.sh`) | 1886 (regen) | **1905**, two runs byte-identical (SHA-256 3a881871...), DRC unchanged, no via_dangling |

**regen_final.sh** `RT-15-td.kicad_pcb work-route15/regen-draft --tag DRAFT-RT15 --draft` (`regen-draft/SUMMARY.txt`): **RESULT FAIL (3 failing gates, 2 warnings).**
- FAIL:
  - `drc_violations` 9: the lib mismatches.
  - `drc_unconnected` 10.
  - `lib_footprint_mismatch` 9.
- WARN:
  - `fab_extents`: BM83 silk overhang, by design.
  - `stencil_thermal_pads`: 1 of 11, the Q103 artefact.
- PASS:
  - `teardrops_current`: 1905 = headless regeneration.
  - `zone_fill`: current.
  - `schematic_parity`: 243, 0 new.
  - `rules_file`: proposed-project.kicad_dru c47d6aed.
  - CPL 345, BOM 90 / 318 equal to committed, ERC 240 inherited, STEP.
  - `fab_drill_hits`: PTH 1041 = 70 pads + 971 vias, NPTH 24.
  - Stencil AR, and the three sentinels.

## 5. HP_EN option (`t/gD/gD.plan.json`, board `variant/RT-15H.kicad_pcb`)

- **Route:**
  - U3-47 F under the body to a 0.5/0.2 via (126.1, 72.475).
  - B NW, then the B lane x 117.85 north.
  - Hops at (120-124, 57-61), then F / In2 to (135.8, 40.025).
  - B y 40.025 east, F y 41.175 to x 158.7.
  - F diagonal to (170.5, 52.9), In2 y 56.7-57.7 east, then F into R236-1.
  - 125.7 mm, ratio 1.70, 14 vias.
- BT_UART_RX middle section re-routed (26.6 mm, 2 vias).
- **Gates on its own:** DRC 0, only HP_EN closes, exact 100 %, sensitive +0.
- **Void: +10.7 mm** (HP_EN 11.1 mm). 5.15 mm of it is the unavoidable U3-body escape over the In2 5V_LOGIC trunk. The merged total is **299.6 mm**, against the cap of 290; only about 1.8 mm is repayable.
- Excluded from RT-15 by the brief's cap. **Coordinator decision:** accept `variant/RT-15H.kicad_pcb` (9 unconnected; HP_EN is a slow enable line), or leave HP_EN to the GUI.

## 6. Remaining open connections (10) and GUI actions

Owner routes by hand in 45-degree steps. Rules for all rows:
- Audio 0.3 mm / 0.5 mm clearance. B.Cu only over In2 GND, with a stitch within 1.5 mm.
- I2S 0.6 mm spacing.
- Slow nets may use In2 (rules 11/21, 0.3 mm from islands).

| # | from | to | net | verified cause (RT-15) | suggested layer / corridor |
|---|---|---|---|---|---|
| 1 | U7-13 (192.29, 126.39) | BCK stub (147.15, 93.75) | I2S_BCK | Pin 13 lies directly under the SDATA vertical x 192.345 (router 0 nodes). The hub lane east of R207 is closed by CHG_ENABLE / CHG_SYS_ENABLE B y 93.375 / 94.2 and the VBUS_PD trunk. | Re-space the U7 bundle (verticals at 0.85 mm pitch, diagonals 1.2 apart in x - y): SDATA diagonal x - y = 78.3975 shortened to corner (191.795, 113.3975), vertical x 191.795 straight into pin 14; **BCK** diagonal x - y = 79.6 from (174.15, 94.55), corner (192.65, 113.05), vertical x 192.65, jog to pin 13; LRCK B hop (180.345, 103.2475) -> (181.3525, 103.2475) -> via (182.7, 101.9), F diagonal x - y = 80.8, corner (193.5, 112.7), vertical x 193.5, jog to pin 12; AMP_FAULT_N F (179.545, 99.895) -> (182.095, 99.895), diagonal x - y = 82.2, vertical x 194.295. BCK west part: CHG_ENABLE / CHG_SYS_ENABLE B locally to y 92.6 / 91.8, second VBUS_PD window x 147.4-149.3, y 92.8-94.0 (both zones), B hop from a via at (147.15, 93.75) to (150.6, 93.75) with a stitch, then F y 94.55 parallel to SDATA's y 93.6975 run to (174.15, 94.55). |
| 2 | U7-15 (191.29, 126.39) | TP17-1 (142.30, 108.30) / AUD_SDA net | AUD_SDA | needs row 1; 60 mm through the U7 bundle | Vertical x 190.95 (0.6 mm from AUD_SCL x 190.1 and SDATA x 191.795), diagonal x - y about 76.1 midway between AUD_SCL (73.8) and SDATA (78.4), then F parallel to the AUD_SCL branch at 0.6 mm back to about (167, 104), then west on F (or In2: AUD_SDA is a rule-11 net) to TP17 / its In2 feed via (140.0, 108.59). |
| 3 | U24-23 (150.75, 88.28) | AUD_SDA In2 track (139.05, 83.10) | AUD_SDA | boxed in the BKO_ADC notch (3V3_AUDIO via (150.30, 90.50), U24 LRCK/BCK/DOUT resistor row); F west crosses the VBUS_PD strip only on F | RT-13 recipe: 3V3 via to (150.0, 90.6), its In2 branch to y 90.3; AUD_SDA F x 150.745 down to a via (150.75, 91.3) in the notch, then In2 west is blocked by the VBUS_PD strip (x 139-149.3); use F over the strip at y 91-92 west of the resistor row, or join row 2's AUD_SDA from the notch instead. |
| 4 | R204-1 (156.35, 90.73) | C204-2 (191.14, 40.17) | C204-Pad2 | The AUD_SCL hook is gone (RT-15: AUD_SCL on In2), so R204-1 is free to the east on F. The north field is closed by F walls of slow nets (HP_SEL_A y 68.3 x 158-175, HP_G0 y 69 x 167-175, SWDIO, the HP_G1 diagonal). B hops there cross the In2 3V3_AUDIO branch (x + y = 230.15) or the 5V_CODEC NE leg (x + y = 238.25): void. Router FAIL 4.9 M nodes. | F east along y 89-91 over the In2 AUD_SCL, north at x 167-176 on F. Where the slow walls cross, move those slow runs locally (HP_SEL_A / HP_G0 to B outside BKO_MUX, or In2 where no In2 track crosses), or move the thin 3V3_AUDIO In2 branch (157.35, 72.8)-(169.6, 60.55) to F so audio B hops sit over In2 GND. Then NE to the jack. |
| 5 | R205-1 (156.95, 89.28) | C205-2 (192.89, 42.37) | C205-Pad2 | as 4 | parallel to 4 at 0.6 mm |
| 6 | C201-1 (162.02, 77.65) | USB_AUDIO_R (168.75, 56.43) | USB_AUDIO_R | east exit at y 77.65 blocked by GND via (163.75, 77.6) and by the AUD_SCL via (163.6, 76.725), which is 0.475 mm from the lane (0.5 needed); north field as row 4 (router FAIL 2.28 M nodes) | Move GND via (163.75, 77.6) to about (164.9, 78.4) (re-check the BT_AUDIO_L hop stitch); move the AUD_SCL via 0.1 mm along its diagonal to (163.7, 76.825); then nested bands NE (USB_R innermost, USB_L, BT_R) on F with the slow walls moved as row 4. |
| 7 | C200-1 (162.02, 79.00) | USB_AUDIO_L (174.55, 60.88) | USB_AUDIO_L | as 6 (BT_AUDIO_R T-branch (165.53, 73.77-77.47) to C203 also walls it) | as 6 (delete and re-route the BT_AUDIO_R T-branch as the outer band) |
| 8 | U3-47 (124.75, 70.83) | U10-13 (197.04, 63.78) | HP_EN | routable only at +10.7 mm void | take `t/gD/gD.plan.json` (`variant/RT-15H`) if the void cap may be exceeded; otherwise as that route with the U3 escape moved off the In2 5V_LOGIC trunk |
| 9 | U3-51 (122.33, 73.75) | R235-1 (183.40, 58.70) | HP_SEL_B | boxed by BT_TX_IND F x 123.425, BT_RST_N F x 124.05 and via (124.05, 74.2), BT_FORCE_PWM, the In2 5V_LOGIC trunk (no via west of the pin); FAIL 634 k nodes even with BT_TX_IND/BT_RST_N re-routed | Re-route BT_RST_N (In2 (120.6, 77.65)->(123.6, 74.65), F x 123.6) and BT_TX_IND (F x 124.525) first; U3-51 F east to a via about (124.3, 73.7), B NW parallel to HP_EN at 0.6 mm, B lane x 117.25-118.45, north band; east leg found by router (51.7 mm, F y 40.5, `t/gD/r1/j_s3.log`) |
| 10 | U3-29 (133.68, 74.25) | R242-2 (189.82, 36.30) | AUX_DET | U3 end escapes (via about (132.5, 74.15), B west under the body); R242-2 is sealed inside the AUX_TIPSW loop; moving R242 between J2/J3 misses HA8 by about 0.02 mm | Reshape the AUX_TIPSW loop (same net, audio F): west run to x 188.0, north run to y 34.5; this opens a via site about (189.0, 35.5) for AUX_DET, then B west into the 3V_AO corridor. |

## 7. Before ordering

1. Route the 10 rows above in the GUI (or accept `variant/RT-15H` for HP_EN), on a copy of RT-15 or RT-15-td.
2. Regenerate the teardrops: `regen_final.sh --teardrops`, or `scripts/td15.sh`.
3. Library step (coordinator): `python3 ai-files/fab/draft-rt14/paste_fix.py <final board> --lib DesktopSpeaker-kicad/kicad-library/footprint`. This removes the 9 lib_footprint_mismatch.
4. Run `regen_final.sh` **without --draft**; it must print RESULT PASS.
5. Adopt into `DesktopSpeaker-kicad/` per release-todo section 3 (coordinator).
- `ldo_stub_fix.py` and `paste_fix.py` are idempotent. On RT-15 / RT-15-td they report "already applied".

## 8. Files (`ai-files/pcb/work-route15/`)

- **Results:** `RT-15.kicad_pcb` / `.kicad_pro` / `.kicad_dru` / `.drc.json` / `.geo.json`; `RT-15-td.*`; `RT-15S.*` (pre-paste); `RT-15P.*` (pre-silk); `variant/RT-15H.*`.
- **Plans:** `t/RT-15.plan.json` (merged), `t/gA/gA.plan.json`, `t/gB/gB.plan.json`, `t/gW/gW.plan.json`, `t/gD/gD.plan.json` (variant only), `t/ldo.plan.json`; edit report `t/RT-15.edit.json`.
- **Gates:** `t/RT-15.gates.txt`, `t/RT-15S.gates.json` (locked manifest), `t/RT-15S.check.*`, `t/RT-15S.r7.*`, `t/RT-15S.par.*`, `t/RT-15S.ha8.json`, `t/RT-15S.cp.json`, `t/RT-15.silkgate.json`, `t/RT-15.td.txt`, `t/RT-15.stencil.md/.json`, `t/RT-15.vip.json`, `t/RT-15.pastefix.json`; DRC against the patched library copy `libpf/RT-15*.drc.json`.
- **Draft release run:** `regen-draft/` (SUMMARY.txt; 50 MB, do not commit).
- **Scripts (new):** `assemble15.sh`, `td15.sh`, `zonecut.py`, `segq.py`, `cycleA.sh`, `gates15.sh`, `sentinel21_15.sh`, `hr15.py` (= hr14 reading RT-15.kicad_dru), `render15.sh`. Fab: `ai-files/fab/draft-rt14/paste_fix.py`, `ldo_stub_fix.py`, `stencil-report-RT15.md`.
- **Evidence:** `evidence/rt15-F.png`, `rt15-B.png`, `rt15-bck.png`, `rt15-ilim.png`, `rt14-audscl.png` / `rt15-audscl.png`; sub-agent crops `t/gB/GB3-ilim.png`, `t/gW/GW-bck.png`.
- **Size:** trial boards and folders (gA, gB, gD, gW, td, libpf, stencil, regen-draft: about 0.4 GB). Do not commit them.
