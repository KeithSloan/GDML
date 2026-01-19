from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLsolid:
    def __init__(self, obj):
        """Init"""
        if hasattr(obj, "InList"):
            for j in obj.InList:
                if hasattr(j, "OutList"):
                    ln = len(j.OutList)
                    r = indexBoolean(j.OutList, ln)
                # print('index : '+str(r))
                if r >= 0:
                    if (ln - r) >= 2:
                        # print('Tool : '+obj.Label)
                        return  # Let Placement default to 0
        # obj.setEditorMode('Placement', 2)

    def getMaterial(self):
        return self.obj.material

    def scale(self, fp):
        print(f"Rescale : {fp.scale}")
        mat = FreeCAD.Matrix()
        mat.scale(fp.scale)
        fp.Shape = fp.Shape.transformGeometry(mat)

    def execute(self, fp):
        self.createGeometry(fp)

    def __getstate__(self):
        """When saving the document this object gets stored using Python's json
        module.
        Since we have some un-serializable parts here -- the Coin stuff --
        we must define this method\
        to return a tuple of all serializable objects or None."""
        if hasattr(self, "Type"):
            # print(f"getstate : Type {self.Type}")
            return {"type": self.Type}
        elif hasattr(self.Proxy, "Type"):
            # print(f"getstate : Type {self.Proxy.Type}")
            return {"type": self.Proxy.Type}

        else:
            print(f"Error GDMLsolid should have Type")
            #print(f" self {self}")
            pass

    def __setstate__(self, arg):
        """When restoring the serialized object from document we have the
        chance to set some internals here. Since no data were serialized
        nothing needs to be done here."""
        #print(f"setstate : arg {arg} type {type(arg)}")
        # Handle bug in FreeCAD 0.21.2 handling of json
        if arg is not None and arg != {}:
            if 'type' in arg:
                self.Type = arg["type"]
            else: #elif 'Type' in arg:
                self.Type = arg["Type"]
