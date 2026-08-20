from __future__ import annotations
# Mon Aug 26 2024
# Sat Mar 28 8:44 AM PDT 2023
# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2019 Keith Sloan <keithsloan52@icloud.com>              *
# *             (c) 2020 Dam Lambert                                       *
# *             (c) 2021 Munther Hindi
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
# *   Acknowledgements : Ideas & code copied from                          *
# *                      https://github.com/ignamv/geanTipi                *
# *                                                                        *
# ***************************************************************************
__title__ = "FreeCAD - GDML exporter Version"
__author__ = "Keith Sloan <keithsloan52@icloud.com>"
__url__ = ["https://github.com/KeithSloan/FreeCAD_Geant4"]

from sys import breakpointhook

import FreeCAD, os, Part, math
import Sketcher
import FreeCAD as App
import FreeCADGui
from PySide import QtGui

from FreeCAD import Vector

import random
import re
from .GDMLObjects import GDMLcommon, GDMLBox, GDMLTube

# modif add
# from .GDMLObjects import getMult, convertionlisteCharToLunit

import sys
from pathlib import Path

try:
    import lxml.etree as ET

    FreeCAD.Console.PrintMessage("running with lxml.etree\n")
    XML_IO_VERSION = "lxml"
except ImportError:
    try:
        import xml.etree.ElementTree as ET

        FreeCAD.Console.PrintMessage("running with xml.etree.ElementTree\n")
        XML_IO_VERSION = "xml"
    except ImportError:
        FreeCAD.Console.PrintMessage("pb xml lib not found\n")
        sys.exit()
# xml handling
# import argparse
# from   xml.etree.ElementTree import XML
#################################

global zOrder

from .GDMLObjects import (
    GDMLQuadrangular,
    GDMLTriangular,
    GDML2dVertex,
    GDMLSection,
    GDMLmaterial,
    GDMLfraction,
    GDMLcomposite,
    GDMLisotope,
    GDMLelement,
    GDMLconstant,
    GDMLvariable,
    GDMLquantity,
    GDMLbordersurface,
)

from . import GDMLShared


def get_active_branch_name():
    gdml_dir = FreeCAD.getUserAppDataDir() + "/Mod/GDML"
    head_dir = Path(gdml_dir) / ".git" / "HEAD"
    try:
        with head_dir.open("r") as f: content = f.read().splitlines()
    except:
        return f"Can't locate .git directory in {gdml_dir}"

    for line in content:
        if line[0:4] == "ref:":
            return line.partition("refs/heads/")[2]


# ***************************************************************************
# Tailor following to your requirements ( Should all be strings )          *
# no doubt there will be a problem when they do implement Value
if open.__module__ in ["__builtin__", "io"]:
    pythonopen = open  # to distinguish python built-in open function from the one declared here

# ## modifs lambda


class NameManager:
    _nameCountDict: dict[str, int] = {}
    _solidsNamesDict = {}
    _volumeNamesDict = {}

    @staticmethod
    def init():
        NameManager._nameCountDict = {}
        NameManager._solidsNamesDict = {}
        NameManager._volumeNamesDict = {}

    @staticmethod
    def getName(obj) -> str:
        if obj in NameManager._solidsNamesDict:
            return NameManager._solidsNamesDict[obj]
        name = obj.Label
        if len(name) > 4:
            if name[0:4] == "GDML":
                if "_" in name:
                    name = name.split("_", 1)[1]

        if name[0].isdigit():
            name = "S" + name

        if name in NameManager._nameCountDict:
            count = 1 + NameManager._nameCountDict[name]
            NameManager._nameCountDict[name] = count
            name = name + str(count)
        else:
            NameManager._nameCountDict[name] = 0

        NameManager._solidsNamesDict[obj] = name

        return name

    @staticmethod
    def nameUsedFor(obj):
        if obj in NameManager._solidsNamesDict:
            return NameManager._solidsNamesDict[obj]
        else:
            return None

    @staticmethod
    def getVolumeName(vol) -> str:
        # breakpoint()
        if vol in NameManager._volumeNamesDict:
            return NameManager._volumeNamesDict[vol]

        if vol.TypeId == "App::Part":
            return vol.Label

        elif vol.TypeId == "App::Link":
            return NameManager.getVolumeName(vol.LinkedObject)
        else:
            name = NameManager.nameUsedFor(vol)
            if name is None:
                name = "LV_"+NameManager.getName(vol)
                NameManager._volumeNamesDict[vol] = name
            return name

    @staticmethod
    def getPhysvolName(vol):
        name = NameManager.getName(vol)
        return "PV_" + name

# ## end modifs lambda

#################################
# Switch functions
################################


class switch(object):
    value = None

    def __new__(class_, value):
        class_.value = value
        return True


def case(*args):
    return any((arg == switch.value for arg in args))


class MultiPlacer:
    def __init__(self, obj):
        self.obj = obj
        self._name = NameManager.getName(obj)

    def place(self, volRef):
        print("Can't place base class MultiPlace")

    def xml(self):
        print("Can't place base class MultiPlace")

    def name(self):
        return self._name

    @staticmethod
    def getPlacer(obj):
        if obj.TypeId == "Part::Mirroring":
            return MirrorPlacer(obj)
        else:
            print(f"{obj.Label} is not a placer")
            return None


class MirrorPlacer(MultiPlacer):
    def __init__(self, obj):
        super().__init__(obj)
        self.assembly = None  # defined AFTER place()

    def xml(self):
        return self.assembly

    def place(self, volRef):
        global structure
        name = self.name()
        assembly = ET.Element("assembly", {"name": name})
        # structure.insert(0, assembly)
        # insert just before worlVol, which should be last
        worldIndex = len(structure) - 1
        structure.insert(worldIndex, assembly)
        pos = self.obj.Source.Placement.Base
        name = volRef + "_mirror"
        # bordersurface might need physvol to have a name
        physvolName = NameManager.getPhysvolName(self.obj)
        pvol = ET.SubElement(
            assembly, "physvol", {"name": physvolName}
        )
        ET.SubElement(pvol, "volumeref", {"ref": volRef})
        normal = self.obj.Normal
        # reflect the position about the reflection plane
        unitVec = normal.normalize()
        posAlongNormal = pos.dot(unitVec) * unitVec
        posParalelToPlane = pos - posAlongNormal
        newPos = posParalelToPlane - posAlongNormal
        # first reflect about x-axis
        # then rotate to bring x-axis to direction of normal
        rotX = False
        if normal.x == 1:
            scl = Vector(-1, 1, 1)
            newPos = Vector(-pos.x, pos.y, pos.z)
        elif normal.y == 1:
            scl = Vector(1, -1, 1)
            newPos = Vector(pos.x, -pos.y, pos.z)
        elif normal.z == 1:
            scl = Vector(1, 1, 1 - 1)
            newPos = Vector(pos.x, pos.y, -pos.z)
        else:
            scl = Vector(-1, 1, 1)
            newPos = Vector(-pos.x, pos.y, pos.z)
            rotX = True

        rot = FreeCAD.Rotation()
        if rotX is True:
            # rotation to bring normal to x-axis (might have to reverse)
            rot = FreeCAD.Rotation(Vector(1, 0, 0), unitVec)
            # The angle of rotation of the image twice the angle of rotation of the mirror
            rot.Angle = 2 * rot.Angle
            newPos = rot * newPos
        sourcePlacement = FreeCAD.Placement(newPos, rot)
        # placement = self.obj.Placement*sourcePlacement
        placement = sourcePlacement
        exportPosition(name, pvol, placement.Base)
        if rotX is True:
            exportRotation(name, pvol, placement.Rotation)
        exportScaling(name, pvol, scl)

        self.assembly = assembly


class PhysVolPlacement:
    def __init__(self, ref, placement):
        self.ref = ref  # name reference: a string
        self.placement = placement  # physvol placement


#########################################################
# Pretty format GDML                                    #
#########################################################


def indent(elem, level=0):
    i = "\n" + level * "  "
    j = "\n" + (level - 1) * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem


#########################################

def cleanGDMLname(name):
    # Clean GDML name for Geant4
    # Replace space and special characters with '_'
    return name.replace('\r','').replace('(','_').replace(')','_').replace(' ','_')


def nameFromLabel(label):
    if " " not in label:
        return label
    else:
        return label.split(" ")[0]


def initGDML():
    NS = "http://www.w3.org/2001/XMLSchema-instance"
    location_attribute = "{%s}noNamespaceSchemaLocation" % NS
    # For some reason on my system around Sep 30, 2024, the following url is unreachable,
    # I think because http:// is no longer accepted, so use https:// instead. DID NOT WORK!,
    # although wget of url works. I don't know what's going on
    gdml = ET.Element(
        "gdml",
         attrib={
              location_attribute: "https://service-spi.web.cern.ch/service-spi/app/releases/GDML/schema/gdml.xsd"
          },
     )

    return gdml


#################################
#  Setup GDML environment
#################################


def GDMLstructure():
    # print("Setup GDML structure")
    #################################
    # globals
    ################################
    global gdml, constants, variables, define, materials, solids, structure, setup
    global WorldVOL
    global defineCnt, LVcount, PVcount, POScount, ROTcount, SCLcount
    global centerDefined
    global identityDefined
    global identityName
    global gxml

    centerDefined = False
    identityDefined = False
    identityName = 'identity'

    defineCnt = LVcount = PVcount = POScount = ROTcount = SCLcount = 1

    gdml = initGDML()
    define = ET.SubElement(gdml, "define")
    materials = ET.SubElement(gdml, "materials")
    solids = ET.SubElement(gdml, "solids")
    solids.clear()
    structure = ET.SubElement(gdml, "structure")
    setup = ET.SubElement(gdml, "setup", {"name": "Default", "version": "1.0"})
    gxml = ET.Element("gxml")
    _ = SurfaceManager()

    return structure


def defineMaterials():
    # Replaced by loading Default
    # print("Define Materials")
    global materials


def exportDefine(name, v):
    global define
    ET.SubElement(
        define,
        "position",
        {
            "name": name,
            "unit": "mm",
            "x": str(v[0]),
            "y": str(v[1]),
            "z": str(v[2]),
        },
    )


"""
def exportDefineVertex(name, v, index):
    global define
    ET.SubElement(define, 'position', {'name': name + str(index),
                                       'unit': 'mm', 'x': str(v.X), 'y': str(v.Y), 'z': str(v.Z)})
"""


def exportDefineVertex(name, v, index):
    global define
    ET.SubElement(
        define,
        "position",
        {
            "name": name + str(index),
            "unit": "mm",
            "x": str(v.x),
            "y": str(v.y),
            "z": str(v.z),
        },
    )


def defineWorldBox(bbox):
    global solids
    for obj in FreeCAD.ActiveDocument.Objects:
        # print("{} + {} = ".format(bbox, obj.Shape.BoundBox))
        if hasattr(obj, "Shape"):
            bbox.add(obj.Shape.BoundBox)
        if hasattr(obj, "Mesh"):
            bbox.add(obj.Mesh.BoundBox)
        if hasattr(obj, "Points"):
            bbox.add(obj.Points.BoundBox)
    #   print(bbox)
    # Solids get added to solids section of gdml ( solids is a global )
    name = "WorldBox"
    ET.SubElement(
        solids,
        "box",
        {
            "name": name,
            "x": str(1000),
            "y": str(1000),
            "z": str(1000),
            # 'x': str(2*max(abs(bbox.XMin), abs(bbox.XMax))), \
            # 'y': str(2*max(abs(bbox.YMin), abs(bbox.YMax))), \
            # 'z': str(2*max(abs(bbox.ZMin), abs(bbox.ZMax))), \
            "lunit": "mm",
        },
    )
    return name


def quaternion2XYZ(rot):
    """
    convert a quaternion rotation to a sequence of rotations around X, Y, Z
    Here is my (Munther Hindi) derivation:
    First, the rotation matrices for rotations around X, Y, Z axes.

    Rx = [      1       0       0]
        [      0  cos(a) -sin(a)]
        [      0  sin(a)  cos(a)]

    Ry= [ cos(b)       0  sin(b)]
       [      0       1       0]
       [-sin(b)       0   cos(b)]

    Rz = [ cos(g) -sin(g)       0]
        [ sin(g)  cos(g)       0]
        [      0       0       1]

    Rederivation from the previous version. Geant processes the rotation from
    the gdml as R = Rx Ry Rz, i.e, Rx applied last, not first, so now we have

    R = Rx Ry Rz =
        [cosb*cosg,	                -cosb*sing,	                     sinb],
        [cosa*sing+cosg*sina*sinb,	cosa*cosg-sina*sinb*sing,	-cosb*sina],
        [sina*sing-cosa*cosg*sinb,	cosa*sinb*sing+cosg*sina,	cosa*cosb]

    To get the angles a(lpha), b(eta) for rotations around x, y axes, transform the unit vector (0,0,1)
    [x,y,z] = Q*(0,0,1) = R*(0,0,1) ==>
    x = sin(b)
    y = -sin(a)cos(b)
    z = cos(a)cos(b)

    ==>   a = atan2(-y, x) = atan2(sin(a)*cos(b), cos(a)*cos(b)) = atan2(sin(a), cos(a))
    then  b = atan2(x*cos(a), z) = atan2(sin(b)*cos(a), cos(b)*cos(a)] = atan2(sin(b), cos(b))

    Once a, b are found, g(amma) can be found by transforming (1, 0, 0), or (0,1,0)
    Since now a, b are known, one can form the inverses of Rx, Ry:
    Rx^-1 = Rx(-a)
    Ry^-1 = Ry(-b)

    Now R*(1,0,0) = Rx*Ry*Rz(1,0,0) = (x, y, z)
    multiply both sides by Ry^-1 Rx^-1:
    Ry^-1 Rx^-1 Rx Ry Rz (1,0,0) = Rz (1,0,0) = Ry(-b) Rx(-a) (x, y, z) = (xp, yp, zp)
    ==>
    xp = cos(g)
    yp = sin(g)
    zp = 0

    and g = atan2(yp, zp)
    """
    v = rot * Vector(0, 0, 1)
    print(v)
    # solution 1.
    if v.x > 1.0:
        v.x = 1.0
    if v.x < -1.0:
        v.x = -1.0
    b = math.asin(v.x)
    if math.cos(b) > 0:
        a = math.atan2(-v.y, v.z)
    else:
        a = math.atan2(v.y, -v.z)
    # sanity check 1
    ysolution = -math.sin(a) * math.cos(b)
    zsolution = math.cos(a) * math.cos(b)
    if v.y * ysolution < 0 or v.z * zsolution < 0:
        print("Trying second solution")
        b = math.pi - b
        if math.cos(b) > 0:
            a = math.atan2(-v.y, v.z)
        else:
            a = math.atan2(v.y, -v.z)
    # sanity check 2
    ysolution = -math.sin(a) * math.cos(b)
    zsolution = math.cos(a) * math.cos(b)
    if v.y * ysolution < 0 or v.z * zsolution < 0:
        print("Failed both solutions!")
        print(v.y, ysolution)
        print(v.z, zsolution)
    Ryinv = FreeCAD.Rotation(Vector(0, 1, 0), math.degrees(-b))
    Rxinv = FreeCAD.Rotation(Vector(1, 0, 0), math.degrees(-a))
    vp = Ryinv * Rxinv * rot * Vector(1, 0, 0)
    g = math.atan2(vp.y, vp.x)

    return [math.degrees(a), math.degrees(b), math.degrees(g)]


def reportObject(obj):

    GDMLShared.trace("Report Object")
    GDMLShared.trace(obj)
    GDMLShared.trace("Name : " + obj.Label)
    GDMLShared.trace("Type : " + obj.TypeId)
    if hasattr(obj, "Placement"):
        print("Placement")
        print("Pos   : " + str(obj.Placement.Base))
        print("axis  : " + str(obj.Placement.Rotation.Axis))
        print("angle : " + str(obj.Placement.Rotation.Angle))

    while switch(obj.TypeId):

        ###########################################
        # FreeCAD GDML Parts                      #
        ###########################################
        if case("Part::FeaturePython"):
            GDMLShared.trace("Part::FeaturePython")
            #
            # if hasattr(obj.Proxy,'Type'):
            #   print (obj.Proxy.Type)
            #   print (obj.Name)
            # else :
            #   print("Not a GDML Feature")

            # print dir(obj)
            # print dir(obj.Proxy)
            # print("cylinder : Height "+str(obj.Height)+ " Radius "+str(obj.Radius))
            break
        ###########################################
        # FreeCAD Parts                           #
        ###########################################
        if case("Part::Sphere"):
            print("Sphere Radius : " + str(obj.Radius))
            break

        if case("Part::Box"):
            print(
                "cube : ("
                + str(obj.Length)
                + ","
                + str(obj.Width)
                + ","
                + str(obj.Height)
                + ")"
            )
            break

        if case("Part::Cylinder"):
            print(
                "cylinder : Height "
                + str(obj.Height)
                + " Radius "
                + str(obj.Radius)
            )
            break

        if case("Part::Cone"):
            print(
                "cone : Height "
                + str(obj.Height)
                + " Radius1 "
                + str(obj.Radius1)
                + " Radius2 "
                + str(obj.Radius2)
            )
            break

        if case("Part::Torus"):
            print("Torus")
            print(obj.Radius1)
            print(obj.Radius2)
            break

        if case("Part::Prism"):
            print("Prism")
            break

        if case("Part::RegularPolygon"):
            print("RegularPolygon")
            break

        if case("Part::Extrusion"):
            print("Extrusion")
            break

        if case("Circle"):
            print("Circle")
            break

        if case("Extrusion"):
            print("Wire extrusion")
            break

        if case("Mesh::Feature"):
            print("Mesh")
            # print dir(obj.Mesh)
            break

        print("Other")
        print(obj.TypeId)
        break


def addPhysVol(xmlVol, volName):
    GDMLShared.trace("Add PhysVol to Vol : " + volName)
    # print(ET.tostring(xmlVol))
    pvol = ET.SubElement(xmlVol, "physvol", {"name": "PV_" + volName})
    ET.SubElement(pvol, "volumeref", {"ref": volName})
    return pvol


def getIdentifier(obj):
    ''' For objects created from a gdml file we need a unique identifier to locate
    the entry in the gdmlInfo sheet.
    '''
    return obj.Label

    if hasattr(obj, "CopyNumber"):
        append = '.' + str(obj.CopyNumber)
    else:
        append = ''

    print(f"{obj.Name}{append}")
    if obj.TypeId == "App::Part":
        name = obj.Name + append
        return name
    elif obj.TypeId == "App::Link":
        return obj.LinkedObject.Name + append
    else:
        return obj.Name


def addPhysVolPlacement(obj, xmlVol, placement, pvName=None, refName=None) -> None:
    # obj: App:Part to be placed.
    # xmlVol: the xml that the <physvol is a subelement of.
    # It may be a <volume, or an <assembly
    # refName = volref: the name of the volume being placed
    # placement: the placement of the <physvol
    # For most situations, the placement (pos, rot) should be that
    # of the obj (obj.Placement.Base, obj.Placement.Rotation), but
    # if the user specifies a placement for the solid, then the placement
    # has to be a product of both placements. Here we don't try to figure
    # that out, so we demand the placement be given explicitly

    if xmlVol is None:
        return

    if refName is None:
        refName = NameManager.getVolumeName(obj)

    # TODO units???
    if placement == obj.Placement:  # placement is same as one sees in the doc
        # try to export the placement as an expression
        xexpr = GDMLShared.getPropertyExpression(obj, '.Placement.Base.x')
        yexpr = GDMLShared.getPropertyExpression(obj, '.Placement.Base.y')
        zexpr = GDMLShared.getPropertyExpression(obj, '.Placement.Base.z')
        # these might be just floats also
        pos = (xexpr, yexpr, zexpr)
    else:
        print(" placement != obj.Placement ")
        print(f" placement = {placement}")
        print(f" obj.Placement = {obj.Placement}")
        pos = placement.Base

    identifier = getIdentifier(obj)
    if pvName is None:
        if xmlVol.tag == "assembly":
            assemblyName = xmlVol.attrib['name']
            if assemblyName in AssemblyDict:
                entry = AssemblyDict[assemblyName]
                pvName = entry.getPVname(obj)
            else:
                pvName = NameManager.getPhysvolName(obj)
        else:
            pvName = NameManager.getPhysvolName(obj)

    if not hasattr(obj, "CopyNumber"):
        if pvName is None:
            pvol = ET.SubElement(xmlVol, "physvol")
        else:
            pvol = ET.SubElement(xmlVol, "physvol", {"name": pvName})
    else:
        cpyNum = str(obj.CopyNumber)
        GDMLShared.trace("CopyNumber : " + cpyNum)
        if pvName is None:
            pvol = ET.SubElement(xmlVol,"physvol", {"copynumber": cpyNum})
        else:
            pvol = ET.SubElement(xmlVol,"physvol", {"name": pvName, "copynumber": cpyNum})

    ET.SubElement(pvol, "volumeref", {"ref": refName})
    exportPosition(identifier, pvol, pos)
    exportRotation(identifier, pvol, placement.Rotation)
    # processPlacement(volName, pvol, placement)
    if hasattr(obj, "GDMLscale"):
        scaleName = refName + "scl"
        ET.SubElement(
            pvol,
            "scale",
            {
                "name": scaleName,
                "x": str(obj.GDMLscale[0]),
                "y": str(obj.GDMLscale[1]),
                "z": str(obj.GDMLscale[2]),
            },
        )

    return


def exportPosition(name, xml, pos):
    global POScount
    global centerDefined
    GDMLShared.trace("export Position")
    GDMLShared.trace(pos)
    x = pos[0]
    y = pos[1]
    z = pos[2]

    posType, posName = GDMLShared.getPositionName(name)
    print(f"exportPosition: name {name} posType {posType} posName {posName}")
    print(f"x {x}")
    print(f"y {y}")
    print(f"z {z}")

    if posType is None:  # The part is not in the gdmlInfo spread spreadsheet
        if x == 0 and y == 0 and z == 0:
            if not centerDefined:
                centerDefined = True
                ET.SubElement(
                    define,
                    "position",
                    {"name": "center", "x": "0", "y": "0", "z": "0", "unit": "mm"},
                )
            ET.SubElement(xml, "positionref", {"ref": "center"})
            return
        else:
            # just export insitu position
            posName = "P-" + name + str(POScount)
            POScount += 1
            posxml = ET.SubElement(xml, "position", {"name": posName, "unit": "mm"})

    else:  # the object exists in the gdmlInfo sheet
        if posType == "positionref":  # it necessarily has a posName
            # does it already exist in the define section
            posxml = define.find("position[@name='%s']" % posName)
            if posxml is not None:
                ET.SubElement(xml, "positionref", {"ref": posName})
                return
            else:
                print(f"name {name} exists in the gdmlInfo sheet, but not in the define sheet")
                print(f"Should not happen, but we'll create {posName} in the define section")
                posxml = ET.SubElement(define, "position", {"name": str(posName), "unit": "mm"})

        else:  # insitu position. It may not necessarily have a name
            posxml = ET.SubElement(xml, "position", {"unit": "mm"})
            if posName is not None:
                posxml.attrib["name"] = posName

    if x != 0:
        posxml.attrib["x"] = str(x)
    if y != 0:
        posxml.attrib["y"] = str(y)
    if z != 0:
        posxml.attrib["z"] = str(z)


def exportRotation(name, xml, rot, invertRotation=True):
    print("Export Rotation")
    global ROTcount
    global identityDefined
    global identityName

    angles = quaternion2XYZ(rot)
    a0 = angles[0]
    a1 = angles[1]
    a2 = angles[2]
    if invertRotation:
        a0 = -a0
        a1 = -a1
        a2 = -a2

    rotType, rotName = GDMLShared.getRotationName(name)
    if rotType is None:  # The part is not in the gdmlInfo spread spreadsheet
        if rot.Angle == 0:
            if not identityDefined:
                identityDefined = True
                rotxml = define.find("rotation[@name='%s']" % identityName)
                if rotxml == None:
                    ET.SubElement(
                        define,
                        "rotation",
                        {"name": identityName, "x": "0", "y": "0", "z": "0"},
                    )

            ET.SubElement(xml, "rotationref", {"ref": identityName})
            return

        else:
            # just export insitu rotation (NOT a rotationref)
            rotName = "R-" + name + str(ROTcount)
            ROTcount += 1
            rotxml = ET.SubElement(xml, "rotation", {"name": rotName, "unit": "deg"})

    else:  # the object exists in the gdmlInfo sheet
        if rotType == "rotationref":  # it necessarily has a rotName
            # does it already exist in the define section
            rotxml = define.find("rotation[@name='%s']" % rotName)
            if rotxml is not None:
                ET.SubElement(xml, "rotationref", {"ref": rotName})
                return
            else:
                print(f"name {name} exists in the gdmlInfo sheet, but not in the define sheet")
                print(f"Should not happen, but we'll create {rotName} in the define section")
                rotxml = ET.SubElement(define, "rotation", {"name": str(rotName), "unit": "degree"})

        else:  # insitu rotation. It may not necessarily have a name
            rotxml = ET.SubElement(xml, "rotation", {"unit": "degree"})
            if rotName is not None:
                rotxml.attrib["name"] = rotName

    if abs(a0) != 0:
        rotxml.attrib["x"] = str(a0)
    if abs(a1) != 0:
        rotxml.attrib["y"] = str(a1)
    if abs(a2) != 0:
        rotxml.attrib["z"] = str(a2)

    return


