import FreeCAD
FreeCAD.addImportType("GDML (*.gdml)","freecad.gdml.importGDML")
FreeCAD.addImportType("XML (*.xml)","freecad.gdml.importGDML")
FreeCAD.addExportType("GDML (*.gdml)","freecad.gdml.exportGDML")
FreeCAD.addExportType("GDML (*.GDML)","freecad.gdml.exportGDML")
FreeCAD.addExportType("XML (*.XML)","freecad.gdml.exportGDML")
FreeCAD.addExportType("XML (*.xml)","freecad.gdml.exportGDML")
FreeCAD.addExportType("GEMC - stl (*.gemc)","freecad.gdml.exportGDML")
FreeCAD.addExportType("GEMC - gdml (*.GEMC)","freecad.gdml.exportGDML")
