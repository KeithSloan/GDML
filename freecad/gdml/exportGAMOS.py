#**************************************************************************
#*                                                                        * 
#*   Copyright (c) 2019 Keith Sloan <keith@sloan-home.co.uk>              *
#*             (c) 2020 Dam Lambert                                       *
#*                                                                        *
#*   This program is free software; you can redistribute it and/or modify *
#*   it under the terms of the GNU Lesser General Public License (LGPL)   *
#*   as published by the Free Software Foundation; either version 2 of    *
#*   the License, or (at your option) any later version.                  *
#*   for detail see the LICENCE text file.                                *
#*                                                                        *
#*   This program is distributed in the hope that it will be useful,      *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of       *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        *
#*   GNU Library General Public License for more details.                 *
#*                                                                        *
#*   You should have received a copy of the GNU Library General Public    *
#*   License along with this program; if not, write to the Free Software  *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 *
#*   USA                                                                  *
#*                                                                        *
#*   Acknowledgements : Ideas & code copied from                          *
#*                      https://github.com/ignamv/geanTipi                *
#*                                                                        *
#***************************************************************************
__title__="FreeCAD - GAMOS exporter Version"
__author__ = "Keith Sloan <keith@sloan-home.co.uk>"
__url__ = ["https://github.com/KeithSloan/FreeCAD_Geant4"]

if open.__module__ == '__builtin__':
    pythonopen = open # to distinguish python built-in open function from the one declared here

import FreeCAD, os, Part, math
from FreeCAD import Vector
from .GDMLObjects import GDMLcommon, GDMLBox, GDMLTube

# modif add 
#from .GDMLObjects import getMult, convertionlisteCharToLunit

import sys

try: import FreeCADGui
except ValueError: gui = False
else: gui = True

global zOrder

from .GDMLObjects import GDMLQuadrangular, GDMLTriangular, \
                        GDML2dVertex, GDMLSection, \
                        GDMLmaterial, GDMLfraction, \
                        GDMLcomposite, GDMLisotope, \
                        GDMLelement, GDMLconstant

from . import GDMLShared

#***************************************************************************
# Tailor following to your requirements ( Should all be strings )          *
# no doubt there will be a problem when they do implement Value
if open.__module__ in ['__builtin__', 'io']:
    pythonopen = open # to distinguish python built-in open function from the one declared here

def verifNameUnique(name):
   # need to be done!!
   return True

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

def nameFromLabel(label) :
    if ' ' not in label :
       return label
    else :
       return(label.split(' ')[0])

def defineMaterials():
    # Replaced by loading Default
    #print("Define Materials")
    global materials

def exportDefine(name, v) :
    global define
    print('define : '+name)
    #print(v)
    #print(v[0])
    #ET.SubElement(define,'position',{'name' : name, 'unit': 'mm',   \
    #            'x': str(v[0]), 'y': str(v[1]), 'z': str(v[2]) })

def defineWorldBox(bbox):
    for obj in FreeCAD.ActiveDocument.Objects :
        # print("{} + {} = ".format(bbox, obj.Shape.BoundBox))
        if hasattr(obj,"Shape"):
           bbox.add(obj.Shape.BoundBox)
        if hasattr(obj,"Mesh"):
           bbox.add(obj.Mesh.BoundBox)
        if hasattr(obj,"Points"):
           bbox.add(obj.Points.BoundBox)
    #   print(bbox)
    # Solids get added to solids section of gdml ( solids is a global )
    name = 'WorldBox'
    #ET.SubElement(solids, 'box', {'name': name,
    #                         'x': str(1000), \
    #                         'y': str(1000), \
    #                         'z': str(1000), \
    #                 #'x': str(2*max(abs(bbox.XMin), abs(bbox.XMax))), \
    #                 #'y': str(2*max(abs(bbox.YMin), abs(bbox.YMax))), \
    #                 #'z': str(2*max(abs(bbox.ZMin), abs(bbox.ZMax))), \
    #                 'lunit': 'mm'})
    return(name)

def addObjectToVol(obj, lvol, name, solidName, material) :
    print('addObject')
    #lvol = ET.SubElement(vol,'volume', {'name':name})
    #ET.SubElement(lvol, 'materialref', {'ref': material})
    #ET.SubElement(lvol, 'solidref', {'ref': solidName})

def createLVandPV(obj, name, solidName):
    #
    # Logical & Physical Volumes get added to structure section of gdml
    #
    #ET.ElementTree(gdml).write("test9d", 'utf-8', True)
    #print("Object Base")
    #dir(obj.Base)
    #print dir(obj)
    #print dir(obj.Placement)
    global PVcount, POScount, ROTcount
    return
    pvName = 'PV'+name+str(PVcount)
    PVcount += 1
    pos  = obj.Placement.Base
    lvol = ET.SubElement(structure,'volume', {'name':pvName})
    #ET.SubElement(lvol, 'materialref', {'ref': 'SSteel0x56070ee87d10'})
    ET.SubElement(lvol, 'solidref', {'ref': solidName})
    # Place child physical volume in World Volume
    phys = ET.SubElement(lvol, 'physvol',{'name':'pv'+name})
    #ET.SubElement(phys, 'volumeref', {'ref': pvName})
    x = pos[0]
    y = pos[1]
    z = pos[2]
    if x!=0 and y!=0 and z!=0 :
       posName = 'Pos'+name+str(POScount)
       POScount += 1
       #ET.SubElement(phys, 'positionref', {'name': posName})
       #ET.SubElement(define, 'position', {'name': posName, 'unit': 'mm', \
       #           'x': str(x), 'y': str(y), 'z': str(z) })
    angles = obj.Placement.Rotation.toEuler()
    GDMLShared.trace("Angles")
    GDMLShared.trace(angles)
    a0 = angles[0]
    a1 = angles[1]
    a2 = angles[2]
    if a0!=0 and a1!=0 and a2!=0 :
       rotName = 'Rot'+name+str(ROTcount)
       ROTcount += 1
       #ET.SubElement(phys, 'rotationref', {'name': rotName})
       #ET.SubElement(define, 'rotation', {'name': rotName, 'unit': 'deg', \
       #           'x': str(-a2), 'y': str(-a1), 'z': str(-a0)})

