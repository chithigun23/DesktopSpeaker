# Independent electrical review: TPS25730D and BQ25792 candidate sheets

Date: 2026-10-05. This was a read-only review. The only file written is this report. Scope: `ai-files/candidates/TPS25730D_USB_PD_candidate.kicad_sch` and `ai-files/candidates/Battery_Charger.kicad_sch`. I checked the electrical design against the netlists exported by kicad-cli 10.0.6 and against the local datasheets. I did not review drawing style. Sources: TPS25730 SLVSGP9, TPS25730EVM SLVUCP4A Rev A (Aug 2025), BQ25792 SLUSDG1C, TVS2200, TPS7B84-Q1, CSD17579Q3A, Nexperia 2N7002, ESDA25L, and the Samsung DC-bias data in `reports/samsung-mlcc-dcbias-estimates.json`.

Pin mapping: all 29 BQ25792 RQM pins and all 38+2 TPS25730D REF pins match the datasheet pin tables. No pin is wired to the wrong function. Both bootstrap capacitors are wired correctly (BTST1-SW1 and BTST2-SW2), and L1 runs from SW1 to SW2. Every VBUS and VBUS_IN pin is shorted together, as the TPS ROC footnote requires.

## A. Must fix before integration (ranked)

| # | Sev | Sheet | Finding | Concrete fix |
|---|---|---|---|---|
| 1 | High | root | Integration breaks if the files are swapped as-is. The active USB_PD sheet block has a `GND` input pin, but the candidate has no GND port (it uses the global GND symbol). New candidate ports have no sheet pins. | Apply the port list in section C. Delete the USB_PD `GND` sheet pin. Add PWR_FLAGs on root `USB_VBUS`, on `GND`, and on charger `PACK_RAW` or `BAT_PACK`, because J1 and J5 are passive. Also add one on `VBUS_PD` unless the PPHV pin type is power-out. |
| 2 | High | PD | **PDCTRL_SDA/SCL float.** There are no pull-ups. J4.1 carries a *local* label `3V_AO`, which connects to nothing. TI requires a pull-up on each line, or a tie to GND if unused. Floating I2C inputs invite spurious activity. | Add R14 and R15, 10k 1%, from PDCTRL_SDA and PDCTRL_SCL to **LDO_3V3**. Rename the J4.1 label to LDO_3V3. Do **not** pull up to 3V_AO: that rail is battery-backed and would back-power an unpowered TPS25730 and leak in standby. |
| 3 | Med-High | PD | The open-drain status outputs have no pull-ups. | For the outputs that will be used, add R16 (PLUG_EVENT) and R17 (SINK_EN), 100k to LDO_3V3, about 34 µA each when asserted. Leave CAP_MIS, PLUG_FLIP and DBG_ACC unconnected and delete their ports. With operating current set to 0 A, CAP_MIS never toggles (§8.3.13). |
| 4 | Med-High | PD | **The Schottky that TI recommends is missing.** §8.5 asks for a Schottky from VBUS to GND to absorb ground current from cable inductance on sudden disconnect. | Add **D7**: a 40 V / 1 A Schottky (B5819W SOD-123 class; verify LCSC part and leakage), cathode on USB_VBUS and anode on GND, placed at the U11 VBUS_IN/GND pins. |
| 5 | Med | PD | **CVBUS is marginal.** C2 (1 µF/50 V 1210, no MPN) plus C184 (1 µF/50 V 0805) give only about 1 µF effective at 20 V. TI's minimum is 1 µF, nominal 4.7 µF, and note 3 says use the high side for fast-disable. | Change C2 to **4.7 µF/50 V X7R 1210** (e.g. GRM32ER71H475KA88L; verify) and keep C184. That gives about 3 µF effective at 20 V and stays under the 10 µF maximum at 5 V. |
| 6 | Med | PD | **CLDO_3V3 is marginal.** C6 is CL21B106KPQNNNE, which retains about 68% at 3.4 V (6.8 µF typ). After -10% tolerance and -15% temperature it is about 5.2 µF, against a **5 µF minimum** (window 5–25 µF). | Change C6 to **22 µF/10 V X7R 0805, GRM21BZ71A226ME15L** (already in use for SYS). That gives over 10 µF effective and stays under 25 µF. CLDO_1V5 (C181) is fine: about 9.4 µF typ at 1.5 V, at most about 10.4 µF against the 4.5–12 µF window. |
| 7 | Med | CHG | **SYS has no 0.1 µF capacitor.** TI layout priority #1 (§12.1) and the pin table call for one. | Add **C115, 100 nF 50 V X7R 0402**, at U4.25 SYS/GND on the top layer. |
| 8 | Med | CHG | **MPN does not match footprint.** C113/C114 carry CL21B104KBCNNNC (LCSC C1711), which is an **0805** part, but the footprint is PD_C_0603. TI also wants a small 0402/0201 part closest to the pin. | Use one 0402 100 nF 50 V X7R part for C113, C114 and C115 (e.g. GRM155R71H104KE14D; verify stock), with a 0402 footprint. |
| 9 | Low-Med | PD | **RESERVED pin 36** is hard-grounded. That follows the datasheet, but the EVM Rev A2 schematic names pin 36 **FAULT_OUT** and routes it to an LED driver. | Tie pin 36 to GND through **10k (R18)**. This still meets "tie to ground" and limits current if newer firmware drives it. Keep pins 26/27 on GND. |
| 10 | Low-Med | CHG | **2N7002 gate drive from 3.0 V.** VGS(th) max is 2.5 V at 25 °C and 2.75 V at -55 °C, and RDS(on) is only specified at ≥4.5 V. Q100 must pull CE below VIL 0.4 V against R103 10k from REGN (0.5 mA). Q102 sinks only 50 µA (R110). | Change **R103 from 10k to 100k**. CE VIH is 1.3 V and VIL 0.4 V, so CE stays defined and the sink drops to 50 µA. Optionally change Q100 and Q102 to a logic-level NMOS (AO3400A class, VGS(th) ≤1.45 V, RDS(on) specified at 2.5 V). Q101 (gate at REGN, ≥4.6 V) is fine as a 2N7002. |

