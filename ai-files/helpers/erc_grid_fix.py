#!/usr/bin/env python3
"""One-shot ERC grid fix (2026-10-09). Netlist-neutral geometry snap.

Root sheet: J1 (TYPE-C-31-M-12) origin y 248.75 -> 248.92 (+0.17 mm) so every
pin lands on the 1.27 mm grid; its stub wires, labels and no-connect markers
follow (+0.17 mm in y). Stub label ends x 40.51 -> 40.64 (left) and
76.83 -> 76.20 (right) so both ends of every stub are on grid.
USB_Audio: hierarchical labels 5V_CODEC/USB_DN/USB_DP and their wire ends
x 57 -> 57.15.

Edits are limited to items identified by UUID. Refuses to run twice.
"""
import re
import sys

KI = "/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/"
DY = 0.17

ROOT_UUIDS = [
    # J1 stub wires/labels (left)
    "72f181d1-c170-4260-88d7-433348e34c1a", "91cc5953-2d5a-4da8-91d7-3f3a3826967b",
    "ca480749-a9a6-4b92-bc8b-3855967fdfaa", "bdfda1d2-05d1-4f4b-a8c7-1c5798a3f9f1",
    "d8ecbd90-8297-421f-9138-2440b7b1e7c8", "cad7003f-db8f-4859-a5f0-56656cbb8a9e",
    "75ee01ff-0ed4-4e53-8338-53a26da1c156", "385f470f-1046-4bff-8ae3-c30bfe6f3aa6",
    "75278b0c-d29b-4154-93a0-b967c4921dd3", "f5b60fa8-fa72-4870-a8f0-eaf5f5d45e79",
    "f9771fe6-3674-490a-8582-abde9e9a9111", "7072d72b-644f-413e-94e4-73f5204b1ca6",
    "76abd565-82e3-4d9f-960e-b870a5cbd673", "8505003d-7163-41c7-82c3-472c400f8eb9",
    "38549f61-c9b2-436c-9264-42e1798702ee", "a9e1fe12-6c9a-4f2e-84fa-79ecfdbb09a7",
    "ac81919d-6c37-4be5-968e-5074360e707f", "b069eda1-993e-40b8-a0f1-f158ab790bc5",
    "e02a8125-fc37-4d16-812a-bb317fabbf99", "db16aaf7-82b4-4a55-b88d-9581366acbfb",
    # right (shield) stubs
    "4403516d-ee39-425e-be9e-20c5a517e627", "9aabd67d-a92f-42a7-848f-a64f1696768a",
    "f25df0ca-1983-4c64-b8f5-76ca08db20a9", "51dc3f4f-f0dd-4468-a87c-cd3646434a9f",
    "d410a3a4-69a8-4f50-96a1-6cf98f5d37fe", "9357366d-b21f-4d63-be1c-eacde05d1c8b",
    "0e3477f3-fdab-482b-a389-7ffec205f21e", "82ce6f87-2a92-44dc-b580-b4b2cc4b5c9d",
    # no-connect markers on J1 SBU pins
    "ef6ce4e4-7174-40dc-a4fa-06d4e1990d7e", "e58555a8-afcb-488f-aa98-b66e5d8419e0",
]
J1_UUID = "a2b8bc56-f228-4bb8-a394-b10f74b026d9"
USBA_UUIDS = [
    "979d4529-687f-4e23-a7e1-85943697021e", "027cfc16-bf3c-4e94-b8e7-17324b0a55e8",
    "2f0a3ab7-ec38-4fb6-ace5-c986ad42dede", "a3b4d2d4-2026-4ae6-ab8e-6288c840ef05",
    "a9fa6c51-dff8-4850-9f88-5988751e08c7", "f7d27265-8e1e-4361-9509-f4cae4f4dc0a",
]

XMAP_ROOT = {"40.51": "40.64", "76.83": "76.2"}


def fmt(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return s


def shift_y(m):
    return "(%s %s %s" % (m.group(1), m.group(2), fmt(float(m.group(3)) + DY))


def fix_line(line, xmap, dy):
    if dy:
        line = re.sub(r"\((at|xy) ([-\d.]+) ([-\d.]+)", shift_y, line)
    def fx(m):
        return "(%s %s %s" % (m.group(1), xmap.get(m.group(2), m.group(2)), m.group(3))
    return re.sub(r"\((at|xy) ([-\d.]+) ([-\d.]+)", fx, line)


def process(path, uuids, xmap, dy, extra_line_uuid=None):
    lines = open(path).read().split("\n")
    hit = set()
    for i, line in enumerate(lines):
        for u in uuids:
            if '(uuid "%s")' % u in line:
                lines[i] = fix_line(line, xmap, dy)
                hit.add(u)
        if extra_line_uuid and line.startswith("(symbol (lib_id") and extra_line_uuid in line:
            if "(at 55.88 248.75 0)" not in line:
                sys.exit("J1 already moved; refusing to re-run")
            # move only the instance origin and its field positions (all (at ...) in the line)
            lines[i] = re.sub(r"\((at) ([-\d.]+) ([-\d.]+)", shift_y, line)
            hit.add(extra_line_uuid)
    missing = set(uuids + ([extra_line_uuid] if extra_line_uuid else [])) - hit
    if missing:
        sys.exit("missing uuids in %s: %s" % (path, missing))
    open(path, "w").write("\n".join(lines))


root = KI + "DesktopSpeaker.kicad_sch"
usba = KI + "USB_Audio.kicad_sch"
if "(xy 57 68.58)" not in open(usba).read():
    sys.exit("USB_Audio already fixed; refusing to re-run")
process(root, ROOT_UUIDS, XMAP_ROOT, DY, extra_line_uuid=J1_UUID)
process(usba, USBA_UUIDS, {"57": "57.15"}, 0)
print("done")
