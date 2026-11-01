# Routing S0b (escape copper) and USB J1/U2 template (2026-11-02)

Agent: "S0b escape copper and USB J1 template". Input `ai-files/pcb/work-r10/R10-0.*` copied to `ai-files/pcb/work-route/RT-0.*`. Output `ai-files/pcb/work-route/RT-1.kicad_pcb/.kicad_pro/.kicad_dru`. Placement frozen (0 footprint poses changed). All edits are text edits (`work-route/scripts/edit.py`), zones refilled in a separate pcbnew process (`helpers/route_oct_refill.py`) with the pristine project `.kicad_pro/.kicad_dru` beside the board. Rule files of RT-1 have the project SHA-256 (dru 102fbee4…, pro aa88e8c9…). Nothing in `DesktopSpeaker-kicad/`, `work-r10/`, `helpers/` or `work-oct2/` was edited. Not committed.

## 1. Result

| gate | RT-0 (= R10-0) | after task A (A3) | RT-1 (A + B) |
|---|---|---|---|
| DRC `--severity-all --all-track-errors`, violations | 0 | 0 | **0** (no USB gap / skew / uncoupled items) |
| DRC unconnected | 295 | 294 (XTO U2-20 -> Y170-3 closed, intended) | **285** (+ 9 USB connections closed, intended) |
| unconnected items that changed other than intended | - | 0 | 0 (the pre-existing LDO_3V3 island near U11-1 keeps 1 item; only its reported anchor differs) |
| pad nets (1192 pads, by ref/pad) | - | - | **0 differences**; 0 footprint pose changes |
| exit probe, failing signal pads, whole board (`scripts/probe.py`, same model as R10 `r10lib.exits`) | 56 | **28** | 30 = 28 + J1-A6 and U2-1 (both now routed USB pads, blocked only by their own USB partner track) |
| new copper exact 0/45/90 (own gate, all 78 added segments, 138.7 mm) | - | - | **100 %**, 0 not exact |
| `route_oct_check.py` on USB + XTO nets | - | - | exact 100.000 %, max dev 0.0000 deg, joints < 90 0, 90-deg away from pads/vias 0, shorts 0, dangling 0, pad exit short 0, par < 0.6 mm 0.0 mm, T-junctions 3, bend spacing short 1 |
| r7 joints < 80 deg (whole board) / < 30 | 22 / 7 | - | **19 / 7** (not increased) |
| r7 F.Cu over In1 void (whole board) | 7.8 mm | - | 9.2 mm (+1.4 mm = antipads of the 3 DP vias) |
| sentinel rule (`route_oct_sentinel.sh`) | - | - | **FIRES** (4 track_width items) |
| copper lock | - | - | 1616 of 1668 RT-0 items byte-identical in RT-1; manifest SHA-256 of the untouched set `4b4f452819c5d6380bcb7851255b37acbcc532f6d1aacd7aae7297feabd338d6`; the 52 removed/changed and 100 added/changed items are listed in `RT-1.gates.json` |

Target "below 20 failing exit pads" was **not reached (28)**. 19 of the 28 are pad-bound (blocked by a foreign pad or a design rule at the pad itself) and cannot be fixed by copper with placement frozen (section 3).

## 2. Task A: copper-only escape fixes (3 iterations)

| iteration | change | probe |
|---|---|---|
| A1 | U9 GND vias, U15, U10, R120, R102, R18, U23 GND vias/tracks; D5/D6 GND; U16 3V_AO; C206/C207 AVDD reroute; C183 VBUS reroute; C182 VBUS pour notch + C2-2 GND to via 42f6; U11-37 VIN_LOW; U8-2 GND via; R10 LDO_3V3; XTO template (U2-20 -> Y170-3). First run shorted a new C2-2 GND via onto a hidden VBUS via (143.85, 52.3): replaced by a track to the existing GND via, re-run clean. | 56 -> 37 |
| A2 | pour outlines: BAT_U4PIN_F (finger 0.6 mm on U4-22/23 only, lanes for U4-20/21/24), SYS_BOOST_F notch (U25-10), U25_SW_F top edge +0.08 (R252-1), PVDD_BOOST_F / _G (R250-2), PVDD_C271_F (R262-2), PACK_RAW_F (J5-2); BTST2 moved east | 37 -> 29 |
| A3 | BTST2 diagonal shifted further (U4-17 still 0.067 short in A2) | 29 -> 28 |

