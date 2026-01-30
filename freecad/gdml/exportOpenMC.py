from __future__ import annotations
# Mon Aug 26 2024
# Sat Mar 28 8:44 AM PDT 2023
# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2019 Keith Sloan <keith@sloan-home.co.uk>              *
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
__author__ = "Keith Sloan <keith@sloan-home.co.uk>"
__url__ = ["https://github.com/KeithSloan/FreeCAD_Geant4"]

from gettext import translation
from sys import breakpointhook

import FreeCAD, os, Part, math
import Sketcher
import FreeCAD as App
import FreeCADGui
from PySide import QtGui

from FreeCAD import Vector
import  BOPTools.SplitAPI
from BOPTools import BOPFeatures
from collections import defaultdict


import random
import re
from .GDMLObjects import GDMLcommon, GDMLBox, GDMLTube

# modif add
# from .GDMLObjects import getMult, convertionlisteCharToLunit

import sys
from pathlib import Path

from .GDMLShared import getMult
from .GmshUtils import meshObj
from .polygonsHelper import inner_outer

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
global element_table   # dictionary of ElementIsotopes object for an element symbol as key
global nuclide_table   # dictionary of Isotope obj for nuclide name as key

element_table = None

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


class Isotope:
    def __init__(self, nuclide, atomic_weight, fraction, element):
        self.nuclide = nuclide  # nuclide, example 'U235'
        self.atomic_weight = atomic_weight  # float atomic weight (234.99, eg)
        self.fraction = fraction  # atomic fraction of isotope in its element
        self.element = element   #  the ElementIsotopes this isotope belongs to

    def weight_fraction(self):
        return self.fraction * self.atomic_weight/self.element.atomic_weight


class ElementIsotopes:
    def __init__(self, Z, symbol, element, atomic_weight, isotopes):
        self.Z = Z
        self.symbol = symbol
        self.element = element  # element name
        self.atomic_weight = atomic_weight  # mean atomic weight of element
        self.isotopes = isotopes  # list[Isotope]


def gen_element_table(file_name):
    '''read the given file and return a dictionary of ElementIsotopes: dict[element_symbol] = ElementIsotope
    '''

    table = {}

    fd = open(file_name, 'r')
    for line in fd.readlines():
        if line[0] == '#':
            continue
        words = line.strip().split()
        Z = int(words[0])
        sym = words[1]
        element = words[2].lower()
        nuclide_list = words[3:]
        if 3 * int(len(nuclide_list) / 3) != len(nuclide_list):
            print(
                f"*** Nuclide list for element {Z} {element} might be missing something a nuclide or a fraction. Please check file ***")
            exit(0)

        num_words = len(nuclide_list)
        tot_fraction = 0
        average_atomic_weight = 0
        isotopes_list = []
        elementIsotopes = ElementIsotopes(Z, sym, element, average_atomic_weight, isotopes_list)
        for i in range(0, num_words, 3):
            nuclide = nuclide_list[i]
            atomic_weight = float(nuclide_list[i + 1])
            fraction = float(nuclide_list[i + 2])
            isotope = Isotope(nuclide, atomic_weight, fraction, elementIsotopes)
            isotopes_list.append(isotope)
            tot_fraction += fraction
            average_atomic_weight += atomic_weight

            # sanity check for typos
            nuclide_element = nuclide[:len(sym)]
            if nuclide_element != sym:
                print(f"nuclide {nuclide} does not have the same element name as its element {sym}")
                return
            # another check, atomic weight should be within 0.1% of mass number
            mass_number = int(nuclide[len(sym):])
            if abs(mass_number - atomic_weight) / atomic_weight > 5.0e-3:
                print(
                    f" {nuclide} atomic wieght {atomic_weight} different than mass number by more than 0.5%. Please check")

        average_atomic_weight = average_atomic_weight / len(isotopes_list)
        elementIsotopes.atomic_weight = average_atomic_weight
        table[sym] = elementIsotopes
        # sanity check
        if abs(tot_fraction - 1.0) > 2.0e-03 and tot_fraction != 0:
            print(f"Warning: {element} sum of fraction is {tot_fraction} differs from 1.0 by at least 0.2%")

    return table

def gen_nuclide_table():
    global element_table
    '''
    put all nuclides is a dictionary dict[nuclide] = Isotope  (isotope class containing the nuclide)
    '''
    table = {}
    for elementSymbol in element_table:
        elementObject = element_table[elementSymbol]
        isotopes = elementObject.isotopes
        for isotope in isotopes:
            table[isotope.nuclide] = isotope

    return table

#################################
#  Setup GDML environment
#################################

def GDMLstructure():
    # print("Setup GDML structure")
    #################################
    # globals
    ################################
    from .init_gui import joinDir
    global gdml, geometry, materials
    global WorldVOL
    global defineCnt, LVcount, PVcount, POScount, ROTcount, SCLcount
    global centerDefined
    global identityDefined
    global identityName
    global gxml
    global material_ids
    global element_table
    global nuclide_table


    centerDefined = False
    identityDefined = False
    identityName = 'identity'


    defineCnt = LVcount = PVcount = POScount = ROTcount = SCLcount = 1
    # gdml = initGDML()

    materials = ET.Element('materials')
    geometry = ET.Element('geometry')
    material_ids = {}

    if element_table is None:
        element_table = gen_element_table(joinDir('Resources/Isotopic_abundances.csv'))
        nuclide_table = gen_nuclide_table()
    return


def defineMaterials():
    # Replaced by loading Default
    # print("Define Materials")
    global materials

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

#-------------------------- OpenMC Materials exporting code -----------------------------------
import re


def elementSymbol_from_Z(Z):
    '''return element symbol for element with atomic number Z'''
    global element_table
    for sym in element_table:
        elementIsotopes = element_table[sym]
        if elementIsotopes.Z == Z:
            return sym
    return None



def elementSymbol(elem):
    # first try an actual element define via material
    obj = FreeCAD.ActiveDocument.getObject(elem)
    if hasattr(obj, 'Z'):
        Z = int(obj.Z)
        sym = elementSymbol_from_Z(Z)
        return sym

    pattern = r'^([A-Z][a-z]?)$'  # Element symbol, say C, or Cd
    match = re.match(pattern, elem)
    if match:
        sym = match.group(1)
        return sym

    pattern = r'^([A-Z][a-z]?)_element$'  # Element of the form Cd_element or C_element

    match = re.match(pattern, elem)
    if match:
        sym = match.group(1)
        return sym

    pattern = r'^G4_([A-Z][a-z]?$)'  # Element Ga_sym
    match = re.match(pattern, elem)
    if match:
        sym = match.group(1)
        return sym

    # Try element defined in Elements Group
    elem_grp = elementGroup(elem)
    if elem_grp is not None and hasattr(elem_grp, 'formula'):
        sym = elem_grp.formula
        return sym

    return None


def elementGroup(elem):
    elementsGroup = FreeCAD.ActiveDocument.getObject('Elements')
    elem1 = elem[:]
    if elem1.endswith("_element"):
        elem1 = elem1[:-len("_element")]

    for grp in elementsGroup.Group:
        label = grp.Label
        if label.endswith("_element"):
            label = label[:-len("_element")]

        if label == elem1:
            return grp

    return None


def materialGroup(mat):
    materialGroup = FreeCAD.ActiveDocument.getObject('Materials')

    for grp in materialGroup.Group:
        if grp.Label == mat:
            return grp

    return None


def merge_lists(list1, list2):
    ''' merge the two lists of dictionaries
    Say list1 is [{'nuclide': A, 'fraction': fA1, 'type': typeA}, {'nuclide': B,'fraction': fB1, 'type': typeB},...]
    and list2 is
    [{nuclide: C,'fraction': fC, 'type': typeC}, {nuclide: A,'fraction': fA2, 'type': typeA2},...]

    then we want to return a list
    [{'nuclide': A, 'fraction': fA+fA2, 'type': typeA}, {'nuclide': 'B', ....}, {'nuclide': C, ...}]
    '''

    both_lists = list1 + list2
    merged_dict = {}
    for nuc_dict in both_lists:
        nuclide = nuc_dict['nuclide']
        frac = nuc_dict['fraction']
        typ = nuc_dict['type']
        if nuclide in merged_dict:
            frac += merged_dict[nuclide][0]
        else:
            merged_dict[nuclide] = (frac, nuc_dict['type'])

    combined_list = []
    for nuclide in merged_dict:
        combined_dict = {'nuclide': nuclide, 'fraction': merged_dict[nuclide][0], 'type': merged_dict[nuclide][1]}
        combined_list.append(combined_dict)

    return combined_list


def material_nuclides(mat):
    '''
    return a list of
    {'nuclide': nuclide(str), 'fraction': fraction, 'type': (ao for atomic fraction | wo for weioght fraction)

    for the material

    :param: mat: name of material (a string)
    '''
    global element_table
    global nuclide_table

    nuclide_list = []  # a list of {'nuclide': isotope, 'fraction', fraction, 'type': 'ao' or 'wo'}

    # A single natural element
    sym = elementSymbol(mat)
    if sym is not None:
        elementIsotopes = element_table[sym]
        isotopes = elementIsotopes.isotopes
        for isotope in isotopes:
            nuclide_list.append({'nuclide': isotope.nuclide, 'fraction': isotope.fraction, 'type': 'ao'})
        return nuclide_list

    print(mat)
    mat_obj = FreeCAD.ActiveDocument.getObject(mat)
    if mat_obj is None:
        # perhaps the minus in the name. clean the name
        mat = mat.replace('-', '_')
        mat_obj = FreeCAD.ActiveDocument.getObject(mat)
        print(f"Cannot find object with name {mat}")

    print(mat_obj.Label)

    # A Chemical formula
    if hasattr(mat_obj, 'formula'):
        for grp in mat_obj.Group:
            element_count = grp.n
            # print(element_count)
            elementName = grp.Label[:grp.Label.find(' :')]
            sym = elementSymbol(elementName)
            if sym not in element_table:
                print(f" formula {mat_obj.Label} has a component {grp.Label} with unknown element {elementName}")
                continue

            elementIsotopes = element_table[sym]
            isotopes = elementIsotopes.isotopes
            for isotope in isotopes:
                # print(nucleus)
                nuc_dict = {}
                nuc_dict['nuclide'] = isotope.nuclide
                nuc_dict['fraction'] = element_count * isotope.fraction
                nuc_dict['type'] = 'ao'
                nuclide_list.append(nuc_dict)
        return nuclide_list

    # A mixture
    print(f"I think {mat} is a mixture")
    print(mat_obj.Group)
    # in a mixture the fractions are weight fractions
    for grp in mat_obj.Group:
        print(grp.Label)
        mat_or_element = grp.Label[:grp.Label.find(' :')]
        weight_fraction = float(grp.Label[1+grp.Label.find(':'):])
        print(mat_or_element)
        sym = elementSymbol(mat_or_element)
        if sym is not None:  # The mixture involves a natural element
            component_list = material_nuclides(mat_or_element)
            for component in component_list:
                isotopeName = component['nuclide']
                isotopeObject = nuclide_table[isotopeName]
                # for a natural element, the isotope fractions are atomic fractions
                # for mixtures (of elements) the fractions should be weight fractions
                # The components returned above are for an element an so need to convert to weight_fractions
                component['fraction'] *= weight_fraction * isotopeObject.atomic_weight/isotopeObject.element.atomic_weight
                component['type'] = 'wo'
            nuclide_list = merge_lists(nuclide_list, component_list)
            continue

        print(f"checking if {grp.Label} is defined in the Elements Group")
        elem_grp = elementGroup(mat_or_element)
        if elem_grp is not None:
            for isotope in elem_grp.Group:
                print(isotope.Label)
                index = isotope.Label.find(' :')
                print(index)
                isotope_name = isotope.Label[:isotope.Label.find(' :')]
                isotope_fraction = isotope.n
                nuc_dict = {}
                nuc_dict['nuclide'] = isotope_name
                # in an element definition the isotope fractions are ATOMIC fractions,
                # but here we are processing mixtures, the fractions should be WEIGHT fractions
                # so we need to convert
                isotopeObject = nuclide_table[isotope_name]
                nuc_dict['fraction'] = weight_fraction*isotope_fraction * isotopeObject.atomic_weight/isotopeObject.element.atomic_weight
                nuc_dict['type'] = 'wo'
                nuclide_list.append(nuc_dict)
            continue

        # TODO: Should Check if the component is actually a Single isotope

        print(f"checking if {grp.Label} is defined in the Materials Group")
        mat_grp = materialGroup(mat_or_element)
        if mat_grp is not None:
            fraction = float(grp.Label[grp.Label.find(':') + 1:])
            component_list = material_nuclides(mat_or_element)
            if component_list is None:
                print(f"material component {mat_or_element} is not a material and not an element")
                continue
            # multiply the fractions in the returned list by the fraction of the material in the mixture
            for component in component_list:
                component['fraction'] *= fraction
                # a material fraction in a mixture is a weight fraction
                # the component might be an element and hence the resulting component might atomic fraction
                # we check and compensate here
                if component['type'] == 'ao':
                    nuclideName = component['nuclide']
                    nuclideObject = nuclide_table[nuclideName]
                    component['fraction'] *= weight_fraction*nuclideObject.atomic_weight/nuclideObject.element.atomic_weight
            # update the current nuclide_list with that of the current material
            nuclide_list = merge_lists(nuclide_list, component_list)

        else:
            print(f" material {mat} has a component {grp.Label} that is not in Group Elements or in group Materials")

    return nuclide_list


def processMaterials():
    print("\nProcess Materials")
    global materials

    for GName in [
        # "Define",
        # "Isotopes",
        # "Elements",
        "Materials",
    ]:
        Grp = FreeCAD.ActiveDocument.getObject(GName)
        if Grp is not None:
            # print(Grp.TypeId+" : "+Grp.Label)
            print(Grp.Label)
            if processGroup(Grp) is False:
                break

def createMaterials(group):
    global materials
    global material_ids

    density_multipliers = {
        'g/cm3': 1,
        'g/cc': 1,
        'mg/cm3': 0.001
    }

    preprocessMaterialIds()
    for mat in material_ids:

        print(f"processing material {mat}")
        id = material_ids[mat]

        item = ET.SubElement(
            materials, "material", {"name": str(mat) }
        )

        item.attrib['id'] = str(id)

        # property must be first
        # openmc does not use properties
        '''
        for prop in obj.PropertiesList:
            if obj.getGroupOfProperty(prop) == "Properties":
                ET.SubElement(
                    item,
                    "property",
                    {"name": prop, "ref": getattr(obj, prop)},
                )
        '''


        # hyphens are wreaking havoc in getting properties from labels.
        # so replace them with underscores
        mat = mat.replace('-', '_')
        obj = FreeCAD.ActiveDocument.getObject(mat)

        if hasattr(obj, "Tvalue"):
            temperature = float(obj.Tvalue)
            if hasattr(obj, "Tunit"):
                if obj.Tunit == 'Celsius' or obj.Tunit == 'C' or obj.Tunit == 'Centigrade':
                    temperature += 273.15
                elif obj.Tunit == 'Fahrenheit' or obj.Tunit == 'F':  # ich!! nobody should do that
                    temperature = 273.15 + (temperature - 32)/9*5
            item['temperature'] = str(temperature)


        if hasattr(obj, "Dunit") or hasattr(obj, "Dvalue"):
            # print("Dunit or DValue")
            D = ET.SubElement(item, "density")
            unit_multiplier = 1
            if hasattr(obj, "Dunit"):
                if obj.Dunit in density_multipliers:
                    unit_multiplier = density_multipliers[obj.Dunit]
                    D.set("units", 'g/cm3')
                else:
                    D.set("units", str(obj.Dunit))
            else:  # default to g/cm3, if no Dunit is given
                D.set("units", 'g/cm3')
            if hasattr(obj, "Dvalue"):
                density = float(obj.Dvalue)
                if obj.Dvalue <= 0:
                    density = 1.0e-25
                D.set("value", str(density*unit_multiplier))

        # process common options material / element
        nuclides_in_material = material_nuclides(mat)
        for nuclide in nuclides_in_material:
            xml_item = ET.SubElement(item, 'nuclide')

            nuclide_name = nuclide['nuclide']
            nuclide_fraction = nuclide['fraction']
            fraction_type  = nuclide['type']

            xml_item.attrib['name'] = str(nuclide_name)
            xml_item.attrib[fraction_type] = str(nuclide_fraction)


def createElement(elementLabel, item):
    global materials

    elementsGroup = FreeCAD.ActiveDocument.getObject('Elements')
    for grp in elementsGroup.Group:
        if grp.Label == elementLabel:
            for nuclideGrp in grp.Group:
                nuclide_name = nuclideGrp.Label[:nuclideGrp.Label.find(' :')]
                fraction = nuclideGrp.n
                xml_item = ET.SubElement(item, 'nuclide')
                xml_item.attrib['name'] = str(nuclide_name)
                xml_item.attrib['ao'] = str(fraction)

# -------------------------- End process OpenMC materials ------------------------

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
                # skip defines for openMC.
                # createDefine(obj.Group)
                break

            if case("Quantities"):
                # print("Quantities")
                # skip quantities
                # createQuantities(obj.Group)
                break

            if case("Isotopes"):
                # print("Isotopes")
                # skip Isotopes
                # createIsotopes(obj.Group)
                break

            if case("Elements"):
                # print("Elements")
                # createElements(obj.Group)
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

def processArrayPart(array):
    # array: array object
    from . import arrayUtils
    # array: Array item
    # new approach 2024-08-07:
    # Create an assembly for the array. The assembly has the name of the array Part
    # place the repeated array elements in this new assembly and place
    # the array assembly in the xmlVol with the position and rotation of the array
    # xmlVol: xml item into which the array elements are placed/exported

    # arrayRef = NameManager.getName(array)
    base = array.Base
    baseName = NameManager.getName(array.Base)
    # create a cell with id = universe_dict[baseName]
    # baseUniverseId = universe_dict[baseName]
    # basePhysVol = physVolStack.pop()
    # baseRotation = basePhysVol.placement.Rotation
    # baseTranslation = basePhysVol.placement.Base

    arrayType = arrayUtils.typeOfArray(array)
    saved_placement = FreeCAD.Placement(base.Placement.Base, base.Placement.Rotation)
    doc = FreeCAD.ActiveDocument
    while switch(arrayType):
        if case("ortho"):
            placements = arrayUtils.placementList(array)
            print(f'Number of placements = {len(placements)}')
            for i, placement in enumerate(placements):
                base.Placement = placement
                doc.recompute()
                geomExporter = GeomObjExporter.getExporter(base)
                geomExporter.export()
            break

        if case("polar"):
            placements = arrayUtils.placementList(array)
            print(f'Number of placements = {len(placements)}')
            for i, placement in enumerate(placements):
                base.Placement = placement
                doc.recompute()
                geomExporter = GeomObjExporter.getExporter(base)
                geomExporter.export()
            break

        if case("PathArray") or case("PointArray"):
            placements = arrayUtils.placementList(array)
            for i, placement in enumerate(placements):
                base.Placement = placement
                doc.recompute()
                geomExporter = GeomObjExporter.getExporter(base)
                geomExporter.export()
            break

    base.Placement = saved_placement
    doc.recompute()

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


def createWorldVol(volName):
    print("Need to create Dummy Volume and World Box ")
    bbox = FreeCAD.BoundBox()
    boxName = defineWorldBox(bbox)
    worldVol = ET.SubElement(structure, "volume", {"name": volName})
    ET.SubElement(worldVol, "materialref", {"ref": "G4_AIR"})
    ET.SubElement(worldVol, "solidref", {"ref": boxName})
    ET.SubElement(gxml, "volume", {"name": volName, "material": "G4_AIR"})
    return worldVol


def get_global_placement(obj):
    """
    Placement of obj in the current traversal context.

    If the current logical parent on parent_stack is an App::Link,
    use that link's hierarchy; otherwise fall back to the object's
    own global placement in the document.

    GPT-5.1 crap that does not work
    if parent_stack:
        parent = parent_stack[-1]
        if parent.TypeId == "App::Link" and getattr(parent, "LinkedObject", None):
            try:
                # Placement via the Link's hierarchy: includes link.Placement
                return parent.getSubObject(obj.Name, retType=3)
            except Exception:
                pass

    # Generic / non-link context
    try:
        return obj.getSubObject("", retType=3)
    except Exception:
        return obj.Placement

    """

    pl = obj.Placement
    for parent in reversed(parent_stack):
        pl = parent.Placement*pl

    return pl


#------------------------------------------------------------------------------
def buildDocTree():
    from PySide import QtWidgets

    global obj_top_children_dict
    global parent_stack

    obj_top_children_dict = {}  # dictionary of list of child objects for each object
    parent_stack  = [] # a LIFO of the parent of the current child being processed by exporters

    # TypeIds that should not go in to the tree
    skippedTypes = ["App::Origin", "Sketcher::SketchObject", "Part::Compound", "App::FeaturePython", "Points::Feature"]

    def addDaughters(item: QtWidgets.QTreeWidgetItem):
        print (f"--------addDaughters {item.text(0)}")
        objectLabel = item.text(0)
        object = App.ActiveDocument.getObjectsByLabel(objectLabel)[0]

        if object not in obj_top_children_dict:
            obj_top_children_dict[object] = []

        if SolidExporter.isSolid(object):   # that takes care of arrays and booleans
            return

        for i in range(item.childCount()):
            childItem = item.child(i)
            treeLabel = childItem.text(0)
            try:
                childObject = App.ActiveDocument.getObjectsByLabel(treeLabel)[0]
                objType = childObject.TypeId
                if objType not in skippedTypes:
                    obj_top_children_dict[object].append(childObject)
                    addDaughters(childItem)
            except Exception as e:
                print(e)
        return

    # Get world volume from document tree widget
    worldObj = FreeCADGui.Selection.getSelection()[0]
    # tree = FreeCADGui.getMainWindow().findChildren(QtGui.QTreeWidget)[0]
    # it = QtGui.QTreeWidgetItemIterator(tree)

    mw1 = FreeCADGui.getMainWindow()
    print (f"---------Number of trees {len(mw1.findChildren(QtGui.QTreeWidget))}")
    treesSel = mw1.findChildren(QtGui.QTreeWidget)
    print (f"---------Number of trees {len(treesSel)}")

    doc = FreeCAD.ActiveDocument
    found = False

    for tree in treesSel:
        print(f"--------Tree {tree.objectName()}")
        items = tree.selectedItems()
        for item in items:
            treeLabel = item.text(0)
            print(f"--------Item {treeLabel}")
            print(f"--------Doc.Label {doc.Label}")
            # if not found:
            #     if treeLabel != doc.Label:
            #         continue
            # found = True
            try:
                objs = doc.getObjectsByLabel(treeLabel)
                print(f"--------Objects {objs}")
                if len(objs) == 0:
                    continue

                obj = objs[0]
                if obj == worldObj:
                    print(f"--------World Object {obj.Label}")
                    # we presume first app part is world volume
                    addDaughters(item)
                    break
            except Exception as e:
                print(e)
                FreeCADobject = None


    # Links will have empty children with above because iemchildcount is zero for links
    # so we populate links with the children of the object they are linked to
    for obj in obj_top_children_dict:
        if obj.TypeId == "App::Link":
            target = obj.LinkedObject
            if target in obj_top_children_dict:
                obj_top_children_dict[obj] = obj_top_children_dict[target]


