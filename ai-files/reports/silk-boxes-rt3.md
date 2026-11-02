# Silkscreen section boxes RT-3: one tiling of the board (2026-11-02)

Agent: "Silkscreen section boxes tiling".
- **Input.** `ai-files/pcb/work-route2/RT-2.kicad_pcb`, read only. Its SHA-256 is unchanged (`dbd01106…`).
- **Output.** `ai-files/pcb/work-route3/RT-3.kicad_pcb`. `RT-3.kicad_pro` and `RT-3.kicad_dru` are byte copies of the RT-2 files.
- **Method.** Text-level edit of F.SilkS board graphics only, by `ai-files/helpers/silk_tile.py`.
- **Gates.** Independent script `ai-files/helpers/silk_tile_gate.py`.
- **Tools.** Headless only: AppImage `kicad-cli` and `python3.11`, plus Chrome `--headless` for the PNGs. Nothing was committed or published.

## 1. Result

| gate | RT-2 | RT-3 |
|---|---|---|
| G1: board text with the F.SilkS `gr_*` items removed | - | **byte-identical** (5 507 241 bytes); F.SilkS `gr_*` items 203 → 171 |
| G2: footprints (360), position / rotation / side | - | **0 moved** (each footprint block is also byte-identical through G1) |
| G3: DRC (`--severity-all --all-track-errors`, project rules) | 0 violations, 152 unconnected | **0 violations, 152 unconnected** |
| G4: box segments, end sharing | 88 lines + 3 arcs, open ends, frame gaps | **58 segments**: 30 T points (3 ends), 7 corners (2 ends), 12 ends on the region boundary; 0 dangling, 0 four-way, 0 unsplit T, 0 overlaps, 0 diagonals |
| G5: tiling | 26 faces, several untitled or with two titles | **22 faces, one title each**; face areas sum to 17 332.56 mm² = region; 18 rectangles, 4 rectilinear |
| G6: line clearances | - | **0** violations: every exposed pad ≥ 0.2 mm (minimum 0.255, R112); no courtyard, footprint silk, footprint text, board text or mounting-hole square crossed |

- **Other clearances.** The closest courtyard is H2 at 0.029 mm. The closest mounting-hole square is 0.175 mm away (silk to silk).
- **Silk DRC.** Silk DRC items before and after: silk_over_copper 0 → 0, silk_edge_clearance 0 → 0, silk_overlap 0 → 0.
- **Idempotent.** Running `silk_tile.py` on RT-3 reproduces RT-3 byte for byte.

**Region and frame.** The tiled region is the Edge.Cuts rectangle inset by 0.4 mm: x 86.65..213.35, y 20.4..157.2.
- There is no outer frame line. The board edge closes the tiling, and every outer box edge ends 0.4 mm from the edge.
- Why no frame: a frame at 0.4 mm would pass 0.05 mm from the J1 shell pads (y 20.52). It would also cross J1, J2, J3, SW100, J9–J11, SW101 and J5, which overhang the outline.
- The old frame at 1.0 mm was broken at every connector. It is removed, together with its three corner arcs.

## 2. Sections

The coordinates are mm. "Parts" counts the F-side footprints whose centre lies in the region; the 359 parts are each in exactly one section, and LOGO1 is on B.Cu.
- **Membership.** Membership follows the RT-2 boxes. As in RT-2, a few parts sit in the box of their neighbourhood rather than their schematic sheet: R106 (charger sheet) in MCU, TP26 in ADC, R258 in Charger FETs, R259 in MCU, TP25 (MCU sheet) in SWD Header, and SW100/R113 in Wake.
- **Holes.** The holes are assigned by position.

