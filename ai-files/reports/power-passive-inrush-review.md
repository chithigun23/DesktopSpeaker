# Power passive and startup review

2026-10-05. Capture/review calculations; no physical tests, ERC or PCB layout.

## eFuse ramp capacitor

C181 is22nF X7R50V0603 from U18 dVdT12 directly to grounded RTN. It replaces only the intentional no-connect on pin12. The initially considered C0G22nF50V part was unavailable in0603. X7R is practical here: during a5/9V output ramp, the control pin is only about0.2–0.4V, far below the capacitor50V rating. Temperature/initial-tolerance effects are included below; DC-bias/aging still need qualification. Concrete MPN selection is recorded in the sourcing handoff/BOM when reviewed.

[TI TPS2660 datasheet §9.3.4](https://www.ti.com/lit/ds/symlink/tps2660.pdf) specifies startup `dVout/dt = IdVdT × Gain / C`. Using4.7µA,24.6 and22nF gives5.255V/ms, approximately0.951ms at5V and1.713ms at9V. The datasheet's rounded Equation2 gives slightly different approximate times; the values here use the listed electrical parameters. The previous open-pin ramp is23.9V/1.6ms≈14.94V/ms.

Using4–5.5µA, gain23.75–25.5 and capacitor±10% plus X7R±15% temperature allowance yields approximately3.41–8.33V/ms, or1.08–2.64ms for a9V ramp, before aging/DC-bias uncertainty. These electrical characteristics use their stated datasheet conditions, including24V input; they do not constitute verified5/9V board startup timing.

For a deliberately conservative60µF directly/reflected-connected input-capacitor scenario, `I=C×dV/dt` gives about0.315A typical and0.500A at the fastest calculated corner, versus0.896A with the old nominal open-pin ramp. C100, PMID C101/C108 and the connected sense capacitor are nominally46.3µF; BQ's input switch/converter behavior means they are not a single guaranteed lumped capacitance. Its SYS/regulated-rail capacitors and any running load add dynamic demand not represented by this calculation.

This reduces capacitive inrush but is not a complete USB compliance or source-current proof. Charging and downstream rails remain default-disabled. Startup from a weak source and battery-absent conditions still require qualification. U18 current limit is not the source entitlement, and the ramp capacitor does not fix hotplug overshoot ahead of U18 or9→20V OVP response.

The drawing uses a direct wire, no extra net label, and downward ground. R182's ground tail was shortened to make room. Before/after physical netlist review preserved all prior groups after excluding the intended U18.12 connection; the new net contains only U18.12 and C181.1, with C181.2 on GND. PD detail preview was inspected.

## Discharge resistor R4

Selected **YAGEO RC1206FR-073K3L, LCSC C137292**, preserving3.3k displayed value and1206 footprint. [Exact maker spec](https://yageogroup.com/component-documentation/download/specsheet/RC1206FR-073K3L) gives±1%,±100ppm/°C,0.25W at70°C, body3.1×1.6×0.55mm and200V maximum continuous voltage (power-based limit also applies). Generic installed KiCad1206 package model remains a package visualization, not exact maker CAD.

With resistor initial tolerance included, worst resistance at25°C is3267Ω. Continuous powers are0.0248W at9V,0.1224W at20V and0.1481W at22V. All are below0.25W at70°C. Board/enclosure heating and further derating above70°C remain applicable; source faults beyond the normal5/9V operating policy are not a claim of indefinite survival at every temperature. At28.4V the same initial-tolerance calculation is0.247W before temperature effects, so the high-rated raw-TVS scenario must be evaluated as a transient, not a continuous operating case.

No specialized pulse-overload claim is made from the general-purpose resistor rating. Sustained20/22V dissipation is bounded under the stated temperature conditions; final discharge timing, transistor/IC pin limits, pulse-energy and live-transition qualification remain open.

## Regulator feedback temperature sensitivity

Selected1%0603 resistors with up to100ppm/°C TCR add independent temperature drift to the earlier initial-tolerance calculations. Do not quote those earlier numbers as full-temperature output bounds. Opposite-sign100ppm/°C drift across75°C can change the divider ratio by approximately1.5% before reference and bias-current effects. TPS61023 PFM reference has no maximum in its listed electrical-characteristics table; typical601mV versus595mV PWM reference and comparator-delay ripple do not prove an upper bound.

The existing732k/100k nominal4.95V rail therefore remains **unqualified against PCM2902C's5.25V upper operating limit over all loads/temperatures**. Feedback-target adjustment or a better-bounded regulator is a later design decision; displayed values are preserved in this capture. The3.819V Bluetooth target also needs temperature/ripple/transient review, but has more room below BM83's4.2V maximum than the current codec rail.

## Charger capacitor margin and selected parts

C101/C108 use Samsung CL32B226KAJNNNE (C309062), 22uF25VX7R1210 each. At9V the official typical curve gives11.506uF each; illustrative initial-tolerance0.90 and temperature0.85 factors give17.604uF for the pair before aging/chart uncertainty. TI describes8.2uF as suggested for typical3–5A charging, not an explicit guaranteed effective-capacitance minimum.

C102/C109 use Samsung CL21B106KPQNNNE (C32635),10uF10VX7R0805 each. At6V the typical curve gives3.98uF each; the same illustrative factors give about6.09uF for the pair. TI's REGN pin guidance specifies nominal4.7uF ceramic. Doubling the bank improves margin but adds startup demand; typical curves do not guarantee compliance over every production part and temperature.

C180 uses Samsung CL21B105KBFNNNE (C28323),1uF50V0805. It sees the eFuse input, including a20V fault. Maker curve at20V gives about0.700uF typical, or0.535uF after the same factors, above the0.1uF local target before aging/chart uncertainty. C5 is Samsung CL31B475KBHNNNE (C51205); its footprint changed to1206 to match the documented4.7uF50V part. Local standard1206 footprint/STEP are package visualizations rather than exact Samsung CAD.

Other power resistors/decouplers now have selected MPN/LCSC metadata; see power-passives-selected.json and applied-power-passives.json. C100's exact listing is recorded but no standalone exact-part manufacturer PDF was obtained. C10347nF remains unassigned pending review. Final package heights, nominal-versus-effective capacitance and regulator stability/transient behavior still require board-level qualification.

## Legacy USB source identification

PCM2902C's fixed USB configuration descriptor is bus powered with bMaxPower0x32 (100mA). A legacy computer connection therefore cannot be treated as a5V2A adapter. Firmware must apply the permitted current for the actual source; a Type-C/PD grant is a separate case. The BQ25895 reset500mA setting is not universal permission. Battery supplementation may support load while respecting host input current.

BQ D+/D− remain intentionally unused in this capture. Automatic legacy charger detection would require an agreed shared USB-data detection/mux arrangement, or a user-selected known-adapter setting. User preference is pending. No detector, MCU, codec or audio data connections were added. Source policy must be applied after resets/watchdog events before enabling charging.
