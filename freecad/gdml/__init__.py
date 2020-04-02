import FreeCAD
FreeCAD.addImportType("GDML (*.gdml)","freecad.gdml.importGDML")
FreeCAD.addImportType("OBJ (*.obj)","freecad.gdml.importPLY")
FreeCAD.addExportType("GDML (*.gdml)","freecad.gdml.exportGDML")
FreeCAD.addExportType("GDML (*.GDML)","freecad.gdml.exportGDML")
