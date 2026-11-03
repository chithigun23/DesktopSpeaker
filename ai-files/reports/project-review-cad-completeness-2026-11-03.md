# Project review: CAD completeness and whole-project status (2026-11-03)

Agent "CAD completeness and project review". Read-only review: nothing in the CAD, board, schematic, BOM or website was changed. Fasteners (T10 post-Torx) are out of scope (another agent).

Inputs: CAD v15 (`ai-files/cad/v15/`: meta.json, fit_findings.json, interference.md, volumes.md, renders, work/brep), `cad/mechanical-bom.md`, `bom/hardware-buy-list.csv`, `reports/battery-pack-rfq.md`, `audio-chain-architecture.md`, `firmware-system-spec-2026-11-01.md`, `power-analysis-2026-11-01.md`, `release-todo-2026-11-03.md`, HANDOVER (latest sections), plan.md, board `ai-files/pcb/gui-finish/DesktopSpeaker-RT15H.kicad_pcb` (positions, pads and silkscreen read as text).

New measurements: FreeCAD 1.0 (`freecadcmd`) probes on the v15 solids. They covered bounding boxes, swept-path collisions, slot widths, distances and tipping. Three new section renders are in `ai-files/reports/review-2026-11-03/`:

- `encoder_dish_section.png`
- `jack_J2_recess_section.png`
- `driver_screw_L1_L2_access_section.png`

Tags used below:

- **[V]**: verified in this review, either measured on the CAD v15 solids or read directly from project files.
- **[D]**: documented by earlier work and not re-measured.
- **[J]**: my judgement or estimate.

---

## 1. Top findings (read these first)

1. **The PCB cannot be installed as drawn [V].** SW102's shaft passes up through the 8.5 mm hole in the knob-dish floor. So the board would have to come in from below the dish, but it can only come in horizontally from the rear and then drop onto its spacers.
   - The shaft top is at z 93.09 and the dish floor underside at z 82.09. The board therefore has to sit 11.0 mm lower than its final height to slide under the well.
   - The most it can drop is about 8 mm. Even with the spacers left out, the J2 pins hit the insert roof (z 57) at a 9 mm drop.
   - I tested a drop of 7.5 mm with the board moved 3, 10 and 25 mm toward the rear: SW102 collides with the shell at every offset.
   - Tilting the board makes this worse, because the shaft sits 56 mm from the front edge and 81 mm from the rear edge.
   - Must fix before printing the shell. See M1 for two fixes that need no board change.
2. **Once the woofer-chamber insert is bonded, the battery and both front drivers are captive [V].**
   - The slot over the insert roof is 40 mm high (z 57 to 97), and only 25 mm under the knob well. The smallest ND65-4 dimension is 48 mm (its depth), so a driver cannot pass.
   - The battery has to come down in front of the insert. There the gap between the ND65 magnet backs (Y 55.8) and the shelf/gusset front (Y 76.0 to 78.5) is 20.2 to 22.7 mm between z 50 and 56. The brick is 21.75 mm thick, and up to 23.0 is allowed by the RFQ.
   - Consequences:
     - The pack and drivers must go in **before** the insert is bonded.
     - After bonding, a dead cell, a PCM fault or a damaged driver means destroying the shell.
   - Must decide: make the insert removable (M2), or accept this and test everything before bonding.
3. **The "sealed" main chamber is not sealed [V geometry, J acoustics].** The rear-lid cut-outs and the encoder hole open straight into the main chamber. None of the connector faces touch the lid, and nothing is modelled to close the gaps.

   | Opening | Open area (mm²) |
   |---|---|
   | J1 opening (80.6 minus the 8.94 x 3.16 shell) | 52 |
   | J2 + J3 bores (2 x 56.7; jack faces 1.51 mm behind the lid) | 113 |
   | SW100 bore | 19.6 |
   | Encoder shaft gap (1.25 mm radial) | 28.5 |
   | **Total** | **about 214 (a 16.5 mm round hole)** |

   - [J] With 1.9 L behind it, this acts like a lossy port tuned somewhere around 130-170 Hz, which is right at the 150 Hz crossover. It also lets dust and spilled liquid reach the PCB through the encoder hole.
   - Should fix (S1): foam seals on the connector faces, an encoder foam washer and the SW100 plunger.
4. **SW100 still has no actuator part [V]: a must.** The actuator tip is 0.50 mm behind the lid inner face and 4.50 mm behind the outer face. A concrete plunger design is in M3.
5. **Nothing holds the wiring [V].** The J10 lead is about 300 mm long and runs across both drivers 0.5 mm under the top wall with no anchor. The J9/J11/J5 leads and the inline PH pair in the woofer chamber are also free.
   - There are no tie anchors, ties, clips or tie mounts in the CAD or the buy list.
   - A loose lead against a driver basket or a wall buzzes at bass. Must fix (M4).
6. **The battery path has no fuse anywhere, on the board or in the pack spec [V].** The schematics have no F reference. The RFQ asks for per-cell fusible links and a 12-20 A PCM, but no secondary fuse and no thermal cut-off.
   - A 4P 21700 brick can source far more than 100 A. If the PCM MOSFETs fail short, the only remaining protection is the BQ25792 current limit on the board side.
   - Must fix: add a PACK+ fuse to the RFQ (M5).
