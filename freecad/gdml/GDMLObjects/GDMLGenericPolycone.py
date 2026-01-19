from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLGenericPolycone(GDMLsolid):  # Thanks to Dam Lamb
    def __init__(
        self, obj, startphi, deltaphi, aunit, lunit, material, colour=None
    ):
        super().__init__(obj)
        """Add some custom properties to our GenericPolycone feature"""
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
        self.Type = "GDMLGenericPolycone"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLGenericPolycone"

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
        rzpoints = fp.OutList
        if len(rzpoints) < 3:
            print("Error in genericPolycone: number of rzpoints less than 3")
            return

        deltaphi = getAngleDeg(fp.aunit, fp.deltaphi)
        startphi = getAngleDeg(fp.aunit, fp.startphi)

        mul = GDMLShared.getMult(fp.lunit)
        verts = [FreeCAD.Vector(rz.r * mul, 0, rz.z * mul) for rz in rzpoints]
        verts.append(
            FreeCAD.Vector(rzpoints[0].r * mul, 0, rzpoints[0].z * mul)
        )
        line = Part.makePolygon(verts)
        line.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), startphi)
        face = Part.Face(line)
        surf = face.revolve(
            FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), deltaphi
        )
        solid = Part.makeSolid(surf)

        fp.Shape = solid
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
