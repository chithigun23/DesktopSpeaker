# Routing R6n (2026-10-10): J7 NRST/SWCLK routed, U4 PGND pin-27 return for 5 A charge

Work copies only (`ai-files/pcb/work-r6/`). `DesktopSpeaker-kicad/` was not touched, nothing was committed, no process was killed, no router ran (no prune risk).

- **Base:** `work-r6/R6n-0.kicad_pcb`, a byte copy of the current project board `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb` (= R6m-final plus the C241 value and synced sourcing fields; copper identical).
- **Final board:** `work-r6/R6n-final.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`, `.drc.json`, `.open2.json`, `.isl.json`, `.bends.json`, `.strict.json`, `.sliver.json`, `.pour.json`).
- **Rules:** `R6n.kicad_pro` = `R6m-final.kicad_pro`; `R6n.kicad_dru` = the project `.kicad_dru` = `R6m-final.kicad_dru` (all `cmp` identical, also the final copies). No rule, rule area, netclass or footprint keepout was added, relaxed or moved.
- **Renders:** `ai-files/pcb/route-r6n-top.png` (F.Cu), `route-r6n-bottom.png`, `route-r6n-in2.png`.
- **Specs and logs (`work-r6/r6n/`):** `j2.json` (J7), `p1.json`, `p3.json`, `p4.json` (PGND), `eval0.txt` (R6n-0 gates), `final.gates.txt`, `pgnd.txt` + `pgnd_R6n-0.json` / `pgnd_R6n-final.json` (return-current solver), `u4clr.txt` (clearances of the re-routed U4 signals). Intermediate boards deleted.

## Gates (R6n-0 → R6n-final)

| Gate | Before | After |
|---|---|---|
| Open edges (fragment-aware, `route_p2_open2.py all`) | 2 (J7 NRST, SWCLK) | **0** |
| DRC clearance / shorts / dangling / isolated / width / annular / hole | 0 | **0** |
| DRC USB items | 3 skew, 1 uncoupled | unchanged; USB copper identical (52 items, `r6l/usbcmp.py`) |
| DRC silk / lib | 36 | 36 |
| Strict DRC (every track in 1 mm pieces, `--all-track-errors`) | 3 inherited items | **the same 3**: 5V_LOGIC–SYS_RAW In2 0.3991 mm; U24 XI / VINR2 0.2 mm escapes; USB gap pieces at J1 |
| Power connectivity (union of split pours per net/layer, `route_r6l_union.py`) | 1 piece each | unchanged, same zone-union / copper-piece counts for every net |
| Island continuity (`route_r6h_isl.py` vs R6n-0) | 1 outline per island | 1 outline per island. Only change: SYS_IN2 502.41 → 500.54 mm² (new GND vias under U4), still 1 piece |
| Foreign non-GND vias in In2 islands | 32 | **32**. The CHG_INT, CTRL_SCL, BATP and QON vias moved inside SYS_IN2 (4 removed, 4 added at new spots) |
| In2 slow signals to an island outline | ≥ 0.32 mm | ≥ 0.32 mm, same list |
| AUDIO / I2S / USB / clock copper on In2 | none | none. The only In2 edit is a 1.0 mm 3V_AO trunk piece |
| Corner hits (`route_r6i_bends.py`) | 7 | **5**, all inherited. The two 3V_AO In2 corner hits at 169.4–170.1, 99.65 are gone with the removed via |
| Via centre in SMD pad | 3 | **3** (R10.2, R224.1, C215.1). **No via in any J7 pad** |
| Net changes by uuid (`route_r6l_netcmp.py`) | – | 0 net changes, 0 pad-net changes (41 items removed, 50 added) |
| GND fill pieces / floating (`route_r6m_gndfloat.py`) | F 5 / In1 1 / In2 116 / B 5, 0 floating | the same, **0 floating**. B GND 15196.2 → 15205.5 mm² (the old CHG_INT diagonal no longer splits the B GND under the U4 body) |
| Narrow copper in the net copper union (`route_r6m_sliver.py`, 0.15 / 0.12 mm) | 0 | **0** (per-zone residues 46, the inherited edge strips) |
| Power pour area | – | unchanged except SYS_RAW In2 −1.9 mm² |
| Vias | 958 | 962 (GND +3, signal +1) |

