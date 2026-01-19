from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLElTube(GDMLsolid):
    def __init__(self, obj, dx, dy, dz, lunit, material, colour=None):
        super().__init__(obj)
        """Add some custom properties to our Elliptical Tube feature"""
        obj.addProperty(
            "App::PropertyFloat", "dx", "GDMLElTube", "x semi axis1"
        ).dx = dx
        obj.addProperty(
            "App::PropertyFloat", "dy", "GDMLElTube", "y semi axis1"
        ).dy = dy
        obj.addProperty(
            "App::PropertyFloat", "dz", "GDMLElTube", "z half height"
        ).dz = dz
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLElTube", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLElTube", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLElTube"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLElTube"

    def onChanged(self, fp, prop):
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        """Do something when a property has changed"""
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

        if prop in ["dx", "dy", "dz", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    '''
    def createGeometry(self, fp):
        currPlacement = fp.Placement
        mul = GDMLShared.getMult(fp)
        tube = Part.makeCylinder(100, 100)
        mat = FreeCAD.Matrix()
        mat.unity()
        mat.A11 = (fp.dx * mul) / 100
        mat.A22 = (fp.dy * mul) / 100
        mat.A33 = (fp.dz * mul) / 50
        mat.A44 = 1
        # trace mat
        newtube = tube.transformGeometry(mat)
        base = FreeCAD.Vector(0, 0, -(fp.dz * mul))  # dz is half height
        fp.Shape = translate(newtube, base)
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
    '''
    def createGeometry(self, fp):
        currPlacement = fp.Placement
        mul = GDMLShared.getMult(fp)
        dx = fp.dx * mul
        dy = fp.dy * mul
        h = 2 * fp.dz * mul
        if dy > dx:
            ellipse = Part.Ellipse(FreeCAD.Vector(0, 0, 0), dy, dx)
        else:
            ellipse = Part.Ellipse(FreeCAD.Vector(0, 0, 0), dx, dy)
        edge = Part.Edge(ellipse)
        edge.translate(FreeCAD.Vector(0,0,-h/2))
        if dy > dx:
            edge.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), 90)
        wire = Part.Wire(edge)
        face = Part.Face(wire)
        solid = face.extrude(FreeCAD.Vector(0, 0, h))

        fp.Shape = solid
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
