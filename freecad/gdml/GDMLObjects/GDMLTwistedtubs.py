from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLTwistedtubs(GDMLsolid):
    def __init__(
        self,
        obj,
        endinnerrad,
        endouterrad,
        zlen,
        twistedangle,
        phi,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        """Twisted tube"""
        obj.addProperty(
            "App::PropertyFloat", "zlen", "GDMLTwistedtubs", "zlen"
        ).zlen = zlen
        obj.addProperty(
            "App::PropertyFloat",
            "endinnerrad",
            "GDMLTwistedtubs",
            "Inside radius at caps",
        ).endinnerrad = endinnerrad
        obj.addProperty(
            "App::PropertyFloat",
            "endouterrad",
            "GDMLTwistedtubs",
            "Outside radius at caps",
        ).endouterrad = endouterrad
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTwistedtubs", "lunit"
        )
        angle = getAngleDeg(aunit, twistedangle)
        if angle > 90:
            print("PhiTwist angle cannot be larger than 90 deg")
            angle = 90
            aunit = "deg"
        elif angle < -90:
            print("PhiTwist angle cannot be less than -90 deg")
            angle = -90
            aunit = "deg"
        else:
            angle = twistedangle

        obj.addProperty(
            "App::PropertyFloat",
            "twistedangle",
            "GDMLTwistedtubs",
            "Twist Angle",
        ).twistedangle = angle
        obj.addProperty(
            "App::PropertyFloat", "phi", "GDMLTwistedtubs", "Delta phi"
        ).phi = phi
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLTwistedtubs", "aunit"
        )
        setAngleQuantity(obj, aunit)
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLTwistedtubs",
            "Material",
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLTwistedtubs"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLTwistedtubs"

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # Changing Shape in createGeometry will redrive onChanged
        if "Restore" in fp.State:
            return

        if prop in ["material"]:
            if FreeCAD.GuiUp:
                if self.colour is None:
                    fp.ViewObject.ShapeColor = colourMaterial(fp.material)
                if fp.material == "G4_AIR":
                    print("Set Transparency")
                    fp.ViewObject.Transparency = 98
        if prop in [
            "endinnerrad",
            "endouterrad",
            "zlen",
            "twistedangle",
            "phi",
            "lunit",
            "aunit",
        ]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        # print('createGeometry')
        # print(fp)

        if all((fp.endouterrad, fp.zlen, fp.phi)):
            currPlacement = fp.Placement

            mul = GDMLShared.getMult(fp)
            rin = fp.endinnerrad * mul
            rout = fp.endouterrad * mul
            if rin > rout:
                print(
                    f"Error: Inner radius ({rin}) greater than outer radius ({rout})"
                )
                return
            zlen = fp.zlen * mul
            GDMLShared.trace("mul : " + str(mul))
            angle = getAngleDeg(fp.aunit, fp.twistedangle)
            phi = getAngleRad(fp.aunit, fp.phi)
            phideg = getAngleDeg(fp.aunit, fp.phi)
            slices = []
            N = 20  # number of slices
            dz = zlen / (N - 1)
            dtwist = angle / (N - 1)
            # construct base wire
            # Vertexes
            v1 = FreeCAD.Vector(rin, 0, 0)
            v2 = FreeCAD.Vector(rout, 0, 0)
            v3 = FreeCAD.Vector(rout * math.cos(phi), rout * math.sin(phi), 0)
            v4 = FreeCAD.Vector(rin * math.cos(phi), rin * math.sin(phi), 0)
            # arc center points
            vCin = FreeCAD.Vector(
                rin * math.cos(phi / 2), rin * math.sin(phi / 2), 0
            )
            vCout = FreeCAD.Vector(
                rout * math.cos(phi / 2), rout * math.sin(phi / 2), 0
            )
            # Center of twisting
            rc = (rin + rout) / 2
            vc = FreeCAD.Vector(
                rc * math.cos(phi / 2), rc * math.sin(phi / 2), 0
            )
            # wire
            arcin = Part.Arc(v1, vCin, v4)
            line1 = Part.LineSegment(v4, v3)
            arcout = Part.Arc(v3, vCout, v2)
            line2 = Part.LineSegment(v2, v1)

            s = Part.Shape([arcin, line1, arcout, line2])
            w = Part.Wire(s.Edges)
            angoffset = -angle / 2 - phideg / 2

            for i in range(0, N):
                p = w.translated(FreeCAD.Vector(0, 0, -zlen / 2 + i * dz))
                # p.rotate(vc, FreeCAD.Vector(0, 0, 1), angoffset + i * dtwist)
                p.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), angoffset + i * dtwist)
                slices.append(p)

            loft = Part.makeLoft(slices, True, False)
            fp.Shape = loft
            if hasattr(fp, "scale"):
                super().scale(fp)
            fp.Placement = currPlacement

    def OnDocumentRestored(self, obj):
        print("Doc Restored")