def exportScaling(name, xml, scl):
    global SCLcount
    global centerDefined
    GDMLShared.trace("export Scaling")
    GDMLShared.trace(scl)
    x = scl[0]
    y = scl[1]
    z = scl[2]
    sclName = "S-" + name + str(SCLcount)
    SCLcount += 1
    ET.SubElement(
        define,
        "scale",
        {"name": sclName, "x": str(x), "y": str(y), "z": str(z)},
    )
    ET.SubElement(xml, "scaleref", {"ref": sclName})


def processPlacement(name, xml, placement):
    exportPosition(name, xml, placement.Base)
    exportRotation(name, xml, placement.Rotation)



def addVolRef(volxml, volName, obj, solidName=None):
    # Pass material as Boolean
    material = getMaterial(obj)
    if solidName is None:
        solidName = NameManager.getName(obj)
    ET.SubElement(volxml, "materialref", {"ref": material})
    ET.SubElement(volxml, "solidref", {"ref": solidName})

    ET.SubElement(gxml, "volume", {"name": volName, "material": material})

    params = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/GDML")
    addColor = params.GetBool('exportColors', True)

    if (
        addColor is True
        and FreeCAD.GuiUp
        and hasattr(obj, "ViewObject")
        and hasattr(obj.ViewObject, "ShapeColor")
        and volName != WorldVOL
    ):
        c = obj.ViewObject.ShapeColor
        colour = (c[0], c[1], c[2], obj.ViewObject.Transparency/100)
        colStr = "#" + "".join("{:02x}".format(round(v * 255)) for v in colour)
        ET.SubElement(
            volxml, "auxiliary", {"auxtype": "Color", "auxvalue": colStr}
        )

    ''' Not sure why Keith put this in. It is leading to a surface being exported twice
    # Temp Fix ??? porosev issue 97
    print(f"Temp Fix {obj.Label}")
    # obj.Parents does not work?
    if hasattr(obj, "InList"):
        parent = obj.InList[0]
        print(f"Parent {parent.Label}")
        if hasattr(parent, "SensDet"):
            print(f"Parent {parent.Label} has SensDet")
            # SensDet could be enumeration of text value None
            if parent.SensDet != "None":
                print("Volume : " + volName)
                print("SensDet : " + parent.SensDet)
                ET.SubElement(
                    volxml,
                    "auxiliary",
                    {"auxtype": "SensDet", "auxvalue": parent.SensDet},
                )
        if hasattr(parent, "SkinSurface"):
            print(f"SkinSurf Property : {parent.SkinSurface}")
            # SkinSurfface could be enumeration of text value None
            if parent.SkinSurface != "None":
                print("Need to export : skinsurface")
                ss = ET.Element(
                    "skinsurface",
                    {
                        "name": "skin" + parent.SkinSurface,
                        "surfaceproperty": parent.SkinSurface,
                    },
                )
                ET.SubElement(ss, "volumeref", {"ref": volName})

                skinSurfaces.append(ss)
    # End Temp Fix        
    '''
    # print(ET.tostring(volxml))


def processIsotope(
    obj, item
):  # maybe part of material or element (common code)
    if hasattr(obj, "Z"):
        # print(dir(obj))
        item.set("Z", str(obj.Z))

    if hasattr(obj, "N"):
        # print(dir(obj))
        item.set("N", str(obj.N))

    if hasattr(obj, "formula"):
        # print(dir(obj))
        item.set("formula", str(obj.formula))

    if (
        hasattr(obj, "unit")
        or hasattr(obj, "atom_value")
        or hasattr(obj, "value")
    ):
        atom = ET.SubElement(item, "atom")

        if hasattr(obj, "unit"):
            atom.set("unit", str(obj.unit))

        if hasattr(obj, "type"):
            atom.set("unit", str(obj.type))

        if hasattr(obj, "atom_value"):
            atom.set("value", str(obj.atom_value))

        if hasattr(obj, "value"):
            atom.set("value", str(obj.value))


def processMatrix(obj):

    global define
    print("add matrix to define")
    ET.SubElement(
        define,
        "matrix",
        {"name": obj.Label, "coldim": str(obj.coldim), "values": obj.values},
    )


class SurfaceManager:
    ''' Class to isolate methods and globals dealing with surfaces
    from the rest of the code
    '''

    skinSurfaces = []

    def __init__(self):
        SurfaceManager.skinSurfaces = []

    @staticmethod
    def addSurface(s):
        SurfaceManager.skinSurfaces.append(s)

    @staticmethod
    def cleanFinish(finish):
        print(f"finish {finish}")
        if finish == "polished | polished":
            return "polished"
        else:
            ext = "extended | "
            if ext not in finish:
                # print('Does not contain')
                return finish.replace(" | ", "")
            else:
                # print(f"Replace {finish.replace(ext,'')}")
                return finish.replace(ext, "")

    @staticmethod
    def cleanExtended(var):
        ext = "extended | "
        if ext not in var:
            return var
        else:
            return var.replace(ext, "")


    @staticmethod
    def processOpticalSurface(obj):
        global solids
        # print(solids)
        print("Add opticalsurface")
        print(str(solids))
        finish = SurfaceManager.cleanFinish(obj.finish)
        type = SurfaceManager.cleanExtended(obj.type)
        op = ET.SubElement(
            solids,
            "opticalsurface",
            {
                "name": obj.Label,
                "model": obj.model,
                "finish": finish,
                "type": type,
                "value": str(obj.value),
            },
        )
        for prop in obj.PropertiesList:
            if obj.getGroupOfProperty(prop) == "Properties":
                ET.SubElement(
                    op, "property", {"name": prop, "ref": getattr(obj, prop)}
                )


    @staticmethod
    def processSkinSurfaces():
        global structure

        for ss in SurfaceManager.skinSurfaces:
            structure.append(ss)
        return

    @staticmethod
    def getPVobject(doc, name_or_obj):
        '''
        In an older version of GDMLbordersurface the two properties
        PV1 and PV2 where strings that are the names of the physvol gdml.
        In the current version PV1 and PV2 and App::Parts (or App::Link)
        that eventually give rise to a physvol export. This helper metjod
        returns the App::part object, in case PVname is a name (a string)
        '''
        print(f"getPVobject {type(name_or_obj)}")
        if hasattr(name_or_obj, "TypeId"):
            # name_or_obj is an object
            obj = name_or_obj  # not necessary, but to emphasize type or argument
            print(f"{obj.Label} {obj.TypeId}")
            if obj.TypeId == "App::Part":
                return obj
            elif obj.TypeId == "App::Link":
                return obj
            else:
                print("Not handled")
        else:
            name = name_or_obj  # not necessary, but to emphasize type or argument
            print("Old type : string")
            obj = doc.getObject(name)
            print(f"Found Object {obj.Label}")
            return obj

    @staticmethod
    def getPVname(parentObj, obj, idx, dictKey) -> str:
        '''
        Unfortunately, geant produces its own internal names for assemblies. The generated name
        is a very complicated thing that depends on the volume being placed and the number of times
        it is being placed. As part of exporting the the document as gdml, we first build
        a dictionary in buildAssemblyDict, that associates with each physvol placement of an assembly
        the same name that geant generates. Here we retrieve the physvol name from the dictionary
        if the dictKey is a key in the Assembly dictionary, or the name physvol name associated
        with the parentObj (an App::Part)
        '''
        # Obj is the source used to create candidates
        print(f"getPVname {obj.Label}")
        if dictKey in AssemblyDict:
            print(f"returning name of {dictKey} from Assembly dictionary")
            entry = AssemblyDict[dictKey]
            return entry.getPVname(obj, idx)
        else:
            print("No Parent")

        return NameManager.getPhysvolName(parentObj)

    @staticmethod
    def exportSurfaceProperty(Name, Surface, ref1, ref2):
        borderSurface = ET.SubElement(
            structure, "bordersurface", {"name": Name, "surfaceproperty": Surface}
        )
        ET.SubElement(borderSurface, "physvolref", {"ref": ref1})
        ET.SubElement(borderSurface, "physvolref", {"ref": ref2})


    @staticmethod
    def checkFaces(pair1, pair2):
        def preCheck(shape1, shape2):
            #
            # Precheck common faces, by checking
            # if bounding boxes separation is comparable
            # to sum of half-lengths
            #
            b1 = shape1.BoundBox
            b2 = shape2.BoundBox
            vcc = b2.Center - b1.Center
            if (
                abs(vcc.x) > (b1.XLength + b2.XLength) * 1.01 / 2
                or abs(vcc.y) > (b1.YLength + b2.YLength) * 1.01 / 2
                or abs(vcc.z) > (b1.ZLength + b2.ZLength) * 1.01 / 2
            ):
                return False
            else:
                return True

        tolerence = 1e-6
        obj1 = pair1[0]
        matrix1 = pair1[1].Matrix
        obj2 = pair2[0]
        matrix2 = pair2[1].Matrix

        if hasattr(obj1, "Shape") and hasattr(obj2, "Shape"):
            obj1t = obj1.Shape.transformGeometry(matrix1)
            obj2t = obj2.Shape.transformGeometry(matrix2)
            if not preCheck(obj1t, obj2t):
                print("Fails precheck")
                return False

            faces1 = obj1t.Faces
            faces2 = obj2t.Faces
            #        faces1 = obj1.Shape.Faces
            #        faces2 = obj2.Shape.Faces
            for f1 in faces1:
                comShape = f1.common(faces2, tolerence)
                if len(comShape.Faces) > 0:
                    print("Common")
                    return True
                else:
                    print("Not common")
        return False


    @staticmethod
    def processSurface(name, cnt, surface,
                       Obj1, obj1, idx1, dictKey1,
                       Obj2, obj2, idx2, dictKey2):
        print(f"processSurface {name} {surface}")
        print(f" {Obj1.Label} {obj1.Label} {Obj2.Label} {obj2.Label}")
        ref1 = SurfaceManager.getPVname(Obj1, obj1, idx1, dictKey1)
        ref2 = SurfaceManager.getPVname(Obj2, obj2, idx2, dictKey2)
        SurfaceManager.exportSurfaceProperty(name + str(cnt), surface, ref1, ref2)
        return cnt + 1

    @staticmethod
    def processCandidates(name, surface, check, Obj1, dict1, Obj2, dict2):
        cnt = 1
        for assem1, set1 in dict1.items():
            print(f"process Candidates {assem1} {check} {len(set1)}")
            for assem2, set2 in dict2.items():
                print(f"process Candidates {assem2} {check} {len(set2)}")
                for idx1, items1 in enumerate(set1):
                    obj1 = items1[0]
                    for idx2, items2 in enumerate(set2):
                        obj2 = items2[0]
                        if items1 != items2:
                            if check:
                                pairStr = f"{obj1.Label} : {obj2.Label} "
                                if SurfaceManager.checkFaces(items1, items2):
                                    cnt = SurfaceManager.processSurface(name, cnt, surface,
                                                         Obj1, obj1, idx1, assem1,
                                                         Obj2, obj2, idx2, assem2)
                                    print(f"<<< Common face : {pairStr} >>>")
                                    cnt += 1
                                else:
                                    print(f"<<< No common face : {pairStr} >>>")
                            else:
                                cnt = SurfaceManager.processSurface(
                                    name, cnt, surface,
                                    Obj1, obj1, idx1, assem1,
                                    Obj2, obj2, idx2, assem2
                                )

    @staticmethod
    def _getSubVols(vol, placement, volLabel):
        global childObjects

        """return a flattened list of terminal solids that fall
        under this vol. By flattened we mean something like:
           vol
             subVol1
                subVol2
                   solid1
                   solid2
                    ...
                subVol3
                   solid3
                   solid4
                    ....
    
        The returned list is a list of triples:
                 ((solid1, placement1, subvol2.Label), (solid2, placement2, subvol2.Label), (solid3, placement3, subVol3.Label), ...
        """
        print(f"getSubVols {vol.Label} {volLabel} {placement} ")
        volsList = []
        print(f"_getSubVols: isContainer({vol.Label}) = {isContainer(vol)}")
        if len(childObjects[vol]) == 0:
            return [(vol, placement, volLabel)]

        # we assume that the user meant to select ONLY the top volume of a container as the solid with
        # the optical surface property.
        if isContainer(vol):
            obj = childObjects[vol][0]
            return [(obj, placement * obj.Placement, volLabel)]

        # vol must be an assembly, recurse
        for obj in childObjects[vol]:
            # breakpoint()
            typeId = obj.TypeId
            tObj = obj
            # print(obj.Label)
            if hasattr(obj, "LinkedObject"):
                typeId = obj.LinkedObject.TypeId
                if len(childObjects[obj]) != 0:
                    tObj = childObjects[obj][0]

            if typeId == "App::Part":
                volsList += SurfaceManager._getSubVols(tObj, placement * obj.Placement, obj.Label)
            else:
                if typeId == "Part::FeaturePython":
                    volsList.append((obj, placement, volLabel))

        return volsList

    @staticmethod
    def getSubVols(vol, placement):
        """
        given a structure of the form
           vol
             subVol1
                subVol2
                   solid1
                   solid2
                    ...
                subVol3
                   solid3
                   solid4
                    ....

        return a dictionary:
        {subVol2.Label: ((solid1, placement1), (solid2, placement2)),
         subVol3.Label: ((solid1, placement1), (solid2, placement2))}
        """

        flattenedList = SurfaceManager._getSubVols(vol, placement, vol.Label)
        solidsDict = {}
        for item in flattenedList:
            vol = item[0]
            parentLabel = item[2]
            if parentLabel in solidsDict:
                solidsDict[parentLabel].append((item[0], item[1]))
            else:
                solidsDict[parentLabel] = [(item[0], item[1])]

        return solidsDict

    @staticmethod
    def processBorderSurfaces():
        print("==============================================")
        print(f"Export Border Surfaces - Assemblies {len(AssemblyDict)}")
        print("==============================================")
        # print(AssemblyDict)
        doc = FreeCAD.ActiveDocument

        for obj in doc.Objects:
            if obj.TypeId == "App::FeaturePython":
                print(f"TypeId {obj.TypeId} Name {obj.Label}")
                # print(dir(obj))
                # print(obj.Proxy)
                if isinstance(obj.Proxy, GDMLbordersurface):
                    print("Border Surface")
                    obj1 = SurfaceManager.getPVobject(doc, obj.PV1)
                    candSet1 = SurfaceManager.getSubVols(obj1, obj1.Placement)
                    print(f"Candidates 1 : {obj1.Label} {len(candSet1)}")
                    printSet("Candidate1", candSet1)
                    obj2 = SurfaceManager.getPVobject(doc, obj.PV2)
                    candSet2 = SurfaceManager.getSubVols(obj2, obj2.Placement)
                    print(f"Candidates 2 : {obj2.Label} {len(candSet2)}")
                    printSet("Candidate2", candSet2)
                    # default for old borderSurface Objects
                    check = False
                    if hasattr(obj, "CheckCommonFaces"):
                        check = obj.CheckCommonFaces
                    SurfaceManager.processCandidates(
                        obj.Label,
                        obj.Surface,
                        check,
                        obj1,
                        candSet1,
                        obj2,
                        candSet2,
                    )


def printListObj(name, listArg):
    print(f"<=== Object {name} list ===>")
    for obj in listArg:
        print(obj.Label)
    print("<===============================")


def printSet(name, dictArg):
    print(f"<=== Object Set {name} len {len(dictArg)} ===>")
    for k, v in dictArg.items():
        print(k)
        for obj in v:
            print(f"\t {obj[0].Label}")
    print("<===============================")



def processSpreadsheetMatrix(sheet):
    # Stupid way of finding how many rows. columns:
    # increase col, row until we get an exception for that cell
    # You would think the API would provide a simple function
    def ncols():
        n = 0
        try:
            # TODO: deal with case n > 26
            while n < 26 * 26:
                sheet.get(chr(ord("A") + n) + "1")
                n += 1
        except:
            pass
        return n

    def nrows():
        n = 0
        try:
            while n < 256 * 256:
                sheet.get("A" + str(n + 1))
                n += 1
        except:
            pass
        return n

    global define
    print("add matrix to define")

    coldim = ncols()
    rows = nrows()

    s = ""
    for row in range(0, rows):
        for col in range(0, coldim):
            cell = chr(ord("A") + col) + str(row + 1)
            s += str(sheet.get(cell)) + " "

    ET.SubElement(
        define,
        "matrix",
        {"name": sheet.Label, "coldim": str(coldim), "values": s[:-1]},
    )


def processOpticals():
    print("Process Opticals")
    Grp = FreeCAD.ActiveDocument.getObject("Opticals")
    if hasattr(Grp, "Group"):
        for obj in Grp.Group:
            print(f"Name : {obj.Label}")
            while switch(obj.Label):
                if case("Matrix"):
                    print("Matrix")
                    for m in obj.Group:
                        if m.TypeId == "Spreadsheet::Sheet":
                            processSpreadsheetMatrix(m)
                        else:
                            processMatrix(m)
                    break

                if case("Surfaces"):
                    print("Surfaces")
                    print(obj.Group)
                    for s in obj.Group:
                        SurfaceManager.processOpticalSurface(s)
                    break

                if case("SkinSurfaces"):
                    print("SkinSurfaces")
                    for s in obj.Group:
                        SurfaceManager.processSkinSurfaces(s)
                    break


_nist_isotope_cache = None   # loaded once on first use


def _getNISTIsotopeMap():
    """Parse Resources/NIST_Isotopes.xml once and return a dict name→ET.Element."""
    global _nist_isotope_cache
    if _nist_isotope_cache is not None:
        return _nist_isotope_cache
    _nist_isotope_cache = {}
    try:
        from .init_gui import joinDir
        path = joinDir("Resources/NIST_Isotopes.xml")
        tree = ET.parse(path)
        for iso in tree.getroot().iter("isotope"):
            name = iso.get("name")
            if name:
                _nist_isotope_cache[name] = iso
        print(f"[GDML export] Loaded {len(_nist_isotope_cache)} isotopes "
              f"from NIST_Isotopes.xml")
    except Exception as exc:
        print(f"[GDML export] WARNING: could not load NIST_Isotopes.xml: {exc}")
    return _nist_isotope_cache


def _fixMissingIsotopes():
    """Post-export pass: insert any isotope definitions that are referenced
    by <element> fraction children but were not emitted by createIsotopes().

    Priority order for sourcing a missing isotope definition:
      1. GDMLisotope proxy objects anywhere in the FreeCAD document
      2. NIST_Isotopes.xml (covers all standard isotopes incl. U235, U238 …)

    Inserts definitions immediately before the first <element> node so that
    GDML ordering rules (definitions before references) are satisfied.
    """
    global materials

    # Isotopes already written to the materials section
    defined = {iso.get("name") for iso in materials.findall("isotope")}

    # Isotope names referenced as fraction targets inside any <element>
    referenced = set()
    for elem in materials.findall("element"):
        for frac in elem.findall("fraction"):
            ref = frac.get("ref")
            if ref:
                referenced.add(ref)

    missing = referenced - defined
    if not missing:
        return

    print(f"[GDML export] Isotopes referenced in elements but not defined: "
          f"{sorted(missing)}")

    # Source 1: GDMLisotope proxy objects anywhere in the document
    iso_map = {}
    for obj in FreeCAD.ActiveDocument.Objects:
        if hasattr(obj, "Proxy") and isinstance(obj.Proxy, GDMLisotope):
            iso_map[obj.Label] = obj

    # Source 2: NIST_Isotopes.xml (pre-parsed ET.Element nodes)
    nist_map = _getNISTIsotopeMap()

    # Insertion point: just before the first <element> so ordering is valid
    children = list(materials)
    first_elem_idx = next(
        (i for i, c in enumerate(children) if c.tag == "element"), None
    )

    inserted = 0
    for name in sorted(missing):
        iso_xml = None
        if name in iso_map:
            # Build from FreeCAD proxy object
            iso_xml = ET.Element("isotope", {"name": name})
            processIsotope(iso_map[name], iso_xml)
        elif name in nist_map:
            # Copy directly from NIST table
            import copy
            iso_xml = copy.deepcopy(nist_map[name])
        else:
            print(f"[GDML export]   WARNING: isotope '{name}' not found in "
                  f"document or NIST table — it will be absent from output")

        if iso_xml is not None:
            if first_elem_idx is not None:
                materials.insert(first_elem_idx, iso_xml)
                first_elem_idx += 1   # keep subsequent inserts in order
            else:
                materials.append(iso_xml)
            inserted += 1
            print(f"[GDML export]   Inserted missing isotope: {name}")

    if inserted:
        print(f"[GDML export] {inserted} missing isotope definition(s) added.")


def processMaterials():
    print("\nProcess Materials")
    global materials

    for GName in [
        "Define",
        "Isotopes",
        "Elements",
        "Materials",
    ]:
        Grp = FreeCAD.ActiveDocument.getObject(GName)
        if Grp is not None:
            # print(Grp.TypeId+" : "+Grp.Label)
            print(Grp.Label)
            if processGroup(Grp) is False:
                break

    # Note: _fixMissingIsotopes() is NOT called here.  It is called once
    # after ALL material-writing passes (including postCreateGeantMaterials)
    # complete, in the main export function.


def processFractionsComposites(obj, item):
    # Fractions are used in Material and Elements
    if isinstance(obj.Proxy, GDMLfraction):
        # print("GDML fraction :" + obj.Label)
        # GDMLfraction stores ref as the property group name, not as a
        # separate property.  Recover it via getGroupOfProperty("n").
        ref = (
            str(obj.ref)
            if hasattr(obj, "ref")
            else obj.getGroupOfProperty("n")
        )
        ET.SubElement(
            item,
            "fraction",
            {"n": str(obj.n), "ref": ref},
        )

    if isinstance(obj.Proxy, GDMLcomposite):
        # print("GDML Composite")
        ET.SubElement(
            item,
            "composite",
            {"n": str(obj.n), "ref": str(obj.ref)},
        )


# --- Container-group label handling (issue #176) --------------------------
# FreeCAD appends a numeric suffix (e.g. "ReactorMaterials002") when a Label
# collides with another object's Label.  The OpenMC-only "ReactorMaterials"
# container and the "Geant4" predefined container must never be written to a
# GDML file, so match the base name followed by any trailing digits.
_REACTOR_CONTAINER_RE = re.compile(r"^ReactorMaterials\d*$")
_GEANT4_CONTAINER_RE = re.compile(r"^Geant4\d*$")


def _isReactorContainer(label):
    return bool(_REACTOR_CONTAINER_RE.match(label))


def _isGeant4Container(label):
    return bool(_GEANT4_CONTAINER_RE.match(label))


def createMaterials(group):
    global materials
    # "Geant4" is handled by postCreateGeantMaterials().
    # "ReactorMaterials" is an OpenMC-only container — never exported to GDML.
    for obj in group:
        # "Geant4" is exported by postCreateGeantMaterials(); "ReactorMaterials"
        # is an OpenMC-only container.  Both (and their numeric-suffixed
        # variants, e.g. "ReactorMaterials002") must be skipped here.  See #176.
        if _isGeant4Container(obj.Label) or _isReactorContainer(obj.Label):
            continue
        if not hasattr(obj, 'Group'):
            continue
        item = ET.SubElement(
            materials, "material", {"name": nameFromLabel(obj.Label)}
        )

        # property must be first
        for prop in obj.PropertiesList:
            if obj.getGroupOfProperty(prop) == "Properties":
                ET.SubElement(
                    item,
                    "property",
                    {"name": prop, "ref": getattr(obj, prop)},
                )

        if hasattr(obj, "Tunit") and hasattr(obj, "Tvalue"):
            ET.SubElement(
                item,
                "T",
                {"unit": obj.Tunit, "value": str(obj.Tvalue)},
            )

        if hasattr(obj, "MEEunit"):
            ET.SubElement(
                item,
                "MEE",
                {"unit": obj.MEEunit, "value": str(obj.MEEvalue)},
            )

        if hasattr(obj, "Dunit") or hasattr(obj, "Dvalue"):
            D = ET.SubElement(item, "D")
            if hasattr(obj, "Dunit"):
                D.set("unit", str(obj.Dunit))
            if hasattr(obj, "Dvalue"):
                D.set("value", str(obj.Dvalue))

        # process common options material / element
        processIsotope(obj, item)
        for o in obj.Group:
            processFractionsComposites(o, item)