Fixed pads (28): U9-1/2/4, U15-2/4, U10-1, R120-2, R102-1, R18-1, U23-3, D5-2, U16-1, C206-1, C207-1, C182-1, C183-1, U11-37, U8-2, R10-2, U4-17/20/21/24, U25-10, R252-1, R250-2, R262-2, J5-2.

Design notes on the power edits:
- Hot loops: BTST2 (U4-19 -> C110-1) 3.08 -> 3.4 mm; U25 SW pour 0.08 mm smaller; U24 AVDD feed C216-1 -> via 4.1 -> 4.8 mm, all 0.5 mm.
- BAT_U4PIN_F: the pour now reaches U4-22/23 through a 0.6 x 1.7 mm finger (it was the whole east side). This is the same copper the pour would keep once PROG / CHG_INT / Q103-G are routed through it; check charge current against it (open problem 4).
- C2-2 (VBUS cap) GND via: was 922f at (140.9, 52.4), now a 0.4 mm track to the existing GND via 42f6 (140.7, 53.45), 0.7 mm edge to edge. No GND via fits east (VBUS via array).
- D6-7 (VBUS TVS pad) now ties to D6-2 directly; its old 50-deg track across D5-2 was deleted.
- Decoupling GND vias moved, all still within 1 mm of their pads: R18/C184 0.33 mm.
- New vias are 0.6/0.3, except neck vias 0.5/0.2 inside NECK areas.
- Widths kept from the replaced track, or wider (3V_AO diagonal 0.4 replaces 0.2 + 0.6).
- XTO template: U2-20 -> 0.6 mm stub -> 45 deg -> between Y170-1 and Y170-2 -> Y170-3, 0.25 mm, bend spacing >= 0.75 mm. It is a valid escape, but the straight-line probe still counts U2-20 (Y170-1 is 0.19 mm from a centred 1 mm stub at any offset that stays inside the pad). The H0 `--all-signals` strip would remove it; lock or exclude it.

## 3. Remaining 28 failing pads

| class | pads | why |
|---|---|---|
| pad-bound (needs placement) | U6-17 (C283-1), U7-8 (C294-1), U7-17 (C296-1), U20-2/4/7 (C124/C125), U24-4 (C212-1), U24-30 (C210-1), U25-2/3 (R252/U25-4), U25-13 (C314-2), U25-17 (C314-1), R140-2 (C141/C142/L2), U2-15 (C173-1 pad sits in front of the pin; the VCCP2I track is not the binding item), U2-20 (Y170-1 0.01), U11-36 (U11-34, footprint), J1-B5 (J1-B4A9 pad 0.005), Y200-1 (C226-2 on the centre line; an offset straight drop to C226-1 exists) | 18 pads |
| rule-bound | U4-18 (BATP needs 2.0 mm to BTST2 by `switch_critical`; U4-19 is a BTST2 pad 0.2 mm away) | 1 |
| copper-fixable, not done | U8-6/7 (3V3_AUDIO feed: on F.Cu every path from U8-8 to C238 crosses the 6/7 or 9/10 lanes because R226-1 sits 0.6 mm north; an under-body via to In2 collides with the In2 5V_CODEC track 38ad57ff), R110-2 (REGN arc; fix = 6 mm detour or REGN via move), R13-2 (VBUS_PD pour corner, VBUS_PD vias, 5V_LOGIC via fa30 + B.Cu track), U14-1 (SYS_RAW input via/tracks of the buck-boost hot loop), R152-1 (U15 SW pour, 1.0 mm rule), Q103-4 / R112-2 (BAT_INT vias and pour on all sides), R100-2 (+x needs a 0.8 x 1.0 mm notch in the SYS pour) | 9 |

So the copper-only floor is about 19. Reaching it would need the 9 copper edits above, several of which cut hot-loop or battery pours.

## 4. Task B: USB template (stage S1 copper)

