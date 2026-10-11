# Routing R6p (2026-10-12): teardrop strip/prune tools, detour and geometry cleanup

I worked only on copies in `ai-files/pcb/work-r6/`. I did not touch the project board `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb`, the schematics, the libraries or the rules. Nothing was committed and no process was killed. Background jobs I started were stopped with the task tool only.

- **Saved GUI board:** `work-r6/R6p-td-gui.kicad_pcb` (+ `.kicad_dru`) is a byte copy of the project board as the user saved it. It has 1979 teardrop zones; the "about 4100" in the brief is the raw `teardrop` text count. Its `.kicad_pro` = `R6o-final.kicad_pro`.
- **Base:** `work-r6/R6p-0.kicad_pcb` is R6p-td-gui with every teardrop removed, all zones refilled and the U14-L2 GUI edit undone (section A.2). It has the same copper as R6o-final.
- **Final:** `work-r6/R6p-final.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`). Gate files: `.drc.json`, `.open2.json`, `.isl.json`, `.bends.json`, `.strict.json`, `.sliver.json`, `.pour.json`, `.geom.json`, `.audiogv.txt`. Gate log: `r6p/final.gates.txt`.
- **Rules:** I changed no rules. `R6p-final.kicad_pro` / `.kicad_dru` are byte copies of `R6o.kicad_pro` / `R6o.kicad_dru`, the R6o rules including the USB waiver.
- **Renders:** `ai-files/pcb/route-r6p-top.png` (F.Cu + F.Silkscreen), `route-r6p-bottom.png` (B.Cu + B.Silkscreen) and `route-r6p-in2.png`. All three are without teardrops.
- **Logs (`work-r6/r6p/`):**
  - `geom0.*` / `geomF.*`: geometry reports before and after.
  - `imp1..4.log.json` / `.out`: one record per net for every re-route attempt.
  - `td-gui*.log` / `.drc.json`: pruner test.
  - `c*.json`: hand candidates and their legality checks.
  - `v/`: net views.
  - I deleted the intermediate boards.

## A. Teardrops

### A.1 Strip (`route_td_strip.py`)

`route_td_strip.py IN OUT [--nofill]` deletes every zone where `IsTeardropArea()` is true, then refills and saves. On R6p-td-gui it found 2062 zones, of which 1979 were teardrops, leaving 83 zones.

**Comparison with R6o-final** (`route_r6p_cucmp.py`: tracks, arcs and vias by geometry, width, layer and net; zone outlines, properties and filled area per layer; footprint position, rotation, FPID and pad nets):

| Item | Result |
|---|---|
| Vias, zones, zone fills, footprints | identical |
| Footprint fields | 0 changed. "Update PCB from Schematic" changed no field values. |
| Pad and via teardrop flags | `(teardrops … enabled yes)` added by the GUI. Harmless. |
| Tracks | **not identical.** Net-(U14-L2) was re-drawn in the GUI (A.2). |

### A.2 U14-L2 GUI edit: undone in R6p-0, decision for the user

In the saved board, the U14 switch-node link (U14.7 → L2.2) had been replaced. The R6o version was a 0.2 mm pin stub, a 1.0 mm arc and a 0.8 mm segment. The GUI version is a **0.3 mm polyline of 33 segments** (a segmented arc).

- **These are the 22 `track_width` DRC items** in the GUI board: rule `width_switch` has a minimum of 0.4 mm.
- It narrows a switch node from 1.0 mm to 0.3 mm.
- **What I did:** I restored the R6o-final copper of this one net in R6p-0 (`r6p/restore_l2.py`).
- **Where the GUI version is kept:** `R6p-td-gui.kicad_pcb`.
- **Your call:** if the re-draw was intentional, it has to be at least 0.4 mm wide, and widths of 0.8 to 1.0 mm are recommended.

**After the strip:** R6p-0 matches R6o-final in copper, with 0 differences in tracks, vias, zones and fills. R6p-0 gates = R6o-final gates (DRC 0/0, open 0, `.isl.json` identical to R6o-final).

### A.3 Why the GUI DRC showed 499 teardrop clearance errors

