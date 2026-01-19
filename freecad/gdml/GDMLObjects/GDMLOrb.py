from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLOrb(GDMLsolid):
    def __init__(self, obj, r, lunit, material, colour=None):
        super().__init__(obj)
        """Add some custom properties for Polyhedra feature"""
        obj.addProperty("App::PropertyFloat", "r", "GDMLOrb", "Radius").r = r
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLOrb", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLOrb", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLOrb"
        self.Object = obj
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLOrb"

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        if "Restore" in fp.State:
            return

        if prop in ["material"]:
            if FreeCAD.GuiUp:
                if hasattr(self, "colour"):
                    if self.colour is None:
                        fp.ViewObject.ShapeColor = colourMaterial(fp.material)
                if fp.material == "G4_AIR":
                    print("Set Transparency")
                    fp.ViewObject.Transparency = 98

        if prop in ["r", "lunit"]:
            # print(dir(fp))
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        # GDMLShared.setTrace(True)
        GDMLShared.trace("Execute Orb")
        mul = GDMLShared.getMult(fp.lunit)
        r = mul * fp.r
        fp.Shape = Part.makeSphere(r)
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
