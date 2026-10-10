# Routing R6a (2026-10-08): rules, planes and power routing on placement v10d (phases 1-3 of the revised plan)

Work copies only: `ai-files/pcb/work-r6/`. Final board `work-r6/R6a-final.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`). `DesktopSpeaker-kicad/` was not touched, no build script was run into it, no commit. The whole result rebuilds from `R6a-base` (= v10d copy) with `ai-files/helpers/route_r6a_build.sh` (about 4 min). Every track, via and zone on the final board is locked (942 track/via items, 56 zones).

Renders: `ai-files/pcb/route-r6a-top.png` (F.Cu + silk), `route-r6a-in2.png`, `route-r6a-bottom.png`, and net-coloured power views `route-r6a-power-F.png` and `route-r6a-power-In2B.png`.

## 1. Rules (`R6a.kicad_dru`, KiCad 10 syntax checked by a DRC dry run on v10d)

- **switch_clear is split into three rules.**
  - `switch_power`: 0.3 mm from SWITCH to power and BOOT copper.
  - `switch_sensitive`: 1.0 mm to SIGNAL/Default, I2C, AUDIO, I2S_CLK and USB. Pads are included; only pad-to-pad pairs are exempt.
  - `switch_critical`: 2.0 mm from SWITCH/BOOT to BATP, U25 FB, COMP and ILIM.
- **Necks are courtyard-scoped.** `neck_ic` allows 0.2 mm track, 0.2 mm clearance and 0.45/0.2 vias, and comes last. It applies inside the IC courtyards and the `NECK_<ref>` rule areas (courtyard + 1.5 mm).
  - ICs from the brief: U4, U6, U7, U8, U9, U11, U14, U15, U19, U24, U25.
  - **Added:** U3, U5, U10, U20 and J1, which are also 0.5 mm pitch. U3, U10 and J1 come from the review's sec. 4 rule.
  - **Changed:** NECK_U6 and NECK_U7 reach 3.8 mm further down to cover the bootstrap cap stack.
  - The board-wide 0.15 mm annular-ring minimum means the fine via has to be 0.5/0.2 mm in practice; 0.45/0.2 fails it.
- **Other rules:**
  - `neck_u11`: 0.15 mm track and clearance (v10c m1).
  - U11 footprint-via exception: drill 0.2 mm. The 8 `drill_out_of_range` items are gone.
  - `fine_pitch` pad pairs moved after the neck rules.
  - New `in2_power_only` rule.
  - There is no board-wide width exemption.
- **Netclass bug found and fixed (it hit the old rules too).** The `*` → SIGNAL catch-all pattern gives every net a composite class name in KiCad 10 (for example "GND,SIGNAL"). As a result, every `NetClass == 'X'` rule matched wrongly or not at all. I removed the catch-all, so unmatched nets fall to Default. All patterns are exact names.
- **Zone clearances.** The zone filler does not apply the custom clearance rules, so I set local zone clearances: POWER_HI 0.4, PVDD/SPK/SWITCH 0.3, F.Cu GND 0.4 mm.

## 2. Gates: DRC and open edges per phase

Open edges come from `route_p2_open2.py` (fragment-aware, all nets). DRC was run inside the work folder with the R6a rules.

| Stage | DRC (new items) | SWITCH | BOOT | POWER_HI | PVDD | SPK_OUT | PWR_5V | PWR_3V | PWR_LOCAL |
|---|---|---|---|---|---|---|---|---|---|
| v10d + rules (dry run) | 0 | | | | | | | | |
| P1 planes, EP arrays, necks | 0 | 30 | 11 | 61 | 27 | 12 | 25 | 69 | 23 |
| P2 hand power copper + In2 islands | 0 | 8 | 0 | 12 | 0 | 12 | 20 | 67 | 21 |
| P3 scripted SW/OUT/speaker | 1 width (fixed later) | 0 | 0 | 12 | 0 | 0 | 20 | 67 | 21 |
| P4 SYS/BAT branches | 0 | 0 | 0 | **0** | 0 | 0 | 20 | 67 | 21 |
| P5 rails + local decoupling | 14 width (fixed by the widen pass) | 0 | 0 | 0 | 0 | 0 | **0** | **0** | 3 |
| **R6a-final** | **0** | **0** | **0** | **0** | **0** | **0** | **0** | **0** | **3** |

**Final DRC:** 0 for clearance, shorting, track_width, track_dangling, isolated copper, items_not_allowed, annular and drill.

