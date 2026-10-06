# PCB placement v9 (2026-10-06)

Pipeline: `helpers/build_pcb_v9.sh` (build_pcb_v9.py), floorplan `pcb/floorplan-v9.json` (from `fp_sp_v9.py` / `fp_spec_v9.py`, chosen raw `floorplan-v9-raw2_9.json`, 8 seeds x 1.2 M iterations), logo footprint from `helpers/make_logo_fp.py`. Render `pcb/layout-v9-top.png`, `pcb/layout-3d-bottom.png`.

## Added
- **SW102 EC11E volume encoder** (Alps EC11E, vertical, H20 mm, with mounting-tab pads on GND) in its own "Volume Encoder" tile, nets ENC_A/ENC_B/ENC_SW on PC8/PC9/PC10, 10 nF debounce C308-C310. Shaft pokes up through the lid (20 mm shaft: check lid height and knob choice; a bushing/panel nut is not modelled). No STEP model for the footprint (CAD uses a parametric stand-in).
- **25 test points**: TP1-TP22 Keystone 5015 SMD loops (scope hook or multimeter probe), TP23-TP25 Keystone 5010 THT loops for GND (scope ground clip). Each has its net name in 0.7 mm silk beside it (TP ref moved to F.Fab). Placed >= 5 mm from the net's IC pin so decap space stays free; I2S, I2C, NRST, BT UART, rails (VBUS, SYS_RAW, BAT_PACK, 3V_AO, LDO_3V3, 3V3_AUDIO, 5V_LOGIC, 5V_CODEC, 3V8_BT, PVDD_AMP, REGN).
- **Silkscreen**: every section rectangle is closed (edges that lie on the board edge use the border), facing edges < 2 mm apart merged (title-carrying edge wins), thin rounded border 0.45 mm inside the board edge, titles Title Case at 1.4 mm with a gap to the lines (shrunk if wider than the tile), "Jacks" -> "Audio Connectors", "Boost" -> "Boost Converter", thick (0.4 mm) square round every mounting hole, standard-thickness rectangle round SW101, Bluetooth title moved below the module with a rune logo, SWD pin names (SWDIO/SWCLK/NRST/GND), J9/J10/J11 labelled "Front Left / Front Right / Woofer" with +/-, USB TVS D1/D5/D6 directly behind J1, "Desktop Speaker Rev A" + "CG + Sonnet V1.0" on the front, and on the back the Orwellian Industries logo (57 x 63 mm, about 24% of the board area, bottom right as seen from the back, reads correctly in the 3D bottom render) plus the board name/version.

## Result
- Board 130.5 x 127.8 mm (16,678 mm², was 15,428): the encoder tile, 25 test points and their labels enlarged several sections; floorplan re-annealed. 11 mounting holes (NH 9 + inductor-row holes).
- DRC: no courtyard/overlap/outline/shorting findings; remaining items are the SW100 NPTH clearance (0.175 mm) and the TPS25730D 0.2 mm thermal via drills (JLC minimum 0.3 mm, change the footprint vias or choose JLC's 0.2 mm option), plus silk warnings (silk over pads/text, mostly test point labels and the mounting hole squares).
- CAD rebuilt with an EC11E stand-in, 0 unintended overlaps (harness route follows the new board edge), woofer chamber 0.525 L unchanged.

## Known items
- Logo silk crosses two mounting-hole pads on the back (cosmetic; silk is clipped at the pad openings). Move the holes or the logo if you want it clean.
- A few TP labels cross a section line (no free spot inside the tile); J9 label shares space with a capacitor reference.
- Some section edges still step by about 1.8 mm where a title strip prevents merging (PDIN/SWG vs JACKS/MUX).
- BOM xlsx not regenerated (CSV has SW102, C308-C310 and a TP line, all unverified, no LCSC codes).
- Decap distances are unchanged from v8 by the checker (U6 PVDD bulk 0805 6.5 mm, U25 bulk 8.5 mm, 0402 HF caps close).

## v9b: mounting hole moves (user request)
- Encoder support: the middle hole of the three left of the encoder (H5) now sits directly under H6, so two holes bracket the encoder's right side (the encoder is a push switch: support against the press force). The encoder's left side keeps H4.
- Woofer inductor row: one hole inline between L205 and L206 (AMP7 cell hole, same mechanism as the front amp row).
- Hole between the Front Amp and Woofer Amp sections, just below the inductor row, between U6 and U7 (7.8 mm gap column inserted).
- The two bottom-right holes (H7/H8) are removed (replaced by the two above). Hole count unchanged (10).
- Cost: the board is 136.9 x 127.8 mm (17,497 mm²; +6.4 mm width: gap column plus the wider woofer amp); the right column (Battery, BT Supply, ADC, USB Audio Codec) shifted right with void left of it.
- CAD: PCB re-centred in the enclosure (pcb_cx -3.5), harness route follows the board edge, 0 unintended overlaps.
