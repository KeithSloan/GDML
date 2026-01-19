from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLEllipsoid(GDMLsolid):
    def __init__(
        self, obj, ax, by, cz, zcut1, zcut2, lunit, material, colour=None
    ):
        super().__init__(obj)
        """Add some custom properties to our Elliptical Tube feature"""
        obj.addProperty(
            "App::PropertyFloat", "ax", "GDMLEllipsoid", "x semi axis"
        ).ax = ax
        obj.addProperty(
            "App::PropertyFloat", "by", "GDMLEllipsoid", "y semi axis"
        ).by = by
        obj.addProperty(
            "App::PropertyFloat", "cz", "GDMLEllipsoid", "z semi axis"
        ).cz = cz
        obj.addProperty(
            "App::PropertyFloat", "zcut1", "GDMLEllipsoid", "z axis cut1"
        ).zcut1 = zcut1
        obj.addProperty(
            "App::PropertyFloat", "zcut2", "GDMLEllipsoid", "z axis1 cut2"
        ).zcut2 = zcut2
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLEllipsoid", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLEllipsoid", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLEllipsoid"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLEllipsoid"

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

        if prop in ["ax", "by", "cz", "zcut1", "zcut2", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        mul = GDMLShared.getMult(fp)
        sphere = Part.makeSphere(100)  # 100= sphere radius = 1/2 diameter
        ax = fp.ax * mul
        by = fp.by * mul
        cz = fp.cz * mul
        mat = FreeCAD.Matrix()
        mat.unity()
        mat.A11 = ax / 100
        mat.A22 = by / 100
        mat.A33 = cz / 100
        mat.A44 = 1

        if fp.zcut1 is not None:
            zcut1 = fp.zcut1 * mul
        else:
            zcut1 = -2 * cz

        if fp.zcut2 is not None:
            zcut2 = fp.zcut2 * mul
        else:
            zcut2 = 2 * cz

        GDMLShared.trace("zcut2 : " + str(zcut2))
        t1ellipsoid = sphere.transformGeometry(mat)
        if zcut2 > -cz and zcut2 < cz:  # Remove from upper z
            box1 = Part.makeBox(2 * ax, 2 * by, 2 * cz)
            pl = FreeCAD.Placement()
            # Only need to move to semi axis
            pl.move(FreeCAD.Vector(-ax, -by, zcut2))
            box1.Placement = pl
            t2ellipsoid = t1ellipsoid.cut(box1)
        else:
            t2ellipsoid = t1ellipsoid
        if zcut1 < zcut2 and zcut1 > -cz and zcut1 < cz:
            box2 = Part.makeBox(2 * ax, 2 * by, 2 * cz)
            pl = FreeCAD.Placement()
            # cut with the upper edge of the box
            pl.move(FreeCAD.Vector(-ax, -by, -2 * cz + zcut1))
            box2.Placement = pl
            shape = t2ellipsoid.cut(box2)
        else:
            shape = t2ellipsoid

        base = FreeCAD.Vector(0, 0, 0)
        fp.Shape = translate(shape, base)
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