def createAdjustedLVandPV(obj, name, solidName, delta):
    # Allow for difference in placement between FreeCAD and GDML
    adjObj = obj
    rot = FreeCAD.Rotation(obj.Placement.Rotation)
    adjObj.Placement.move(rot.multVec(delta))#.negative()
    createLVandPV(adjObj, name, solidName)

def reportObject(obj) :
    
    GDMLShared.trace("Report Object")
    GDMLShared.trace(obj)
    GDMLShared.trace("Name : "+obj.Name)
    GDMLShared.trace("Type : "+obj.TypeId) 
    if hasattr(obj,'Placement') :
       print("Placement")
       print("Pos   : "+str(obj.Placement.Base))
       print("axis  : "+str(obj.Placement.Rotation.Axis))
       print("angle : "+str(obj.Placement.Rotation.Angle))
    
    while switch(obj.TypeId) :

      ###########################################
      # FreeCAD GDML Parts                      #
      ###########################################
      if case("Part::FeaturePython") : 
         GDMLShared.trace("Part::FeaturePython")
         #
         #if hasattr(obj.Proxy,'Type'):
         #   print (obj.Proxy.Type)
         #   print (obj.Name)
         #else :
         #   print("Not a GDML Feature")
            
         #print dir(obj)
         #print dir(obj.Proxy)
         #print("cylinder : Height "+str(obj.Height)+ " Radius "+str(obj.Radius))
         break
      ###########################################
      # FreeCAD Parts                           #
      ###########################################
      if case("Part::Sphere") :
         print("Sphere Radius : "+str(obj.Radius))
         break
           
      if case("Part::Box") : 
         print("cube : ("+ str(obj.Length)+","+str(obj.Width)+","+str(obj.Height)+")")
         break

      if case("Part::Cylinder") : 
         print("cylinder : Height "+str(obj.Height)+ " Radius "+str(obj.Radius))
         break
   
      if case("Part::Cone") :
         print("cone : Height "+str(obj.Height)+ " Radius1 "+str(obj.Radius1)+" Radius2 "+str(obj.Radius2))
         break

      if case("Part::Torus") : 
         print("Torus")
         print(obj.Radius1)
         print(obj.Radius2)
         break

      if case("Part::Prism") :
         print("Prism")
         break

      if case("Part::RegularPolygon") :
         print("RegularPolygon")
         break

      if case("Part::Extrusion") :
         print("Extrusion")
         break

      if case("Circle") :
         print("Circle")
         break

      if case("Extrusion") : 
         print("Wire extrusion")
         break

      if case("Mesh::Feature") :
         print("Mesh")
         #print dir(obj.Mesh)
         break


      print("Other")
      print(obj.TypeId)
      break

def processPlanar(obj, shape, name ) :
    print ('Polyhedron ????')
    global defineCnt
    #
    #print("Add tessellated Solid")
    #tess = ET.SubElement(solids,'tessellated',{'name': name})
    #print("Add Vertex positions")
    for f in shape.Faces :
       baseVrt = defineCnt
       for vrt in f.Vertexes :
           vnum = 'v'+str(defineCnt)
           #ET.SubElement(define, 'position', {'name': vnum, \
           #   'x': str(vrt.Point.x), \
           #   'y': str(vrt.Point.y), \
           #   'z': str(vrt.Point.z), \
           #   'unit': 'mm'})
           #defineCnt += 1
       #print("Add vertex to tessellated Solid")
       vrt1 = 'v'+str(baseVrt)
       vrt2 = 'v'+str(baseVrt+1)
       vrt3 = 'v'+str(baseVrt+2)
       vrt4 = 'v'+str(baseVrt+3)
       NumVrt = len(f.Vertexes)
       if NumVrt == 3 :
          pass
          #ET.SubElement(tess,'triangular',{ \
          #            'vertex1': vrt1, \
          #            'vertex2': vrt2, \
          #            'vertex3': vrt3, \
          #            'type': 'ABSOLUTE'})
       elif NumVrt == 4 :
          pass
          #ET.SubElement(tess,'quadrangular',{ \
          #            'vertex1': vrt1, \
          #            'vertex2': vrt2, \
          #            'vertex3': vrt3, \
          #            'vertex4': vrt4, \
          #            'type': 'ABSOLUTE'})

def checkShapeAllPlanar(Shape) :
    for f in Shape.Faces :
        if f.Surface.isPlanar() == False :
           return False
        break
    return True

#    Add XML for TessellateSolid
def mesh2Tessellate(mesh, name) :
     global defineCnt

     baseVrt = defineCnt
     print ("mesh")
     print (mesh)
     print (dir(mesh))
     print ("Facets")
     print (mesh.Facets)
     print ("mesh topology")
     print (dir(mesh.Topology))
     print (mesh.Topology)
#
#    mesh.Topology[0] = points
#    mesh.Topology[1] = faces
#
#    First setup vertex in define section vetexs (points) 
     print("Add Vertex positions")
     for fc_points in mesh.Topology[0] : 
         print(fc_points)
         v = 'v'+str(defineCnt)
         #ET.SubElement(define, 'position', {'name': v, \
         #         'x': str(fc_points[0]), \
         #         'y': str(fc_points[1]), \
         #         'z': str(fc_points[2]), \
         #         'unit': 'mm'})
         #defineCnt += 1         
#                  
#     Add faces
#
     print("Add Triangular vertex")
     #tess = ET.SubElement(solids,'tessellated',{'name': name})
     for fc_facet in mesh.Topology[1] : 
       print(fc_facet)
       vrt1 = 'v'+str(baseVrt+fc_facet[0])
       vrt2 = 'v'+str(baseVrt+fc_facet[1])
       vrt3 = 'v'+str(baseVrt+fc_facet[2])
       #ET.SubElement(tess,'triangular',{ \
       #  'vertex1': vrt1, 'vertex2': vrt2 ,'vertex3': vrt3, 'type': 'ABSOLUTE'})


def processMesh(obj, Mesh, Name) :
    #  obj needed for Volune names
    #  object maynot have Mesh as part of Obj
    #  Name - allows control over name
    print("Create Tessellate Logical Volume")
    createLVandPV(obj, Name, 'Tessellated')
    mesh2Tessellate(Mesh, Name)
    return(Name)

