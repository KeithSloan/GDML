from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLGmshTessellated(GDMLsolid):
    def __init__(
        self,
        obj,
        sourceObj,
        meshLen,
        vertex,
        facets,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyInteger", "numFacets", "GDMLGmshTessellated", "Facets"
        ).numFacets = len(facets)
        obj.setEditorMode("numFacets", 1)
        obj.addProperty(
            "App::PropertyInteger", "numVertex", "GDMLGmshTessellated", "Vertex"
        ).numVertex = len(vertex)
        obj.setEditorMode("numVertex", 1)
        # Properties NOT the same GmshTessellate GmshMinTessellate
        #obj.addProperty(
        #    "App::PropertyFloat",
        #    "m_maxLength",
        #    "GDMLGmshTessellated",
        #    "Max Length",
        #).m_maxLength = meshLen
        #obj.addProperty(
        #    "App::PropertyFloat",
        #    "m_curveLen",
        #    "GDMLGmshTessellated",
        #    "Curve Length",
        #).m_curveLen = meshLen
        #obj.addProperty(
        #    "App::PropertyFloat",
        #    "m_pointLen",
        #    "GDMLGmshTessellated",
        #    "Point Length",
        #).m_pointLen = meshLen
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLGmshTessellated", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLTessellated",
            "Material",
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        self.Type = "GDMLGmshTessellated"
        self.SourceObj = sourceObj
        self.vertex = vertex
        self.facets = facets
        self.Object = obj
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLGmshTessellated"

    def updateParams(self, vertex, facets, flag):
        self.vertex = vertex
        self.facets = facets
        self.numFacets = len(self.facets)
        self.numVertex = len(self.vertex)
        print(f"Vertex : {self.numVertex} Facets : {self.numFacets}")

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
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

        if prop in ["m_Remesh"]:
            if fp.m_Remesh is True:
                self.reMesh(fp)
                self.execute(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    def execute(self, fp):  # Here for remesh?
        self.createGeometry(fp)

    def addProperties(self):
        print("Add Properties")

    def reMesh(self, fp):
        from .GmshUtils import initialize, meshObj, getVertex, getFacets

        initialize()
        meshObj(fp.Proxy.SourceObj, 2, True, fp.Proxy.Object)
        self.facets = getFacets()
        self.vertex = getVertex()
        fp.Proxy.vertex = self.vertex
        self.Object.numVertex = len(self.vertex)
        fp.Proxy.facets = self.facets
        self.Object.numFacets = len(self.facets)
        FreeCADGui.updateGui()

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        mul = GDMLShared.getMult(fp)
        FCfaces = []
        for f in self.facets:
            if len(f) == 3:
                face = GDMLShared.triangle(
                    mul * self.vertex[f[0]],
                    mul * self.vertex[f[1]],
                    mul * self.vertex[f[2]]
                )
                if face is not None:
                    FCfaces.append(face)
            else:  # len should then be 4
                quadFace = GDMLShared.quad(
                    mul * self.vertex[f[0]],
                    mul * self.vertex[f[1]],
                    mul * self.vertex[f[2]],
                    mul * self.vertex[f[3]]
                )
                if quadFace is not None:
                    FCfaces.append(quadFace)
                else:
                    print(f"Create Quad Failed {f[0]} {f[1]} {f[2]} {f[3]}")
                    print("Creating as two triangles")
                    face = GDMLShared.triangle(
                        mul * self.vertex[f[0]],
                        mul * self.vertex[f[1]],
                        mul * self.vertex[f[2]]
                    )
                    if face is not None:
                        FCfaces.append(face)
                    face = GDMLShared.triangle(
                        mul * self.vertex[f[0]],
                        mul * self.vertex[f[2]],
                        mul * self.vertex[f[3]]
                    )
                    if face is not None:
                        FCfaces.append(face)

        shell = Part.makeShell(FCfaces)
        if shell.isValid is False:
            FreeCAD.Console.PrintWarning("Not a valid Shell/n")

        try:
            solid = Part.Solid(shell)
        except:
            # make compound rather than just barf
            # visually able to view at least
            FreeCAD.Console.PrintWarning("Problem making Solid/n")
            solid = Part.makeCompound(FCfaces)
        # if solid.Volume < 0:
        #   solid.reverse()
        # print(dir(solid))
        # bbox = solid.BoundBox
        # base = FreeCAD.Vector(-(bbox.XMin+bbox.XMax)/2, \
        #                      -(bbox.YMin+bbox.YMax)/2 \
        #                      -(bbox.ZMin+bbox.ZMax)/2)
        # print(base)

        # base = FreeCAD.Vector(0,0,0)
        # fp.Shape = translate(solid,base)
        fp.Shape = solid
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
