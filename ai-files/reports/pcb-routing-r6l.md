# Routing R6l (2026-10-09): R6k review conditions A1, A2, minors, then the overspec pass

Work copies only (`ai-files/pcb/work-r6/`). `DesktopSpeaker-kicad/` was not touched, nothing was committed, no process was killed, no sub-agents were used, and no router ran (`route_r6i_route.py` not needed, so no prune risk).

- **Final board:** `work-r6/R6l-final.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`, `.drc.json`, `.open2.json`, `.isl.json`, `.bends.json`). `R6l-0.*` is a byte copy of R6k-final, used as the baseline.
- **Rules:** `R6l.kicad_pro` / `R6l.kicad_dru` and the final `.kicad_pro`/`.kicad_dru` are byte copies of the R6k files (checked with `cmp`). No rule, rule area or netclass was added, relaxed or moved.
- **Renders:** `ai-files/pcb/route-r6l-top.png`, `route-r6l-bottom.png`, `route-r6l-in2.png`.
- **Specs and logs:** `work-r6/r6l/`:
  - edit specs `l1.json` (A1), `l2.json` (A2), `l3.json` (minors);
  - neck and cut case files;
  - `capacity.txt`, `final.gates.txt`;
  - width statistics `wstat0/wstat_final`, pour areas `pour0/pour_final`;
  - widening state `R6l-4.widen.json` and log `widen2.log`, pour-growth state `R6l-5.zgrow.json`.

  Intermediate boards were deleted.

Ratings below use IPC-2221 at a 15 K rise, the same basis as the review:
- outer 1 oz: 1.0 mm = 2.9 A, 2.0 mm = 4.7 A, 2.43 mm = 5.4 A, 3.1 mm = 6.5 A, 3.56 mm = 7.2 A, 5.9 mm = 10.3 A;
- inner 0.5 oz: 6.28 mm = 3.0 A, 7.24 mm = 3.3 A.

"Widest" is the widest single path (`route_r6k_neck.py`, 0.1 mm grid). "Cut" is the narrowest total cross-section (`route_r6k_cut.py`).

## Gates (R6l-0 = R6k-final → R6l-final)

| Gate | Before | After |
|---|---|---|
| Open edges (fragment-aware) | 2 (J7 NRST/SWCLK) | **2**, the same two |
| DRC clearance / shorts / dangling / isolated / track width | 0 | **0** |
| DRC USB items | 3 skew, 1 uncoupled 17.34 mm | unchanged; USB copper identical (52 items, compared item by item) |
| DRC silk/lib | 37 | 37. The TP2 `SYS_RAW` board text was moved 3.95 mm down, below TP2, because the moved C106 pad sat under it. |
| Strict DRC (copy with every track split into 1 mm pieces, see below) | 3 inherited items | the same 3 inherited items, nothing new |
| Power connectivity | 0 power open edges | 0. The union of every split pour is 1 piece per net and layer (`route_r6l_union.py`). |
| Island continuity | 1 outline per island | 1 outline per original island. In2 unions are 1 piece each for PVDD, VBUS_PD, USB_VBUS, BAT_INT, BAT_PACK and SYS. |
| Foreign non-GND vias in In2 islands | 32 | 32 (the Q103-G via moved inside the same SYS column) |
| In2 slow signals to an island outline | ≥ 0.32 mm | ≥ 0.35 mm (grown islands stop 0.35 mm away) |
| AUDIO / I2S / USB / clock copper on In2 | none | none |
| Corner hits (`route_r6i_bends.py`) | 7 | **7**, all inherited |
| Via centre in SMD pad | 3 | **3** (R10.2, R224.1, C215.1) |
| Audio/I2S vias without a GND via within 1.2 mm | 8 | 8 |
| Net of any via/track/pad changed (`route_r6l_netcmp.py`) | – | 0 |
| Vias | 955 | 957 (GND +2: C106/R102 split; PVDD +1 at C271; SYS 3 moved) |

**Strict DRC check.** KiCad applies `intersectsArea('NECK_*')` and `intersectsCourtyard()` to a whole item. So a long track, or a pour, that touches a neck area gets the relaxed 0.2 mm neck clearance over its whole length.
- The first widening attempt exploited this: 2 hidden violations appeared once the copy was split, so that attempt was discarded and redone with the strict check.
- The strict check DRCs a copy with every track split into 1 mm pieces (`route_r6l_splitall.py`), so rules apply per piece.
- The 3 items it reports in **both** R6l-0 and R6l-final are inherited:
  - 5V_LOGIC to SYS_RAW on In2: 0.3991 vs 0.4 mm at 96.7, 94.9;
  - two 0.2 mm audio pin escapes (U24 XI, VINR2) whose pieces fall just outside NECK_U24;
  - the USB pair gap pieces at the J1 bridge.
