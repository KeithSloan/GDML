# Mon Dec  6 08:49:56 AM PST 2021
# **************************************************************************
# *                                                                        * 
# *   Copyright (c) 2019 Keith Sloan <keith@sloan-home.co.uk>              *
# *             (c) 2020 Dam Lambert                                       *
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
from . import exportExtrusion

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
    global defineCnt, LVcount, PVcount, POScount, ROTcount
    global gxml

    defineCnt = LVcount = PVcount = POScount = ROTcount = 1

    gdml = initGDML()
    define = ET.SubElement(gdml, 'define')
    materials = ET.SubElement(gdml, 'materials')
    solids = ET.SubElement(gdml, 'solids')
    structure = ET.SubElement(gdml, 'structure')
    setup = ET.SubElement(gdml, 'setup', {'name': 'Default', 'version': '1.0'})
    gxml = ET.Element('gxml')

    exportExtrusion.setGlobals(define, materials, solids)

    return structure


def defineMaterials():
    # Replaced by loading Default
    # print("Define Materials")
    global materials


def exportDefine(name, v):
    global define
    ET.SubElement(define, 'position', {'name': name, 'unit': 'mm',
                                       'x': str(v[0]), 'y': str(v[1]), 'z': str(v[2])})


def exportDefineVertex(name, v, index):
    global define
    ET.SubElement(define, 'position', {'name': name + str(index),
                                       'unit': 'mm', 'x': str(v.X), 'y': str(v.Y), 'z': str(v.Z)})


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

    R = Rz Ry Rx = [
    [cos(b)*cos(g), cos(g)*sin(a)*sin(b) - cos(a)*sin(g), cos(a)*cos(g)*sin(b) + sin(a)*sin(g)]
    [cos(b)*sin(g), sin(a)*sin(b)*sin(g) + cos(a)*cos(g), cos(a)*sin(b)*sin(g) - cos(g)*sin(a)]
    [-sin(b),        cos(b)*sin(a),                       ,  cos(a)*cos(b)]]

    To get the angles b(eta), g(amma) for rotations around y, z axes, transform the unit vector (1,0,0)
    [x,y,z] = Q*(1,0,0) = R*(1,0,0) ==>
    x = cos(b)*cos(g)
    y = cos(b)*sin(g)
    z = -sin(b)

    ==>   g = atan2(y, x) = atan2(sin(b)*sin(g), cos(g)*sin(b)) = atan2(sin(g), cos(g))
    then  b = atan2(-z*cos(g), x) = atan2(sin(b)*cos(g), cos(b)*cos(g)] = atan2(sin(b), cos(b))

    Once b, g are found, a(lpha) can be found by transforming (0, 0, 1), or (0,1,0)
    Since now g, b are known, one can form the inverses of Ry, Rz:
    Rz^-1 = Rz(-g)
    Ry^-1 = Ry(-b)

    Now R*(0,0,1) = Rz*Ry*Rz(0,1,0) = (x, y, z)
    multiply both sides by Ry^-1 Rz^-1:
    Ry^-1 Rz^-1 Rz Ry Rx (0,1,0) = Rx (0,1,0) = Ry(-b) Rz(-g) (x, y, z) = (xp, yp, zp)
    ==>
    xp = 0
    yp = cos(a)
    zp = sin(a)

    and a = atan2(zp, yp)
    '''
    v = rot*Vector(1, 0, 0)
    g = math.atan2(v.y, v.x)
    b = math.atan2(-v.z*math.cos(g), v.x)
    Ryinv = FreeCAD.Rotation(Vector(0, 1, 0), math.degrees(-b))
    Rzinv = FreeCAD.Rotation(Vector(0, 0, 1), math.degrees(-g))
    vp = Ryinv*Rzinv*rot*Vector(0, 1, 0)
    a = math.atan2(vp.z, vp.y)

    print([math.degrees(a), math.degrees(b), math.degrees(g)])
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
    ET.SubElement(lvol, 'materialref', {'ref': 'SSteel0x56070ee87d10'})
    ET.SubElement(lvol, 'solidref', {'ref': solidName})
    # Place child physical volume in World Volume
    phys = ET.SubElement(lvol, 'physvol', {'name': 'PV-'+name})
    ET.SubElement(phys, 'volumeref', {'ref': pvName})
    x = pos[0]
    y = pos[1]
    z = pos[2]
    if x != 0 and y != 0 and z != 0:
        posName = 'Pos'+name+str(POScount)
        POScount += 1
        ET.SubElement(phys, 'positionref', {'name': posName})
        ET.SubElement(define, 'position', {'name': posName, 'unit': 'mm',
                                           'x': str(x), 'y': str(y), 'z': str(z)})
    # Realthunders enhancement to toEuler ixyz is intrinsic
    rot = obj.Placement.Rotation
    if hasattr(rot, 'toEulerAngles'):
        angles = rot.toEulerAngles('ixyz')
        angles = (angles[2], angles[1], angles[0])
    else:
        print('Export of rotation probably wrong')
        print('Needs toEulerAngles function - Use LinkStage 3')
        angles = rot.toEuler()
    GDMLShared.trace("Angles")
    GDMLShared.trace(angles)
    angles = quaternion2XYZ(rot)
    a0 = angles[0]
    # print(a0)
    a1 = angles[1]
    # print(a1)
    a2 = angles[2]
    # print(a2)
    if a0 != 0 and a1 != 0 and a2 != 0:
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


def processBoxObject(obj, addVolsFlag):
    # Needs unique Name
    # This for non GDML Box

    boxName = obj.Name

    ET.SubElement(solids, 'box', {'name': boxName,
                                  'x': str(obj.Length.Value),
                                  'y': str(obj.Width.Value),
                                  'z': str(obj.Height.Value),
                                  'lunit': 'mm'})
    if addVolsFlag:
        # Adjustment for position in GDML
        delta = FreeCAD.Vector(obj.Length.Value / 2,
                               obj.Width.Value / 2,
                               obj.Height.Value / 2)

        createAdjustedLVandPV(obj, obj.Name, boxName, delta)
    return(boxName)


def processCylinderObject(obj, addVolsFlag):
    # Needs unique Name
    # This is for non GDML cylinder/tube
    cylName = obj.Name
    ET.SubElement(solids, 'tube', {'name': cylName,
                                   'rmax': str(obj.Radius.Value),
                                   'deltaphi': str(float(obj.Angle)),
                                   'aunit': obj.aunit,
                                   'z': str(obj.Height.Value),
                                   'lunit': 'mm'})
    if addVolsFlag:
        # Adjustment for position in GDML
        delta = FreeCAD.Vector(0, 0, obj.Height.Value / 2)
        createAdjustedLVandPV(obj, obj.Name, cylName, delta)
    return(cylName)


def processConeObject(obj, addVolsFlag):
    # Needs unique Name
    coneName = obj.Name
    ET.SubElement(solids, 'cone', {
       'name': coneName,
       'rmax1': str(obj.Radius1.Value),
       'rmax2': str(obj.Radius2.Value),
       'deltaphi': str(float(obj.Angle)),
       'aunit': obj.aunit,
       'z': str(obj.Height.Value),
       'lunit': 'mm'})
    if addVolsFlag:
        # Adjustment for position in GDML
        delta = FreeCAD.Vector(0, 0, obj.Height.Value / 2)
        createAdjustedLVandPV(obj, obj.Name, coneName, delta)
    return(coneName)


def processSection(obj, addVolsflag):
    # print("Process Section")
    ET.SubElement(solids, 'section', {
       'vertex1': obj.v1,
       'vertex2': obj.v2,
       'vertex3': obj.v3, 'vertex4': obj.v4,
       'type': obj.vtype})


def processSphereObject(obj, addVolsFlag):
    # Needs unique Name
    # modif lambda (if we change the name here, each time we import and export the file, the name will be change 
    # sphereName = 'Sphere' + obj.Name
    sphereName = obj.Name

    ET.SubElement(solids, 'sphere', {
       'name': sphereName,
       'rmax': str(obj.Radius.Value),
       'starttheta': str(90.-float(obj.Angle2)),
       'deltatheta': str(float(obj.Angle2-obj.Angle1)),
       'deltaphi': str(float(obj.Angle3)),
       'aunit': obj.aunit,
       'lunit': 'mm'})
    if addVolsFlag:
        createLVandPV(obj, obj.Name, sphereName)
    return(sphereName)


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


def addPhysVolPlacement(obj, xmlVol, volName):
    # ??? Is volName not obj.Label after correction
    # Get proper Volume Name
    refName = cleanVolName(obj, volName)
    # GDMLShared.setTrace(True)
    GDMLShared.trace("Add PhysVol to Vol : "+refName)
    # print(ET.tostring(xmlVol))
    if xmlVol is not None:
        if not hasattr(obj, 'CopyNumber'):
            pvol = ET.SubElement(xmlVol, 'physvol', {'name': 'PV-' + volName})
        else:
            cpyNum = str(obj.CopyNumber)
            GDMLShared.trace('CopyNumber : '+cpyNum)
            pvol = ET.SubElement(xmlVol, 'physvol', {'copynumber': cpyNum})
        ET.SubElement(pvol, 'volumeref', {'ref': refName})
        processPosition(obj, pvol)
        processRotation(obj, pvol)
        if hasattr(obj, 'GDMLscale'):
            scaleName = refName+'scl'
            ET.SubElement(pvol, 'scale', {'name': scaleName,
                                          'x': str(obj.GDMLscale[0]),
                                          'y': str(obj.GDMLscale[1]),
                                          'z': str(obj.GDMLscale[2])})

        return pvol


def exportPosition(name, xml, pos):
    global POScount
    GDMLShared.trace('export Position')
    GDMLShared.trace(pos)
    x = pos[0]
    y = pos[1]
    z = pos[2]
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


def exportRotation(name, xml, Rotation):
    print('Export Rotation')
    global ROTcount
    if Rotation.Angle != 0:
        # Realthunders enhancement to toEuler ixyz is intrinsic
        if hasattr(Rotation, 'toEulerAngles'):
            angles = Rotation.toEulerAngles('ixyz')
            angles = (angles[2], angles[1], angles[0])
        else:
            print('Export of rotation probably wrong')
            print('Needs toEulerAngles function - Use LinkStage 3')
            angles = Rotation.toEuler()
        GDMLShared.trace("Angles")
        GDMLShared.trace(angles)
        a0 = angles[0]
        print(a0)
        a1 = angles[1]
        print(a1)
        a2 = angles[2]
        print(a2)
        if a0 != 0 or a1 != 0 or a2 != 0:
            rotName = 'R-'+name+str(ROTcount)
            ROTcount += 1
            rotxml = ET.SubElement(define, 'rotation', {'name': rotName,
                                                        'unit': 'deg'})
            if abs(a2) != 0:
                rotxml.attrib['x'] = str(-a2)
            if abs(a1) != 0:
                rotxml.attrib['y'] = str(-a1)
            if abs(a0) != 0:
                rotxml.attrib['z'] = str(-a0)
            ET.SubElement(xml, 'rotationref', {'ref': rotName})


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
            processPosition(obj, pvol)
            processRotation(obj, pvol)
        else:
            print('Root/World Volume')


def addVolRef(volxml, volName, obj, solidName=None):
    # Pass material as Boolean
    material = getMaterial(obj)
    if solidName is None:
        solidName = nameOfGDMLobject(obj)
    ET.SubElement(volxml, 'materialref', {'ref': material})
    ET.SubElement(volxml, 'solidref', {'ref': solidName})
    ET.SubElement(gxml, 'volume', {'name': volName, 'material': material})
    if hasattr(obj.ViewObject, 'ShapeColor') and volName != WorldVOL:
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


def processGDMLArb8Object(obj):
    # Needs unique Name
    # Remove leading GDMLArb8 from name on export
    arb8Name = nameOfGDMLobject(obj)

    solid = ET.SubElement(solids, 'arb8', {'name': arb8Name,
                                           'v1x': str(obj.v1x),
                                           'v1y': str(obj.v1y),
                                           'v2x': str(obj.v2x),
                                           'v2y': str(obj.v2y),
                                           'v3x': str(obj.v3x),
                                           'v3y': str(obj.v3y),
                                           'v4x': str(obj.v4x),
                                           'v4y': str(obj.v4y),
                                           'v5x': str(obj.v5x),
                                           'v5y': str(obj.v5y),
                                           'v6x': str(obj.v6x),
                                           'v6y': str(obj.v6y),
                                           'v7x': str(obj.v7x),
                                           'v7y': str(obj.v7y),
                                           'v8x': str(obj.v8x),
                                           'v8y': str(obj.v8y),
                                           'dz': str(obj.dz),
                                           'lunit': obj.lunit})
    return solid, arb8Name


def processGDMLBoxObject(obj):
    # Needs unique Name
    # Remove leading GDMLBox_ from name on export
    boxName = nameOfGDMLobject(obj)

    solid = ET.SubElement(solids, 'box', {'name': boxName,
                                          'x': str(obj.x),
                                          'y': str(obj.y),
                                          'z': str(obj.z),
                                          'lunit': obj.lunit})
    return solid, boxName


def processGDMLConeObject(obj):
    # Needs unique Name
    # Remove leading GDMLTube_ from name on export
    coneName = nameOfGDMLobject(obj)
    solid = ET.SubElement(solids, 'cone', {'name': coneName,
                                           'rmin1': str(obj.rmin1),
                                           'rmin2': str(obj.rmin2),
                                           'rmax1': str(obj.rmax1),
                                           'rmax2': str(obj.rmax2),
                                           'startphi': str(obj.startphi),
                                           'deltaphi': str(obj.deltaphi),
                                           'aunit': obj.aunit,
                                           'z': str(obj.z),
                                           'lunit': obj.lunit})
    # modif 'mm' -> obj.lunit
    return solid, coneName


def processGDMLCutTubeObject(obj):
    # Needs unique Name
    # Remove leading GDML text from name
    cTubeName = nameOfGDMLobject(obj)
    solid = ET.SubElement(solids, 'cutTube', {'name': cTubeName,
                                              'rmin': str(obj.rmin),
                                              'rmax': str(obj.rmax),
                                              'startphi': str(obj.startphi),
                                              'deltaphi': str(obj.deltaphi),
                                              'aunit': obj.aunit,
                                              'z': str(obj.z),
                                              'highX': str(obj.highX),
                                              'highY': str(obj.highY),
                                              'highZ': str(obj.highZ),
                                              'lowX': str(obj.lowX),
                                              'lowY': str(obj.lowY),
                                              'lowZ': str(obj.lowZ),
                                              'lunit': obj.lunit})
    return solid, cTubeName


def processGDMLElConeObject(obj):
    GDMLShared.trace('Elliptical Cone')
    elconeName = nameOfGDMLobject(obj)
    solid = ET.SubElement(solids, 'elcone', {'name': elconeName,
                                             'dx': str(obj.dx),
                                             'dy': str(obj.dy),
                                             'zcut': str(obj.zcut),
                                             'zmax': str(obj.zmax),
                                             'lunit': str(obj.lunit)})

    return solid, elconeName


def processGDMLEllipsoidObject(obj):
    # Needs unique Name
    ellipsoidName = nameOfGDMLobject(obj)
    solid = ET.SubElement(solids, 'ellipsoid', {'name': ellipsoidName,
                                                'ax': str(obj.ax),
                                                'by': str(obj.by),
                                                'cz': str(obj.cz),
                                                'zcut1': str(obj.zcut1),
                                                'zcut2': str(obj.zcut2),
                                                'lunit': obj.lunit})
    return solid, ellipsoidName


def processGDMLElTubeObject(obj):
    # Needs unique Name
    # flag needed for boolean otherwise parse twice
    eltubeName = nameOfGDMLobject(obj)
    solid = ET.SubElement(solids, 'eltube', {'name': eltubeName,
                                             'dx': str(obj.dx),
                                             'dy': str(obj.dy),
                                             'dz': str(obj.dz),
                                             'lunit': obj.lunit})
    return solid, eltubeName


def processGDMLHypeObject(obj):
    # Needs unique Name
    # Remove leading GDMLTube_ from name on export
    hypeName = nameOfGDMLobject(obj)
    solid = ET.SubElement(solids, 'hype', {'name': hypeName,
                                           'rmin': str(obj.rmin),
                                           'rmax': str(obj.rmax),
                                           'z': str(obj.z),
                                           'inst': str(obj.inst),
                                           'outst': str(obj.outst),
                                           'aunit': obj.aunit,
                                           'lunit': obj.lunit})
    # modif 'mm' -> obj.lunit
    return solid, hypeName


def processGDMLParaboloidObject(obj):
    # Needs unique Name
    # Remove leading GDMLTube_ from name on export
    solidName = nameOfGDMLobject(obj)
    solid = ET.SubElement(solids, 'paraboloid', {'name': solidName,
                                                 'rlo': str(obj.rlo),
                                                 'rhi': str(obj.rhi),
                                                 'dz': str(obj.dz),
                                                 'lunit': obj.lunit})
    # modif 'mm' -> obj.lunit
    return solid, solidName


def processGDMLOrbObject(obj):
    # Needs unique Name
    # flag needed for boolean otherwise parse twice
    orbName = nameOfGDMLobject(obj)
    solid = ET.SubElement(solids, 'orb', {'name': orbName,
                                          'r': str(obj.r),
                                          'lunit': obj.lunit})
    return solid, orbName


def processGDMLParaObject(obj):
    # Needs unique Name
    # flag needed for boolean otherwise parse twice
    paraName = nameOfGDMLobject(obj)
    solid = ET.SubElement(solids, 'para', {'name': paraName,
                                           'x': str(obj.x),
                                           'y': str(obj.y),
                                           'z': str(obj.z),
                                           'alpha': str(obj.alpha),
                                           'theta': str(obj.theta),
                                           'phi': str(obj.phi),
                                           'aunit': str(obj.aunit),
                                           'lunit': obj.lunit})
    return solid, paraName


def processGDMLPolyconeObject(obj):
    # Needs unique Name
    # flag needed for boolean otherwise parse twice
    # polyconeName = 'Cone' + obj.Name
    polyconeName = nameOfGDMLobject(obj)
    cone = ET.SubElement(solids, 'polycone', {'name': polyconeName,
                                              'startphi': str(obj.startphi),
                                              'deltaphi': str(obj.deltaphi),
                                              'aunit': obj.aunit,
                                              'lunit': obj.lunit})
    for zplane in obj.OutList:
        ET.SubElement(cone, 'zplane', {'rmin': str(zplane.rmin),
                                       'rmax': str(zplane.rmax),
                                       'z': str(zplane.z)})
    return cone, polyconeName


def processGDMLGenericPolyconeObject(obj):
    polyconeName = nameOfGDMLobject(obj)
    cone = ET.SubElement(solids, 'genericPolycone', {
       'name': polyconeName,
       'startphi': str(obj.startphi),
       'deltaphi': str(obj.deltaphi),
       'aunit': obj.aunit,
       'lunit': obj.lunit})
    for rzpoint in obj.OutList:
        ET.SubElement(cone, 'rzpoint', {'r': str(rzpoint.r),
                                        'z': str(rzpoint.z)})
    return cone, polyconeName


def processGDMLGenericPolyhedraObject(obj):
    polyhedraName = nameOfGDMLobject(obj)
    polyhedra = ET.SubElement(solids, 'genericPolyhedra', {
       'name': polyhedraName,
       'startphi': str(obj.startphi),
       'deltaphi': str(obj.deltaphi),
       'numsides': str(obj.numsides),
       'aunit': obj.aunit,
       'lunit': obj.lunit})
    for rzpoint in obj.OutList:
        ET.SubElement(polyhedra, 'rzpoint', {'r': str(rzpoint.r),
                                             'z': str(rzpoint.z)})
    return polyhedra, polyhedraName


def processGDMLPolyhedraObject(obj):
    # Needs unique Name
    # flag needed for boolean otherwise parse twice
    # polyconeName = 'Cone' + obj.Name
    GDMLShared.trace('export Polyhedra')
    polyhedraName = nameOfGDMLobject(obj)
    poly = ET.SubElement(solids, 'polyhedra', {'name': polyhedraName,
                                               'startphi': str(obj.startphi),
                                               'deltaphi': str(obj.deltaphi),
                                               'numsides': str(obj.numsides),
                                               'aunit': obj.aunit,
                                               'lunit': obj.lunit})
    for zplane in obj.OutList:
        ET.SubElement(poly, 'zplane', {'rmin': str(zplane.rmin),
                                       'rmax': str(zplane.rmax),
                                       'z': str(zplane.z)})
    return poly, polyhedraName


def processGDMLQuadObject(obj):
    GDMLShared.trace("GDMLQuadrangular")
    ET.SubElement(solids, 'quadrangular', {'vertex1': obj.v1,
                                           'vertex2': obj.v2,
                                           'vertex3': obj.v3,
                                           'vertex4': obj.v4,
                                           'type': obj.vtype})


def processGDMLSphereObject(obj):
    # Needs unique Name
    sphereName = nameOfGDMLobject(obj)

    solid = ET.SubElement(solids, 'sphere', {'name': sphereName,
                                             'rmin': str(obj.rmin),
                                             'rmax': str(obj.rmax),
                                             'startphi': str(obj.startphi),
                                             'deltaphi': str(obj.deltaphi),
                                             'starttheta': str(obj.starttheta),
                                             'deltatheta': str(obj.deltatheta),
                                             'aunit': obj.aunit,
                                             'lunit': obj.lunit})
    return solid, sphereName


def processGDMLTessellatedObject(obj):
    # Needs unique Name
    # Need to output unique define positions
    # Need to create set of positions

    tessName = nameOfGDMLobject(obj)
    # Use more readable version
    tessVname = tessName + '_'
    # print(dir(obj))
    vertexHashcodeDict = {}

    tess = ET.SubElement(solids, 'tessellated', {'name': tessName})
    for i, v in enumerate(obj.Shape.Vertexes):
        vertexHashcodeDict[v.hashCode()] = i
        exportDefineVertex(tessVname, v, i)

    for f in obj.Shape.Faces:
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
            i3 = vertexHashcodeDict[vertexes[3].hashCode()]
            ET.SubElement(tess, 'quadrangular', {
               'vertex1': tessVname+str(i0),
               'vertex2': tessVname+str(i1),
               'vertex3': tessVname+str(i2),
               'vertex4': tessVname+str(i3),
               'type': 'ABSOLUTE'})

    return tess, tessName


def processGDMLTetraObject(obj):
    tetraName = nameOfGDMLobject(obj)
    v1Name = tetraName + 'v1'
    v2Name = tetraName + 'v2'
    v3Name = tetraName + 'v3'
    v4Name = tetraName + 'v4'
    exportDefine(v1Name, obj.v1)
    exportDefine(v2Name, obj.v2)
    exportDefine(v3Name, obj.v3)
    exportDefine(v4Name, obj.v4)

    tetra = ET.SubElement(solids, 'tet', {'name': tetraName,
                                          'vertex1': v1Name,
                                          'vertex2': v2Name,
                                          'vertex3': v3Name,
                                          'vertex4': v4Name})
    return tetra, tetraName


def processGDMLTetrahedronObject(obj):
    global structure
    global solids
    tetrahedronName = nameOfGDMLobject(obj)
    print('Len Tet' + str(len(obj.Proxy.Tetra)))
    count = 0
    for t in obj.Proxy.Tetra:
        tetraName = 'Tetra_' + str(count)
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
        ET.SubElement(lvol, 'materialref', {'ref': obj.material})
        ET.SubElement(lvol, 'solidref', {'ref': tetraName})
        count += 1

    # Now put out Assembly
    assembly = ET.SubElement(structure, 'assembly', {'name': tetrahedronName})
    count = 0
    for t in obj.Proxy.Tetra:
        lvName = 'LVtetra' + str(count)
        physvol = ET.SubElement(assembly, 'physvol')
        ET.SubElement(physvol, 'volumeref', {'ref': lvName})
        # ET.SubElement(physvol, 'position')
        # ET.SubElement(physvol, 'rotation')
        count += 1

    return assembly, tetrahedronName


def processGDMLTorusObject(obj):
    torusName = nameOfGDMLobject(obj)
    print(f'Torus: {torusName}')
    torus = ET.SubElement(solids, 'torus', {'name': torusName,
                                            'rmin': str(obj.rmin),
                                            'rmax': str(obj.rmax),
                                            'rtor': str(obj.rtor),
                                            'startphi': str(obj.startphi),
                                            'deltaphi': str(obj.deltaphi),
                                            'aunit': obj.aunit,
                                            'lunit': obj.lunit})

    return torus, torusName


def processGDMLTrapObject(obj):
    # Needs unique Name
    trapName = nameOfGDMLobject(obj)
    trap = ET.SubElement(solids, 'trap', {'name': trapName,
                                          'z': str(obj.z),
                                          'theta': str(obj.theta),
                                          'phi': str(obj.phi),
                                          'x1': str(obj.x1),
                                          'x2': str(obj.x2),
                                          'x3': str(obj.x3),
                                          'x4': str(obj.x4),
                                          'y1': str(obj.y1),
                                          'y2': str(obj.y2),
                                          'alpha1': str(obj.alpha),
                                          'alpha2': str(obj.alpha),
                                          'aunit': obj.aunit,
                                          'lunit': obj.lunit})
    return trap, trapName


def processGDMLTrdObject(obj):
    # Needs unique Name
    trdName = nameOfGDMLobject(obj)
    trd = ET.SubElement(solids, 'trd', {'name': trdName,
                                        'z': str(obj.z),
                                        'x1': str(obj.x1),
                                        'x2': str(obj.x2),
                                        'y1': str(obj.y1),
                                        'y2': str(obj.y2),
                                        'lunit': obj.lunit})
    return trd, trdName

def processGDMLTriangle(obj):
    # print("Process GDML Triangle")
    ET.SubElement(solids, 'triangular', {'vertex1': obj.v1,
                                         'vertex2': obj.v2, 'vertex3': obj.v3,
                                         'type': obj.vtype})


def processGDMLTubeObject(obj):
    # Needs unique Name
    # flag needed for boolean otherwise parse twice
    tubeName = nameOfGDMLobject(obj)
    print(f'Tube: {tubeName}')
    tube = ET.SubElement(solids, 'tube', {'name': tubeName,
                                          'rmin': str(obj.rmin),
                                          'rmax': str(obj.rmax),
                                          'startphi': str(obj.startphi),
                                          'deltaphi': str(obj.deltaphi),
                                          'aunit': obj.aunit,
                                          'z': str(obj.z),
                                          'lunit': obj.lunit})
    return tube, tubeName


def processGDMLTwistedboxObject(obj):

    solidName = nameOfGDMLobject(obj)

    solid = ET.SubElement(solids, 'twistedbox', {'name': solidName,
                                                 'PhiTwist': str(obj.PhiTwist),
                                                 'x': str(obj.x),
                                                 'y': str(obj.y),
                                                 'z': str(obj.z),
                                                 'aunit': str(obj.aunit),
                                                 'lunit': obj.lunit})
    return solid, solidName


def processGDMLTwistedtrdObject(obj):
    # Needs unique Name
    # flag needed for boolean otherwise parse twice
    solidName = nameOfGDMLobject(obj)
    solid = ET.SubElement(solids, 'twistedtrd', {'name': solidName,
                                                 'PhiTwist': str(obj.PhiTwist),
                                                 'x1': str(obj.x1),
                                                 'x2': str(obj.x2),
                                                 'y1': str(obj.y1),
                                                 'y2': str(obj.y2),
                                                 'z': str(obj.z),
                                                 'aunit': str(obj.aunit),
                                                 'lunit': obj.lunit})
    return solid, solidName


def processGDMLTwistedtrapObject(obj):
    # Needs unique Name
    # flag needed for boolean otherwise parse twice
    solidName = nameOfGDMLobject(obj)
    solid = ET.SubElement(solids, 'twistedtrap', {'name': solidName,
                                                  'PhiTwist': str(obj.PhiTwist),
                                                  'x1': str(obj.x1),
                                                  'x2': str(obj.x2),
                                                  'y1': str(obj.y1),
                                                  'y2': str(obj.y2),
                                                  'x3': str(obj.x3),
                                                  'x4': str(obj.x4),
                                                  'z': str(obj.z),
                                                  'Theta': str(obj.Theta),
                                                  'Phi': str(obj.Phi),
                                                  'Alph': str(obj.Alph),
                                                  'aunit': str(obj.aunit),
                                                  'lunit': obj.lunit})
    return solid, solidName


def processGDMLTwistedtubsObject(obj):
    # Needs unique Name
    # flag needed for boolean otherwise parse twice
    solidName = nameOfGDMLobject(obj)
    solid = ET.SubElement(solids, 'twistedtubs', {
       'name': solidName,
       'twistedangle': str(obj.twistedangle),
       'endinnerrad': str(obj.endinnerrad),
       'endouterrad': str(obj.endouterrad),
       'zlen': str(obj.zlen),
       'phi': str(obj.phi),
       'aunit': str(obj.aunit),
       'lunit': obj.lunit})
    return solid, solidName


def processGDMLXtruObject(obj):
    # Needs unique Name
    xtruName = nameOfGDMLobject(obj)

    xtru = ET.SubElement(solids, 'xtru', {'name': xtruName,
                                          'lunit': obj.lunit})
    for items in obj.OutList:
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
    return xtru, xtruName


def processGDML2dVertex(obj):
    # print("Process 2d Vertex")
    ET.SubElement(solids, 'twoDimVertex', {'x': obj.x, 'y': obj.y})


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


def processGDMLSolid(obj):
    # Deal with GDML Solids first
    # Deal with FC Objects that convert
    # print(dir(obj))
    # print(dir(obj.Proxy))
    print(obj.Proxy.Type)
    while switch(obj.Proxy.Type):
        if case("GDMLArb8"):
            # print("      GDMLArb8")
            return(processGDMLArb8Object(obj))

        if case("GDMLBox"):
            # print("      GDMLBox")
            return(processGDMLBoxObject(obj))

        if case("GDMLCone"):
            # print("      GDMLCone")
            return(processGDMLConeObject(obj))

        if case("GDMLcutTube"):
            # print("      GDMLcutTube")
            return(processGDMLCutTubeObject(obj))

        if case("GDMLElCone"):
            # print("      GDMLElCone")
            return(processGDMLElConeObject(obj))

        if case("GDMLEllipsoid"):
            # print("      GDMLEllipsoid")
            return(processGDMLEllipsoidObject(obj))

        if case("GDMLElTube"):
            # print("      GDMLElTube")
            return(processGDMLElTubeObject(obj))

        if case("GDMLHype"):
            # print("      GDMLHype")
            return(processGDMLHypeObject(obj))

        if case("GDMLOrb"):
            # print("      GDMLOrb")
            return(processGDMLOrbObject(obj))

        if case("GDMLPara"):
            # print("      GDMLPara")
            return(processGDMLParaObject(obj))

        if case("GDMLParaboloid"):
            # print("      GDMLParaboloid")
            return(processGDMLParaboloidObject(obj))

        if case("GDMLPolycone"):
            # print("      GDMLPolycone")
            return(processGDMLPolyconeObject(obj))

        if case("GDMLGenericPolycone"):
            # print("      GDMLGenericPolycone")
            return(processGDMLGenericPolyconeObject(obj))

        if case("GDMLPolyhedra"):
            # print("      GDMLPolyhedra")
            return(processGDMLPolyhedraObject(obj))

        if case("GDMLGenericPolyhedra"):
            # print("      GDMLPolyhedra")
            return(processGDMLGenericPolyhedraObject(obj))

        if case("GDMLSphere"):
            # print("      GDMLSphere")
            return(processGDMLSphereObject(obj))

        if case("GDMLTessellated"):
            # print("      GDMLTessellated")
            ret = processGDMLTessellatedObject(obj)
            return ret

        if case("GDMLGmshTessellated"):
            # print("      GDMLGmshTessellated")
            # export GDMLTessellated & GDMLGmshTesssellated should be the same
            return(processGDMLTessellatedObject(obj))

        if case("GDMLTetra"):
            # print("      GDMLTetra")
            return(processGDMLTetraObject(obj))

        if case("GDMLTetrahedron"):
            print("      GDMLTetrahedron")
            return(processGDMLTetrahedronObject(obj))

        if case("GDMLTorus"):
            print("      GDMLTorus")
            return(processGDMLTorusObject(obj))

        if case("GDMLTrap"):
            # print("      GDMLTrap")
            return(processGDMLTrapObject(obj))

        if case("GDMLTrd"):
            # print("      GDMLTrd")
            return(processGDMLTrdObject(obj))

        if case("GDMLTube"):
            # print("      GDMLTube")
            return(processGDMLTubeObject(obj))

        if case("GDMLTwistedbox"):
            # print("      GDMLTwistedbox")
            return(processGDMLTwistedboxObject(obj))

        if case("GDMLTwistedtrap"):
            # print("      GDMLTwistedtrap")
            return(processGDMLTwistedtrapObject(obj))

        if case("GDMLTwistedtrd"):
            # print("      GDMLTwistedbox")
            return(processGDMLTwistedtrdObject(obj))

        if case("GDMLTwistedtubs"):
            # print("      GDMLTwistedbox")
            return(processGDMLTwistedtubsObject(obj))

        if case("GDMLXtru"):
            # print("      GDMLXtru")
            return(processGDMLXtruObject(obj))

        print("Not yet Handled")
        break


def processSolid(obj, addVolsFlag):
    # export solid & return Name
    # Needs to deal with Boolean solids
    # separate from Boolean Objects
    # return count, solidxml, solidName
    # print('Process Solid')
    while switch(obj.TypeId):

        if case("Part::FeaturePython"):
            # print("   Python Feature")
            # if hasattr(obj.Proxy, 'Type') :
            #    #print(obj.Proxy.Type)
            #    return(processGDMLSolid(obj))
            solidxml, solidName = processGDMLSolid(obj)
            return solidxml, solidName
        #
        #  Now deal with Boolean solids
        #  Note handle different from Bookean Objects
        #  that need volume, physvol etc
        #  i.e. just details needed to be added to Solids
        #
        if case("Part::MultiFuse"):
            GDMLShared.trace("Multifuse - multiunion")
            # test and fix
            solidName = 'MultiFuse' + obj.Name
            # First add solids in list before reference
            print('Output Solids')
            for sub in obj.OutList:
                processSolid(sub, False)
            GDMLShared.trace('Output Solids Complete')
            multUnion = ET.SubElement(solids, 'multiUnion', {
               'name': solidName})
            num = 1

            for sub in obj.OutList:
                GDMLShared.trace(sub.Name)
                node = processMuNod(multUnion, 'node-'+str(num))
                ET.SubElement(node, 'solid', {'ref': sub.Name})
                processPosition(sub, node)
                processRotation(sub, node)
                num += 1

            GDMLShared.trace('Return MultiUnion')
            # return idx + num
            return solidName

        if case("Part::MultiCommon"):
            print("   Multi Common / intersection")
            print("   Not available in GDML")
            exit(-3)
            break

        #  Now deal with objects that map to GDML solids
        #
        if case("Part::Box"):
            print("    Box")
            return(processBoxObject(obj, addVolsFlag))
            break

        if case("Part::Cylinder"):
            print("    Cylinder")
            return(processCylinderObject(obj, addVolsFlag))
            break

        if case("Part::Cone"):
            print("    Cone")
            return(processConeObject(obj, addVolsFlag))
            break

        if case("Part::Sphere"):
            print("    Sphere")
            return(processSphereObject(obj, addVolsFlag))
            break

        print(f'Part : {obj.Label}')
        print(f'TypeId : {obj.TypeId}')


def processMuNod(xmlelem, name):
    node = ET.SubElement(xmlelem, 'multiUnionNode', {'name': name})
    return node


import collections
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
    GDMLShared.trace('get Material : '+obj.Label)
    if hasattr(obj, 'material'):
        return obj.material
    if hasattr(obj, 'Tool'):
        GDMLShared.trace('Has tool - check Base')
        material = getMaterial(obj.Base)
        return material
    else:
        return None


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


def isBoolean(obj):
    id = obj.TypeId
    return (id == "Part::Cut" or id == "Part::Fuse" or
            id == "Part::Common")


def boolOperation(obj):
    opsDict = {"Part::Cut": 'subtraction',
               "Part::Fuse": 'union',
               "Part::Common": 'intersection'}
    if obj.TypeId in opsDict:
        return opsDict[obj.TypeId]
    else:
        print(f'Boolean type {obj.TypId} not handled yet')
        return None


def processBooleanObject(obj, xmlVol, volName, xmlParent, parentName):
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
    In the gdml file, boolean solids must always refer to PREVIOUSLY defined
    solids. So the last booleans must be written first:
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

    boolsList = [obj]  # list of booleans that are part of obj
    # dynamic list the is used to figure out when we've iterated over all subobjects
    # that are booleans
    tmpList = [obj]
    ref1 = {}  # first solid reference of boolean
    ref2 = {}  # second solid reference of boolean
    count = 1  # number of solids under this boolean
    while(len(tmpList) > 0):
        obj1 = tmpList.pop()
        if isBoolean(obj1.Base):
            tmpList.append(obj1.Base)
            boolsList.append(obj1.Base)
            ref1[obj1] = obj1.Base.Label
        else:
            solidxml, solidName = processSolid(obj1.Base, False)
            ref1[obj1] = solidName

        if isBoolean(obj1.Tool):
            tmpList.append(obj1.Tool)
            boolsList.append(obj1.Tool)
            ref2[obj1] = obj1.Tool.Label
        else:
            solidxml, solidName = processSolid(obj1.Tool, False)
            ref2[obj1] = solidName

        count += len(obj1.Base.OutList) + len(obj1.Tool.OutList)

    # Now tmpList is empty and boolsList has list of all booleans
    for obj1 in reversed(boolsList):
        operation = boolOperation(obj1)
        if operation is None:
            continue
        solidName = obj1.Label
        boolXML = ET.SubElement(solids, str(operation), {
            'name': solidName})
        ET.SubElement(boolXML, 'first', {'ref': ref1[obj1]})
        ET.SubElement(boolXML, 'second', {'ref': ref2[obj1]})
        # process position & rotationt
        processPosition(obj1.Tool, boolXML)
        # For booleans, gdml want actual rotation, not reverse
        # processRotation export negative of rotation angle(s)
        # This is ugly way of NOT reversing angle:
        angle = obj1.Tool.Placement.Rotation.Angle
        obj1.Tool.Placement.Rotation.Angle = -angle
        processRotation(obj1.Tool, boolXML)
        obj1.Tool.Placement.Rotation.Angle = angle

    # The material and colour are those of the Base of the boolean
    # the solidName is that of the LAST solid in the above loop. Since
    # the boolList is traversed in reverse order, this is the topmost boolean
    addVolRef(xmlVol, volName, obj)

    return 2 + count


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


def processObject(cnt, idx, obj, xmlVol, volName,
                  xmlParent, parentName):
    # cnt - number of GDML objects in Part/Volume
    # If cnt == 1 - No need to create Volume use Part.Label & No PhysVol
    # idx - index into OutList
    # obj - This object
    # xmlVol    - xmlVol
    # xmlParent - xmlParent Volume
    # parentName - Parent Name
    GDMLShared.trace('Process Object : ' + obj.Label)
    while switch(obj.TypeId):

        if case("App::Part"):
            if obj.Label[:12] != 'NOT_Expanded':
                if hasattr(obj, 'InList'):
                    parentName = obj.InList[0].Label
            else:
                parentName = None
            print(obj.Label)
            # print(dir(obj))
            processVolAssem(obj, xmlVol, volName, True)
            return idx + 1

        if case("PartDesign::Body"):
            print("Part Design Body - ignoring")
            return idx + 1

        if case("Sketcher::SketchObject"):
            print(f'Sketch {obj.Label}')
            if hasattr(obj, 'InList'):
                print(f'Has InList {obj.InList}')
                for subObj in obj.InList:
                    print(f'subobj typeid {subObj.TypeId}')
                    if subObj.TypeId == "Part::Extrusion":
                        exportExtrusion.processExtrudedSketch(subObj, obj, xmlVol)
            return idx + 1

        if case("Part::Extrusion"):
            print("Part Extrusion - Handle in Sketch")
            return idx + 1

        if case("App::Origin"):
            # print("App Origin")
            return idx + 1

        # Okay this is duplicate  Volume cpynum > 1 - parent is a Volume
        if case("App::Link"):
            print('App::Link :' + obj.Label)
            # print(dir(obj))
            print(obj.LinkedObject.Label)
            addPhysVolPlacement(obj, xmlVol, obj.LinkedObject.Label)
            return idx + 1

        if case("Part::Cut"):
            GDMLShared.trace("Cut - subtraction")
            retval = idx + processBooleanObject(obj, xmlVol, volName,
                                                xmlParent, parentName)
            return retval

        if case("Part::Fuse"):
            GDMLShared.trace("Fuse - union")
            retval = idx + processBooleanObject(obj, xmlVol, volName,
                                                xmlParent, parentName)
            print(f'retval {retval}')
            return retval

        if case("Part::Common"):
            GDMLShared.trace("Common - Intersection")
            retval = idx + processBooleanObject(obj, xmlVol, volName,
                                                xmlParent, parentName)
            return retval

        if case("Part::MultiFuse"):
            GDMLShared.trace("   Multifuse")
            print("   Multifuse")
            # test and fix
            solidName = obj.Label
            print('Output Solids')
            for sub in obj.OutList:
                processGDMLSolid(sub)
            print('Output Solids Complete')
            multUnion = ET.SubElement(solids, 'multiUnion', {
               'name': solidName})
            num = 1

            for sub in obj.OutList:
                print(sub.Name)
                node = processMuNod(multUnion, 'node-' + str(num))
                ET.SubElement(node, 'solid', {'ref': sub.Name})
                processPosition(sub, node)
                processRotation(sub, node)
                num += 1

            return idx + num

        if case("Part::MultiCommon"):
            print("   Multi Common / intersection")
            print("   Not available in GDML")
            exit(-3)

        if case("Mesh::Feature"):
            print("   Mesh Feature")
            # test and Fix
            # processMesh(obj, obj.Mesh, obj.Label)
            # addVolRef(xmlVol, volName, solidName, obj)
            # print('Need to add code for Mesh Material and colour')
            # testAddPhysVol(obj, xmlParent, parentName):
            # return solid ???
            return idx + 1

        if case("Part::FeaturePython"):
            GDMLShared.trace("   Python Feature")
            print(f'FeaturePython: {obj.Label}')
            if GDMLShared.getTrace is True:
                if hasattr(obj.Proxy, 'Type'):
                    print(obj.Proxy.Type)
            solidxml, solidName = processSolid(obj, True)
            if cnt > 1:
                volName = 'LV-'+solidName
                xmlVol = insertXMLvolume(volName)
            addVolRef(xmlVol, volName, obj, solidName)
            return idx + 1

        # Same as Part::Feature but no position
        if case("App::FeaturePython"):
            print("App::FeaturePython")
            # Following not needed as handled bu Outlist on Tessellated
            # if isinstance(obj.Proxy, GDMLQuadrangular) :
            #   return(processGDMLQuadObject(obj, addVolsFlag))
            #   break
  
            # if isinstance(obj.Proxy, GDMLTriangular) :
            #   return(processGDMLTriangleObject(obj, addVolsFlag))
            #   break
          
            # Following not needed as handled bu Outlist on Xtru

            # if isinstance(obj.Proxy, GDML2dVertex) :
            #   return(processGDML2dVertObject(obj, addVolsFlag))
            #   break
            
            # if isinstance(obj.Proxy, GDMLSection) :
            #   return(processGDMLSection(obj, addVolsFlag))
            #   break
            return idx + 1

        #
        #  Now deal with objects that map to GDML solids
        #
        if case("Part::Box"):
            print("    Box")
            # return(processBoxObject(obj, addVolsFlag))
            processBoxObject(obj, True)
            # testAddPhysVol(obj, xmlParent, parentName)
            return idx + 1

        if case("Part::Cylinder"):
            print("    Cylinder")
            # return(processCylinderObject(obj, addVolsFlag))
            processCylinderObject(obj, True)
            # testAddPhysVol(obj, xmlParent, parentName)
            return idx + 1

        if case("Part::Cone"):
            print("    Cone")
            # return(processConeObject(obj, addVolsFlag))
            processConeObject(obj, True)
            # testAddPhysVol(obj, xmlParent, parentName)
            return idx + 1

        if case("Part::Sphere"):
            print("    Sphere")
            # return(processSphereObject(obj, addVolsFlag))
            processSphereObject(obj, True)
            # testAddPhysVol(obj, xmlParent, parentName)
            return idx + 1

        # Not a Solid that translated to GDML solid
        # Dropped through so treat object as a shape
        # Need to check obj has attribute Shape
        # Create tessellated solid
        #
        # return(processObjectShape(obj, addVolsFlag))
        # print("Convert FreeCAD shape to GDML Tessellated")
        print(f"Object {obj.Label} Type : {obj.TypeId} Not yet handled")
        print(obj.TypeId)
        return idx + 1

        if hasattr(obj, 'Shape'):
            if obj.Shape.isValid():
                # return(processObjectShape(obj))
                processObjectShape(obj)
                # testAddPhysVol(obj, xmlParent, parentName)
        return idx + 1


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


def processAssembly(vol, xmlVol, xmlParent, parentName, addVolsFlag):
    # vol - Volume Object
    # xmlVol - xml of this volume
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
    if hasattr(vol, 'OutList'):
        print('Has OutList')
        for obj in vol.OutList:
            if obj.TypeId == 'App::Part':
                processVolAssem(obj, xmlVol, volName, addVolsFlag)

            elif obj.TypeId == 'App::Link':
                print('Process Link')
                # objName = cleanVolName(obj, obj.Label)
                addPhysVolPlacement(obj, xmlVol, obj.LinkedObject.Label)

            elif obj.TypeId == "Sketcher::SketchObject":
                print(f'Sketch {obj.Label}')
                if hasattr(obj, 'InList'):
                    print(f'Has InList {obj.InList}')
                    for subObj in obj.InList:
                        print(f'subobj typeid {subObj.TypeId}')
                        if subObj.TypeId == "Part::Extrusion":
                            exportExtrusion.processExtrudedSketch(subObj,
                                                                  obj, xmlVol)

        addPhysVolPlacement(vol, xmlParent, volName)


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


def processVolume(vol, xmlVol, xmlParent, parentName, addVolsFlag):
    # vol - Volume Object
    # xmlVol - xml of this volume
    # xmlParent - xml of this volumes Paretnt
    # App::Part will have Booleans & Multifuse objects also in the list
    # So for s in list is not so good
    # type 1 straight GDML type = 2 for GEMC
    # xmlVol could be created dummy volume
    volName = vol.Label
    print(f'Process Volume : {volName}')
    # volName = cleanVolName(vol, vol.Label)
    if GDMLShared.getTrace() is True:
        GDMLShared.trace('Process Volume : ' + volName)
        printVolumeInfo(vol, xmlVol, xmlParent, parentName)

    if hasattr(vol, 'SensDet'):
        if vol.SensDet is not None:
            print('Volume : ' + volName)
            print('SensDet : ' + vol.SensDet)
            ET.SubElement(xmlVol, 'auxiliary', {'auxtype': 'SensDet',
                                                'auxvalue': vol.SensDet})
    idx = 0
    cnt = 0
    if hasattr(vol, 'OutList'):
        num = len(vol.OutList)
        cnt = countGDMLObj(vol.OutList)
        # Depending on how the Parts were constructed, the
        # the order of items in the OutList may not reflect
        # the tree hierarchy in view. If we have bolleans of
        # booleans, we must start with the top most boolean
        # code below gets the boolean that has the largest
        # number of sub booleans
        maxCount = 0
        rootBool = None
        for obj in vol.OutList:
            boolCount = getBooleanCount(obj)
            if boolCount > maxCount:
                maxCount = boolCount
                rootBool = obj

        if rootBool is not None:
            processObject(cnt, idx, rootBool,
                          xmlVol, volName, xmlParent, parentName)
        else:
            GDMLShared.trace('OutList length : ' + str(num))
            while idx < num:
                print(f'idx {idx} {vol.OutList[idx].TypeId}')
                idx = processObject(cnt, idx, vol.OutList[idx],
                                    xmlVol, volName, xmlParent, parentName)
        addPhysVolPlacement(vol, xmlParent, volName)


def processVolAssem(vol, xmlParent, parentName, addVolsFlag):
    # vol - Volume Object
    # xmlVol - xml of this volume
    # xmlParent - xml of this volumes Paretnt
    # xmlVol could be created dummy volume
    print('process volasm '+vol.Label)
    volName = vol.Label
    # volName = cleanVolName(vol, vol.Label)
    if hasattr(vol, 'OutList'):  # Do we have Objects ?
        cnt = countGDMLObj(vol.OutList)
        print('VolAsm - count ' + str(cnt))
        if cnt > 0:
            newXmlVol = insertXMLvolume(volName)
            processVolume(vol, newXmlVol, xmlParent, parentName, addVolsFlag)
        else:
            newXmlVol = insertXMLassembly(volName)
            processAssembly(vol, newXmlVol, xmlParent, parentName, addVolsFlag)

        # addPhysVolPlacement(vol,xmlParent,volName)
        # elif obj.TypeId == 'App::Link' :
        #         addPhysVolPlacement(obj,xmlVol,objName)


def createWorldVol(volName):
    print("Need to create Dummy Volume and World Box ")
    bbox = FreeCAD.BoundBox()
    boxName = defineWorldBox(bbox)
    worldVol = ET.SubElement(structure, 'volume', {'name': volName})
    print("Need to FIX !!!! To use defined gas")
    ET.SubElement(worldVol, 'materialref', {'ref': 'G4_Galactic'})
    ET.SubElement(worldVol, 'solidref', {'ref': boxName})
    ET.SubElement(gxml, 'volume', {'name': volName, 'material': 'G4_AIR'})
    return worldVol


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
    # if len(objList) < 3 :
    #     return False
    # if objList[0].TypeId != 'App::Origin' \
    #     or objList[2].TypeId != 'App::Part' :
    #        return False
    # return True


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
            xmlVol = createXMLvol('dummy')
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
    if cnt > 0:
        xmlVol = insertXMLvolume(vol.Label)
        processVolume(vol, xmlVol, xmlParent, parentName, False)
    else:
        xmlVol = insertXMLassembly(vol.Label)
        processAssembly(vol, xmlVol, xmlParent, parentName, False)


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
        indent(gdml)
        print("Write to gdml file")
        # ET.ElementTree(gdml).write(filepath, 'utf-8', True)
        ET.ElementTree(gdml).write(filepath, xml_declaration=True)
        # ET.ElementTree(gdml).write(filepath, pretty_print=True, \
        # xml_declaration=True)
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