## 1. J7 (decision A): NRST and SWCLK routed with no via in pad and no move

Via-in-pad turned out not to be the simplest *legal* route. The TC2030 footprint carries an F.Cu rule area between its six pad centres (169.495–172.035 × 94.67–95.94) that forbids vias, zones and footprints. A test with 0.6/0.3 vias centred in pads 3 and 4 gave 2 `items_not_allowed` (keepout area of J7). The board's minimum via outside a neck area is also 0.6/0.3, so the 0.5/0.2 or 0.45/0.2 vias suggested would break `via_std` as well. That version was discarded.

Instead every inner pad leaves on F.Cu through one of the gaps between the NPTH holes. Each gap is 0.76–0.86 mm wide and passes one 0.2–0.3 mm track at the 0.25 mm hole clearance:

| Pad | Net | Gap used | Route | Clearance to the hole edges |
|---|---|---|---|---|
| 2 | SWDIO | top-left leg hole / left alignment hole, y 94.381 | F 0.2 mm west, then F 0.25 mm north at x 166.6 to the J6 SWDIO node (167.05, 85.6) | 0.33 / 0.33 mm |
| 1 | 3V_AO | left alignment hole / bottom-left leg hole, y 96.229 | F 0.3 mm west to a new 0.6/0.3 via on the In2 3V_AO trunk (164.275, 96.839) | 0.28 / 0.28 mm |
| 4 | SWCLK | between the two top leg holes, x 169.8125 | F 0.2 mm north → via 0.6/0.3 (169.5, 88.3) → B 0.25 mm → via 0.6/0.3 (169.8125, 84.9) → F 0.25 mm onto the SWCLK track (split at 169.8125, 82.4895). The B hop crosses the SWDIO and NRST F diagonals. | 0.30 / 0.30 mm |
| 3 | NRST | between the two bottom leg holes, x 169.8125 | F 0.2 mm south to y 99.4, east to 173.636, 45° to the existing NRST via (177.4, 95.636) on the TP19 / U3 side | 0.30 / 0.30 mm |
| 5 | GND | right alignment holes (unchanged) | – | – |

**Neighbour changes:**
- SWDIO: removed the via (169.7, 93.95), its F stub and the four B segments under J7. The SWDIO via (174.35, 92.45) still joins the J6 F diagonal to the U3 B track.
- 3V_AO: removed the J7.1 F track and via (169.813, 99.75). On In2, the two 1.2 mm stubs around that via were replaced by one 1.0 mm segment (169.4–170.1, y 99.65).

**What did not change:**
- J7 is not moved. Its holes, legs and NPTH are untouched.
- No copper sits inside the J7 keepout.
- B.Cu under J7 now holds only GND fill, which leaves room for the clip legs.
- Spring-pin pads stay flat (no via holes).

Tracks are 0.2 mm in the gaps (Default class, DRC minimum 0.2) and 0.25 mm elsewhere.

## 2. PGND pin 27 (decision B): body via field for 5 A charge

### Changes (`p1.json`, `p3.json`, `p4.json`)

**Signal vias moved out of the body centre**, all 0.5/0.2 (neck minimum annulus 0.15):