## B. Decisions on the questions asked

**TPS25730D straps.** Keep **ADCIN2 code 7**, tied directly to LDO_3V3 (divider ratio 1.0, inside the code-7 window 0.9061–1.0). Code 7 is the 20 V code in the normative tables: Table 8-3 (straps and I2C address) and Table 8-5 (only codes 1/3/5/7 are defined). The EVM guide Rev A, Tables 2-8 and 2-10, uses code 7 for "5–20 V, 3 A". Code 6 appears only in the example Tables 8-7/8-8 and is not a defined maximum-voltage code, so do not use it. The other straps decode as follows:
- ADCIN1 = GND: code 0 (5 V minimum).
- ADCIN3 = GND: code 0.
- ADCIN4 = 10k/(200k+10k) = 0.0476: code 1 (window 0.0229–0.0722, robust with 1% parts).

The result is **5–20 V, 0 A operating, 3 A maximum**, at I2C address 0x20. This is right for maximum source compatibility: minimum power is 0, so every source is accepted, and firmware reads ACTIVE_CONTRACT_RDO (0x35) before granting current. Bench-verify which PDO gets selected (expected: the highest voltage in range). Dead-battery mode is AlwaysEnableSink. The EVM negotiates from straps alone, with no host.

**VIN_3V3 via R12.** Correct for low standby. The EVM does the same: R36 10k to GND, pull-up R30 not populated. Feeding VIN_3V3 from 3V_AO would add a 56 µA sleep current with no VBUS present and would sit at the 3.0 V ROC minimum. Running from the VBUS LDO limits the external LDO_3V3 load to **5 mA** (ROC). Present load is about 16 µA (ADCIN4 divider), and fixes 2 and 3 add at most about 0.8 mA, which is acceptable. Firmware must never try to move the supply to VIN_3V3 or clear the dead-battery flag. The TRM exposes no such command anyway. The C185 10 µF capacitor on a grounded pin is harmless and kept for EVM parity.

**FAULT_IN.** R13 10k to LDO_3V3 matches EVM R21, with 1 meaning no fault. That is fine. Optional later: an MCU open-drain pulldown to force a port disconnect.

