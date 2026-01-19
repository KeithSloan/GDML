from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLGenericPolyhedra(GDMLsolid):
    def __init__(
        self,
        obj,
        startphi,
        deltaphi,
        numsides,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        """Add some custom properties for Generic Polyhedra feature"""
        obj.addProperty(
            "App::PropertyFloat",
            "startphi",
            "GDMLGenericPolyhedra",
            "Start Angle",
        ).startphi = startphi
        obj.addProperty(
            "App::PropertyFloat",
            "deltaphi",
            "GDMLGenericPolyhedra",
            "Delta Angle",
        ).deltaphi = deltaphi
        obj.addProperty(
            "App::PropertyInteger",
            "numsides",
            "GDMLGenericPolyhedra",
            "Number of Side",
        ).numsides = numsides
        obj.addProperty(
            "App::PropertyEnumeration",
            "aunit",
            "GDMLGenericPolyhedra",
            "aunit",
        )
        setAngleQuantity(obj, aunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "lunit",
            "GDMLGenericPolyhdera",
            "lunit",
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLGenericPolyhedra",
            "Material",
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLGenericPolyhedra"
        self.colour = colour
        self.Object = obj
        obj.Proxy = self
        obj.Proxy.Type = "GDMLGenericPolyhedra"

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

        if prop in ["startphi", "deltaphi", "numsides", "aunit", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        # GDMLShared.setTrace(True)
        GDMLShared.trace("Execute GenericPolyhedra")
        rzpoints = fp.OutList
        if len(rzpoints) < 3:
            print("Error in genericPolyhedra: number of rzpoints less than 3")
            return
        GDMLShared.trace("Number of rzpoints : " + str(len(rzpoints)))
        numsides = fp.numsides
        GDMLShared.trace("Number of sides : " + str(numsides))
        mul = GDMLShared.getMult(fp)
        faces = []
        startphi = getAngleRad(fp.aunit, fp.startphi)
        dphi = getAngleRad(fp.aunit, fp.deltaphi) / numsides
        # form vertexes
        verts = []
        for ptr in rzpoints:
            z = ptr.z * mul
            r = ptr.r * mul
            phi = startphi
            for i in range(0, numsides + 1):
                v = FreeCAD.Vector(r * math.cos(phi), r * math.sin(phi), z)
                verts.append(v)
                phi += dphi

        numverts = len(verts)
        stride = numsides + 1
        # outer faces
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
                f = Part.Face(wire)
                if f.Area != 0:
                    faces.append(f)

        # inner faces
        for i in range(0, numsides):
            k = numverts - stride + i
            wire = Part.makePolygon(
                [verts[i], verts[k], verts[k + 1], verts[i + 1], verts[i]]
            )
            f = Part.Face(wire)
            if f.Area != 0:
                faces.append(f)

        # side faces
        if checkFullCircle(fp.aunit, fp.deltaphi) is False:
            verts1 = [
                verts[k] for k in range(0, numverts - stride + 1, stride)
            ]
            verts1.append(verts1[0])
            wire = Part.makePolygon(verts1)
            faces.append(Part.Face(wire))
            verts1 = [verts[k] for k in range(numsides, numverts, stride)]
            verts1.append(verts1[0])
            wire = Part.makePolygon(verts1)
            f = Part.Face(wire)
            if f.Area != 0:
                faces.append(f)

        shell = Part.makeShell(faces)
        solid = Part.makeSolid(shell)
        fp.Shape = solid
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