def dot_separated_path_to(target):
    global paretn_stack

    ''' Return a string of the form rootParentLabel.parent_1_Label.parent_2_Label...target Label'''
    path = parent_stack[:]
    return ".".join(obj.Label for obj in path[1:])+"."+target.Label
#------------------------------------------------------------------------------


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
    # This is in contrast to assembly, which is exported as
    # <assembly
    #   <physvol 1>
    #   <physvol 2>
    #   ....
    #
    # Must be assembly first
    global obj_top_children_dict

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

    global obj_top_children_dict

    print(f"testing isAsembly for: {obj.Label}")
    if obj.TypeId != "App::Part":
        if (obj.TypeId == "App::Link" and obj.LinkedObject.TypeId != "App::Part"):
            return False

    for ob in obj_top_children_dict[obj]:
        if ob.TypeId == "App::Part" or (ob.TypeId == "App::Link" and ob.LinkedObject.TypeId == "App::Part"):
            print(True)
            return True  # Yes, even if ONE App::Part is under this, we treat it as an assembly

    if len(obj_top_children_dict[obj]) > 1:
        print("Yes, it is an Assembly")
        return True
    else:
        # need to check for arrays. Arrays of App::Part are treated as an assembly
        if len(obj_top_children_dict[obj]) == 1:
            topObject = obj_top_children_dict[obj][0]
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
    global obj_top_children_dict

    return obj_top_children_dict[obj]


def checkExportFlag(obj):
    if hasattr(obj, "exportFlag"):
        return obj.exportFlag
    else:
        return True


def topObj(obj):
    # The topmost object in an App::Part
    # The App::Part is assumed NOT to be an assembly
    global obj_top_children_dict

    if isAssembly(obj):
        print(f"***** Non Assembly expected  for {obj.Label}")
        return

    if len(obj_top_children_dict[obj]) == 0:
        return obj
    else:
        return obj_top_children_dict[obj][0]


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
    global obj_top_children_dict

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
    global obj_top_children_dict

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


def exportWorldVol(vol, fileExt):
    global obj_top_children_dict
    global WorldVOL

    WorldVOL = vol.Label
    if fileExt != ".xml":
        print("Export World Process Volume : " + vol.Label)
        GDMLShared.trace("Export Word Process Volume" + vol.Label)

        if checkGDMLstructure(vol) is False:
            GDMLShared.trace("Insert Dummy Volume")
            # createXMLvolume("dummy")
            xmlParent = createWorldVol(vol.Label)
            parentName = vol.Label
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

    processDocTree(1)

