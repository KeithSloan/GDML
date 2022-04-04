# Thu Mar 03 12:50:19 PM PST 2022
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

import FreeCAD, os, Part, math
from FreeCAD import Vector
from .GDMLObjects import GDMLcommon, GDMLBox, GDMLTube
# modif add
# from .GDMLObjects import getMult, convertionlisteCharToLunit

import sys
try:
    import lxml.etree as ET
    FreeCAD.Console.PrintMessage("running with lxml.etree\n")
    XML_IO_VERSION = 'lxml'
except ImportError:
    try:
        import xml.etree.ElementTree as ET
        FreeCAD.Console.PrintMessage("running with xml.etree.ElementTree\n")
        XML_IO_VERSION = 'xml'
    except ImportError:
        FreeCAD.Console.PrintMessage('pb xml lib not found\n')
        sys.exit()
# xml handling
# import argparse
# from   xml.etree.ElementTree import XML
#################################

global zOrder

from .GDMLObjects import GDMLQuadrangular, GDMLTriangular, \
                        GDML2dVertex, GDMLSection, \
                        GDMLmaterial, GDMLfraction, \
                        GDMLcomposite, GDMLisotope, \
                        GDMLelement, GDMLconstant, GDMLvariable, \
                        GDMLquantity

from . import GDMLShared

# ***************************************************************************
# Tailor following to your requirements ( Should all be strings )          *
# no doubt there will be a problem when they do implement Value
if open.__module__ in ['__builtin__', 'io']:
    pythonopen = open  # to distinguish python built-in open function from the one declared here

# ## modifs lambda


def verifNameUnique(name):
    # need to be done!!
    return True

# ## end modifs lambda

#########################################################
# Pretty format GDML                                    #
#########################################################

def indent(elem, level=0):
    i = "\n" + level*"  "
    j = "\n" + (level-1)*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem
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

    def place(self, volRef):
        print("Can't place base class MultiPlace")

    def xml(self):
        print("Can't place base class MultiPlace")

    def name(self):
        prefix = 'x'
        if self.obj.Label[0].isdigit():
            prefix = 'x'
        return prefix + self.obj.Label

    @staticmethod
    def getPlacer(obj):
        if obj.TypeId == 'Part::Mirroring':
            return MirrorPlacer(obj)
        else:
            print(f'{obj.Label} is not a placer')
            return None


class MirrorPlacer(MultiPlacer):
    def __init__(self, obj):
        super().__init__(obj)

    def place(self, volRef):
        global structure
        assembly = ET.Element('assembly', {'name': self.obj.Label})
        # structure.insert(0, assembly)
        # insert just before worlVol, which should be last
        worldIndex = len(structure) - 1
        structure.insert(worldIndex, assembly)
        pos = self.obj.Source.Placement.Base
        name = volRef+'_mirror'
        pvol = ET.SubElement(assembly, 'physvol')
        ET.SubElement(pvol, 'volumeref', {'ref': volRef})
        normal = self.obj.Normal
        # reflect the position about the reflection plane
        unitVec = normal.normalize()
        posAlongNormal = pos.dot(unitVec)*unitVec
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
            scl = Vector(1, 1, 1-1)
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
            rot.Angle = 2*rot.Angle
            newPos = rot*newPos
        sourcePlacement = FreeCAD.Placement(newPos, rot)
        # placement = self.obj.Placement*sourcePlacement
        placement = sourcePlacement
        exportPosition(name, pvol, placement.Base)
        if rotX is True:
            exportRotation(name, pvol, placement.Rotation)
        exportScaling(name, pvol, scl)


#########################################################
# Pretty format GDML                                    #
#########################################################


def indent(elem, level=0):
    i = "\n" + level*"  "
    j = "\n" + (level-1)*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem

#########################################


def nameFromLabel(label):
    if ' ' not in label:
        return label
    else:
        return(label.split(' ')[0])


def initGDML():
    NS = 'http://www.w3.org/2001/XMLSchema-instance'
    location_attribute = '{%s}noNamespaceSchemaLocation' % NS
    gdml = ET.Element('gdml', attrib={location_attribute:
                                      'http://service-spi.web.cern.ch/service-spi/app/releases/GDML/schema/gdml.xsd'})
    # print(gdml.tag)

    return gdml

#################################
#  Setup GDML environment
#################################


def GDMLstructure():
    # print("Setup GDML structure")
    #################################
    # globals
    ################################
    global gdml, constants, variables, define, materials, solids, \
           structure, setup
    global WorldVOL
    global defineCnt, LVcount, PVcount, POScount, ROTcount, SCLcount
    global centerDefined
    global identityDefined
    global gxml

    centerDefined = False
    identityDefined = False
    defineCnt = LVcount = PVcount = POScount = ROTcount = SCLcount = 1

    gdml = initGDML()
    define = ET.SubElement(gdml, 'define')
    materials = ET.SubElement(gdml, 'materials')
    solids = ET.SubElement(gdml, 'solids')
    solids.clear()
    structure = ET.SubElement(gdml, 'structure')
    setup = ET.SubElement(gdml, 'setup', {'name': 'Default', 'version': '1.0'})
    gxml = ET.Element('gxml')

    return structure


def defineMaterials():
    # Replaced by loading Default
    # print("Define Materials")
    global materials


def exportDefine(name, v):
    global define
    ET.SubElement(define, 'position', {'name': name, 'unit': 'mm',
                                       'x': str(v[0]),
                                       'y': str(v[1]),
                                       'z': str(v[2])})


'''
def exportDefineVertex(name, v, index):
    global define
    ET.SubElement(define, 'position', {'name': name + str(index),
                                       'unit': 'mm', 'x': str(v.X), 'y': str(v.Y), 'z': str(v.Z)})
'''


def exportDefineVertex(name, v, index):
    global define
    ET.SubElement(define, 'position', {'name': name + str(index),
                                       'unit': 'mm',
                                       'x': str(v.x),
                                       'y': str(v.y),
                                       'z': str(v.z)})


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
    name = 'WorldBox'
    ET.SubElement(solids, 'box', {'name': name,
                                  'x': str(1000),
                                  'y': str(1000),
                                  'z': str(1000),
                                  # 'x': str(2*max(abs(bbox.XMin), abs(bbox.XMax))), \
                                  # 'y': str(2*max(abs(bbox.YMin), abs(bbox.YMax))), \
                                  # 'z': str(2*max(abs(bbox.ZMin), abs(bbox.ZMax))), \
                                  'lunit': 'mm'})
    return(name)


def quaternion2XYZ(rot):
    '''
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
    the gdml as R = Rz Ry Rx, i.e, Rx apllied lsat, not first, so now we have
  
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
    '''
    v = rot*Vector(0, 0, 1)
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
    ysolution = -math.sin(a)*math.cos(b)
    zsolution = math.cos(a)*math.cos(b)
    if v.y*ysolution < 0 or v.z*zsolution < 0:
        print('Trying second solution')
        b = math.pi - b
        if math.cos(b) > 0:
            a = math.atan2(-v.y, v.z)
        else:
            a = math.atan2(v.y, -v.z)
    # sanity check 2
    ysolution = -math.sin(a)*math.cos(b)
    zsolution = math.cos(a)*math.cos(b)
    if v.y*ysolution < 0 or v.z*zsolution < 0:
        print('Failed both solutions!')
        print(v.y, ysolution)
        print(v.z, zsolution)
    Ryinv = FreeCAD.Rotation(Vector(0, 1, 0), math.degrees(-b))
    Rxinv = FreeCAD.Rotation(Vector(1, 0, 0), math.degrees(-a))
    vp = Ryinv*Rxinv*rot*Vector(1, 0, 0)
    g = math.atan2(vp.y, vp.x)

    return [math.degrees(a), math.degrees(b), math.degrees(g)]


def createLVandPV(obj, name, solidName):
    #
    # Logical & Physical Volumes get added to structure section of gdml
    #
    # Need to update so that use export of Rotation & position
    # rather than this as well i.e one Place
    #
    global PVcount, POScount, ROTcount
    pvName = 'PV'+name+str(PVcount)
    PVcount += 1
    pos = obj.Placement.Base
    lvol = ET.SubElement(structure, 'volume', {'name': pvName})
    material = getMaterial(obj)
    ET.SubElement(lvol, 'materialref', {'ref': material})
    ET.SubElement(lvol, 'solidref', {'ref': solidName})
    # Place child physical volume in World Volume
    phys = ET.SubElement(lvol, 'physvol', {'name': 'PV-'+name})
    ET.SubElement(phys, 'volumeref', {'ref': pvName})
    x = pos[0]
    y = pos[1]
    z = pos[2]
    if x != 0 or y != 0 or z != 0:
        posName = 'Pos'+name+str(POScount)
        POScount += 1
        ET.SubElement(phys, 'positionref', {'name': posName})
        ET.SubElement(define, 'position', {'name': posName, 'unit': 'mm',
                                           'x': str(x), 'y': str(y), 'z': str(z)})
    rot = obj.Placement.Rotation
    angles = quaternion2XYZ(rot)
    a0 = angles[0]
    # print(a0)
    a1 = angles[1]
    # print(a1)
    a2 = angles[2]
    # print(a2)
    if a0 != 0 or a1 != 0 or a2 != 0:
        rotName = 'Rot'+name+str(ROTcount)
        ROTcount += 1
        ET.SubElement(phys, 'rotationref', {'name': rotName})
        ET.SubElement(define, 'rotation', {'name': rotName, 'unit': 'deg',
                                           'x': str(-a0), 'y': str(-a1), 'z': str(-a2)})


def createAdjustedLVandPV(obj, name, solidName, delta):
    # Allow for difference in placement between FreeCAD and GDML
    adjObj = obj
    rot = FreeCAD.Rotation(obj.Placement.Rotation)
    adjObj.Placement.move(rot.multVec(delta))  # .negative()
    createLVandPV(adjObj, name, solidName)


def reportObject(obj):

    GDMLShared.trace("Report Object")
    GDMLShared.trace(obj)
    GDMLShared.trace("Name : "+obj.Name)
    GDMLShared.trace("Type : "+obj.TypeId)
    if hasattr(obj, 'Placement'):
        print("Placement")
        print("Pos   : "+str(obj.Placement.Base))
        print("axis  : "+str(obj.Placement.Rotation.Axis))
        print("angle : "+str(obj.Placement.Rotation.Angle))

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
            print("Sphere Radius : "+str(obj.Radius))
            break

        if case("Part::Box"):
            print("cube : (" + str(obj.Length)+"," + str(obj.Width)+"," +
                  str(obj.Height) + ")")
            break

        if case("Part::Cylinder"):
            print("cylinder : Height " + str(obj.Height) +
                  " Radius "+str(obj.Radius))
            break

        if case("Part::Cone"):
            print("cone : Height "+str(obj.Height) +
                  " Radius1 "+str(obj.Radius1)+" Radius2 "+str(obj.Radius2))
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


def processPlanar(obj, shape, name):
    print('Polyhedron ????')
    global defineCnt
    #
    # print("Add tessellated Solid")
    tess = ET.SubElement(solids, 'tessellated', {'name': name})
    # print("Add Vertex positions")
    for f in shape.Faces:
        baseVrt = defineCnt
        for vrt in f.Vertexes:
            vnum = 'v'+str(defineCnt)
            ET.SubElement(define, 'position', {'name': vnum,
                                               'x': str(vrt.Point.x),
                                               'y': str(vrt.Point.y),
                                               'z': str(vrt.Point.z),
                                               'unit': 'mm'})
            defineCnt += 1
        # print("Add vertex to tessellated Solid")
        vrt1 = 'v'+str(baseVrt)
        vrt2 = 'v'+str(baseVrt+1)
        vrt3 = 'v'+str(baseVrt+2)
        vrt4 = 'v'+str(baseVrt+3)
        NumVrt = len(f.Vertexes)
        if NumVrt == 3:
            ET.SubElement(tess, 'triangular', {
               'vertex1': vrt1,
               'vertex2': vrt2,
               'vertex3': vrt3,
               'type': 'ABSOLUTE'})
        elif NumVrt == 4:
            ET.SubElement(tess, 'quadrangular', {
               'vertex1': vrt1,
               'vertex2': vrt2,
               'vertex3': vrt3,
               'vertex4': vrt4,
               'type': 'ABSOLUTE'})


def checkShapeAllPlanar(Shape):
    for f in Shape.Faces:
        if f.Surface.isPlanar() is False:
            return False
    return True


#    Add XML for TessellateSolid
def mesh2Tessellate(mesh, name):
    global defineCnt

    baseVrt = defineCnt
    # print ("mesh")
    # print (mesh)
    # print ("Facets")
    # print (mesh.Facets)
    # print ("mesh topology")
    # print (dir(mesh.Topology))
    # print (mesh.Topology)
    #
    #    mesh.Topology[0] = points
    #    mesh.Topology[1] = faces
    #
    #    First setup vertex in define section vetexs (points)
    # print("Add Vertex positions")
    for fc_points in mesh.Topology[0]:
        # print(fc_points)
        v = 'v'+str(defineCnt)
        ET.SubElement(define, 'position', {'name': v,
                                           'x': str(fc_points[0]),
                                           'y': str(fc_points[1]),
                                           'z': str(fc_points[2]),
                                           'unit': 'mm'})
        defineCnt += 1
    #
    #     Add faces
    #
    # print("Add Triangular vertex")
    tess = ET.SubElement(solids, 'tessellated', {'name': name})
    for fc_facet in mesh.Topology[1]:
        # print(fc_facet)
        vrt1 = 'v'+str(baseVrt+fc_facet[0])
        vrt2 = 'v'+str(baseVrt+fc_facet[1])
        vrt3 = 'v'+str(baseVrt+fc_facet[2])
        ET.SubElement(tess, 'triangular', {
           'vertex1': vrt1, 'vertex2': vrt2,
           'vertex3': vrt3, 'type': 'ABSOLUTE'})


def processMesh(obj, Mesh, Name):
    #  obj needed for Volune names
    #  object maynot have Mesh as part of Obj
    #  Name - allows control over name
    print("Create Tessellate Logical Volume")
    createLVandPV(obj, Name, 'Tessellated')
    mesh2Tessellate(Mesh, Name)
    return(Name)


def shape2Mesh(shape):
    import MeshPart
    return (MeshPart.meshFromShape(Shape=shape, Deflection=0.0))
#            Deflection= params.GetFloat('meshdeflection',0.0))


