from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLmatrix(GDMLcommon):
    def __init__(self, obj, name, coldim, values):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyInteger", "coldim", "GDMLmatrix", "coldin"
        ).coldim = coldim
        obj.addProperty(
            "App::PropertyString", "values", "GDMLmatrix", "values"
        ).values = values
        obj.Proxy = self
        self.Object = obj
