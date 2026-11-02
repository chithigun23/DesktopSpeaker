# Battery pack 1S3P / 1S4P feasibility (2026-11-03)

Owner request: "see if we can go up to 4 without significant mechanical changes or electrical changes so it would have them in parallel".

Scope:
- Read-only on the project.
- CAD variants are built in `ai-files/cad/v13p4/` from copies of the v13 scripts, with the v13 board STEP and layout from `ai-files/pcb/work-cad13/`.
- Nothing in `DesktopSpeaker-kicad/`, `ai-files/cad/v13/`, the work-route folders or the website was changed. Nothing was committed.

Labels:
- **[DS]**: read in a local datasheet (file, page or section).
- **[CAD]**: measured in the v13p4 FreeCAD models.
- **[EST]**: my arithmetic or model.
- **[UNVERIFIED]**: not read in a primary document.

## 0. Answer

| | 2P (today) | 3P | 4P |
|---|---|---|---|
| Capacity / energy (50S typ 5.0 Ah, 3.6 V) | 10 Ah / 36 Wh | 15 Ah / 54 Wh | 20 Ah / 72 Wh |
| Fits the main chamber unchanged outside (163 x 100 x 206.6; drivers, woofer, PCB, insert, lid unchanged) | yes | **yes** | **yes**, with a rotated pack |
| Mechanical change | - | shell cradle only: rib profile and end stops extended by one row, rear strap block +21.7 mm | shell cradle only: new cradle for a 4-cell brick with the cell axes front to back, PCM at the rear end, harness re-routed |
| Interference (pairwise Boolean, 0.5 mm³) | 0 | **0** | **0** |
| Main chamber net volume (target ≥ 0.80 L) | 1.962 L | 1.934 L (−0.028) | **1.905 L (−0.057)** |
| Board electrical change | - | none | none (PCB, BQ25792, MAX17048, J5, SW101, TS network unchanged) |
| Firmware / settings change | - | ITERM, timer | ITERM, IPRECHG, timer, gauge CRATE thresholds, capacity constant |
| Full charge, 9-15 V PD, product off [EST] | 2.9 h | 4.1 h | **5.1 h** |
| Runtime at 10 W average [EST] | 3.1 h | 4.6 h | **6.1 h** |
| Verdict | - | **needs small mechanical change (shell cradle only)** | **needs small mechanical change (shell cradle + harness route)** |

**Recommendation: 4P is feasible and is my recommendation if run time matters more than charge time.**
- Only the battery cradle inside the shell changes.
- No board change is needed, because the pack terminal current is set by the load, not by the cell count. J5, SW101, the copper, Q103, the charger and the gauge see exactly the same currents as with 2P.
- The cost of 4P is about twice the charge time: about 5 h from empty with a 9 V or higher PD source. The 17 W input cap (BQ25792 converter rating), not ICHG, sets the charge rate.
- 3P is the fallback with the smallest change: the v13 cradle plus one row, with the pack in the same orientation and the same PCM position.

## 1. Mechanical (CAD, v13 pipeline)

### 1.1 Method

`ai-files/cad/v13p4/scripts/` holds copies of `build_speaker_cad.py`, `check_cad.py` and `render_cad.py`, plus `batt_check.py` and `render_batt.py`.
- Env `BATT=2P|3P|4P` selects the layout. 2P reproduces v13 exactly: main 1.962 L, woofer 0.525 L, 0 unintended overlaps, shell 380.5 cm³.
- `run_variant.sh` builds and checks one variant. `SKIP_EXPORT=1` skips the 48 MB STEP and the FCStd. Each variant has `print/*.stl`, `work/` (breps, `meta.json`, `check.json`, `batt.json`) and `renders/`.
- `batt_check.py` measures the pack envelope, the overlap with the PCB footprint, clearances from every battery object to every other object, mass and centre of mass (CoM), and a print-overhang audit of the STLs. The audit counts downward facets steeper than 45° in the print orientation, excluding the bed.
- Assumptions are the v13 ones:
  - cells at the 50S maximum Ø21.25 x 70.62 on a 21.7 pitch (wrap allowance); cradle radius 11.15 (0.3 mm gap; also takes the P45B at Ø21.55);
  - `cell_l` 70.7; PCM a 3 mm slab with 1 mm gaps; 20 mm hook-and-loop strap; harness tube Ø4.

