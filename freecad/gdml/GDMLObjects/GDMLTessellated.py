from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLTessellated(GDMLsolid):
    def __init__(
        self, obj, vertex, facets, flag, lunit, material, colour=None
    ):
        super().__init__(obj)
        # ########################################
        # if flag == True  - facets is Mesh.Facets - with Normals
        # if flag == False - facets is Faces i.e. from import GDMLTessellated
        # ########################################
        obj.addProperty(
            "App::PropertyInteger", "facets", "GDMLTessellated", "Facets"
        ).facets = len(facets)
        obj.setEditorMode("facets", 1)
        obj.addProperty(
            "App::PropertyInteger", "vertex", "GDMLTessellated", "Vertex"
        ).vertex = len(vertex)
        obj.setEditorMode("vertex", 1)
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTessellated", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLTessellated",
            "Material",
        )
        setMaterial(obj, material)
        self.updateParams(vertex, facets, flag)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        self.Type = "GDMLTessellated"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLTessellated"

    def updateParams(self, vertex, facets, flag):
        # print('Update Params & Shape')
        self.pshape = self.createShape(vertex, facets, flag)
        # print(f"Pshape vertex {len(self.pshape.Vertexes)}")
        self.facets = len(facets)
        self.vertex = len(vertex)
        # print(f"Vertex : {self.vertex} Facets : {self.facets}")

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

        if prop in ["editable"]:
            if fp.editable is True:
                self.addProperties()

        if prop in ["scale"]:
            self.createGeometry(fp)

    def addProperties(self):
        print("Add Properties")

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        if hasattr(self, "pshape"):
            # print('Update Shape')
            fp.Shape = self.pshape
            if hasattr(fp, "pshape"):
                fp.pshape = self.pshape
            fp.vertex = self.vertex
            fp.facets = self.facets
        if hasattr(fp, "scale"):
            super().scale(fp)

    def createShape(self, vertex, facets, flag):
        # Viewing outside of face vertex must be counter clockwise
        # if flag == True  - facets is Mesh.Facets
        # if flag == False - factes is Faces i.e. from import GDMLTessellated
        # mul = GDMLShared.getMult(fp)
        mul = GDMLShared.getMult(self)
        # print('Create Shape')
        FCfaces = []
        for f in facets:
            # print('Facet')
            # print(f)
            if flag is True:
                FCfaces.append(GDMLShared.facet(f))
            else:
                if len(f) == 3:
                    FCfaces.append(
                        GDMLShared.triangle(
                            mul * vertex[f[0]],
                            mul * vertex[f[1]],
                            mul * vertex[f[2]]
                        )
                    )
                else:  # len should then be 4
                    try:
                        face = GDMLShared.quad(
                            mul * vertex[f[0]],
                            mul * vertex[f[1]],
                            mul * vertex[f[2]],
                            mul * vertex[f[3]]
                        )
                        FCfaces.append(face)
                    except:
                        face = GDMLShared.triangle(
                            mul * vertex[f[0]],
                            mul * vertex[f[1]],
                            mul * vertex[f[2]]
                        )
                        FCfaces.append(face)
                        face = GDMLShared.triangle(
                            mul * vertex[f[0]],
                            mul * vertex[f[2]],
                            mul * vertex[f[3]]
                        )
                        FCfaces.append(face)
        shell = Part.makeShell(FCfaces)
        if shell.isValid is False:
            FreeCAD.Console.PrintWarning("Not a valid Shell/n")

        # shell.check()
        # solid=Part.Solid(shell).removeSplitter()
        try:
            solid = Part.Solid(shell)
        except:
            # make compound rather than just barf
            # visually able to view at least
            FreeCAD.Console.PrintWarning("Problem making Solid/n")
            solid = Part.makeCompound(FCfaces)

        return solid