def exportGDML(first, filepath, fileExt):
    from . import GDMLShared
    from sys import platform

    global zOrder

    global usedGeant4Materials
    usedGeant4Materials = set()

    global gdml
    global universe_dict


    universe_dict = {}
    universe_dict['worlVOL'] = 1  # world volume = root volume = 1
    SurfaceExporter.reset_ids()

    # GDMLShared.setTrace(True)
    GDMLShared.trace("exportGDML")

    print("====> Start OpenMC Export 0.1")
    branch = get_active_branch_name()
    print(f"branch: {branch}")
    print("File extension : " + fileExt)

    GDMLstructure()
    zOrder = 1
    # TODO: process and export materials
    processMaterials()
    exportWorldVol(first, fileExt)

    params = FreeCAD.ParamGet(
        "User parameter:BaseApp/Preferences/Mod/GDML"
    )
    exportG4Materials = params.GetBool('exportG4Materials', False)

    # format & write GDML file
    # xmlstr = ET.tostring(structure)
    # print('Structure : '+str(xmlstr))
    if fileExt == ".xml":
        # indent(gdml)
        print(len(list(geometry)))
        print("Write to xml file")
        # ET.ElementTree(gdml).write(filepath, 'utf-8', True)
        # ET.ElementTree(gdml).write(filepath, xml_declaration=True)
        # Problem with pretty Print on Windows ?
        combined_file = filepath
        geom_file_path = filepath[:-4] + '_geometry.xml'
        materials_file_path = filepath[:-4] + '_materials.xml'
        openmc = ET.Element('openmc')
        openmc.append(materials)
        openmc.append(geometry)

        SurfaceExporter.export_surfaces()
        CellExporter.export_cells()

        if platform == "win32":
            indent(geometry)
            indent(materials)
            ET.ElementTree(materials).write(materials_file_path, xml_declaration=True, encoding='UTF-8')
            ET.ElementTree(geometry).write(geom_file_path, xml_declaration=True, encoding='UTF-8')
            ET.ElementTree(openmc).write(filepath, xml_declaration=True, encoding='UTF-8')
        else:
            ET.ElementTree(materials).write(materials_file_path, pretty_print=True, xml_declaration=True, encoding='UTF-8')
            ET.ElementTree(geometry).write(geom_file_path, pretty_print=True, xml_declaration=True, encoding='UTF-8')
            ET.ElementTree(openmc).write(filepath, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        print("OpenMC xml files written")


def preprocessMaterialIds():

    global obj_top_children_dict
    global material_ids

    material_ids = {}

    for obj in obj_top_children_dict:
        if len(obj_top_children_dict[obj]) == 0:
            continue  # this item will get exported as a child of some other item
        if isContainer(obj) or isAssembly(obj):
            pass

        elif SolidExporter.isSolid(obj):
            solidExporter = SolidExporter.getExporter(obj)

            if solidExporter is None:
                pass
            else:
                material_name = getMaterial(obj)
                if material_name not in material_ids:
                    id = len(material_ids) + 1
                    material_ids[material_name] = id

        for child in obj_top_children_dict[obj]:
            if isContainer(child) or isAssembly(child):
                pass
            elif SolidExporter.isSolid(child):
                material_name = getMaterial(child)
                if material_name not in material_ids:
                    id = len(material_ids) + 1
                    material_ids[material_name] = id

    print(f" Material ids: {material_ids}")

#------------------------------   Geometry Objects exporters -------------------------

from abc import ABC, abstractmethod
class GeomObjExporter(ABC):
    global obj_top_children_dict

    def __init__(self, obj):
        self.obj = obj

    @staticmethod
    def getExporter(obj):
        '''
        if obj.TypeId == "App::Link":
            target = obj.LinkedObject
            doc = FreeCAD.ActiveDocument
            children = [doc.copyObject(child, True) for child in obj_top_children_dict[target]]
            obj_top_children_dict[obj] = children
            for child in children:
                obj_top_children_dict[child] = []
            if len(children) == 1:
                return SingleVolumeExporter(obj)
            elif len(children) > 1:
                return AssemblyExporter(obj)
            else:
                return None
        '''

        if isContainer(obj):
            return ContainerExporter(obj)
        elif isAssembly(obj):
            return AssemblyExporter(obj)
        elif SolidExporter.isSolid(obj):
            return SingleSolidExporter(obj)
        else:
            childObjects = obj_top_children_dict[obj]
            if len(childObjects) == 1:
                return SingleVolumeExporter(obj)
            else:
                print(f"Can't find a GeomObjExporter for {obj.Label}")
                return

    @abstractmethod
    def getRegion(self):
        ''' get region surrounding this object '''

    @abstractmethod
    def export(self):
        ''' export all surfaces needed and a cell with a material and region for the object '''


class ContainerExporter(GeomObjExporter):
    def __init__(self, obj):
        super().__init__(obj)
        firstChild = obj_top_children_dict[obj][0]

        if not SolidExporter.isSolid(firstChild):
            print(f" Expect a solid for first child of {obj.Label}, but {firstChild.Label} is not")
            return

        self.containerSolidExporter = SolidExporter.getExporter(firstChild)
        self.children_geom_exporters = []
        for child in obj_top_children_dict[obj][1:]:
            geomExporter = GeomObjExporter.getExporter(child)
            if geomExporter is None:
                print(f" No GeomObjectExporter for {child.Label}. Skipping")
                continue
            self.children_geom_exporters.append(geomExporter)

    def getRegion(self):
        ''' Note this region is that of the surrounding solid
        If this container is contained in another container, the solid of this container should
        be subtacted from it's motherregion
        '''
        return self.containerSolidExporter.get_region()

    def myRegion(self):
        '''
        return region occupied by material in this Exporter
        This is the solid region for the container minus the region occupied by all its children
        '''
        solid_region = self.containerSolidExporter.get_region()
        children_region = Region("")
        for child_geom_exporter in self.children_geom_exporters:
            child_region = child_geom_exporter.getRegion()
            if child_region is not None:
                children_region = children_region.union(child_region)

        return solid_region.cut(children_region)

    def export(self):
        # Very ugly way of checking whether we are exporting world volume
        worldObject =  list(obj_top_children_dict.keys())[0]
        if self.obj == worldObject:
            self.containerSolidExporter.set_boundary_type("vacuum")

        # Push this container as current parent
        parent_stack.append(self.obj)
        try:
            # Export container's own surfaces
            self.containerSolidExporter.export()

            # Export all children under this container
            for child_geom_exporter in self.children_geom_exporters:
                child_geom_exporter.export()
        finally:
            parent_stack.pop()

        region = self.myRegion()
        # material is that of the containing box
        mat_name = getMaterial(self.containerSolidExporter.obj)
        cellExporter = CellExporter(self.obj.Label, material_name=mat_name, region=region.expr)
        cellExporter.export()


class AssemblyExporter(GeomObjExporter):
    def __init__(self, obj):
        super().__init__(obj)
        self.children_geom_exporters = []
        firstChild = obj_top_children_dict[obj][0]

        arrayOfPart = False
        if isArrayType(firstChild) and firstChild.Base.isDerivedFrom("App::Part"):
            processArrayPart(firstChild)
            arrayOfPart = True

        for child in obj_top_children_dict[obj]:
            if child is firstChild and arrayOfPart:
                continue

            geomExporter = GeomObjExporter.getExporter(child)
            if geomExporter is None:
                print(f" No GeomObjectExporter for {child.Label}. Skipping")
                continue
            self.children_geom_exporters.append(geomExporter)

    def getRegion(self):
        children_region = Region("")
        for child_geom_exporter in self.children_geom_exporters:
            children_region = children_region.union(child_geom_exporter.getRegion())

        return children_region

    def export(self):
        # Push this assembly as current parent
        parent_stack.append(self.obj)
        try:
            for child_geom_exporter in self.children_geom_exporters:
                child_geom_exporter.export()
        finally:
            parent_stack.pop()


class SingleVolumeExporter(GeomObjExporter):
    '''
    A Logical volume of the form:
    App::Part
       Solid
    '''
    global material_ids
    def __init__(self, obj):
        super().__init__(obj)
        child = obj_top_children_dict[obj][0]
        self.child_solid_exporter = SolidExporter.getExporter(child)
        if self.child_solid_exporter is None:
            if hasattr(child, "TypeId"):
                print(f"TpeId {child.TypeId} does not have a SolidExporter")
            print(f"{child.Label} has no SolidExporter")

    def getRegion(self):
        if self.child_solid_exporter is None:
            return

        return self.child_solid_exporter.get_region()

    def export(self):
        if self.child_solid_exporter is None:
            return

        # Treat this volume (App::Part or App::Link) as the current parent
        parent_stack.append(self.obj)
        try:
            # Inside here, the solid exporter will see self.obj as parent
            self.child_solid_exporter.export()
        finally:
            parent_stack.pop()

        mat_name = getMaterial(self.child_solid_exporter.obj)
        solidRegion = self.child_solid_exporter.get_region()
        cellExporter = CellExporter(self.obj.Label,
                                    material_name=mat_name,
                                    region=solidRegion.expr)
        cellExporter.export()


class SingleSolidExporter(GeomObjExporter):
    def __init__(self, obj):
        super().__init__(obj)

        self.solidExporter = SolidExporter.getExporter(obj)

    def getRegion(self):
        return self.solidExporter.get_region()

    def export(self):
        if self.solidExporter is None:
            print(f"There is no exporter for object {self.obj.Label}")
            return

        self.solidExporter.export()
        solidRegion = self.solidExporter.get_region()
        mat_name = getMaterial(self.obj)
        cellExporter = CellExporter(self.obj.Label, material_name=mat_name, region=solidRegion.expr)
        cellExporter.export()

#------------------------------   Geometry Objects exporters -------------------------

def processDocTree(rootUniverseId):

    global obj_top_children_dict
    objects = list(obj_top_children_dict.keys())
    worldObj = objects[0]

    geomExporter = GeomObjExporter.getExporter(worldObj)
    print(f"{worldObj.Label} {worldObj}")

    geomExporter.export()


def exportGDMLworld(first, filepath, fileExt):
    global obj_top_children_dict

    buildDocTree()  # creates global obj_top_children_dict
    NameManager.init()
    SolidExporter.init()

    # for debugging doc tree
    for obj in obj_top_children_dict:
        s = ""
        for child in obj_top_children_dict[obj]:
            s += child.Label + ", "
        print(f"{obj.Label} [{s}]")

    if filepath.lower().endswith(".xml"):
        # GDML Export
        print("OpenMC Export")
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

def export(exportList, filepath):
    "called when FreeCAD exports a file"

    print("OpenMC exporter version 0.1")

    first = exportList[0]
    print(f"Export Volume: {first.Label}")

    import os

    path, fileExt = os.path.splitext(filepath)
    print("filepath : " + path)
    print("file extension : " + fileExt)

    if fileExt.lower() == ".xml":
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

#
# -------------------------------------------------------------------------------------------------------
#

class Region:
    def __init__(self, expr):
        self.expr = expr

    def union(self, other):
        if self.expr == "":
            return Region(f"({other.expr})")
        return Region(f"(({self.expr}) | ({other.expr}))")

    def intersection(self, other):
        if self.expr == "":
            return Region(f"({other.expr})")
        return Region(f"(({self.expr}) ({other.expr}))")

    def cut(self, other):
        if self.expr == "":
            return Region(f"~({other.expr})")
        return Region(f"(({self.expr}) ~ ({other.expr}))")

    def __str__(self):
        return self.expr

class CellExporter:
    _ids = []  # dictionary of name vs id: __ids[name] = id
    _ids_dict = {}
    cell_cache = []

    def __init__(self, name, material_name=None, region=None, universe=None, fill=None,
                 rotation=None, translation=None):

        id = 1
        while id in CellExporter._ids:
            id += 1
        CellExporter._ids.append(id)
        CellExporter._ids_dict[name] = id

        self.id = id
        self.name = name
        if material_name in material_ids:
            self.material = material_ids[material_name]
        else:
            self.material = None

        self.fill = fill

        self.region = region
        self.rotation = rotation
        self.translation = translation
        self.universe = universe

    @staticmethod
    def export_cells():
        for cell in CellExporter.cell_cache:
            cell.replace_surface_ids(SurfaceExporter.replacement_ids)
            cell._export()

        CellExporter.cell_cache = []  # reset the cache after exporting

    def replace_surface_ids(self, replacement_dict):
        ''' replace every occurrence of a surface id in our region with its replacement id'''
        region = self.region
        for surface_id in replacement_dict:
            pattern = rf"([+-]){re.escape(str(surface_id))}\b"
            replacement = rf"\g<1>{str(replacement_dict[surface_id])}"
            region = re.sub(pattern, replacement, region)
        self.region = region

    def _export(self):
        cell = ET.SubElement(geometry, 'cell')
        cell.attrib['name'] = self.name
        cell.attrib['id'] = str(self.id)
        if self.universe is not None:
            cell.attrib['universe'] = str(self.universe)
        if self.material is not None:
            cell.attrib['material'] = str(self.material)

        if self.region is not None:
            cell.attrib['region'] = str(self.region)

        if self.fill is not None:
            cell.attrib['fill'] = str(self.fill)

            if self.rotation is not None:
                angles = quaternion2XYZ(self.rotation)
                cell.attrib['rotation'] = f"{angles[0]} {angles[1]} {angles[2]}"

            if self.translation is not None:
                cell.attrib['translation'] = f"{self.translation.x} {self.translation.y} {self.translation.z}"

    def export(self):
        CellExporter.cell_cache.append(self)


def quadric_coeffs(F, **kwargs):
    ''' Given a function F that calculates a surface F(x, y, z, **kwargs) return
    the coefficients A, B, C, D, E, F, G, H, J, K of the quadric expression
    A x^2 + B y^2 + C z^2 + D xy + E yz + F xz + G x + H y + J z + K
        # Suppose one has a means of evaluating F(x, y, z) = A x^2 + B y^2 + C z^2 +
        #                                                   D xy  + E yz  + F xz +
        #                                                   G x   + H y    + J z +
        #                                                   K
        # Usually this is done by rotating/translating a vector (x', y', z') in which the surface has a simple
        # form (say x'2 + y'2) = R^2 for a cylinder surface, to the system in which the axes are rotated/translated
        # say, v = R v', where is the 4x4 transformation matrix.
        # Now the numerical extraction of the coefficients A, B, C, ....
        # K = F(0, 0, 0)
        # A = 1/2 (F(1, 0, 0) + F(-1, 0, 0)) - K
        # B = 1/2 (F(0, 1, 0) + F(0, -1, 0)) - K
        # C = 1/2 (F(0, 0, 1) + F(0, 0, -1)) - K
        # G = 1/2 (F(1, 0, 0) - F(-1, 0, 0))
        # H = 1/2 (F(0, 1, 0) - F(0, -1, 0))
        # J = 1/2 (F(0, 0, 1) - F(0, 0, -1))
        # For the cross terms (D, E, F)
        # F(1, 1, 0) = A + B + D + G + H + K  ==> D = F(1, 1, 0) -A -B -G -H -K
        # F(0, 1, 1) = B + C + E + H + J + K  ==> E = F(0, 1, 1) -B -C -H -J -K
        # F(1, 0, 1) = A + C + F + G + J + K  ==> F = F(1, 0, 1) -A -C -G -J -K
    '''

    K = F(0, 0, 0, **kwargs)
    A = 1/2 * (F(1, 0, 0, **kwargs) + F(-1, 0, 0, **kwargs)) - K
    B = 1/2 * (F(0, 1, 0, **kwargs) + F(0, -1, 0, **kwargs)) - K
    C = 1/2 * (F(0, 0, 1, **kwargs) + F(0, 0, -1, **kwargs)) - K
    G = 1/2 * (F(1, 0, 0, **kwargs) - F(-1, 0, 0, **kwargs))
    H = 1/2 * (F(0, 1, 0, **kwargs) - F(0, -1, 0, **kwargs))
    J = 1/2 * (F(0, 0, 1, **kwargs) - F(0, 0, -1, **kwargs))
    # For the cross terms (D, E, F)
    D = F(1, 1, 0, **kwargs) -A -B -G -H -K
    E = F(0, 1, 1, **kwargs) -B -C -H -J -K
    F_coeff = F(1, 0, 1, **kwargs) -A -C -G -J -K

    print(A, B, C, D, E, F_coeff, G, H, J, K)
    return A, B, C, D, E, F_coeff, G, H, J, K

def ellipsoid(x, y, z, ax=1.0, by=1.0, cz=1.0, center=Vector(0,0,0), rotation=FreeCAD.Rotation()):
    ''' for an ellipsoid center at the origin and axes coinciding with the x, y, and z axes
    The equation is x^2/ax^2 + y^2/by^2 + z^2/cz^2 - 1 = 0;
    If the origin is translated to x0, y0, z0 the equation becomes
    (x-x0)^2 / ax^2 + (y-y0)^2 / by^2 + (z-z0)^2 / cz^2 - 1 = 0;
    If the axes are subjected to a rotation R, then the equation becomes
    (x'-x0)^2 / ax^2 + (y'-y0)^2 / by^2 + (z'-z0)^2 / cz^2 - 1 = 0;
    where (x', y', z') = R^-1 (x, y, z)
    '''

    vprime = rotation.inverted()*(Vector(x, y, z) - center)

    x = vprime.x
    y = vprime.y
    z = vprime.z

    return (x/ax)**2 + (y/by)**2 + (z/cz)**2 - 1

def cylinder(x, y, z, radius=1, center=Vector(0,0,0), axis=Vector(0, 0, 1)):

    rotation = FreeCAD.Rotation(Vector(0, 0, 1), axis)
    vprime = rotation.inverted()*(Vector(x, y, z) - center)

    x = vprime.x
    y = vprime.y
    z = vprime.z

    return x*x + y*y - radius*radius

def elliptical_tube(x, y, z, dx=1, dy=1, center=Vector(0,0,0), rotation=FreeCAD.Rotation()):

    R = rotation.inverted()
    vprime = R*(Vector(x, y, z) - center)

    x = vprime.x
    y = vprime.y
    z = vprime.z

    return (x/dx)**2 + (y/dy)**2 - 1.0


def elliptical_cone(x, y, z, dx=1, dy=1, zHeight=1, center=Vector(0,0,0), rotation=FreeCAD.Rotation()):

    R = rotation.inverted()
    vprime = R*(Vector(x, y, z) - center)

    x = vprime.x
    y = vprime.y
    z = vprime.z

    return (x/dx)**2 + (y/dy)**2 - (zHeight - z)**2


def cone(x, y, z, center=Vector(0,0,0), axis=Vector(0, 0, 1), theta=1.0):

    rotation = FreeCAD.Rotation(Vector(0, 0, 1), axis)
    vprime = rotation.inverted()*(Vector(x, y, z) - center)


    x = vprime.x
    y = vprime.y
    z = vprime.z
    t = math.tan(theta)

    return x**2 + y**2 - (z*t)**2


def paraboloid(x, y, z, k1, k2, center=Vector(0,0,0), rotation=FreeCAD.Rotation()):

    vprime = rotation.inverted()*(Vector(x, y, z) - center)

    x = vprime.x
    y = vprime.y
    z = vprime.z

    return x**2 + y**2 - (k1*z + k2)

class SurfaceExporter:
    _ids = []  # dictionary of name vs id: __ids[name] = id
    _ids_dict = {}
    cached_surfaces = {}
    replacement_ids = {}

    def __init__(self, name, type, coeffs, boundary="transmission"):
        id = 1
        while id in SurfaceExporter._ids:
            id += 1
        SurfaceExporter._ids.append(id)
        SurfaceExporter._ids_dict[name] = id
#
        self.id = id
        self.type = type
        if name != "":
            self.name = name
        else:
            self.name = f"{type}_{id}"
        self.boundary = boundary
        self.coeffs = coeffs

        self.saved_state = vars(self).copy()

    def copy(self):
        return  # should be declared abstract

    @staticmethod
    def export_surfaces():
        for key in SurfaceExporter.cached_surfaces:
            surface = SurfaceExporter.cached_surfaces[key]
            surface._export()

    @staticmethod
    def reset_ids():
        SurfaceExporter._ids = []
        SurfaceExporter._ids_dict = {}
        SurfaceExporter.cached_surfaces = {}
        SurfaceExporter.replacement_ids = {}

    def _export(self):
        surface = ET.SubElement(geometry, 'surface')
        surface.attrib['id'] = str(self.id)
        surface.attrib['name'] = str(self.name)
        surface.attrib['type'] = str(self.type)
        surface.attrib['coeffs'] = str(self.coeffs)
        surface.attrib['boundary'] = self.boundary

    def export(self):
        key = self.mykey()
        if key not in self.cached_surfaces:
            SurfaceExporter.cached_surfaces[key] = self
        else:
            cached_surface = SurfaceExporter.cached_surfaces[key]
            SurfaceExporter.replacement_ids[self.id] = cached_surface.id

    def translate(self, T):
        return

    def rotate(self, R):
        return

    def mykey(self):
        s = ""
        for w in self.coeffs.strip().split():
            s += f" {float(w):.6e}"
        return s

    def __hash__(self):
        # hash coefficients to within 1 part in 10^6. This so when we compare two
        # surfaces we will consider them to be the same if all the coefficients agree
        # to within 1 part in 10^6
        s = []
        for w in self.coeffs.strip().split():
            s.append(float(f" {float(w):.6e}"))

        return hash(tuple(s))

    def __eq__(self, other):

        # note that if the coefficients match, then we return ==, eventhough the ids might be different
        if not (type(self) is type(other)):
            return False

        return hash(self) == hash(other)


class PlaneSurfaceExporter(SurfaceExporter):
    def __init__(self, name:str, normal:FreeCAD.Vector, D:float):
        self.normal = normal
        self.D = 0.1*D/self.normal.Length
        self.normal.normalize()
        self.to_coeffs()
        super().__init__(name, "plane", self.coeffs)

    def translate(self, T):
        T = 0.1 * T  # convert from mm to cm for openmc
        self.D += self.normal.dot(T)
        self.to_coeffs()

    def rotate(self, R):
        self.normal = R*self.normal
        self.to_coeffs()

    def to_coeffs(self):
        self.coeffs = f"{self.normal.x} {self.normal.y} {self.normal.z} {self.D}"

    def inRegion(self, point):
        pcm = 0.1*point

        return self.normal.dot(pcm) - self.D < 0


class SphereSurfaceExporter(SurfaceExporter):
    def __init__(self, name, center, radius):
        self.center = 0.1*center
        self.radius = 0.1*radius
        self.to_coeffs()
        super().__init__(name, "sphere", self.coeffs)
        self.saved_radius = radius
        self.saved_center = center

    def copy(self):
        return SphereSurfaceExporter(self.name, self.saved_center, self.saved_radius)

    def to_coeffs(self):
        self.coeffs = f"{self.center.x} {self.center.y} {self.center.z} {self.radius}"

    def translate(self, T):
        T = 0.1 * T  # convert from mm to cm for openmc
        self.center += T
        self.to_coeffs()

    def rotate(self, R):
        self.center = R*self.center
        self.to_coeffs()


class CylinderSurfaceExporter(SurfaceExporter):
    def __init__(self, name, center, axis, radius):
        # convert to quadric surface:
        self.center = 0.1*center
        self.axis = axis
        self.radius = 0.1*radius
        self.to_quadric()
        super().__init__(name, "quadric", self.coeffs)
        self.saved_radius = radius
        self.saved_center = center
        self.saved_axis = axis


    def copy(self):
        return CylinderSurfaceExporter(self.name, self.saved_center, self.saved_axis, self.saved_radius)

    def to_quadric(self):
        A, B, C, D, E, F, G, H, J, K = quadric_coeffs(cylinder, radius=self.radius,
                                                      center=self.center, axis=self.axis)

        self.coeffs = f"{A} {B} {C} {D} {E} {F} {G} {H} {J} {K}"

    def translate(self, T):
        T = 0.1 * T  # convert from mm to cm for openmc
        self.center += T
        self.to_quadric()


    def rotate(self, R):
        self.axis = R*self.axis
        self.center = R*self.center
        self.to_quadric()


class EllipticalCylinderSurfaceExporter(SurfaceExporter):
    def __init__(self, name, center,dx, dy):
        # convert to quadric surface:
        self.center = 0.1*center
        self.dx = 0.1*dx
        self.dy = 0.1*dy
        self.rotation = FreeCAD.Rotation()
        self.to_quadric()
        super().__init__(name, "quadric", self.coeffs)
        self.saved_dx = dx
        self.saved_dy = dy
        self.saved_rotation = FreeCAD.Rotation()
        self.saved_center = center


    def copy(self):
        return EllipticalCylinderSurfaceExporter(self.name, self.saved_center, self.saved_dx, self.saved_dy)


    def to_quadric(self):
        A, B, C, D, E, F, G, H, J, K = quadric_coeffs(elliptical_tube, dx=self.dx, dy=self.dy,
                                                      center=self.center, rotation=self.rotation)

        self.coeffs = f"{A} {B} {C} {D} {E} {F} {G} {H} {J} {K}"

    def translate(self, T):
        T = 0.1 * T  # convert from mm to cm for openmc
        self.center += T
        self.to_quadric()


    def rotate(self, R):
        self.rotation = R*self.rotation
        self.center = R*self.center
        self.to_quadric()


class EllipticalConeSurfaceExporter(SurfaceExporter):
    def __init__(self, name, center, dx, dy, zHeight):
        # convert to quadric surface:
        self.center = 0.1*center
        self.dx = dx  # this is  ration, so no conversion from mm to cm
        self.dy = dy
        self.zHeight = 0.1*zHeight
        self.rotation = FreeCAD.Rotation()
        self.to_quadric()
        super().__init__(name, "quadric", self.coeffs)
        self.saved_center = center
        self.saved_dx = dx
        self.saved_dy = dy
        self.saved_zHeight = zHeight
        self.saved_rotation = FreeCAD.Rotation()


    def copy(self):
        return EllipticalConeSurfaceExporter(self.name, self.saved_center, self.saved_dx, self.saved_dy, self.saved_zHeight)


    def to_quadric(self):
        A, B, C, D, E, F, G, H, J, K = quadric_coeffs(elliptical_cone, dx=self.dx, dy=self.dy,
                                                      zHeight=self.zHeight,
                                                      center=self.center, rotation=self.rotation)

        self.coeffs = f"{A} {B} {C} {D} {E} {F} {G} {H} {J} {K}"

    def translate(self, T):
        T = 0.1 * T  # convert from mm to cm for openmc
        self.center += T
        self.to_quadric()


    def rotate(self, R):
        self.rotation = R*self.rotation
        self.center = R*self.center
        self.to_quadric()


class ConeSurfaceExporter(SurfaceExporter):
    def __init__(self, name, center, axis, theta):
        '''
        :param: center: cone vertex posidion
        :param: axis: unit vector directiom of cone axis
        :param: theta: cone half angle, in radians
        '''
        # convert to quadric surface:
        self.center = 0.1*center
        self.axis = axis
        self.theta = theta

        self.to_quadric()
        super().__init__(name, "quadric", self.coeffs)

        self.saved_center = center
        self.saved_axis = axis
        self.saved_theta = theta

    def copy(self):
        return ConeSurfaceExporter(self.name, self.saved_center, self.saved_axis, self.saved_theta)

    def to_quadric(self):
        A, B, C, D, E, F, G, H, J, K = quadric_coeffs(cone, center=self.center, axis=self.axis, theta=self.theta)
        self.coeffs = f"{A} {B} {C} {D} {E} {F} {G} {H} {J} {K}"


    def translate(self, T):
        T = 0.1 * T  # convert from mm to cm for openmc
        self.center += T
        self.to_quadric()


    def rotate(self, R):
        self.axis = R*self.axis
        self.center = R*self.center
        self.to_quadric()


class EllipsoidSurfaceExporter(SurfaceExporter):
    def __init__(self, name, ax, by, cz, center=Vector(0, 0, 0), rotation=FreeCAD.Rotation()):
        '''
        :param: center: cone vertex posidion
        :param: axis: unit vector directiom of cone axis
        :param: theta: cone half angle, in radians
        '''
        # convert to quadric surface:
        self.ax = 0.1*ax
        self.by = 0.1*by
        self.cz = 0.1*cz
        self.center = 0.1*center
        self.rotation = rotation

        self.to_quadric()
        super().__init__(name, "quadric", self.coeffs)
        self.saved_ax = ax
        self.saved_by = by
        self.saved_cz = cz
        self.saved_center = center
        self.saved_rotation = rotation


    def copy(self):
        return EllipsoidSurfaceExporter(self.name, self.saved_ax, self.saved_by, self.saved_cz, self.saved_center, self.saved_rotation)

    def to_quadric(self):
        A, B, C, D, E, F, G, H, J, K = quadric_coeffs(ellipsoid, ax=self.ax, by=self.by, cz=self.cz,
                                                      center=self.center, rotation=self.rotation)
        self.coeffs = f"{A} {B} {C} {D} {E} {F} {G} {H} {J} {K}"


    def translate(self, T):
        T = 0.1 * T  # convert from mm to cm for openmc
        self.center += T
        self.to_quadric()


    def rotate(self, R):
        self.center = R*self.center  # is this needed
        self.rotation = R*self.rotation
        self.to_quadric()


class ParaboloidSurfaceExporter(SurfaceExporter):
    def __init__(self, name, rlo, rhi, dz, center=Vector(0, 0, 0), rotation=FreeCAD.Rotation()):
        '''

        Equation of paraboloid is given by
        (x^2+y^2) - rho^2 = k1 z + k2
        :param: rlo: k1 * (-dz) + k2; value of rho at z=-dz
        :param: rhi: k1 * (+dz) + k2  value of rho at z=+dz
        :param: dx: half height of parbolid
        :param: center: center of paraboloid
        :param: rotation: rotaion of axis from z-axis
        '''
        # Equation of Paraboloid in geant4 is:
        # (x^2+y^2) = rho^2 - k1 z + k2
        # k1 and k2 determined from
        # rlo^2 = k1 *(-dz) + k2
        # rhi^2 = k1 *(+dz) + k2
        # ==> k1 = (rhi^2 - rlo^2)/2 dz
        # ==> k2 = (rlo^2+rhi^2)/2

        # convert to quadric surface:
        dz *= 0.1  # convert to cm
        rlo *= 0.1
        rhi *= 0.1
        self.k1 = (rhi*rhi - rlo*rlo)/(2*dz)
        self.k2 = (rhi*rhi + rlo*rlo)/2
        self.center = 0.1*center
        self.rotation = rotation

        self.to_quadric()
        super().__init__(name, "quadric", self.coeffs)

        self.saved_rlo = rlo
        self.saved_rhi = rhi
        self.saved_dz = dz
        self.saved_center = center
        self.saved_rotation = rotation

    def copy(self):
        return ParaboloidSurfaceExporter(self.name, self.saved_rlo, self.saved_rhi, self.saved_dz, self.saved_center, self.saved_rotation)

    def to_quadric(self):
        A, B, C, D, E, F, G, H, J, K = quadric_coeffs(paraboloid, k1=self.k1, k2=self.k2,
                                                      center=self.center, rotation=self.rotation)
        self.coeffs = f"{A} {B} {C} {D} {E} {F} {G} {H} {J} {K}"


    def translate(self, T):
        T = 0.1 * T  # convert from mm to cm for openmc
        self.center += T
        self.to_quadric()


    def rotate(self, R):
        self.center = R*self.center  # is this needed
        self.rotation = R*self.rotation
        self.to_quadric()


class SolidExporter:
    # Abstract class to export object as gdml
    _exported = []  # a list of already exported objects
    solidExporters = {
        "GDMLArb8": "AutoTessellateExporter",
        "GDMLBox": "GDMLBoxExporter",
        "GDMLCone": "GDMLConeExporter",
        "GDMLcutTube": "GDMLcutTubeExporter",
        "GDMLElCone": "GDMLElConeExporter",
        "GDMLEllipsoid": "GDMLEllipsoidExporter",
        "GDMLElTube": "GDMLElTubeExporter",
        "GDMLHype": "GDMLHypeExporter",
        "GDMLOrb": "GDMLOrbExporter",
        "GDMLPara": "AutoTessellateExporter",
        "GDMLParaboloid": "GDMLParaboloidExporter",
        "GDMLPolycone": "GDMLPolyconeExporter",
        "GDMLGenericPolycone": "GDMLGenericPolyconeExporter",
        "GDMLPolyhedra": "AutoTessellateExporter",
        "GDMLGenericPolyhedra": "AutoTessellateExporter",
        "GDMLSphere": "GDMLSphereExporter",
        "GDMLTessellated": "AutoTessellateExporter",
        "GDMLSampledTessellated": "AutoTessellateExporter",
        "GDMLGmshTessellated": "AutoTessellateExporter",
        "GDMLTetra": "AutoTessellateExporter",
        "GDMLTetrahedron": "AutoTessellateExporter",
        "GDMLTorus": "GDMLTorusExporter",
        "GDMLTrap": "AutoTessellateExporter",
        "GDMLTrd": "AutoTessellateExporter",
        "GDMLTube": "GDMLTubeExporter",
        "GDMLTwistedbox": "GDMLTwistedboxExporter",
        "GDMLTwistedtrap": "GDMLTwistedtrapExporter",
        "GDMLTwistedtrd": "GDMLTwistedtrdExporter",
        "GDMLTwistedtubs": "GDMLTwistedtubsExporter",
        "GDMLXtru": "AutoTessellateExporter",
        "Mesh::Feature": "AutoTessellateExporter",
        "Part::MultiFuse": "MultiFuseExporter",
        "Part::MultiCommon": "MultiCommonExporter",
        "Part::Extrusion": "ExtrusionExporter",
        "Part::Revolution": "RevolutionExporter",
        "Part::Box": "BoxExporter",
        "Part::Cylinder": "CylinderExporter",
        "Part::Torus": "TorusExporter",
        "Tube": "TubeExporter",
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
        """Return True for objects whose primary identity is their own Shape."""
        print(f"isSolid {obj.Label}")
        # return hasattr(obj, 'Shape')  # does not work. App::Parts have Shape, but they are not solids!

        obj1 = obj
        if obj.TypeId == "App::Link":
            obj1 = obj.LinkedObject

        if not hasattr(obj, "Shape") or obj.Shape.isNull():
            return False

        # Exclude known containers / special cases
        if obj.isDerivedFrom("App::Part"):
            return False  # container, aggregate shape

        if obj.isDerivedFrom("PartDesign::Body"):
            # optional: treat Body as container rather than primitive
            return False

        # we tread arrays of parts as containers, not as solids
        if isArrayType(obj1) and obj1.Base.isDerivedFrom("App::Part"):
            return False

        # Part::Compound is a grey zone:
        # treat it as "real shape" or as aggregate depending on your needs
        # Example: treat as aggregate and skip here:
        if obj.TypeId in ("Part::Compound", "Part::CompoundPython"):
            return False

        # Everything else derived from Part::Feature is fair game
        if obj.isDerivedFrom("Part::Feature"):
            return True

        if obj1.TypeId == "Part::FeaturePython":
            if hasattr(obj, 'Shape') and not obj.Shape.isNull():
                return True

        return False

    @staticmethod
    def getExporter(obj):
        if hasattr(obj, 'LinkedObject'):
            solidExporter = SolidExporter.getExporter(obj.LinkedObject)
            if solidExporter is not None:
                return type(solidExporter)(obj)

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
                name = obj.Name
                if name[:4] == 'Tube':
                    return TubeExporter(obj)

                # default, fall thru
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
            if hasattr(obj, 'Shape') and not obj.Shape.isNull():
                print(f"{obj.Label} does not have a Native Solid Exporter, Using AutoTessellator")
                return AutoTessellateExporter(obj)
        else:
            if hasattr(obj, 'Shape') and not obj.Shape.isNull():
                print(f"{obj.Label} does not have a native Solid Exporter, Using AutoTessellator")
                return AutoTessellateExporter(obj)

        return None

    def __init__(self, obj):
        self.obj = obj
        self._name = NameManager.getName(obj)
        self.region = None
        self.surfaces = []

    def generate_surfaces(self):
        ''' build the list of surfaces. Implemented by implementors'''
        return

    def name(self):
        return self._name

    def position(self):
        # return self.obj.Placement.Base  we ar expect each solid to translate/rotate its surfaces
        return FreeCAD.Vector()

    def rotation(self):
        return FreeCAD.Rotation()
        # return self.obj.Placement.Rotation. we expect objects to rotate their surfaces


    def placement(self):
        return FreeCAD.Placement(self.position(), self.rotation())


    def exported(self):
        return self.obj in SolidExporter._exported

    def export(self):
        if self.region is None:
            self.generate_surfaces()
        for surf in self.surfaces:
            surf.export()
        return

    def rotate(self, R):
        for surf in self.surfaces:
            surf.rotate(R)

    def translate(self, T):
        for surf in self.surfaces:
            surf.translate(T)

    def get_region(self):
        if self.region is None:
            self.generate_surfaces()
        return self.region

    def set_boundary_type(self, boundary_type):
        if self.region is None:
            self.generate_surfaces()
        for surf in self.surfaces:
            surf.boundary=boundary_type

    def position_globally(self):
        identity = FreeCAD.Placement()

        placement = get_global_placement(self.obj)

        if placement != identity:
            rot = placement.Rotation
            trans = placement.Base
            for surf in self.surfaces:
                surf.rotate(rot)
                surf.translate(trans)

    def getMult(self):
        ''' return multiplier for length units of self.obj'''
        unit = "mm"  # set default
        # Watch for unit and lunit
        # print('getMult : '+str(fp))
        if hasattr(self.obj, "lunit"):
            unit = self.obj.lunit
        elif hasattr(self.obj, "unit"):
            unit = self.obj.unit
        elif hasattr(self.obj, "attrib"):
            if "unit" in self.obj.attrib:
                unit = self.obj.attrib["unit"]
            elif "lunit" in self.obj.attrib:
                unit = self.obj.attrib["lunit"]
        else:
            return 1

        # The exporters will convert to cm. Here we convert to mm
        unitsDict = {
            "mm": 1,
            "cm": 10.0,
            "m": 1000.,
            "um": 0.001,
            "nm": 1.0e-6,
            # "dm": 100,   decimeter not recognized by geant
            "km": 1000000.0,
        }
        if unit in unitsDict:
            return unitsDict[unit]

        print("unit not handled : " + unit)


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


class BoxExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        self.surfaces = []
        placement = self.obj.Placement

        normal = Vector(1, 0, 0)
        D = 0
        x1surface = PlaneSurfaceExporter(f"{self.obj.Label}_x1_plane", normal, D)
        D = self.obj.Length.Value
        x2surface = PlaneSurfaceExporter(f"{self.obj.Label}_x2_plane", normal, D)

        normal = Vector(0, 1, 0)
        D = 0
        y1surface = PlaneSurfaceExporter(f"{self.obj.Label}_y1_plane", normal, D)
        D = self.obj.Width.Value
        y2surface = PlaneSurfaceExporter(f"{self.obj.Label}_y2_plane", normal, D)

        normal = Vector(0, 0, 1)
        D = 0
        z1surface = PlaneSurfaceExporter(f"{self.obj.Label}_z1_plane", normal, D)
        D = self.obj.Height.Value
        z2surface = PlaneSurfaceExporter(f"{self.obj.Label}_z2_plane", normal, D)

        self.surfaces = [x1surface, x2surface, y1surface, y2surface, z1surface, z2surface]
        self.region = Region(f"+{x1surface.id} -{x2surface.id} +{y1surface.id} -{y2surface.id} +{z1surface.id} -{z2surface.id}")

        self.position_globally()



class CylinderExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        normal = Vector(0, 0, 1)
        D = self.obj.Height.Value
        top_surface = PlaneSurfaceExporter(f"{self.obj.Label}_top", normal, D)
        D = 0
        bottom_surface = PlaneSurfaceExporter(f"{self.obj.Label}_bot", normal, D)

        axis = Vector(0, 0, 1)
        center = Vector(0, 0, 0)
        radius = self.obj.Radius.Value
        cylinder_surface = CylinderSurfaceExporter(f"{self.name()}_cylinder", center, axis, radius)

        self.surfaces = [top_surface, bottom_surface, cylinder_surface]
        self.region = Region(f"-{cylinder_surface.id} +{bottom_surface.id} -{top_surface.id}")

        self.position_globally()


class TubeExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        normal = Vector(0, 0, 1)

        D = self.obj.Height.Value
        top_surface = PlaneSurfaceExporter(f"{self.obj.Label}_top)", normal, D)
        D = 0
        bottom_surface = PlaneSurfaceExporter(f"{self.obj.Label}_bot)", normal, D)

        if self.obj.InnerRadius != 0:
            radius = self.obj.InnerRadius.Value
            axis = normal
            center = Vector(0, 0, 0)
            inner_surface = CylinderSurfaceExporter(f"{self.name()}_ir)", center, axis, radius)
        else:
            inner_surface = None

        radius = self.obj.OuterRadius.Value
        outer_surface = CylinderSurfaceExporter(f"{self.name()}_ot)", center, axis, radius)

        self.surfaces = [top_surface, bottom_surface, outer_surface]
        if inner_surface is not None:
            self.surfaces.append(inner_surface)

        region_expr = f"-{top_surface.id} +{bottom_surface.id} -{outer_surface.id}"
        if inner_surface is not None:
            region_expr += f" +{inner_surface.id}"

        self.region = Region(region_expr)

        self.position_globally()

class GDMLElTubeExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        axis = Vector(0, 0, 1)
        mul = self.getMult(self.obj)

        D = mul*self.obj.dz
        center = Vector(0, 0, 0)

        name = NameManager.getName(self.obj)
        top_surface = PlaneSurfaceExporter(f"{name}_top", axis, D)
        bottom_surface = PlaneSurfaceExporter(f"{name}_bot", axis, -D)

        dx = mul*self.obj.dx
        dy = mul*self.obj.dy
        surf = EllipticalCylinderSurfaceExporter(f"{name}", center, dx, dy)

        self.surfaces = [top_surface, bottom_surface, surf]
        self.region = Region(f"-{surf.id} +{bottom_surface.id} -{top_surface.id}")

        self.position_globally()


class ConeExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):

        # Cone half angle
        r1 = self.obj.Radius1.Value
        r2 = self.obj.Radius2.Value
        h = self.obj.Height.Value
        theta = math.atan(abs(r2-r1)/h)
        if r1 > r2:
            axis = Vector(0, 0, 1)
            center = Vector(0, 0, r1/math.tan(theta))
            surface = ConeSurfaceExporter(self.name(), center, axis, theta)
            bottom_plane = PlaneSurfaceExporter(self.name()+'_bot', axis, 0)
            top_plane = PlaneSurfaceExporter(self.name()+'_top', axis, h)
        elif r2 > r1:
            axis = Vector(0, 0, -1)
            center = Vector(0, 0, -r1/math.tan(theta))
            surface = ConeSurfaceExporter(self.name(), center, axis, theta)
            bottom_plane = PlaneSurfaceExporter(self.name()+'_bot', axis, 0)
            top_plane = PlaneSurfaceExporter(self.name()+'_top', axis, h)
        else:
            center = Vector(0, 0, 0)
            axis = Vector(0, 0, 1)
            surface = ConeSurfaceExporter(self.name(), center, axis, r1)
            bottom_plane = PlaneSurfaceExporter(self.name()+'_bot', axis, 0)
            top_plane = PlaneSurfaceExporter(self.name()+'_top', axis, h)

        self.surfaces = [surface, bottom_plane, top_plane]
        self.region = Region(f'-{surface.id} +{bottom_plane.id} -{top_plane.id}')

        angle = self.obj.Angle.Value
        if angle != 360:
            phi0_normal = Vector(0, 1, 0)
            phi0_plane = PlaneSurfaceExporter(self.name()+'_phi0', phi0_normal, 0)

            phi1_normal = Vector(math.cos(math.radians(angle+90)), math.sin(math.radians(angle+90)), 0)
            phi1_plane = PlaneSurfaceExporter(self.name()+'_phi0', phi1_normal, 0)
            self.surfaces += [phi0_plane, phi1_plane]

            if phi0_normal.cross(phi1_normal).z > 0:
                self.region = Region(f'-{surface.id} +{bottom_plane.id} -{top_plane.id} +{phi0_plane.id} -{phi1_plane.id}')
            else:
                self.region = Region(f'-{surface.id} +{bottom_plane.id} -{top_plane.id} (+{phi0_plane.id} | -{phi1_plane.id})')



        self.position_globally()


class SphereExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        self.surfaces = []
        center = Vector(0, 0, 0)  # Note off -center spheres are handled by their position placement
        radius = self.obj.Radius.Value
        sphere_surface = SphereSurfaceExporter(f"{self.name()}_surf", center, radius)
        self.surfaces.append(sphere_surface)

        if self.obj.Angle1 != 0:
            z1 = self.obj.Radius * math.sin(math.radians(self.obj.Angle1))
            normal = Vector(0, 0, 1)
            D = z1
            z1surface = PlaneSurfaceExporter(f"{self.obj.Label}_z1_plane", normal, D)
            self.surfaces.append(z1surface)

        if self.obj.Angle2 != 0:
            z2 = self.obj.Radius * math.sin(math.radians(self.obj.Angle2))
            normal = Vector(0, 0, 1)
            D = z2
            z2surface = PlaneSurfaceExporter(f"{self.obj.Label}_z2_plane", normal, D)
            self.surfaces.append(z2surface)

        if self.obj.Angle3 != 360:
            phi0_normal = Vector(0, 1, 0)
            D = 0
            phi0_plane = PlaneSurfaceExporter(f"{self.obj.Label}_pho0_plane", phi0_normal, D)
            self.surfaces.append(phi0_plane)

            nx = -math.sin(math.radians(self.obj.Angle3))
            ny = math.cos(math.radians(self.obj.Angle3))
            phi1_normal = Vector(nx, ny, 0)

            phi1_plane = PlaneSurfaceExporter(f"{self.obj.Label}_pho1_plane", phi1_normal, D)
            self.surfaces.append(phi1_plane)

        region = f"-{sphere_surface.id}"
        if self.obj.Angle1 != 0:
            region += f" +{z1surface.id}"
        if self.obj.Angle2 != 0:
            region += f" -{z2surface.id}"

        if self.obj.Angle3 != 360:
            if phi0_normal.cross(phi1_normal).z > 0:
                region += f" +{phi0_plane.id} -{phi1_plane.id}"
            else:
                region += f"(+{phi0_plane.id} | -{phi1_plane.id})"

        self.region = Region(region)

        self.position_globally()


class BooleanExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)
        baseExporter = SolidExporter.getExporter(self.obj.Base)
        basePlacement = baseExporter.placement()
        self._placement = self.obj.Placement * basePlacement
        # self._placement = get_global_placement(obj)  # according to GPT-5.1. Does not work!


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

    def generate_surfaces(self):
        self.surfaces = []
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

            solidExporter = SolidExporter.getExporter(boolobj.Tool)
            ref2[boolobj] = solidExporter
            if self.isBoolean(boolobj.Tool):
                tmpList.append(boolobj.Tool)
                boolsList.append(boolobj.Tool)

        # Now tmpList is empty and boolsList has list of all booleans
        self.region = Region("")
        self.surfaces = []
        for boolobj in reversed(boolsList):
            operation = self.boolOperation(boolobj)
            if operation is None:
                continue
            solidName = boolobj.Label
            solidExporter1 = ref1[boolobj]
            solidExporter2 = ref2[boolobj]
            region1 = solidExporter1.get_region()  # this will generate the surfaces
            region2 = solidExporter2.get_region()  # this will generate the surfaces

            self.surfaces += solidExporter1.surfaces
            self.surfaces += solidExporter2.surfaces

            if operation == 'union':
                self.region = region1.union(region2)
            elif operation == 'subtraction':
                self.region = region1.cut(region2)
            elif operation == 'intersection':
                self.region = region1.intersection(region2)

        if self._placement != FreeCAD.Placement():
            translation = self._placement.Base
            rotation = self._placement.Rotation
            for surf in self.surfaces:
                surf.rotate(rotation)
                surf.translate(translation)


class GDMLBoxExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        mul = self.getMult()
        normal = Vector(1, 0, 0)
        D = -self.obj.x/2 * mul
        x1surface = PlaneSurfaceExporter(f"{self.obj.Label}_x1_plane", normal, D)
        D = self.obj.x/2 * mul
        x2surface = PlaneSurfaceExporter(f"{self.obj.Label}_x2_plane", normal, D)

        normal = Vector(0, 1, 0)
        D = -self.obj.y/2 * mul
        y1surface = PlaneSurfaceExporter(f"{self.obj.Label}_y1_plane", normal, D)
        D = self.obj.y/2 * mul
        y2surface = PlaneSurfaceExporter(f"{self.obj.Label}_y2_plane", normal, D)

        normal = Vector(0, 0, 1)
        D = -self.obj.z/2 * mul
        z1surface = PlaneSurfaceExporter(f"{self.obj.Label}_z1_plane", normal, D)
        D = self.obj.z/2 * mul
        z2surface = PlaneSurfaceExporter(f"{self.obj.Label}_z2_plane", normal, D)

        self.surfaces = [x1surface, x2surface, y1surface, y2surface, z1surface, z2surface]
        self.region = Region(f"+{x1surface.id} -{x2surface.id} +{y1surface.id} -{y2surface.id} +{z1surface.id} -{z2surface.id}")

        self.position_globally()


class GDMLConeExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        from .GDMLObjects import checkFullCircle, getAngleRad
        def cone_surface(name_suffix, r1, r2, h):
            theta = math.atan(abs(r1-r2)/h)
            if abs(r1-r2) < 1.0e-9:  # a cylinder, not a cone
                return CylinderSurfaceExporter(self.name, Vector(0, 0, 0), Vector(0, 0, 1), r1)

            if r1 > r2:  # cone base at bottom, cone vertex at top
                H = r1/math.tan(theta)  # Height of cone, from base to vertex
                axis = Vector(0, 0, 1)  #  has to be z-axis for rotations to work correcly
                center = (H - h/2) * Vector(0, 0, 1)  # center is location of vertex
                return ConeSurfaceExporter(name+name_suffix, center, axis, theta)
            else:  # r1<r2, cone base at top, vertex at bottom
                H = r2/math.tan(theta)  # Height of cone, from base to vertex
                axis = Vector(0, 0, 1)  # has to be z-axis
                center = (H - h/2) * Vector(0, 0, -1)  # center is location of vertex
                return ConeSurfaceExporter(name+name_suffix, center, axis, theta)

        # inner cone:
        region_expr = ""
        mul = self.getMult()
        name = NameManager.getName(self.obj)

        if self.obj.rmin1 != 0 or self.obj.rmin2 != 0:
            inner_cone = cone_surface('_inner_cone', self.obj.rmin1*mul,
                                      self.obj.rmin2*mul, self.obj.z*mul)
            self.surfaces.append(inner_cone)
            region_expr += f"+{inner_cone.id} "

        # outer cone
        outer_cone = cone_surface('_outer_cone_', self.obj.rmax1*mul, self.obj.rmax2*mul,
                                  self.obj.z*mul)

        self.surfaces.append(outer_cone)
        region_expr += f"-{outer_cone.id} "

        bottom_plane = PlaneSurfaceExporter(self.obj.Label+'_bot', Vector(0, 0, 1), -self.obj.z/2*mul)
        top_plane = PlaneSurfaceExporter(self.obj.Label+'_top', Vector(0, 0, 1), self.obj.z/2*mul)

        self.surfaces += [bottom_plane, top_plane]
        region_expr += f"+{bottom_plane.id} -{top_plane.id}"

        if not checkFullCircle(self.obj.aunit, self.obj.deltaphi):
            startPhi = getAngleRad(self.obj.aunit, self.obj.startphi)
            nx = -math.sin(startPhi)
            ny = math.cos(startPhi)
            phi0_normal = Vector(nx, ny, 0)
            D = 0

            phi0_plane = PlaneSurfaceExporter(f"{self.obj.Label}_phi0_plane", phi0_normal, D)
            self.surfaces.append(phi0_plane)

            deltaphi = getAngleRad(self.obj.aunit, self.obj.deltaphi)
            endphi = startPhi + deltaphi
            nx = -math.sin(endphi)
            ny = math.cos(endphi)
            phi1_normal = Vector(nx, ny, 0)

            phi1_plane = PlaneSurfaceExporter(f"{self.obj.Label}_phi1_plane", phi1_normal, D)
            self.surfaces.append(phi1_plane)

            if phi0_normal.cross(phi1_normal).z > 0:
                region_expr += f"+{phi0_plane.id} -{phi1_plane.id}"
            else:
                region_expr += f"(+{phi0_plane.id} | -{phi1_plane.id})"

        self.region = Region(region_expr)
        self.position_globally()


class GDMLcutTubeExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        from .GDMLObjects import checkFullCircle, getAngleRad

        region_expr = ""
        axis = Vector(0, 0, 1)
        mul = self.getMult()
        center = Vector(0, 0, 0)
        radius = self.obj.rmin * mul
        if radius != 0:
            surf = CylinderSurfaceExporter(f"{self.name()}_ir", center, axis, radius)
            self.surfaces.append(surf)
            region_expr += f"+{surf.id} "

        radius = self.obj.rmax * mul
        surf = CylinderSurfaceExporter(f"{self.name()}_or", center, axis, radius)
        self.surfaces.append(surf)
        region_expr += f"-{surf.id} "

        normal_top = Vector(self.obj.highX, self.obj.highY, self.obj.highZ)
        normal_top.normalize()
        D_top = Vector(0, 0, mul*self.obj.z/2).dot(normal_top)
        surf = PlaneSurfaceExporter(f"{self.name()}_top", normal_top, D_top)
        self.surfaces.append(surf)
        region_expr += f"-{surf.id} "

        normal_bot = Vector(self.obj.lowX, self.obj.lowY, self.obj.lowZ)
        normal_bot.normalize()
        # D_bot = mul*self.obj.z/2  # not minus because the normal at the bottom points away from the bottom
        # this is better calculated as Vector(0, 0, -z/2).dot(nromal)
        D_bot = Vector(0, 0, -mul*self.obj.z/2).dot(normal_bot)
        surf = PlaneSurfaceExporter(f"{self.name()}_bot", normal_bot, D_bot)
        self.surfaces.append(surf)
        region_expr += f"-{surf.id} "

        if not checkFullCircle(self.obj.aunit, self.obj.deltaphi):
            startPhi = getAngleRad(self.obj.aunit, self.obj.startphi)
            nx = -math.sin(startPhi)
            ny = math.cos(startPhi)
            phi0_normal = Vector(nx, ny, 0)
            D = 0
            phi0_plane = PlaneSurfaceExporter(f"{self.obj.Label}_phi0_plane", phi0_normal, D)
            self.surfaces.append(phi0_plane)

            deltaphi = getAngleRad(self.obj.aunit, self.obj.deltaphi)
            endphi = startPhi + deltaphi
            nx = -math.sin(endphi)
            ny = math.cos(endphi)
            phi1_normal = Vector(nx, ny, 0)

            phi1_plane = PlaneSurfaceExporter(f"{self.obj.Label}_phi1_plane", phi1_normal, D)
            self.surfaces.append(phi1_plane)

            if phi0_normal.cross(phi1_normal).z > 0:
                region_expr += f"+{phi0_plane.id} -{phi1_plane.id}"
            else:
                region_expr += f"(+{phi0_plane.id} | -{phi1_plane.id})"


        self.region = Region(region_expr)
        self.position_globally()


class GDMLElConeExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        mul = self.getMult()
        dx = self.obj.dx
        dy = self.obj.dy
        zcut = mul*self.obj.zcut
        zmax = mul*self.obj.zmax
        name = NameManager.getName(self.obj)
        center = Vector(0, 0, 0)
        surf = EllipticalConeSurfaceExporter(name+'_cone', center, dx, dy, zmax)
        self.surfaces.append(surf)

        normal = Vector(0, 0, 1)
        bot_plane = PlaneSurfaceExporter(name+'_bot', normal, -zcut)
        top_plane = PlaneSurfaceExporter(name+'_top', normal, zcut)
        self.surfaces += [bot_plane, top_plane]

        self.region = Region(f"-{surf.id} +{bot_plane.id} -{top_plane.id}")

        self.position_globally()


class GDMLEllipsoidExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)


    def generate_surfaces(self):
        mul = self.getMult()
        name = NameManager.getName(self.obj)
        surf1 = EllipsoidSurfaceExporter(name, mul*self.obj.ax, mul*self.obj.by, mul*self.obj.cz)
        self.surfaces = [surf1]
        region_expr = f"-{surf1.id}"
        if hasattr(self.obj, 'zcut1'):
            bot_plane = PlaneSurfaceExporter(name+'_zcut1', Vector(0, 0, 1), self.obj.zcut1)
            self.surfaces.append(bot_plane)
            region_expr += f' +{bot_plane.id}'
        if hasattr(self.obj, 'zcut2'):
            top_plane = PlaneSurfaceExporter(name+'_zcut2', Vector(0, 0, 1), self.obj.zcut2)
            self.surfaces.append(top_plane)
            region_expr += f' -{top_plane.id}'

        self.region = Region(region_expr)
        self.position_globally()


class GDMLHypeExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        from .GDMLObjects import getAngleRad

        name = NameManager.getName(self.obj)

        mul = self.getMult()
        name = NameManager.getName(self.obj)
        rmin = mul*self.obj.rmin
        rmax = mul*self.obj.rmax
        z = mul*self.obj.z
        outst = getAngleRad(self.obj.aunit, self.obj.outst)
        inst = getAngleRad(self.obj.aunit, self.obj.inst)

        # this should probably be a global variable, but
        # for now adopt the value used in geant4.10.07.p02
        NUMBER_OF_DIVISIONS = 36
        sqrtan1 = math.tan(inst)
        sqrtan1 *= sqrtan1
        sqrtan2 = math.tan(outst)
        sqrtan2 *= sqrtan2

        # Prepare two polylines
        ns = NUMBER_OF_DIVISIONS
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

        self.region = Region("")

        planes_dict = {}
        outer_region = Region("")
        for i in range(0, nz2-1):
            v0 = Vector(rr[i], 0, zz[i])
            v1 = Vector(rr[i+1], 0, zz[i+1])
            surface = cone_from_line_segment(v0, v1)
            self.surfaces.append(surface)
            edge_region = f"-{surface.id} "
            for v in [v0, v1]:
                if v.z in planes_dict:
                    plane = planes_dict[v.z]
                else:
                    plane = PlaneSurfaceExporter(", Vector(0, 0, 1", v.z)
                    self.surfaces.append(plane)
                if v==v0:
                    edge_region += f"+{plane.id} "
                else:
                    edge_region += f"-{plane.id} "
            outer_region = outer_region.union(edge_region)

        self.region = outer_region

        if rmin != 0:
            #
            # solid generated by internal hyperboloid
            dz1 = z / (nz1 - 1)
            zz = [halfZ - dz1 * i for i in range(0, nz1)]
            rr = [math.sqrt(sqrtan1 * zi * zi + rmin * rmin) for zi in zz]

            inner_region = Region("")
            for i in range(0, nz1-1):
                v0 = Vector(rr[i], 0, zz[i])
                v1 = Vector(rr[i+1], 0, zz[i+1])
                surface = cone_from_line_segment(v0, v1)
                self.surfaces.append(surface)
                edge_region = f"-{surface.id} "
                for v in [v0, v1]:
                    if v.z in planes_dict:
                        plane = planes_dict[v.z]
                    else:
                        plane = PlaneSurfaceExporter(", Vector(0, 0, 1", v.z)
                        self.surfaces.append(plane)
                    if v == v0:
                        edge_region += f"+{plane.id} "
                    else:
                        edge_region += f"-{plane.id} "
                inner_region = inner_region.union(edge_region)

            self.region = self.region.cut(inner_region)

        top_plane = PlaneSurfaceExporter(name+'_top', Vector(0, 0, 1), z/2)
        bot_plane = PlaneSurfaceExporter(name+'_top', Vector(0, 0, 1), -z/2)
        self.surfaces += [top_plane, bot_plane]
        self.region = self.region.intersection(Region(f"-{top_plane.id} +{bot_plane.id}"))

        self.position_globally()


class GDMLParaboloidExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        mul = self.getMult()
        name = NameManager.getName(self.obj)
        rlo = mul*self.obj.rlo
        rhi = mul*self.obj.rhi
        dz = mul*self.obj.dz

        surf = ParaboloidSurfaceExporter(name, rlo, rhi, dz)
        top_surface = PlaneSurfaceExporter(name+'_top', Vector(0, 0, 1), dz)
        bot_surface = PlaneSurfaceExporter(name+'_bot', Vector(0, 0, 1), -dz)

        self.surfaces = [surf, top_surface, bot_surface]
        self.region = Region(f"-{surf.id} +{bot_surface.id} -{top_surface.id}")

        self.position_globally()


class GDMLOrbExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        mul = self.getMult()
        center = Vector(0, 0, 0)
        radius = self.obj.rmin * mul
        surf = SphereSurfaceExporter(f"{self.name()}", center, radius)
        self.surfaces.append(surf)
        self.region = Region(f"-{surf.id}")
        self.position_globally()


class GDMLPolyconeExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        from .GDMLObjects import getAngleRad

        name = NameManager.getName(self.obj)
        mul = self.getMult()
        planes_dict = {}
        phi0 = getAngleRad(self.obj.aunit, self.obj.startphi)
        deltaphi = getAngleRad(self.obj.aunit, self.obj.deltaphi)
        phi1 = phi0 + deltaphi

        zplanes = self.obj.OutList
        num_zplanes = len(zplanes)

        self.region = Region("")

        normal = Vector(0, 0, 1)
        for i in range(num_zplanes - 1):
            region = ""

            zplane0 = zplanes[i]
            zplane1 = zplanes[i + 1]

            rmin0 = mul * zplane0.rmin
            rmax0 = mul * zplane0.rmax
            z0 = mul * zplane0.z

            rmin1 = mul * zplane1.rmin
            rmax1 = mul * zplane1.rmax
            z1 = mul * zplane1.z
            if rmin0 != 0 and rmin1 != 0:
                v0 = Vector(rmin0, 0, z0)
                v1 = Vector(rmin1, 0, z1)
                surface = cone_from_line_segment(v0, v1)
                self.surfaces.append(surface)
                region += f"+{surface.id} "

            if rmax0 != 0 and rmax1 != 0:
                v0 = Vector(rmax0, 0, z0)
                v1 = Vector(rmax1, 0, z1)
                surface = cone_from_line_segment(v0, v1)
                self.surfaces.append(surface)
                region += f"-{surface.id} "

            if z0 in planes_dict:
                bot_plane = planes_dict[z0]
            else:
                bot_plane = PlaneSurfaceExporter(name+'_bot', normal, z0)
                planes_dict[z0] = bot_plane
                self.surfaces.append(bot_plane)

            if z1 in planes_dict:
                top_plane = planes_dict[z1]
            else:
                top_plane = PlaneSurfaceExporter(name+'_top', normal, z1)
                planes_dict[z1] = top_plane
                self.surfaces.append(top_plane)

            region += f"+{bot_plane.id} -{top_plane.id} "

            self.region = self.region.union(Region(region))


        if deltaphi < 2*math.pi:
            phi0_normal = Vector(math.sin(phi0), -math.cos(phi0), 0)
            phi1_normal = Vector(math.sin(phi1), -math.cos(phi1), 0)
            phi0_plane = PlaneSurfaceExporter(name+'_phi0', phi0_normal, 0)
            phi1_plane = PlaneSurfaceExporter(name+'_phi1', phi1_normal, 0)
            self.surfaces += [phi0_plane, phi1_plane]
            if phi0_normal.cross(phi1_normal).z > 0:
                region = f" +{phi0_plane.id} -{phi1_plane.id}"
            else:
                region = f"( +{phi0_plane.id} | -{phi1_plane.id})"

            self.region = self.region.intersection(Region(region))

        self.position_globally()


class GDMLGenericPolyconeExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        from .GDMLObjects import getAngleRad

        name = NameManager.getName(self.obj)
        mul = self.getMult()
        planes_dict = {}
        phi0 = getAngleRad(self.obj.aunit, self.obj.startphi)
        deltaphi = getAngleRad(self.obj.aunit, self.obj.deltaphi)
        phi1 = phi0 + deltaphi

        zplanes = self.obj.OutList
        num_zplanes = len(zplanes)

        self.region = Region("")

        normal = Vector(0, 0, 1)
        for i in range(num_zplanes):
            region = ""

            zplane0 = zplanes[i]
            zplane1 = zplanes[(i + 1) % num_zplanes]

            r0 = mul * zplane0.r
            z0 = mul * zplane0.z

            r1 = mul * zplane1.r
            z1 = mul * zplane1.z

            v0 = Vector(r0, 0, z0)
            v1 = Vector(r1, 0, z1)
            surface = cone_from_line_segment(v0, v1)
            self.surfaces.append(surface)

            if i == num_zplanes - 1:
                region += f"+{surface.id} "
            else:
                region += f"-{surface.id} "


            if z0 in planes_dict:
                bot_plane = planes_dict[z0]
            else:
                bot_plane = PlaneSurfaceExporter(name+'_bot', normal, z0)
                planes_dict[z0] = bot_plane
                self.surfaces.append(bot_plane)

            if z1 in planes_dict:
                top_plane = planes_dict[z1]
            else:
                top_plane = PlaneSurfaceExporter(name+'_top', normal, z1)
                planes_dict[z1] = top_plane
                self.surfaces.append(top_plane)

            if i < num_zplanes - 1:
                region += f"+{bot_plane.id} -{top_plane.id} "
                self.region = self.region.union(Region(region))
            else:
                self.region = self.region.intersection(Region(region))


        if deltaphi < 2*math.pi:
            phi0_normal = Vector(math.sin(phi0), -math.cos(phi0), 0)
            phi1_normal = Vector(math.sin(phi1), -math.cos(phi1), 0)
            phi0_plane = PlaneSurfaceExporter(name+'_phi0', phi0_normal, 0)
            phi1_plane = PlaneSurfaceExporter(name+'_phi1', phi1_normal, 0)
            self.surfaces += [phi0_plane, phi1_plane]
            if phi0_normal.cross(phi1_normal).z > 0:
                region = f" +{phi0_plane.id} -{phi1_plane.id}"
            else:
                region = f"( +{phi0_plane.id} | -{phi1_plane.id})"

            self.region = self.region.intersection(Region(region))

        self.position_globally()


class GDMLSphereExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        from .GDMLObjects import checkFullCircle, getAngleRad

        mul = self.getMult()
        center = Vector(0, 0, 0)
        radius = self.obj.rmin * mul
        if radius != 0:
            inner_surface = SphereSurfaceExporter(f"{self.name()}_ir", center, radius)
            self.surfaces.append(inner_surface)
        else:
            inner_surface = None

        radius = self.obj.rmax * mul
        outer_surface = SphereSurfaceExporter(f"{self.name()}_or",
                                         center, radius)
        self.surfaces.append(outer_surface)

        if not checkFullCircle(self.obj.aunit, self.obj.deltaphi):
            startPhi = getAngleRad(self.obj.aunit, self.obj.startphi)
            nx = -math.sin(startPhi)
            ny = math.cos(startPhi)
            phi0_normal = Vector(nx, ny, 0)
            D = 0

            phi0_plane = PlaneSurfaceExporter(f"{self.obj.Label}_phi0_plane", phi0_normal, D)
            self.surfaces.append(phi0_plane)

            deltaphi = getAngleRad(self.obj.aunit, self.obj.deltaphi)
            endphi = startPhi + deltaphi
            nx = -math.sin(endphi)
            ny = math.cos(endphi)
            phi1_normal = Vector(nx, ny, 0)

            phi1_plane = PlaneSurfaceExporter(f"{self.obj.Label}_phi1_plane", phi1_normal, D)
            self.surfaces.append(phi1_plane)

        startTheta = getAngleRad(self.obj.aunit, self.obj.starttheta)
        deltaTheta = getAngleRad(self.obj.aunit, self.obj.deltatheta)
        endTheta = startTheta + deltaTheta
        if endTheta > math.pi:
            endTheta = math.pi

        cones_region = ""
        if startTheta > 0:
            center = Vector(0, 0, 0)
            axis = Vector(0, 0, 1)
            mid_plane = PlaneSurfaceExporter(f"{self.obj.Label}_mid_plane", axis, 0)

            cone1_surface = None
            if startTheta < math.pi/2:
                cone1_surface = ConeSurfaceExporter(f"{self.obj.Label}_thet1_cone", center, axis, startTheta)
            elif startTheta > math.pi/2:
                cone1_surface = ConeSurfaceExporter(f"{self.obj.Label}_thet1_cone", center, axis, math.pi-startTheta)

            cone2_surface = None
            if endTheta < math.pi/2:
                cone2_surface = ConeSurfaceExporter(f"{self.obj.Label}_thet2_cone", center, axis, endTheta)
            elif endTheta > math.pi/2 and endTheta != math.pi:
                cone2_surface = ConeSurfaceExporter(f"{self.obj.Label}_thet2_cone", center, axis, math.pi-endTheta)

            if cone1_surface is not None:
                self.surfaces.append(cone1_surface)
            if cone2_surface is not None:
                self.surfaces.append(cone2_surface)
            self.surfaces. append(mid_plane)

            # three cases:
            # case 1, startTheta, endTheta < 90 deg
            if (0 < startTheta < math.pi/2) and (0 < endTheta < math.pi/2):
                cones_region = f"+{cone1_surface.id} -{cone2_surface.id} +{mid_plane.id}"

            # case 2 startTheta < 90, endTheta > 90
            elif (0 < startTheta < math.pi/2) and (math.pi/2 < endTheta < math.pi):
                cones_region = f"(+{mid_plane.id} +{cone1_surface.id}) | (-{mid_plane.id} +{cone2_surface.id})"

            # case 3, startTheta, endTheta > 90 deg
            elif (math.pi/2 < startTheta < math.pi) and (math.pi/2 < endTheta < math.pi):
                cones_region = f"+{cone2_surface.id} -{cone1_surface.id} -{mid_plane.id}"

            # edge cases: one or the other of starTheta, endTheta = math.pi/2, math.pi
            elif (startTheta == math.pi/2) and (endTheta < math.pi):
                cones_region = f"-{mid_plane.id} +{cone2_surface.id}"

            elif (0 < startTheta < math.pi/2) and endTheta == math.pi/2:
                cones_region = f"+{cone1_surface.id} +{mid_plane.id}"

            elif startTheta == math.pi/2 and endTheta == math.pi:
                cones_region = f"-{mid_plane.id}"

            elif startTheta > math.pi/2 and endTheta == math.pi:
                cones_region = f"-{cone1_surface.id} -{mid_plane.id}"

        elif startTheta == 0 and endTheta != math.pi:
            center = Vector(0, 0, 0)
            axis = Vector(0, 0, 1)
            mid_plane = PlaneSurfaceExporter(f"{self.obj.Label}_mid_plane", axis, 0)
            self.surfaces.append(mid_plane)

            if endTheta < math.pi/2:
                cone2_surface = ConeSurfaceExporter(f"{self.obj.Label}_thet2_cone", center, axis, endTheta)
                self.surfaces.append(cone2_surface)
                cones_region = f"-{cone2_surface.id} +{mid_plane.id}"
            elif endTheta > math.pi/2:
                cone2_surface = ConeSurfaceExporter(f"{self.obj.Label}_thet2_cone", center, axis, math.pi - endTheta)
                self.surfaces.append(cone2_surface)
                cones_region = f"+{cone2_surface.id} | +{mid_plane.id}"
            else:  # endTheta == pi/2
                cones_region = f"+{mid_plane.id}"

        region = f"-{outer_surface.id}"
        if inner_surface is not None:
            region += f" +{inner_surface.id}"

        if not checkFullCircle(self.obj.aunit, self.obj.deltaphi):
            if phi0_normal.cross(phi1_normal).z > 0:
                region += f" +{phi0_plane.id} -{phi1_plane.id}"
            else:
                region += f" (+{phi0_plane.id} | -{phi1_plane.id})"


        self.region = Region(region)
        if cones_region != "":
            self.region = self.region.intersection(Region(cones_region))


        self.position_globally()


def generate_half_loop_surfaces(loop_half, surfaces):
    '''
    generate surfaces needed for the half loop(circle).
    :param: loop_half: vertexes of the half circle
    :return: The region of the surfaces
    '''

    Nvert = len(loop_half)
    region = Region("")
    # Instead of producing a bottom and top planes for each edge, we produce
    # only one plane per vertex. To keep track if we produced a plane for a given
    # vertex, we use a dictionary plane_dict[vertex.z = surface. See below of how we decide the region
    planes_dict = {}
    for i in range(0, Nvert - 1):
        v0 = loop_half[i]
        v1 = loop_half[i + 1]
        outer = v1.z > v0.z
        surface = cone_from_line_segment(v0, v1)
        if surface is not None:
            surfaces.append(surface)
            if outer:
                edge_region = f"-{surface.id} "
            else:
                edge_region = f"+{surface.id} "

            for v in [v0, v1]:
                if v.z in planes_dict:
                    plane = planes_dict[v.z]
                else:
                    plane = PlaneSurfaceExporter("", Vector(0, 0, 1), v.z)
                    surfaces.append(plane)
                    planes_dict[v.z] = plane
                if outer and v == v0:
                    plane_region = f"+{plane.id} "
                elif outer and v == v1:
                    plane_region = f"-{plane.id} "
                elif (not outer) and v == v0:
                    plane_region = f"-{plane.id} "
                elif (not outer) and v == v1:
                    plane_region = f"+{plane.id} "

                edge_region += plane_region

            region = region.union(Region(edge_region))

    return region

class GDMLTorusExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)
        deviation = obj.ViewObject.Deviation/100
        costhet = 1 - deviation
        thet = math.acos(costhet)
        N = int(2*math.pi/(2*thet)) # number of divisions of the circle that that given a maximum radial difference
                                         # if Deviation, in percent
        # make it even
        self.N = 2*int(N/2)


    def inner_outer(self, center, radius):
        ''' Return two ploylines, one is the outer (-90, 90 deg)
        and one the inner (90, 270 degrees)
        '''
        thet = -math.pi/2
        dethet = 2*math.pi/(self.N)
        verts = []
        for i in range(self.N+1):
            x = radius * math.cos(thet)
            z = radius * math.sin(thet)
            verts.append(center + Vector(x, 0, z))
            thet += dethet

        outer = verts[:int(self.N/2)+1]
        inner = verts[int(self.N/2):]
        return inner, outer

    def generate_circle_revolve(self, radius):
        mul = self.getMult()
        center = mul * self.obj.rtor * Vector(1, 0, 0)
        inner, outer = self.inner_outer(center, mul * radius)
        outer_region = generate_half_loop_surfaces(outer, self.surfaces)
        inner_region = generate_half_loop_surfaces(inner, self.surfaces)

        region = outer_region.intersection(inner_region)
        return region

    def generate_surfaces(self):
        from .GDMLObjects import checkFullCircle, getAngleRad

        self.region = self.generate_circle_revolve(self.obj.rmax)
        if self.obj.rmin > 0:
            inside_region = self.generate_circle_revolve(self.obj.rmin)
            self.region = self.region.cut(inside_region)

        if not checkFullCircle(self.obj.aunit, self.obj.deltaphi):
            startPhi = getAngleRad(self.obj.aunit, self.obj.startphi)
            nx = -math.sin(startPhi)
            ny = math.cos(startPhi)
            phi0_normal = Vector(nx, ny, 0)
            D = 0

            phi0_plane = PlaneSurfaceExporter(f"{self.obj.Label}_phi0_plane", phi0_normal, D)
            self.surfaces.append(phi0_plane)

            deltaphi = getAngleRad(self.obj.aunit, self.obj.deltaphi)
            endphi = startPhi + deltaphi
            nx = -math.sin(endphi)
            ny = math.cos(endphi)
            phi1_normal = Vector(nx, ny, 0)

            phi1_plane = PlaneSurfaceExporter(f"{self.obj.Label}_phi1_plane", phi1_normal, D)
            self.surfaces.append(phi1_plane)

            if phi0_normal.cross(phi1_normal).z > 0:
                self.region = self.region.intersection(Region(f"+{phi0_plane.id} -{phi1_plane.id}"))
            else:
                self.region = self.region.intersection(Region(f"(+{phi0_plane.id} | -{phi1_plane.id})"))

        self.position_globally()


class TorusExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)
        deviation = self.obj.ViewObject.Deviation/100
        costhet = 1 - deviation
        thet = math.acos(costhet)
        self.dthet = 2*thet

    def get_verts(self):
        ''' this is quite a bit more involved than appears'''
        verts = []
        center = self.obj.Radius1.Value * Vector(1, 0, 0)
        angle1 = math.radians(self.obj.Angle1)
        angle2 = math.radians(self.obj.Angle2)

        v1 = Vector(math.cos(angle1), 0, -math.sin(angle1))  # unit vector in direction of angle1
        v2 = Vector(math.cos(angle2), 0, -math.sin(angle2))  # unit vector in direction of angle2
        # angular span is angle from v1 to v2, in CW direction.
        sinthet = v1.cross(v2).y
        thet = math.atan2(sinthet, v1.dot(v2))
        if thet < 0:
            thet = 2*math.pi + thet

        N = int(thet/self.dthet) + 1
        if N < 2:
            N = 2

        radius = self.obj.Radius2.Value
        dthet = thet/(N-1)  # this is local
        if thet < 2*math.pi:
            verts.append(center)

        verts += [center + radius * Vector(math.cos(angle1+i*dthet), 0, -math.sin(angle1+i*dthet)) for i in range(N)]

        return verts

    def process_convex_polygon(self, verts):

        # generate the surfaces and region (one region!) for a convex polygon in the
        # x-z plane. The assumption is that the verts are in CCW order. One needs to specify
        # exactly what we mean by CCW in the x-z plane. If I look at the x-z plane, such that x is to my right
        # and z upward, then a polygon with xy verts arranged CCW is one for which for, for two consecutive edges
        # e1 and e2, e1 x e2 is in the -y direction. Yes, minus y, not positive y.
        N = len(verts)
        region_expr = ""
        zmin = min([v.z for v in verts])
        zmax = max([v.z for v in verts])

        for i in range(N):
            v0 = verts[i]
            v1 = verts[(i+1) % N]
            surf = cone_from_line_segment(v0, v1)
            if surf is None:
                continue
            self.surfaces.append(surf)
            # now we have to worry about the other half of the cone cutting out part of the  polygon.
            # it can do that if the vertex of the cone lies between zmin and zmax
            extra_plane = None
            # ugly, but we must remember surface properties are already in cm, so we need to multiply them by 10
            if isinstance(surf, ConeSurfaceExporter) and (zmin < 10*surf.center.z < zmax):
                extra_plane = PlaneSurfaceExporter("", Vector(0, 0, 1), 10*surf.center.z)
                self.surfaces.append(extra_plane)

            if v1.z > v0.z:  # we are on the up side
                region_expr += f"-{surf.id} "

            elif v1.z < v0.z:  # on the down side, the extra plane can interfere
                if extra_plane is not None:
                    if v1.z < 0:
                        region_expr += f"(+{surf.id} | +{extra_plane.id}) "
                    else:
                        region_expr += f"(+{surf.id} | -{extra_plane.id}) "
                else:
                    region_expr += f"+{surf.id} "

            else:  # v1.z == v0.z, the surface is a plane, either at the very top or very bottom, for the closed polygon
                if v1.x < v0.x:
                    region_expr += f"-{surf.id} "
                else:
                    region_expr += f"+{surf.id} "


        self.region = self.region.union(Region(region_expr))


    def generate_surfaces(self):
        verts = self.get_verts()
        verts.reverse()

        self.region = Region("")
        # do we have a concave polygon in the x-z plane?
        if (self.obj.Angle2 - self.obj.Angle1) < 360:
            # Not a complete circle, so there is possibility of convext polygon
            radius = self.obj.Radius2.Value
            center = self.obj.Radius1.Value * Vector(1, 0, 0)
            angle1 = math.radians(self.obj.Angle1)
            angle2 = math.radians(self.obj.Angle2)
            v1 =  radius * Vector(math.cos(angle1), 0, -math.sin(angle1))
            v2 =  radius * Vector(math.cos(angle2), 0, -math.sin(angle2))
            if v1.cross(v2).y < 0:  # This is concave, break it into two convex polygons
                imid = int(len(verts)/2)
                seg1 = verts[:imid+1]
                seg1.append(center)
                seg2 = verts[imid:]
                for seg in [seg1, seg2]:
                    self.process_convex_polygon(seg)
            else:
                self.process_convex_polygon(verts)
        else:
            self.process_convex_polygon(verts)

        if self.obj.Angle3 != 360:
            startPhi = 0
            nx = -math.sin(startPhi)
            ny = math.cos(startPhi)
            phi0_normal = Vector(nx, ny, 0)
            D = 0
            phi0_plane = PlaneSurfaceExporter(f"{self.obj.Label}_phi0_plane", phi0_normal, D)
            self.surfaces.append(phi0_plane)

            deltaphi = math.radians(self.obj.Angle3)
            endphi = startPhi + deltaphi
            nx = -math.sin(endphi)
            ny = math.cos(endphi)
            phi1_normal = Vector(nx, ny, 0)

            phi1_plane = PlaneSurfaceExporter(f"{self.obj.Label}_phi1_plane", phi1_normal, D)
            self.surfaces.append(phi1_plane)

            if phi0_normal.cross(phi1_normal).z > 0:
                region = f" +{phi0_plane.id} -{phi1_plane.id}"
            else:
                region = f" (+{phi0_plane.id} | -{phi1_plane.id})"

            self.region = self.region.intersection(Region(region))

        self.position_globally()


class GDMLTubeExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        from .GDMLObjects import checkFullCircle, getAngleRad

        normal = Vector(0, 0, 1)
        mul = self.getMult()

        D = self.obj.z/2*mul
        # a gdml tube has origin at its center
        top_surface = PlaneSurfaceExporter(f"{self.name()}_top", normal, D)

        D = -self.obj.z/2*mul
        # a gdml tube has origin at its center
        bottom_surface = PlaneSurfaceExporter(f"{self.name()}_bot", normal, D)

        center = Vector(0, 0, 0)
        axis = normal
        radius = self.obj.rmin * mul
        if radius != 0:
            inner_surface = CylinderSurfaceExporter(f"{self.name()}_ir", center, axis, radius)
        else:
            inner_surface = None

        radius = self.obj.rmax * mul
        outer_surface = CylinderSurfaceExporter(f"{self.name()}_or", center, axis, radius)

        if not checkFullCircle(self.obj.aunit, self.obj.deltaphi):
            startPhi = getAngleRad(self.obj.aunit, self.obj.startphi)
            nx = -math.sin(startPhi)
            ny = math.cos(startPhi)
            phi0_normal = Vector(nx, ny, 0)
            D = 0
            phi0_plane = PlaneSurfaceExporter(f"{self.obj.Label}_phi0_plane", phi0_normal, D)

            deltaphi = getAngleRad(self.obj.aunit, self.obj.deltaphi)
            endphi = startPhi + deltaphi
            nx = -math.sin(endphi)
            ny = math.cos(endphi)
            phi1_normal = Vector(nx, ny, 0)

            phi1_plane = PlaneSurfaceExporter(f"{self.obj.Label}_phi1_plane", phi1_normal, D)

        self.surfaces = [top_surface, bottom_surface, outer_surface]
        if inner_surface is not None:
            self.surfaces.append(inner_surface)

        if not checkFullCircle(self.obj.aunit, self.obj.deltaphi):
            self.surfaces += [phi0_plane, phi1_plane]


        region =  f"+{bottom_surface.id} -{top_surface.id} -{outer_surface.id}"
        if inner_surface is not None:
            region += f" +{inner_surface.id}"

        if not checkFullCircle(self.obj.aunit, self.obj.deltaphi):
            if phi0_normal.cross(phi1_normal).z > 0:
                region += f" +{phi0_plane.id} -{phi1_plane.id}"
            else:
                region += f" (+{phi0_plane.id} | -{phi1_plane.id})"

        self.region = Region(region)
        self.position_globally()


class GDMLTwistedSolidExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)
        self.slice = 0
        self.dTwist = obj.ViewObject.AngularDeflection.Value
        self.dTwist = min(self.dTwist, 5)


