# Adopt R6m into the project, SW100 library fix, schematic fixes (2026-10-10)

Scope: review items B1, M1, M6 and the minors on CHG_VIO_3V0, the TPS61088 datasheet and the MCU page render
(`reports/project-review-fable.md`). KiCad 10.0.6 Flatpak CLI (`helpers/bin/kicad-cli`). Not committed. HANDOVER.md, the BOM
CSV/XLSX and J7 are untouched. No USB waiver was added. Backups of every changed file are in `ai-files/backups/*.pre-adopt`
(board, dru, pro, prl, root sch, Headphone_Aux, MCU, Battery_Charger, the SW100 `.kicad_mod`, the preview PDF).

## 1. Board and rules adopted (B1)

- `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb` is now a copy of `pcb/work-r6/R6m-final.kicad_pcb`. The only difference is one
  line: the C241 footprint `Value` changes from 1uF to 2.2uF (hidden F.Fab text, see sec. 3). Copper, zones and placement are
  byte-identical. Grep counts: 360 footprints, 2586 segments, 30 arcs. The review gives 385 footprints; that figure could not be
  reproduced (R6m-final itself has 360).
- `DesktopSpeaker.kicad_dru` is a byte copy of `R6m-final.kicad_dru` (sha1 d77f2c8a...).
- `DesktopSpeaker.kicad_pro` is kept, with **one change: the `{"netclass": "SIGNAL", "pattern": "*"}` catch-all is removed**.
  The review's claim that the catch-all is harmless is wrong:
  - With it in place, DRC on the adopted board gives **75 extra clearance errors**. These come from `switch_sensitive`
    (1.0 mm) and `vbus_clear` (0.4 mm), because nets that are Default in R6m (for example Net-(U7-BST_B+), /PD_SINK_EN) become
    SIGNAL. Those rules match `NetClass == 'SIGNAL'`, and `in2_slow_island` matches `'Default'`.
  - `reports/pcb-routing-r6a.md` already records that R6a removed this catch-all as a bug: KiCad 10 builds composite class
    names, so `NetClass == 'X'` rules misfire.
  - After the removal, the project netclasses match R6m for routing: the same 15 classes with identical values and the same 111
    patterns in the same order. Default and SIGNAL values are identical. No `design_settings` differences except
    `teardrop_parameters.td_curve_segcount` (5 in the project, 1 in R6m). That was kept at 5 per the review minor; there are no
    teardrops yet.
  - The ERC exclusion (U11 pin 38 VIN_3V3) is intact and still matches (sec. 4).
- 3D models: 41 distinct `${KIPRJMOD}/kicad-library/3d/*.step` paths, all resolve. Footprints with no model at all:
  - TestPoint 5015 x22 and 5010-5014 x5
  - MountingHole_3.2mm_M3_PTH_GND x11
  - JST_B2P_VH x3
  - KCD1-201 rocker, TC2030 J7, TE 1977066-1 SW100, Molex 43650-0300 J5 (one each)
  - Logo
  These were not changed. Missing connector, switch and test-point models only affect the 3D/enclosure review.

## 2. SW100 library footprint (M6)

`kicad-library/footprint/TE_1977066-1_Tact_RA_SMD.kicad_mod`: both pad-1 instances changed from 0.9 x 1.8 at y 0 to
**0.9 x 1.7 at y -0.05**, matching the board copy. The board footprint is unchanged. DRC `lib_footprint_mismatch` is now 0
(was 1). The land pattern is still the DRAFT from the TE drawing: the one-time check against
`datasheets/TE_1977066-1_datasheet.pdf` that the review asked for was not done here.

## 3. Schematic fixes

- **M1, U10 VDD capacitor: the brief's "C242" is C241.** C242 no longer exists (it was removed in the low-risk cuts). The
  netlist shows:
  - C241 sits on /3V3_AUDIO to U10 pin 14 (VDD).
  - C240 is the INR- input coupling cap (HP_R to U10 pin 4) and must stay 1 uF.

  Changes on C241 (`Headphone_Aux.kicad_sch`):
  - Value 1uF -> 2.2uF
  - MPN CL05A105KO5NNNC -> CL05A225KP5NNNC
  - LCSC C29266 -> empty (C243/C244 with the same MPN also have none; the BOM row says "LCSC code open")
  - Same 0402 HandSolder footprint, ref kept

  The PCB C241 value field was changed to match.
  **BOM owner action:** move C241 from the CL05A105KO5NNNC row (now 32 pcs) to the CL05A225KP5NNNC row (now 9 pcs).
