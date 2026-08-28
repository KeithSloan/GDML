"""Exercise GDML external-file import through the real workbench interface."""

import os
import sys
from pathlib import Path


repository_root = Path(os.environ["GDML_REPOSITORY_ROOT"])
fixture_directory = Path(os.environ["GDML_EXTERNAL_FILE_FIXTURES"])
sys.path.insert(0, str(repository_root / "freecad"))

import FreeCAD as App
import FreeCADGui as Gui
import freecad


Gui.setupWithoutGUI()
freecad.__path__.append(str(repository_root / "freecad"))

from freecad.gdml import importGDML


def one_object(document, label):
    matches = document.getObjectsByLabel(label)
    if len(matches) != 1:
        raise AssertionError(
            f"expected one object labelled {label!r}, found {len(matches)}"
        )
    return matches[0]


def assert_valid_solid(obj):
    shape = obj.Shape
    if shape.isNull():
        raise AssertionError(f"{obj.Label} has a null CAD shape")
    if not shape.isValid():
        raise AssertionError(f"{obj.Label} has an invalid CAD shape")
    if shape.Volume <= 0:
        raise AssertionError(f"{obj.Label} has no solid volume")


document = importGDML.open(
    str(fixture_directory / "assembly.gdml"), processType=1, prompt=False
)
document.recompute()

external_world = one_object(document, "LV_partWorld")
external_solid = one_object(document, "GDMLBox_partWorld")
external_child = one_object(document, "LV_part")
external_child_solid = one_object(document, "GDMLBox_Part")
inline_volume = one_object(document, "LV_inline")
inline_solid = one_object(document, "GDMLBox_Inline")

for solid in (external_solid, external_child_solid, inline_solid):
    assert_valid_solid(solid)

if external_solid not in external_world.OutList:
    raise AssertionError("external world solid is not owned by the external world")
if external_child not in external_world.OutList:
    raise AssertionError("external child volume is not owned by the external world")
if external_child_solid not in external_child.OutList:
    raise AssertionError("external child solid is not owned by its logical volume")
if inline_solid not in inline_volume.OutList:
    raise AssertionError("parent-file volume import used the external file context")

position = external_world.Placement.Base
if (position.x, position.y, position.z) != (10.0, 20.0, 30.0):
    raise AssertionError(f"external file placement was not applied: {position}")

App.closeDocument(document.Name)

document = importGDML.open(
    str(fixture_directory / "assembly_volname.gdml"),
    processType=1,
    prompt=False,
)
document.recompute()

selected_volume = one_object(document, "LV_part")
selected_solid = one_object(document, "GDMLBox_Part")
assert_valid_solid(selected_solid)
if selected_solid not in selected_volume.OutList:
    raise AssertionError("file@volname did not import the selected logical volume")
if document.getObjectsByLabel("LV_partWorld"):
    raise AssertionError("file@volname was ignored in favour of the setup world")

position = selected_volume.Placement.Base
if (position.x, position.y, position.z) != (40.0, 50.0, 60.0):
    raise AssertionError(f"file@volname placement was not applied: {position}")

App.closeDocument(document.Name)
print("GDML_EXTERNAL_FILE_IMPORT=COMPLETE", flush=True)
