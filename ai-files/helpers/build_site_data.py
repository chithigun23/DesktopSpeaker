#!/usr/bin/env python3
"""Build the data, downloads and docs of the Desktop Speaker project website.

Plain python3, standard library only. Run from anywhere:

    python3 ai-files/helpers/build_site_data.py

Reads (never writes) the repo sources:
  ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv   electronics BOM (per-reference rows)
  ai-files/bom/DesktopSpeaker_JLC_BOM.csv            assembly BOM (grouped by LCSC code)
  ai-files/bom/hardware-buy-list.csv                 mechanical / hardware buy list
  ai-files/bom/candidate_fixes_BOM.csv               old candidate rows (download only)
  DesktopSpeaker-kicad/*.kicad_sch                   reference -> sheet, value, DNP
  ai-files/cad/print/*.stl, ai-files/cad/*.step      print files and STEP (v11)
  ai-files/DesktopSpeaker-preview.pdf                schematic preview

Writes only inside ai-files/website/desktopSpeaker-site/:
  data/bom.json        BOM tables, status classification, caveats, partial subtotals
  data/files.json      downloads and documents with size and SHA256
  downloads/*          copies of the CSVs and schematic PDF + SHA256SUMS; the v11 STLs and zipped STEP only
                       while cad/downloads/ (the newer CAD export) is absent, or with --with-v11-cad
  docs/*               copies of the key reports and the small (<= 5 MB) datasheets
It never touches data/specs.json (hand-curated facts with sources) or cad/ (owned by the CAD export).
"""
import csv
import datetime
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SITE = REPO / "ai-files" / "website" / "desktopSpeaker-site"
MAX_DOC = 5 * 1024 * 1024

BOM_MAIN = REPO / "ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv"
BOM_JLC = REPO / "ai-files/bom/DesktopSpeaker_JLC_BOM.csv"
BOM_HW = REPO / "ai-files/bom/hardware-buy-list.csv"
BOM_CAND = REPO / "ai-files/bom/candidate_fixes_BOM.csv"

# Key reports for the Documents section (repo-relative). Missing files are skipped with a warning.
REPORTS = [
    ("ai-files/HANDOVER.md", "Single project handover: decisions, evidence, open items (older sections superseded)"),
    ("plan.md", "Schematic completion checklist and subsystem status"),
    ("ai-files/reports/audio-chain-architecture.md", "Audio chain architecture and MCU sizing"),
    ("ai-files/reports/power-analysis-2026-11-01.md", "Power analysis: standby, surge clamp, PPHV, inrush"),
    ("ai-files/reports/charge-policy-2026-11-02.md", "Charge policy: ICHG 4.0 A, 17 W input cap, VREG 4.10 V"),
    ("ai-files/reports/firmware-system-spec-2026-11-01.md", "Firmware system specification and open decisions"),
    ("ai-files/reports/hand-assembly-research-2026-11-01.md", "Hand assembly: stencil, hotplate, paste, profile"),
    ("ai-files/reports/bench-bringup-plan.md", "Bench bring-up plan"),
    ("ai-files/reports/pcb-layout-best-practices.md", "PCB layout best practices (section 14 routing standard)"),
    ("ai-files/reports/routing-review-r6q.md", "Routing review of the old R6q board (restart decision)"),
    ("ai-files/reports/routing-s1-s3-run.md", "Staged routing S1-S3 (RT-2): 145 of 283 connections"),
    ("ai-files/reports/silk-boxes-rt3.md", "Silkscreen section boxes (RT-3)"),
    ("ai-files/reports/release-review-r8.md", "Release review R8 of the old board"),
    ("ai-files/reports/project-review-fable.md", "Whole-project review (2026-10-10)"),
    ("ai-files/reports/cad-v11-print-ready.md", "Enclosure CAD v11 print-ready report"),
    ("ai-files/reports/sourcing-2026-10-12.md", "Sourcing: woofer data, battery pack candidates"),
    ("ai-files/reports/battery-pack-rfq.md", "Battery pack request for quote"),
    ("ai-files/reports/bom-restock-2026-11-01.md", "BOM restock check: U1/U2/U19 out of stock"),
    ("ai-files/reports/bom-sourcing-pass.md", "BOM sourcing pass (2026-10-10)"),
    ("ai-files/reports/mcu-pin-allocation.md", "MCU pin allocation (one stale line, see open items)"),
    ("ai-files/reports/bluetooth-notes.md", "Bluetooth module notes"),
    ("ai-files/reports/usb-audio-notes.md", "USB audio codec notes"),
    ("ai-files/cad/README.md", "Enclosure CAD build: rebuild, assumptions"),
    ("ai-files/cad/interference.md", "CAD interference check results"),
    ("ai-files/cad/volumes.md", "Acoustic chamber volumes"),
    ("ai-files/cad/mechanical-bom.md", "Mechanical BOM (fasteners, inserts)"),
    ("ai-files/bom/hardware-buy-list.md", "Hardware buy list (A$ snapshot prices)"),
    ("ai-files/bom/jlc-assembly-notes.md", "JLC assembly BOM notes"),
    ("ai-files/fab/ORDER-NOTES.md", "Fabrication order notes (old R9 outputs)"),
]