def _getSubGroup(topGroupName, subLabel):
    """Return the sub-group with label *subLabel* inside the top-level FreeCAD
    group named *topGroupName*, or None if not found."""
    doc = FreeCAD.ActiveDocument
    topGrp = doc.getObject(topGroupName)
    if topGrp is None:
        return None
    for child in topGrp.Group:
        # Tolerate FreeCAD numeric suffixes (e.g. "ReactorMaterials002"); see #176
        if child.Label == subLabel or child.Label.rstrip("0123456789") == subLabel:
            return child
    return None


def _isReactorMaterial(name):
    """Return True if *name* is defined in Materials/ReactorMaterials."""
    grp = _getSubGroup("Materials", "ReactorMaterials")
    if grp is None:
        return False
    return any(obj.Label == name for obj in grp.Group)


def postCreateReactorMaterials():
    """Export reactor material definitions that are actually referenced by
    volumes, together with any element and isotope dependencies.

    Called only when one or more volumes have a material that lives in the
    Materials/ReactorMaterials sub-group (normally an OpenMC-only document).
    Isotope gaps (U235, U238 etc.) are filled by _fixMissingIsotopes() which
    runs as a post-pass after this function.
    """
    global materials
    global usedReactorMaterials

    if not usedReactorMaterials:
        return

    reactorMatGrp  = _getSubGroup("Materials", "ReactorMaterials")
    reactorElemGrp = _getSubGroup("Elements",  "ReactorMaterials")

    # Names already written to <materials> — avoid duplicates
    already_elems = {e.get("name") for e in materials.findall("element")}
    already_mats  = {m.get("name") for m in materials.findall("material")}

    for matName in sorted(usedReactorMaterials):
        # --- find the FreeCAD object ---
        matObj = None
        if reactorMatGrp:
            for obj in reactorMatGrp.Group:
                if obj.Label == matName:
                    matObj = obj
                    break
        if matObj is None:
            print(f"[GDML export] WARNING: reactor material '{matName}' used "
                  f"by a volume but not found in Materials/ReactorMaterials")
            continue

        # --- export element dependencies first ---
        if reactorElemGrp and hasattr(matObj, 'Group'):
            elem_refs = set()
            for frac in matObj.Group:
                if hasattr(frac, 'ref'):
                    elem_refs.add(str(frac.ref))
            for elemObj in reactorElemGrp.Group:
                if elemObj.Label in elem_refs and \
                        elemObj.Label not in already_elems:
                    createElement(elemObj)
                    already_elems.add(elemObj.Label)

        # --- export the material definition ---
        if matName in already_mats:
            continue
        item = ET.SubElement(
            materials, "material", {"name": nameFromLabel(matObj.Label)}
        )
        for prop in matObj.PropertiesList:
            if matObj.getGroupOfProperty(prop) == "Properties":
                ET.SubElement(
                    item, "property",
                    {"name": prop, "ref": getattr(matObj, prop)},
                )
        if hasattr(matObj, "Tunit") and hasattr(matObj, "Tvalue"):
            ET.SubElement(
                item, "T",
                {"unit": matObj.Tunit, "value": str(matObj.Tvalue)},
            )
        if hasattr(matObj, "MEEunit"):
            ET.SubElement(
                item, "MEE",
                {"unit": matObj.MEEunit, "value": str(matObj.MEEvalue)},
            )
        if hasattr(matObj, "Dunit") or hasattr(matObj, "Dvalue"):
            D = ET.SubElement(item, "D")
            if hasattr(matObj, "Dunit"):
                D.set("unit", str(matObj.Dunit))
            if hasattr(matObj, "Dvalue"):
                D.set("value", str(matObj.Dvalue))
        processIsotope(matObj, item)
        if hasattr(matObj, 'Group'):
            for o in matObj.Group:
                processFractionsComposites(o, item)
        already_mats.add(matName)
        print(f"[GDML export] Reactor material '{matName}' exported on demand")


def postCreateGeantMaterials():
    '''
    Geant4 materials are not added or created in createMaterials.
    Here we add those materials to the materials group
    '''
    global materials
    global usedGeant4Materials

    # Note: element/isotope decomposition for G4_* materials is intentionally
    # omitted here. Geant4 resolves G4_* materials via its internal NIST manager
    # and does not need explicit element/isotope definitions in the GDML file.
    # Element/isotope decomposition is only needed for OpenMC export (exportOpenMC.py).

    for mat in usedGeant4Materials:
        obj = FreeCAD.ActiveDocument.getObjectsByLabel(mat)[0]
        item = ET.SubElement(
            materials, "material", {"name": str(mat)}
        )
        # property must be first
        for prop in obj.PropertiesList:
            if obj.getGroupOfProperty(prop) == "Properties":
                ET.SubElement(
                    item,
                    "property",
                    {"name": prop, "ref": getattr(obj, prop)},
                )

        if hasattr(obj, "Dunit") or hasattr(obj, "Dvalue"):
            # print("Dunit or DValue")
            D = ET.SubElement(item, "D")
            if hasattr(obj, "Dunit"):
                D.set("unit", str(obj.Dunit))

            if hasattr(obj, "Dvalue"):
                D.set("value", str(obj.Dvalue))

            if hasattr(obj, "Tunit") and hasattr(obj, "Tvalue"):
                ET.SubElement(
                    item,
                    "T",
                    {"unit": obj.Tunit, "value": str(obj.Tvalue)},
                )

            if hasattr(obj, "MEEunit"):
                ET.SubElement(
                    item,
                    "MEE",
                    {"unit": obj.MEEunit, "value": str(obj.MEEvalue)},
                )
        # process common options material / element
        processIsotope(obj, item)
        if len(obj.Group) > 0:
            for o in obj.Group:
                processFractionsComposites(o, item)


def createElements(group):
    global materials
    for obj in group:
        # "ReactorMaterials" sub-group holds OpenMC-only elements — skip for GDML
        if _isReactorContainer(obj.Label):
            continue
        createElement(obj)


def createElement(obj):
    global materials
    item = ET.SubElement(
        materials, "element", {"name": nameFromLabel(obj.Label)}
    )
    # Common code Isotope and Elements1
    processIsotope(obj, item)

    if len(obj.Group) > 0:
        for o in obj.Group:
            processFractionsComposites(o, item)


def createConstants(group):
    global define
    for obj in group:
        if isinstance(obj.Proxy, GDMLconstant):
            # print("GDML constant")
            # print(dir(obj))

            ET.SubElement(
                define, "constant", {"name": obj.Label, "value": obj.value}
            )

def createDefine(group):
    global define

    from .GDMLShared import definesColumn
    # should come up with a test that relies on version number of the WB to test for this
    sheet = FreeCAD.ActiveDocument.getObject("defines")
    if sheet is None:  # Older docs not having a define spreadsheet
        createConstants(group)
        createVariables(group)
        return

    numRows = GDMLShared.lastRow(sheet)
    for row in range(1, numRows+1):
        entryType = sheet.get(definesColumn['type']+str(row))
        entryName = sheet.get(definesColumn['name']+str(row))

        if entryType == 'constant' or entryType == 'variable':
            value = sheet.getContents(definesColumn['value'] + str(row))
            if len(value) > 0:
                if value[0] == "=":
                    value = GDMLShared.SheetHandler.FC_expression_to_gdml(value[1:])

                ET.SubElement(
                    define, str(entryType), {"name": str(entryName), "value": str(value)}
                )

        elif entryType == "quantity":
            quantityType = sheet.get(definesColumn['quantity_type'] + str(row))
            quantityUnit = sheet.get(definesColumn['quantity_unit'] + str(row))
            quantityValue = sheet.getContents(definesColumn['quantity_value'] + str(row))
            if quantityValue[0] == '=':
                quantityValue = GDMLShared.SheetHandler.FC_expression_to_gdml(quantityValue)

            ET.SubElement(
                define, str(entryType), {"name": str(entryName), "type": str(quantityType),
                                         "value": str(quantityValue),"unit": quantityUnit}
            )


        elif entryType == "position":
            attrib = {}
            attrib["name"] = str(entryName)
            for prop in ["x", "y", "z", "unit"]:
                cell = definesColumn["pos_" + prop] + str(row)
                value = sheet.getContents(cell)
                if len(value) > 0:
                    if value[0] == "=":
                        value = GDMLShared.SheetHandler.FC_expression_to_gdml(value[1:])
                    else:
                        value = sheet.get(cell)
                    attrib[prop] = str(value)

            ET.SubElement( define, str(entryType), attrib)

        elif entryType == "rotation":
            attrib = {}
            attrib["name"] = str(entryName)
            for prop in ["x", "y", "z", "unit"]:
                cell = definesColumn["rot_" + prop] + str(row)
                value = sheet.getContents(cell)
                if len(value) > 0:
                    if value[0] == "=":
                        value = GDMLShared.SheetHandler.FC_expression_to_gdml(value[1:])
                    else:
                        value = sheet.get(cell)
                    attrib[prop] = str(value)

            ET.SubElement( define, str(entryType), attrib)


def createVariables(group):
    global define
    for obj in group:
        if isinstance(obj.Proxy, GDMLvariable):
            # print("GDML variable")
            # print(dir(obj))

            ET.SubElement(
                define, "variable", {"name": obj.Label, "value": obj.value}
            )


def createQuantities(group):
    global define
    for obj in group:
        if isinstance(obj.Proxy, GDMLquantity):
            # print("GDML quantity")
            # print(dir(obj))

            ET.SubElement(
                define,
                "quantity",
                {
                    "name": obj.Label,
                    "type": obj.type,
                    "unit": obj.unit,
                    "value": obj.value,
                },
            )


def createIsotopes(group):
    global materials
    for obj in group:
        # "ReactorMaterials" sub-group holds OpenMC-only isotopes — skip for GDML
        if _isReactorContainer(obj.Label):
            continue
        if isinstance(obj.Proxy, GDMLisotope):
            # print("GDML isotope")
            # item = ET.SubElement(materials,'isotope',{'N': str(obj.N), \
            #                                           'Z': str(obj.Z), \
            #                                           'name' : obj.Label})
            # ET.SubElement(item,'atom',{'unit': obj.unit, \
            #                           'value': str(obj.value)})
            item = ET.SubElement(materials, "isotope", {"name": obj.Label})
            processIsotope(obj, item)


def processGroup(obj):
    print("Process Group " + obj.Label)
    # print(obj.TypeId)
    # print(obj.Group)
    #      if hasattr(obj,'Group') :
    # return
    if hasattr(obj, "Group"):
        # print("   Object List : "+obj.Label)
        # print(obj)
        while switch(obj.Label):
            if case("Define"):
                # print("Constants")
                createDefine(obj.Group)
                break

            if case("Quantities"):
                # print("Quantities")
                createQuantities(obj.Group)
                break

            if case("Isotopes"):
                # print("Isotopes")
                createIsotopes(obj.Group)
                break

            if case("Elements"):
                # print("Elements")
                createElements(obj.Group)
                break

            if case("Materials"):
                print("Materials")
                createMaterials(obj.Group)
                break

            if case("Geant4"):
                # Do not export predefine in Geant4
                print("Geant4")
                break


from itertools import islice


def consume(iterator):
    next(islice(iterator, 2, 2), None)


def getDefaultMaterial():
    # should get this from GDML settings under "settings"
    # for now this does not exist, so simply put steel
    return "G4_STAINLESS-STEEL"


def getMaterial(obj):
    # Temporary fix until the SetMaterials works
    # Somehow (now Feb 20) if a new gdml object is added
    # the default material is Geant4, and SetMaterials fails to change it
    from .GDMLMaterials import getMaterialsList
    global usedGeant4Materials

    GDMLShared.trace("get Material : " + obj.Label)
    if hasattr(obj, "material"):
        material = obj.material
    elif hasattr(obj, "Tool"):
        GDMLShared.trace("Has tool - check Base")
        try:
            material = getMaterial(obj.Base)
        except Exception as e:
            print(e)
            print("Using default material")
            material = getDefaultMaterial()

    elif hasattr(obj, "Base"):
        GDMLShared.trace("Has Base - check Base")
        try:
            material = getMaterial(obj.Base)
        except Exception as e:
            print(e)
            print("Using default material")
            material = getDefaultMaterial()

    elif hasattr(obj, "Objects"):
        GDMLShared.trace("Has Objects - check Objects")
        try:
            material = getMaterial(obj.Objects[0])
        except Exception as e:
            print(e)
            print("Using default material")
            material = getDefaultMaterial()

    else:
        material = getDefaultMaterial()

    if material[0:3] == "G4_":
        print(f"Found Geant material {material}")
        usedGeant4Materials.add(material)
    elif _isReactorContainer(material):
        # The volume has been assigned the OpenMC container group name itself,
        # which has no GDML definition.  Substitute the default and warn.
        default = getDefaultMaterial()
        print(f"WARNING: volume '{obj.Label}' has material set to "
              f"'ReactorMaterials' (the container group, not a material) — "
              f"substituting {default} for GDML export")
        material = default
    elif _isReactorMaterial(material):
        # Material is a named entry inside Materials/ReactorMaterials (e.g.
        # TMZ, LBE).  Track it so postCreateReactorMaterials() exports its
        # definition on demand.
        usedReactorMaterials.add(material)

    return material


"""
def printObjectInfo(xmlVol, volName, xmlParent, parentName):
    print("Process Object : "+obj.Label+' Type '+obj.TypeId)
    if xmlVol is not None :
       xmlstr = ET.tostring(xmlVol)
    else :
       xmlstr = 'None'
    print('Volume : '+volName+' : '+str(xmlstr))
    if xmlParent is not None :
       xmlstr = ET.tostring(xmlParent)
    else :
       xmlstr = 'None'
    print('Parent : '+str(parentName)+' : '+str(xmlstr))
"""


def exportCone(name, radius, height):
    cylEl = ET.SubElement(
        solids,
        "cone",
        {
            "name": name,
            "rmin1": "0",
            "rmax1": str(radius),
            "rmin2": "0",
            "rmax2": str(radius),
            "z": str(height),
            "startphi": "0",
            "deltaphi": "360",
            "aunit": "deg",
            "lunit": "mm",
        },
    )
    return cylEl


def buildAssemblyTree(worldVol):
    from .AssemblyHelper import AssemblyHelper

    global AssemblyDict

    def processContainer(vol):
        objects = assemblyHeads(vol)
        imprNum = 1
        for obj in objects[1:]:
            # Skip objects suppressed from GDML export (e.g. source replaced by GmshTessellated)
            if not checkExportFlag(obj):
                continue
            print(
                f" buildAssemblyTree::processContainer {obj.Label} {obj.TypeId} "
            )
            processVolAssem(obj, imprNum)

    def processVolAssem(vol, imprNum):
        # vol - Volume Object
        # xmlParent - xml of this volume's Parent
        if vol.Label[:12] != "NOT_Expanded":
            if isContainer(vol):
                processContainer(vol)
            elif isAssembly(vol):
                processAssembly(vol, imprNum)
            elif vol.TypeId == "App::Link":
                processLink(vol, imprNum)
            else:
                print(
                    f"{vol.Label} is neither a link, nor an assembly nor a container"
                )

    def processLink(vol, imprNum):
        linkedObj = vol.getLinkedObject()
        if linkedObj.Label in AssemblyDict:
            entry = AssemblyDict[linkedObj.Label]
            instCnt = entry.www
            imprNum = entry.xxx + 1
            entry = AssemblyHelper(vol, instCnt, imprNum)
            AssemblyDict[vol.Label] = entry
        else:
            processVolAssem(linkedObj, imprNum)

    def processAssembly(vol, imprNum):
        print(f"{vol.Label} typeId= {vol.TypeId}")
        if hasattr(vol, "LinkedObject"):
            print(f"{vol.Label} has a LinkedObject")
            linkedObj = vol.getLinkedObject()
            if linkedObj.Label in AssemblyDict:
                entry = AssemblyDict[linkedObj.Label]
                instCnt = entry.www
                imprNum = entry.xxx + 1
        else:
            instCnt = AssemblyHelper.maxWww + 1
        entry = AssemblyHelper(vol, instCnt, imprNum)
        AssemblyDict[vol.Label] = entry
        assemObjs = assemblyHeads(vol)
        imprNum += 1
        for obj in assemObjs:
            # Skip objects suppressed from GDML export (e.g. source replaced by GmshTessellated)
            if not checkExportFlag(obj):
                continue
            print(
                f" buildAssemblyTree::processAssembly {obj.Label} {obj.TypeId} "
            )
            if obj.TypeId == "App::Part":
                processVolAssem(obj, imprNum)
            elif obj.TypeId == "App::Link":
                processLink(obj, imprNum)
            else:
                if SolidExporter.isSolid(obj):
                    entry.addSolid(obj)

    processContainer(worldVol)

    for k, v in AssemblyDict.items():
        print(f"Assembly: {k} av_{v.www}_impr_{v.xxx}")


def createXMLvolume(name):
    GDMLShared.trace("create xml volume : " + name)
    elem = ET.Element("volume", {"name": name})
    return elem


def createXMLassembly(name):
    GDMLShared.trace("create  xml assembly : " + name)
    elem = ET.Element("assembly", {"name": name})
    return elem


def invPlacement(placement):
    inv = placement.inverse()
    return inv
    # tra = inv.Base
    # rot = inv.Rotation
    # T = FreeCAD.Placement(tra, FreeCAD.Rotation())
    # R = FreeCAD.Placement(FreeCAD.Vector(), rot)
    # return R*T


def isArrayType(obj):
    obj1 = obj
    if obj.TypeId == "App::Link":
        obj1 = obj.LinkedObject
    if obj1.TypeId == "Part::FeaturePython":
        if not hasattr(obj1.Proxy, 'Type'):
            return False  # discovered that InvoluteGears don't have a 'Type'
        typeId = obj1.Proxy.Type
        if typeId == "Array":
            if obj1.ArrayType == "ortho":
                return True
            elif obj1.ArrayType == "polar":
                return True
        elif typeId == "PathArray":
            return True
        elif typeId == "PointArray":
            return True
        elif typeId == "Clone":
            clonedObj = obj1.Objects[0]
            return isArrayType(clonedObj)

        else:
            return False
    else:
        return False


def isArrayOfPart(obj):
    ''' test if the obj (an array) is an array of App::Part '''
    obj1 = obj
    if obj.TypeId == "App::Link":
        obj1 = obj.LinkedObject
    typeId = obj1.Proxy.Type
    if typeId == "Clone":
        clonedObj = obj1.Objects[0]
        return isArrayOfPart(clonedObj)
    else:
        return obj1.Base.TypeId == "App::Part"

def processArrayPart(array, xmlVol):
    # vol: array object
    global physVolStack
    from . import arrayUtils
    # vol: Array item
    # new approach 2024-08-07:
    # Create an assembly for the array. The assembly has the name of the array Part
    # place the repeated array elements in this new assembly and place
    # the array assembly in the xmlVol with the position and rotation of the array
    # xmlVol: xml item into which the array elements are placed/exported

    arrayRef = NameManager.getName(array)
    arrayXML = createXMLassembly(arrayRef)
    print(f"Process Array Part {array.Label} Base {array.Base} {xmlVol}")
    processVolAssem(array.Base, None, array.Base.Label)
    basePhysVol = physVolStack.pop()
    baseRotation = basePhysVol.placement.Rotation
    baseTranslation = basePhysVol.placement.Base

    arrayPos = array.Placement.Base
    arrayRot = array.Placement.Rotation
    
    parent = array.InList[0]
    print(f"parent {parent}")
    arrayType = arrayUtils.typeOfArray(array)
    while switch(arrayType):
        if case("ortho"):
            pos = basePhysVol.placement.Base
            print(f"basePhysVol: {basePhysVol.ref} position: {arrayPos}")
            placements = arrayUtils.placementList(array, offsetVector=pos, rot=baseRotation)
            print(f'Number of placements = {len(placements)}')
            for i, placement in enumerate(placements):
                ix, iy, iz = arrayUtils.orthoIndexes(i, array)
                baseName = array.Base.Label + '-' + str(ix) + '-' + str(iy) + \
                    '-' + str(iz)
                print(f"Base Name {baseName}")
                # print(f"Add Placement to {parent.Label} volref {vol.Base.Label}")
                addPhysVolPlacement(array.Base, arrayXML,
                                    placement, pvName=str(baseName))
            break

        if case("polar"):
            positionVector = baseRotation.inverted()*baseTranslation  # + vol.Placement.Base
            placements = arrayUtils.placementList(array, offsetVector=positionVector, rot=baseRotation)
            print(f'Number of placements = {len(placements)}')
            for i, placement in enumerate(placements):
                baseName = array.Base.Label + '-' + str(i)
                addPhysVolPlacement(array.Base, arrayXML,
                                    placement, pvName=str(baseName))
            break

        if case("PathArray") or case("PointArray"):
            pos = basePhysVol.placement.Base
            print(f"basePhysVol: {basePhysVol.ref} position: {arrayPos}")
            placements = arrayUtils.placementList(array, offsetVector=pos, rot=baseRotation)
            for i, placement in enumerate(placements):
                baseName = array.Base.Label + '-' + str(i)
                addPhysVolPlacement(array.Base, arrayXML,
                                    placement, pvName=str(baseName))
            break

    placement = array.Placement
    # if psPlacement is not None:
    #     placement = invPlacement(psPlacement) * placement
    addPhysVolPlacement(array, xmlVol, placement)
    physVolStack.append(PhysVolPlacement(array, placement))

    structure.append(arrayXML)
    # structure.append(xmlVol)


def processAssembly(vol, xmlVol, xmlParent, parentName, psPlacement):
    global structure
    global physVolStack

    # vol - Volume Object
    # xmlVol - xml of this assembly
    # xmlParent - xml of this volume's Parent
    # psPlacement: parent solid placement, may be None
    # App::Part will have Booleans & Multifuse objects also in the list
    # So for s in list is not so good
    # xmlVol could be created dummy volume

    # GDMLShared.setTrace(True)
    volName = NameManager.getVolumeName(vol)
    # GDMLShared.trace("Process Assembly : " + volName)
    # if GDMLShared.getTrace() == True :
    #   printVolumeInfo(vol, xmlVol, xmlParent, parentName)
    assemObjs = assemblyHeads(vol)
    #  print(f"ProcessAssembly: vol.TypeId {vol.TypeId}")
    print(f"ProcessAssembly: {vol.Name} Label {vol.Label}")
    print(f"Assem Objs {assemObjs}")
    #
    # Note that the assembly object is under an App::Part, not
    # a solid, so there is no need to adjust for a "parent solid"
    # placement.
    #
    for obj in assemObjs:
        # Skip objects suppressed from GDML export (e.g. source replaced by GmshTessellated)
        if not checkExportFlag(obj):
            continue
        if obj.TypeId == "App::Part":
            processVolAssem(obj, xmlVol, volName, None)
        elif obj.TypeId == "App::Link":
            print("Process Link")
            # PhysVol needs to be unique
            if hasattr(obj, "LinkedObject"):
                volRef = NameManager.getVolumeName(obj.LinkedObject)
            elif hasattr(obj, "VolRef"):
                volRef = obj.VolRef
            print(f"VolRef {volRef}")
            addPhysVolPlacement(obj, xmlVol, obj.Placement, refName=volRef)
            physVolStack.append(PhysVolPlacement(volName, obj.Placement))
        elif isArrayType(obj):
            processArrayPart(obj, xmlVol)
        else:
            _ = processVolume(obj, xmlVol, None)

    # the assembly could be placed in a container; adjust
    # for its placement, if any, given in the argument
    placement = vol.Placement
    if psPlacement is not None:
        placement = invPlacement(psPlacement) * placement
    addPhysVolPlacement(vol, xmlParent, placement)
    physVolStack.append(PhysVolPlacement(volName, placement))

    structure.append(xmlVol)


