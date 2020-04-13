import sys

# add folder containing FreeCAD.pyd, FreeCADGui.pyd to sys.path
#sys.path.append("C:/Program Files/FreeCAD 0.18/bin") # example for Windows
sys.path.append("/usr/lib/freecad-daily/lib") # example for Linux
#sys.path.append("/usr/lib/freecad/lib") # example for Linux

import FreeCAD
import FreeCADGui
import Part
import DraftUtils

if len(sys.argv)<3:
  print ("Usage: sys.argv[0] <in_file> <out_file>")
  sys.exit(1)

iname=sys.argv[1]
oname=sys.argv[2]

import importGDML as iGDML
iGDML.open(iname)

#ImportGui.export(oname)
#FreeCAD.export(oname)
# iterate through all objects
#for o in App.ActiveDocument.Objects:
for o in FreeCAD.ActiveDocument.Objects:
  # find root object and export the shape
  if len(o.InList)==0:
      print(dir(o))
      o.ImportGui.export(oname)
  sys.exit(0)

print ("Error: can't find any object")
sys.exit(1)
