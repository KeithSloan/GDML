from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLPara(GDMLsolid):
    def __init__(
        self,
        obj,
        x,
        y,
        z,
        alpha,
        theta,
        phi,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        """Add some custom properties for Polyhedra feature"""
        obj.addProperty("App::PropertyFloat", "x", "GDMLParapiped", "x").x = x
        obj.addProperty("App::PropertyFloat", "y", "GDMLParapiped", "y").y = y
        obj.addProperty("App::PropertyFloat", "z", "GDMLParapiped", "z").z = z
        obj.addProperty(
            "App::PropertyFloat", "alpha", "GDMLParapiped", "Angle with y axis"
        ).alpha = alpha
        obj.addProperty(
            "App::PropertyFloat",
            "theta",
            "GDMLParapiped",
            "Polar Angle with faces",
        ).theta = theta
        obj.addProperty(
            "App::PropertyFloat",
            "phi",
            "GDMLParapiped",
            "Azimuthal Angle with faces",
        ).phi = phi
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLParapiped", "aunit"
        )
        setAngleQuantity(obj, aunit)
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLParapiped", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLParapiped", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLPara"
        self.colour = colour
        self.Object = obj
        obj.Proxy = self
        obj.Proxy.Type = "GDMLPara"

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

        if prop in ["x", "y", "z", "alpha", "theta", "phi", "aunit", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        # GDMLShared.setTrace(True)
        GDMLShared.trace("Execute Polyparallepiped")
        mul = GDMLShared.getMult(fp)
        x = mul * fp.x
        y = mul * fp.y
        z = mul * fp.z
        alpha = getAngleRad(fp.aunit, fp.alpha)
        theta = getAngleRad(fp.aunit, fp.theta)
        phi = getAngleRad(fp.aunit, fp.phi)
        # Vertexes
        v1 = FreeCAD.Vector(0, 0, 0)
        v2 = FreeCAD.Vector(x, 0, 0)
        v3 = FreeCAD.Vector(x, y, 0)
        v4 = FreeCAD.Vector(0, y, 0)
        v5 = FreeCAD.Vector(0, 0, z)
        v6 = FreeCAD.Vector(x, 0, z)
        v7 = FreeCAD.Vector(x, y, z)
        v8 = FreeCAD.Vector(0, y, z)
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

        # Apply alpha angle distortions
        #
        dx = z * math.tan(alpha)
        for i in range(0, 4):
            vzx2[i][0] += dx
        #
        # apply theta, phi distortions
        #
        rho = z * math.tan(theta)
        dx = rho * math.cos(phi)
        dy = rho * math.sin(phi)
        for i in range(0, 4):
            vxy2[i][0] += dx
            vxy2[i][1] += dy

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
        center = (v7 - v1) / 2
        fp.Shape = translate(solid, -center)
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