def processVolume(vol, xmlParent, psPlacement):

    global structure
    global physVolStack

    # vol - Volume Object
    # xmlParent - xml of this volume's Parent
    # App::Part will have Booleans & Multifuse objects also in the list
    # So for s in list is not so good
    # type 1 straight GDML type = 2 for GEMC
    # xmlVol could be created dummy volume
    # breakpoint()
    if vol.TypeId == "App::Link":
        print("Volume is Link")
        placement = vol.Placement
        if psPlacement is not None:
            placement = invPlacement(psPlacement) * placement

        addPhysVolPlacement(
            vol,
            xmlParent,
            placement)
        return

    volName = NameManager.getVolumeName(vol)

    if vol.TypeId == "App::Part":
        topObject = topObj(vol)
    else:
        topObject = vol
    if topObject is None:
        return

    if isMultiPlacement(topObject):
        xmlVol, volName = processMultiPlacement(topObject, xmlParent)
        partPlacement = topObject.Placement
        if psPlacement is not None:
            partPlacement = invPlacement(psPlacement) * partPlacement
    else:
        solidExporter = SolidExporter.getExporter(topObject)
        if solidExporter is None:
            return
        solidExporter.export()
        print(f"Process Volume - solids count {len(list(solids))}")
        # 1- adds a <volume element to <structure with name volName
        xmlVol = createXMLvolume(volName)
        # 2- add material info to the generated <volume pointed to by xmlVol
        addVolRef(xmlVol, volName, topObject, solidExporter.name())
        # 3- add a <physvol. A <physvol, can go under the <worlVol, or under
        #    a <assembly
        # first we need to convolve the solids placement, with the vols placement
        partPlacement = solidExporter.placement()
        if vol.TypeId == "App::Part":
            partPlacement = vol.Placement * partPlacement
            if psPlacement is not None:
                partPlacement = invPlacement(psPlacement) * partPlacement

    addPhysVolPlacement(vol, xmlParent, partPlacement, refName=volName)
    structure.append(xmlVol)
    physVolStack.append(PhysVolPlacement(volName, partPlacement))

    if hasattr(vol, "SensDet"):
        # SensDet could be enumeration of text value None
        if vol.SensDet != "None":
            print("Volume : " + volName)
            print("SensDet : " + vol.SensDet)
            ET.SubElement(
                xmlVol,
                "auxiliary",
                {"auxtype": "SensDet", "auxvalue": vol.SensDet},
            )
    if hasattr(vol, "SkinSurface"):
        print(f"SkinSurf Property : {vol.SkinSurface}")
        # SkinSurfface could be enumeration of text value None
        if vol.SkinSurface != "None":
            print("Need to export : skinsurface")
            ss = ET.Element(
                "skinsurface",
                {
                    "name": "skin" + vol.SkinSurface,
                    "surfaceproperty": vol.SkinSurface,
                },
            )
            ET.SubElement(ss, "volumeref", {"ref": volName})
            SurfaceManager.addSurface(ss)
    print(f"Processed Volume : {volName}")

    return xmlVol


def processContainer(vol, xmlParent, psPlacement):
    # vol: a container: a volume that has a solid that contains other volume
    # psPlacement: placement of parent solid. Could be None.
    #
    print(f"Process Container {vol.Label}")
    global structure
    global physVolStack

    volName = NameManager.getVolumeName(vol)
    objects = assemblyHeads(vol)
    newXmlVol = createXMLvolume(volName)
    solidExporter = SolidExporter.getExporter(objects[0])
    #print(f"solidExporter {objects[0].Label} {solidExporter}")
    solidExporter.export()
    addVolRef(newXmlVol, volName, objects[0], solidExporter.name())

    solidPlacement = solidExporter.placement()

    # for reasons I don't understand, perhaps, just floating point precision issue
    # I am getting partPlacement != vol.Placement even when solidPlacement is identity placement
    # So I have to test by hand. MMH
    if solidPlacement == FreeCAD.Placement():
        partPlacement = vol.Placement
    else:
        partPlacement = vol.Placement * solidPlacement

    #
    # Note that instead of testing for None, I could have
    # just used an identity placement which has an identity inverse
    #
    if psPlacement is not None:
        partPlacement = invPlacement(psPlacement) * partPlacement

    addPhysVolPlacement(vol, xmlParent, partPlacement)
    # N.B. the parent solid placement (psPlacement) only directly
    # affects vol, the container volume. All the daughters are placed
    # relative to that, so do not need the extra shift of psPlacement
    # directly.
    # However, if the container solid has a non-dentity placement
    # then the daughters need adjustment by that
    # The solid containing the daughter volumes has been exported above
    # so start at the next object.
    if solidPlacement == FreeCAD.Placement():
        # No adjustment of daughters needed
        myPlacement = None
    else:
        # adjust by our solids non-zero placement
        myPlacement = solidPlacement

    for obj in objects[1:]:
        # Skip objects suppressed from GDML export (e.g. source replaced by GmshTessellated)
        if not checkExportFlag(obj):
            continue
        if obj.TypeId == "App::Link":
            print("Process Link")
            if solidPlacement == FreeCAD.Placement():
                addPhysVolPlacement(obj, newXmlVol, obj.Placement)
            else:
                addPhysVolPlacement(
                    obj, newXmlVol,
                    invPlacement(solidPlacement) * obj.Placement)
        elif obj.TypeId == "App::Part":
            processVolAssem(obj, newXmlVol, volName, myPlacement)
        else:
            _ = processVolume(obj, newXmlVol, myPlacement)

    # Note that the placement of the container itself should be last
    # so it can be popped first if we are being called from an array
    physVolStack.append(PhysVolPlacement(volName, partPlacement))
    structure.append(newXmlVol)


def processVolAssem(vol, xmlParent, parentName, psPlacement=None):

    # vol - Volume Object
    # xmlParent - xml of this volume's Parent
    # psPlacement = parent solid placement.
    #               If the vol is placed inside a solid
    #               and that solid has a non-zero placement
    #               we need to shift vol by inverse of the psPlacement
    # breakpoint()
    if vol.Label[:12] != "NOT_Expanded":
        print(f"process VolAsm Name {vol.Name} Label {vol.Label}")
        volName = NameManager.getName(vol)
        if isContainer(vol):
            processContainer(vol, xmlParent, psPlacement)
        elif isAssembly(vol):
            newXmlVol = createXMLassembly(volName)
            processAssembly(vol, newXmlVol, xmlParent, parentName,
                            psPlacement)
        else:
            processVolume(vol, xmlParent, psPlacement)
    else:
        print("skipping " + vol.Label)


def printVolumeInfo(vol, xmlVol, xmlParent, parentName):
    if xmlVol is not None:
        xmlstr = ET.tostring(xmlVol)
    else:
        xmlstr = "None"
    print(xmlstr)
    GDMLShared.trace("     " + vol.Label + " - " + str(xmlstr))
    if xmlParent is not None:
        xmlstr = ET.tostring(xmlParent)
    else:
        xmlstr = "None"
    GDMLShared.trace("     Parent : " + str(parentName) + " : " + str(xmlstr))


def processMultiPlacement(obj, xmlParent):
    global childObjects
    print(f"procesMultiPlacement {obj.Label}")

    def getChildren(obj):
        children = []
        for o in childObjects[obj]:
            children.append(o)
            children += getChildren(o)

        return children

    children = [obj] + getChildren(obj)
    # export first solid in solids (booleans etc)
    for i, s in enumerate(children):
        if SolidExporter.isSolid(s):
            exporter = SolidExporter.getExporter(s)
            exporter.export()
            solidName = exporter.name()
            volName = "LV_" + solidName
            volXML = createXMLvolume(volName)
            structure.append(volXML)
            addVolRef(volXML, obj.Label, s, solidName)
            addPhysVolPlacement(s, xmlParent, exporter.placement(), refName=volName)
            break
    placers = children[:i]  # placers without the solids
    j = len(placers)
    for pl in reversed(placers):
        j -= 1
        placer = MultiPlacer.getPlacer(pl)
        placer.place(volName)
        volName = placer.name()
        volXML = placer.xml()
        structure.append(volXML)
        if j != 0:
            addPhysVolPlacement(pl, xmlParent, pl.Placement, refName=volName)

    return volXML, volName  # name of last placer (an assembly)


def createWorldVol(volName):
    print("Need to create Dummy Volume and World Box ")
    bbox = FreeCAD.BoundBox()
    boxName = defineWorldBox(bbox)
    worldVol = ET.SubElement(structure, "volume", {"name": volName})
    ET.SubElement(worldVol, "materialref", {"ref": "G4_AIR"})
    ET.SubElement(worldVol, "solidref", {"ref": boxName})
    ET.SubElement(gxml, "volume", {"name": volName, "material": "G4_AIR"})
    return worldVol


def buildDocTree():
    # _MODEL_DOCTREE_ : build childObjects from the document model, not the GUI
    # tree widget's selection.  claimChildren() is what populates the model tree
    # (including boolean Base/Tool and App::Part groups); walking it here makes
    # the export self-contained and re-runnable (the old code scraped
    # QTreeWidget.selectedItems(), which is empty/stale on a re-run).
    global childObjects
    childObjects = {}  # dictionary of list of child objects for each object
    skippedTypes = ["App::Origin", "Sketcher::SketchObject", "Part::Compound"]

    def childrenOf(obj):
        kids = []
        try:
            vo = getattr(obj, "ViewObject", None)
            if vo is not None:
                kids = vo.claimChildren() or []
        except Exception:
            kids = []
        if not kids:
            kids = getattr(obj, "Group", []) or []
        return kids

    def addDaughters(obj):
        if obj in childObjects:      # already processed (also breaks cycles)
            return
        childObjects[obj] = []
        for child in childrenOf(obj):
            if child is None or child.TypeId in skippedTypes:
                continue
            childObjects[obj].append(child)
            addDaughters(child)

    # world volume is the App::Part selected for export
    sel = FreeCADGui.Selection.getSelection()
    worldObj = sel[0] if sel else None
    if worldObj is None:
        return
    addDaughters(worldObj)


def isContainer(obj):
    # return True if The App::Part is of the form:
    # App::Part
    #     -solid (Part:xxx)
    #     -App::Part
    #     -App::Part
    #     ....
    # So a container satisfies the current isAssembly requirements
    # plus the siblings must have the above form
    # obj that satisfy isContainer get exported as
    # <volume ....>
    #   <solidref = first solid
    #   <physvol ..ref to first App::Part>
    #   <physvol ..ref to second App::Part>
    # </volume>
    #
    # This is in contract to assembly, which is exported as
    # <assembly
    #   <physvol 1>
    #   <physvol 2>
    #   ....
    #
    # Must be assembly first
    global childObjects

    if not isAssembly(obj):
        return False
    heads = assemblyHeads(obj)
    if heads is None:
        return False
    if len(heads) < 2:
        return False

    # first must be solid
    if not SolidExporter.isSolid(heads[0]):
        return False

    # we cannot have an array as the containing solid of a container
    if isArrayType(heads[0]):
        return False

    # rest must not be solids, but only second is tested here
    if SolidExporter.isSolid(heads[1]):
        return False

    return True


# is the object something we export as a Volume, or Assembly or a solid?
def isGeometryExport(obj):
    return obj.TypeId == "App::Part" or SolidExporter.isSolid(obj)


def isAssembly(obj):
    # return True if obj is an assembly.
    # To be an assembly the obj must be:
    # (1) an App::Part or an App::Link and
    # (2) it has either (1) At least one App::Part as a subpart or
    #                   (2) more than one "terminal" object
    # A terminal object is one that has associated with it ONE volume
    # A volume refers to ONE solid
    # A terminal item CAN be a boolean, or an extrusion (and in the future
    # a chamfer or a fillet. So a terminal element need NOT have an empty
    # child list
    # N.B. App::Link is treated as a non-assembly, even though it might be linked
    # to an assembly, because all we need to place it is the volref of its link

    global childObjects

    print(f"testing isAsembly for: {obj.Label}")
    if obj.TypeId != "App::Part":
        return False

    for ob in childObjects[obj]:
        if ob.TypeId == "App::Part" or ob.TypeId == "App::Link":
            print(True)
            return True  # Yes, even if ONE App::Part is under this, we treat it as an assembly

    if len(childObjects[obj]) > 1:
        print("Yes, it is an Assembly")
        return True
    else:
        # need to check for arrays. Arrays of App::Part are treated as an assembly
        if len(childObjects[obj]) == 1:
            topObject = childObjects[obj][0]
            if isArrayType(topObject) and isArrayOfPart(topObject):
                return True
            else:
                return False
        else:
            return False


def assemblyHeads(obj):
    # return a list of subassembly heads for this object
    # Subassembly heads are themselves either assemblies
    # or terminal objects (those that produce a <volume and <physvol)
    global childObjects

    return childObjects[obj]


def checkExportFlag(obj):
    if hasattr(obj, "exportFlag"):
        return obj.exportFlag
    else:
        return True


def topObj(obj):
    # The topmost object in an App::Part
    # The App::Part is assumed NOT to be an assembly
    global childObjects

    if isAssembly(obj):
        print(f"***** Non Assembly expected  for {obj.Label}")
        return

    if len(childObjects[obj]) == 0:
        return obj
    else:
        return childObjects[obj][0]


def isMultiPlacement(obj):
    return obj.TypeId == "Part::Mirroring"


def checkGDML(Obj):
    if hasattr(Obj, "Proxy"):
        if hasattr(Obj.Proxy, "Type"):
            if Obj.Proxy.Type[:4] == "GDML":
                return True
    return False


def countGDMLObj(Obj):
    # Return counts of Volume, GDML objects exportables
    # GDMLShared.trace("countGDMLObj")
    global childObjects

    vCount = lCount = gCount = 0
    for obj in Obj.OutList:
        # print(obj.Label, obj.TypeId)
        if hasattr(obj, "exportFlag"):
            if obj.exportFlag is False:
                continue
        if (
            obj.TypeId == "Part::Cut"
            or obj.TypeId == "Part::Fuse"
            or obj.TypeId == "Part::Common"
        ):
            gCount -= 1
        if hasattr(obj, "LinkedObject"):
            obj = obj.LinkedObject
            if obj.TypeId == "App::Part":
                lCount += 1
            elif checkGDML(obj):
                lCount += 1
        else:
            if obj.TypeId == "App::Part":
                vCount += 1
            elif checkGDML(obj):
                gCount += 1

    # print("countGDMLObj - Count : " + str(gCount))
    # GDMLShared.trace("countGDMLObj - gdml : " + str(gCount))
    return vCount, lCount, gCount


def checkGDMLstructure(obj):
    # Should be
    # World Vol - App::Part
    # App::Origin
    # GDML Object
    global childObjects

    GDMLShared.trace("check GDML structure")
    GDMLShared.trace(obj)
    print("check GDML structure")
    vCount, lCount, gCount = countGDMLObj(obj)
    print(f"GDML Counts : {vCount} {gCount}")
    if gCount > 1:  # More than one GDML Object need to insert Dummy
        return False
    if (
        gCount == 1 and len(obj.OutList) == 2
    ):  # Just a single GDML obj insert Dummy
        return False
    return True


def locateXMLvol(vol):
    global structure
    xmlVol = structure.find("volume[@name='%s']" % vol.Label)
    return xmlVol


def exportWorldVol(vol, fileExt):
    global childObjects
    global WorldVOL

    WorldVOL = vol.Label
    if fileExt != ".xml":
        print("Export World Process Volume : " + vol.Label)
        GDMLShared.trace("Export Word Process Volume" + vol.Label)
        ET.SubElement(setup, "world", {"ref": vol.Label})

        if checkGDMLstructure(vol) is False:
            GDMLShared.trace("Insert Dummy Volume")
            createXMLvolume("dummy")
            xmlParent = createWorldVol(vol.Label)
            parentName = vol.Label
            addPhysVol(xmlParent, "dummy")
        else:
            GDMLShared.trace("Valid Structure")
            xmlParent = None
            parentName = None
    else:
        xmlParent = None
        parentName = None

    # print(vol.OutList)
    vCount, lCount, gCount = countGDMLObj(vol)
    print(f"Root GDML Counts {vCount} {gCount}")

    # Munther Please check/correct
    # if gCount  > 0:  # one GDML defining world volume
    #    if isAssembly(vol):
    #        heads = assemblyHeads(vol)
    #        worlSolid = heads[0]
    #        xmlVol = processVolume(worlSolid, xmlParent, volName=WorldVOL)
    #        for obj in heads[1:]:  # skip first volume (done above)
    #            processVolAssem(obj, xmlVol, WorldVOL)
    #    else:
    #        xmlVol = processVolume(vol, xmlParent)
    # else:  # no volume defining world
    #    xmlVol = createXMLassembly(vol.Label)
    #    processAssembly(vol, xmlVol, xmlParent, parentName)

    # The world volume does not have a parent

    buildAssemblyTree(vol)
    processVolAssem(vol, xmlParent, WorldVOL)

    SurfaceManager.processSkinSurfaces()
    SurfaceManager.processBorderSurfaces()


def exportElementAsXML(dirPath, fileName, flag, elemName, elem):
    # gdml is a global
    global gdml, docString, importStr
    if elem is not None:
        # xmlElem = ET.Element('xml')
        # xmlElem.append(elem)
        # indent(xmlElem)
        if flag is True:
            filename = fileName + "-" + elemName + ".xml"
        else:
            filename = elemName + ".xml"
        # ET.ElementTree(xmlElem).write(os.path.join(dirPath,filename))
        ET.ElementTree(elem).write(os.path.join(dirPath, filename))
        docString += "<!ENTITY " + elemName + ' SYSTEM "' + filename + '">\n'
        gdml.append(ET.Entity(elemName))


def exportGDMLstructure(dirPath, fileName):
    global gdml, docString, importStr
    print("Write GDML structure to Directory")
    gdml = initGDML()
    docString = "\n<!DOCTYPE gdml [\n"
    # exportElementAsXML(dirPath, fileName, False, 'constants',constants)
    exportElementAsXML(dirPath, fileName, False, "define", define)
    exportElementAsXML(dirPath, fileName, False, "materials", materials)
    exportElementAsXML(dirPath, fileName, True, "solids", solids)
    exportElementAsXML(dirPath, fileName, True, "structure", structure)
    exportElementAsXML(dirPath, fileName, False, "setup", setup)
    print(f"setup : {setup}")
    docString += "]>\n"
    # print(docString)
    # print(len(docString))
    # gdml = ET.fromstring(docString.encode("UTF-8"))
    indent(gdml)
    ET.ElementTree(gdml).write(
        os.path.join(dirPath, fileName + ".gdml"),
        doctype=docString.encode("UTF-8"),
    )
    print("GDML file structure written")


def exportGDML(first, filepath, fileExt):
    from . import GDMLShared
    from sys import platform
    from .AssemblyHelper import AssemblyHelper

    global zOrder
    global AssemblyDict
    AssemblyDict = {}
    AssemblyHelper.maxWww = 0

    global usedGeant4Materials
    usedGeant4Materials = set()

    global usedReactorMaterials
    usedReactorMaterials = set()

    global physVolStack
    physVolStack = []

    # GDMLShared.setTrace(True)
    GDMLShared.trace("exportGDML")
    print("====> Start GDML Export 2.1")
    branch = get_active_branch_name()
    print(f"branch: {branch}")
    print("File extension : " + fileExt)

    GDMLstructure()
    zOrder = 1
    processMaterials()
    exportWorldVol(first, fileExt)
    params = FreeCAD.ParamGet(
        "User parameter:BaseApp/Preferences/Mod/GDML"
    )
    exportG4Materials = params.GetBool('exportG4Materials', False)
    if exportG4Materials:
        postCreateGeantMaterials()
    # Export any reactor materials actually referenced by volumes (rare —
    # only when the user has deliberately assigned a ReactorMaterials material
    # to a GDML object).  Must run after volumes so usedReactorMaterials is
    # fully populated, and before _fixMissingIsotopes so isotope gaps are
    # caught in the same post-pass.
    postCreateReactorMaterials()
    # Single post-pass: fill any isotope definitions missing from elements.
    _fixMissingIsotopes()
    processOpticals()
    # format & write GDML file
    # xmlstr = ET.tostring(structure)
    # print('Structure : '+str(xmlstr))
    if fileExt == ".gdml":
        # indent(gdml)
        print(len(list(solids)))
        print("Write to gdml file")
        # ET.ElementTree(gdml).write(filepath, 'utf-8', True)
        # ET.ElementTree(gdml).write(filepath, xml_declaration=True)
        # Problem with pretty Print on Windows ?
        if platform == "win32":
            indent(gdml)
            ET.ElementTree(gdml).write(filepath, xml_declaration=True, encoding='UTF-8')
        else:
            ET.ElementTree(gdml).write(
                filepath, pretty_print=True, xml_declaration=True,
                encoding='UTF-8'
            )
        print("GDML file written")

    if fileExt == ".GDML":
        filePath = os.path.split(filepath)
        print("Input File Path : " + filepath)
        fileName = os.path.splitext(filePath[1])[0]
        print("File Name : " + fileName)
        dirPath = os.path.join(filePath[0], fileName)
        print("Directory Path : " + dirPath)
        if os.path.exists(dirPath) is False:
            if os.path.isdir(dirPath) is False:
                os.makedirs(dirPath)
        if os.path.isdir(dirPath) is True:
            exportGDMLstructure(dirPath, fileName)
        else:
            print("Invalid Path")
            # change to Qt Warning

    if fileExt == ".xml":
        xmlElem = ET.Element("xml")
        xmlElem.append(solids)
        xmlElem.append(structure)
        indent(xmlElem)
        ET.ElementTree(xmlElem).write(filepath)
        print("XML file written")


def exportGDMLworld(first, filepath, fileExt):
    # global childObjects
    # childObjects = {}  # dictionary of list of child objects for each object
    # buildDocTree now creates global childObjects 

    buildDocTree()  # creates global childObjects
    NameManager.init()
    SolidExporter.init()

    # for debugging doc tree
    for obj in childObjects:
        s = ""
        for child in childObjects[obj]:
            s += child.Label + ", "
        print(f"{obj.Label} [{s}]")

    if filepath.lower().endswith(".gdml"):
        # GDML Export
        print("GDML Export")
        # if hasattr(first,'InList') :
        #   print(len(first.InList))

        vCount, lcount, gCount = countGDMLObj(first)
        if gCount > 1:
            from .GDMLQtDialogs import showInvalidWorldVol

            showInvalidWorldVol()
        else:
            exportGDML(first, filepath, fileExt)


def hexInt(f):
    return hex(int(f * 255))[2:].zfill(2)


def formatPosition(pos):
    s = str(pos[0]) + "*mm " + str(pos[1]) + "*mm " + str(pos[2]) + "*mm"
    print(s)
    return s


def scanForStl(first, gxml, path, flag):
    from .GDMLColourMap import lookupColour
    global childObjects

    # if flag == True ignore Parts that convert
    print("scanForStl")
    print(first.Name + " : " + first.Label + " : " + first.TypeId)
    while switch(first.TypeId):

        if case("App::Origin"):
            # print("App Origin")
            return

        if case("App::GeoFeature"):
            # print("App GeoFeature")
            return

        if case("App::Line"):
            # print("App Line")
            return

        if case("App::Plane"):
            # print("App Plane")
            return

        break

    if flag is True:
        #
        #  Now deal with objects that map to GDML solids
        #
        while switch(first.TypeId):
            if case("Part::FeaturePython"):
                return

            if case("Part::Box"):
                print("    Box")
                return

            if case("Part::Cylinder"):
                print("    Cylinder")
                return

            if case("Part::Cone"):
                print("    Cone")
                return

            if case("Part::Sphere"):
                print("    Sphere")
                return

            break

    # Deal with Booleans which will have Tool
    if hasattr(first, "Tool"):
        print(first.TypeId)
        scanForStl(first.Base, gxml, path, flag)
        scanForStl(first.Tool, gxml, path, flag)

    for obj in childObjects[first]:
        scanForStl(obj, gxml, path, flag)

    if first.TypeId != "App::Part":
        if hasattr(first, "Shape"):
            print("Write out stl")
            print(
                "===> Name : "
                + first.Name
                + " Label : "
                + first.Label
                + " \
            Type :"
                + first.TypeId
                + " : "
                + str(hasattr(first, "Shape"))
            )
            newpath = os.path.join(path, first.Label + ".stl")
            print("Exporting : " + newpath)
            first.Shape.exportStl(newpath)
            # Set Defaults
            colHex = "ff0000"
            mat = "G4Si"
            if FreeCAD.GuiUp and hasattr(first, "ViewObject") and hasattr(first.ViewObject, "ShapeColor"):
                # print(dir(first))
                col = first.ViewObject.ShapeColor
                colHex = hexInt(col[0]) + hexInt(col[1]) + hexInt(col[2])
                print("===> Colour " + str(col) + " " + colHex)
                mat = lookupColour(col)
                print("Material : " + mat)
                if hasattr(first, "Placement"):
                    print(first.Placement.Base)
                    pos = formatPosition(first.Placement.Base)
                    ET.SubElement(
                        gxml,
                        "volume",
                        {
                            "name": first.Label,
                            "color": colHex,
                            "material": mat,
                            "position": pos,
                        },
                    )