| Net | Old via | New via | New escape | B lane |
|---|---|---|---|---|
| CTRL_SCL | 151.7, 122.0 | **152.17, 123.45** | pin 14, F 0.6 mm stub | west along y 122.86 to the old lane at 148.535 |
| QON | 151.2, 122.85 | **151.37, 123.42** | pin 12, F 0.67 mm stub | west via (150.6, 123.3) to 148.6, 123.25 |
| BATP | 152.55, 122.985 | **152.6, 122.85** | – | to (152.8, 123.25), then the old lane to 153.1, 125.2 |
| CHG_INT | 152.55, 121.785 | **152.72, 122.15** | pin 21, F stub with a 45° end | see below |

**CHG_INT B lane re-routed.** It used to cross the body diagonally under pin 27 to x 150.5. It now runs north at x 152.84 (121.9 → 120.75), then 45° to x 151.55 and north to its old path at 116.25. Clearances:

| To | Clearance |
|---|---|
| REGN B | 0.24 mm |
| SYS via (152.62, 119.4) | 0.45 mm |
| SW1 / SW2 | ≥ 1.08 mm |

**CTRL_SDA B:** one vertex moved from (151.5, 124.0) to (151.55, 124.06), so the QON via clears it by 0.22 mm.

**REGN B narrowed to 0.5 mm** over 3.2 mm: segments (153.433, 120.4)–(153.483, 121.617), was 0.7, and (153.483, 121.617)–(153.567, 123.633), was 0.8.
- These were overspec widenings. REGN's class minimum is 0.4 mm and it carries gate-drive current only.
- The narrowing gives the CHG_INT via and lane their 0.2 mm.

**GND_U4_PGND_F outline enlarged** to the whole body interior: x 150.2–152.55, y 121.2–122.95. The south bridge to pads 10/11 is unchanged, as is the 0.3 mm tongue onto pin 27.
- Fill area 2.57 → 4.54 mm², 1 piece.
- The two 0.5/0.2 GND vias (150.65, 121.65) / (151.2, 121.5) and their GND tracks were removed.

**New GND vias in the body** (tented front and back by board setting; none is in a pad):

| Via | Size | Role |
|---|---|---|
| 150.98, 121.5 | 0.6/0.3 | ring around the tongue exit |
| 152.2, 121.58 | 0.6/0.3 | ring around the tongue exit |
| 151.57, 121.9 | **0.8/0.4** | ring around the tongue exit |
| 150.5, 121.9 | 0.6/0.3 | second row |
| 151.0, 122.25 | 0.6/0.3 | second row |

The bridge via 0.6/0.3 (150.77, 124.65) stays. Hole-to-hole spacing is ≥ 0.31 mm, and the vias sit ≥ 0.22 mm from the pin ends.

**B.Cu:** the B GND under the U4 body is now one continuous area (+9 mm²), because the CHG_INT lane no longer cuts it diagonally.

**Not used (not needed):** moving C311/C312, via-in-pad on pin 27 (its pad is 0.2 mm wide), and DRC exceptions.

### Return-current model (`route_r6n_pgnd.py`)

The prior reports used a lumped model: full 1.6 mm barrels (0.3 mm via 1.37 mΩ, 0.4 mm 1.04 mΩ, 0.2 mm 2.0 mΩ) in parallel, with the bridge path at about 3.1 mΩ. It ignores copper spreading, so it splits the current almost evenly.

The new solver is a 2D resistive grid of the GND F.Cu copper connected to pin 27, with 0.02 mm cells and 35 µm copper. It injects the current over the pin-27 pad, and each GND via conducts through its F→In1 barrel (0.21 mm prepreg, 20 µm plating). It has two variants:
- **ideal:** In1 is an ideal plane. This is the worst case for crowding.
- **plane:** In1 is a 15.2 µm grid with its antipads, over 27 × 30 mm, with the edge at 0 V.

B.Cu is ignored in both.

Ratings:
- **Project rule:** 1 A per 0.3 mm of drill, so a 0.2 mm drill is rated 0.67 A, 0.3 mm 1.0 A and 0.4 mm 1.33 A.
- **IPC-2221 external at 15 K** (barrel π(d+t)t): 0.2 mm 1.46 A, 0.3 mm 1.91 A, 0.4 mm 2.33 A.