### 1.2 Space available (measured on v13) [CAD]

- Floor of the main chamber: X ±78.5, Y 3.0 (baffle inner face) to 90.17 (woofer-chamber partition; floor groove at 89.97).
- Vertical room under the ND65s:
  - 26.1 mm (floor z 3.0 to the flange underside z 29.08 at y 11-14);
  - 31-33.9 at y 14-29;
  - 40.8 behind y 29;
  - nothing beyond y 55.75.

  So under the drivers there is room for **one** layer of 21700 cells only.
- Behind the drivers (y 55.75-90.17 = 34.4 mm deep) the height is up to z 54 (PCB shelf). That is too shallow (34.4 < 43.4) for a 2 x 2 block.

### 1.3 Layouts considered

| Layout | Result |
|---|---|
| 4 rows, axes along X (today's orientation + 2 rows) | **No.** It needs y 11.3-98.1 (86.8 mm of cells), which crosses the partition at 90.17 by 8 mm. Starting at y 4 still ends at 90.8 and puts cells under the driver pads with 0.85 mm. |
| 2 x 2 stacked under the drivers | **No.** It needs 43.4 mm of height; only 26.1 mm is available. |
| 2 x 2 stacked behind the drivers | **No.** It needs 43.4 mm in Y; only 34.4 mm is available. |
| 3 flat + 1 stacked behind the drivers (L shape) | Fits geometrically (cell 4 at z 26-48, y 56.5-78.2). Rejected: not a standard pack shape, and the PCM, nickel and NTC have to span an L. |
| 2 end-to-end x 2 rows, axes along X | Rejected: 141.4 + PCM/stops ≈ 152 of 157 mm. It hits the front feet bosses (x ±68, y 25). Parallel connection of the two halves needs long links, and the J5 harness side path is blocked. |
| **4 side by side in X, axes along Y (1S4P brick 86.8 x 73.7 x 21.7)** | **Chosen for 4P.** |
| **3 flat rows, axes along X (v13 + 1 row)** | **Chosen for 3P.** |
| 3 side by side, axes along Y | Also fits (65.1 wide, same length as 4P). It is not better than 3 rows and changes more. |

### 1.4 Results [CAD]

| | 2P (v13) | 3P | 4P |
|---|---|---|---|
| Pack envelope X x Y x Z (cells + PCM, mm) | 73.75 x 43.4 x 21.25 (x −36.65..37.1, y 11.3-54.7, z 4.2-25.5) | 73.75 x 65.1 x 21.25 (y 11.3-76.4) | 86.35 x 73.75 x 21.25 (x ±43.2, y 15.42-89.17, z 4.2-25.5) |
| Unintended overlaps | 0 | 0 | 0 |
| Cells to the nearest ND65 | 7.21 (PCM 5.43) | 7.21 (PCM 5.43) | **5.73** (cells 1/4 to the L/R driver) |
| Cells to driver screws/inserts | 11.29 | 11.29 | 10.92 |
| Pack to the partition (insert) | 33.8 | 13.77 | **1.0** (PCM to partition, by design: the partition is the rear stop) |
| Pack to the woofer | 53.4 | 31.7 | 18.9 |
| Pack to the PCB board / nearest PCB part | 44.3 / ≥ 40 | 41.5 / ≥ 40 | 41.5 / 39.9 (J11) |
| Pack to PCB standoffs/screws/inserts | 37.7 (HA2) | 28.0 (HA2) | 26.3 (HA1) |
| Pack to feet studs/inserts | 28.3 | 28.3 | 23.8 |
| Pack to SW101 rocker | 141 | 122 | 112 |
| Pack to J5 harness tube / route length J5 → pack | 2.4 / 176 mm | 2.4 / 165 mm | **1.82** (above cell 4) / **123 mm** |
| J5 harness to the partition / woofer-chamber air | 7.0 / 10.0 | 7.0 / 10.0 | **1.2** / 4.2 |
| Pack to the woofer harness / grommet | 15.7 / 37.8 | 14.5 / 18.4 | 14.1 / 12.1 |
| Cells to the cradle (radial gap) | 0.50 | 0.50 | 0.44 |
| Pack area under the PCB outline (plan view) | **0 %** | 18 % (878 mm²) | 33 % (2130 mm²) |
| Vertical gap pack top → PCB bottom | 41.5 | 41.5 | 41.5 |
| Main chamber net | 1.962 L | 1.934 L | 1.905 L |
| Shell volume (PETG) | 380.5 cm³ | 382.4 cm³ (+1.9) | 387.0 cm³ (+6.5) |
| Shell print: overhang > 45° off the bed (vs 2P) | 978 mm² (baseline) | **identical** | **+30 mm²**: two strap-tunnel ceilings, 2.5 x 6 mm bridges each; no support needed |
| Estimated total mass / pack mass | 1740 g / 152 g | 1815 g / 224 g | 1893 g / 296 g |
| CoM (x, y, z) | (−0.21, 88.94, 44.38) | (−0.20, 88.05, 43.16): Δy −0.9, Δz −1.2 | (−0.33, 87.58, 41.96): **Δy −1.4, Δz −2.4** |

Notes:
- "Under the PCB footprint as today" is not true today. The v13 pack sits under the front drivers, in front of the PCB, which starts at y 64.5. In plan view, the 3P third row and the rear third of the 4P brick are under the front strip of the PCB outline, 41.5 mm below it. For y ≥ 76 the woofer-insert shelf (z 54-57) lies between.
- Clearance artefact: `batt_check` reported 0.0 mm between the 2P/3P cells and PCB_U22. This is the OCC distToShape artefact already guarded in v13 `fit_check.py`. A vertex check gives 125.5 mm.
- The CoM moves lower and slightly forward with more cells, which is more stable; the front tipping angle rises 47.1° → 47.7°. Masses are estimates:
  - PETG at 100 % infill;
  - 50S taken as 69 g per cell [UNVERIFIED; the P45B is 70 g max, DS];
  - pack overhead (PCM, nickel, wrap, leads) taken as 8 g + 3 g per cell [EST].
- The 4P clearance tightest points are all ≥ 1.0 mm:
  - PCM to partition 1.0 (stop);
  - J5 harness to partition 1.2 and to cell 4 1.82;
  - cells to the drivers 5.73.

  The harness numbers are for a Ø4 schematic tube. Real leads (2 x 18 AWG + NTC) are smaller.

Renders (inspected):
- `v13p4/4P/renders/batt_section_x10.85_side.png`: pack length under the driver and up to the partition.
- `batt_section_y40_front.png` and `batt_section_y72_front.png`: 4 cells under the drivers; strap anchors at the sides.
- `batt_section_z15_top.png` and `batt_open_view.png`.
- The full v13 set, including `print_shell.png`.
- The same `batt_*` views for 3P and 2P.

### 1.5 Exact CAD/parameter changes

**3P** (`BATT=3P`; shell only):
- Pack centre `by` 33.0 → 43.85; rows at y 22.15 / 43.85 / 65.55 (pitch 21.7).
- Rib profile (Y-Z, ribs at x −31 and 22) generalised to N arcs. Rear end `rib_y1` 59.62 → 81.32.
- X end stops lengthened to y 81.32.
- Rear strap block moved +21.7: y 75.8-86.8, 3.2 mm before the floor groove. The Y tunnel is unchanged in section (22 x 2.5).
- PCM placeholder 3 x 43.4 x 18 → 3 x 65.1 x 18 at the +X end, as today.
- J5 harness end y 33 → 43.85.
- Lid, insert, outer size, drivers, woofer and PCB unchanged.

**4P** (`BATT=4P`; shell + harness route):
- Cells: axes along +Y, negative ends forward.
  - x centres −32.55 / −10.85 / 10.85 / 32.55; y 15.47-86.17; axis z 14.85 (unchanged).
  - PCM on the positive end: y 86.17-89.17; placeholder 60 x 3 x 18.
  - **Rear stop = the woofer-chamber partition**, 1.0 mm gap. No new stop part; insert unchanged.
- Removed v13 cradle parts: Y-Z ribs at x −31/22, X end stops, front/rear strap blocks with the Y tunnel.
- New cradle parts (all grown from the floor, printed baffle-down):
  - two 3 mm X-Z saddle ribs at y 19.47 and 79.17 following the four Ø22.3 arcs, with 3 mm side lips at x ±43.7..46.7 up to the axis height and 45° lead-ins (11.85 mm) toward the baffle;
  - front stop: four 8 mm fingers on the cell axes, from the baffle to y 14.47 (1.0 mm from the negative ends);
  - one 20 mm strap around the brick in the X-Z plane at y 44.89, anchored in two 6 x 28 x 6 blocks at x −53.7..−47.7 and 47.7..53.7. Each block has a 22 x 2.5 tunnel along X and a 45° lead-in.
- J5 harness: J5 → right side pocket (x 70) → down to z 29 (above the cells) → forward to y 86.97 → over the PCM top edge to x 28. Route 123 mm (v13 176 mm).
- The lid, insert, outer size, drivers, woofer, PCB position and screws are unchanged.

**Print-ready (no supports):** survives for both.
- All three bodies are valid single solids.
- 3P adds no overhang.
- 4P adds only the two 2.5 mm tunnel-ceiling bridges.
- The lid and insert are unchanged (same overhang figures as 2P).
- This was verified on the final geometry by the overhang audit. Pass 2 of 4P had a lead-in bug, found by that audit and fixed (section 6).

## 2. Electrical and safety

### 2.1 Key point: board currents do not change with the cell count

The amplifier boost U25 limits the pack draw to about 8 A in (`audio-chain-architecture.md` §3). The BQ25792 limits charge to ICHG and discharge OCP to 9.3 A (`charge-policy-2026-11-02.md` §2.7). The pack terminal current through J5, SW101, PACK_RAW/BAT_PACK, Q103 and BAT_INT is therefore the same for 2P, 3P and 4P.

What changes:
- per-cell current (it falls);
- stored energy and charge time (they rise);
- the prospective internal-fault current fed by neighbouring cells (it rises).

### 2.2 Per-cell current versus the cell limits

| Pack current | 2P per cell | 3P | 4P | 50S limit [DS deck p.3] | P45B limit [DS v1.2] |
|---|---|---|---|---|---|
| Typical listening, about 2.5 W SYS ≈ 0.8 A [EST] | 0.4 A | 0.27 | 0.2 | 25 A continuous w/o T-cut | 45 A continuous (80 °C cut-off) |
| BQ25792 battery rating 6 A RMS (design worst case) | 3.0 A | 2.0 | 1.5 | 25 A | 45 A |
| Boost-limited peak about 8 A (OCP 9.3 A) | 4.0-4.65 A | 2.7-3.1 | 2.0-2.3 | 45 A with 80 °C T-cut | 45 A |
| Charge ICHG 4.0 A | 2.0 A (0.4C) | 1.33 (0.27C) | **1.0 (0.2C)** | standard 2.5 A, max 6.0 A | standard 4.5 A, max 13.5 A (70 °C cut-off) |

All pack sizes are far inside the cell ratings.

Cell heating at 6 A RMS [EST, 16.3 mΩ DCIR, deck p.5]:
- 2P: 0.15 W per cell (0.29 W pack);
- 4P: 37 mW per cell (0.15 W pack).

Charging at 4 A: 64 mW per cell at 2P, 16 mW per cell at 4P. **4P runs cooler.**

### 2.3 Charge current and charge time

**ICHG stays 4.0 A (REG03 = 0x0190).** Raising it buys nothing:
- The charge rate is set by the 17 W input-power cap (`charge-policy` §2.2). That cap exists because the BQ25792 switch output ISW is rated 5 A maximum (SLUSDG1C §8.3), and ISW carries SYS load plus charge current.
- With the product off, the cap already gives only 3.6-3.9 A. ICHG 5 A (the IC maximum, §8.5: ICHG range 0.05-5 A) would not be reached.
- U4 heat (TREG 100 °C), L1 (66 % of Irms at 3.95 A) and the BAT_INT copper are unchanged because the current is unchanged.
- A faster charge would need either a dynamic cap or a hardware change. Optional later firmware (not recommended before bench thermal data): a "product-off" mode with a cap of about 20 W and ICHG about 4.5 A, only while the amplifier boost is off. It would save about 0.5 h on 4P.

Charge time from empty to termination [EST]:
- Same CC-CV model as `charge-policy` §5 (generic NMC OCV curve, 40 mΩ path + cell DCIR/n), recalibrated: it gives 2.80 h / 3.05 h / 3.40 h at 4.0 / 3.5 / 3.0 A for 2P (policy: 2.75 / 3.02 / 3.40).
- VREG 4.10 V; ITERM scaled to 0.05C per cell (section 2.10). The value in brackets is with ITERM left at 0.48 A.

| Source / condition (charge current) | 2P | 3P | 4P | 4P, 20-80 % |
|---|---|---|---|---|
| ICHG 4.0 A reached | 2.8 h | 3.9 h (4.1) | 4.9 h (5.5) | 3.1 h |
| 9-15 V PD, product off (≈ 3.7 A) | 2.9 h | 4.1 h (4.4) | **5.1 h (5.8)** | 3.3 h |
| 1 W SYS or 5 V/3 A (≈ 3.2 A) | 3.2 h | 4.6 h (4.8) | 5.8 h (6.4) | 3.8 h |
| 20 V, U4 in TREG (≈ 3.1 A) | 3.3 h | 4.7 h (4.9) | 5.9 h (6.6) | 3.9 h |
| 5 V/1.5 A (≈ 1.5 A) | 6.1 h | 8.9 h | 11.6 h | 8.1 h |
| VREG 4.16 V "full" mode, ≈ 3.7 A | 3.2 h | 4.4 h | 5.5 h | |

### 2.4 Protection board (PCM)

**The same PCM specification as `battery-pack-rfq.md` still applies.** A PCM protects the 1S group: one cell voltage and the pack terminal current. The number of parallel cells changes neither its interface nor its trip points.

The specification:
- overcharge 4.25 V;
- over-discharge 2.5-2.8 V;
- discharge ≥ 10 A continuous, 20 A for 1 s;
- charge OCP ≥ 5 A;
- short-circuit protection;
- under 10 µA drain.

Recommended trip window: OCP at 12-20 A with a delay of 10 ms or more.
- Its lower limit is set by the board, not by the cells: above the BQ25792 9.3 A OCP and the 8 A boost peaks.
- Its upper limit is what J5 and the 18 AWG harness can carry for the trip time.
- A "4P" board advertised at 20-30 A is acceptable only if its OCP is not far above this window. A 40 A trip would no longer protect J5 (8.5 A) or the harness.
- Fuse/PTC: add a pack-level fuse of about 15 A in the B+ lead (or a PCM with secondary protection), because the stored energy doubles [EST, best practice].

The interface stays a single off-the-shelf 1S board with three wires:
- B+ to the positive strip;
- B− / P− through the PCM MOSFETs;
- NTC on its own lead to J5-2, the other NTC end on P−.

J5 pin function is unchanged: 1 PACK+, 2 TS, 3 GND (HANDOVER "Pack connector and switch selection").

The real PCM, its OCP and OV values and its size are unknown (RFQ only). The 60 x 3 x 18 and 65 x 3 x 18 CAD slabs are placeholders.

### 2.5 J5, SW101, copper: unchanged

- **J5 Molex 43650-0300.**
  - The local datasheet `Molex_43650-0300_C503478.pdf` is an **LXW H3000S14 clone drawing rated 5 A AC/DC** [DS, page 1, read]. The genuine Molex 8.5 A per contact is from the LCSC listing [UNVERIFIED].
  - The current is unchanged by 4P: about 0.8 A typical, 4 A charge, 6 A RMS worst, 8 A peaks.
  - This is a **pre-existing** point, not a 4P one: order genuine Molex, because a 5 A clone is below the 6 A RMS design case.
- **SW101 CW GRB112B802BR1.**
  - The CW drawing R13-112B8-02-BRR-L1 rev 3 (`cad/models-v13/downloads/cw_GRB112B802BR1/grb112b802br1.pdf`, read): **20 A 14 VDC**, contact resistance **50 mΩ max**.
  - The rating is unchanged and adequate.
  - Pre-existing note: 50 mΩ max would be 0.8 W at 4 A and 1.8 W at 6 A worst case; typical will be much lower. Bench-check the voltage drop.
- **Battery-path copper.** PACK_RAW, BAT_PACK, the J5 pads, Q103 and BAT_INT (2.82-3.32 mΩ per `charge-policy` §7) carry the same current. No change.

### 2.6 MAX17048 gauge

- ModelGauge is voltage-based. It "eliminates current-sense resistor and battery-learn cycles" [DS, MAX17048 p.1] and starts from a preloaded ROM model at POR. It has **no capacity setting**: the OCV-SOC relationship is a property of the cell chemistry, and parallel cells look like one cell. No hardware or register change is needed for SOC.
- **CRATE** (%/h) for a given current falls by 2/n.
  - The default HIBRT 0x8030 means hibernate below HibThr 0x80 x 0.208 %/h = 26.6 %/h [DS, HIBRT register]. That is 2.7 A at 10 Ah but 5.3 A at 20 Ah, so the gauge would hibernate (slow updates) even during playback at 4P.
  - If firmware uses the default, scale HibThr by 2/n: 0x40 for 4P, 0x55 for 3P. Scale any other CRATE-based firmware threshold the same way.
- Firmware run-time or time-to-empty estimates need the pack capacity constant changed (10 → 15 or 20 Ah).
- The VREG 4.10 V reading of about 85-90 % (policy §2.3) is unchanged.

### 2.7 TS / NTC

Keep one 10 kΩ 103AT-type NTC (B 3435) and the R100/R101 network unchanged (`charge-policy` §2.6).
- 4P: glue the NTC between the two middle cells (2 and 3) at mid-length, the hottest spot.
- 3P: on the middle row.

A single NTC on a 4-cell brick is normal practice for 1S packs at these currents [UNVERIFIED as a standard]. The per-cell heating is a quarter of today's.

### 2.8 Paralleling, cell matching and per-cell fusing

**Build:**
- Same model and the same production lot. Capacity within about 2 % and DCIR within about ±1 mΩ [EST, common pack practice].
- Bring every cell to the same OCV (within 10 mV) before the first nickel joint.
- Spot-weld 0.15-0.2 mm pure nickel; never solder the cans.
- A 100 mV mismatch drives about 3 A between two cells at weld time (0.1 V / 32 mΩ) [EST]. That is harmless, but it shows why matching matters.
- Have the vendor build it. Hand-assembly at home suits the PCB, not spot-welding a 72 Wh pack.

**Handling:**
- Once welded, the cells are one cell; never replace a single cell.
- Store at 30-60 % SOC.
- Ship mode / SW101 off for transport.

**Per-cell fuses:** best practice for 4P and recommended.
- In an internal short of one cell, the other three discharge into it.
- Use fusible nickel links (slotted strip) or fuse wire on each cell's positive end, sized well above 2.3 A per cell.
- They fit inside the 1.0 mm end gap and wrap allowance of the CAD; no geometry change.
- Ask the vendor; many consumer 1S packs omit them.

### 2.9 Thermal, shipping, cost, weight

- Thermal: see 2.2. Charge heating per cell falls 4x at 4P. The 45 °C JEITA suspend and 40 °C derate are unchanged.
- Shipping/airline (mention only): 72 Wh nominal (69 Wh at the 4.8 Ah rated minimum; 64.8 Wh with P45B) is under the 100 Wh airline limit. UN38.3 documentation is still required to ship the pack. The 2P RFQ already asks for it.
- Cost: **unknown.** The BOM pack line (`hardware-buy-list.csv` row 32) is a quote placeholder ("TBD"), and no cell price is recorded in the BOM sources. The partial BOM subtotals do not include the pack.
- Weight: +69 g (3P) / +138 g (4P) of cells [50S mass UNVERIFIED; P45B 70 g max DS]. Estimated product mass 1.74 → 1.82 / 1.89 kg (shell +2 g / +8 g PETG).

### 2.10 Runtime [EST]

Basis:
- energy = n x 5.0 Ah x 3.6 V (50S typical, deck p.3);
- 85 % conversion efficiency;
- full charge to 4.20 V-equivalent capacity.

The value in brackets is with the 4.10 V default float (about 90 % capacity, `charge-policy` §2.3).

| Average load | 2P (36 Wh) | 3P (54 Wh) | 4P (72 Wh) |
|---|---|---|---|
| 5 W | 6.1 h (5.5) | 9.2 h (8.3) | **12.2 h (11.0)** |
| 10 W | 3.1 h (2.8) | 4.6 h (4.1) | **6.1 h (5.5)** |
| 20 W | 1.5 h (1.4) | 2.3 h (2.1) | **3.1 h (2.8)** |

20 W average is near the boost ceiling (about 20-23 W out) and is not a realistic continuous load. P45B cells give 10 % less (4.5 Ah).

## 3. Change list

### 3.1 Firmware / charge-policy values (BQ25792 SLUSDG1C register map; MAX17048)

| Item | 2P (today) | 3P | 4P | Reason |
|---|---|---|---|---|
| REG03 ICHG | 0x0190 (4.0 A) | **keep** | **keep** | capped by 17 W input; 0.27C / 0.2C |
| REG09 ITERM | 0x0C (480 mA) | **0x12 (720 mA)** | **0x19 (1000 mA)** | keep 0.05C per cell (Samsung cut-off 250 mA per cell, deck p.3 note 1); range 40-1000 mA, 40 mA step [DS REG09] |
| REG08 VBAT_LOWV / IPRECHG | 0xCC (71.4 %, 480 mA) | keep | **0xD2 (720 mA)** | 2 h pre-charge timer vs 20 Ah; U4 BATFET-LDO loss (3.7 − 2.5) x 0.72 = 0.86 W [EST], covered by TREG |
| REG0E timers | 0x3B (8 h, TMR2X) / 0x3F (24 h) under 15 W | **0x3D (12 h)** / 0x3F | **0x3D (12 h)** / 0x3F | worst ≥ 15 W case 4.7 h (3P), 5.9 h (4P) → ≥ 2x headroom; CHG_TMR 5/8/12/24 h [DS §8.5 tSAFETY, REG0E] |
| 5 V/0.5 A fallback | maintenance only | maintenance only | maintenance only (0.2 A ≈ 100 h) | unchanged |
| VREG, JEITA, TREG, OCP | 4.10 / 4.16 V, 45 °C suspend, 100 °C, EN_BATOC | unchanged | unchanged | per cell / current, not per capacity |
| MAX17048 HIBRT | default 0x8030 | HibThr 0x55 if the default is used | HibThr **0x40** | CRATE scales 2/n |
| Firmware capacity constant (time-to-empty / UI / charge-time estimate) | 10 Ah | 15 Ah | 20 Ah | |
| Bench plan | `charge-policy` §8 | + timer check | + timer check, NTC-position check, cell-temperature spread | |

### 3.2 BOM lines (`ai-files/bom/hardware-buy-list.csv`; edits are for the coordinator)

- Row 32, pack:
  - 4P: "1S4P 21700, 20 Ah (4 x INR21700-50S, same lot, matched), PCM ≥ 10 A cont / 20 A 1 s, OCP 12-20 A, charge OCP ≥ 5 A, OV 4.25 V, per-cell fusible links, 10k NTC B3435 between the middle cells, max **87.0 x 75.0 x 23.0 mm** incl. wrap and PCM (PCM on the + end, leads off the PCM top edge), lead about 180 mm (route 123 mm + slack), Micro-Fit 43645-0300".
  - 3P: "1S3P, 15 Ah, max 73.7 x 65.5 x 22.5, PCM at the end as today, lead about 230 mm".
  - The cradle allows 87.4 x 75.7 (4P).
- RFQ `battery-pack-rfq.md` item 1 (cell count), item 5 (outline) and item 4 (lead length) change accordingly.
- Row 25, hook-and-loop strap:
  - 4P loop ≈ 2 x (87 + 22) + anchors ≈ **330 mm** (the 300 mm line is too short; order ≥ 350 mm or a 20 mm One-Wrap);
  - 3P ≈ 270 mm (the 300 mm line is OK).
  - Width still UNVERIFIED (22 x 2.5 tunnels).
- J5 mating housing, crimps, NTC spare: unchanged.
- `cad/mechanical-bom.md`: strap line length.

### 3.3 CAD (to adopt into the main CAD)

Port the `BATT` branch of `v13p4/scripts/build_speaker_cad.py` into the next CAD version. It is a self-contained battery section plus the harness end, and 2P stays the default. The section 1.5 parameter list applies. No change to the lid or insert STL.

## 4. Verdict

- **3P: needs small mechanical change.**
  - Shell cradle only: rib profile +1 arc, end stops to y 81.3, rear strap block +21.7 mm. The pack orientation, PCM end and harness route are as today.
  - 0 interference; main chamber −0.028 L; print-ready unchanged.
  - Electrically drop-in; firmware ITERM and timer only.
  - Charge about 4.1 h; 10 W runtime 4.6 h.
- **4P: needs small mechanical change.**
  - Shell cradle replaced by a 4-cell brick cradle: pack rotated 90°, PCM at the rear against the partition, harness re-routed.
  - 0 interference; tightest gaps 1.0-1.8 mm by design; main chamber −0.057 L; print-ready (+2 short bridges).
  - The outer size, drivers, woofer, insert, lid and PCB are unchanged.
  - Electrically drop-in on the board; firmware ITERM, IPRECHG, timer, gauge threshold and capacity constant.
  - Charge about 5.1 h (product off, ≥ 9 V PD); 10 W runtime 6.1 h.
- Not advisable: 4 rows in the v13 orientation, any 2 x 2 stack and the 2 x 2 end-to-end layout (section 1.3).

**Recommendation:** 4P if the owner accepts about 5 h full charge (3.3 h for 20-80 %). Otherwise 3P is the lower-change option. In either case, specify per-cell fusing and a 12-20 A PCM OCP in the RFQ.

## 5. Not verified / open

- The real PCM size, OCP/OV values, the pack outline and the cell holder or wrap thickness. The CAD uses placeholders and the 21.7 pitch.
- Samsung 50S formal specification (charge-temperature window, mass): only the SDI 2021 deck was read; the siblings are as in `charge-policy`.
- Molex genuine 8.5 A rating (local file is the LXW 5 A clone).
- Cell price: unknown.
- Charge times use a generic OCV curve (estimates, about ±10 %).
- The strap width and buckle are UNVERIFIED (as v13). In 4P the strap passes in the 1.0 mm floor gap under the cells, as in v13.
- The insert partition acts as the 4P rear stop. It is located by floor grooves and screwed, but drop loads on it are not analysed.

## 6. Files and iterations

- `ai-files/cad/v13p4/scripts/`: `build_speaker_cad.py` (v13 copy + `BATT`), `check_cad.py` (battery clearance loop generalised), `render_cad.py` (copy), `render_batt.py`, `batt_check.py`.
- `ai-files/cad/v13p4/run_variant.sh`.
- `ai-files/cad/v13p4/{2P,3P,4P}/`: `print/*.stl`, `renders/*.png`, `volumes.md`, `interference.md`, `work/{meta,check,batt}.json` and breps, build/check logs.
  - About 42 MB of breps per variant in `work/`. These are not git-ignored: add `ai-files/cad/v13p4/*/work/` to `.gitignore` before committing.
- Iterations:
  - 4P pass 1 had three ribs and two straps, whose rib lead-ins ran into the strap bands (seen in the y = 40 section).
  - Pass 2 had two ribs and one central strap, but the lead-in was a translated copy and left the ribs as unsupported shelves: +700 mm² of overhang, found by the overhang audit.
  - Pass 3 (final) uses a swept lead-in; the overhang delta is 30 mm².
- Charge-time model: the scratchpad script `chg.py` (CC-CV, recalibrated to `charge-policy` §5).
