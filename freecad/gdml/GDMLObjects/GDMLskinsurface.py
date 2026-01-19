from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLskinsurface(GDMLcommon):
    def __init__(self, obj, name, prop):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyString", "surface", "GDMLskin", "surface property"
        ).surface = prop
        obj.Proxy = self
        self.Object = obj
