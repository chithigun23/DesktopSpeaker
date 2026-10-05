# Existing L1 suitability envelope

2026-10-05; planning arithmetic, not physical qualification.

BQ25792 750 kHz requires 2.2 µH (TI section10.2.2.1). Current L1 Bourns SRN6045TA-2R2Y has ±30% initial inductance, DCR15mΩ maximum, Irms6A (40°C rise at maker conditions), Isat9.5A (30% inductance drop). Keep only as a provisional selection until total SYS+charge power is agreed.

Using Lmin1.54µH, nominal750kHz, SYS4.8V and input21V (20V+5%), ideal buck ripple is 3.21A peak-to-peak. TI provides nominal frequency only in this table; these are illustrative calculations, not oscillator/temperature/DC-bias worst-case guarantees.

| Average inductor current (SYS plus charge in buck mode) | Estimated RMS | Estimated peak |
|---|---|---|
| 4.0 A | 4.11 A | 5.60 A |
| 6.0 A | 6.07 A | 7.60 A |
| 8.0 A | 8.05 A | 9.60 A |

An 8A average load clearly exceeds the 6A thermal rating and reaches the maker saturation-current criterion. Even 6A average has ripple-related RMS above6A. Do not approve this inductor simply because programmed charging is only1A: SYS load also flows through it. The selected pack/driver/amplifier load is not yet specified, so the full-load choice is open. Inductance reduction under current further increases ripple.

At weak3.6V input boosted toSYS4.8V, an illustrative4A total output requires about5.93A mean input at90% efficiency, before ripple; that already approaches the6A thermal rating. Actual source-current policy should prevent that demand on a legacy1.5/2A USB source, reducing charging then audio power. No converter efficiency guarantee or battery runtime is inferred.

Sources: local TI BQ25792.pdf §10.2.2.1; Bourns_SRN6045TA.pdf electricaltable and temperature/saturation definitions. No active L1 change or PCB layout.
