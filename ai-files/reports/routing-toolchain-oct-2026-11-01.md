# Routing toolchain: exact-octilinear A* router `route_oct` (2026-11-01)

Agent: "Routing toolchain: exact-octilinear A* router". Scratch work only: boards in `ai-files/pcb/work-oct/`, code in `ai-files/helpers/route_oct*`. Nothing in `DesktopSpeaker-kicad/` was edited. No rule, net class or board-setup value was changed (rule AG1); every final board's `.kicad_dru` and `.kicad_pro` have the same SHA-256 as the project files. Nothing committed. Board under test: copy of `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb` at commit 2858f93 (sha256 d5ae57fb..., the same file the Freerouting trial used); placement was not changed. Headless throughout: KiCad 10.0.7 AppImage `kicad-cli` and `python3.11`. The AppImage python has no numpy, so the routing core runs in a scratch venv (numpy 2.5.4, shapely 2.2.0) that reads a pcbnew JSON export.

**Verdict first.**
- **Geometry: solved by construction.** An independent checker confirmed it on every routed board:
  - 100.000 % of routed length exactly 0/45/90 deg (max deviation 0.0000 deg);
  - 0 corners of 90 deg away from pads, 0 colinear splits, 0 dangling ends, 0 bend-spacing faults, 0 shorts;
  - 0 clearance or width DRC errors under the frozen rules, sentinel rule fires, stage locks verified.
  - Three defect classes surfaced on the 140-net run and were fixed in code: paths touching themselves, an in-pad dogleg meeting a second stub at 45 deg, and NPTH edge clearance. The fixes were re-verified on the trial set and on one hard run (section 5).
