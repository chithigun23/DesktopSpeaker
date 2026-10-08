# Routing plan review (2026-10-08): `pcb-routing-plan.md` against P1-P3, the R5 review and v10b M6

This is a read-only review. It covers the plan as the method for routing placement v10c. It draws on `pcb-routing-p1/p2/p3.md`, `pcb-routing-review.md` (R5), `pcb-layout-best-practices.md`, `pcb-placement-v10b-review.md` (M6) and the active `DesktopSpeaker-kicad/DesktopSpeaker.kicad_dru`. No board or rule file was changed.

**Verdict:** the plan's intent is sound. The layer roles, the "pours for power" and "audio on L1 over solid In1" rules, the block guidance and the post-route list are all right. As an executable method it is not ready. It contradicts the process that actually produced connectivity in P1-P3, and its rule set cannot be met at 0.4-0.5 mm pitch. Once those rules were relaxed board-wide, the relaxations hid real defects in R5: the 0.2 mm power necks, BATP sitting 0.31 mm from SW1, and audio clearance turned off by `neck_exempt`. Its order of operations also let the routers strip thermal vias and decoupling vias. Fix the items in sec. 1 before v10c routing starts.

## 1. Must-fix before routing

**MF1. Replace the width floors and the width-based neck exemption with area-scoped neck rules.**
- `width_power` 0.5 and `width_5v` 0.4 apply everywhere. The U4 VBUS pins (0.2 mm at 0.4 pitch), the U25 VOUT pins (0.25) and the U6/U7 PVDD pins cannot be entered legally, which accounts for P2/P3's 199 `track_width` items.
- P2's `neck_exempt` (either track < 0.26 mm) switched off `audio_clear` and `clk_clear` board-wide (review M11). Inside the 199 "necks" it hid real defects: PVDD 0.2 x 3.4 mm and 0.2 x 7 mm, SW2 0.2 x 1.45 mm, and VBUS_PD at 0.2 mm.
- Fix:
  - Allow 0.2 mm width and 0.2 mm clearance only inside named fine-pitch courtyards plus a 1.5 mm rule area. That is v10b M6's proposal (rule text in sec. 4).
  - Add a script gate that measures each sub-floor segment's distance from its own pad: at most 1.0 mm (1.5 mm inside a neck rule area). Any longer one fails.

**MF2. Rewrite `switch_clear` as two rules: voltage clearance and noise clearance.**
- 1.0 mm board-wide is unroutable at the amp and charger corners, because BOOT is not exempt and the PMID/SYS stubs sit at 0.45 pitch. P2's 0.3 mm board-wide fix removed the protection that mattered: SW1 to BATP measured 0.31 mm, SW2 to ILIM_HIZ 0.31 mm.
- All the custom clearance rules also exclude pads (`A.Type != 'Pad' && B.Type != 'Pad'`). So no rule protects a BATP or FB track from an SW or OUT pad, or from an inductor pad.
- Fix:
  - SWITCH against power or BOOT nets: 0.3 mm (22 V voltage clearance; IPC allows 0.1).
  - SWITCH against SIGNAL, I2C, AUDIO, I2S_CLK and USB: 1.0 mm, pads included. Only pad-to-pad pairs are excluded.
  - SWITCH against Net-(U4-BATP), Net-(U25-FB), Net-(U25-COMP) and Net-(U25-ILIM): 2.0 mm.
  - All of these are overridden only by the neck areas.

**MF3. Add a via policy for 0.4-0.5 mm pitch and hand-soldered 0402s.**
- The plan's only via sizes are 0.6/0.3 and 0.8/0.4, and it has no rule about via-in-pad. The results:
  - P3 left 16 GND pads with "no legal via within 6 mm".
  - The routers placed 178 untented vias in SMD pads (review M1), including C105 SYS, the Y200 pads, U25.11/20 and the L1 SW1 pad.
  - The active `via_min` (0.3 mm hole) flags U11's own 0.2 mm footprint vias as 8 `drill_out_of_range` errors.