def shape2Mesh(shape) :
     import MeshPart
     return (MeshPart.meshFromShape(Shape=shape, Deflection = 0.0))
#            Deflection= params.GetFloat('meshdeflection',0.0)) 

def processObjectShape(obj) :
    # Check if Planar
    # If plannar create Tessellated Solid with 3 & 4 vertex as appropriate
    # If not planar create a mesh and the a Tessellated Solid with 3 vertex
    print("Process Object Shape")
    print(obj)
    print(obj.PropertiesList)
    if not hasattr(obj,'Shape') :
       return 
    shape = obj.Shape
    #print (shape)
    #print(shape.ShapeType)
    while switch(shape.ShapeType) : 
      if case("Mesh::Feature") :
         print("Mesh - Should not occur should have been handled")
         #print("Mesh")
         #tessellate = mesh2Tessellate(mesh) 
         #return(tessellate)
         #break

         print("ShapeType Not handled")
         print(shape.ShapeType)
         break

#   Dropped through to here
#   Need to check has Shape

    print('Check if All planar')
    planar = checkShapeAllPlanar(shape)
    print(planar)

    if planar :
       return(processPlanar(obj,shape,obj.Name))

    else :
       # Create Mesh from shape & then Process Mesh
       #to create Tessellated Solid in Geant4
       return(processMesh(obj,shape2Mesh(shape),obj.Name))

def processBoxObject(obj, fp, addVolsFlag) :
    # Needs unique Name
    # This for non GDML Box
 
    boxName =  obj.Name

    #fp.write('BOX: '+objET.SubElement(solids, 'box',{'name': boxName, \
    #                       'x': str(obj.Length.Value),  \
    #                       'y': str(obj.Width.Value),  \
    #                       'z': str(obj.Height.Value),  \
    #                       'lunit' : 'mm'})
    if addVolsFlag :
       # Adjustment for position in GDML
       delta = FreeCAD.Vector(obj.Length.Value / 2, \
                           obj.Width.Value / 2,  \
                           obj.Height.Value / 2)

       createAdjustedLVandPV(obj, obj.Name, boxName, delta)
    return(boxName)

def processCylinderObject(obj, addVolsFlag) :
    # Needs unique Name
    # This is for non GDML cylinder/tube
    cylName = obj.Name
    #ET.SubElement(solids, 'tube',{'name': cylName, \
    #                       'rmax': str(obj.Radius.Value), \
    #                       'deltaphi': str(float(obj.Angle)), \
    #                       'aunit': obj.aunit,
    #                       'z': str(obj.Height.Value),  \
    #                       'lunit' : 'mm'})
    if addVolsFlag :
       # Adjustment for position in GDML
       delta = FreeCAD.Vector(0, 0, obj.Height.Value / 2)
       createAdjustedLVandPV(obj, obj.Name, cylName, delta)
    return(cylName)

def processConeObject(obj, addVolsFlag) :
    # Needs unique Name
    coneName = obj.Name
    #ET.SubElement(solids, 'cone',{'name': coneName, \
    #                       'rmax1': str(obj.Radius1.Value),  \
    #                       'rmax2': str(obj.Radius2.Value),  \
    #                       'deltaphi': str(float(obj.Angle)), \
    #                       'aunit': obj.aunit,
    #                       'z': str(obj.Height.Value),  \
    #                       'lunit' : 'mm'})
    if addVolsFlag :
       # Adjustment for position in GDML
       delta = FreeCAD.Vector(0, 0, obj.Height.Value / 2)
       createAdjustedLVandPV(obj, obj.Name, coneName, delta)
    return(coneName)

def processSection(obj, addVolsflag) :
    print("Process Section")
    #ET.SubElement(solids, 'section',{'vertex1': obj.v1, \
    #        'vertex2': obj.v2, 'vertex3': obj.v3, 'vertex4': obj.v4, \
    #        'type': obj.vtype})


def processSphereObject(obj, addVolsFlag) :
    # Needs unique Name
    #modif lambda (if we change the name here, each time we import and export the file, the name will be change 
    #sphereName = 'Sphere' + obj.Name
    sphereName = obj.Name

    #ET.SubElement(solids, 'sphere',{'name': sphereName, \
    #                       'rmax': str(obj.Radius.Value), \
    #                       'starttheta': str(90.-float(obj.Angle2)), \
    #                       'deltatheta': str(float(obj.Angle2-obj.Angle1)), \
    #                       'deltaphi': str(float(obj.Angle3)), \
    #                       'aunit': obj.aunit,
    #                       'lunit' : 'mm'})
    if addVolsFlag :
       createLVandPV(obj,obj.Name,sphereName)
    return(sphereName)

def addPhysVol(xmlVol, volName) :
    print("Add PhysVol to Vol") 
    #pvol = ET.SubElement(xmlVol,'physvol',{'name':'PV-'+volName})
    #ET.SubElement(pvol,'volumeref',{'ref':volName})
    return pvol

def exportPosition(name, xml, pos) :
    global POScount
    GDMLShared.trace('export Position')
    GDMLShared.trace(pos)
    x = pos[0]
    y = pos[1]
    z = pos[2]
    posName = 'P-'+name+str(POScount)
    POScount += 1
    #posxml = ET.SubElement(define,'position',{'name' : posName, \
    #                      'unit': 'mm'})
    if x != 0 :
       posxml.attrib['x'] = str(x)
    if y != 0 :
       posxml.attrib['y'] = str(y)
    if z != 0 :
       posxml.attrib['z'] = str(z)
    #ET.SubElement(xml,'positionref',{'ref' : posName})

def exportRotation(name, xml, Rotation) :
    global ROTcount
    if Rotation.Angle != 0 :
        angles = Rotation.toEuler()
        GDMLShared.trace("Angles")
        GDMLShared.trace(angles)
        a0 = angles[0]
        a1 = angles[1]
        a2 = angles[2]
        if a0!=0 or a1!=0 or a2!=0 :
            rotName = 'R-'+name+str(ROTcount)
            ROTcount += 1
            #rotxml = ET.SubElement(define, 'rotation', {'name': rotName, \
            #        'unit': 'deg'})
            if abs(a2) != 0 :
                rotxml.attrib['x']=str(a2)
            if abs(a1) != 0 :
                rotxml.attrib['y']=str(a1)
            if abs(a0) != 0 :
                rotxml.attrib['z']=str(a0)
            #ET.SubElement(xml, 'rotationref', {'ref': rotName})

