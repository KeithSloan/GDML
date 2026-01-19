from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLCone(GDMLsolid):
    def __init__(
        self,
        obj,
        rmin1,
        rmax1,
        rmin2,
        rmax2,
        z,
        startphi,
        deltaphi,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        """Add some custom properties to our Cone feature"""
        obj.addProperty(
            "App::PropertyFloat", "rmin1", "GDMLCone", "Min Radius 1"
        ).rmin1 = rmin1
        obj.addProperty(
            "App::PropertyFloat", "rmax1", "GDMLCone", "Max Radius 1"
        ).rmax1 = rmax1
        obj.addProperty(
            "App::PropertyFloat", "rmin2", "GDMLCone", "Min Radius 2"
        ).rmin2 = rmin2
        obj.addProperty(
            "App::PropertyFloat", "rmax2", "GDMLCone", "Max Radius 2"
        ).rmax2 = rmax2
        obj.addProperty(
            "App::PropertyFloat", "z", "GDMLCone", "Height of Cone"
        ).z = z
        obj.addProperty(
            "App::PropertyFloat", "startphi", "GDMLCone", "Start Angle"
        ).startphi = startphi
        obj.addProperty(
            "App::PropertyFloat", "deltaphi", "GDMLCone", "Delta Angle"
        ).deltaphi = deltaphi
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLCone", "aunit"
        )
        setAngleQuantity(obj, aunit)
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLCone", "lunit"
        )
        setLengthQuantity(obj, lunit)

        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLCone", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLCone"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLCone"

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

        if prop in [
            "rmin1",
            "rmax1",
            "rmin2",
            "rmax2",
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
        # print("fp : ")
        # print(vars(fp))
        # if all((fp.rmin1,fp.rmin2,fp.rmax1,fp.rmax2,fp.z)) :
        if (
            hasattr(fp, "rmin1")
            and hasattr(fp, "rmax1")
            and hasattr(fp, "rmin2")
            and hasattr(fp, "rmax2")
            and hasattr(fp, "z")
        ):
            # Need to add code to check variables will make a valid cone
            # i.e.max > min etc etc
            # print("execute cone")
            currPlacement = fp.Placement
            mul = GDMLShared.getMult(fp)
            rmin1 = mul * fp.rmin1
            rmin2 = mul * fp.rmin2
            rmax1 = mul * fp.rmax1
            rmax2 = mul * fp.rmax2
            z = mul * fp.z
            # print(mul)
            # print(rmax1)
            # print(rmax2)
            # print(rmin1)
            # print(rmin2)
            # print(z)
            if rmax1 != rmax2:
                cone1 = Part.makeCone(rmax1, rmax2, z)
            else:
                cone1 = Part.makeCylinder(rmax1, z)

            if rmin1 != 0 and rmin2 != 0:
                if rmin1 != rmin2:
                    cone2 = Part.makeCone(rmin1, rmin2, z)
                else:
                    cone2 = Part.makeCylinder(rmin1, z)

                if rmax1 > rmin1:
                    cone3 = cone1.cut(cone2)
                else:
                    cone3 = cone2.cut(cone1)
            else:
                cone3 = cone1
            base = FreeCAD.Vector(0, 0, -z / 2)
            if checkFullCircle(fp.aunit, fp.deltaphi) is False:
                rmax = max(rmax1, rmax2)
                cone = angleSectionSolid(fp, rmax, z, cone3)
                fp.Shape = translate(cone, base)
            else:
                fp.Shape = translate(cone3, base)
            if hasattr(fp, "scale"):
                super().scale(fp)
            fp.Placement = currPlacement
