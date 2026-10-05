# 5 V input headroom review

2026-10-04. Calculation and datasheet review only; no physical validation or PCB thermal analysis.

## Inputs and limits

- [TPS2660 datasheet](https://www.ti.com/lit/ds/symlink/tps2660.pdf): operating input minimum 4.2 V; total on resistance 150 mΩ typical, 250 mΩ maximum over the specified temperature range. Electrical-characteristic test conditions use 24 V input, so the maximum is not a complete characterization of this board at 5 V. PWP JEDEC reference-board RθJA is 38.6 °C/W.
- [STL9P3LLH6 datasheet](https://www.st.com/resource/en/datasheet/stl9p3llh6.pdf): each PMOS is 22.5 mΩ maximum at VGS=-4.5 V, ID=-4.5 A, 25 °C; paired allowance 45 mΩ. This is not a hot-board bound or a guarantee at lower gate drive.
- [BQ25895 datasheet](https://www.ti.com/lit/ds/symlink/bq25895.pdf): input operating range 3.9–14 V, maximum PWM duty 97%, VINDPM accuracy ±3% at specified 4.4/9 V conditions. Input voltage regulation reduces current to avoid collapse; battery supplement can cover insufficient input power but cannot be assumed when battery is absent.
- The existing 220 Ω ILIM resistor allows approximately 1.45–1.77 A. Firmware must keep EN_ILIM enabled and apply a lower limit whenever source permission or input headroom requires it.

## Illustrative voltage budget

Use Rboard=0.250+0.045=0.295 Ω. Cable/contact resistance below is an explicit scenario, not a USB compliance limit. Ignore PCB trace losses, connector tolerance, source dynamic droop and capacitor ESR for this first calculation.

`VBUS_PD = Vsource - Iinput × (Rcable + 0.295 Ω)`

| Source | Cable/contact loop | Input current | Calculated charger input |
|---|---:|---:|---:|
| 5.00 V | 0 Ω | 1.50 A | 4.558 V |
| 5.00 V | 0.20 Ω | 1.50 A | 4.258 V |
| 4.75 V | 0.20 Ω | 1.50 A | 4.008 V |
| 4.75 V | 0.20 Ω | 1.00 A | 4.255 V |
| 4.75 V | 0.20 Ω | 0.50 A | 4.503 V |

The first-pass 4.75 V / 0.20 Ω / 1.5 A case leaves only 108 mV above the charger's 3.9 V operating minimum. The eFuse input before its own resistance is 4.383 V, only 183 mV above its 4.2 V minimum. Neither margin is sufficient to claim robust full-load operation without further qualification.

At 4.008 V, the ideal 97% duty ceiling is only 3.887 V before internal losses. That does not support full-current charging of a cell near 4.2 V. The system can still operate at reduced power; charging must taper or stop. External-power operation with a missing battery requires the audio load to remain within the reduced available power.

For a nominal 4.4 V VINDPM setting, the same resistance model gives `(4.75-4.4)/0.495≈0.71 A` before voltage regulation reduces current. A 4.532 V upper threshold corner gives approximately 0.44 A under that scenario. These are illustrative intersections, not firmware limits or guaranteed limits.

## Dissipation

At 1.77 A and 250 mΩ the eFuse alone dissipates approximately 0.783 W. Its reference-board RθJA would imply about 30 °C rise from that conduction loss. Real enclosure temperature, copper, pad soldering and transient losses are not represented by the JEDEC figure. At 1 A the same allowance is 0.25 W. This is a meaningful thermal and 5 V efficiency cost of the current protection choice.

## Integration policy

1. Start with charging disabled and both regulated downstream rails disabled. Use the permitted source current, never just the 2 A adapter label.
2. Preserve a conservative input-current setting while identifying the source. Raise it gradually only after checking VBUS ADC, VINDPM/IDPM and fault status. Keep an independent source-current ceiling throughout.
3. Reduce charge current first when VINDPM/IDPM is active, then reduce audio demand. For battery-absent operation, enforce the external input budget directly; do not rely on supplement mode.
4. Do not lower VINDPM merely to conceal excessive series voltage loss. Maintain converter and eFuse input margins and adequate buck headroom for the requested battery voltage.
5. Prefer the qualified 9 V contract when available. It improves headroom but does not authorize exceeding source, ILIM, pack or thermal limits.
6. Keep final 5 V current capability open until cable/temperature/dropout characterization. A lower-resistance, sufficiently high-voltage-rated protection alternative is a potential redesign if the required 5 V loudness cannot be met; no replacement is selected in this review.

The schematic is unchanged by this review. The findings belong to MCU source management and later component/thermal qualification; the existing hardware ILIM ceiling is not a promise of 1.77 A operation from every 5 V source.
