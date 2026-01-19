from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLquantity(GDMLcommon):
    def __init__(self, obj, name, type, unit, value):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyString", "name", "GDMLvariable", "name"
        ).name = name
        obj.addProperty(
            "App::PropertyString", "type", "GDMLvariable", "type"
        ).type = type
        obj.addProperty(
            "App::PropertyString", "unit", "GDMLvariable", "unit"
        ).unit = unit
        obj.addProperty(
            "App::PropertyString", "value", "GDMLvariable", "value"
        ).value = value
        obj.Proxy = self
        self.Object = obj
