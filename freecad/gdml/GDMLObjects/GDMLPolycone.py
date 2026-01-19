from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLPolycone(GDMLsolid):  # Thanks to Dam Lamb
    def __init__(
        self, obj, startphi, deltaphi, aunit, lunit, material, colour=None
    ):
        super().__init__(obj)
        """Add some custom properties to our Polycone feature"""
        obj.addExtension("App::GroupExtensionPython")
        obj.addProperty(
            "App::PropertyFloat", "startphi", "GDMLPolycone", "Start Angle"
        ).startphi = startphi
        obj.addProperty(
            "App::PropertyFloat", "deltaphi", "GDMLPolycone", "Delta Angle"
        ).deltaphi = deltaphi
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLPolycone", "aunit"
        )
        setAngleQuantity(obj, aunit)
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLPolycone", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLPolycone", "Material"
        )
        setMaterial(obj, material)
        # For debugging
        # obj.setEditorMode('Placement',0)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLPolycone"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLPolycone"

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

    def createGeometry(self, fp):

        currPlacement = fp.Placement
        zplanes = fp.OutList
        # GDMLShared.trace("Number of zplanes : "+str(len(zplanes)))
        mul = GDMLShared.getMult(fp.lunit)
        offset = zplanes[0].z * mul
        angleDeltaPhiDeg = 360.0
        if hasattr(fp, "deltaphi"):
            angleDeltaPhiDeg = min(
                [getAngleDeg(fp.aunit, fp.deltaphi), angleDeltaPhiDeg]
            )
            if angleDeltaPhiDeg <= 0.0:
                return

        listShape = [0 for i in range((len(zplanes) - 1))]

        sinPhi = 0.0
        cosPhi = 1.0
        if fp.startphi != 0:
            angleRad = getAngleRad(fp.aunit, fp.startphi)
            sinPhi = math.sin(angleRad)
            cosPhi = math.cos(angleRad)

        # loops on each z level
        for i in range(len(zplanes) - 1):
            GDMLShared.trace("index : " + str(i))
            if i == 0:
                rmin1 = zplanes[i].rmin * mul
                rmax1 = zplanes[i].rmax * mul
                z1 = zplanes[i].z * mul
            else:
                rmin1 = rmin2  # for i > 0, rmin2 will have been defined below
                rmax1 = rmax2
                z1 = z2

            rmin2 = zplanes[i + 1].rmin * mul
            rmax2 = zplanes[i + 1].rmax * mul
            z2 = zplanes[i + 1].z * mul

            # def of one face to rotate
            face = Part.Face(
                Part.makePolygon(
                    [
                        FreeCAD.Vector(rmin1 * cosPhi, rmin1 * sinPhi, z1),
                        FreeCAD.Vector(rmax1 * cosPhi, rmax1 * sinPhi, z1),
                        FreeCAD.Vector(rmax2 * cosPhi, rmax2 * sinPhi, z2),
                        FreeCAD.Vector(rmin2 * cosPhi, rmin2 * sinPhi, z2),
                        FreeCAD.Vector(rmin1 * cosPhi, rmin1 * sinPhi, z1),
                    ]
                )
            )
            # rotation of the face
            listShape[i] = face.revolve(
                FreeCAD.Vector(0, 0, 0),
                FreeCAD.Vector(0, 0, 1),
                angleDeltaPhiDeg,
            )
        # compound of all faces
        fp.Shape = Part.makeCompound(listShape)
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