7. **The CAD, BOM and RFQ disagree in several places [V]** (section 4):
   - the woofer M3x20 screws are missing from the buy list;
   - the buy list still has 11 nylon lid washers at a price;
   - `mechanical-bom.md` still says woofer bolt circle 77, an 83.4 x 1.0 woofer gasket recess and a rocker body depth of about 11 mm, but the CAD has 96.52, no recess with the factory gasket, and 22.4 mm;
   - the grommet hole in the CAD is 6.0 mm with a 1.6 mm web, but the modelled Heyco 2000 needs 6.35 mm and at most 1.57 mm;
   - the RFQ allows a 23.0 mm thick pack, but the cradle arcs are cut for a 21.75 mm brick.
8. **Project status.** No firmware exists (only the spec), and nothing works without it. The board is 273 of 282 connections routed (RT-15H, DRC 0 violations, 9 open). The pack is not quoted. The CAD fixes above need a shell reprint. Section 5 ranks the risks to a first working prototype.

---

## 2. Missing or placeholder elements, by priority

Each entry gives the problem, the proposed part or geometry, where it goes, the CAD change and the BOM line. Part numbers marked "e.g." are examples I have not verified.

### MUST (blocks assembly, safety or basic function)

**M1. Encoder/knob installation path (finding 1) [V problem, J fix].** Options, in my order of preference:

- **(a) Panel-mount the encoder in the dish floor on a 5-wire pigtail.** No board change and no new shell geometry beyond the hole.
  - Part: an EC11-class encoder with a threaded bushing (M7 x 0.75 class; e.g. a bushing variant of the Alps EC11E, or a Bourns PEC11R ...F-S0024). Check the bushing length (at least 3 mm floor plus nut and washer) and the shaft length.
  - The shaft should leave the knob top 3-5 mm proud of the top surface (see S6).
  - Fit it from inside the shell before the PCB goes in. Solder five 26-28 AWG leads, about 120 mm long, into the existing SW102 holes (A, B, C, S1, S2; leave MP unused, or ground it with a sixth lead).
  - The nut and washer close the floor hole. This also fixes the 28.5 mm² leak in finding 3.
  - CAD: floor hole 8.5 becomes the bushing size (about 7.2 mm); add an anti-rotation slot if the part has a tab; move the encoder body from the board to the floor; model the pigtail.
  - BOM: the encoder (replaces SW102 on the hardware list; SW102 is then not fitted on the board), a 5-core ribbon, heat-shrink.
- **(b) Separate printed well cup.**
  - Cut a 42 mm hole in the top wall. The board slides in with the shaft passing 3.9 mm under the top wall.
  - The well cup (the existing 36 mm dish, 3 mm wall and floor, 8.5 hole) then drops in from above, with a 46 mm flange in a 1 mm recess.
  - Retention: 3 x M2.5 or M3 screws into inserts, plus a 1 mm foam ring or an O-ring for the seal.
  - CAD: a new part `Knob_well_cup` and a reworked shell top wall. H8 can then be reached from above once the cup is out.
- (c) A board change, such as a right-angle encoder at the rear edge. Not recommended now.

**M2. Insert retention and serviceability (finding 2) [V problem, J fix].**

- Recommended: make the insert removable.
  - Replace the Sikaflex bond with a foam gasket in the floor grooves: the same 2 x 1.5 groove and 2-3 mm sponge cord as the lid.
  - Fix it with 4-6 M3 screws from below through the floor into new bosses on the insert walls (countersunk T10 to match), placed between the feet and away from the woofer grille.
  - Service order is then: lid, PCB, woofer, insert, battery or drivers.
  - CAD: floor screw holes with countersinks, bosses on the insert wall feet, a groove gasket.
  - BOM: +6 screws, +6 inserts, about 0.5 m of extra gasket cord.
- If the owner keeps the bonded insert, record a hard rule: fully test the drivers, the pack (including the PCM) and the leads before bonding. The pack is a consumable (500-1000 cycles), so a bonded insert makes the product non-repairable [J].

**M3. SW100 lid plunger [V gap, J design].**

- Geometry: actuator tip 0.50 mm behind the lid inner face, 4.50 mm behind the outer face; bore 5.0; switch body 1.35 mm from the lid [V].
- Proposed part: a printed PETG plunger fitted from inside before the lid goes on.
  - Shank Ø4.6, passing the 5.0 bore.
  - Inner flange Ø7.0 x 0.8, seated in a new **Ø7.4 x 1.0 counterbore in the lid inner face**.
  - A Ø1.8 nub on the flange, sized to leave 0.10-0.20 mm to the actuator at rest.
  - Outer face 0.3-0.5 mm **below** the lid outer face, so the button is recessed against accidental ship-mode or wake presses.
- The TE travel is unknown (no text in the drawing; typically about 0.25 mm [J]). Print three plungers with nub lengths 0.4, 0.6 and 0.8 mm and keep the one that clicks without preload.
- The plunger also closes most of the 19.6 mm² bore (about 3 mm² left).
- CAD: a new part `SW100_plunger` and the lid counterbore. Check the 4.4 mm web to the J1 opening: with a 7.4 counterbore on the inside the web stays above 2 mm.
- BOM: none (printed).

**M4. Cable management and anti-rattle [V gap].**