- Pours that touch a neck area were not grown at all. Their growth went into separate companion zones that touch no neck area or courtyard, so strict rules apply to the new copper (see Overspec).

## A1: BAT_INT strip (U4 pins 22/23 → BAT block at x 163.9)

**Placement moves (authorised):**
- C106 (BAT 10 µF): 156.8, 121.9 → 157.2, 123.14, i.e. 1.24 mm south and 0.4 mm east. The east shift clears C110, and C106's courtyard now sits 0.015 mm clear of TP2's.
- R102 (PROG): 159.1, 122.0 → 159.4, 123.14, i.e. 1.14 mm south.

The full 1.5 mm south move was not possible: TP2's courtyard (top at y 125.09) and C110 limit it.

**Re-routes:**

| Item | Change |
|---|---|
| PROG | Leaves pin 20 and turns 45° SE at x 154.08. It runs along y 123.14 between the C106 pads (0.35 mm to each) to R102.1, now on the south edge of the strip. |
| BTST2 | Single 45° run from pin 19 (x 153.9) to C110.1. Clearances: 0.21 to the pin-18 corner, 0.29 to ILIM_HIZ, ≥ 0.21 to PROG. |
| Q103-G | Via 154.95, 120.1 → **155.0, 119.87**. The F track leaves the corner pin at 153.55 at 45° to y 119.87. The B track follows the via. |
| C106.2 / R102.2 GND | Old GND via 157.25, 123.85 and the GND track removed. New vias 158.3, 124.18 (C106, 0.38 mm from its pad) and 159.9, 124.25 (R102, 0.79 mm). |
| SYS B→F transition | The 3 vias at y 122.6 (which sat where the strip now is) became a second row at y 124.6. Both rows moved 0.1 mm east (161.0 / 162.0 / 163.0). Still 6 × 0.8/0.4. |
| SYS_COL_B | Extended south to y 125.0 at x 160.4–163.4 for the new via row. |
| ILIM_HIZ (B) | Moved 0.7 mm south along y 125.55, x 159.65–163.65, with 45° bends of ≥ 1 mm. |

**Zone outlines:**
- BAT_INT_F bottom edge 121.5 → 122.9;
- BAT_U4PIN_F now follows PROG and Q103-G;
- SYS_BOOST_F extension top edge 121.95 → 123.3.

**Capacity at 15 K:**

| Section | Before | After |
|---|---|---|
| Strip x 156–164.5, widest / cut | 1.9 / 2.00 mm (4.7 A) | **3.1 / 3.14 mm (6.5 A)**. At 7 A the rise is 18 K, at 9 A 31 K (was 65 K). |
| x 154.6 → block, widest | 1.43 mm | **2.43 mm (5.4 A)** |
| Near-pin section x 153.8–154.5, cut at x 154.2 | 1.32 mm | **1.56 mm (≈ 0.7 mm long)** |
| From the pins (widest from 153.5, 121.2) | 1.23 mm | 1.43 mm |
| SYS_COL_B cut, y 117–123.2 | 5.88 mm | 6.20 mm (≈ 11 A); widest 2.9 → 3.1 mm |
| SYS F from B-col vias to field 2, widest | 2.56 mm | 2.36 mm, in parallel with SYS_IN2; SYS_BOOST_F grew 86 mm² (Overspec) |

**Parallel BAT on B.Cu west of x 163.9: no legal room.**
- BAT runs west to east and SYS north to south through the same 8 mm.
- In2 is SYS_IN2 and B.Cu is SYS_COL_B. Both are needed for SYS's ≥ 9 A, so a B.Cu BAT strip would have to cut SYS_COL_B.
- West of x 157.2, B.Cu holds only the SW2/REGN jumpers and GND.

**What remains:**
- The pins themselves: 2 × 0.2 mm pads, 0.6 mm together, pitch-limited.
- About 0.7 mm at 1.4–1.6 mm wide, bounded by the Q103-G corner-pin escape (north) and the PROG/BTST2 escapes (south).
- The strip proper is 3.1 mm wide (6.5 A at 15 K). The plan's 9 A needs about 4.7 mm.
- 9 A is reachable only with:
  - the SYS cap-row vias at y 118.65 moved (they set the strip top at 119.45), or
  - 2 oz outer copper.

  The alternative is a derating: 6.5 A at 15 K, or 7 A at 18 K.

