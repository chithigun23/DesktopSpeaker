# Cold-start-safe USB input path options

Updated: 2026-10-05. Research only. No schematic or firmware changes. This note supplements [`automatic-usb-source-policy.md`](automatic-usb-source-policy.md).

## Finding on the proposed limited bootstrap branch

The TPS26600 cannot serve as a guaranteed 100 mA-or-less bootstrap limiter. Its specified adjustable overload range starts at 100 mA nominal; for the 120 kΩ setting the data sheet gives 85/100/115 mA min/typ/max. Its 4.2 V minimum operating voltage and integrated reverse blocking are useful, but do not cure the current-limit maximum above the conservative fallback.

TPS26620 is a closer fit electrically, but the available guaranteed points do not support the proposed 60–70 mA setpoint claim:

- It has adjustable 25–880 mA nominal current limit, but TI only states ±5% accuracy at 880 mA. At the lowest documented resistor, 267 kΩ, TI specifies 20/25/32 mA at 1 V headroom. The 44.2 kΩ point specifies 145/152/159 mA. Although the formula gives about 94.8 kΩ for 70 mA nominal, the data sheet provides no full-temperature min/max bound at that point. Do not call a 70 mA setting “90 mA maximum” without written TI clarification or qualification data that supports the product requirement.
- A 25 mA setting’s specified maximum is 32 mA, too close to BQ25895’s typical 30 mA bad-source qualification pulse to be a robust bootstrap for the charger, and far too low to power the MCU plus controller rails as well.
- Its recommended input range begins at 4.5 V. Thus a 4.45 V raw-input corner is outside specification; it cannot be relied on to start there. At 70 mA, its 478 mΩ typical pass-FET resistance adds about 33 mV drop, but input-voltage qualification is the larger issue.
- TPS26620 has adjustable OVP cutoff and integrated back-to-back FET reverse-current blocking. The OVP rising threshold is 1.18–1.23 V (nominal 1.2 V); divider accuracy and resistor tolerances need to be included when setting an approximately 11 V trip. Reverse-current protection turns off the FET after V(IN)−V(OUT) falls below −2.6 V (310 ns typical), so it is not an ideal-diode zero-reverse-current guarantee during the comparator response interval.
- TPS26620 is latch-off for overload/thermal faults. A fault requires cycling SHDN, UVLO, or input power. TPS26621 auto-retries after a 512 ms retry interval, but it does not solve the unqualified 70 mA current-limit bound or 4.5 V operating minimum. Select latch-off versus retry only after defining fault recovery and ensuring the main bypass stays hardware-off.

The orderable candidate is **TPS26620DRCT**, TI 10-pin 3 × 3 mm SON/VSON, LCSC **C2155827**. The LCSC listing and MPN were found, but live inventory was not verified; the available listing is not a stock guarantee. TI datasheet `ai-files/datasheets/TI_TPS2662.pdf` (Rev. F) and official product page: https://www.ti.com/product/TPS2662/part-details/TPS26620DRCT . LCSC listing: https://www.lcsc.com/product-detail/surge-protection-devices-spds_ti-tps26620drct_C2155827.html .

## Sequencing consequence

The parallel-path concept is directionally sound only if the limited path’s guaranteed maximum truly stays below the desired fallback ceiling, and the high-current path is physically held off through MCU reset/brownout. The default-off control should be hardware-biased inactive and require a fresh, volatile source classification; reset, watchdog, I2C failure, detach, or invalid classification must deassert it. An adapter label and BQ reset/current-detect result are not grants.

There is a second bootstrap issue: BQ25895’s converter startup input limit is the lower of 200 mA and programmed IINLIM while SYS is below 2.2 V (§8.2.3.5). A 60–70 mA branch may therefore prevent BQ startup if that path is expected to supply BQ SYS or the MCU. The BQ’s 220 ms REGN startup delay may leave a window for independently powered control to configure it, but the MCU must have its own supply and the exact timing/reset behavior must be proven. Reopening a path that causes VBUS POR restores the BQ defaults, so preconfiguration before that POR does not persist.

Before freezing this architecture, choose one demonstrable path:

1. Use a bootstrap limiter with a manufacturer-guaranteed upper current bound below 100 mA at the chosen setting, and separately power the MCU/control load without allowing aggregate connector current above the fallback ceiling; or
2. Use a device/startup profile with a true hardware 100 mA default and sufficient control startup capability; or
3. Keep the charger isolated until independently powered control has established a compliant input limit, then attach it in a way that does not re-enter an unsafe POR/default interval.

The TPS26600 proposal fails option 1 due to its 115 mA specified maximum at the lowest nominal setting. TPS26620 does not yet substantiate option 1 at 60–70 mA and has a 4.5 V minimum. Do not present either as a proven <=100 mA bootstrap. Any design must account for aggregate current consumed directly from VBUS by the eFuse, PD controller, regulator, MCU and detection circuitry, not just current delivered to the BQ.

## Primary references

- TI TPS2662x Rev. F, `../datasheets/TI_TPS2662.pdf`, especially Recommended Operating Conditions, Electrical Characteristics, §§9.3.5–9.3.6 and §10.2.2.2. https://www.ti.com/lit/ds/symlink/tps2662.pdf
- TI TPS26600 data sheet, `../datasheets/TPS2660.pdf`, current-limit range and electrical characteristics. https://www.ti.com/lit/ds/symlink/tps2660.pdf
- TI BQ25895 Rev. C, `../datasheets/BQ25895.pdf`, §8.2.3.5 and startup sequence. https://www.ti.com/lit/ds/symlink/bq25895.pdf
