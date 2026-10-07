# Routing P2 (2026-10-07): power nets (SWITCH, POWER_HI, PVDD, SPK_OUT, BOOT) - DRAFT for coordinator adoption

Everything is a copy in `ai-files/pcb/work-p2/` (start: `work-p1/R3-final`). Final board: `work-p2/R4-final.kicad_pcb` (+ `.kicad_pro` = P1 project, `.kicad_dru` = P1 rules with two changes, see 4). Nothing in `DesktopSpeaker-kicad/` touched, `build_pcb_v9.sh` not run, no commit. Render: `ai-files/pcb/route-p2-top.png` (F.Cu). DRC json / open lists: `R4-final.drc.json`, `R4-final.open.json` (P1 oracle), `R4-final.open2.json` (fragment-aware oracle).

## 1. Result (open edges by class, R3-final -> R4-final)
| Class | R3 | R4 (P1 oracle `route_p1_open`) | R4 (fragment-aware `route_p2_open2`) |
|---|---|---|---|
| SWITCH | 30 | 2 | 2 (U6 OUT_B-: pin 27 - C288 - L204) |
| BOOT | 11 | 3 | 3 (U6 BST_A-, BST_B-, U7 BST_B-) |
| POWER_HI | 35 | 1 (U25.9 pad vs SYS_RAW pour, oracle artifact: pad centre outside the fill) | 0 |
| PVDD | 17 | 0 | 0 |
| SPK_OUT | 12 | 0 | 0 |
| **5 classes** | **105** | **6** | **5** |
Not routed in P2 and changed by the rip-up: AUDIO 17 -> 16, I2S 11 -> 11, USB 7 -> 7, SIGNAL 35 -> 42, I2C 23, PWR_LOCAL 12, PWR_3V 52, PWR_5V 14 -> 16, GND 79 -> 75 (P1 oracle). KiCad's own DRC (243 unconnected items board wide) lists for the 5 classes only the 5 bootstrap items below.
- **Still open (5 edges, all placement-blocked):** U6 pins 27/28/29 and U7 pin 28 (OUT_B-, BST_B-, BST_A-, U7 BST_B-). The bootstrap caps C286/C288 (U6) and C299/C301 (U7) sit 0.5 mm above the pin row: the channel between pin tops (y 133.36) and the cap pad bottoms (y 132.80) is 0.56 mm, a 0.2 track needs 0.6, and the pads of C286 cover pins 27-30. Fix = placement: move the four bootstrap caps >= 1.2 mm outward (or rotate) and re-run `route_p2_run.py ... --only`. Not done because the task allowed routing only.
## 2. DRC (project rules + the two rule changes)
clearance 0, shorting_items 0, track_dangling 0, via_dangling 0, items_not_allowed (antenna keep-out, J7 keep-out) 0, isolated_copper 0 (was 12), hole_to_hole 0. Unchanged/inherited: hole_clearance 2, drill_out_of_range 8, silk_over_copper 19, silk_overlap 18, silk_edge_clearance 6, lib_footprint_issues 199, skew_out_of_range 3 (USB pair still open). **track_width 199 (P1: 45)**: pin escape necks of 0.2 mm on 0.4-0.5 mm pitch pins (floors 0.4/0.5 for SWITCH/POWER_HI/PVDD/SPK_OUT/BOOT PWR) - trunks are 0.5-2.0 mm. Copper: F.Cu 1880 segments, B.Cu 123, In2 163; vias 265 (R3: 1923/76/174, 221 vias).
## 3. Method (all scripts in `ai-files/helpers/route_p2_*`)
- `route_p2_lib.py/core.py` + `route_p2_astar.c/.so`: own 0.05 mm raster router (numpy + C A*, 8 directions, F.Cu/In2/B.Cu with through vias). Obstacles from exact pad polygons/tracks/vias, per-class clearances (AUDIO 0.5, I2S/USB 0.4, POWER_HI 0.4, PVDD/SPK 0.3, GND stubs per rule), board edge 0.5, BM83 antenna keep-out + 0.5. Width tiers per class (POWER_HI/PVDD/SPK_OUT 2.0/1.0/0.5, SWITCH 1.5/0.8/0.4, BOOT 0.3/0.25) with 0.2 mm necks only near own pads; exact-width fit and straight-shortcut simplification against the real board geometry. Fine-pitch pads get exact 0.2 mm stubs along the pad axis. SWITCH/BOOT on F.Cu + B.Cu, SPK_OUT F.Cu only, power on all three.
- Foreign pours are not obstacles (the refill re-cuts them); GND stubs, signal nets and (for power nets) other managed nets are ripped with a penalty and re-routed (`route_p2_run.py`, queue rounds; 68 nets ripped in total, 189 GND stubs lost a via and were re-attached by `route_p2_fix.py` where room exists: 18 GND pads stay without via = already open in P1).
- `route_p2_fix.py`: GND re-attach vias and vias for isolated pour fragments (12 -> 0 isolated_copper; 14 vias, 0.8/0.4 or 0.6/0.3, each tied to the same-net F.Cu copper). `route_p2_drcfix.py` + `route_p2_cycle.sh`: DRC-driven removal and re-route cycles. `route_p2_open2.py`: connectivity with every zone fill outline as its own node (P1 oracle treats a zone as one node and checks only pad centres; it under-counts SYS_RAW/PVDD/BAT_PACK/USB_VBUS fragments and flags U25.9).
- In2: 163 signal segments remain (R3 174): power islands are now tied with vias; no In2 signal was removed only to make room, ripped nets were re-routed in place.
## 4. Rule changes (`R4-final.kicad_dru`)
1. `switch_clear` 1.0 mm -> 0.3 mm (at 1.0 mm the pin-dense QFN/MSOP neighbours gave 109+ violations; goal 2.0 mm is unreachable around U4/U25/U6/U7).
2. New `neck_exempt`: track-to-track clearance 0.2 mm when either track is < 0.26 mm wide (pin-pitch escape stubs of different classes on 0.4-0.5 mm pitch pins cannot keep 0.3-0.4 mm). Pad-to-track, via and zone rules are unchanged.
## 5. Risks / next
- Teardrops, width floors at necks (199 items) and the 5 bootstrap edges need a decision; SIGNAL +7 and PWR_5V +2 open edges come from the re-routed neighbours (U4/U6/U7/U25 corridors cleared for power) - a signal pass (P3) should re-run Freerouting-style chunks on the remaining open nets.
- Large pours/trunk widths: BAT_PACK 2 mm on B.Cu, SPK_OUT 2.0 mm (F.Cu), PVDD 1-2 mm, SYS_RAW 2 mm; loop areas and via counts per plan sec. 7 not measured.
- Runs are not bit-reproducible after rip-up (managed nets oscillate); `R4-final` is the checked state. Never use `pkill -f`.