# Datasheets of the major parts (ai-files/datasheets/ unless a path is given).
DATASHEETS = [
    ("TPS25730.pdf", "U11 TPS25730D USB PD sink controller"),
    ("TPS25730_TRM.pdf", "TPS25730 technical reference manual"),
    ("BQ25792.pdf", "U4 BQ25792 1-4S buck-boost charger"),
    ("MAX17048_MAX17049.pdf", "U5 MAX17048 fuel gauge"),
    ("STM32G071x8_xB.pdf", "U3 STM32G071RBT6 MCU"),
    ("BM83_Bluetooth_Stereo_Audio_Module.pdf", "U1 BM83 Bluetooth audio module"),
    ("TAS5825M.pdf", "U6/U7 TAS5825M class-D amplifiers"),
    ("PCM2902C.pdf", "U2 PCM2902C USB audio codec"),
    ("PCM1862.pdf", "U24 PCM1862 audio ADC"),
    ("TPA6132A2.pdf", "U10 TPA6132A2 headphone amplifier"),
    ("TS5A23157.pdf", "U8/U9 TS5A23157 analogue switches"),
    ("TPS61023.pdf", "U14 TPS61023 5 V logic boost"),
    ("TPS63802.pdf", "U15 TPS63802 3.8 V Bluetooth buck-boost"),
    ("TPS7B84-Q1.pdf", "U19 TPS7B84 LDO"),
    ("TPS7A02.pdf", "U12 TPS7A02 always-on LDO"),
    ("TPS22917.pdf", "U23 TPS22917 load switch"),
    ("TMUX1511.pdf", "TMUX1511 switch"),
    ("TVS2200.pdf", "TVS2200 surge clamp"),
    ("Bourns_SRN6045TA.pdf", "L1/L2 SRN6045TA inductors"),
    ("TYPE-C-31-M-12.pdf", "J1 USB-C receptacle"),
    ("Molex_43650-0300_C503478.pdf", "J5 pack connector (LCSC-linked drawing, see handover)"),
    ("TE_1977066-1_datasheet.pdf", "SW100 TE tactile switch (footprint unverified against it)"),
    ("Alps_EC11E.pdf", "SW102 Alps EC11E encoder"),
    ("Samsung_INR21700-50S_SDI_introduction_2021.pdf", "Samsung INR21700-50S cell introduction (no full spec)"),
    ("Samsung_INR21700-50E_spec_v0.2_sibling.pdf", "Samsung 50E sibling cell spec (used for the charge window)"),
    ("../cad/parts/290-204-dayton-audio-nd65-4-specifications.pdf", "Dayton Audio ND65-4 driver specification"),
]