### Capacity, before and after (return current 4.5 A ≈ 5 A charge; currents scale linearly)

| Quantity | R6n-0 (= R6m): 2 × 0.5/0.2 + bridge | R6n-final: 4 × 0.6/0.3 + 1 × 0.8/0.4 + bridge |
|---|---|---|
| Lumped (prior-report) model, A per via at 4.5 A | 1.66 A per 0.2 mm via (**2.5 × rule**, 1.14 × IPC) | **0.78 A per 0.3 mm via (0.78 × rule)**, 1.03 A on the 0.4 mm via (0.77 × rule), bridge 0.34 A |
| 2D ideal-plane, worst via at 4.5 A | 3.26 A on 0.5/0.2 (4.9 × rule, 2.2 × IPC) | **1.22 A** on 0.6/0.3 (152.2, 121.58) (1.22 × rule, **0.64 × IPC**); 1.54 A on 0.8/0.4 (1.15 × rule, 0.66 × IPC) |
| 2D In1-sheet, worst via at 4.5 A | 2.50 A (3.75 × rule, 1.7 × IPC) | **1.26 A** (1.26 × rule, **0.66 × IPC**); 0.8/0.4 0.79 A |
| Per-via currents at 4.5 A, ideal / sheet | 3.26 / 2.50, 1.13 / 1.26, bridge 0.11 / 0.57 | 1.54 / 0.79 (0.8), 1.22 / 1.26, 1.12 / 0.98, 0.33 / 0.27, 0.27 / 0.63, bridge 0.02 / 0.41 |
| Return current where the worst via reaches the **project rule** | lumped 1.9 A, ideal 0.9 A, sheet 1.2 A | lumped **5.8 A**, ideal **3.7 A**, sheet **3.6 A** |
| Return current where the worst via reaches **IPC 15 K** | lumped 4.0 A, ideal 2.0 A, sheet 2.6 A | lumped 11 A, ideal **6.8 A**, sheet **6.8 A** |
| Worst via at 2.7 A (3 A charge from 9 V), ideal / sheet | 1.96 / 1.50 A | 0.73 / 0.75 A (within the rule) |
| Worst via at 5.0 A return, ideal / sheet | 3.62 / 2.78 A | 1.36 / 1.40 A (IPC 1.91 A) |
| Pin-27 land to In1 (ideal) / to the In1 box edge (sheet) | 1.65 / 2.54 mΩ | 1.37 / 2.09 mΩ |

**Result at 5 A charge:**
- Every via carries at most 1.26 A on a 0.3 mm barrel (1.54 A on the 0.4 mm), at least 1.5 × below the IPC 15 K rating.
- In the prior report's lumped model, every via is inside the project rule (0.78 A per 0.3 mm via).

**Target not fully met: ≤ 0.7 A per via (the project rule) under the conservative 2D models.**
- The worst via reaches its 1.0 A rule at about 3.6 A return, i.e. about 4 A charge.
- The whole return enters the field through the 0.3 mm tongue at the end of the 0.2 mm pin. The pin sits between the SW1/SW2 pads, with 0.2 mm to each.
- So the first ring of three vias (≤ 0.65 mm from the tongue) carries about 85 % (ideal model).

**Layouts tried with the solver (ideal model, worst load × rule):**

| Layout | Worst load |
|---|---|
| 6 × 0.6/0.3 grid at 0.63 pitch | 2.28 |
| Symmetric grid | 1.77 |
| Triangular ring | 1.40 |
| 2 × 0.8/0.4 | 1.45 |
| Ring with a 0.8/0.4 centre | 1.18–1.27 (the final layout is 1.22) |

No further ring positions exist. They are bounded by:
- the pin ends (0.2 mm);
- the relocated CHG_INT / BATP / QON / SCL vias;
- the 0.3 mm hole-to-hole minimum;
- the SCL B lane, which has 0.21 mm to the second-row via.