What remains:
- **Inherited:** hole_clearance 2 (SW100 footprint) and silk 32.
- **via_dangling 5:** the v10d signal reservation vias for BATP, U8-COM1/COM2, HP_L and PD_PLUG_EVENT.
- **475 unconnected items.** All of them are next-phase classes, except 3 PWR_LOCAL edges.

Final open edges by class: Default 137, AUDIO 85, I2C 24, I2S_CLK 22, USB 9, GND 191, PWR_LOCAL 3 (U24-LDO ×2, U10-CPP). Every power class is at 0.

## 3. Vias

332 in total: 329 at 0.6/0.3 mm and 3 fine vias at 0.5/0.2 mm, all inside neck areas (Q103 gate at U4, U7 BST_B+, U6 3V3).

| Class | GND | POWER_HI | PVDD | PWR_3V | PWR_5V | SWITCH | BOOT | Signal reservations |
|---|---|---|---|---|---|---|---|---|
| Vias | 92 | 153 | 20 | 37 | 15 | 4 | 4 | 7 |

- **EP / thermal arrays (locked):** U6 4x4 = 16, U7 16, U25 pad 21 2x4 = 8, U11 8 (footprint, 0.2 mm drill). All are solid-connected.
- **Transitions:**

  | Net / location | Vias |
  |---|---|
  | USB_VBUS, U11 end | 17 |
  | USB_VBUS, J1 end | 7 |
  | VBUS_PD, U11 end | 13 (target 15) |
  | VBUS_PD, U4 end | 6 |
  | SYS caps | 8 |
  | SYS trunk | 14 + 18 |
  | SYS at L200 | 7 |
  | BAT_INT at C106 | 18 |
  | BAT_INT at Q103 | 18 |
  | BAT_PACK at Q103 | 18 |
  | PVDD | 19 reservation vias + TP10 |

- **Via-in-pad:** 0 router vias. 25 were moved to dogbones by `route_r6a_dogbone.py` and one by hand at U14. One inherited v10d reservation via still touches C274.1 at (186.09, 128.3).

## 4. Power copper and widths

| Net | F.Cu | In2 (0.5 oz) | B.Cu / notes |
|---|---|---|---|
| USB_VBUS | J1 pads → vias (0.5 mm stubs). U11 pour 4.25 mm. | Island 18 × 27 mm | The USB pair and CC lines cross over In2 |
| VBUS_PD | U11 pour 4.9 mm. At U4: pin necks 0.2 mm, 0.4-0.5 mm to the caps and vias. | Column 8.3 mm × 74 mm | No 1.5 mm F.Cu run in parallel (see 5.2) |
| SYS_RAW | U4 cap pour 2.65 mm. Trunk 6.0 mm (vertical) / 5.4 mm (west), plus the boost input pour. | 12.7-13.8 mm, neck 7.5 mm × 6 mm under U4, 2.1 mm strip to the L200 field. Branches to U14/U15/U20: 2.0 mm. | Branch crossings 0.5-1.0 mm |
| BAT_INT | 4.45 mm (horizontal) / **3.5 mm** (vertical leg beside Q100). U4 pins 22/23: 0.6 mm neck. | L-shape 6.3 / 8.7 mm | |
| BAT_PACK | Q103 pour 5.7 × 5.7 mm + 18 vias | Band 13.0 / 12.7 mm to SW101.1 (THT, joins all layers) | B.Cu band 6.2 / 5.0 / 5.4 mm. Gauge branch on In2 0.6-1.0 mm. |
| PACK_RAW | 5.45 mm × 17 mm (J5.1 → SW101.2) | | |
| PVDD | Boost band 1.75 mm at U25 pins 14-16 (0.8 mm past C314), link 0.6 mm and column 2.1-2.85 mm to C275, bottom row 3 mm. TAS PVDD lanes 0.82-0.87 mm. | Band 17 mm (y 140-157), 5.8 mm strip to the U6 island, U6/U7 islands | No 2 mm F.Cu trunk to the amps (see 5.2) |
| SW1 / SW2 | Polygons 1.85 mm from the L1 pads, 0.6 mm × 0.9 mm beside the pin-27 GND via column (m4), 0.2 mm pin neck | | BTST cap links 0.4 mm on B.Cu |
| U25 SW | Bar 1.85 mm (L200.2 pad 1.92 mm) × 4.4 mm. R252/C267 link 0.4 / 0.25 mm. | | BOOT 0.25 mm with a B.Cu jumper |
| SPK_OUT (6) | 2.0 mm. Minimum 0.7 mm at L202.2 (C303) and 1.0 mm at C305. | | |
| U6/U7 OUT_x | 0.2 mm pin necks, then 0.4-1.0 mm tracks + pours of 11-18 mm² to the inductors | | |
| TPS63802 L1/L2 | L1 pours 1.0-1.35 mm. L2 0.6 mm. | | |
| Rails | 5V_LOGIC 0.4-0.6 mm | 5V_LOGIC up to 2.0 mm, 5V_CODEC 1.5 mm, 3V3_AUDIO 0.3-1.5 mm, 3V_AO 0.5-1.0 mm, 3V8_BT 1.5 mm, LDO_3V3 0.5-1.0 mm | 3V_AO 0.5-0.8 mm on B.Cu (37 mm); REGN 0.4-0.5 mm on F.Cu + 0.4 mm on B.Cu |

