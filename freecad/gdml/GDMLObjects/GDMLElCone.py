from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLElCone(GDMLsolid):
    def __init__(self, obj, dx, dy, zmax, zcut, lunit, material, colour=None):
        super().__init__(obj)
        """Add some custom properties to our ElCone feature"""
        obj.addProperty(
            "App::PropertyFloat", "dx", "GDMLElCone", "x semi axis"
        ).dx = dx
        obj.addProperty(
            "App::PropertyFloat", "dy", "GDMLElCone", "y semi axis"
        ).dy = dy
        obj.addProperty(
            "App::PropertyFloat", "zmax", "GDMLElCone", "z length"
        ).zmax = zmax
        obj.addProperty(
            "App::PropertyFloat", "zcut", "GDMLElCone", "z cut"
        ).zcut = zcut
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLElCone", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLElCone", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLElCone"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLElCone"

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

        if prop in ["dx", "dy", "zmax", "zcut", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    '''
    def createGeometry(self, fp):
        # Form the Web page documentation page for elliptical cone:
        # https://geant4-userdoc.web.cern.ch/UsersGuides/ForApplicationDeveloper/html/Detector/Geometry/geomSolids.html
        # the parametric equation of the elliptical cone:
        # x = dx*(zmax - u) * cos(v), v = 0..2Pi (note, as of 2021-11-21,
        # web page mistakenly shows /u)
        # y = dy*(zmax - u) * sin(v)
        # z = u, u = -zcut..zcut
        # Therefore the bottom base of the cone (at z=u=-zcut) has
        # xmax = dxmax = dx*(zmax+zcut)
        # and ymax=dymax = dy*(zmax+zcut)
        # The ellipse at the top has simi-major axis dx*(zmax-zcut) and
        # semiminor axis dy*(zmax-zcut)
        # as per the above, the "bottom of the cone is at z = -zcut
        # Note that dx is a SCALING factor for the semi major axis,
        # NOT the actual semi major axis
        # ditto for dy

        mul = GDMLShared.getMult(fp)
        currPlacement = fp.Placement
        rmax = (fp.zmax + fp.zcut) * mul
        cone1 = Part.makeCone(rmax, 0, rmax)
        mat = FreeCAD.Matrix()
        mat.unity()
        # Semi axis values so need to double
        dx = fp.dx
        dy = fp.dy
        zcut = fp.zcut * mul
        zmax = fp.zmax * mul
        mat.A11 = dx
        mat.A22 = dy
        mat.A33 = 1
        mat.A34 = -zcut  # move bottom of cone to -zcut
        mat.A44 = 1
        xmax = dx * rmax
        ymax = dy * rmax
        cone2 = cone1.transformGeometry(mat)
        if zcut is not None:
            box = Part.makeBox(2 * xmax, 2 * ymax, zmax)
            pl = FreeCAD.Placement()
            # Only need to move to semi axis
            pl.move(FreeCAD.Vector(-xmax, -ymax, zcut))
            box.Placement = pl
            fp.Shape = cone2.cut(box)
        else:
            fp.Shape = cone2
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
        '''


    def createGeometry(self, fp):
        # Form the Web page documentation page for elliptical cone:
        # https://geant4-userdoc.web.cern.ch/UsersGuides/ForApplicationDeveloper/html/Detector/Geometry/geomSolids.html
        # the parametric equation of the elliptical cone:
        # x = dx*(zmax - u) * cos(v), v = 0..2Pi (note, as of 2021-11-21,
        # web page mistakenly shows /u)
        # y = dy*(zmax - u) * sin(v)
        # z = u, u = -zcut..zcut
        # Therefore the bottom base of the cone (at z=u=-zcut) has
        # xmax = dxmax = dx*(zmax+zcut)
        # and ymax=dymax = dy*(zmax+zcut)
        # The ellipse at the top has simi-major axis dx*(zmax-zcut) and
        # semiminor axis dy*(zmax-zcut)
        # as per the above, the "bottom of the cone is at z = -zcut
        # Note that dx is a SCALING factor for the semi major axis,
        # NOT the actual semi major axis
        # ditto for dy

        mul = GDMLShared.getMult(fp)
        currPlacement = fp.Placement
        # Semi axis values so need to double
        dx = fp.dx
        dy = fp.dy
        zcut = fp.zcut * mul
        zmax = fp.zmax * mul
        a_bot = dx*(zmax + zcut)
        a_top = dx*(zmax - zcut)
        b_bot = dy*(zmax + zcut)
        b_top = dy*(zmax - zcut)

        if dx > dy:
            ellipse_bot = Part.Ellipse(FreeCAD.Vector(0, 0, 0), a_bot, b_bot)
            ellipse_top = Part.Ellipse(FreeCAD.Vector(0, 0, 0), a_top, b_top)
        else:
            ellipse_bot = Part.Ellipse(FreeCAD.Vector(0, 0, 0), b_bot, a_bot)
            ellipse_top = Part.Ellipse(FreeCAD.Vector(0, 0, 0), b_top, a_top)

        edge_bot = Part.Edge(ellipse_bot)
        edge_top = Part.Edge(ellipse_top)

        if dy > dx:
            edge_bot.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), 90)
            edge_top.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), 90)
        edge_bot.translate(FreeCAD.Vector(0, 0, -zcut))
        edge_top.translate(FreeCAD.Vector(0, 0, zcut))

        wire_bot = Part.Wire(edge_bot)
        wire_top = Part.Wire(edge_top)
        solid = Part.makeLoft([wire_bot, wire_top], True, False)

        fp.Shape = solid
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement
