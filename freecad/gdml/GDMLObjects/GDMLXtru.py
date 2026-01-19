from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLXtru(GDMLsolid):
    def __init__(self, obj, lunit, material, colour=None):
        super().__init__(obj)
        obj.addExtension("App::GroupExtensionPython")
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLXtru", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLXtru", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLXtru"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLXtru"

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

        if prop in ["startphi", "deltaphi", "aunit", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def layerPoints(self, polyList, sf, xOffset, yOffset, zPosition):
        vl = []
        for p in polyList:
            # print(p)
            vl.append(
                FreeCAD.Vector(
                    p[0] * sf + xOffset, p[1] * sf + yOffset, zPosition
                )
            )
        # Close list
        vl.append(vl[0])
        return vl

    def createGeometry(self, fp):
        # GDMLShared.setTrace(True)
        currPlacement = fp.Placement
        # print("Create Geometry")
        parms = fp.OutList
        # print("OutList")
        # print(parms)
        GDMLShared.trace("Number of parms : " + str(len(parms)))
        polyList = []
        faceList = []
        sections = []
        mul = GDMLShared.getMult(fp)
        for ptr in parms:
            if hasattr(ptr, "x"):
                x = ptr.x * mul
                y = ptr.y * mul
                GDMLShared.trace("x : " + str(x))
                GDMLShared.trace("y : " + str(y))
                polyList.append([x, y])
            if hasattr(ptr, "zOrder"):
                zOrder = ptr.zOrder
                xOffset = ptr.xOffset * mul
                yOffset = ptr.yOffset * mul
                zPosition = ptr.zPosition * mul
                sf = ptr.scalingFactor
                s = [zOrder, xOffset, yOffset, zPosition, sf]
                sections.append(s)
        # print('sections : '+str(len(sections)))
        #
        # Deal with Base Face
        #
        # baseList = layerPoints(polyList,sf,xOffset,yOffset,zPosition):
        # form all vertexes
        verts = []
        for s in sections:
            verts += self.layerPoints(polyList, s[4], s[1], s[2], s[3])

        numverts = len(verts)
        numsides = len(polyList)
        stride = numsides + 1
        # side faces
        for k0 in range(0, numverts - stride, stride):
            for i in range(0, numsides):
                k = k0 + i
                wire = Part.makePolygon(
                    [
                        verts[k],
                        verts[k + stride],
                        verts[k + stride + 1],
                        verts[k + 1],
                        verts[k],
                    ]
                )
                faceList.append(Part.Face(wire))
        # bottom face
        wire = Part.makePolygon(verts[0 : numsides + 1])
        faceList.append(Part.Face(wire))
        # Top face
        wire = Part.makePolygon(verts[numverts - numsides - 1 :])
        faceList.append(Part.Face(wire))

        shell = Part.makeShell(faceList)
        solid = Part.makeSolid(shell)
        fp.Shape = solid
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