- Fix:
  - Standard via: 0.6/0.3 (0.3 hole ≈ 1 A).
  - Fine via: 0.45/0.2, allowed only inside neck areas and for GND escapes. JLC 4-layer builds 0.2 mm drills. Confirm in the quote whether it adds cost; if it does, accept 0.5/0.25.
  - Power arrays: 0.8/0.4.
  - Via-in-pad: allowed only in EP/thermal pads, plus a short list of named IC power pins with POFV ordered. Otherwise use a dogbone with 0.25 mm from the pad edge. KiCad DRC does not flag a same-net via inside a pad, so this must be a script gate.
  - Add a U11 rule exception for its 0.2 mm footprint vias, and make those vias solid (no relief).

**MF4. Lock items and fix the order of operations so no router can delete design-critical copper.**
- In P1 the P0 GND vias and stubs were stripped. In P2, 68 nets were ripped up and 189 GND stubs lost their vias. The EP arrays dropped to 1/1/0 vias (U6/U7/U25, review B2).
- Plan sec. 3 says power first. P1 actually routed signals first with Freerouting, and P2 then ripped them up to make room for power. The routers treated the planned via fields as obstacles that could be removed.
- Fix:
  - Run the order in sec. 3 below.
  - EP arrays, power via fields, power polygons and hand-routed critical nets get KiCad `locked` and are exported as fixed wires (`(type protect)`) in the DSN.
  - The own A* rip-up treats locked items as hard obstacles.
  - A gate counts EP vias and via-field vias after every phase.

**MF5. Decide the copper weights and power widths before any power routing.**
- The plan rests BAT 8-9 A and SYS 6-8 A on L3 pours, but the stackup still says 0.5 oz inner, and "1 oz inner" is still open.
- IPC-2221 at a 10 K rise gives the following widths for a single layer:

| Current | 1 oz outer | 0.5 oz inner | 1 oz inner |
|---|---|---|---|
| 3 A | 1.4 mm | ≈ 9 mm | ≈ 3.9 mm |
| 5 A | 2.8 mm | | |
| 8 A | 5.3 mm | ≈ 32 mm | ≈ 14 mm |

- Fix:
  - Order 1 oz inner and set 0.035 mm in the stackup. This was already the plan's recommendation; make it a decision.
  - Restate the trunk minima per layer pair. Each sum is F.Cu plus In2 or B.Cu, with via arrays at every transition:
    - BAT_INT/BAT_PACK/PACK_RAW (8 A): F.Cu ≥ 5 mm + In2 ≥ 12 mm, or F.Cu + B.Cu.
    - SYS_RAW (8 A): the same as BAT.
    - VBUS (3 A): F.Cu ≥ 1.5 mm + In2 ≥ 4 mm.
    - PVDD (3 A average, 8 A peak): F.Cu ≥ 2 mm + In2 ≥ 4 mm.
    - SW1/SW2 (5 A): F.Cu polygons at least the inductor pad width, under 5 mm long.
    - U25 SW (8.7 A peak): a polygon as wide as the L200 pad.
  - The plan's 1.5 mm "pref" width for SWITCH is not enough for SW1/SW2 and U25.

**MF6. Turn In2 and B.Cu into planned planes, not leftover space.**
- The plan says In2 holds power islands plus "a few slow signals", and B.Cu holds a GND pour plus slow signals. In P1-P3 they ended up as:
  - 1.6 m of signal on In2, about 250 mm of it inside other-net islands, splitting them into fragments
  - 579 mm of AUDIO on B.Cu
  - a B.Cu GND pour in 19 fragments
  - only 1 via under each amp heat spreader
- The stackup makes this worse. In2 sits 0.21 mm from B.Cu and 1.065 mm from In1, so In2 signals reference the (fragmented) B.Cu GND, not In1. B.Cu signals reference In2 power islands.
- Fix:
  - Draw the In2 power islands as final polygons before signal routing. They follow the v10b via fields: SYS/BAT ≥ 12 mm, VBUS_PD, PVDD ≥ 4-6 mm, 5V, 3V rails.
  - Export them to the router as keep-outs for other nets on In2. In2 signals are allowed only in drawn corridors between islands, and only in the SIGNAL and I2C classes.
  - On B.Cu, add rule areas that keep out tracks and vias of other nets:
    - under each amp: ≥ 900 mm², as the GND heat spreader
    - under the BM83 module
    - under the PCM1862/PCM2902/mux audio region
  - B.Cu signals elsewhere must run over In2 GND (no island), or right beside an F.Cu GND pour. Better: put a GND patch on In2 under any B.Cu signal corridor.
  - AUDIO, I2S_CLK, USB and crystal nets: F.Cu only (sec. 2.4 gives the single exception).