- Proposed geometry: printed cable-tie bridges, slot 3.0 x 1.4 and bridge 1.5 mm, on the shell inner faces. Suggested positions:
  - 3 along the J10 path on the top wall: over the left driver, at the centre, over the right driver;
  - 1 over the left driver for J9;
  - 2 on the right side wall for the J5 leads: at the drop at x 77, and near the grommet boss;
  - 1 on the insert roof edge for J11, before the grommet;
  - 1 inside the woofer chamber on the insert side wall, holding the inline PH pair and the splice sleeves off the woofer basket.
- Also tie or glue each ND65 lead to the basket next to its solder tab (strain relief).
- With the shell printed baffle-down the walls are vertical, so the bridges print without supports [J].
- Alternative with no CAD change: adhesive tie mounts (e.g. 13 x 13 mm for ties up to 2.5 mm) plus a dab of CA glue.
- BOM: 2.5 x 100 mm nylon ties (pack of 100); adhesive mounts (10) if not printed; and a foam tape strip where a lead crosses a driver basket.
- Re-run `wire_check.py` with the anchor positions as fixed waypoints.

**M5. Pack fuse and thermal cut-off [V gap, J part].** Add to the RFQ:

- "Secondary protection: one 15 A fuse in PACK+ at the PCM output (e.g. Littelfuse 456-series 15 A SMD or equivalent), plus a thermal cut-off or mini breaker of about 85 °C on the cells (Komatsulite/Bourns NR-type or equivalent). State the part numbers."

Why: the PCM trip window is 12-20 A, the J5 Micro-Fit is 8.5 A per contact (genuine part, unverified) or 5 A (clone drawing), and the board's BQ25792 current limit is 9.3 A.

- No CAD change (inside the brick). If the vendor declines, fit an inline 15 A ATO/mini-blade holder in the PACK+ lead and model it. There is room: the 180 mm RFQ lead is 49 mm longer than the 131 mm CAD route.

**M6. Install the drivers and pack before the insert [V, follows from finding 2].** If the insert stays bonded:

- At least 4 of the 8 driver screws have no straight tool path once the insert and knob well are in. My probe used a 4 mm-radius tool along +Y:
  - L2 and R4 (z 38) are blocked by the insert;
  - L1 is blocked by the knob well;
  - L3, L4, R1 and R2 are blocked only by later-fitted wires, the rocker or the lid gasket.
- So drive all 8 screws before the insert goes in (section 6 gives the order). L1 is blocked by the well even then, so it needs a T10 post-Torx L-key or a right-angle driver: buy one (the buy list has only the straight bit).
- Render: `review-2026-11-03/driver_screw_L1_L2_access_section.png`.

### SHOULD (quality, acoustics, usability, sourcing)

**S1. Seal the main-chamber openings (finding 3).**

- (a) A die-cut 2.0 mm closed-cell foam gasket (PE, EPDM or PORON, adhesive one side) on the lid inner face around J1, J2, J3 and SW100. The gaps to the connector faces are 1.5 mm, so it compresses about 25%.
  - Cut-outs: J1 8.6 x 2.9 (grips the 8.94 x 3.16 shell, which enters the lid by 0.69 mm); J2/J3 Ø5.0 aligned with the bores; SW100 Ø5.0.
- (b) Encoder: a closed-cell foam washer, ID 7.0 / OD 14 / 3.0 thick, on the encoder bushing. The bushing top is about 2.1 mm below the well floor [V], so the washer compresses to about 2.1 mm without touching the shaft. Not needed if M1(a) is used.
- (c) Then add one deliberate equalisation vent (S3).
- Verify by measuring the front-driver impedance in the box: a vented box shows two peaks.
- BOM: foam sheet. The driver gasket line is already unsourced, so buy one 0.8-1 mm sheet and one 2 mm sheet.
- Render: `review-2026-11-03/jack_J2_recess_section.png`.

**S2. Seal the four lid screws inside the woofer-chamber loop (LidScrew 6, 7, 10, 11; their inserts sit in the woofer-chamber displacement list) [V].**

- The clearance holes (3.4 for an M3 screw) leak past the boss faces into the sealed chamber, and the nylon washers no longer fit under countersunk heads.
- Proposal:
  - counterbore each of the 4 boss tops Ø7.6 x 0.7 mm;
  - fit 1.0 mm closed-cell neoprene washers (ID 3.2 / OD 7.5, cut from the 1 mm sheet), which compress 30% when the lid seats.
- A non-curing butyl dab is the no-CAD alternative. Do not use thread sealant: it does not seal the boss-face path.
- The other 7 lid screws open into the main chamber, so they matter less until S1 is done.

**S3. Pressure equalisation for the sealed woofer chamber [J calc].**

- A fully sealed 0.52 L chamber sees about 4 kPa peak at Xmax (Sd assumed 30 cm²), and several kPa static change with temperature and altitude (air freight about 25 kPa).
- Fix: drill **one 0.5 mm hole through the lid** in the woofer zone with a 0.5 mm carbide PCB drill. A 4 mm-long, 0.5 mm capillary into 0.52 L gives a time constant of about 0.17 s, a corner at about 0.9 Hz (Poiseuille, my calculation), so it is acoustically invisible.
- Cover it inside with a felt or PTFE dot.
- Do not print a 1 mm hole: that moves the corner to about 15 Hz.
- After S1, add the same vent to the main chamber.

**S4. Lid gasket gland [V numbers, J assessment].**

