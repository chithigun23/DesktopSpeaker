# Low-current bootstrap switch search

Updated: 2026-10-05. Bounded component search only; no schematic or firmware changes. Goal was a 5 V branch switch with a documented 70–80 mA setting and guaranteed maximum below 90 mA over temperature, without a startup current-limit bypass.

## Best branch-switch candidate: MAX4995B

ADI’s **MAX4995** adjustable current-limit family is the strongest fit found. The datasheet specifies an adjustable 50–600 mA limit with ±10% accuracy over −40 °C to +125 °C (VIN 1.7–5.5 V). It has no startup current-limit bypass specified, has 120 µs typical switch turn-on for the stated 1 µF/20 Ω condition, and integrates reverse-current protection. Use the **MAX4995B** latch-off response for fail-safe behavior, with MCU-controlled ON reset after faults; MAX4995C is continuous limit but the observed LCSC listing was out of stock.

Concrete setting candidate: **RSETI = 390 kΩ, 1%**. The datasheet product limit is `(RSETI + 2.48 kΩ) × ILIM = 26,138 / 29,042 / 31,946 V` min/typ/max. Including 1% resistor tolerance, this yields approximately **66.6 mA min / 74.0 mA typ / 82.2 mA max** across the specified conditions. Add the IC’s 300 µA maximum quiescent current and the other raw-input loads separately. At a 10 µF downstream capacitance and 5 V, 50 µC is charged through a maximum 82.2 mA branch limit in at least about **0.61 ms** (`50 µC / 82.2 mA`), ignoring ramp/profile details. There is no TPS22946-style 435 mA/8 ms startup override in the MAX4995 datasheet.

Exact purchasable candidate found: **MAX4995BAUT+T**, LCSC **C2155763**, Maxim/ADI SOT-23-6. LCSC showed 42 units in a current page snapshot; inventory is volatile. Price shown was about $6.76 each at quantity 1. Datasheet saved as [`ADI_MAX4995.pdf`](../datasheets/ADI_MAX4995.pdf); product page https://www.analog.com/en/products/MAX4995B.html ; LCSC https://www.lcsc.com/product-detail/Power-Distribution-Switches_Analog-Devices-Inc-Maxim-Integrated-MAX4995BAUT-T_C2155763.html .

**Voltage caveat:** the MAX4995 is rated only to 5.5 V at IN and 6 V absolute maximum on OUT. Its reverse-current feature does not make it safe to expose OUT to the parallel 9 V charger bus. Add a reverse-rated isolation element between MAX4995 OUT and common BQ VBUS, with voltage margin for the protected bus/transients. A 30 V-rated diode is an option to evaluate, but its worst-case forward drop at ~80–90 mA must be included. With 4.75 V at the connector, the TPS7B8450 may be in dropout: using the 225 mV maximum dropout specified at 150 mA gives conservative 4.525 V LDO output; subtracting a diode with ≤0.4 V maximum drop and roughly 0.03 V switch drop leaves about **4.10 V at BQ VBUS**, above its typical 3.8 V poor-source threshold, but with modest margin. Actual cable sag, LDO dropout-vs-current guarantee, diode Vf, BQ load, and temperature need to be checked together.

## Limiting constraint in the proposed full bootstrap chain

The MAX4995 can bound current **through the BQ branch** after the LDO. It cannot bound the total cold-attach current of `USB raw → TPS7B8450-Q1 → MAX4995 → BQ`, because the LDO’s required output capacitor is ahead of the MAX4995 and charges directly from raw VBUS at attach. TPS7B84-Q1 specifies 180–260 mA output current limit across the table’s full-range condition; this is not a ≤90 mA source bound. Its output requires ≥2.2 µF, so that capacitor stores 11 µC at 5 V. The raw-side direct-input capacitance also has to be counted against the USB attach charge budget (10 µF at 5 V is 50 µC). The downstream BQ capacitance can be placed after MAX4995 and is current-limited; the LDO output capacitor cannot. A separate high-voltage raw-input limiter/controlled-start path, or a power-tree sequencing solution that proves total attach current, is still required before claiming a whole-device ≤90 mA cold-start ceiling.

BQ25895’s poor-source test current is **30 mA typical only** in the electrical table and startup text; TI publishes no min/max on that parameter. The MAX4995 candidate’s 66.6 mA minimum setting leaves headroom over typical 30 mA but cannot prove margin over an unspecified maximum. BQ25895’s SYS<2.2 V startup clause sets the converter input-current ceiling to `min(200 mA, IINLIM)`; that is a limit, not a forced draw. The actual startup interaction with an 80 mA source, battery absent/present, SYS load, capacitor ramp, and VINDPM remains a hardware qualification question.

## Candidates ruled out or weaker

- **TPS2553/TPS2553-1:** recommended RILIM range ends at 232 kΩ. TI’s published equations give, at 232 kΩ, about 99.7 mA min, 117.0 mA nominal, and 137.3 mA max. It cannot meet ≤90 mA.
- **AP22652/AP22653:** nominal adjustment starts at 125 mA; its ±10% accuracy is only claimed at high settings. Not suitable for 70–80 mA.
- **MAX14575:** adjustment starts at 250 mA (and ±10% applies from 500 mA up), too high.
- **TPS22946:** its 30 mA mode documents max60mA at test points, but uses an 8 ms inrush window at 435 mA typical/685 mA max, and its documented max-limit table does not cover 5 V input. It is not a hard attach-current solution.
- **MAX4786:** fixed 50/100 mA options are guaranteed current limits; 100 mA leaves no budget for switch supply current, STUSB4500 raw current, regulator IQ, or other raw loads. 50 mA might be too close to the BQ’s typical30mA qualification plus SYS start; no better than the adjustable MAX4995 candidate.

## Primary references

- ADI MAX4995A–MAX4995C Rev. 3, `../datasheets/ADI_MAX4995.pdf`, especially pp. 1–3: https://www.analog.com/media/en/technical-documentation/data-sheets/MAX4995A-MAX4995C.pdf .
- TI TPS7B84-Q1 Rev. B, `../datasheets/TPS7B84-Q1.pdf`, output capacitor, dropout and current-limit characteristics: https://www.ti.com/lit/ds/symlink/tps7b84-q1.pdf .
- TI TPS2553 Rev. F, `../datasheets/TI_TPS2553.pdf`, Table 7.5 and §9.3 equations: https://www.ti.com/lit/ds/symlink/tps2553.pdf .
- TI BQ25895 Rev. C, `../datasheets/BQ25895.pdf`, Tables 7-5/7-6 and §8.2.3.2/8.2.3.5: https://www.ti.com/lit/ds/symlink/bq25895.pdf .
