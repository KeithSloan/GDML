# insert date with Ctrl-u ESC-! date
# Wed Jan 26 04:44:48 PM PST 2022
#
# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2017 Keith Sloan <keith@sloan-home.co.uk>              *
# *             (c) Dam Lambert 2020                                       *
# *             (c) Munther Hindi 2021                                     *
# *                                                                        *
# *   This program is free software; you can redistribute it and/or modify *
# *   it under the terms of the GNU Lesser General Public License (LGPL)   *
# *   as published by the Free Software Foundation; either version 2 of    *
# *   the License, or (at your option) any later version.                  *
# *   for detail see the LICENCE text file.                                *
# *                                                                        *
# *   This program is distributed in the hope that it will be useful,      *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of       *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        *
# *   GNU Library General Public License for more details.                 *
# *                                                                        *
# *   You should have received a copy of the GNU Library General Public    *
# *   License along with this program; if not, write to the Free Software  *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 *
# *   USA                                                                  *
# *                                                                        *
# *   Acknowledgements :                                                   *
# *                                                                        *
# *                                                                        *
# **************************************************************************

import FreeCAD, FreeCADGui, Part
from pivy import coin
import math
from . import GDMLShared

# Global Material List
# Used for setting material enum in GDMLObjects
# Will be lost by file save & load
# So need to be able to rebuild from Objects
global MaterialsList
MaterialsList = []
global GroupedMaterials
GroupedMaterials = {}  # dictionary of material lists by type

global SurfsList
SurfsList = []

global LengthQuantityList
LengthQuantityList = ["nm", "um", "mm", "cm", "dm", "m", "km"]
# cf definition https://wiki.freecadweb.org/Quantity


def setLengthQuantity(obj, m):
    global LengthQuantityList
    if LengthQuantityList is not None:
        obj.lunit = LengthQuantityList
        obj.lunit = 0
        if len(LengthQuantityList) > 0:
            if not (m == 0 or m is None):
                obj.lunit = LengthQuantityList.index(m)
    else:
        obj.lunit = 2


def getSurfsListFromGroup(doc):
    SurfsList = ["None"]
    surfs = doc.getObject("Surfaces")
    if surfs is not None:
        if hasattr(surfs, "Group"):
            for i in surfs.Group:
                SurfsList.append(i.Label)
        return SurfsList
    return None


def addMaterialsFromGroup(doc, MatList, grpName):
    mmats = doc.getObject(grpName)
    if mmats is not None:
        if hasattr(mmats, "Group"):
            for i in mmats.Group:
                if i.Label != "Geant4":
                    MatList.append(i.Label)
    else:
        # rebuild Materials from scratch
        print(f"Rebuilding Materials Structure")
        from .importGDML import processGDML, joinDir

        processGDML(
            doc,
            True,
            joinDir("Resources/Default.gdml"),
            False,
            True,
        )


def rebuildMaterialsList():
    global MaterialsList
    print("Restore MaterialsList from Materials Lists")
    doc = FreeCAD.ActiveDocument
    addMaterialsFromGroup(doc, MaterialsList, "Materials")
    # print(MaterialsList)
    G4Materials = doc.getObject("G4Materials")
    if G4Materials is not None:
        for g in G4Materials.Group:
            # print(g.Label)
            addMaterialsFromGroup(doc, MaterialsList, g.Label)
    # print('MaterialsList')
    # print(MaterialsList)


def checkMaterial(material):
    global MaterialsList
    try:
        i = MaterialsList.index(material)
    except ValueError:
        return False
    return True


def setMaterial(obj, m):
    # print(f'setMaterial {obj} {m}')
    if MaterialsList is not None:
        if len(MaterialsList) > 0:
            obj.material = MaterialsList
            obj.material = 0
            if not (m == 0 or m is None):
                try:
                    obj.material = MaterialsList.index(m)
                except:
                    print("Not in List")
                    print(MaterialsList)
                    obj.material = 0
                return
            return
    rebuildMaterialsList()
    setMaterial(obj, m)


def checkFullCircle(aunit, angle):
    # print(angle)
    if aunit == "deg" and angle == 360:
        return True
    if aunit == "rad" and angle == 2 * math.pi:
        return True
    return False


# Get angle in Radians
def getAngleRad(aunit, angle):
    # print("aunit : "+str(aunit))
    if aunit == "deg":  # 0 radians 1 Degrees
        return angle * math.pi / 180
    else:
        return angle


# Get angle in Degrees
def getAngleDeg(aunit, angle):
    # print("aunit : "+str(aunit))
    if aunit == "rad":  # 0 radians 1 Degrees
        return angle * 180 / math.pi
    else:
        return angle


def makeRegularPolygon(n, r, z):
    from math import cos, sin, pi

    vecs = [
        FreeCAD.Vector(cos(2 * pi * i / n) * r, sin(2 * pi * i / n) * r, z)
        for i in range(n + 1)
    ]
    return vecs


def printPolyVec(n, v):
    print("Polygon : " + n)
    for i in v:
        print(
            "Vertex - x : "
            + str(i[0])
            + " y : "
            + str(i[1])
            + " z : "
            + str(i[2])
        )


def translate(shape, base):
    # Input Object and displacement vector - return a transformed shape
    # return shape
    myPlacement = FreeCAD.Placement()
    myPlacement.move(base)
    mat1 = myPlacement.toMatrix()
    # print(mat1)
    mat2 = shape.Matrix
    mat = mat1.multiply(mat2)
    # print(mat)
    retShape = shape.copy()
    retShape.transformShape(mat, True)
    return retShape


def make_face3(v1, v2, v3):
    # helper method to create the faces
    wire = Part.makePolygon([v1, v2, v3, v1])
    face = Part.Face(wire)
    return face


def make_face4(v1, v2, v3, v4):
    # helper method to create the faces
    wire = Part.makePolygon([v1, v2, v3, v4, v1])
    face = Part.Face(wire)
    return face


def makeFrustrum(num, poly0, poly1):
    # return list of faces
    # print("Make Frustrum : "+str(num)+" Faces")
    faces = []
    for i in range(num):
        j = i + 1
        # print([poly0[i],poly0[j],poly1[j],poly1[i]])
        w = Part.makePolygon(
            [poly0[i], poly0[j], poly1[j], poly1[i], poly0[i]]
        )
        faces.append(Part.Face(w))
    # print("Number of Faces : "+str(len(faces)))
    return faces


def angleSectionSolid(fp, rmax, z, shape):
    # Different Solids have different rmax and height
    # print("angleSectionSolid")
    # print('rmax : '+str(rmax))
    # print('z : '+str(z))
    # print("aunit : "+fp.aunit)
    startPhiDeg = getAngleDeg(fp.aunit, fp.startphi)
    deltaPhiDeg = getAngleDeg(fp.aunit, fp.deltaphi)
    # print('delta')
    # print(deltaPhiDeg)
    # print('start')
    # print(startPhiDeg)
    v1 = FreeCAD.Vector(0, 0, 0)
    v2 = FreeCAD.Vector(rmax, 0, 0)
    v3 = FreeCAD.Vector(rmax, 0, z)
    v4 = FreeCAD.Vector(0, 0, z)

    f1 = make_face4(v1, v2, v3, v4)
    s1 = f1.revolve(v1, v4, 360 - deltaPhiDeg)
    # Problem with FreeCAD 0.18
    # s2 = s1.rotate(v1,v4,startPhiDeg)

    s2 = s1.rotate(v1, v4, deltaPhiDeg)

    # Part.show(s2)
    # return(shape.cut(s2))
    # return(s2)

    shape = shape.cut(s2)
    if startPhiDeg != 0:
        shape.rotate(
            FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), startPhiDeg
        )
    return shape


def indiceToRay(indiceIn):  # Thanks to Dam
    if indiceIn < 1:
        return 0
    else:
        lray = [0.0, 1.0]
        puissanceDown = 2
        while len(lray) <= indiceIn:
            for indiceTmp in range(1, puissanceDown, 2):
                lray.append(float(indiceTmp) / float(puissanceDown))
            puissanceDown = 2 * puissanceDown
        return lray[indiceIn]


def colorFromRay(rayIn):  # Thanks to Dam
    coeffR = coeffG = coeffB = 1.0

    if rayIn < 0.2 and rayIn >= 0.0:
        coeffR = 1.0
        coeffG = rayIn * 5.0
        coeffB = 0.0
    elif rayIn < 0.4:
        coeffR = 2.0 - (5.0 * rayIn)
        coeffG = 1.0
        coeffB = 0.0
    elif rayIn < 0.6:
        coeffR = 0.0
        coeffG = 1.0
        coeffB = rayIn * 5.0 - 2.0
    elif rayIn < 0.8:
        coeffR = 1.0
        coeffG = 4.0 - (5.0 * rayIn)
        coeffB = 1.0
    elif rayIn <= 1.0:
        coeffR = (5.0 * rayIn) - 4.0
        coeffG = 0.0
        coeffB = 1.0
    return (coeffR, coeffG, coeffB, 0.0)


def colourMaterial(m):

    if MaterialsList is None:
        return (0.5, 0.5, 0.5, 0.0)
    else:
        if m is None:
            return (0.5, 0.5, 0.5, 0, 0)
        elif len(MaterialsList) <= 1:
            return (0.5, 0.5, 0.5, 0.0)
        elif m not in MaterialsList:
            return (0.5, 0.5, 0.5, 0.0)
        else:
            coeffRGB = MaterialsList.index(m)
            return colorFromRay(indiceToRay(coeffRGB))


def updateColour(obj, colour, material):
    if colour is None:
        colour = colourMaterial(material)
    obj.ViewObject.ShapeColor = colour
    # print(f'Colour {colour}')
    if colour is not None:
        obj.ViewObject.Transparency = int(colour[3] * 100)


def rotateAroundZ(nstep, z, r):
    #######################################
    # Create a polyhedron by rotation of two polylines around z-axis
    #
    # Input: nstep: number divisions along circle of revolution
    #        z   - list of z coordinates of polylines
    #        r   - list of r coordinates of polylines
    #
    verts = []
    verts.append(FreeCAD.Vector(0, 0, z[0]))
    verts.extend([FreeCAD.Vector(r[i], 0, z[i]) for i in range(0, len(z))])
    verts.append(FreeCAD.Vector(0, 0, z[len(z) - 1]))
    line = Part.makePolygon(verts)
    surf = line.revolve(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), 360)
    return Part.makeSolid(surf)


class GDMLColourMapEntry:
    def __init__(self, obj, colour, material):
        obj.addProperty(
            "App::PropertyColor", "colour", "GDMLColourMapEntry", "colour"
        ).colour = colour
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLColourMapEntry",
            "Material",
        )
        setMaterial(obj, material)


def indexBoolean(list, ln):
    # print('Length : '+str(ln))
    if ln > 3:
        # print(range(ln-3))
        for r in range(ln - 2, -1, -1):
            t = list[r].TypeId
            # print(t)
            if t == "Part::Cut" or t == "Part::Fuse" or t == "Part::Common":
                return r
    return -1


class GDMLsolid:
    def __init__(self, obj):
        """Init"""
        if hasattr(obj, "InList"):
            for j in obj.InList:
                if hasattr(j, "OutList"):
                    ln = len(j.OutList)
                    r = indexBoolean(j.OutList, ln)
                # print('index : '+str(r))
                if r >= 0:
                    if (ln - r) >= 2:
                        # print('Tool : '+obj.Label)
                        return  # Let Placement default to 0
        # obj.setEditorMode('Placement', 2)

    def getMaterial(self):
        return self.obj.material

    def scale(self, fp):
        print(f"Rescale : {fp.scale}")
        mat = FreeCAD.Matrix()
        mat.scale(fp.scale)
        fp.Shape = fp.Shape.transformGeometry(mat)

    def execute(self, fp):
        self.createGeometry(fp)

    def __getstate__(self):
        """When saving the document this object gets stored using Python's json
        module.
        Since we have some un-serializable parts here -- the Coin stuff --
        we must define this method\
        to return a tuple of all serializable objects or None."""
        if hasattr(self, "Type"):
            return {"type": self.Type}
        else:
            pass

    def __setstate__(self, arg):
        """When restoring the serialized object from document we have the
        chance to set some internals here. Since no data were serialized
        nothing needs to be done here."""
        self.Type = arg["type"]


class GDMLcommon:
    def __init__(self, obj):
        """Init"""

    def __getstate__(self):
        """When saving the document this object gets stored using Python's
        json module.
        Since we have some un-serializable parts here -- the Coin stuff --
        we must define this method
        to return a tuple of all serializable objects or None."""
        if hasattr(self, "Type"):  # If not saved just return
            return {"type": self.Type}
        else:
            pass

    def __setstate__(self, arg):
        """When restoring the serialized object from document we have the
        chance to set some internals here.
        Since no data were serialized nothing needs to be done here."""
        if arg is not None:
            self.Type = arg["type"]


