import sys
# add folder containing FreeCAD.pyd, FreeCADGui.pyd to sys.path
#sys.path.append("C:/Program Files/FreeCAD 0.18/bin") # example for Windows
#sys.path.append("/usr/lib/freecad-daily/lib") # example for Linux
#sys.path.append("/usr/lib/freecad-daily/Mod") # example for Linux
#sys.path.append("/usr/lib/freecad/lib") # example for Linux
sys.path.append("/Applications/FreeCAD_0.19-B.app/Contents/Resources/lib")
sys.path.append("/Applications/FreeCAD_0.19-B.app/Contents/Resources/lib/python3.8/site-packages") # example for Mac OS

print(sys.path)
try :
  import FreeCAD
except :
  print("FreeCAD module not found - Update the sys.path.append in this script")
  exit(0)
import FreeCADGui
import Part
#import PySide2
import Draft
import Import


if len(sys.argv)<3:
  print ("Usage: sys.argv[0] <in_file> <out_file>")
  sys.exit(1)

iname=sys.argv[1]
oname=sys.argv[2]

print('Importing : '+iname)
FreeCAD.loadFile(iname)

# iterate through all objects
for o in App.ActiveDocument.Objects:
  # find root object and export the shape
  #print(dir(o))
  #print(o.Name)
  if o.TypeId == 'App::Part' :
     #print(o.TypeId) 
     print('Exporting STEP file : '+oname)
     print('This can be a very slow process')
     print('for large files Please be patient')
     #Import.export([o],"/tmp/test4.step")
     Import.export([o],oname)
     sys.exit(0)

sys.exit(0)

print ("Error: can't find any object")
sys.exit(1)