def processPosition(obj, solid) :
    if obj.Placement.Base == FreeCAD.Vector(0,0,0) :
        return
    GDMLShared.trace("Define position & references to Solid")
    exportPosition(obj.Name, solid, obj.Placement.Base)

def processRotation(obj, solid) :
    if obj.Placement.Rotation.Angle == 0 :
       return
    GDMLShared.trace('Deal with Rotation')
    exportRotation(obj.Name,solid,obj.Placement.Rotation)


def addVolRef(vol,solidName,material) :
    #ET.SubElement(vol,'solidref',{'ref': solidName})
    if material != None :   # MultiUnion no material
       pass
       #ET.SubElement(vol,'materialref',{'ref': material})

def testDefaultPlacement(obj) :
    #print(dir(obj.Placement.Rotation))
    print('Test Default Placement : '+obj.Name)
    print('No longer used ??')
    print(obj.Placement.Base)
    print(obj.Placement.Rotation.Angle)
    if obj.Placement.Base == FreeCAD.Vector(0,0,0) and \
       obj.Placement.Rotation.Angle == 0 :
       return True
    else :
       return False

def getName(obj) :
    return(obj.Label.split('_',1)[1])

def processGDMLArb8Object(obj, name, fp) :
    print('Arb8 - Not Supported')

    #fp.write(*    ET.SubElement(solids, 'arb8',{'name': arb8Name, \
    #                      'v1x': str(obj.v1x),  \
    #                      'v1y': str(obj.v1y),  \
    #                      'v2x': str(obj.v2x),  \
    #                      'v2y': str(obj.v2y),  \
    #                      'v3x': str(obj.v3x),  \
    #                      'v3y': str(obj.v3y),  \
    #                      'v4x': str(obj.v4x),  \
    #                      'v4y': str(obj.v4y),  \
    #                      'v5x': str(obj.v5x),  \
    #                      'v5y': str(obj.v5y),  \
    #                      'v6x': str(obj.v6x),  \
    #                      'v6y': str(obj.v6y),  \
    #                      'v7x': str(obj.v7x),  \
    #                      'v7y': str(obj.v7y),  \
    #                      'v8x': str(obj.v8x),  \
    #                      'v8y': str(obj.v8y),  \
    #                      'dz': str(obj.dz),  \
    #                      'lunit' : obj.lunit})
    return (arb8Name)

def processGDMLBoxObject(obj, name,fp) :

    fp.write('BOX: '+name+ \
                          ' ' + str(obj.x) +  \
                          ' ' + str(obj.y) +  \
                          ' ' + str(obj.z))
    return (name)

def processGDMLConeObject(obj, fp) :
   
    # add check 360 delta for shorter output 
    fp.write('CONE: '+name+ \
                          ' '+ str(obj.rmin1),  \
                          ' '+ str(obj.rmin2),  \
                          ' '+ str(obj.rmax1),  \
                          ' '+ str(obj.rmax2),  \
                          ' '+ str(obj.z),  \
                          ' '+ str(obj.startphi), \
                          ' '+ str(obj.deltaphi))
    return(name)

def processGDMLCutTubeObject(obj, name, fp) :
    print('Cut Tube')
    #fp.write('    ET.SubElement(solids, 'cutTube',{'name': cTubeName, \
    #                      'rmin': str(obj.rmin),  \
    #                      'rmax': str(obj.rmax),  \
    #                      'startphi': str(obj.startphi), \
    #                      'deltaphi': str(obj.deltaphi), \
    #                      'aunit': obj.aunit, \
    #                      'z': str(obj.z),  \
    #                      'highX':str(obj.highX), \
    #                      'highY':str(obj.highY), \
    #                      'highZ':str(obj.highZ), \
    #                      'lowX':str(obj.lowX), \
    #                      'lowY':str(obj.lowY), \
    #                      'lowZ':str(obj.lowZ), \
    #                      'lunit' : obj.lunit})
    return(name)

def processGDMLElConeObject(obj, name, fp) :
    GDMLShared.trace('Elliptical Cone')
    fp.write('ELLIPTICALCONE: '+name+ \
                ' ' + str(obj.dx), \
                ' ' + str(obj.dy), \
                ' ' + str(obj.zcut), \
                ' ' + str(obj.zmax))
    return(name)

def processGDMLEllipsoidObject(obj, name, fp) :
    fp.write('ELLIPSOID: '+name+ \
                          ' ' + str(obj.ax),  \
                          ' ' + str(obj.by),  \
                          ' ' + str(obj.cz),  \
                          ' ' + str(obj.zcut1),  \
                          ' ' + str(obj.zcut2))
    return(name)

def processGDMLElTubeObject(obj, name, fp) :
    fp.write('ELLIPTICALTUBE: ' \
                          ' ' + str(obj.dx),  \
                          ' ' + str(obj.dy),  \
                          ' ' + str(obj.dz))
    return(name)

def processGDMLOrbObject(obj, name, fp) :
    fp.write('ORB: '+name, \
                   ' ' + str(obj.r))
    return(name)

def processGDMLParaObject(obj, name, fp) :
    fp.write('PARA: '+name+ \
                          ' ' + str(obj.x),  \
                          ' ' + str(obj.y),  \
                          ' ' + str(obj.z),  \
                          ' ' + str(obj.alpha), \
                          ' ' + str(obj.theta), \
                          ' ' + str(obj.phi))
    return(name)


def processGDMLPolyconeObject(obj, name, fp) :
    fp.write('POLYCONE: '+name+ \
                          ' ' + str(obj.startphi),  \
                          ' ' + str(obj.deltaphi),  \
                          ' ' + str(len(obj.OutList)))
    print('Add position, Tangent distances')
    #for zplane in obj.OutList :
    #    #fp.writeET.SubElement(cone, 'zplane',{'rmin': str(zplane.rmin), \
    #    #                   'rmax' : str(zplane.rmax), \
    #    #                   'z' : str(zplane.z)})
    #    pass
    return(name)