class GDMLArb8(GDMLsolid):  # Thanks to Dam Lamb
    def __init__(
        self,
        obj,
        v1x,
        v1y,
        v2x,
        v2y,
        v3x,
        v3y,
        v4x,
        v4y,
        v5x,
        v5y,
        v6x,
        v6y,
        v7x,
        v7y,
        v8x,
        v8y,
        dz,
        lunit,
        material,
        colour=None,
    ):
        """Add some custom properties to our Tube feature"""
        obj.addProperty(
            "App::PropertyFloat", "v1x", "GDMLArb8", "vertex 1 x position"
        ).v1x = v1x
        obj.addProperty(
            "App::PropertyFloat", "v1y", "GDMLArb8", "vertex 1 y position"
        ).v1y = v1y
        obj.addProperty(
            "App::PropertyFloat", "v2x", "GDMLArb8", "vertex 2 x position"
        ).v2x = v2x
        obj.addProperty(
            "App::PropertyFloat", "v2y", "GDMLArb8", "vertex 2 y position"
        ).v2y = v2y
        obj.addProperty(
            "App::PropertyFloat", "v3x", "GDMLArb8", "vertex 3 x position"
        ).v3x = v3x
        obj.addProperty(
            "App::PropertyFloat", "v3y", "GDMLArb8", "vertex 3 y position"
        ).v3y = v3y
        obj.addProperty(
            "App::PropertyFloat", "v4x", "GDMLArb8", "vertex 4 x position"
        ).v4x = v4x
        obj.addProperty(
            "App::PropertyFloat", "v4y", "GDMLArb8", "vertex 4 y position"
        ).v4y = v4y
        obj.addProperty(
            "App::PropertyFloat", "v5x", "GDMLArb8", "vertex 5 x position"
        ).v5x = v5x
        obj.addProperty(
            "App::PropertyFloat", "v5y", "GDMLArb8", "vertex 5 y position"
        ).v5y = v5y
        obj.addProperty(
            "App::PropertyFloat", "v6x", "GDMLArb8", "vertex 6 x position"
        ).v6x = v6x
        obj.addProperty(
            "App::PropertyFloat", "v6y", "GDMLArb8", "vertex 6 y position"
        ).v6y = v6y
        obj.addProperty(
            "App::PropertyFloat", "v7x", "GDMLArb8", "vertex 7 x position"
        ).v7x = v7x
        obj.addProperty(
            "App::PropertyFloat", "v7y", "GDMLArb8", "vertex 7 y position"
        ).v7y = v7y
        obj.addProperty(
            "App::PropertyFloat", "v8x", "GDMLArb8", "vertex 8 x position"
        ).v8x = v8x
        obj.addProperty(
            "App::PropertyFloat", "v8y", "GDMLArb8", "vertex 8 y position"
        ).v8y = v8y
        obj.addProperty(
            "App::PropertyFloat", "dz", "GDMLArb8", "Half z Length"
        ).dz = dz
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLArb8", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLArb8", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        obj.Proxy = self
        self.Type = "GDMLArb8"
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

        if prop in [
            "v1x",
            "v1y",
            "v2x",
            "v2y",
            "v3x",
            "v3y",
            "v4x",
            "v4y",
            "v5x",
            "v5y",
            "v6x",
            "v6y",
            "v7x",
            "v7y",
            "v8x",
            "v8y",
            "dz",
            "lunit",
        ]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)
            super().scale(fp)

    # def execute(self, fp): in GDMLsolid

    # http://geant4-userdoc.web.cern.ch/geant4-userdoc/UsersGuides/ForApplicationDeveloper/html/Detector/Geometry/geomSolids.html
    # The order of specification of the coordinates for the vertices in G4GenericTrap is important. The first four points are the vertices sitting on the -hz plane; the last four points are the vertices sitting on the +hz plane.
    #
    # The order of defining the vertices of the solid is the following:
    #
    #    point 0 is connected with points 1,3,4
    #    point 1 is connected with points 0,2,5
    #    point 2 is connected with points 1,3,6
    #    point 3 is connected with points 0,2,7
    #    point 4 is connected with points 0,5,7
    #    point 5 is connected with points 1,4,6
    #    point 6 is connected with points 2,5,7
    #    point 7 is connected with points 3,4,6

    def createGeometry(self, fp):

        currPlacement = fp.Placement
        mul = GDMLShared.getMult(fp)

        pt1 = FreeCAD.Vector(fp.v1x * mul, fp.v1y * mul, -fp.dz * mul)
        pt2 = FreeCAD.Vector(fp.v2x * mul, fp.v2y * mul, -fp.dz * mul)
        pt3 = FreeCAD.Vector(fp.v3x * mul, fp.v3y * mul, -fp.dz * mul)
        pt4 = FreeCAD.Vector(fp.v4x * mul, fp.v4y * mul, -fp.dz * mul)
        pt5 = FreeCAD.Vector(fp.v5x * mul, fp.v5y * mul, fp.dz * mul)
        pt6 = FreeCAD.Vector(fp.v6x * mul, fp.v6y * mul, fp.dz * mul)
        pt7 = FreeCAD.Vector(fp.v7x * mul, fp.v7y * mul, fp.dz * mul)
        pt8 = FreeCAD.Vector(fp.v8x * mul, fp.v8y * mul, fp.dz * mul)

        faceZmin = Part.Face(Part.makePolygon([pt1, pt2, pt3, pt4, pt1]))
        faceZmax = Part.Face(Part.makePolygon([pt5, pt6, pt7, pt8, pt5]))

        faceXminA = Part.Face(Part.makePolygon([pt1, pt2, pt6, pt1]))
        faceXminB = Part.Face(Part.makePolygon([pt6, pt5, pt1, pt6]))
        faceXmaxA = Part.Face(Part.makePolygon([pt4, pt3, pt7, pt4]))
        faceXmaxB = Part.Face(Part.makePolygon([pt8, pt4, pt7, pt8]))

        faceYminA = Part.Face(Part.makePolygon([pt1, pt8, pt4, pt1]))
        faceYminB = Part.Face(Part.makePolygon([pt1, pt5, pt8, pt1]))

        faceYmaxA = Part.Face(Part.makePolygon([pt2, pt3, pt7, pt2]))
        faceYmaxB = Part.Face(Part.makePolygon([pt2, pt7, pt6, pt2]))

        fp.Shape = Part.makeSolid(
            Part.makeShell(
                [
                    faceXminA,
                    faceXminB,
                    faceXmaxA,
                    faceXmaxB,
                    faceYminA,
                    faceYminB,
                    faceYmaxA,
                    faceYmaxB,
                    faceZmin,
                    faceZmax,
                ]
            )
        )
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement


class GDMLBox(GDMLsolid):
    def __init__(self, obj, x, y, z, lunit, material, colour=None):
        super().__init__(obj)
        """Add some custom properties to our Box feature"""
        GDMLShared.trace("GDMLBox init")
        # GDMLShared.trace("material : "+material)
        obj.addProperty("App::PropertyFloat", "x", "GDMLBox", "Length x").x = x
        obj.addProperty("App::PropertyFloat", "y", "GDMLBox", "Length y").y = y
        obj.addProperty("App::PropertyFloat", "z", "GDMLBox", "Length z").z = z
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLBox", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.lunit = LengthQuantityList.index(lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLBox", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
            # Suppress Placement - position & Rotation via parent App::Part
            # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLBox"
        self.colour = colour
        obj.Proxy = self

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # Changing Shape in createGeometry will redrive onChanged
        if "Restore" in fp.State:
            return

        if prop in ["material"]:
            if FreeCAD.GuiUp:
                if hasattr(self, "colour"):
                    if self.colour is None:
                        fp.ViewObject.ShapeColor = colourMaterial(fp.material)

        if prop in ["x", "y", "z", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

        # execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        # print('createGeometry')

        if all((fp.x, fp.y, fp.z)):
            currPlacement = fp.Placement

            # if (hasattr(fp,'x') and hasattr(fp,'y') and hasattr(fp,'z')) :
            mul = GDMLShared.getMult(fp)
            GDMLShared.trace("mul : " + str(mul))
            x = mul * fp.x
            y = mul * fp.y
            z = mul * fp.z
            box = Part.makeBox(x, y, z)
            base = FreeCAD.Vector(-x / 2, -y / 2, -z / 2)
            fp.Shape = translate(box, base)
            fp.Placement = currPlacement
        if hasattr(fp, "scale"):
            super().scale(fp)

    def OnDocumentRestored(self, obj):
        print("Doc Restored")


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
        obj.aunit = ["rad", "deg"]
        obj.aunit = ["rad", "deg"].index(aunit[0:3])
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

        if prop in ["dx", "dy", "zmax", "zcut", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

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

        if prop in ["dx", "dy", "dz", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

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


class GDMLOrb(GDMLsolid):
    def __init__(self, obj, r, lunit, material, colour=None):
        super().__init__(obj)
        """Add some custom properties for Polyhedra feature"""
        obj.addProperty("App::PropertyFloat", "r", "GDMLOrb", "Radius").r = r
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLOrb", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLOrb", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLOrb"
        self.Object = obj
        self.colour = colour
        obj.Proxy = self

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

        if prop in ["r", "lunit"]:
            # print(dir(fp))
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        # GDMLShared.setTrace(True)
        GDMLShared.trace("Execute Orb")
        mul = GDMLShared.getMult(fp.lunit)
        r = mul * fp.r
        fp.Shape = Part.makeSphere(r)
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement


class GDMLPara(GDMLsolid):
    def __init__(
        self,
        obj,
        x,
        y,
        z,
        alpha,
        theta,
        phi,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        """Add some custom properties for Polyhedra feature"""
        obj.addProperty("App::PropertyFloat", "x", "GDMLParapiped", "x").x = x
        obj.addProperty("App::PropertyFloat", "y", "GDMLParapiped", "y").y = y
        obj.addProperty("App::PropertyFloat", "z", "GDMLParapiped", "z").z = z
        obj.addProperty(
            "App::PropertyFloat", "alpha", "GDMLParapiped", "Angle with y axis"
        ).alpha = alpha
        obj.addProperty(
            "App::PropertyFloat",
            "theta",
            "GDMLParapiped",
            "Polar Angle with faces",
        ).theta = theta
        obj.addProperty(
            "App::PropertyFloat",
            "phi",
            "GDMLParapiped",
            "Azimuthal Angle with faces",
        ).phi = phi
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLParapiped", "aunit"
        )
        obj.aunit = ["rad", "deg"]
        obj.aunit = ["rad", "deg"].index(aunit[0:3])
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLParapiped", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLParapiped", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLPara"
        self.colour = colour
        self.Object = obj
        obj.Proxy = self

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

        if prop in ["x", "y", "z", "alpha", "theta", "phi", "aunit", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        # GDMLShared.setTrace(True)
        GDMLShared.trace("Execute Polyparallepiped")
        mul = GDMLShared.getMult(fp)
        x = mul * fp.x
        y = mul * fp.y
        z = mul * fp.z
        alpha = getAngleRad(fp.aunit, fp.alpha)
        theta = getAngleRad(fp.aunit, fp.theta)
        phi = getAngleRad(fp.aunit, fp.phi)
        # Vertexes
        v1 = FreeCAD.Vector(0, 0, 0)
        v2 = FreeCAD.Vector(x, 0, 0)
        v3 = FreeCAD.Vector(x, y, 0)
        v4 = FreeCAD.Vector(0, y, 0)
        v5 = FreeCAD.Vector(0, 0, z)
        v6 = FreeCAD.Vector(x, 0, z)
        v7 = FreeCAD.Vector(x, y, z)
        v8 = FreeCAD.Vector(0, y, z)
        #
        # xy faces
        #
        vxy1 = [v1, v4, v3, v2, v1]
        vxy2 = [v5, v6, v7, v8, v5]
        #
        # zx faces
        #
        vzx1 = [v1, v2, v6, v5, v1]
        vzx2 = [v3, v4, v8, v7, v3]
        #
        # yz faces
        #
        vyz1 = [v5, v8, v4, v1, v5]
        vyz2 = [v2, v3, v7, v6, v2]

        # Apply alpha angle distortions
        #
        dx = z * math.tan(alpha)
        for i in range(0, 4):
            vzx2[i][0] += dx
        #
        # apply theta, phi distortions
        #
        rho = z * math.tan(theta)
        dx = rho * math.cos(phi)
        dy = rho * math.sin(phi)
        for i in range(0, 4):
            vxy2[i][0] += dx
            vxy2[i][1] += dy

        fxy1 = Part.Face(Part.makePolygon(vxy1))
        fxy2 = Part.Face(Part.makePolygon(vxy2))
        fzx1 = Part.Face(Part.makePolygon(vzx1))
        fzx2 = Part.Face(Part.makePolygon(vzx2))
        fyz1 = Part.Face(Part.makePolygon(vyz1))
        fyz2 = Part.Face(Part.makePolygon(vyz2))

        shell = Part.makeShell([fxy1, fxy2, fzx1, fzx2, fyz1, fyz2])
        solid = Part.makeSolid(shell)

        # center is mid point of diagonal
        #
        center = (v7 - v1) / 2
        fp.Shape = translate(solid, -center)
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement


class GDMLHype(GDMLsolid):
    def __init__(
        self,
        obj,
        rmin,
        rmax,
        z,
        inst,
        outst,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        """Add some custom properties for Hyperbolic Tube feature"""
        obj.addProperty(
            "App::PropertyFloat", "rmin", "GDMLHype", "inner radius at z=0"
        ).rmin = rmin
        obj.addProperty(
            "App::PropertyFloat", "rmax", "GDMLHype", "outer radius at z=0"
        ).rmax = rmax
        obj.addProperty(
            "App::PropertyFloat", "z", "GDMLHype", "Tube length"
        ).z = z
        obj.addProperty(
            "App::PropertyFloat", "inst", "GDMLHype", "Inner stereo"
        ).inst = inst
        obj.addProperty(
            "App::PropertyFloat", "outst", "GDMLHype", "Outer stero"
        ).outst = outst
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLHype", "aunit"
        )
        obj.aunit = ["rad", "deg"]
        obj.aunit = ["rad", "deg"].index(aunit[0:3])
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLHype", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLHype", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLHype"
        self.colour = colour
        self.Object = obj
        obj.Proxy = self

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

        if prop in ["rmin", "rmax", "z", "inst", "outst", "aunit", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        # GDMLShared.setTrace(True)
        GDMLShared.trace("Execute Hyperbolic Tube")
        # this should probably be a global variable, but
        # for now adopt the value used in geant4.10.07.p02
        NUMBER_OF_DIVISIONS = 36
        mul = GDMLShared.getMult(fp)
        rmin = mul * fp.rmin
        rmax = mul * fp.rmax
        z = mul * fp.z
        inst = getAngleRad(fp.aunit, fp.inst)
        outst = getAngleRad(fp.aunit, fp.outst)
        sqrtan1 = math.tan(inst)
        sqrtan1 *= sqrtan1
        sqrtan2 = math.tan(outst)
        sqrtan2 *= sqrtan2

        # mirroring error checking in HepPolyhedron.cc
        k = 0
        if rmin < 0.0 or rmax < 0.0 or rmin >= rmax:
            k = 1
        if z <= 0.0:
            k += 2

        if k != 0:
            errmsg = "HepPolyhedronHype: error in input parameters: "
            if (k & 1) != 0:
                errmsg += " (radii)"
            if (k & 2) != 0:
                errmsg += " (half-length)"
            print(errmsg)
            print(f" rmin= {rmin} rmax= {rmax}  z= {z}")
            return

        # Prepare two polylines
        ns = NUMBER_OF_DIVISIONS
        if ns < 3:
            ns = 3
        if sqrtan1 == 0.0:
            nz1 = 2
        else:
            nz1 = ns + 1
        if sqrtan2 == 0.0:
            nz2 = 2
        else:
            nz2 = ns + 1

        halfZ = z / 2
        #
        # solid generated by external hyperbeloid
        dz2 = z / (nz2 - 1)
        zz = [halfZ - dz2 * i for i in range(0, nz2)]
        rr = [math.sqrt(sqrtan2 * zi * zi + rmax * rmax) for zi in zz]
        outersolid = rotateAroundZ(NUMBER_OF_DIVISIONS, zz, rr)
        fp.Shape = outersolid

        if rmin != 0:
            #
            # solid generated by internal hyperbeloid
            dz1 = z / (nz1 - 1)
            zz = [halfZ - dz1 * i for i in range(0, nz1)]
            rr = [math.sqrt(sqrtan1 * zi * zi + rmin * rmin) for zi in zz]
            innersolid = rotateAroundZ(NUMBER_OF_DIVISIONS, zz, rr)
            fp.Shape = outersolid.cut(innersolid)
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement


class GDMLParaboloid(GDMLsolid):
    def __init__(self, obj, rlo, rhi, dz, lunit, material, colour=None):
        super().__init__(obj)
        """Add some custom properties for the Paraboloid feature"""
        obj.addProperty(
            "App::PropertyFloat", "rlo", "GDMLParaboloid", "radius at -z/2"
        ).rlo = rlo
        obj.addProperty(
            "App::PropertyFloat", "rhi", "GDMLParaboloid", "radius at +z/2"
        ).rhi = rhi
        obj.addProperty(
            "App::PropertyFloat",
            "dz",
            "GDMLParaboloid",
            "Paraboloid half length",
        ).dz = dz
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLParaboloid", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLParaboloid",
            "Material",
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLParaboloid"
        self.colour = colour
        self.Object = obj
        obj.Proxy = self

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

        if prop in ["rlo", "rhi", "z", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        # GDMLShared.setTrace(True)
        GDMLShared.trace("Execute Hyperbolic Tube")
        # this should probably be a global variable, but
        # for now adopt the value used in geant4.10.07.p02
        NUMBER_OF_DIVISIONS = 24
        mul = GDMLShared.getMult(fp)
        rlo = mul * fp.rlo
        rhi = mul * fp.rhi
        dz = mul * fp.dz
        if dz < 0 or rlo > rhi:
            errmsg = "paraboloid: error in input parameters: dz < 0 and/or rlo > rhi"
            print(errmsg)
            print(f" rlo= {rlo} rhi= {rhi}  dz= {dz}")
            return

        # Prepare polylines
        ns = NUMBER_OF_DIVISIONS
        # paraboloid given by following equation:
        # rho^2 = k1 * z + k2, (rho = distance of point on surface from z-axis)
        # k1 and k2 can be obtained from requirement:
        # rlo^2 = k1*(-dz) + k2
        # rhi^2 = k1*(dz) + k2
        k1 = (rhi * rhi - rlo * rlo) / (2 * dz)
        k2 = (rhi * rhi + rlo * rlo) / 2
        #
        # solid generated by external hyperbeloid
        deltaz = 2 * dz / (ns - 1)
        zz = [dz - deltaz * i for i in range(0, ns)]
        rr = [math.sqrt(k1 * zi + k2) for zi in zz]
        outersolid = rotateAroundZ(NUMBER_OF_DIVISIONS, zz, rr)
        fp.Shape = outersolid
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement


class GDMLPolyhedra(GDMLsolid):
    def __init__(
        self,
        obj,
        startphi,
        deltaphi,
        numsides,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        """Add some custom properties for Polyhedra feature"""
        obj.addProperty(
            "App::PropertyFloat", "startphi", "GDMLPolyhedra", "Start Angle"
        ).startphi = startphi
        obj.addProperty(
            "App::PropertyFloat", "deltaphi", "GDMLPolyhedra", "Delta Angle"
        ).deltaphi = deltaphi
        obj.addProperty(
            "App::PropertyInteger",
            "numsides",
            "GDMLPolyhedra",
            "Number of Side",
        ).numsides = numsides
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLPolyhedra", "aunit"
        )
        obj.aunit = ["rad", "deg"]
        obj.aunit = ["rad", "deg"].index(aunit[0:3])
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLPolyhdera", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLPolyhedra", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLPolyhedra"
        self.colour = colour
        self.Object = obj
        obj.Proxy = self

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

        if prop in ["startphi", "deltaphi", "numsides", "aunit", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        from math import sin, cos, pi

        currPlacement = fp.Placement
        # GDMLShared.setTrace(True)
        GDMLShared.trace("Execute Polyhedra")
        parms = fp.OutList
        GDMLShared.trace("Number of parms : " + str(len(parms)))
        numsides = fp.numsides
        GDMLShared.trace("Number of sides : " + str(numsides))
        mul = GDMLShared.getMult(fp)
        z0 = parms[0].z * mul
        rmin0 = parms[0].rmin * mul
        rmax0 = parms[0].rmax * mul
        GDMLShared.trace("Top z    : " + str(z0))
        GDMLShared.trace("Top rmin : " + str(rmin0))
        GDMLShared.trace("Top rmax : " + str(rmax0))
        fullCircle = checkFullCircle(fp.aunit, fp.deltaphi)
        faces = []
        # numsides = int(numsides * 360 / getAngleDeg(fp.aunit, fp.deltaphi))
        # Deal with Inner Top Face
        # Could be point rmin0 = rmax0 = 0
        dPhi = getAngleRad(fp.aunit, fp.deltaphi) / numsides
        phi0 = getAngleRad(fp.aunit, fp.startphi)
        rp = rmin0 / cos(dPhi / 2)
        inner_poly0 = [
            FreeCAD.Vector(
                rp * cos(phi0 + i * dPhi), rp * sin(phi0 + i * dPhi), z0
            )
            for i in range(numsides + 1)
        ]
        rp = rmax0 / cos(dPhi / 2)
        outer_poly0 = [
            FreeCAD.Vector(
                rp * cos(phi0 + i * dPhi), rp * sin(phi0 + i * dPhi), z0
            )
            for i in range(numsides + 1)
        ]
        bottom_verts = inner_poly0 + outer_poly0[::-1]
        bottom_verts.append(bottom_verts[0])
        if rmax0 > 0:
            faces.append(Part.Face(Part.makePolygon(bottom_verts)))
        for ptr in parms[1:]:
            z1 = ptr.z * mul
            rmin1 = ptr.rmin * mul
            rmax1 = ptr.rmax * mul
            GDMLShared.trace("z1    : " + str(z1))
            GDMLShared.trace("rmin1 : " + str(rmin1))
            GDMLShared.trace("rmax1 : " + str(rmax1))
            # Concat face lists
            rp = rmin1 / cos(dPhi / 2)
            inner_poly1 = [
                FreeCAD.Vector(
                    rp * cos(phi0 + i * dPhi), rp * sin(phi0 + i * dPhi), z1
                )
                for i in range(numsides + 1)
            ]
            faces = faces + makeFrustrum(numsides, inner_poly0, inner_poly1)
            inner_poly0 = inner_poly1
            # Deal with Outer
            rp = rmax1 / cos(dPhi / 2)
            outer_poly1 = [
                FreeCAD.Vector(
                    rp * cos(phi0 + i * dPhi), rp * sin(phi0 + i * dPhi), z1
                )
                for i in range(numsides + 1)
            ]
            faces = faces + makeFrustrum(numsides, outer_poly0, outer_poly1)
            # update for next zsection
            outer_poly0 = outer_poly1
            z0 = z1

        if not fullCircle:  # build side faces
            side0_verts = []
            for p in parms:
                r = p.rmax * mul / cos(dPhi / 2)
                side0_verts.append(
                    FreeCAD.Vector(r * cos(phi0), r * sin(phi0), p.z)
                )
            for p in reversed(parms):
                r = p.rmin * mul / cos(dPhi / 2)
                side0_verts.append(
                    FreeCAD.Vector(r * cos(phi0), r * sin(phi0), p.z)
                )
            side0_verts.append(side0_verts[0])
            faces.append(Part.Face(Part.makePolygon(side0_verts)))
            siden_verts = []
            phi = phi0 + numsides * dPhi
            for p in parms:
                r = p.rmax * mul / cos(dPhi / 2)
                siden_verts.append(
                    FreeCAD.Vector(r * cos(phi), r * sin(phi), p.z)
                )
            for p in reversed(parms):
                r = p.rmin * mul / cos(dPhi / 2)
                siden_verts.append(
                    FreeCAD.Vector(r * cos(phi), r * sin(phi), p.z)
                )
            siden_verts.append(siden_verts[0])
            faces.append(Part.Face(Part.makePolygon(siden_verts)))

        # add top polygon face
        top_verts = outer_poly1 + inner_poly1[::-1]
        top_verts.append(top_verts[0])
        if rmax1 > 0:
            faces.append(Part.Face(Part.makePolygon(top_verts)))
        GDMLShared.trace("Total Faces : " + str(len(faces)))
        shell = Part.makeShell(faces)
        fp.Shape = Part.makeSolid(shell)
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement


class GDMLGenericPolyhedra(GDMLsolid):
    def __init__(
        self,
        obj,
        startphi,
        deltaphi,
        numsides,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        """Add some custom properties for Generic Polyhedra feature"""
        obj.addProperty(
            "App::PropertyFloat",
            "startphi",
            "GDMLGenericPolyhedra",
            "Start Angle",
        ).startphi = startphi
        obj.addProperty(
            "App::PropertyFloat",
            "deltaphi",
            "GDMLGenericPolyhedra",
            "Delta Angle",
        ).deltaphi = deltaphi
        obj.addProperty(
            "App::PropertyInteger",
            "numsides",
            "GDMLGenericPolyhedra",
            "Number of Side",
        ).numsides = numsides
        obj.addProperty(
            "App::PropertyEnumeration",
            "aunit",
            "GDMLGenericPolyhedra",
            "aunit",
        )
        obj.aunit = ["rad", "deg"]
        obj.aunit = ["rad", "deg"].index(aunit[0:3])
        obj.addProperty(
            "App::PropertyEnumeration",
            "lunit",
            "GDMLGenericPolyhdera",
            "lunit",
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLGenericPolyhedra",
            "Material",
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLGenericPolyhedra"
        self.colour = colour
        self.Object = obj
        obj.Proxy = self

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

        if prop in ["startphi", "deltaphi", "numsides", "aunit", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        # GDMLShared.setTrace(True)
        GDMLShared.trace("Execute GenericPolyhedra")
        rzpoints = fp.OutList
        if len(rzpoints) < 3:
            print("Error in genericPolyhedra: number of rzpoints less than 3")
            return
        GDMLShared.trace("Number of rzpoints : " + str(len(rzpoints)))
        numsides = fp.numsides
        GDMLShared.trace("Number of sides : " + str(numsides))
        mul = GDMLShared.getMult(fp)
        faces = []
        startphi = getAngleRad(fp.aunit, fp.startphi)
        dphi = getAngleRad(fp.aunit, fp.deltaphi) / numsides
        # form vertexes
        verts = []
        for ptr in rzpoints:
            z = ptr.z * mul
            r = ptr.r * mul
            phi = startphi
            for i in range(0, numsides + 1):
                v = FreeCAD.Vector(r * math.cos(phi), r * math.sin(phi), z)
                verts.append(v)
                phi += dphi

        numverts = len(verts)
        stride = numsides + 1
        # outer faces
        for k0 in range(0, numverts - stride, stride):
            for i in range(0, numsides):
                k = k0 + i
                wire = Part.makePolygon(
                    [
                        verts[k],
                        verts[k + stride],
                        verts[k + stride + 1],
                        verts[k + 1],
                        verts[k],
                    ]
                )
                faces.append(Part.Face(wire))

        # inner faces
        for i in range(0, numsides):
            k = numverts - stride + i
            wire = Part.makePolygon(
                [verts[i], verts[k], verts[k + 1], verts[i + 1], verts[i]]
            )
            faces.append(Part.Face(wire))

        # side faces
        if checkFullCircle(fp.aunit, fp.deltaphi) is False:
            verts1 = [
                verts[k] for k in range(0, numverts - stride + 1, stride)
            ]
            verts1.append(verts1[0])
            wire = Part.makePolygon(verts1)
            faces.append(Part.Face(wire))
            verts1 = [verts[k] for k in range(numsides, numverts, stride)]
            verts1.append(verts1[0])
            wire = Part.makePolygon(verts1)
            faces.append(Part.Face(wire))

        shell = Part.makeShell(faces)
        solid = Part.makeSolid(shell)
        fp.Shape = solid
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement


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


class GDMLTwistedbox(GDMLsolid):
    def __init__(
        self, obj, PhiTwist, x, y, z, aunit, lunit, material, colour=None
    ):
        super().__init__(obj)
        """Add some custom properties to our Box feature"""
        GDMLShared.trace("GDMLTwistedbox init")
        # GDMLShared.trace("material : "+material)
        obj.addProperty(
            "App::PropertyFloat", "x", "GDMLTwistedbox", "Length x"
        ).x = x
        obj.addProperty(
            "App::PropertyFloat", "y", "GDMLTwistedbox", "Length y"
        ).y = y
        obj.addProperty(
            "App::PropertyFloat", "z", "GDMLTwistedbox", "Length z"
        ).z = z
        angle = getAngleDeg(aunit, PhiTwist)
        if angle > 90:
            print("PhiTwist angle cannot be larger than 90 deg")
            angle = 90
            aunit = "deg"
        elif angle < -90:
            print("PhiTwist angle cannot be less than -90 deg")
            angle = -90
            aunit = "deg"
        else:
            angle = PhiTwist

        obj.addProperty(
            "App::PropertyFloat", "PhiTwist", "GDMLTwistedbox", "Twist Angle"
        ).PhiTwist = angle
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLTwistedbox", "aunit"
        )
        obj.aunit = ["rad", "deg"]
        obj.aunit = ["rad", "deg"].index(aunit[0:3])
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTwistedbox", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLTwistedbox",
            "Material",
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLTwistedbox"
        self.colour = colour
        obj.Proxy = self

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # Changing Shape in createGeometry will redrive onChanged
        if "Restore" in fp.State:
            return

        if prop in ["material"]:
            if FreeCAD.GuiUp:
                if self.colour is None:
                    fp.ViewObject.ShapeColor = colourMaterial(fp.material)

        if prop in ["x", "y", "z", "PhiTwist", "lunit", "aunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        # print('createGeometry')
        # print(fp)

        if all((fp.x, fp.y, fp.z, fp.PhiTwist)):
            currPlacement = fp.Placement

            # if (hasattr(fp,'x') and hasattr(fp,'y') and hasattr(fp,'z')) :
            mul = GDMLShared.getMult(fp)
            GDMLShared.trace("mul : " + str(mul))
            x = mul * fp.x
            y = mul * fp.y
            z = mul * fp.z
            angle = getAngleDeg(fp.aunit, fp.PhiTwist)
            # lower rectanngle vertexes
            v1 = FreeCAD.Vector(-x / 2, -y / 2, -z / 2)
            v2 = FreeCAD.Vector(x / 2, -y / 2, -z / 2)
            v3 = FreeCAD.Vector(x / 2, y / 2, -z / 2)
            v4 = FreeCAD.Vector(-x / 2, y / 2, -z / 2)
            pbot = Part.makePolygon([v1, v2, v3, v4, v1])
            slices = []
            N = 5
            dz = z / (N - 1)
            dPhi = angle / (N - 1)
            for i in range(0, N):
                p = pbot.translated(FreeCAD.Vector(0, 0, i * dz))
                p.rotate(
                    FreeCAD.Vector(0, 0, 0),
                    FreeCAD.Vector(0, 0, 1),
                    -angle / 2 + i * dPhi,
                )
                slices.append(p)
            loft = Part.makeLoft(slices, True, False)

            fp.Shape = loft
            if hasattr(fp, "scale"):
                super().scale(fp)
            fp.Placement = currPlacement

    def OnDocumentRestored(self, obj):
        print("Doc Restored")


class GDMLTwistedtrap(GDMLsolid):
    def __init__(
        self,
        obj,
        PhiTwist,
        z,
        theta,
        phi,
        x1,
        x2,
        x3,
        x4,
        y1,
        y2,
        alpha,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        """General Trapezoid"""
        obj.addProperty(
            "App::PropertyFloat", "PhiTwist", "GDMLTwistedtrap", "Twist angle"
        ).PhiTwist = PhiTwist
        obj.addProperty(
            "App::PropertyFloat", "z", "GDMLTwistedtrap", "z"
        ).z = z
        obj.addProperty(
            "App::PropertyFloat", "Theta", "GDMLTwistedtrap", "Theta"
        ).Theta = theta
        obj.addProperty(
            "App::PropertyFloat", "Phi", "GDMLTwistedtrap", "Phi"
        ).Phi = phi
        obj.addProperty(
            "App::PropertyFloat",
            "x1",
            "GDMLTwistedtrap",
            "Length x at y= -y1/2 of face at -z/2",
        ).x1 = x1
        obj.addProperty(
            "App::PropertyFloat",
            "x2",
            "GDMLTwistedtrap",
            "Length x at y= +y1/2 of face at -z/2",
        ).x2 = x2
        obj.addProperty(
            "App::PropertyFloat",
            "x3",
            "GDMLTwistedtrap",
            "Length x at y= -y2/2 of face at +z/2",
        ).x3 = x3
        obj.addProperty(
            "App::PropertyFloat",
            "x4",
            "GDMLTwistedtrap",
            "Length x at y= +y2/2 of face at +z/2",
        ).x4 = x4
        obj.addProperty(
            "App::PropertyFloat",
            "y1",
            "GDMLTwistedtrap",
            "Length y at face -z/2",
        ).y1 = y1
        obj.addProperty(
            "App::PropertyFloat",
            "y2",
            "GDMLTwistedtrap",
            "Length y at face +z/2",
        ).y2 = y2
        obj.addProperty(
            "App::PropertyFloat", "Alph", "GDMLTwistedtrap", "Alph"
        ).Alph = alpha
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLTwistedtrap", "aunit"
        )
        obj.aunit = ["rad", "deg"]
        obj.aunit = ["rad", "deg"].index(aunit[0:3])
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTwistedtrap", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLTwistedtrap",
            "Material",
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        obj.Proxy = self
        self.Type = "GDMLTwistedtrap"
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

        if prop in [
            "PhiTwist",
            "z",
            "theta",
            "phi",
            "x1",
            "x2",
            "x3",
            "x4",
            "y1",
            "y2",
            "alpha",
            "aunit",
            "lunit",
        ]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        # Define six vetices for the shape
        alpha = getAngleRad(fp.aunit, fp.Alph)
        theta = getAngleRad(fp.aunit, fp.Theta)
        phi = getAngleRad(fp.aunit, fp.Phi)
        PhiTwist = getAngleDeg(fp.aunit, fp.PhiTwist)
        mul = GDMLShared.getMult(fp)
        y1 = mul * fp.y1
        x1 = mul * fp.x1
        x2 = mul * fp.x2
        y2 = mul * fp.y2
        x3 = mul * fp.x3
        x4 = mul * fp.x4
        z = mul * fp.z

        N = 9
        dz = z / (N - 1)
        dTwist = PhiTwist / (N - 1)

        tanalpha = math.tan(alpha)

        dt = 1.0 / (N - 1)
        t = 0
        slices = []
        tanthet = math.tan(theta)
        cosphi = math.cos(phi)
        sinphi = math.sin(phi)
        rhomax = z * tanthet
        xoffset = -rhomax * cosphi / 2
        yoffset = -rhomax * sinphi / 2
        for i in range(0, N):
            # Vertexes, counter clock wise order
            y = y1 + t * (y2 - y1)  # go continuously from y1 to y2
            dx = y * tanalpha
            x13 = x1 + t * (x3 - x1)  # go continuously from x1 to x3
            x24 = x2 + t * (x4 - x2)  # go continuously from x1 to x3
            zt = -z / 2 + t * z
            rho = i * dz * tanthet
            dxphi = xoffset + rho * cosphi
            dyphi = yoffset + rho * sinphi
            v1 = FreeCAD.Vector(-x13 / 2 - dx / 2 + dxphi, -y / 2 + dyphi, zt)
            v2 = FreeCAD.Vector(x13 / 2 - dx / 2 + dxphi, -y / 2 + dyphi, zt)
            v3 = FreeCAD.Vector(x24 / 2 + dx / 2 + dxphi, y / 2 + dyphi, zt)
            v4 = FreeCAD.Vector(-x24 / 2 + dx / 2 + dxphi, y / 2 + dyphi, zt)
            p = Part.makePolygon([v1, v2, v3, v4, v1])
            p.rotate(
                FreeCAD.Vector(0, 0, 0),
                FreeCAD.Vector(0, 0, 1),
                -PhiTwist / 2 + i * dTwist,
            )
            slices.append(p)
            t += dt

        loft = Part.makeLoft(slices, True, False)
        fp.Shape = loft
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement


class GDMLTwistedtrd(GDMLsolid):
    def __init__(
        self,
        obj,
        PhiTwist,
        z,
        x1,
        x2,
        y1,
        y2,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        "3.4.15 : Trapezoid – x & y varying along z"
        obj.addProperty("App::PropertyFloat", "z", "GDMLTwistedtrd", "z").z = z
        obj.addProperty(
            "App::PropertyFloat",
            "x1",
            "GDMLTwistedtrd",
            "Length x at face -z/2",
        ).x1 = x1
        obj.addProperty(
            "App::PropertyFloat",
            "x2",
            "GDMLTwistedtrd",
            "Length x at face +z/2",
        ).x2 = x2
        obj.addProperty(
            "App::PropertyFloat",
            "y1",
            "GDMLTwistedtrd",
            "Length y at face -z/2",
        ).y1 = y1
        obj.addProperty(
            "App::PropertyFloat",
            "y2",
            "GDMLTwistedtrd",
            "Length y at face +z/2",
        ).y2 = y2
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTwistedtrd", "lunit"
        )
        angle = getAngleDeg(aunit, PhiTwist)
        if angle > 90:
            print("PhiTwist angle cannot be larger than 90 deg")
            angle = 90
            aunit = "deg"
        elif angle < -90:
            print("PhiTwist angle cannot be less than -90 deg")
            angle = -90
            aunit = "deg"
        else:
            angle = PhiTwist

        obj.addProperty(
            "App::PropertyFloat", "PhiTwist", "GDMLTwistedtrd", "Twist Angle"
        ).PhiTwist = angle
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLTwistedtrd", "aunit"
        )
        obj.aunit = ["rad", "deg"]
        obj.aunit = ["rad", "deg"].index(aunit[0:3])
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLTwistedtrd",
            "Material",
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLTwistedtrd"
        self.colour = colour
        obj.Proxy = self

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # Changing Shape in createGeometry will redrive onChanged
        if "Restore" in fp.State:
            return

        if prop in ["material"]:
            if FreeCAD.GuiUp:
                if self.colour is None:
                    fp.ViewObject.ShapeColor = colourMaterial(fp.material)

        if prop in ["x1", "y1", "x2", "y2", "z", "PhiTwist", "lunit", "aunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)
            super().scale(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        # print('createGeometry')
        # print(fp)

        if all((fp.x1, fp.x2, fp.y1, fp.y2, fp.z, fp.PhiTwist)):
            currPlacement = fp.Placement

            # if (hasattr(fp,'x') and hasattr(fp,'y') and hasattr(fp,'z')) :
            mul = GDMLShared.getMult(fp)
            x1 = fp.x1 * mul
            x2 = fp.x2 * mul
            y1 = fp.y1 * mul
            y2 = fp.y2 * mul
            z = fp.z * mul
            GDMLShared.trace("mul : " + str(mul))
            angle = getAngleDeg(fp.aunit, fp.PhiTwist)
            slices = []
            N = 9  # number of slices
            dz = z / (N - 1)
            dPhi = angle / (N - 1)
            for i in range(0, N):
                t = i * 1.0 / (N - 1)
                xside = x1 + t * (x2 - x1)
                yside = y1 + t * (y2 - y1)
                v1 = FreeCAD.Vector(-xside / 2, -yside / 2, -z / 2 + i * dz)
                v2 = FreeCAD.Vector(xside / 2, -yside / 2, -z / 2 + i * dz)
                v3 = FreeCAD.Vector(xside / 2, yside / 2, -z / 2 + i * dz)
                v4 = FreeCAD.Vector(-xside / 2, yside / 2, -z / 2 + i * dz)
                p = Part.makePolygon([v1, v2, v3, v4, v1])
                p.rotate(
                    FreeCAD.Vector(0, 0, 0),
                    FreeCAD.Vector(0, 0, 1),
                    -angle / 2 + i * dPhi,
                )
                slices.append(p)

            loft = Part.makeLoft(slices, True, False)
            fp.Shape = loft
            if hasattr(fp, "scale"):
                super().scale(fp)
            fp.Placement = currPlacement

    def OnDocumentRestored(self, obj):
        print("Doc Restored")


class GDMLTwistedtubs(GDMLsolid):
    def __init__(
        self,
        obj,
        endinnerrad,
        endouterrad,
        zlen,
        twistedangle,
        phi,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        """Twisted tube"""
        obj.addProperty(
            "App::PropertyFloat", "zlen", "GDMLTwistedtubs", "zlen"
        ).zlen = zlen
        obj.addProperty(
            "App::PropertyFloat",
            "endinnerrad",
            "GDMLTwistedtubs",
            "Inside radius at caps",
        ).endinnerrad = endinnerrad
        obj.addProperty(
            "App::PropertyFloat",
            "endouterrad",
            "GDMLTwistedtubs",
            "Outside radius at caps",
        ).endouterrad = endouterrad
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTwistedtubs", "lunit"
        )
        angle = getAngleDeg(aunit, twistedangle)
        if angle > 90:
            print("PhiTwist angle cannot be larger than 90 deg")
            angle = 90
            aunit = "deg"
        elif angle < -90:
            print("PhiTwist angle cannot be less than -90 deg")
            angle = -90
            aunit = "deg"
        else:
            angle = twistedangle

        obj.addProperty(
            "App::PropertyFloat",
            "twistedangle",
            "GDMLTwistedtubs",
            "Twist Angle",
        ).twistedangle = angle
        obj.addProperty(
            "App::PropertyFloat", "phi", "GDMLTwistedtubs", "Delta phi"
        ).phi = phi
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLTwistedtubs", "aunit"
        )
        obj.aunit = ["rad", "deg"]
        obj.aunit = ["rad", "deg"].index(aunit[0:3])
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLTwistedtubs",
            "Material",
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLTwistedtubs"
        self.colour = colour
        obj.Proxy = self

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # Changing Shape in createGeometry will redrive onChanged
        if "Restore" in fp.State:
            return

        if prop in ["material"]:
            if FreeCAD.GuiUp:
                if self.colour is None:
                    fp.ViewObject.ShapeColor = colourMaterial(fp.material)

        if prop in [
            "endinnerrad",
            "endouterrad",
            "zlen",
            "twistedangle",
            "phi",
            "lunit",
            "aunit",
        ]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        # print('createGeometry')
        # print(fp)

        if all((fp.endouterrad, fp.zlen, fp.phi)):
            currPlacement = fp.Placement

            mul = GDMLShared.getMult(fp)
            rin = fp.endinnerrad * mul
            rout = fp.endouterrad * mul
            if rin > rout:
                print(
                    f"Error: Inner radius ({rin}) greater than outer radius ({rout})"
                )
                return
            zlen = fp.zlen * mul
            GDMLShared.trace("mul : " + str(mul))
            angle = getAngleDeg(fp.aunit, fp.twistedangle)
            phi = getAngleRad(fp.aunit, fp.phi)
            phideg = getAngleDeg(fp.aunit, fp.phi)
            slices = []
            N = 9  # number of slices
            dz = zlen / (N - 1)
            dtwist = angle / (N - 1)
            # construct base wire
            # Vertexes
            v1 = FreeCAD.Vector(rin, 0, 0)
            v2 = FreeCAD.Vector(rout, 0, 0)
            v3 = FreeCAD.Vector(rout * math.cos(phi), rout * math.sin(phi), 0)
            v4 = FreeCAD.Vector(rin * math.cos(phi), rin * math.sin(phi), 0)
            # arc center points
            vCin = FreeCAD.Vector(
                rin * math.cos(phi / 2), rin * math.sin(phi / 2), 0
            )
            vCout = FreeCAD.Vector(
                rout * math.cos(phi / 2), rout * math.sin(phi / 2), 0
            )
            # Center of twisting
            rc = (rin + rout) / 2
            vc = FreeCAD.Vector(
                rc * math.cos(phi / 2), rc * math.sin(phi / 2), 0
            )
            # wire
            arcin = Part.Arc(v1, vCin, v4)
            line1 = Part.LineSegment(v4, v3)
            arcout = Part.Arc(v3, vCout, v2)
            line2 = Part.LineSegment(v2, v1)

            s = Part.Shape([arcin, line1, arcout, line2])
            w = Part.Wire(s.Edges)
            angoffset = -angle / 2 - phideg / 2

            for i in range(0, N):
                p = w.translated(FreeCAD.Vector(0, 0, -zlen / 2 + i * dz))
                p.rotate(vc, FreeCAD.Vector(0, 0, 1), angoffset + i * dtwist)
                slices.append(p)

            loft = Part.makeLoft(slices, True, False)
            fp.Shape = loft
            if hasattr(fp, "scale"):
                super().scale(fp)
            fp.Placement = currPlacement

    def OnDocumentRestored(self, obj):
        print("Doc Restored")


class GDMLXtru(GDMLsolid):
    def __init__(self, obj, lunit, material, colour=None):
        super().__init__(obj)
        obj.addExtension("App::GroupExtensionPython")
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLXtru", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLXtru", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLXtru"
        self.colour = colour
        obj.Proxy = self

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

        if prop in ["startphi", "deltaphi", "aunit", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def layerPoints(self, polyList, sf, xOffset, yOffset, zPosition):
        vl = []
        for p in polyList:
            # print(p)
            vl.append(
                FreeCAD.Vector(
                    p[0] * sf + xOffset, p[1] * sf + yOffset, zPosition
                )
            )
        # Close list
        vl.append(vl[0])
        return vl

    def createGeometry(self, fp):
        # GDMLShared.setTrace(True)
        currPlacement = fp.Placement
        # print("Create Geometry")
        parms = fp.OutList
        # print("OutList")
        # print(parms)
        GDMLShared.trace("Number of parms : " + str(len(parms)))
        polyList = []
        faceList = []
        sections = []
        mul = GDMLShared.getMult(fp)
        for ptr in parms:
            if hasattr(ptr, "x"):
                x = ptr.x * mul
                y = ptr.y * mul
                GDMLShared.trace("x : " + str(x))
                GDMLShared.trace("y : " + str(y))
                polyList.append([x, y])
            if hasattr(ptr, "zOrder"):
                zOrder = ptr.zOrder
                xOffset = ptr.xOffset * mul
                yOffset = ptr.yOffset * mul
                zPosition = ptr.zPosition * mul
                sf = ptr.scalingFactor
                s = [zOrder, xOffset, yOffset, zPosition, sf]
                sections.append(s)
        # print('sections : '+str(len(sections)))
        #
        # Deal with Base Face
        #
        # baseList = layerPoints(polyList,sf,xOffset,yOffset,zPosition):
        # form all vertexes
        verts = []
        for s in sections:
            verts += self.layerPoints(polyList, s[4], s[1], s[2], s[3])

        numverts = len(verts)
        numsides = len(polyList)
        stride = numsides + 1
        # side faces
        for k0 in range(0, numverts - stride, stride):
            for i in range(0, numsides):
                k = k0 + i
                wire = Part.makePolygon(
                    [
                        verts[k],
                        verts[k + stride],
                        verts[k + stride + 1],
                        verts[k + 1],
                        verts[k],
                    ]
                )
                faceList.append(Part.Face(wire))
        # bottom face
        wire = Part.makePolygon(verts[0 : numsides + 1])
        faceList.append(Part.Face(wire))
        # Top face
        wire = Part.makePolygon(verts[numverts - numsides - 1 :])
        faceList.append(Part.Face(wire))

        shell = Part.makeShell(faceList)
        solid = Part.makeSolid(shell)
        fp.Shape = solid
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement


class GDML2dVertex(GDMLcommon):
    def __init__(self, obj, x, y):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyString", "Type", "Vertex", "twoDimVertex"
        ).Type = "twoDimVertex"
        obj.addProperty("App::PropertyFloat", "x", "Vertex", "x").x = x
        obj.addProperty("App::PropertyFloat", "y", "Vertex", "y").y = y
        obj.setEditorMode("Type", 1)
        self.Type = "Vertex"
        self.Object = obj
        obj.Proxy = self

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # if prop in ['x','y'] :
        #   self.execute(fp)
        # GDMLShared.trace("Change property: " + str(prop) + "\n")
        pass

    def execute(self, fp):
        pass


class GDMLSection(GDMLcommon):
    def __init__(
        self, obj, zOrder, zPosition, xOffset, yOffset, scalingFactor
    ):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyString", "Type", "section", "section"
        ).Type = "section"
        obj.addProperty(
            "App::PropertyInteger", "zOrder", "section", "zOrder"
        ).zOrder = zOrder
        obj.addProperty(
            "App::PropertyFloat", "zPosition", "section", "zPosition"
        ).zPosition = zPosition
        obj.addProperty(
            "App::PropertyFloat", "xOffset", "section", "xOffset"
        ).xOffset = xOffset
        obj.addProperty(
            "App::PropertyFloat", "yOffset", "section", "yOffset"
        ).yOffset = yOffset
        obj.addProperty(
            "App::PropertyFloat", "scalingFactor", "section", "scalingFactor"
        ).scalingFactor = scalingFactor
        obj.setEditorMode("Type", 1)
        self.Type = "section"
        obj.Proxy = self

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # if prop in ['zOrder','zPosition','xOffset','yOffset','scaleFactor'] :
        #   self.execute(fp)
        # GDMLShared.trace("Change property: " + str(prop) + "\n")
        pass

    def execute(self, fp):
        pass


class GDMLzplane(GDMLcommon):
    def __init__(self, obj, rmin, rmax, z):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyFloat", "rmin", "zplane", "Inside Radius"
        ).rmin = rmin
        obj.addProperty(
            "App::PropertyFloat", "rmax", "zplane", "Outside Radius"
        ).rmax = rmax
        obj.addProperty("App::PropertyFloat", "z", "zplane", "z").z = z
        self.Type = "zplane"
        obj.Proxy = self

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # if not ('Restore' in fp.State) :
        # if prop in ['rmin','rmax','z'] :
        #   self.execute(fp)
        # GDMLShared.trace("Change property: " + str(prop) + "\n")
        pass

    def execute(self, fp):
        pass


class GDMLrzpoint(GDMLcommon):
    def __init__(self, obj, r, z):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyFloat", "r", "rzpoint", "r-coordinate"
        ).r = r
        obj.addProperty(
            "App::PropertyFloat", "z", "rzpoint", "z-coordinate"
        ).z = z
        self.Type = "zplane"
        obj.Proxy = self

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # if not ('Restore' in fp.State) :
        # if prop in ['rmin','rmax','z'] :
        #   self.execute(fp)
        # GDMLShared.trace("Change property: " + str(prop) + "\n")
        pass

    def execute(self, fp):
        pass


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
        obj.aunit = ["rad", "deg"]
        obj.aunit = ["rad", "deg"].index(aunit[0:3])
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
                z1 = zplanes[i].z * mul - offset
            else:
                rmin1 = rmin2  # for i > 0, rmin2 will have been defined below
                rmax1 = rmax2
                z1 = z2

            rmin2 = zplanes[i + 1].rmin * mul
            rmax2 = zplanes[i + 1].rmax * mul
            z2 = zplanes[i + 1].z * mul - offset

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
        obj.aunit = ["rad", "deg"]
        obj.aunit = ["rad", "deg"].index(aunit[0:3])
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
        obj.aunit = ["rad", "deg"]
        obj.aunit = ["rad", "deg"].index(aunit[0:3])
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
        # Based on code by Dam Lamb
        currPlacement = fp.Placement
        mul = GDMLShared.getMult(fp)
        rmax = mul * fp.rmax
        if rmax <= 0.0:
            return
        rmin = mul * fp.rmin
        spos = FreeCAD.Vector(0, 0, 0)
        sdir = FreeCAD.Vector(0, 0, 1)
        HalfPi = math.pi / 2.0
        deltaphi_deg = getAngleDeg(fp.aunit, fp.deltaphi)
        if deltaphi_deg < 360.0 and deltaphi_deg > 0:
            sphere2 = Part.makeSphere(
                rmax, spos, sdir, -90.0, 90.0, deltaphi_deg
            )
            if fp.startphi != 0:
                sphere2.rotate(spos, sdir, getAngleDeg(fp.aunit, fp.startphi))
        else:
            sphere2 = Part.makeSphere(rmax)

        # if starttheta > 0 cut the upper cone
        startthetaRad = getAngleRad(fp.aunit, fp.starttheta)
        startthetaDeg = getAngleDeg(fp.aunit, fp.starttheta)

        if startthetaDeg > 0.0:
            if startthetaDeg == 90.0:
                cylToCut = Part.makeCylinder(
                    2.0 * rmax, rmax, FreeCAD.Vector(0, 0, 0)
                )
                sphere2 = sphere2.cut(cylToCut)
            elif startthetaDeg < 90.0:
                sphere2 = sphere2.cut(
                    Part.makeCone(
                        0.0,
                        rmax * math.sin(startthetaRad),
                        rmax * math.cos(startthetaRad),
                    )
                )

                cylToCut = Part.makeCylinder(
                    2.0 * rmax,
                    rmax,
                    FreeCAD.Vector(0, 0, rmax * math.cos(startthetaRad)),
                )
                sphere2 = sphere2.cut(cylToCut)

            elif startthetaDeg < 180.0:
                sphere2 = sphere2.common(
                    Part.makeCone(
                        0.0,
                        rmax / math.cos(math.pi - startthetaRad),
                        rmax,
                        spos,
                        FreeCAD.Vector(0, 0, -1.0),
                    )
                )

        # if deltatheta -> cut the down cone
        deltathetaRad = getAngleRad(fp.aunit, fp.deltatheta)
        thetaSumRad = startthetaRad + deltathetaRad
        if thetaSumRad < math.pi:
            if thetaSumRad > HalfPi:

                sphere2 = sphere2.cut(
                    Part.makeCone(
                        0.0,
                        rmax * math.sin(math.pi - thetaSumRad),
                        rmax * math.cos(math.pi - thetaSumRad),
                        spos,
                        FreeCAD.Vector(0, 0, -1.0),
                    )
                )

                cylToCut = Part.makeCylinder(
                    2.0 * rmax,
                    rmax,
                    FreeCAD.Vector(
                        0, 0, rmax * (-1.0 + math.cos(thetaSumRad))
                    ),
                )
                sphere2 = sphere2.cut(cylToCut)

            elif thetaSumRad == HalfPi:
                cylToCut = Part.makeCylinder(
                    2.0 * rmax, rmax, FreeCAD.Vector(0, 0, -rmax)
                )
                sphere2 = sphere2.cut(cylToCut)
            elif thetaSumRad > 0:
                sphere2 = sphere2.common(
                    Part.makeCone(
                        0.0, 2 * rmax * math.tan(thetaSumRad), 2 * rmax
                    )
                )

        if rmin <= 0 or rmin > rmax:
            fp.Shape = sphere2
        else:
            fp.Shape = sphere2.cut(Part.makeSphere(rmin))
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement


class GDMLTrap(GDMLsolid):
    def __init__(
        self,
        obj,
        z,
        theta,
        phi,
        x1,
        x2,
        x3,
        x4,
        y1,
        y2,
        alpha,
        aunit,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        "General Trapezoid"
        obj.addProperty("App::PropertyFloat", "z", "GDMLTrap", "z").z = z
        obj.addProperty(
            "App::PropertyFloat", "theta", "GDMLTrap", "theta"
        ).theta = theta
        obj.addProperty(
            "App::PropertyFloat", "phi", "GDMLTrap", "phi"
        ).phi = phi
        obj.addProperty(
            "App::PropertyFloat",
            "x1",
            "GDMLTrap",
            "Length x at y= -y1/2 of face at -z/2",
        ).x1 = x1
        obj.addProperty(
            "App::PropertyFloat",
            "x2",
            "GDMLTrap",
            "Length x at y= +y1/2 of face at -z/2",
        ).x2 = x2
        obj.addProperty(
            "App::PropertyFloat",
            "x3",
            "GDMLTrap",
            "Length x at y= -y2/2 of face at +z/2",
        ).x3 = x3
        obj.addProperty(
            "App::PropertyFloat",
            "x4",
            "GDMLTrap",
            "Length x at y= +y2/2 of face at +z/2",
        ).x4 = x4
        obj.addProperty(
            "App::PropertyFloat", "y1", "GDMLTrap", "Length y at face -z/2"
        ).y1 = y1
        obj.addProperty(
            "App::PropertyFloat", "y2", "GDMLTrap", "Length y at face +z/2"
        ).y2 = y2
        obj.addProperty(
            "App::PropertyFloat", "alpha", "GDMLTrap", "alpha"
        ).alpha = alpha
        obj.addProperty(
            "App::PropertyEnumeration", "aunit", "GDMLTrap", "aunit"
        )
        obj.aunit = ["rad", "deg"]
        obj.aunit = ["rad", "deg"].index(aunit[0:3])
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTrap", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLTrap", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        obj.Proxy = self
        self.Type = "GDMLTrap"
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

        if prop in [
            "z",
            "theta",
            "phi",
            "x1",
            "x2",
            "x3",
            "x4",
            "y1",
            "y2",
            "alpha",
            "aunit",
            "lunit",
        ]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        # Define six vetices for the shape
        alpha = getAngleRad(fp.aunit, fp.alpha)
        theta = getAngleRad(fp.aunit, fp.theta)
        phi = getAngleRad(fp.aunit, fp.phi)
        mul = GDMLShared.getMult(fp)
        y1 = mul * fp.y1
        x1 = mul * fp.x1
        x2 = mul * fp.x2
        y2 = mul * fp.y2
        x3 = mul * fp.x3
        x4 = mul * fp.x4
        z = mul * fp.z
        dx1 = y1 * math.tan(alpha)
        dx2 = y2 * math.tan(alpha)

        # Vertexes, counter clock wise order
        v1 = FreeCAD.Vector(-x1 / 2 - dx1 / 2, -y1 / 2, -z / 2)
        v2 = FreeCAD.Vector(x1 / 2 - dx1 / 2, -y1 / 2, -z / 2)
        v3 = FreeCAD.Vector(x2 / 2 + dx1 / 2, y1 / 2, -z / 2)
        v4 = FreeCAD.Vector(-x2 / 2 + dx1 / 2, y1 / 2, -z / 2)
        v5 = FreeCAD.Vector(-x3 / 2 - dx2 / 2, -y2 / 2, z / 2)
        v6 = FreeCAD.Vector(x3 / 2 - dx2 / 2, -y2 / 2, z / 2)
        v7 = FreeCAD.Vector(x4 / 2 + dx2 / 2, y2 / 2, z / 2)
        v8 = FreeCAD.Vector(-x4 / 2 + dx2 / 2, y2 / 2, z / 2)
        #
        # xy faces
        #
        vxy1 = [v1, v4, v3, v2, v1]
        vxy2 = [v5, v6, v7, v8, v5]
        #
        # zx faces
        #
        vzx1 = [v1, v2, v6, v5, v1]
        vzx2 = [v3, v4, v8, v7, v3]
        #
        # yz faces
        #
        vyz1 = [v5, v8, v4, v1, v5]
        vyz2 = [v2, v3, v7, v6, v2]
        #
        # apply theta, phi distortions
        #
        rho = z * math.tan(theta)
        dx = rho * math.cos(phi)
        dy = rho * math.sin(phi)
        for i in range(0, 4):
            vxy1[i][0] -= dx / 2
            vxy1[i][1] -= dy / 2
            vxy2[i][0] += dx / 2
            vxy2[i][1] += dy / 2

        fxy1 = Part.Face(Part.makePolygon(vxy1))
        fxy2 = Part.Face(Part.makePolygon(vxy2))
        fzx1 = Part.Face(Part.makePolygon(vzx1))
        fzx2 = Part.Face(Part.makePolygon(vzx2))
        fyz1 = Part.Face(Part.makePolygon(vyz1))
        fyz2 = Part.Face(Part.makePolygon(vyz2))

        shell = Part.makeShell([fxy1, fxy2, fzx1, fzx2, fyz1, fyz2])
        solid = Part.makeSolid(shell)

        # center is mid point of diagonal
        #
        botCenter = ((v3 + v4) + (v1 + v2)) / 2
        topCenter = ((v7 + v8) + (v5 + v6)) / 2
        center = (topCenter + botCenter) / 2

        fp.Shape = translate(solid, -center)
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement


class GDMLTrd(GDMLsolid):
    def __init__(self, obj, z, x1, x2, y1, y2, lunit, material, colour=None):
        super().__init__(obj)
        "3.4.15 : Trapezoid – x & y varying along z"
        obj.addProperty("App::PropertyFloat", "z", "GDMLTrd", "z").z = z
        obj.addProperty(
            "App::PropertyFloat", "x1", "GDMLTrd", "Length x at face -z/2"
        ).x1 = x1
        obj.addProperty(
            "App::PropertyFloat", "x2", "GDMLTrd", "Length x at face +z/2"
        ).x2 = x2
        obj.addProperty(
            "App::PropertyFloat", "y1", "GDMLTrd", "Length y at face -z/2"
        ).y1 = y1
        obj.addProperty(
            "App::PropertyFloat", "y2", "GDMLTrd", "Length y at face +z/2"
        ).y2 = y2
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTrd", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLTrd", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        obj.Proxy = self
        self.Type = "GDMLTrd"
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

        if prop in ["z", "x1", "x2", "y1", "y2", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        GDMLShared.trace("x2  : " + str(fp.x2))

        mul = GDMLShared.getMult(fp)
        x1 = (fp.x1 * mul) / 2
        x2 = (fp.x2 * mul) / 2
        y1 = (fp.y1 * mul) / 2
        y2 = (fp.y2 * mul) / 2
        z = (fp.z * mul) / 2
        v1 = FreeCAD.Vector(-x1, -y1, -z)
        v2 = FreeCAD.Vector(-x1, +y1, -z)
        v3 = FreeCAD.Vector(x1, +y1, -z)
        v4 = FreeCAD.Vector(x1, -y1, -z)

        v5 = FreeCAD.Vector(-x2, -y2, z)
        v6 = FreeCAD.Vector(-x2, +y2, z)
        v7 = FreeCAD.Vector(x2, +y2, z)
        v8 = FreeCAD.Vector(x2, -y2, z)
        # Make the wires/faces
        f1 = make_face4(v1, v2, v3, v4)
        f2 = make_face4(v1, v2, v6, v5)
        f3 = make_face4(v2, v3, v7, v6)
        f4 = make_face4(v3, v4, v8, v7)
        f5 = make_face4(v1, v4, v8, v5)
        f6 = make_face4(v5, v6, v7, v8)
        shell = Part.makeShell([f1, f2, f3, f4, f5, f6])
        solid = Part.makeSolid(shell)

        # solid = Part.makePolygon([v1,v2,v3,v4,v5,v6,v7,v1])

        fp.Shape = solid
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement


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
        obj.aunit = ["rad", "deg"]
        obj.aunit = ["rad", "deg"].index(aunit[0:3])
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
        obj.aunit = ["rad", "deg"]
        obj.aunit = ["rad", "deg"].index(aunit[0:3])
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
        # print('Plane extruded')
        # print(plane.normalAt(1,1))
        # return so
        # print('Extrude made - Now Cut')
        cut = shape.cut(so)
        # print('Return Cut')
        return cut

    def createGeometry(self, fp):
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
        topDir = FreeCAD.Vector(fp.highX, fp.highY, fp.highZ)

        tube1 = Part.makeCylinder(rmax, z, pntC, dirC, angle)
        tube2 = Part.makeCylinder(rmin, z, pntC, dirC, angle)
        tube = tube1.cut(tube2)
        topPlane = Part.makePlane(
            depth, depth, FreeCAD.Vector(-rmax, -rmax, z), topDir
        )
        cutTube1 = self.cutShapeWithPlane(tube, topPlane, depth)
        botPlane = Part.makePlane(
            depth, depth, FreeCAD.Vector(rmax, rmax, 0.0), botDir
        )
        cutTube2 = self.cutShapeWithPlane(cutTube1, botPlane, depth)
        base = FreeCAD.Vector(0, 0, -z / 2)
        fp.Shape = translate(cutTube2, base)
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
        cutTube1 = self.cutShapeWithPlane(tube, topPlane)
        botPlane = Part.makePlane(
            100, 100, FreeCAD.Vector(20, 20, 0), FreeCAD.Vector(0, -0.7, -0.71)
        )
        Part.show(botPlane)
        cutTube2 = self.cutShapeWithPlane(cutTube1, botPlane)
        print("Return result")
        fp.Shape = cutTube2


class GDMLVertex(GDMLcommon):
    def __init__(self, obj, x, y, z, lunit):
        super().__init__(obj)
        obj.addProperty("App::PropertyFloat", "x", "GDMLVertex", "x").x = x
        obj.addProperty("App::PropertyFloat", "y", "GDMLVertex", "y").y = y
        obj.addProperty("App::PropertyFloat", "z", "GDMLVertex", "z").z = z
        self.Type = "GDMLVertex"
        self.Object = obj
        obj.Proxy = self

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # if not ('Restore' in fp.State) :
        #   if prop in ['x','y', 'z'] :
        #      self.execute(fp)
        # GDMLShared.trace("Change property: " + str(prop) + "\n")
        pass

    def execute(self, fp):
        pass


class GDMLTriangular(GDMLcommon):
    def __init__(self, obj, v1, v2, v3, vtype):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyVector", "v1", "Triangular", "v1"
        ).v1 = v1
        obj.addProperty(
            "App::PropertyVector", "v2", "Triangular", "v1"
        ).v2 = v2
        obj.addProperty(
            "App::PropertyVector", "v3", "Triangular", "v1"
        ).v3 = v3
        obj.addProperty(
            "App::PropertyEnumeration", "vtype", "Triangular", "vtype"
        )
        obj.vtype = ["ABSOLUTE", "RELATIVE"]
        obj.vtype = ["ABSOLUTE", "RELATIVE"].index(vtype)
        self.Type = "GDMLTriangular"
        obj.Proxy = self

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        pass

    def execute(self, fp):
        pass


class GDMLQuadrangular(GDMLcommon):
    def __init__(self, obj, v1, v2, v3, v4, vtype):
        super().__init__(obj)
        obj.addProperty("App::PropertyVector", "v1", "Quadrang", "v1").v1 = v1
        obj.addProperty("App::PropertyVector", "v2", "Quadrang", "v2").v2 = v2
        obj.addProperty("App::PropertyVector", "v3", "Quadrang", "v3").v3 = v3
        obj.addProperty("App::PropertyVector", "v4", "Quadrang", "v4").v4 = v4
        obj.addProperty(
            "App::PropertyEnumeration", "vtype", "Quadrang", "vtype"
        )
        obj.vtype = ["ABSOLUTE", "RELATIVE"]
        obj.vtype = 0
        self.Type = "GDMLQuadrangular"
        obj.Proxy = self

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        if "Restore" in fp.State:
            return

        pass

    def execute(self, fp):
        pass


class GDMLGmshTessellated(GDMLsolid):
    def __init__(
        self,
        obj,
        sourceObj,
        meshLen,
        vertex,
        facets,
        lunit,
        material,
        colour=None,
    ):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyInteger", "facets", "GDMLGmshTessellated", "Facets"
        ).facets = len(facets)
        obj.setEditorMode("facets", 1)
        obj.addProperty(
            "App::PropertyInteger", "vertex", "GDMLGmshTessellated", "Vertex"
        ).vertex = len(vertex)
        obj.setEditorMode("vertex", 1)
        # Properties NOT the same GmshTessellate GmshMinTessellate
        #obj.addProperty(
        #    "App::PropertyFloat",
        #    "m_maxLength",
        #    "GDMLGmshTessellated",
        #    "Max Length",
        #).m_maxLength = meshLen
        #obj.addProperty(
        #    "App::PropertyFloat",
        #    "m_curveLen",
        #    "GDMLGmshTessellated",
        #    "Curve Length",
        #).m_curveLen = meshLen
        #obj.addProperty(
        #    "App::PropertyFloat",
        #    "m_pointLen",
        #    "GDMLGmshTessellated",
        #    "Point Length",
        #).m_pointLen = meshLen
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLGmshTessellated", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLTessellated",
            "Material",
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        self.Type = "GDMLGmshTessellated"
        self.SourceObj = sourceObj
        self.Vertex = vertex
        self.Facets = facets
        self.Object = obj
        self.colour = colour
        obj.Proxy = self

    def updateParams(self, vertex, facets, flag):
        self.Vertex = vertex
        self.Facets = facets
        self.facets = len(facets)
        self.vertex = len(vertex)
        print(f"Vertex : {self.vertex} Facets : {self.facets}")

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        if "Restore" in fp.State:
            return

        if prop in ["material"]:
            if FreeCAD.GuiUp:
                if hasattr(self, "colour"):
                    if self.colour is None:
                        fp.ViewObject.ShapeColor = colourMaterial(fp.material)

        if prop in ["editable"]:
            if fp.editable is True:
                self.addProperties()

        if prop in ["m_Remesh"]:
            if fp.m_Remesh is True:
                self.reMesh(fp)
                self.execute(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    def execute(self, fp):  # Here for remesh?
        self.createGeometry(fp)

    def addProperties(self):
        print("Add Properties")

    def reMesh(self, fp):
        from .GmshUtils import initialize, meshObj, getVertex, getFacets

        initialize()
        meshObj(fp.Proxy.SourceObj, 2, True, fp.Proxy.Object)
        facets = getFacets()
        vertex = getVertex()
        fp.Proxy.Vertex = vertex
        self.Object.vertex = len(vertex)
        fp.Proxy.Facets = facets
        self.Object.facets = len(facets)
        FreeCADGui.updateGui()

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        mul = GDMLShared.getMult(fp)
        FCfaces = []
        for f in self.Facets:
            if len(f) == 3:
                face = GDMLShared.triangle(
                    mul * self.Vertex[f[0]],
                    mul * self.Vertex[f[1]],
                    mul * self.Vertex[f[2]]
                )
                if face is not None:
                    FCfaces.append(face)
            else:  # len should then be 4
                quadFace = GDMLShared.quad(
                    mul * self.Vertex[f[0]],
                    mul * self.Vertex[f[1]],
                    mul * self.Vertex[f[2]],
                    mul * self.Vertex[f[3]]
                )
                if quadFace is not None:
                    FCfaces.append(quadFace)
                else:
                    print(f"Create Quad Failed {f[0]} {f[1]} {f[2]} {f[3]}")
                    print("Creating as two triangles")
                    face = GDMLShared.triangle(
                        mul * self.Vertex[f[0]],
                        mul * self.Vertex[f[1]],
                        mul * self.Vertex[f[2]]
                    )
                    if face is not None:
                        FCfaces.append(face)
                    face = GDMLShared.triangle(
                        mul * self.Vertex[f[0]],
                        mul * self.Vertex[f[2]],
                        mul * self.Vertex[f[3]]
                    )
                    if face is not None:
                        FCfaces.append(face)

        shell = Part.makeShell(FCfaces)
        if shell.isValid is False:
            FreeCAD.Console.PrintWarning("Not a valid Shell/n")

        try:
            solid = Part.Solid(shell)
        except:
            # make compound rather than just barf
            # visually able to view at least
            FreeCAD.Console.PrintWarning("Problem making Solid/n")
            solid = Part.makeCompound(FCfaces)
        # if solid.Volume < 0:
        #   solid.reverse()
        # print(dir(solid))
        # bbox = solid.BoundBox
        # base = FreeCAD.Vector(-(bbox.XMin+bbox.XMax)/2, \
        #                      -(bbox.YMin+bbox.YMax)/2 \
        #                      -(bbox.ZMin+bbox.ZMax)/2)
        # print(base)

        # base = FreeCAD.Vector(0,0,0)
        # fp.Shape = translate(solid,base)
        fp.Shape = solid
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement


class GDMLTessellated(GDMLsolid):
    def __init__(
        self, obj, vertex, facets, flag, lunit, material, colour=None
    ):
        super().__init__(obj)
        # ########################################
        # if flag == True  - facets is Mesh.Facets - with Normals
        # if flag == False - facets is Faces i.e. from import GDMLTessellated
        # ########################################
        obj.addProperty(
            "App::PropertyInteger", "facets", "GDMLTessellated", "Facets"
        ).facets = len(facets)
        obj.setEditorMode("facets", 1)
        obj.addProperty(
            "App::PropertyInteger", "vertex", "GDMLTessellated", "Vertex"
        ).vertex = len(vertex)
        obj.setEditorMode("vertex", 1)
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTessellated", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLTessellated",
            "Material",
        )
        setMaterial(obj, material)
        self.updateParams(vertex, facets, flag)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
            self.Type = "GDMLTessellated"
            self.colour = colour
            obj.Proxy = self

    def updateParams(self, vertex, facets, flag):
        # print('Update Params & Shape')
        self.pshape = self.createShape(vertex, facets, flag)
        # print(f"Pshape vertex {len(self.pshape.Vertexes)}")
        self.facets = len(facets)
        self.vertex = len(vertex)
        # print(f"Vertex : {self.vertex} Facets : {self.facets}")

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

        if prop in ["editable"]:
            if fp.editable is True:
                self.addProperties()

        if prop in ["scale"]:
            self.createGeometry(fp)

    def addProperties(self):
        print("Add Properties")

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        if hasattr(self, "pshape"):
            # print('Update Shape')
            fp.Shape = self.pshape
            if hasattr(fp, "pshape"):
                fp.pshape = self.pshape
            fp.vertex = self.vertex
            fp.facets = self.facets
        if hasattr(fp, "scale"):
            super().scale(fp)

    def createShape(self, vertex, facets, flag):
        # Viewing outside of face vertex must be counter clockwise
        # if flag == True  - facets is Mesh.Facets
        # if flag == False - factes is Faces i.e. from import GDMLTessellated
        # mul = GDMLShared.getMult(fp)
        mul = GDMLShared.getMult(self)
        # print('Create Shape')
        FCfaces = []
        for f in facets:
            # print('Facet')
            # print(f)
            if flag is True:
                FCfaces.append(GDMLShared.facet(f))
            else:
                if len(f) == 3:
                    FCfaces.append(
                        GDMLShared.triangle(
                            mul * vertex[f[0]],
                            mul * vertex[f[1]],
                            mul * vertex[f[2]]
                        )
                    )
                else:  # len should then be 4
                    try:
                        face = GDMLShared.quad(
                            mul * vertex[f[0]],
                            mul * vertex[f[1]],
                            mul * vertex[f[2]],
                            mul * vertex[f[3]]
                        )
                        FCfaces.append(face)
                    except:
                        face = GDMLShared.triangle(
                            mul * vertex[f[0]],
                            mul * vertex[f[1]],
                            mul * vertex[f[2]]
                        )
                        FCfaces.append(face)
                        face = GDMLShared.triangle(
                            mul * vertex[f[0]],
                            mul * vertex[f[2]],
                            mul * vertex[f[3]]
                        )
                        FCfaces.append(face)
        shell = Part.makeShell(FCfaces)
        if shell.isValid is False:
            FreeCAD.Console.PrintWarning("Not a valid Shell/n")

        # shell.check()
        # solid=Part.Solid(shell).removeSplitter()
        try:
            solid = Part.Solid(shell)
        except:
            # make compound rather than just barf
            # visually able to view at least
            FreeCAD.Console.PrintWarning("Problem making Solid/n")
            solid = Part.makeCompound(FCfaces)

        return solid


class GDMLSampledTessellated(GDMLsolid):
    def __init__(
        self,
        obj,
        vertex,
        facets,
        lunit,
        material,
        solidFlag,
        sampledFraction,
        colour=None,
        flag=True,
    ):
        super().__init__(obj)
        from random import random

        # ########################################
        # if flag == True  - facets is Mesh.Facets - with Normals
        # if flag == False - facets is Faces i.e. from import GDMLTessellated
        # ########################################
        obj.addProperty(
            "App::PropertyInteger",
            "facets",
            "GDMLSampledTessellated",
            "Facets",
        ).facets = len(facets)
        obj.setEditorMode("facets", 1)
        obj.addProperty(
            "App::PropertyInteger",
            "vertex",
            "GDMLSampledTessellated",
            "Vertex",
        ).vertex = len(vertex)
        obj.setEditorMode("vertex", 1)
        obj.addProperty(
            "App::PropertyEnumeration",
            "lunit",
            "GDMLSampledTessellated",
            "lunit",
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLSampledTessellated",
            "Material",
        )

        if flag is True:
            nList = [len(f.Points) for f in facets]
        else:
            nList = [len(f) for f in facets]

        obj.addProperty(
            "App::PropertyIntegerList",
            "vertsPerFacet",
            "GDMLSampledTessellated",
            "Number of vertexes in each facet",
        ).vertsPerFacet = nList
        obj.setEditorMode("vertsPerFacet", 2)

        obj.addProperty(
            "App::PropertyBool",
            "solidFlag",
            "GDMLSampledTessellated",
            "Facets",
        ).solidFlag = solidFlag

        percentageList = [str(i) for i in range(0, 105, 5)]
        obj.addProperty(
            "App::PropertyEnumeration",
            "sampledFraction",
            "GDMLSampledTessellated",
            "Sampled percentage",
        ).sampledFraction = percentageList
        obj.sampledFraction = str(sampledFraction)

        # we use a set first to get rid of duplicate points
        vertsSet = set()
        for f in facets:
            if flag is True:
                for p in f.Points:
                    vertsSet.add(p)
            else:
                vertsSet.add(vertex[f[0]])
                vertsSet.add(vertex[f[1]])
                vertsSet.add(vertex[f[2]])
                if len(f) == 4:
                    vertsSet.add(vertex[f[3]])

        vertsList = list(vertsSet)
        obj.addProperty(
            "App::PropertyVectorList",
            "vertsList",
            "GDMLSampledTessellated",
            "Vertex list",
        ).vertsList = vertsList
        obj.setEditorMode("vertsList", 2)

        # create list of indexes for each face
        Dict = {}
        for i, v in enumerate(vertsList):
            Dict[v] = i

        # now create a list of vert number references for each face
        # there is probably a way to have lists of lists as a property;
        # I just don't know about it, so we list the indexs in order
        # and rely on the nList to get the number of points
        indexList = []
        for f in facets:
            if flag is True:
                for v in f.Points:
                    indexList.append(Dict[v])
            else:
                indexList.append(Dict[vertex[f[0]]])
                indexList.append(Dict[vertex[f[1]]])
                indexList.append(Dict[vertex[f[2]]])
                if len(f) == 4:
                    indexList.append(Dict[vertex[f[3]]])

        obj.addProperty(
            "App::PropertyIntegerList",
            "indexList",
            "GDMLSampledTessellated",
            "Index List",
        ).indexList = indexList
        obj.setEditorMode("indexList", 2)

        setMaterial(obj, material)
        self.updateParams(vertex, facets, solidFlag, sampledFraction, flag)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
            if sampledFraction == 0 and solidFlag is False:
                ViewProvider(obj.ViewObject)
                modes = obj.ViewObject.Proxy.getDisplayModes(obj)
                if "Points" in modes:
                    obj.ViewObject.DisplayMode = "Points"
                obj.ViewObject.PointColor = (random(), random(), random(), 0.0)
        self.Type = "GDMLSampledTessellated"
        self.colour = colour
        obj.Proxy = self
        obj.Proxy.Type = "GDMLSampledTessellated"

    def updateParams(self, vertex, facets, solidFlag, sampledFraction, flag):
        # print('Update Params & Shape')
        self.pshape = self.createShape(
            vertex, facets, solidFlag, sampledFraction, flag
        )
        # print(f"Pshape vertex {len(self.pshape.Vertexes)}")
        self.facets = len(facets)
        self.vertex = len(vertex)
        # print(f"Vertex : {self.vertex} Facets : {self.facets}")

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

        if prop in ["editable"]:
            if fp.editable is True:
                self.addProperties()

        if prop in ["scale"]:
            self.createGeometry(fp)

    def addProperties(self):
        print("Add Properties")

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        if hasattr(self, "pshape"):
            # print('Update Shape')
            fp.Shape = self.pshape
            if hasattr(fp, "pshape"):
                fp.pshape = self.pshape
            fp.vertex = self.vertex
            fp.facets = self.facets
        if hasattr(fp, "scale"):
            super().scale(fp)

    def createShape(self, vertex, facets, solidFlag, sampledFraction, flag):
        # Viewing outside of face vertex must be counter clockwise
        # if flag == True  - facets is Mesh.Facets
        # if flag == False - factes is Faces i.e. from import GDMLTessellated
        # mul = GDMLShared.getMult(fp)
        mul = GDMLShared.getMult(self)
        if sampledFraction == 0 and solidFlag is False:
            shape = self.cloud(vertex, facets, flag)
            return shape
        # print('Create Shape')
        if solidFlag is False:
            NMax = sampledFraction * len(facets) / 100
            nskip = int(len(facets) / NMax)
            if nskip < 1:
                nskip = 1
        else:
            nskip = 1

        FCfaces = []
        for i in range(0, len(facets), nskip):
            f = facets[i]
            # print('Facet')
            # print(f)
            if flag is True:
                FCfaces.append(GDMLShared.facet(f))
            else:
                if len(f) == 3:
                    FCfaces.append(
                        GDMLShared.triangle(
                            mul * vertex[f[0]],
                            mul * vertex[f[1]],
                            mul * vertex[f[2]]
                        )
                    )
                else:  # len should then be 4
                    FCfaces.append(
                        GDMLShared.quad(
                            mul * vertex[f[0]],
                            mul * vertex[f[1]],
                            mul * vertex[f[2]],
                            mul * vertex[f[3]]
                        )
                    )
        if solidFlag is False:
            solid = Part.makeCompound(FCfaces)
        else:
            shell = Part.makeShell(FCfaces)
            if shell.isValid is False:
                FreeCAD.Console.PrintWarning("Not a valid Shell/n")

            # shell.check()
            # solid=Part.Solid(shell).removeSplitter()
            try:
                solid = Part.Solid(shell)
            except:
                # make compound rather than just barf
                # visually able to view at least
                FreeCAD.Console.PrintWarning("Problem making Solid/n")
                solid = Part.makeCompound(FCfaces)

        return solid

    def toMesh(self, obj):
        import Mesh

        mesh = Mesh.Mesh()
        # Viewing outside of face vertex must be counter clockwise
        # if flag == True  - facets is Mesh.Facets
        # if flag == False - factes is Faces i.e. from import GDMLTessellated
        # mul = GDMLShared.getMult(fp)
        mul = GDMLShared.getMult(self)
        print(f"mul {mul}")
        verts = obj.vertsList
        indexList = obj.indexList
        i = 0
        for nVerts in obj.vertsPerFacet:
            # print(f'Normal at : {n} dot {dot} {clockWise}')
            i0 = indexList[i]
            i1 = indexList[i + 1]
            i2 = indexList[i + 2]
            if nVerts == 3:
                mesh.addFacet(
                    mul * verts[i0], mul * verts[i1], mul * verts[i2]
                )
            elif nVerts == 4:
                i3 = indexList[i + 3]
                mesh.addFacet(
                    mul * verts[i0],
                    mul * verts[i1],
                    mul * verts[i2],
                    mul * verts[i3],
                )
            i += nVerts

        return mesh

    def cloud(self, vertex, facets, flag):
        print("Cloud called")
        import random

        mul = GDMLShared.getMult(self)
        pts = []
        if flag is True:
            frac = 0.01
            Npts = int(frac * (len(facets)))
            while Npts < 1000 and frac < 1:
                frac += 0.01
                Npts = int(frac * (len(facets)))
            jmax = len(facets)
            for i in range(Npts):
                j = random.randrange(jmax)
                f = facets[j]
                v = Part.Vertex(f.Points[0])
                pts.append(v)
        else:
            frac = 0.01
            Npts = int(frac * len(vertex))
            while Npts < 1000 and frac < 1:
                frac += 0.01
                Npts = int(frac * (len(vertex)))
            jmax = len(vertex)
            for i in range(Npts):
                j = random.randrange(jmax)
                v = vertex[j]
                pts.append(Part.Vertex(mul * v[0], mul * v[1], mul * v[2]))

        ret = Part.makeCompound(pts)
        return ret

    def onChanged0(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        if "Restore" in fp.State:
            return

        if prop in ["material"]:
            if FreeCAD.GuiUp:
                if hasattr(self, "colour"):
                    if self.colour is None:
                        fp.ViewObject.ShapeColor = colourMaterial(fp.material)

        if prop in ["scale", "solidFlag", "sampledFraction"]:
            self.createGeometry(fp)

    def createGeometry0(self, fp):
        import time

        currPlacement = fp.Placement
        mul = GDMLShared.getMult(fp)
        if int(fp.sampledFraction) == 0:
            return
        # print('Create Shape')

        # The vertex index list, is not uniform, because some facets
        # could have four vertexes, instead of three:
        # indexList =     [i00, i01, i02,  i10, i11, i12, i13, i20, i21, i22, ....]
        # vertsPerFacet = [2,              3,                , 2, ...]
        # if one traverses the facets in order, as we do on export, there is no
        # problem finding the starting index for each facet. Bit if skip facets,
        # as we do below, then we must build a list of the starting indexes of
        # each facet
        """
        i0List = []
        i = 0
        for j, nVerts in enumerate(fp.vertsPerFacet):
            i0List.append(i)
            i += nVerts
        """

        FCfaces = []
        if fp.solidFlag is False:
            NMax = int(fp.sampledFraction) * fp.facets / 100
            nskip = int(fp.facets / NMax)
            if nskip < 1:
                nskip = 1
        else:
            nskip = 1

        print(f"nskip {nskip}")
        indexList = fp.indexList
        start = time.perf_counter()
        i = 0
        for j, nVerts in enumerate(fp.vertsPerFacet):
            if nVerts == 3:
                i0 = indexList[i]
                i1 = indexList[i + 1]
                i2 = indexList[i + 2]
                if j % nskip == 0:
                    FCfaces.append(
                        GDMLShared.triangle(
                            mul * fp.vertsList[i0],
                            mul * fp.vertsList[i1],
                            mul * fp.vertsList[i2]
                        )
                    )
            else:  # len should then be 4
                i0 = indexList[i]
                i1 = indexList[i + 1]
                i2 = indexList[i + 2]
                i3 = indexList[i + 3]
                if j % nskip == 0:
                    FCfaces.append(
                        GDMLShared.quad(
                            mul * fp.vertsList[i0],
                            mul * fp.vertsList[i1],
                            mul * fp.vertsList[i2],
                            mul * fp.vertsList[i3],
                        )
                    )
            i += nVerts
        end = time.perf_counter()
        print(f"time to generate faces {(end-start)}")

        start = time.perf_counter()
        if fp.solidFlag is False:
            solid = Part.makeCompound(FCfaces)
        else:
            shell = Part.makeShell(FCfaces)
            if shell.isValid is False:
                FreeCAD.Console.PrintWarning("Not a valid Shell/n")

            # shell.check()
            # solid=Part.Solid(shell).removeSplitter()
            try:
                solid = Part.Solid(shell)
            except:
                # make compound rather than just barf
                # visually able to view at least
                FreeCAD.Console.PrintWarning("Problem making Solid/n")
                solid = Part.makeCompound(FCfaces)
        end = time.perf_counter()
        print(f"time to make solid {(end-start)}")

        fp.Shape = solid
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement


class GDMLTetra(GDMLsolid):  # 4 point Tetrahedron
    def __init__(self, obj, v1, v2, v3, v4, lunit, material, colour=None):
        super().__init__(obj)
        obj.addProperty("App::PropertyVector", "v1", "GDMLTra", "v1").v1 = v1
        obj.addProperty("App::PropertyVector", "v2", "GDMLTra", "v2").v2 = v2
        obj.addProperty("App::PropertyVector", "v3", "GDMLTra", "v3").v3 = v3
        obj.addProperty("App::PropertyVector", "v4", "GDMLTra", "v4").v4 = v4
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTra", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration", "material", "GDMLTra", "Material"
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        self.Type = "GDMLTetra"
        self.colour = colour
        obj.Proxy = self

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

        if prop in ["v1", "v2", "v3", "v4", "lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        mul = GDMLShared.getMult(fp)
        pt1 = mul * fp.v1
        pt2 = mul * fp.v2
        pt3 = mul * fp.v3
        pt4 = mul * fp.v4
        face1 = Part.Face(Part.makePolygon([pt1, pt2, pt3, pt1]))
        face2 = Part.Face(Part.makePolygon([pt1, pt2, pt4, pt1]))
        face3 = Part.Face(Part.makePolygon([pt4, pt2, pt3, pt4]))
        face4 = Part.Face(Part.makePolygon([pt1, pt3, pt4, pt1]))
        fp.Shape = Part.makeSolid(Part.makeShell([face1, face2, face3, face4]))
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement


class GDMLTetrahedron(GDMLsolid):

    """Does not exist as a GDML solid, but export as an Assembly of G4Tet"""

    """ See paper Poole at al - Fast Tessellated solid navigation in GEANT4 """

    def __init__(self, obj, tetra, lunit, material, colour=None):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyInteger", "tetra", "GDMLTetrahedron", "Tetra"
        ).tetra = len(tetra)
        obj.setEditorMode("tetra", 1)
        obj.addProperty(
            "App::PropertyEnumeration", "lunit", "GDMLTetrahedron", "lunit"
        )
        setLengthQuantity(obj, lunit)
        obj.addProperty(
            "App::PropertyEnumeration",
            "material",
            "GDMLTetrahedron",
            "Material",
        )
        setMaterial(obj, material)
        if FreeCAD.GuiUp:
            updateColour(obj, colour, material)
        # Suppress Placement - position & Rotation via parent App::Part
        # this makes Placement via Phyvol easier and allows copies etc
        # obj.addExtension('App::GroupExtensionPython')
        self.Tetra = tetra
        self.Object = obj
        self.Type = "GDMLTetrahedron"
        self.colour = colour
        obj.Proxy = self

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

        if prop in ["lunit"]:
            self.createGeometry(fp)

        if prop in ["scale"]:
            self.createGeometry(fp)

    # def execute(self, fp): in GDMLsolid

    def makeTetra(self, pt1, pt2, pt3, pt4):
        face1 = Part.Face(Part.makePolygon([pt1, pt2, pt3, pt1]))
        face2 = Part.Face(Part.makePolygon([pt1, pt2, pt4, pt1]))
        face3 = Part.Face(Part.makePolygon([pt4, pt2, pt3, pt4]))
        face4 = Part.Face(Part.makePolygon([pt1, pt3, pt4, pt1]))
        return Part.makeShell([face1, face2, face3, face4])

    def createGeometry(self, fp):
        currPlacement = fp.Placement
        print("Tetrahedron")
        mul = GDMLShared.getMult(fp)
        print(len(self.Tetra))
        tetraShells = []
        for t in self.Tetra:
            pt1 = mul * t[0]
            pt2 = mul * t[1]
            pt3 = mul * t[2]
            pt4 = mul * t[3]
            tetraShells.append(self.makeTetra(pt1, pt2, pt3, pt4))
        fp.Shape = Part.makeCompound(tetraShells)
        if hasattr(fp, "scale"):
            super().scale(fp)
        fp.Placement = currPlacement


class GDMLFiles(GDMLcommon):
    def __init__(self, obj, FilesEntity, sectionDict):
        super().__init__(obj)
        """Add some custom properties to our Cone feature"""
        GDMLShared.trace("GDML Files")
        GDMLShared.trace(FilesEntity)
        obj.addProperty(
            "App::PropertyBool", "active", "GDMLFiles", "split option"
        ).active = FilesEntity
        obj.addProperty(
            "App::PropertyString", "define", "GDMLFiles", "define section"
        ).define = sectionDict.get("define", "")
        obj.addProperty(
            "App::PropertyString",
            "materials",
            "GDMLFiles",
            "materials section",
        ).materials = sectionDict.get("materials", "")
        obj.addProperty(
            "App::PropertyString", "solids", "GDMLFiles", "solids section"
        ).solids = sectionDict.get("solids", "")
        obj.addProperty(
            "App::PropertyString",
            "structure",
            "GDMLFiles",
            "structure section",
        ).structure = sectionDict.get("structure", "")
        self.Type = "GDMLFiles"
        obj.Proxy = self

    def execute(self, fp):
        """Do something when doing a recomputation, this method is mandatory"""
        pass

    def onChanged(self, fp, prop):
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # if not ('Restore' in fp.State) :
        #   if not hasattr(fp,'onchange') or not fp.onchange : return
        pass


class GDMLvolume:
    def __init__(self, obj):
        obj.Proxy = self
        self.Object = obj


class GDMLconstant(GDMLcommon):
    def __init__(self, obj, name, value):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyString", "name", "GDMLconstant", "name"
        ).name = name
        obj.addProperty(
            "App::PropertyString", "value", "GDMLconstant", "value"
        ).value = value
        obj.Proxy = self
        self.Object = obj


class GDMLvariable(GDMLcommon):
    def __init__(self, obj, name, value):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyString", "name", "GDMLvariable", "name"
        ).name = name
        obj.addProperty(
            "App::PropertyString", "value", "GDMLvariable", "value"
        ).value = value
        obj.Proxy = self
        self.Object = obj


class GDMLquantity(GDMLcommon):
    def __init__(self, obj, name, type, unit, value):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyString", "name", "GDMLvariable", "name"
        ).name = name
        obj.addProperty(
            "App::PropertyString", "type", "GDMLvariable", "type"
        ).type = type
        obj.addProperty(
            "App::PropertyString", "unit", "GDMLvariable", "unit"
        ).unit = unit
        obj.addProperty(
            "App::PropertyString", "value", "GDMLvariable", "value"
        ).value = value
        obj.Proxy = self
        self.Object = obj


class GDMLmaterial(GDMLcommon):
    def __init__(
        self, obj, name, density=1.0, conduct=2.0, expand=3.0, specific=4.0
    ):
        super().__init__(obj)
        # Add most properties later
        obj.addProperty(
            "App::PropertyString", "name", "GDMLmaterial", "name"
        ).name = name
        obj.addProperty(
            "App::PropertyFloat", "density", "GDMLmaterial", "Density kg/m^3"
        ).density = density
        obj.addProperty(
            "App::PropertyFloat",
            "conduct",
            "GDMLmaterial",
            "Thermal Conductivity W/m/K",
        ).conduct = conduct
        obj.addProperty(
            "App::PropertyFloat",
            "expand",
            "GDMLmaterial",
            "Expansion Coefficient m/m/K",
        ).expand = expand
        obj.addProperty(
            "App::PropertyFloat",
            "specific",
            "GDMLmaterial",
            "Specific Heat J/kg/K",
        ).specific = specific

        obj.Proxy = self
        self.Object = obj


class GDMLfraction(GDMLcommon):
    def __init__(self, obj, ref, n):
        super().__init__(obj)
        obj.addProperty("App::PropertyFloat", "n", ref).n = n
        obj.Proxy = self
        self.Object = obj


class GDMLcomposite(GDMLcommon):
    def __init__(self, obj, name, n, ref):
        super().__init__(obj)
        obj.addProperty("App::PropertyInteger", "n", name).n = n
        obj.addProperty("App::PropertyString", "ref", name).ref = ref
        obj.Proxy = self
        self.Object = obj


class GDMLelement(GDMLcommon):
    def __init__(self, obj, name):
        super().__init__(obj)
        obj.addProperty("App::PropertyString", "name", name).name = name
        obj.Proxy = self
        self.Object = obj


class GDMLisotope(GDMLcommon):
    def __init__(self, obj, name, N, Z):
        super().__init__(obj)
        obj.addProperty("App::PropertyString", "name", name).name = name
        obj.addProperty("App::PropertyInteger", "N", name).N = N
        obj.addProperty("App::PropertyInteger", "Z", name).Z = Z
        # Name, N and Z are minimum other values are added by import
        # obj.addProperty("App::PropertyString","unit",name).unit = unit
        # obj.addProperty("App::PropertyFloat","value",name).value = value
        obj.Proxy = self
        self.Object = obj


class GDMLmatrix(GDMLcommon):
    def __init__(self, obj, name, coldim, values):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyInteger", "coldim", "GDMLmatrix", "coldin"
        ).coldim = coldim
        obj.addProperty(
            "App::PropertyString", "values", "GDMLmatrix", "values"
        ).values = values
        obj.Proxy = self
        self.Object = obj


class GDMLopticalsurface(GDMLcommon):
    def __init__(self, obj, name, model, finish, type, value):
        super().__init__(obj)
        print(f"passed finish {finish} type {type}")
        obj.addProperty(
            "App::PropertyEnumeration", "model", "GDMLoptical", "model"
        )
        obj.model = [
            "glisur",  # original GEANT3 model \
            "unified",  # UNIFIED model  \
            "LUT",  # Look-Up-Table model (LBNL model) \
            "DAVIS",  # DAVIS model \
            "dichroic",  # dichroic filter \
        ]
        obj.addProperty(
            "App::PropertyEnumeration", "finish", "GDMLoptical" "finish"
        )
        obj.finish = [
            "polished | polished",  # smooth perfectly polished surface
            "polished | frontpainted",  # smooth top-layer (front) paint
            "polished | backpainted",  # same is 'polished' but with a back-paint
            # meltmount
            "polished | air",  # mechanically polished surface
            "polished | teflonair",  # mechanically polished surface, with teflon
            "polished | tioair",  # mechanically polished surface, with tio paint
            "polished | tyvekair",  #  mechanically polished surface, with tyvek
            "polished | vm2000air",  # mechanically polished surface, with esr film
            "polished | vm2000glue",  # mechanically polished surface, with esr film &
            # // for LBNL LUT model
            "polished | lumirrorair",  # mechanically polished surface, with lumirror
            "polished | lumirrorglue",  # mechanically polished surface, with lumirror &
            # meltmount
            "etched | lumirrorair",  # chemically etched surface, with lumirror
            "etched | lumirrorglue",  # chemically etched surface, with lumirror & meltmount
            "etched | air",  # chemically etched surface
            "etched | teflonair",  # chemically etched surface, with teflon
            "etched | tioair",  # chemically etched surface, with tio paint
            "etched | tyvekair",  # chemically etched surface, with tyvek
            "etched | vm2000air",  # chemically etched surface, with esr film
            "etched | vm2000glue",  # chemically etched surface, with esr film & meltmount
            "ground | ground",  # // rough surface
            "ground | frontpainted",  # rough top-layer (front) paint
            "ground | backpainted",  # same as 'ground' but with a back-paint
            "ground | lumirrorair",  # rough-cut surface, with lumirror
            "ground | lumirrorglue",  # rough-cut surface, with lumirror & meltmount
            "ground | air",  # rough-cut surface
            "ground | teflonair",  # rough-cut surface, with teflon
            "ground | tioair",  # rough-cut surface, with tio paint
            "ground | tyvekair",  # rough-cut surface, with tyvek
            "ground | vm2000air",  # rough-cut surface, with esr film
            "ground | vm2000glue",  # rough-cut surface, with esr film & meltmount
            "Rough_LUT",  # rough surface \
            "RoughTeflon_LUT",  # rough surface wrapped in Teflon tape \
            "RoughESR_LUT",  # rough surface wrapped with ESR \
            "RoughESRGrease_LUT",  # rough surface wrapped with ESR \
            # and coupled with optical grease
            "Polished_LUT",  # polished surface \
            "PolishedTeflon_LUT",  # polished surface wrapped in Teflon tape \
            "PolishedESR_LUT",  # polished surface wrapped with ESR \
            "PolishedESRGrease_LUT",  # polished surface wrapped with ESR \
            # and coupled with optical grease
            "Detector_LUT",  # polished surface with optical grease
            "extended | 0",
            "extended | 1",
            "extended | 2",
            "extended | 3",
            "extended | 4",
            "extended | 5",
            "extended | 6",
            "extended | 7",
            "extended | 8",
            "extended | 9",
        ]
        print(f"finish {finish}")
        if finish in "0123456789":
            obj.finish = "extended | " + finish
        elif finish == "polished":
            obj.finish = "polished | polished"
        elif finish == "ground":
            obj.finish = "ground | ground"
        else:
            print(f"last finish {finish}")
            finish = finish.replace("polished", "polished | ")
            finish = finish.replace("etched", "etched | ")
            finish = finish.replace("ground", "ground | ")
            obj.finish = finish

        obj.addProperty(
            "App::PropertyEnumeration", "type", "GDMLoptical", "type"
        )
        obj.type = [
            "dielectric_dielectric",
            "dielectric_metal",
            "extended | 0",
            "extended | 1",
            "extended | 2",
            "extended | 3",
            "extended | 4",
            "extended | 5",
            "extended | 6",
            "extended | 7",
            "extended | 8",
            "extended | 9",
        ]
        if type in "0123456789":
            obj.type = "extended | " + type
        else:
            obj.type = type
        obj.addProperty(
            "App::PropertyFloat", "value", "GDMLoptical"
        ).value = value
        obj.Proxy = self
        self.Object = obj


class GDMLskinsurface(GDMLcommon):
    def __init__(self, obj, name, prop):
        super().__init__(obj)
        obj.addProperty(
            "App::PropertyString", "surface", "GDMLskin", "surface property"
        ).surface = prop
        obj.Proxy = self
        self.Object = obj


# ??? need for GDMLcommon ???
class GDMLbordersurface(GDMLcommon):
    def __init__(self, obj, name, surface, pv1, pv2, check):
        super().__init__(obj)
        # print(f'pv1 : {pv1} pv2 : {pv2}')
        obj.addProperty(
            "App::PropertyString", "Surface", "GDMLborder", "surface property"
        ).Surface = surface
        obj.addProperty(
            "App::PropertyBool",
            "CheckCommonFaces",
            "GDMLborder",
            "Perform check of common faces on export",
        )
        obj.CheckCommonFaces = check
        obj.addProperty(
            "App::PropertyLinkGlobal", "PV1", "GDMLborder", "physvol PV1"
        ).PV1 = pv1
        obj.setEditorMode("PV1", 1)
        obj.addProperty(
            "App::PropertyLinkGlobal", "PV2", "GDMLborder", "physvol PV2"
        ).PV2 = pv2
        obj.setEditorMode("PV2", 1)
        obj.Proxy = self
        self.Object = obj


class ViewProviderExtension(GDMLcommon):
    def __init__(self, obj):
        super().__init__(obj)
        obj.addExtension("Gui::ViewProviderGroupExtensionPython")
        obj.Proxy = self

    def getDisplayModes(self, obj):
        """Return a list of display modes."""
        modes = []
        modes.append("Shaded")
        modes.append("Wireframe")
        modes.append("Points")
        return modes

    def updateData(self, fp, prop):
        """If a property of the handled feature has changed we have the chance to handle this here"""
        # fp is the handled feature, prop is the name of the property that has changed
        # l = fp.getPropertyByName("Length")
        # w = fp.getPropertyByName("Width")
        # h = fp.getPropertyByName("Height")
        # self.scale.scaleFactor.setValue(float(l),float(w),float(h))
        pass

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode. It must be defined in getDisplayModes."""
        return "Shaded"


# use general ViewProvider if poss
class ViewProvider(GDMLcommon):
    def __init__(self, obj):
        super().__init__(obj)
        """Set this object to the proxy object of the actual view provider"""
        obj.Proxy = self

    def updateData(self, fp, prop):
        """If a property of the handled feature has changed we have the chance to handle this here"""
        # print("updateData")
        # fp is the handled feature, prop is the name of the property that has changed
        # l = fp.getPropertyByName("Length")
        # w = fp.getPropertyByName("Width")
        # h = fp.getPropertyByName("Height")
        # self.scale.scaleFactor.setValue(float(l),float(w),float(h))
        pass

    def getDisplayModes(self, obj):
        """Return a list of display modes."""
        # print("getDisplayModes")
        modes = []
        modes.append("Shaded")
        modes.append("Wireframe")
        modes.append("Points")
        return modes

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode. It must be defined in getDisplayModes."""
        return "Shaded"

    def setDisplayMode(self, mode):
        """Map the display mode defined in attach with those defined in getDisplayModes.\
               Since they have the same names nothing needs to be done. This method is optional"""
        return mode

    def onChanged(self, vp, prop):
        """Here we can do something when a single property got changed"""
        # if hasattr(vp,'Name') :
        #   print("View Provider : "+vp.Name+" State : "+str(vp.State)+" prop : "+prop)
        # else :
        #   print("View Provider : prop : "+prop)
        # GDMLShared.trace("Change property: " + str(prop) + "\n")
        # if prop == "Color":
        #    c = vp.getPropertyByName("Color")
        #    self.color.rgb.setValue(c[0],c[1],c[2])

    def getIcon(self):
        """Return the icon in XPM format which will appear in the tree view. This method is\
               optional and if not defined a default icon is shown."""
        return """
           /* XPM */
           static const char * ViewProviderBox_xpm[] = {
           "16 16 6 1",
           "   c None",
           ".  c #141010",
           "+  c #615BD2",
           "@  c #C39D55",
           "#  c #000000",
           "$  c #57C355",
           "        ........",
           "   ......++..+..",
           "   .@@@@.++..++.",
           "   .@@@@.++..++.",
           "   .@@  .++++++.",
           "  ..@@  .++..++.",
           "###@@@@ .++..++.",
           "##$.@@$#.++++++.",
           "#$#$.$$$........",
           "#$$#######      ",
           "#$$#$$$$$#      ",
           "#$$#$$$$$#      ",
           "#$$#$$$$$#      ",
           " #$#$$$$$#      ",
           "  ##$$$$$#      ",
           "   #######      "};
           """

    def __getstate__(self):
        """When saving the document this object gets stored using Python's json module.\
               Since we have some un-serializable parts here -- the Coin stuff -- we must define this method\
               to return a tuple of all serializable objects or None."""
        return None

    def __setstate__(self, state):
        """When restoring the serialized object from document we have the chance to set some internals here.\
               Since no data were serialized nothing needs to be done here."""
        return None


#
#   Need to add variables to these functions or delete?
#
def makeBox(x, y, z, lunit, material, colour=None):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "GDMLBox")
    if obj is not None:
        GDMLBox(obj, x, y, z, lunit, material, colour=None)
        ViewProvider(obj.ViewObject)
        obj.recompute()
    return obj


def makeCone(rmin1, rmin2, rmax1, rmax2, z, startphi, deltaphi, \
       aunit, lunit, material, colour=None):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "GDMLCone")
    if obj is not None:
        GDMLCone(obj, rmin1, rmin2, rmax1, rmax2, z, startphi, deltaphi, \
            aunit, lunit, material, colour=None)
        ViewProvider(obj.ViewObject)
        obj.recompute()
    return obj


def makeSphere(rmin, rmax, startphi, deltaphi, starttheta, deltatheta, \
        aunit, lunit, material, colour=None):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "GDMLSphere")
    if obj is not None:
        GDMLSphere(obj, rmin, rmax, startphi, deltaphi, starttheta, deltatheta, \
            aunit, lunit, material, colour=None)
        ViewProvider(obj.ViewObject)
        obj.recompute()
    return obj


def makeTube(rmin, rmax, z, startphi, deltaphi, aunit, lunit, material, \
        colour=None):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "GDMLTube")
    if obj is not None:
        GDMLTube(obj, rmin, rmax, z, startphi, deltaphi, aunit, lunit, \
            material, colour=None)
        ViewProvider(obj.ViewObject)
        obj.recompute()
    return obj
   

def makeArb8(v1x, v1y, v2x, v2y, v3x, v3y, v4x, v4y, v5x, v5y, v6x,
        v6y, v7x, v7y, v8x, v8y, dz, lunit, material, colour=None):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "GDMLArb8")
    if obj is not None:
        GDMLArb8(obj, v1x, v1y, v2x, v2y, v3x, v3y, v4x, v4y, v5x, v5y, v6x,
            v6y, v7x, v7y, v8x, v8y, dz, lunit, material, colour=None)
        ViewProvider(obj.ViewObject)
        obj.recompute()
    return obj