**TVS2200.** Keep TVS2200 for 20 V operation.
- It is TI's named pairing (§6.1.1 note 4).
- Its 22 V standoff sits above 20 V + 5%, and its breakdown (24.6–27.6 V) sits between the 22 V ROC and the 28 V absolute maximum.
- Maximum clamp is 28.0 V at 40 A/27 °C. The 28.35 V figure only applies at 35 A, 125 °C, pre-biased at 22 V.

**Do not add a series element.** A ferrite, PTC or eFuse in a 3 A path adds loss and inductive overshoot, and does nothing for ESD edges. A conventional SMBJ/SMAJ22A clamps near 35 V, which is worse. A TVS with lower standoff (18 V class) is not compatible with a 21 V source. Do these instead:
- Place D6 at J1 with the shortest return.
- Add D7 (fix 4).
- Make the measured U11 pin voltage a release gate.

**Optional decision D1, for the user:** cap the maximum at **15 V**: ADCIN2 tied to LDO_1V5 gives code 5, an explicit Table 8-1 option.
- Under PD power rules, every source above 27 W offers 15 V, so a 15 V sink still reaches 45 W.
- It is more efficient for a 1S buck, cuts U19 dissipation, and leaves 6 V of headroom to the 22 V ROC.
- It allows an 18 V-standoff flat-clamp TVS (TVS1800 class; verify clamp ≤24 V).

This is the only way to get real margin below 28 V. It departs from the user's 5/9/15/20 V decision, so it is not applied here.

**BQ25792 capacitors** (effective minima from the datasheet ROC: VBUS 2, PMID 4, SYS 6, BAT 3 µF):
- VBUS: 2×10 µF/50 V 1210 + 0.1 µF matches TI; about 7.7 µF effective at 21 V. OK.
- PMID: 3×10 µF + 0.1 µF matches TI; about 11.6 µF effective. OK.
- SYS: 3×22 µF/10 V 0805 against TI's 5×10 µF + 0.1 µF. Effective capacitance at 4.2 V is comparable (about 30 µF typ). A 10 V rating is fine for 1S. Add the missing 0.1 µF (fix 7). A 4th 22 µF is optional for audio load steps.
- BAT: 1×22 µF (C106), about 11 µF typ, which meets 3 µF effective. TI shows 2×10 µF; a second is optional.
- REGN: 2×10 µF against TI's 4.7 µF/10 V. Harmless, but C109 can be left unpopulated (later).
- VAC note 1 (2.2 µF + 0.1 µF for >15 V hot-plug) does not apply. VAC1/2 tie to VBUS, which only ever rises through the TPS25730 PPHV soft-start (3.3 V/ms), and PD sources start at 5 V.
- Total bulk on PPHV/VBUS_PD is about 50 µF nominal, at most about 69 µF in the worst case, below the 100 µF cSnkBulkPd limit.

**SFET_PRESENT cold start.** The datasheet resolves this; no hardware change is needed.
- REG14 says SFET_PRESENT=0 locks SDRV_CTRL=00.
- §9.3.12 defines SDRV_CTRL=00 (POR) as IDLE: "the external ship FET is fully on". The SDRV pin text says the FET "is always turned on when the ship mode is disabled".
- So SFET_PRESENT=0 only disables ship and shutdown control. It does not hold Q103 off.

**Q103 orientation is correct.**
- Source is on BAT_INT and drain on BAT_PACK, so the body diode conducts BAT_INT to pack and blocks pack to SYS.
- SDRV is referenced to BAT (the source), with SDRV-BAT ≤6 V. VGS is about 5 V, giving ≤14.2 mΩ.

**Pack-only start.**
- The chip runs from BATP through R112 from the pack side. Quiescent and shutdown currents are specified at BATP in ship/shutdown with the SFET off, and VBAT_UVLOZ is 3.4 V in ship mode and 2.6 V in normal mode.
- At POR, SDRV turns Q103 on through its 100 nA charge pump. Qg is 5.3–6.9 nC, so turn-on takes about 70 ms, which also gives a soft SYS inrush.
- SYS then supplies 3V_AO through U20 and U12.