The fills were stale. The board was saved with the teardrop fills (and the GND fills around them) un-refilled. In KiCad 10 a teardrop is a zone, so a refill clips it to the clearance rules.

| R6p-td-gui after a refill only | Result |
|---|---|
| DRC | **0 teardrop items**. 22 `track_width` (U14-L2) remain, plus 0 clearance and 0 sliver. |
| Teardrops kept | all 1979 |
| Teardrop fill area | 614.7 → 613.0 mm² |

### A.4 Pruner (`route_td_prune.py`), ready for the final pass

`route_td_prune.py IN OUT [DRC.json] [--maxiter N]` loops:
1. Refill and save (it copies IN's `.kicad_pro` / `.kicad_dru` next to OUT).
2. Run kicad-cli DRC.
3. Delete only the teardrop zones that are items of a violation. It matches by uuid; the fallback is a "Teardrop [net] on layer" item whose reported position lies inside a teardrop of the same net and layer (0.05 mm).
4. Repeat until no violation involves a teardrop. It prints the remaining teardrop count and any non-teardrop violations, and never touches those.

Tests on R6p-td-gui:

| Mode | Iteration 1 | Final |
|---|---|---|
| Normal (refill first) | 22 violations, none teardrop | **1979 teardrops kept**, DRC = 22 `track_width` (U14-L2 only), 0 unconnected |
| Seeded with the stale GUI DRC (`r6p/td-gui.drc.json`) | 522 violations, 471 teardrops removed | **1508 teardrops**, DRC = the same 22 `track_width` |

So the refill alone clears the problem; pruning against a stale DRC removes 471 teardrops for nothing. In the final pass, refill (or use the pruner without a seed DRC), then run the full gate script. Teardrops change the GND fills slightly, so the island and sliver gates need re-checking with teardrops in place.

**Note:** `pcbnew.LoadBoard` / `Save` rewrites `STEM.kicad_pro` from the board's project. Run any helper on a board whose own `.kicad_pro` is correct, or copy `R6o.kicad_pro` back afterwards, as `route_r6o_eval.sh` does. A board in a sub-folder also loses the footprint library table (199 `lib_footprint_issues`), so the gates must run in `work-r6/`.

## B. Geometry: tool, findings, fixes

### B.1 `route_r6p_geom.py BOARD [--json] [--nets] [--top] [--all]`

Per net it reports:

- **(a) Acute turns:** a plain vertex (two same-net, same-layer ends; no via or pad) where the direction changes by more than 90°. Arcs count by their end tangents.
- **(b) Within 3 mm of path along plain chains:**
  - **U-turn:** the signed direction changes add up to ≥ 150°.
  - **Zig-zag:** ≥ 3 alternating bends of ≥ 30° each, or two opposite bends of ≥ 90°.
- **(c) Two-pin connections:** the ratsnest edges, i.e. a Euclidean MST over the pads of each copper-connected group. Each edge is measured along the copper (tracks, arcs, vias, T-joints and overlapping ends), giving routed length, straight distance, ratio, excess and vias.
- **(d) Net totals:** track length, via count, and the pad MST.

Pairs joined only by pours are not listed.

### B.2 Before and after (R6p-0 → R6p-final)

| Metric | Before | After |
|---|---|---|
| Acute turns (> 90°) | **0** | **0** |
| U-turns (≥ 150° within 3 mm) | 15 | 15. Same list except PD_PLUG_EVENT's In2 zig-zag (now gone); see B.5 |
| Zig-zags | 13 | 13. PD_PLUG_EVENT In2 wiggle gone; new BT_PWR_EN In2 wiggle (−41/+39/−42°, dodges a GND via) |
| Two-pin connections, ratio > 1.6 and excess > 10 mm | 29 | **23** |
| Two-pin connections, ratio > 1.3 and excess > 3 mm | 105 | 102 |
| Total track length, Default/I2C/SIGNAL nets | 4942.8 mm | **4681.2 mm (−261.6 mm)** |
| Vias, all nets | 964 | **889 (−75)**. GND 272 unchanged |

### B.3 Net lengths (every changed net; all re-routed by script, all gates held)

| Net | Before mm (vias) | After mm (vias) | Δ mm | How |
|---|---|---|---|---|
| /AUD_SDA | 277.9 (13) | **220.3 (10)** | −57.6 | Topology change: the 150 mm loop U7 → board edge → south → U6/U24 junction was ripped and replaced by one B route from the U3/U7 side to the U24 side |
| /BT_RST_N | 187.2 (8) | **141.2 (8)** | −46.1 | Full rip, turn penalty 3 (keeps the corner rule) |
| /PDCTRL_SDA | 148.5 (16) | **122.8 (8)** | −25.7 | Re-route |
| /PD_PLUG_EVENT | 105.5 (13) | **80.4 (6)** | −25.1 | Re-route, 4 mm pad-local stubs kept |
| /PD_SINK_EN | 134.2 (11) | **119.1 (9)** | −15.1 | Re-route |
| /Battery_Charger/CE_N | 68.1 (5) | **55.3 (2)** | −12.8 | Re-route. It also removed one foreign via from BAT_PACK_IN2 (32 → 31) |
| /BT_UART_TX | 146.3 (18) | **134.9 (9)** | −11.4 | Re-route |
| /MCU/ENC_SW | 203.5 (17) | **193.7 (3)** | −9.8 | Re-route; 14 layer hops removed (see B.4) |
| /BT_PWR_EN | 140.4 (7) | 130.7 (8) | −9.8 | Re-route |
| /CTRL_SDA | 172.3 (16) | **162.7 (7)** | −9.5 | Re-route |
| /GAUGE_ALRT_N | 119.0 (8) | 110.1 (4) | −8.8 | Re-route |
| Net-(U4-QON) | 135.5 (10) | 126.9 (8) | −8.6 | Re-route, 7 mm stubs kept (U4 neck) |
| /PDCTRL_SCL | 124.1 (13) | 117.0 (10) | −7.1 | Re-route |
| /AMP_BOOST_EN | 88.3 (7) | 83.2 (4) | −5.1 | Re-route |
| /CHG_QON_SENSE | 135.0 (13) | 130.1 (6) | −5.0 | Re-route |
| /AUD_SCL | 158.4 (10) | 154.3 (8) | −4.1 | Re-route. One bend moved by hand to keep 0.22 mm from the AMP_PDN via (`r6p/scl.json`) |

**Acceptance rule for every re-route** (`route_r6p_improve.py`):
- every routed net OK;
- kicad-cli DRC 0 violations and 0 unconnected;
- 0 open edges on the whole board;
- at least 3 mm shorter, and no more than one extra via per net.

Leftover dangling stubs were removed only where KiCad's own `track_dangling` / `via_dangling` verdict flagged them (by uuid, `route_r6p_dangle.py`).

**Afterwards:**
- `route_r6j_smooth.py` on the changed nets widened 13 short middles.
- The two remaining new corner hits came from BT_RST_N. I removed them by re-routing that net with a full rip and turn penalty 3.

### B.4 Priority nets: what limits them

**Main finding:** In2 is cut from top to bottom by the USB_VBUS_IN2 and VBUS_PD_IN2 / _G islands (x 135–153, y 27–130). Every east–west slow signal must cross that column on F or B. Below the U2/U4 area there is essentially **one free F/B corridor, at y ≈ 97 (x 128–160)**.

| Net | Result | Reason |
|---|---|---|
| ENC_SW (U3 → C310/SW102) | 203.5 → 193.7 mm, **17 → 3 vias** | Shares the y ≈ 97 corridor with CTRL_SDA. **Tested trade-off:** a direct ENC_SW route of **61–66 mm** is possible, but only if CTRL_SDA leaves the corridor. Then CTRL_SDA becomes 245–257 mm around the amplifiers and south edge (`v/s1.png`), worse overall and visibly worse. With CTRL_SDA in the corridor, the best ENC_SW was 137–160 mm via the north (y ≈ 40) crossing, but that cost PD_SINK_EN and BT_RST_N length, so the greedy sequence kept the shorter total. **Needs your decision:** accept CTRL_SDA via the south to get ENC_SW direct, or move one of them to a different pin, or open a second corridor (e.g. narrow VBUS_PD_IN2_G at one y band). |
| AMP_FAULT_N | **232 mm, unchanged** | Topology U3/U7 (east) ↔ U6/R262/TP20 (west). The router finds no west–east path except the existing board-edge loop, even with the loop alone ripped and a full-board window. The south-middle has the SYS/BAT/PVDD In2 islands and the amplifier B keep-outs. Needs a corridor decision (as for ENC_SW) or a different MCU pin closer to the amplifier side. |
| AUD_SDA | 278 → 220 mm | U3 → U24 still runs 157 mm, around the U2/U4 block. The 70 mm path the router found on R6p-0 was taken by later accepted routes. Same corridor limit. |
| BT_RST_N | 187 → 141 mm | Done |
| CTRL_SDA | 172 → 163 mm | Done (corridor) |
| CTRL_SCL | 140.5 mm, unchanged | Every re-route was longer (+0 to +3.5 mm) or failed at the U4 neck |
| QON | 135.5 → 126.9 mm | Done |
| PD_SINK_EN | 134 → 119 mm | Done |

### B.5 Remaining U-turns and zig-zags (all inherited, each checked)

The candidate polylines were checked with `route_r6p_try.py`, which applies the route_r6k_why rules; the blockers are named.

| Item | Why it stays |
|---|---|
| USB_DP / USB_DN (6 U-turns, 1 zig-zag) | USB copper must stay untouched (J1 interleave / serpentine) |
| HP_EN at U3.47, PD_PLUG_EVENT at U3.4 | Pin escapes under the LQFP body, a ~1.5 mm hook to the via. **HP_EN:** east is blocked by the SWCLK F lane and west by the HP_DET In2 track and the ENC_A / ENC_SW vias. **PD_PLUG_EVENT:** the pin-1…3 escapes block the west side. |
| U6/U7 BST_B−/OUT_B−(+) nests (8 items) | On U6 the bootstrap cap C288 sits below C286; U7 is the mirror image. The two traces must wrap around the upper cap. Only fixable by moving or rotating the caps; I left them because of amplifier layout sensitivity. |
| U6/U7 VR_DIG 90/90 Z | A direct 45° path is blocked by the 3V3_AUDIO track and pad C281.1 / C294.1 (needs 0.2 mm) |
| Net-(U14-FB) | Must pass around C140 and the SYS_RAW trunk on F. A B hop is blocked by the SYS_RAW via (POWER_HI 0.4 mm) and R142. |
| Net-(U8-NO2) | Must pass under pin U8.5 (HP_SEL_A exits upward) and between pin 5 and R229.1. The direction change is inherently about 170°. |
| U1-SYS_PWR, LDO_3V3 (U11 pin 1 ↔ 3 jumper) | Escape between BM83 pads; a pin-to-pin jumper around pin 2 |
| USB_CC1, U2-XTO, C205-Pad2, BT_PWR_EN wiggles (30–45°) | Each bend dodges a via or pad: USB_DN via, Y170 pads, GND / 3V3_AUDIO vias, GND via 159.85, 52.6 |

## Gates (R6p-0 → R6p-final, R6o rules)

| Gate | R6p-0 (= R6o-final) | R6p-final |
|---|---|---|
| Open edges (`route_p2_open2.py all`) | 0 | **0** |
| DRC violations / unconnected (USB waiver rule as is) | 0 / 0 | **0 / 0** |
| Strict DRC (1 mm pieces) | U24 XI / VINR2 0.2 mm; USB gap pieces | **the same 3 items** |
| In2 islands (`route_r6h_isl.py` vs R6p-0) | 1 outline each | **1 outline each**. BAT_PACK_IN2 +1.7 mm² and VBUS_PD_IN2_G +0.5 mm² (fewer vias) |
| Power union pieces / pour areas | – | unchanged (VBUS_PD In2 679.5 → 680.0 mm²) |
| Foreign non-GND vias in In2 islands | 32 | **31** |
| In2 slow signals < 0.3 mm to an island | none | none |
| AUDIO / I2S / USB / clock on In2 | none | none (`in2_power_only` 0 items; VMID_HP re-route not accepted) |
| Corner hits (`route_r6i_bends.py`) | 5 | **5, all inherited** |
| Via centre in SMD pad | 3 | **3** (R10.2, R224.1, C215.1) |
| Narrow copper in net union (`route_r6m_sliver.py`) | 0 | **0** |
| Audio/I2S vias without a GND via ≤ 1.2 mm (`route_r6k_audiogv.py`) | 5 | **the same 5**, no regression |
| USB copper (`r6l/usbcmp.py`) | 52 items | **52, identical** |
| Net / pad-net changes (`route_r6l_netcmp.py`) | – | 0 / 0 |
| GND fill pieces / floating | F 5 / In1 1 / In2 116 / B 5, 0 floating | F 5 / In1 1 / **In2 90** / **B 14**, **0 floating** |
| GND area In1 / In2 / B | 16519 / 7848 / 15206 mm² | 16568 / **8974** / 14710 mm² |

**GND fill changes:**
- **In2:** gains 1126 mm² because fewer slow traces and vias cut it.
- **B.Cu:** loses 496 mm² and splits into 14 pieces, all via-stitched, because the re-routes moved slow signals from In2/F to B.
- **In1:** 16519 → 16568 mm² (fewer antipads).

## Exceptions (complete list)

**New in R6p:**
- **U14-L2 GUI re-draw undone** in R6p-0 (section A.2). Decision for the user.
- **B.Cu GND** is down 3.3 % in area, with 14 fill pieces instead of 5 (0 floating).
- **ENC_SW and AMP_FAULT_N remain long** (corridor limit, B.4). The ENC_SW / CTRL_SDA trade-off needs a decision.
- **One new small In2 wiggle on BT_PWR_EN** (≤ 42°, forced by a GND via). The PD_PLUG_EVENT In2 wiggle is removed.
- **AUD_SCL bend** at 137.95, 106.52 has 0.222 mm to the AMP_PDN via (rule 0.2).

**Inherited, unchanged:**
- USB waiver.
- 3 via-in-pad.
- 3 strict-DRC items.
- 5 corner hits.
- 46 per-zone edge strips.
- 5 audio vias without a GND via.
- PGND per-via target.
- Teardrops: the final board has none. Regenerate them in the GUI, refill, then run `route_td_prune.py` and the gates.

## Helpers (new, `ai-files/helpers/`)

| Helper | Purpose |
|---|---|
| `route_td_strip.py` | Delete every teardrop zone, refill and save |
| `route_td_prune.py` | Delete only the teardrops that are items of DRC violations, looping until DRC has no teardrop item; refills first |
| `route_r6p_cucmp.py` | Copper comparison of two boards (tracks, vias, zones and fills, footprints, field changes) |
| `route_r6p_geom.py` | Acute turns, U-turns, zig-zags, ratsnest detours and net lengths |
| `route_r6p_improve.py` | Greedy rip/re-route driver with DRC, open-edge and length acceptance and a dangling cleanup (`IMPTMP`, `--keep`, `--min`) |
| `route_r6p_dangle.py` | Remove the tracks / vias KiCad flags as dangling, by uuid |
| `route_r6p_try.py` | Legality check of candidate polylines and vias with blocker names |
| `route_r6p_netsvg.py` | Net-highlight SVG view of the board (convert with `route_p1_png.mjs`) |

**Reproduction:**
1. `route_td_strip.py R6p-td-gui → R6p-0`, then `r6p/restore_l2.py R6o-final R6p-0`, refill.
2. `NOPRUNE=1 route_r6p_improve.py` with `r6p/mkplan.py`, passes `imp1` (keep 1.5), `imp2` (keep 4) and `imp3` (keep 7).
3. `route_r6i_route.py … r6p/try/sda2.json` (AUD_SDA loop rip).
4. `imp4`.
5. `route_r6j_smooth.py --nets …`.
6. BT_RST_N full-rip re-route with turn 3 (`mkplan … 1 … '{"turn":3}'`).
7. `route_r6l_edit.py … r6p/scl.json`.
8. Copy to R6p-final, then run `ISLREF=R6p-0 route_r6o_eval.sh R6p-final R6p-0 full`.

The per-net verdicts are in `r6p/imp*.log.json`.