- **CHG_VIO_3V0: not dangling, so no change.** Inside Battery_Charger the port at (38.1, 166.37) is wired to R106 pin 1, the
  CHG_INT 10k pull-up. On the root, the sheet pin (166.37, 195.58) is wired to the `3V_AO` label. The netlist confirms R106.1
  is on /3V_AO. The name is a misnomer (BQ25792 has no VIO; it is the INT pull-up rail). Renaming was not done, to avoid churn.
  The "dangling, nothing behind it" statements in `plan.md` line 322 and `HANDOVER.md` line 479 are stale; the coordinator
  should correct them.
- **Datasheet links (report only):**
  - `TPS61088RHLR` (3 uses) points to `${KIPRJMOD}/../ai-files/datasheets/TPS61088_zh.pdf`, which is missing (only
    `tps61088-layout-excerpt.txt` exists).
  - A full scan of local links found one more missing target: `PESD5V0S2BT.pdf`.
- **MCU page 7 cosmetics (fixed):**
  - C162 ref/value text moved from y 120.65/123.19 to 121.92/124.46. The ref overlapped the HP_EN hierarchical label.
  - SW102 ref/value text moved from x 90.17 to 88.9. "SW102" ran into the BT_UART_RX label.
  - The supply note said "VREF+ 100nF + 1uF", but C163/C164 were cut (`reports/bom-reduction-audit.md` decision D). It now says
    "VREF+ tied to VDDA, VREFBUF off (no separate VREF+ caps)".
  - No symbol, wire or label was moved.
  - **Coordinator action:** `reports/mcu-pin-allocation.md` line 8 still lists C163/C164.
- **MCU page 7, reported and not fixed (layout, not pure cosmetics):**
  - About a quarter of the page height above the content is empty (A4); compacting it would need moving everything.
  - Outputs HP_EN and 5V_LOGIC_EN sit as left-side hierarchical labels near pins 47/18. That is legible, but inconsistent with
    the outputs-right convention used for the other outputs.
  - SWDIO/SWCLK/NRST reach J6/J7/TP19 through matching remote labels, which the style rules accept.
  - No wire crossings, ambiguous junctions or unlabelled stubs were seen. U3 text is centred below the body; passive text is on
    the right.

## 4. Verification

The DRC, ERC and netlist checks ran on a byte-identical copy of the project in the session scratchpad, so kicad-cli wrote
nothing into the project. The sha1 of every `.kicad_sch/.kicad_pcb/.kicad_pro/.kicad_dru/.kicad_prl` was compared before each
run. The preview was exported from the project itself so its datasheet hyperlinks resolve to the project path.

| Gate | Result | Expected |
|---|---|---|
| ERC (default severities) | 0 | 0 |
| ERC `--severity-all --severity-exclusions` | 1, excluded: power_pin_not_driven U11 pin 38 VIN_3V3 | exclusion intact |
| Netlist vs pre-change (`helpers/netlist_equiv.py`) | 348 comps / 311 nets / 1130 pins; nets and pins identical; only C241 fields differ; MCU text edits identical | as intended |
| DRC `--schematic-parity --severity-all` errors | 3 skew_out_of_range + 1 diff_pair_uncoupled (usb_diff) | 4 USB |
| DRC warnings | 20 silk_over_copper, 8 silk_edge_clearance, 8 silk_overlap; lib_footprint_mismatch 0 | silk only |
| DRC unconnected | 2: J7 pad 3 /MCU/NRST, J7 pad 4 /MCU/SWCLK | 2 J7 |
| Parity | 244: 199 field, 30 attribute, 15 net_conflict (6 U11 merged-pad "no pad found" + 9 `{slash}` encoding); set identical to the pre-change baseline | 15 net_conflict, no new pad-net conflicts |
| Open edges (`route_p2_open2.py ... all`) | 2: /MCU/NRST 1, /MCU/SWCLK 1; power classes 0 | 2 |

The 244 parity items still need the GUI "Update PCB from Schematic" (fields, TP exclude-from-BOM, R256 DNP, TP13/TP14 values,
net-name encoding), as in B1.

Evidence:
- `reports/adopt-r6m-drc.json`, `reports/adopt-r6m-erc.json`, `reports/adopt-r6m-open2.json`
- `previews/adopt-r6m-MCU-p7.png`, `previews/adopt-r6m-MCU-textfix.png`, `previews/adopt-r6m-Headphone_Aux-C241.png`
- `DesktopSpeaker-preview.pdf` refreshed (12 pages)

## Changed files

- `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb`, `DesktopSpeaker.kicad_dru`, `DesktopSpeaker.kicad_pro` (catch-all removed)
- `DesktopSpeaker-kicad/Headphone_Aux.kicad_sch` (C241)
- `DesktopSpeaker-kicad/MCU.kicad_sch` (text only)
- `DesktopSpeaker-kicad/kicad-library/footprint/TE_1977066-1_Tact_RA_SMD.kicad_mod`
- `ai-files/DesktopSpeaker-preview.pdf`, this report, and the evidence files above
