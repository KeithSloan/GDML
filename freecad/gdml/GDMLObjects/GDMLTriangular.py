from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLTriangular(GDMLcommon):
    def __init__(self, obj, v1, v2, v3, vtype):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyVector", "v1", "Triangular", "v1"
        ).v1 = v1
        obj.addProperty(
            "App::PropertyVector", "v2", "Triangular", "v1"
        ).v2 = v2
        obj.addProperty(
            "App::PropertyVector", "v3", "Triangular", "v1"
        ).v3 = v3
        obj.addProperty(
            "App::PropertyEnumeration", "vtype", "Triangular", "vtype"
        )
        obj.vtype = ["ABSOLUTE", "RELATIVE"]
        obj.vtype = ["ABSOLUTE", "RELATIVE"].index(vtype)
        self.Type = "GDMLTriangular"
        obj.Proxy = self
        obj.Proxy.Type = "GDMLTriangular"

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        pass

    def execute(self, fp):
        pass
