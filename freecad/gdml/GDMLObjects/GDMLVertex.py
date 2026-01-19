from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLVertex(GDMLcommon):
    def __init__(self, obj, x, y, z, lunit):
        super().__init__(obj)
        obj.addProperty("App::PropertyFloat", "x", "GDMLVertex", "x").x = x
        obj.addProperty("App::PropertyFloat", "y", "GDMLVertex", "y").y = y
        obj.addProperty("App::PropertyFloat", "z", "GDMLVertex", "z").z = z
        self.Type = "GDMLVertex"
        self.Object = obj
        obj.Proxy = self
        obj.Proxy.Type = "GDMLVertex"

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # if not ('Restore' in fp.State) :
        #   if prop in ['x','y', 'z'] :
        #      self.execute(fp)
        # GDMLShared.trace("Change property: " + str(prop) + "\n")
        pass

    def execute(self, fp):
        pass
