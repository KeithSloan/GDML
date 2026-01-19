from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLzplane(GDMLcommon):
    def __init__(self, obj, rmin, rmax, z):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyFloat", "rmin", "zplane", "Inside Radius"
        ).rmin = rmin
        obj.addProperty(
            "App::PropertyFloat", "rmax", "zplane", "Outside Radius"
        ).rmax = rmax
        obj.addProperty("App::PropertyFloat", "z", "zplane", "z").z = z
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