def processGDMLPolyhedraObject(obj, name, fp) :
    fp.write('POLYHEDRA: '+name+ \
                          ' ' + str(obj.startphi),  \
                          ' ' + str(obj.deltaphi),  \
                          ' ' + str(obj.numsides), \
                          ' ' + str(len(obj.OutList)))
    print('Position, tangent inner, tangent outer')
    #or zplane in obj.OutList :
    #        ET.SubElement(cone, 'zplane',{'rmin': str(zplane.rmin), \
    #                           'rmax' : str(zplane.rmax), \
    #                           'z' : str(zplane.z)})
    #       pass

    return(name)

def processGDMLQuadObject(obj, flag) :
    GDMLShared.trace("GDMLQuadrangular")
    #ET.SubElement(solids, 'quadrangular',{'vertex1': obj.v1, \
    #        'vertex2': obj.v2, 'vertex3': obj.v3, 'vertex4': obj.v4, \
    #        'type': obj.vtype})
    

def processGDMLSphereObject(obj, name, fp) :
    fp.write('SPHERE: '+name+ \
             ' ' + str(obj.rmin),  
             ' ' + str(obj.rmax),  
             ' ' + str(obj.startphi), 
             ' ' + str(obj.deltaphi), 
             ' ' + str(obj.deltatheta)) 
    return(name)

def processGDMLTessellatedObject(obj, name, fp) :
    fp.write('TESSElATED: '+name+' '+str(len(obj.OutList)))
    print(len(obj.OutList))
    index = 0    
    for ptr in obj.OutList :
        #v1Name = tessName+str(index)+'v1'
        #v2Name = tessName+str(index)+'v2'
        #v3Name = tessName+str(index)+'v3'
        #exportDefine(v1Name,ptr.v1)
        #exportDefine(v2Name,ptr.v2)
        #exportDefine(v3Name,ptr.v3)

        #if hasattr(ptr,'v4' ) :
        #   v4Name = tessName+str(index)+'v4'
        #   exportDefine(v4Name,ptr.v4)
        #ET.SubElement(tess,'quadrangular',{'vertex1':v1Name, \
        #    'vertex2':v2Name, 'vertex3':v3Name, 'vertex4':v4Name,
        #                            'type':'ABSOLUTE'})
        #    else :    
        #ET.SubElement(tess,'triangular',{'vertex1':v1Name, \
        #        'vertex2': v2Name, \
        #        'vertex3': v3Name,'type':'ABSOLUTE'})
            index += 1    

    return(name)

def processGDMLTetraObject(obj, name, fp) :
    #    v1Name = tetraName + 'v1'
    #    v2Name = tetraName + 'v2'
    #    v3Name = tetraName + 'v3'
    #    v4Name = tetraName + 'v4'
    #    exportDefine(v1Name,obj.v1)
    #    exportDefine(v2Name,obj.v2)
    #    exportDefine(v3Name,obj.v3)
    #    exportDefine(v4Name,obj.v4)

    #fp.write('TET: '+name+:  \
    #                'vertex1': v1Name, \
    #                'vertex2': v2Name, \
    #                'vertex3': v3Name, \
    #                'vertex4': v4Name})
    return name    

def processGDMLTorusObject(obj, name, fp) :
    fp.write('TORUS: '+name+ \
             ' ' + str(obj.rmin), \
             ' ' + str(obj.rmax), \
             ' ' + str(obj.rtor), \
             ' ' + str(obj.startphi), \
             ' ' + str(obj.deltaphi))
    return(name)


def processGDMLTrapObject(obj, name, fp) :
    fp.write('TRAP: '+name+ \
             ' ' + str(obj.z),  \
             ' ' + str(obj.theta),  \
             ' ' + str(obj.phi), \
             ' ' + str(obj.x1),  \
             ' ' + str(obj.x2),  \
             ' ' + str(obj.x3),  \
             ' ' + str(obj.x4),  \
             ' ' + str(obj.y1),  \
             ' ' + str(obj.y2),  \
             ' ' + str(obj.alpha), \
             ' ' + str(obj.alpha))
    return(name)

def processGDMLTrdObject(obj, name, fp) :
    fp.write('TRD: '+name+ \
             ' ' + str(obj.x1),  \
             ' ' + str(obj.x2),  \
             ' ' + str(obj.y1),  \
             ' ' + str(obj.y2),  \
             ' ' + str(obj.z))
    return(name)

def processGDMLTriangle(obj, flag) :
    if flag == True :
        print("Process GDML Triangle")
        #ET.SubElement(solids, 'triangular',{'vertex1': obj.v1, \
        #    'vertex2': obj.v2, 'vertex3': obj.v3,  \
        #    'type': obj.vtype})

def processGDMLTubeObject(obj, name, fp) :
    fp.write('TUBS: '+name+ \
             ' ' + str(obj.rmin),  \
             ' ' + str(obj.rmax),  \
             ' ' + str(obj.z),  \
             ' ' + str(obj.startphi), \
             ' ' + str(obj.deltaphi))
    return(name)

def processGDMLXtruObject(obj, flag) :
    # Needs unique Name
    xtruName = obj.Label.split('_',1)[1]

    if flag == True :
        #xtru = ET.SubElement(solids, 'xtru',{'name': xtruName, \
        #                  'lunit' : obj.lunit})
        for items in obj.OutList :
            #if items.Type == 'twoDimVertex' :
            #    #ET.SubElement(xtru, 'twoDimVertex',{'x': str(items.x), \
            #    #                   'y': str(items.y)})
            #if items.Type == 'section' :
            #    ET.SubElement(xtru, 'section',{'zOrder': str(items.zOrder), \
            #                      'zPosition': str(items.zPosition), \
            #                      'xOffset' : str(items.xOffset), \
            #                      'yOffset' : str(items.yOffset), \
            #                      'scalingFactor' : str(items.scalingFactor)})
            pass
    return(xtruName)

def processGDML2dVertex(obj, flag) :
    if flag == True :
        print("Process 2d Vertex")
        #ET.SubElement(solids, 'twoDimVertex',{'x': obj.x, 'y': obj.y})

