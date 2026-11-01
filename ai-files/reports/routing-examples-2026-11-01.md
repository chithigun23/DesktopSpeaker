# Routing examples and benchmark boards (2026-11-01)

Gathered by a research agent; geometry numbers computed by the coordinator with `ai-files/helpers/r7_bench.py` (parse only, nothing executed from the repos). Quality of these boards is judged by author reputation and this geometry check, not by visual review. Original files were downloaded to the session scratchpad and are not stored in the repository.

| Board | Layers | Licence | Length exactly on 0/45/90 | Signal length / octilinear minimum |
|---|---|---|---|---|
| RainbowLabsDE/USB2Speakon (USB-audio class-D amp, 15x26 mm) | 4 | CERN-OHL-W-2.0 | 100% | 1.50 (tiny board) |
| Jana-Marie/analog-toolkit (STM32G431 + USB-C PD sink) | 4 | CERN-OHL-S-2.0 | 100% | 1.11 |
| mikesmitty/power-manifold charger-module (TPS55288 buck-boost, USB-C PD, STM32G071) | 4 | CERN-OHL-P-2.0 | 100% | 0.99 |
| LibreSolar/bms-c1 | 4 | CERN-OHL-W-2.0 | 100% | 0.88 |
| YC-Lammy/IP5328P powerbank | 2 | GPL-3.0 | 100% | 1.32 |
| LibreSolar/mppt-2420-hc (KiCad 5 format) | 4 | CERN-OHL-W-2.0 | 99.5% | not computed |
| DesktopSpeaker R6q | 4 | n/a | 38.5% | 1.24 |

Manufacturer layout sources read (text only, no layout images seen): TI BQ25792/98 EVM guide SLUUCB5E s3; BQ25798 datasheet 8.4.1; TAS5825M datasheet 10.4; SLYT614 (step-down five steps, best statement of routing order); TPS63802 s12; TPA6132A2 s10; TPS61088 layout guidelines (Q1 variant); BM83 datasheet s7 (search excerpts only). Not verified: TPS25730EVM, TPS61088EVM, TPA6132A2EVM, PCM1862EVM, BM83 EVB, ST Nucleo layouts.

Routing order distilled (manufacturer + opinion): switcher input cap, inductor and SW node, output cap, small-signal parts, digital pins, single-point ground join; BQ25792 EVM priority: 0.1 uF PMID/SYS caps on the IC layer with no vias, bulk caps, REGN/BTST, VBUS/BAT HF caps (>= 2 vias per terminal if vias are needed), bulk, inductor close to SW; after power loops: sensitive audio/analog, USB pair, clocks, general digital, pours. Altium simulation: 90-degree turn, two 45s and an arc differ very little in return loss, so angle is a manufacturing and neatness choice.
