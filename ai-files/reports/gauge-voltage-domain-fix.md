# Active gauge interface fix

U13/U16/U17 and their bypass capacitors now use3V_AO rather thanBAT_PACK. U21 BAT-powered TPS3839G33DBZR qualifies battery voltage and Q104 pulls shared active-low switch enable down only after supervisor reset recovery. R1261M pulls switches off by default; R1271M prevents gate retention/leakage from enabling them with an absent pack. C126 bypasses U21. MAX17048 measurement supply remainsBAT_PACK. Both power switches retain their series topology.

Threshold3.08V nominal (3.003–3.126V falling), recovery200ms typical after threshold+hysteresis; exact reset timing/collapse and cold gate drive remain prototype qualification gates. Manufacturer sources: TPS3839.pdf table7.5; 2N7002.pdf electrical characteristics; TS5A3167.pdf powered-off isolation and analog limits; MAX17048_MAX17049.pdf operating supply range.

Supervisor and gate pulldown add about4.35uA at4.2V typical, or~38mAh/year; this is not the complete board/pack storage current. R126 adds about3uA when AO powered and switches enabled. Physical disconnect still eliminates board draw.

Fresh netlist: preserved all unrelated physical pin groups, verified AO switch supply, shared IN/drain/pullup, supervisor reset/gate/pulldown, BAT supply/bypass and ground. ERC319 inherited root findings,0 in captured children. Preview rendered and inspected. Standard KiCadSOT23 model linked to reviewedTI DBZ footprint; individual symbol/footprint/model installed without library subfolders.

Remaining: cold-temperatureMOS margin, fastcollapse, no-battery/USB transition behavior and whole-system storage budget. No bench tests claimed. BOM113physicalrefs reconciled, U21LCSC field normalized toC485802.
