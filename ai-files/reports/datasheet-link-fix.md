# Datasheet link fix (2026-10-11)

Schematic Datasheet fields only (6 sheets: Amplifiers, Battery_Charger, Bluetooth_Power, Source_Select_ADC, USB_Audio, USB_PD). No wiring, net, position, PCB or reference changes. Not committed. PCB parity comes from the GUI "Update PCB from Schematic".

Downloads (LCSC datasheet CDN, PDF header and part number checked; series files are shared):
UNI_ROYAL_0402WGF_series (R100, R150), Yageo_AC0402FR_series (R101, R151), TDK_C2012X7R1H475KT0A0E (C2, C5), Murata_GRM155R71H473KE14D (C103, C110, C266), Samsung_CL05B682KB5NNNC (C268), Murata_GRM1555C1H103JE01D (C206-C211, and C226/C227 whose GRM1555C1H150JA01D is the same GRM155 C0G family, no separate file), HRE_CGA0402X7R474K160GT (C285-C288, C298-C301), FOJAN_FCC0402N330J500AT (C177, C178), KYX_K3A120002010 (Y170). C275 and Y200 already pointed at the correct existing files. Caveat: the KYX file is a short vendor sheet and the HRE file is in Chinese; the UNI-ROYAL file is the generic thick-film series sheet.

Field changes (ref, old -> new); "(none)" means the field was empty:
```
C268 (none) -> Samsung_CL05B682KB5NNNC.pdf
C266 (none) -> Murata_GRM155R71H473KE14D.pdf
C285 (none) -> HRE_CGA0402X7R474K160GT.pdf
C286 (none) -> HRE_CGA0402X7R474K160GT.pdf
C287 (none) -> HRE_CGA0402X7R474K160GT.pdf
C288 (none) -> HRE_CGA0402X7R474K160GT.pdf
C298 (none) -> HRE_CGA0402X7R474K160GT.pdf
C299 (none) -> HRE_CGA0402X7R474K160GT.pdf
C300 (none) -> HRE_CGA0402X7R474K160GT.pdf
C301 (none) -> HRE_CGA0402X7R474K160GT.pdf
C103 YAGEO_C107093_CC0603KRX7R9BB473.pdf -> Murata_GRM155R71H473KE14D.pdf
C110 CC0603KRX7R9BB473.pdf -> Murata_GRM155R71H473KE14D.pdf
R100 SAE_1RC0603F_series.pdf -> UNI_ROYAL_0402WGF_series.pdf
R101 SAE_1RC0603F_series.pdf -> Yageo_AC0402FR_series.pdf
C206 (none) -> Murata_GRM1555C1H103JE01D.pdf
C207 (none) -> Murata_GRM1555C1H103JE01D.pdf
C208 (none) -> Murata_GRM1555C1H103JE01D.pdf
C209 (none) -> Murata_GRM1555C1H103JE01D.pdf
C210 (none) -> Murata_GRM1555C1H103JE01D.pdf
C211 (none) -> Murata_GRM1555C1H103JE01D.pdf
C226 (none) -> Murata_GRM1555C1H103JE01D.pdf
C227 (none) -> Murata_GRM1555C1H103JE01D.pdf
C177 (none) -> FOJAN_FCC0402N330J500AT.pdf
C178 (none) -> FOJAN_FCC0402N330J500AT.pdf
Y170 (none) -> KYX_K3A120002010.pdf
C2 (none) -> TDK_C2012X7R1H475KT0A0E.pdf
C5 (none) -> TDK_C2012X7R1H475KT0A0E.pdf
R150 FOJAN_FRC0603_resistors.pdf -> UNI_ROYAL_0402WGF_series.pdf
R151 Yageo_AC0603FR-0791KL.pdf -> Yageo_AC0402FR_series.pdf
```

Checks (scratch copies): kicad-cli ERC 0 violations at default severity. netlist_equiv.py HEAD vs now: nets 311/311 and pins 1130/1130 identical, libparts identical; component differences are property fields only.

Also: ai-files/reports/mcu-pin-allocation.md line 8 corrected (VREF+ tied to VDDA, no C163/C164).

New untracked datasheets for the coordinator to commit: Panasonic_EEH-ZA_hybrid_polymer.pdf, YXC_YSX321SL_X322524576MOB4SI.pdf, plus the nine files above.
