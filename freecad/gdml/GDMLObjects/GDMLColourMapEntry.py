from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLColourMapEntry:
    def __init__(self, obj, colour, material):
        obj.addProperty(
            "App::PropertyColor", "colour", "GDMLColourMapEntry", "colour"
        ).colour = colour
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLColourMapEntry",
            "Material",
        )
        setMaterial(obj, material)
