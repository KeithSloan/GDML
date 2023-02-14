# **************************************************************************
# *                                                                        * 
# *   Copyright (c) 2022 Keith Sloan <keith@sloan-home.co.uk>              *
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
# ***************************************************************************
__title__ = "convertOBJ - Convert Obj to GDML Tessellated"
__author__ = "Keith Sloan <keith@sloan-home.co.uk>"
__url__ = ["https://github.com/KeithSloan/GDML/Utils"]

import os, sys

class switch(object):
    value = None
    def __new__(class_, value):
        class_.value = value
        return True

def case(*args):
    return any((arg == switch.value for arg in args))

class tessellated:
    def __init__(self, gdmlStr, name):
        self.tess = gdmlStr.defineTessellated(name)

    def addTriFace(self, vrt1, vrt2, vrt3):
        ET.SubElement(self.tess,'triangular',{
          'vertex1' : vrt1, 'vertex2' : vrt2, 'vertex3' : vrt3,
          'type':'ABSOLUTE'})

    def addQuadFace(self, vrt1, vrt2, vrt3, vrt4):
        ET.SubElement(self.tess,'quadrangular',{
          'vertex1' : vrt1, 'vertex2' : vrt2, 'vertex3' : vrt3, 'vertex4': vrt4,
          'type':'ABSOLUTE'})

class xmlStructure:
    def __init__(self):
        self.vertex = ['dummy']

    def indent(self, elem, level=0):
        #########################################################
        # Pretty format GDML                                    #
        #########################################################
        i = "\n" + level*"  "
        j = "\n" + (level-1)*"  "
        if len(elem):
           if not elem.text or not elem.text.strip():
              elem.text = i + "  "
           if not elem.tail or not elem.tail.strip():
               elem.tail = i
           for subelem in elem:
               self.indent(subelem, level+1)
           if not elem.tail or not elem.tail.strip():
               elem.tail = j
        else:
           if level and (not elem.tail or not elem.tail.strip()):
               elem.tail = j

    def initGDML(self):
        NS = 'http://www.w3.org/2001/XMLSchema-instance'
        location_attribute = '{%s}noNamespaceSchemaLocation' % NS
        self.element = ET.Element('gdml',attrib={location_attribute: \
             'http://service-spi.web.cern.ch/service-spi/app/releases/GDML/schema/gdml.xsd'})
        #print(self.element.tag)
        #'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
        #'xsi:noNamespaceSchemaLocation': "http://service-spi.web.cern.ch/service-spi/app/releases/GDML/schema/gdml.xsd"
#}

    def init(self):
        self.define = ET.SubElement(self.element, 'define')
        ET.SubElement(self.define, 'position', {'name':'center', 'x':'0', 'y':'0', 'z':'0'})
        ET.SubElement(self.define, 'rotation', {'name':'identity', 'x':'0', 'y':'0', 'z':'0'})
        self.defineCount = 0
        self.vertexCount = 0
        self.materials = ET.SubElement(self.element, 'materials')
        self.solids = ET.SubElement(self.element, 'solids')
        self.structure = ET.SubElement(self.element, 'structure')
        self.setup = ET.SubElement(self.element, 'setup', {'name': 'Default', 'version': '1.0'})


    def addWorldBox(self, x, y, z):
        name = 'worldBox'
        ET.SubElement(self.solids, 'box', {'name': name, \
                        'x': str(x), 'y': str(y), 'z': str(z)})
        return name

    def addWorldVol(self,name):
        ET.SubElement(self.setup, 'world', {'ref': name})
        return(self.addVol(name, 'G4_AIR',self.addWorldBox(1000,1000,1000)))

    def addVol(self, name, material, solid):
        vol = ET.SubElement(self.structure, 'volume',{'name': name})
        ET.SubElement(vol, 'materialref',{'ref': material})
        ET.SubElement(vol, 'solidref',{'ref': solid})
        return vol

    def addPhysVol(self, vol, name):
        pvol = ET.SubElement(vol,'physvol', {'name': 'PV'+name})
        ET.SubElement(pvol, 'volumeref', {'ref': name})
        ET.SubElement(pvol, 'positionref', {'ref': 'center'})
        ET.SubElement(pvol, 'rotationref', {'ref': 'identity'})


    def addVertex(self, x, y, z):
        # Add to Define position name
        vnum = 'v'+str(self.defineCount)
        self.defineCount += 1
        self.vertexCount += 1
        ET.SubElement(self.define, 'position', {'name': vnum, \
                        'x': str(x), 'y': str(y), 'z': str(z)})
        self.vertex.append(vnum)

    def addTriFace(self, tess, items):
        tess.addTriFace(self.vertex[int(items[1])], \
                        self.vertex[int(items[2])], \
                        self.vertex[int(items[3])])
    
    def addQuadFace(self, tess, items):
        tess.addQuadFace(self.vertex[int(items[1])], \
                         self.vertex[int(items[2])], \
                         self.vertex[int(items[3])], \
                         self.vertex[int(items[4])])
        
    def defineTessellated(self, name):
        # return Tessellated Element
        return ET.SubElement(self.solids,'tessellated',{'name': name})

    def writeElement(self, path):
        print('Write Element to : '+path)
        self.indent(self.element)
        ET.ElementTree(self.element).write(path, xml_declaration=True)
   