def processObjectShape(obj):
    # Check if Planar
    # If plannar create Tessellated Solid with 3 & 4 vertex as appropriate
    # If not planar create a mesh and the a Tessellated Solid with 3 vertex
    # print("Process Object Shape")
    # print(obj)
    # print(obj.PropertiesList)
    if not hasattr(obj, 'Shape'):
        return
    shape = obj.Shape
    # print (shape)
    # print(shape.ShapeType)
    while switch(shape.ShapeType):
        if case("Mesh::Feature"):
            print("Mesh - Should not occur should have been handled")
            # print("Mesh")
            # tessellate = mesh2Tessellate(mesh)
            # return(tessellate)
            # break

            print("ShapeType Not handled")
            print(shape.ShapeType)
            break

#   Dropped through to here
#   Need to check has Shape

    # print('Check if All planar')
    planar = checkShapeAllPlanar(shape)
    # print(planar)

    if planar:
        return(processPlanar(obj, shape, obj.Name))

    else:
        # Create Mesh from shape & then Process Mesh
        # to create Tessellated Solid in Geant4
        return(processMesh(obj, shape2Mesh(shape), obj.Name))


def processSection(obj):
    # print("Process Section")
    ET.SubElement(solids, 'section', {
       'vertex1': obj.v1,
       'vertex2': obj.v2,
       'vertex3': obj.v3, 'vertex4': obj.v4,
       'type': obj.vtype})


def addPhysVol(xmlVol, volName):
    GDMLShared.trace("Add PhysVol to Vol : " + volName)
    # print(ET.tostring(xmlVol))
    pvol = ET.SubElement(xmlVol, 'physvol', {'name': 'PV-'+volName})
    ET.SubElement(pvol, 'volumeref', {'ref': volName})
    return pvol


def cleanVolName(obj, volName):
    # Get proper Volume Name
    # print('clean name : '+volName)
    if hasattr(obj, 'Copynumber'):
        # print('Has copynumber')
        i = len(volName)
        if '_' in volName and i > 2:
            volName = volName[:-2]
    # print('returning name : '+volName)
    return volName


def addPhysVolPlacement(obj, xmlVol, volName, placement, refName=None):
    # obj: App:Part to be placed.
    # xmlVol: the xml that the <physvol is a subelement of.
    # It may be a <volume, or an <assembly
    # volName = volref: the name of the volume being placed
    # placement: the placement of the <physvol
    # For most situations, the placement (pos, rot) should be that
    # of the obj (obj.Placement.Base, obj.Placement.Rotation), but
    # if the user specifies a placement for the solid, then the palcement
    # has to be a product of both placements. Here we don't try to figure
    # that out, so we demand the placement be given explicitly

    # returns xml of of reated <physvol element

    # Get proper Volume Name
    # I am commenting this out I don't know why it's needed.
    # the <volume or <assembly name is ceated withoutout any cleanup,m so the
    # reference to it musl also not have any cleanup
    if refName is None:
        refName = cleanVolName(obj, volName)
    # GDMLShared.setTrace(True)
    GDMLShared.trace("Add PhysVol to Vol : "+volName)
    # print(ET.tostring(xmlVol))
    if xmlVol is not None:
        if not hasattr(obj, 'CopyNumber'):
            pvol = ET.SubElement(xmlVol, 'physvol', {'name': 'PV-' + volName})
        else:
            cpyNum = str(obj.CopyNumber)
            GDMLShared.trace('CopyNumber : '+cpyNum)
            pvol = ET.SubElement(xmlVol, 'physvol', {'copynumber': cpyNum})

        ET.SubElement(pvol, 'volumeref', {'ref': refName})
        processPlacement(volName, pvol, placement)
        if hasattr(obj, 'GDMLscale'):
            scaleName = volName+'scl'
            ET.SubElement(pvol, 'scale', {'name': scaleName,
                                          'x': str(obj.GDMLscale[0]),
                                          'y': str(obj.GDMLscale[1]),
                                          'z': str(obj.GDMLscale[2])})

        return pvol


def exportPosition(name, xml, pos):
    global POScount
    global centerDefined
    GDMLShared.trace('export Position')
    GDMLShared.trace(pos)
    x = pos[0]
    y = pos[1]
    z = pos[2]
    if x == 0 and y == 0 and z == 0:
        if not centerDefined:
            centerDefined = True
            ET.SubElement(define, 'position', {'name': 'center',
                                               'x': '0', 'y': '0', 'z': '0',
                                               'unit': 'mm'})
        ET.SubElement(xml, 'positionref', {'ref': 'center'})

    else:
        posName = 'P-' + name + str(POScount)
        POScount += 1
        posxml = ET.SubElement(define, 'position', {'name': posName,
                                                    'unit': 'mm'})
        if x != 0:
            posxml.attrib['x'] = str(x)
        if y != 0:
            posxml.attrib['y'] = str(y)
        if z != 0:
            posxml.attrib['z'] = str(z)
        ET.SubElement(xml, 'positionref', {'ref': posName})


def exportRotation(name, xml, rot):
    print('Export Rotation')
    global ROTcount
    global identityDefined
    if rot.Angle == 0:
        if not identityDefined:
            identityDefined = True
            ET.SubElement(define, 'rotation', {'name': 'identity',
                                               'x': '0', 'y': '0', 'z': '0'})
        ET.SubElement(xml, 'rotationref', {'ref': 'identity'})

    else:
        angles = quaternion2XYZ(rot)
        a0 = angles[0]
        a1 = angles[1]
        a2 = angles[2]
        if a0 != 0 or a1 != 0 or a2 != 0:
            rotName = 'R-'+name+str(ROTcount)
            ROTcount += 1
            rotxml = ET.SubElement(define, 'rotation', {'name': rotName,
                                                        'unit': 'deg'})
            if abs(a0) != 0:
                rotxml.attrib['x'] = str(-a0)
            if abs(a1) != 0:
                rotxml.attrib['y'] = str(-a1)
            if abs(a2) != 0:
                rotxml.attrib['z'] = str(-a2)
            ET.SubElement(xml, 'rotationref', {'ref': rotName})


def exportScaling(name, xml, scl):
    global SCLcount
    global centerDefined
    GDMLShared.trace('export Scaling')
    GDMLShared.trace(scl)
    x = scl[0]
    y = scl[1]
    z = scl[2]
    sclName = 'S-' + name + str(SCLcount)
    SCLcount += 1
    ET.SubElement(define, 'scale', {'name': sclName,
                                    'x': str(x),
                                    'y': str(y),
                                    'z': str(z)})
    ET.SubElement(xml, 'scaleref', {'ref': sclName})


def processPlacement(name, xml, placement):
    exportPosition(name, xml, placement.Base)
    exportRotation(name, xml, placement.Rotation)


def processPosition(obj, solid):
    if obj.Placement.Base == FreeCAD.Vector(0, 0, 0):
        return
    GDMLShared.trace("Define position & references to Solid")
    exportPosition(obj.Name, solid, obj.Placement.Base)


def processRotation(obj, solid):
    if obj.Placement.Rotation.Angle == 0:
        return
    GDMLShared.trace('Deal with Rotation')
    exportRotation(obj.Name, solid, obj.Placement.Rotation)


def testDefaultPlacement(obj):
    # print(dir(obj.Placement.Rotation))
    # print('Test Default Placement : '+obj.Name)
    # print(obj.Placement.Base)
    # print(obj.Placement.Rotation.Angle)
    if obj.Placement.Base == FreeCAD.Vector(0, 0, 0) and \
       obj.Placement.Rotation.Angle == 0:
        return True
    else:
        return False


def testAddPhysVol(obj, xmlParent, volName):
    if testDefaultPlacement(obj) is False:
        if xmlParent is not None:
            pvol = addPhysVol(xmlParent, volName)
            processPlacement(obj, pvol)
        else:
            print('Root/World Volume')


def addVolRef(volxml, volName, obj, solidName=None, addColor=True):
    # Pass material as Boolean
    material = getMaterial(obj)
    if solidName is None:
        solidName = nameOfGDMLobject(obj)
    ET.SubElement(volxml, 'materialref', {'ref': material})
    ET.SubElement(volxml, 'solidref', {'ref': solidName})

    ET.SubElement(gxml, 'volume', {'name': volName, 'material': material})

    if addColor is True and hasattr(obj.ViewObject, 'ShapeColor') and volName != WorldVOL:
        colour = obj.ViewObject.ShapeColor
        colStr = '#'+''.join('{:02x}'.format(round(v*255)) for v in colour)
        ET.SubElement(volxml, 'auxiliary', {'auxtype': 'Color',
                                            'auxvalue': colStr})
    # print(ET.tostring(volxml))


def nameOfGDMLobject(obj):
    name = obj.Label
    if len(name) > 4:
        if name[0:4] == 'GDML':
            if '_' in name:
                return(name.split('_', 1)[1])
    return name


def processIsotope(obj, item):  # maybe part of material or element (common code)
    if hasattr(obj, 'Z'):
        # print(dir(obj))
        item.set('Z', str(obj.Z))

    if hasattr(obj, 'N'):
        # print(dir(obj))
        item.set('N', str(obj.N))

    if hasattr(obj, 'formula'):
        # print(dir(obj))
        item.set('formula', str(obj.formula))

    if hasattr(obj, 'unit') or hasattr(obj, 'atom_value') or \
       hasattr(obj, 'value'):
        atom = ET.SubElement(item, 'atom')

        if hasattr(obj, 'unit'):
            atom.set('unit', str(obj.unit))

        if hasattr(obj, 'type'):
            atom.set('unit', str(obj.type))

        if hasattr(obj, 'atom_value'):
            atom.set('value', str(obj.atom_value))

        if hasattr(obj, 'value'):
            atom.set('value', str(obj.value))


def processMaterials():
    print("\nProcess Materials")
    global materials

    for GName in ['Constants', 'Variables',
                  'Isotopes', 'Elements', 'Materials']:
        Grp = FreeCAD.ActiveDocument.getObject(GName)
        if Grp is not None:
            # print(Grp.TypeId+" : "+Grp.Name)
            print(Grp.Label)
            if processGroup(Grp) is False:
                break


def processFractionsComposites(obj, item):
    # Fractions are used in Material and Elements
    if isinstance(obj.Proxy, GDMLfraction):
        # print("GDML fraction :" + obj.Label)
        # need to strip number making it unique
        ET.SubElement(item, 'fraction', {'n': str(obj.n),
                                         'ref': nameFromLabel(obj.Label)})

    if isinstance(obj.Proxy, GDMLcomposite):
        # print("GDML Composite")
        ET.SubElement(item, 'composite', {'n': str(obj.n),
                                          'ref': nameFromLabel(obj.Label)})


def createMaterials(group):
    global materials
    for obj in group:
        if obj.Label != 'Geant4':
            item = ET.SubElement(materials, 'material', {
               'name':
               nameFromLabel(obj.Label)})

            # Dunit & Dvalue must be first for Geant4
            if hasattr(obj, 'Dunit') or hasattr(obj, 'Dvalue'):
                # print("Dunit or DValue")
                D = ET.SubElement(item, 'D')
                if hasattr(obj, 'Dunit'):
                    D.set('unit', str(obj.Dunit))

                if hasattr(obj, 'Dvalue'):
                    D.set('value', str(obj.Dvalue))

                if hasattr(obj, 'Tunit') and hasattr(obj, 'Tvalue'):
                    ET.SubElement(item, 'T', {'unit': obj.Tunit,
                                              'value': str(obj.Tvalue)})

                if hasattr(obj, 'MEEunit'):
                    ET.SubElement(item, 'MEE', {'unit': obj.MEEunit,
                                                'value': str(obj.MEEvalue)})
            # process common options material / element
            processIsotope(obj, item)
            if len(obj.Group) > 0:
                for o in obj.Group:
                    processFractionsComposites(o, item)


def createElements(group):
    global materials
    for obj in group:
        # print(f'Element : {obj.Label}')
        item = ET.SubElement(materials, 'element', {
           'name': nameFromLabel(obj.Label)})
        # Common code IsoTope and Elements1
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

            ET.SubElement(define, 'constant', {'name': obj.Label,
                                               'value': obj.value})


def createVariables(group):
    global define
    for obj in group:
        if isinstance(obj.Proxy, GDMLvariable):
            # print("GDML variable")
            # print(dir(obj))

            ET.SubElement(define, 'variable', {'name': obj.Label,
                                               'value': obj.value})


def createQuantities(group):
    global define
    for obj in group:
        if isinstance(obj.Proxy, GDMLquantity):
            # print("GDML quantity")
            # print(dir(obj))

            ET.SubElement(define, 'quantity', {'name': obj.Label,
                                               'type': obj.type,
                                               'unit': obj.unit,
                                               'value': obj.value})


def createIsotopes(group):
    global materials
    for obj in group:
        if isinstance(obj.Proxy, GDMLisotope):
            # print("GDML isotope")
            # item = ET.SubElement(materials,'isotope',{'N': str(obj.N), \
            #                                           'Z': str(obj.Z), \
            #                                           'name' : obj.Label})
            # ET.SubElement(item,'atom',{'unit': obj.unit, \
            #                           'value': str(obj.value)})
            item = ET.SubElement(materials, 'isotope', {'name': obj.Label})
            processIsotope(obj, item)


def processGroup(obj):
    print('Process Group '+obj.Label)
    # print(obj.TypeId)
    # print(obj.Group)
    #      if hasattr(obj,'Group') :
    # return
    if hasattr(obj, 'Group'):
        # print("   Object List : "+obj.Label)
        # print(obj)
        while switch(obj.Name):
            if case("Constants"):
                # print("Constants")
                createConstants(obj.Group)
                break

            if case("Variables"):
                # print("Variables")
                createVariables(obj.Group)
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


def getXmlVolume(volObj):
    global structure
    if volObj is None:
        return None
    xmlvol = structure.find("volume[@name='%s']" % volObj.Label)
    if xmlvol is None:
        print(volObj.Label+' Not Found')
    return xmlvol


def getDefaultMaterial():
    # should get this from GDML settings under "settings"
    # for now this does not exist, so simply put steel
    return 'G4_STAINLESS-STEEL'


def getBooleanCount(obj):
    GDMLShared.trace('get Count : ' + obj.Name)
    if hasattr(obj, 'Tool'):
        GDMLShared.trace('Has tool - check Base')
        baseCnt = getBooleanCount(obj.Base)
        toolCnt = getBooleanCount(obj.Tool)
        GDMLShared.trace('Count is : ' + str(baseCnt + toolCnt))
        return (baseCnt + toolCnt)
    else:
        return 0