## A2: U4 top-row escapes (pins 25–29)

**PGND:**
- Pin 27's north track and its 2 GND vias (151.57, 117.5 / 118.4) were removed.
- New F pour GND_U4_PGND_F inside the U4 body: 0.3 mm on the pad end, then the body area. It carries 2 × 0.5/0.2 GND vias at 151.2, 121.5 and 150.65, 121.65, plus a 0.2 mm track. Authorised.
- A third via does not fit: CTRL_SCL, CHG_INT and QON vias and their B tracks fill the body.
- On the 0.3 mm 0.2-drill rule the two fine vias carry about 1.4 A, about 3 A on the IPC barrel. The old path was a 0.2 mm track (0.9 A).

**Pours:**
- SW1_F and SW2_F now reach the pin ends. A short 0.2 mm track on each pin enters the pour.
- PMID_U4PIN_F turns west at y 119.2 into C312.1, and SYS_U4PIN_F turns east at y 119.2 into C311.1. This frees the area above the pins.

| | Before | After |
|---|---|---|
| SW1 (pin 28) | 0.2 mm track for 1.2 mm, then 0.7 mm | pin 0.2 mm (0.2 mm long) → **0.36 mm for 0.9 mm** (pitch limit) → **0.92–1.1 mm** from y 118.9 to L1.1. Neck about 1.7 mΩ, 43 mW at 5 A (was 3.6 mΩ, 90 mW). |
| SW2 (pin 26) | 0.2–0.24 mm for 1.7 mm, then 0.5 mm | pin 0.2 mm → **0.30 mm pour + pad (0.42 mm) for 0.95 mm** → **0.91 mm** from y 118.85 to L1.2. About 1.6 mΩ. |
| SW1/SW2 pour area | 11.5 / 11.3 mm² | 14.7 / 13.2 mm² |

The 0.7 / 1.0 mm asked for is reached from about 1 mm above the pins. The first 0.9–1.1 mm is set by the 0.45 mm pin pitch, with 0.3 mm kept to the PMID and SYS columns. C311/C312 were not moved: it would not shorten this section, which PMID's and SYS's own pin escapes fix.

**Switch-node clearances** (`route_r6l_swclr.py`):
- New pour-to-pour clearances: ≥ 0.3 mm to PMID, SYS and BOOT; 0.2 mm between SW1 and SW2 (switch to switch).
- Pad-level 0.20 mm to PMID and SYS remains. This is the footprint pin gap; the old pour-to-pour 0.200 mm SW2–SYS at 152.2, 118.9 is gone.
- To signals, unchanged and inherited, all inside NECK_U4: CTRL_SCL 0.80–0.89, CHG_INT 0.68, ILIM_HIZ 0.48 mm.

**SW2 B jumper:**
- The bend moved 154.15 → 154.3, 120.0.
- SW2 to REGN B: 0.237 → **0.306 mm**.
- SW2 to the Q103-G via: 0.215 → 0.24 mm.

## Minor items

| Item | Result |
|---|---|
| C101/C108 GND vias | New GND via at 148.8, 114.0 on the F GND pour, in the VBUS_PD_IN2 edge strip (only 1.05 mm of In2 cut). The column via at 142.0, 114.3 was removed so the two do not stack. C101: 2.67 → **0.91 mm**; C108: 3.06 → **2.51 mm**; C112 unchanged at 0.7 mm. VBUS_PD_IN2 cuts are unchanged: 7.28 / 7.24 / 6.28 mm. |
| C271 second via | Added 0.6/0.3 at 116.2, 124.6. It is 0.32 mm from AMP_FAULT_N, 0.40 mm hole-to-hole from the first via, and its centre is outside the pad. PVDD_C271_F also grew from 3.5 to 4.0 mm². |
| B.Cu GND under U4 | Pieces 20.3 / 7.5 → 23.2 / 13.8 mm². They are not joined: SYS_COL_B, the SW2/REGN jumpers and ILIM_HIZ wall them in on B, and every piece has its own vias to In1. |
| SW2 B jumper gaps | See A2 (REGN 0.31, Q103-G 0.24 mm). |

## Overspec pass

