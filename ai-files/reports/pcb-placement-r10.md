# PCB placement R10: routing-topology fixes (2026-11-02)

Agent: "Placement R10: routing topology fixes". Input: `ai-files/pcb/work-r9/R9-0.kicad_pcb` (same bytes as `work-r8/R8b-placement.kicad_pcb`). Output: `ai-files/pcb/work-r10/R10-0.kicad_pcb` with `R10-0.kicad_pro` and `R10-0.kicad_dru`, both identical to the project files (SHA-256 102fbee4… and aa88e8c9…). Nothing in `DesktopSpeaker-kicad/` or `work-r9/` was edited. No net, rule or schematic was changed. All edits are text edits of the board file (`scripts/apply_text.py`), and zones were refilled in a separate pcbnew process (`helpers/route_oct_refill.py`). Headless only: AppImage `kicad-cli` and `python3.11`, plus the scratch venv for shapely. Nothing was committed.

## 1. Result

| gate | R9-0 | R10-0 |
|---|---|---|
| DRC (`--severity-all --all-track-errors`, project rules) | 0 violations, 295 unconnected | **0 violations, 295 unconnected** |
| pad nets, 1192 pads compared by (ref, pad) | - | **0 differences** |
| parts on the bottom side / side changes | 0 / - | 0 / 0 |
| HA8 failing pairs, strict tiers (`r8b_ha8`) | 123 (a0.40 63, a0.25 29, b 3, c 28) | **123**, the same pairs |
| HA8 pairs new / tighter than R9-0 (AG3) | - | **0 / 0** |
| signal-net octilinear MST | 4389.42 mm | 4389.87 mm (**+0.01 %**) |
| decoupling distance, nearest cap to pin, every IC rail | - | unchanged |
| router S1, connections closed | 18/31 (old placement Hga 18/31) | **22/31**; 8/14 nets complete (R9-0: 3) |
| router S2, connections closed | 43/95 (old placement Hga 45/95) | **46/95**; 10/49 nets complete (R9-0: 12) |
| exit probe, failing pads of the 12 listed parts | 24 of 58 | **20 of 58** |
| exit probe, failing signal pads on the whole board | 67 | **56** |

- **Router runs.** Each run is the H0 procedure (strip all signal nets, refill, export, `route_oct_order.py`) followed by stage S1 and stage S2 once, using `--via-cost 1.5 --pair-avoid 1 --hweight 1 --max-exp 3e7`. Nothing was added to the router. Script: `work-r10/scripts/measure_s12.sh`.
- **Baseline.** The R9-0 baseline (B9) was measured the same way, because the 18/45 baseline came from the older pre-R8 placement.
- **S2 complete nets.** The count fell from 12 to 10 although connections rose from 43 to 46. The router is sequential, so complete-net counts move by ±2 between runs.
- **Minimum neighbour gaps.**
  - Board minimum: 0.000 mm (C243–U10, pre-existing, unchanged).
  - Minimum for each moved part: C170 0.196 (U2, unchanged pre-existing pair), C205 0.26, C234 0.29, D1 1.14 (J1, unchanged), R170 0.55, R206/R207/R208 0.42, R211 0.295 (U24, support-part tier 0.25), R226 0.55, R228 0.35, R252 0.125 (U25 hot-loop pair, unchanged), TP12/TP13/TP14 0.41.
  - 18 pairs that involve a moved part came closer than in R9-0. All 18 still meet their HA8 tier; the list is in `R10-it3`'s `it3.metrics.json`, key `pairs_shrunk`.

## 2. Moves (15 parts)

