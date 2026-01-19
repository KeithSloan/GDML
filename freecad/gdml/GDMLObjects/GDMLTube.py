from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLTube(GDMLsolid):
    def __init__(
        self,
        obj,
        rmin,
        rmax,
        z,
        startphi,
        deltaphi,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        """Add some custom properties to our Tube feature"""
        obj.addProperty(
            "App::PropertyFloat", "rmin", "GDMLTube", "Inside Radius"
        ).rmin = rmin
        obj.addProperty(
            "App::PropertyFloat", "rmax", "GDMLTube", "Outside Radius"
        ).rmax = rmax
        obj.addProperty(
            "App::PropertyFloat", "z", "GDMLTube", "Length z"
        ).z = z
        obj.addProperty(
            "App::PropertyFloat", "startphi", "GDMLTube", "Start Angle"
        ).startphi = startphi
        obj.addProperty(
            "App::PropertyFloat", "deltaphi", "GDMLTube", "Delta Angle"
        ).deltaphi = deltaphi
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLTube", "aunit"
        )
        setAngleQuantity(obj, aunit)
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTube", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLTube", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        obj.Proxy = self
        self.Type = "GDMLTube"
        obj.Proxy.Type = "GDMLTube"
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
            "rmin",
            "rmax",
            "z",
            "startphi",
            "deltaphi",
            "aunit",
            "lunit",
        ]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        mul = GDMLShared.getMult(fp)
        rmax = mul * fp.rmax
        rmin = mul * fp.rmin
        z = mul * fp.z
        spos = FreeCAD.Vector(0, 0, 0)
        sdir = FreeCAD.Vector(0, 0, 1)
        # print('mul : '+str(mul))
        # print('rmax : '+str(rmax))
        # print('z    : '+str(z))
        # print('deltaPhi : '+str(fp.deltaphi))
        tube = Part.makeCylinder(
            rmax, z, spos, sdir, getAngleDeg(fp.aunit, fp.deltaphi)
        )

        if fp.startphi != 0:
            tube.rotate(spos, sdir, getAngleDeg(fp.aunit, fp.startphi))

        if rmin > 0:
            tube = tube.cut(Part.makeCylinder(rmin, z))

        base = FreeCAD.Vector(0, 0, -z / 2)
        fp.Shape = translate(tube, base)
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
