from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLBox(GDMLsolid):
    def __init__(self, obj, x, y, z, lunit, material, colour=None):
        super().__init__(obj)
        """Add some custom properties to our Box feature"""
        GDMLShared.trace("GDMLBox init")
        # GDMLShared.trace("material : "+material)
        obj.addProperty("App::PropertyFloat", "x", "GDMLBox", "Length x").x = x
        obj.addProperty("App::PropertyFloat", "y", "GDMLBox", "Length y").y = y
        obj.addProperty("App::PropertyFloat", "z", "GDMLBox", "Length z").z = z
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLBox", "lunit"
        )
        setLengthQuantity(obj, lunit)
        #obj.lunit = LengthQuantityList.index(lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLBox", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
            # Suppress Placement - position & Rotation via parent App::Part
            # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLBox"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLBox"

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # Changing Shape in createGeometry will redrive onChanged
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

        if prop in ["x", "y", "z", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

        # execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        # print('createGeometry')

        if (hasattr(fp,'x') and hasattr(fp,'y') and hasattr(fp,'z')) :

            currPlacement = fp.Placement
            mul = GDMLShared.getMult(fp)
            GDMLShared.trace("mul : " + str(mul))
            x = mul * fp.x
            y = mul * fp.y
            z = mul * fp.z
            box = Part.makeBox(x, y, z)
            base = FreeCAD.Vector(-x / 2, -y / 2, -z / 2)
            fp.Shape = translate(box, base)
            fp.Placement = currPlacement
        if hasattr(fp, "scale"):
            super().scale(fp)

    def OnDocumentRestored(self, obj):
        print("Doc Restored")
