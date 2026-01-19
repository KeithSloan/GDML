from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLelement(GDMLcommon):
    def __init__(self, obj, name):
        super().__init__(obj)
        obj.addProperty("App::PropertyString", "name", name).name = name
        obj.Proxy = self
        self.Object = obj