Script `work-route/scripts/usb_template.py` (waypoints, exactness asserted). Nets /USB_DP, /USB_DN, Net-(U2-D+), Net-(U2-D-) complete.

- **J1:**
  - DP dives: B6 and A6 0.25/0.3 mm stubs to neck vias 0.5/0.2 at (148.23, 27.84) and (149.23, 27.35); B.Cu jumper (149.23, 27.35)-(148.74, 27.84)-(148.23, 27.84)-(148.23, 29.06); return via 0.6/0.3 at (148.23, 29.06).
  - DN joins A7 and B7 on F.Cu with a symmetric Y around the A6 via (stubs at x 148.705 / 149.755, junction (149.23, 28.095)).
  - All J1 exit stubs are 0.25 mm (A6 0.3), so every parallel DP/DN exit pair has a 0.225-0.25 mm gap. KiCad treats parallel stubs of the pair as coupled and flagged the 0.30 mm gap in B1/B2.
- **J1 -> D1:**
  - DN north at y 28.365, DP south at y 28.765 (0.15 mm gap), heading west.
  - DP taps D1-3 from the east (T at (146.6, 28.765)); DN drops through the middle of D1 at x 145.2 and taps D1-5 with a 0.6 mm stub.
  - The split around D1 raises no gap item: D1 pads lie between the split legs, so KiCad does not count them as coupled.
  - VBUS via d3c5 moved (146.58, 27.85) -> (146.58, 27.6), stub shortened, to make room for DN between it and D1.
- **Trunk:**
  - coupled pair (0.25/0.15) down x 144.28/144.68 (west of C5);
  - one 45-deg jog with a 0.566 mm offset of the diagonals (constant 0.15 mm gap);
  - down x 147.95/148.35;
  - DP enters R173-1 from the north-west, R173-1 -> R171-1 straight;
  - DN continues to R172-1 (3.6 mm uncoupled; R172 sits below R171).
- **U2:**
  - D+ R171-2 -> east -> 45 deg -> U2-1 from the **inner (body-side) end** (2.81 mm).
  - D- R172-2 -> south -> 45-deg U under the pin row (y 64.445) -> U2-2 from outside (4.25 mm).
  - Deviation from "U-turn under U2" for D+: a U-turn needs >= 1.81 mm of lateral room at 0.75 mm bend spacing. Only 1.16 mm exists between R172 (east edge 149.22 + 0.275) and U2-1. So D+ uses the inner end (FO1 waived here; coordinator decision).
- **Numbers:**

| item | value |
|---|---|
| routed length | /USB_DP 40.18 mm (3 vias, B.Cu 2.43 mm), /USB_DN 44.01 mm, U2-D+ 2.81, U2-D- 4.25, XTO 4.88 |
| coupled run | 32.8 mm at gap 0.15 (r7 parallel report) |
| KiCad skew and uncoupled rules | pass. Skew is within 3.5 mm with via heights; plain track length difference 3.8 mm, of which DN carries both J1 branches and the R171/R172 offset |
| octilinear ratio | DP 1.115, DN 1.089, U2-D- 1.65 (U shape), U2-D+ 0.96 |
| B.Cu over In2 | B.Cu is only the DP jumper. Over In2 GND 0.64 mm; over "void" 1.79 mm, which is the antipads of its own 3 vias; 0 mm over any In2 island |
| GND vias added for the return current | (149.3, 29.4) and (149.95, 28.55): 1.12 / 1.40 mm from the jumper. Nearest GND via per DP via: 1.4 / 1.9 / 1.1 mm (B6 via 1.9 > 1.5) |
| halo | parallel run within 0.6 mm of any other signal: 0.0 mm |
| pad exits | all >= 0.3 mm straight |
| widths | 0.2 mm nowhere (all USB copper >= 0.25), so neck areas are not used |

- **Exceptions:**
  - T-junctions (3): DN Y at J1, DN tap D1-5, DP tap D1-3.
  - Bend spacing below 0.75 mm (all at J1/D1, 0.5 mm-pitch geometry makes 0.75 impossible there):
    - DN junction -> first bend 0.38 mm;
    - DN D1 entry diagonal 0.59 mm;
    - DP return-via exit diagonal 0.42 mm;
    - J1 Y branches 0.74 mm.
  - One 90-deg corner on B.Cu at the B6 via (inside the via).

