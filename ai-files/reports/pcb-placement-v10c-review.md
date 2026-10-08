# PCB placement v10c review (2026-10-08)

This is a read-only review of `ai-files/pcb/work-v10c/DesktopSpeaker-v10c.kicad_pcb` (sha1 `ab4d5910…`). It checks it against `pcb-placement-v10b-review.md` and the v10c section of `pcb-placement-v10.md`. This is the third round, so findings are classed as follows:
- **BLOCKER**: routing cannot succeed, or a part will be damaged.
- **MAJOR**
- **MINOR**

Items that routing can absorb are marked *fix during routing*. No board was modified.

Accepted beforehand and not re-raised:
- Rule exemptions (courtyard neck-down, `switch_clear`/BOOT, U11 drills) are handled in the routing plan.
- R256 (DNP, MODE) and the U10 1 µF-only decoupling are schematic items for the user.
- The SW100 footprint fix is pending.

User decisions applied in this review:
- In2 is power-only (no signals).
- Inner copper is 0.5 oz.
- An overspec widening pass follows routing.

## Method
Scratch files are in `ai-files/pcb/work-v10c-review/`. The v10b-review and v10c checks were re-run first: `dump.py`, `esc.py`, `dec.py`, `verify_v10c.py`, and DRC (`drc.json`). Their results match the v10c report.

Because `esc.py` only tests a 1 mm straight ray, three new tools do the measurements:
- **`fan2.py`**: a sequential F.Cu fan-out router per IC. It works on real pad polygons (`dump2.py` → `poly.json`) on a 0.05 mm grid.
  - Neck rules: 0.2 mm track and 0.2 mm clearance. Vias are 0.45/0.2 within 1.5 mm of the courtyard and 0.6/0.3 elsewhere.
  - Vias are never placed in a foreign courtyard or within 0.5 mm of the IC's own courtyard. Tracks never run under the IC body. Routed tracks and new vias block later pins.
  - Each pin must reach a same-net pad, a same-net via or track, its own EP, or a legal via spot.
  - Rip-up and reorder, 8 tries. Via penalty swept from 1 to 8 mm.
  - Renders: `ov_*.png`.
- **`route1.py`**: a single-net width test. Optional obstacles: the fan-out tracks, plus neck boxes.
- **`dumpw.py` + `wcheck.py`**: what-if moves, computed in memory with pcbnew and never saved. They check courtyard overlaps, pad and via gaps, and via-to-via gaps.

## Verdict: FAIL (1 blocker, a local fix of 4 caps and 5 vias)

All three v10b blockers are fixed, and so are majors M1-M5. Every IC fans out completely at 0.2/0.2: U1-U12, U14, U15, U19, U22, U24 and U25.

The new blocker is that the bulk PVDD supply cannot reach the amplifier PVDD pins. The v10b-review B2 fix put each 100 nF PVDD cap horizontally in front of the PVDD pins, with its GND pad and GND via at the outer end. That closes the only lane. The fix is verified below.

## v10b items: re-measured

| Item | Status | Own measurement |
|---|---|---|
| B1 U7 PBTL bottom (pins 27/29/30) | **Fixed** | Nearest foreign copper below the pins is 1.45 mm, the same as U6. `fan2` routes all four bottom pins on F.Cu:<br>- 27 → C301 OUT (around the left of C299)<br>- 28 → C301 BST (through the C299/C301 slot)<br>- 29/30 → C299<br>No crossings (`ov_U7.png`). |
| B2 U6/U7 DVDD/VR_DIG | **Fixed** (but see new B1) | Pins 5-8 have 0.63/0.64 mm lateral clearance. Pins 6/7 reach C281/C282 and C294/C295, and pin 8 goes around C282. OUT_A+ C276→C285 gap is 1.28 mm. |
| B3 U11 top row | **Fixed** | `fan2`: 30/30 routed (pins 26-38 included). CC2/CC1 caps are at 0.57 mm. Pins 34-38 have a 1.98 mm band. Needs m1 below. |
| M1 U4 VBUS_PD / REGN | Fixed | VBUS_PD vias at (148.45, 120.0/120.7), (148.55, 125.0) and (148.25, 127.0). REGN routes C109 → TP11 at 0.4 mm on F.Cu (7.4 mm), with C313/C111 fed from their own VBUS vias. |
| M2 via fields | Fixed | 110 vias, all 0.6/0.3. DRC: 0 clearance and 0 hole errors. Same-net pitch is at least 0.7 mm (hole-to-hole 0.4, above the 0.3 minimum). The closest different-net pairs are GND/PVDD at 0.37-0.58 mm edge (pvdd 0.3). BAT_INT has 8 + 9 vias. |
| M3 BATP via | Fixed | U4 R is clear. U4 fans out 26/26 (see m3). |
| M4 U24 filter order | Fixed | VIN pins 1-4 fan out crossing-free. U24 is 24/24 when GND pins tie under the body (m2). |
| M5 U8/U9 top rows | Fixed | U8/U9 are 10/10 each. The COM1/COM2/HP_L audio vias are usable. |
| M6 rules | Accepted | Handled in the routing plan. Add the U11 width item (m1). |

