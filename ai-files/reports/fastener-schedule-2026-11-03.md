# Fastener schedule: T10 post-Torx conversion (CAD v15 basis), 2026-11-03

Owner request: replace the remaining internal hex (socket) screws with T10 post-Torx screws like the lid and driver screws. Use 10 mm where possible and 16 mm where needed, and check what Bolt and Nut stocks.
Basis: `ai-files/cad/v15/scripts/build_speaker_cad.py` (fastener sites and stacks), `v15_detail.py` (CSK head, cup washer), `cad/v15/work/meta.json`, `cad/v15/fit_findings.json`, `bom/hardware-buy-list.csv`.
Machine-readable copy: `ai-files/cad/fastener-schedule.json`. No CAD or BOM file was edited.

Conventions: Bolt and Nut countersunk lengths are **overall including the head**. Button lengths are **under the head**. Inserts are Ruthex-type M3 x 5.7 (pilot 4.0), with the insert top flush with the face it sits in. Engagement: 5.7 = whole insert, >= 4.5 (1.5 d) acceptable, 3.0-4.5 marginal.

## 1. Schedule (recommended)

| Site | Qty | Now | Recommended (Bolt and Nut SKU) | Stack | Thread past insert top / insert engaged | Length |
|---|---|---|---|---|---|---|
| Lid (LidScrew_1-11, 2 into the chamber insert roof) | 11 | CSK post-Torx M3x10 (v15) | CSK post-Torx M3x10, **22CPTS310** | lid 4.0, head flush in a 6.0 x 90 countersink; pilot 8 | 6.0 / 5.7 full, tip 2.0 above the pilot floor | **10** |
| ND65 drivers (DrvScrew_L1-R4) | 8 | CSK M3x10 on an unsourced 8 x 1.6 cup washer | CSK post-Torx M3x10 **22CPTS310** + 6g stainless cup washer **71CS6** (11.0-11.4 x 2.1-2.3, 90 deg) | head top about 1.75 above the flange, flange 0.75; insert in the 11 mm pad, pilot 10 | about 7.5 (+-0.3) / 5.7 full, tip about 2.5 above the pilot floor | **10** |
| PCB (H1-H9, HA1, HA2, insert roof z 57.0) | 11 | ISO 4762 socket M3x16 through a 10 mm F/F spacer (Wurth 970100321) | **Wurth 971100321 M/F standoff (10 + 6 stud)** + button post-Torx M3x10 **22BPTS310** | stud into the roof insert; screw through PCB 1.6 into the standoff's female end | stud: 5.7 full (0.7 above the 6.7 pilot floor); screw: 8.4 in steel thread | **10** |
| Woofer W3-2052SC (WoofScrew_1-4) | 4 | ISO 4762 socket M3x20 (not on the buy list) | button post-Torx M3x20 **22BPTS320** | head on the frame back, frame 13.3 + gasket 3.3, insert at the seat, pilot 6.7 | 3.4 with the gasket free / 4.4 with it compressed 1 mm (marginal, as today); 5.4 / 5.7 with the 2 mm boss tweak (section 3) | **20** |
| Feet | 4 | Wurth 971120321 M/F stud + 3M SJ5312 | unchanged (external hex stud, no drive recess) | male 6 in the 5.7 insert | 5.7 | - |
| Other: SW101 rocker (snap-in, fastons), Heyco 2000 grommet (snap), grilles and chamber insert (Sikaflex), battery strap (tunnels), knob (grub screw supplied with the Jaycar HK7011), wiring (no clips in v15) | - | - | no fasteners to change | - | - | - |

Result: the owner can use **10 mm everywhere except the four woofer screws (20 mm)**. 16 mm is needed only if the PCB keeps the current through-spacer stack (option a).

## 2. Availability at Bolt and Nut

Each price below is per piece, in AUD including GST, read from the Magento product JSON of the page on 2026-11-03. Shipping was not read.