## 5. Iterations (AG13) and log

- Task A: 3 iterations (A1-A3).
- Task B: 4 builds to reach DRC 0.
  - B1: annular ring of the 0.45/0.2 vias, and gap 0.30 at the J1 stubs.
  - B2: gap 0.275 between a DP stub and the narrowed part of a DN stub.
  - B3: D1-3 clearance 0.147.
  - B4: DRC 0.
- Then one clean-up build (B5/B6): the D- bend 0.7495 -> 0.764 mm, a second return GND via, and removal of the 0.05 mm LDO_3V3 overlap segment cddb4150 left by the A1 R10 fix.
- This is one build over the AG13 limit; disclosed here.
- All boards, edit logs (`*.edit.json`), DRC, probe and dumps are in `work-route/`.

## 6. Open problems

1. **Probe target missed:** 28 failing pads, floor about 19 without placement changes. To go lower:
   - placement or footprint moves: C124/C125, C173, C283/C294/C296, C210/C212, R252, C314, R226 (U8-6/7), Y170, C226;
   - the 9 copper edits listed in section 3.
2. **USB D+ inner entry at U2-1** (under the SSOP body) instead of the requested U-turn. Accept it, or move R172 west by about 0.7 mm (placement) to allow an outer U-turn.
3. **J1 CC lines.**
   - CC2 (B5) and CC1 (A5) escapes now run within the 0.6 mm USB halo just below the pins.
   - Both must take a B.Cu hop right at J1 in S3. CC1 has 0.27 mm to the new GND via (149.95, 28.55).
   - J1-B5 was already pad-bound.
4. **BAT_U4PIN_F** is now a 0.6 mm finger into U4-22/23: confirm the charge current; widen by moving U4-20/21/24 escapes to vias if needed.
5. **Teardrops:** 51 teardrop zones next to edited copper were removed (A1 39, A2 9, A3 0, B6 3). Regenerate them after routing.
6. **XTO template** (U2-20 -> Y170-3) and the USB copper must be excluded from the H0 `--all-signals` strip, or locked as S1 copper, before the router runs.
7. **Return vias:** the per-via GND distance for the B6 jumper via is 1.9 mm (> 1.5 mm); no legal spot closer (CC2 lane, A8, VBUS via).

## 7. Files (`ai-files/pcb/work-route/`)

- **Boards:**
  - `RT-0.*` (copy of R10-0) and `RT-1.kicad_pcb/.kicad_pro/.kicad_dru` (result);
  - intermediates `A1-A3`, `B1-B6` (`*-raw` = before refill);
  - plans `planA1-3.json`, `planB*.json`, `planC1.json`.
- **Gates:**
  - `RT-1.drc.json`, `RT-1.gates.json` (pad nets, lock manifest, exactness, joints), `RT-1.check.json` / `.log` (route_oct_check, USB + XTO);
  - `RT-0.r7.json` / `RT-1.r7.json`;
  - `RT-1.sentinel.log` with `sentinel/`;
  - `RT-0.allexits.txt` / `A*.allexits.txt` / `RT-1.allexits.txt` (probe), `RT-0.detail.txt` (per-direction blockers).
- **Scripts (`scripts/`):** `pcbtext.py`, `edit.py`, `cycle.sh`, `probe.py`, `win.py`, `usb_template.py`, `gates.py`, `uncdiff.py`, `drcsum.py`.
- **Evidence:** `evidence/rt1-usb-j1-d1.png`, `evidence/rt1-usb-u2.png`, `evidence/rt1-u4.png`.
- About 190 MB of scratch; commit only the scripts, RT-1 and this report if wanted.

## 8. Edit log (net, layer, coordinates)