def getMaterial(obj):
    # Temporary fix until the SetMaterials works
    # Somehow (now Feb 20) if a new gdml object is added
    # the defalut material is Geant4, and SetMaterials fails to change it
    from .GDMLMaterials import getMaterialsList
    GDMLShared.trace('get Material : '+obj.Label)
    print(f'get Material : {obj.Label}')
    if hasattr(obj, 'material'):
        material = obj.material
        return material
    elif hasattr(obj, 'Tool'):
        GDMLShared.trace('Has tool - check Base')
        material = getMaterial(obj.Base)
        return material
    elif hasattr(obj, 'Base'):
        GDMLShared.trace('Has Base - check Base')
        material = getMaterial(obj.Base)
        return material
    elif hasattr(obj, 'Objects'):
        GDMLShared.trace('Has Objects - check Objects')
        material = getMaterial(obj.Objects[0])
        return material
    else:
        return getDefaultMaterial()


'''
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
'''


def exportCone(name, radius, height):
    cylEl = ET.SubElement(solids, 'cone', {'name': name,
                                           'rmin1': '0',
                                           'rmax1': str(radius),
                                           'rmin2': '0',
                                           'rmax2': str(radius),
                                           'z': str(height),
                                           'startphi': '0',
                                           'deltaphi': '360',
                                           'aunit': 'deg', 'lunit': 'mm'})
    return cylEl


def insertXMLvolume(name):
    # Insert at beginning for sub volumes
    GDMLShared.trace('insert xml volume : ' + name)
    elem = ET.Element('volume', {'name': name})
    global structure
    structure.insert(0, elem)
    return elem


def insertXMLvolObj(obj):
    # name = cleanVolName(obj, obj.Label)
    name = obj.Label
    return insertXMLvolume(name)


def insertXMLassembly(name):
    # Insert at beginning for sub volumes
    GDMLShared.trace('insert xml assembly : ' + name)
    elem = ET.Element('assembly', {'name': name})
    global structure
    structure.insert(0, elem)
    return elem


def insertXMLassemObj(obj):
    # name = cleanVolName(obj, obj.Label)
    name = obj.Label
    return insertXMLassembly(name)


def createXMLvol(name):
    return ET.SubElement(structure, 'volume', {'name': name})


def processAssembly(vol, xmlVol, xmlParent, parentName):
    # vol - Volume Object
    # xmlVol - xml of this assembly
    # xmlParent - xml of this volumes Paretnt
    # App::Part will have Booleans & Multifuse objects also in the list
    # So for s in list is not so good
    # type 1 straight GDML type = 2 for GEMC
    # xmlVol could be created dummy volume
    GDMLShared.setTrace(True)
    volName = vol.Label
    # volName = cleanVolName(vol, vol.Label)
    GDMLShared.trace('Process Assembly : '+volName)
    # if GDMLShared.getTrace() == True :
    #   printVolumeInfo(vol, xmlVol, xmlParent, parentName)
    assemObjs = assemblyHeads(vol)
    print(f'processAssembly: vol.TypeId {vol.TypeId}')
    for obj in assemObjs:
        if obj.TypeId == 'App::Part':
            processVolAssem(obj, xmlVol, volName)
        elif obj.TypeId == 'App::Link':
            print('Process Link')
            # objName = cleanVolName(obj, obj.Label)
            addPhysVolPlacement(obj, xmlVol, volName,
                                obj.Placement, refName=obj.VolRef)
        else:
            _ = processVolume(obj, xmlVol)

    addPhysVolPlacement(vol, xmlParent, volName, vol.Placement)


def processVolume(vol, xmlParent, volName=None):

    # vol - Volume Object
    # xmlParent - xml of this volumes Paretnt
    # App::Part will have Booleans & Multifuse objects also in the list
    # So for s in list is not so good
    # type 1 straight GDML type = 2 for GEMC
    # xmlVol could be created dummy volume
    if vol.TypeId == 'App::Link':
        print('Volume is Link')
        # objName = cleanVolName(obj, obj.Label)
        addPhysVolPlacement(vol, xmlParent, vol.Label,
                            vol.Placement, refName=vol.VolRef)
        return

    if volName is None:
        volName = vol.Label
    if vol.TypeId == 'App::Part':
        topObject = topObj(vol)
    else:
        topObject = vol
    if topObject is None:
        return

    if isMultiPlacement(topObject):
        xmlVol, volName = processMultiPlacement(topObject, xmlParent)
        partPlacement = topObject.Placement

    else:
        solidExporter = SolidExporter.getExporter(topObject)
        if solidExporter is None:
            return
        solidExporter.export()
        print(f'solids count {len(list(solids))}')
        # 1- adds a <volume element to <structure with name volName
        if volName == solidExporter.name():
            volName = 'V-'+solidExporter.name()
        xmlVol = insertXMLvolume(volName)
        # 2- add material info to the generated <volume pointerd to by xmlVol
        addVolRef(xmlVol, volName, topObject, solidExporter.name())
        # 3- add a <physvol. A <physvol, can go under the <worlVol, or under
        #    a <assembly
        # first we need to convolve the solids placement, with the vols placement
        partPlacement = solidExporter.placement()
        if vol.TypeId == 'App::Part':
            partPlacement = vol.Placement*partPlacement

    addPhysVolPlacement(vol, xmlParent, volName, partPlacement)
    if hasattr(vol, 'SensDet'):
        if vol.SensDet is not None:
            print('Volume : ' + volName)
            print('SensDet : ' + vol.SensDet)
            ET.SubElement(xmlVol, 'auxiliary', {'auxtype': 'SensDet',
                                                'auxvalue': vol.SensDet})
    print(f'Processed Volume : {volName}')

    return xmlVol


def processContainer(vol, xmlParent):
    volName = vol.Label
    objects = assemblyHeads(vol)
    newXmlVol = insertXMLvolume(volName)
    solidExporter = SolidExporter.getExporter(objects[0])
    solidExporter.export()
    addVolRef(newXmlVol, volName, objects[0], solidExporter.name(), addColor=False)
    addPhysVolPlacement(vol, xmlParent, volName, vol.Placement)
    for obj in objects[1:]:
        if obj.TypeId == 'App::Part':
            processVolAssem(obj, newXmlVol, volName)
        elif obj.TypeId == 'App::Link':
            print('Process Link')
            # objName = cleanVolName(obj, obj.Label)
            addPhysVolPlacement(obj, newXmlVol, obj.Label,
                                obj.Placement, refName=obj.VolRef)
        else:
            _ = processVolume(obj, newXmlVol)


def processVolAssem(vol, xmlParent, parentName):
    # vol - Volume Object
    # xmlVol - xml of this volume
    # xmlParent - xml of this volumes Paretnt
    # xmlVol could be created dummy volume
    if vol.Label[:12] != 'NOT_Expanded':
        print('process volasm '+vol.Label)
        volName = vol.Label
        if isContainer(vol):
            processContainer(vol, xmlParent)
        elif isAssembly(vol):
            newXmlVol = insertXMLassembly(volName)
            processAssembly(vol, newXmlVol, xmlParent, parentName)
        else:
            processVolume(vol, xmlParent)
    else:
        print('skipping '+vol.Label)


def printVolumeInfo(vol, xmlVol, xmlParent, parentName):
    if xmlVol is not None:
        xmlstr = ET.tostring(xmlVol)
    else:
        xmlstr = 'None'
    print(xmlstr)
    GDMLShared.trace('     '+vol.Label + ' - ' + str(xmlstr))
    if xmlParent is not None:
        xmlstr = ET.tostring(xmlParent)
    else:
        xmlstr = 'None'
    GDMLShared.trace('     Parent : ' + str(parentName) + ' : ' + str(xmlstr))


def processMultiPlacement(obj, xmlParent):

    print(f'procesMultiPlacement {obj.Label}')

    def getChildren(obj):
        children = []
        for o in obj.OutList:
            if o.TypeId != 'App::Origin':
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
            volName = 'LV-'+solidName
            volXML = insertXMLvolume(volName)
            addVolRef(volXML, obj.Label, s, solidName)
            addPhysVolPlacement(s, xmlParent, volName, exporter.placement())
            break
    placers = children[:i]  # placers without the solids
    j = len(placers)
    for pl in reversed(placers):
        j -= 1
        placer = MultiPlacer.getPlacer(pl)
        placer.place(volName)
        volName = placer.name()
        volXML = placer.xml()
        if j != 0:
            addPhysVolPlacement(pl, xmlParent, volName, pl.Placement)

    return volXML, volName  # name of last placer (an assembly)


def createWorldVol(volName):
    print("Need to create Dummy Volume and World Box ")
    bbox = FreeCAD.BoundBox()
    boxName = defineWorldBox(bbox)
    worldVol = ET.SubElement(structure, 'volume', {'name': volName})
    ET.SubElement(worldVol, 'materialref', {'ref': 'G4_AIR'})
    ET.SubElement(worldVol, 'solidref', {'ref': boxName})
    ET.SubElement(gxml, 'volume', {'name': volName, 'material': 'G4_AIR'})
    return worldVol


def isContainer(obj):
    # return True if The App::Part is of the form:
    # App::Part
    #     -solid (Part:xxx)
    #     -App::Part
    #     -App::Part
    #     ....
    # So a container satisfies the current isAssembly requirements
    # plus the siblings must have the above form
    # obj that satisfy is container get exported as
    # <volume ....>
    #   <solidref = first solid
    #   <physvol ..ref to first App::Part>
    #   <physvol ..ref to first App::Part>
    # </volume>
    #
    # This is in contract to assembly, which is exported as
    # <assembly
    #   <physvol 1>
    #   <physvol 2>
    #   ....
    #
    # Must be assembly first
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

    # rest must not be solids, but only second is tested here
    if SolidExporter.isSolid(heads[1]):
        return False

    return True


def isAssembly(obj):
    # return True if obj is an assembly
    # to be an assembly the obj must be:
    # (1) and App::Part or an App::Link and
    # (2) it has either (1) At least one App::Part as a subpart or
    #                   (2) more than one "terminal" object
    # A terminal object is one that has associated with it ONE volume
    # A volume refers to ONE solid
    # A terminal item CAN be a boolean, or an extrusion (and in the future
    # a chamfer or a fillet. So a terminal element need NOT have an empty
    # OutList
    # N.B. App::Link is treated as a non-assembly, eventhough it might be linked
    # to an assembly, because all we need to place it is the volref of its link

    subObjs = []
    if obj.TypeId != 'App::Part':
        return False
    for ob in obj.OutList:
        if ob.TypeId == 'App::Part' or ob.TypeId == 'App::Link':
            return True  # Yes, even if ONE App::Part is under this, we treat it as an assembly
        else:
            if ob.TypeId != 'App::Origin':
                subObjs.append(ob)

    # now remove any OutList objects from the subObjs
    for subObj in subObjs[:]:  # the slice is a COPY of the list, not the list itself
        if hasattr(subObj, 'OutList'):
            for o in subObj.OutList:
                if o in subObjs:
                    subObjs.remove(o)

    if len(subObjs) > 1:
        return True
    else:
        return False


def assemblyHeads(obj):
    # return a list of subassembly heads for this object
    # Subassembly heads are themselves either assemblies
    # or terminal objects (those that produce a <volume and <physvol)
    assemblyHeads = []
    if isAssembly(obj):
        for ob in obj.OutList:
            if ob.Label[:12] != 'NOT_Expanded':
                if ob.TypeId == 'App::Part':
                    print(f'adding {ob.Label}')
                    assemblyHeads.append(ob)
                elif ob.TypeId == 'App::Link':
                    if ob.LinkedObject.Label[:12] != 'NOT_Expanded':
                        print(f'adding {ob.Label}')
                        assemblyHeads.append(ob)
                else:
                    if ob.TypeId != 'App::Origin':
                        print(f'T2 adding {ob.Label}')
                        assemblyHeads.append(ob)

        # now remove any OutList objects from from the subObjs
        for subObj in assemblyHeads[:]:  # the slice is a COPY of the list, not the list itself
            if hasattr(subObj, 'OutList'):
                # App:Links has the object they are linked to in their OutList
                # We do not want to remove the link!
                if subObj.TypeId == 'App::Link':
                    print(f'skipping {subObj.Label}')
                    continue
                for o in subObj.OutList:
                    if o in assemblyHeads:
                        print(f'removing {ob.Label}')
                        assemblyHeads.remove(o)

    return assemblyHeads


def topObj(obj):
    # The topmost object in an App::Part
    # The App::Part is assumed NOT to be an assembly
    if isAssembly(obj):
        print(f'***** Non Assembly expected  for {obj.Label}')
        return

    if not hasattr(obj, 'OutList'):
        return obj

    if len(obj.OutList) == 0:
        return obj

    sublist = []
    for ob in obj.OutList:
        if ob.TypeId != 'App::Origin':
            sublist.append(ob)

    for subObj in sublist[:]:
        if hasattr(subObj, 'OutList'):
            for o in subObj.OutList:
                if o in sublist:
                    sublist.remove(o)

    if len(sublist) > 1:
        print(f'Found more than one top object in {obj.Label}. \n Returning first only')
    elif len(sublist) == 0:
        return None

    return sublist[0]


def isMultiPlacement(obj):
    return obj.TypeId == 'Part::Mirroring'


def countGDMLObj(objList):
    # Return counts GDML objects exportables
    # #rint('countGDMLObj')
    GDMLShared.trace('countGDMLObj')
    gcount = 0
    # print(range(len(objList)))
    for idx in range(len(objList)):
        # print('idx : '+str(idx))
        obj = objList[idx]
        if obj.TypeId == 'Part::FeaturePython':
            gcount += 1
        if obj.TypeId == 'Part::Cut' \
           or obj.TypeId == 'Part::Fuse' \
           or obj.TypeId == 'Part::Common':
            gcount -= 1
    # print('countGDMLObj - Count : '+str(gcount))
    GDMLShared.trace('countGDMLObj - gdml : ' + str(gcount))
    return gcount


def checkGDMLstructure(objList):
    # Should be
    # World Vol - App::Part
    # App::Origin
    # GDML Object
    GDMLShared.trace('check GDML structure')
    GDMLShared.trace(objList)
    # print(objList)
    cnt = countGDMLObj(objList)
    if cnt > 1:  # More than one GDML Object need to insert Dummy
        return False
    if cnt == 1 and len(objList) == 2:  # Just a single GDML obj insert Dummy
        return False
    return True


def locateXMLvol(vol):
    global structure
    xmlVol = structure.find("volume[@name='%s']" % vol.Label)
    return xmlVol


