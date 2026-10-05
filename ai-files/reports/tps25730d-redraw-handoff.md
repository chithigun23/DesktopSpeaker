# TPS25730D candidate redraw handoff

Files changed (only): `ai-files/candidates/TPS25730D_USB_PD_candidate.kicad_sch`, `ai-files/helpers/build_tps25730d_candidate.py`; regenerated outputs `TPS25730D_USB_PD_candidate.{net,pdf}` and `-page.png`. Symbol, footprint and DesktopSpeaker-kicad/ are untouched.

## Changes
- Layout section of the builder rewritten (explicit 1.27 mm-grid placement, no 50 mm shift hack). Inputs/bidirectional ports left (USB_VBUS, USB_CC1/2, PDCTRL_SDA/SCL); outputs right (VBUS_PD, PD_CAP_MIS, PD_SINK_EN, PD_PLUG_EVENT, PD_PLUG_FLIP, PD_DBG_ACC, USB_AUX_5V).
- Direct orthogonal wires, no crossings; GND symbols all point down; ADC1/ADC3 GND placed directly on pins; IC ref/value centred under body (U19 text sits below its GND strap); passive/diode/connector text to the right.
- Remote sections joined by matching local labels (each section <=1 label): LDO_3V3 (names shortened from PD_LDO_3V3), LDO_1V5, VIN_LOW, USB_CC1/2, USB_VBUS (U19 section), J4 labels. Local label names changed (net names only).
- Pin-text size inside U11 left unchanged (0.5 mm font, set in the shared symbol file I do not own): small at overview scale. Stacked pin numbers are long strings.

## Connectivity proof
The committed draft (HEAD) was electrically broken (CC1 shorted to SDA/SCL/J4; PPHV shorted to CAP_MIS; ADC1/3/4 and reserved pins floating; divider midpoint unlabelled) so it cannot be the reference. Reference used: `TPS25730D_before_readability.net` (the intended pre-draft netlist). Physical (ref,pin) groups, stacked pads expanded, power-symbol pins ignored: after redraw is identical except the intentionally retired C180 (VBUS_PD group now U11.20-22 only; GND group lacks C180.2). Checks: U11.2/5 (ADC1/3) GND; U11.3 on LDO_3V3 with U11.1; U11.7+R10.2+R11.1; U11.26/27/36 GND; 15/30/40 NC; U11.6/10/13/19/37 now port-wired singletons (previously unconnected-draft, same single-pin groups). Netlists: before `ai-files/candidates/TPS25730D_before_readability.net`, after `TPS25730D_USB_PD_candidate.net`.
Note: `TPS25730D_after_readability_netgroups.json` (not mine) is stale; I did not modify it.

## ERC (kicad-cli 10.0.6, unsuppressed; 74 total standalone-sheet findings)
- 12 pin_not_connected errors: all hierarchical ports reported as "root sheet, no parent" (expected for isolated candidate).
- 3 power_pin_not_driven errors: GND symbol at C2 (#PWR01), U11 VBUS_IN, U11 VIN_3V3 (no PWR_FLAG / output driver in isolated sheet; they are driven by parent USB_VBUS and by the ground-low strap respectively).
- 7 isolated_pin_label warnings: 6 single-pin ports (status outputs, VBUS_PD) and J4 label 3V_AO (no source on sheet).
- 35 lib_symbol_issues + 17 footprint_link_issues: libraries not configured for the isolated candidate (project tables not loaded).
- No wire/endpoint/off-grid/dangling findings after moving ports onto the 1.27 mm grid.

## Electrical flags (datasheet SLVSGP9, nothing silently changed)
1. RESERVED 26/27/36: datasheet "tie to ground or LDO_3V3"; HEAD draft left them floating; I grounded them (as in the earlier intended netlist). Confirm.
2. ADCIN2 code 7 (tie to LDO_3V3, Table 8-1 OK) conflicts with datasheet Tables 8-7/8-8 (code 6) as already noted in TPS25730D-assets.md; relies on EVM guide Rev A. ADCIN1/3 GND = code 0, ADCIN4 200k/10k = ratio 0.0476, code 1: consistent with the stated 5-20 V/0 A/3 A config.
3. No I2C pull-ups on SDA/SCL (datasheet: tie through resistors). Open-drain outputs CAP_MIS, SINK_EN, PLUG_EVENT, PLUG_FLIP, DBG_ACC need pull-ups in the consumer domain; none on this sheet. J4 service header has 3V_AO label but nothing sources it here.
4. VIN_3V3 permanently low (R12 100k) so the device always runs from the VBUS LDO; datasheet describes VIN_3V3 as the normal supply and the VBUS LDO as dead-battery mode, and the dead-battery flag cleared over I2C never switches to VIN_3V3. Unverified: LDO capability/limits and thermal over 5-20 V with external loads (R10 divider, R13, any pull-ups on LDO_3V3).
5. FAULT_IN pulled to LDO_3V3 via 10k: OK per pin description (1 = no fault); nothing drives it, so no external fault input.
6. Capacitors vs Recommended Capacitance: CVBUS 1 uF/50 V (1-10 uF, OK); CC 330 pF (200-480 pF, OK); CLDO_3V3 10 uF/10 V (5-25 uF; DC-bias derating unverified); CLDO_1V5 10 uF/10 V (4.5-12 uF; nominal 10 uF may exceed 12 uF at low bias or tolerance high end, verify effective value); CVIN_3V3 10 uF/10 V (min 5 uF, OK). No PPHV bulk capacitor (C180 retired; bulk sits on BQ25792 sheet, see cSnkBulkPd note in TPS25730D-assets.md).
7. DRAIN 15/30/40 left NC per TI layout guidance; GND exposed pad 39 on the GND stack.
8. TVS2200 28.35 V clamp vs 28 V abs max on VBUS/PPHV pins: already noted open item.

## Unresolved
- U11 pin text is tiny; improving it needs a shared-symbol edit (not in scope).
- Several pin groups share one label text per stacked-pad name; GND pin number string is unreadable at print scale.
- Not committed.
