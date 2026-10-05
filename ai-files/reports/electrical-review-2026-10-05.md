# Independent electrical review — 2026-10-05

Read-only review of the active `Fuel_Gauge_Power`, `USB_PD`, and `Battery_Charger` sheets plus the isolated `ai-files/candidates/Battery_Charger.kicad_sch` BQ25792 draft. Pin relationships were checked against the project’s latest captured netlist evidence (`reports/usb-aux-logic-integrated.xml`, candidate export `reports/review-candidate-netlist.xml`) and local manufacturer datasheets. No schematic edits or electrical tests were made. The candidate is not approved for integration.

## Prioritized findings

### Medium — gauge switches can be on while the gauge is below its valid supply range

**Active, concrete interface-range mismatch.** U13/U16/U17 TS5A3167 VCC pins (pin 5) are on `BAT_PACK`; each active-low IN pin 4 is grounded, so the switch is commanded on whenever it is powered. Their COM pins 2 join the MCU-side `CTRL_SDA`, `CTRL_SCL`, and `GAUGE_ALRT_N` nets pulled up to `3V_AO`; NC pins 1 go to MAX17048 U5 pins 8, 7, and 5. U5 VDD (pin 3) is also `BAT_PACK`. Thus, with a weak but nonzero pack, the switches remain commanded on while U5 is below its specified 2.5 V minimum. For BAT_PACK below the 3 V AO pull-up, TS5A3167’s recommended analog-port condition `0 ≤ VCOM ≤ VCC` is exceeded; below 1.65 V its supply is also outside recommended operation. The “powered-off isolation, VCC=0” feature covers an absent pack, not this low-but-nonzero range. USB can keep `3V_AO` alive throughout this condition.

**Action:** Hold the analog switches off until BAT/gauge voltage is in range, or change to a 3V_AO-powered isolation/level-translation arrangement with safe defaults and verify pull-up domains. Keep the MAX17048 disconnected whenever its supply is below its allowed range. Primary references: local `MAX17048_MAX17049.pdf`, electrical characteristics (VIN 2.5–4.5 V); local `TS5A3167.pdf`, §5.3 and powered-off leakage table. Schematic references: `Fuel_Gauge_Power.kicad_sch`, U13/U16/U17 and U5; latest integrated netlist confirms the pin groups above.

### Low — active USB auxiliary rail is an MCU-startup source, but its usable load/headroom is not yet bounded

**Active qualification gate, not a demonstrated wrong connection.** USB_VBUS feeds U19 TPS7B8450 (IN/EN pins 8/7); its output `USB_AUX_5V` feeds U20 TPS2116 VIN1 pin 3 and MODE pin 5. U20 VIN2 pin 6 is `SYS_RAW`; pins 2/7 drive U12 TPS7A0230 VIN/EN and C122. This does provide the intended independent USB-priority path to 3V_AO when BQ switching or a battery is unavailable. TPS2116 recommended VIN range is 1.6–5.5 V, and USB priority changes near a nominal 2.8 V AUX threshold. However, U19 is a 5 V fixed LDO fed from nominally 5 V USB: guaranteed 5.0 V regulation at a weak/low USB input is not established, and no actual MCU/I²C/pull-up startup load or U19 dropout corner is closed. TPS2116 accepts undervoltage well below 5 V, so this is a source/load qualification rather than evidence the mux cannot operate.

**Action:** Bound U19 output at the weakest permitted USB source, startup load and temperature; confirm U12 maintains 3V_AO and MCU/I²C startup margin. Record the low-input switchover/BOR behavior. Primary references: local `TPS7B84-Q1.pdf` operating/dropout data; local `TPS2116.pdf` §§6.3, 7.3.1 and 7.6.1.1. Active schematic references: `USB_PD` U19 and `Fuel_Gauge_Power` U20/U12.

### Candidate-only — BQ25792 POR hold, charge default and external ship-FET routing are directionally sound, but firmware/source permission remains a hard integration gate

The draft netlist shows Q101 pulling U4 ILIM_HIZ pin 17 low at POR through the REGN pull-up / default-off Q102 arrangement; Q100 separately keeps active-low CE pin 13 disabled by default. Q103 is the external ship FET, with U4 SDRV pin 24 to its gate, BAT_INT on its source pads and BAT_PACK on its drain pads; SW101 is in series with the physical pack-positive connector. This is consistent with an external series ship FET and hardware-off startup. For 1S, the BQ25792 SYS regulation maximum is 4.55 V at BAT=4.2 V, under U20’s 5.5 V input limit; the candidate’s 1S SYS notes do not expose a static rail-max conflict in the reviewed configuration.

The protection is not self-sufficient after startup: the candidate’s documented POR sample below 1.08 V caches the 100 mA external clamp. There is no proven re-sample on Q101 release. Raising current requires a host sequence that clears `EN_EXTILIM`, programs and reads back source-specific IINDPM, and manages reset/watchdog/source changes before release. The draft also has a concrete purchasing-field mismatch: R102 is displayed as 4.7 kΩ but its hidden MPN/LCSC fields still specify Yageo RC0603FR-07220RL / C107696 (220 Ω). Table 9-1 calls for 4.7 kΩ for the 1S / 750 kHz POR profile; 220 Ω is not a listed setting, so the assembled POR cell/frequency cannot be trusted. In addition, REG14 `SFET_PRESENT` resets to 0; TI says the ship-control fields, including `SDRV_CTRL`, are locked at 0 until firmware sets `SFET_PRESENT=1`. The sheet has no hardware strap for this bit, so electronic ship mode depends on firmware explicitly enabling and retaining this configuration before requesting ship. The DP/DM source-detection ports also remain unmapped to a source-selection mux, and a 100 mA USB-host bootstrap permission still needs enumeration policy. These candidate defects/gates do not describe the active BQ25895 circuit.

**Action:** Correct R102 MPN/LCSC, include `SFET_PRESENT=1` in startup configuration and verify it before shipping, then implement and verify watchdog/REG_RST, USB-source permission and charge-enable policy. Preserve default-off behavior through MCU reset. Primary references: local `BQ25792.pdf`, §§7, 9.3.4.3, 9.3.6, 9.3.12, 9.4; local `BQ25792` ILIM report `reports/bq25792-ilim-startup-review.md`. Candidate netlist refs: U4/Q100/Q101/Q102/Q103/SW101.

## What is currently supported

- The active TPS2116 pin mapping and net isolation are consistent with its priority mux function: USB_AUX_5V is VIN1/MODE, SYS_RAW is VIN2, and mux output alone feeds U12 VIN/EN. Latest integration evidence reports raw USB, AUX, SYS, mux output and PR1 as distinct domains.
- With BAT_PACK at 0 V, the TS5A3167 powered-off-isolation feature is intended for this case; the open concern is low nonzero BAT voltage and leakage/domain behavior, not a claim of a demonstrated absent-pack short.
- The candidate BQ25792 1S SYS maximum (4.55 V under the specified 1S test condition) is below TPS2116’s 5.5 V recommended input maximum. This does not replace transient or no-battery/charge-enabled system qualification.
- The active USB_PD/BQ25895 design remains 5/9 V only; the existing 11 V cutoff and 5–20 V redesign gate are already documented in the handover and are not repeated here as new findings.

## Evidence limits

No transient, load-step, battery-collapse, cold-start, USB compliance, MCU firmware or PCB/layout measurement was made. The latest active netlist evidence is the auxiliary-mux integration export; the candidate export was generated with the project KiCad 10.0.6 CLI. The BQ25792 candidate remains style-unapproved and integration-unapproved per its full-pin review record.
