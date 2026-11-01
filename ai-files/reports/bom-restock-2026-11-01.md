# BOM restock check and alternates (accessed 2026-11-01)

Scope: BOM files only. Nothing in `DesktopSpeaker-kicad/` was touched. Prior sourcing (`bom-sourcing-pass.md`, `sourcing-2026-10-12.md`) was read first and is not repeated.

## Method and limits

- Web lookups used: 12, the whole budget (6 LCSC product JSON `wmsc.lcsc.com/ftps/wm/product/detail?productCode=` + 6 JLCPCB `selectSmtComponentList` searches, one pair per code). lcsc.com and jlcpcb.com were NOT blocked; the public JSON endpoints answered HTTP 200 with no login. No further lookups were made, so every alternate below comes from the local datasheets in `ai-files/datasheets/` or from general knowledge and is UNVERIFIED for stock and price.
- Stock figures are lookups, not reservations. LCSC (retail) and JLC parts list (assembly) agreed on all rows except where noted.
- Exception: LCSC detail API returns `result: null` for C7245133 (same as 2026-10-10), so the LCSC side of L201-L206 is unverified; the JLC list answered.

## Findings table

| Ref | MPN | Code / stock now (2026-11-01) | Finding | Proposed action | Approval | Verified |
|---|---|---|---|---|---|---|
| U1 | BM83SM1-00TA | C6752723; LCSC 0, JLC 0 (was 1 on 10-10); $22.40 at 1 | Sold out at both. Cannot cover order qty 1. | Buy outside LCSC: Microchip direct / Digi-Key / Mouser (stock unverified). The datasheet (Table 11-1) lists sister orderables BM83SM1-00AA and -00AB for the same module; the -00TA vs -00AA/-AB difference (firmware/flash/packaging) is NOT stated in the datasheet and must be confirmed with Microchip before substituting. Same module footprint, so no schematic or footprint change if the variant is accepted. Module cannot be JLC-assembled from non-JLC stock unless consigned; otherwise hand-solder or consignment. | User: source and variant choice | Stock: verified 2026-11-01. Alternates: unverified |
| U2 | PCM2902CDBR | C2651869; LCSC 0, JLC 0 (was 3); $12.21 at 1 | Sold out at both. | Same die, same SSOP-28 footprint, no schematic change: PCM2902CDB (rail pack, 47/rail; TI ordering table in `datasheets/PCM2902C.pdf`) or the same DBR from TI store / Digi-Key / Mouser (stock unverified). PCM2900CDB(R) is the same package without S/PDIF; DIN/DOUT pins would be unused or differ, so treat as a last resort and check the sheet before use. | User: source choice (reel vs rail is no electrical change) | Stock: verified. Alternates: from local datasheet, stock unverified |
| U19 | TPS7B8450QWDRBRQ1 | C3751394; LCSC 0, JLC 0 (was 1); price now $2.9959 at 1 (was $1.3452) | Sold out at both. | Same part from Digi-Key/Mouser/TI store (stock unverified; it is an active production TI part per the local datasheet package table). The only other 5 V fixed package, TPS7B8450QDCYRQ1 (SOT-223), has a different footprint and pinout: needs a schematic symbol and footprint change, not recommended. | User: source choice | Stock: verified. Alternates: from local datasheet, stock unverified |
| C184, C270, C316 | CL21B105KBFNNNE | C28323; LCSC 20 (was 10), JLC basic 2,355,245; $0.0426 at 10 | LCSC retail stock 20 covers the BOM order qty 10 (min buy 10). Fitted 3 pcs; spares limited to 17 at LCSC. JLC assembly uses JLC stock (2.36 M), so assembly is not at risk. | No change. If more spares are wanted order 20 at LCSC; or buy at JLC basic. No alternate needed. | None | Verified 2026-11-01 |
| L200 | XAL7070-222MEC | C3911470; LCSC 347, JLC 359 (was 262); $8.5474 at 1 (was $8.2372) | Already coded and in stock; coded in the BOM since 10-10 (earlier "not stocked" note is stale). Price up about 4 %. | Keep. Alternates and the footprint-change options stay as recorded in `bom-sourcing-pass.md`. | None (price only) | Verified 2026-11-01 |
| L201-L206 | MWSA1265S-220MT | C7245133; JLC 454 (was 54); $0.8465 at 1 (was $0.7183); LCSC detail API returns null | Already coded. JLC list shows 454 against 6 needed, so stock is fine on the JLC list. LCSC-side stock unverified (API null). Price up about 18 %. | Keep. Order via the JLC assembly list. Order qty 6 may be raised for spares. | None | JLC list verified; LCSC side unverified |

Tasks 2: no new search was needed or done; the BOM already holds codes for L200 (C3911470) and L201-L206 (C7245133). Both are stocked, and only their stock/price were refreshed.

## Starter CSV changes (`ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv`)

Seven rows changed, in the Stock qty, Availability (old text kept after "Previous (2026-10-10):"), Accessed (46327) and Cache age (2026-11-01) fields only: U1, U2, U19, `C184, C270`, C316, L200, `L201..L206`. No MPN, LCSC code, quantity, price or footprint field was changed. Unit USD columns were deliberately NOT updated: new prices are in the table and the Availability text.

## Follow-ups

- `DesktopSpeaker_LCSC_Starter_BOM.xlsx` needs regenerating from the CSV (not done).
- `DesktopSpeaker_JLC_BOM.csv` unchanged. U1, U2 and U19 cannot be assembled by JLC from their stock until a source is chosen (consign or hand-solder).
- If the buy goes ahead, re-check all three ICs at order time; the stock count fell from 1/3/1 to 0 in three weeks.

## Decisions the user must make

1. U1: which BM83SM1 variant (-00TA, or -00AA/-00AB after Microchip confirms equivalence) and which supplier; assembled by JLC (consign) or by hand.
2. U2 and U19: approve buying the identical MPN (or PCM2902CDB rails) from Digi-Key/Mouser/TI instead of LCSC.
3. Confirm no schematic or footprint change is wanted (none is needed for any proposal above except the not-recommended SOT-223 LDO).
