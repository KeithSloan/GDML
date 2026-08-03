#!/usr/bin/env python3
"""Generate 4 VELO-subset test files for the testReplica command.
Each is INDIVIDUAL placements; the header states the category testReplica
should report.  R-sensor = silicon half-disk tube (rmin 8, thick 0.3, phi 0-180).
"""
import os
D = os.path.dirname(os.path.abspath(__file__))

HDR = '''<?xml version="1.0" encoding="UTF-8"?>
<!-- {title}
     testReplica expected result: {expect} -->
<gdml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:noNamespaceSchemaLocation="http://service-spi.web.cern.ch/service-spi/app/releases/GDML/schema/gdml.xsd">
  <define/>
  <materials>
    <material name="Vacuum" Z="1"><D value="1e-25" unit="g/cm3"/><atom value="1.008"/></material>
    <material name="Silicon" Z="14"><D value="2.33" unit="g/cm3"/><atom value="28.09"/></material>
  </materials>
'''
FTR = '''  <setup name="Default" version="1.0">
    <world ref="World"/>
  </setup>
</gdml>
'''
def tube(name, rmax):
    return f'    <tube name="{name}" rmin="8" rmax="{rmax}" z="0.3" startphi="0" deltaphi="180" aunit="deg" lunit="mm"/>\n'
def box(name, x, y, z):
    return f'    <box name="{name}" x="{x}" y="{y}" z="{z}" lunit="mm"/>\n'

def make(fname, title, expect, copies):
    """copies: list of (z, rmax). Identical daughters => shared volume."""
    rmaxes = sorted(set(r for _, r in copies))
    identical = len(rmaxes) == 1
    x = HDR.format(title=title, expect=expect)
    x += "  <solids>\n"
    if identical:
        x += tube("rSensor", rmaxes[0])
    else:
        for r in rmaxes:
            x += tube(f"rSensor{int(r)}", r)
    x += box("veloBox", 160, 160, 1600)
    x += box("worldBox", 240, 240, 2000)
    x += "  </solids>\n  <structure>\n"
    if identical:
        x += '    <volume name="lvRSensor"><materialref ref="Silicon"/><solidref ref="rSensor"/></volume>\n'
    else:
        for r in rmaxes:
            x += (f'    <volume name="lvRSensor{int(r)}"><materialref ref="Silicon"/>'
                  f'<solidref ref="rSensor{int(r)}"/></volume>\n')
    x += '    <volume name="lvVelo">\n      <materialref ref="Vacuum"/>\n      <solidref ref="veloBox"/>\n'
    for i, (z, r) in enumerate(copies):
        vol = "lvRSensor" if identical else f"lvRSensor{int(r)}"
        x += (f'      <physvol name="pv_{i:02d}"><volumeref ref="{vol}"/>'
              f'<position name="p_{i:02d}" x="0" y="0" z="{z}" unit="mm"/></physvol>\n')
    x += '    </volume>\n'
    x += ('    <volume name="World">\n      <materialref ref="Vacuum"/>\n      <solidref ref="worldBox"/>\n'
          '      <physvol name="pvVelo"><volumeref ref="lvVelo"/></physvol>\n    </volume>\n')
    x += "  </structure>\n" + FTR
    open(os.path.join(D, fname), "w").write(x)
    print(f"wrote {fname:28s} ({len(copies)} copies, identical={identical})")

# real R-side z's
z_reg  = [-175.0 + 30*i for i in range(16)]
z_down = [435.0, 585.0, 635.0, 685.0, 735.0]

# 1. VeloFlat : full R-side, identical, overall irregular -> Param Volume identical
make("VeloFlat.gdml", "VeloFlat : full R-side cut-down VELO, individual placements",
     "Param Volume / identical Daughters",
     [(z, 42.0) for z in z_reg + z_down])

# 2. A valid TestReplica : identical daughters, uniform 30 mm pitch -> Param Replica
make("TestReplica.gdml", "TestReplica : identical sensors, uniform 30 mm pitch",
     "Param Replica (linear, pitch 30, axis z)",
     [(z, 42.0) for z in z_reg])

# 3. VeloTestParamVol : identical daughters, irregular spacing -> Param Volume identical
make("VeloTestParamVol.gdml", "VeloTestParamVol : identical sensors, irregular spacing",
     "Param Volume / identical Daughters",
     [(z, 42.0) for z in [-200,-150,-120,-60,-20,40,90,160,240]])

# 4. A valid but Complex TestParamVol : varying daughters (graded rmax) -> Complex
make("ComplexParamVol.gdml", "ComplexParamVol : graded sensors (rmax varies per copy)",
     "Param Volume / Complex (daughters differ)",
     [(-175.0 + 30*i, 42.0 + 2*i) for i in range(8)])