def exportWorldVol(vol, fileExt):

    global WorldVOL
    WorldVOL = vol.Label
    if fileExt != '.xml':
        print('Export World Process Volume : ' + vol.Label)
        GDMLShared.trace('Export Word Process Volume' + vol.Label)
        ET.SubElement(setup, 'world', {'ref': vol.Label})

        if checkGDMLstructure(vol.OutList) is False:
            GDMLShared.trace('Insert Dummy Volume')
            createXMLvol('dummy')
            xmlParent = createWorldVol(vol.Label)
            parentName = vol.Label
            addPhysVol(xmlParent, 'dummy')
        else:
            GDMLShared.trace('Valid Structure')
            xmlParent = None
            parentName = None
    else:
        xmlParent = None
        parentName = None

    if hasattr(vol, 'OutList'):
        # print(vol.OutList)
        cnt = countGDMLObj(vol.OutList)
    print('Root GDML Count ' + str(cnt))

    if cnt > 0:  # one GDML defining world volume
        if isAssembly(vol):
            heads = assemblyHeads(vol)
            worlSolid = heads[0]
            xmlVol = processVolume(worlSolid, xmlParent, volName=WorldVOL)
            for obj in heads[1:]:  # skip first volume (done above)
                processVolAssem(obj, xmlVol, WorldVOL)
        else:
            xmlVol = processVolume(vol, xmlParent)
    else:  # no volume defining world
        xmlVol = insertXMLassembly(vol.Label)
        processAssembly(vol, xmlVol, xmlParent, parentName)


def exportElementAsXML(dirPath, fileName, flag, elemName, elem):
    # gdml is a global
    global gdml, docString, importStr
    if elem is not None:
        # xmlElem = ET.Element('xml')
        # xmlElem.append(elem)
        # indent(xmlElem)
        if flag is True:
            filename = fileName+'-' + elemName + '.xml'
        else:
            filename = elemName + '.xml'
        # ET.ElementTree(xmlElem).write(os.path.join(dirPath,filename))
        ET.ElementTree(elem).write(os.path.join(dirPath, filename))
        docString += '<!ENTITY ' + elemName + ' SYSTEM "' + filename+'">\n'
        gdml.append(ET.Entity(elemName))


def exportGDMLstructure(dirPath, fileName):
    global gdml, docString, importStr
    print("Write GDML structure to Directory")
    gdml = initGDML()
    docString = '\n<!DOCTYPE gdml [\n'
    # exportElementAsXML(dirPath, fileName, False, 'constants',constants)
    exportElementAsXML(dirPath, fileName, False, 'define', define)
    exportElementAsXML(dirPath, fileName, False, 'materials', materials)
    exportElementAsXML(dirPath, fileName, True, 'solids', solids)
    exportElementAsXML(dirPath, fileName, True, 'structure', structure)
    exportElementAsXML(dirPath, fileName, False, 'setup', setup)
    print(f"setup : {setup}")
    docString += ']>\n'
    # print(docString)
    # print(len(docString))
    # gdml = ET.fromstring(docString.encode("UTF-8"))
    indent(gdml)
    ET.ElementTree(gdml).write(os.path.join(dirPath, fileName+'.gdml'),
                               doctype=docString.encode('UTF-8'))
    print("GDML file structure written")


def exportGDML(first, filepath, fileExt):
    from . import GDMLShared
    from sys import platform
    global zOrder

    # GDMLShared.setTrace(True)
    GDMLShared.trace('exportGDML')
    print("====> Start GDML Export 1.6")
    print('File extension : '+fileExt)

    GDMLstructure()
    zOrder = 1
    processMaterials()
    exportWorldVol(first, fileExt)
    # format & write GDML file
    # xmlstr = ET.tostring(structure)
    # print('Structure : '+str(xmlstr))
    if fileExt == '.gdml':
        # indent(gdml)
        print(len(list(solids)))
        print("Write to gdml file")
        # ET.ElementTree(gdml).write(filepath, 'utf-8', True)
        # ET.ElementTree(gdml).write(filepath, xml_declaration=True)
        # Problem with pretty Print on Windows ?
        if platform == "win32":
            indent(gdml)
            ET.ElementTree(gdml).write(filepath, xml_declaration=True)
        else:
            ET.ElementTree(gdml).write(filepath, pretty_print=True,
                                   xml_declaration=True)
        print("GDML file written")

    if fileExt == '.GDML':
        filePath = os.path.split(filepath)
        print('Input File Path : '+filepath)
        fileName = os.path.splitext(filePath[1])[0]
        print('File Name : '+fileName)
        dirPath = os.path.join(filePath[0], fileName)
        print('Directory Path : '+dirPath)
        if os.path.exists(dirPath) is False:
            if os.path.isdir(dirPath) is False:
                os.makedirs(dirPath)
        if os.path.isdir(dirPath) is True:
            exportGDMLstructure(dirPath, fileName)
        else:
            print('Invalid Path')
            # change to Qt Warning

    if fileExt == '.xml':
        xmlElem = ET.Element('xml')
        xmlElem.append(solids)
        xmlElem.append(structure)
        indent(xmlElem)
        ET.ElementTree(xmlElem).write(filepath)
        print("XML file written")


def exportGDMLworld(first, filepath, fileExt):
    if filepath.lower().endswith('.gdml'):
        # GDML Export
        print('GDML Export')
        # if hasattr(first,'InList') :
        #   print(len(first.InList))

        if hasattr(first, 'OutList'):
            cnt = countGDMLObj(first.OutList)
            GDMLShared.trace('Count : ' + str(cnt))
            if cnt > 1:
                from .GDMLQtDialogs import showInvalidWorldVol
                showInvalidWorldVol()
            else:
                exportGDML(first, filepath, fileExt)


def hexInt(f):
    return hex(int(f*255))[2:].zfill(2)


def formatPosition(pos):
    s = str(pos[0]) + '*mm ' + str(pos[1]) + '*mm ' +str(pos[2]) + '*mm'
    print(s)
    return s


def scanForStl(first, gxml, path, flag):

    from .GDMLColourMap import lookupColour

    # if flag == True ignore Parts that convert
    print('scanForStl')
    print(first.Name+' : '+first.Label+' : '+first.TypeId)
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
    if hasattr(first, 'Tool'):
        print(first.TypeId)
        scanForStl(first.Base, gxml, path, flag)
        scanForStl(first.Tool, gxml, path, flag)

    if hasattr(first, 'OutList'):
        for obj in first.OutList:
            scanForStl(obj, gxml, path, flag)

    if first.TypeId != 'App::Part':
        if hasattr(first, 'Shape'):
            print('Write out stl')
            print('===> Name : '+first.Name+' Label : '+first.Label+' \
            Type :'+first.TypeId+' : '+str(hasattr(first, 'Shape')))
            newpath = os.path.join(path, first.Label + '.stl')
            print('Exporting : ' + newpath)
            first.Shape.exportStl(newpath)
            # Set Defaults
            colHex = 'ff0000'
            mat = 'G4Si'
            if hasattr(first.ViewObject, 'ShapeColor'):
                # print(dir(first))
                col = first.ViewObject.ShapeColor
                colHex = hexInt(col[0]) + hexInt(col[1]) + hexInt(col[2])
                print('===> Colour '+str(col) + ' '+colHex)
                mat = lookupColour(col)
                print('Material : '+mat)
                if hasattr(first, 'Placement'):
                    print(first.Placement.Base)
                    pos = formatPosition(first.Placement.Base)
                    ET.SubElement(gxml, 'volume', {'name': first.Label,
                                                   'color': colHex,
                                                   'material': mat,
                                                   'position': pos})


def exportGXML(first, path, flag):
    print('Path : '+path)
    # basename = 'target_'+os.path.basename(path)
    gxml = ET.Element('gxml')
    print('ScanForStl')
    scanForStl(first, gxml, path, flag)
    # format & write gxml file
    indent(gxml)
    print("Write to gxml file")
    # ET.ElementTree(gxml).write(os.path.join(path,basename+'.gxml'))
    ET.ElementTree(gxml).write(os.path.join(path, 'target_cad.gxml'))
    print("gxml file written")


def exportMaterials(first, filename):
    if filename.lower().endswith('.xml'):
        print('Export Materials to XML file : '+filename)
        xml = ET.Element('xml')
        global define
        define = ET.SubElement(xml, 'define')
        global materials
        materials = ET.SubElement(xml, 'materials')
        processMaterials()
        indent(xml)
        ET.ElementTree(xml).write(filename)
    else:
        print('File extension must be xml')


def create_gcard(path, flag):
    basename = os.path.basename(path)
    print('Create gcard : '+basename)
    print('Path : '+path)
    gcard = ET.Element('gcard')
    ET.SubElement(gcard, 'detector', {'name': 'target_cad', 'factory': 'CAD'})
    if flag is True:
        ET.SubElement(gcard, 'detector', {
           'name': 'target_gdml', 'factory': 'GDML'})
    indent(gcard)
    path = os.path.join(path, basename + '.gcard')
    ET.ElementTree(gcard).write(path)


def checkDirectory(path):
    if not os.path.exists(path):
        print('Creating Directory : ' + path)
        os.mkdir(path)


def exportGEMC(first, path, flag):
    # flag = True  GEMC - GDML
    # flag = False just CAD
    global gxml

    print('Export GEMC')
    # basename = os.path.basename(path)
    print(path)
    print(flag)
    checkDirectory(path)
    # Create CAD directory
    cadPath = os.path.join(path, 'cad')
    checkDirectory(cadPath)
    # Create gcard
    create_gcard(path, flag)
    exportGXML(first, cadPath, flag)
    if flag is True:
        print('Create GDML directory')
        gdmlPath = os.path.join(path, 'gdml')
        checkDirectory(gdmlPath)
        # gdmlFilePath  = os.path.join(gdmlPath,basename+'.gdml')
        gdmlFilePath = os.path.join(gdmlPath, 'target_gdml.gdml')
        exportGDML(first, gdmlFilePath, 'gdml')
        # newpath = os.path.join(gdmlPath,basename+'.gxml')
        newpath = os.path.join(gdmlPath, 'target_gdml.gxml')
        indent(gxml)
        ET.ElementTree(gxml).write(newpath)


def export(exportList, filepath):
    "called when FreeCAD exports a file"
    global refPlacement

    refPlacement = {}  # a dictionary of name as key, and placement as value
                       # the name could that of <solid, an <assembly, or a <physvol

    first = exportList[0]
    print(f'Export Volume: {first.Label}')

    import os
    path, fileExt = os.path.splitext(filepath)
    print('filepath : '+path)
    print('file extension : '+fileExt)

    if fileExt.lower() == '.gdml':
        if first.TypeId == "App::Part":
            exportGDMLworld(first, filepath, fileExt)

        elif first.Label == "Materials":
            exportMaterials(first, filepath)

        else:
            print("Needs to be a Part for export")
            from PySide import QtGui
            QtGui.QMessageBox.critical(None,
                                       'Need to select a Part for export',
                                       'Press OK')

    elif fileExt.lower == '.xml':
        print('Export XML structure & solids')
        exportGDML(first, filepath, '.xml')

    if fileExt == '.gemc':
        exportGEMC(first, path, False)

    elif fileExt == '.GEMC':
        exportGEMC(first, path, True)
#
# -------------------------------------------------------------------------------------------------------
#


class SolidExporter:
    # Abstract class to export object as gdml
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
        "GDMLGmshTessellated": "GDMLGmshTessellatedExporter",
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
        "Part::MultiFuse": "MultiFuseExporter",
        "Part::Extrusion": "ExtrusionExporter",
        "Part::Revolution": "RevolutionExporter",
        "Part::Box": "BoxExporter",
        "Part::Cylinder": "CylinderExporter",
        "Part::Cone": "ConeExporter",
        "Part::Sphere": "SphereExporter",
        "Part::Cut": "BooleanExporter",
        "Part::Fuse": "BooleanExporter",
        "Part::Common": "BooleanExporter"}

    @staticmethod
    def isSolid(obj):
        print(f'isSolid {obj.Label}')
        if obj.TypeId == "Part::FeaturePython":
            typeId = obj.Proxy.Type
            if typeId == 'Array':
                if obj.ArrayType == 'ortho':
                    return True
                elif obj.ArrayType == 'polar':
                    return True
            elif typeId == 'Clone':
                clonedObj = obj.Objects[0]
                return SolidExporter.isSolid(clonedObj)

            else:
                return obj.Proxy.Type in SolidExporter.solidExporters
        else:
            return obj.TypeId in SolidExporter.solidExporters

    @staticmethod
    def getExporter(obj):
        if obj.TypeId == "Part::FeaturePython":
            typeId = obj.Proxy.Type
            if typeId == 'Array':
                if obj.ArrayType == 'ortho':
                    return OrthoArrayExporter(obj)
                elif obj.ArrayType == 'polar':
                    return PolarArrayExporter(obj)
            elif typeId == 'Clone':
                return CloneExporter(obj)
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
                print(f'classname {classname}')
                klass = globals()[classname]
                return klass(obj)
        else:
            print(f'{obj.Label} does not have a Solid Exporter')
            return None

    def __init__(self, obj):
        self.obj = obj
        self._name = self.obj.Label

    def name(self):
        prefix = ''
        if self._name[0].isdigit():
            prefix = 'S'
        ret = prefix + self._name
        print(prefix, self._name)
        return ret

    def position(self):
        return self.obj.Placement.Base

    def rotation(self):
        return self.obj.Placement.Rotation

    def placement(self):
        return FreeCAD.Placement(self.position(), self.rotation())

    def export(self):
        print('This abstract base')
        return

    def hasScale(self):
        return hasattr(self.obj, 'scale') or hasattr(self.obj, 'Scale')

    def getScale(self):
        if hasattr(self.obj, 'scale'):
            return self.obj.scale
        elif hasattr(self.obj, 'Scale'):
            return self.obj.Scale
        else:
            return FreeCAD.vector(1, 1, 1)

    def _exportScaled(self):
        if self.hasScale():
            scale = self.getScale()
            xml = ET.SubElement(solids, 'scaledSolid', {'name': self._name+'_scaled'})
            ET.SubElement(xml, 'solidref', {'ref': self.name()})
            ET.SubElement(xml, 'scale', {'name': self.name()+'_scale',
                                         'x': str(scale.x),
                                         'y': str(scale.y),
                                         'z': str(scale.z)})
            self._name += '_scaled'


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

        unionXML = ET.SubElement(solids, 'multiUnion', {'name': self.name()})
        for i, exporter in enumerate(exporters):
            volRef = exporter.name()
            nodeName = f'{self.name()}_{i}'
            nodeXML = ET.SubElement(unionXML, 'multiUnionNode', {'name': nodeName})
            ET.SubElement(nodeXML, 'solid', {'ref': volRef})
            exportPosition(nodeName, nodeXML, exporter.position())
            rot = FreeCAD.Rotation(exporter.rotation())
            # for reasons that I don't understand, in booleans and multiunions
            # angle is NOT reverse, so undo reversal of exportRotation
            rot.Angle = -rot.Angle
            exportRotation(nodeName, nodeXML, rot)

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
        # not necessary to repeat the the scaling. HOWEVER, for several of the
        # objects we deal with, the position that is
        # exported to the gdml IS NOT obj.Placment. For example, a regular box
        # as its origin at corner, whereas a gdml box has its origin at the
        # center, so we take that into account on export by adding a shift by
        # half of each dimension. Draft/scale will scale the
        # cube.Placement, which is (0,0,0), so nothing happens. The solution:
        # get the clone position, unscale it, then get the exporter.position(),
        # and then scale THAT. Note that once an object has been cloned, the
        # clone no longer keepts track of the objects POSITION, but it does
        # keep track of its dimensions. So if the object is doubles in size,
        # the (scaled) double will change, but if the object is MOVED, the
        # clone will not change its position! So the following algorith, would
        # fail. There is no way to know if the difference between the scaled
        # position and the clone's position is due to the clone moving or the
        # object moving.
        clonedPlacement = FreeCAD.Placement(exporter.placement())  # copy the placement
        m = clonedPlacement.Matrix
        invRotation = FreeCAD.Placement(m.inverse()).Rotation
        clonedPosition = clonedPlacement.Base
        clonedRotation = clonedPlacement.Rotation
        # unrotate original position
        r1 = invRotation*clonedPosition
        objPosition = FreeCAD.Vector(clonedObj.Placement.Base)
        if self.hasScale():
            scale = self.obj.Scale
            r1.scale(scale.x, scale.y, scale.z)
            delta = self.obj.Placement.Base - objPosition.scale(scale.x, scale.y, scale.z)
        else:
            delta = self.obj.Placement.Base - objPosition
        objRotation = FreeCAD.Rotation(clonedObj.Placement.Rotation)
        myRotation = self.obj.Placement.Rotation
        # additional rotation of clone
        objRotation.invert()
        additionalRotation = myRotation*objRotation
        desiredRotation = additionalRotation*clonedRotation
        r2 = desiredRotation*r1
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
        ET.SubElement(solids, 'box', {'name': self.name(),
                                      'x': str(self.obj.Length.Value),
                                      'y': str(self.obj.Width.Value),
                                      'z': str(self.obj.Height.Value),
                                      'lunit': 'mm'})
        self._exportScaled()

    def position(self):
        delta = FreeCAD.Vector(self.obj.Length.Value / 2,
                               self.obj.Width.Value / 2,
                               self.obj.Height.Value / 2)
        # Part::Box  has its origin at the corner
        # gdml box has its origin at the center
        # In FC, rotations are about corner. Ing GDML about
        # center. The following gives correct position of center
        # of exported cube
        pos = self.obj.Placement.Base + self.obj.Placement.Rotation*delta
        return pos


class CylinderExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        # Needs unique Name
        # This is for non GDML cylinder/tube
        ET.SubElement(solids, 'tube', {'name': self.name(),
                                       'rmax': str(self.obj.Radius.Value),
                                       'deltaphi': str(float(self.obj.Angle.Value)),
                                       'aunit': 'deg',
                                       'z': str(self.obj.Height.Value),
                                       'lunit': 'mm'})
        self._exportScaled()

    def position(self):
        delta = FreeCAD.Vector(0, 0, self.obj.Height.Value / 2)
        # see comments in BoxExporter
        pos = self.obj.Placement.Base + self.obj.Placement.Rotation*delta
        return pos


class ConeExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'cone', {
            'name': self.name(),
            'rmax1': str(self.obj.Radius1.Value),
            'rmax2': str(self.obj.Radius2.Value),
            'deltaphi': str(float(self.obj.Angle.Value)),
            'aunit': 'deg',
            'z': str(self.obj.Height.Value),
            'lunit': 'mm'})
        self._exportScaled()

    def position(self):
        # Adjustment for position in GDML
        delta = FreeCAD.Vector(0, 0, self.obj.Height.Value / 2)
        # see comments in BoxExporter
        pos = self.obj.Placement.Base + self.obj.Placement.Rotation*delta
        return pos


class SphereExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'sphere', {
            'name': self.name(),
            'rmax': str(self.obj.Radius.Value),
            'starttheta': str(90.-float(self.obj.Angle2.Value)),
            'deltatheta': str(float(self.obj.Angle2.Value - self.obj.Angle1.Value)),
            'deltaphi': str(float(self.obj.Angle3.Value)),
            'aunit': 'deg',
            'lunit': 'mm'})
        self._exportScaled()

    def position(self):
        # see comments in processBoxObject
        unrotatedpos = self.obj.Placement.Base
        pos = self.obj.Placement.Rotation*unrotatedpos
        return pos


class BooleanExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def isBoolean(self, obj):
        id = obj.TypeId
        return (id == "Part::Cut" or id == "Part::Fuse" or
                id == "Part::Common")

    def boolOperation(self, obj):
        opsDict = {"Part::Cut": 'subtraction',
                   "Part::Fuse": 'union',
                   "Part::Common": 'intersection'}
        if obj.TypeId in opsDict:
            return opsDict[obj.TypeId]
        else:
            print(f'Boolean type {obj.TypId} not handled yet')
            return None

    def export(self):
        '''
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
        '''
        GDMLShared.trace('Process Boolean Object')

        obj = self.obj
        boolsList = [obj]  # list of booleans that are part of obj
        # dynamic list the is used to figure out when we've iterated over all
        #  subobjects that are booleans
        tmpList = [obj]
        ref1 = {}  # first solid exporter
        ref2 = {}  # second solid exporter
        while(len(tmpList) > 0):
            obj1 = tmpList.pop()
            solidExporter = SolidExporter.getExporter(obj1.Base)
            ref1[obj1] = solidExporter
            if self.isBoolean(obj1.Base):
                tmpList.append(obj1.Base)
                boolsList.append(obj1.Base)
            else:
                solidExporter.export()

            solidExporter = SolidExporter.getExporter(obj1.Tool)
            ref2[obj1] = solidExporter
            if self.isBoolean(obj1.Tool):
                tmpList.append(obj1.Tool)
                boolsList.append(obj1.Tool)
            else:
                solidExporter.export()

        # Now tmpList is empty and boolsList has list of all booleans
        for obj1 in reversed(boolsList):
            operation = self.boolOperation(obj1)
            if operation is None:
                continue
            solidName = obj1.Label
            boolXML = ET.SubElement(solids, str(operation), {
                'name': solidName})
            ET.SubElement(boolXML, 'first', {'ref': ref1[obj1].name()})
            ET.SubElement(boolXML, 'second', {'ref': ref2[obj1].name()})
            # process position & rotation
            pos = ref2[obj1].position()
            exportPosition(ref2[obj1].name(), boolXML, pos)
            # For booleans, gdml want actual rotation, not reverse
            # processRotation export negative of rotation angle(s)
            # This is ugly way of NOT reversing angle:

            rot = FreeCAD.Rotation()
            rot.Axis = ref2[obj1].rotation().Axis
            angle = ref2[obj1].rotation().Angle
            rot.Angle = -angle
            exportRotation(ref2[obj1].name(), boolXML, rot)
        self._exportScaled()


class GDMLSolidExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)
        self._name = nameOfGDMLobject(self.obj)

    def name(self):
        prefix = ''
        if self._name[0].isdigit():
            prefix = 'S'
        return prefix + self._name


class GDMLArb8Exporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'arb8', {'name': self.name(),
                                       'v1x': str(self.obj.v1x),
                                       'v1y': str(self.obj.v1y),
                                       'v2x': str(self.obj.v2x),
                                       'v2y': str(self.obj.v2y),
                                       'v3x': str(self.obj.v3x),
                                       'v3y': str(self.obj.v3y),
                                       'v4x': str(self.obj.v4x),
                                       'v4y': str(self.obj.v4y),
                                       'v5x': str(self.obj.v5x),
                                       'v5y': str(self.obj.v5y),
                                       'v6x': str(self.obj.v6x),
                                       'v6y': str(self.obj.v6y),
                                       'v7x': str(self.obj.v7x),
                                       'v7y': str(self.obj.v7y),
                                       'v8x': str(self.obj.v8x),
                                       'v8y': str(self.obj.v8y),
                                       'dz': str(self.obj.dz),
                                       'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLBoxExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'box', {'name': self.name(),
                                      'x': str(self.obj.x),
                                      'y': str(self.obj.y),
                                      'z': str(self.obj.z),
                                      'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLConeExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'cone', {'name': self.name(),
                                       'rmin1': str(self.obj.rmin1),
                                       'rmin2': str(self.obj.rmin2),
                                       'rmax1': str(self.obj.rmax1),
                                       'rmax2': str(self.obj.rmax2),
                                       'startphi': str(self.obj.startphi),
                                       'deltaphi': str(self.obj.deltaphi),
                                       'aunit': self.obj.aunit,
                                       'z': str(self.obj.z),
                                       'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLcutTubeExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'cutTube', {'name': self.name(),
                                          'rmin': str(self.obj.rmin),
                                          'rmax': str(self.obj.rmax),
                                          'startphi': str(self.obj.startphi),
                                          'deltaphi': str(self.obj.deltaphi),
                                          'aunit': self.obj.aunit,
                                          'z': str(self.obj.z),
                                          'highX': str(self.obj.highX),
                                          'highY': str(self.obj.highY),
                                          'highZ': str(self.obj.highZ),
                                          'lowX': str(self.obj.lowX),
                                          'lowY': str(self.obj.lowY),
                                          'lowZ': str(self.obj.lowZ),
                                          'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLElConeExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'elcone', {'name': self.name(),
                                         'dx': str(self.obj.dx),
                                         'dy': str(self.obj.dy),
                                         'zcut': str(self.obj.zcut),
                                         'zmax': str(self.obj.zmax),
                                         'lunit': str(self.obj.lunit)})
        self._exportScaled()


class GDMLEllipsoidExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'ellipsoid', {'name': self.name(),
                                            'ax': str(self.obj.ax),
                                            'by': str(self.obj.by),
                                            'cz': str(self.obj.cz),
                                            'zcut1': str(self.obj.zcut1),
                                            'zcut2': str(self.obj.zcut2),
                                            'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLElTubeExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'eltube', {'name': self.name(),
                                         'dx': str(self.obj.dx),
                                         'dy': str(self.obj.dy),
                                         'dz': str(self.obj.dz),
                                         'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLHypeExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'hype', {'name': self.name(),
                                       'rmin': str(self.obj.rmin),
                                       'rmax': str(self.obj.rmax),
                                       'z': str(self.obj.z),
                                       'inst': str(self.obj.inst),
                                       'outst': str(self.obj.outst),
                                       'aunit': self.obj.aunit,
                                       'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLParaboloidExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'paraboloid', {'name': self.name(),
                                             'rlo': str(self.obj.rlo),
                                             'rhi': str(self.obj.rhi),
                                             'dz': str(self.obj.dz),
                                             'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLOrbExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'orb', {'name': self.name(),
                                      'r': str(self.obj.r),
                                      'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLParaExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'para', {'name': self.name(),
                                       'x': str(self.obj.x),
                                       'y': str(self.obj.y),
                                       'z': str(self.obj.z),
                                       'alpha': str(self.obj.alpha),
                                       'theta': str(self.obj.theta),
                                       'phi': str(self.obj.phi),
                                       'aunit': str(self.obj.aunit),
                                       'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLPolyconeExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        cone = ET.SubElement(solids, 'polycone', {
            'name': self.name(),
            'startphi': str(self.obj.startphi),
            'deltaphi': str(self.obj.deltaphi),
            'aunit': self.obj.aunit,
            'lunit': self.obj.lunit})
        self._exportScaled()

        for zplane in self.obj.OutList:
            ET.SubElement(cone, 'zplane', {'rmin': str(zplane.rmin),
                                           'rmax': str(zplane.rmax),
                                           'z': str(zplane.z)})


class GDMLGenericPolyconeExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        cone = ET.SubElement(solids, 'genericPolycone', {
            'name': self.name(),
            'startphi': str(self.obj.startphi),
            'deltaphi': str(self.obj.deltaphi),
            'aunit': self.obj.aunit,
            'lunit': self.obj.lunit})
        self._exportScaled()
        for rzpoint in self.obj.OutList:
            ET.SubElement(cone, 'rzpoint', {'r': str(rzpoint.r),
                                            'z': str(rzpoint.z)})


class GDMLGenericPolyhedraExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        polyhedra = ET.SubElement(solids, 'genericPolyhedra', {
            'name': self.name(),
            'startphi': str(self.obj.startphi),
            'deltaphi': str(self.obj.deltaphi),
            'numsides': str(self.obj.numsides),
            'aunit': self.obj.aunit,
            'lunit': self.obj.lunit})
        self._exportScaled()
        for rzpoint in self.obj.OutList:
            ET.SubElement(polyhedra, 'rzpoint', {'r': str(rzpoint.r),
                                                 'z': str(rzpoint.z)})


class GDMLPolyhedraExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        poly = ET.SubElement(solids, 'polyhedra', {
            'name': self.name(),
            'startphi': str(self.obj.startphi),
            'deltaphi': str(self.obj.deltaphi),
            'numsides': str(self.obj.numsides),
            'aunit': self.obj.aunit,
            'lunit': self.obj.lunit})
        self._exportScaled()

        for zplane in self.obj.OutList:
            ET.SubElement(poly, 'zplane', {'rmin': str(zplane.rmin),
                                           'rmax': str(zplane.rmax),
                                           'z': str(zplane.z)})


class GDMLSphereExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'sphere', {
            'name': self.name(),
            'rmin': str(self.obj.rmin),
            'rmax': str(self.obj.rmax),
            'startphi': str(self.obj.startphi),
            'deltaphi': str(self.obj.deltaphi),
            'starttheta': str(self.obj.starttheta),
            'deltatheta': str(self.obj.deltatheta),
            'aunit': self.obj.aunit,
            'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLSampledTessellatedExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        tessName = self.name()
        print(f'tessname: {tessName}')
        # Use more readable version
        tessVname = tessName + '_'
        # print(dir(obj))

