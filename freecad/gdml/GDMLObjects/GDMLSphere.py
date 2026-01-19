from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLSphere(GDMLsolid):
    def __init__(
        self,
        obj,
        rmin,
        rmax,
        startphi,
        deltaphi,
        starttheta,
        deltatheta,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        """Add some custom properties to our Sphere feature"""
        GDMLShared.trace("GDMLSphere init")
        obj.addProperty(
            "App::PropertyFloat", "rmin", "GDMLSphere", "Inside Radius"
        ).rmin = rmin
        obj.addProperty(
            "App::PropertyFloat", "rmax", "GDMLSphere", "Outside Radius"
        ).rmax = rmax
        obj.addProperty(
            "App::PropertyFloat", "startphi", "GDMLSphere", "Start Angle"
        ).startphi = startphi
        obj.addProperty(
            "App::PropertyFloat", "deltaphi", "GDMLSphere", "Delta Angle"
        ).deltaphi = deltaphi
        obj.addProperty(
            "App::PropertyFloat", "starttheta", "GDMLSphere", "Start Theta pos"
        ).starttheta = starttheta
        obj.addProperty(
            "App::PropertyFloat", "deltatheta", "GDMLSphere", "Delta Angle"
        ).deltatheta = deltatheta
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLSphere", "aunit"
        )
        setAngleQuantity(obj, aunit)
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLSphere", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLSphere", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        obj.Proxy = self
        self.Type = "GDMLSphere"
        obj.Proxy.Type = "GDMLSphere"
        self.colour = colour

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
            "rmin",
            "rmax",
            "startphi",
            "deltaphi",
            "starttheta",
            "deltatheta",
            "aunit",
            "lunit",
        ]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        import math
        import FreeCAD, Part

        currPlacement = fp.Placement
        mul = GDMLShared.getMult(fp)
        rmax = mul * fp.rmax
        if rmax <= 0.0:
            return
        rmin = mul * fp.rmin

        spos = FreeCAD.Vector(0, 0, 0)
        sdir = FreeCAD.Vector(0, 0, 1)
        HalfPi = math.pi / 2.0
        tol = 1e-6  # small tolerance to avoid floating point errors

        # Handle phi slicing
        deltaphiDeg = getAngleDeg(fp.aunit, fp.deltaphi)
        if 0 < deltaphiDeg < 360.0:
            sphere = Part.makeSphere(rmax, spos, sdir, -90.0, 90.0, deltaphiDeg)
            if fp.startphi != 0:
                sphere.rotate(spos, sdir, getAngleDeg(fp.aunit, fp.startphi))
        else:
            sphere = Part.makeSphere(rmax)

        # Convert starttheta and deltatheta to radians
        startthetaRad = getAngleRad(fp.aunit, fp.starttheta)
        deltathetaRad = getAngleRad(fp.aunit, fp.deltatheta)
        thetaSumRad = startthetaRad + deltathetaRad

        # ----- Cut upper part if starttheta > 0 -----
        if startthetaRad > tol:
            if startthetaRad < HalfPi:
                # Small theta cut - use cone
                h = rmax * math.cos(startthetaRad)
                r_top = rmax * math.sin(startthetaRad)
                if h > tol:
                    cone = Part.makeCone(0.0, r_top, h, spos, FreeCAD.Vector(0, 0, 1))
                    sphere = sphere.cut(cone)
            else:
                # Theta > HalfPi - use cylinder cut to be safe
                cyl = Part.makeCylinder(
                    2.0 * rmax, rmax, spos + FreeCAD.Vector(0, 0, rmax * math.cos(startthetaRad))
                )
                sphere = sphere.cut(cyl)

        # ----- Cut lower part if deltatheta + starttheta < pi -----
        if thetaSumRad < math.pi - tol:
            if thetaSumRad > HalfPi:
                # Cone cut downward
                h = rmax * math.cos(math.pi - thetaSumRad)
                r_top = rmax * math.sin(math.pi - thetaSumRad)
                if h > tol:
                    cone = Part.makeCone(0.0, r_top, h, spos, FreeCAD.Vector(0, 0, -1))
                    sphere = sphere.cut(cone)
                # Optional cylinder to clean bottom
                cyl = Part.makeCylinder(
                    2.0 * rmax,
                    rmax,
                    spos + FreeCAD.Vector(0, 0, rmax * (-1 + math.cos(thetaSumRad))),
                )
                sphere = sphere.cut(cyl)
            elif abs(thetaSumRad - HalfPi) < tol:
                # HalfPi - simple cylinder cut
                cyl = Part.makeCylinder(2.0 * rmax, rmax, spos + FreeCAD.Vector(0, 0, -rmax))
                sphere = sphere.cut(cyl)
            elif thetaSumRad > tol:
                # Small thetaSum - use cone intersection
                cone = Part.makeCone(0.0, 2 * rmax * math.tan(thetaSumRad), 2 * rmax, spos, FreeCAD.Vector(0, 0, -1))
                sphere = sphere.common(cone)

        # ----- Apply rmin cut if needed -----
        if 0 < rmin < rmax:
            inner_sphere = Part.makeSphere(rmin)
            sphere = sphere.cut(inner_sphere)

        # Assign final shape
        fp.Shape = sphere

        # Apply scaling if present
        if hasattr(fp, "scale"):
            super().scale(fp)

        # Restore placement
        fp.Placement = currPlacement
