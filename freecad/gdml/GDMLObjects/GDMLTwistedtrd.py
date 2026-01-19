from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLTwistedtrd(GDMLsolid):
    def __init__(
        self,
        obj,
        PhiTwist,
        z,
        x1,
        x2,
        y1,
        y2,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        "3.4.15 : Trapezoid – x & y varying along z"
        obj.addProperty("App::PropertyFloat", "z", "GDMLTwistedtrd", "z").z = z
        obj.addProperty(
            "App::PropertyFloat",
            "x1",
            "GDMLTwistedtrd",
            "Length x at face -z/2",
        ).x1 = x1
        obj.addProperty(
            "App::PropertyFloat",
            "x2",
            "GDMLTwistedtrd",
            "Length x at face +z/2",
        ).x2 = x2
        obj.addProperty(
            "App::PropertyFloat",
            "y1",
            "GDMLTwistedtrd",
            "Length y at face -z/2",
        ).y1 = y1
        obj.addProperty(
            "App::PropertyFloat",
            "y2",
            "GDMLTwistedtrd",
            "Length y at face +z/2",
        ).y2 = y2
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTwistedtrd", "lunit"
        )
        angle = getAngleDeg(aunit, PhiTwist)
        if angle > 90:
            print("PhiTwist angle cannot be larger than 90 deg")
            angle = 90
            aunit = "deg"
        elif angle < -90:
            print("PhiTwist angle cannot be less than -90 deg")
            angle = -90
            aunit = "deg"
        else:
            angle = PhiTwist

        obj.addProperty(
            "App::PropertyFloat", "PhiTwist", "GDMLTwistedtrd", "Twist Angle"
        ).PhiTwist = angle
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLTwistedtrd", "aunit"
        )
        setAngleQuantity(obj, aunit)
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLTwistedtrd",
            "Material",
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLTwistedtrd"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLTwistedtrd"

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # Changing Shape in createGeometry will redrive onChanged
        if "Restore" in fp.State:
            return

        if prop in ["material"]:
            if FreeCAD.GuiUp:
                if self.colour is None:
                    fp.ViewObject.ShapeColor = colourMaterial(fp.material)
                if fp.material == "G4_AIR":
                    print("G4_AIR - Set Transparency 98")
                    fp.ViewObject.Transparency = 98

        if prop in ["x1", "y1", "x2", "y2", "z", "PhiTwist", "lunit", "aunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)
            super().scale(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        # print('createGeometry')
        # print(fp)

        if all((fp.x1, fp.x2, fp.y1, fp.y2, fp.z, fp.PhiTwist)):
            currPlacement = fp.Placement

            # if (hasattr(fp,'x') and hasattr(fp,'y') and hasattr(fp,'z')) :
            mul = GDMLShared.getMult(fp)
            x1 = fp.x1 * mul
            x2 = fp.x2 * mul
            y1 = fp.y1 * mul
            y2 = fp.y2 * mul
            z = fp.z * mul
            GDMLShared.trace("mul : " + str(mul))
            angle = getAngleDeg(fp.aunit, fp.PhiTwist)
            slices = []
            N = 9  # number of slices
            dz = z / (N - 1)
            dPhi = angle / (N - 1)
            for i in range(0, N):
                t = i * 1.0 / (N - 1)
                xside = x1 + t * (x2 - x1)
                yside = y1 + t * (y2 - y1)
                v1 = FreeCAD.Vector(-xside / 2, -yside / 2, -z / 2 + i * dz)
                v2 = FreeCAD.Vector(xside / 2, -yside / 2, -z / 2 + i * dz)
                v3 = FreeCAD.Vector(xside / 2, yside / 2, -z / 2 + i * dz)
                v4 = FreeCAD.Vector(-xside / 2, yside / 2, -z / 2 + i * dz)
                p = Part.makePolygon([v1, v2, v3, v4, v1])
                p.rotate(
                    FreeCAD.Vector(0, 0, 0),
                    FreeCAD.Vector(0, 0, 1),
                    -angle / 2 + i * dPhi,
                )
                slices.append(p)

            loft = Part.makeLoft(slices, True, False)
            fp.Shape = loft
            if hasattr(fp, "scale"):
                super().scale(fp)
            fp.Placement = currPlacement

    def OnDocumentRestored(self, obj):
        print("Doc Restored")
