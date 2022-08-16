import sys
# add folder containing FreeCAD.pyd, FreeCADGui.pyd to sys.path
#sys.path.append("C:/Program Files/FreeCAD 0.18/bin") # example for Windows
sys.path.append("/usr/lib/freecad-daily/lib") # example for Linux
sys.path.append("/usr/lib/freecad-daily/Mod") # example for Linux
#sys.path.append("/usr/lib/freecad/lib") # example for Linux
import FreeCAD
import FreeCADGui
import Part
import Draft
import Import


if len(sys.argv)<3:
  print ("Usage: sys.argv[0] <in_file> <out_file>")
  sys.exit(1)

iname=sys.argv[1]
oname=sys.argv[2]

print('Importing : '+iname)
FreeCAD.loadFile(iname)

#print(dir(App.ActiveDocument))
App.ActiveDocument.saveAs(oname)

sys.exit(0)

print ("Error: can't find any object")
sys.exit(1)

