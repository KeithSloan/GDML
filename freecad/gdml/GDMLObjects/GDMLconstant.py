from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLconstant(GDMLcommon):
    def __init__(self, obj, name, value):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyString", "name", "GDMLconstant", "name"
        ).name = name
        obj.addProperty(
            "App::PropertyString", "value", "GDMLconstant", "value"
        ).value = value
        obj.Proxy = self
        self.Object = obj