**Tracks** (`route_r6l_widen.py` driven by `route_r6l_widen2.sh`):

*Nets covered:*
- POWER_HI, PVDD, SPK_OUT, PWR_5V, PWR_3V and PWR_LOCAL on every layer;
- on F.Cu only, the amp OUT_x nets and the U14/U15/U25 switch nodes;
- not U4 SW1/SW2, which keep the minimum switch-node area.

*How it works:*
1. Long segments are cut into collinear 2 mm pieces, so that a local obstacle only limits its own piece. Pieces that end at the same width are merged back afterwards: 260 merges.
2. Each item tries a descending width ladder, 60 items per round, until it reaches the first width the strict DRC accepts. 43 rounds ran. kicad-cli caps the number of violations it reports per type, so large batches hide violations.

*What an item may never be widened past:*
- the pad it ends in: segment ends inside small pads keep a neck no wider than the pad;
- `length / 3` for a segment between two bends (the corner rule);
- the arc radius, for arcs;
- 0.4 mm short of another net's non-GND pour outline. The In2 3V_AO trunk uses 0.0 instead, so it may take up to its DRC clearance from an island.

*Safeguards:*
- Every via and track net is pinned and restored on load. A temporary short had let KiCad move a GND via onto 3V_AO, which this caught.

Result: 835 candidate items (pieces included); 559 widened.

**Pours** (`route_r6l_zgrow.py` / `.sh`):

*What may grow, and by how much:*
- Non-GND power pours on F.Cu and In2 grow 0.5 mm per round, 4 rounds, so 2 mm at most.
- SWITCH and B.Cu pours do not grow.

*What a pour never grows into:*
- another power pour (0.5 mm kept from its outline);
- any foreign track, via or pad (0.4 / 0.6 mm on F, 0.35 mm on In2);
- the NECK areas.

*Pours that touch a neck area or an IC courtyard:*
- They keep their outline.
- Their growth goes into a companion zone `<name>_G` of the same net, one free priority level below the original. It overlaps the original only outside the relaxed areas.

*Checks after every round:*
- a zone is reverted on a DRC item, an extra fill piece or no area gain;
- a global check reverts the nearest zone accepted in that round if any other zone (GND included) gained a fill piece.

*Dropped:* SYS_IN2_G, because it produced an In2 copper sliver.

**Pour area per net** (filled, all zones of the net):

| Net | Layer | Before mm² | After mm² | Δ |
|---|---|---|---|---|
| PVDD_AMP | In2 | 2509.3 | 2761.5 | +252.2 |
| PVDD_AMP | F | 98.3 | 173.4 | +75.1 |
| BAT_PACK | In2 | 671.7 | 823.8 | +152.1 |
| BAT_PACK | F | 30.5 | 50.4 | +19.9 |
| PACK_RAW | F | 106.2 | 202.3 | +96.1 |
| BAT_INT | F | 89.5 | 144.8 | +55.3 (A1 + growth) |
| BAT_INT | In2 | 152.7 | 158.6 | +5.9 |
| SYS_RAW | F | 343.9 | 430.1 | +86.2 |
| SYS_RAW | B | 51.9 | 52.7 | +0.8 |
| VBUS_PD | In2 | 597.9 | 680.2 | +82.3 |
| VBUS_PD | F | 37.5 | 40.7 | +3.2 |
| USB_VBUS | In2 | 289.1 | 325.8 | +36.7 |
| USB_VBUS | F | 27.3 | 53.1 | +25.8 |
| PMID | F | 12.7 | 23.9 | +11.2 |
| **Total power pour** | | 5839.8 | 6747.5 | **+907.7** |

**Where the area came from:**
- In2 GND filler (GND_IN2_BG): 8897 → 7780 mm², pieces 103 → 121.
- B.Cu GND: 15285 → 15196 mm².
- F.Cu GND pours: 91.7 → 90.1 mm².
- In1 unchanged at 16520 mm², 1 piece.

**Per-net track widths, before → after.** Columns:
- *min / min of segments ≥ 1 mm:* the smallest width on the net, and the smallest among segments at least 1 mm long. The overall minimum is almost always a fine-pitch pin neck that cannot change.
- *length-weighted average:* average width, weighted by segment length.
- *% length ≥ 0.5 mm:* share of the net's track length that is at least 0.5 mm wide.

BAT_INT, PACK_RAW, PMID and VBUS_PD have no tracks; they are pour-only (see the table above).