def exportGXML(first, path, flag):
    print("Path : " + path)
    # basename = 'target_'+os.path.basename(path)
    gxml = ET.Element("gxml")
    print("ScanForStl")
    scanForStl(first, gxml, path, flag)
    # format & write gxml file
    indent(gxml)
    print("Write to gxml file")
    # ET.ElementTree(gxml).write(os.path.join(path,basename+'.gxml'))
    ET.ElementTree(gxml).write(os.path.join(path, "target_cad.gxml"))
    print("gxml file written")


def exportMaterials(first, filename):
    if filename.lower().endswith(".xml"):
        print("Export Materials to XML file : " + filename)
        xml = ET.Element("xml")
        global define
        define = ET.SubElement(xml, "define")
        global materials
        materials = ET.SubElement(xml, "materials")
        processMaterials()
        indent(xml)
        ET.ElementTree(xml).write(filename)
    else:
        print("File extension must be xml")


def exportOpticals(first, filename):
    if filename.lower().endswith(".xml"):
        print("Export Opticals to XML file : " + filename)
        xml = ET.Element("xml")
        global define
        define = ET.SubElement(xml, "define")
        global solids
        solids = ET.SubElement(xml, "solids")
        processOpticals()
        indent(xml)
        ET.ElementTree(xml).write(filename)
    else:
        print("File extension must be xml")


def create_gcard(path, flag):
    basename = os.path.basename(path)
    print("Create gcard : " + basename)
    print("Path : " + path)
    gcard = ET.Element("gcard")
    ET.SubElement(gcard, "detector", {"name": "target_cad", "factory": "CAD"})
    if flag is True:
        ET.SubElement(
            gcard, "detector", {"name": "target_gdml", "factory": "GDML"}
        )
    indent(gcard)
    path = os.path.join(path, basename + ".gcard")
    ET.ElementTree(gcard).write(path)


def checkDirectory(path):
    if not os.path.exists(path):
        print("Creating Directory : " + path)
        os.mkdir(path)

def exportGEMC(first, path, flag):
    # flag = True  GEMC - GDML
    # flag = False just CAD
    global gxml

    print("Export GEMC")
    # basename = os.path.basename(path)
    print(path)
    print(flag)
    checkDirectory(path)
    # Create CAD directory
    cadPath = os.path.join(path, "cad")
    checkDirectory(cadPath)
    # Create gcard
    create_gcard(path, flag)
    exportGXML(first, cadPath, flag)
    if flag is True:
        print("Create GDML directory")
        gdmlPath = os.path.join(path, "gdml")
        checkDirectory(gdmlPath)
        # gdmlFilePath  = os.path.join(gdmlPath,basename+'.gdml')
        gdmlFilePath = os.path.join(gdmlPath, "target_gdml.gdml")
        exportGDML(first, gdmlFilePath, "gdml")
        # newpath = os.path.join(gdmlPath,basename+'.gxml')
        newpath = os.path.join(gdmlPath, "target_gdml.gxml")
        indent(gxml)
        ET.ElementTree(gxml).write(newpath)


def export(exportList, filepath):
    "called when FreeCAD exports a file"
    global refPlacement

    refPlacement = {}  # a dictionary of name as key, and placement as value
    # the name could that of <solid, an <assembly, or a <physvol

    first = exportList[0]
    print(f"Export Volume: {first.Label}")

    import os

    path, fileExt = os.path.splitext(filepath)
    print("filepath : " + path)
    print("file extension : " + fileExt)

    if fileExt.lower() == ".gdml":
        # import cProfile, pstats
        # profiler = cProfile.Profile()
        # profiler.enable()

        if first.TypeId == "App::Part":
            exportGDMLworld(first, filepath, fileExt)
        #
        # elif first.Label == "Materials":
        #    exportMaterials(first, filepath)

        else:
            print("Needs to be a Part for export")
            from PySide import QtGui

            QtGui.QMessageBox.critical(
                None, "Need to select a Part for export", "Need to select Part of GDML Volume to be exported \n\n Press OK to return"
            )
        # profiler.disable()
        # stats = pstats.Stats(profiler).sort_stats('cumtime')
        # stats.print_stats()

    elif fileExt.lower() == ".xml":
        if first.Label == "Materials":
            exportMaterials(first, filepath)

        elif first.Label == "Opticals":
            exportOpticals(first, filepath)

        else:
            print("Export XML structure & solids")
            exportGDML(first, filepath, ".xml")

    elif fileExt == ".gemc":
        exportGEMC(first, path, False)

    elif fileExt == ".GEMC":
        exportGEMC(first, path, True)

#
# -------------------------------------------------------------------------------------------------------
#


class SolidExporter:
    # Abstract class to export object as gdml
    _exported = []  # a list of already exported objects
    solidExporters = {
        "GDMLArb8": "GDMLArb8Exporter",
        "GDMLBox": "GDMLBoxExporter",
        "GDMLCone": "GDMLConeExporter",
        "GDMLcutTube": "GDMLcutTubeExporter",
        "GDMLElCone": "GDMLElConeExporter",
        "GDMLEllipsoid": "GDMLEllipsoidExporter",
        "GDMLElTube": "GDMLElTubeExporter",
        "GDMLHype": "GDMLHypeExporter",
        "GDMLOrb": "GDMLOrbExporter",
        "GDMLPara": "GDMLParaExporter",
        "GDMLParaboloid": "GDMLParaboloidExporter",
        "GDMLPolycone": "GDMLPolyconeExporter",
        "GDMLGenericPolycone": "GDMLGenericPolyconeExporter",
        "GDMLPolyhedra": "GDMLPolyhedraExporter",
        "GDMLGenericPolyhedra": "GDMLGenericPolyhedraExporter",
        "GDMLSphere": "GDMLSphereExporter",
        "GDMLTessellated": "GDMLTessellatedExporter",
        "GDMLSampledTessellated": "GDMLSampledTessellatedExporter",
        # Use the GDMLTessellated exporter",
        "GDMLGmshTessellated": "GDMLTessellatedExporter",
        "GDMLTetra": "GDMLTetraExporter",
        "GDMLTetrahedron": "GDMLTetrahedronExporter",
        "GDMLTorus": "GDMLTorusExporter",
        "GDMLTrap": "GDMLTrapExporter",
        "GDMLTrd": "GDMLTrdExporter",
        "GDMLTube": "GDMLTubeExporter",
        "GDMLTwistedbox": "GDMLTwistedboxExporter",
        "GDMLTwistedtrap": "GDMLTwistedtrapExporter",
        "GDMLTwistedtrd": "GDMLTwistedtrdExporter",
        "GDMLTwistedtubs": "GDMLTwistedtubsExporter",
        "GDMLXtru": "GDMLXtruExporter",
        "Mesh::Feature": "GDMLMeshExporter",
        "Part::MultiFuse": "MultiFuseExporter",
        "Part::Extrusion": "ExtrusionExporter",
        "Part::Revolution": "RevolutionExporter",
        "Part::Box": "BoxExporter",
        "Part::Cylinder": "CylinderExporter",
        "Part::Cone": "ConeExporter",
        "Part::Sphere": "SphereExporter",
        "Part::Cut": "BooleanExporter",
        "Part::Fuse": "BooleanExporter",
        "Part::Common": "BooleanExporter",
        "Part::Fillet": "AutoTessellateExporter",
        "Part::Chamfer": "AutoTessellateExporter",
        "Part::Loft": "AutoTessellateExporter",
        "Part::Sweep": "AutoTessellateExporter"
    }

    @staticmethod
    def init():
        SolidExporter._exported = []

    @staticmethod
    def isSolid(obj):
        print(f"isSolid {obj.Label}")
        # return hasattr(obj, 'Shape')  # does not work. App::Parts have Shape, but they are not solids!

        obj1 = obj
        if obj.TypeId == "App::Link":
            obj1 = obj.LinkedObject
        if obj1.TypeId == "Part::FeaturePython":
            return True  # All Part::FeturePython have a 'Shape', and a Shape can be tessellated
            '''
            typeId = obj1.Proxy.Type
            if typeId == "Array":
                if obj1.ArrayType == "ortho":
                    return True
                elif obj1.ArrayType == "polar":
                    return True
            elif typeId == "PathArray":
                return True
            elif typeId == "PointArray":
                return True
            elif typeId == "Clone":
                clonedObj = obj1.Objects[0]
                return SolidExporter.isSolid(clonedObj)

            else:
                return obj1.Proxy.Type in SolidExporter.solidExporters
            '''

        else:
            # Munther REVIEW
            #return obj1.TypeId in SolidExporter.solidExporters
            return obj.TypeId in SolidExporter.solidExporters



    @staticmethod
    def getExporter(obj):
        # Munther Review
        # Extra Test case simple_array_expanded
        if hasattr(obj, "LinkedObject"):
            return SolidExporter.getExporter(obj.LinkedObject)
        if obj.TypeId == "Part::FeaturePython":
            if hasattr(obj.Proxy, 'Type'):
                typeId = obj.Proxy.Type
                if typeId == "Array":
                    if obj.ArrayType == "ortho":
                        return OrthoArrayExporter(obj)
                    elif obj.ArrayType == "polar":
                        return PolarArrayExporter(obj)
                elif typeId == "PathArray":
                    return PathArrayExporter(obj)
                elif typeId == "PointArray":
                    return PointArrayExporter(obj)
                elif typeId == "Clone":
                    return CloneExporter(obj)
            else:
                typeId = obj.TypeId
        else:
            typeId = obj.TypeId

        if typeId in SolidExporter.solidExporters:
            classname = SolidExporter.solidExporters[typeId]
            # kludge for classes imported from another module
            # globals["RevolutionExporter"] returns key error
            if classname == "ExtrusionExporter":
                return ExtrusionExporter(obj)
            elif classname == "RevolutionExporter":
                return RevolutionExporter(obj)
            else:
                print(f"classname {classname}")
                klass = globals()[classname]
                return klass(obj)
        elif obj.TypeId == "Part::FeaturePython":  # This may appear to be duplication of above, but
                                                   # we need to pass through all the specialized exporters
                                                   # before we fall back to tessellation
            return AutoTessellateExporter(obj)
        else:
            print(f"{obj.Label} does not have a Solid Exporter")
            return None

    def __init__(self, obj):
        self.obj = obj
        self._name = NameManager.getName(obj)

    def name(self):
        return self._name

    def position(self):
        return self.obj.Placement.Base

    def rotation(self):
        return self.obj.Placement.Rotation

    def placement(self):
        return FreeCAD.Placement(self.position(), self.rotation())

    def exported(self):
        return self.obj in SolidExporter._exported

    def export(self):
        if not self.exported():
            SolidExporter._exported.append(self.obj)
        return

    def hasScale(self):
        return hasattr(self.obj, "scale") or hasattr(self.obj, "Scale")

    def getScale(self):
        if hasattr(self.obj, "ScaleVector"):
            return self.obj.ScaleVector
        elif hasattr(self.obj, "scale"):
            return self.obj.scale
        elif hasattr(self.obj, "Scale"):
            return self.obj.Scale
        else:
            return FreeCAD.vector(1, 1, 1)

    def _exportScaled(self):
        if self.hasScale():
            scale = self.getScale()
            if scale.x == 1.0 and scale.y == 1.0 and scale.z == 1.0:
                return
            xml = ET.SubElement(
                solids, "scaledSolid", {"name": self._name + "_scaled"}
            )
            ET.SubElement(xml, "solidref", {"ref": self.name()})
            ET.SubElement(
                xml,
                "scale",
                {
                    "name": self.name() + "_scale",
                    "x": str(scale.x),
                    "y": str(scale.y),
                    "z": str(scale.z),
                },
            )
            self._name += "_scaled"


class CloneExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)
        self._position = self.obj.Placement.Base
        self._rotation = self.obj.Placement.Rotation

    def position(self):
        return self._position

    def rotation(self):
        return self._rotation

    def getScale(self):
        if self.hasScale():
            # For rotation first, followed by scaling, the scaling would
            # need to change: Looking for scaling S', such that
            # S*R v = R*S' v ==>
            # S' = R^-1 * S * R
            #
            # s = FreeCAD.Matrix()
            # s.scale(self.obj.Scale.x, self.obj.Scale.y, self.obj.Scale.z)
            # rot = FreeCAD.Rotation(self.rotation())
            # rot.Angle = -rot.Angle
            # sprime = rot.inverted()*s*rot
            # return FreeCAD.Vector(sprime.A11, sprime.A22, sprime.A33)
            #
            # For scaling then rotating
            return self.obj.Scale
        else:
            return FreeCAD.Vector(1, 1, 1)

    def export(self):
        if len(self.obj.Objects) == 1:
            self._export1(self.obj.Objects[0])
            return

        # Here deal with scaling multi objects:
        # Make a multiunion of all the objects, then scale that
        exporters = []
        for obj in self.obj.Objects:
            exporter = SolidExporter.getExporter(obj)
            exporter.export()
            exporters.append(exporter)

        unionXML = ET.SubElement(solids, "multiUnion", {"name": self.name()})
        for i, exporter in enumerate(exporters):
            volRef = exporter.name()
            nodeName = f"{self.name()}_{i}"
            nodeXML = ET.SubElement(
                unionXML, "multiUnionNode", {"name": nodeName}
            )
            ET.SubElement(nodeXML, "solid", {"ref": volRef})
            exportPosition(nodeName, nodeXML, exporter.position())
            rot = FreeCAD.Rotation(exporter.rotation())
            # for reasons that I don't understand, in booleans and multiunions
            # angle is NOT reversed, so undo reversal of exportRotation
            exportRotation(nodeName, nodeXML, rot, invertRotation=False)

        self._exportScaled()

    def _export1(self, clonedObj):
        # for now we only deal with one cloned object
        clonedObj = self.obj.Objects[0]
        exporter = SolidExporter.getExporter(clonedObj)
        exporter.export()
        # The scaling of the position turns out to be more complicated
        # than I first thought (MMH). Draft->scale scales the position of the
        # the cloned object, i.e., the clone has a placement that already
        # includes the scaling of the placement of the cloned object, so it is
        # not necessary to repeat the scaling. HOWEVER, for several of the
        # objects we deal with, the position that is
        # exported to the gdml IS NOT obj.Placement. For example, a regular box
        # as its origin at corner, whereas a gdml box has its origin at the
        # center, so we take that into account on export by adding a shift by
        # half of each dimension. Draft/scale will scale the
        # cube.Placement, which is (0,0,0), so nothing happens. The solution:
        # get the clone position, unscale it, then get the exporter.position(),
        # and then scale THAT. Note that once an object has been cloned, the
        # clone no longer keeps track of the objects POSITION, but it does
        # keep track of its dimensions. So if the object is doubles in size,
        # the (scaled) double will change, but if the object is MOVED, the
        # clone will not change its position! So the following algorithm, would
        # fail. There is no way to know if the difference between the scaled
        # position and the clone's position is due to the clone moving or the
        # object moving.
        clonedPlacement = FreeCAD.Placement(
            exporter.placement()
        )  # copy the placement
        m = clonedPlacement.Matrix
        invRotation = FreeCAD.Placement(m.inverse()).Rotation
        clonedPosition = clonedPlacement.Base
        clonedRotation = clonedPlacement.Rotation
        # unrotate original position
        r1 = invRotation * clonedPosition
        objPosition = FreeCAD.Vector(clonedObj.Placement.Base)
        if self.hasScale():
            scale = self.obj.Scale
            r1.scale(scale.x, scale.y, scale.z)
            delta = self.obj.Placement.Base - objPosition.scale(
                scale.x, scale.y, scale.z
            )
        else:
            delta = self.obj.Placement.Base - objPosition
        objRotation = FreeCAD.Rotation(clonedObj.Placement.Rotation)
        myRotation = self.obj.Placement.Rotation
        # additional rotation of clone
        objRotation.invert()
        additionalRotation = myRotation * objRotation
        desiredRotation = additionalRotation * clonedRotation
        r2 = desiredRotation * r1
        # if neither clone not original have moved, delta should be zero
        # If it is not, there is no way to know which moved, but we are working
        # on the assumption only clone moved
        # same consideration for rotations. Draft scale copies the obj.Placement.Rotation
        # But that is not necessarily the exporters rotation (e.g. extruded ellipses
        # rotation depends on orientation of ellipse). Further, the clone itself
        # could have an extra rotation.
        print(r2, delta)
        clonedPosition = r2 + delta
        placement = FreeCAD.Placement(clonedPosition, desiredRotation)

        self._position = placement.Base
        self._rotation = placement.Rotation
        self._name = exporter.name()
        self._exportScaled()


class BoxExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        if self.exported():
            return
        super().export()

        ET.SubElement(
            solids,
            "box",
            {
                "name": self.name(),
                "x": str(self.obj.Length.Value),
                "y": str(self.obj.Width.Value),
                "z": str(self.obj.Height.Value),
                "lunit": "mm",
            },
        )
        self._exportScaled()

    def position(self):
        delta = FreeCAD.Vector(
            self.obj.Length.Value / 2,
            self.obj.Width.Value / 2,
            self.obj.Height.Value / 2,
        )
        # Part::Box  has its origin at the corner
        # gdml box has its origin at the center
        # In FC, rotations are about corner. In GDML about
        # center. The following gives correct position of center
        # of exported cube
        pos = self.obj.Placement.Base + self.obj.Placement.Rotation * delta
        return pos


class CylinderExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        if self.exported():
            return
        super().export()

        # Needs unique Name
        # This is for non GDML cylinder/tube
        ET.SubElement(
            solids,
            "tube",
            {
                "name": self.name(),
                "rmax": str(self.obj.Radius.Value),
                "deltaphi": str(float(self.obj.Angle.Value)),
                "aunit": "deg",
                "z": str(self.obj.Height.Value),
                "lunit": "mm",
            },
        )
        self._exportScaled()

    def position(self):
        delta = FreeCAD.Vector(0, 0, self.obj.Height.Value / 2)
        # see comments in BoxExporter
        pos = self.obj.Placement.Base + self.obj.Placement.Rotation * delta
        return pos


class ConeExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        if self.exported():
            return
        super().export()

        ET.SubElement(
            solids,
            "cone",
            {
                "name": self.name(),
                "rmax1": str(self.obj.Radius1.Value),
                "rmax2": str(self.obj.Radius2.Value),
                "deltaphi": str(float(self.obj.Angle.Value)),
                "aunit": "deg",
                "z": str(self.obj.Height.Value),
                "lunit": "mm",
            },
        )
        self._exportScaled()

    def position(self):
        # Adjustment for position in GDML
        delta = FreeCAD.Vector(0, 0, self.obj.Height.Value / 2)
        # see comments in BoxExporter
        pos = self.obj.Placement.Base + self.obj.Placement.Rotation * delta
        return pos


class SphereExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        if self.exported():
            return
        super().export()

        ET.SubElement(
            solids,
            "sphere",
            {
                "name": self.name(),
                "rmax": str(self.obj.Radius.Value),
                "starttheta": str(90.0 - float(self.obj.Angle2.Value)),
                "deltatheta": str(
                    float(self.obj.Angle2.Value - self.obj.Angle1.Value)
                ),
                "deltaphi": str(float(self.obj.Angle3.Value)),
                "aunit": "deg",
                "lunit": "mm",
            },
        )
        self._exportScaled()

    def position(self):
        # see comments in processBoxObject
        unrotatedpos = self.obj.Placement.Base
        pos = self.obj.Placement.Rotation * unrotatedpos
        return pos


class BooleanExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)
        baseExporter = SolidExporter.getExporter(self.obj.Base)
        basePlacement = baseExporter.placement()
        self._placement = self.obj.Placement * basePlacement

    def isBoolean(self, obj):
        id = obj.TypeId
        return id == "Part::Cut" or id == "Part::Fuse" or id == "Part::Common"

    def boolOperation(self, obj):
        opsDict = {
            "Part::Cut": "subtraction",
            "Part::Fuse": "union",
            "Part::Common": "intersection",
        }
        if obj.TypeId in opsDict:
            return opsDict[obj.TypeId]
        else:
            print(f"Boolean type {obj.TypeId} not handled yet")
            return None

    def position(self):
        return self._placement.Base

    def rotation(self):
        return self._placement.Rotation

    def placement(self):
        return self._placement

    def export(self):
        """
        In FreeCAD doc booleans that are themselves composed of other booleans
        are listed in sequence, eg:
                  topBool:
                      Base: Nonbool_0
                      Tool: bool1:
                            Base: bool2:
                                  Base: Nonbool_1
                                  Tool: Nonbool_2
                            Tool: bool3:
                                  Base: Nonbool_3
                                  Tool: Nonbool_4
        In the gdml file, boolean solids must always refer to PREVIOUSLY
        defined solids. So the last booleans must be written first:
        <Nonbool_0 />
        <Nonbool_1 />
        <Nonbool_2 />
        <Nonbool_3 />
        <Nonbool_4 />
        <bool3: 1st=Nonbool_3, 2nd=Nonbool_4 />
        <bool2: 1st=Nonbool_1, 2nd=Nonbool_2 />
        <bool1: 1st=bool2, 2nd=bool3 />
        <TopBool: 1st=Nonbool_0, 2nd=bool1 />

        The code below first builds the list of booleans in order:
        [topBool, bool1, bool2, bool3]

        Then outputs them to gdml in reverse order.
        In the process of scanning for booleans, the Nonbooleans are exported
        """
        GDMLShared.trace("Process Boolean Object")
        if self.exported():
            return
        super().export()


        obj = self.obj
        boolsList = [obj]  # list of booleans that are part of obj
        # dynamic list that is used to figure out when we've iterated over all
        #  subobjects that are booleans
        tmpList = [obj]
        ref1 = {}  # first solid exporter
        ref2 = {}  # second solid exporter
        while len(tmpList) > 0:
            boolobj = tmpList.pop()
            solidExporter = SolidExporter.getExporter(boolobj.Base)
            ref1[boolobj] = solidExporter
            if self.isBoolean(boolobj.Base):
                tmpList.append(boolobj.Base)
                boolsList.append(boolobj.Base)
            else:
                solidExporter.export()

            solidExporter = SolidExporter.getExporter(boolobj.Tool)
            ref2[boolobj] = solidExporter
            if self.isBoolean(boolobj.Tool):
                tmpList.append(boolobj.Tool)
                boolsList.append(boolobj.Tool)
            else:
                solidExporter.export()

        # Now tmpList is empty and boolsList has list of all booleans
        for boolobj in reversed(boolsList):
            operation = self.boolOperation(boolobj)
            if operation is None:
                continue
            solidName = boolobj.Label
            boolXML = ET.SubElement(
                solids, str(operation), {"name": solidName}
            )
            ET.SubElement(boolXML, "first", {"ref": ref1[boolobj].name()})
            ET.SubElement(boolXML, "second", {"ref": ref2[boolobj].name()})
            # process position & rotation
            # Note that only the second item in the boolean (the Tool in FC parlance)
            # gets a position and a rotation. But these are relative to the
            # first. So convolve placement of second with inverse placement of first
            placementFirst = ref1[boolobj].placement()
            placementSecond = invPlacement(placementFirst) * ref2[boolobj].placement()
            rot = placementSecond.Rotation
            pos = placementSecond.Base  # must also rotate position
            toolObj = ref2[boolobj].obj  # the tool object of the boolean
            if placementFirst == FreeCAD.Placement():  #  we give up on expressions, unless 1st object (Base( has no placement
                xexpr = GDMLShared.getPropertyExpression(toolObj, '.Placement.Base.x')
                yexpr = GDMLShared.getPropertyExpression(toolObj, '.Placement.Base.y')
                zexpr = GDMLShared.getPropertyExpression(toolObj, '.Placement.Base.z')
                pos = (xexpr, yexpr, zexpr)

            exportPosition(toolObj.Name, boolXML, pos)
            # For booleans, gdml want actual rotation, not reverse
            # processRotation export negative of rotation angle(s)
            exportRotation(toolObj.Name, boolXML, rot, invertRotation=False)
        self._exportScaled()