TOOL_NOTE = ("Generated by ai-files/helpers/build_site_data.py; data/specs.json is curated by hand with a "
             "source path on every entry.")


def rel(p):
    return str(Path(p).resolve().relative_to(REPO))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fnum(s):
    try:
        return float(str(s).replace(",", "").strip())
    except ValueError:
        return None


# ----------------------------------------------------------------------------- schematics
def sexpr_blocks(text, head):
    """Yield balanced s-expression blocks that start with `head` (e.g. '(symbol (lib_id')."""
    i = 0
    while True:
        i = text.find(head, i)
        if i < 0:
            return
        depth, j, in_str = 0, i, False
        while j < len(text):
            c = text[j]
            if in_str:
                if c == "\\":
                    j += 1
                elif c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        yield text[i:j + 1]
        i = j + 1


def parse_schematics():
    refs = {}
    for sch in sorted((REPO / "DesktopSpeaker-kicad").glob("*.kicad_sch")):
        sheet = "Root" if sch.stem == "DesktopSpeaker" else sch.stem
        text = sch.read_text(encoding="utf-8", errors="replace")
        # one symbol instance per block; the lib_symbols section uses (symbol "name" ...) and is skipped
        for blk in sexpr_blocks(text, "(symbol (lib_id"):
            pass_refs = re.findall(r'\(reference "([^"]+)"\)', blk)
            if not pass_refs:
                m = re.search(r'\(property "Reference" "([^"]+)"', blk)
                pass_refs = [m.group(1)] if m else []
            val = re.search(r'\(property "Value" "([^"]*)"', blk)
            fp = re.search(r'\(property "Footprint" "([^"]*)"', blk)
            dnp = "(dnp yes)" in blk
            for r in pass_refs:
                if r.startswith("#"):
                    continue
                refs[r] = {"sheet": sheet, "value": val.group(1) if val else "",
                           "footprint": (fp.group(1).split(":")[-1] if fp else ""), "dnp": dnp}
        # multi-line formatted files
        if not refs or "(symbol\n" in text:
            for blk in sexpr_blocks(text, "(symbol\n"):
                if "(lib_id" not in blk[:200]:
                    continue
                for r in re.findall(r'\(reference "([^"]+)"\)', blk):
                    if r.startswith("#") or r in refs:
                        continue
                    val = re.search(r'\(property "Value" "([^"]*)"', blk)
                    refs[r] = {"sheet": sheet, "value": val.group(1) if val else "", "footprint": "",
                               "dnp": "(dnp yes)" in blk}
    return refs


def expand_refs(s):
    out = []
    for part in re.findall(r"\b[A-Z]+\d+(?:-[A-Z]*\d+)?\b", s):
        m = re.fullmatch(r"([A-Za-z]+)(\d+)-([A-Za-z]*)(\d+)", part)
        if m and (not m.group(3) or m.group(3) == m.group(1)):
            a, b = int(m.group(2)), int(m.group(4))
            if 0 <= b - a < 400:
                out += [f"{m.group(1)}{n}" for n in range(a, b + 1)]
                continue
        out.append(part)
    return out


# ----------------------------------------------------------------------------- BOM
def snapshot_date(row):
    for key in ("Cache age", "Accessed"):
        v = (row.get(key) or "").strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            return v
        if re.fullmatch(r"\d{5}", v):  # spreadsheet serial day number
            return (datetime.date(1899, 12, 30) + datetime.timedelta(days=int(v))).isoformat()
    m = re.search(r"(20\d\d-\d\d-\d\d)", row.get("Availability", ""))
    return m.group(1) if m else ""