### A1 (planA1.json on RT-0.kicad_pcb; 39 teardrop zones removed)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| seg del 6b717085 | GND | F.Cu | 0.3 | (194.795, 65.0275)-(193.995, 65.0275) |
| seg del d4023062 | GND | F.Cu | 0.3 | (194.795, 65.5275)-(193.995, 65.0275) |
| seg del b1531a8a | GND | F.Cu | 0.3 | (184.708, 51.84)-(182.802, 52.6293) |
| seg del 841ba753 | GND | F.Cu | 0.3 | (153.719, 33.5)-(154.667, 31.855) |
| seg del 6519d685 | GND | F.Cu | 0.3 | (149.38, 32.855)-(152.3, 33.5) |
| seg del 20f7c49c | GND | F.Cu | 0.3 | (152.3, 33.5)-(153.719, 33.5) |
| seg del 950d5022 | /3V_AO | F.Cu | 0.2 | (108.064, 73.0347)-(106.55, 72.6) |
| seg del b1b83b19 | /3V_AO | F.Cu | 0.6 | (108.91, 73.2775)-(108.064, 73.0347) |
| seg del 98617e08 | Net-(U24-AVDD) | F.Cu | 0.5 | (154.96, 75.2)-(153.5, 77.7) |
| seg del 90035776 | Net-(U24-AVDD) | F.Cu | 0.5 | (153.5, 77.7)-(152.45, 78.3) |
| seg del c48324b8 | /USB_VBUS | F.Cu | 0.6 | (137.2, 52)-(136.6, 51.4) |
| seg del 634fcc95 | GND | F.Cu | 0.4 | (142.3, 52.362)-(140.9, 52.4) |
| seg del 7facaf33 | GND | F.Cu | 0.3 | (172.29, 68.9)-(171.85, 69.65) |
| seg del f257ff77 | /USB_PD/LDO_3V3 | F.Cu | 0.4 | (137.276, 61.0228)-(136.266, 59.55) |
| seg del 578447c8 | /USB_PD/LDO_3V3 | F.Cu | 0.6 | (137.722, 61.6)-(137.276, 61.1539) |
| seg del 3a1c032b | /USB_PD/LDO_3V3 | F.Cu | 0.6 | (137.276, 61.1539)-(137.276, 61.0228) |
| seg set caee2f4e | GND | F.Cu | 0.3 | (181.99, 68.59)-(182.7, 68.7) -> (181.99, 68.59)-(182.62, 68.59) |
| seg set dd9138b7 | GND | F.Cu | 0.25 | (184.295, 67.388)-(184.3, 68.55) -> (184.295, 67.388)-(184.295, 69.55) |
| seg set 741ac858 | GND | F.Cu | 0.3 | (116.165, 36.565)-(115.165, 36.565) -> (116.165, 36.565)-(114.65, 36.565) |
| seg set fd4b7335 | GND | F.Cu | 0.3 | (196.295, 65.2775)-(193.545, 65.2775) -> (196.295, 65.2775)-(194.545, 65.2775) |
| seg set 3a36dea9 | GND | F.Cu | 0.3 | (106.31, 75.1775)-(105.31, 75.1775) -> (106.31, 75.21)-(105.31, 75.21) |
| seg set da259741 | GND | F.Cu | 0.3 | (159.9, 123.337)-(159.9, 124.25) -> (159.9, 123.338)-(159.9, 124.35) |
| seg set ed1da618 | GND | F.Cu | 0.6 | (134.45, 49.45)-(134.463, 50.9) -> (134.463, 49.55)-(134.463, 50.9) |
| seg set 14b98ab1 | GND | F.Cu | 0.3 | (172.29, 68)-(172.29, 68.9) -> (172.295, 68)-(172.295, 69.7) |
| seg set b957bc6a | /3V_AO | F.Cu | 0.3 | (106.55, 72.6)-(105.3, 72.6) -> (108.233, 72.6)-(105.3, 72.6) |
| seg set a1d4ee01 | /USB_VBUS | F.Cu | 0.6 | (137.2, 53.875)-(137.2, 53.275) -> (137.2, 53.875)-(137.2, 53.55) |
| seg set f1a862c9 | /USB_VBUS | F.Cu | 0.3 | (137.2, 53.275)-(137.2, 52) -> (137.2, 53.55)-(136.5, 52.85) |
| seg set 8fdd8f79 | /USB_PD/VIN_LOW | F.Cu | 0.3 | (133.7, 52.15)-(135, 53.45) -> (133.7, 52.15)-(134.7, 53.15) |
| seg set 14a1281b | /USB_PD/LDO_3V3 | F.Cu | 0.3 | (136.266, 59.55)-(135.3, 59.55) -> (137.273, 59.55)-(135.3, 59.55) |
| seg add | GND | F.Cu | 0.3 | (194.545, 65.2775)-(193.545, 65.2775) |
| seg add | GND | F.Cu | 0.3 | (194.795, 65.0275)-(194.545, 65.2775) |
| seg add | GND | F.Cu | 0.3 | (194.795, 65.5275)-(194.545, 65.2775) |
| seg add | GND | F.Cu | 0.3 | (184.708, 51.95)-(182.8, 51.95) |
| seg add | GND | F.Cu | 0.3 | (182.8, 51.95)-(182.2, 52.55) |
| seg add | GND | F.Cu | 0.3 | (154.95, 31.855)-(154.95, 33.1) |
| seg add | GND | F.Cu | 0.3 | (154.95, 33.1)-(154.2, 33.85) |
| seg add | GND | F.Cu | 0.3 | (149.38, 32.855)-(149.38, 33.83) |
| seg add | /3V_AO | F.Cu | 0.4 | (108.91, 73.2775)-(108.233, 72.6) |
| seg add | Net-(U24-AVDD) | F.Cu | 0.5 | (154.963, 75.2)-(153.85, 75.2) |
| seg add | Net-(U24-AVDD) | F.Cu | 0.5 | (153.85, 75.2)-(153.15, 75.9) |
| seg add | Net-(U24-AVDD) | F.Cu | 0.5 | (153.15, 75.9)-(153.15, 77.6) |
| seg add | Net-(U24-AVDD) | F.Cu | 0.5 | (153.15, 77.6)-(152.45, 78.3) |
| seg add | /USB_VBUS | F.Cu | 0.4 | (136.5, 52.85)-(136.5, 51.4) |
| seg add | /USB_PD/VIN_LOW | F.Cu | 0.2 | (134.7, 53.15)-(135, 53.45) |
| seg add | /USB_PD/LDO_3V3 | F.Cu | 0.4 | (137.722, 61.6)-(137.722, 60) |
| seg add | /USB_PD/LDO_3V3 | F.Cu | 0.4 | (137.722, 60)-(137.273, 59.55) |
| seg add | Net-(U2-XTO) | F.Cu | 0.25 | (155.865, 55.655)-(155.865, 54.05) |
| seg add | Net-(U2-XTO) | F.Cu | 0.25 | (155.865, 54.05)-(156.4, 53.515) |
| seg add | Net-(U2-XTO) | F.Cu | 0.25 | (156.4, 53.515)-(156.4, 51.7) |
| seg add | Net-(U2-XTO) | F.Cu | 0.25 | (156.4, 51.7)-(156.9, 51.2) |
| seg add | GND | F.Cu | 0.4 | (142.3, 52.362)-(141.788, 52.362) |
| seg add | GND | F.Cu | 0.4 | (141.788, 52.362)-(140.7, 53.45) |
| via del 26c943a7 | GND | F-B | 0.5/0.2 | (184.3, 68.55) |
| via del f383c299 | GND | F-B | 0.5/0.2 | (193.995, 65.0275) |
| via del 7a06e34b | GND | F-B | 0.6/0.3 | (182.802, 52.6293) |
| via del 922f27d9 | GND | F-B | 0.6/0.3 | (140.9, 52.4) |
| via move dfa04d4b | GND | F-B | - | (182.7, 68.7) -> (182.62, 68.59) |
| via move 91f752a0 | GND | F-B | - | (115.165, 36.565) -> (114.65, 36.565) |
| via move 6c51a9fb | GND | F-B | - | (105.31, 75.1775) -> (105.31, 75.21) |
| via move 99689be8 | GND | F-B | - | (159.9, 124.25) -> (159.9, 124.35) |
| via move c9b9d0a0 | GND | F-B | - | (134.45, 49.45) -> (134.463, 49.55) |
| via move b7ef195d | GND | F-B | - | (171.849, 69.649) -> (172.295, 69.7) |
| via add | GND | F-B | 0.6/0.3 | (184.295, 69.55) |
| via add | GND | F-B | 0.6/0.3 | (182.2, 52.55) |
| zone outline USB_VBUS_U11_F | /USB_VBUS | F.Cu | - | 201730fa: 4 -> 8 vertices |