class GDMLTwistedboxExporter(GDMLTwistedSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def make4Walls(self, x, y):
        name = NameManager.getName(self.obj)
        surf1 = PlaneSurfaceExporter(f"{name}_{self.slice}_1", Vector(1, 0, 0), x/2)
        surf2 = PlaneSurfaceExporter(f"{name}_{self.slice}_2", Vector(0, 1, 0), y/2)
        surf3 = PlaneSurfaceExporter(f"{name}_{self.slice}_3", Vector(-1, 0, 0), x/2)
        surf4 = PlaneSurfaceExporter(f"{name}_{self.slice}_4", Vector(0, -1, 0), y/2)

        return [surf1, surf2, surf3, surf4]

    def generate_surfaces(self):
        from .GDMLObjects import getAngleDeg
        mul = self.getMult()

        x = mul * self.obj.x
        y = mul * self.obj.y
        z = mul * self.obj.z

        angle = getAngleDeg(self.obj.aunit, self.obj.PhiTwist)
        dPhi = self.dTwist  # 2 degree rotation per step
        N = int(angle/dPhi)
        N = max(N, 10)
        dz = z /N

        planes_dict = {}
        region_expr = ""
        z0 = -z/2
        for i in range(0, N):
            name = NameManager.getName(self.obj)
            walls = self.make4Walls(x, y)
            self.surfaces += walls
            if z0 in planes_dict:
                bot_plane = planes_dict[z0]
            else:
                bot_plane = PlaneSurfaceExporter(f"{name}_{self.slice}_bot", Vector(0, 0, 1), z0)
                planes_dict[z0] = bot_plane
                self.surfaces.append(bot_plane)

            z0 += dz
            if z0 in planes_dict:
                top_plane = planes_dict[z0]
            else:
                top_plane = PlaneSurfaceExporter(f"{name}_{self.slice}_top", Vector(0, 0, 1), z0)
                planes_dict[z0] = top_plane
                self.surfaces.append(top_plane)

            if region_expr == "":
                region_expr = f"(-{walls[0].id} -{walls[1].id} -{walls[2].id} -{walls[3].id} +{bot_plane.id} -{top_plane.id})"
            else:
                region_expr += f" | (-{walls[0].id} -{walls[1].id} -{walls[2].id} -{walls[3].id} +{bot_plane.id} -{top_plane.id})"

            rot = FreeCAD.Rotation(Vector(0, 0, 1), -angle / 2 + i * dPhi)
            for wall in walls:
                wall.rotate(rot)
            self.slice += 1

        self.region = Region(region_expr)

        self.position_globally()


class GDMLTwistedtrdExporter(GDMLTwistedSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def make4Walls(self, x, y):
        name = NameManager.getName(self.obj)
        surf1 = PlaneSurfaceExporter(f"{name}_{self.slice}_1", Vector(1, 0, 0), x/2)
        surf2 = PlaneSurfaceExporter(f"{name}_{self.slice}_2", Vector(0, 1, 0), y/2)
        surf3 = PlaneSurfaceExporter(f"{name}_{self.slice}_3", Vector(-1, 0, 0), x/2)
        surf4 = PlaneSurfaceExporter(f"{name}_{self.slice}_4", Vector(0, -1, 0), y/2)

        return [surf1, surf2, surf3, surf4]

    def generate_surfaces(self):
        from .GDMLObjects import getAngleDeg

        mul = self.getMult()

        x1 = self.obj.x1 * mul
        x2 = self.obj.x2 * mul
        y1 = self.obj.y1 * mul
        y2 = self.obj.y2 * mul
        z = self.obj.z * mul

        angle = getAngleDeg(self.obj.aunit, self.obj.PhiTwist)
        dPhi = self.dTwist  # 2 degree rotation per step
        N = int(angle/dPhi)
        N = max(N, 10)
        dz = z /N

        planes_dict = {}
        region_expr = ""
        z0 = -z/2
        for i in range(0, N):
            t = i * 1.0 / (N - 1)
            xside = x1 + t * (x2 - x1)
            yside = y1 + t * (y2 - y1)

            name = NameManager.getName(self.obj)
            walls = self.make4Walls(xside, yside)
            self.surfaces += walls
            if z0 in planes_dict:
                bot_plane = planes_dict[z0]
            else:
                bot_plane = PlaneSurfaceExporter(f"{name}_{self.slice}_bot", Vector(0, 0, 1), z0)
                planes_dict[z0] = bot_plane
                self.surfaces.append(bot_plane)

            z0 += dz
            if z0 in planes_dict:
                top_plane = planes_dict[z0]
            else:
                top_plane = PlaneSurfaceExporter(f"{name}_{self.slice}_top", Vector(0, 0, 1), z0)
                planes_dict[z0] = top_plane
                self.surfaces.append(top_plane)

            if region_expr == "":
                region_expr = f"(-{walls[0].id} -{walls[1].id} -{walls[2].id} -{walls[3].id} +{bot_plane.id} -{top_plane.id})"
            else:
                region_expr += f" | (-{walls[0].id} -{walls[1].id} -{walls[2].id} -{walls[3].id} +{bot_plane.id} -{top_plane.id})"

            rot = FreeCAD.Rotation(Vector(0, 0, 1), -angle / 2 + i * dPhi)
            for wall in walls:
                wall.rotate(rot)
            self.slice += 1

        self.region = Region(region_expr)

        self.position_globally()


class GDMLTwistedtrapExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def make4Walls(self, verts):
        name = NameManager.getName(self.obj)
        n  = len(verts)
        surfaces = []
        for i in range(n):
            i1 = (i+1) % n
            v0 = verts[i]
            v1 = verts[i1]
            dx = (v1-v0).x
            dy = (v1-v0).y
            normal = Vector(dy, -dx, 0)
            normal.normalize()
            D = v0.dot(normal)

            surf = PlaneSurfaceExporter(f"{name}_{self.slice}_1", normal, D)
            surfaces.append(surf)

        return surfaces

    def generate_surfaces(self):
        from .GDMLObjects import getAngleRad, getAngleDeg

        mul = self.getMult()
        alpha = getAngleRad(self.obj.aunit, self.obj.Alph)
        theta = getAngleRad(self.obj.aunit, self.obj.Theta)
        phi = getAngleRad(self.obj.aunit, self.obj.Phi)
        PhiTwist = getAngleDeg(self.obj.aunit, self.obj.PhiTwist)
        y1 = mul * self.obj.y1
        x1 = mul * self.obj.x1
        x2 = mul * self.obj.x2
        y2 = mul * self.obj.y2
        x3 = mul * self.obj.x3
        x4 = mul * self.obj.x4
        z = mul * self.obj.z

        dTwist = self.dTwist
        N = int(PhiTwist/dTwist)
        N = max(N, 10)
        dz = z /N

        tanalpha = math.tan(alpha)

        dt = 1.0 /N
        t = 0

        tanthet = math.tan(theta)
        cosphi = math.cos(phi)
        sinphi = math.sin(phi)
        rhomax = z * tanthet
        xoffset = -rhomax * cosphi / 2
        yoffset = -rhomax * sinphi / 2

        planes_dict = {}
        region_expr = ""

        for i in range(N):
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
            name = NameManager.getName(self.obj)
            walls = self.make4Walls([v1, v2, v3, v4])

            self.surfaces += walls
            if zt in planes_dict:
                bot_plane = planes_dict[zt]
            else:
                bot_plane = PlaneSurfaceExporter(f"{name}_{self.slice}_bot", Vector(0, 0, 1), zt)
                planes_dict[zt] = bot_plane
                self.surfaces.append(bot_plane)

            zt += dz
            if zt in planes_dict:
                top_plane = planes_dict[zt]
            else:
                top_plane = PlaneSurfaceExporter(f"{name}_{self.slice}_top", Vector(0, 0, 1), zt)
                planes_dict[zt] = top_plane
                self.surfaces.append(top_plane)

            if region_expr == "":
                region_expr = f"(-{walls[0].id} -{walls[1].id} -{walls[2].id} -{walls[3].id} +{bot_plane.id} -{top_plane.id})"
            else:
                region_expr += f" | (-{walls[0].id} -{walls[1].id} -{walls[2].id} -{walls[3].id} +{bot_plane.id} -{top_plane.id})"

            rot = FreeCAD.Rotation(Vector(0, 0, 1), -PhiTwist / 2 + i * dTwist)
            for wall in walls:
                wall.rotate(rot)

            t += dt
            self.slice += 1

        self.region = Region(region_expr)

        self.position_globally()


class GDMLTwistedtubsExporter(GDMLTwistedSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def tubeWalls(self, rin, rout, phi0, phi1):
        ''' return four surfaces: a cylinder of radius rin, None if rin = 0
        a cylinder or radius rout, two planes with normals in the x-y plane
        one starting at ph0, the other ending at phi1
        '''
        cylinder_in = None
        name = NameManager.getName(self.obj)
        center = Vector(0, 0, 0)
        axis = Vector(0, 0, 1)
        if rin > 0:
            cylinder_in = CylinderSurfaceExporter(name+"_in", center, axis, rin)
        cylinder_out = CylinderSurfaceExporter(name+"_out", center, axis, rout)

        u0 = Vector(math.cos(phi0), math.sin(phi0), 0)
        u1 = Vector(math.cos(phi1), math.sin(phi1), 0)
        n0 = Vector(-u0.y, u0.x, 0)
        n1 = Vector(-u1.y, u1.x, 0)

        phi0_plane = PlaneSurfaceExporter(name+"_phi0", n0, 0)
        phi1_plane = PlaneSurfaceExporter(name+"_phi1", n1, 0)

        return [cylinder_in, cylinder_out, phi0_plane, phi1_plane]

    def generate_surfaces(self):
        from .GDMLObjects import getAngleRad, getAngleDeg
        mul = self.getMult()
        rin = mul*self.obj.endinnerrad
        rout = mul*self.obj.endouterrad
        z = mul*self.obj.zlen
        phi = getAngleRad(self.obj.aunit, self.obj.phi)
        angle = getAngleDeg(self.obj.aunit, self.obj.twistedangle)
        dTwist = self.dTwist  # 2 degree rotation per step
        N = int(angle/dTwist)
        N = max(N, 10)
        dz = z /N

        planes_dict = {}
        region_expr = ""
        z0 = -z/2
        phi0 = -phi/2
        phi1 = phi/2

        region_expr = ""
        self.region = Region("")
        for i in range(0, N):
            name = NameManager.getName(self.obj)
            walls = self.tubeWalls(rin, rout, phi0, phi1)
            rin_cylinder = walls[0]
            rout_cylinder = walls[1]

            if rin > 0:
                self.surfaces += walls
            else:
                self.surfaces += walls[1:]

            if z0 in planes_dict:
                bot_plane = planes_dict[z0]
            else:
                bot_plane = PlaneSurfaceExporter(f"{name}_{self.slice}_bot", Vector(0, 0, 1), z0)
                planes_dict[z0] = bot_plane
                self.surfaces.append(bot_plane)

            z0 += dz
            if z0 in planes_dict:
                top_plane = planes_dict[z0]
            else:
                top_plane = PlaneSurfaceExporter(f"{name}_{self.slice}_top", Vector(0, 0, 1), z0)
                planes_dict[z0] = top_plane
                self.surfaces.append(top_plane)

            phi0_plane = walls[2]
            phi1_plane = walls[3]
            phi0_normal = phi0_plane.normal
            phi1_normal = phi1_plane.normal

            if rin > 0:
                rin_region = f"+{rin_cylinder.id}"
            else:
                rin_region = ""

            if phi0_normal.cross(phi1_normal).z > 0:
                region_expr += f'({rin_region} -{rout_cylinder.id} +{bot_plane.id} -{top_plane.id} +{phi0_plane.id} -{phi1_plane.id})'
            else:
                region_expr += f'({rin_region} -{rout_cylinder.id} +{bot_plane.id} -{top_plane.id} (+{phi0_plane.id} | -{phi1_plane.id}))'
            if i != N -1:
                region_expr += ' | '

            rot = FreeCAD.Rotation(Vector(0, 0, 1), -angle / 2 + i * dTwist)
            for wall in [phi0_plane, phi1_plane]:
                wall.rotate(rot)
            self.slice += 1

        self.region = Region(region_expr)

        self.position_globally()


class MultiFuseExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def name(self):
        solidName = "MultiFuse" + self.obj.Label
        return solidName

    def generate_surfaces(self):
        print("Output Solids")
        exporters = []
        self.surfaces = []
        self.region = Region("")
        for sub in self.obj.OutList:
            exporter = SolidExporter.getExporter(sub)
            if exporter is not None:
                exporter.generate_surfaces()
                self.surfaces += exporter.surfaces
                if self.region.expr == "":
                    self.region = Region(f'({exporter.get_region()})')
                else:
                    self.region = self.region.union(exporter.get_region())

        '''
        The surfaces generated above already contain the absoulte placement, including that of the
        boolean object, so no need for this
        
        objPlacement = self.obj.Placement
        if objPlacement != FreeCAD.Placement():
            translation = objPlacement.Base
            rotation = objPlacement.Rotation
            for surf in self.surfaces:
                surf.rotate(rotation)
                surf.translate(translation)
        '''

class MultiCommonExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def name(self):
        solidName = "MultiCommon" + self.obj.Label
        return solidName

    def generate_surfaces(self):
        print("Output Solids")
        exporters = []
        self.surfaces = []
        self.region = Region("")
        for sub in self.obj.OutList:
            exporter = SolidExporter.getExporter(sub)
            if exporter is not None:
                exporter.generate_surfaces()
                self.surfaces += exporter.surfaces
                if self.region.expr == "":
                    self.region = Region(f'({exporter.get_region()})')
                else:
                    self.region = self.region.intersection(exporter.get_region())



class OrthoArrayExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)


    def generate_surfaces(self):
        self.region = Region("")

        # for the time being and array is treated is a solid with a single material
        # its region is the union of the array of regions of the individual array elements
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

        # heuristic: If the rotation is not intrinsic to the base solid, then the
        # position must be rotated as well.
        tolerance = 1.0e-7
        rotatePosition = not base.Placement.Rotation.isSame(base.getGlobalPlacement().Rotation, tolerance)
        positionRotation = base.getGlobalPlacement().Rotation
        if rotatePosition:
            print(f" Will apply position rotation to {base.Label} because global rotation is different than base rotation")
        # we need to also check for the array object rotation. This is NOT included in the global placement
        if not self.obj.Placement.Rotation.isSame(base.getGlobalPlacement().Rotation, tolerance):
            rotatePosition = True
            positionRotation = self.obj.Placement.Rotation

        for i, placement in enumerate(arrayUtils.placementList(self.obj, offsetVector=self.obj.Placement.Base)):
            solidExporter = SolidExporter.getExporter(base)
            item_region = solidExporter.get_region()
            translation = placement.Base
            if rotatePosition:
                translation = positionRotation*translation
                # the rotation should also apply to the base, not just the position
                solidExporter.rotate(positionRotation)
            solidExporter.translate(translation)
            self.region = self.region.union(item_region)
            self.surfaces += solidExporter.surfaces


class PolarArrayExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        from . import arrayUtils
        base = self.obj.Base

        self.region = Region("")

        print(base.Label)
        appPartBase = False
        if hasattr(base, "TypeId") and base.TypeId == "App::Part":
            print(
                f"**** Arrays of {base.TypeId} ({base.Label}) currently not supported ***"
            )

            return


        baseExporter = SolidExporter.getExporter(base)
        if baseExporter is None:
            print(f"Cannot export {base.Label}")
            return

        arrayRotation = self.obj.Placement.Rotation
        basePos = base.Placement.Base
        # arrayUtils takes care of the offset center of of rotation
        # But the array may have been shifted/rotatied by its parent.
        # Since the array itself is not exported, but rather the array base is,
        # the base global position does not reflect the arrays global position

        placements = arrayUtils.placementList(self.obj, rot=arrayRotation)

        # I'll try doing the rotations from scratch
        # let GlobalPlacement = G   # Note: FOR AN ARRAY GLOBAL PLACEMENT APPLIES to the ARRAY, NOT BASE of the ARRAY
        # let Container Placement = C (the effect of all the App::Parts that contain the base)
        # let the base placement be P
        # then must have G = C*P  ==> C = G*P^-1
        # If the rotation by the polar array is rot
        # Then the position after rotation ought to be
        # rotation by polar array:  position_by_array = array_center + rot * (P.Base - array_center)
        # Position globally   rotated_global_position = C*position_by_array
        # Because we don't give a position or a rotation to the solid exporter surfaces (we only rotate or translate them)
        # We need to first unrotate and untranslate the surfaces, then translate and rotate by the array rotation and
        # translation as above
        arrayObj = self.obj
        G = arrayObj.getGlobalPlacement()
        P = arrayObj.Placement
        Pinv = P.inverse()
        C = G*Pinv  # this is what puts the array in its position globally
        baseInvPlacement = base.Placement.inverse()

        for placement in placements:
            rot = arrayRotation*placement.Rotation
            local_rotated_position = arrayObj.Placement.Base + self.obj.Center + rot*(basePos - self.obj.Center)
            global_rotated_position = C*local_rotated_position

            # rot = rot * baseRotation
            # rot.Angle = -rot.Angle  # undo angle reversal by exportRotation


            solidExporter = SolidExporter.getExporter(base)
            # get region generates a region with # global translation and global rotation
            # let us assume now that object rotation is 0
            # array utils give position rotated about array center then shifter by array center
            #
            item_region = solidExporter.get_region()  # also positions solidExorter object globally
            # undo surfaces positioning
            solidExporter.translate(baseInvPlacement.Base)
            solidExporter.rotate(baseInvPlacement.Rotation)
            # then apply rotated global position
            solidExporter.rotate(rot)
            solidExporter.translate(global_rotated_position)
            self.region = self.region.union(item_region)
            self.surfaces += solidExporter.surfaces


class PathArrayExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)


    def generate_surfaces(self):
        self.region = Region("")

        base = self.obj.Base
        print(base.Label)
        if hasattr(base, "TypeId") and base.TypeId == "App::Part":
            print(
                f"**** Arrays of {base.TypeId} ({base.Label}) currently not supported ***"
            )
            return

        baseExporter = SolidExporter.getExporter(base)
        if baseExporter is None:
            print(f"Cannot export {base.Label}")
            return

        count = self.obj.Count
        positionVector = base.Placement.Base
        rot = base.Placement.Rotation

        extraTranslation = self.obj.ExtraTranslation

        pathObj = self.obj.PathObject
        path = pathObj.Shape.Edges[0]
        points = path.discretize(Number=count)

        for i, point in enumerate(points):
            pos = point + positionVector + extraTranslation
            solidExporter = SolidExporter.getExporter(base)
            item_region = solidExporter.get_region()
            solidExporter.translate(pos)
            self.region = self.region.union(item_region)
            self.surfaces += solidExporter.surfaces


class PointArrayExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def generate_surfaces(self):
        from . import arrayUtils

        self.surfaces = []
        self.region = Region("")

        base = self.obj.Base
        print(base.Label)
        if hasattr(base, "TypeId") and base.TypeId == "App::Part":
            print(
                f"**** Arrays of {base.TypeId} ({base.Label}) currently not supported ***"
            )
            return

        baseExporter = SolidExporter.getExporter(base)
        if baseExporter is None:
            print(f"Cannot export {base.Label}")
            return

        extraTranslation = self.obj.ExtraPlacement.Base
        extraRotation = self.obj.ExtraPlacement.Rotation

        pointObj = self.obj.PointObject
        points = pointObj.Points.Points
        arrayTranslation = self.obj.Placement.Base
        arrayRotation = self.obj.Placement.Rotation

        # points = arrayUtils.placementList(self.obj, offsetVector=self.obj.Placement.Base)
        for point in points:
            if not arrayRotation.isSame(FreeCAD.Rotation(), 1e-7):
                point = arrayRotation*point
            pos = point + arrayTranslation + extraTranslation
            solidExporter = SolidExporter.getExporter(base)
            item_region = solidExporter.get_region()
            solidExporter.rotate(arrayRotation)
            solidExporter.translate(pos)
            self.region = self.region.union(item_region)
            self.surfaces += solidExporter.surfaces


#
# ------------------------------revolutionExporter ----------------------------
#
global Deviation  # Fractional deviation of revolve object
#############################################
# Helper functions for Revolve construction

# One of the closed curves (list of edges) representing a part
# of the sketch

def cone_from_line_segment(v0, v1):
    '''
    Given a line segment in the x-z plane, generate a cone in the half space containing the segment
    :param: v0: One point on the segment (v0=Vector(x0, 0, z0)
    :param: v1: another point on the segment v1=(Vector(x1, 0, z1)
    :Return: The cone passing through the line segment. if v0.z == v1.z, return a cylinder
    '''

    dx = v1.x - v0.x
    dz = v1.z - v0.z
    u = (v1-v0).normalize()  # unit vector fro m v0 to v1
    if abs(dz) > 1e-9:
        theta = math.atan(abs(dx/dz))
        axis = Vector(0, 0, 1)

        if abs(u.x) <  1e-9:  # return a cylinder
            surf = CylinderSurfaceExporter("", Vector(0, 0, 0), Vector(0, 0, 1), abs(v0.x))
        else:  # return a cone
            t2 = -v0.x / u.x
            center = v0 + t2 * u
            surf = ConeSurfaceExporter("", center, axis, theta)

        return surf

    elif abs(dx) > 1e-9:  # a horizontal line, not sure if a plane is the correct answer
        surf = PlaneSurfaceExporter("", Vector(0, 0, 1), v0.z)
        return surf

    return None



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
    def __init__(self, name, edgelist):
        super().__init__(name, edgelist)
        self.position = Vector(0, 0, 0)
        self.rotation = [0, 0, 0]  # TBD
        self.deflectionFraction = 0.001
        self.surfaces = []
        self.region = Region("")

    def add_top_bottom(self, verts):
        ''' If there is a single top/bottom vertex the cylinders/conves
        meeting there will eventuall y extend to a common region that is outside
        the revolved solid. So we must cap the top/botton with a top/bottom
        plane in that case'''
        zs =  [v.z for v in verts]
        maxz = max(zs)
        minz = min(zs)
        top_plane = PlaneSurfaceExporter("", Vector(0, 0, 1), maxz)
        # add a top plane if one does not exist already
        add_it = True
        for surf in self.surfaces:
            if surf == top_plane:
                add_it = False
                break
        if add_it:
            self.surfaces.append(top_plane)
            self.region = self.region.intersection(Region(f"-{top_plane.id}"))

        bottom_plane = PlaneSurfaceExporter("", Vector(0, 0, 1), minz)
        # add a top plane if one does not exist already
        add_it = True
        for surf in self.surfaces:
            if surf == bottom_plane:
                add_it = False
                break
        if add_it:
            self.surfaces.append(bottom_plane)
            self.region = self.region.intersection(Region(f"+{bottom_plane.id}"))

    def getVertexes(self):
        return self.discretize()

    def generated_triangulated_surfaces(self, xy_verts):
        from .polygonsHelper import triangulate_polygon_earclip, inner_outer
        polys = triangulate_polygon_earclip(xy_verts)

        self.region = Region("")
        for poly in polys:
            verts = [Vector(v.x, 0, v.y) for v in poly]
            arrangeCCW(verts, Vector(0, -1, 0))   # arrange in CCW in xz plane
            inner, outer = inner_outer(verts)

            nouter = len(outer)
            outer_region = Region("")
            for i in range(0, nouter-1):
                v0 = outer[i]
                v1 = outer[i+1]
                surface = cone_from_line_segment(v0, v1)
                if surface is not None:
                    top_plane = PlaneSurfaceExporter("", Vector(0, 0, 1), v1.z)
                    bot_plane = PlaneSurfaceExporter("", Vector(0, 0, 1), v0.z)
                    self.surfaces += [surface, top_plane, bot_plane]
                    outer_region = outer_region.union(Region(f"-{surface.id} -{top_plane.id} +{bot_plane.id}"))

            ninner = len(inner)
            inner_region = Region("")
            for i in range(0, ninner-1):
                v0 = inner[i]
                v1 = inner[i+1]
                surface = cone_from_line_segment(v0, v1)
                if surface is not None:
                    top_plane = PlaneSurfaceExporter("", Vector(0, 0, 1), v0.z)
                    bot_plane = PlaneSurfaceExporter("", Vector(0, 0, 1), v1.z)
                    self.surfaces += [surface, top_plane, bot_plane]
                    inner_region = inner_region.union(Region(f"+{surface.id} -{top_plane.id} +{bot_plane.id}"))

            region = outer_region.intersection(inner_region)
            self.region = self.region.union(region)

    def generate_surfaces(self):
        from .polygonsHelper import is_convex_polygon, inner_outer

        verts = self.getVertexes()
        # the revolve and triangulate algorithm assume the last point and first point are NOT the same.
        # more generally, we omit edges of near zero length
        vpruned = []
        for i in range(len(verts)):
            i1 = (i+1) % len(verts)
            if (verts[i1] - verts[i]).Length > 1.0e-07:
                vpruned.append(verts[i])

        arrangeCCW(vpruned, Vector(0, -1, 0))   # arrange in CCW in xz plane
        verts = vpruned
        xy_verts = [Vector(v.x, v.z, 0) for v in verts]
        if not is_convex_polygon(xy_verts):
            self.generated_triangulated_surfaces(xy_verts)
            return

        inner, outer = inner_outer(verts)
        outer_region = generate_half_loop_surfaces(outer, self.surfaces)
        inner_region = generate_half_loop_surfaces(inner, self.surfaces)

        region = outer_region.intersection(inner_region)

        zs = [v.z for v in verts]
        maxz = max(zs)
        minz = min(zs)
        top_plane = PlaneSurfaceExporter("", Vector(0, 0, 1), maxz)
        bot_plane = PlaneSurfaceExporter("", Vector(0, 0, 1), minz)
        self.surfaces += [top_plane, bot_plane]

        bounding_planes = Region(f"-{top_plane.id} +{bot_plane.id}")

        self.region = region.intersection(bounding_planes)


    def discretize(self):
        deflection = Deviation * radialExtent(self.edgeList)
        print(f"Deflection = {deflection}")
        edge = self.edgeList[0]
        return edge.discretize(Deflection=deflection)


class RevolvedNEdges(RevolvedClosedCurve):
    def __init__(self, name, edgelist):
        super().__init__(name, edgelist)

    def getVertexes(self):
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
                        curveName, [e])
                    verts += curveSection.discretize()
                    break
        return verts


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


