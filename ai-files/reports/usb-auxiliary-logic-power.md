# Independent USB auxiliary logic power — architecture review

2026-10-05; candidate direction, no active connection changes.

## Need

The replacement BQ25792 converter is held off by ILIM_HIZ until a controller sets source-appropriate limits. U12 currently takes SYS_RAW, so with an absent/disconnected battery it cannot boot that controller. Retain U19 on raw USB as USB_AUX_5V and feed the always-on logic regulator from either that auxiliary output or SYS_RAW, with reverse blocking. Do not feed the codec or amplifier from this auxiliary path.

## Preferred candidate

TPS2116DRLR priority power mux: IN1 = USB_AUX_5V, IN2 = SYS_RAW, OUT = U12 input. MODE = IN1. PR1 divider selects a USB-valid threshold around 2.8 V (candidate 180 kΩ / 100 kΩ), pending leakage/weak-source analysis. The reference is 0.92–1.08 V; including opposing 1% resistor tolerances gives about2.54–3.06 V before pin leakage. This keeps priority selection below the expected auxiliary output at a valid3.6V charger input. Auxiliary USB remains preferred even if SYS is also present. Its input range is 1.6–5.5 V, so both candidate inputs fit the intended low-voltage domain; verify actual transient maxima. 2.5 A capability exceeds the small logic load, but use it only for logic. Reverse current blocking prevents AUX feeding SYS or SYS backfeeding the USB LDO.

Primary datasheet Rev A electrical table gives 1.35 µA typical IN2 current when IN2 powers OUT and IN2 > IN1 + 0.2 V; maximum 3.7 µA through85°C /4.5µA through105°C in that condition. Include this in battery-enabled standby, not a measured board budget. In ship mode SYS is disconnected, so this mux does not itself bypass the ship FET or physical pack switch. USB-present electronic off still requires MCU sleep and all audio/BT rails disabled.

Two LM66100 devices were compared (150 nA typical each). Their simplest dual OR wiring can turn both off when inputs stay equal; TI supplies a more elaborate continuous-output arrangement. TPS2116 has a clearer single-chip priority/switchover policy, at the expense of roughly another microamp in battery operation. Plain Schottky OR would consume less control current but sacrifices low-battery dropout headroom and can have material reverse leakage over temperature.

## Before capture

Select exact LCSC part/stock, pin mapping, DRL footprint/model; verify PR1 threshold including reference/resistor/leakage; include local bypass and output capacitance; examine switchover dip versus MCU brownout and U12 dropout. Confirm startup auxiliary budget includes PD, charger qualification, MCU and pull-ups. USB attach and suspend budgets remain system-level requirements.

## Sources

- TI TPS2116 datasheet Rev A: https://www.ti.com/lit/ds/symlink/tps2116.pdf (local ai-files/datasheets/TPS2116.pdf).
- TI LM66100 datasheet: https://www.ti.com/lit/ds/symlink/lm66100.pdf (local ai-files/datasheets/LM66100.pdf).

No change to current BOM or active fuel-gauge child yet.

## TPS2116DRLR library and sourcing review

Candidate library assets are staged under `ai-files/candidates/` and remain unregistered: `TPS2116DRLR.kicad_sym`, `TPS2116DRLR.kicad_mod`, and `TPS2116DRLR.step`. The symbol uses the datasheet's full DRL0008A eight-pin map. VOUT is a native common pin stack `[2,7]`; VIN1=3, PR1=4, MODE=5, VIN2=6, ST=8, and GND=1 remain separate. MODE5 is placed at the top of the symbol for a direct short tie to VIN1; reference and value are centered below the body. KiCad 10.0.6 CLI symbol SVG export passes. The symbol/footprint library IDs target the project's `DesktopSpeaker:TPS2116DRLR` namespace, with a project-relative 3D link `${KIPRJMOD}/kicad-library/3d/TPS2116DRLR.step`.

The DRL orderable is an eight-pin SOT-5X3 (TI drawing DRL0008A), not a six-pin SC-70. The candidate uses the installed KiCad `SOT-583-8` footprint and matching `SOT-583-8.step` package model. The pad geometry matches TI's DRL land-pattern dimensions: 0.5 mm row pitch, 1.48 mm spacing between pad columns, and 0.67 × 0.30 mm lands. FreeCAD 1.0.0 inspection of the package STEP measured the main body section at about 1.19 × 2.09 mm over z=0.15–0.20 mm and 1.13 × 2.03 mm at z=0.60 mm, consistent with TI's 1.1–1.3 × 2.0–2.2 mm body limits. The model has pin-1 marker at x<0, y>0, which maps to footprint pin 1 at x<0, y<0 under KiCad's Y-axis convention. Its land underside is z=0; model is placed at zero offset/rotation. Full bbox is 1.6 × 2.1 × 0.695 mm; the extra topmost 0.1-mm-scale feature is a small marker, while the plastic body section remains within the 0.6-mm max height. Evidence: `ai-files/reports/tps2116-model-inspection.json`, `tps2116-model-sections.json`, and TI drawing render in `ai-files/reports/tps2116-ti-render/`.

Current supplier snapshot: LCSC C3235557 showed 79,248 pieces in stock; $0.4024 at quantity 1 and $0.3088 at quantity 10. TI's own product page currently reports out of stock. This is a sourcing snapshot, not a purchase or final BOM commitment. The existing report's low-current estimate (50 nA typical VIN2 standby, 1.35 µA max through 85°C / 4.5 µA max through 105°C in the stated VIN2-powered case) remains the relevant battery standby budget.

For bypassing, reserve C124 and C125 as 1 µF input capacitors, one local to each VIN pin group, per TI's power-supply recommendation that 1 µF is sufficient in most cases to avoid input droop on turn-on. Use the existing U12 input capacitor as the mux output reservoir if it is physically close and its value meets the regulator's requirement; add a separate output capacitor only if that check fails. U20, R124/R125 and C124/C125 were not found in the current schematic and are reserved designators for main capture. Candidate assets are not registered and no active schematic has been changed.

### PR1 divider part sources

Candidate R124 is Yageo RC0603FR-07180KL, LCSC C123419 (180 kΩ, ±1%, 0603, 100 mW). The retrieved LCSC product page reports 83,300 pieces, MOQ100, and $0.0012 each at 100+ / $0.0009 at 1,000+. [LCSC part page](https://www.lcsc.com/product-detail/C123419.html), [Yageo datasheet](https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-07180KL). R125 is the already-used Yageo RC0603FR-07100KL, LCSC C14675 (100 kΩ, ±1%, 0603); it is present in other subsystem candidates and active circuitry, so only one MPN/LCSC mapping is needed. Yageo datasheet confirms the 180 kΩ resistor's 0603 body and ±1% tolerance. Stock and pricing are sourcing snapshots, not guaranteed quote values. The 180 kΩ LCSC page crawl may be stale, so reconfirm inventory and minimum purchase quantity before buying.