**MF7. Router rules must come from a config, not from the netclass clearance.**
- The `.kicad_pro` netclass clearance is 0.2 for every class, chosen so the pad pitch passes. Freerouting reads only the DSN, so it never sees `audio_clear`, `clk_clear` or `switch_clear`. P1 worked around this with keep-out halos and DRC rip-up loops, which is why managed classes plateaued at 105-170 open edges.
- Fix:
  - `route_p1_dsn.py` config: routing width 0.2 (0.25 for AUDIO/I2S/USB), clearance 0.21, and the 0.5/0.4 halos around already-locked AUDIO/I2S/USB/SWITCH copper.
  - The final widths and clearances are enforced by DRC plus a post-route widening pass (`route_p1_widen.py`).
  - Record this method in the plan. It replaces the plan's claim that "netclass widths/clearances [are] exported from KiCad (DSN)".

## 2. Should-fix

1. **Audio vias.** "No vias on AUDIO" left 17 audio edges open in P1. A test that allowed vias routed 24 of 34, and v10b already reserves audio-class vias (U8 COM1, U9 HP_L/COM2). Rule:
   - At most one B.Cu jumper per audio net, no longer than 6 mm.
   - A GND via within 1 mm of each signal via.
   - In2 above the jumper must be GND or empty, never a power island.
   - The jumper is listed in the report.
2. **The I2S length limit.** 60 mm is an EMI and crosstalk number, not a signal-integrity one: BCK is about 3 MHz. The v10 star is 51-61 mm. Set the limit to ≤ 70 mm, with a 22-33 Ω series resistor at the source on each branch (or one at the source if the branches stay under 15 mm), F.Cu only, and no TP stubs over 2 mm. Drop "length-matched to 5 mm", which is meaningless at I2S rates.
3. **Thermal arrays.**
   - "About 20 vias at a 1.0-1.2 mm pitch" does not fit a 3.45 mm TAS5825M EP. Use 4x4 at 0.9 mm inside the pad, plus 4-8 more in the GND flood beside the package.
   - U25 pad 21: at least 6.
   - U4: per its footprint.
   - All solid connection (no relief), tied to In1 and the B.Cu spreader.
4. **The SW via text.** Delete "4+ vias in the pins only to L1 pads" (sec. 3, charger), which is ambiguous. SW1/SW2/U25 SW/OUT_x get no vias, apart from documented exceptions. BTST links may change layer (v10b M3 BTST2 on B.Cu) but count as switching for the noise rule: 1 mm from BATP, run under 2.5 mm.
5. **The leftover protocol** (the plan has none).
   - After two router rounds with no gain, classify each open edge as placement-blocked, via-blocked or search-blocked.
   - Placement- and via-blocked edges go back as a placement fix list. P3 and v10b show this, and v10c is that fix.
   - Search-blocked edges are hand-routed, with a named owner.
   - No new rule relaxation unless it is area-scoped and recorded with a reason.
   - Never accept dangling or isolated copper.
   - Each net is pruned or completed whole.
6. **The connectivity oracle.**
   - `kicad-cli` caps `unconnected_items` at 499 in the JSON, and the P1 oracle treats a zone as one node. Use `route_p2_open2.py` (fragment-aware) for every gate.
   - Run DRC on the board inside the project folder (or with the fp-lib-table) so the 199 `lib_footprint_issues` artifacts disappear.
7. **Teardrops.** The GUI-only flow is correct for 10.0.6. Add the following:
   - Disable teardrops on pads narrower than 0.3 mm (the QFN 0.4-0.5 pitch pins of U4/U6/U7/U11/U25/U3/U24, and J1). These cause clearance hits.
   - Remove teardrops, re-add them, refill zones, then run DRC as the final step. A teardrop zone count is part of the gate.
   - The user's GUI session is the only way. Schedule it once, after sign-off.
8. **Stale text.** Two sections are numbered "7". Sec. 4 (the v3 decoupling table) and the v3 coordinates are obsolete; replace them with a pointer to the v10c distance check. The TPS61088 open item is still only an excerpt, so verify U25 pins against the full datasheet or record that the v10 footprint check covers it.
9. **Hygiene gate.** Report counts after the cleanup pass, each with a target:
   - acute joints and segments under 0.08 mm: 0
   - any-angle segments
   - 90-degree corners on power and RF nets

   Run a simplify or retrace pass after the A* router: its raster staircases and the 790 any-angle segments came from it.

