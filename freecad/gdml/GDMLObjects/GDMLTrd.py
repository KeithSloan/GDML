from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLTrd(GDMLsolid):
    def __init__(self, obj, z, x1, x2, y1, y2, lunit, material, colour=None):
        super().__init__(obj)
        "3.4.15 : Trapezoid – x & y varying along z"
        obj.addProperty("App::PropertyFloat", "z", "GDMLTrd", "z").z = z
        obj.addProperty(
            "App::PropertyFloat", "x1", "GDMLTrd", "Length x at face -z/2"
        ).x1 = x1
        obj.addProperty(
            "App::PropertyFloat", "x2", "GDMLTrd", "Length x at face +z/2"
        ).x2 = x2
        obj.addProperty(
            "App::PropertyFloat", "y1", "GDMLTrd", "Length y at face -z/2"
        ).y1 = y1
        obj.addProperty(
            "App::PropertyFloat", "y2", "GDMLTrd", "Length y at face +z/2"
        ).y2 = y2
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTrd", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLTrd", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        obj.Proxy = self
        self.Type = "GDMLTrd"
        obj.Proxy.Type = "GDMLTrd"
        self.colour = colour

    def onChanged(self, fp, prop):
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

        if prop in ["z", "x1", "x2", "y1", "y2", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        GDMLShared.trace("x2  : " + str(fp.x2))

        mul = GDMLShared.getMult(fp)
        x1 = (fp.x1 * mul) / 2
        x2 = (fp.x2 * mul) / 2
        y1 = (fp.y1 * mul) / 2
        y2 = (fp.y2 * mul) / 2
        z = (fp.z * mul) / 2
        v1 = FreeCAD.Vector(-x1, -y1, -z)
        v2 = FreeCAD.Vector(-x1, +y1, -z)
        v3 = FreeCAD.Vector(x1, +y1, -z)
        v4 = FreeCAD.Vector(x1, -y1, -z)

        v5 = FreeCAD.Vector(-x2, -y2, z)
        v6 = FreeCAD.Vector(-x2, +y2, z)
        v7 = FreeCAD.Vector(x2, +y2, z)
        v8 = FreeCAD.Vector(x2, -y2, z)
        # Make the wires/faces
        f1 = make_face4(v1, v2, v3, v4)
        f2 = make_face4(v1, v2, v6, v5)
        f3 = make_face4(v2, v3, v7, v6)
        f4 = make_face4(v3, v4, v8, v7)
        f5 = make_face4(v1, v4, v8, v5)
        f6 = make_face4(v5, v6, v7, v8)
        shell = Part.makeShell([f1, f2, f3, f4, f5, f6])
        solid = Part.makeSolid(shell)

        # solid = Part.makePolygon([v1,v2,v3,v4,v5,v6,v7,v1])

        fp.Shape = solid
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
