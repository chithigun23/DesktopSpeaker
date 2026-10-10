#!/usr/bin/env python3
"""Compare two KiCad XML netlists for electrical/BOM equivalence.

Checks: component set with value, footprint, lib id and every field;
net set (name -> sorted (ref, pin, pintype)); pin -> net mapping;
libpart pin tables. Prints a JSON summary; exit 1 on any difference.
Usage: netlist_equiv.py before.xml after.xml [out.json]
"""
import json
import sys
import xml.etree.ElementTree as ET


def load(path):
    r = ET.parse(path).getroot()
    comps = {}
    for c in r.find("components"):
        ref = c.get("ref")
        lib = c.find("libsource")
        fields = {f.get("name"): (f.text or "") for f in c.iter("field")}
        comps[ref] = {
            "value": c.findtext("value"),
            "footprint": c.findtext("footprint"),
            "lib": (lib.get("lib"), lib.get("part")) if lib is not None else None,
            "fields": fields,
            "datasheet": c.findtext("datasheet"),
        }
    nets = {}
    pin2net = {}
    for n in r.find("nets"):
        name = n.get("name")
        nodes = sorted((x.get("ref"), x.get("pin"), x.get("pintype") or "") for x in n.iter("node"))
        nets[name] = nodes
        for ref, pin, _ in nodes:
            pin2net[(ref, pin)] = name
    libparts = {}
    lp = r.find("libparts")
    if lp is not None:
        for p in lp:
            pins = sorted((q.get("num"), q.get("name"), q.get("type")) for q in p.iter("pin"))
            libparts[(p.get("lib"), p.get("part"))] = pins
    return comps, nets, pin2net, libparts


def main():
    a, b = load(sys.argv[1]), load(sys.argv[2])
    res = {}
    res["components"] = {"before": len(a[0]), "after": len(b[0]),
                         "diff": sorted(k for k in set(a[0]) | set(b[0]) if a[0].get(k) != b[0].get(k))}
    res["nets"] = {"before": len(a[1]), "after": len(b[1]),
                   "diff": sorted(k for k in set(a[1]) | set(b[1]) if a[1].get(k) != b[1].get(k))}
    res["pins"] = {"before": len(a[2]), "after": len(b[2]),
                   "diff": sorted("%s.%s" % k for k in set(a[2]) | set(b[2]) if a[2].get(k) != b[2].get(k))}
    res["libparts"] = {"before": len(a[3]), "after": len(b[3]),
                       "diff": sorted("%s:%s" % k for k in set(a[3]) | set(b[3]) if a[3].get(k) != b[3].get(k))}
    res["identical"] = not any(res[k]["diff"] for k in ("components", "nets", "pins", "libparts"))
    out = json.dumps(res, indent=2)
    print(out)
    if len(sys.argv) > 3:
        open(sys.argv[3], "w").write(out + "\n")
    sys.exit(0 if res["identical"] else 1)


if __name__ == "__main__":
    main()
