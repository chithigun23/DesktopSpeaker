# BQ25792 VBUS/PMID capacitor sourcing review

Research snapshot: 2026-10-05. This is a sourcing recommendation only; active schematics, libraries, and BOM were not edited.

## Recommended part

Use Samsung Electro-Mechanics **CL32B106KBJNNNE**, LCSC **C138687**, for the shared five-cap bank (two VBUS, three PMID): 10 µF, ±10%, 50 V, X7R, 1210. The maker lists 3.20 × 2.50 × 2.50 mm nominal package dimensions and X7R operation from −55 to +125 °C. [Samsung product page](https://product.samsungsem.com/mlcc/CL32B106KBJNNN.do)

Samsung's public component library embeds a typical DC-bias curve measured at 25 °C, 1 Vrms, and 1 kHz. Interpolating its data at 21 V gives about 5.04 µF from a 10 µF nominal part. Applying initial capacitance tolerance of −10% and the X7R temperature bound of −15% gives an estimate of 3.86 µF per part. That estimates 7.72 µF across two VBUS parts and 11.57 µF across three PMID parts, exceeding the required 2 µF and 4 µF minima. The curve is typical design-reference data, not a guaranteed minimum; final temperature, aging, ripple, and lot margin still need qualification. Curve points and calculation are in [the extracted curve data](Samsung_CL32B106KBJNNN_DCBias_25C_1kHz.json); the raw official component-library snapshot is also retained under `ai-files/reports/`.

LCSC displayed 183,897 pieces, MOQ/multiple 1, and $0.1571 at 1+ when checked on 2026-10-05. Five pieces estimate to $0.7855 before shipping/tax. Stock and price are listing snapshots, not order-time guarantees. [LCSC C138687](https://www.lcsc.com/product-detail/C138687.html)

## Existing package assets

Reuse the project's `DesktopSpeaker:PD_C_1210` footprint and `PD_C_1210.step`. Their footprint geometry matches installed KiCad's standard `Capacitor_SMD:C_1210_3225Metric`; the STEP hash matches the installed official KiCad 1210 model exactly. FreeCAD 1.0.0 measured a 3.2 × 2.5 × 2.5 mm single-solid body matching Samsung's nominal body size. This is a generic standard 1210 model, not a Samsung-specific rendering.

## Price comparison

Murata **GRM32ER71H106KA12L**, LCSC **C77102**, is another exact 10 µF, 50 V, X7R, 1210 choice. The opened listing showed 48,910 stock, MOQ 5, and $0.3304 at 5+ (about $1.652 for five). Samsung is the lower-cost snapshot and has a smaller MOQ. [LCSC C77102](https://www.lcsc.com/product-detail/C77102.html)

The local TI BQ25792 datasheet, §10.2.2.2, uses two 10 µF VBUS and three 10 µF PMID capacitors. This review uses the requested 2 µF/4 µF effective-capacitance targets at 21 V.