| Net | Class | Length mm | Before min / min ≥ 1 mm | After min / min ≥ 1 mm | Length-weighted average | % length ≥ 0.5 mm |
|---|---|---|---|---|---|---|
| BAT_PACK | POWER_HI | 92.3 | 0.20 / 0.5 | 0.25 / 0.6 | 0.76 → 1.19 | 99 → 98 |
| SYS_RAW | POWER_HI | 143.4 | 0.20 / 0.2 | 0.20 / 0.5 | 1.61 → 1.78 | 93 → 97 |
| USB_VBUS | POWER_HI | 20.6 | 0.24 / 0.3 | 0.24 / 0.3 | 0.48 → 0.74 | 84 → 91 |
| PVDD_AMP | PVDD | 19.2 | 0.24 / 0.24 | 0.24 / 0.24 | 0.52 → 0.90 | 85 → 85 |
| SPK C302 | SPK_OUT | 28.1 | 1.5 / 1.5 | 1.5 / 1.5 | 1.87 → 2.27 | 100 |
| SPK C303 | SPK_OUT | 17.1 | 0.7 / 0.7 | 1.0 / 1.0 | 1.72 → 2.59 | 100 |
| SPK C304 | SPK_OUT | 31.5 | 2.0 / 2.0 | 2.0 / 2.0 | 2.00 → 2.33 | 100 |
| SPK C305 | SPK_OUT | 26.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.17 → 1.92 | 100 |
| SPK C306 / C307 | SPK_OUT | 29.1 each | 2.0 / 2.0 | 2.0 / 2.0 | 2.00 → 2.88 | 100 |
| 5V_CODEC | PWR_5V | 71.5 | 0.40 / 0.4 | 0.60 / 0.6 | 1.38 → 1.49 | 94 → 100 |
| 5V_LOGIC | PWR_5V | 130.9 | 0.20 / 0.2 | 0.25 / 0.3 | 0.60 → 1.08 | 22 → 73 |
| USB_AUX_5V | PWR_5V | 75.6 | 0.20 / 0.2 | 0.20 / 0.4 | 0.45 → 1.15 | 71 → 82 |
| REGN | PWR_5V | 67.1 | 0.20 / 0.4 | 0.20 / 0.4 | 0.40 → 0.77 | 7 → 57 |
| 3V_AO | PWR_3V | 200.8 | 0.20 / 0.2 | 0.20 / 0.2 | 0.70 → 1.02 | 85 → 93 |
| 3V3_AUDIO | PWR_3V | 299.8 | 0.20 / 0.2 | 0.20 / 0.2 | 0.35 → 0.64 | 14 → 55 |
| 3V8_BT | PWR_3V | 29.6 | 0.20 / 0.2 | 0.25 / 0.3 | 0.53 → 0.81 | 36 → 66 |
| LDO_3V3 | PWR_3V | 79.2 | 0.20 / 0.2 | 0.20 / 0.3 | 0.58 → 0.76 | 76 → 90 |
| U1 SYS_PWR | PWR_3V | 8.8 | 0.40 / 0.4 | 0.50 / 0.5 | 0.48 → 0.56 | 78 → 100 |
| U2 VCCP2I | PWR_LOCAL | 8.3 | 0.25 / 0.25 | **0.30 / 0.3** | 0.25 → 0.58 | 0 → 75 |
| U2 VCCCI | PWR_LOCAL | 7.6 | 0.40 / 0.4 | 0.40 / 0.4 | 0.40 → 0.74 | 0 → 84 |
| U24 AVDD | PWR_LOCAL | 28.4 | 0.20 / 0.2 | 0.20 / 0.2 | 0.34 → 0.61 | 0 → 72 |
| U24 LDO | PWR_LOCAL | 8.0 | 0.25 / 0.3 | 0.25 / 0.6 | 0.29 → 0.63 | 0 → 85 |
| U6 OUT_A− | SWITCH (amp) | 10.3 | 0.20 / 0.2 | 0.25 / 0.4 | 0.37 → 1.03 | 0 → 83 |
| U6 OUT_B− | SWITCH (amp) | 11.9 | 0.20 / 0.2 | 0.20 / 0.2 | 0.43 → 0.86 | 57 |
| U7 OUT_A+ | SWITCH (amp) | 13.4 | 0.20 / 0.2 | 0.20 / 0.2 | 0.41 → 0.64 | 63 → 66 |
| U7 OUT_B+ | SWITCH (amp) | 19.1 | 0.20 / 0.2 | 0.20 / 0.2 | 0.40 → 0.55 | 34 → 42 |
| U15 L1 / U14 L2 | SWITCH | 3.3 / 6.8 | 0.20 / 0.2 / 0.6 | 0.25 / 0.6 / 1.0 | 0.20 → 0.52 / 0.50 → 0.78 | – |
| U25 SW | SWITCH | 3.9 | 0.24 | 0.24 | 0.34 → 0.51 | 0 → 38 |

