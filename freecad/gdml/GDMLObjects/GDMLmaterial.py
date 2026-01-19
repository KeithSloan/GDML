from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLmaterial(GDMLcommon):
    def __init__(
        self, obj, name, density=1.0, conduct=2.0, expand=3.0, specific=4.0
    ):
        super().__init__(obj)
        # Add most properties later
        obj.addProperty(
            "App::PropertyString", "name", "GDMLmaterial", "name"
        ).name = name
        obj.addProperty(
            "App::PropertyFloat", "density", "GDMLmaterial", "Density kg/m^3"
        ).density = density
        obj.addProperty(
            "App::PropertyFloat",
            "conduct",
            "GDMLmaterial",
            "Thermal Conductivity W/m/K",
        ).conduct = conduct
        obj.addProperty(
            "App::PropertyFloat",
            "expand",
            "GDMLmaterial",
            "Expansion Coefficient m/m/K",
        ).expand = expand
        obj.addProperty(
            "App::PropertyFloat",
            "specific",
            "GDMLmaterial",
            "Specific Heat J/kg/K",
        ).specific = specific

        obj.Proxy = self
        self.Object = obj