        verts = self.obj.vertsList
        tess = ET.SubElement(solids, 'tessellated', {'name': tessName})
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
                ET.SubElement(tess, 'triangular', {
                   'vertex1': tessVname+str(i0),
                   'vertex2': tessVname+str(i1),
                   'vertex3': tessVname+str(i2),
                   'type': 'ABSOLUTE'})
            elif nVerts == 4:
                i0 = indexList[i]
                i1 = indexList[i + 1]
                i2 = indexList[i + 2]
                i3 = indexList[i + 3]
                ET.SubElement(tess, 'quadrangular', {
                   'vertex1': tessVname+str(i0),
                   'vertex2': tessVname+str(i1),
                   'vertex3': tessVname+str(i2),
                   'vertex4': tessVname+str(i3),
                   'type': 'ABSOLUTE'})
            i += nVerts
        self._exportScaled()


class GDMLTessellatedExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        tessName = self.name()
        # Use more readable version
        tessVname = tessName + '_'
        # print(dir(obj))
        vertexHashcodeDict = {}

        '''
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
        '''
        tess = ET.SubElement(solids, 'tessellated', {'name': tessName})
        placementCorrection = self.obj.Placement.inverse()
        for i, v in enumerate(self.obj.Shape.Vertexes):
            vertexHashcodeDict[v.hashCode()] = i
            exportDefineVertex(tessVname, placementCorrection*v.Point, i)

        for f in self.obj.Shape.Faces:
            # print(f'len(f.Edges) {len(f.Edges)}')
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
        self._exportScaled()


class GDMLTetraExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        tetraName = self.name()
        v1Name = tetraName + 'v1'
        v2Name = tetraName + 'v2'
        v3Name = tetraName + 'v3'
        v4Name = tetraName + 'v4'
        exportDefine(v1Name, self.obj.v1)
        exportDefine(v2Name, self.obj.v2)
        exportDefine(v3Name, self.obj.v3)
        exportDefine(v4Name, self.obj.v4)

        ET.SubElement(solids, 'tet', {'name': tetraName,
                                      'vertex1': v1Name,
                                      'vertex2': v2Name,
                                      'vertex3': v3Name,
                                      'vertex4': v4Name})
        self._exportScaled()


class GDMLTetrahedronExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        global structure
        global solids
        tetrahedronName = self.name()
        print('Len Tet' + str(len(self.obj.Proxy.Tetra)))
        count = 0
        for t in self.obj.Proxy.Tetra:
            tetraName = tetrahedronName + '_' + str(count)
            v1Name = tetraName + 'v1'
            v2Name = tetraName + 'v2'
            v3Name = tetraName + 'v3'
            v4Name = tetraName + 'v4'
            exportDefine(v1Name, t[0])
            exportDefine(v2Name, t[1])
            exportDefine(v3Name, t[2])
            exportDefine(v4Name, t[3])
            ET.SubElement(solids, 'tet', {'name': tetraName,
                                          'vertex1': v1Name,
                                          'vertex2': v2Name,
                                          'vertex3': v3Name,
                                          'vertex4': v4Name})
            lvName = 'LVtetra' + str(count)
            lvol = ET.SubElement(structure, 'volume', {'name': lvName})
            ET.SubElement(lvol, 'materialref', {'ref': self.obj.material})
            ET.SubElement(lvol, 'solidref', {'ref': tetraName})
            count += 1

        # Now put out Assembly
        assembly = ET.SubElement(structure, 'assembly', {
            'name': tetrahedronName})
        count = 0
        for t in self.obj.Proxy.Tetra:
            lvName = 'LVtetra' + str(count)
            physvol = ET.SubElement(assembly, 'physvol')
            ET.SubElement(physvol, 'volumeref', {'ref': lvName})
            # ET.SubElement(physvol, 'position')
            # ET.SubElement(physvol, 'rotation')
            count += 1
        self._exportScaled()


class GDMLTorusExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'torus', {'name': self.name(),
                                        'rmin': str(self.obj.rmin),
                                        'rmax': str(self.obj.rmax),
                                        'rtor': str(self.obj.rtor),
                                        'startphi': str(self.obj.startphi),
                                        'deltaphi': str(self.obj.deltaphi),
                                        'aunit': self.obj.aunit,
                                        'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLTrapExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'trap', {'name': self.name(),
                                       'z': str(self.obj.z),
                                       'theta': str(self.obj.theta),
                                       'phi': str(self.obj.phi),
                                       'x1': str(self.obj.x1),
                                       'x2': str(self.obj.x2),
                                       'x3': str(self.obj.x3),
                                       'x4': str(self.obj.x4),
                                       'y1': str(self.obj.y1),
                                       'y2': str(self.obj.y2),
                                       'alpha1': str(self.obj.alpha),
                                       'alpha2': str(self.obj.alpha),
                                       'aunit': self.obj.aunit,
                                       'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLTrdExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'trd', {'name': self.name(),
                                      'z': str(self.obj.z),
                                      'x1': str(self.obj.x1),
                                      'x2': str(self.obj.x2),
                                      'y1': str(self.obj.y1),
                                      'y2': str(self.obj.y2),
                                      'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLTubeExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'tube', {'name': self.name(),
                                       'rmin': str(self.obj.rmin),
                                       'rmax': str(self.obj.rmax),
                                       'startphi': str(self.obj.startphi),
                                       'deltaphi': str(self.obj.deltaphi),
                                       'aunit': self.obj.aunit,
                                       'z': str(self.obj.z),
                                       'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLTwistedboxExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'twistedbox', {
            'name': self.name(),
            'PhiTwist': str(self.obj.PhiTwist),
            'x': str(self.obj.x),
            'y': str(self.obj.y),
            'z': str(self.obj.z),
            'aunit': str(self.obj.aunit),
            'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLTwistedtrdExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'twistedtrd', {
            'name': self.name(),
            'PhiTwist': str(self.obj.PhiTwist),
            'x1': str(self.obj.x1),
            'x2': str(self.obj.x2),
            'y1': str(self.obj.y1),
            'y2': str(self.obj.y2),
            'z': str(self.obj.z),
            'aunit': str(self.obj.aunit),
            'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLTwistedtrapExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'twistedtrap', {
            'name': self.name(),
            'PhiTwist': str(self.obj.PhiTwist),
            'x1': str(self.obj.x1),
            'x2': str(self.obj.x2),
            'y1': str(self.obj.y1),
            'y2': str(self.obj.y2),
            'x3': str(self.obj.x3),
            'x4': str(self.obj.x4),
            'z': str(self.obj.z),
            'Theta': str(self.obj.Theta),
            'Phi': str(self.obj.Phi),
            'Alph': str(self.obj.Alph),
            'aunit': str(self.obj.aunit),
            'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLTwistedtubsExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'twistedtubs', {
            'name': self.name(),
            'twistedangle': str(self.obj.twistedangle),
            'endinnerrad': str(self.obj.endinnerrad),
            'endouterrad': str(self.obj.endouterrad),
            'zlen': str(self.obj.zlen),
            'phi': str(self.obj.phi),
            'aunit': str(self.obj.aunit),
            'lunit': self.obj.lunit})
        self._exportScaled()


class GDMLXtruExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        xtru = ET.SubElement(solids, 'xtru', {'name': self.name(),
                                              'lunit': self.obj.lunit})
        for items in self.obj.OutList:
            if items.Type == 'twoDimVertex':
                ET.SubElement(xtru, 'twoDimVertex', {'x': str(items.x),
                                                     'y': str(items.y)})
            if items.Type == 'section':
                ET.SubElement(xtru, 'section', {
                    'zOrder': str(items.zOrder),
                    'zPosition': str(items.zPosition),
                    'xOffset': str(items.xOffset),
                    'yOffset': str(items.yOffset),
                    'scalingFactor': str(items.scalingFactor)})
        self._exportScaled()


class GDML2dVertexExporter(GDMLSolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def export(self):
        ET.SubElement(solids, 'twoDimVertex', {'x': self.obj.x,
                                               'y': self.obj.y})


class MultiFuseExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def name(self):
        solidName = 'MultiFuse' + self.obj.Label
        return solidName

    def export(self):
        GDMLShared.trace("Multifuse - multiunion")
        # test and fix
        # First add solids in list before reference
        print('Output Solids')
        exporters = []
        for sub in self.obj.OutList:
            exporter = SolidExporter.getExporter(sub)
            if exporter is not None:
                exporter.export()
                exporters.append(exporter)

        GDMLShared.trace('Output Solids Complete')
        multUnion = ET.SubElement(solids, 'multiUnion', {
            'name': self.name()})

        num = 1
        for exp in exporters:
            GDMLShared.trace(exp.name())
            node = ET.SubElement(multUnion, 'multiUnionNode', {
                'name': 'node-'+str(num)})
            ET.SubElement(node, 'solid', {'ref': exp.name()})
            processPlacement(exp.name(), node, exp.placement())
            num += 1

        GDMLShared.trace('Return MultiFuse')
        self._exportScaled()


class OrthoArrayExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)
        self._name = 'MultiUnion-' + self.obj.Label

    def export(self):
        base = self.obj.OutList[0]
        print(base.Label)
        if hasattr(base, 'TypeId') and base.TypeId == 'App::Part':
            print(f'**** Arrays of {base.TypeId} ({base.Label}) currently not supported ***')
            return
        baseExporter = SolidExporter.getExporter(base)
        if baseExporter is None:
            print(f'Cannot export {base.Label}')
            return
        baseExporter.export()
        volRef = baseExporter.name()
        unionXML = ET.SubElement(solids, 'multiUnion', {'name': self.name()})
        basePos = baseExporter.position()
        for ix in range(self.obj.NumberX):
            translate = basePos + ix*self.obj.IntervalX
            for iy in range(self.obj.NumberY):
                translate += iy*self.obj.IntervalY
                for iz in range(self.obj.NumberZ):
                    nodeName = f'{self.name()}_{ix}_{iy}_{iz}'
                    translate += iz*self.obj.IntervalZ
                    nodeXML = ET.SubElement(unionXML, 'multiUnionNode', {
                        'name': nodeName})
                    ET.SubElement(nodeXML, 'solid', {'ref': volRef})
                    ET.SubElement(nodeXML, 'position', {
                        'x': str(translate.x),
                        'y': str(translate.y),
                        'z': str(translate.z),
                        'unit': 'mm'})
        self._exportScaled()


class PolarArrayExporter(SolidExporter):
    def __init__(self, obj):
        super().__init__(obj)

    def name(self):
        solidName = 'MultiUnion-' + self.obj.Label
        return solidName

    def export(self):
        base = self.obj.OutList[0]
        print(base.Label)
        if hasattr(base, 'TypeId') and base.TypeId == 'App::Part':
            print(f'**** Arrays of {base.TypeId} ({base.Label}) currently not supported ***')
            return
        baseExporter = SolidExporter.getExporter(base)
        baseExporter.export()
        volRef = baseExporter.name()
        unionXML = ET.SubElement(solids, 'multiUnion', {'name': self.name()})
        dthet = self.obj.Angle/self.obj.NumberPolar
        positionVector = baseExporter.position()
        axis = self.obj.Axis
        # TODO adjust for center of rotation != origin
        for i in range(self.obj.NumberPolar):
            rot = FreeCAD.Rotation(axis, i*dthet)
            pos = rot*positionVector     # position has to be roated too!
            rot.Angle = -rot.Angle   # undo angle reversal by exportRotation
            nodeName = f'{self.name()}_{i}'
            nodeXML = ET.SubElement(unionXML, 'multiUnionNode', {'name': nodeName})
            ET.SubElement(nodeXML, 'solid', {'ref': volRef})
            exportPosition(nodeName, nodeXML, pos)
            exportRotation(nodeName, nodeXML, rot)
        self._exportScaled()

#
# -------------------------------------- revolutionExporter ----------------------------------------------------------------
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
        return self.face.isInside(otherCurve.edgeList[0].Vertexes[0].Point, 0.001, True)


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
        deflection = Deviation*radialExtent(self.edgeList)
        print(f'Deflection = {deflection}')
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
        rtor = math.sqrt(x*x + y*y)
        exportTorus(self.name, rmax, rtor, self.angle)


class RevolvedNEdges(RevolvedClosedCurve):
    def __init__(self, name, edgelist, angle, axis):
        super().__init__(name, edgelist, angle, axis)

    def export(self):
        global solids

        # maxdev = self.deflectionFraction*radialExtent(self.edgeList)
        verts = []
        for i, e in enumerate(self.edgeList):

            while switch(e.Curve.TypeId):
                if case('Part::GeomLineSegment'):
                    print('Part::GeomLineSegment')
                    verts.append(e.Vertexes[0].Point)
                    break

                if case('Part::GeomLine'):
                    print('Part::GeomLine')
                    verts.append(e.Vertexes[0].Point)
                    break

                else:
                    curveName = self.name + '_c'+str(i)
                    curveSection = RevolvedClosedCurve(curveName, [e],
                                                       self.angle, self.axis)
                    verts += curveSection.discretize()
                    break

        xtruName = self.name
        exportPolycone(xtruName, verts, self.angle)


# arrange a list of edges in the x-y plane in Counter Clock Wise direction
# This can be easily generalized for points in ANY plane: if the normal
# defining the desired direction of the plane is given, then the z component
# below should be changed a dot prduct with the normal


def arrangeCCW(verts, normal=Vector(0, 0, 1)):
    reverse = False
    v0 = verts[0]
    rays = [(v - v0) for v in verts[1:]]
    area = 0
    for i, ray in enumerate(rays[:-1]):
        area += (rays[i].cross(rays[i+1])).dot(normal)
    if area < 0:
        verts.reverse()
        reverse = True

    return reverse

# Utility to determine if vector from point v0 to point v1 (v1-v0)
# is on sime side of normal or opposite. Return true if v ploints along normal


def pointInsideEdge(v0, v1, normal):
    v = v1 - v0
    if v.dot(normal) < 0:
        return False
    else:
        return True


def edgelistBB(edgelist):
    # get edge list bounding box
    bb = FreeCAD.BoundBox(0, 0, 0, 0, 0, 0)
    for e in edgelist:
        bb.add(e.BoundBox)
    return bb


def edgelistBBoxArea(edgelist):
    bb = edgelistBB(edgelist)
    return bb.XLength * bb.YLength


def sortEdgelistsByBoundingBoxArea(listoflists):
    listoflists.sort(reverse=True, key=edgelistBBoxArea)