This needs no QON press. Fallback: an adapter powers the chip from VBUS, and the MCU boots from USB_AUX_5V even with the converter in HIZ, so there is no bootstrap deadlock. Bench-verify that the chip powers up from BATP with BAT at 0 V.

Layout and part rules for Q103 and the standby modes:
- **Do not add a gate pull-down.** Any resistor under about 50 MΩ overwhelms the 100 nA drive. IGSS is ≤100 nA at 20 V, so keep the gate node clean.
- Ship mode (11/16 µA at BATP) can be exited with QON, an adapter or I2C.
- Shutdown mode (0.5 µA) **cannot be exited with QON**, only by an adapter, so do not use it for a button-wake product.

**ILIM_HIZ and EN_EXTILIM.** The gate works and fails safe. Q101 holds ILIM_HIZ below 0.75 V through POR, so the ADC caches a 100 mA clamp. If firmware never clears EN_EXTILIM, the charger runs at 100 mA or less. REG_RST re-arms EN_EXTILIM. R108/R109 (about 1.79 V on release, above the 1 V resume threshold) only needs to stay above 1 V.

Optional simplification (later): feed the divider straight from CHG_SYS_ENABLE (R108 100k from the port, R109 150k to GND, about 1.8 V at 3.0 V; 0 V when the MCU is in reset) and delete Q101, Q102, R110 and R111.

**D+/D- protection.** The BQ D+/D- abs max is 6 V. CHG_DP_RAW and CHG_DM_RAW are bare ports, and root J1 DP/DN and the root ESD part D1 (TPD2E2U06) are all unconnected. For now, leave the BQ D+/D- unconnected (no root net) and set AUTO_INDET_EN=0 (HVDCP_EN is already 0 at POR). If BC1.2 is wanted later, route through an analog switch shared with PCM2902C and keep D1 at the connector. A 5.5 V ESD diode does not protect against a short to 20 V VBUS.

**Other items checked and found OK:**
- CE never floats: it is pulled to REGN, and is 0 V only when REGN is off with no VBUS.
- TS: 5.23k/30.1k matches TI's 5.24k/30.31k. A missing NTC reads cold, so charging is suspended (safe).
- PROG: 4.7k 1% selects 1S at 750 kHz with 2.2 µH.
- L1: SRN6045TA-2R2Y, Isat 9.5 A, Irms 6 A.
- ACDRV1/2 on GND and VAC on VBUS are both allowed.
- STAT is unconnected (open drain, no current).
- INT has 10k to 3V_AO, as TI recommends (not REGN).
- BQ SCL/SDA pull-ups exist at system level: R120/R121 4.7k to 3V_AO on the CTRL bus in Fuel_Gauge_Power.
- VAC_OVP POR default is 26 V, fine for 20 V.
- BATP has 100R, as TI specifies.
- U19 TPS7B8450 pinout is correct (IN 8, EN 7, OUT 1, GND 5): 40 V input, 150 mA, C5 4.7 µF/50 V meets the 2.2 µF minimum. NC pins 3, 4 and 6 can go to GND for thermal relief.
- ESDA25L on CC: 24 V standoff survives a CC short to 20 V VBUS. 330 pF plus about 50 pF ESD capacitance is within 200–480 pF.

**Standby, battery only.** Ship mode draws BQ 11–16 µA at BATP. The TPS25730, U19 and the TVS are 0 because they only see VBUS. Q103 IDSS is ≤1 µA. Note that the gauge parts U5 and U21 on BAT_PACK still draw from the pack in ship mode (see the gauge isolation proposal). In IDLE with SYS up, the BQ adds 17–24 µA (ADC off). R107/R111 cost 30 µA each only while their enables are high, which firmware avoids in battery standby.

## C. Root-sheet interface needed to replace the children

Current root sheet pins come from `DesktopSpeaker.kicad_sch`. Existing root nets are `/USB_VBUS`, `/USB_CC1/2`, `/USB_PD/VBUS_PD`, `/USB_PD/USB_AUX_5V`, `/SYS_RAW`, `/Fuel_Gauge_Power/BAT_PACK`, `/CTRL_SCL`, `/CTRL_SDA`, `/3V_AO`, `/CHG_ENABLE` and `/CHG_INT`.

