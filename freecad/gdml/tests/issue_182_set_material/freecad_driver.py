"""Set Material on a logical volume must change the solid that is exported."""

import os
import re
import sys
import tempfile
from pathlib import Path


repository_root = Path(os.environ["GDML_REPOSITORY_ROOT"])
sys.path.insert(0, str(repository_root / "freecad"))

import FreeCAD as App
import FreeCADGui as Gui
import freecad


Gui.setupWithoutGUI()
freecad.__path__.append(str(repository_root / "freecad"))

# freecadcmd has no toolbar or active 3D view. Keep those GUI adapters outside
# the behavior under test while exercising the real resolution and CAD document.
if not hasattr(Gui, "addCommand"):
    Gui.addCommand = lambda name, command: None
if not hasattr(Gui, "SendMsgToActiveView"):
    Gui.SendMsgToActiveView = lambda message: None


class SelectionAdapter:
    def __init__(self):
        self.objects = []

    def getSelection(self):
        return self.objects


Gui.Selection = SelectionAdapter()

from freecad.gdml import GDMLCommands, importGDML
from freecad.gdml.GDMLObjects import GDMLBox


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def create_box(parent, name, material):
    volume = parent.newObject("App::Part", f"LV-{name}")
    box = volume.newObject("Part::FeaturePython", f"GDMLBox_{name}")
    GDMLBox(box, 10.0, 10.0, 10.0, "mm", material)
    return volume, box


document = App.newDocument("SetMaterial182")
importGDML.processGDML(
    document,
    True,
    str(repository_root / "freecad/gdml/Resources/Default.gdml"),
    False,
    1,
    True,
)
world = document.getObject("worldVOL")

# Plain volume: LV -> GDMLBox
lv_box, box = create_box(world, "Box", "G4_AIR")

# Volume holding a boolean: LV -> Cut(Base=A, Tool=B)
lv_cut = world.newObject("App::Part", "LV-Cut")
base = lv_cut.newObject("Part::FeaturePython", "GDMLBox_A")
GDMLBox(base, 20.0, 20.0, 20.0, "mm", "G4_AIR")
tool = lv_cut.newObject("Part::FeaturePython", "GDMLBox_B")
GDMLBox(tool, 5.0, 5.0, 40.0, "mm", "G4_AIR")
cut = lv_cut.newObject("Part::Cut", "Cut")
cut.Base = base
cut.Tool = tool

# A physvol (App::Link) placing the boolean volume again
link = world.newObject("App::Link", "LinkToCut")
link.LinkedObject = lv_cut
document.recompute()

# App::Part answers hasattr(..., "Shape") via Part.getShape - this is why
# Set Material accepted the LV and gave it an unused 'material' (#182).
check(hasattr(lv_box, "Shape"), "App::Part no longer exposes Shape")

targets, volumes = GDMLCommands._resolveMaterialTargets([lv_box])
check(targets == [box], f"LV-Box resolved to {[t.Label for t in targets]}")
check(volumes == [lv_box], "LV-Box not reported as a volume")

targets, volumes = GDMLCommands._resolveMaterialTargets([lv_cut])
check(targets == [base], f"LV-Cut resolved to {[t.Label for t in targets]}")

targets, volumes = GDMLCommands._resolveMaterialTargets([link])
check(targets == [base], f"Link resolved to {[t.Label for t in targets]}")
check(volumes == [lv_cut], "Link did not resolve to its volume")

# A solid selected directly is still set directly
targets, _ = GDMLCommands._resolveMaterialTargets([box, lv_box])
check(targets == [box], "direct solid + its LV should give the solid once")

# The volume's material in the exported GDML follows the resolved solid
box.material = "G4_Pb"
base.material = "G4_WATER"
from freecad.gdml import exportGDML

Gui.Selection.objects = [world]
out = Path(tempfile.mkdtemp()) / "issue182.gdml"
exportGDML.export([world], str(out))
volumes_xml = dict(
    re.findall(
        r'<volume name="([^"]+)">\s*<materialref ref="([^"]+)"',
        out.read_text(),
    )
)
check(volumes_xml.get("LV_Box") == "G4_Pb", f"LV_Box exported {volumes_xml}")
check(volumes_xml.get("LV_Cut") == "G4_WATER", f"LV_Cut exported {volumes_xml}")

App.closeDocument(document.Name)
print("GDML_SET_MATERIAL_182=COMPLETE", flush=True)
