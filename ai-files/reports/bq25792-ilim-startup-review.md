# BQ25792 ILIM_HIZ startup review

**Scope:** Primary-source review of the proposed Q101 cold-start HIZ gate and host current-limit policy. No schematic edits were made.

## Finding

TI datasheet Rev. C §9.3.4.3 says the charger ADC samples ILIM_HIZ once “at POR,” before switching, and computes the external clamp. A sample below 1.08 V maps to the minimum 100 mA clamp. The same section says switching resumes once the pin rises above 1 V, but does not say that this re-samples or updates the cached clamp. Therefore, with Q101 holding the pin below 0.75 V at POR, assume the sampled 100 mA clamp remains in force after Q101 releases. Do not rely on release to resample. The documented escape is clearing `EN_EXTILIM` (REG14 bit 1); then the host can program IINDPM above the sampled clamp. TI support also describes disabling the external clamp and rewriting IINDPM as the remedy for an ILIM clamp [TI E2E response](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1579692/bq25792-issue-with-bq25792-in-design-based-on-usb-pd-chg-evm-01-evaluation-board).

The reset behavior is favorable for a host-managed design but needs deliberate watchdog handling:

- REG06 IINDPM is reset by `REG_RST`, not by watchdog; its POR default is 3 A. D+/D− source detection can set other values.
- REG14 `EN_EXTILIM` is reset by `REG_RST`, not by watchdog. REG14 `EN_IINDPM` is reset by watchdog and `REG_RST`.
- Datasheet §9.4.1 says watchdog expiry returns the device to default mode; §9.4.2 describes the distinct `REG_RST` reset. Thus a watchdog expiry does not, by itself, restore the external ILIM clamp. `REG_RST` does.

The proposed 180 kΩ/100 kΩ REGN divider is **not a fixed hardware current ceiling** once firmware clears `EN_EXTILIM`; the external clamp is disabled then. With the clamp enabled, its nominal threshold follows `IILIM = (0.357 × VREGN − 1 V) / 0.8 Ω` when the result is in range; it depends on REGN voltage and tolerances. More critically, if sampled below 1.08 V it means 100 mA, not the claimed 0.8–1.1 A. Do not describe this divider as an assured 0.8–1.1 A ceiling without verified REGN range/tolerance calculations and prototype measurements.

## Candidate host startup policy

1. Keep Q101 asserting ILIM_HIZ low through POR and MCU initialization; this keeps the converter stopped while the host configures it.
2. Before releasing Q101, disable the BQ watchdog (`WATCHDOG=00`) or implement and verify a watchdog service/recovery path. Disable automatic input detection, ICO and HVDCP actions if the host will own the negotiated-source limit; TI documents that D+/D− detection changes IINDPM. Confirm the exact configuration bits and read back their state.
3. With ILIM_HIZ still low, clear `EN_EXTILIM`, keep `EN_IINDPM=1`, program IINDPM from the actual source capability (including a conservative 100 mA limit for unknown/weak sources), and read back the register. Configure and verify the 1S battery voltage/charge-current limits and charge-enable state. Use PD contract/current information for PD sources; do not infer a 100 mA allowance from the charger’s adapter detection alone.
4. Release Q101 only after those checks; then enable charging as a separate step. On source change, lower IINDPM before allowing the new source to supply the load/charger. If firmware cannot establish the source limit, leave HIZ asserted.
5. Treat any `REG_RST` as a fresh unsafe configuration: it resets both IINDPM and `EN_EXTILIM`. Keep HIZ asserted and repeat configuration before release. A watchdog-based recovery must account for `EN_IINDPM` reset and for charger return to default mode; disabling the watchdog is simpler if firmware supervision is dependable.

This sequence is a practical host-controlled startup proposal, not a validated firmware implementation. TI documentation establishes that clearing `EN_EXTILIM` removes the pin clamp; it does not document a dynamic re-sampling on gate release. Confirm register-write ordering and behavior on the BQ25792EVM/prototype before relying on it. If the product must enforce a weak-source ceiling when the host is absent or failed, this host-only scheme is insufficient; retain a characterized hardware clamp and do not clear `EN_EXTILIM`, or add independent source-current enforcement.

## Sources

- [BQ25792 datasheet, Rev. C, §9.3.4.3, §9.3.4.5, §9.4.1–9.4.2, REG06 and REG14](https://www.ti.com/lit/ds/symlink/bq25792.pdf) (local copy: `ai-files/datasheets/BQ25792.pdf` and extracted text).
- [TI E2E: BQ25792 issue—TI response on disabling EN_ILIM and rewriting IINDPM](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1579692/bq25792-issue-with-bq25792-in-design-based-on-usb-pd-chg-evm-01-evaluation-board).
