from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLTwistedtrap(GDMLsolid):
    def __init__(
        self,
        obj,
        PhiTwist,
        z,
        theta,
        phi,
        x1,
        x2,
        x3,
        x4,
        y1,
        y2,
        alpha,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        """General Trapezoid"""
        obj.addProperty(
            "App::PropertyFloat", "PhiTwist", "GDMLTwistedtrap", "Twist angle"
        ).PhiTwist = PhiTwist
        obj.addProperty(
            "App::PropertyFloat", "z", "GDMLTwistedtrap", "z"
        ).z = z
        obj.addProperty(
            "App::PropertyFloat", "Theta", "GDMLTwistedtrap", "Theta"
        ).Theta = theta
        obj.addProperty(
            "App::PropertyFloat", "Phi", "GDMLTwistedtrap", "Phi"
        ).Phi = phi
        obj.addProperty(
            "App::PropertyFloat",
            "x1",
            "GDMLTwistedtrap",
            "Length x at y= -y1/2 of face at -z/2",
        ).x1 = x1
        obj.addProperty(
            "App::PropertyFloat",
            "x2",
            "GDMLTwistedtrap",
            "Length x at y= +y1/2 of face at -z/2",
        ).x2 = x2
        obj.addProperty(
            "App::PropertyFloat",
            "x3",
            "GDMLTwistedtrap",
            "Length x at y= -y2/2 of face at +z/2",
        ).x3 = x3
        obj.addProperty(
            "App::PropertyFloat",
            "x4",
            "GDMLTwistedtrap",
            "Length x at y= +y2/2 of face at +z/2",
        ).x4 = x4
        obj.addProperty(
            "App::PropertyFloat",
            "y1",
            "GDMLTwistedtrap",
            "Length y at face -z/2",
        ).y1 = y1
        obj.addProperty(
            "App::PropertyFloat",
            "y2",
            "GDMLTwistedtrap",
            "Length y at face +z/2",
        ).y2 = y2
        obj.addProperty(
            "App::PropertyFloat", "Alph", "GDMLTwistedtrap", "Alph"
        ).Alph = alpha
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLTwistedtrap", "aunit"
        )
        setAngleQuantity(obj, aunit)
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTwistedtrap", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLTwistedtrap",
            "Material",
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        obj.Proxy = self
        self.Type = "GDMLTwistedtrap"
        obj.Proxy.Type = "GDMLTwistedtrap"
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
                    print("G4_AIR - Set Transparency 98")
                    fp.ViewObject.Transparency = 98

        if prop in [
            "PhiTwist",
            "z",
            "theta",
            "phi",
            "x1",
            "x2",
            "x3",
            "x4",
            "y1",
            "y2",
            "alpha",
            "aunit",
            "lunit",
        ]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        # Define six vetices for the shape
        alpha = getAngleRad(fp.aunit, fp.Alph)
        theta = getAngleRad(fp.aunit, fp.Theta)
        phi = getAngleRad(fp.aunit, fp.Phi)
        PhiTwist = getAngleDeg(fp.aunit, fp.PhiTwist)
        mul = GDMLShared.getMult(fp)
        y1 = mul * fp.y1
        x1 = mul * fp.x1
        x2 = mul * fp.x2
        y2 = mul * fp.y2
        x3 = mul * fp.x3
        x4 = mul * fp.x4
        z = mul * fp.z

        N = 9
        dz = z / (N - 1)
        dTwist = PhiTwist / (N - 1)

        tanalpha = math.tan(alpha)

        dt = 1.0 / (N - 1)
        t = 0
        slices = []
        tanthet = math.tan(theta)
        cosphi = math.cos(phi)
        sinphi = math.sin(phi)
        rhomax = z * tanthet
        xoffset = -rhomax * cosphi / 2
        yoffset = -rhomax * sinphi / 2
        for i in range(0, N):
            # Vertexes, counter clock wise order
            y = y1 + t * (y2 - y1)  # go continuously from y1 to y2
            dx = y * tanalpha
            x13 = x1 + t * (x3 - x1)  # go continuously from x1 to x3
            x24 = x2 + t * (x4 - x2)  # go continuously from x1 to x3
            zt = -z / 2 + t * z
            rho = i * dz * tanthet
            dxphi = xoffset + rho * cosphi
            dyphi = yoffset + rho * sinphi
            v1 = FreeCAD.Vector(-x13 / 2 - dx / 2 + dxphi, -y / 2 + dyphi, zt)
            v2 = FreeCAD.Vector(x13 / 2 - dx / 2 + dxphi, -y / 2 + dyphi, zt)
            v3 = FreeCAD.Vector(x24 / 2 + dx / 2 + dxphi, y / 2 + dyphi, zt)
            v4 = FreeCAD.Vector(-x24 / 2 + dx / 2 + dxphi, y / 2 + dyphi, zt)
            p = Part.makePolygon([v1, v2, v3, v4, v1])
            p.rotate(
                FreeCAD.Vector(0, 0, 0),
                FreeCAD.Vector(0, 0, 1),
                -PhiTwist / 2 + i * dTwist,
            )
            slices.append(p)
            t += dt

        loft = Part.makeLoft(slices, True, False)
        fp.Shape = loft
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
