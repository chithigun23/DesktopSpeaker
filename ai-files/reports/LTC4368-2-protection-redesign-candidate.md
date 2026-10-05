# LTC4368-2 protection redesign candidate

Research snapshot: 2026-10-05. This is a schematic-level candidate, not a qualified design. It addresses raw USB-C VBUS TVS2200, STUSB4500 VDD and VBUS_VS_DISCH exposure, 5/9 V sources, about 10.5 V OV, 3.9 V UV and a nominal 2.2 A breaker target.

## Proposed power path

Replace the existing TPS26600 plus Q1/Q2 high-side path with an ADI LTC4368-2 controlling a back-to-back 60 V N-MOSFET pair and series sense resistor. Keep TVS2200 at raw connector VBUS and the BQ25895/bypass capacitors on protected output. Limit the PD profile to 5 V and 9 V; 15/20 V cannot feed the BQ25895 input. Set nominal UV/OV near 3.9 V/10.5 V, then calculate divider values against the LTC4368 ±1.5% comparator accuracy and resistor tolerances.

| Function | Candidate | LCSC observation (2026-10-05) | Notes |
|---|---|---|---|
| Controller | ADI LTC4368IMS-2#PBF, C688402 | 65 pcs, US$8.85 each | MSOP-10; 2.5–60 V operating, −40 to +100 V withstand, +50 mV forward and −3 mV reverse thresholds. [LCSC](https://www.lcsc.com/product-detail/Surge-Protection-Devices-SPDs_ADI-LTC4368IMS-2-PBF_C688402.html) |
| N-FET pair | Infineon BSC014N06NS, C113391, qty 2 | about 29,589 pcs, US$1.49 each | 60 V TDSON-8FL; LCSC gives 1.45 mΩ at 10 V gate drive. Max RDS(on) 1.45 mΩ at VGS=10 V; verify hot RDS(on), SOA, VDS overshoot and thermal layout before use. Manufacturer Rev 2.6 datasheet linked below; the downloaded copy under ai-files/datasheets is an older manufacturer revision hosted by LCSC. [LCSC](https://www.lcsc.com/product-detail/MOSFETs_Infineon-Technologies-BSC014N06NS_C113391.html) |
| Sense resistor | Vishay WSK2512R0200FEA, 20 mΩ, 2512 | LCSC C1517429; 13 pcs and US$1.4176 each in the 2026-10-05 snapshot | ±1%, 1 W, ±35 ppm/°C. Low stock; recheck before purchase. [LCSC](https://www.lcsc.com/pl/product-detail/C1517429.html) |

Use a 20 mΩ sense resistor rather than 22 mΩ. At the 50 mV typical forward threshold, this gives 2.50 A nominal. LTC4368 Rev C specifies 40–60 mV at VOUT≈VIN; with 1% shunt tolerance, the normal-output trip range is about 1.98–3.03 A. At very low output voltage it permits a wider 30–70 mV threshold, so the startup trip range is wider still. The lower threshold (about 1.98 A) is above the existing R102 hardware-limit estimate of about 1.79 A, leaving little but positive nominal margin before hot/cold and measurement effects. It is still only a circuit breaker: current can exceed the threshold during comparator and gate response, and it does not regulate the current to 2.5 A.

For an illustrative 23 mΩ board path (20 mΩ shunt plus about 3 mΩ room-temperature two-FET path), loss at 1.5 A is about 52 mW and drop about 35 mV. With a 4.75 V connector source and the explicit 0.20 Ω cable/contact loop, the charger input estimates 4.41 V at 1.5 A and 4.30 V at 2.0 A. These estimates exclude MOSFET hot resistance, layout, connector/PCB resistance and source/cable variation.

### Inrush and 9-to-20 V edge

ADI's application circuit uses a gate-slew network and demonstrates a particular inrush result, but it does not establish this design's current waveform with a different MOSFET pair and load. Model and scope the actual 60 µF output capacitance plus powered downstream loads at 5 V/9 V startup; check MOSFET SOA and LTC4368 response timing. The 32 ms turn-on delay occurs before the gate is enabled; it does not itself limit the subsequent capacitive inrush.

For a live 9-to-20 V fault, 10.5 V OV should pull the gates down. However, LTC4368 is a circuit breaker, not a current limiter: current can overshoot its sense threshold while its comparator and gate discharge turn the MOSFETs off. Do not infer a constant-current charging time from the 2.5 A nominal trip setting. Simulate the actual 60 µF network and controller/MOSFET transient model; check MOSFET SOA and peak voltage/current, then scope both raw and protected nodes. ADI documents a 1 µs OV comparator, fast gate fault response in microseconds, and a 32 ms gate re-enable delay after voltage faults. Keep 20 V disabled in the STUSB4500 NVM.

### STUSB4500 enable polarity

STUSB4500 `VBUS_EN_SNK` is active-low open-drain; LTC4368 `SHDN` is high-to-enable and low-to-shutdown. Add an inverter transistor stage with defined pull-up so a low asserted `VBUS_EN_SNK` drives SHDN high. Released/high-impedance `VBUS_EN_SNK` must pull SHDN low. Check startup, hard reset, detach and unpowered-node leakage at schematic level.

## STUSB4500 pin protection and supply

### VBUS_VS_DISCH sensing

Keep raw connector-side sensing so the STUSB4500 sees normal 5 V/9 V, and add a 12 V zener from the U11 pin-side `VBUS_VS_DISCH` node to ground, **after existing R4=3.3 kΩ**. The sheet also has R1=470 Ω and D4=1N4148W in this sense/discharge network; confirm exact net topology before capture. The 12 V clamp is above the valid 9 V monitor window (about 10.5 V nominal high limit), so 20/28.4 V faults remain overvoltage rather than reading as a valid contract. At raw 28.4 V, R4 limits current to about (28.4−12)/3.3k = 5 mA and zener dissipation to about 60 mW. At 9 V +5% (9.45 V), the zener should remain off. Select an actual 12 V zener whose cold minimum breakdown exceeds 9.45 V and whose hot clamp remains below STUSB4500's 28 V absolute maximum; verify dynamic clamp and pulse/temperature rating. ST requires a series resistor to limit discharge current through this pin to 50 mA max. Do not place the clamp before R4.

### VDD supply

Candidate: raw connector VBUS to TI TPS7B8450QWDRBRQ1, fixed 5 V, then STUSB4500 VDD; ground VSYS. The LDO is rated 3–40 V input (42 V max), so 28.4 V TVS2200 max clamp is below its input rating. It has ±0.75% output accuracy and 225 mV maximum dropout at 150 mA. [TI TPS7B84 datasheet](https://www.ti.com/lit/ds/symlink/tps7b84-q1.pdf); downloaded copy: `ai-files/datasheets/TPS7B84-Q1.pdf`.

Using 225 mV full-load maximum as a conservative bound: 4.75 V connector source less 0.20 Ω cable/contact at 1.5 A gives 4.45 V at the port; minus 225 mV gives 4.225 V VDD. At 2.0 A, 4.35−0.225=4.125 V, narrowly above STUSB4500's 4.1 V minimum. At 2.2 A, 4.31−0.225=4.085 V, below minimum. So the candidate retains margin for the 5 V/2 A corner in that cable model, but not at the full nominal breaker current. TPS7B8450QWDRBRQ1 was LCSC C3751394 and showed only 1 pc at US$1.3452; stock is thin and not a purchase commitment. [LCSC](https://www.lcsc.com/de/product-detail/C3751394.html).

The dropout bound comes from the 150 mA maximum-dropout row, not a guaranteed maximum at STUSB4500's light load. STUSB4500 Rev 3 lists 210 µA maximum idle VDD current at 25°C, but does not establish active I²C/startup peak or full-temperature current. Confirm VDD startup ramp and actual peak load/current before freezing the LDO. The LDO is upstream of the LTC cutoff, so raw TVS plus the LDO's 40 V input rating protect it; the LTC path does not.

The older TPS7A1650 proposal is not selected: its 60 mV at 20 mA is typical, not guaranteed maximum; its 500 mV max row is at 100 mA. Do not claim weak-5-V margin from the typical dropout alone. Its datasheet copy is `ai-files/datasheets/TPS7A16.pdf`.

## Prepared local library assets (not registered or captured)

- `DesktopSpeaker-kicad/kicad-library/schematic/BSC014N06NS.kicad_sym`: standard NMOS graphic; KiCad 10 native common-pad stacks use Gate 4, Source `[1-3]`, Drain `[5-8]`. Mapping is from the Infineon pin assignment.
- `DesktopSpeaker-kicad/kicad-library/footprint/BSC014N06NS_TDSON-8FL.kicad_mod`: based on the installed KiCad Infineon PG-TDSON-8 pattern; side pads mapped 1-4 and drain pads 5-8, center exposed drain pad numbered 5, electrically common with drain pins 5-8. Infineon Rev 2.6 pin diagram identifies only drain pins 5-8; it assigns no separate pin 9. Dimensions match the PG-TDSON-8 envelope (6.15 x 5.15 x 1 mm). `BSC014N06NS.step` is the installed KiCad generic TDSON-8 model; Cartesian geometry bounds are 6.15 x 5.15 x 1.03 mm, not a manufacturer-authenticated STEP. The symbol footprint field matches the actual `BSC014N06NS_TDSON-8FL` footprint filename. Infineon maker STEP was located but the vendor download endpoint blocked direct retrieval.
- `DesktopSpeaker-kicad/kicad-library/footprint/TPS7B8450QWDRBRQ1_WSON-8.kicad_mod`: matching TI DRB 3 x 3 mm WSON-8 with 1.6 x 2.0 mm exposed pad and pad 9 to GND; fixed-output pin 2 remains NC per the datasheet. Its STEP is the installed KiCad generic model (3.0 x 2.98 x 0.83 mm), not TI-authenticated CAD.
- These assets are unregistered; the project footprint/symbol tables and schematic were not changed. Review package land numbering and thermal-pad treatment before board work.

## Open checks

- Recalculate UV/OV dividers at worst-case tolerance; confirm UV=3.9 V does not nuisance-trip at the desired cable sag and OV=10.5 V catches the 9-to-20 edge.
- The LTC4368 is 60 V rated, but MOSFETs, capacitors and protection parts need voltage/SOA margin over the TVS max clamp plus measured layout overshoot. D6 does not guarantee full-rated surge protection for STUSB4500.
- Check 32 ms turn-on/recovery behavior with source attachment/renegotiation and `VBUS_EN_SNK` sequencing.
- The 2.5 A nominal breaker has a broad published tolerance band (about 1.98–3.03 A around normal output). Confirm that this is acceptable; it does not constitute a 2.2 A current limit.
- Validate reverse/backfeed behavior, MOSFET SOA during startup and 20 V fault, thermal rise, TVS/zener pulse energy, and cable/source corners. No hardware qualification has been done.

## Primary evidence

- ADI [LTC4368 Rev C datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4368.pdf): operating/absolute voltage, OV/UV reference accuracy, breaker threshold, comparator/gate response, 32 ms restart and inrush application circuit.
- ST [STUSB4500 Rev 8 datasheet](https://www.st.com/resource/en/datasheet/stusb4500.pdf): VDD 4.1–22 V operation, 28 V absolute maximum, raw-receptacle monitor/discharge pin, 50 mA discharge limit, active-low `VBUS_EN_SNK`.
- TI [TPS7B84-Q1 Rev B datasheet](https://www.ti.com/lit/ds/symlink/tps7b84-q1.pdf): 40 V input / 42 V max, 5 V option, 225 mV max dropout at 150 mA, ±0.75% output accuracy.
- Infineon [BSC014N06NS Rev 2.6 datasheet](https://www.infineon.com/assets/row/public/documents/24/49/infineon-bsc014n06ns-datasheet-en.pdf); downloaded older copy at `ai-files/datasheets/BSC014N06NS.pdf`.
- Downloaded controller datasheet: `ai-files/datasheets/LTC4368.pdf` (ADI Rev C).