# return maxRadialdistance - minRadialDistance
def radialExtent(edges, axis=Vector(0, 0, 1)):
    rmin = sys.float_info.max
    rmax = -sys.float_info.max
    for e in edges:
        b = e.BoundBox
        for i in range(0, 8):  # loop over box bounraries
            v = b.getPoint(i)
            radialVector = v - v.dot(axis) * axis
            r = radialVector.Length
            if r < rmin:
                rmin = r
            elif r > rmax:
                rmax = r

    return (rmax - rmin)


def exportEllipticalTube(name, dx, dy, height):
    global solids

    ET.SubElement(solids, 'eltube', {'name': name,
                                     'dx': str(dx),
                                     'dy': str(dy),
                                     'dz': str(height/2),
                                     'lunit': 'mm'})


def exportTorus(name, rmax, rtor, angle):
    global solids

    ET.SubElement(solids, 'torus', {'name': name,
                                    'rmin': '0',
                                    'rmax': str(rmax),
                                    'rtor': str(rtor),
                                    'startphi': '0',
                                    'deltaphi': str(angle),
                                    'aunit': 'deg',
                                    'lunit': 'mm'})


def exportPolycone(name, vlist, angle):
    global solids

    cone = ET.SubElement(solids, 'genericPolycone', {
        'name': name,
        'startphi': '0',
        'deltaphi': str(angle),
        'aunit': 'deg',
        'lunit': 'mm'})
    for v in vlist:
        r = math.sqrt(v.x*v.x + v.y*v.y)
        ET.SubElement(cone, 'rzpoint', {'r': str(r),
                                        'z': str(v.z)})
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
            if case('Part::GeomCircle'):
                if closed is True:
                    print('Circle')
                    return RevolvedCircle(name, edges, angle, axis)
                else:
                    print('Revolve Arc of Circle')
                    return RevolvedClosedCurve(name, edges, angle, axis)
                    # return RevolvedArcSection(name, edges, height)

            else:
                print(f'revolve {e.Curve.TypeId}')
                return RevolvedClosedCurve(name, edges, angle, axis)

    else:  # three or more edges
        return RevolvedNEdges(name, edges, angle, axis)


# scale up a solid that will be subtracted so it ounched thru parent
def scaleUp(scaledName, originalName, zFactor):
    ss = ET.SubElement(solids, 'scaledSolid', {'name': scaledName})
    ET.SubElement(ss, 'solidref', {'ref': originalName})
    ET.SubElement(ss, 'scale', {'name': originalName+'_ss',
                                'x': '1', 'y': '1', 'z': str(zFactor)})


def rotatedPos(closedCurve, rot):
    # Circles and ellipses (tubes and elliptical tubes) are referenced to origin
    # in GDML and have to be translated to their position via a position reference
    # when placed as a physical volume. This is done by adding the translation
    # to the Part::Extrusion Placement. However, if the placement includes
    # a rotation, Geant4 GDML would rotate the Origin-based curve THEN translate.
    # This would not work. We have to translate first THEN rotate. This method
    # just does the needed rotation of the poisition vector
    #
    pos = closedCurve.position
    if isinstance(closedCurve, ExtrudedCircle) or \
       isinstance(closedCurve, ExtrudedEllipse):
        pos = rot*closedCurve.position

    return pos


class RevolutionExporter(SolidExporter):
    def __init__(self, revolveObj):
        super().__init__(revolveObj)
        self.sketchObj = revolveObj.Source
        self.lastName = self.obj.Label  # initial name: might be modified later

    def name(self):
        # override default name in SolidExporter
        prefix = ''
        if self.lastName[0].isdigit():
            prefix = 'R'
        return prefix + self.lastName

    def position(self):
        # This presumes export has been called before postion()
        # Things will be screwed up, other wise
        return self._position

    def rotation(self):
        # This presumes export has been called before postion()
        # Things will be screwed up, other wise
        return self._rotation

    def export(self):
        global Deviation
        revolveObj = self.obj

        # Fractional deviation
        Deviation = revolveObj.ViewObject.Deviation/100.0
        sortededges = Part.sortEdges(self.sketchObj.Shape.Edges)
        # sort by largest area to smallest area
        sortEdgelistsByBoundingBoxArea(sortededges)
        # getClosedCurve returns one of the sub classes of ClosedCurve that
        # knows how to export the specifc closed edges
        # Make names based on Revolve name
        angle = revolveObj.Angle
        axis = revolveObj.Axis
        eName = revolveObj.Label
        # get a list of curves (instances of class ClosedCurve)
        # for each set of closed edges
        curves = []
        for i, edges in enumerate(sortededges):
            curve = getRevolvedCurve(eName+str(i), edges, angle, axis)
            if curve is not None:
                curves.append(curve)
        if len(curves) == 0:
            print('No edges that can be revolved were found')
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
        rootCurve.export()  # a curve is created with a unique name
        firstName = rootCurve.name
        booleanName = firstName

        rootPos = rootCurve.position
        rootRot = rootCurve.rotation  # for now consider only angle of rotation about z-axis

        for c in lst[1:]:
            node = c[0]
            parity = c[1]
            curve = node.closedCurve
            curve.export()
            if parity == 0:
                boolType = 'union'
                secondName = curve.name
                secondPos = curve.position
            else:
                boolType = 'subtraction'
                secondName = curve.name
                secondPos = curve.position

            booleanName = curve.name + '_bool'
            boolSolid = ET.SubElement(solids, boolType, {'name': booleanName})
            ET.SubElement(boolSolid, 'first', {'ref': firstName})
            ET.SubElement(boolSolid, 'second', {'ref': secondName})
            relativePosition = secondPos - rootPos
            zAngle = curve.rotation[2] - rootRot[2]
            posName = curve.name+'_pos'
            rotName = curve.name+'_rot'
            # position of second relative to first
            exportDefine(posName, relativePosition)
            ET.SubElement(define, 'rotation', {'name': rotName, 'unit': 'deg',
                                               'x': '0', 'y': '0',
                                               'z': str(zAngle)})

            ET.SubElement(boolSolid, 'positionref', {'ref': posName})
            ET.SubElement(boolSolid, 'rotationref', {'ref': rotName})
            firstName = booleanName

        self.lastName = booleanName
        # Because the position of each closed curve might not be at the
        # origin, whereas primitives (tubes, cones, etc, are created centered at
        # the origin, we need to shift the position of the very first node by its
        # position, in addition to the shift by the Extrusion placement

        revolvePosition = revolveObj.Placement.Base
        zoffset = Vector(0, 0, 0)
        angles = quaternion2XYZ(revolveObj.Placement.Rotation)
        # need to add rotations of elliptical tubes. Assume extrusion is on z-axis
        # Probably wil not work in general
        zAngle = angles[2] + rootRot[2]
        print(rootPos)
        print(rootCurve.name)
        print(rootCurve.position)
        rootPos = rotatedPos(rootCurve, revolveObj.Placement.Rotation)
        print(rootPos)
        Base = revolvePosition + rootPos - zoffset

        rotX = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), angles[0])
        rotY = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), angles[1])
        rotZ = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), zAngle)

        rot = rotX*rotY*rotZ

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


class ClosedCurve:
    def __init__(self, name, edgeList):
        self.name = name
        self.face = Part.Face(Part.Wire(edgeList))
        self.edgeList = edgeList

    def isInside(self, otherCurve):
        # ClosedCurves are closed: so if ANY vertex of the otherCurve
        # is inside, then the whole curve is inside
        return self.face.isInside(otherCurve.edgeList[0].Vertexes[0].Point, 0.001, True)


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
        return verts[int(len(verts)/2)]

    def discretize(self):
        global Deviation
        edge = self.edgeList[0]
        deflection = Deviation*edge.BoundBox.DiagonalLength
        print(f'Deflection = {deflection}')
        return edge.discretize(Deflection=deflection)


class ExtrudedCircle(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)
        self.position = edgelist[0].Curve.Center + Vector(0, 0, height/2)

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
        vc = (v1+v2)/2
        v = v2-v1
        u = v.normalize()
        # extend the ends of the chord so extrusion can cut all of circle, if needed
        v1 = vc + radius*u
        v2 = vc - radius*u
        # component of vmid perpendicular to u
        vc_vmid = vmid - vc
        n = vc_vmid - u.dot(vc_vmid)*u
        n.normalize()
        # complete edges of box paerpendicular to chord, toward mid arc point
        v3 = v2 + 2*radius*n
        v4 = v1 + 2*radius*n

        xtruName = self.name+'_xtru'
        exportXtru(xtruName, [v1, v2, v3, v4], self.height)

        # tube to be cut1
        tubeName = self.name+'_tube'
        exportTube(tubeName, edge.Curve.Radius, self.height)

        # note, it is mandatory that name be that of ClosedCurve
        intersect = ET.SubElement(solids, 'intersection', {'name': self.name})
        ET.SubElement(intersect, 'first', {'ref': xtruName})
        ET.SubElement(intersect, 'second', {'ref': tubeName})
        pos = edge.Curve.Center + Vector(0, 0, self.height/2)
        exportPosition(tubeName, intersect, pos)


class ExtrudedEllipse(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)
        curve = edgelist[0].Curve
        self.position = curve.Center + Vector(0, 0, height/2)
        angle = math.degrees(curve.AngleXU)
        self.rotation = [0, 0, angle]

    def export(self):
        edge = self.edgeList[0]
        exportEllipticalTube(self.name, edge.Curve.MajorRadius,
                             edge.Curve.MinorRadius,
                             self.height)


class ExtrudedEllipticalSection(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)
        # Note extrusion polyogn will be in absolute coordinates
        # since arc section is relative to that, position is actually (0,0,0)
        # same goes for rotation

    '''
    def midPoint(self):
        edge = self.edgeList[0]
        a = edge.Curve.MajorRadius
        b = edge.Curve.MinorRadius
        angleXU = edge.Curve.AngleXU
        thet1 = edge.FirstParameter  # in radians, in unorated ellipse
        thet2 = edge.LastParameter  # in radians, in onrated ellipse
        thetmid = (thet1+thet2)/2 + angleXU

        # Major axis angle seems to be off by pi for some ellipse. Restrict it to be
        # be between 0 an pi
        if angleXU < 0:
            angleXU += 180

        # TODO must deal with case where cutting chord is along major axis
        # u_vc_vcenter = vc_vcenter.normalize()  # unit vector fom center of circle to center of chord

        # vertexes of triangle formed by chord ends and ellise mid point
        # In polar coordinates equation of ellipse is r(thet) = a*(1-eps*eps)/(1+eps*cos(thet))
        # if the ellipse is rotatated by an angle AngleXU, then
        # x = r*cos(thet+angleXU), y = r*sin(thet+angleXU), for thet in frame of unrotated ellipse
        # now edge.FirstParameter is begining angle of unrotaeted ellipse

        def sqr(x):
            return x*x

        def r(thet):
            return math.sqrt(1.0/(sqr(math.cos(thet)/a) + sqr(math.sin(thet)/b)))

        rmid = r(thetmid)
        vmid = Vector(rmid*math.cos(thetmid), rmid*math.sin(thetmid), 0)

        vmid += edge.Curve.Center

        return vmid
    '''

    def export(self):
        global solids

        edge = self.edgeList[0]
        a = dx = edge.Curve.MajorRadius
        b = dy = edge.Curve.MinorRadius

        # vertexes of triangle formed by chord ends and ellise mid point
        # In polar coordinates equation of ellipse is r(thet) = a*(1-eps*eps)/(1+eps*cos(thet))
        # if the ellipse is rotatated by an angle AngleXU, then
        # x = r*cos(thet+angleXU), y = r*sin(thet+angleXU), for thet in frame of unrotated ellipse
        # now edge.FirstParameter is begining angle of unrotaeted ellipse
        # polar equation of ellipse, with r measured from FOCUS. Focus at a*eps
        # r = lambda thet: a*(1-eps*eps)/(1+eps*math.cos(thet))
        # polar equation of ellipse, with r measured from center a*eps

        def sqr(x):
            return x*x

        def r(thet):
            return math.sqrt(1.0/(sqr(math.cos(thet)/a) + sqr(math.sin(thet)/b)))

        v1 = edge.Vertexes[0].Point
        v2 = edge.Vertexes[1].Point
        vmid = self.midPoint()

        # midpoint of chord
        vc = (v1+v2)/2
        v = v2-v1
        u = v.normalize()  # unit vector from v1 to v2
        # extend the ends of the chord so extrusion can cut all of ellipse, if needed
        v1 = vc + 2*a*u
        v2 = vc - 2*a*u

        # component of vmid perpendicular to u
        vc_vmid = vmid - vc
        n = vc_vmid - u.dot(vc_vmid)*u
        n.normalize()
        v3 = v2 + 2*a*n
        v4 = v1 + 2*a*n

        xtruName = self.name+'_xtru'
        exportXtru(xtruName, [v1, v2, v3, v4], self.height)

        # tube to be cut1
        tubeName = self.name+'_tube'
        exportEllipticalTube(tubeName, dx, dy, self.height)

        # note, it is mandatory that name be that of ClosedCurve
        intersect = ET.SubElement(solids, 'intersection', {'name': self.name})
        ET.SubElement(intersect, 'first', {'ref': xtruName})
        ET.SubElement(intersect, 'second', {'ref': tubeName})
        pos = edge.Curve.Center + Vector(0, 0, self.height/2)
        exportPosition(tubeName, intersect, pos)
        rotName = tubeName+'_rot'
        # zAngle = math.degrees(edge.Curve.AngleXU)
        # Focus1 is on the positive x side, Focus2 on the negative side
        dy = edge.Curve.Focus1[1] - edge.Curve.Focus2[1]
        dx = edge.Curve.Focus1[0] - edge.Curve.Focus2[0]
        zAngle = math.degrees(math.atan2(dy, dx))
        print(f'{self.name} zAngle = {zAngle}')
        # if zAngle < 0:
        #    zAngle += 180
        ET.SubElement(define, 'rotation', {'name': rotName, 'unit': 'deg',
                                           'x': '0', 'y': '0', 'z': str(zAngle)})

        ET.SubElement(intersect, 'rotationref', {'ref': rotName})


class ExtrudedBSpline(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)


