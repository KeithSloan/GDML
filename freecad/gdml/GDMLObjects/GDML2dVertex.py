from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDML2dVertex(GDMLcommon):
    def __init__(self, obj, x, y):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyString", "Type", "Vertex", "twoDimVertex"
        ).Type = "twoDimVertex"
        obj.addProperty("App::PropertyFloat", "x", "Vertex", "x").x = x
        obj.addProperty("App::PropertyFloat", "y", "Vertex", "y").y = y
        obj.setEditorMode("Type", 1)
        self.Type = "Vertex"
        self.Object = obj
        obj.Proxy = self
        obj.Proxy.Type = "Vertex"

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # if prop in ['x','y'] :
        #   self.execute(fp)
        # GDMLShared.trace("Change property: " + str(prop) + "\n")
        pass

    def execute(self, fp):
        pass