def processElement(obj, item): # maybe part of material or element (common code)
    if hasattr(obj,'Z') :
       #print(dir(obj))
       item.set('Z',str(obj.Z)) 

    if hasattr(obj,'N') :
       #print(dir(obj))
       item.set('N',str(obj.N)) 

    if hasattr(obj,'formula') :
       #print(dir(obj))
       item.set('formula',str(obj.formula)) 

    if hasattr(obj,'atom_unit') or hasattr(obj,'atom_value') :
       atom = ET.SubElement(item,'atom') 
    
       if hasattr(obj,'atom_unit') :
          atom.set('unit',str(obj.atom_unit)) 
            
       if hasattr(obj,'atom_value') :
          atom.set('value',str(obj.atom_value)) 

def processMaterialsGroupObjects(fp) :
    print("\nProcess Materials Group Objects")
   
    for obj in FreeCAD.ActiveDocument.Objects:
       print(obj.TypeId+" : "+obj.Name)

       if obj.TypeId == "App::DocumentObjectGroupPython":
          print("   Object List : "+obj.Name)
          #print(obj)
          while switch(obj.Name) :
             if case("Constants") : 
                print("Constants")
                processConstants(obj, fp)
                break

             if case("Isotopes") :
                print("Isotopes")
                processIsotopes(obj, fp)
                break
            
             if case("Elements") :
                print("Elements")
                processElements(obj, fp)
                break

             if case("Materials") : 
                print("Materials")
                processMaterials(obj, fp)
                break
         
             break

def processConstants(obj,fp):
    print('Process Constants')

def processIsotopes(obj,fp):
    print('Process Isotopes')
   
def processElements(obj,fp):
    print('Process Elements')
   
def processMaterials(obj,fp):
    print('Process Materials')

def tobesorted():
          if isinstance(obj.Proxy,GDMLconstant) :
             #print("GDML constant")
             #print(dir(obj))

             item = ET.SubElement(define,'constant',{'name': obj.Name, \
                                 'value': obj.value })
             #return True
          #return   
            
          if isinstance(obj.Proxy,GDMLmaterial) :
             #print("GDML material")
             #print(dir(obj))

             item = ET.SubElement(materials,'material',{'name': \
                    nameFromLabel(obj.Label)})

             # process common options material / element
             processElement(obj, item)

          if hasattr(obj,'Dunit') or hasattr(obj,'Dvalue') :
             D = ET.SubElement(item,'D')
             if hasattr(obj,'Dunit') :
                D.set('unit',str(obj.Dunit))
             
             if hasattr(obj,'Dvalue') :
                D.set('value',str(obj.Dvalue))

          if hasattr(obj,'Tunit') :
             ET.SubElement(item,'T',{'unit': obj.Tunit, \
                                      'value': str(obj.Tvalue)})
           
          if hasattr(obj,'MEEunit') :
             ET.SubElement(item,'MEE',{'unit': obj.MEEunit, \
                                               'value': str(obj.MEEvalue)})

          #return True
          #break

          if isinstance(obj.Proxy,GDMLfraction) :

             #print("GDML fraction :" + obj.Name)
             # need to strip number making it unique
             #ET.SubElement(item,'fraction',{'n': str(obj.n), \
             #        'ref': nameFromLabel(obj.Label)})

             return True

          if isinstance(obj.Proxy,GDMLcomposite) :
             print("GDML Composite")
             fp.write('ELEM_FROM_ISOT '+ nameFromLabel(obj.Label))

             #ET.SubElement(item,'composite',{'n': str(obj.n), \
             #        'ref': nameFromLabel(obj.Label)})
             #return True

          if isinstance(obj.Proxy,GDMLisotope) :
             print("GDML isotope")
             fp.write(':ISOT '+obj.Name+' '+obj.Z+' '+obj.N+' '+str(obj.value))

          if isinstance(obj.Proxy,GDMLelement) :
             print("GDML element")
             fp.write(':ELEM '+nameFromLabel(obj.Label)+' '+obj.formula+ \
                      ' '+obj.Z+' '+str(obj.value))

          # Commented out as individual objects will also exist
          #if len(obj.Group) > 1 :
          #   for grp in obj.Group :
          #       processObject(grp, addVolsFlag)
          # All non Material Objects should terminate Loop
          #return False


def processGDMLSolid(obj, fp) :
    # Deal with GDML Solids first
    # Deal with FC Objects that convert
    #print(obj.Proxy.Type)
    name = getName(obj)
    print(fp)
    while switch(obj.Proxy.Type) :
       if case("GDMLArb8") :
          print("      GDMLArb8") 
          return(processGDMLArb8Object(obj, name, fp))
          break

       if case("GDMLBox") :
          #print("      GDMLBox") 
          return(processGDMLBoxObject(obj, name, fp))
          break

       if case("GDMLCone") :
          #print("      GDMLCone") 
          return(processGDMLConeObject(obj,  name, fp))
          break

       if case("GDMLcutTube") :
          #print("      GDMLcutTube") 
          return(processGDMLCutTubeObject(obj,name,  fp))
          break
       
       if case("GDMLElCone") :
          #print("      GDMLElCone") 
          return(processGDMLElConeObject(obj,name,   fp))
          break

       if case("GDMLEllipsoid") :
          #print("      GDMLEllipsoid") 
          return(processGDMLEllipsoidObject(obj,name,  fp))
          break

       if case("GDMLElTube") :
          #print("      GDMLElTube") 
          return(processGDMLElTubeObject(obj, name,  fp))
          break

       if case("GDMLOrb") :
          #print("      GDMLOrb") 
          return(processGDMLOrbObject(obj, name, fp))
          break

       if case("GDMLPara") :
          #print("      GDMLPara") 
          return(processGDMLParaObject(obj, name, fp))
          break
             
       if case("GDMLPolycone") :
          #print("      GDMLPolycone") 
          return(processGDMLPolyconeObject(obj, name, fp))
          break
             
       if case("GDMLPolyhedra") :
          #print("      GDMLPolyhedra") 
          return(processGDMLPolyhedraObject(obj, name, fp))
          break
             
       if case("GDMLSphere") :
          #print("      GDMLSphere") 
          return(processGDMLSphereObject(obj, name, fp))
          break

       if case("GDMLTessellated") :
          #print("      GDMLTessellated") 
          return(processGDMLTessellatedObject(obj,name,  fp))
          break

       if case("GDMLTetra") :
          #print("      GDMLTetra") 
          return(processGDMLTetraObject(obj, name, fp))
          break

       if case("GDMLTorus") :
          print("      GDMLTorus") 
          return(processGDMLTorusObject(obj, name, fp))
          break

       if case("GDMLTrap") :
          #print("      GDMLTrap") 
          return(processGDMLTrapObject(obj,  name, fp))
          break

       if case("GDMLTrd") :
          #print("      GDMLTrd") 
          return(processGDMLTrdObject(obj,  name, fp))
          break

       if case("GDMLTube") :
          #print("      GDMLTube") 
          return(processGDMLTubeObject(obj, name, fp))
          break

       if case("GDMLXtru") :
          #print("      GDMLXtru") 
          return(processGDMLXtruObject(obj, name, fp))
          break

       print("Not yet Handled")
       break  