**Other requested items:**
- Planes: In1 is solid GND, B.Cu has a GND pour, and In2 has a GND background under the islands. The antenna keep-out has no copper on any layer.
- In2 carries power copper only: 0 signal tracks; 189 mm of POWER_HI, 212 mm of 5V and 354 mm of 3V tracks.
- Minors applied: the U11 neck rule (m1) and the U24 GND tie (m2: pins 7/12/15/25/26 to a patch under the body with 2 vias).
- U4 bottom row (m3): not routed, because these are signals. The R103-R108 gap and the TS lane (pin 16 → R100.2) are kept open: REGN now runs straight down to TP11, with a B.Cu jumper at R108. The routing order SCL → SDA → QON → CE_N is carried forward.

## 5. Deviations and open items for the next phase

1. **Neck rule granularity.** KiCad applies `neck_ic` to a whole zone or track that touches a NECK area. The 1 mm and 2 mm switch distances are therefore held by the geometry, not proven by DRC. The phase-5 script check should measure them.
2. **Widths below the brief.**
   - BAT_INT on F.Cu is 3.5-4.45 mm, limited by Q100's placement.
   - VBUS_PD and PVDD have no F.Cu run in parallel along their long paths: it would wall off the audio/USB F.Cu area and cross the OUT fan-out. Their In2 widths were raised instead (VBUS 8.3 mm, PVDD 5.8-17 mm).
   - The SW1/SW2 lanes narrow to 0.6 mm (m4).
   - VBUS_PD has 13 vias at U11 against a target of 15.
3. **TAS5825M.**
   - No extra GND vias beside the package, only the 16 in the pad. There is no free GND copper there that would not block an escape.
   - U7 ADR (pin 8) has no escape left: the VR_DIG and 3V3 escapes fill the 0.65 mm slot. It needs a fine via or a move of R261.
   - U6's DVDD cluster (pin 6 / C281 / R262) is fed through one 0.5/0.2 via, because the VR_DIG escape encloses it.
   - U7's 3V3 comes in as a 0.3 mm F.Cu run from the north.
4. **The charger copper forms a closed barrier.** The pieces are the SYS cap pour, the BAT_INT F.Cu pour, the SYS trunk, the SW2 and gate B.Cu jumpers, and the BAT_PACK B.Cu band. The U4 bottom and right signals (CTRL I2C, CE_N, QON, CHG_INT, PROG, TS, BATP) must leave on B.Cu to the west or south:
   - BATP: south of its via (155.1, 123.35), then east, then north at x ≈ 162 to R112.2.
   - CE_N to Q100: from the north.
5. **Not done here.**
   - B.Cu keep-out rule areas under the amps, BM83 and audio block. My U7 BST_B+ and U25 BOOT jumpers sit there, so add them with exceptions.
   - PWR_LOCAL U24-LDO and U10-CPP: placement-blocked, as in v10c m2.
   - Teardrops (GUI, phase 5).
6. **For the overspec pass:** the long 3V_AO B.Cu run, the rail strips on In2, and the narrow F.Cu 3V3 runs near U24.

**Scripts** (`ai-files/helpers/`):
- `route_r6a_lib.py`: zones, legal-via and legal-track helpers
- `route_r6a_phase1.py`
- `route_r6a_power.py`: hand geometry per block
- `route_r6a_astar.py`: the route_p2 A* with zone obstacles, In2 preference, via-only keep-outs and seeds; uses `route_r6a_astar.c/.so`
- `route_r6a_widen.py`
- `route_r6a_final.py`: OUT/L1 pours and locking
- `route_r6a_dogbone.py`
- `route_r6a_u14fix.py`
- `route_r6a_swwiden.py`
- `route_r6a_metrics.py`
- `route_r6a_build.sh`

Evidence in `work-r6/`: `R6a-final.drc.json`, `R6a-final.open2.json`, `R6a-final.metrics.json`, the stage boards `P1`-`P10`, and `s/` (viewer and checks).