def edgelistArea(edgelist: list[Part.Edge]) -> float:
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



def getRevolvedCurve(name, edges):
    # Return an RevolvedClosedCurve object of the list of edges

    if len(edges) == 1:  # single edge ==> a closed curve, or curve section
        return RevolvedClosedCurve(name, edges)

    else:  # three or more edges
        return RevolvedNEdges(name, edges)


def revolve_convex_polygon(verts, eps=1.0e-4):
    '''Given the vertexes of a convex polygon (as FreeCAD Vectors),
    produce surfaces, the interior of which forms a surface of revolution
    of the triangle.

    The vertexes of the triangle are to be given as x-z point (in the x-z plane)
    and are assumed to be already given in CCW order
    There are three possible surfaces:
    (1) A horizontal line (z = z0 = constant) -> horizontal plane
    (2) A vertical line (x = x0 = constant) -> a cylinder
    (2) A slanted line (x0, z0) -> (x1, z1) -> a cone
    '''

    surfaces = []
    expr = ""
    for i in range(len(verts)):
        i1 = (i + 1) % len(verts)
        v0 = verts[i]
        v1 = verts[i1]
        dx = v1.x - v0.x
        dz = v1.z - v0.z
        normal = Vector(dz, 0, -dx)
        if normal.Length < 1.0e-07:
            continue
        normal.normalize()

        if abs(dx) < eps:  #a cylinder
            center = Vector(0, 0, 0)
            axis = Vector(0, 0, 1)
            radius = abs(v0.x)
            cylinder = CylinderSurfaceExporter("", center, axis, radius)
            surfaces.append(cylinder)
            if normal.x < 0:
                expr += f"+{cylinder.id} "
            else:
                expr += f"-{cylinder.id} "

        elif abs(dz) < eps:  # a horizontal plane
            D = v0.dot(normal)
            surf = PlaneSurfaceExporter("", normal, D)
            surfaces.append(surf)
            expr += f"-{surf.id} "

        else:  # must be a slanted line. a conical surface
            theta = math.atan(abs(dx/dz))
            t2 = v0.dot(normal)/normal.z
            center = t2*Vector(0, 0, 1)
            axis = Vector(0, 0, 1)
            surf = ConeSurfaceExporter("", center, axis, theta)
            surfaces.append(surf)
            if normal.x > 0:
                expr += f"-{surf.id} "
            else:
                expr += f"+{surf.id} "

            # we want to select half space of the cone that includes the edge
            # The normal to the plane is Vector(0, 0, 1) (the z-axis)
            # D = coneverex.z
            # if v0.z < center.z, we are on the lower half, i.e, on the - sode f the plane
            # other was we are on the + side of the plane
            selecting_plane = PlaneSurfaceExporter("", axis, center.z)
            surfaces.append(selecting_plane)
            if v0.z < center.z:
                expr += f"-{selecting_plane.id} "
            else:
                expr += f"+{selecting_plane.id} "

    return surfaces, Region(expr)


class RevolutionExporter(SolidExporter):
    def __init__(self, revolveObj):
        super().__init__(revolveObj)
        self.sketchObj = revolveObj.Source
        self.lastName = self.obj.Label  # initial name: might be modified later
        # generate the positions that get computed during export
        self.region = None
        self.surfaces = []

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

    def generate_surfaces(self):
        #
        global Deviation
        revolveObj = self.obj
        axis = revolveObj.Axis
        angle = revolveObj.Angle
        revolveCenter = revolveObj.Base

        # Fractional deviation
        Deviation = revolveObj.ViewObject.Deviation / 100.0


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
            curve = getRevolvedCurve(eName + str(i), edges)
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
        rootCurve.generate_surfaces()
        self.surfaces = rootCurve.surfaces

        firstName = rootCurve.name
        booleanName = firstName

        self.region = rootCurve.region

        rootPos = rootCurve.position
        rootRot = (
            rootCurve.rotation
        )  # for now consider only angle of rotation about z-axis

        for c in lst[1:]:
            node = c[0]
            parity = c[1]
            curve = node.closedCurve
            curve.generate_surfaces()
            self.surfaces += curve.surfaces
            if parity == 0:
                self.region = self.region.union(curve.region)
            else:
                self.region = self.region.cut(curve.region)

        # add cutoff planes if revolution angle is not 360 deg
        if angle != 360:
            phi0_normal = Vector(0, 1, 0)
            phi0_plane = PlaneSurfaceExporter(self.name()+'_phi0', phi0_normal, 0)
            phi1_normal = Vector(math.cos(math.radians(angle+90)), math.sin(math.radians(angle+90)), 0)
            phi1_plane = PlaneSurfaceExporter(self.name()+'_phi1', phi1_normal, 0)
            self.surfaces += [phi0_plane, phi1_plane]

            if phi0_normal.cross(phi1_normal).z > 0:
                planes_region = Region(f"+{phi0_plane.id} -{phi1_plane.id}")
            else:
                planes_region = f"(+{phi0_plane.id} | -{phi1_plane.id})"

            self.region = self.region.intersection(planes_region)

        rot_z_to_dir = FreeCAD.Rotation(Vector(0, 0, 1), axis)  # rotation from z-axis to original axis of revolution
        for surf in self.surfaces:
            surf.rotate(rot_z_to_dir)

        self.position_globally()

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
        self.region = None
        self.surfaces = []


    def generate_surfaces(self):
        verts = self.discretize()
        self.surfaces, self.region = exportXtru(self.name, verts, self.height)

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
        self.position = edgelist[0].Curve.Center

    def generate_surfaces(self):
        edge = self.edgeList[0]
        print(f"circle position {self.position}")
        surf = exportTube(self.name, self.position, edge.Curve.Radius, self.height)
        self.surfaces = [surf]
        self.region = Region(f"-{surf.id}")


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

    def generate_surfaces(self):
        global solids

        edge = self.edgeList[0]
        radius = edge.Curve.Radius
        center = edge.Curve.Center
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

        xtruName = self.name + "_xtru"

        chord_plane, chord_region  = exportXtru(xtruName, [v1, v2], self.height)[0]
        # we want the plane normal to point AWAY from the chord
        if chord_plane.normal.dot(vmid) > 0:
            chord_plane.normal = -chord_plane.Normal
            chord_plane.to_coeffs()
        self.surfaces.append(chord_plane)

        # tube to be cut1
        tubeName = self.name + "_tube"
        cylinder = exportTube(tubeName, center, edge.Curve.Radius, self.height)
        self.surfaces.append(cylinder)

        self.region = Region(f"-{cylinder.id} -{chord_plane.id}")


class ExtrudedEllipticalSection(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)
        # Note extrusion polyogn will be in absolute coordinates
        # since arc section is relative to that, position is actually (0,0,0)
        # same goes for rotation


    def generate_surfaces(self):
        global solids

        edge = self.edgeList[0]
        deflection = Deviation * edge.BoundBox.DiagonalLength
        points = edge.discretize(Deflection=deflection)
        points.append(points[0])
        arrangeCCW(points)
        self.surfaces, self.region = exportXtru(self.name, points, self.height)


class ExtrudedBSpline(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)


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

    def generate_surfaces(self):
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
        self.surfaces, self.region = exportXtru(xtruName, verts, self.height)

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


def exportTube(name, center, radius, height):
    global solids

    axis = Vector(0, 0, 1)
    outer_surface = CylinderSurfaceExporter(name, center, axis, radius)
    return outer_surface


def exportXtru(name, vlist, height):
    from .polygonsHelper import is_convex_polygon, triangulate_polygon_earclip

    def convex_poly_planes(points):
        planes = []
        for i in range(len(points)):
            i1 = (i+1) % len(points)
            edge = points[i1] - points[i]
            normal = Vector(edge.y, -edge.x, 0)
            normal.normalize()

            D = normal.dot(points[i])
            planes.append(PlaneSurfaceExporter(name, normal, D))
        return planes

    def convex_poly_region(planes):
        expr = ""
        for surf in planes:
            expr += f"-{surf.id} "
        return Region(expr)


    # We are assuming that the points that form
    # the edges to be extruded are al coplanar and in the x-y plane
    # with a possible zoffset, which is taken as the common
    # z-coordinate of the first vertex
    if len(vlist) < 3:
        return [], Region("")

    # prune verts: Closed curves get stitched from adjacent edges
    # sometimes the beginning vertex of the next edge is the same as the end vertex
    # of the previous edge. Geant gives a warning about that. To remove the warning
    # we will remove vertices closer to each other than 0.1 nm - 1e-7 mm. If someone is trying
    # to model objects with smaller dimensions, then they should take a lesson in Quantum Mechanic2s
    # Because only adjacent edges could be the same, we just compare each edge to the preceding edge
    vpruned = vlist[:]
    arrangeCCW(vpruned)
    for i in range(len(vlist)):
        i1 = (i+1) % len(vlist)
        if ((vlist[i1] - vlist[i]).Length < 1e-7):
            vpruned.remove(vlist[i1])

    planes = []

    if is_convex_polygon(vpruned):
        planes = convex_poly_planes(vpruned)
        region = convex_poly_region(planes)

    else:
        region = Region("")
        polygon_list = triangulate_polygon_earclip(vpruned)
        for polygon in polygon_list:
            convex_planes = convex_poly_planes(polygon)
            convex_region = convex_poly_region(convex_planes)

            # TODO: remove common planes with opposite normals
            planes += convex_planes
            region = region.union(convex_region)

    return planes, region

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
        Deviation = self.obj.ViewObject.Deviation / 100.0
        # generate the positions that get computed during export

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

    def generate_surfaces(self):
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
        savedSketchPlacement = self.sketchObj.Placement
        self.sketchObj.Placement *= savedSketchPlacement.inverse()
        # do we need a recompute after this?

        # rot_dir_to_z = FreeCAD.Rotation(extrudeDirection, Vector(0, 0, 1))
        # edges = [edge.rotated(Vector(0, 0, 0), rot_dir_to_z.Axis, math.degrees(rot_dir_to_z.Angle)) for edge in sketchObj.Shape.Edges]
        edges = sketchObj.Shape.Edges
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
        rootCurve.generate_surfaces()  # a curve is created with a unique name

        # Our construction assumes extrusion is along z-axis
        # and that the sketch object does not have any placement AND
        # that the edges in a acurve are positioned relative to sketc,
        # It turns out that is WRONG. The edges already fold in the sketch's
        # placement. So we undo the effect of the sketched non-identity
        # placement and then apply it back again at the end

        self.region = rootCurve.region

        firstName = rootCurve.name
        booleanName = firstName

        rootPos = rootCurve.position
        rootRot = (
            rootCurve.rotation
        )  # for now consider only angle of rotation about z-axis

        self.surfaces = rootCurve.surfaces

        for c in lst[1:]:
            node = c[0]
            parity = c[1]
            curve = node.closedCurve
            curve.generate_surfaces()
            self.surfaces += curve.surfaces
            if parity == 0:
                self.region = self.region.union(curve.region)
            else:
                self.region = self.region.cut(curve.region)

        if extrudeObj.Symmetric is False:
            if extrudeObj.Reversed is False:
                zoffset = extrudeObj.LengthRev.Value
            else:
                zoffset = extrudeObj.LengthFwd.Value
        else:
            zoffset = extrudeObj.LengthFwd.Value / 2

        axis = Vector(0, 0, 1)
        top_surface =    PlaneSurfaceExporter(self.obj.Label+'_top', axis, zoffset+height)
        bottom_surface = PlaneSurfaceExporter(self.obj.Label+'_bot', axis, zoffset)
        self.surfaces += [bottom_surface, top_surface]
        self.region = Region(self.region.expr + f" -{top_surface.id} +{bottom_surface.id}")

        # Restore the sketch Placement
        # undo the sketch placement
        self.sketchObj.Placement = savedSketchPlacement
        print(f"Extrude global placement = {self.obj.getGlobalPlacement()}")
        print(f"Sketch local placement = {self.sketchObj.Placement}")
        globalPlacement = self.obj.getGlobalPlacement()*self.sketchObj.Placement
        print(f"sketch elements global placement is {globalPlacement}")

        T = globalPlacement.Base
        R = globalPlacement.Rotation

        for surf in self.surfaces:
            surf.rotate(R)
            surf.translate(T)

#--------------------Auto tessellation classes and routines -----------------------------------------------------------

class Plane:
    def __init__(self, normal, D):
        self.normal = normal
        self.D = D

    def inside(self, point):
        return self.normal.dot(point) < self.D

    def __hash__(self):
        s = [float(f" {f:.4e}") for f in self.normal]
        s.append(float(f" {self.D:.4e}"))
        return hash(tuple(s))

    def __eq__(self, other):
        if not (type(self) is type(other)):
            return False

        return hash(self) == hash(other)


class RegionSet:
    def __init__(self, v2planes_dict, mesh):
        ''' v2planes_dict is a dictionary of a mesh point index and all the Planes that pass through that point
        and a Plane that contains it as value '''
        self.v2p = v2planes_dict
        self.mesh = mesh

    def is_edge_inside(self, edge, plane):
        ''' test if the edge (a pair of point indexes is inside this RegionSet
        To be inside both points must be in the set of points AND there must be points
        in the set on BOTH sides of the given plane
        '''

        mypoints = self.v2p.keys()

        count = 0
        for vid in edge:
            if vid in mypoints:
                count += 1
                if count >= 2:
                    break

        if count < 2:
            return False

        nplus = 0  # number of points on the + side of the plane
        nminus = 0  # number of points on the nedgative side of the plane

        eps = 1.0e-9
        for vid in mypoints:
            point = self.mesh.Points[vid].Vector
            dist = plane.normal.dot(point) - plane.D
            if dist < -eps:
                nminus += 1
            elif dist > eps:
                nplus += 1
            if nplus > 0 and nminus > 0:
                return True

        return False

    def split_by_plane(self, plane):
        ''' split this region set into two region sets, one where all the points are on the inside of
        the plane and one on the outside'''

        region1 = defaultdict(list)
        region2 = defaultdict(list)

        eps = 1.0e-9
        onplane = []   # list of points on the plane (gain, there are point indexes, not points)
        for vid in list(self.v2p.keys()):
            vec = self.mesh.Points[vid].Vector
            dist = plane.normal.dot(vec) - plane.D
            if dist < -eps:
                region1[vid] = self.v2p[vid][:]
            elif dist > eps:
                region2[vid] = self.v2p[vid][:]   # otherwise, put the planes in region 2
            else:
                onplane.append(vid)

        # add the splitting plane to the edge points and remove the "wrong" face from the edge vertexes
        plane1 = plane  # just a change of notation for clarity
        plane2 = Plane(-plane.normal, -plane.D)  # flip the cutting plane for region2
        for vid in  onplane:
            region1[vid] = self.v2p[vid][:]
            region2[vid] = self.v2p[vid][:]
            for pl in region1[vid][:]:  # copy so we don't screw up the list while we're iterating over it
                if pl.normal.dot(plane1.normal) < 0:
                    region1[vid].remove(pl)   # remove the wrong plane
            region1[vid].append(plane1)  # and add the cutting plane

            for pl in region2[vid][:]:  # copy so we don't screw up the list while we're iterating over it
                if pl.normal.dot(plane2.normal) < 0:
                    region2[vid].remove(pl)   # remove the wrong plane
            region2[vid].append(plane2)  # and add the cutting plane

        R1 = RegionSet(region1, self.mesh)
        R2 = RegionSet(region2, self.mesh)

        return R1, R2