| Product | Verdict | Data |
|---|---|---|
| [CSK post-Torx T10 M3, A2-70](https://www.boltandnut.com.au/m3-x-0-50p-coarse-stainless-a2-70-g304-countersunk-post-torx-t10-machine-screws) | **VERIFIED** | Hobson. dk 5.90, k 2.00, 90 deg. Lengths overall 6/8/10/12/16/20 (SKU 22CPTS3<L>; maker MPN YCXSA2M3X<L>) and 25 (22CPTS325, **discontinued**, 355 left). Stock 29,203-29,979 per length. Tiers: 1 = 6.00, 10+ = 1.00, 20+ = 0.75, 30+ = 0.63, 50+ = 0.42 (0.46 for 16/20), 100+ = 0.25-0.28 |
| [Button post-Torx T10 M3, A2-70](https://www.boltandnut.com.au/security-fasteners/machine-screws/m3-x-0-50p-coarse-stainless-a2-70-g304-button-post-torx-t10-machine-screws) | **VERIFIED** | Hobson (alt. Sentinel). dk 5.11-5.70, k 1.60-1.80. Lengths under the head 6/8/10/12/16/20 (22BPTS36 ... 22BPTS320). Stock 20,345-29,894. Tiers: 1 = 6.00, 5+ = 1.60 (1.50 for 8 mm), 10+ = 1.00, 20+ = 0.70, 30+ = 0.60, 50+ = 0.46, 100+ = 0.26 |
| Pan, cheese or flange post-Torx M3 | **VERIFIED: none** | The Security Fasteners > Machine Screws category lists 28 products. M3 appears only as countersunk and button. |
| Button post-Torx M3x22 or longer | **not found** | No length above 20 in any category. The site search is rendered client-side and could not be read. |
| [Cup washer 6g G304](https://www.boltandnut.com.au/washers/cup-washers/6g-3-5mm-g304-stainless-cup-washers) 71CS6 | **VERIFIED** (an M3 head fit is calculated from geometry, not tested) | ID 4.1-4.5, OD 11.0-11.4, cup 2.1-2.3, 90 deg. 1 = 5.50, 5+ = 1.20, 10+ = 0.64, 20+ = 0.34. In stock |
| [T10 x 25 post-Torx insert bit](https://www.boltandnut.com.au/t10-x-25mm-alpha-post-torx-insert-security-standard-driver-bit) 11PT1025A (Alpha TXSE1025) | **VERIFIED** | 1/4 in hex. 9.00 each, 2+ = 7.00. The screw pages offer it as a bundle buy for 3.00 (the bundle quantity rule was not checked). In stock |
| [T10 post-Torx L-key 90 mm](https://www.boltandnut.com.au/t10-x-90mm-hobson-post-torx-security-allen-key) 11PTK10H (Hobson ISKPT10) | **VERIFIED** | Short arm 19 mm, alloy tool steel. 9.00 each, 2+ = 6.00. Bundle price 5.00. In stock |
| Plain Torx T10 pan M3, A4-70, ISO 14583 ([limited stock](https://www.boltandnut.com.au/machine-screws/pan-head/limited-stock-m3-x-0-50p-metric-coarse-pan-head-torx-t10-machine-screws-a4-70-stainless-g316-iso-14583)) | **VERIFIED** | Lengths 8 and 10 only (21PTS38M stock 10,000; 21PTS310M stock 2,500). dk 5.7-6.0, k 2.28-2.52. 10+ = 0.90, 20+ = 0.50. Only useful at H8 (section 4) |
| PCB spacers or standoffs | **not sold** | The site navigation has no spacer category, so spacers stay Wurth via Digi-Key |
| Wurth 971100321 M/F standoff (Digi-Key 732-10398-ND) | price and stock **VERIFIED**; female thread depth **UNVERIFIED** | USD 0.33, 32,433 in stock. Overall 16 (10 + 6), 5.5 AF. An RS listing (seen only as a search snippet) gives "hole depth 10 mm". The Wurth datasheet returned 403 and Farnell timed out |

## 3. Length analysis per site

The tables give the thread past the insert top, the insert length engaged, and the margin from the screw tip to the pilot floor (all in mm).

**Lid** (CSK, overall length; lid 4.0; pilot 8): 6 = 2.0, no. 8 = 4.0, marginal. **10 = 6.0, full, 2.0 margin**. 12 = 8.0, bottoms out. M3x10 stays.

**Drivers** (CSK on the 6g cup; the head top sits about 1.75 above the 0.75 flange; pilot 10): 8 = 5.5 (acceptable). **10 = 7.5, full, 2.5 margin**. 12 = 9.5, 0.5 margin (too tight).
- Alternative: button M3x10 with an M3 x 8 x 0.8 washer gives 8.45, full, 1.55 margin.
- A button head **directly** on the flange is not acceptable. dk 5.11 on a 4.2 hole leaves a 0.45 mm bearing ring on a 0.75 mm flange.
- CAD follow-up: the cup washer model goes from 8.0 x 1.6 to 11.2 x 2.2. The hole centre is 8.6 mm from the flange edge, so the 5.7 mm washer radius fits the flange. It still needs checking against the ND65 basket ribs.

**PCB** (insert in the roof at z 57.0, pilot 6.7; board bottom at z 67):

| Option | Engagement for 8 / 10 / 12 / 16 / 20 | CAD impact | Verdict |
|---|---|---|---|
| (a) button M3x16 through the 10 mm spacer | 12 = 0.4; **16 = 4.4** (1.47 d, as today); 20 bottoms out | none. Head 1.8 instead of 3.0 | Fallback. The F/F spacer is screwed through, so it is not clamped to the roof; an unthreaded spacer would be the correct part. This is the only site that needs 16 mm |
| (b) 6 mm spacer + M3x12 | 10 = 2.4; 12 = 4.4; 16 bottoms out | The board drops 4 mm. All lid cutouts (USB-C, jacks, SW100, TC2030 access) move, and so do the knob dish depth and shaft exposure. M3x10 would need a 4 mm spacer (board 6 mm lower) | Rejected |
| (c) printed 10 mm boss on the roof, insert at its top, M3x10 | 8 = 6.4; 10 = 8.4 (pilot 9.4 in the boss). Removing the under-roof bosses gains about 2.6 cm3 of chamber | The insert prints **roof-down** (roof top on the bed), so a boss above the roof cannot print with it. Separate glued posts would carry the screw torque through a glue joint | Rejected |
| **(d) Wurth 971100321 M/F standoff + button M3x10** | stud 6 into the 5.7 insert: full, 0.7 above the pilot floor. Screw into the steel female end: 6 = 4.4, 8 = 6.4, **10 = 8.4** | Model swap only: same 5.5 AF x 10 body, the stud replaces the screw shank in the insert, head 5.7 x 1.8 | **Recommended.** All PCB screws are 10 mm, the PCB screw threads into steel, and the stud preloads the standoff onto the insert. Condition: female thread at least 8.5 deep (RS listing says 10; unverified). If it is shorter, use button M3x8 (22BPTS38, 6.4 mm) |

**Woofer** (button, length under the head; frame 13.3 + gasket 3.3, both photo estimates +-1.5; insert top at the seat; pilot 6.7):
- 16 mm gives -0.6 with the gasket free and 0.4 compressed: no.
- **20 mm gives 3.4 free and 4.4 with 1 mm compression: marginal, the same as today's socket M3x20.**
- 20 is the longest M3 button post-Torx at Bolt and Nut. 25 exists only as the discontinued countersunk, and the frame back has no seat for a countersink. A 25 would also need a 10.4 pilot and outside bosses 8.4 deep.
- **Design tweak for full engagement with M3x20:**
  - Add four bosses 2.0 high, OD 7.0, on the floor inner face at the screw axes. This raises the insert top by 2.0. Punch 7.5 mm holes in the factory gasket at the screws.
  - Deepen the pilot to 7.7 from the boss top. The outside bosses then shrink from 4.7 to 3.7 below the floor.
  - Result: 5.4 with the gasket free and 5.7 (full) at 1 mm compression, with 1.3-2.3 margin to the pilot floor.
  - Conditions:
    - The bosses must stay below the compressed gasket height.
    - About 6 mm of gasket seal band remains inside the bosses (the bolt corners sit at radius 48.26, the aperture at 38.1).
    - Print: the bosses are a small 2 mm overhang off the floor in the baffle-down print, so give them a 45 deg teardrop like the outside bosses.
    - Chamber volume change: about -0.3 cm3.
  - Caliper the frame and gasket before making this change (an open item since v13). The photo also shows a possible front counterbore of about 7.3 mm. If it is real, it could take part of the boss height.

## 4. Tool access (new constraint from post-Torx)

- **H8 sits under the knob dish floor.** There is 11.7 mm from the button head top (z 70.4) to the dish floor (z 82.09). The post-Torx L-key short arm is 19 mm and the bit is 25 mm, so neither fits. Ball-end keys do not work with post-Torx.
  - Option 1: cut a second ISKPT10 short arm to about 8 mm (8 mm arm + about 2.8 mm bar = 10.8, which fits the 11.7 mm space with very little room).
  - Option 2: fit the plain-Torx pan M3x10 21PTS310M at H8 only and drive it with a ball-end T10 key (a standard tool; not found at Bolt and Nut).
- The other 10 PCB holes have about 26.6 mm above the head, so the 19 mm short arm fits. HA1 and HA2 are about 120 mm in from the rear opening, so the 90 mm key needs the fingers about 30 mm inside the box. This is the same reach problem as the previous ball-end hex key; check it with the real key.
- Woofer screws are driven before the chamber insert goes in, with 77 mm of vertical space; the L-key or a stubby 1/4 in bit holder fits.
- Driver screws are driven through the empty shell, about 190 mm deep, so they need a 1/4 in bit extension of 200 mm or more (owner tool, not sourced).

## 5. Buy list (one unit, at least 10 % spares)

| Item | Need | Order | Unit | Line | Source / part | Status |
|---|---|---|---|---|---|---|
| CSK post-Torx M3x10 (lid 11 + drivers 8) | 19 | 21 | AUD 0.75 | AUD 15.75 | Bolt and Nut 22CPTS310 | verified (50 cost AUD 21.00 and cover two units) |
| Button post-Torx M3x10 (PCB) | 11 | 13 | AUD 1.00 | AUD 13.00 | Bolt and Nut 22BPTS310 | verified (20 cost AUD 14.00) |
| Button post-Torx M3x20 (woofer) | 4 | 5 | AUD 1.60 | AUD 8.00 | Bolt and Nut 22BPTS320 | verified |
| Cup washer 6g G304 (drivers) | 8 | 10 | AUD 0.64 | AUD 6.40 | Bolt and Nut 71CS6 | verified (10 cost less than 9) |
| T10 post-Torx bit 25 mm (one + spare) | 2 | 2 | AUD 3.00 bundle (7.00) | AUD 6.00 (14.00) | Bolt and Nut 11PT1025A | verified; bundle quantity rule unverified |
| T10 post-Torx L-key 90 mm (one + one to cut for H8) | 2 | 2 | AUD 5.00 bundle (6.00) | AUD 10.00 (12.00) | Bolt and Nut 11PTK10H | verified; bundle quantity rule unverified |
| Wurth 971100321 M/F standoff (PCB) | 11 | 13 | USD 0.33 | USD 4.29 | Digi-Key 732-10398-ND | verified; female thread depth UNVERIFIED |
| Optional: button M3x8 (PCB fallback) | 0 | 0 | AUD 1.00 | - | Bolt and Nut 22BPTS38 | excluded |
| Heat-set inserts (38: lid 11, drivers 8, woofer 4, PCB 11, feet 4) | 38 | unchanged | - | - | line 16 | unchanged |
| Feet studs + bumpons | 4 | unchanged | - | - | lines 21-22 | unchanged |

**Total for this list:**
- Bolt and Nut: **AUD 59.15** with the bundle tool prices, or AUD 69.15 with the standalone tool prices. Shipping is extra (not read).
- Digi-Key: **USD 4.29**.
- These lines no longer need buying: line 18 (AUD 7.68), line 20 (USD 3.19) and line 23 (USD 1.10).
- This is a partial fastener subtotal, not a product cost.

### Rows ready to append to `ai-files/bom/hardware-buy-list.csv` (not applied)

```
"Countersunk post-Torx (T10 security) machine screw M3 x 10, A2-70 (304) stainless",21,19,"M3 x 0.5, 90 deg CSK, head 5.90 x 2.00, length 10 overall incl. head; 19 per unit (11 lid + 8 drivers) + 2 spares",Bolt and Nut Australia (Hobson Engineering),22CPTS310 (YCXSA2M3X10),AUD 0.75,AUD 15.75,"29,590 (page JSON 2026-11-03)","Replaces line 41. Tiers per piece: 10+ 1.00, 20+ 0.75, 30+ 0.63, 50+ 0.42 (50 covers two units for AUD 21.00).",Mechanical,confirmed,https://www.boltandnut.com.au/m3-x-0-50p-coarse-stainless-a2-70-g304-countersunk-post-torx-t10-machine-screws
"Button post-Torx (T10 security) machine screw M3 x 10, A2-70 (304) stainless",13,11,"M3 x 0.5 button head 5.11-5.70 x 1.60-1.80, length 10 under the head; PCB H1-H9, HA1, HA2 into the Wurth 971100321 standoffs (8.4 mm in the steel female thread)",Bolt and Nut Australia (Hobson Engineering),22BPTS310,AUD 1.00,AUD 13.00,"20,345 (page JSON 2026-11-03)","Replaces line 18 (M3x16 socket). 20+ tier AUD 0.70. H8 under the knob dish: drive with a cut-down post-Torx L-key (11.7 mm headroom).",Mechanical,confirmed,https://www.boltandnut.com.au/security-fasteners/machine-screws/m3-x-0-50p-coarse-stainless-a2-70-g304-button-post-torx-t10-machine-screws
"Button post-Torx (T10 security) machine screw M3 x 20, A2-70 (304) stainless",5,4,"M3 x 0.5 button head 5.11-5.70 x 1.60-1.80, length 20 under the head; woofer W3-2052SC (frame 13.3 + gasket 3.3)",Bolt and Nut Australia (Hobson Engineering),22BPTS320,AUD 1.60,AUD 8.00,"29,639 (page JSON 2026-11-03)","Replaces the unlisted ISO 4762 M3x20. Engagement 3.4 free / 4.4 compressed; 5.4-5.7 with the 2 mm floor-boss tweak. 20 is the longest M3 button post-Torx at Bolt and Nut.",Mechanical,confirmed,https://www.boltandnut.com.au/security-fasteners/machine-screws/m3-x-0-50p-coarse-stainless-a2-70-g304-button-post-torx-t10-machine-screws
"Cup washer 6g (3.5 mm) G304 stainless, OD 11.0-11.4, ID 4.1-4.5, cup 2.1-2.3, 90 deg",10,8,"under the M3 CSK post-Torx heads on the 0.75 mm ND65 flanges (8 per unit)",Bolt and Nut Australia (Hobson Engineering),71CS6,AUD 0.64,AUD 6.40,In stock (page 2026-11-03),"Replaces line 43 (unsourced 8 x 1.6). 10 cost less than 9 (5+ tier AUD 1.20). Fit of the 5.90 head in a 6g cup by geometry only; CAD: check the 11.4 OD against the ND65 basket ribs.",Mechanical,confirmed,https://www.boltandnut.com.au/washers/cup-washers/6g-3-5mm-g304-stainless-cup-washers
"T10 x 25 mm post-Torx (security, pin) insert driver bit, 1/4 in hex",2,0,"Alpha TXSE1025; one + spare",Bolt and Nut Australia,11PT1025A,AUD 3.00,AUD 6.00,In stock (page 2026-11-03),"Replaces line 42 (qty 1). AUD 3.00 is the bundle price on the screw pages (quantity rule not verified); standalone AUD 9.00, 2+ AUD 7.00.",Tools,confirmed,https://www.boltandnut.com.au/t10-x-25mm-alpha-post-torx-insert-security-standard-driver-bit
"T10 post-Torx L-key 90 mm, short arm 19 mm",2,0,"Hobson ISKPT10, alloy tool steel; one for the PCB screws, one cut to about 8 mm short arm for H8",Bolt and Nut Australia,11PTK10H,AUD 5.00,AUD 10.00,In stock (page 2026-11-03),"Bundle price on the screw pages (quantity rule not verified); standalone AUD 9.00, 2+ AUD 6.00.",Tools,confirmed,https://www.boltandnut.com.au/t10-x-90mm-hobson-post-torx-security-allen-key
"Hex standoff M3 M/F, 10 mm body + 6 mm stud, 5.5 AF, steel zinc",13,11,"PCB stack: stud into the roof insert, button M3x10 into the female end",Digi-Key,Wurth 971100321 (DK 732-10398-ND),USD 0.33,USD 4.29,"32,433 (DK 2026-11-03)","Replaces line 20 (F/F 970100321). Female thread depth UNVERIFIED (RS listing: hole depth 10); if < 8.5 mm use button M3x8 22BPTS38.",Mechanical,confirmed,https://www.digikey.com/en/products/result?keywords=971100321
```

Row actions for whoever edits the CSV:
- Set line 18 (M3x16 socket), line 20 (F/F spacer) and line 23 (nylon washers) to quantity 0 and mark them superseded.
- Replace lines 41-43 with the rows above.
- Lines 16, 21 and 22 stay as they are.
- `cad/mechanical-bom.md` lines 24-29 need the same update.

## 6. Owner decisions

1. **PCB:** choose option (d), Wurth M/F standoffs with button M3x10 (all 10 mm; Digi-Key line changes). Or choose option (a), button M3x16 through the current spacer (one 16 mm length, no Digi-Key change, 4.4 mm engagement as today).
2. **Woofer:** accept button M3x20 (3.4-4.4 mm, as today), or approve the 2 mm floor-boss tweak (5.4-5.7 mm) after calipering the frame and gasket.
3. **Drivers:** CSK M3x10 on the 6g cup washer (recommended, matches the lid), or button M3x10 with a flat washer.
4. **H8:** cut down a second post-Torx L-key, or use a plain-Torx pan screw at H8 with a ball-end T10 key.
5. **Quantity:** one unit with spares (AUD 59.15 at Bolt and Nut), or the 50-piece CSK tier (AUD 21.00) if a second unit is planned.

## 7. Notes for the CAD and BOM agents

- If the owner approves the changes:
  - `build_speaker_cad.py`: PCB `screw=10`, a stud model for 971100321 (10 + 6), and the button-head model (dk 5.7, k 1.8, T10 pin recess) for PCB and woofer.
  - `v15_detail.py`: `CUPW` becomes 11.2 x 2.2.
  - For the woofer tweak: inner bosses 2.0 x OD 7.0, pilot 7.7, `W_BOSS_H` 3.7.
- Re-run `check_cad.py` and the interference check. Expected: no new overlaps; the M3x16/spacer intended pairs become stud/insert pairs.
- `fit_findings.json` currently rates the PCB 4.4 mm as "ok". By the 1.5 d rule it is borderline (1.47 d). It is moot under option (d).
