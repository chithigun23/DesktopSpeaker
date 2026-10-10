# Routing R6m (2026-10-09): R6l review B1 slivers, m-L1 PGND, m-L2 / m-L3 clearances

Work copies only (`ai-files/pcb/work-r6/`). `DesktopSpeaker-kicad/` was not touched, nothing was committed, no process was killed, no router ran (no prune risk), no sub-agents.

- **Base:** `work-r6/R6l-final.kicad_pcb` (review `pcb-routing-r6l-fable-review.md`).
- **Final board:** `work-r6/R6m-final.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`, `.drc.json`, `.open2.json`, `.isl.json`, `.bends.json`; also `.strict.json`, `.sliver.json`, `.pour.json`).
- **Rules:** `R6m.kicad_pro` / `R6m.kicad_dru` and the final `.kicad_pro` / `.kicad_dru` are byte copies of the R6l (= R6k) files (`cmp`). No rule, rule area or netclass was added, relaxed or moved.
- **Renders:** `ai-files/pcb/route-r6m-top.png` (F.Cu), `route-r6m-bottom.png`, `route-r6m-in2.png`.
- **Specs and logs:** `work-r6/r6m/`: `m1.json` (zone fixes), `m2.json` (PGND, REGN, 5V_CODEC), `eval0.txt` (R6l-final gates), `final.gates.txt`, `sliver0.json`, `strict0.json`, `pour0.json` / `pour_final.json`. Intermediate boards deleted.

## Gates (R6l-final → R6m-final)