| ref | old x, y, rot | new x, y, rot | move | reason |
|---|---|---|---|---|
| R206 | 149.095, 90.618, -90 | 149.095, 91.900, -90 | 1.28 | I2S series R row moved down: opens the U24-16 (LRCK) and U24-18 (DOUT) escapes |
| R207 | 147.745, 90.668, -90 | 147.745, 91.900, -90 | 1.23 | same row |
| R208 | 146.395, 90.668, -90 | 146.395, 91.900, -90 | 1.23 | same row |
| R211 | 150.400, 92.600, 0 | 145.200, 88.100, 0 | 6.88 | cleared the room R206 needed; no legal spot within 4 mm; ADC_INT MST 25.6 -> 22.1 |
| TP14 (/I2S_LRCK) | 147.000, 101.600, 0 | 146.350, 95.400, 0 | 6.23 | TP column reordered to L, B, S top to bottom, the same order as the R row; x set so that every I2S chain is U6 -> TP -> R -> U7 |
| TP12 (/I2S_BCK) | 147.000, 98.500, 0 | 146.350, 98.500, 0 | 0.65 | same column |
| TP13 (/I2S_SDATA) | 147.000, 95.400, 0 | 146.350, 101.600, 0 | 6.23 | same column |
| D1 | 145.230, 29.340, 0 | 145.230, 29.340, 180 | rot | ESD order DN west / DP east, consistent with U2 (section 4) |
| C170 | 152.450, 64.480, 0 | 152.600, 64.480, 0 | 0.15 | clears the U2-2 (D-) escape |
| R170 | 150.500, 65.230, 90 | 150.500, 65.798, 90 | 0.57 | its VBUS feed track no longer runs under U2 pins 1 and 2 |
| R228 | 170.940, 69.840, 90 | 169.690, 70.290, 90 | 1.33 | opens the U8-1 escape |
| R226 | 172.290, 60.650, 180 | 171.840, 60.800, 180 | 0.47 | opens the R226-1 escape without blocking U8-10 |
| C234 | 192.340, 38.800, -90 | 192.340, 38.800, 90 | rot | pad swap: C234-1, C234-2 and R224-1 escapes |
| C205 | 192.490, 41.400, -90 | 192.890, 41.800, -90 | 0.57 | opens the C204/C234 escapes |
| R252 | 150.300, 146.550, -90 | 150.300, 146.300, -90 | 0.25 | U25 FSW resistor, opens one U25-area escape; hot-loop limit is 0.3 mm |

**Retained copper.** Retained copper was dragged with the parts and kept on 0/45/90. Nothing was ripped.
- **D1.** The GND stub was redrawn from pin 4 to the west, and its via moved from (146.8, 29.75) to (143.6, 28.84).
- **R211.** The GND stub and via moved with the part; the via is now at (145.80, 89.10).
- **U2-VBUS (C170/R170).**
  - pin 3 to C170 to R170 is now a straight vertical 0.4 mm track at x 151.955 plus a 0.6 mm horizontal track at y 65.20;
  - two crooked segments and one dangling 5V_CODEC stub were deleted;
  - the 5V_CODEC link from R170-1 to the via at (151.25, 66.135) is now a 45/0 pair of segments;
  - the U2 pin 4 GND track now steps 45 degrees around C170 pad 1.
- **Teardrops.** 5 teardrop zones next to the edited copper were removed; regenerate them after routing.
- **Silkscreen.** The three I2S TP net labels follow their TPs. With the swap they now name the correct pads (TP13 = I2S_SDATA, TP14 = I2S_LRCK); before, they were swapped. The I2S_LRCK label is at y 94.6 to stay off TP15's outline. The footprint *values* of TP13/TP14 are still stale and were not edited.

## 3. I2S trio and AUD I2C (problems 1 and 2): what placement can and cannot do

**Proof that the requested single-layer route does not exist.**
- U6 and U7 are fixed and identical, both at rotation 180, with the bus pins on their north edge. West to east, both have pins 16 SCL, 15 SDA, 14 SDATA, 13 BCK, 12 LRCK.
- Every net's tree contains a path from U6 to U7. The plane outside two disjoint pads is an annulus, and non-crossing curves between its two boundaries need the counter-clockwise pin order at U6 to equal the clockwise pin order at U7. Here one is the reverse of the other.
- So any two of these nets must cross an odd number of times unless one of them wraps around an amplifier. A rainbow route (no wrap) can carry only one net.
- The source has the same problem. The three series resistors carry U24's pin order, and U24's south-facing row (LRCK 147.3, BCK 147.8, DOUT 148.3) is mirrored against both amplifiers.
- Consequences:
  - no TP or resistor order makes the three chains crossing-free on one layer;
  - the I2C pair must cross the I2S trio (2 × 3 net crossings);
  - one-layer completion is bounded at about 5 of the 9 I2S connections;
  - the minimum is 2 B.Cu hops for the I2S reversal (n − LIS = 3 − 1) and 4 for all five nets.
- The rule file already allows /AUD_SDA and /AUD_SCL on In2 (`in2_power_only` exemption). That is the cleanest way to cross the I2S bus; the router never uses In2.