## 3. Revised order for v10c

| Phase | Who | What | Gate before next phase |
|---|---|---|---|
| 0 | script | Rules from sec. 4. Lock the EP arrays and v10b via fields. Dogbone GND vias for every decap and GND pad (no via-in-pad). In1 solid GND. In2 islands drawn final. B.Cu keep-out areas (amps, BM83, audio). Antenna keep-out on all layers. | DRC clean apart from unconnected items. EP via counts (U6/U7 ≥ 16, U25 ≥ 6). Via-in-pad = 0 outside the allowed list. Island via counts: VBUS 6, VBUS_IN 15, SYS 12, BAT 18, PVDD 8. |
| 1 | own A* + hand, F.Cu polygons | Hot loops and switch nodes: U25 VOUT ceramics and SW, U4 SYS/PMID/VBUS caps and SW1/SW2, U6/U7 PVDD caps, OUT_x→L, BST. Then trunks as F.Cu + In2 pours to the via fields: VBUS, SYS, BAT, PVDD, SPK_OUT. Lock. | Widths per MF5. Neck lengths ≤ 1 mm. Loop areas (plan sec. 7). SW distance to sensitive nets ≥ 1 mm (2 mm for BATP/FB/COMP). |
| 2 | hand / A*, F.Cu only | USB pair (J1→D1→R171/172→U2, 0.25/0.15, no vias), CC to U11, crystals, I2S star, AUDIO and mux nets (≤ 1 jumper each). Lock. | Skew ≤ 0.5 mm, uncoupled ≤ 3 mm. AUDIO/I2S/USB copper on B.Cu/In2 = 0 (except listed jumpers). Audio ≥ 20 mm from class-D/boost copper. |
| 3 | own A* (fine pins) then Freerouting | Fan-out escapes of U3/U4/U6/U7/U11/U10/U24 with the 0.45/0.2 vias. Then Freerouting, chunked, `-mp 1`, shortest first: PWR_3V/5V/LOCAL, I2C, SIGNAL. B.Cu allowed outside keep-outs, In2 only in corridors. | Open edges (open2) per class. In2 signal length inside islands = 0. B.Cu GND fragments: no new ones larger than 1 mm². |
| 4 | script | Widen to the class preference. GND re-attach. Stitching on a 5 mm grid (≤ 3 mm at the BM83 and edges). Audio/amp fence. F.Cu GND fill in free areas. Hygiene cleanup. | Leftover protocol (sec. 2.5). 0 unconnected. |
| 5 | user GUI + script | Teardrops, refill zones, final DRC, then the width, via-in-pad, decap-via, loop and teardrop scripts. | Acceptance criteria below. |

**DRC acceptance.** The following must all be 0:
- clearance, shorting_items, unconnected_items (open2 = 0)
- track_dangling, via_dangling, isolated_copper, items_not_allowed
- track_width outside neck areas
- drill_out_of_range (U11 is covered by its exception)
- skew/diff_pair items

Remaining allowed items: only the recorded inherited footprint and silk items (SW100 hole_clearance until its footprint is fixed, LOGO1/J10/SW101 silk). Every exception is listed by item.

## 4. Proposed rule set (replaces the active `.kicad_dru` rules 3 and 5, and adds new rules)

KiCad gives precedence to the later rule, so the neck rules come last.