### A2 (planA2.json on A1.kicad_pcb; 9 teardrop zones removed)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| seg set 7f90c54d | /Battery_Charger/BTST2 | F.Cu | 0.2 | (153.43, 122.585)-(153.902, 122.585) -> (153.43, 122.585)-(154.4, 122.585) |
| seg set cca0b769 | /Battery_Charger/BTST2 | F.Cu | 0.2 | (153.902, 122.585)-(155.75, 124.433) -> (154.4, 122.585)-(156, 124.185) |
| zone outline BAT_U4PIN_F | /Battery_Charger/BAT_INT | F.Cu | - | 019a336f: 10 -> 11 vertices |
| zone outline SYS_BOOST_F | /SYS_RAW | F.Cu | - | eb2fa469: 14 -> 18 vertices |
| zone outline U25_SW_F | Net-(U25-SW) | F.Cu | - | 9e28bc9d: 4 -> 4 vertices |
| zone outline PVDD_BOOST_F | /Amplifiers/PVDD_AMP | F.Cu | - | 81657627: 12 -> 12 vertices |
| zone outline PVDD_BOOST_F_G | /Amplifiers/PVDD_AMP | F.Cu | - | b413116f: 137 -> 136 vertices |
| zone outline PVDD_C271_F | /Amplifiers/PVDD_AMP | F.Cu | - | d8953839: 22 -> 23 vertices |
| zone outline PACK_RAW_F | /Battery_Charger/PACK_RAW | F.Cu | - | 03f4b94c: 102 -> 102 vertices |