**What R10 does.**
- **Hub order.** The TP column order now matches the R row (TP→R hop is planar). The column sits at x 146.35, west of R208, so the router builds the same chain order U6 → TP → R → U7 for all three nets. In R9-0 the LRCK chain took a different order.
- **U24 escapes.** The R row moved 1.2 mm down, which gives U24-16/18 room for a stub, a 45-degree jog and a forced run.
- **Measured I2S result.** 4/9 (R9-0) → 5/9 (R10). SDATA is complete; BCK and LRCK are 1/3 each.
- **Measured AUD I2C result.** 2/10 → 4/10. The remaining I2C failures are the inherent crossing with I2S plus U24-23/24, which sit east of U24's I2S pins on the same row.
- **Where the inherent reversals are.** On the long U6 and U7 legs, which have room for B.Cu jumpers over In2 GND (LA2).

## 4. USB (problem 3)

**Cause.** J1 and U2 both face south, so the pair reaches U2 through a U-turn under the pins, and a U-turn swaps west and east. The single-layer-change topology is therefore:
1. At J1, DP dives to B.Cu: B6 and A6 are joined on B.Cu, emerging east of B7. DN joins A7 and B7 on F.Cu. The pair then leaves heading south with DN west and DP east.
2. D1 is rotated 180 degrees, so DN is on the west column and DP on the east column. DP enters pin 3 from the east; DN passes north of D1 and the new GND via and enters pin 5 from the west.
3. R173-1, R171-1 and R172 are unchanged. DN reaches R172-1 west of R171.
4. Under U2 the pair U-turns with D+ inside at pin 1 (150.66) and D- outside at pin 2 (151.31). That inner/outer order now matches.

This is the J1 template the router does not have (report `routing-toolchain-oct` section 6.2). It is the only layer change.

**Escapes.** C170 and R170 no longer sit in the U2-1/2 escape: both pads pass the 1.0 mm probe (R9-0: blocked by the VBUS track).

**Measured.**
- USB_DP: 3/4 → 4/4 (complete).
- Net-(U2-D+): 0/1 → complete.
- USB_DN: 2/3 → 1/3.
- Net-(U2-D-): still 0/1.

**Why D- still fails.** In every run the router routed D+ the long way round R172 (west of R172, then under it) instead of in the 1.2 mm gap between R172 and U2-1, and that enclosed D-. This is routing order, not a missing lane. Moving R171/R172 side by side was tried and blocked by D7 (HA8), the 5V_LOGIC via at (150, 62.2) (HA6) and tile silk.

**Gap rule at D1.** The D1 package puts DP and DN on opposite columns, so a local pair split of about 1.4 mm at D1 is unavoidable (`diff_pair_gap` items at D1, as before).

## 5. Escape lanes (problem 4)

**Probe.** `scripts/exitprobe.py` runs a straight 0.25 mm track, 0.2 mm inside a neck area, 1.0 mm outward from the pad edge, against the router's own clearances (`route_oct_rules.clr_strict` / `clr_neck`). Fine-pitch pads leave outward only. GND fills are ignored because they refill.

Listed parts, failing pads (R9-0 → R10):

| part | R9-0 | R10 | remaining blocker (shortfall mm) | placement-fixable? |
|---|---|---|---|---|
| U9 | 3 | 3 | GND vias beside pins 1, 2, 4 (0.005 / 0.045 / 0.055) | no: needs the vias moved about 0.1 mm (copper edit) |
| U2 | 4 | 2 | pin 15 VOUTR: VCCP2I power track (0.5 audio rule); pin 20 XTO: Y170-1 pad (0.010) | no: Y170 cannot move 0.05 mm without HA8/HA6 failures (C173, C178, GND vias); VCCP2I is copper |
| U11 | 2 | 2 | pin 36: own pin 34 (0.024, neck geometry); pin 37: VIN_LOW track (0.05) | no (copper / footprint) |
| U4 | 5 | 5 | BTST2 hot-loop track (pin 18 BATP needs 2.0 mm); BAT_U4PIN_F pour (pins 20, 21, 24) | no: needs pour/hot-loop redraw |
| U8 | 4 | 3 | pin 2: GND track; pins 6/7: 3V3_AUDIO feed track | partly: pin 1 fixed by moving R228 |
| U20 | 3 | 3 | C124 pads, USB_AUX_5V/SYS_RAW tracks | no: hot-loop caps with power copper |
| C207 | 1 | 1 | own GND stub and the U24-AVDD F.Cu track (0.5 audio rule) | no (copper) |
| C182 | 1 | 1 | the C182/C183 GND bar | no (copper) |
| R226 | 1 | 0 | - | yes, moved |
| J7, R225, R108 | 0 | 0 | - | - |

