from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLPolyhedra(GDMLsolid):
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
        """Add some custom properties for Polyhedra feature"""
        obj.addProperty(
            "App::PropertyFloat", "startphi", "GDMLPolyhedra", "Start Angle"
        ).startphi = startphi
        obj.addProperty(
            "App::PropertyFloat", "deltaphi", "GDMLPolyhedra", "Delta Angle"
        ).deltaphi = deltaphi
        obj.addProperty(
            "App::PropertyInteger",
            "numsides",
            "GDMLPolyhedra",
            "Number of Side",
        ).numsides = numsides
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLPolyhedra", "aunit"
        )
        setAngleQuantity(obj, aunit)
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLPolyhdera", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLPolyhedra", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLPolyhedra"
        self.colour = colour
        self.Object = obj
        obj.Proxy = self
        obj.Proxy.Type = "GDMLPolyhedra"

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
        from math import sin, cos, pi

        currPlacement = fp.Placement
        # GDMLShared.setTrace(True)
        GDMLShared.trace("Execute Polyhedra")
        parms = fp.OutList
        GDMLShared.trace("Number of parms : " + str(len(parms)))
        numsides = fp.numsides
        GDMLShared.trace("Number of sides : " + str(numsides))
        mul = GDMLShared.getMult(fp)
        z0 = parms[0].z * mul
        rmin0 = parms[0].rmin * mul
        rmax0 = parms[0].rmax * mul
        GDMLShared.trace("Top z    : " + str(z0))
        GDMLShared.trace("Top rmin : " + str(rmin0))
        GDMLShared.trace("Top rmax : " + str(rmax0))
        fullCircle = checkFullCircle(fp.aunit, fp.deltaphi)
        faces = []
        # numsides = int(numsides * 360 / getAngleDeg(fp.aunit, fp.deltaphi))
        # Deal with Inner Top Face
        # Could be point rmin0 = rmax0 = 0
        dPhi = getAngleRad(fp.aunit, fp.deltaphi) / numsides
        phi0 = getAngleRad(fp.aunit, fp.startphi)
        rp = rmin0 / cos(dPhi / 2)
        inner_poly0 = [
            FreeCAD.Vector(
                rp * cos(phi0 + i * dPhi), rp * sin(phi0 + i * dPhi), z0
            )
            for i in range(numsides + 1)
        ]
        rp = rmax0 / cos(dPhi / 2)
        outer_poly0 = [
            FreeCAD.Vector(
                rp * cos(phi0 + i * dPhi), rp * sin(phi0 + i * dPhi), z0
            )
            for i in range(numsides + 1)
        ]
        bottom_verts = inner_poly0 + outer_poly0[::-1]
        bottom_verts.append(bottom_verts[0])
        if rmax0 > 0:
            faces.append(Part.Face(Part.makePolygon(bottom_verts)))
        for ptr in parms[1:]:
            z1 = ptr.z * mul
            rmin1 = ptr.rmin * mul
            rmax1 = ptr.rmax * mul
            GDMLShared.trace("z1    : " + str(z1))
            GDMLShared.trace("rmin1 : " + str(rmin1))
            GDMLShared.trace("rmax1 : " + str(rmax1))
            # Concat face lists
            rp = rmin1 / cos(dPhi / 2)
            inner_poly1 = [
                FreeCAD.Vector(
                    rp * cos(phi0 + i * dPhi), rp * sin(phi0 + i * dPhi), z1
                )
                for i in range(numsides + 1)
            ]
            faces = faces + makeFrustrum(numsides, inner_poly0, inner_poly1)
            inner_poly0 = inner_poly1
            # Deal with Outer
            rp = rmax1 / cos(dPhi / 2)
            outer_poly1 = [
                FreeCAD.Vector(
                    rp * cos(phi0 + i * dPhi), rp * sin(phi0 + i * dPhi), z1
                )
                for i in range(numsides + 1)
            ]
            faces = faces + makeFrustrum(numsides, outer_poly0, outer_poly1)
            # update for next zsection
            outer_poly0 = outer_poly1
            z0 = z1

        if not fullCircle:  # build side faces
            side0_verts = []
            for p in parms:
                r = p.rmax * mul / cos(dPhi / 2)
                side0_verts.append(
                    FreeCAD.Vector(r * cos(phi0), r * sin(phi0), p.z)
                )
            for p in reversed(parms):
                r = p.rmin * mul / cos(dPhi / 2)
                side0_verts.append(
                    FreeCAD.Vector(r * cos(phi0), r * sin(phi0), p.z)
                )
            side0_verts.append(side0_verts[0])
            faces.append(Part.Face(Part.makePolygon(side0_verts)))
            siden_verts = []
            phi = phi0 + numsides * dPhi
            for p in parms:
                r = p.rmax * mul / cos(dPhi / 2)
                siden_verts.append(
                    FreeCAD.Vector(r * cos(phi), r * sin(phi), p.z)
                )
            for p in reversed(parms):
                r = p.rmin * mul / cos(dPhi / 2)
                siden_verts.append(
                    FreeCAD.Vector(r * cos(phi), r * sin(phi), p.z)
                )
            siden_verts.append(siden_verts[0])
            faces.append(Part.Face(Part.makePolygon(siden_verts)))

        # add top polygon face
        top_verts = outer_poly1 + inner_poly1[::-1]
        top_verts.append(top_verts[0])
        if rmax1 > 0:
            faces.append(Part.Face(Part.makePolygon(top_verts)))
        GDMLShared.trace("Total Faces : " + str(len(faces)))
        shell = Part.makeShell(faces)
        fp.Shape = Part.makeSolid(shell)
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
