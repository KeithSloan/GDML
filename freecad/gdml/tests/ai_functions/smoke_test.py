"""Smoke test for the GDMLDesign scripting API (branch AI_Functions).

Run inside FreeCAD with the GUI (Python console, a macro, or the FreeCAD
MCP execute_code tool).  This line works wherever the workbench is
installed (Addon Manager or git):

    import os, freecad.gdml as g; exec(open(os.path.join(os.path.dirname(g.__file__), "tests", "ai_functions", "smoke_test.py")).read())

It builds a small design using every kind of call, checks the results,
exports ai_functions_smoke.gdml to the system temp folder and prints
PASS/FAIL lines.
"""
import os
import tempfile

from freecad.gdml import GDMLDesign as gd

results = []


def check(label, cond):
    results.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + label)


def raises(label, fn, exc=ValueError):
    try:
        fn()
    except exc as e:
        check(f"{label} -> {e}", True)
        return
    check(f"{label} (no exception)", False)


doc = gd.newDocument("AI_Functions_Smoke")
world = gd.getWorld(doc)
check("world exists", world is not None)
check("world material G4_AIR", gd.describe(world)["solid"]["material"] == "G4_AIR")

# --- materials --------------------------------------------------------
check("listMaterials finds G4_Pb", "G4_Pb" in gd.listMaterials("g4_pb"))
check("glob search", "G4_WATER" in gd.listMaterials("G4_WAT*"))
raises("unknown material suggests matches",
       lambda: gd.makeBox(10, 10, 10, material="G4_LEAD"))
gd.addMaterial("Scint", "1.032 g/cm3", formula="C9H10")
gd.addMaterial("Brass", 8.5, mixture="0.7 G4_Cu + 0.3 G4_Zn")
check("custom materials listed",
      {"Scint", "Brass"} <= set(gd.listMaterials()))

# --- solids -----------------------------------------------------------
box = gd.makeBox(100, 80, 10, material="G4_Pb", name="Absorber",
                 position=(0, 0, 50), colour="grey")
check("box volume named", gd.getVolume(box).Label == "Absorber")
check("box size", gd.describe(box)["size_mm"] == (100.0, 80.0, 10.0))
check("box placed on volume",
      gd.describe(gd.getVolume(box))["position_mm"] == (0.0, 0.0, 50.0))
raises("duplicate name", lambda: gd.makeBox(1, 1, 1, material="G4_Pb",
                                             name="Absorber"))
check("failed call left no debris",
      len(doc.getObjectsByLabel("Absorber")) == 1)

cone = gd.makeCone(rmin1=0, rmax1=10, rmin2=0, rmax2=5, z=20,
                   material="Brass", name="Cone", position=(0, 0, -50))
p = gd.describe(cone)["params"]
check("cone keyword args land on the right properties",
      (p["rmin1"], p["rmax1"], p["rmin2"], p["rmax2"]) == (0, 10, 0, 5))

tube = gd.makeTube(0, 2, 3, lunit="cm", material="Scint",
                   position=(0, 0, -10), rotation=(90, 0, 0))
check("tube lunit cm", gd.describe(tube)["lunit"] == "cm")
check("position uses lunit",
      gd.describe(gd.getVolume(tube))["position_mm"] == (0.0, 0.0, -100.0))
check("rotation round-trips",
      gd.describe(gd.getVolume(tube))["rotation_xyz_deg"] == (90.0, 0.0, 0.0))

