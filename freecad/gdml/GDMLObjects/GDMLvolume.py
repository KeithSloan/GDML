from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLvolume:
    def __init__(self, obj):
        obj.Proxy = self
        self.Object = obj
