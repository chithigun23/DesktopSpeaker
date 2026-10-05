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