def processSolid(obj, fp) :
    # export solid & return Name
    while switch(obj.TypeId) :

        if case("Part::FeaturePython"):
            #print("   Python Feature")
            if hasattr(obj.Proxy, 'Type') :
                #print(obj.Proxy.Type) 
                return(processGDMLSolid(obj, fp))
        #
        #  Now deal with objects that map to GDML solids
        #
        if case("Part::Box") :
            print("    Box")
            return(processBoxObject(obj, fp))
            break

        if case("Part::Cylinder") :
            print("    Cylinder")
            return(processCylinderObject(obj, fp))
            break

        if case("Part::Cone") :
            print("    Cone")
            return(processConeObject(obj, fp))
            break

        if case("Part::Sphere") :
            print("    Sphere")
            return(processSphereObject(obj, fp))
            break
   
def processMuNod(xmlelem, name) :
    node = ET.SubElement(xmlelem,'multiUnionNode',{'name' : name})
    return node

import collections
from itertools import islice

def consume(iterator) :
    next(islice(iterator,2,2), None)

def getXmlVolume(volObj) :
    if volObj == None :
       return None 
    xmlvol = structure.find("volume[@name='%s']" % volObj.Name)
    if xmlvol == None :
       print(volObj.Name+' Not Found') 
    return xmlvol

def processObject(idx, OutList, xmlVol, xmlParent, parentName, fp) :
    # idx - index into OutList
    # OutList - OutList 
    # xmlVol    - xmlVol
    # xmlParent - xmlParent Volume
    # parenName - Parent Name
    # addVolsFlag - Add physical Vol
    # return idx of next Object to be processed
    # solid or boolean reference name or None
    # addVolsFlag = True then create Logical & Physical Volumes
    #             = False needed for booleans
    #ET.ElementTree(gdml).write("test9a", 'utf-8', True)
    obj = OutList[idx]
    #print("Process Object : "+obj.Name+' Type '+obj.TypeId)
    while switch(obj.TypeId) :

      if case("App::Part") :
          #subXMLvol = insertXMLvol(obj.Name)
          if hasattr(obj,'OutList') :
                #print('Process '+obj.Name)
                #processVols(obj, subXMLvol, xmlVol, obj.Name, True)
                pass
          return idx + 1
         
      if case("App::Origin") :
         #print("App Origin")
         return idx + 1
         break

      #if case("App::GeoFeature") :
      #   #print("App GeoFeature")
      #   return
      #   break

      #if case("App::Line") :
      #   #print("App Line")
      #   return
      #   break

      #f case("App::Plane") :
      #   #print("App Plane")
      #   return
      #   break

      if case("Part::Cut") :
         # Maybe Booleans could be grouped with GDML solids 
         #print("   Cut")
         #print(boolFlg)
         cutName = 'Cut'+obj.Name
         ref1 = processSolid(obj.Base, fp)
         ref2 = processSolid(obj.Tool, fp)
         subtract = ET.SubElement(solids,'subtraction',{'name': cutName })
         ET.SubElement(subtract,'first', {'ref': ref1})
         ET.SubElement(subtract,'second',{'ref': ref2})
         addVolRef(xmlVol,cutName,obj.Base.material)
         pvol = addPhysVol(xmlParent,parentName)
         processPosition(obj,pvol)
         processRotation(obj,pvol)
         processPosition(obj.Tool,subtract)
         processRotation(obj.Tool,subtract)
         return idx + 3
         #return True, cutName
         break

      if case("Part::Fuse") :
         #print("   Union")
         unionName = 'Union'+obj.Name
         ref1 = processSolid(obj.Base, fp)
         ref2 = processSolid(obj.Tool, fp)
         union = ET.SubElement(solids,'union',{'name': unionName })
         ET.SubElement(union,'first', {'ref': ref1})
         ET.SubElement(union,'second',{'ref': ref2})
         addVolRef(xmlVol,unionName,obj.Base.material)
         pvol = addPhysVol(xmlParent,parentName)
         processPosition(obj,pvol)
         processRotation(obj,pvol)
         processPosition(obj.Tool,union)
         processRotation(obj.Tool,union)
         return idx + 3
         #return True, unionName
         break

      if case("Part::Common") :
         #print("   Intersection")
         intersectName = 'Intersect'+obj.Name
         ref1 = processSolid(obj.Base, fp)
         ref2 = processSolid(obj.Tool, fp)
         intersect = ET.SubElement(solids,'intersection',{'name': \
                     intersectName })
         ET.SubElement(intersect,'first', {'ref': ref1})
         ET.SubElement(intersect,'second',{'ref': ref2})
         addVolRef(xmlVol,intersectName,obj.Base.material)
         pvol = addPhysVol(xmlParent,parentName)
         processPosition(obj,pvol)
         processRotation(obj,pvol)
         processPosition(obj.Tool,intersect)
         processRotation(obj.Tool,intersect)
         return idx + 3
         #return True, intersectName
         break

      if case("Part::MultiFuse") :
         print("   Multifuse") 
         # test and fix
         multName = 'MultiFuse'+obj.Name
         addVolRef(xmlVol,multName,None)
         # First add solids in list before reference
         print('Output Solids')
         for sub in obj.OutList:
             processSolid(sub,fp)
         print('Output Solids Complete')
         multUnion = ET.SubElement(solids,'multiUnion',{'name': multName })
         num = 1

         for sub in obj.OutList:
             print(sub.Name)
             node = processMuNod(multUnion, 'node-'+str(num))
             ET.SubElement(node,'solid',{'ref':sub.Name})
             processPosition(sub,node)
             processRotation(sub,node)
             num += 1

         #return multName
         print('Return MultiUnion')
         return idx + num 
         break

      if case("Part::MultiCommon") :
         print("   Multi Common / intersection")
         print("   Not available in GDML")
         exit(-3)
         break

      if case("Mesh::Feature") :
         print("   Mesh Feature") 
         # test and Fix
         return(processMesh(obj, obj.Mesh, obj.Name))
         break

      if case("Part::FeaturePython"):
          #print("   Python Feature")
          if hasattr(obj.Proxy, 'Type') :
             #print(obj.Proxy.Type) 
             solidName = processSolid(obj, fp)
             addVolRef(xmlVol,solidName,obj.material)
             if xmlParent != None :
                pvol = addPhysVol(xmlParent,parentName)
                processPosition(obj,pvol)
                processRotation(obj,pvol)
          else :
             print("Not a GDML Feature")
          return idx + 1 
          break  

      # Same as Part::Feature but no position
      if case("App::FeaturePython") :
         print("App::FeaturePython") 
         # Following not needed as handled bu Outlist on Tessellated
         #if isinstance(obj.Proxy, GDMLQuadrangular) :
         #   return(processGDMLQuadObject(obj, addVolsFlag))
         #   break
  
         #if isinstance(obj.Proxy, GDMLTriangular) :
         #   return(processGDMLTriangleObject(obj, addVolsFlag))
         #   break
          
         # Following not needed as handled bu Outlist on Xtru

         #if isinstance(obj.Proxy, GDML2dVertex) :
         #   return(processGDML2dVertObject(obj, addVolsFlag))
         #   break
            
         #if isinstance(obj.Proxy, GDMLSection) :
         #   return(processGDMLSection(obj, addVolsFlag))
         #   break
         return idx + 1
         break  

      #
      #  Now deal with objects that map to GDML solids
      #
      if case("Part::Box") :
         print("    Box")
         return(processBoxObject(obj, addVolsFlag))
         break

      if case("Part::Cylinder") :
         print("    Cylinder")
         return(processCylinderObject(obj, addVolsFlag))
         break

      if case("Part::Cone") :
         print("    Cone")
         return(processConeObject(obj, addVolsFlag))
         break

      if case("Part::Sphere") :
         print("    Sphere")
         return(processSphereObject(obj, addVolsFlag))
         break

      # Not a Solid that translated to GDML solid
      # Dropped through so treat object as a shape
      # Need to check obj has attribute Shape
      # Create tessellated solid
      #
      #return(processObjectShape(obj, addVolsFlag))
      print("Convert FreeCAD shape to GDML Tessellated")
      print(obj.TypeId)
      if hasattr(obj,'Shape') :
         if obj.Shape.isValid() : 
            return(processObjectShape(obj))
      break

