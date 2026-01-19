from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLTwistedbox(GDMLsolid):
    def __init__(
        self, obj, PhiTwist, x, y, z, aunit, lunit, material, colour=None
    ):
        super().__init__(obj)
        """Add some custom properties to our Box feature"""
        GDMLShared.trace("GDMLTwistedbox init")
        # GDMLShared.trace("material : "+material)
        obj.addProperty(
            "App::PropertyFloat", "x", "GDMLTwistedbox", "Length x"
        ).x = x
        obj.addProperty(
            "App::PropertyFloat", "y", "GDMLTwistedbox", "Length y"
        ).y = y
        obj.addProperty(
            "App::PropertyFloat", "z", "GDMLTwistedbox", "Length z"
        ).z = z
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
            "App::PropertyFloat", "PhiTwist", "GDMLTwistedbox", "Twist Angle"
        ).PhiTwist = angle
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLTwistedbox", "aunit"
        )
        setAngleQuantity(obj, aunit)
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTwistedbox", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLTwistedbox",
            "Material",
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLTwistedbox"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLTwistedbox"

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

        if prop in ["x", "y", "z", "PhiTwist", "lunit", "aunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        # print('createGeometry')
        # print(fp)

        if all((fp.x, fp.y, fp.z, fp.PhiTwist)):
            currPlacement = fp.Placement

            # if (hasattr(fp,'x') and hasattr(fp,'y') and hasattr(fp,'z')) :
            mul = GDMLShared.getMult(fp)
            GDMLShared.trace("mul : " + str(mul))
            x = mul * fp.x
            y = mul * fp.y
            z = mul * fp.z
            angle = getAngleDeg(fp.aunit, fp.PhiTwist)
            # lower rectanngle vertexes
            v1 = FreeCAD.Vector(-x / 2, -y / 2, -z / 2)
            v2 = FreeCAD.Vector(x / 2, -y / 2, -z / 2)
            v3 = FreeCAD.Vector(x / 2, y / 2, -z / 2)
            v4 = FreeCAD.Vector(-x / 2, y / 2, -z / 2)
            pbot = Part.makePolygon([v1, v2, v3, v4, v1])
            slices = []
            N = 5
            dz = z / (N - 1)
            dPhi = angle / (N - 1)
            for i in range(0, N):
                p = pbot.translated(FreeCAD.Vector(0, 0, i * dz))
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