class GDMLSolidExporter(SolidExporter):
    def __init__(self, obj, tag, propertyList=None):
        super().__init__(obj)
        self._name = NameManager.getName(obj)
        self.propertyList = propertyList
        self.tag = tag

    def name(self):
        return self._name

    def export(self):
        if self.exported():
            return
        super().export()

        if self.propertyList is None:
            return   # presumably the child will do its own export in that case

        attrib = {}
        attrib["name"] = self.name()
        for prop in self.propertyList:
            attrib[prop] = str(GDMLShared.getPropertyExpression(self.obj, prop))  # get expression or value

        ET.SubElement(solids, str(self.tag), attrib)
        self._exportScaled()


class GDMLArb8Exporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'arb8', ['v1x', 'v1y', 'v2x', 'v2y', 'v3x', 'v3y', 'v4x', 'v4y',
                                       'v5x', 'v5y', 'v6x', 'v6y', 'v7x', 'v7y', 'v8x', 'v8y', 'dz', 'lunit'])

    def export(self):
        if self.exported():
            return
        super().export()

        ET.SubElement(
            solids,
            "arb8",
            {
                "name": self.name(),
                "v1x": str(self.obj.v1x),
                "v1y": str(self.obj.v1y),
                "v2x": str(self.obj.v2x),
                "v2y": str(self.obj.v2y),
                "v3x": str(self.obj.v3x),
                "v3y": str(self.obj.v3y),
                "v4x": str(self.obj.v4x),
                "v4y": str(self.obj.v4y),
                "v5x": str(self.obj.v5x),
                "v5y": str(self.obj.v5y),
                "v6x": str(self.obj.v6x),
                "v6y": str(self.obj.v6y),
                "v7x": str(self.obj.v7x),
                "v7y": str(self.obj.v7y),
                "v8x": str(self.obj.v8x),
                "v8y": str(self.obj.v8y),
                "dz": str(self.obj.dz),
                "lunit": self.obj.lunit,
            },
        )
        self._exportScaled()


class GDMLBoxExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, "box", ['x', 'y', 'z', 'lunit'])


class GDMLConeExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, "cone", ['rmin1', 'rmin2', 'rmax1', 'rmax2', 'startphi', 'deltaphi', 'aunit', 'z', 'lunit'])


class GDMLcutTubeExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, "cutTube", ['rmin', 'rmax', 'startphi', 'deltaphi', 'aunit', 'z',
                                          'highX', 'highY', 'highZ', 'lowX', 'lowY', 'lowZ', 'lunit'] )


class GDMLElConeExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'elcone', ['dx', 'dy', 'zcut', 'zmax', 'lunit'])


class GDMLEllipsoidExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'ellipsoid', ['ax', 'by', 'cz', 'zcut1', 'zcut2', 'lunit'])


class GDMLElTubeExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'eltube', ['dx', 'dy', 'dz', 'lunit'])


class GDMLHypeExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'hype', ['rmin', 'rmax', 'z', 'inst', 'outst', 'aunit', 'lunit'])


class GDMLParaboloidExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'paraboloid', ['rlo', 'rhi', 'dz', 'lunit'])


class GDMLOrbExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'orb', ['r', 'lunit'])


class GDMLParaExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'para', ['x', 'y', 'z', 'alpha', 'theta', 'phi', 'aunit', 'lunit'])


class GDMLPolyconeExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'polycone')

    def export(self):
        if self.exported():
            return
        super().export()

        cone = ET.SubElement(
            solids,
            "polycone",
            {
                "name": self.name(),
                "startphi": str(self.obj.startphi),
                "deltaphi": str(self.obj.deltaphi),
                "aunit": self.obj.aunit,
                "lunit": self.obj.lunit,
            },
        )
        self._exportScaled()

        for zplane in self.obj.OutList:
            ET.SubElement(
                cone,
                "zplane",
                {
                    "rmin": str(zplane.rmin),
                    "rmax": str(zplane.rmax),
                    "z": str(zplane.z),
                },
            )


class GDMLGenericPolyconeExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'genericPolycone')

    def export(self):
        if self.exported():
            return
        super().export()

        cone = ET.SubElement(
            solids,
            "genericPolycone",
            {
                "name": self.name(),
                "startphi": str(self.obj.startphi),
                "deltaphi": str(self.obj.deltaphi),
                "aunit": self.obj.aunit,
                "lunit": self.obj.lunit,
            },
        )
        self._exportScaled()
        for rzpoint in self.obj.OutList:
            ET.SubElement(
                cone, "rzpoint", {"r": str(rzpoint.r), "z": str(rzpoint.z)}
            )


class GDMLGenericPolyhedraExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'genericPolyhedra')

    def export(self):
        if self.exported():
            return
        super().export()

        polyhedra = ET.SubElement(
            solids,
            "genericPolyhedra",
            {
                "name": self.name(),
                "startphi": str(self.obj.startphi),
                "deltaphi": str(self.obj.deltaphi),
                "numsides": str(self.obj.numsides),
                "aunit": self.obj.aunit,
                "lunit": self.obj.lunit,
            },
        )
        self._exportScaled()
        for rzpoint in self.obj.OutList:
            ET.SubElement(
                polyhedra,
                "rzpoint",
                {"r": str(rzpoint.r), "z": str(rzpoint.z)},
            )


class GDMLPolyhedraExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'polyhedra')

    def export(self):
        if self.exported():
            return
        super().export()

        poly = ET.SubElement(
            solids,
            "polyhedra",
            {
                "name": self.name(),
                "startphi": str(self.obj.startphi),
                "deltaphi": str(self.obj.deltaphi),
                "numsides": str(self.obj.numsides),
                "aunit": self.obj.aunit,
                "lunit": self.obj.lunit,
            },
        )
        self._exportScaled()

        for zplane in self.obj.OutList:
            ET.SubElement(
                poly,
                "zplane",
                {
                    "rmin": str(zplane.rmin),
                    "rmax": str(zplane.rmax),
                    "z": str(zplane.z),
                },
            )


class GDMLSphereExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, "sphere", ['rmin', 'rmax', 'startphi', 'deltaphi',
                                         'starttheta', 'deltatheta', 'aunit', 'lunit'])


class GDMLSampledTessellatedExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'tesselated')

    def export(self):
        if self.exported():
            return
        super().export()

        tessName = self.name()
        print(f"tessname: {tessName}")
        # Use more readable version
        tessVname = tessName + "_"
        # print(dir(obj))

        verts = self.obj.vertsList
        tess = ET.SubElement(solids, "tessellated", {"name": tessName})
        for i, v in enumerate(verts):
            exportDefineVertex(tessVname, v, i)

        i = 0
        indexList = self.obj.indexList
        for nVerts in self.obj.vertsPerFacet:
            # print(f'Normal at : {n} dot {dot} {clockWise}')
            if nVerts == 3:
                i0 = indexList[i]
                i1 = indexList[i + 1]
                i2 = indexList[i + 2]
                ET.SubElement(
                    tess,
                    "triangular",
                    {
                        "vertex1": tessVname + str(i0),
                        "vertex2": tessVname + str(i1),
                        "vertex3": tessVname + str(i2),
                        "type": "ABSOLUTE",
                    },
                )
            elif nVerts == 4:
                i0 = indexList[i]
                i1 = indexList[i + 1]
                i2 = indexList[i + 2]
                i3 = indexList[i + 3]
                ET.SubElement(
                    tess,
                    "quadrangular",
                    {
                        "vertex1": tessVname + str(i0),
                        "vertex2": tessVname + str(i1),
                        "vertex3": tessVname + str(i2),
                        "vertex4": tessVname + str(i3),
                        "type": "ABSOLUTE",
                    },
                )
            i += nVerts
        self._exportScaled()


class GDMLTessellatedExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'tesselated')

    def export(self):
        if self.exported():
            return
        super().export()

        tessName = self.name()
        # Use more readable version
        tessVname = tessName + "_"
        # print(dir(obj))
        vertexHashcodeDict = {}

        """
        tess = ET.SubElement(solids, 'tessellated', {'name': tessName})

        #for i, v in enumerate(self.obj.Shape.Vertexes):
        for i, v in enumerate(self.obj.Shape.Vertexes):
            vertexHashcodeDict[v.hashCode()] = i
            exportDefineVertex(tessVname, self.obj.Vertexes[i], i)

        for f in self.obj.Shape.Faces:
            # print(f'Normal at : {n} dot {dot} {clockWise}')
            vertexes = f.OuterWire.OrderedVertexes
            if len(f.Edges) == 3:
                i0 = vertexHashcodeDict[vertexes[0].hashCode()]
                i1 = vertexHashcodeDict[vertexes[1].hashCode()]
                i2 = vertexHashcodeDict[vertexes[2].hashCode()]
                ET.SubElement(tess, 'triangular', {
                    'vertex1': tessVname+str(i0),
                    'vertex2': tessVname+str(i1),
                    'vertex3': tessVname+str(i2),
                    'type': 'ABSOLUTE'})
            elif len(f.Edges) == 4:
                i0 = vertexHashcodeDict[vertexes[0].hashCode()]
                i1 = vertexHashcodeDict[vertexes[1].hashCode()]
                i2 = vertexHashcodeDict[vertexes[2].hashCode()]
                i3 = vertexHashcodeDict[vertexes[3].hashCode()]
                ET.SubElement(tess, 'quadrangular', {
                    'vertex1': tessVname+str(i0),
                    'vertex2': tessVname+str(i1),
                    'vertex3': tessVname+str(i2),
                    'vertex4': tessVname+str(i3),
                    'type': 'ABSOLUTE'})
        """
        tess = ET.SubElement(solids, "tessellated", {"name": tessName})
        placementCorrection = self.obj.Placement.inverse()

        # keepQuads mode: GmshShape is intentionally empty; export directly
        # from proxy.vertex / proxy.facets to preserve all quads (including
        # non-planar ones that cannot be represented as BRep faces).
        proxy = getattr(self.obj, "Proxy", None)
        if getattr(self.obj, "keepQuads", False) and proxy is not None \
                and hasattr(proxy, "vertex") and hasattr(proxy, "facets"):
            vertex = proxy.vertex
            facets = proxy.facets
            mul = 1.0  # vertex coordinates are already in document units
            for i, v in enumerate(vertex):
                pt = placementCorrection * FreeCAD.Vector(
                    float(v.x) * mul, float(v.y) * mul, float(v.z) * mul
                )
                exportDefineVertex(tessVname, pt, i)
            tri_count = quad_count = 0
            for f in facets:
                if len(f) == 3:
                    ET.SubElement(
                        tess, "triangular",
                        {
                            "vertex1": tessVname + str(int(f[0])),
                            "vertex2": tessVname + str(int(f[1])),
                            "vertex3": tessVname + str(int(f[2])),
                            "type": "ABSOLUTE",
                        },
                    )
                    tri_count += 1
                elif len(f) == 4:
                    ET.SubElement(
                        tess, "quadrangular",
                        {
                            "vertex1": tessVname + str(int(f[0])),
                            "vertex2": tessVname + str(int(f[1])),
                            "vertex3": tessVname + str(int(f[2])),
                            "vertex4": tessVname + str(int(f[3])),
                            "type": "ABSOLUTE",
                        },
                    )
                    quad_count += 1
            FreeCAD.Console.PrintMessage(
                f"[GDML] keepQuads export: {len(vertex)} vertices,"
                f" {tri_count} triangles, {quad_count} quads\n"
            )
        else:
            # Normal path: read from GmshShape (tri + BRep-representable quads)
            # or fp.Shape for GDMLTessellated.
            # GDMLGmshTessellated stores the compound in GmshShape (not Shape) to
            # bypass BRepMesh_IncrementalMesh in FreeCAD 1.1+.  fp.Shape is kept
            # empty to prevent the UI hang.  Fall back to Shape for GDMLTessellated.
            _gmsh_shape = getattr(self.obj, "GmshShape", None)
            _export_shape = (
                _gmsh_shape
                if _gmsh_shape is not None and not _gmsh_shape.isNull()
                else self.obj.Shape
            )
            for i, v in enumerate(_export_shape.Vertexes):
                vertexHashcodeDict[v.hashCode()] = i
                exportDefineVertex(tessVname, placementCorrection * v.Point, i)

            for f in _export_shape.Faces:
                vertexes = f.OuterWire.OrderedVertexes
                if len(f.Edges) == 3:
                    i0 = vertexHashcodeDict[vertexes[0].hashCode()]
                    i1 = vertexHashcodeDict[vertexes[1].hashCode()]
                    i2 = vertexHashcodeDict[vertexes[2].hashCode()]
                    ET.SubElement(
                        tess,
                        "triangular",
                        {
                            "vertex1": tessVname + str(i0),
                            "vertex2": tessVname + str(i1),
                            "vertex3": tessVname + str(i2),
                            "type": "ABSOLUTE",
                        },
                    )
                elif len(f.Edges) == 4:
                    i0 = vertexHashcodeDict[vertexes[0].hashCode()]
                    i1 = vertexHashcodeDict[vertexes[1].hashCode()]
                    i2 = vertexHashcodeDict[vertexes[2].hashCode()]
                    i3 = vertexHashcodeDict[vertexes[3].hashCode()]
                    ET.SubElement(
                        tess,
                        "quadrangular",
                        {
                            "vertex1": tessVname + str(i0),
                            "vertex2": tessVname + str(i1),
                            "vertex3": tessVname + str(i2),
                            "vertex4": tessVname + str(i3),
                            "type": "ABSOLUTE",
                        },
                    )
        self._exportScaled()


class GDMLTetraExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'tet')

    def export(self):
        if self.exported():
            return
        super().export()

        tetraName = self.name()
        v1Name = tetraName + "v1"
        v2Name = tetraName + "v2"
        v3Name = tetraName + "v3"
        v4Name = tetraName + "v4"
        exportDefine(v1Name, self.obj.v1)
        exportDefine(v2Name, self.obj.v2)
        exportDefine(v3Name, self.obj.v3)
        exportDefine(v4Name, self.obj.v4)

        ET.SubElement(
            solids,
            "tet",
            {
                "name": tetraName,
                "vertex1": v1Name,
                "vertex2": v2Name,
                "vertex3": v3Name,
                "vertex4": v4Name,
            },
        )
        self._exportScaled()


class GDMLTetrahedronExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'tet')

    def export(self):
        if self.exported():
            return
        super().export()

        global structure
        global solids
        tetrahedronName = self.name()
        print("Len Tet" + str(len(self.obj.Proxy.Tetra)))
        count = 0
        for t in self.obj.Proxy.Tetra:
            tetraName = tetrahedronName + "_" + str(count)
            v1Name = tetraName + "v1"
            v2Name = tetraName + "v2"
            v3Name = tetraName + "v3"
            v4Name = tetraName + "v4"
            exportDefine(v1Name, t[0])
            exportDefine(v2Name, t[1])
            exportDefine(v3Name, t[2])
            exportDefine(v4Name, t[3])
            ET.SubElement(
                solids,
                "tet",
                {
                    "name": tetraName,
                    "vertex1": v1Name,
                    "vertex2": v2Name,
                    "vertex3": v3Name,
                    "vertex4": v4Name,
                },
            )
            lvName = "LVtetra" + str(count)
            lvol = ET.SubElement(structure, "volume", {"name": lvName})
            ET.SubElement(lvol, "materialref", {"ref": self.obj.material})
            ET.SubElement(lvol, "solidref", {"ref": tetraName})
            count += 1

        # Now put out Assembly
        assembly = ET.SubElement(
            structure, "assembly", {"name": tetrahedronName}
        )
        count = 0
        for t in self.obj.Proxy.Tetra:
            lvName = "Tetra" + str(count)
            physvol = ET.SubElement(
                assembly, "physvol", {"name": "PV_Tetra" + str(count)}
            )
            ET.SubElement(physvol, "volumeref", {"ref": lvName})
            # ET.SubElement(physvol, 'position')
            # ET.SubElement(physvol, 'rotation')
            count += 1
        self._exportScaled()


class GDMLTorusExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'torus', ['rmin', 'rmax', 'rtor',
                                        'startphi', 'deltaphi', 'aunit', 'lunit'])


class GDMLTrapExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'trap', ['z', 'theta', 'phi',
                                       'x1', 'x2', 'x3', 'x4', 'y1', 'y2'])

    def export(self):
        if self.exported():
            return
        super().export()

        ET.SubElement(
            solids,
            "trap",
            {
                "name": self.name(),
                "z": str(self.obj.z),
                "theta": str(self.obj.theta),
                "phi": str(self.obj.phi),
                "x1": str(self.obj.x1),
                "x2": str(self.obj.x2),
                "x3": str(self.obj.x3),
                "x4": str(self.obj.x4),
                "y1": str(self.obj.y1),
                "y2": str(self.obj.y2),
                "alpha1": str(self.obj.alpha),
                "alpha2": str(self.obj.alpha),
                "aunit": self.obj.aunit,
                "lunit": self.obj.lunit,
            },
        )
        self._exportScaled()


class GDMLTrdExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'trd', ['z', 'x1', 'x2', 'y1', 'y2', 'lunit'])


class GDMLTubeExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'tube', ['rmin', 'rmax', 'startphi', 'deltaphi', 'aunit', 'z', 'lunit'])


class GDMLTwistedboxExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'twistedbox', ['PhiTwist', 'x', 'y', 'z', 'aunit', 'lunit'])


class GDMLTwistedtrdExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'twistedtrd', ['PhiTwist', 'x1', 'x2', 'y1', 'y2', 'z', 'aunit', 'lunit'])


class GDMLTwistedtrapExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'twistedtrap', ['PhiTwist', 'x1', 'x2', 'y1', 'y2', 'x3', 'x4', 'z',
                                              'Theta', 'Phi', 'Alph', 'aunit', 'lunit'])


class GDMLTwistedtubsExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'twistedtubs', ['twistedangle', 'endinnerrad', 'endouterrad', 'zlen',
                                              'phi', 'aunit', 'lunit'])


class GDMLXtruExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'xtru')

    def export(self):
        if self.exported():
            return
        super().export()

        xtru = ET.SubElement(
            solids, "xtru", {"name": self.name(), "lunit": self.obj.lunit}
        )
        for items in self.obj.OutList:
            if items.Type == "twoDimVertex":
                ET.SubElement(
                    xtru,
                    "twoDimVertex",
                    {"x": str(items.x), "y": str(items.y)},
                )
            if items.Type == "section":
                ET.SubElement(
                    xtru,
                    "section",
                    {
                        "zOrder": str(items.zOrder),
                        "zPosition": str(items.zPosition),
                        "xOffset": str(items.xOffset),
                        "yOffset": str(items.yOffset),
                        "scalingFactor": str(items.scalingFactor),
                    },
                )
        self._exportScaled()


class GDML2dVertexExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'twoDimVertex')

    def export(self):
        ET.SubElement(
            solids, "twoDimVertex", {"x": self.obj.x, "y": self.obj.y}
        )


class GDMLborderSurfaceExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj, 'bordersurface')

    def export(self):
        borderSurface = ET.SubElement(
            structure,
            "bordersurface",
            {"name": self.obj.Name, "surfaceproperty": self.obj.surface},
        )

        print(self.obj.pv1)
        if self.obj.pv1[:3] == "av_":
            # for assembly auto generated names (starting with 'av_' we do not
            # include the 'PV_' in the name
            ET.SubElement(borderSurface, "physvolref", {"ref": self.obj.pv1})
        else:
            ET.SubElement(
                borderSurface, "physvolref", {"ref": "PV_" + self.obj.pv1}
            )
        print(self.obj.pv1)
        if self.obj.pv2[:3] == "av_":
            ET.SubElement(borderSurface, "physvolref", {"ref": self.obj.pv2})
        else:
            ET.SubElement(
                borderSurface, "physvolref", {"ref": "PV_" + self.obj.pv2}
            )


class MultiFuseExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def name(self):
        solidName = "MultiFuse" + self.obj.Label
        return solidName

    def export(self):
        if self.exported():
            return
        super().export()

        GDMLShared.trace("Multifuse - multiunion")
        # test and fix
        # First add solids in list before reference
        print("Output Solids")
        exporters = []
        for sub in self.obj.OutList:
            exporter = SolidExporter.getExporter(sub)
            if exporter is not None:
                exporter.export()
                exporters.append(exporter)

        GDMLShared.trace("Output Solids Complete")
        multUnion = ET.SubElement(solids, "multiUnion", {"name": self.name()})

        num = 1
        for exp in exporters:
            GDMLShared.trace(exp.name())
            node = ET.SubElement(
                multUnion, "multiUnionNode", {"name": "node-" + str(num)}
            )
            ET.SubElement(node, "solid", {"ref": exp.name()})
            processPlacement(exp.name(), node, exp.placement())
            num += 1

        GDMLShared.trace("Return MultiFuse")
        self._exportScaled()


class OrthoArrayExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)
        self._name = "MultiUnion-" + self.obj.Label

    def export(self):
        if self.exported():
            return
        super().export()

        from . import arrayUtils
        base = self.obj.Base
        print(f"Base {base.Label}")
        if hasattr(base, "TypeId") and base.TypeId == "App::Part":
            print(
                f"**** Arrays of {base.TypeId} ({base.Label}) currently not supported ***"
            )
            return
        baseExporter = SolidExporter.getExporter(base)
        if baseExporter is None:
            print(f"Cannot export {base.Label}")
            return
        baseExporter.export()
        volRef = baseExporter.name()
        unionXML = ET.SubElement(solids, "multiUnion", {"name": self.name()})
        basePos = baseExporter.position()
        baseRotation = FreeCAD.Rotation(baseExporter.rotation())
        for i, placement in enumerate(arrayUtils.placementList(self.obj, offsetVector=basePos)):
            ix, iy, iz = arrayUtils.orthoIndexes(i, self.obj)
            nodeName = f"{self.name()}_{ix}_{iy}_{iz}"
            translate = placement.Base
            nodeXML = ET.SubElement(
                unionXML, "multiUnionNode", {"name": nodeName}
            )
            ET.SubElement(nodeXML, "solid", {"ref": volRef})
            ET.SubElement(
                nodeXML,
                "position",
                {
                    "name": f"{self.name()}_pos_{ix}_{iy}_{iz}",
                    "x": str(translate.x),
                    "y": str(translate.y),
                    "z": str(translate.z),
                    "unit": "mm",
                },
            )
            if baseRotation.Angle != 0:
                exportRotation(self.name(), nodeXML, baseRotation, invertRotation=False)

        self._exportScaled()


class PolarArrayExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def name(self):
        solidName = "MultiUnion-" + self.obj.Label
        return solidName

    def export(self):
        if self.exported():
            return
        super().export()

        from . import arrayUtils
        base = self.obj.Base
        print(base.Label)
        if hasattr(base, "TypeId") and base.TypeId == "App::Part":
            print(
                f"**** Arrays of {base.TypeId} ({base.Label}) currently not supported ***"
            )
            return
        baseExporter = SolidExporter.getExporter(base)
        baseExporter.export()
        baseRotation = baseExporter.rotation()
        volRef = baseExporter.name()
        unionXML = ET.SubElement(solids, "multiUnion", {"name": self.name()})
        positionVector = baseExporter.position()
        for i, placement in enumerate(arrayUtils.placementList(self.obj,
                                                               offsetVector=positionVector)):
            rot = placement.Rotation
            pos = placement.Base
            rot = rot * baseRotation
            rot.Angle = -rot.Angle  # undo angle reversal by exportRotation
            nodeName = f"{self.name()}_{i}"
            nodeXML = ET.SubElement(
                unionXML, "multiUnionNode", {"name": nodeName}
            )
            ET.SubElement(nodeXML, "solid", {"ref": volRef})
            exportPosition(nodeName, nodeXML, pos)
            exportRotation(nodeName, nodeXML, rot)
        self._exportScaled()


class PathArrayExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def name(self):
        solidName = "MultiUnion-" + self.obj.Label
        return solidName

    def export(self):
        if self.exported():
            return
        super().export()

        base = self.obj.Base
        print(base.Label)
        if hasattr(base, "TypeId") and base.TypeId == "App::Part":
            print(
                f"**** Arrays of {base.TypeId} ({base.Label}) currently not supported ***"
            )
            return
        baseExporter = SolidExporter.getExporter(base)
        baseExporter.export()
        volRef = baseExporter.name()
        unionXML = ET.SubElement(solids, "multiUnion", {"name": self.name()})
        count = self.obj.Count
        positionVector = baseExporter.position()
        rot = base.Placement.Rotation
        extraTranslation = self.obj.ExtraTranslation
        pathObj = self.obj.PathObject
        path = pathObj.Shape.Edges[0]
        points = path.discretize(Number=count)
        for i, point in enumerate(points):
            pos = point + positionVector + extraTranslation
            nodeName = f"{self.name()}_{i}"
            nodeXML = ET.SubElement(
                unionXML, "multiUnionNode", {"name": nodeName}
            )
            ET.SubElement(nodeXML, "solid", {"ref": volRef})
            exportPosition(nodeName, nodeXML, pos)
            exportRotation(nodeName, nodeXML, rot)
        self._exportScaled()


class PointArrayExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def name(self):
        solidName = "MultiUnion-" + self.obj.Label
        return solidName

    def export(self):
        if self.exported():
            return
        super().export()

        base = self.obj.Base
        print(base.Label)
        if hasattr(base, "TypeId") and base.TypeId == "App::Part":
            print(
                f"**** Arrays of {base.TypeId} ({base.Label}) currently not supported ***"
            )
            return
        baseExporter = SolidExporter.getExporter(base)
        baseExporter.export()
        volRef = baseExporter.name()
        unionXML = ET.SubElement(solids, "multiUnion", {"name": self.name()})
        positionVector = baseExporter.position()
        rotBase = base.Placement.Rotation
        extraTranslation = self.obj.ExtraPlacement.Base
        extraRotation = self.obj.ExtraPlacement.Rotation
        extraRotation.Angle = -extraRotation.Angle
        rot = extraRotation * rotBase
        pointObj = self.obj.PointObject
        points = pointObj.Links
        for i, point in enumerate(points):
            pos = point.Placement.Base + positionVector + extraTranslation
            nodeName = f"{self.name()}_{i}"
            nodeXML = ET.SubElement(
                unionXML, "multiUnionNode", {"name": nodeName}
            )
            ET.SubElement(nodeXML, "solid", {"ref": volRef})
            exportPosition(nodeName, nodeXML, pos)
            exportRotation(nodeName, nodeXML, rot)
        self._exportScaled()


#
# ------------------------------revolutionExporter ----------------------------
#
global Deviation  # Fractional deviation of revolve object
#############################################
# Helper functions for Revolve construction

# One of the closed curves (list of edges) representing a part
# of the sketch


class ClosedCurve:
    def __init__(self, name, edgeList):
        self.name = name
        self.face = Part.Face(Part.Wire(edgeList))
        self.edgeList = edgeList

    def isInside(self, otherCurve):
        # ClosedCurves are closed: so if ANY vertex of the otherCurve
        # is inside, then the whole curve is inside
        return self.face.isInside(
            otherCurve.edgeList[0].Vertexes[0].Point, 0.001, True
        )

    @staticmethod
    def isCircle(arc1, arc2):
        '''
        test if two arcs can be joined into a single circle
        return true if so, false if not
        TODO: make tests in terms of some small fraction epsilon
        '''
        # Both must be circular arcs
        c1 = arc1.Curve
        c2 = arc2.Curve
        if (c1.TypeId != "Part::GeomCircle" or
             c2.TypeId != "Part::GeomCircle"):
            print("Not Arc")
            return False
        # They must have same radius
        if c1.Radius != c2.Radius:
            print("Not same radius")
            return False
        # They must have the same center
        if c1.Center != c2.Center:
            print("not same center")
            return False
        # They must join end to end
        # for reasons I don't understand, both arcs
        # have the same first and last parameters and the
        # last parameter is 2*pi. The sort edges must
        # not be calculating edges correctly
        '''
        if (c1.FirstParameter != c2.LastParameter or
            c1.LastParameter != c2.FirstParameter):
            print("dont match ends")
            print(f'c1.0 {c1.FirstParameter} c1.1 {c1.LastParameter}')
            print(f'c2.0 {c2.FirstParameter} c2.1 {c2.LastParameter}')
            return False
        '''
        if (arc1.Vertexes[0].Point != arc2.Vertexes[1].Point or
            arc1.Vertexes[1].Point != arc2.Vertexes[0].Point):
            print("dont match ends")
            print(f'c1.0 {arc1.Vertexes[0].Point} c1.1 {arc1.Vertexes[1].Point}')
            print(f'c2.0 {arc2.Vertexes[0].Point} c2.1 {arc2.Vertexes[1].Point}')
            return False

        # They must be in the same plane
        if c1.Axis != c2.Axis:
            print("not same axis")
            return False

        return True

    @staticmethod
    def arcs2circle(arc1, arc2):
        '''
        combine two arc edges into a single circle edge
        '''
        circle = None
        if ClosedCurve.isCircle(arc1, arc2):
            curve = arc1.Curve
            circle = Part.makeCircle(curve.Radius, curve.Center, curve.Axis)
        return circle


class RevolvedClosedCurve(ClosedCurve):
    def __init__(self, name, edgelist, angle, axis):
        super().__init__(name, edgelist)
        self.angle = angle
        self.axis = axis
        self.position = Vector(0, 0, 0)
        self.rotation = [0, 0, 0]  # TBD
        self.deflectionFraction = 0.001

    def export(self):
        verts = self.discretize()
        exportPolycone(self.name, verts, self.angle)

    def discretize(self):
        deflection = Deviation * radialExtent(self.edgeList)
        print(f"Deflection = {deflection}")
        edge = self.edgeList[0]
        return edge.discretize(Deflection=deflection)


class RevolvedCircle(RevolvedClosedCurve):
    def __init__(self, name, edgelist, angle, axis):
        super().__init__(name, edgelist, angle, axis)
        z = edgelist[0].Curve.Center.z
        self.position = FreeCAD.Vector(0, 0, z)

    def export(self):
        edge = self.edgeList[0]
        rmax = edge.Curve.Radius
        x = edge.Curve.Center.x
        y = edge.Curve.Center.y
        startphi = math.degrees(math.atan2(y, x))
        rtor = math.sqrt(x * x + y * y)
        exportTorus(self.name, rmax, rtor, startphi, self.angle)


class RevolvedNEdges(RevolvedClosedCurve):
    def __init__(self, name, edgelist, angle, axis):
        super().__init__(name, edgelist, angle, axis)

    def export(self):
        global solids

        # maxdev = self.deflectionFraction*radialExtent(self.edgeList)
        verts = []
        for i, e in enumerate(self.edgeList):

            while switch(e.Curve.TypeId):
                if case("Part::GeomLineSegment"):
                    print("Part::GeomLineSegment")
                    verts.append(e.Vertexes[0].Point)
                    break

                if case("Part::GeomLine"):
                    print("Part::GeomLine")
                    verts.append(e.Vertexes[0].Point)
                    break

                else:
                    curveName = self.name + "_c" + str(i)
                    curveSection = RevolvedClosedCurve(
                        curveName, [e], self.angle, self.axis
                    )
                    verts += curveSection.discretize()
                    break

        xtruName = self.name
        exportPolycone(xtruName, verts, self.angle)


# arrange a list of edges in the x-y plane in Counter Clockwise direction
# This can be easily generalized for points in ANY plane: if the normal
# defining the desired direction of the plane is given, then the z component
# below should be changed a dot prduct with the normal


def arrangeCCW(verts, normal=Vector(0, 0, 1)):
    reverse = False
    v0 = verts[0]
    rays = [(v - v0) for v in verts[1:]]
    area = 0
    for i, ray in enumerate(rays[:-1]):
        area += (rays[i].cross(rays[i + 1])).dot(normal)
    if area < 0:
        verts.reverse()
        reverse = True

    return reverse


# Utility to determine if vector from point v0 to point v1 (v1-v0)
# is on same side of normal or opposite. Return true if v points along normal


def pointInsideEdge(v0, v1, normal):
    v = v1 - v0
    if v.dot(normal) < 0:
        return False
    else:
        return True


#def edgelistArea(edgelist: list[Part.Edge]) -> float:
def edgelistArea(edgelist) -> float:
    face = Part.Face(Part.Wire(edgelist))
    return face.Area


def sortEdgelistsByFaceArea(listoflists):
    listoflists.sort(reverse=True, key=edgelistArea)


# return maxRadialdistance - minRadialDistance
def radialExtent(edges, axis=Vector(0, 0, 1)):
    rmin = sys.float_info.max
    rmax = -sys.float_info.max
    for e in edges:
        b = e.BoundBox
        for i in range(0, 8):  # loop over box boundaries
            v = b.getPoint(i)
            radialVector = v - v.dot(axis) * axis
            r = radialVector.Length
            if r < rmin:
                rmin = r
            elif r > rmax:
                rmax = r

    return rmax - rmin


def exportEllipticalTube(name, dx, dy, height):
    global solids

    ET.SubElement(
        solids,
        "eltube",
        {
            "name": name,
            "dx": str(dx),
            "dy": str(dy),
            "dz": str(height / 2),
            "lunit": "mm",
        },
    )


def exportTorus(name, rmax, rtor, startphi, angle):
    global solids

    ET.SubElement(
        solids,
        "torus",
        {
            "name": name,
            "rmin": "0",
            "rmax": str(rmax),
            "rtor": str(rtor),
            "startphi": str(startphi),
            "deltaphi": str(angle),
            "aunit": "deg",
            "lunit": "mm",
        },
    )


def exportPolycone(name, vlist, angle):
    global solids

    # if x > 0 stratphi = 0
    # if x < 0 startphi = 180
    # FreeCAD says can't recompute of both x < 0 and x> are used in a revolve
    startphi = 0
    for v in vlist:
        if v.x != 0 or v.y != 0:
            startphi = math.degrees(math.atan2(v.y, v.x))
            break

    cone = ET.SubElement(
        solids,
        "genericPolycone",
        {
            "name": name,
            "startphi": str(startphi),
            "deltaphi": str(angle),
            "aunit": "deg",
            "lunit": "mm",
        },
    )
    for v in vlist:
        r = math.sqrt(v.x * v.x + v.y * v.y)
        ET.SubElement(cone, "rzpoint", {"r": str(r), "z": str(v.z)})
    return


def getRevolvedCurve(name, edges, angle, axis):
    # Return an RevolvedClosedCurve object of the list of edges

    if len(edges) == 1:  # single edge ==> a closed curve, or curve section
        e = edges[0]
        if len(e.Vertexes) == 1:  # a closed curve
            closed = True
        else:
            closed = False  # a section of a curve

        while switch(e.Curve.TypeId):
            if case("Part::GeomCircle"):
                if closed is True:
                    print("Circle")
                    return RevolvedCircle(name, edges, angle, axis)
                else:
                    print("Revolve Arc of Circle")
                    return RevolvedClosedCurve(name, edges, angle, axis)
                    # return RevolvedArcSection(name, edges, height)

            else:
                print(f"revolve {e.Curve.TypeId}")
                return RevolvedClosedCurve(name, edges, angle, axis)

    else:  # three or more edges
        return RevolvedNEdges(name, edges, angle, axis)


# scale up a solid that will be subtracted so it punches through parent
def scaleUp(scaledName, originalName, zFactor):
    ss = ET.SubElement(solids, "scaledSolid", {"name": scaledName})
    ET.SubElement(ss, "solidref", {"ref": originalName})
    ET.SubElement(
        ss,
        "scale",
        {"name": originalName + "_ss", "x": "1", "y": "1", "z": str(zFactor)},
    )


def rotatedPos(closedCurve, rot):
    # Circles and ellipses (tubes and elliptical tubes) are referenced to origin
    # in GDML and have to be translated to their position via a position reference
    # when placed as a physical volume. This is done by adding the translation
    # to the Part::Extrusion Placement. However, if the placement includes
    # a rotation, Geant4 GDML would rotate the Origin-based curve THEN translate.
    # This would not work. We have to translate first THEN rotate. This method
    # just does the needed rotation of the position vector
    #
    pos = closedCurve.position
    if isinstance(closedCurve, ExtrudedCircle) or isinstance(
        closedCurve, ExtrudedEllipse
    ):
        pos = rot * closedCurve.position

    return pos


class RevolutionExporter(SolidExporter):
    def __init__(self, revolveObj):
        super().__init__(revolveObj)
        self.sketchObj = revolveObj.Source
        self.lastName = self.obj.Label  # initial name: might be modified later
        # generate the positions that get computed during export
        self.export(doExport=False)

    def name(self):
        # override default name in SolidExporter
        prefix = ""
        if self.lastName[0].isdigit():
            prefix = "R"
        return prefix + self.lastName

    def position(self):
        # This presumes export has been called before position()
        # Things will be screwed up, otherwise
        return self._position

    def rotation(self):
        # This presumes export has been called before position()
        # Things will be screwed up, other wise
        return self._rotation

    def export(self, doExport=True):
        # The placement of the revolved item gets calculated here, during export
        # but boolean exporter tries to get the position BEFORE the export here happens
        # so to generate the position before the export happens, the doExport flag is used
        # to run this code to generate the position, WITHOUT actually doing the export
        #
        global Deviation
        revolveObj = self.obj
        axis = revolveObj.Axis
        angle = revolveObj.Angle
        revolveCenter = revolveObj.Base

        # Fractional deviation
        if FreeCAD.GuiUp and hasattr(revolveObj, "ViewObject"):
            Deviation = revolveObj.ViewObject.Deviation / 100.0
        else:
            Deviation = 0.001  # FreeCAD default fractional deviation

        # rotation to take revolve direction to z -axis
        rot_dir_to_z = FreeCAD.Rotation(axis, Vector(0, 0, 1))
        edges = [edge.rotated(Vector(0, 0, 0), rot_dir_to_z.Axis, math.degrees(rot_dir_to_z.Angle))
                 for edge in revolveObj.Source.Shape.Edges]

        # adjustment of Symmetric revolves
        if revolveObj.Symmetric:
            edges = [edge.rotated(Vector(0, 0, 0), Vector(0, 0, 1), -angle/2)
                     for edge in edges]

        # adjustment for off-center revolve axis
        if revolveCenter != Vector(0, 0, 0):
            edges = [edge.translated(-revolveCenter) for edge in edges]


        sortededges = Part.sortEdges(edges)

        # sort by largest area to smallest area
        sortEdgelistsByFaceArea(sortededges)
        # getClosedCurve returns one of the sub classes of ClosedCurve that
        # knows how to export the specific closed edges
        # Make names based on Revolve name
        eName = revolveObj.Label
        # get a list of curves (instances of class ClosedCurve)
        # for each set of closed edges
        curves = []
        for i, edges in enumerate(sortededges):
            curve = getRevolvedCurve(eName + str(i), edges, angle, axis)
            if curve is not None:
                curves.append(curve)
        if len(curves) == 0:
            print("No edges that can be revolved were found")
            return

        # build a generalized binary tree of closed curves.
        root = Node(curves[0], None, 0)
        for c in curves[1:]:
            root.insert(c)

        # Traverse the tree. The list returned is a list of [Node, parity],
        # where parity = 0, says add to parent, 1 mean subtract
        lst = root.preOrderTraversal(root)
        rootnode = lst[0][0]
        rootCurve = rootnode.closedCurve
        if doExport:
            rootCurve.export()  # a curve is created with a unique name
        firstName = rootCurve.name
        booleanName = firstName

        rootPos = rootCurve.position
        rootRot = (
            rootCurve.rotation
        )  # for now consider only angle of rotation about z-axis

        for c in lst[1:]:
            node = c[0]
            parity = c[1]
            curve = node.closedCurve
            if doExport:
                curve.export()
            if parity == 0:
                boolType = "union"
                secondName = curve.name
                secondPos = curve.position
            else:
                boolType = "subtraction"
                secondName = curve.name
                secondPos = curve.position

            booleanName = curve.name + "_bool"
            if doExport:
                boolSolid = ET.SubElement(solids, boolType, {"name": booleanName})
                ET.SubElement(boolSolid, "first", {"ref": firstName})
                ET.SubElement(boolSolid, "second", {"ref": secondName})

            relativePosition = secondPos - rootPos
            zAngle = curve.rotation[2] - rootRot[2]
            posName = curve.name + "_pos"
            rotName = curve.name + "_rot"
            # position of second relative to first
            if doExport:
                exportDefine(posName, relativePosition)
                ET.SubElement(
                    define,
                    "rotation",
                    {
                        "name": rotName,
                        "unit": "deg",
                        "x": "0",
                        "y": "0",
                        "z": str(zAngle),
                    },
                )

                ET.SubElement(boolSolid, "positionref", {"ref": posName})
                ET.SubElement(boolSolid, "rotationref", {"ref": rotName})
            firstName = booleanName

        self.lastName = booleanName
        # Because the position of each closed curve might not be at the
        # origin, whereas primitives (tubes, cones, etc, are created centered at
        # the origin, we need to shift the position of the very first node by its
        # position, in addition to the shift by the Revolution placement

        revolvePosition = revolveObj.Placement.Base
        zoffset = Vector(0, 0, 0)
        angles = quaternion2XYZ(revolveObj.Placement.Rotation)
        # need to add rotations of elliptical tubes. Assume extrusion is on z-axis
        # Probably will not work in general
        zAngle = angles[2] + rootRot[2]
        print(rootPos)
        print(rootCurve.name)
        print(rootCurve.position)
        rootPos = rotatedPos(rootCurve, revolveObj.Placement.Rotation)
        print(rootPos)
        Base = revolvePosition + rootPos - zoffset

        # add back the off-center revolve axis
        if revolveCenter != Vector(0, 0, 0):
            Base += revolveCenter

        rotX = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), angles[0])
        rotY = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), angles[1])
        rotZ = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), zAngle)

        rot = rotX * rotY * rotZ

        # rotate back to revolve direction
        rot = rot_dir_to_z.inverted() * rot

        placement = FreeCAD.Placement(Base, FreeCAD.Rotation(rot))
        self._position = placement.Base
        self._rotation = placement.Rotation


#
# -----------------------------------------------extrusionExporter-----------------------------------------------------
#
#############################################
# Helper functions for extrude construction

# One of the closed curves (list of edges) representing a part
# of the sketch

class ExtrudedClosedCurve(ClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist)
        self.height = height
        self.position = Vector(0, 0, 0)
        self.rotation = [0, 0, 0]  # TBD

    def export(self):
        verts = self.discretize()
        exportXtru(self.name, verts, self.height)

    def midPoint(self):
        edge = self.edgeList[0]
        verts = edge.discretize(Number=51)
        return verts[int(len(verts) / 2)]

    def discretize(self):
        global Deviation
        edge = self.edgeList[0]
        deflection = Deviation * edge.BoundBox.DiagonalLength
        print(f"Deflection = {deflection}")
        return edge.discretize(Deflection=deflection)


class ExtrudedCircle(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)
        self.position = edgelist[0].Curve.Center + Vector(0, 0, height / 2)

    def export(self):
        edge = self.edgeList[0]
        exportTube(self.name, edge.Curve.Radius, self.height)


class ExtrudedArcSection(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)
        # Note extrusion polyogn will be in absolute coordinates
        # since arc section is relative to that, position is actually (0,0,0)
        # same goes for rotation

    def midPoint(self):
        edge = self.edgeList[0]
        verts = edge.discretize(Number=3)
        return verts[1]

    def area(self):
        edge = self.edgeList[0]
        v0 = edge.Vertexes[0].Point
        v1 = edge.Vertexes[1].Point
        L1 = Part.LineSegment(v0, v1)
        chordEdge = Part.Edge(L1)
        face = Part.Face(Part.Wire([edge, chordEdge]))

        return face.Area

    def export(self):
        global solids

        edge = self.edgeList[0]
        radius = edge.Curve.Radius
        # First form a bounding rectangle (polygon) for the arc.
        # Arc edges
        v1 = edge.Vertexes[0].Point
        v2 = edge.Vertexes[1].Point
        vmid = self.midPoint()

        # midpoint of chord
        vc = (v1 + v2) / 2
        v = v2 - v1
        u = v.normalize()
        # extend the ends of the chord so extrusion can cut all of circle, if needed
        v1 = vc + radius * u
        v2 = vc - radius * u
        # component of vmid perpendicular to u
        vc_vmid = vmid - vc
        n = vc_vmid - u.dot(vc_vmid) * u
        n.normalize()
        # complete edges of box paerpendicular to chord, toward mid arc point
        v3 = v2 + 2 * radius * n
        v4 = v1 + 2 * radius * n

        xtruName = self.name + "_xtru"
        exportXtru(xtruName, [v1, v2, v3, v4], self.height)

        # tube to be cut1
        tubeName = self.name + "_tube"
        exportTube(tubeName, edge.Curve.Radius, self.height)

        # note, it is mandatory that name be that of ClosedCurve
        intersect = ET.SubElement(solids, "intersection", {"name": self.name})
        ET.SubElement(intersect, "first", {"ref": xtruName})
        ET.SubElement(intersect, "second", {"ref": tubeName})
        pos = edge.Curve.Center + Vector(0, 0, self.height / 2)
        exportPosition(tubeName, intersect, pos)


class ExtrudedEllipse(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)
        curve = edgelist[0].Curve
        self.position = curve.Center + Vector(0, 0, height / 2)
        angle = math.degrees(curve.AngleXU)
        self.rotation = [0, 0, angle]

    def export(self):
        edge = self.edgeList[0]
        exportEllipticalTube(
            self.name,
            edge.Curve.MajorRadius,
            edge.Curve.MinorRadius,
            self.height,
        )


class ExtrudedEllipticalSection(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)
        # Note extrusion polyogn will be in absolute coordinates
        # since arc section is relative to that, position is actually (0,0,0)
        # same goes for rotation

    """
    def midPoint(self):
        edge = self.edgeList[0]
        a = edge.Curve.MajorRadius
        b = edge.Curve.MinorRadius
        angleXU = edge.Curve.AngleXU
        thet1 = edge.FirstParameter  # in radians, in unorated ellipse
        thet2 = edge.LastParameter  # in radians, in onrated ellipse
        thetmid = (thet1+thet2)/2 + angleXU

        # Major axis angle seems to be off by pi for some ellipse.
        # Restrict it to be be between 0 an pi
        if angleXU < 0:
            angleXU += 180

        # TODO must deal with case where cutting chord is along major axis
        # u_vc_vcenter = vc_vcenter.normalize()
        # unit vector from center of circle to center of chord

        # vertexes of triangle formed by chord ends and ellise mid point
        # In polar coordinates equation of ellipse is
        # r(thet) = a*(1-eps*eps)/(1+eps*cos(thet))
        # if the ellipse is rotated by an angle AngleXU, then
        # x = r*cos(thet+angleXU), y = r*sin(thet+angleXU),
        # for thet in frame of unrotated ellipse
        # now edge.FirstParameter is beginning angle of unrotated ellipse

        def sqr(x):
            return x*x

        def r(thet):
            return math.sqrt(1.0/(sqr(math.cos(thet)/a) + sqr(math.sin(thet)/b)))

        rmid = r(thetmid)
        vmid = Vector(rmid*math.cos(thetmid), rmid*math.sin(thetmid), 0)

        vmid += edge.Curve.Center

        return vmid
    """

    def export(self):
        global solids

        edge = self.edgeList[0]
        a = dx = edge.Curve.MajorRadius
        b = dy = edge.Curve.MinorRadius

        # vertexes of triangle formed by chord ends and ellise mid point
        # In polar coordinates equation of ellipse is
        # r(thet) = a*(1-eps*eps)/(1+eps*cos(thet))
        # if the ellipse is rotated by an angle AngleXU, then
        # x = r*cos(thet+angleXU), y = r*sin(thet+angleXU),
        # for thet in frame of unrotated ellipse
        # now edge.FirstParameter is beginning angle of unrotated ellipse
        # polar equation of ellipse, with r measured from FOCUS. Focus at a*eps
        # r = lambda thet: a*(1-eps*eps)/(1+eps*math.cos(thet))
        # polar equation of ellipse, with r measured from center a*eps

        def sqr(x):
            return x * x

        def r(thet):
            return math.sqrt(
                1.0 / (sqr(math.cos(thet) / a) + sqr(math.sin(thet) / b))
            )

        v1 = edge.Vertexes[0].Point
        v2 = edge.Vertexes[1].Point
        vmid = self.midPoint()

        # midpoint of chord
        vc = (v1 + v2) / 2
        v = v2 - v1
        u = v.normalize()  # unit vector from v1 to v2
        # extend the ends of the chord so extrusion can cut all of ellipse,
        # if needed
        v1 = vc + 2 * a * u
        v2 = vc - 2 * a * u

        # component of vmid perpendicular to u
        vc_vmid = vmid - vc
        n = vc_vmid - u.dot(vc_vmid) * u
        n.normalize()
        v3 = v2 + 2 * a * n
        v4 = v1 + 2 * a * n

        xtruName = self.name + "_xtru"
        exportXtru(xtruName, [v1, v2, v3, v4], self.height)

        # tube to be cut1
        tubeName = self.name + "_tube"
        exportEllipticalTube(tubeName, dx, dy, self.height)

        # note, it is mandatory that name be that of ClosedCurve
        intersect = ET.SubElement(solids, "intersection", {"name": self.name})
        ET.SubElement(intersect, "first", {"ref": xtruName})
        ET.SubElement(intersect, "second", {"ref": tubeName})
        pos = edge.Curve.Center + Vector(0, 0, self.height / 2)
        exportPosition(tubeName, intersect, pos)
        rotName = tubeName + "_rot"
        # zAngle = math.degrees(edge.Curve.AngleXU)
        # Focus1 is on the positive x side, Focus2 on the negative side
        dy = edge.Curve.Focus1[1] - edge.Curve.Focus2[1]
        dx = edge.Curve.Focus1[0] - edge.Curve.Focus2[0]
        zAngle = math.degrees(math.atan2(dy, dx))
        print(f"{self.name} zAngle = {zAngle}")
        # if zAngle < 0:
        #    zAngle += 180
        ET.SubElement(
            define,
            "rotation",
            {
                "name": rotName,
                "unit": "deg",
                "x": "0",
                "y": "0",
                "z": str(zAngle),
            },
        )

        ET.SubElement(intersect, "rotationref", {"ref": rotName})


