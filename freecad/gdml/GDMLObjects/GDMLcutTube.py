from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLcutTube(GDMLsolid):
    def __init__(
        self,
        obj,
        rmin,
        rmax,
        z,
        startphi,
        deltaphi,
        aunit,
        lowX,
        lowY,
        lowZ,
        highX,
        highY,
        highZ,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        """Add some custom properties to our Tube feature"""
        obj.addProperty(
            "App::PropertyFloat", "rmin", "GDMLcutTube", "Inside Radius"
        ).rmin = rmin
        obj.addProperty(
            "App::PropertyFloat", "rmax", "GDMLcutTube", "Outside Radius"
        ).rmax = rmax
        obj.addProperty(
            "App::PropertyFloat", "z", "GDMLcutTube", "Length z"
        ).z = z
        obj.addProperty(
            "App::PropertyFloat", "startphi", "GDMLcutTube", "Start Angle"
        ).startphi = startphi
        obj.addProperty(
            "App::PropertyFloat", "deltaphi", "GDMLcutTube", "Delta Angle"
        ).deltaphi = deltaphi
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLcutTube", "aunit"
        )
        setAngleQuantity(obj, aunit)
        obj.addProperty(
            "App::PropertyFloat", "lowX", "GDMLcutTube", "low X"
        ).lowX = lowX
        obj.addProperty(
            "App::PropertyFloat", "lowY", "GDMLcutTube", "low Y"
        ).lowY = lowY
        obj.addProperty(
            "App::PropertyFloat", "lowZ", "GDMLcutTube", "low Z"
        ).lowZ = lowZ
        obj.addProperty(
            "App::PropertyFloat", "highX", "GDMLcutTube", "high X"
        ).highX = highX
        obj.addProperty(
            "App::PropertyFloat", "highY", "GDMLcutTube", "high Y"
        ).highY = highY
        obj.addProperty(
            "App::PropertyFloat", "highZ", "GDMLcutTube", "high Z"
        ).highZ = highZ
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLcutTube", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLcutTube", "Material"
        )
        # print('Add material')
        # print(material)
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # print(MaterialsList)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        obj.Proxy = self
        self.Type = "GDMLcutTube"
        obj.Proxy.Type = "GDMLcutTube"
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
            "lowX",
            "lowY",
            "lowZ",
            "highX",
            "highY",
            "highZ",
            "lunit",
        ]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def cutShapeWithPlane(self, shape, plane, depth):
        "Cut a shape with a plane"
        # print('Cut Shape with Plane')
        # print('depth : '+str(depth))
        # so = plane.extrude(plane.*1e10)
        # so = plane.extrude(plane.normalAt(1,1)*1e10)
        # so = plane.extrude(plane.normalAt(1,1)*100)
        so = plane.extrude(plane.normalAt(1, 1) * depth)
        print('Plane extruded')
        # print('Plane extruded')
        # print(plane.normalAt(1,1))
        print(f" Normal {plane.normalAt(1,1)}")
        # return so
        # print('Extrude made - Now Cut')
        cut = shape.cut(so)
        # print('Return Cut')
        return cut

    def createGeometry(self, fp):
        # Munther improved version Sep 23
        currPlacement = fp.Placement
        angle = getAngleDeg(fp.aunit, fp.deltaphi)
        pntC = FreeCAD.Vector(0, 0, 0)
        dirC = FreeCAD.Vector(0, 0, 1)
        mul = GDMLShared.getMult(fp)
        rmin = mul * fp.rmin
        rmax = mul * fp.rmax
        z = mul * fp.z
        depth = 2 * max(rmax, z)
        botDir = FreeCAD.Vector(fp.lowX, fp.lowY, fp.lowZ)
        botDir.normalize()
        topDir = FreeCAD.Vector(fp.highX, fp.highY, fp.highZ)
        topDir.normalize()

        k = FreeCAD.Vector(0, 0, 1)  # vector along z -axis
        u = k - (k.dot(topDir))*topDir  # component of k vector along plane
        u.normalize()  # unit vector along major axis

        v = k.cross(u)  # unit vector along minor axis
        v.normalize()
        # print(f'u={u}, v={v}')

        costhet = k.dot(topDir)
        thet_top = math.acos(costhet)

        corner_top = u*rmax/costhet + v*rmax + z/2*k
        a = rmax/costhet  # semi-major axis
        b = rmax          # semi-minor axis

        # print(f'corner_top = {corner_top}, topDir = {topDir}')
        topPlane = Part.makePlane(
            2*a, 2*b, corner_top, topDir, -u
        )
        # Part.show(topPlane)

        k = -FreeCAD.Vector(0, 0, 1)  # vector along -z -axis
        u = k - (k.dot(botDir))*botDir  # componentof k vector along plane
        u.normalize()  # unit vector along major axis

        v = k.cross(u)  # unit vector along minor axis
        v.normalize()
        # print(f'u={u}, v={v}')

        costhet = k.dot(botDir)
        thet_bot = math.acos(costhet)

        corner_bot = u*rmax/costhet + v*rmax + z/2*k  # remember this k points down
        a = rmax/costhet  # semi-major axis
        b = rmax          # semi-minor axis
        # print(f'corner_bot = {corner_bot}, botDir = {botDir}')

        botPlane = Part.makePlane(
            2*a, 2*b, corner_bot, botDir, -u
        )
        # Part.show(botPlane)

        tube_height = z + rmax*math.tan(thet_top) + rmax*math.tan(thet_bot)

        tube1 = Part.makeCylinder(rmax, tube_height, pntC, dirC, angle)
        tube2 = Part.makeCylinder(rmin, tube_height, pntC, dirC, angle)
        tube = tube1.cut(tube2)
        tube.translate(FreeCAD.Vector(0, 0, -z/2 - rmax*math.tan(thet_bot)))

        cutTube1 = self.cutShapeWithPlane(tube, topPlane, depth)
        cutTube2 = self.cutShapeWithPlane(cutTube1, botPlane, depth)
        fp.Shape = cutTube2
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement

    def createGeometry_hardcoded(self, fp):
        angle = getAngleDeg(fp.aunit, fp.deltaphi)
        pntC = FreeCAD.Vector(0, 0, 0)
        dirC = FreeCAD.Vector(0, 0, 1)

        tube1 = Part.makeCylinder(20, 60, pntC, dirC, angle)
        tube2 = Part.makeCylinder(12, 60, pntC, dirC, angle)
        tube = tube1.cut(tube2)
        topPlane = Part.makePlane(
            100,
            100,
            FreeCAD.Vector(-20, -20, 60),
            FreeCAD.Vector(0.7, 0, 0.71),
        )
        cutTube1 = self.cutShapeWithPlane(tube, topPlane, 120)
        botPlane = Part.makePlane(
            100, 100, FreeCAD.Vector(20, 20, 0), FreeCAD.Vector(0, -0.7, -0.71)
        )
        Part.show(botPlane)
        cutTube2 = self.cutShapeWithPlane(cutTube1, botPlane, 120)
        print("Return result")
        fp.Shape = cutTube2