def processVols(vol, xmlVol, xmlParent, parentName, fp) :
    # App::Part will have Booleans & Multifuse objects also in the list
    # So for s in list is not so good
    ##print('processVol : '+vol.Name)
    # xmlVol could be created dummy volume

    num = len(vol.OutList)
    idx = 0
    boolflg = False
    while idx < num :
        #print(idx)
        idx  = processObject(idx, vol.OutList, xmlVol, \
                xmlParent, parentName, fp)

    #for obj in vol.OutList :
    #    if obj.TypeId == 'App::Part' :
    #        subXMLvol = insertXMLvol(obj.Name)
    #        if hasattr(obj,'OutList') :
    #            #print('Process '+obj.Name)
    #            processVols(obj, subXMLvol, xmlVol, obj.Name, True)
    #    boolflg = processObject(obj, boolflg, xmlVol, xmlParent, \
    #                  parentName, addVolsFlag)

def createWorldVol(volName) :
    print("Need to create Dummy Volume and World Box ")
    bbox = FreeCAD.BoundBox()
    boxName = defineWorldBox(bbox)
    worldVol = ET.SubElement(structure,'volume',{'name': volName}) 
    ET.SubElement(worldVol, 'solidref',{'ref': boxName})
    print("Need to FIX !!!! To use defined gas")
    ET.SubElement(worldVol, 'materialref',{'ref': 'G4_Galactic'})
    return worldVol

def checkGDMLstructure(objList) :
    # Should be 
    # World Vol - App::Part
    # App::Origin
    # GDML Object
    if objList[0].TypeId != 'App::Origin' \
        or objList[2].TypeId != 'App::Part' :
            return False
    return True

def createXMLvol(name) :
    print(name)
    return(name)

def locateXMLvol(vol) :
    global structure
    xmlVol = structure.find("volume[@name='%s']" % vol.Name)
    return xmlVol

def exportWorldVol(vol,fp) :

    print('Export World Process Volume')
    #ET.SubElement(setup,'world',{'ref':vol.Name}) 

    if hasattr(vol,'OutList') :
        if checkGDMLstructure(vol.OutList) == False :
            xmlVol = createXMLvol('dummy') 
            xmlParent = createWorldVol(vol.Name)
            addPhysVol(xmlParent,'dummy')
        else :
            xmlParent = None
            xmlVol = createXMLvol(vol.Name)

        processVols(vol, xmlVol, xmlParent, vol.Name, fp)

def exportGAMOS(first,filename) :
       # GAMOS Export
       print("\nStart GDML GAMOS Export 0.1")

       fp = pythonopen(filename,'w')
       processMaterialsGroupObjects(fp)
       exportWorldVol(first,fp)
       print("GAMOS file written")

def export(exportList,filename) :
    "called when FreeCAD exports a file"
    
    first = exportList[0]
    if first.TypeId == "App::Part" :
       exportGAMOS(first,filename)

       from PyQt4 import QtGui
       QtGui.QMessageBox.critical(None,'Need to select a Part for export','Press OK')

