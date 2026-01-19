from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLTorus(GDMLsolid):
    def __init__(
        self,
        obj,
        rmin,
        rmax,
        rtor,
        startphi,
        deltaphi,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyFloat", "rmin", "GDMLTorus", "rmin"
        ).rmin = rmin
        obj.addProperty(
            "App::PropertyFloat", "rmax", "GDMLTorus", "rmax"
        ).rmax = rmax
        obj.addProperty(
            "App::PropertyFloat", "rtor", "GDMLTorus", "rtor"
        ).rtor = rtor
        obj.addProperty(
            "App::PropertyFloat", "startphi", "GDMLTorus", "startphi"
        ).startphi = startphi
        obj.addProperty(
            "App::PropertyFloat", "deltaphi", "GDMLTorus", "deltaphi"
        ).deltaphi = deltaphi
        obj.addProperty(
            "App::PropertyString", "aunit", "GDMLTorus", "aunit"
        ).aunit = aunit
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTorus", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLTorus", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLTorus"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLTorus"

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
                    print("G4_AIR  - Set Transparency")
                    fp.ViewObject.Transparency = 98

        if prop in [
            "rmin",
            "rmax",
            "rtor",
            "startphi",
            "deltaphi",
            "aunit",
            "lunit",
        ]:
            # print(f'Change Prop : {prop}')
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        GDMLShared.trace("Create Torus")
        mul = GDMLShared.getMult(fp)
        rmin = mul * fp.rmin
        rmax = mul * fp.rmax
        rtor = mul * fp.rtor

        spnt = FreeCAD.Vector(0, 0, 0)
        sdir = FreeCAD.Vector(0, 0, 1)

        outerTorus = Part.makeTorus(
            rtor, rmax, spnt, sdir, 0, 360, getAngleDeg(fp.aunit, fp.deltaphi)
        )
        if rmin > 0:
            innerTorus = Part.makeTorus(
                rtor,
                rmin,
                spnt,
                sdir,
                0,
                360,
                getAngleDeg(fp.aunit, fp.deltaphi),
            )
            torus = outerTorus.cut(innerTorus)
        else:
            torus = outerTorus
        if fp.startphi != 0:
            torus.rotate(spnt, sdir, getAngleDeg(fp.aunit, fp.startphi))
        fp.Shape = torus
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