class ShapeMesher:
    deflection = 0.5
    angularDeflection = math.radians(28.5)

    def __init__(self, shape):
        import MeshPart

        self.shape = shape
        self.mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=ShapeMesher.deflection,
                                           AngularDeflection=ShapeMesher.angularDeflection, Relative=False)

        self.mesh.harmonizeNormals()
        # Debug

        self.edge_dict = self.edge_face_dict()
        self.parallel_face_dict = self.parallel_set()

        print(f"Num faces = {len(self.mesh.Facets)}")
        print(f"Num edges = {len(self.edge_dict)}")

    def _edge_dir(self, edge):
        """Return a unit vector along the geometric edge defined by mesh point indices."""
        idx = list(edge)
        v0 = self.mesh.Points[idx[0]].Vector
        v1 = self.mesh.Points[idx[1]].Vector
        v = v1 - v0
        if v.Length == 0:
            return v
        v.normalize()
        return v

    def plane(self, facet):
        normal = facet.Normal
        vid = facet.PointIndices[0]
        p0 = self.mesh.Points[vid].Vector
        D = normal.dot(p0)
        return Plane(normal, D)

    def vertex_to_planes_map(self):
        v2planes = {}
        for fi, facet in enumerate(self.mesh.Facets):
            for vid in facet.PointIndices:
                plane = self.plane(facet)
                v2planes[vid] = plane
        return v2planes

    def parallel_set(self):
        ''' return a dictionary of face as key and set of faces that are parallel with that face'''
        par_face_dict = {}
        for face1 in self.mesh.Facets:
            s = set()
            normal1 = face1.Normal
            for face2 in self.mesh.Facets:
                if face1.Index == face2.Index:
                    continue
                normal2 = face2.Normal
                if normal2.dot(normal1) > 0.999:
                    s.add(face2.Index)
            par_face_dict[face1.Index] = s

        return par_face_dict

    def edge_face_dict(self):
        d = {}
        for face in self.mesh.Facets:
            pointIndexes = face.PointIndices
            n = len(pointIndexes)
            for i in range(n):
                i1 = (i+1)  % n

                edge = (pointIndexes[i], pointIndexes[i1])
                fz = frozenset(edge)
                if fz not in d:
                    d[fz]  = [face.Index]
                else:
                    d[fz].append(face.Index)
        return d

    def is_mesh_concave(self):
        edge, _ = self.get_concave_edge()
        return edge is not None

    def my_concave_edge_test(self, edge):
        faceIndexes = self.edge_dict[edge]
        f1 = self.mesh.Facets[faceIndexes[0]]
        f2 = self.mesh.Facets[faceIndexes[1]]
        c1 = (Vector(f1.Points[0]) + Vector(f1.Points[1]) + Vector(f1.Points[2])) / 3
        c2 = (Vector(f2.Points[0]) + Vector(f2.Points[1]) + Vector(f2.Points[2])) / 3
        eps = (c2-c1).Length/10
        p1 = c1 - eps * f1.Normal
        p2 = c2 - eps * f2.Normal

        if abs(f1.Normal.dot(f2.Normal)) > 0.999:
            return False

        if (p2 - p1).Length > (c2 - c1).Length:
            self.display_edge(edge)
            return True

        return False

    def get_concave_edge(self):
        """
        Return (edge, nmean, max_concave_angle) where:
          - edge: a concave edge chosen among all concave candidates
          - nmean: n1 + n2 for that edge (for your plane construction)
          - max_concave_angle: maximum dihedral angle (in radians) among
                               all edges that are classified as concave

        If no concave edges are found, returns (None, None, 0.0).
        """
        # Your “interesting concavity” threshold per *edge*
        MIN_DIHEDRAL_ANGLE = math.radians(5.0)  # tune as you like
        MIN_SIN = math.sin(MIN_DIHEDRAL_ANGLE)

        # How close to -1 we require (n1 × n2) · ê to be
        EPS_SIGN = 1e-3  # tolerance; adjust if needed

        best_edge = None
        best_nmean = None

        best_sin_concave = 0.0  # sin(dihedral) for the **most concave** edge (among concave ones)
        chosen_debug = None

        for edge, faceIndexes in self.edge_dict.items():
            # Only internal edges with exactly two adjacent facets
            if len(faceIndexes) != 2:
                continue

            f1 = self.mesh.Facets[faceIndexes[0]]
            f2 = self.mesh.Facets[faceIndexes[1]]

            v_edge = self._edge_dir(edge)
            if v_edge.Length == 0:
                continue

            n1 = f1.Normal
            n2 = f2.Normal

            # Cross product gives a vector along the intersection line
            n1xn2 = n1.cross(n2)
            sinthet = n1xn2.Length  # ~ sin(dihedral angle between n1 and n2)

            # 1) Filter out almost-parallel normals: flat or nearly flat adjacency
            if sinthet < MIN_SIN:
                continue

            # 2) Concavity sign test using your sign convention
            n1xn2.normalize()
            dot_ce = n1xn2.dot(v_edge)

            # We consider the edge concave only if the cross product
            # is pointing reliably in the opposite direction of the edge
            if self.my_concave_edge_test(edge):
                # print("my_concave_edge_test says this edge is convex. The get concave_edge says it is concave")
                if sinthet > best_sin_concave:
                    best_sin_concave = sinthet
                    best_edge = edge
                    best_nmean = n1 + n2

                    angle = math.asin(max(min(sinthet, 1.0), -1.0))

        if best_edge is None:
            # No concave edges found at all
            return None, None, 0.0

        # Convert the maximum concave sin(angle) to an angle in radians
        max_concave_angle = math.asin(
            max(min(best_sin_concave, 1.0), -1.0)
        )

        return best_edge, best_nmean, max_concave_angle

    def share_edge(self, iFace1, iFace2):
        ''' return true if faces with indexes iFace1, iFace2 share an edge'''

        edges_set = set()
        face1 = self.mesh.Facets[iFace1]
        face2 = self.mesh.Facets[iFace2]
        for f in [face1, face2]:
            pointIndexes = f.PointIndices
            n = len(f.PointIndices)
            for i in range(n):
                i1 = (i+1) % n
                edge = (pointIndexes[i], pointIndexes[i1])
                fz = frozenset(edge)
                edges_set.add(fz)

        return len(edges_set) < 6  # if the faces share an edge, then there should be less than 6 edges in the set


    def get_face_edges(self, iFace):
        ''' return the three edges as a frozenset of the end point indexes of the endpoint'''
        face = self.mesh.Facets[iFace]
        pointIndexes = face.PointIndices
        n = len(pointIndexes)
        edges = []
        for i in range(n):
            i1 = (i+1) % n
            edge = (pointIndexes[i], pointIndexes[i1])
            fz = frozenset(edge)
            edges.append(fz)

        return edges


    def concave_face_chains(self):
        ''' return a list of a list of faces that share an edge and that are concave at the shared edge'''
        concave_edges = self.get_concave_edges()

        def concave_edge_chain(edge, chain_set):
            if edge in concave_edges:
                chain_set.add(edge)
                concave_edges.remove(edge)
                f1 = self.edge_dict[edge][0]
                f2 = self.edge_dict[edge][1]
                for f in [f1, f2]:
                    edges = self.get_face_edges(f)
                    for e in edges:
                        concave_edge_chain(e, chain_set)
            else:
                return

        concave_chains = []
        while len(concave_edges) > 0:
            edge_set = set()
            edge = concave_edges[0]
            concave_edge_chain(edge, edge_set)

            face_set = set()
            for e in edge_set:
                f1 = self.edge_dict[e][0]
                f2 = self.edge_dict[e][1]
                face_set.add(f1)
                face_set.add(f2)
                # add all edges that are parallel to the two faces to the same chain
                for f1par in self.parallel_face_dict[f1]:
                    face_set.add(f1par)
                for f2par in self.parallel_face_dict[f2]:
                    face_set.add(f2par)

            concave_chains.append(face_set)

        return concave_chains

    def get_concave_edges(self):
        """
        return list of concave edges
        """
        chosen_debug = None

        concaveList = []
        for edge, faceIndexes in self.edge_dict.items():
            # Only internal edges with exactly two adjacent facets
            if len(faceIndexes) != 2:
                continue

            f1 = self.mesh.Facets[faceIndexes[0]]
            f2 = self.mesh.Facets[faceIndexes[1]]

            v_edge = self._edge_dir(edge)
            if v_edge.Length == 0:
                continue

            if self.my_concave_edge_test(edge):
                concaveList.append(edge)

        return concaveList

    def is_valid(self):
        '''
        Validate mesh:
        (1) Volume must be > deflection^3
        (2) All faces must have area > deflection^2
        (3) All edges must have length > deflection
        (4) all normals must have length > 0
        (5) number of faces must greater than 4
        '''
        nfaces = self.mesh.CountFacets
        if nfaces <= 4:
            print(f"mesh has 4 or fewer faces = {nfaces}")
            return 5

        if self.mesh.Volume < ShapeMesher.deflection**3:
            print(f"mesh volume {self.mesh.Volume} less than deflectin^3 {ShapeMesher.deflection**3}")
            return 1

        for i, face in enumerate(self.mesh.Facets):
            if face.Normal.Length < 0.5:
                print(f"face {i}'s normal length is less than 1: {face.Normal.Length}")
                return 4
            if face.Area < ShapeMesher.deflection*ShapeMesher.deflection:
                print(f"face area smaller than deflection^2: {face.Area}")
                return 2

            n = len(face.Points)
            for j in range(n):
                v0 = Vector(face.Points[j][0], face.Points[j][1], face.Points[j][2])
                j1 = (j+1) % n
                v1 = Vector(face.Points[j1][0], face.Points[j1][1], face.Points[j1][2])
                edge_len = (v1-v0).Length
                if edge_len < ShapeMesher.deflection:
                    print(f"Warning  edge {j} of face {i} is shorter than deflection: edge length = {edge_len}  deflection = {ShapeMesher.deflection}")
                    continue

        return 0

    def display_face(self, iFace, color):
        facet = self.mesh.Facets[iFace]
        pnts = facet.Points
        vecs = [ Vector(pnt) for pnt in pnts ]
        vecs.append(vecs[0])
        wire = Part.makePolygon(vecs)
        face = Part.Face(wire)
        obj = Part.show(face)
        obj.ViewObject.ShapeColor = color

        normal = facet.Normal
        c = (vecs[0] + vecs[1] + vecs[2])/3
        p1 = c - 0.5*normal
        p2 = c + 2.0*normal
        L = Part.LineSegment(p1, p2)
        Part.show(L.toShape(), "normal")

    def display_edge(self, edge):
        pts = list(edge)
        idx1 = pts[0]
        idx2 = pts[1]
        v1 = Vector(self.mesh.Points[idx1].x, self.mesh.Points[idx1].y, self.mesh.Points[idx1].z)
        v2 = Vector(self.mesh.Points[idx2].x, self.mesh.Points[idx2].y, self.mesh.Points[idx2].z)
        L = Part.LineSegment(v1, v2)
        shape = L.toShape()
        # shape.ViewObject.LineColor = (255, 255, 255)
        Part.show(shape, "edge")

    def edge_plane(self, edge):
        ''' Return a plane that passes through the edge. The plane is midway between the two
        faces that border thed edge
        '''
        faceIndexes = self.edge_dict[edge]
        f1 = self.mesh.Facets[faceIndexes[0]]
        f2 = self.mesh.Facets[faceIndexes[1]]
        v_edge = self._edge_dir(edge)
        n1 = f1.Normal
        n2 = f2.Normal
        nmean = n1 + n2  # only direction matters, so we don't need to normalize

        plane_normal = v_edge.cross(nmean)  # note that the sense of the plane_normal could be eiher way
        plane_normal.normalize()
        p0 = self.mesh.Points[list(edge)[0]].Vector  # one of the points on the edge
        D = plane_normal.dot(p0)

        return Plane(plane_normal, D)


    def split_along_concaves(self):
        ''' Returns a list of RegionSets that are presumably all convex
        It does this by splitting an initial RegionSet containing all the mesh points (point indexes, actually)
        into two halves by a splitting plane that passes through a concaved edge. Do this until all the
        concaved edges have been consumed
        '''

        concave_edges = self.get_concave_edges()

        # first form a RegionSet of all the points and planes of faces
        v2p = defaultdict(list)
        for fi, facet in enumerate(self.mesh.Facets):
            for vid in facet.PointIndices:
                plane = self.plane(facet)
                v2p[vid].append(plane)

        r0 = RegionSet(v2p, self.mesh)
        regions = [r0]
        while len(concave_edges) > 0:
            edge = concave_edges[0]
            for region in regions:
                plane = self.edge_plane(edge)  # create a splitting plane along that edge
                if region.is_edge_inside(edge, plane):  # find which region edge is inside
                    region1, region2 = region.split_by_plane(plane)  # get the two split regions
                    if region1 is None or region2 is None:
                        break  # no split happened. Cutting by a degenerate plane, ie. a plane that has been used before
                    regions.remove(region)  # remove the region that has been just split
                    regions.append(region1) # and replace with the two split regions
                    regions.append(region2)
                    break
            concave_edges.remove(edge) # remove the splitting edge from the list of concave edges

        return regions


def compound_to_solids(shape):
    """Convert a Compound (or other) to a list of Solids if possible."""
    if shape.ShapeType == "Solid":
        return [shape]
    sols = []
    # If we got a Compound of shells / faces, try to make solids from its shells
    for sh in shape.Shells:
        try:
            sld = Part.makeSolid(sh)
        except Exception:
            continue
        if sld.ShapeType == "Solid" and sld.isValid():
            sols.append(sld)
    # If there are already Solids in the compound, include them
    for s in shape.Solids:
        if s.ShapeType == "Solid" and s.isValid():
            sols.append(s)
    return sols

def common_via_bopfeatures(shapeA, shapeB, base_name="CommonTmp"):
    """Compute intersection of two Part.Shapes using the same BOPFeatures
    path that the GUI 'Common' command uses. Returns the resulting Shape."""
    doc = FreeCAD.ActiveDocument

    # 1) Create temporary Part::Feature objects
    objA = doc.addObject("Part::Feature", base_name + "_A")
    objA.Shape = shapeA
    objB = doc.addObject("Part::Feature", base_name + "_B")
    objB.Shape = shapeB
    doc.recompute()

    # 2) Run BOPFeatures.make_multi_common on their names
    bp = BOPFeatures.BOPFeatures(doc)
    common_obj = bp.make_multi_common([objA.Name, objB.Name])
    doc.recompute()

    # 3) Extract the resulting Shape
    common_shape = common_obj.Shape

    # (Optional) clean up the temp inputs, keep only result if you like
    # doc.removeObject(objA.Name)
    # doc.removeObject(objB.Name)

    return common_shape, common_obj

MAX_DEPTH = 50
def decompose_recursive(shapeMesher, results, depth=0):

    if depth >= MAX_DEPTH:
        results.append(shapeMesher)
        return

    mesh = shapeMesher.mesh
    concave_edge, nmean, max_angle = shapeMesher.get_concave_edge()
    MIN_GLOBAL_ANGLE = math.radians(5.0)

    if concave_edge is None or max_angle < MIN_GLOBAL_ANGLE:
        results.append(shapeMesher)
        return

    edge_pts = [mesh.Points[pntIndex].Vector for pntIndex in list(concave_edge)]
    p0, p1 = edge_pts
    edgeVec = p1 - p0
    # DEBUG
    # edge_line = Part.makeLine(p0, p1)
    # Part.show(edge_line, "edge_line")

    normal = edgeVec.cross(nmean)
    if normal.Length == 0:
        results.append(shapeMesher)
        return
    normal.normalize()

    base = shapeMesher.shape
    bbox = base.BoundBox
    planeWidth = 2 * bbox.DiagonalLength

    # (if you still want to re-center by COM, keep your translation here)
    cuttingPlane = Part.makePlane(planeWidth, planeWidth, p0, normal)
    # translate plane so center of mass of plane is at edge point
    planeCM = cuttingPlane.CenterOfMass
    cuttingPlane.Placement.Base -= planeCM - p0

    if not cuttingPlane.isValid():
        results.append(shapeMesher)
        return

    # Make solid from shell
    solid = Part.makeSolid(base)
    if solid.ShapeType != "Solid" or not solid.isValid():
        results.append(shapeMesher)
        return

    # Build two slabs by extruding plane
    n = cuttingPlane.normalAt(0.5, 0.5)
    if n.Length == 0:
        results.append(shapeMesher)
        return
    n.normalize()
    h = solid.BoundBox.DiagonalLength * 2.0

    upper_extrude = cuttingPlane.extrude(n * h)
    lower_extrude = cuttingPlane.extrude(-n * h)

    # Use BOPFeatures (same as GUI) to get the intersections
    upper, upper_obj = common_via_bopfeatures(solid, upper_extrude, "UpperCut")
    lower, lower_obj = common_via_bopfeatures(solid, lower_extrude, "LowerCut")

    print("upper:", upper.ShapeType, "valid:", upper.isValid(), "vol:", upper.Volume)
    print("lower:", lower.ShapeType, "valid:", lower.isValid(), "vol:", lower.Volume)

    child_shapes = []

    # upper can be a Solid or a Compound; extract solids if needed
    if upper.ShapeType == "Solid" and upper.isValid():
        child_shapes.append(upper)
    elif upper.Solids:
        for s in upper.Solids:
            if s.isValid():
                child_shapes.append(s)

    if lower.ShapeType == "Solid" and lower.isValid():
        child_shapes.append(lower)
    elif lower.Solids:
        for s in lower.Solids:
            if s.isValid():
                child_shapes.append(s)

    # If nothing usable came out, stop recursing on this shape
    if not child_shapes:
        results.append(shapeMesher)
        return

    for s in child_shapes:
        print(f"child: type={s.ShapeType}, valid={s.isValid()}, vol={s.Volume}")
        if not s.isValid():
            continue

        mesher = ShapeMesher(s)

        code = mesher.is_valid()

        if code == 1:  # volume too small
            continue
        elif code == 5:  # too few faces
            results.append(mesher)
            continue
        elif code == 4:  # normal too small.
            results.append(mesher)
            continue


        # if s.Volume < ShapeMesher.deflection**3:
        #     results.append(ShapeMesher(s))
        #    print("Skipped decomposing this shape. Volume too small")
        #     continue
        # should check if the cutting resulted in more than one component
        components = mesher.mesh.getSeparateComponents()
        if len(components) > 1:
            print("** cut mesh has more than one component **")

        decompose_recursive(mesher, results, depth+1)


class AutoTessellateExporter(SolidExporter):

    shapesDict = {}  # a dictionary of exported shapes and their names

    def __init__(self, obj):
        super().__init__(obj)
        self.index = 0

        # So my understanding of the structure of the mesh, so far, is the following
        # if E is the number of Edges, F the number of faces and V the number of Volumes
        # then Edge_ids go from 1 - E
        # Face ids go form E+1 - E+1+F
        # and volume ids go from E+F+1+1 - E+F+1+1+V
        # so mesh.getElementNode(id) will get the edge node ids of id is in the Edge ids range
        # will get the face id nodes for ids in the Face ids range
        # and will get the volume id nodes for id in the Volume id range.
        # For edges there will be two node ids, corresponding to the ends of the edge
        # For faces, there will be three ids, corresponding to the triangle coordinates
        # and for Volume ids, there will be four node ids, corresponding to the four corners of
        # of the tetrahedron
        # mesh.Node[id] gives the Vector coordinates of the node, that is the point
        # P.S: Face ids are those of the boundary faces only, not of every tetrahedron surface

        # get a list of planes, one for each face. At present the sense of
        # the normal is arbitrary. When we build the regions for each tetrahedron, we will
        # figure out the in/out of each plane

        self.surfacesDict = {}  # to reducs the number of duplicate planes for parallel faces

    def solidMesh(self):
        import ObjectsFem
        import femmesh.gmshtools as gmshtools

        def gmsh_sizes_from_view(obj,
                                 elems_across=10,
                                 interior_factor=3.0,
                                 min_hmin = 10.0):
            """
            Map FreeCAD ViewObject Deviation / AngularDeflection to Gmsh mesh sizes.
            Returns:
              h_min, h_max, min_elems_2pi
            """
            v = obj.ViewObject

            shp = obj.Shape
            bbox = shp.BoundBox

            L = max(bbox.XLength, bbox.YLength, bbox.ZLength)

            if L <= 0:
                # degenerate
                h_min = min_hmin
            else:
                h_min = max(L / elems_across, min_hmin)

            h_max = h_min * interior_factor

            return h_min, h_max

        doc = FreeCAD.ActiveDocument



        h_min, h_max = gmsh_sizes_from_view(self.obj)
        # mesh = doc.addObject('Fem::FemMeshGmshFromShape', 'GmshMesh')
        mesh = ObjectsFem.makeMeshGmsh(doc, f"{self.obj.Label}_temporary_mesh")
        print(mesh, mesh.TypeId)

        mesh.Shape = self.obj

        mesh.CharacteristicLengthMin = h_min
        mesh.CharacteristicLengthMax = h_max

        # Curvature-based refinement
        mesh.MeshSizeFromCurvature = True

        # 3D mesh algorithm and optimization
        mesh.Algorithm3D = 1  # Tetrahedral
        mesh.OptimizeStd = True

        mesher = gmshtools.GmshTools(mesh)
        mesher.create_mesh()
        doc.recompute()

        # 4 loop over tetrahedra, creating planes and regions for each

        fem_mesh = mesh.FemMesh
        faces_attr = fem_mesh.Faces
        if isinstance(faces_attr, dict):
            face_ids = list(faces_attr.keys())
        else:
            face_ids = list(faces_attr)

        # So my understanding of the structure of the mesh, so far, is the following
        # if E is the number of Edges, F the number of faces and V the number of Volumes
        # then Edge_ids go from 1 - E
        # Face ids go form E+1 - E+1+F
        # and volume ids go from E+F+1+1 - E+F+1+1+V
        # so mesh.getElementNoded(id) will get the edge node ids of id is in the Edge ids range
        # will get the face id nodes for ids in the Face ids range
        # and will get the volume id nodes for id in the Volume id range.
        # For edges there will be two node ids, corresponding to the ends of the edge
        # For faces, there will be three ids, corresponding to the triangle coordinates
        # and for Volume ids, there will be four node ids, corresponding to the four coreners of
        # of the tetrahedron
        # mesh.Node[id] gives the Vector coordinates of the node, that is the point
        # P.S: Face ids are those of the boundary faces only, not of every tetrahedron surface

        # get a list of planes, one for each face. At present the sense of
        # the normal is arbitrary. When we build the regions for each tetrahedron, we will
        # figure out the in/out of each plane

        def plane_from_face(node_ids):
            face_key = frozenset(node_ids)
            coords = [fem_mesh.Nodes[n] for n in node_ids]
            v1 = coords[1] - coords[0]
            v2 = coords[2] - coords[1]
            normal = v1.cross(v2)
            normal.normalize()
            D = normal.dot(coords[0])
            surf = PlaneSurfaceExporter(f"{self.obj.Label}_{vol_id}_{i}", normal, D)
            plane_nodes_dict[face_key] = surf  # given three node ids, we identify the plane
            # regardless of the order in which node ids are given
            surfaces.append(surf)

        surfaces = []
        plane_nodes_dict = {}
        region_expr = ""

        for vol_id in fem_mesh.Volumes:
            volume_region = ""
            # Get the node IDs associated with this tetrahedron
            # For a 1st order mesh, this will return 4 nodes
            node_ids = fem_mesh.getElementNodes(vol_id)
            for i in range(4):  # we should doublecheck we are using tetrahedra
                opposite_corner = node_ids[i]
                face_corners = node_ids[:i] + node_ids[i + 1:]  # other corners
                face = frozenset(face_corners)
                if face not in plane_nodes_dict:  # if face not already in dictionary, build it
                    plane_from_face(face_corners)
                vector_to_face = fem_mesh.Nodes[face_corners[0]] - fem_mesh.Nodes[opposite_corner]
                surface = plane_nodes_dict[face]
                if surface.normal.dot(vector_to_face) > 0:  # normal points to outside, we want to be in
                    volume_region += f"-{surface.id} "
                else:
                    volume_region += f"+{surface.id} "

            if region_expr == "":
                region_expr = f"({volume_region})"
            else:
                region_expr += f"|({volume_region})"

        return surfaces, Region(region_expr)

    def face_to_plane(self, face):
        def plane_key():
            return (round(normal.x, 7), round(normal.y, 7), round(normal.z, 7), round(D, 7))

        normal = Vector(face.Normal.x, face.Normal.y, face.Normal.z)
        # remember we need to convert from mm to cm
        point0 = Vector(face.Points[0][0], face.Points[0][1], face.Points[0][2])
        D = normal.dot(point0)
        key =  plane_key()
        if  key in self.surfacesDict:
            return None  # may be a poor way of signaling to the caller that the surface has been processed
        else:
            planesurface = PlaneSurfaceExporter(self.name()+f"_{self.index}", normal, D)
            self.surfacesDict[key] = planesurface

        self.index += 1
        return planesurface

    def remove_redundant_planes(self, planes):
        set_of_planes = set()
        for plane in planes:
            set_of_planes.add(plane)
        return list(set_of_planes)

    def check_convex_face(self, face, mesh):
        normal = Vector(face.Normal.x, face.Normal.y, face.Normal.z)
        point0 = Vector(face.Points[0][0], face.Points[0][1], face.Points[0][2])
        D = normal.dot(point0)
        pnts = [p.Vector for p in mesh.Points]

        for p in pnts:
            if p.dot(normal) > D:
                return False
        return True

    def generate_surfaces(self):
        import MeshPart
        global obj_top_children_dict

        if self.obj.TypeId != 'Mesh::Feature':

            shape = self.obj.Shape.copy(False)

            bbox = shape.BoundBox
            minLength = min([bbox.XLength, bbox.YLength, bbox.ZLength])

            # shape.Placement = FreeCAD.Placement()  # remove object's placement

            print(f"Autotessellating {self.obj.Label} which is of type {self.obj.TypeId}")
            viewObject = self.obj.ViewObject
            deflection = viewObject.Deviation  # this is in percent
            linearDeflection = deflection/100*minLength
            angularDeflection = viewObject.AngularDeflection.Value
            ShapeMesher.deflection = linearDeflection
            ShapeMesher.angularDeflection = angularDeflection

            shapeMesher = ShapeMesher(shape)

            components = shapeMesher.mesh.getSeparateComponents()
        else:
            components = self.obj.Mesh.getSeparateComponents()

        self.region = Region("")
        for i, comp in enumerate(components):
            V = comp.CountPoints
            E = comp.CountEdges
            F = comp.CountFacets
            chi = V - E + F
            genus = (2 - chi) / 2
            print(f"Component {i} Verts = {V}, Edges = {E}, Faces = {F}, Eueler = {chi} genus = {genus}")

            shape = Part.Shape()
            tolerance = 0.1
            shape.makeShapeFromMesh(comp.Topology, tolerance)
            componentMesher = ShapeMesher(shape)
            component_region = ""

            region_sets = componentMesher.split_along_concaves()
            j = 0
            for region in region_sets:
                planes = set()
                for vid in region.v2p:
                    vid_planes = region.v2p[vid]
                    for pl in vid_planes:
                        planes.add(pl)
                region_expr = ""
                k = 0
                for plane in planes:
                    # i = mesh component index
                    # j = region index in this component
                    # k = plane index for planes in this region
                    surf = PlaneSurfaceExporter(self.name()+f"_{i}_{j}_{k}", Vector(plane.normal), plane.D)
                    k += 1
                    self.surfaces.append(surf)
                    region_expr += f"-{surf.id} "
                if component_region == "":
                    component_region = f"({region_expr})"
                else:
                    component_region += f" | ({region_expr})"
                j += 1

            # TODO, test if the regions formaed are convex or not.
            self.region = self.region.union(Region(component_region))

        self.position_globally()
