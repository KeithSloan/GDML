from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLTrap(GDMLsolid):
    def __init__(
        self,
        obj,
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
        "General Trapezoid"
        obj.addProperty("App::PropertyFloat", "z", "GDMLTrap", "z").z = z
        obj.addProperty(
            "App::PropertyFloat", "theta", "GDMLTrap", "theta"
        ).theta = theta
        obj.addProperty(
            "App::PropertyFloat", "phi", "GDMLTrap", "phi"
        ).phi = phi
        obj.addProperty(
            "App::PropertyFloat",
            "x1",
            "GDMLTrap",
            "Length x at y= -y1/2 of face at -z/2",
        ).x1 = x1
        obj.addProperty(
            "App::PropertyFloat",
            "x2",
            "GDMLTrap",
            "Length x at y= +y1/2 of face at -z/2",
        ).x2 = x2
        obj.addProperty(
            "App::PropertyFloat",
            "x3",
            "GDMLTrap",
            "Length x at y= -y2/2 of face at +z/2",
        ).x3 = x3
        obj.addProperty(
            "App::PropertyFloat",
            "x4",
            "GDMLTrap",
            "Length x at y= +y2/2 of face at +z/2",
        ).x4 = x4
        obj.addProperty(
            "App::PropertyFloat", "y1", "GDMLTrap", "Length y at face -z/2"
        ).y1 = y1
        obj.addProperty(
            "App::PropertyFloat", "y2", "GDMLTrap", "Length y at face +z/2"
        ).y2 = y2
        obj.addProperty(
            "App::PropertyFloat", "alpha", "GDMLTrap", "alpha"
        ).alpha = alpha
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLTrap", "aunit"
        )
        setAngleQuantity(obj, aunit)
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTrap", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLTrap", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        obj.Proxy = self
        self.Type = "GDMLTrap"
        obj.Proxy.Type = "GDMLTrap"
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

        if prop in [
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
        alpha = getAngleRad(fp.aunit, fp.alpha)
        theta = getAngleRad(fp.aunit, fp.theta)
        phi = getAngleRad(fp.aunit, fp.phi)
        mul = GDMLShared.getMult(fp)
        y1 = mul * fp.y1
        x1 = mul * fp.x1
        x2 = mul * fp.x2
        y2 = mul * fp.y2
        x3 = mul * fp.x3
        x4 = mul * fp.x4
        z = mul * fp.z
        dx1 = y1 * math.tan(alpha)
        dx2 = y2 * math.tan(alpha)

        # Vertexes, counter clock wise order
        v1 = FreeCAD.Vector(-x1 / 2 - dx1 / 2, -y1 / 2, -z / 2)
        v2 = FreeCAD.Vector(x1 / 2 - dx1 / 2, -y1 / 2, -z / 2)
        v3 = FreeCAD.Vector(x2 / 2 + dx1 / 2, y1 / 2, -z / 2)
        v4 = FreeCAD.Vector(-x2 / 2 + dx1 / 2, y1 / 2, -z / 2)
        v5 = FreeCAD.Vector(-x3 / 2 - dx2 / 2, -y2 / 2, z / 2)
        v6 = FreeCAD.Vector(x3 / 2 - dx2 / 2, -y2 / 2, z / 2)
        v7 = FreeCAD.Vector(x4 / 2 + dx2 / 2, y2 / 2, z / 2)
        v8 = FreeCAD.Vector(-x4 / 2 + dx2 / 2, y2 / 2, z / 2)
        #
        # xy faces
        #
        vxy1 = [v1, v4, v3, v2, v1]
        vxy2 = [v5, v6, v7, v8, v5]
        #
        # zx faces
        #
        vzx1 = [v1, v2, v6, v5, v1]
        vzx2 = [v3, v4, v8, v7, v3]
        #
        # yz faces
        #
        vyz1 = [v5, v8, v4, v1, v5]
        vyz2 = [v2, v3, v7, v6, v2]
        #
        # apply theta, phi distortions
        #
        rho = z * math.tan(theta)
        dx = rho * math.cos(phi)
        dy = rho * math.sin(phi)
        for i in range(0, 4):
            vxy1[i][0] -= dx / 2
            vxy1[i][1] -= dy / 2
            vxy2[i][0] += dx / 2
            vxy2[i][1] += dy / 2

        fxy1 = Part.Face(Part.makePolygon(vxy1))
        fxy2 = Part.Face(Part.makePolygon(vxy2))
        fzx1 = Part.Face(Part.makePolygon(vzx1))
        fzx2 = Part.Face(Part.makePolygon(vzx2))
        fyz1 = Part.Face(Part.makePolygon(vyz1))
        fyz2 = Part.Face(Part.makePolygon(vyz2))

        shell = Part.makeShell([fxy1, fxy2, fzx1, fzx2, fyz1, fyz2])
        solid = Part.makeSolid(shell)

        # center is mid point of diagonal
        #
        botCenter = ((v3 + v4) + (v1 + v2)) / 2
        topCenter = ((v7 + v8) + (v5 + v6)) / 2
        center = (topCenter + botCenter) / 2

        fp.Shape = translate(solid, -center)
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
