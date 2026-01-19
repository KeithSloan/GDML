from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLTetrahedron(GDMLsolid):

    """Does not exist as a GDML solid, but export as an Assembly of G4Tet"""

    """ See paper Poole at al - Fast Tessellated solid navigation in GEANT4 """

    def __init__(self, obj, tetra, lunit, material, colour=None):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyInteger", "tetra", "GDMLTetrahedron", "Tetra"
        ).tetra = len(tetra)
        obj.setEditorMode("tetra", 1)
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTetrahedron", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLTetrahedron",
            "Material",
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        # obj.addExtension('App::GroupExtensionPython')
        self.Tetra = tetra
        self.Object = obj
        self.Type = "GDMLTetrahedron"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLTetrahedron"

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

        if prop in ["lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def makeTetra(self, pt1, pt2, pt3, pt4):
        face1 = Part.Face(Part.makePolygon([pt1, pt2, pt3, pt1]))
        face2 = Part.Face(Part.makePolygon([pt1, pt2, pt4, pt1]))
        face3 = Part.Face(Part.makePolygon([pt4, pt2, pt3, pt4]))
        face4 = Part.Face(Part.makePolygon([pt1, pt3, pt4, pt1]))
        return Part.makeShell([face1, face2, face3, face4])

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        print("Tetrahedron")
        mul = GDMLShared.getMult(fp)
        print(len(self.Tetra))
        tetraShells = []
        for t in self.Tetra:
            pt1 = mul * t[0]
            pt2 = mul * t[1]
            pt3 = mul * t[2]
            pt4 = mul * t[3]
            tetraShells.append(self.makeTetra(pt1, pt2, pt3, pt4))
        fp.Shape = Part.makeCompound(tetraShells)
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