| section | region (x0–x1 × y0–y1) | shape | RT-2 box | parts | title (size, at) |
|---|---|---|---|---|---|
| Bluetooth | 86.65-127.50 × 20.40-55.90 | rect | 87.25-126.3 × 21-55.9 | 29: C150, C152-154, C190-195, J8, L3, R150-154, R180-187, TP9, TP22, U1, U15 | 1.4 at (92.21, 21.72) |
| Wake | 127.50-143.00 × 20.40-40.52 | rect | 130.2-143.35 × 21-31.2 | 3: H7, R113, SW100 | 1.4 at (130.66, 21.72) |
| USB-C Jack | 143.00-169.55 × 20.40-40.52 | rect | 143.35-160.85 × 21-44.3 | 7: C5, C316, D1, D5, D6, J1, U19 | 1.4 at (162.457, 21.72) top-right |
| Audio Connectors | 169.55-213.35 × 20.40-45.00 | rect | 170.25-203.45 × 21-46.1 | 17: C204, C205, C234, C235, C246, D200, D201, J2, J3, R224, R225, R239-244 | 1.4 at (179.31, 40.22), below J2/J3 |
| USB-C PD | 127.50-147.95 × 40.52-68.70 | rect | 126.29-148.0 × 44.26-69.1 | 22: C2, C6, C181-184, C315, D7, J4, R10-18, TP1, TP5, TP23, U11 | 1.4 at (133.66, 45.09), below J4 |
| USB Audio Codec | 147.95-169.55 × 40.52-68.70 | rect | 148.0-170.25 × 44.3-69.1 | 20: C170-178, C186, C187, R170-176, U2, Y170 | 1.4 at (157.677, 41.84) |
| 5V Codec Rail | 169.55-213.35 × 45.00-56.80 | rect | 170.25-194.25 × 46.1-56.3 | 8: C221, C222, C224, C225, H5, R212, U22, U23 | 1.4 at (177.643, 46.32) |
| Source Mux + Headphone | 169.55-213.35 × 56.80-75.75 + 165.95-169.55 × 68.70-75.75 | rectilinear (foot) | 170.25-204.55 × 56.3-73.5 (open) | 33: C230-233, C236-241, C243-245, R220-223, R226-238, U8-10 | **1.0** at (203.002, 57.8) top-right |
| Gauge + LC Power | 86.65-110.40 × 55.90-91.40 | rect | 87.25-110.43 × 66.9-91.5 | 24: C120, C124-126, C130-132, H9, Q104, R120-122, R124-127, TP3, TP4, U5, U13, U16, U17, U20, U21 | 1.4 at (97.243, 64.72), below H9 |
| 3V AO | 110.40-117.00 × 71.30-80.60 | rect | 110.43-116.81 × 71.5-80.4 | 3: C122, C123, U12 | 0.9 (as RT-2) at (113.024, 72.327) |
| MCU | 110.40-127.50 × 55.90-91.40 minus 3V AO, + 127.50-137.30 × 68.70-91.40, + 130.00-137.30 × 91.40-93.30 | rectilinear | L 87.25-137.0 × 55.9-93.3 | 11: C160-162, H8, J7, R106, R160, R259, TP19, TP21, U3 | 1.4 at (113.193, 57.22) |
| ADC | 137.30-165.95 × 68.70-93.30 | rect | 137.0-165.95 × 69.1-93.3 | 40: C200-203, C206-220, C223, C226, C227, FB200, R200-211, TP6, TP8, TP26, U24, Y200 | 1.4 at (139.86, 70.02) |
| SWD Header | 165.95-188.20 × 75.75-103.13 | rect | 165.95-196.65 × 73.5-101.1 (open) | 2: J6, TP25 | **1.0** at (170.988, 76.836) |
| Battery | 188.20-213.35 × 75.75-114.86 | rect | 196.65-212.75 × 73.5-112.9 + SW101 sub-box | 4: H6, J5, R101, SW101 | 1.4 at (192.46, 77.07) |
| Charger FETs | 162.40-188.20 × 103.13-114.86 | rect | 162.55-188.25 × 101.1-115.5 | 10: Q100-103, R107, R109-112, R258 | 1.4 at (169.893, 104.45) |
| 5V Logic | 86.65-103.50 × 91.40-109.30 | rect | 87.25-102.25 × 91.5-108.5 | 9: C140-142, L2, R140-142, TP7, U14 | 1.4 at (91.777, 92.72) |
| Volume Encoder | 103.50-130.00 × 91.40-109.30 | rect | 102.25-131.45 × 91.5-109.5 | 4: C308-310, SW102 | 1.4 at (112.527, 92.72) |
| Test Points (**new title**) | 130.00-165.95 × 93.30-103.13 + 130.00-140.75 × 103.13-109.30 | rectilinear (L) | untitled gap | 8: H2, TP12-18 | **1.2** at (153.894, 101.95), below H2 |
| Charger | 140.75-162.40 × 103.13-136.40 + 162.40-172.50 × 114.86-136.40 | rectilinear (L) | 140.55-162.55 × 104.5-134.0 | 26: C100-112, C311-313, H3, L1, R100, R102, R103, R108, TP2, TP11, TP27, U4 | 1.4 at (145.377, 104.45) |
| Front Amp U6 + Filters | 86.65-140.75 × 109.30-157.20 | rect | 87.25-132.75 × 114.1-156.6 | 32: C271, C272, C276, C278, C280-288, C302-305, H1, H4, HA1, J9, J10, L201-204, R257, R262, TP10, TP20, TP24, U6 | 1.4 at (99.777, 110.62) |
| Boost Converter | 140.75-172.50 × 136.40-157.20 | rect | 132.75-172.45 × 134.0-156.6 | 26: C260-270, C275, C277, C279, C290, C292, C314, L200, R250-256, U25 | 1.4 at (149.743, 137.72) |
| Woofer Amp U7 | 172.50-213.35 × 114.86-157.20 | rect | 172.45-212.65 × 118.6-156.6 | 21: C273, C274, C289, C291, C293-301, C306, C307, HA2, J11, L205, L206, R261, U7 | 1.4 at (181.193, 116.18) |