| Gate | Before | After |
|---|---|---|
| Open edges (fragment-aware) | 2 (J7 NRST/SWCLK) | **2**, the same two |
| DRC clearance / shorts / dangling / isolated / width | 0 | **0** |
| DRC USB items | 3 skew, 1 uncoupled | unchanged; USB copper identical (52 items, `r6l/usbcmp.py`) |
| DRC silk / lib | 37 | 37 |
| Strict DRC (all tracks split into 1 mm pieces, `--all-track-errors`) | 3 inherited items | **the same 3**: 5V_LOGIC–SYS_RAW In2 0.3991 mm; U24 XI / VINR2 0.2 mm escapes; USB gap pieces at J1. (The split copy's USB skew/uncoupled markers sit on different 1 mm pieces; the unsplit USB copper is identical.) |
| Power connectivity (union of split pours per net/layer) | 1 piece each | 1 piece each, same zone-union and copper-piece counts for every net |
| Island continuity | 1 outline per island | 1 outline per original island. SYS_IN2 502.66 → 502.41 mm², 1 piece |
| Foreign non-GND vias in In2 islands | 32 | 32 (same list) |
| In2 slow signals to an island outline | ≥ 0.32 mm | ≥ 0.32 mm. PDCTRL_SCL 0.36 → 0.58, BT_TX_IND 0.35 → 0.58, BT_MFB 0.53 → 0.58 |
| AUDIO / I2S / USB / clock copper on In2 | none | none |
| Corner hits (`route_r6i_bends.py`) | 7 | **7**, all inherited |
| Via centre in SMD pad | 3 | **3** (R10.2, R224.1, C215.1) |
| Net changes by uuid (`route_r6l_netcmp.py`) | – | 0. Removed: 1 REGN segment, zone USB_VBUS_IN2_G. Added: 2 REGN segments, 1 GND via |
| GND fill pieces, floating | F 5 / In1 1 / In2 121 / B 5, 0 floating | F 5 / In1 1 / **In2 116** / B 5, **0 floating** (`route_r6m_gndfloat.py`) |
| Narrow copper in the net copper union, < 0.15 mm outer / < 0.12 mm inner | 0 | **0** (`route_r6m_sliver.py`) |
| Vias | 957 | 958 (GND +1) |

## 1. B1 companion-pour slivers

**Edits (`m1.json`, `route_r6m_zfix.py`):**
- Deleted `USB_VBUS_IN2_G`.
- `SYS_U4CAP_F_G`: removed the outline area at x < 160.7, y < 116.9. The 6 mm × 0.12 mm strip is gone. The main piece (x 160.8–165.2) is unchanged. 2 pieces → 1, 12.87 → 12.11 mm².
- `PVDD_BOOST_F_G`: removed the 0.065 mm² piece (156.4–156.6, 153.6–154.1) and the 3.5 × 0.22 mm strip (y 148.6–148.95). 4 pieces → 2, 55.42 → 54.56 mm².
  - Kept: the 47.28 mm² main piece and the 7.28 mm² piece at 157.0–160.8 × 144.4–146.9. That piece is clean (opening test loses 0.005 mm²) and edge-attached to PVDD_BOOST_F.
- Min thickness 0.3 mm on all 12 remaining `*_G` zones (was 0.2), refilled.
- `PVDD_U7R_F_G`: removed a 0.01 × 0.06 mm zero-area fragment that appeared at (200.15, 129.7) after the 0.3 mm refill. It came from an outline spike; a small box was subtracted there.

**Narrow-copper scan of every zone fill on all four layers (`route_r6m_sliver.py`).** The scan is a morphological opening: deflate by W/2, inflate by W/2 with round corners, then take the difference. Each D piece (difference piece) of at least 0.003 mm² that overlaps a zone fill is reported.

| Scan | R6l-final | R6m-final |
|---|---|---|
| Net copper union (all zone fills of the net + its tracks, pads, vias), W = 0.15 outer / 0.12 inner | **0** | **0** |
| Same, stricter W = 0.20 / 0.15 | 1 | 1, the same: SYS_COL_B (B) tip at 159.0–159.2 × 124.17–124.35, about 0.18 mm wide, inherited |
| Each zone fill on its own, W = 0.15 / 0.12 | 68 | 46 |

**The 46 per-zone residues are not copper slivers.** They are 0.02–0.15 mm edge strips of a companion fill (VBUS_PD_IN2_G 18, SYS_BOOST_F_G 7, PVDD_IN2_G 5, PMID_F_G 4, …). Each lies flush against its higher-priority parent's fill.
- Probes at 0.01 mm show the companion copper starting exactly where the parent's ends.
- In the copper union they only widen the parent, which is why the union scan finds 0.
- This also applies to the strips B1 named. The USB_VBUS tongues at x 153.50–153.65 continue the USB_VBUS_IN2 edge at x 153.49. The SYS strip at y 116.68–116.75 continues SYS_U4CAP_F from y 116.76. They are removed anyway as instructed.
- The 0.3 mm minimum thickness does not remove these strips. They are what remains after the same-net, higher-priority parent fill is knocked out of the companion.

**Pour area per net** (filled, all zones of the net, `route_r6l_pourarea.py`):

| Net | Layer | R6l-final mm² | R6m-final mm² | Δ |
|---|---|---|---|---|
| USB_VBUS | In2 | 325.8 | 289.1 | −36.7 (USB_VBUS_IN2_G deleted) |
| SYS_RAW | F | 430.1 | 429.1 | −1.0 (strip, min thickness) |
| PVDD_AMP | F | 173.4 | 172.5 | −0.9 (two pieces, min thickness) |
| VBUS_PD | In2 | 680.2 | 679.5 | −0.7 (min thickness) |
| SYS_RAW | In2 | 502.7 | 502.4 | −0.3 (new GND via clearance, see 2) |
| PVDD_AMP | In2 | 2761.5 | 2761.4 | −0.1 |
| all others | | | | < 0.05 |
| **Total power pour** | | **6747.5** | **6707.8** | **−39.7** |

- **Overspec gain kept:** against R6l-0 (5839.8 mm²) it is +868.0 mm², down from +907.7, so 96 % is kept.
- **GND recovered:** In2 GND filler 7780.3 → 7846.9 mm² (+66.6) and 121 → 116 pieces. F GND 90.1 → 92.7 mm².
- **Unchanged:** B GND 15196.2 mm² and In1 16519.8 mm².

## 2. m-L1: PGND pin 27

**F bridge:** the GND_U4_PGND_F outline was extended south, between pins 7/8 and the QON via, to the tops of pads 10/11 (ACDRV1/2, tied to GND).
- The fill is at least 0.5 mm wide: 0.55 mm at y 122.85 west of the QON via and about 0.6 mm at the pad tops. It is 0.2 mm (the U4 neck rule) from pads 7/8, the QON via, the QON track and pad 9.
- Fill area 1.57 → 2.57 mm².
- The outline keeps x ≥ 150.45 below y 123.25, so VBUS_U4B_F loses only 0.03 mm².

**Third via, on the bridge path:** a 0.6/0.3 GND via at (150.77, 124.65). It sits on the two pad-10/11 GND tracks just south of the pads, outside every pad (its centre is not in C313.2).

| Neighbour | Layer | Clearance |
|---|---|---|
| QON pad 12 | F | 0.28–0.29 mm |
| C313.1 (VBUS_PD) | F | 0.28–0.29 mm |
| CTRL_SDA | B | 0.36–0.37 mm |

The neck rule at U4 is 0.2 mm. Distances were measured by shape collision at 0.01 mm steps.

- In2: it lands on the GND filler.
- It cuts 0.25 mm² from the south-west edge of SYS_IN2 (y 124.1–124.5). The island stays 1 piece and is not counted as a foreign via.
- It replaces nothing.

**Why no third via inside the body:** the only F-free spots in the body lie on the 0.41 mm B.Cu channel between the CTRL_SCL and QON B tracks, and a 0.5 mm via plus 2 × 0.2 mm clearance needs 0.9 mm.

**Estimate.** Copper resistance model: 1 oz, 20 µm barrel plating.

| | Before | After |
|---|---|---|
| Paths | 2 × 0.5/0.2 body vias, about 1.1 mΩ in parallel | the same, plus the new bridge path |
| Bridge path | – | about 2 mΩ of F bridge, then the 0.3 mm via (about 1.5 mΩ) in parallel with the pad-10/11 tracks to the C111.2 vias, ≈ 3.1 mΩ |
| Share of the PGND return on the bridge | – | about 26 % |
| Return current at which the fine vias reach the project's 0.7 A per 0.2 mm via | 1.4 A | about 1.9 A |
| Each fine via at 3 A charge from 9 V (≈ 2.7 A return) | about 1.35 A | about 1.0 A (IPC barrel rating about 1.5 A each at 15 K) |

**Still below the project via rule at ≥ 3 A charge from 9 V.** The 0.2 × 1.0 mm pin-27 pad remains the narrowest cross-section. Decision item: cap charge current, or accept by IPC.

## 3. m-L2 / m-L3 clearances (`route_r6l_swclr.py`)

| Item | Before | After | Change |
|---|---|---|---|
| SW2 B jumper to REGN B | 0.215 mm | **0.328 mm** (now at the 0.4 mm segment, 153.4, 117.44) | REGN segment (153.40, 119.60)–(153.48, 121.62) split collinearly at y 120.40: 0.40 mm for 0.80 mm at the jumper, 0.70 mm for the remaining 1.22 mm. No bend, so no corner hit. REGN class minimum is 0.4 mm. |
| 5V_CODEC In2 to USB_AUDIO_R via (174.2, 61.8) | 0.292 mm | **0.542 mm** (audio rule 0.5 met) | Piece (176.28, 61.97)–(170.52, 67.73) back to 1.5 mm. Both neighbouring pieces are 1.5 mm, so there is no series-capacity loss. U8-COM2 via 0.505 → 0.755 mm. |
| SW2 to Q103-G via | 0.240 mm | 0.240 mm | – |

## Open items (unchanged unless noted)
- **PGND** about 1.0 A per 0.2 mm via at 3 A charge from 9 V. See 2 for the decision item.
- **SYS_COL_B tip** about 0.18 mm wide on B (≥ 0.15, inherited).
- **Other review minors not in scope:** m-L4 (U15 L1 0.206 mm, U14 L2 0.777 mm); I2S_LRCK via to VBUS_PD_IN2_G 0.40 mm.
- **Inherited:** USB 17.3 mm uncoupled (waiver), 3 via-in-pad, J7 2 open edges, 7 corner hits, 3 strict items, teardrops (GUI).

## Helpers (new, `ai-files/helpers/`)

| Helper | Purpose |
|---|---|
| `route_r6m_sliver.py` | Zone table plus narrow-copper scan (morphological opening) of the per-net copper union and of each zone fill alone, all layers |
| `route_r6m_zfix.py` | Delete zones, set min thickness by name pattern, subtract a box from a zone outline, refill |
| `route_r6m_gndfloat.py` | GND fill pieces per layer and floating-piece test |
| `route_r6m_eval.sh` | R6m gates: DRC, open edges, `route_r6c_gates`, islands vs R6l-final, strict split DRC, corner rule vs R6l-final, sliver scan, pour area, union, GND fill |

**Reproduction:**
1. `route_r6m_zfix.py R6l-final.kicad_pcb R6m-1.kicad_pcb r6m/m1.json`
2. `route_r6l_edit.py R6m-1.kicad_pcb R6m-2.kicad_pcb r6m/m2.json`
3. Copy R6m-2 → R6m-final, then `route_r6m_eval.sh R6m-final R6l-final full`.
