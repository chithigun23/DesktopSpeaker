# Pack, J5 connector, SW100/SW101 options - 2026-10-06

Research only; BOM and schematics unchanged. Only ~7 web lookups were used; prices/stock/LCSC numbers were NOT retrieved and are marked UNVERIFIED. Re-check before ordering.

## Basis
- Plan s2: user selected protected 1S ~10 Ah pack with NTC; geometry, discharge/charge rating and NTC curve open. Charger BQ25792 (5-20 V PD), J5 = 3 contacts PACK+, TS/NTC, GND; 103AT-2 (10k, B25/50 = 3435 K nominal for the Semitec 103AT-2 family; 103AT-2 also quoted as 3435 +/-1%).
- Cabinet allocation for pack: about 140 x 65 x 20 mm (mechanical-fit report).
- Peak load ASSUMPTION (no amp/driver/rail data in repo): 2 x TAS5825M-class at ~20 W/ch bursts + woofer ~20-30 W = ~50-60 W electrical peak output, ~60-70 W input at ~88% efficiency. At a 3.3 V sagging cell (if PVDD is boosted from the battery) that is ~18-20 A for short bursts; music average is typically 1/8 to 1/4 of peak, i.e. ~2-4 A. If instead amps run from a 12-20 V boost rail the battery-side numbers are the same. Design target: 10 A continuous, 20 A for <100 ms bursts; or firmware/amp limiting so the battery never sees more than the pack PCM allows (see risk).

## 1) Pack options
| Option | Cell/pack | Size | NTC / connector | Ratings | Notes |
|---|---|---|---|---|---|
| A (lead) LP1260100 "10000 mAh 1S1P PCM" (LiPol Battery Co. generic; sold by resellers, e.g. Soldered, Electrokit (JST-PH), Videotronics) | 3.7 V 10 Ah LiPo, 1260100 pouch | 12 x 60 x 110 mm, ~200 g | 10k 1% B3435 (matches 103AT-2 B-value), JST PHR-3 (2.0 mm PH, 3 pos) per listing | Continuous/peak discharge and PCM trip NOT stated in listings; typical for this class 1C-2C (10-20 A max) with PCM trip ~10-15 A. Max charge 0.5C-1C typical = 5 A; assume 5 A max | Price/stock UNVERIFIED (non-LCSC, ~USD 25-45 typical). Request datasheet; pouch 12 mm thick exceeds the 20 mm slot only if stacked. Fits 140x65x20 allocation with margin (110x60x12) |
| B Generic 3.7 V 10 Ah 1260110/ 123x73x8 pouch packs (othoba, eBay, AliExpress) | LiPo pouch | 100x60x11 up to 123x73x8 | NTC / connector varies, often 2-wire without NTC | Usually 1C, unverified | Quality/protection unverifiable; avoid for a product, ok for prototype only if NTC and PCM confirmed |
| C Build: 2P 21700 (2 x 5 Ah, e.g. Samsung 50S / Molicel P50B) in dual holder + 1S 2P PCM/NTC board | 1S2P cylindrical | ~2 x 21 mm dia x 70 mm, ~145 g | add own 10k B3435 NTC bonded to cells, JST-PH harness | 50S 25 A cont/cell, Molicel P50B 35 A/cell; 2P gives 50-70 A cell capability, limit set by PCM (choose 15-30 A) | Best for audio peaks and cycle life; fallback only if a ready pack with proven >=10 A rating is unavailable. Requires own protection design, holder (Keystone), cert burden. 18650 3.5 Ah x3P = 10.5 Ah also possible (3P 18650 holder), ~20x 54x65 mm |

Recommendation: Option A for prototype/first build with a datasheet request that states (a) PCM overcurrent trip >= 15 A and continuous >= 5 A (b) NTC curve 103AT-2 / B3435 (c) charge limit 5 A. If supplier cannot state discharge rating >= 10 A, use Option C (2P 21700 or a power-rated cell pack) since pouch packs at 1C-2C will sag and trip on bass bursts. Firmware needs a battery-current-aware loudness limiter either way.

NTC note: 103AT-2 vs "10k B3435" are the same family (Semitec 103AT-2 = 10 kOhm at 25 C, B25/50 3435 K); a B3380 pack NTC differs by ~0.5-1 C error at 0-45 C (acceptable for charge window, but program ITS/JEITA thresholds from the actual curve). Never accept a pack without a stated curve.

