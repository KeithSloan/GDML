"""Create GDML geometry with a configured default material in FreeCAD."""

import os
import sys
from pathlib import Path


repository_root = Path(os.environ["GDML_REPOSITORY_ROOT"])
sys.path.insert(0, str(repository_root / "freecad"))

import FreeCAD as App
import FreeCADGui as Gui
import freecad


Gui.setupWithoutGUI()
freecad.__path__.append(str(repository_root / "freecad"))

# freecadcmd has no toolbar or active 3D view. Keep those GUI adapters outside
# the behavior under test while exercising the real command and CAD document.
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


def create_box(parent, name, material):
    volume = parent.newObject("App::Part", f"LV-{name}")
    box = volume.newObject("Part::FeaturePython", f"GDMLBox_{name}")
    GDMLBox(box, 10.0, 10.0, 10.0, "mm", material)
    return box


preferences = App.ParamGet("User parameter:BaseApp/Preferences/Mod/GDML")
previous_default = preferences.GetString("defaultMaterial", "")

try:
    preferences.SetString("defaultMaterial", "G4_Al")
    document = App.newDocument("DefaultMaterial")
    importGDML.processGDML(
        document,
        True,
        str(repository_root / "freecad/gdml/Resources/Default.gdml"),
        False,
        1,
        True,
    )
    parent, material = GDMLCommands.getSelectedPM()
    box = create_box(parent, "Box", material)
    document.recompute()

    boxes = document.getObjectsByLabel("GDMLBox_Box")
    if len(boxes) != 1:
        raise AssertionError(f"expected one new GDML box, found {len(boxes)}")
    box = boxes[0]
    if box.material != "G4_Al":
        raise AssertionError(
            f"configured default material was not used: {box.material}"
        )
    if box.Shape.isNull() or not box.Shape.isValid() or box.Shape.Volume <= 0:
        raise AssertionError("default-material command did not create valid geometry")

    selected_materials = document.getObjectsByLabel("G4_Cu")
    if len(selected_materials) != 1:
        raise AssertionError("G4_Cu material is unavailable for selection")
    Gui.Selection.objects = selected_materials
    parent, material = GDMLCommands.getSelectedPM()
    if material != "G4_Cu":
        raise AssertionError(
            f"selected material did not override the configured default: {material}"
        )

    fallback_material = box.getEnumerationsOfProperty("material")[0]
    Gui.Selection.objects = []
    preferences.SetString("defaultMaterial", "NOT_A_GDML_MATERIAL")
    parent, material = GDMLCommands.getSelectedPM()
    invalid_default_box = create_box(parent, "InvalidDefault", material)
    if invalid_default_box.material != fallback_material:
        raise AssertionError("invalid default did not preserve the existing fallback")

    preferences.RemString("defaultMaterial")
    parent, material = GDMLCommands.getSelectedPM()
    missing_default_box = create_box(parent, "MissingDefault", material)
    if missing_default_box.material != fallback_material:
        raise AssertionError("missing default did not preserve the existing fallback")

    App.closeDocument(document.Name)
finally:
    if previous_default:
        preferences.SetString("defaultMaterial", previous_default)
    else:
        preferences.RemString("defaultMaterial")

print("GDML_DEFAULT_MATERIAL=COMPLETE", flush=True)
