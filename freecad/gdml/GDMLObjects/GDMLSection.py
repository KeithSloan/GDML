from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLSection(GDMLcommon):
    def __init__(
        self, obj, zOrder, zPosition, xOffset, yOffset, scalingFactor
    ):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyString", "Type", "section", "section"
        ).Type = "section"
        obj.addProperty(
            "App::PropertyInteger", "zOrder", "section", "zOrder"
        ).zOrder = zOrder
        obj.addProperty(
            "App::PropertyFloat", "zPosition", "section", "zPosition"
        ).zPosition = zPosition
        obj.addProperty(
            "App::PropertyFloat", "xOffset", "section", "xOffset"
        ).xOffset = xOffset
        obj.addProperty(
            "App::PropertyFloat", "yOffset", "section", "yOffset"
        ).yOffset = yOffset
        obj.addProperty(
            "App::PropertyFloat", "scalingFactor", "section", "scalingFactor"
        ).scalingFactor = scalingFactor
        obj.setEditorMode("Type", 1)
        self.Type = "section"
        obj.Proxy = self
        obj.Proxy.Type = "section"

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # if prop in ['zOrder','zPosition','xOffset','yOffset','scaleFactor'] :
        #   self.execute(fp)
        # GDMLShared.trace("Change property: " + str(prop) + "\n")
        pass

    def execute(self, fp):
        pass