## Charge current limit and IINLIM budget
- Max longevity: <=0.5C = 5 A absolute; recommended default 0.2C-0.3C = 2-3 A, with a reduced-rate or "gentle" mode of 0.1C = 1 A for plug-in use. With ICHG programmed in the BQ25792 at 1 A (typical) up to 3 A.
- 5 V / 2 A adapter (IINLIM <= ~1.5-1.77 A given the 220 ohm ILIM clamp; 10 W max): charge power Pchg = Vbat x Ichg / 0.9 = ~4.2 W at 1 A and 3.8 V = 0.85 A input at 5 V. Leaves ~0.7-0.9 A (~4 W) for the system; audio bursts then draw from the pack (supplement) or require charge to be throttled. Recommend 0.5-1 A charge, audio priority, charge current reduced first (matches the existing policy).
- 9 V/12 V/15 V/20 V PD (>=27 W): 2-3 A charge is available together with ~10 W of audio. 0.5C (5 A, ~20 W) needs a >=30-45 W PD source and is not recommended as default.

## 2) J5 matching 3-pin board connector
| Option | Part | Rating | LCSC | Notes |
|---|---|---|---|---|
| A (lead, matches Option A pack) | JST PH 2.0 mm 3 pos header: S3B-PH-K-S (right angle) or B3B-PH-K-S (vertical), mates PHR-3 | 2 A per contact (JST spec) | LCSC numbers UNVERIFIED (JST PH headers are carried on LCSC/JLCPCB) | PH is only 2 A: PACK+ pin limited to 2 A continuous, not 10+ A. Not adequate for audio peaks if the full load passes through J5 |
| B JST XH 2.5 mm 3 pos (B3B-XH-A / S3B-XH-A) | 3 A per contact | UNVERIFIED | Still below peak; mating pack harness would differ (XH) |
| C Power-rated: JST VH 3.96 mm 3 pos (B3P-VH) or Molex Micro-Fit 3.0 (43650-0319 / 43045) or Molex Mini-Fit Jr; signal NTC pin on a separate 2-pin PH | 10 A (VH), 8.5 A (Micro-Fit 3.0) | UNVERIFIED | Use if pack current wiring is on J5. Alternatively keep PH-3 for PACK+/NTC/GND only for low-current charge/sense and run a separate 2-wire XT30/XT60 (XT30 PW 15 A) for discharge |
Recommendation: Because the user specifies a single 3-contact connector for PACK+, TS, GND with peaks around 15-20 A, a PH/XH connector (2-3 A per pin) is inadequate; use an XT30(2+2)-style or Micro-Fit 3.0 3-pin (8.5 A, derate) with tinned 18-20 AWG leads, or limit peak current <=2 A (not suitable). Decision needed on J5 type; the pack choice (PHR-3 harness) dictates a PH header only for a low-power system.

## 3) SW101 pack-positive disconnect, SW100 QON
SW101 (series in PACK+; needs >=15 A DC, contact resistance <=10 mOhm, mounts on panel):
| Option | Part | Rating | Notes |
|---|---|---|---|
| A E-Switch R6ABLKBLKFF rocker SPST (digikey), cutout 19.2 x 6.65 mm | 10 A @125 VAC (DC rating lower, ~6-10 A at 12-30 VDC: verify) | Not LCSC; quick-connect 4.7 mm tabs |
| B CWSB11AAF (773grp listing) rocker SPST | 6 A @250 VAC | below peak; not recommended |
| C Slide-switch DPDT paralleled or marine-grade toggle (e.g. C&K / NKK / Nidec) 10-16 A DC | 10-16 A | pick a DC-rated switch; alternatively NKK AS series. No LCSC number verified |
Recommendation: DC-rated rocker or toggle, >=10 A DC continuous with paralleled contacts if dual-pole, quick-connect or soldered. A mechanical switch in a 20 A-peak path is the weak link; the preferable alternative is to keep the existing ship FET (Q103, BQ25792 BATFET ship mode) and use SW101 only as a hardware service/transport disconnect rated >=10 A, or replace with a slide switch for logic use (<1 A) driving the charger's ship mode and leave the high-current path unswitched.

SW100 (QON, momentary): TE/WEC 1977066-1 (listed on Digikey as WEC 1977066-1; SPST-NO, 50 mA @12 V, IP67 sealed tactile; LCSC C2972219 in project BOM -- the number could not be confirmed online here). Current rating is adequate (QON is a ~3-5 V logic input with <1 mA). Alternatives (any 6x6 SMD tactile, e.g. Alps SKRPACE010, XKB TS-1187A-B-A-B, C318938; numbers UNVERIFIED). Recommend keeping 1977066-1 if panel/IP rating required; otherwise TS-1187A for cost.

## Open items for the user
1. Decide whether pack connector J5 carries discharge current. 2. Obtain datasheet: PCM trip, continuous/peak discharge, NTC curve for the chosen pack. 3. Verify LCSC stock/prices for every part above (all UNVERIFIED). 4. Define audio peak power (driver choice) to confirm the 15-20 A assumption.

Sources: LP1260100 listing summaries (reseller search results: Soldered, Electrokit, Videotronics), RS Components B3B/S3B-PH-K-S pages, E-Switch R6ABLKBLKFF Digikey, DigiKey WEC 1977066-1.