Barrel loss in the worst via is about 0.3 mW (0.19 mΩ F→In1). The total PGND path loss is about 28 mW at 4.5 A.

**Decision for the user:**
- (a) Accept by IPC: 1.5 × margin at 5 A charge on the worst-case model, and inside the rule on the lumped model. Or
- (b) Cap firmware ICHG at about 4 A to stay inside the 1 A/via rule on the conservative model.

**Out of scope but relevant at 5 A:** the SW1/SW2 pin escapes are unchanged at 0.36 / 0.30 mm for about 0.9 mm (pitch-limited, R6l), and BAT_INT is 3.1 mm (6.5 A at 15 K).

## Exceptions and items (complete list)

**New in R6n, all DRC-legal:**
- PGND target ≤ 0.7 A/via (project rule) not met in the 2D models: 1.22–1.26 A worst at 4.5 A return. It is met in the lumped model, and IPC margin is ≥ 1.5 × (see 2).
- GND vias under the U4 body: 5 in the body pour, including one 0.8/0.4. They are tented by board setting and none is in a pad.
- REGN B narrowed from 0.7/0.8 to 0.5 mm over 3.2 mm (class minimum 0.4).
- Clearances at or near the 0.2 mm NECK_U4 minimum on the moved items:

  | Item | Clearance |
  |---|---|
  | CHG_INT via to pin 20 (PROG) / BAT_INT pad | 0.20 mm |
  | CTRL_SCL F to CE_N / CTRL_SDA pins | 0.20 mm (pin pitch) |
  | CTRL_SCL B to the QON via | 0.21 mm |
  | CTRL_SCL B to the second-row GND via | ≈ 0.21 mm |
  | CHG_INT to BATP | 0.21 mm |
  | CTRL_SDA B to QON | 0.22 mm |
  | CTRL_SCL to BATP | 0.24 mm |

  All are inside NECK_U4, in the same class as the inherited U4 escapes.
- J7 F escapes run 0.28–0.33 mm from the NPTH hole edges (rule 0.25).
- No via-in-pad at J7. Via-in-pad count stays 3.

**Inherited, unchanged:**
- USB 3 skew + 17.3 mm uncoupled (waiver item).
- 3 via-in-pad (R10.2, R224.1, C215.1).
- 3 strict-DRC items.
- 5 corner hits.
- 46 per-zone companion edge strips (0 in the copper union).
- SYS_COL_B tip about 0.18 mm.
- m-L4 (U15 L1 0.206 mm, U14 L2 0.777 mm).
- I2S_LRCK via to VBUS_PD_IN2_G 0.40 mm.
- 8 audio vias without a GND via.
- Teardrops not generated (GUI).
- 244 schematic-parity items until "Update PCB from Schematic".

## Helpers (new, `ai-files/helpers/`)

| Helper | Purpose |
|---|---|
| `route_r6n_eval.sh` | R6n gates (= R6m gates with R6n rules). Islands and corner rule are compared with `ISLREF` (default R6n-0) |
| `route_r6n_pgnd.py` | U4 PGND return-current solver: 2D F.Cu grid, ideal-In1 and In1-sheet models, per-via current versus the project rule and IPC. `PGND_MODEL=ideal` runs the fast model only |

**Reproduction:**
1. `route_r6l_step.sh R6n-0 R6n-1 r6n/j2.json`
2. `route_r6l_step.sh R6n-1 R6n-2 r6n/p1.json`
3. `route_r6l_step.sh R6n-2 R6n-3 r6n/p3.json`
4. `route_r6l_step.sh R6n-3 R6n-4 r6n/p4.json`
5. Copy R6n-4 → R6n-final, then run `route_r6n_eval.sh R6n-final R6n-0 full` and `route_r6n_pgnd.py R6n-final.kicad_pcb 4.5`.
