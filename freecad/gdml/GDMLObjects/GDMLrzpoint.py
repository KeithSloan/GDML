from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLrzpoint(GDMLcommon):
    def __init__(self, obj, r, z):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyFloat", "r", "rzpoint", "r-coordinate"
        ).r = r
        obj.addProperty(
            "App::PropertyFloat", "z", "rzpoint", "z-coordinate"
        ).z = z
        self.Type = "zplane"
        obj.Proxy = self
        obj.Proxy.Type = "zplane"

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # if not ('Restore' in fp.State) :
        # if prop in ['rmin','rmax','z'] :
        #   self.execute(fp)
        # GDMLShared.trace("Change property: " + str(prop) + "\n")
        pass

    def execute(self, fp):
        pass