def classify(row):
    av = row.get("Availability", "")
    up = av.upper()
    stock, order = fnum(row.get("Stock qty")), fnum(row.get("Order qty"))
    if up.startswith("EXCLUDED") or "EXCLUDED FROM PER-PART BOM" in up:
        return "excluded", "Not a BOM purchase line (hand-fitted, in_bom no)"
    if up.startswith("UNRESOLVED") or not row.get("MPN", "").strip():
        return "unresolved", "No part number selected"
    if "OUT OF STOCK" in up or (row.get("LCSC part") and stock == 0):
        return "stock-zero", "0 stock at LCSC/JLC at the last check (hand assembly can use another distributor)"
    if not row.get("LCSC part", "").strip():
        return "other-supplier", "Not an LCSC part; bought from another distributor"
    if stock is not None and order and stock < order:
        return "below-order", "Listed stock below the order quantity"
    if "SUBSTITUT" in up or "REPLACEMENT" in up or "VALUE CHANGE" in up:
        return "substituted", "Approved substitution or value change; listing checked"
    if up.startswith("IN STOCK") or "IN STOCK" in up[:60] or (stock and stock > 0):
        return "in-stock", "Listed in stock at the snapshot date (not order-time verified)"
    return "check", "See availability note"


def build_bom(refmap):
    rows = []
    with open(BOM_MAIN, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            refs = expand_refs(r["Reference"])
            sheets = sorted({refmap[x]["sheet"] for x in refs if x in refmap})
            values = sorted({refmap[x]["value"] for x in refs if x in refmap and refmap[x]["value"]})
            dnp = sorted(x for x in refs if x in refmap and refmap[x]["dnp"])
            missing = [x for x in refs if x not in refmap]
            status, why = classify(r)
            rows.append({
                "ref": r["Reference"], "refs": refs, "function": r["Function"],
                "value": " / ".join(values), "mfr": r["Manufacturer"], "mpn": r["MPN"],
                "lcsc": r["LCSC part"], "qty": fnum(r["Fitted qty"]), "order_qty": fnum(r["Order qty"]),
                "unit_usd": fnum(r["Unit USD"]), "fitted_usd": fnum(r["Fitted USD"]),
                "order_usd": fnum(r["Order USD"]), "stock": fnum(r["Stock qty"]),
                "snapshot": snapshot_date(r), "availability": r["Availability"],
                "notes": r.get("", "") or "", "url": r.get("LCSC source URL", ""),
                "sheets": sheets or (["(not in schematic)"] if refs and missing == refs else []),
                "dnp": dnp, "not_in_schematic": missing if len(missing) < len(refs) else ([] if not refs else missing),
                "status": status, "status_why": why,
            })
    priced = [x for x in rows if x["fitted_usd"] is not None]
    unpriced = [x["ref"] for x in rows if x["fitted_usd"] is None and x["status"] != "excluded"]
    counts = {}
    for x in rows:
        counts[x["status"]] = counts.get(x["status"], 0) + 1
    placements = sum(int(x["qty"] or 0) for x in rows if x["status"] != "excluded")

    hw = []
    with open(BOM_HW, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            hw.append({k.strip().lower().replace(" ", "_").replace("/", "_"): v for k, v in r.items()})

    jlc_lines, jlc_place = 0, 0
    with open(BOM_JLC, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            jlc_lines += 1
            jlc_place += int(fnum(r.get("Qty")) or 0)

    snaps = sorted({x["snapshot"] for x in rows if x["snapshot"]})
    return {
        "generated": datetime.date.today().isoformat(),
        "tool": TOOL_NOTE,
        "sources": [rel(BOM_MAIN), rel(BOM_JLC), rel(BOM_HW), "DesktopSpeaker-kicad/*.kicad_sch (sheet, value, DNP)"],
        "caveats": [
            "Partial subtotal only: the sums below cover priced LCSC electronics lines at snapshot prices. "
            "They are NOT a product cost (no pack, PCB fabrication, enclosure, drivers, shipping, tax or unpriced lines).",
            "Stock and prices are snapshots (dates per row, %s to %s), not verified order-time availability; "
            "re-check every line before ordering." % (snaps[0] if snaps else "?", snaps[-1] if snaps else "?"),
            "U1 BM83, U2 PCM2902C and U19 TPS7B84 showed 0 stock at LCSC and JLC on 2026-11-01. The owner assembles "
            "by hand (stencil and hotplate), so JLC assembly stock does not block the build: buy these from another distributor.",
            "Unresolved: the battery pack (1S2P 21700 with PCM and NTC) has no part number; quotes pending.",
            "Value column comes from the schematic Value field; the BOM function text is the description.",
        ],
        "summary": {
            "lines": len(rows), "placements_listed": placements, "status_counts": counts,
            "fitted_usd_partial": round(sum(x["fitted_usd"] for x in priced), 2),
            "order_usd_partial": round(sum(x["order_usd"] or 0 for x in priced), 2),
            "unpriced_lines": unpriced,
            "jlc_bom_lines": jlc_lines, "jlc_bom_placements": jlc_place,
            "hardware_lines": len(hw),
        },
        "status_legend": {
            "in-stock": "Listed in stock at the snapshot date",
            "substituted": "Approved substitution or value change, listing checked",
            "below-order": "Listed stock below the order quantity",
            "stock-zero": "0 stock at LCSC/JLC at the last check",
            "other-supplier": "Bought outside LCSC (e.g. Digi-Key)",
            "unresolved": "No part number selected",
            "excluded": "Not a purchase line (test points)",
            "check": "See the availability note",
        },
        "rows": rows,
        "hardware": hw,
    }


# ----------------------------------------------------------------------------- files
def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists() or dst.stat().st_size != src.stat().st_size or dst.stat().st_mtime < src.stat().st_mtime:
        shutil.copy2(src, dst)
    return dst


def entry(path, desc, src):
    st = path.stat()
    return {"name": path.name, "href": str(path.relative_to(SITE)), "bytes": st.st_size,
            "sha256": sha256(path), "desc": desc, "source": src}


def build_files():
    dl = SITE / "downloads"
    docs = SITE / "docs"
    downloads, documents, skipped = [], [], []

    for p, d in [(BOM_MAIN, "Electronics BOM (LCSC starter, per reference)"),
                 (BOM_JLC, "Assembly BOM grouped by LCSC code (JLC format)"),
                 (BOM_HW, "Hardware and mechanical buy list"),
                 (BOM_CAND, "Old candidate-fix rows (history)")]:
        if p.exists():
            downloads.append(entry(copy(p, dl / p.name), d, rel(p)))
    pdf = REPO / "ai-files/DesktopSpeaker-preview.pdf"
    if pdf.exists():
        downloads.append(entry(copy(pdf, dl / "DesktopSpeaker-schematic.pdf"), "Schematic preview PDF (all sheets)", rel(pdf)))
    # v11 print files and STEP only while the CAD export (cad/downloads/, newer) is not published
    with_v11 = "--with-v11-cad" in sys.argv or not (SITE / "cad" / "downloads" / "SHA256SUMS").exists()
    for stale in ([] if with_v11 else list(dl.glob("*.stl")) + list(dl.glob("*_v11.step.zip"))):
        stale.unlink()
    for stl in (sorted((REPO / "ai-files/cad/print").glob("*.stl")) if with_v11 else []):
        downloads.append(entry(copy(stl, dl / stl.name), "Print file, enclosure CAD v11 (2026-10-12)", rel(stl)))
    step = REPO / "ai-files/cad/DesktopSpeaker_internal.step"
    if step.exists() and with_v11:
        z = dl / "DesktopSpeaker_internal_v11.step.zip"
        if not z.exists() or z.stat().st_mtime < step.stat().st_mtime:
            with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                zf.write(step, step.name)
        downloads.append(entry(z, "Enclosure + board assembly STEP, CAD v11 (zipped, %.0f MB unzipped)"
                               % (step.stat().st_size / 1e6), rel(step)))

    reports = list(REPORTS)
    specs = SITE / "data" / "specs.json"
    if specs.exists():  # documents named in the curated facts file are published too
        known = {p for p, _ in reports}
        for d in json.loads(specs.read_text()).get("documents", []):
            if d.get("path") and d["path"] not in known:
                reports.append((d["path"], d.get("what") or d.get("title") or ""))
                known.add(d["path"])
    for path, desc in reports:
        p = REPO / path
        if p.stat().st_size > MAX_DOC if p.exists() else False:
            skipped.append({"name": path, "why": "larger than 5 MB"})
            continue
        if not p.exists():
            skipped.append({"name": path, "why": "missing"})
            continue
        name = p.name if p.name not in ("README.md",) else "cad-README.md"
        documents.append(dict(entry(copy(p, docs / name), desc, path), kind="report"))
    for name, desc in DATASHEETS:
        p = (REPO / "ai-files/datasheets" / name).resolve()
        if not p.exists():
            skipped.append({"name": name, "why": "missing"})
            continue
        if p.stat().st_size > MAX_DOC:
            documents.append({"name": p.name, "href": None, "bytes": p.stat().st_size, "sha256": None,
                              "desc": desc, "source": rel(p), "kind": "datasheet",
                              "note": "Larger than 5 MB: not copied; in the repo at " + rel(p)})
            continue
        documents.append(dict(entry(copy(p, docs / p.name), desc, rel(p)), kind="datasheet"))
    for missing in ("TPS61088 datasheet (only a layout excerpt is saved)", "PESD5V0S2BT datasheet (download blocked)"):
        skipped.append({"name": missing, "why": "not in the repo"})

    renders = []
    captions = {
        "assembled_front_right": "Assembled, front right", "assembled_rear_left": "Assembled, rear left",
        "assembled_underside": "Underside (woofer)", "exploded_front_right": "Exploded, front right",
        "exploded_rear_left": "Exploded, rear left", "open_top_view": "Open, top view",
        "print_shell": "Print body: shell (baffle down)", "print_insert": "Print body: woofer chamber insert",
        "print_lid": "Print body: rear lid", "rear_lid_drawing": "Rear lid drawing",
        "section_x0_woofer": "Section x 0 through the woofer", "section_x-41_driver": "Section x -41 through a driver",
        "section_z15_top": "Section z 15, from the top", "section_z75_top": "Section z 75, from the top",
    }
    for png in sorted((REPO / "ai-files/cad/renders").glob("*.png")):
        out = copy(png, SITE / "img" / png.name)
        renders.append({"href": str(out.relative_to(SITE)), "caption": "CAD v11: " + captions.get(png.stem, png.stem.replace("_", " ")),
                        "source": rel(png)})

    with open(dl / "SHA256SUMS", "w") as f:
        for e in downloads:
            f.write(f"{e['sha256']}  {e['name']}\n")
    with open(docs / "SHA256SUMS", "w") as f:
        for e in documents:
            if e.get("sha256"):
                f.write(f"{e['sha256']}  {e['name']}\n")
    return {"generated": datetime.date.today().isoformat(), "tool": TOOL_NOTE,
            "downloads": downloads, "documents": documents, "renders": renders, "not_available": skipped}


def main():
    if not SITE.exists():
        sys.exit(f"site folder missing: {SITE}")
    (SITE / "data").mkdir(exist_ok=True)
    refmap = parse_schematics()
    bom = build_bom(refmap)
    bom["schematic_refs"] = len(refmap)
    with open(SITE / "data/bom.json", "w") as f:
        json.dump(bom, f, indent=1)
    files = build_files()
    with open(SITE / "data/files.json", "w") as f:
        json.dump(files, f, indent=1)
    s = bom["summary"]
    print(f"bom.json: {s['lines']} lines, {s['placements_listed']} placements, status {s['status_counts']}, "
          f"partial fitted ${s['fitted_usd_partial']} / order ${s['order_usd_partial']}, "
          f"{len(s['unpriced_lines'])} unpriced; schematic refs {len(refmap)}")
    print(f"files.json: {len(files['downloads'])} downloads, {len(files['documents'])} documents, "
          f"{len(files['not_available'])} not available")


if __name__ == "__main__":
    main()
