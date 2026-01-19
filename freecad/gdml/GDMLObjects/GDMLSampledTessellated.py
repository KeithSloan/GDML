from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLSampledTessellated(GDMLsolid):
    def __init__(
        self,
        obj,
        vertex,
        facets,
        lunit,
        material,
        solidFlag,
        sampledFraction,
        colour=None,
        flag=True,
    ):
        super().__init__(obj)
        from random import random

        # ########################################
        # if flag == True  - facets is Mesh.Facets - with Normals
        # if flag == False - facets is Faces i.e. from import GDMLTessellated
        # ########################################
        obj.addProperty(
            "App::PropertyInteger",
            "facets",
            "GDMLSampledTessellated",
            "Facets",
        ).facets = len(facets)
        obj.setEditorMode("facets", 1)
        obj.addProperty(
            "App::PropertyInteger",
            "vertex",
            "GDMLSampledTessellated",
            "Vertex",
        ).vertex = len(vertex)
        obj.setEditorMode("vertex", 1)
        obj.addProperty(
            "App::PropertyEnumeration",
            "lunit",
            "GDMLSampledTessellated",
            "lunit",
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLSampledTessellated",
            "Material",
        )

        if flag is True:
            nList = [len(f.Points) for f in facets]
        else:
            nList = [len(f) for f in facets]

        obj.addProperty(
            "App::PropertyIntegerList",
            "vertsPerFacet",
            "GDMLSampledTessellated",
            "Number of vertexes in each facet",
        ).vertsPerFacet = nList
        obj.setEditorMode("vertsPerFacet", 2)

        obj.addProperty(
            "App::PropertyBool",
            "solidFlag",
            "GDMLSampledTessellated",
            "Facets",
        ).solidFlag = solidFlag

        percentageList = [str(i) for i in range(0, 105, 5)]
        obj.addProperty(
            "App::PropertyEnumeration",
            "sampledFraction",
            "GDMLSampledTessellated",
            "Sampled percentage",
        ).sampledFraction = percentageList
        obj.sampledFraction = str(sampledFraction)

        # we use a set first to get rid of duplicate points
        vertsSet = set()
        for f in facets:
            if flag is True:
                for p in f.Points:
                    vertsSet.add(p)
            else:
                vertsSet.add(vertex[f[0]])
                vertsSet.add(vertex[f[1]])
                vertsSet.add(vertex[f[2]])
                if len(f) == 4:
                    vertsSet.add(vertex[f[3]])

        vertsList = list(vertsSet)
        obj.addProperty(
            "App::PropertyVectorList",
            "vertsList",
            "GDMLSampledTessellated",
            "Vertex list",
        ).vertsList = vertsList
        obj.setEditorMode("vertsList", 2)

        # create list of indexes for each face
        Dict = {}
        for i, v in enumerate(vertsList):
            Dict[v] = i

        # now create a list of vert number references for each face
        # there is probably a way to have lists of lists as a property;
        # I just don't know about it, so we list the indexs in order
        # and rely on the nList to get the number of points
        indexList = []
        for f in facets:
            if flag is True:
                for v in f.Points:
                    indexList.append(Dict[v])
            else:
                indexList.append(Dict[vertex[f[0]]])
                indexList.append(Dict[vertex[f[1]]])
                indexList.append(Dict[vertex[f[2]]])
                if len(f) == 4:
                    indexList.append(Dict[vertex[f[3]]])

        obj.addProperty(
            "App::PropertyIntegerList",
            "indexList",
            "GDMLSampledTessellated",
            "Index List",
        ).indexList = indexList
        obj.setEditorMode("indexList", 2)

        setMaterial(obj, material)
        self.updateParams(vertex, facets, solidFlag, sampledFraction, flag)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
            if sampledFraction == 0 and solidFlag is False:
                ViewProvider(obj.ViewObject)
                modes = obj.ViewObject.Proxy.getDisplayModes(obj)
                if "Points" in modes:
                    obj.ViewObject.DisplayMode = "Points"
                obj.ViewObject.PointColor = (random(), random(), random(), 0.0)
        self.Type = "GDMLSampledTessellated"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLSampledTessellated"

    def updateParams(self, vertex, facets, solidFlag, sampledFraction, flag):
        # print('Update Params & Shape')
        self.pshape = self.createShape(
            vertex, facets, solidFlag, sampledFraction, flag
        )
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

    def createShape(self, vertex, facets, solidFlag, sampledFraction, flag):
        # Viewing outside of face vertex must be counter clockwise
        # if flag == True  - facets is Mesh.Facets
        # if flag == False - factes is Faces i.e. from import GDMLTessellated
        # mul = GDMLShared.getMult(fp)
        mul = GDMLShared.getMult(self)
        if sampledFraction == 0 and solidFlag is False:
            shape = self.cloud(vertex, facets, flag)
            return shape
        # print('Create Shape')
        if solidFlag is False:
            NMax = sampledFraction * len(facets) / 100
            nskip = int(len(facets) / NMax)
            if nskip < 1:
                nskip = 1
        else:
            nskip = 1

        FCfaces = []
        for i in range(0, len(facets), nskip):
            f = facets[i]
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
                    FCfaces.append(
                        GDMLShared.quad(
                            mul * vertex[f[0]],
                            mul * vertex[f[1]],
                            mul * vertex[f[2]],
                            mul * vertex[f[3]]
                        )
                    )
        if solidFlag is False:
            solid = Part.makeCompound(FCfaces)
        else:
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

    def toMesh(self, obj):
        import Mesh

        mesh = Mesh.Mesh()
        # Viewing outside of face vertex must be counter clockwise
        # if flag == True  - facets is Mesh.Facets
        # if flag == False - factes is Faces i.e. from import GDMLTessellated
        # mul = GDMLShared.getMult(fp)
        mul = GDMLShared.getMult(self)
        print(f"mul {mul}")
        verts = obj.vertsList
        indexList = obj.indexList
        i = 0
        for nVerts in obj.vertsPerFacet:
            # print(f'Normal at : {n} dot {dot} {clockWise}')
            i0 = indexList[i]
            i1 = indexList[i + 1]
            i2 = indexList[i + 2]
            if nVerts == 3:
                mesh.addFacet(
                    mul * verts[i0], mul * verts[i1], mul * verts[i2]
                )
            elif nVerts == 4:
                i3 = indexList[i + 3]
                mesh.addFacet(
                    mul * verts[i0],
                    mul * verts[i1],
                    mul * verts[i2],
                    mul * verts[i3],
                )
            i += nVerts

        return mesh

    def cloud(self, vertex, facets, flag):
        print("Cloud called")
        import random

        mul = GDMLShared.getMult(self)
        pts = []
        if flag is True:
            frac = 0.01
            Npts = int(frac * (len(facets)))
            while Npts < 1000 and frac < 1:
                frac += 0.01
                Npts = int(frac * (len(facets)))
            jmax = len(facets)
            for i in range(Npts):
                j = random.randrange(jmax)
                f = facets[j]
                v = Part.Vertex(f.Points[0])
                pts.append(v)
        else:
            frac = 0.01
            Npts = int(frac * len(vertex))
            while Npts < 1000 and frac < 1:
                frac += 0.01
                Npts = int(frac * (len(vertex)))
            jmax = len(vertex)
            for i in range(Npts):
                j = random.randrange(jmax)
                v = vertex[j]
                pts.append(Part.Vertex(mul * v[0], mul * v[1], mul * v[2]))

        ret = Part.makeCompound(pts)
        return ret

    def onChanged0(self, fp, prop):
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

        if prop in ["scale", "solidFlag", "sampledFraction"]:
            self.createGeometry(fp)

    def createGeometry0(self, fp):
        import time

        currPlacement = fp.Placement
        mul = GDMLShared.getMult(fp)
        if int(fp.sampledFraction) == 0:
            return
        # print('Create Shape')

        # The vertex index list, is not uniform, because some facets
        # could have four vertexes, instead of three:
        # indexList =     [i00, i01, i02,  i10, i11, i12, i13, i20, i21, i22, ....]
        # vertsPerFacet = [2,              3,                , 2, ...]
        # if one traverses the facets in order, as we do on export, there is no
        # problem finding the starting index for each facet. Bit if skip facets,
        # as we do below, then we must build a list of the starting indexes of
        # each facet
        """
        i0List = []
        i = 0
        for j, nVerts in enumerate(fp.vertsPerFacet):
            i0List.append(i)
            i += nVerts
        """

        FCfaces = []
        if fp.solidFlag is False:
            NMax = int(fp.sampledFraction) * fp.facets / 100
            nskip = int(fp.facets / NMax)
            if nskip < 1:
                nskip = 1
        else:
            nskip = 1

        print(f"nskip {nskip}")
        indexList = fp.indexList
        start = time.perf_counter()
        i = 0
        for j, nVerts in enumerate(fp.vertsPerFacet):
            if nVerts == 3:
                i0 = indexList[i]
                i1 = indexList[i + 1]
                i2 = indexList[i + 2]
                if j % nskip == 0:
                    FCfaces.append(
                        GDMLShared.triangle(
                            mul * fp.vertsList[i0],
                            mul * fp.vertsList[i1],
                            mul * fp.vertsList[i2]
                        )
                    )
            else:  # len should then be 4
                i0 = indexList[i]
                i1 = indexList[i + 1]
                i2 = indexList[i + 2]
                i3 = indexList[i + 3]
                if j % nskip == 0:
                    FCfaces.append(
                        GDMLShared.quad(
                            mul * fp.vertsList[i0],
                            mul * fp.vertsList[i1],
                            mul * fp.vertsList[i2],
                            mul * fp.vertsList[i3],
                        )
                    )
            i += nVerts
        end = time.perf_counter()
        print(f"time to generate faces {(end-start)}")

        start = time.perf_counter()
        if fp.solidFlag is False:
            solid = Part.makeCompound(FCfaces)
        else:
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
        end = time.perf_counter()
        print(f"time to make solid {(end-start)}")

        fp.Shape = solid
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