class Extruded2Edges(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)

    def export(self):
        global solids

        # form normals to the edges. For case of two edges, sidedness is irrelevant
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
            ny = -e.x/e.y
        normal = Vector(nx, ny, 0).normalize()

        edgeCurves = []  # list of ExtrudedClosedCurve's

        for i, e in enumerate(self.edgeList):  # just TWO edges
            while switch(e.Curve.TypeId):
                if case('Part::GeomLineSegment'):
                    break

                if case('Part::GeomLine'):
                    break

                if case('Part::GeomCircle'):
                    print('Arc of Circle')
                    arcXtruName = self.name + '_c'+str(i)
                    arcSection = ExtrudedArcSection(arcXtruName, [e], self.height)
                    arcSection.export()

                    midpnt = arcSection.midPoint()
                    inside = pointInsideEdge(midpnt, v0, normal)
                    edgeCurves.append([arcXtruName, inside])
                    break

                if case('Part::GeomEllipse'):
                    print('Arc of Ellipse')
                    arcXtruName = self.name+'_e'+str(i)
                    arcSection = ExtrudedEllipticalSection(arcXtruName, [e], self.height)
                    arcSection.export()
                    midpnt = arcSection.midPoint()
                    inside = pointInsideEdge(midpnt, v0, normal)
                    edgeCurves.append([arcXtruName, inside])
                    break

                else:
                    print(f'Arc of {e.Curve.TypeId}')
                    arcXtruName = self.name+'_bs'+str(i)
                    arcSection = ExtrudedClosedCurve(arcXtruName, [e], self.height)
                    arcSection.export()

                    midpnt = arcSection.midPoint()
                    inside = pointInsideEdge(midpnt, v0, normal)
                    edgeCurves.append([arcXtruName, inside])
                    break

        if len(edgeCurves) == 1:
            # change our name to be that of the constructed curve
            # not a violation of the contract of a unique name, since the curve name is based on ours
            self.position = arcSection.position
            self.rotation = arcSection.rotation
            self.name = edgeCurves[0][0]

        else:
            inside0 = edgeCurves[0][1]
            inside1 = edgeCurves[1][1]
            sameSide = (inside0 == inside1)
            if sameSide is False:
                booleanSolid = ET.SubElement(solids, 'union', {'name': self.name})
            else:
                booleanSolid = ET.SubElement(solids, 'subtraction', {'name': self.name})

            area0 = edgelistBBoxArea([self.edgeList[0]])
            area1 = edgelistBBoxArea([self.edgeList[1]])
            if area0 > area1:
                firstSolid = edgeCurves[0][0]
                secondSolid = edgeCurves[1][0]
            else:
                firstSolid = edgeCurves[1][0]
                secondSolid = edgeCurves[0][0]

            ET.SubElement(booleanSolid, 'first', {'ref': firstSolid})
            ET.SubElement(booleanSolid, 'second', {'ref': secondSolid})


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
        print(f'totArea {totArea}, edgeArea {edgeArea}, withoutArea {withoutArea}')

        if totArea < 0.999*(edgeArea + withoutArea):  # 0.99 saftey margin for totArea = edgeArea+withoutArea
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
        for e in self.edgeList:
            if len(e.Vertexes) > 1:
                verts.append(e.Vertexes[0].Point)
        verts.append(verts[0])

        # face = Part.Face(Part.makePolygon(verts))

        edgeCurves = []  # list of ExtrudedClosedCurve's
        verts = []

        for i, e in enumerate(self.edgeList):
            if len(e.Vertexes) > 1:
                verts.append(e.Vertexes[0].Point)
            while switch(e.Curve.TypeId):
                if case('Part::GeomLineSegment'):
                    # verts.append(e.Vertexes[0].Point)
                    break

                if case('Part::GeomLine'):
                    # verts.append(e.Vertexes[0].Point)
                    break

                if case('Part::GeomCircle'):
                    print('Arc of Circle')
                    # this turns out more intricate than meets the eye.
                    # form face without this edge and then test for midpoint
                    # inside that face.
                    arcXtruName = self.name + '_c'+str(i)
                    arcSection = ExtrudedArcSection(arcXtruName, [e], self.height)
                    inside = self.isSubtraction(e)
                    arcSection.export()
                    # this is not general. Needs to be changed
                    # to a test against sidedness of edge of section
                    edgeCurves.append([arcXtruName, inside])
                    break

                if case('Part::GeomEllipse'):
                    print('Arc of Ellipse')
                    arcXtruName = self.name+'_e'+str(i)
                    arcSection = ExtrudedEllipticalSection(arcXtruName, [e], self.height)
                    inside = self.isSubtraction(e)
                    arcSection.export()
                    edgeCurves.append([arcXtruName, inside])
                    break

                else:
                    print(f'Curve {e.Curve.TypeId}')
                    arcXtruName = self.name+'_g'+str(i)
                    arcSection = ExtrudedClosedCurve(arcXtruName, [e], self.height)
                    bsplineVerts = arcSection.discretize()
                    verts = verts + bsplineVerts
                    break

        verts.append(verts[0])
        xtruName = self.name
        if len(edgeCurves) > 0:
            xtruName += '_xtru'
        exportXtru(xtruName, verts, self.height)

        currentSolid = xtruName
        if len(edgeCurves) > 0:
            for i, c in enumerate(edgeCurves):
                curveName = c[0]
                isSubtraction = c[1]
                if i == len(edgeCurves) - 1:
                    name = self.name  # last boolean must have this classes name
                else:
                    name = 'bool' + curveName
                if isSubtraction is False:
                    booleanSolid = ET.SubElement(solids, 'union', {'name': name})
                    ET.SubElement(booleanSolid, 'first', {'ref': currentSolid})
                    ET.SubElement(booleanSolid, 'second', {'ref': curveName})
                elif isSubtraction is True:
                    secondName = curveName+'_s'  # scale solids along z, so it punches thru
                    secondPos = Vector(0, 0, -0.01*self.height)
                    scaleUp(secondName, curveName, 1.10)
                    booleanSolid = ET.SubElement(solids, 'subtraction', {'name': name})
                    ET.SubElement(booleanSolid, 'first', {'ref': currentSolid})
                    ET.SubElement(booleanSolid, 'second', {'ref': secondName})
                    exportPosition(secondName, booleanSolid, secondPos)
                else:  # neither true, not false, must reverse subtraction order
                    secondName = currentSolid+'_s'  # scale solids along z, so it punches thru
                    secondPos = Vector(0, 0, -0.01*self.height)
                    scaleUp(secondName, currentSolid, 1.10)
                    booleanSolid = ET.SubElement(solids, 'subtraction', {'name': name})
                    ET.SubElement(booleanSolid, 'first', {'ref': curveName})
                    ET.SubElement(booleanSolid, 'second', {'ref': secondName})

                currentSolid = name

# Node of a tree that represents the topology of the sketch being exported
# a left_child is a ClosedCurve that is inside of its parent
# a right_sibling is a closedCurve that is outside of its parent


class Node:
    def __init__(self, closedCurve, parent, parity):
        # the nomenclature is redundant, but a reminder that left is a child and right
        # a sibling
        self.parent = parent
        if parent is None:
            self.parity = 0  # if parity is 0, print as union with current solid
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
                # if this node does not have a child, insert it as the left_child
                # otherwise check if it is a child of the child
                if self.left_child is None:
                    self.left_child = Node(closedCurve, self, 1-self.parity)
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
        if i == iSkip or edge.Curve.TypeId == 'Part::GeomLine' or \
           edge.Curve.TypeId == 'Part::GeomLineSegment':
            verts.append(edge.Vertexes[0].Point)
            verts.append(edge.Vertexes[1].Point)
        else:
            verts += edge.discretize(24)
    return verts


def exportTube(name, radius, height):
    global solids

    ET.SubElement(solids, 'tube', {'name': name,
                                   'rmax': str(radius),
                                   'z': str(height),
                                   'startphi': '0',
                                   'deltaphi': '360',
                                   'aunit': 'deg', 'lunit': 'mm'})


def exportXtru(name, vlist, height, zoffset=0):
    global solids

    xtru = ET.SubElement(solids, 'xtru', {'name': name, 'lunit': 'mm'})
    for v in vlist:
        ET.SubElement(xtru, 'twoDimVertex', {'x': str(v.x),
                                             'y': str(v.y)})
    ET.SubElement(xtru, 'section', {'zOrder': '0',
                                    'zPosition': str(zoffset),
                                    'xOffset': '0', 'yOffset': '0',
                                    'scalingFactor': '1'})
    ET.SubElement(xtru, 'section', {'zOrder': '1',
                                    'zPosition': str(height+zoffset),
                                    'xOffset': '0', 'yOffset': '0',
                                    'scalingFactor': '1'})


def getExtrudedCurve(name, edges, height):
    # Return an ExtrudedClosedCurve object of the list of edges

    if len(edges) == 1:  # single edge ==> a closed curve, or curve section
        e = edges[0]
        if len(e.Vertexes) == 1:  # a closed curve
            closed = True
        else:
            closed = False  # a section of a curve

        while switch(e.Curve.TypeId):
            if case('Part::GeomLineSegment'):
                print(' Sketch not closed')
                return ExtrudedClosedCurve(edges, name, height)

            if case('Part::GeomLine'):
                print(' Sketch not closed')
                return ExtrudedClosedCurve(name, edges, height)

            if case('Part::GeomCircle'):
                if closed is True:
                    print('Circle')
                    return ExtrudedCircle(name, edges, height)
                else:
                    print('Arc of Circle')
                    return ExtrudedArcSection(name, edges, height)

            if case('Part::GeomEllipse'):
                if closed is True:
                    print('Ellipse')
                    return ExtrudedEllipse(name, edges, height)
                else:
                    print('Arc of Ellipse')
                    return ExtrudedEllipticalSection(name, edges, height)

            else:
                print(' B spline')
                return ExtrudedClosedCurve(name, edges, height)

    elif len(edges) == 2:  # exactly two edges
        return Extruded2Edges(name, edges, height)
    else:  # three or more edges
        return ExtrudedNEdges(name, edges, height)


class ExtrusionExporter(SolidExporter):

    def __init__(self, extrudeObj):
        global Deviation
        super().__init__(extrudeObj)
        self.sketchObj = extrudeObj.Base
        self.lastName = self.obj.Label  # initial name: might be modified later
        Deviation = self.obj.ViewObject.Deviation/100.0

    def position(self):
        # This presumes export has been called before postion()
        # Things will be screwed up, other wise
        return self._position

    def rotation(self):
        # This presumes export has been called before postion()
        # Things will be screwed up, other wise
        return self._rotation

    def name(self):
        # override default name in SolidExporter
        prefix = ''
        if self.lastName[0].isdigit():
            prefix = 'X'
        return prefix + self.lastName

    def export(self):

        sketchObj = self.sketchObj
        extrudeObj = self.obj
        eName = self.name()

        sortededges = Part.sortEdges(sketchObj.Shape.Edges)
        # sort by largest area to smallest area
        sortEdgelistsByBoundingBoxArea(sortededges)
        # getCurve returns one of the sub classes of ClosedCurve that
        # knows how to export the specifc closed edges
        # Make names based on Extrude name
        # curves = [getCurve(edges, extrudeObj.Label + str(i)) for i, edges
        # in enumerate(sortededges)]
        if extrudeObj.Symmetric is True:
            height = extrudeObj.LengthFwd.Value
        else:
            height = extrudeObj.LengthFwd.Value + extrudeObj.LengthRev.Value
        # get a list of curves (instances of class ClosedCurve) for each
        # set of closed edges
        curves = [getExtrudedCurve(eName+str(i), edges, height)
                  for i, edges in enumerate(sortededges)]
        # build a generalized binary tree of closed curves.
        root = Node(curves[0], None, 0)
        for c in curves[1:]:
            root.insert(c)

        # Traverse the tree. The list returned is a list of [Node, parity],
        # where parity = 0, says add to parent, 1 mean subtract
        lst = root.preOrderTraversal(root)
        rootnode = lst[0][0]
        rootCurve = rootnode.closedCurve
        rootCurve.export()  # a curve is created with a unique name
        firstName = rootCurve.name
        booleanName = firstName

        rootPos = rootCurve.position
        rootRot = rootCurve.rotation  # for now consider only angle of rotation about z-axis

        for c in lst[1:]:
            node = c[0]
            parity = c[1]
            curve = node.closedCurve
            curve.export()
            if parity == 0:
                boolType = 'union'
                secondName = curve.name
                secondPos = curve.position
            else:
                boolType = 'subtraction'
                secondName = curve.name+'_s'  # scale solids along z, so it punches thru
                scaleUp(secondName, curve.name, 1.10)
                secondPos = curve.position - Vector(0, 0, 0.01*height)

            booleanName = curve.name + '_bool'
            boolSolid = ET.SubElement(solids, boolType, {'name': booleanName})
            ET.SubElement(boolSolid, 'first', {'ref': firstName})
            ET.SubElement(boolSolid, 'second', {'ref': secondName})
            relativePosition = secondPos - rootPos
            zAngle = curve.rotation[2] - rootRot[2]
            posName = curve.name+'_pos'
            rotName = curve.name+'_rot'
            exportDefine(posName, relativePosition)  # position of second relative to first
            ET.SubElement(define, 'rotation', {'name': rotName, 'unit': 'deg',
                                               'x': '0', 'y': '0',
                                               'z': str(zAngle)})

            ET.SubElement(boolSolid, 'positionref', {'ref': posName})
            ET.SubElement(boolSolid, 'rotationref', {'ref': rotName})
            firstName = booleanName

        self.lastName = booleanName  # our name should the name f the last solid created

        # Because the position of each closed curve might not be at the
        # origin, whereas primitives (tubes, cones, etc, are created centered at
        # the origin, we need to shift the position of the very first node by its
        # position, in addition to the shift by the Extrusion placement
        extrudeObj = self.obj
        extrudePosition = extrudeObj.Placement.Base
        if extrudeObj.Symmetric is False:
            if extrudeObj.Reversed is False:
                zoffset = Vector(0, 0, extrudeObj.LengthRev.Value)
            else:
                zoffset = Vector(0, 0, extrudeObj.LengthFwd.Value)
        else:
            zoffset = Vector(0, 0, extrudeObj.LengthFwd.Value/2)

        angles = quaternion2XYZ(extrudeObj.Placement.Rotation)
        # need to add rotations of elliptical tubes. Assume extrusion is on z-axis
        # Probably wil not work in general
        zAngle = angles[2] + rootRot[2]
        rootPos = rotatedPos(rootCurve, extrudeObj.Placement.Rotation)
        print(rootPos)
        Base = extrudePosition + rootPos - zoffset

        rotX = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), angles[0])
        rotY = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), angles[1])
        rotZ = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), zAngle)

        rot = rotZ*rotY*rotX

        placement = FreeCAD.Placement(Base, FreeCAD.Rotation(rot))
        self._position = placement.Base
        self._rotation = placement.Rotation