**The requested example.** The Front Amp top moved up from y 114.1 to 109.3, which closes the 4.8 mm empty strip.
- 5V Logic and Volume Encoder now share both edges: top 91.4 and bottom 109.3.
- The line between them (x 103.5) meets the Front Amp top in a T.

**Long shared edges.** These edges each run as one straight line:
- y 55.9: Bluetooth bottom.
- y 68.7: from x 127.5 to 169.55.
- y 109.3: from the left edge to x 140.75.
- y 114.86: from x 162.4 to the right edge.
- x 127.5: from the top edge to y 68.7.
- x 140.75: from y 103.13 to the bottom edge.
- x 172.5: Boost | Woofer.
- x 188.2: SWD and FETs | Battery.

**Other changes.**
- The SW101 sub-box is merged into Battery.
- The untitled boxes around H5, H7 and R228 and the empty strip at x 160.85–170.25 are absorbed into their neighbours.

## 3. Why four sections are not rectangles

Parts may not move, so these were forced. Each case was checked at pad level, which is the weakest constraint used.

1. **MCU, an L shape with the 3V AO notch.**
   - R160 sits against the U3 corner, so R160 and U3 must share a box. That puts the MCU west edge at x ≤ 119.5.
   - So H8 (x 113.35–120.94) is inside MCU.
   - The PD/MCU edge must pass between the TP23 pad (bottom 67.0) and the R160/U3 pads (top 69.98). In that window the TP21 pad (114.6–116.4 × 66.3–69.7) blocks it.
   - So MCU wraps J7 and TP21 in an arm up to y 55.9.
   - U12/C122/C123 (x 111.1–116.1) overlap H8's x range, so 3V AO is a notch in MCU's west side.
   - The 1.9 mm step at x 130–137.3: west of x 130 the edge is at y 91.4, which leaves room for the Volume Encoder title above SW102. East of it the edge must stay at 93.3, between R206–R209 (bottom 93.11) and H2.
2. **Test Points, an L shape.**
   - The TP12–14 pads end at x 148.05 and the L1 pads start at 148.32, 0.27 mm apart, so no vertical edge fits.
   - TP17 and the AUD_SDA label reach y 108.92, while L1 starts at 106.73.
   - So the Charger top edge is at y 103.13 east of x 140.75 only.
3. **Charger, an L shape.** Mounting hole H3 sits in the pocket between Charger, Charger FETs, Woofer and Boost. Any rectangle for it would be an empty, untitled box, so the pocket joins Charger.
4. **Source Mux + Headphone, with a 3.6 × 7.05 mm foot.**
   - The vertical spine has to step at y 68.7. The C187 reference text (x 166.45–168.94) forces the upper spine to x ≥ 169.02, and the R176 pad excludes anything west of it.
   - The J6 outline (x 166.82) forces the lower spine to x ≤ 166.75.
   - Iteration 1 used one straight spine at x 166.87. DRC then reported 6 `silk_overlap` items: J6 outline × 5 and C187 reference × 1.
   - Upper spine: x 169.55. Lower spine: x 165.95.

## 4. Titles and labels

**Title rule** (data in `TITLES`):
1. top-left, 0.4 mm inside the box;
2. else top-right;
3. else 1.2 mm, then 1.0 mm, at top-left or top-right;
4. else the free spot nearest the top-left corner.

Height and thickness are kept unless shrunk.

**Free means:** not over a pad (+0.15 mm), a part body (courtyard −0.25 mm), footprint silk or text, a board label, a mounting-hole square or a box line.

**Where the titles went:**
- 16 at top-left.
- USB-C Jack and Source Mux at top-right.
- Audio Connectors, USB-C PD, Gauge and Test Points at the nearest free spot: J2/J3, J4, H9 and H2 fill their top-left corners.

**Sizes:**
- Source Mux + Headphone 1.4 → 1.0 (there is no 28 mm free run).
- SWD Header 1.4 → 1.0 (J6 and TP25 fill the top).
- Test Points is a new title at 1.2. It names the old untitled test-point area (TP12–TP18 and H2).
- The other 19 keep 1.4, and 3V AO keeps 0.9.

**Other moved silk:**
- The Bluetooth rune (5 lines, 0.2 mm wide) moved with the Bluetooth title, keeping a 1.55 mm gap. Its bounding-box minimum went from (100.32, 53.85) to (98.92, 20.82).
- 21 existing titles moved (positions in the table) and 1 was added.

