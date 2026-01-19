from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLvariable(GDMLcommon):
    def __init__(self, obj, name, value):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyString", "name", "GDMLvariable", "name"
        ).name = name
        obj.addProperty(
            "App::PropertyString", "value", "GDMLvariable", "value"
        ).value = value
        obj.Proxy = self
        self.Object = obj
