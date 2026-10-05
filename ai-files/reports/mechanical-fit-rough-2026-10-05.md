# Rough mechanical fit check — 2026-10-05

## Basis and interpretation

Samsung lists the Galaxy S22 Ultra at **163.3 × 77.9 × 8.9 mm (H × W × D)** ([Samsung Global Newsroom specifications](https://news.samsung.com/global/samsung-galaxy-s22-ultra-offers-the-ultimate-and-most-premium-s-series-experience-yet)). I interpret “footprint of two S22 Ultras” as two phone face dimensions placed side by side: 163.3 mm long × 155.8 mm wide (2 × 77.9 mm), with a target cabinet height around half a phone length: 81.7 mm. That gives a nominal outer envelope of roughly **163 × 156 × 82 mm**. This is an assumption; if “two phones” means a different orientation, the footprint changes.

That envelope is about **2.08 L gross external volume**. With illustrative 2–3 mm walls on all sides, the simple inside box is roughly 159–157 × 152–150 × 78–76 mm, or about **1.79–1.88 L gross internal volume** before braces, partitions, drivers, battery, PCB, wiring and grille/feet. These are rectangular bounding volumes, not acoustic chamber volumes.

## What the project currently selects

- The plan calls for two front-facing stereo drivers and one downward-facing woofer, with the front on the long side. It does not select driver models or dimensions, impedance, sealed/ported tuning, chamber split or minimum acoustic volume.
- The target is a protected 1S pack around 10 Ah with a 10 kΩ temperature sensor. The BOM row `PACK` still has no manufacturer, part number, geometry, protection/current specification, connector or NTC curve. The handover also says pack geometry is open; I found no sourced 10 Ah pack envelope to check.
- The BOM has amplifier ICs but no speaker drivers. The active project has no PCB layout or board dimensions; the handover says no PCB layout exists.

## Likely constraints

- The external envelope is a plausible starting box, but **fit is not demonstrated**. The largest unknowns—the 10 Ah pack envelope and acoustic volume required by the eventual woofer/front drivers—are also the dominant volume users. A net internal volume below about 1.9 L must be split among the woofer chamber, stereo front-driver chambers, pack and electronics, so the enclosure may need to grow once drivers are chosen.
- The 163 mm front length is the favorable orientation for two front drivers; their frame diameters, mounting flanges, edge margins and spacing are unselected. The bottom-facing woofer needs a defined aperture, grille/feet clearance and a chamber that does not conflict with the battery or board.
- PCB fit cannot yet be checked from schematic placement: there is no board outline, component placement, connector orientation, mounting pattern or 3D assembly. The BQ25792 candidate package/fitting work does not establish a product PCB envelope.

## Next inputs for a real fit pass

Choose candidate driver models and enclosure loading first, obtain a dimensioned/protected 1S 10 Ah pack drawing, then sketch chamber partitions and a board keep-in envelope inside the stated shell. Until then, treat **163 × 156 × 82 mm as an outer target only**, not a validated enclosure or internal fit.

## Illustrative space reservation, not selected hardware

To make the rough check concrete, the following rectangular keep-in boxes can be used for the next sketch. They are allocations, not verified dimensions or proof that a protected10Ah pack or suitable acoustic drivers exist within them.

| Item | Assumed reserved envelope | Volume | Rough fit observation |
|---|---|---|---|
| Two front drivers | Each50×50×30mm |0.15L total | Two50mm frames plus a10mm center gap fit the163mm front width, leaving about26mm each end before wall/mount details; height is feasible. |
| Downward woofer |70×70×40mm |0.196L | Bottom aperture fits; rear/center placement should keep its magnet clear of front driver baskets. |
| Protected pack allocation |140×65×20mm |0.182L | Fits a rear shelf as an allocation; actual10Ah pack dimensions/protection/harness must be sourced. |
| PCB/component keep-in |120×60×15mm |0.108L | Fits a shelf as an allocation; connector access, thermal clearance and mounting remain open. |

Those boxes total about0.64L, leaving roughly1.15–1.24L before chamber partitions, braces, wiring and clearances. This deliberately overcounts driver metal displacement using bounding boxes, but does not establish usable acoustic volume because the boxes must also be placed without overlap. A20mm pack layer plus15mm board zone and40mm woofer depth already use75mm if stacked: the available76–78mm internal height makes that arrangement too tight. Distribute them laterally and place board/pack away from the woofer basket; do not stack all three. A sealed electronics/pack bay also removes air volume from the woofer chamber.

Reserve an illustrative10–15mm under-cabinet gap using feet for the downward driver, then tune the gap with the selected driver/grille. This adds height if82mm refers to the body rather than the overall assembly. Bass output cannot be assessed from these geometric allocations: driver Thiele–Small parameters and chamber tuning are needed.

**Rough conclusion:** packaging is plausible with small front drivers and a compact woofer, but10Ah pack fit is unverified and the approximately1L remaining air budget makes bass tuning the likely constraint. Preserve some freedom to increase cabinet depth/height after choosing the actual pack and drivers.