**Net and pin labels:** none moved, because no new edge crosses a label. The Rev A / V1.0 texts, J9/J10/J11 labels and +/− marks did not move either.

## 5. Soft notes and open problems

- **U5 reference text.** It is a footprint text at x 99.4–100.8, y 91.52–92.58, just below the Gauge | 5V Logic edge (y 91.4), so it reads inside 5V Logic. In RT-2 the old edge at 91.5 crossed it. Moving the edge below it would leave no room for the Volume Encoder title. Footprint texts were not edited.
- **Tight courtyard gaps.** Lines come close to H2 (0.029 mm), R112 and TP13 (0.06 mm) and C120 (0.07 mm) without crossing. Pads stay ≥ 0.255 mm away.
- **Line ends near the edge.** Box line ends sit 0.4 mm from Edge.Cuts. DRC `silk_edge_clearance` is clean with the project rules; a fab that clips silk within 0.5 mm of the edge would shorten each end by ≤ 0.1 mm.
- **Reusing the script on a later board.** `silk_tile.py` reads part-independent data: edges, titles and the rune target. A later board with the same placement can be processed directly. If parts move, rerun `silk_tile_gate.py` (G6 checks pads, courtyards and silk), then adjust the named edges at the top of the script. The title positions came from an offline placer (scratch). After a placement change, re-check them with G5/G6 and the PNGs.
- **Iterations: 3.**
  - It1: straight spine; DRC 6 `silk_overlap`; Volume Encoder had no title room.
  - It2: spine step, y 91.4 west edge, 0.2 mm pad and silk gates clean.
  - It3: title nudges (Source Mux, SWD, Test Points).

## 6. Files

| file | role |
|---|---|
| `ai-files/pcb/work-route3/RT-3.kicad_pcb`, `.kicad_pro`, `.kicad_dru` | output board; pro/dru are copies of RT-2 |
| `ai-files/pcb/work-route3/fp-lib-table`, `kicad-library` (symlink) | library access for kicad-cli beside the work copy |
| `ai-files/pcb/work-route3/RT-3.drc.json`, `evidence/RT-2.drc-baseline.json` | DRC after / before, same command and rules |
| `ai-files/pcb/work-route3/RT-3.gate.json` | gate output, including the face list |
| `ai-files/pcb/work-route3/RT-3.silk_tile.json` | apply report (removed items, 58 segments) |
| `ai-files/pcb/work-route3/evidence/rt2-silk.png`, `rt3-silk.png` | before / after, F.SilkS + Edge.Cuts |
| `ai-files/pcb/work-route3/evidence/rt2-silk-mask.png`, `rt3-silk-mask.png` | the same with F.Mask openings |
| `ai-files/pcb/work-route3/evidence/rt3-tiling-parts.png` | new lines over part extents coloured by section |
| `ai-files/helpers/silk_tile.py` | the edit (plain `python3`; section regions, edges and titles as data at the top) |
| `ai-files/helpers/silk_tile_gate.py` | gates G1–G6 (AppImage `python3.11`, pcbnew) |

**Reproduce:**
```
python3 ai-files/helpers/silk_tile.py ai-files/pcb/work-route2/RT-2.kicad_pcb ai-files/pcb/work-route3/RT-3.kicad_pcb
cd ai-files/pcb/work-route3 && ~/Applications/kicad.AppImage kicad-cli pcb drc --severity-all --all-track-errors --format json -o RT-3.drc.json RT-3.kicad_pcb
~/Applications/kicad.AppImage python3.11 ai-files/helpers/silk_tile_gate.py ai-files/pcb/work-route2/RT-2.kicad_pcb ai-files/pcb/work-route3/RT-3.kicad_pcb --drc-base ai-files/pcb/work-route3/evidence/RT-2.drc-baseline.json --drc-new ai-files/pcb/work-route3/RT-3.drc.json
```

## Update 2026-11-02 (owner request)
- MCU title moved from the top-left of its box to just below U3 (centre 128.2, 87.0; free gap between the caps at y 84-85 and the NRST button).
- New label "TC2030" (size 1.0, thickness 0.15) at (122.4, 58.4), directly above J7 (TC2030 pads x 118.4-126.4, y 59.75-68.25). Defined in `EXTRA_LABELS` in `helpers/silk_tile.py`; the gate ignores it as a title.
- Re-applied with `silk_tile.py` (idempotent), gates G1-G6 all pass, DRC 0 violations / 152 unconnected (same as before). The hand-routing board RT-4 must get the same silkscreen by running `python3 ai-files/helpers/silk_tile.py RT-4.kicad_pcb RT-4s.kicad_pcb` at the end.
