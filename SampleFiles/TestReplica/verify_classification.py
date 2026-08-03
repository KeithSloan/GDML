#!/usr/bin/env python3
"""Parse each test GDML, build (signatures, points) from its physvols, and
assert testReplica.classify reports the intended category."""
import xml.etree.ElementTree as ET, os, sys
from testReplica import classify, report_text, REPLICA, PARAM_ID, COMPLEX

D = os.path.dirname(os.path.abspath(__file__))
EXPECT = {
    "VeloFlat.gdml":            PARAM_ID,
    "TestReplica.gdml":     REPLICA,
    "VeloTestParamVol.gdml":    PARAM_ID,
    "ComplexParamVol.gdml": COMPLEX,
}
fails = []
for fn, want in EXPECT.items():
    root = ET.parse(os.path.join(D, fn)).getroot()
    solids = {s.get("name"): s for s in root.find("solids")}
    vols = {v.get("name"): v for v in root.find("structure").findall("volume")}
    sigs, pts = [], []
    for pv in root.find("structure").iter("physvol"):
        ref = pv.find("volumeref").get("ref")
        if not ref.startswith("lvRSensor"): continue
        if ref not in vols or vols[ref].find("solidref") is None:
            continue
        vol = vols[ref]
        sname = vol.find("solidref").get("ref")
        if sname not in solids:
            continue
        s = solids[sname]
        mat = vol.find("materialref").get("ref")
        # signature = solid tag + geometric attrs + material  => "identical daughter" test
        sig = (s.tag, mat, tuple(sorted((k, s.get(k)) for k in s.attrib if k != "name")))
        sigs.append(sig)
        p = pv.find("position")
        pts.append((float(p.get("x")), float(p.get("y")), float(p.get("z"))))
    r = classify(sigs, pts)
    ok = r["category"] == want
    fails.append(fn) if not ok else None
    print(f"{'PASS' if ok else 'FAIL'}  {fn:28s} -> {report_text(r)[0]:35s} (n={r['count']})")
print("\n" + ("ALL CLASSIFICATIONS AS EXPECTED" if not fails else f"MISMATCH: {fails}"))
sys.exit(1 if fails else 0)