- The groove is 2.0 W x 1.5 D (3.0 mm²). The buy list cord is 3 mm round (7.1 mm²), which is 235% groove fill. Normal glands run about 75-90%.
- A soft sponge will probably still close, but the closing force rises steeply. The 4 mm PETG lid spans about 75 mm between screws (5→81.5→155.5 along the top edge) and may bow open mid-span: my rough beam estimate is of the order of 1 mm at 0.3 N/mm, against 1.5 mm of compression.
- Options:
  - a 2.0-2.4 mm sponge cord in the existing groove;
  - or widen the groove to 3.0 x 2.2 for the 3 mm cord;
  - or use flat 3 x 1.5 adhesive closed-cell tape on a flat land.
- Check with a feeler or a paper strip after the first fit.

**S5. Pack retention and cushioning [V geometry, J design].**

- The PCM is the rear contact, 0.63 mm from the partition [V]. In a drop, about 300 g of pack lands on the PCM components.
- Proposal: two printed stop ribs on the partition, about 6 mm wide at x ±37, with 0.5 mm EVA or PORON pads. They should touch the wrap over cells 1 and 4 (outside the PCM's ±30 mm extent) and leave at least 2 mm to the PCM. Confirm against the vendor drawing.
- Also re-cut the cradle from the vendor drawing before printing. The arcs fit a 21.75 brick with 0.275 mm radial clearance (about 22.3 effective). A 23.0 mm pack (RFQ maximum) sits about 1.3 mm higher and looser, which takes the clearance under the ND65 from 5.29 to about 4 mm.
- Tighten the RFQ thickness to 22.3 mm, or state "cradle printed after the drawing".

**S6. Knob usability [V geometry, J].**

- The knob top is at z 99.84 against a top surface at 100: flush [V]. The dish is 36 mm and the real knob (Jaycar HK7011) is 29 mm, so the radial finger gap is 3.5 mm.
- A smooth anodised knob that is flush and sunk in a 3.5 mm moat cannot be gripped by its sides.
- Options:
  - a knob with a finger dimple, or a knurled or rubber top;
  - raise the knob 4-5 mm (shaft engagement is only 7.25 mm now, so this needs the longer-shaft encoder of M1(a));
  - widen the dish to 42 mm.
- The 6.35 mm (1/4 in) bore on a 6 mm D-shaft with one grub screw sits 0.35 mm off-centre: buy a true 6 mm D-bore knob, or shim it.

**S7. Rear-lid openings for real plugs [V recess, J plug sizes].**

- **USB-C:** the receptacle face is 3.31 mm behind the outer face, so the plug overmold must enter the 12.0 x 7.0 opening.
  - From memory, the USB-C cable guidance allows overmolds up to about 12.35 x 6.5 mm (unverified).
  - Widen the opening to 13.0 x 7.5 R2. The web to the SW100 bore drops from 4.41 to 3.91 mm (still at least 1.6).
- **3.5 mm jacks:** the jack face is 4.84 mm behind the outer face, so the plug nose must enter 2 mm of the Ø11 counterbore and 2.84 mm of the Ø8.5 bore.
  - Overmolds wider than 8.5 mm will not seat, and the plug will not reach full depth.
  - Open the bore to Ø10.0 (web 3.4 at the 13.4 mm pitch). The face seal from S1 moves with it.
- **Rocker:** the CAD body protrudes 11.5 mm behind the lid (Y up to 218.1) [V]. Note this for wall placement; it is not a change.

**S8. Rocker SW101 leads [V gap].**

- The board pads are oval THT, drill 2.4 x 1.2, at (210.5, 86.8). That is CAD X 59.8, Y 135.3: 67 mm inside the lid.
- The rocker body (18.4 mm inside the lid inner face) and its insulated fastons (about 20 mm more) are not wired in the CAD.
- Model 2 x 18 AWG silicone leads, about 150 mm each, with a 60-80 mm service loop. The lid must swing clear before the fastons can be pulled off.
- Insulate the unused lamp tab (buy list line 6 already has 3 receptacles).
- Route them clear of J3 (3.87 mm from the rocker body [V]).

**S9. Harness slack for the assembly order [J].**

- J9 is modelled at 49/55 mm. With the drivers fitted first, J9, J10 and J11 have to be plugged in while the board is held above its spacers, 120-130 mm deep in a 28 mm slot.
- Set the cut lengths to about 110 mm for J9, the modelled length + 40 mm for J10 and J11, and J5 as quoted (180 mm). Dress the slack on the anchors from M4.

**S10. Front driver gaskets and woofer gasket.**

- Drivers: the CAD has a 0.5 mm recess on 63 mm squares [V]; the foam is unsourced. Use 0.8-1.0 mm closed-cell PE or neoprene sheet, adhesive one side, cut as a 63 mm square ring with a 59.5 mm hole.
- Woofer: confirm on the sample that the factory 3.3 mm gasket exists. If it does, drop the separate ring. If not, cut a ring 83 OD / 76.2 ID from the 1 mm sheet.

**S11. Acoustic damping (not modelled) [J].**

- Woofer chamber: 6-8 g of Acousta-Stuf, loose, kept 10 mm off the magnet and the cone back.
  - Calculation: Qtc 0.72 and Fc 86 Hz without fill (W3-2052SC: Fs 59, Qts 0.49, Vas 0.595 L in 0.524 L) [V arithmetic, matching the firmware-spec table]. Fill raises the effective volume 10-20%, giving Qtc about 0.69-0.70, which is still inside the 0.45-0.60 L design window.
- Main chamber: line the walls with 10 mm open-cell foam or felt instead of loose fill, so fibres stay off the PCB, encoder and jacks.
  - Line the top wall over the drivers (but not under the cable path) and the side walls in front of the insert.
  - About 15-20 g, or about 0.04 L displaced (negligible).
  - Calculation: ND65 Qtc about 0.76 and fc about 112 Hz in 0.95 L each [V arithmetic], below the 150 Hz LR4 high-pass.
- CAD: add a lining placeholder (10 mm) so the volumes report includes it.
- BOM: foam sheet. The polyfill is already listed.

**S12. Feet [V gap, J part].**

- The current design glues a 12.7 mm adhesive bumper to the 5.5 AF end of a steel stud (Wurth 971120321). The bond area is tiny and the feet will shear off when the speaker is slid.
- Replace with 4 cylindrical rubber buffers, 15 x 15 mm with an M3 x 6 male stud (generic "anti-vibration mount, type with one stud, rubber face"), screwed into the existing foot inserts.
  - This keeps the 15 mm downfiring gap and adds some decoupling from the desk.
- BOM: replace the stud + bumper lines (2 lines become 1).
- Tipping is unchanged; see 3.1.

**S13. Woofer grille dust and debris [J].**

- The bottom grille has no cloth, and a downfiring cone 15 mm above a desk collects debris.
- Back the grille with the same black cloth (buy list line 4).
- Optionally enlarge the perforated zone from Ø64 to about Ø74 so it covers the 76.2 aperture. Today's open area is about 26% of the aperture; my estimate of the peak hole velocity at Xmax is about 5 m/s, which is acceptable.

**S14. Labels [V gap].** The lid has no markings, and J2 (HEAD_OUT) and J3 (AUX_IN) look identical.

- Deboss on the lid outer face (the bed face, so print it mirrored):
  - text 0.4-0.5 mm deep, 3.5 mm high, 0.6 mm strokes;
  - "USB-C 5-20 V 3 A", "HP OUT" with a headphone icon, "AUX IN", "WAKE" at SW100, "BATT OFF / ON" at the rocker.
- Rating label with an inside warning: "Li-ion 3.6 V 20 Ah 72 Wh, do not puncture". The pack vendor's label may cover this.
- Board silkscreen: J8 and J4 have no pin-name labels (J6 does) [V]. Add them on the next revision.

**S15. Status indicator (owner decision) [D firmware spec].**

- No LED, light pipe or STAT connection exists. PB14, PB15 and PA2 are reserved.
- This is a board change: an RGB LED near the rear edge, three resistors and a printed or acrylic light pipe in the lid. It is not compatible with the current 97%-routed board without rework.
- Alternatives: BM83 voice prompts or phone battery reporting. Decide before the next board revision.

**S16. Panel stiffness of the insert roof [J calc].**

- The roof is 3 mm PETG, about 120 x 126 mm, and also carries the PCB (82 g plus standoffs).
- My estimate of the clamped-plate first mode is about 460 Hz unloaded. It drops toward the woofer's upper band with the PCB mass, and it deflects about 0.2 mm at the about 4 kPa Xmax pressure.
- Add two 8 mm ribs under the roof, or a 5 mm roof. This takes about 10-15 cm³ from the woofer chamber, so the net stays at about 0.51 L, inside the window.
- Check by tapping and listening, or with a phone accelerometer, after the first print.

### NICE

- **N1.** Swap H9's steel M3x16 screw and spacer for nylon parts. They are the nearest metal to the BM83 antenna end at 16.3 mm [V]; the next metal is lid screws 3 and 8 (insert/screw) at 18.7-22.1 mm [V].
  - Also run an RSSI test front versus rear: the pack and the driver magnets sit between the antenna (rear-left) and a listener in front [J].
- **N2.** Field firmware updates need the lid off (11 screws plus the rocker fastons), and both the STM32 and the BM83 are flashed over headers [V].
  - J6 (SWD, 4-pin) has 19.9 mm under the top wall. Standard Dupont housings plus a wire bend barely fit, so use right-angle Dupont.
  - J7 (TC2030) has 28.4 mm. Check it with the real TC2030-CTX cable (already open in the CAD notes).
  - Flash the MCU and the BM83 on the bench before installation.
  - A USB or UART bootloader path would be a board change.
- **N3.** A removable front grille with magnets is not needed: the drivers are rear-mounted.
- **N4.** EMI: the class-D outputs already have 22 µH + 0.68 µF filters, and the encoder MP and USB-C shell are on GND [V]. No ferrites are needed on the internal leads for a prototype [J].
- **N5.** Thermal: no heatsink or thermal pad is needed for a prototype [J]. My estimate:
  - box surface about 0.14 m², PETG walls about 1.5 K/W total, so 4-5 W of internal loss (charging at 4 A plus amplifiers and boost) raises the air temperature about 6-8 K;
  - the TAS5825M (RθJA 24-30 °C/W [D]) at 1-1.5 W adds about 30-45 K over the box air.
  - Risk: at 35 °C room temperature while charging, the pack is near the 45 °C JEITA warm limit, so charging pauses. Log the NTC during the first charge tests.
- **N6.** Tamper resistance is already covered by the post-Torx choice.

### Already modelled (no action beyond the above)

Lid gasket (groove fill as S4), front perforated grille, woofer grille, rubber feet (placeholder), knob (stand-in), rocker (stand-in), Heyco grommet, strap on its tensioned path, pack brick (wrap, fish paper, nickel with fusible links, PCM, NTC), real J5/J9/J10/J11 wires with crimps and housings, inserts, spacers, screws, cup washers [V from the solid list].

---

## 3. Mechanical sanity re-check

### 3.1 Key numbers

| Item | Report value | Re-check | Status |
|---|---|---|---|
| Woofer chamber net | 0.524 L | volumes.md; Qtc 0.72 / Fc 86 Hz from the PE parameters | [V] |
| Main chamber net | 1.897 L | volumes.md; ND65 0.95 L each, Qtc 0.76, fc 112 Hz | [V] |
| SW100 to lid | 1.35 mm (body); tip 0.50 / 4.50 mm | meta `sw100`, SW100 bbox Y 198.65-202.1 | [V] |
| TP20 nearest body | 8.54 mm (H4 spacer) | fit_findings | [D] |
| Tightest gaps | J1/J2/J3 1.51-1.53 to the lid; C288/C301 2.0 to the HA1/HA2 screw heads; cells 0.251 to the cradle; J5 wires 0.1 to the wrap | meta `closest_parts_to_enclosure` and `pack` | [V] |
| Mass | 1879 g | the components sum exactly to 1879 [V]. Assumes 100% infill PETG and **steel** grilles (118 g); the buy list proposes FR4 grilles (about 25 g), so about 1.79 kg with FR4 and less with partial infill | [V]/[J] |
| CoM | (-0.34, 87.6, 42.1) | 57.05 mm above the floor (feet 15 mm) | [V] |
| Tipping | front 47.6° | Recomputed from the foot centres (±68, Y 25/135): front 47.6°, rear 39.7°, left 49.9°, right 50.1°. The rear is the weakest edge (the CoM is 47.6 mm from the rear foot line) but still stable | [V] |
| Woofer screws | M3x20, 3.4-4.4 mm engagement | marginal; unchanged (fastener agent) | [D] |
| Pack in cradle | 0.275 radial, 0.60 front, 0.63 rear | meta `pack` | [V] |
| Encoder | shaft 1.25 mm radial in the 8.5 hole; bushing top about 2.1 mm below the floor | measured | [V] |
| Driver screw access | not reported | L2/R4 blocked by the insert, L1 by the knob well | [V] new |
| PCB insertion path | not reported | impossible (finding 1) | [V] new |
| Pack/driver insertion with the insert in | not reported | impossible (finding 2) | [V] new |

### 3.2 Inconsistencies between CAD, BOM, RFQ and handover [V]

| # | Where | Conflict | Fix |
|---|---|---|---|
| 1 | buy list | Woofer **4 x M3x20** (or M3x22) screws are not on the list ("not on this list") | Add a line (ISO 4762 A2 M3x20, or M3x22 if the fastener agent chooses it) |
| 2 | buy list line 23 | Nylon lid washers still qty 11, A$ priced; mechanical-bom says 0 | Set the qty to 0 or remove; replace with the S2 neoprene washers |
| 3 | mechanical-bom.md | Woofer "bolt circle 77 ASSUMED, conflicts with the 76.2 cutout" | CAD v13+ uses a 96.52 bolt circle and M3x20; update the row |
| 4 | mechanical-bom.md vs buy list vs CAD | Woofer gasket: "83 OD / 70 ID in an 83.4 x 1.0 recess" vs "83 OD / 76.2 ID" vs CAD "factory 3.3 mm gasket, no recess" (`w_recess` 0) | Align on the CAD; buy the ring only if the factory gasket is missing |
| 5 | CAD params vs the modelled grommet | `grom_d` 6.0, `grom_web` 1.6, but the Heyco 2000 needs a 6.35 hole and a panel of at most 1.57 (buy list) | Set the CAD to 6.35 / 1.5 |
| 6 | mechanical-bom.md vs meta | Rocker "body about 11 behind the panel" vs meta `body_depth_behind_panel` 22.4 (bbox Y 184.2) | Measure the real GRB112B802BR1; update both |
| 7 | RFQ vs cradle | RFQ maximum thickness 23.0; cradle arcs cut for 21.75 (+0.275) | RFQ at most 22.3, or print the cradle after the drawing (S5) |
| 8 | mechanical-bom.md | Brick "86.8 x 73.7 x 21.7" (feasibility) vs CAD 86.85 x 74.47 x 21.75; PCM "60 x 3 x 18" vs 60 x 18 x 1.6; "v11 print-ready" title and v11 counts | Refresh from v15 |
| 9 | buy list strap line | Priced placeholder CE09642 (300 mm) is too short (at least 350 needed) | Source a ≥ 350 mm strap or the 20 mm VELCRO roll |
| 10 | buy list | Woofer row still cites the "CAD v11.2 conflict, clamp-ring fallback" | Update to the v13+ geometry |
| 11 | buy list | Heat-shrink, cable ties/mounts, Kapton, the 1 mm and 2 mm foam sheets and a pack fuse are absent | Add consumables lines (M4, M5, S1, S2, S10) |
| 12 | RFQ vs CAD | Lead 180 mm vs routed 131 mm | Fine for service slack (S9); add a tie point |
| 13 | mass | CAD uses steel grilles; buy list proposes FR4 | State which in the next CAD run |
| 14 | plan.md / HANDOVER header | plan.md header "Updated 2026-10-05", PCB status still R6q/R9 and "CAD v11 in progress"; HANDOVER top summary "refreshed 2026-10-10" (R6m) | Refresh both summaries (the dated sections below them are current) |
| 15 | release-todo-2026-11-03 | Still lists "pack 2P/3P/4P" and 12 open connections | Superseded by the 1S4P decision and RT-15H (9); mark the file as superseded |

Fastener counts agree: 19 countersunk T10 + 11 M3x16 + 4 M3x20 = 34 screws, 38 inserts, 11 spacers, 11 lid positions on the drawing [V].

---

## 4. Whole-project status

| Area | Done | Open | Risk |
|---|---|---|---|
| Schematic / ERC | 11 child sheets captured and integrated; P1/P4/P5 patches; ERC 240 = inherited set (238 lib_symbol_issues, 1 documented power_pin_not_driven, 1 same_local_global_label), 0 new [D] | Effective-capacitance and transient qualification; no status LED, button ladder or STAT; several "verify against datasheet" items (MFB polarity, BM83 caps) | Medium |
| PCB | RT-15H: DRC 0 violations, **9 unconnected**, 273/282 routed; paste windows on 10 exposed pads in the library; teardrops regenerate headless; GUI finish package ready [D] | Owner routes the 9 in the GUI; `regen_final.sh` PASS; adoption into `DesktopSpeaker-kicad/` (project still R6q); rules 20/21 into the project `.kicad_dru`; 13 accepted quality exceptions (B.Cu over void about 300 mm on slow nets, I2S BCK/SDATA 0.25 mm over 3.7 mm, HP_R 1.83x, 121 HA8 pairs, etc.) | Medium |
| BOM / stock / sourcing | JLC BOM 90 lines / 318 placements; hardware buy list about A$474 snapshot [D] | U1 BM83, U2 PCM2902C, U19 at 0 stock at LCSC/JLC (buy at DK/Mouser; BM83 variant question); pack unpriced; T10 screw price; cup washers; gasket foam; grilles not quoted; missing lines (section 3.2) | Medium-high (lead times) |
| Firmware | Full system spec (states, sequences, register values) [D] | **No code exists** [V: no MCU sources in the project]. Needed even for a first sound: charger CE default-off, TAS5825M coefficient load, PCM1862 setup, BM83 UART | **High** |
| Power / charge | Policy defined (ICHG 4.0 A, VREG 4.10 V, ITERM 1 A, timers, JEITA), standby estimate 57/105 µA, attach inrush [D] | All unbenched; TVS2200 clamp 28.0-28.35 V vs TPS25730D 28 V maximum (surge unproven); boost compensation calculated only; pack NTC and PCM unknown; no pack fuse (M5) | Medium-high |
| Acoustics / DSP | Volumes and alignment (Qtc 0.72 / 0.76) [V]; LR4 at 150 Hz proposal; PBTL pairing verified from the datasheet figure [D] | No PPC3 tuning; U7 (L+R)/2 mixer unverified; woofer parameters from the PE table only (no maker sheet); main-chamber leaks (finding 3); damping not specified | Medium |
| Mechanical / CAD | v15: 218 solids, 0 unintended overlaps, printable bodies, real wiring [D/V] | Findings 1-2 (assembly blockers); SW100 plunger; seals; anchors; placeholders (knob, feet, gasket, PCM); woofer dimensions are photo estimates; CAD must be rebuilt from the final board | **High** (until M1/M2 are fixed) |
| Hand assembly / stencil | Hand-assembly sheet and 0.10 mm stencil report (RT-14 draft); C215/C212-first rule; paste windows applied [D] | Regenerate for the final board; 40 courtyard pairs < 0.2 mm; via-in-pad joints to inspect; SW100 pad-corner nicks | Medium |
| Documentation / website | Single handover with dated sections; site shows CAD v15 and RT-15H [D] | plan.md and HANDOVER top summaries stale; mechanical-bom.md stale lines; release-todo superseded | Low |

### Top 10 risks to the first working prototype (ranked)

| # | Risk | Mitigation | Effort [J] |
|---|---|---|---|
| 1 | **Enclosure cannot be assembled** (PCB vs knob well; pack and drivers captive behind the bonded insert) | M1 and M2 in CAD v16, plus an insertion-path check script before printing | 1-1.5 agent-days CAD + about 1 day of printing |
| 2 | **No firmware**: the board is mute and charging is disabled without it | Start now: bring-up firmware (clocks, I2C scan, BQ25792 safe config with CE off, rails, TAS5825M init from PPC3 dumps, PCM1862 select), then BM83 UART | 2-4 weeks for a basic player |
| 3 | First power-up damage (TPS25730D 28 V maximum vs TVS clamp; untested boost compensation; PD at 20 V) | Bench order from the handover: current-limited 5 V first, then a known PD source, scope VBUS at attach; populate the power section first | 1-2 days |
| 4 | Hand-assembly yield on fine-pitch and exposed-pad parts (U11, TAS5825M, BQ25792, TPS61088, BM83) | Electropolished 0.10 mm stencil with windowed paste (done); order 5 boards and spare ICs; stage it (power, then digital, then audio); inspect with a microscope | 2-3 days per board |
| 5 | **Pack not ordered** (custom 1S4P, UN38.3 shipping to Australia, weeks of lead time) | Send the RFQ now with the M5 fuse/TCO and the 22.3 mm thickness limit; meanwhile bench on a lab supply plus a small protected 1S cell with a 10k NTC | Owner: 1 hour to send; 2-6 weeks of lead time |
| 6 | Long-lead silicon (BM83, PCM2902C, U19 at 0 stock at LCSC/JLC) | Order the identical MPNs from DK/Mouser now; confirm BM83 -00TA vs -00AA/-00AB with Microchip | Owner: 1 hour; lead time variable |
| 7 | TAS5825M PBTL mis-configuration (U7 leaving Hi-Z before DAMP_PBTL; no cycle-by-cycle limit in PBTL) | Follow the firmware rule; first test into 4 Ω dummy loads at low PVDD; read the fault registers | 0.5 day |
| 8 | Main-chamber leaks and rattles hurt the acoustics (finding 3, M4) | S1 seals, M4 anchors, S3 vent; impedance sweep and sine sweep (rattle check) | 0.5 day CAD + 0.5 day bench |
| 9 | Woofer dimensions are photo estimates (frame, gasket, holes, depth) and the screw engagement is marginal | Measure the sample before printing the shell; adjust the seat/bosses; M3x22 if chosen | 2 hours to measure + CAD rerun |
| 10 | SW100 plunger tolerance (unknown travel; board-to-lid stack) giving stuck-pressed or dead wake/ship | M3 plunger with 3 nub lengths; test ship-mode entry/exit on the bench | 2 hours |

Also watch [J]: BT range through the box (N1), charge pausing at 45 °C in warm rooms (N5), and J5 rated 8.5 A (genuine, unverified) against amplifier peaks of about 8.5 A [D].

---

## 5. What I would do next (in order)

**Owner**

1. Decide M1 (panel-mount encoder vs separate well cup) and M2 (removable insert vs bonded with a test-before-bond rule). Do not print the shell until both are decided.
2. Send the pack RFQ with the M5 secondary protection, thickness at most 22.3 mm and lead about 150-180 mm. Order BM83, PCM2902C and U19 from DK/Mouser (confirm the BM83 variant).
3. Route the 9 GUI connections (RT-15H), then run `regen_final.sh` to PASS; the agent then adopts the board and generates the fab outputs. Order the PCB plus the stencil.
4. Buy and measure the woofer, the ND65 tab polarity, the rocker depth and the knob. Approve the SW100 plunger concept and the LED decision (S15).

**Agents**

1. CAD v16 from the adopted board:
   - M1, M2, M3, M4, S1, S2, S3, S5, S7, S8, S9, S10, S12, S14 and S16;
   - re-run the interference, volumes and wire checks;
   - **add a scripted assembly-sequence check**: swept translation of the PCB, pack, drivers and woofer along their insertion paths, plus straight-tool access to every screw. The current checks only verify the final static fit.
2. Fix the BOM and documentation consistency (section 3.2):
   - buy list: M3x20, the nylon washer line, consumables, foam sheets, the fuse, the strap;
   - `mechanical-bom.md` refresh;
   - plan.md and the HANDOVER top summary.
3. Firmware bring-up skeleton (risk 2). Start in parallel now; it does not depend on the CAD.
4. Bench plan update for the 1S4P pack and the assembly order (section 6), then PPC3 tuning once the drivers are measured in the printed box.

---

## 6. Assembly order implied by the v15 geometry [V paths, J sequence]

Valid for the bonded insert. With a removable insert (M2), steps 3-6 can be redone later in reverse.

1. Fit the heat-set inserts (38) in the shell and the insert. Bond the front grille with its cloth and the woofer grille (with cloth, S13).
2. Fit the printed tie bridges (M4) or adhesive mounts. Thread the strap through both tunnels.
3. Fit the pack into the cradle from the open rear: the full 157 x 94 opening is still free. Close the strap and lay the J5 lead along the right side wall (tie it).
4. Fit the front drivers with gaskets; leads pre-soldered with the S9 slack, polarity checked. Drive the 8 screws. Before the insert goes in, 7 of them have a straight path from the rear. L1 (x -17.6, z 85) sits behind the knob-dish well, which is part of the shell, so drive it with a T10 post-Torx L-key or a short bit in a 1/4 in right-angle driver.
5. Test the drivers (continuity, polarity, a rub-and-buzz sweep from a bench amplifier) and the pack (voltage, NTC, PCM).
6. Insert: fit the grommet with the J11 adapter, then slide the insert in from the rear into the floor grooves; seal or bond it.
7. Fit the woofer from the open rear of the chamber: 51 mm internal height against 47.75 mm plus the gasket. Mate the PH pair, tie it to the anchor, add the damping, and drive the 4 M3x20 screws with a ball-end key.
8. Fit the encoder per M1 (panel-mounted), then the PCB:
   - flash the MCU and BM83 on the bench first;
   - plug J5, J9, J10 and J11 with the board held above its spacers;
   - lower the board and drive the 11 M3x16 screws. The deepest (HA1/HA2) are 120 mm from the lid face with 25.4 mm of headroom [V], so use an extra-long 2.5 mm ball-end L-key with a long arm of 140 mm or more. H8 is under the well.
9. Fit the rocker to the lid; connect its leads with the service loop; fit the SW100 plunger; fit the S1 foam and the S2 washers; drill the S3 vent.
10. Fit the lid gasket, then the lid (11 countersunk T10 screws), then the knob, then the feet.
