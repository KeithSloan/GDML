from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLisotope(GDMLcommon):
    def __init__(self, obj, name, N, Z):
        super().__init__(obj)
        obj.addProperty("App::PropertyString", "name", name).name = name
        obj.addProperty("App::PropertyInteger", "N", name).N = N
        obj.addProperty("App::PropertyInteger", "Z", name).Z = Z
        # Name, N and Z are minimum other values are added by import
        # obj.addProperty("App::PropertyString","unit",name).unit = unit
        # obj.addProperty("App::PropertyFloat","value",name).value = value
        obj.Proxy = self
        self.Object = obj