others = [
    gd.makeSphere(5, 10, material="G4_Fe"),
    gd.makeOrb(5, material="G4_Fe"),
    gd.makeEllipsoid(10, 8, 6, material="G4_Fe"),
    gd.makeElTube(10, 5, 8, material="G4_Fe"),
    gd.makeElCone(0.5, 0.3, 20, 10, material="G4_Fe"),
    gd.makeParaboloid(2, 8, 10, material="G4_Fe"),
    gd.makeHype(2, 8, 20, 10, 20, material="G4_Fe"),
    gd.makePara(10, 10, 10, alpha=10, material="G4_Fe"),
    gd.makeTrd(10, 5, 10, 5, 20, material="G4_Fe"),
    gd.makeTrap(20, 0, 0, 10, 10, 5, 5, 8, 4, 0, material="G4_Fe"),
    gd.makeTorus(0, 2, 10, material="G4_Fe"),
    gd.makeCutTube(0, 5, 20, lowNormal=(0, -0.7, -0.71),
                   highNormal=(0.7, 0, 0.71), material="G4_Fe"),
    gd.makeTwistedBox(30, 10, 10, 20, material="G4_Fe"),
    gd.makeTwistedTrd(30, 10, 5, 10, 5, 20, material="G4_Fe"),
    gd.makeTwistedTrap(30, 20, 0, 0, 10, 10, 5, 5, 8, 4, 0,
                       material="G4_Fe"),
    gd.makeTwistedTubs(30, 5, 10, 20, 90, material="G4_Fe"),
    gd.makePolycone([(0, 5, -10), (0, 10, 0), (0, 3, 10)],
                    material="G4_Fe"),
    gd.makePolyhedra(6, [(0, 5, -10), (0, 10, 10)], material="G4_Fe"),
    gd.makeGenericPolycone([(1, -5), (6, -5), (3, 5)], material="G4_Fe"),
    gd.makeGenericPolyhedra(6, [(1, -5), (6, -5), (3, 5)],
                            material="G4_Fe"),
    gd.makeXtru([(-5, -5), (-5, 5), (5, 5), (5, -5)], [-10, (10, 0, 0, 0.5)],
                material="G4_Fe"),
    gd.makeArb8(-5, -5, -5, 5, 5, 5, 5, -5, -3, -3, -3, 3, 3, 3, 3, -3, 10,
                material="G4_Fe"),
    gd.makeTetra((0, 0, 0), (10, 0, 0), (0, 10, 0), (0, 0, 10),
                 material="G4_Fe"),
    gd.makeTessellated([(0, 0, 0), (10, 0, 0), (0, 10, 0), (0, 0, 10)],
                       [(0, 2, 1), (0, 1, 3), (1, 2, 3), (0, 3, 2)],
                       material="G4_Fe"),
]
for s in others:
    check(f"{s.Proxy.Type} has geometry", not s.Shape.isNull())
check("unnamed solids get unique volume names",
      len({gd.getVolume(s).Label for s in others}) == len(others))

# --- booleans -----------------------------------------------------------
block = gd.makeBox(50, 50, 20, material="G4_W", name="Collimator",
                   position=(0, 0, 200))
hole = gd.makeTube(0, 5, 30, material="G4_W", position=(0, 0, 200))
cut = gd.makeSubtraction(block, hole)
check("subtraction in base volume",
      gd.getSolid(gd.getVolume(block)) is cut)
check("tool volume removed", gd.getVolume(hole) is gd.getVolume(block))
check("hole removed volume",
      abs(cut.Shape.Volume - (50 * 50 * 20 - 3.14159265 * 25 * 20)) < 1)

# --- assemblies, copies, sensitive detectors ------------------------------
calo = gd.makeAssembly("Calo", position=(0, 0, -300))
xtal = gd.makeBox(22, 22, 100, material="G4_PbWO4", name="Crystal",
                  parent=calo, position=(-24, 0, 0))
gd.setSensitive(xtal, "CaloSD")
for i in (1, 2):
    gd.placeCopy(xtal, parent=calo, position=(-24 + 24 * i, 0, 0),
                 copynumber=i)
check("copies", len(gd.describe(calo)["daughters"]) == 3)
raises("cannot add daughters to a copy",
       lambda: gd.makeBox(1, 1, 1, material="G4_Fe",
                          parent=doc.getObjectsByLabel("Crystal_copy1")[0]))

# --- materials can be changed ------------------------------------------
gd.assignMaterial(cut, "G4_Pb")
check("boolean material via base", gd.describe(block)["material"] == "G4_Pb")

# --- output -----------------------------------------------------------
tree = gd.designTree()
print(tree)
check("tree lists copies", "Crystal_copy2 = copy of Crystal" in tree)
path = gd.exportGDML(os.path.join(tempfile.gettempdir(),
                                  "ai_functions_smoke.gdml"))
text = open(path).read()
check("export written", os.path.getsize(path) > 0)
for tag in ("<box", "<cone", "<subtraction", "<assembly", "SensDet",
            'name="Absorber"', 'name="Absorber_solid"', "Brass"):
    check(f"export contains {tag}", tag in text)
wx = gd.describe(world)["solid"]["params"]["x"]
check("world grown to fit", wx > 100)

print(f"\n{results.count(True)} passed, {results.count(False)} failed")
print(f"GDML written to {path}")