Also fixed: U2-1, U2-2, U24-16, U24-18, C234-1/2, R224-1 and C204-2. Not fixed: U24-4 (VREF cap C212) and U24-30 (C210), because moving those caps would worsen VREF/input decoupling.

The router's own "no exit" log over S1+S2 changed from U9 5, U8 4, U2 3, C207 2, R226 2 to U9 5, U8 5, U2 2, C207 2, R226 2. Its exit model (stub plus forced 45-degree run) is stricter than the probe, so R226-1 still fails in the router.

## 6. Iterations (AG13: 3 used)

| iteration | change | S1 | S2 | probe, whole board |
|---|---|---|---|---|
| R9-0 (B9) | baseline | 18/31 | 43/95 | 67 |
| it1 (`R10-it1`) | R row down, R211, TP swap, D1 rot 180, C170/R170 with VBUS rework, R228, R226 | 21/31 | 46/95 | 57 |
| it2 (`R10-it2`) | + TP column x 146.35 (uniform chain order), C170 +0.05, greedy C234/C205/R252 | 22/31 | 46/95 | 57 |
| it3 = **R10-0** | + R226 re-placed (the it1 spot blocked U8-10; a probe-radius bug was found and fixed) | **22/31** | **46/95** | **56** |

**Rejected options.**
- TP column at x 144–145: the labels would have to cross TP15 or the tile line.
- R211 within 4 mm: no legal spot (silk, H2 hole, R209, U24).
- Y170 nudges (HA8/HA6) and R171/R172 side by side (D7, via, silk).
- An R row shifted west: LRCK jog 1.6 mm.

## 7. Open problems

1. **I2S and I2C cannot be single-layer** (proof in section 3). Decide on B.Cu hops (LA2, at least 2 for I2S) and/or AUD I2C on In2, which the rule file already allows.
2. **USB.** The J1 DP-dive template and the D-/D+ nesting at U2 need a templated escape or a hand route; the router encloses D-.
3. **Copper-bound escapes.** These need copper edits, not placement: GND vias at U9 (pins 1, 2, 4), U10-1, U15-2/4, R120 and R102 (0.005–0.05 mm each); the U8 3V3/GND feed tracks; the U4 BTST2/BAT pour; U20; C182/C183; C207/AVDD; the U2 VCCP2I track; J1-B5 (VBUS via).
4. **Stale TP values.** The TP13/TP14 footprint values ("I2S_LRCK"/"I2S_SDATA") are still stale; the silk labels are now correct.
5. **Regeneration.** Teardrops (5 removed), position files and fab output must be regenerated after routing.

## 8. Files (`ai-files/pcb/work-r10/`)

- **Boards.** `R10-0.kicad_pcb/.kicad_pro/.kicad_dru` (final). Intermediates `R10-it1/2/3*`. Router runs `B9-*`, `I1-*`, `I2-*`, `I3-*` (stripped H0 boards, S1/S2 boards, `.route.json`, `.drc.json`, logs `*.measure.log`). These are scratch and large; do not commit them.
- **Plans and gate outputs.** Plans `plan-it1/2/3.json`; apply reports `it*.apply.json`; gates `it*.metrics.json`; dumps `r9.json`, `it*.json`; probe outputs `B9.exitprobe.txt`, `I3.exitprobe.txt`, `r9.allexits.txt`, `it3.allexits.txt`.
- **Scripts (`scripts/`).**

| script | role |
|---|---|
| `apply_text.py` | text-level pose / copper / label editor |
| `r10lib.py` | legality model: HA8 + AG3, HA6, copper clearance, silk, outline, exit probe |
| `place_search.py` | local pose search |
| `greedy_exits.py` | greedy escape pass |
| `exitprobe.py` | listed-part probe |
| `metrics.py` | gates |
| `measure_s12.sh` | router measurement |
| `routesum.py`, `crop.py`, `silk_extract.py`, `t_*.py` | helpers |

- **Evidence (`evidence/`).** `r9-*.png`, `r10-*.png` crops of the I2S hub, U2 and J1, and the routed S1 at U2.