```
(rule switch_power      # voltage clearance between switch nodes and power/boot copper
  (condition "A.NetClass == 'SWITCH' && B.NetClass != 'SWITCH' && B.NetClass != 'GND' && !(A.Type == 'Pad' && B.Type == 'Pad')")
  (constraint clearance (min 0.3mm)))
(rule switch_sensitive  # noise: pads included, only pad-pad pairs exempt
  (condition "A.NetClass == 'SWITCH' && (B.NetClass == 'SIGNAL' || B.NetClass == 'I2C' || B.NetClass == 'AUDIO' || B.NetClass == 'I2S_CLK' || B.NetClass == 'USB') && !(A.Type == 'Pad' && B.Type == 'Pad')")
  (constraint clearance (min 1.0mm)))
(rule switch_critical
  (condition "(A.NetClass == 'SWITCH' || A.NetClass == 'BOOT') && (B.NetName == 'Net-(U4-BATP)' || B.NetName == 'Net-(U25-FB)' || B.NetName == 'Net-(U25-COMP)' || B.NetName == 'Net-(U25-ILIM)') && !(A.Type == 'Pad' && B.Type == 'Pad')")
  (constraint clearance (min 2.0mm)))
(rule width_power  (condition "A.NetClass == 'POWER_HI' || A.NetClass == 'PVDD' || A.NetClass == 'SPK_OUT'") (constraint track_width (min 0.5mm)))
(rule width_switch (condition "A.NetClass == 'SWITCH' || A.NetClass == 'PWR_5V'") (constraint track_width (min 0.4mm)))
(rule via_fine     # 0.45/0.2 only in neck areas (see neck_*), elsewhere 0.6/0.3
  (condition "A.Type == 'Via'") (constraint hole_size (min 0.3mm)) (constraint via_diameter (min 0.6mm)))
(rule u11_fp_vias  (condition "A.Type == 'Via' && A.memberOfFootprint('U11')") (constraint hole_size (min 0.2mm)))
# ... audio_clear, vbus_clear, pvdd_clear, clk_clear, usb_diff, rf_keepout, fine_pitch, edge_hole unchanged ...
(rule neck_ic      # LAST: pin-pitch escapes only inside fine-pitch courtyards + NECK_* rule areas (1.5 mm halo)
  (condition "A.intersectsCourtyard('U3') || A.intersectsCourtyard('U4') || A.intersectsCourtyard('U6') || A.intersectsCourtyard('U7') || A.intersectsCourtyard('U10') || A.intersectsCourtyard('U11') || A.intersectsCourtyard('U14') || A.intersectsCourtyard('U15') || A.intersectsCourtyard('U24') || A.intersectsCourtyard('U25') || A.intersectsCourtyard('J1') || A.intersectsArea('NECK_U4') || A.intersectsArea('NECK_U6') || A.intersectsArea('NECK_U7') || A.intersectsArea('NECK_U25')")
  (constraint track_width (min 0.2mm))
  (constraint clearance (min 0.2mm))
  (constraint hole_size (min 0.2mm))
  (constraint via_diameter (min 0.45mm)))
```

Notes:
- **`memberOfFootprint` and other function names:** check them against the KiCad 10 syntax. `insideCourtyard` is the deprecated alias of `intersectsCourtyard`. Test with a DRC dry run on the v10c board before routing.
- **`neck_ic` clearance:** this rule also lowers `audio_clear` near U24/U10 pins (intended), but not outside the courtyard and halo.
- **`switch_sensitive` at U4:** if a SW pin's direct neighbour is a SIGNAL-class pin, the courtyard rule takes over at the pins.
- **Netclass table (plan sec. 2):** keep it.
  - Change SWITCH pref to "polygon at the pad width" and its via to "none".
  - Change GND DRC min 0.4 to 0.2 in neck areas (GND escapes from 0.2 mm pads).
  - Add the "fine via 0.45/0.2" preset.

## 5. What is OK (keep it)

- **Layer roles:** In1 solid GND with no routing. All parts on top. The antenna keep-out on all four layers (0 hits in every run).
- **Stackup and copper weight:** JLC04161H-7628 and 1 oz outer. USB 0.25/0.15 ≈ 90 Ω, pending the JLC calculator.
- **Netclass assignment:** the exact-name patterns after the `[..]` fix (re-verify the count for v10c's nets).
- **Block guidance in plan sec. 3:** BQ25792 priority order, TPS25730 CC caps with the via after the cap, TAS5825M PVDD caps without vias, PCM1862 one plane, BM83 with no L1 routing under the module.
- **Values that held up:** clearances `audio_clear` 0.5, `clk_clear` 0.4, `vbus_clear` 0.4 and `pvdd_clear` 0.3 as DRC values (not as router clearances). Speaker output trunks at 2.0 mm on F.Cu.
- **Post-route checklist (plan sec. 7):** a good base; extend it with the gates in sec. 3.
- **Freerouting usage:** chunked runs with `-mp 1` and the SES merge, as in P1.
- **Process safety:** never use `pkill -f`. Treat the first full route as a draft.