### A3 (planA3.json on A2.kicad_pcb; 0 teardrop zones removed)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| seg set 7f90c54d | /Battery_Charger/BTST2 | F.Cu | 0.2 | (153.43, 122.585)-(154.4, 122.585) -> (153.43, 122.585)-(154.55, 122.585) |
| seg set cca0b769 | /Battery_Charger/BTST2 | F.Cu | 0.2 | (154.4, 122.585)-(156, 124.185) -> (154.55, 122.585)-(155.95, 123.985) |
| seg add | /Battery_Charger/BTST2 | F.Cu | 0.2 | (155.95, 123.985)-(155.95, 124.3) |

### B6 (planB6.json on A3.kicad_pcb; 3 teardrop zones removed)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| seg del cddb4150 | /USB_PD/LDO_3V3 | F.Cu | 0.4 | (137.722, 61.55)-(137.722, 61.6) |
| seg set 02a1aa4a | /USB_VBUS | F.Cu | 0.5 | (146.58, 26.8)-(146.58, 27.85) -> (146.58, 26.8)-(146.58, 27.6) |
| seg add | /USB_DP | F.Cu | 0.25 | (148.23, 26.355)-(148.23, 27.84) |
| seg add | /USB_DP | F.Cu | 0.3 | (149.23, 26.355)-(149.23, 27.35) |
| seg add | /USB_DP | B.Cu | 0.25 | (149.23, 27.35)-(148.74, 27.84) |
| seg add | /USB_DP | B.Cu | 0.25 | (148.74, 27.84)-(148.23, 27.84) |
| seg add | /USB_DP | B.Cu | 0.25 | (148.23, 27.84)-(148.23, 29.06) |
| seg add | /USB_DN | F.Cu | 0.25 | (148.705, 26.355)-(148.705, 27.57) |
| seg add | /USB_DN | F.Cu | 0.25 | (148.705, 27.57)-(149.23, 28.095) |
| seg add | /USB_DN | F.Cu | 0.25 | (149.755, 26.355)-(149.755, 27.57) |
| seg add | /USB_DN | F.Cu | 0.25 | (149.755, 27.57)-(149.23, 28.095) |
| seg add | /USB_DN | F.Cu | 0.25 | (149.23, 28.095)-(148.96, 28.365) |
| seg add | /USB_DN | F.Cu | 0.25 | (148.96, 28.365)-(145.62, 28.365) |
| seg add | /USB_DN | F.Cu | 0.25 | (145.62, 28.365)-(145.2, 28.785) |
| seg add | /USB_DN | F.Cu | 0.25 | (145.2, 28.785)-(145.2, 29.84) |
| seg add | /USB_DN | F.Cu | 0.25 | (145.2, 29.84)-(144.6, 29.84) |
| seg add | /USB_DN | F.Cu | 0.25 | (145.2, 29.84)-(145.2, 31) |
| seg add | /USB_DN | F.Cu | 0.25 | (145.2, 31)-(144.28, 31.92) |
| seg add | /USB_DN | F.Cu | 0.25 | (144.28, 31.92)-(144.28, 39) |
| seg add | /USB_DN | F.Cu | 0.25 | (144.28, 39)-(147.95, 42.67) |
| seg add | /USB_DN | F.Cu | 0.25 | (147.95, 42.67)-(147.95, 61) |
| seg add | /USB_DN | F.Cu | 0.25 | (147.95, 61)-(148.7, 61.75) |
| seg add | /USB_DP | F.Cu | 0.25 | (148.23, 29.06)-(147.935, 28.765) |
| seg add | /USB_DP | F.Cu | 0.25 | (147.935, 28.765)-(146.6, 28.765) |
| seg add | /USB_DP | F.Cu | 0.25 | (146.6, 28.765)-(146, 28.765) |
| seg add | /USB_DP | F.Cu | 0.25 | (146.6, 28.765)-(146.6, 30.1657) |
| seg add | /USB_DP | F.Cu | 0.25 | (146.6, 30.1657)-(144.68, 32.0857) |
| seg add | /USB_DP | F.Cu | 0.25 | (144.68, 32.0857)-(144.68, 38.8343) |
| seg add | /USB_DP | F.Cu | 0.25 | (144.68, 38.8343)-(148.35, 42.5043) |
| seg add | /USB_DP | F.Cu | 0.25 | (148.35, 42.5043)-(148.35, 57.43) |
| seg add | /USB_DP | F.Cu | 0.25 | (148.35, 57.43)-(148.8, 57.88) |
| seg add | /USB_DP | F.Cu | 0.25 | (149.05, 57.83)-(149.05, 59.1325) |
| seg add | Net-(U2-D+) | F.Cu | 0.25 | (149.05, 60.3275)-(149.855, 60.3275) |
| seg add | Net-(U2-D+) | F.Cu | 0.25 | (149.855, 60.3275)-(150.655, 61.1275) |
| seg add | Net-(U2-D+) | F.Cu | 0.25 | (150.655, 61.1275)-(150.655, 62) |
| seg add | Net-(U2-D-) | F.Cu | 0.25 | (148.9, 62.9775)-(148.9, 63.67) |
| seg add | Net-(U2-D-) | F.Cu | 0.25 | (148.9, 63.67)-(149.675, 64.445) |
| seg add | Net-(U2-D-) | F.Cu | 0.25 | (149.675, 64.445)-(150.765, 64.445) |
| seg add | Net-(U2-D-) | F.Cu | 0.25 | (150.765, 64.445)-(151.305, 63.905) |
| seg add | Net-(U2-D-) | F.Cu | 0.25 | (151.305, 63.905)-(151.305, 63.3) |
| via move d3c5ebf1 | /USB_VBUS | F-B | - | (146.58, 27.85) -> (146.58, 27.6) |
| via add | /USB_DP | F-B | 0.5/0.2 | (148.23, 27.84) |
| via add | /USB_DP | F-B | 0.5/0.2 | (149.23, 27.35) |
| via add | /USB_DP | F-B | 0.6/0.3 | (148.23, 29.06) |
| via add | GND | F-B | 0.6/0.3 | (149.3, 29.4) |
| via add | GND | F-B | 0.6/0.3 | (149.95, 28.55) |
