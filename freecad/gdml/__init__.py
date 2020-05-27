import FreeCAD
FreeCAD.addImportType("GDML (*.gdml)","freecad.gdml.importGDML")
FreeCAD.addImportType("GDML (*.xml)","freecad.gdml.importGDML")
FreeCAD.addExportType("GDML (*.gdml)","freecad.gdml.exportGDML")
FreeCAD.addExportType("GDML (*.GDML)","freecad.gdml.exportGDML")
FreeCAD.addExportType("XML (*.XML)","freecad.gdml.exportGDML")
FreeCAD.addExportType("XML (*.xml)","freecad.gdml.exportGDML")
FreeCAD.addExportType("GAMOS (*.gamos)","freecad.gdml.exportGAMOS")
