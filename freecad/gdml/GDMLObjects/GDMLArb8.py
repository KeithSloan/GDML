from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLArb8(GDMLsolid):  # Thanks to Dam Lamb
    def __init__(
        self,
        obj,
        v1x,
        v1y,
        v2x,
        v2y,
        v3x,
        v3y,
        v4x,
        v4y,
        v5x,
        v5y,
        v6x,
        v6y,
        v7x,
        v7y,
        v8x,
        v8y,
        dz,
        lunit,
        material,
        colour=None,
    ):
        """Add some custom properties to our Tube feature"""
        obj.addProperty(
            "App::PropertyFloat", "v1x", "GDMLArb8", "vertex 1 x position"
        ).v1x = v1x
        obj.addProperty(
            "App::PropertyFloat", "v1y", "GDMLArb8", "vertex 1 y position"
        ).v1y = v1y
        obj.addProperty(
            "App::PropertyFloat", "v2x", "GDMLArb8", "vertex 2 x position"
        ).v2x = v2x
        obj.addProperty(
            "App::PropertyFloat", "v2y", "GDMLArb8", "vertex 2 y position"
        ).v2y = v2y
        obj.addProperty(
            "App::PropertyFloat", "v3x", "GDMLArb8", "vertex 3 x position"
        ).v3x = v3x
        obj.addProperty(
            "App::PropertyFloat", "v3y", "GDMLArb8", "vertex 3 y position"
        ).v3y = v3y
        obj.addProperty(
            "App::PropertyFloat", "v4x", "GDMLArb8", "vertex 4 x position"
        ).v4x = v4x
        obj.addProperty(
            "App::PropertyFloat", "v4y", "GDMLArb8", "vertex 4 y position"
        ).v4y = v4y
        obj.addProperty(
            "App::PropertyFloat", "v5x", "GDMLArb8", "vertex 5 x position"
        ).v5x = v5x
        obj.addProperty(
            "App::PropertyFloat", "v5y", "GDMLArb8", "vertex 5 y position"
        ).v5y = v5y
        obj.addProperty(
            "App::PropertyFloat", "v6x", "GDMLArb8", "vertex 6 x position"
        ).v6x = v6x
        obj.addProperty(
            "App::PropertyFloat", "v6y", "GDMLArb8", "vertex 6 y position"
        ).v6y = v6y
        obj.addProperty(
            "App::PropertyFloat", "v7x", "GDMLArb8", "vertex 7 x position"
        ).v7x = v7x
        obj.addProperty(
            "App::PropertyFloat", "v7y", "GDMLArb8", "vertex 7 y position"
        ).v7y = v7y
        obj.addProperty(
            "App::PropertyFloat", "v8x", "GDMLArb8", "vertex 8 x position"
        ).v8x = v8x
        obj.addProperty(
            "App::PropertyFloat", "v8y", "GDMLArb8", "vertex 8 y position"
        ).v8y = v8y
        obj.addProperty(
            "App::PropertyFloat", "dz", "GDMLArb8", "Half z Length"
        ).dz = dz
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLArb8", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLArb8", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        obj.Proxy = self
        self.Type = "GDMLArb8"
        obj.Proxy.Type = "GDMLArb8"
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
            "v1x",
            "v1y",
            "v2x",
            "v2y",
            "v3x",
            "v3y",
            "v4x",
            "v4y",
            "v5x",
            "v5y",
            "v6x",
            "v6y",
            "v7x",
            "v7y",
            "v8x",
            "v8y",
            "dz",
            "lunit",
        ]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)
            super().scale(fp)

    # def execute(self, fp): in GDMLsolid

    # http://geant4-userdoc.web.cern.ch/geant4-userdoc/UsersGuides/ForApplicationDeveloper/html/Detector/Geometry/geomSolids.html
    # The order of specification of the coordinates for the vertices in G4GenericTrap is important. The first four points are the vertices sitting on the -hz plane; the last four points are the vertices sitting on the +hz plane.
    #
    # The order of defining the vertices of the solid is the following:
    #
    #    point 0 is connected with points 1,3,4
    #    point 1 is connected with points 0,2,5
    #    point 2 is connected with points 1,3,6
    #    point 3 is connected with points 0,2,7
    #    point 4 is connected with points 0,5,7
    #    point 5 is connected with points 1,4,6
    #    point 6 is connected with points 2,5,7
    #    point 7 is connected with points 3,4,6

    def isTwisted(self, fp):
        ''' test if the upper face is twisted relative to the lower face
        Computation here mimics that in G4GenericTrap
        '''
        verts2D = [(fp.v1x, fp.v1y), (fp.v2x, fp.v2y), (fp.v3x, fp.v3y), (fp.v4x, fp.v4y),
                   (fp.v5x, fp.v5y), (fp.v6x, fp.v6y), (fp.v7x, fp.v7y), (fp.v8x, fp.v8y)]

        nv = 4

        tolerance = 1.E-03
        twisted = False
        for i in range(4):
            dx1 = verts2D[(i+1) % nv][0] - verts2D[i][0]
            dy1 = verts2D[(i+1) % nv][1] - verts2D[i][1]
            if dx1 == 0 and dy1 == 0:
                continue
            dx2 = verts2D[nv + (i+1) % nv][0] - verts2D[nv + i][0]
            dy2 = verts2D[nv + (i+1) % nv][1] - verts2D[nv + i][1]
            if dx2 == 0 and dy2 == 0:
                continue
            twist_angle = abs(dy1*dx2 - dx1*dy2)  # this is sin(angle)
            if twist_angle < tolerance:
                continue
            twisted = True
            break

        return twisted

    def createGeometry(self, fp):

        currPlacement = fp.Placement
        mul = GDMLShared.getMult(fp)
        subdivisions = 0
        if self.isTwisted(fp):
            subdivisions = 8

        # old construction was giving a Volume that was off by about 3%
        # compared to geant4's. So imitate geant4's construction

        pt1 = mul * FreeCAD.Vector(fp.v1x, fp.v1y, -fp.dz)
        pt2 = mul * FreeCAD.Vector(fp.v2x, fp.v2y, -fp.dz)
        pt3 = mul * FreeCAD.Vector(fp.v3x, fp.v3y, -fp.dz)
        pt4 = mul * FreeCAD.Vector(fp.v4x, fp.v4y, -fp.dz)
        pt5 = mul * FreeCAD.Vector(fp.v5x, fp.v5y, fp.dz)
        pt6 = mul * FreeCAD.Vector(fp.v6x, fp.v6y, fp.dz)
        pt7 = mul * FreeCAD.Vector(fp.v7x, fp.v7y, fp.dz)
        pt8 = mul * FreeCAD.Vector(fp.v8x, fp.v8y, fp.dz)

        verts3D = [pt1, pt2, pt3, pt4, pt5, pt6, pt7, pt8]


        faces = []
        faces.append(Part.Face(Part.makePolygon([verts3D[0], verts3D[3], verts3D[2], verts3D[1], verts3D[0]])))  # -fz plane
        # breakpoint()
        t = 0
        dt = 1./(subdivisions+1)
        u0 = verts3D[4] - verts3D[0]
        u1 = verts3D[5] - verts3D[1]
        u2 = verts3D[6] - verts3D[2]
        u3 = verts3D[7] - verts3D[3]
        for i in range(subdivisions+1):
            j = i*4
            faces.append(Part.Face(Part.makePolygon([verts3D[0] + t * u0, verts3D[1]  + t * u1, verts3D[0] + (t + dt) * u0, verts3D[0] + t * u0])))
            faces.append(Part.Face(Part.makePolygon([verts3D[0] + (t + dt) * u0, verts3D[1]  + t * u1, verts3D[1] + (t + dt) * u1, verts3D[0] + (t + dt) * u0])))

            faces.append(Part.Face(Part.makePolygon([verts3D[1] + t * u1, verts3D[2]  + t * u2, verts3D[1] + (t + dt) * u1, verts3D[1] + t * u1])))
            faces.append(Part.Face(Part.makePolygon([verts3D[1] + (t + dt) * u1, verts3D[2]  + t * u2, verts3D[2] + (t + dt) * u2, verts3D[1] + (t + dt) * u1])))

            faces.append(Part.Face(Part.makePolygon([verts3D[2] + t * u2, verts3D[3]  + t * u3, verts3D[2] + (t + dt) * u2, verts3D[2] + t * u2])))
            faces.append(Part.Face(Part.makePolygon([verts3D[2] + (t + dt) * u2, verts3D[3]  + t * u3, verts3D[3] + (t + dt) * u3, verts3D[2] + (t + dt) * u2])))

            faces.append(Part.Face(Part.makePolygon([verts3D[3] + t * u3, verts3D[0]  + t * u0, verts3D[3] + (t + dt) * u3, verts3D[3] + t * u3])))
            faces.append(Part.Face(Part.makePolygon([verts3D[3] + (t + dt) * u3, verts3D[0]  + t * u0, verts3D[0] + (t + dt) * u0, verts3D[3] + (t + dt) * u3])))

            t += dt

        faces.append(Part.Face(Part.makePolygon([verts3D[4], verts3D[5], verts3D[6], verts3D[7], verts3D[4]])))  # +fz plane

        fp.Shape = Part.makeSolid(Part.makeShell(faces))

        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