class ExtrudedBSpline(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)


class Extruded2Edges(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)

    def export(self):
        global solids

        # form normals to the edges. For case of two edges,
        # sidedness is irrelevant
        v0 = self.edgeList[0].Vertexes[0].Point
        v1 = self.edgeList[0].Vertexes[1].Point
        e = v1 - v0
        if e.x == 0:
            ny = 0
            nx = 1
        elif e.y == 0:
            nx = 0
            ny = 1
        else:
            nx = 1
            ny = -e.x / e.y
        normal = Vector(nx, ny, 0).normalize()

        edgeCurves = []  # list of ExtrudedClosedCurve's

        for i, e in enumerate(self.edgeList):  # just TWO edges
            while switch(e.Curve.TypeId):
                if case("Part::GeomLineSegment"):
                    break

                if case("Part::GeomLine"):
                    break

                if case("Part::GeomCircle"):
                    print("Arc of Circle")
                    arcXtruName = self.name + "_c" + str(i)
                    arcSection = ExtrudedArcSection(
                        arcXtruName, [e], self.height
                    )
                    arcSection.export()

                    midpnt = arcSection.midPoint()
                    inside = pointInsideEdge(midpnt, v0, normal)
                    edgeCurves.append([arcXtruName, inside])
                    break

                if case("Part::GeomEllipse"):
                    print("Arc of Ellipse")
                    arcXtruName = self.name + "_e" + str(i)
                    arcSection = ExtrudedEllipticalSection(
                        arcXtruName, [e], self.height
                    )
                    arcSection.export()
                    midpnt = arcSection.midPoint()
                    inside = pointInsideEdge(midpnt, v0, normal)
                    edgeCurves.append([arcXtruName, inside])
                    break

                else:
                    print(f"Arc of {e.Curve.TypeId}")
                    arcXtruName = self.name + "_bs" + str(i)
                    arcSection = ExtrudedClosedCurve(
                        arcXtruName, [e], self.height
                    )
                    arcSection.export()

                    midpnt = arcSection.midPoint()
                    inside = pointInsideEdge(midpnt, v0, normal)
                    edgeCurves.append([arcXtruName, inside])
                    break

        if len(edgeCurves) == 1:
            # change our name to be that of the constructed curve
            # not a violation of the contract of a unique name,
            # since the curve name is based on ours
            self.position = arcSection.position
            self.rotation = arcSection.rotation
            self.name = edgeCurves[0][0]

        else:
            inside0 = edgeCurves[0][1]
            inside1 = edgeCurves[1][1]
            sameSide = inside0 == inside1
            if sameSide is False:
                booleanSolid = ET.SubElement(
                    solids, "union", {"name": self.name}
                )
            else:
                booleanSolid = ET.SubElement(
                    solids, "subtraction", {"name": self.name}
                )

            area0 = edgelistArea([self.edgeList[0]])
            area1 = edgelistArea([self.edgeList[1]])
            if area0 > area1:
                firstSolid = edgeCurves[0][0]
                secondSolid = edgeCurves[1][0]
            else:
                firstSolid = edgeCurves[1][0]
                secondSolid = edgeCurves[0][0]

            ET.SubElement(booleanSolid, "first", {"ref": firstSolid})
            ET.SubElement(booleanSolid, "second", {"ref": secondSolid})


class ExtrudedNEdges(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)

    def isSubtraction(self, edge):
        # Does the given edge increase or decrease the area
        # of the polygon formed by verts
        ftot = Part.Face(Part.Wire(self.edgeList))
        # form face from edge and its chord
        v0 = edge.Vertexes[0].Point
        v1 = edge.Vertexes[1].Point
        L1 = Part.LineSegment(v0, v1)
        E1 = Part.Edge(L1)
        fEdge = Part.Face(Part.Wire([edge, E1]))

        # form face from other edges without edge being tested
        edgesWithout = []
        for e in self.edgeList:
            if e != edge:
                edgesWithout.append(e)
            else:
                v0 = edge.Vertexes[0].Point
                v1 = edge.Vertexes[1].Point
                L1 = Part.LineSegment(v0, v1)
                edgesWithout.append(Part.Edge(L1))
        fwithout = Part.Face(Part.Wire(edgesWithout))

        totArea = ftot.Area
        edgeArea = fEdge.Area
        withoutArea = fwithout.Area
        print(
            f"totArea {totArea}, edgeArea {edgeArea}, withoutArea {withoutArea}"
        )

        if totArea < 0.999 * (
            edgeArea + withoutArea
        ):  # 0.99 safety margin for totArea = edgeArea+withoutArea
            if totArea > edgeArea:
                return True
            else:
                # we need to reverse order of subtraction
                return None  # poor way of signaling need to swap subtraction order
        else:
            return False

    def export(self):
        global solids

        verts = []

        for i, e in enumerate(self.edgeList):
            while switch(e.Curve.TypeId):
                if case("Part::GeomLineSegment"):
                    verts.append(e.Vertexes[0].Point)
                    break

                if case("Part::GeomLine"):
                    verts.append(e.Vertexes[0].Point)
                    break

                else:
                    print(f"Curve {e.Curve.TypeId}")
                    arcXtruName = self.name + "_g" + str(i)
                    arcSection = ExtrudedClosedCurve(
                        arcXtruName, [e], self.height
                    )
                    bsplineVerts = arcSection.discretize()
                    verts = verts + bsplineVerts
                    break

        # verts.append(verts[0])
        xtruName = self.name
        exportXtru(xtruName, verts, self.height)


# Node of a tree that represents the topology of the sketch being exported
# a left_child is a ClosedCurve that is inside of its parent
# a right_sibling is a closedCurve that is outside of its parent


class Node:
    def __init__(self, closedCurve, parent, parity):
        # the nomenclature is redundant, but a reminder that
        # left is a child and right a sibling
        self.parent = parent
        if parent is None:
            self.parity = (
                0  # if parity is 0, print as union with current solid
            )
            # if parity is 1, print as subtraction from other solid
        else:
            self.parity = parity

        self.left_child = None
        self.right_sibling = None
        self.closedCurve = closedCurve

    def insert(self, closedCurve):
        if self.closedCurve:  # not sure why this test is necessary
            if self.closedCurve.isInside(closedCurve):
                # given curve is inside this curve:
                # if this node does not have a child,
                # insert it as the left_child
                # otherwise check if it is a child of the child
                if self.left_child is None:
                    self.left_child = Node(closedCurve, self, 1 - self.parity)
                else:
                    self.left_child.insert(closedCurve)
            else:  # Since we have no intersecting curves (for well constructed sketch
                # if the given curve is not inside this node, it must be outside
                if self.right_sibling is None:
                    self.right_sibling = Node(closedCurve, self, self.parity)
                else:
                    self.right_sibling.insert(closedCurve)
        else:
            self.closedCurve = closedCurve

    def preOrderTraversal(self, root):
        res = []
        if root:
            res.append([root, root.parity])
            res = res + self.preOrderTraversal(root.left_child)
            res = res + self.preOrderTraversal(root.right_sibling)

        return res


def discretizeMinusOne(edgeList, iSkip):
    # return discretized edge list except for iSkip
    verts = []
    for i in range(len(edgeList)):
        edge = edgeList[i]
        if (
            i == iSkip
            or edge.Curve.TypeId == "Part::GeomLine"
            or edge.Curve.TypeId == "Part::GeomLineSegment"
        ):
            verts.append(edge.Vertexes[0].Point)
            verts.append(edge.Vertexes[1].Point)
        else:
            verts += edge.discretize(24)
    return verts


def exportTube(name, radius, height):
    global solids

    ET.SubElement(
        solids,
        "tube",
        {
            "name": name,
            "rmax": str(radius),
            "z": str(height),
            "startphi": "0",
            "deltaphi": "360",
            "aunit": "deg",
            "lunit": "mm",
        },
    )


def exportXtru(name, vlist, height):
    global solids

    # We are assuming that the points to that form the
    # the edges to be extruded are al coplanar and in the x-y plane
    # with a possible zoffset, which is taken as the common
    # z-coordinate of the first vertex
    if len(vlist) < 3:
        return
    zoffset = vlist[0].z
    xtru = ET.SubElement(solids, "xtru", {"name": name, "lunit": "mm"})

    # prune verts: Closed curves get stitched from adjacent edges
    # sometimes the beginning vertex f the next edge is the same as the end vertex
    # of the previous edge. Geant gives a warning about that. To remove the warning
    # we will remove vertices closer to each other than 0.1 nm - 1e-7 mm. If someone is trying
    # to model objects with smaller dimensions, then they should take a lesson in Quantum Mechanics
    # Because only adjacent edges could be the same, we just compare each edge to the preceding edge
    vpruned = vlist[:]
    for i in range(len(vlist)):
        i1 = (i+1) % len(vlist)
        if ((vlist[i1] - vlist[i]).Length < 1e-7):
            vpruned.remove(vlist[i1])

    for v in vpruned:
        ET.SubElement(xtru, "twoDimVertex", {"x": str(v.x), "y": str(v.y)})
    ET.SubElement(
        xtru,
        "section",
        {
            "zOrder": "0",
            "zPosition": str(zoffset),
            "xOffset": "0",
            "yOffset": "0",
            "scalingFactor": "1",
        },
    )
    ET.SubElement(
        xtru,
        "section",
        {
            "zOrder": "1",
            "zPosition": str(height + zoffset),
            "xOffset": "0",
            "yOffset": "0",
            "scalingFactor": "1",
        },
    )


def getExtrudedCurve(name, edges, height):
    # Return an ExtrudedClosedCurve object of the list of edges

    if len(edges) == 1:  # single edge ==> a closed curve, or curve section
        e = edges[0]
        if len(e.Vertexes) == 1:  # a closed curve
            closed = True
        else:
            closed = False  # a section of a curve

        while switch(e.Curve.TypeId):
            if case("Part::GeomLineSegment"):
                print(" Sketch not closed")
                return ExtrudedClosedCurve(edges, name, height)

            if case("Part::GeomLine"):
                print(" Sketch not closed")
                return ExtrudedClosedCurve(name, edges, height)

            if case("Part::GeomCircle"):
                if closed is True:
                    print("Circle")
                    return ExtrudedCircle(name, edges, height)
                else:
                    print("Arc of Circle")
                    return ExtrudedArcSection(name, edges, height)

            if case("Part::GeomEllipse"):
                if closed is True:
                    print("Ellipse")
                    return ExtrudedEllipse(name, edges, height)
                else:
                    print("Arc of Ellipse")
                    return ExtrudedEllipticalSection(name, edges, height)

            else:
                print(" B spline")
                return ExtrudedClosedCurve(name, edges, height)

    elif len(edges) == 2:  # exactly two edges
        # if the two edges are tow arcs that make a circle, extrude resulting circle
        edge = ClosedCurve.arcs2circle(edges[0], edges[1])
        if edge is not None:
            return ExtrudedCircle(name, [edge], height)
        else:
            return ExtrudedNEdges(name, edges, height)
    else:  # three or more edges
        return ExtrudedNEdges(name, edges, height)


class ExtrusionExporter(SolidExporter):
    def __init__(self, extrudeObj):
        global Deviation
        super().__init__(extrudeObj)
        self.sketchObj = extrudeObj.Base
        self.lastName = self.obj.Label  # initial name: might be modified later
        if FreeCAD.GuiUp and hasattr(self.obj, "ViewObject"):
            Deviation = self.obj.ViewObject.Deviation / 100.0
        else:
            Deviation = 0.001  # FreeCAD default fractional deviation
        # generate the positions that get computed during export
        self.export(doExport=False)

    def position(self):
        # This presumes export has been called before position()
        # Things will be screwed up, otherwise
        return self._position

    def rotation(self):
        # This presumes export has been called before position()
        # Things will be screwed up, otherwise
        return self._rotation

    def name(self):
        # override default name in SolidExporter
        prefix = ""
        if self.lastName[0].isdigit():
            prefix = "X"
        return prefix + self.lastName

    def export(self, doExport=True):
        # The placement of the extruded item gets calculated here, during export
        # but boolean exporter tries to get the position BEFORE the export here happens
        # so to generate the position before the export happens, the doExport flag is used
        # to run this code to generate the position, WITHOUT actually doing the export
        #

        sketchObj: Sketcher.SketchObject = self.sketchObj
        extrudeObj: Part.Feature = self.obj
        eName = self.name()

        extrudeDirection  = extrudeObj.Dir

        # rotation to take extrude direction to z -axis
        rot_dir_to_z = FreeCAD.Rotation(extrudeDirection, Vector(0, 0, 1))
        edges = [edge.rotated(Vector(0, 0, 0), rot_dir_to_z.Axis, math.degrees(rot_dir_to_z.Angle)) for edge in sketchObj.Shape.Edges]
        sortededges = Part.sortEdges(edges)
        # sort by largest area to smallest area
        sortEdgelistsByFaceArea(sortededges)
        # getCurve returns one of the sub classes of ClosedCurve that
        # knows how to export the specific closed edges
        # Make names based on Extrude name
        # curves = [getCurve(edges, extrudeObj.Label + str(i)) for i, edges
        # in enumerate(sortededges)]
        if extrudeObj.Symmetric is True:
            height = extrudeObj.LengthFwd.Value
        else:
            height = extrudeObj.LengthFwd.Value + extrudeObj.LengthRev.Value
        # get a list of curves (instances of class ClosedCurve) for each
        # set of closed edges
        curves = [
            getExtrudedCurve(eName + str(i), edges, height)
            for i, edges in enumerate(sortededges)
        ]
        # build a generalized binary tree of closed curves.
        root = Node(curves[0], None, 0)
        for c in curves[1:]:
            root.insert(c)

        # Traverse the tree. The list returned is a list of [Node, parity],
        # where parity = 0, says add to parent, 1 mean subtract
        lst = root.preOrderTraversal(root)
        rootnode = lst[0][0]
        rootCurve = rootnode.closedCurve
        if doExport:
            rootCurve.export()  # a curve is created with a unique name
        firstName = rootCurve.name
        booleanName = firstName

        rootPos = rootCurve.position
        rootRot = (
            rootCurve.rotation
        )  # for now consider only angle of rotation about z-axis

        for c in lst[1:]:
            node = c[0]
            parity = c[1]
            curve = node.closedCurve
            if doExport:
                curve.export()
            if parity == 0:
                boolType = "union"
                secondName = curve.name
                secondPos = curve.position
            else:
                boolType = "subtraction"
                secondName = (
                    curve.name + "_s"
                )  # scale solids along z, so it punches thru
                if doExport:
                    scaleUp(secondName, curve.name, 1.10)
                secondPos = curve.position - Vector(0, 0, 0.01 * height)

            booleanName = curve.name + "_bool"
            if doExport:
                boolSolid = ET.SubElement(solids, boolType, {"name": booleanName})
                ET.SubElement(boolSolid, "first", {"ref": firstName})
                ET.SubElement(boolSolid, "second", {"ref": secondName})
            relativePosition = secondPos - rootPos
            zAngle = curve.rotation[2] - rootRot[2]
            posName = curve.name + "_pos"
            rotName = curve.name + "_rot"
            if doExport:
                exportDefine(
                    posName, relativePosition
                )  # position of second relative to first
                ET.SubElement(
                    define,
                    "rotation",
                    {
                        "name": rotName,
                        "unit": "deg",
                        "x": "0",
                        "y": "0",
                        "z": str(zAngle),
                    },
                )

                ET.SubElement(boolSolid, "positionref", {"ref": posName})
                ET.SubElement(boolSolid, "rotationref", {"ref": rotName})
                firstName = booleanName

        self.lastName = (
            booleanName  # our name should the name f the last solid created
        )

        # Because the position of each closed curve might not be at the
        # origin, whereas primitives (tubes, cones, etc, are created centered
        # at the origin, we need to shift the position of the very first node
        # by its position, in addition to the shift by the Extrusion placement
        extrudeObj = self.obj
        extrudePosition = extrudeObj.Placement.Base
        if extrudeObj.Symmetric is False:
            if extrudeObj.Reversed is False:
                zoffset = Vector(0, 0, extrudeObj.LengthRev.Value)
            else:
                zoffset = Vector(0, 0, extrudeObj.LengthFwd.Value)
        else:
            zoffset = Vector(0, 0, extrudeObj.LengthFwd.Value / 2)

        angles = quaternion2XYZ(extrudeObj.Placement.Rotation)
        # need to add rotations of elliptical tubes.
        # Assume extrusion is on z-axis
        # Probably will not work in general
        zAngle = angles[2] + rootRot[2]
        rootPos = rotatedPos(rootCurve, extrudeObj.Placement.Rotation)
        print(rootPos)
        Base = extrudePosition + rootPos - zoffset

        rotX = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), angles[0])
        rotY = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), angles[1])
        rotZ = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), zAngle)

        rot = rotZ * rotY * rotX

        # rotate back to extrude direction
        rot = rot_dir_to_z.inverted() * rot

        placement = FreeCAD.Placement(Base, FreeCAD.Rotation(rot))
        self._position = placement.Base
        self._rotation = placement.Rotation


class GDMLMeshExporter(GDMLSolidExporter):
    # FreeCAD Mesh only supports triangular Facets
    def __init__(self, obj):
        super().__init__(obj, 'tessellated')

    def export(self):
        if self.exported():
            return
        super().export()

        tessName = self.name().replace('\r','').replace('(','_').replace(')','_')
        # Use more readable version
        tessVname = tessName + "_"
        tess = ET.SubElement(solids, "tessellated", {"name": tessName})
        placementCorrection = self.obj.Placement.inverse()
        for i, v in enumerate(self.obj.Mesh.Points):
            v = FreeCAD.Vector(v.x, v.y, v.z)
            exportDefineVertex(tessVname, placementCorrection * v, i)
        for f in self.obj.Mesh.Facets:
            indices = f.PointIndices
            i0 = indices[0]
            i1 = indices[1]
            i2 = indices[2]
            ET.SubElement(
                tess,
                "triangular",
                {
                    "vertex1": tessVname + str(i0),
                    "vertex2": tessVname + str(i1),
                    "vertex3": tessVname + str(i2),
                    "type": "ABSOLUTE",
                },
            )
        self._exportScaled()


class AutoTessellateExporter(SolidExporter):
    shapesDict = {}  # a dictionary of exported shapes and their names

    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        import MeshPart

        shape = self.obj.Shape.copy(False)
        shape.Placement = FreeCAD.Placement()  # remove object's placement
        alreadyExportedName = AutoTessellateExporter.alreadyExported(shape)
        if alreadyExportedName is not None:
            self._name = alreadyExportedName
            return

        else:
            AutoTessellateExporter.shapesDict[shape] = self.name()

        if FreeCAD.GuiUp and hasattr(self.obj, "ViewObject"):
            viewObject = self.obj.ViewObject
            deflection = viewObject.Deviation
            angularDeflection = math.radians(viewObject.AngularDeflection)
        else:
            deflection = 0.1        # sensible default: 0.1 mm linear deflection
            angularDeflection = math.radians(28.5)  # FreeCAD default angular deflection
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=deflection,
                                      AngularDeflection=angularDeflection, Relative=False)

        tessName = self.name()
        # Use more readable version
        tess = ET.SubElement(solids, "tessellated", {"name": tessName})
        tessVname = tessName + "_"
        placementCorrection = self.obj.Placement.inverse()
        for i, v in enumerate(mesh.Points):
            v = FreeCAD.Vector(v.x, v.y, v.z)
            exportDefineVertex(tessVname, v, i)
        for f in mesh.Facets:
            indices = f.PointIndices
            i0 = indices[0]
            i1 = indices[1]
            i2 = indices[2]
            ET.SubElement(
                tess,
                "triangular",
                {
                    "vertex1": tessVname + str(i0),
                    "vertex2": tessVname + str(i1),
                    "vertex3": tessVname + str(i2),
                    "type": "ABSOLUTE",
                },
            )
        self._exportScaled()


    @staticmethod
    def centerOfMass(pts: [Vector]) -> Vector:
        cm = Vector(0, 0, 0)
        for pt in pts:
            cm += pt

        return cm

    @staticmethod
    def principalMoments(pts: [Vector]) -> tuple:
        Ixx = 0
        Iyy = 0
        Izz = 0
        for pt in pts:
            Ixx += pt.y * pt.y + pt.z * pt.z
            Iyy += pt.x * pt.x + pt.z * pt.z
            Izz += pt.x * pt.x + pt.y * pt.y

        return Ixx, Iyy, Izz


    @staticmethod
    def identicalShapes(shp1, shp2) -> bool:
        # return True if shapes are the same
        verts1 = shp1.Vertexes
        verts2 = shp2.Vertexes

        # Test 1, same number of vertexes
        if len(verts1) != len(verts2):
            return False

        # Test 2, Center of mass
        pts1 = [v.Point for v in shp1.Vertexes]
        pts2 = [v.Point for v in shp2.Vertexes]
        cm1 = AutoTessellateExporter.centerOfMass(pts1)
        cm2 = AutoTessellateExporter.centerOfMass(pts2)
        if (cm1 - cm2).Length > 1e-04:
            return False

        # Test 3, compare volumes.
        # I am not sure which is faster, moment of inertial calculation or volume calculation
        # I Shape.Volume is calculated in C it is probably faster than CM and should be done first
        # But I don't know for sure
        if (shp1.Volume - shp2.Volume) > 1e-6:
            return False

        # Test 4, same moments of inertia
        II1 = AutoTessellateExporter.principalMoments(pts1)
        II2 = AutoTessellateExporter.principalMoments(pts2)

        for i, II in enumerate(II1):
            if abs(II1[i] - II2[i]) > 1e-08:
                return False

        # Well, ChatGPT says in principle one can have all moments of inertia to be the same  for all axes
        # and the shapes be different. Dr. Omar Hijab also convinced me of this.
        # If all of the above is true, it is likely that the shapes are the same. But to be on
        # the safe side, we sample a few of the points and assume they are ordered the same.
        # If the shapes are really the same but because the ordering of the points is different then
        # at worst we export the same shape twice. This is much better than exporting one shape, when in fact
        # they are two different shapes. The likelihood that two different shapes match in order is extremely
        # small

        # Test 4
        nsamples = int(len(verts1)/10) + 1
        sampled = set()   # to avoid sampling same point twice we keep track of already sampled points
        if nsamples >= len(pts1):
            nsamples = len(pts1)

        while len(sampled) < nsamples:
            index = random.randint(0, nsamples-1)
            if (pts2[index]-pts1[index]).Length > 1e-04:
                return False
            sampled.add(index)

        return True

    @staticmethod
    def alreadyExported(shape) -> str | None:
        for shp in AutoTessellateExporter.shapesDict:
            if AutoTessellateExporter.identicalShapes(shape, shp):
                return AutoTessellateExporter.shapesDict[shp]  # return name of shape

        return None  # shape not already exported

