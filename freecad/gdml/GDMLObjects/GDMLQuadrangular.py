from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLQuadrangular(GDMLcommon):
    def __init__(self, obj, v1, v2, v3, v4, vtype):
        super().__init__(obj)
        obj.addProperty("App::PropertyVector", "v1", "Quadrang", "v1").v1 = v1
        obj.addProperty("App::PropertyVector", "v2", "Quadrang", "v2").v2 = v2
        obj.addProperty("App::PropertyVector", "v3", "Quadrang", "v3").v3 = v3
        obj.addProperty("App::PropertyVector", "v4", "Quadrang", "v4").v4 = v4
        obj.addProperty(
            "App::PropertyEnumeration", "vtype", "Quadrang", "vtype"
        )
        obj.vtype = ["ABSOLUTE", "RELATIVE"]
        obj.vtype = 0
        self.Type = "GDMLQuadrangular"
        obj.Proxy = self
        obj.Proxy.Type = "GDMLQuadrangular"

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        if "Restore" in fp.State:
            return

        pass

    def execute(self, fp):
        pass
