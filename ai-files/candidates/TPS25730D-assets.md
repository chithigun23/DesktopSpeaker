# TPS25730DREFR candidate assets

This is an isolated USB_PD child-sheet candidate. The active project schematic and shared symbol/footprint tables were not changed.

## Files

- `TPS25730D_USB_PD_candidate.kicad_sch` — wired candidate retaining the USB_PD sheet UUID, `U11` UUID and project hierarchy path.
- `TPS25730D_USB_PD_candidate.pdf` — KiCad 10.0.6 render for review.
- `TPS25730D_USB_PD_candidate.net` — exported physical pin netlist.
- `TPS25730D.kicad_sym` — standalone one-component TPS25730DREFR symbol.
- `TPS25730D.pretty/Texas_REF0038A_WQFN-38-2EP_6x4mm_P0.4.kicad_mod` — exact REF0038A package footprint copied from the official KiCad footprint library (package dimensions and exposed pads checked against TI package drawing).
- `fp-lib-table` — candidate-local footprint library mapping.
- `../datasheets/TPS25730.pdf`, `../datasheets/TPS25730_TRM.pdf`, `../datasheets/TPS25730EVM_Users_Guide.pdf` — TI primary references.

## Configuration and connection summary

- TPS25730DREFR (`U11`, LCSC C22438973) uses ADCIN1 code 0, ADCIN2 code 7, ADCIN3 code 0 and ADCIN4 code 1: 5 V minimum, 20 V maximum, 0 A operating, 3 A maximum requested current. The original TPS25730 datasheet's Tables 8-7/8-8 use code 6 for 20 V, conflicting with Table 8-5. The revised TPS25730EVM guide (Rev. A, Tables 2-8 and 2-10) explicitly uses code 7; code 7 is used here. Reconfirm against the selected silicon revision/EVM before production.
- TPS sink switch output is `VBUS_PD`; raw USB input is `USB_VBUS`. The integrated switch is not a continuous input-current regulator. Charger/load limits must follow the accepted contract (`ACTIVE_CONTRACT_PDO`/RDO) and separate charger input limiting.
- `U19` remains the raw-USB auxiliary LDO and exports `USB_AUX_5V`. C2 bypasses `VBUS`; C185 provides 10 µF nominal bypass from `VIN_3V3` to GND. `VIN_3V3` is held low through R12 for VBUS-powered dead-battery startup; TI guidance recommends grounding VIN_3V3 when unused. R13 provides the 10 kΩ `FAULT_IN` pull-up to `LDO_3V3`. Verify effective capacitance/voltage derating for CVIN_3V3 and the exact board startup behavior.
- The child exports `PDCTRL_SDA/SCL`, status ports and power rails, but contains no MCU hookup. Add powered-off I2C isolation or a reviewed sequencing strategy before connecting a separately powered MCU; confirm valid pull-up domains for open-drain statuses.
- C180 is a 33 µF polymer placeholder. The BQ25792 candidate sheet allocates 50 µF nominal ceramic across VBUS and PMID. Their total effective sink-bulk value, DC-bias/tolerance corner and maximum `cSnkBulkPd` must be coordinated; the 83 µF nominal sum does not establish compliance with TI's 47–100 µF effective recommendation.
- TI's recommended TVS2200 has a 28.35 V maximum clamp versus TPS25730's 28 V absolute maximum. Candidate notes preserve this as a physical release qualification; no over-absolute transient allowance is claimed.
- Exposed pad 39 is GND. Exposed drain pad 40 is individually no-connect, like drain pins 15 and 30, per TI bottom-side layout guidance. Pin groups expand to package pad numbers in the exported netlist.

## Provenance and open asset item

The symbol was authored from TI's TPS25730D pin/function and package tables. The footprint source is the official KiCad footprint-library `Texas_REF0038A_WQFN-38-2EP_6x4mm_P0.4` footprint (KiCad library change !3777). The exact TI `REF0038A.stp` STEP was acquired and linked to the candidate footprint at zero offset/rotation. KiCad top/bottom 3D renders verified pin-1 perimeter lead and exposed-pad orientation. The internal merged leadframe solid is a CAD simplification; use the model for mechanical visualization only and do not infer electrical connectivity from the solid topology. Details and measurement artifacts are in `REF0038A-model-inspection.md`. The polymer and ceramic capacitor MPNs remain unselected; verify effective capacitance, voltage rating and physical source stock when the shared cap budget is reviewed.