The full list (53 nets, with per-layer width histograms) is in `r6l/wstat0.txt` and `r6l/wstat_final.txt`.

**3V_AO on In2.** Of the 58 mm of 0.5–0.6 mm In2 trunk, 21 mm remain; 1.5 mm segments now total 50.7 mm. The long 24 mm diagonal (116.5, 78 → 139.6, 70.2) is now 1.0–1.5 mm except where it passes 5V_LOGIC at the 116.5, 78 via. The 0.5–0.6 mm leftovers sit in the U9/U10 mux area:
- 181–187 × 56–77: U9 NO1, HP_L, HP_DET, BT_MFB and ENC_B vias at 0.2 mm, and GND vias;
- 96–101 × 73–80: GAUGE_ISO_N and GND vias.

Widening there needs vias moved.

## Remaining limits

1. **BAT_INT** is 3.1 mm (6.5 A at 15 K; 9 A = 31 K). The pin end (0.6 mm) and about 0.7 mm at 1.4–1.6 mm are footprint- and escape-limited. More needs the SYS cap-row vias moved or 2 oz outer copper; see A1.
2. **SW1/SW2** have about 0.9–1.1 mm at the pitch limit (0.36 / 0.30 + pad). PGND has 2 fine vias (a third does not fit in the U4 body).
3. **SYS pin 25** is unchanged at 0.67–0.7 mm widest (B1, pitch-limited).
4. **Inherited items, unchanged:**
   - USB uncoupled 17.3 mm (waiver);
   - 3 via-in-pad;
   - 8 audio vias without a nearby GND via;
   - J7 NRST/SWCLK open;
   - 7 corner hits;
   - the 3 strict-check items above.
5. **SYS_IN2 did not grow.** Its companion made an In2 copper sliver. VBUS_PD_IN2 cuts are unchanged; the U11 strip minimum is 6.28 mm (3.0 A).
6. **Pour growth used GND copper:** about 1100 mm² of In2 GND filler and about 90 mm² of B.Cu GND. In1 is untouched.

## Helpers (new, `ai-files/helpers/`)

| Helper | Purpose |
|---|---|
| `route_r6l_edit.py` | `route_r6k_edit.py` plus `textmove` and `boardtext` |
| `route_r6l_step.sh`, `route_r6l_eval.sh` | R6l rules, island reference R6l-0 |
| `route_r6l_map.py` | net-coloured SVG map of one layer in a box, with labels and grid |
| `route_r6l_swclr.py` | minimum clearance from a net to every other net, per layer |
| `route_r6l_wstat.py` | per-net track width statistics |
| `route_r6l_widen.py`, `route_r6l_widen2.sh` | overspec track widening with the strict oracle, net pinning, split and merge |
| `route_r6l_splitall.py`, `route_r6l_verify2.sh` | strict DRC: every track split into 1 mm pieces |
| `route_r6l_zgrow.py`, `route_r6l_zgrow.sh` | pour growth: companion zones, per-zone and global fill-piece checks |
| `route_r6l_rmzone.py` | delete named zones |
| `route_r6l_union.py` | per-net union continuity across split pours |
| `route_r6l_gndfill.py` | GND fill pieces and area per layer |
| `route_r6l_pourarea.py` | pour area per net |
| `route_r6l_netcmp.py` | net changes by uuid between two boards |

**Reproduction chain:**
1. R6l-0 + `l1.json` → R6l-1 + `l2.json` → R6l-2 + `l3.json` → R6l-3 (`route_r6l_step.sh`).
2. `R6L_SPLIT=2.0 R6L_STEAL0=/3V_AO route_r6l_widen2.sh R6l-3 R6l-4 60`.
3. `route_r6l_zgrow.sh R6l-4 R6l-5 0.5 4`.
4. `route_r6l_rmzone.py R6l-5 → R6l-6 SYS_IN2_G`.
5. Copy R6l-6 → R6l-final, then `route_r6l_eval.sh R6l-final R6l-0 full`.