def processObjFile(xmlStr, objFp, name):
    tess = tessellated(xmlStr, name)
    for line in objFp:
        #print(line)
        items = line.split(' ')
        l = len(items) - 1
        while switch(items[0]) :
           if case('v') :
              #print('Vertex - len : '+str(l))
              if l >= 3:
                  xmlStr.addVertex(items[1], items[2],items[3])
              else :
                  print('Invalid Vertex')
                  print(items)
              break

           if case('f') :
              #print('Face')
              #print(xmlStr.vertexCount)
              if l == 3 :
                 #print('Triangle')
                 xmlStr.addTriFace(tess, items)
              elif l == 4 : 
                 #print('Quad : '+str(items))
                 xmlStr.addQuadFace(tess, items)
              else :
                 print('Warning Polygon : Number of Face Vertex = '+str(l))
                 print('Converting to Triangle Faces')
                 #verts = []
                 #for i in range(1,l+1) :
                 #    v = vertex[getVert(items[i])]
                 #    #print(v)
                 #    verts.append(v)
                 ##print(verts)
                 #verts.append(verts[0])
              break

           if case('#') :          # Comment ignore
              break

           if case('vt') :
              break

           if case('vn') :
              break

           print('Tag : '+items[0])
           break

def convert2GDML(objFp, outPath, tessName, material):
    print('Creating GDML from Obj')
    gdmlStr = xmlStructure()
    gdmlStr.initGDML()
    gdmlStr.init()
    tessVol = gdmlStr.addVol('LV_'+tessName, material, tessName)
    worldVol = gdmlStr.addWorldVol('worldVol')
    gdmlStr.addPhysVol(worldVol, 'LV_'+tessName)
    processObjFile(gdmlStr, objFp, tessName)
    gdmlStr.writeElement(outPath)

def convert2XML(objFp, outPath, tessName, material):
    print('Creating XML from Obj')
    xmlStr = xmlStructure()
    xmlStr.initXML()
    xmlStr.init()
    processObjFile(xmlStr, objFp, tessName)
    gdmlStr.writeElement(outPath)

argLen = len(sys.argv)
if argLen<3:
  print ("Usage: sys.argv[0] <in_file_path>.obj <out_file_path>.gdml <material>")
  sys.exit(1)

iPath = sys.argv[1]
oPath = sys.argv[2]
if argLen == 3:
   material = 'G4_A-150_TISSUE'
else: 
   material = sys.argv[3]
print('\nConverting Obj file : '+iPath+' to : '+oPath)
print('Material '+material)
objFp = open(iPath)

try:
    import lxml.etree as ET
    print("running with lxml.etree\n")
    XML_IO_VERSION = 'lxml'
except ImportError:
    try:
        import xml.etree.ElementTree as ET
        print("running with xml.etree.ElementTree\n")
        XML_IO_VERSION = 'xml'
    except ImportError:
        print('xml lib not found\n')
        sys.exit()
path, fileExt = os.path.splitext(iPath)
print(path)
tessName = path
print(tessName)
if fileExt.lower() != '.obj':
   print('Invalid Obj file extension')
   sys.exit()
objFp = open(iPath,"r")
if objFp == None:
   print('Failed to open :'+iPath)
   sys.exit()
path, fileExt = os.path.splitext(oPath)
print('target file extension : '+fileExt)
if fileExt.lower() == '.gdml':
   convert2GDML(objFp, oPath, tessName, material)
# elif fileExt.lower() == '.xml':
#   convert2XML(objFp, oPath, tessName, material)
else:
   print('Target path should have File extension of gdml or xml')
