# Routing review of board R6q (coordinator, 2026-11-01)

Independent review of `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb` at commit 2858f93 against vendor layout guidance and general practice. Published as an artifact page "Routing Review R6q". Method: own scripts parse the `.kicad_pcb` directly (`ai-files/helpers/r7_metrics.py`), KiCad 10.0.7 DRC re-run (0 violations, 0 unconnected, 0 parity; a sentinel rule proved the custom rules are active). No simulation or measurement. Baseline numbers: `ai-files/reports/r7-baseline-metrics.json`.

Stack-up: F.Cu / 0.2104 / In1 (GND, one piece 16,569 mm2) / 1.065 / In2 (power islands + GND pieces + signals, 122 pieces) / 0.2104 / B.Cu (GND pour + signals). A B.Cu trace returns through In2, not In1 (about 1.3 mm away).

## What is good (do not break)
- All 17 ICs measured: HF decoupling cap 1.1-3 mm from the pin; BQ25792 follows TI placement order.
- Power paths sized (R6k/R6l reviews). In1 solid ground: 94% of F.Cu signal length over it.
- I2S/analog audio vias have GND vias within 2.2 mm (I2S) and 1.0 mm (BT_AUDIO, USB_AUDIO).
- USB pair coupled 34 mm at 0.15 mm gap. BM83 antenna keep-out empty, B.Cu under module solid GND.

## Findings (baseline numbers)
- **R1 any-angle geometry.** Of 4,702 mm in segments >= 5 mm: 1,964 exactly on 0/45/90 deg, 1,080 within 0.6-5 deg, 931 at 5-15 deg, 727 at 15-22.5 deg. 36 joints < 80 deg, 7 < 30 deg (In2 3V3_AUDIO 9 deg at (174.2,59.1); In2 BAT_PACK 14 deg at (104.156,89.3), 27 deg at (104.0,89.15); F.Cu 5V_LOGIC 16 deg at (184.708,50.89); F.Cu GND 24 deg at (136.435,56.875); F.Cu 5V_CODEC 27 deg (163.245,88.918); In2 3V_AO 27 deg (178.4,93.3); F.Cu 5V_LOGIC 29 deg (94.907,104.97)).
- **R2 B.Cu return path.** B.Cu signal 2,338 mm: 1,018 over In2 GND, 656 over non-GND islands, 664 over no In2 copper. Sensitive nets on B.Cu (GND / island / void mm): AUD_SDA 27.8/62.4/16.7, AUD_SCL 26.4/9.0/23.4, I2S_SDATA 17.2/9.1/14.2, I2S_LRCK 0.4/1.6/4.5, I2S_BCK 0.5/0/1.9, BT_AUDIO_L 10.9/0/4.6, BT_AUDIO_R 3.8/0/4.3, HP_OUTL 11.5/0/5.8, VMID_HP 14.1/0/2.0, USB_AUDIO_L 0/0/3.2, USB_AUDIO_R 6.3/0/5.4.
- **R3 I2S spacing.** F.Cu near-parallel (gap <= 0.30 mm): I2S_BCK|I2S_LRCK 85.9 mm, I2S_BCK|I2S_SDATA 61.8 mm, min gap 0.20 mm. Prepreg height 0.21 mm. `clk_clear` excludes I2S_CLK from itself so DRC allows it. USB DN|DP 34 mm at >= 0.15 mm is a proper pair.
- **R4 rules.** 26 custom rules; `neck_ic` (after the class rules) resets min width/clearance to 0.2 mm inside IC courtyards and 17 `NECK_` areas; `in2_power_only` whitelist; `usb_fs_waiver`; five checks ignored. Missing: I2S-to-I2S spacing, analog/SW clearance inside NECK areas, B.Cu rules for clock/analog nets.
- **R5 placement-driven length.** 30 nets > 100 mm; ENC_SW 194 mm vs 62 mm MST; routed signal 6,731 mm vs MST 5,316 mm (1.27x). Not fixed in R7 except small moves.
- **R6 3V3_AUDIO.** 298 mm of track, 3 layers, 20 vias, 28 pads; 43% under 0.5 mm wide (0.3 mm: 62 mm). Loads: U6, U7 (TAS5825M), U24 ADC, U10 TPA6132A2, U22, U8, U9, FB200, R209/R210/R232/R239/R262, TP6.
- **R7 control pins near switch nodes.** ILIM_HIZ 0.61 mm from SW2 (F.Cu), 1.15 mm (B.Cu); TPS63802 FB 1.08/1.10 mm from L2; TS_SENSE 1.7 mm from SW2.
- **R8 BM83.** 14.9 mm of F.Cu track inside the module pad rectangle (BT_RXD_M 10.6, GND 2.3, SYS_PWR 2.0). Datasheet: no top-layer routing under the module for the certified layout; check the BM83 figure before moving.
- **R9 known/accepted** (not in scope): 3 via-in-pad plus 22 near-pad vias, 100% paste over 16 open thermal vias on U6/U7, PGND pin 27 on two vias, USB waiver.

## User decisions for R7 (2026-11-01)
Scope: targeted fixes (R1 sharpest joints, R2, R3, R6, R7, R8, rules R4). Layer roles: keep (In1 GND, In2 islands). Placement: small moves allowed for passives/test points where it clearly helps; large blocks stay; every move recorded.