| Sheet | Pin | Type (child) | Root action |
|---|---|---|---|
| USB_PD | USB_VBUS | input | keep; J1 VBUS; add PWR_FLAG |
| USB_PD | USB_CC1, USB_CC2 | input (recommend bidirectional) | keep; J1 A5/B5 |
| USB_PD | VBUS_PD | output | keep; to Battery_Charger VBUS_PD |
| USB_PD | USB_AUX_5V | output | keep; to Fuel_Gauge_Power USB_AUX_5V (U20 VIN1, R124) |
| USB_PD | GND | (none in child) | **delete sheet pin** |
| USB_PD | PDCTRL_SDA, PDCTRL_SCL | bidirectional | **add**; no-connect until MCU authorized. Later: a dedicated STM32 I2C (FT pins, MCU powered whenever VBUS is present) or an NMOS isolator (gate = LDO_3V3) if shared with CTRL. Address 0x20 does not clash with BQ 0x6B or MAX17048 0x36. |
| USB_PD | PD_PLUG_EVENT, PD_SINK_EN | output | **add**; no-connect for now |
| USB_PD | PD_CAP_MIS, PD_PLUG_FLIP, PD_DBG_ACC | output | recommend deleting from the child (fix 3); otherwise add with no-connect |
| Battery_Charger | VBUS_PD (in), SYS_RAW (out), BAT_PACK (bidir) | as shown | keep; SYS_RAW goes to Fuel_Gauge, Bluetooth and Logic (all inputs). BAT_PACK is now the pack side of Q103 after SW101, which is still correct for the gauge VDD/sense. |
| Battery_Charger | CHG_SCL, CHG_SDA (bidir) | as shown | keep on /CTRL_SCL and /CTRL_SDA with GAUGE_SCL/SDA (pull-ups in the gauge sheet) |
| Battery_Charger | CHG_VIO_3V0 (in) | as shown | keep, tied to /3V_AO |
| Battery_Charger | CHG_ENABLE (in), CHG_INT (out) | as shown | keep. There is no root driver yet; R107 pulls down in the child, so it is safe unconnected. |
| Battery_Charger | CHG_SYS_ENABLE (in) | input | **add**; unconnected is safe (R111 pull-down holds HIZ) |
| Battery_Charger | CHG_DP_RAW, CHG_DM_RAW | bidirectional | **add with no-connect, or drop the ports for now** (see D+/D- above) |

Fuel_Gauge_Power, Bluetooth_Power and Logic_Audio_Power need no changes: their ports (SYS_RAW, BAT_PACK, USB_AUX_5V, GAUGE_SCL/SDA, 3V_AO) keep the same names and directions.

Reference designators do not collide with the remaining sheets. The proposed new references D7, C115 and R14–R18 are free once the old USB_PD sheet is gone.

Integration housekeeping:
- Move the `TPS25730D:` footprint (TPS25730D.pretty) and the candidate-folder symbols and footprints (BQ25792, CSD17579Q3A) into the shared `kicad-library` folders, one file each, with no new library nicknames (AGENTS rule).
- Re-annotate the copied child-sheet instances so the existing references are kept.

## D. Qualify later (not blocking capture)

1. Measure the TVS2200 and U11 VBUS pin waveforms during ESD, hot-plug and unplug at 20 V, and confirm they stay ≤28 V. Also check the 22 V ROC headroom during 5→20 V transitions.
2. On the EVM or prototype: PDO selection, AlwaysEnableSink at 5 V, the 5 mA dead-battery LDO_3V3 budget, and pin-36 behavior.
3. BQ25792: POR from BATP with BAT at 0 V, Q103 turn-on time and inrush, QON wake from ship mode, and the EN_EXTILIM/IINDPM write order before release.
4. Fill in missing MPN/LCSC fields: C2, C182, C183, R10, D5, D6, U11 (C22438973), U4 (C2862876), L1, Q100, Q103, J5, SW100 and SW101. Check stock and price; the BOM subtotal stays partial.
5. Optional simplifications: drive ILIM_HIZ directly from the MCU, run CE as open-drain from the MCU (removes Q100/R107, polarity becomes active-low), and route a QON sense line to the MCU so the button is visible.