The power paths at U4 were measured outside the neck at 0.3 mm clearance:

| Path | Max width |
|---|---|
| PMID (pin 29) → C101 | 1.46 mm |
| SYS (pin 25) → C104 | 1.46 mm |
| BAT_INT (pins 22/23) → C106 | 1.28 mm |
| SW1/SW2 → L1 | ≈0.6 mm for about 1.5 mm beside the pin-27 GND via column, then wide (m4) |
| U11 VBUS_PD pin 20 → C315 | ≥ 2.3 mm |
| U11 USB_VBUS pin 23 → C2 | 1.5 mm |

## BLOCKER

**B1. U6 and U7: the bulk PVDD feed to pins 3/4 and 21/22 has no copper path (new; created by the v10b B2 fix).**

The lane that bulk PVDD must use is closed on every side:
- **Above:** each PVDD pin pair is bounded by the DVDD/VR_DIG risers (pins 6/7) or the GVDD/AVDD stubs (pins 18/19).
- **Below:** the OUT/BST escapes of pins 1/2 or 23/24.
- **Outward:** the only remaining lane is blocked by the 100 nF cap's own GND pad plus its GND via:

  | Amp side | Cap | GND via |
  |---|---|---|
  | U6 right | C276 | (114.9, 128.4) |
  | U6 left | C278 | (104.2, 129.35) |
  | U7 right | C289 | (197.69, 128.4) |
  | U7 left | C291 | (186.99, 128.95) |

  There is no room for a via next to the PVDD pad.

Measured with `route1.py` and the `fan2` tracks as obstacles:
- PVDD from C271 or C272 to U6 pins 3 or 22: **no path even at 0.3 mm**.
- With no fan-out tracks, a 0.5 mm path exists over the top of C276. Routing it first makes pins 6, 7, 18 and 19 fail.
- The only survivor is a 0.2 mm, roughly 6 mm sliver under C276 (`ov_U6pv.png`). That breaks the 0.5 mm PVDD width rule and is far too thin for 2-3 A peaks.

0.5 oz In2 makes a via-only feed weaker still.

**Fix (verified in what-if `w1`).** Make each PVDD pin pair exit straight outward in a 0.8 mm lane. Move the 100 nF cap so its GND pad is off the lane:

| Part | To | Notes |
|---|---|---|
| **C276** | **(114.15, 128.85) r90** | PVDD pad (bottom) in the lane at 1.34 mm from the pins. GND pad (top) next to the existing GND via (114.9, 128.4). |
| **C278** | **(104.0, 129.36) r180** | In line with the lane, 2.1 mm out. GND pad next to the existing via (102.6, 128.85). **Delete GND via (104.2, 129.35).** |
| **C289** | **(196.94, 128.85) r90** | GND pad next to the existing via (197.69, 128.4). The lane runs on F.Cu under C293 to the C273 PVDD pad (4.1 mm). |
| **C291** | **(186.9, 130.45) r270** | PVDD pad (top) on the lane's lower edge. GND pad down, with a new GND via at **(186.05, 131.0)**. **Delete GND via (186.99, 128.95).** The lane runs on F.Cu to the C274 PVDD pad (3.8 mm). |

New PVDD vias (0.6/0.3) in the lanes:
- U6 right: **(115.4, 129.45) and (116.2, 129.45)**
- U6 left: **(106.2, 129.3) and (105.4, 129.3)**

