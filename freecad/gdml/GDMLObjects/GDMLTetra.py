from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLTetra(GDMLsolid):  # 4 point Tetrahedron
    def __init__(self, obj, v1, v2, v3, v4, lunit, material, colour=None):
        super().__init__(obj)
        obj.addProperty("App::PropertyVector", "v1", "GDMLTra", "v1").v1 = v1
        obj.addProperty("App::PropertyVector", "v2", "GDMLTra", "v2").v2 = v2
        obj.addProperty("App::PropertyVector", "v3", "GDMLTra", "v3").v3 = v3
        obj.addProperty("App::PropertyVector", "v4", "GDMLTra", "v4").v4 = v4
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTra", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLTra", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLTetra"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLTetra"

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

        if prop in ["v1", "v2", "v3", "v4", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        mul = GDMLShared.getMult(fp)
        pt1 = mul * fp.v1
        pt2 = mul * fp.v2
        pt3 = mul * fp.v3
        pt4 = mul * fp.v4
        face1 = Part.Face(Part.makePolygon([pt1, pt2, pt3, pt1]))
        face2 = Part.Face(Part.makePolygon([pt1, pt2, pt4, pt1]))
        face3 = Part.Face(Part.makePolygon([pt4, pt2, pt3, pt4]))
        face4 = Part.Face(Part.makePolygon([pt1, pt3, pt4, pt1]))
        fp.Shape = Part.makeSolid(Part.makeShell([face1, face2, face3, face4]))
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