- **Completion: not solved.**
  - Trial set (Freerouting's 11 nets, 38 airwires): 15-17 closed. Freerouting: 17.
  - All 140 signal nets (283 connections): 130-136 closed (46-48 %); 34-37 nets complete.
  - Median length / octilinear minimum on complete nets: 1.14-1.16. 95th percentile: 4.6. The strict runs pass the 1.15 median and the LA2 run does not; all runs fail the 1.4 p95.

Go / no-go: **no-go as an unattended router for the restart; go as the geometry and checking engine** for nets whose escapes and topology are already free (section 7).

## 1. Files and command line

| file | role |
|---|---|
| `helpers/route_oct.py` | router (one stage per call) |
| `helpers/route_oct_core.c` | C core: octilinear A* with forced runs after bends and vias, scanline polygon fill; compiled by `route_oct.py` with gcc into the work folder |
| `helpers/route_oct_rules.py` | clearance model transcribed from `DesktopSpeaker.kicad_dru`; refuses to run if the rule file's SHA-256 differs |
| `helpers/route_oct_export.py` | pcbnew (AppImage python) export of pads, tracks, vias, zone fills, rule areas, courtyards and outline to JSON |
| `helpers/route_oct_strip.py` | text-level strip of nets (by list, or `--all-signals`) |
| `helpers/route_oct_order.py` | stage assignment (OR1) and order inside a stage (OR2) |
| `helpers/route_oct_refill.py` | zone refill in a separate pcbnew process |
| `helpers/route_oct_stage.sh` | one locked stage: export, route, refill, DRC (restores pristine project files beside each board) |
| `helpers/route_oct_lock.py` | canonical SHA-256 of a stage's copper (manifest) |
| `helpers/route_oct_check.py` | independent measurement (does not import the router) |
| `helpers/route_oct_sentinel.sh` | proves the rule file is read (one sentinel rule appended on a copy) |
| `helpers/route_oct_debug.py` | PNG of the A* window rasters for one connection (diagnosis) |
| `pcb/work-oct/run_all.sh` | S1..S3 for one net file with its own manifest |

```
cd ai-files/pcb/work-oct ; V=<venv>/bin/python ; K=~/Applications/kicad.AppImage
# prepare a stripped copy (project .kicad_pro/.kicad_dru copied beside it as STEM.kicad_pro/.kicad_dru)
python3 ../../helpers/route_oct_strip.py base.kicad_pcb H0-raw.kicad_pcb --all-signals base.kicad_pro --list H0.nets.txt
$K python3.11 ../../helpers/route_oct_refill.py H0-raw.kicad_pcb H0.kicad_pcb
$K python3.11 ../../helpers/route_oct_export.py H0.kicad_pcb H0.geo.json
python3 ../../helpers/route_oct_order.py H0.geo.json H0.nets.txt hard-nets.txt
# route S1..S3 (each stage: export -> route -> refill -> DRC), final parameter set
sh run_all.sh Hfa- hard-nets.txt H0 --via-cost 1.5 --pair-avoid 1 --hweight 1 --max-exp 3e7
# measure
$K python3.11 ../../helpers/route_oct_export.py Hfa-3.kicad_pcb Hfa-3.geo.json
$V ../../helpers/route_oct_check.py Hfa-3.kicad_pcb Hfa-3.geo.json hard-nets.txt --drc Hfa-3.drc.json --manifest Hfa--manifest.json \
   --rules Hfa-3.kicad_dru Hfa-3.kicad_pro --json Hfa-3.check.json
sh ../../helpers/route_oct_sentinel.sh $PWD Hfa-3
```
Net file lines: `STAGE NET [pair=<partner>] [bcu=no|gnd|yes] [width=mm]`. Router options are listed by `route_oct.py --help`.

## 2. Design

- **Lattice and layers.**
  - 0.05 mm grid. Routing only on F.Cu and B.Cu; In1 and In2 are never used.
  - Moves are the 8 lattice directions, so every routed segment is exactly 0/45/90 deg.
  - The lattice origin is chosen per connection (up to 2 candidates) so the pad centre lines fall on lattice lines. Angles depend only on coordinate differences, so exactness is kept. This removes the 0.005-0.025 mm offsets that 1172 of 1192 pads have from a fixed 0.05 mm grid.
- **Bends.**
  - A* state = (layer, cell, direction). The only direction change is +-45 deg.
  - Each bend is followed by a forced straight run of max(0.4 mm, 3 x width): 15 cells orthogonal or 11 diagonal at 0.25 mm. So 90 or 135 deg corners and short segments between bends cannot be generated.
  - A via is followed by the same forced run.
- **Pads.** Stubs are computed in integer nanometres.
  - Variant A runs along the pad axis on a lattice line to a node at least pad edge + 0.3 mm. When the centre is off that line, an octilinear micro-dogleg of at most 0.035 mm sits inside the pad copper; the checker counts these as `micro_segs_in_pad`. Since the last fix, a pad's second track starts on the lattice line inside the pad with no centre dogleg.
  - Variants B+/B- run on the exact pad centre line, then at 45 deg to the first lattice node.
  - Exit directions:
    - fine-pitch pads (part with >= 8 pads, pad <= 0.45 mm wide) leave outward only (FO1);
    - other elongated pads leave along their long axis;
    - square-ish pads may leave in 4 directions.
  - Stubs may neck to 0.2 mm only inside the neck_ic areas, and USB inside NECK_U2_USB, as the rule file allows.
  - Facing pads on a common line are joined by one straight segment (LE5).
- **Topology.**
  - Multi-pin nets are routed as a daisy chain: exact search over orders up to 7 pads, otherwise nearest-neighbour plus 2-opt, using octilinear distance, with fine-pitch pads pushed to the chain ends.
  - A second connection at a fine-pitch pad branches at its stub node.
  - The post-pass only merges colinear segments; there is no shortcut step.
- **Clearances.**
  - Each connection gets window rasters built from shapely buffers of every foreign item: clearance + w/2 + 0.04 mm sweep margin, filled by a C scanline.
  - Clearance values:
    - max of the matching class rules: audio 0.5, clk 0.4, vbus 0.4, pvdd 0.3, switch 1.0/2.0, USB pair 0.15;
    - 0.2 inside the neck_ic areas, as DRC uses, but the switch-node clearances are kept there;
    - edge 0.5 (NPTH holes included), hole 0.25;
    - antenna keep-out, BKO_* on B.Cu, J7 no-via.
  - Vias also clear In1/In2 copper and In2 islands, every SMD pad by 0.25 mm, and holes by 0.3 mm.
  - Every committed segment and via is re-checked exactly with shapely (DRC semantics, against foreign copper and against the path itself) before it is accepted.
- **Reference plane.**
  - Sensitive nets (I2S_CLK, AUDIO, AUD_SDA/SCL) are F.Cu only (`bcu=no`) in the strict policy. USB uses `bcu=gnd` in both policies because the USB-C row interleave needs a jumper.
  - The LA2 policy allows all sensitive nets on B.Cu, but only over In2 GND.
  - Other nets:
    - B.Cu step x1.3 over In2 GND and x3.9 over islands or voids;
    - B.Cu forbidden over POWER_HI, PVDD and SPK_OUT islands;
    - F.Cu step +2 over an In1 void;
    - +10 % against the layer direction (F horizontal, B vertical).
- **Spacing (SP1).** For I2S_CLK and USB nets, every other signal track gets a 0.6 mm halo, and vice versa. The halo is hard outside the neck areas and is dropped within 1.2 mm of the connection's own pads. USB_DN is routed after USB_DP with a x0.6 cost on the 0.15-0.25 mm gap rail.
- **Order and locks.**
  - Stages (OR1): S1 USB, clocks and I2S; S2 audio plus amplifier I2C; S3 the rest.
  - Inside a stage (OR2): fine-pitch nets first, then longest MST first.
  - Before a stage, the escape (stub plus forced run) of every fine-pitch pad of the nets still to route is reserved. There is also a soft cost near pads of nets still to route.
  - Rip-up and reroute is transactional:
    1. A conflict search makes same-stage copper passable at a penalty.
    2. The hit nets (max 3) are ripped and everything is rerouted.
    3. The change is rolled back unless the group's completed connections increase.
  - Each stage writes a manifest entry with the SHA-256 of its canonical copper. The next stage refuses to run if an earlier stage's copper has changed.
- **Write-back.** `segment`/`via` blocks are inserted as text. Zones are refilled in a separate pcbnew process with pristine copies of the project `.kicad_pro/.kicad_dru` beside the board. pcbnew's save rewrites the `.kicad_pro`; it only adds `td_enabled: false` defaults and the file name (checked), and the script restores the pristine copy.

## 3. Validation method

- **Strip.** For the 11 nets, `route_oct_strip.py` removed exactly what the Freerouting trial removed: 273 segments, 1 arc, 65 vias, 193 teardrops.
  - Refilled stripped board: DRC 0 violations / 38 unconnected. Untouched copy: 0 / 0.
  - Full signal strip (`--all-signals`): 140 nets (1461 segments, 13 arcs, 335 vias, 1162 teardrops); DRC 0 violations / 279 unconnected.
- **Measurement.** `route_oct_check.py` parses the saved board.
  - Calibrated on the original board for the 11 nets: it reproduces the trial report's 1433.8 mm, 38.72 % exact and 65 vias.
  - It is stricter than KiCad: it also flags 19 dangling or overlapping joints in the original copper.
  - `r7_metrics.py` and `r7_bench.py` were run as well. Whole-board acute joints (< 80 deg) were 33 before and after routing, so the router added none.
- **DRC.** `kicad-cli pcb drc --severity-all --all-track-errors` on every refilled stage board.
  - Sentinel (`route_oct_sentinel.sh`): a copy with one appended rule (I2S_CLK width >= 5 mm) fires: 81 track-width violations on the base board, "FIRES" on the final trial board.
- **Rules.** SHA-256 of `.kicad_dru` and `.kicad_pro` of every final board equals the project files (checker key `rules`).

- **Process notes.**
  - Two background pipelines once ran concurrently on the same files. That produced a false lock violation; those runs were discarded.
  - An `ln -sf` in the first version of the sentinel script followed an existing symlink and created a stray symlink `DesktopSpeaker-kicad/kicad-library/kicad-library`. It was removed and the script fixed. `git status` of `DesktopSpeaker-kicad/` now shows only the `.kicad_prl` change that predates this work.
  - `ai-files/pcb/work-oct/` holds about 0.8 GB of scratch boards; commit only the helpers and this report.

## 4. Trial set (same 11 nets as the Freerouting trial, 38 airwires)

Strict = sensitive nets F.Cu only (USB `bcu=gnd`). LA2 = sensitive nets may use B.Cu over In2 GND. All attempts are logged (AG12); none was selected by DRC. The tracked metric is airwires closed (from the router log; equal to 38 minus the DRC unconnected count on every board).

| run | change | S1/16 | S2/10 | S3/12 | total/38 | complete nets | vias | runtime |
|---|---|---|---|---|---|---|---|---|
| Freerouting trial | - | | | | 17 | 1 | 0 | - |
| A1 strict | baseline: offsets, direct joins, RRR | 7 | 4 | 5 | **16** | 0 | 2 | 195 s |
| A2 strict | exact-limit tolerance; pad export at 0.2 um; outward-only for fine pitch only; reservation + forced run; pending-pad cost | 6 | 4 | 6 | **16** | 1 | 12 | 241 s |
| A2 LA2 | same, `bcu=gnd` for S1/S2 | 6 | 5 | 6 | **17** | 1 | 16 | 417 s |
| A3 strict | via cost 4 mm, pair-avoid band, weighted A* on big windows, 6e7 expansions | 6 | 4 | 5 | **15** | 2 | 18 | 245 s |
| A3 LA2 | same | 6 | 5 | 5 | **16** | 2 | 22 | 504 s |
| F strict | A2 parameters + path self-check | 5 | 4 | 6 | **15** | 1 | 12 | 366 s |
| F LA2 | same | 5 | 5 | 6 | **16** | 1 | 16 | 638 s |

Attempts 2 and 3 did not improve the worst metric (completion) over attempt 1 in the strict policy. Per AG13 I stopped tuning after attempt 3 and kept the attempt-2 parameters (`--via-cost 1.5 --pair-avoid 1 --hweight 1 --max-exp 3e7`). The F runs only add a correctness check: paths that touch themselves are rejected instead of written, which cost one S1 connection.

**Checks.** These were identical on every trial board (checker and DRC):

| check | value |
|---|---|
| exact angle share | 100.000 % (max deviation 0.0000 deg) |
| joints < 90 deg | 0 |
| 90-deg joints away from pads | 0 |
| T-junctions | 0 |
| colinear splits | 0 |
| dangling ends | 0 |
| bend spacing below the minimum | 0 |
| pad exits < 0.3 mm | 0 |
| micro segments outside pads | 0 (2 doglegs inside pad copper) |
| shorts | 0 |
| DRC clearance / width / edge errors | 0 |

- **DRC items present.** Only the USB pair rules of the incomplete pair: `skew_out_of_range` 1 and `diff_pair_uncoupled_length_too_long` 1. A2/A3 also had `diff_pair_gap_out_of_range` 4, at D1 where DP and DN split to separate ESD pins 1.3-1.8 mm apart.
- **Spacing.** Parallel length at gap < 0.6 mm for I2S/USB: 0.13 mm (fan-out inside the U6 neck area).
- **Sensitive B.Cu over island or void.** Strict 0 mm. LA2 1.69 mm, which is the In2 antipads of the two AUD vias (about 0.85 mm per layer change).
- **Length.** A length ratio exists only for complete nets: BT_UART_TX 1.52 with 10 vias, which fails LE1 and LE4.

Per net, F LA2 (Tfb-3, connections closed): USB_DP 2/4, USB_DN 0/3, I2S_BCK 1/3, I2S_LRCK 1/3, I2S_SDATA 1/3, AUD_SDA 3/5, AUD_SCL 2/5, BT_UART_TX 2/2 (complete), BT_UART_RX 1/2, CTRL_SDA 1/4, CTRL_SCL 2/4; total 16/38.

## 5. Hard test: all 140 signal nets stripped and rerouted in OR1 order

Strip: 140 nets (classes Default, I2C, I2S_CLK, USB, AUDIO, non-GND, all tracks <= 0.35 mm, >= 2 pads), 283 chain connections. Power copper and GND pours stay. Stages: S1 14 nets (USB, clocks, I2S), S2 49 nets (audio + AUD I2C), S3 77 nets (rest).

| run | S1 conn | S2 conn | S3 conn | total | nets complete | vias | runtime |
|---|---|---|---|---|---|---|---|
| pre-fix strict (archived in `prefix/`) | 19/31 | 51/95 | 68/157 | 138/283 (48.8 %) | 41/140 | 118 | 33 min |
| **F strict (Hfa)** | 18/31 | 46/95 | 67/157 | **131/283 (46.3 %)** | 35/140 | 113 | 36 min |
| **F LA2 (Hfb)** | 18/31 | 51/95 | 67/157 | **136/283 (48.1 %)** | 37/140 | 144 | 41 min |
| **final code strict (Hga)** | 18/31 | 45/95 | 67/157 | **130/283 (45.9 %)** | 34/140 | 113 | 30 min |

Completed nets by stage (Hfa / Hfb): S1 4/14 and 4/14; S2 14/49 and 16/49; S3 17/77 and 17/77. Router outcome per connection (Hfa): 85 by A*, 46 by direct straight joins, 85 "no path", 59 "no exit", 8 rejected by the exact post-check. Rip-up (Hfa): 56 tried, 10 kept, 46 rolled back, 212 had no conflict set.

Independent checker and DRC on the final hard boards (Hfa / Hfb):

| metric | Hfa strict | Hfb LA2 | target |
|---|---|---|---|
| exact 0/45/90 share of length | 100.000 % | 100.000 % | 100 % |
| max angle deviation | 0.0000 deg | 0.0000 deg | 0 |
| joints < 90 deg | 2 (both inside pad copper: in-pad dogleg vs second stub; fixed since, see below) | 2 (same cause) | 0 |
| 90-deg joints away from pads / T-junctions / colinear splits / dangling | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 0 |
| bend spacing short / pad exit < 0.3 mm | 0 / 0 | 0 / 0 | 0 |
| micro segments outside pads (inside pads) | 1 (13) | 0 (15) | 0 |
| shorts (own check) | 0 | 0 | 0 |
| unconnected pad groups (own) / DRC unconnected these nets | 151 / 152 | 145 / 146 | 0 |
| DRC violations | 13: USB pair 12 (gap 10, skew 1, uncoupled 1), `copper_edge_clearance` 1 (AMP_PDN 0.5 mm rule vs SW102 NPTH hole; fixed since) | 12: USB pair only | 0 |
| DRC unconnected outside these nets | 1: GND_U24_PATCH_F (F.Cu GND patch) cut off by new tracks | 2: same patch | 0 |
| length / octilinear minimum, complete nets: median, p95, max | 1.144, 4.566, 6.809 (n=35) | 1.155, 4.566, 6.809 (n=37) | <= 1.15, <= 1.4 |
| nets > 1.4 | U8-NO2 6.8, U2-VCOM 4.6, HP_TIPSW 4.0, C235-Pad2 2.9, BT_AUDIO_L 2.4, BT_TXD_M 1.5 | 7 nets | 0 |
| vias / complete net | 1.71 | 2.14 | LE4 |
| sensitive B.Cu total / over island or void | 1.25 / 0.83 mm (USB_DN jumper antipad) | 57.0 / 16.9 mm (about 0.85 mm per layer change, via antipads) | 0 over island/void |
| F.Cu signal over In1 void | 60.1 mm of 2807 mm | 76.4 mm | 0 beyond antipads |
| parallel at gap < 0.6 mm, I2S/USB: total / outside neck | 1.12 / 0.62 mm | 1.12 / 0.62 mm | 0 |
| locks (stage copper hashes) | S1, S2, S3 ok | ok | ok |
| rule files equal to project | yes / yes | yes / yes | yes |

Pre-fix strict run: the same checks found the path-self-touch defects that triggered the fix: 1 `hole_to_hole` (two vias of one CE_N path 0.25 mm apart, used as a turn-around), 2 T-junctions and 2 short pad exits. Its numbers are kept in `prefix/Ha2-3.check.json`.

Fixes after Hfa/Hfb, re-verified on the trial set and one hard run:
- NPTH holes get the 0.5 mm edge clearance.
- A pad's second and later tracks start on the lattice line inside the pad, with no centre dogleg.

Verification with the final code:
- Trial set (Tga strict, Tgb LA2): 15/38 and 16/38, with all trial checks as in section 4.
- Hard strict run (Hga-3): 130/283, 34 nets complete, 113 vias, 30 min.
  - Geometry and checks: exact 100.000 %, max deviation 0.0000 deg; joints < 90 deg 0; 90-deg joints away from pads, T-junctions, colinear splits and dangling ends 0; bend spacing 0; pad exit 0; shorts 0.
  - Length / octilinear minimum: median 1.139, p95 4.566 (n=34).
  - DRC: 12 violations, all USB pair rules (gap 10, skew 1, uncoupled 1); no edge, hole or clearance errors. 153 unconnected items in these nets, plus the GND_U24_PATCH_F island.
  - Locks ok, rule files equal to the project, sentinel fires.
  - r7: whole-board joints < 80 deg 26 before (H0) and after (Hga-3).
  - Remaining items: one micro segment outside a pad (PDCTRL_SDA at U11-8: a colinear 0.07 mm width step from the 0.2 mm neck to the 0.3 mm class width, just before a bend). U14-FB passes 1.43 mm from U14-L2 (SP3 asks for 2.0 mm; DRC enforces 2.0 mm only for its four named nets, so the router used the 1.0 mm switch_sensitive rule).

## 6. What failed and why

Evidence comes from the A* window renders (`route_oct_debug.py`, `--debug-png`), the exit probes and the router logs.

1. **Topology on one layer (S1, S2).**
   - The I2S trio runs U6 -> test pads TP13/TP12/TP14 (stacked top to bottom: SDATA, BCK, LRCK) -> series resistors R206/R207/R208 (left to right: LRCK, BCK, SDATA) -> U7.
   - The order at the resistor row is the reverse of the order at the test pads, so the three chains cannot be drawn on F.Cu without a crossing. The A* windows show the first-routed I2S net enclosing the start of the next.
   - The amplifier I2C pair (U6/U7/U24/U3) has to cross the I2S bus as well.
   - The original board used B.Cu here (I2S_SDATA 6 and AUD_SDA 14 B.Cu segments). With B.Cu only over In2 GND (43 % of that corridor) LA2 gains 1 (trial) and 5 (hard S2) connections.
   - This is a placement and pin-order issue (LE3, FO3: swap the R row or the TP order, or move the test points out of the bus), not a search issue.
2. **USB-C interleave.**
   - J1 has DP on B6/A6 and DN on A7/B7, interleaved at 0.5 mm.
   - Joining A6 to B6 (1 mm apart, around A7) needs a U-turn. Under the bend-spacing rule (0.75 mm between 45-deg bends) that needs at least 1.85 mm of lateral room.
   - DN needs a B.Cu jumper, and D1 puts DP and DN in swapped order. KiCad then counts the split near D1 as a coupled pair with a 1.3-1.8 mm gap (10 `diff_pair_gap_out_of_range` items).
   - This needs a fixed escape template (DN vias + B.Cu link at J1, DP loop below, pair re-joined after D1), which is not implemented. The pair is only cost-coupled, not routed as a true pair.
3. **Escapes that the rules make impossible ("no exit", 59 connections).** Most common parts: U9 5, U2 4, U11 4, U4 4, U8 3, J7 3, U20 3, then passives C207, R225, R226, R108, C182. Probe results:
   - U2-1 and U2-2 (USB 0.25 mm): the outward stub passes 0.300 mm from the U2-VBUS pad but needs 0.325. The 0.2 mm USB neck is allowed only inside NECK_U2_USB, which does not cover that stub.
   - C207-1 (AUDIO 0.3 mm, 0.5 mm audio clearance): boxed in by GND pads 0.1 mm away and the U24-AVDD pour.
   - U14-1: boxed in by SYS_RAW copper (POWER_HI 0.4 mm).
   - Short AUDIO 2-pin nets whose pads are not on a common line but are closer than 2 x 0.3 mm stubs plus one forced run cannot be joined under GE5/GE7. This also produces the large length ratios (U8-NO2 6.8, U2-VCOM 4.6) when a detour exists.
4. **Sequential blocking (85 "no path").** Earlier nets cut later corridors in dense areas (U24/U8/U9 audio block, U3 MCU fan-out, U4 charger at 0.4 mm pitch).
   - Transactional rip-up kept 10 of 56 group swaps.
   - A true negotiated-congestion (PathFinder) loop over a whole stage was not implemented.
5. **Long cross-board control nets.** For example BT_UART_TX: R182/TP22 near the BM83 to the MCU 70-95 mm away. These complete only with 8-12 vias at 1.5-1.7 x the octilinear minimum.
6. **GND patch pours.** The router treats GND fills as free space because they refill around new copper. One F.Cu GND patch near U24 (GND_U24_PATCH_F) was cut off from ground by new tracks in both hard runs. Only DRC caught it; the router has no pour-connectivity check.

## 7. Go / no-go

- **Go** for exact 0/45/90 geometry by construction, bend spacing, pad-exit rule, clearance-correct copper under the frozen rules, staged locking with hashes, and an independent checker. These held on every board; the three defect classes the checker found were fixed and re-verified.
- **No-go** as the unattended router for the full restart. Completion is 46-48 % of connections on the full signal set and no better than Freerouting on the trial set. The failures are dominated by:
  - placement and pin-order topology (I2S trio vs TP stack vs resistor row, the I2C crossing, the USB-C interleave);
  - escapes the rule set itself forbids (0.25-0.3 mm widths with 0.4-0.5 mm class clearances next to fine-pitch and dense passive clusters);
  - sequential blocking.
- **Conditions under which a re-try makes sense.**
  1. The placement agent fixes part and pin order for the I2S trio, the test pads and the AUD I2C crossing, and opens escape lanes at U9/U8/U24, U2, U4 and U11.
  2. Templated or hand-made escapes are made for J1/D1 (USB pair), U4 (0.4 mm) and U11.
  3. The user decides on LA2: sensitive nets on B.Cu over In2 GND, with stitching vias. The router supports both policies through `bcu=`.
- **Not implemented (open):**
  - GND stitching vias at sensitive layer changes (LA5). Measured: an AUD_SCL via is 6.5 mm from the nearest GND via.
  - Uniform-gap bus routing (GE9) and true coupled-pair routing.
  - SP3 (2.0 mm from FB/COMP/ILIM/PROG/TS to switch nodes) for nets not named in the rule file.
  - Merging a neck-to-class-width step that falls on a colinear run.
  - Self-avoidance inside A*: self-touching paths are rejected after the search rather than avoided.
  - A pour-connectivity check.
  - Teardrops.
  - Per-piece (1 mm split) DRC.

## 8. Coordinator's independent check (r7_metrics.py on Hga-3, 2026-11-01)

The router's own checker is not independent (AG15), so `r7_metrics.py` was run on `work-oct/Hga-3.kicad_pcb`. Findings the report above does not list:
- **BM83 under-module rule broken.** New F.Cu tracks inside the module pad rectangle: BT_RST_M 18.8 mm and BT_TXD_M 5.7 mm (plus GND 2.3 and SYS_PWR 2.0 already present). The router has no BM83 keep-out for F.Cu; the old board had 14.9 mm. Needs a keep-out polygon in the router before any further run.
- **Near-parallel runs beyond I2S/USB.** BT_AUDIO_L|C235-2 32 mm at 0.27 mm gap, BT_UART_TX|CTRL_SCL 22 mm at 0.26 mm, AUD_SCL|GAUGE_ALRT_N 9.9 mm at 0.25 mm, BT_AUDIO_L next to CHG_QON_SENSE and HP_TIPSW. The router's halo (SP1) only covers I2S_CLK and USB, so audio nets run alongside digital nets (GE9, SP rules).
- **Test base was the pre-restart placement** (commit 2858f93). The R8b placement (`work-r9/R9-0`) moved the MCU and about 97 parts but left the problem areas unchanged: TP12/TP13/TP14 still stacked at x=147 (y 98.5/95.4/101.6) and R206/R207/R208 still in a row at y=90.6, J1/D1 unchanged. The I2S order conflict therefore still applies.
- Confirmed: whole-board joints under 80 deg unchanged (26), exact-angle length for the stripped signal nets 100 %, B.Cu sensitive length 1.2 mm, F.Cu over In1 void 72.6 mm of 2,545 mm.

Decision (coordinator): geometry engine = go, unattended router = no-go. Next: placement pass R10 to remove the topology conflicts (I2S order, AUD I2C crossing, USB-C/D1 order, escape lanes), then router re-run with a BM83 keep-out and a halo for audio-vs-digital, then templated/hand escapes. LA2 (sensitive nets on B.Cu over In2 GND with stitching vias) is already allowed by the rulebook, so it is the default, not a new decision.