These give the In2 PVDD island and C271/C272 a path to the lane.

Results with these moves:
- `wcheck.py`: 0 courtyard overlaps and no pad or via gap below 0.25 mm. C291 was set at x 186.9 to clear the C274 courtyard.
- `fan2`: U6 30/30 and U7 30/30 still route.
- `route1` PVDD lane width, measured outside a 1 mm pin neck and after the fan-out:

  | Path | Lane width |
  |---|---|
  | U6 pin 3 → C276 | **0.80 mm** |
  | U6 pin 22 → C278 | **0.80 mm** |
  | U7 pin 3 → C273 | **0.82 mm** |
  | U7 pin 22 → C274 | **0.80 mm** |

Cost: the U6-left and U7-left 100 nF caps move 2-3 mm from the pins, a small HF-loop penalty. Record it in the handover as an accepted deviation.

The OUT_A+/OUT_B+ trunks to L201, L203, L205 and L206 run below or outside the lanes, with no crossings.

## MAJOR
None open.

## MINOR (all *fix during routing* unless stated)

- **m1. U11 pins 2, 31 and 36** sit 0.17 mm from the adjacent wide pads (pins 1/3, 32 and 34). This is footprint geometry. A 0.2 mm track centred on the pin cannot keep 0.2 mm clearance. The U11 neck rule needs a 0.15 mm track or 0.17 mm clearance; with that, U11 fans out 30/30. *Rule item.*
- **m2. U24 GND pins 7 and 12** are boxed in on the top side:
  - The C215/C212 slot is 0.43 mm. It was 0.48 mm in v10b; C212 moved 0.05 mm left to keep the VINR1 riser legal.
  - C213 sits beside pin 12.
  - Tie both pins inward under the TSSOP body to a small GND patch with 2 GND vias. All AGND/DGND pins (7, 12, 15, 25, 26) can share it, which follows PCM186x practice.
  - With this, U24 is 24/24.
- **m3. U4 bottom row (pins 12-16) is order-sensitive.** Route SCL (14) first, then SDA (15), QON (12) and CE_N (13). Drop the B.Cu escape vias at about y 125.7-126.0 in the R103-R108 gap, for example (152.32, 125.69), (152.97, 125.69) and (151.17, 125.99). Vias directly at the pin tips block the neighbours. With this order U4 is 26/26.
- **m4. SW1/SW2 lanes beside the pin-27 GND via column** are about 1.0-1.1 mm wide between C312/C311 and the vias. That leaves at most about 0.6 mm of track for about 1.5 mm. This was accepted in v10b. The widening pass can add copper above y 117.5.
- **m5. VBUS_PD at U4** has only 4 vias (0.3 mm drill) for 3 A into a 0.5 oz In2 island. Add 2 vias next to the C111/C313 VBUS pads during routing, and keep the island at least 5 mm wide. The same 0.5 oz note applies to the PVDD and SYS_RAW islands. Prefer F.Cu pours for the high-current runs, as B1's fix does.
- **m6. In2 power-only.** All signal escape vias (I2S/I2C at the amp top rows, U3, U24, U8/U9 audio vias) must change layer to B.Cu only. `fan2` assumed only that the via could be placed. The B.Cu area under these escapes is free apart from the power via fields. *Routing-plan note.*
- **m7. Carry-overs (unchanged), from the DRC re-run:**
  - 2 SW100 hole_clearance
  - 8 U11 drill
  - 32 silk
  - 110 via_dangling (the reservation vias)
  - 499 unconnected
  - schematic parity 0

## What is good
- All three v10b blockers are fixed at the coordinates the review asked for. The U6/U7 bottom bootstrap stacks are identical and route without crossings.
- The fan-out is complete on every fine-pitch IC under the neck rules, with real pad shapes and vias counted as obstacles.
- Via fields are legal: DRC is clean, pitch is at least 0.7 mm, and no field blocks an escape.
- Power paths at U4 and U11 reach at least 1.3 mm width outside the neck.

## Fix order for v10d
1. B1: apply the four cap moves, delete 2 GND vias, add 1 GND via and 4 PVDD vias. Then re-run `fan2.py U6 U7` and `route1.py` (`PRE` unset) from this folder, and DRC.
2. Put m1 and the m6 note into the routing plan. Then route.
