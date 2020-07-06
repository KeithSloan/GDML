#**************************************************************************
#*                                                                        *
#*   Copyright (c) 2017 Keith Sloan <keith@sloan-home.co.uk>              *
#*             (c) Dam Lambert 2020                                          *
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
#*   Acknowledgements :                                                   *
#*                                                                        *
#**************************************************************************

__title__="FreeCAD GDML Workbench - Gmsh Utils"
__author__ = "Keith Sloan"
__url__ = ["http://www.freecadweb.org"]

'''
This Script includes the GUI Commands of the GDML module
'''

import FreeCAD
import sys
sys.path.append('/usr/local/lib/python3.7/site-packages/gmsh-4.5.6-MacOSX-sdk/lib')

def Gmsh(obj) :
    # Uses FreeCAD FEM 
    import ObjectsFem
    from femmesh.gmshtools import GmshTools

    doc = FreeCAD.ActiveDocument
    print('Action Tessellate Mesh')
    femmesh_obj = ObjectsFem.makeMeshGmsh(doc, obj.Name + "_Mesh")
    femmesh_obj.Part = obj
    femmesh_obj.Algorithm2D = 'DelQuad'
    doc.recompute()
    gm = GmshTools(femmesh_obj)
    error = gm.create_mesh()
    print(error)
    doc.recompute()

import gmsh
import numpy as np

def initialize() :
    gmsh.initialize()
    gmsh.option.setNumber('Mesh.Algorithm',6)
    gmsh.option.setNumber('Mesh.Algorithm3D',1)
    gmsh.option.setNumber("Geometry.OCCFixDegenerated", 1)
    gmsh.option.setNumber("Mesh.SaveGroupsOfNodes", 1)
    gmsh.option.setNumber("Mesh.SaveAll", 0)
    #gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
    # Netgen crashes
    gmsh.option.setNumber("Mesh.MaxNumThreads3D", 4)
    gmsh.option.setString("Geometry.OCCTargetUnit", 'mm')
    gmsh.option.setString("General.ErrorFileName", '/tmp/error.log')
    gmsh.option.setNumber('General.Terminal',1)

def maxCord(bbox) :
    maxList = [bbox.XLength, bbox.YLength, bbox.ZLength]
    #print(maxList)
    return max(maxList)

def meshObjShape(obj, dim) :
    obj.Shape.exportBrep("/tmp/Shape2Mesh.brep")
    bbox = obj.Shape.BoundBox
    ml = maxCord(bbox) / 10
    ml = 5 * ml
    print('Mesh length : '+str(ml))
    gmsh.open('/tmp/Shape2Mesh.brep')
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", ml)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", ml)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", ml)
    gmsh.model.mesh.generate(dim)
    print('Mesh Generated')
    gmsh.model.mesh.renumberNodes()
    gmsh.write('/tmp/test.msh')
    return True

def meshObjSTL(obj, dim) :
    obj.Mesh.write('/tmp/transfer.stl')
    bbox = obj.Mesh.BoundBox
    ml = maxCord(bbox) / 5
    print('Mesh length : '+str(ml))
    gmsh.option.setNumber("Mesh.RecombinationAlgorithm",2)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", ml)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", ml)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", ml)
    #gmsh.option.setNumber("Mesh.Optimize",1)
    #gmsh.option.setNumber("Mesh.QualityType",2)
    gmsh.merge('/tmp/transfer.stl')
    n = gmsh.model.getDimension()
    s = gmsh.model.getEntities(n)
    l = gmsh.model.geo.addSurfaceLoop([s[i][1] for i in range(len(s))])
    gmsh.model.geo.addVolume([l])
    print("Volume added")
    gmsh.model.geo.synchronize()
    gmsh.model.mesh.generate(dim)
    print('Mesh Generated '+str(dim))
    gmsh.model.mesh.renumberNodes()
    #printMyInfo()
    return True

def createGmshModelFromFC(fcMesh):
    # Not currently used
    gmsh.model.add('X2')
    gmsh.logger.start()
    print(dir(fcMesh.Points[0]))
    print(fcMesh.Points)
    nodes = range(0,fcMesh.CountPoints)
    coords = []
    for p in fcMesh.Points :
        coords.append([p.x, p.y, p.z])
    
    #gmsh.model.mesh.addNodes(2, 1, nodes, coords)
    for v in fcMesh.Facets :
        print('\n Facet')
        print(dir(v))
        print('Index : '+str(v.Index))
        print('PointIndices : '+str(v.PointIndices))
        print(v.Points)
        print(dir(v.Points))
        # Type 2 for 3-node triangle elements:
        try :
           gmsh.model.mesh.addElementsByType(v.Index, 2, [], v.PointIndices)
        except :
           log = gmsh.logger.get()
           print("Logger has recorded " + str(len(log)) + " lines")
           print(log)
           gmsh.logger.stop()

def meshObjMesh(obj,dim) :
    'Create GMSH from Mesh'
    print('Create gmsh from Mesh')
    meshObjSTL(obj,dim)
    return True

def meshObj(obj, dim) :
    # Create gmsh from shape or mesh
    # Clear any previous models
    gmsh.clear()
    if hasattr(obj,'Shape') :
       return(meshObjShape(obj, dim))

    elif hasattr(obj,'Mesh') :
       return(meshObjMesh(obj,dim))

def getVertexFacets() :
    print('Get Vertex Facets')
    # Element type 0 point, 1 line, 2 triangle 3 quadrangle 4 tetrahedron
    # Face types 3 triangle 4 quadrangle
    nodes, coordLst, pcords = gmsh.model.mesh.getNodes(2)
    faceNodes = gmsh.model.mesh.getElementFaceNodes(2,3,-1,True)
    # nodes, coords are numpy arrays
    print('Max : ' +str(np.amax(nodes)))
    minIdx = int(np.amin(nodes))
    print('Min : ' +str(minIdx))
    print('faceNodes : '+str(len(faceNodes)))
    # gmsh index starts 1
    # fc index starts 0
    facetList = np.subtract(faceNodes,minIdx-1)
    facets = [facetList[x:x+3] for x in range(0, len(facetList),3)]
    coords = [coordLst[x:x+3] for x in range(0, len(coordLst),3)]
    #print(type(facets))
    print('Number of facets : '+str(len(facets)))
    vertex = []
    print('Number coords : '+str(len(coords)))
    print('Number pcords : '+str(len(pcords)))
    for n in coords :
        print(n)
        vertex.append(FreeCAD.Vector(n[0],n[1],n[2]))
    #print(vertex)
    #print(facets)
    return vertex, facets

def getTetrahedrons():
    print('Get Tetrahedrons')
    tags, nodes = gmsh.model.mesh.getElementsByType(4)
    if len(nodes) > 0 :
       print('nodes : '+str(len(nodes)))
       #print(nodes[0])
       FCnodes = []
       for n in nodes :
           coord, pccord = gmsh.model.mesh.getNode(n)
           FCnodes.append(FreeCAD.Vector(coord[0],coord[1],coord[2]))
       TetList = [FCnodes[x:x+4] for x in range(0, len(FCnodes),4)]
       return TetList
    else :
       return None

def addFacet(msh, v0,v1,v2) :
    c = v0 + v1 + v2
    print(c)
    msh.addFacet(c[0],c[1],c[2],c[3],c[4],c[5],c[6],c[7],c[8])

def Tessellated2Mesh(obj) :
    import Mesh

    print('Tessellated 2 Mesh')
    if hasattr(obj.Proxy,'Facets') :
       print('Create Mesh')
       msh = Mesh.Mesh()
       v = obj.Proxy.Vertex
       print(v)
       for f in obj.Proxy.Facets :
           print(f)
           print(type(v[0]))
           ln = len(f)
           if ln == 3 :
              addFacet(msh,v[f[0]], v[f[1]],  v[f[2]])

           elif ln == 4 :
              addFacet(msh,v[f[0]], v[f[1]],  v[f[2]])
              addFacet(msh,v[f[0]], v[f[2]],  v[f[3]])

           else :
              FreeCAD.Console.PrintError('Invalid Facet length '+str(ln))

       return msh


def Tetrahedron2Mesh(obj) :
    print('Tetrahedron 2 Mesh')

def printMyInfo() :
    # Element type 0 point, 1 line, 2 triangle 3 quadrangle 4 tetrahedron
    # 5 pyramid, 6 hexahedron
    # Face types 3 triangle 4 quadrangle
    faces = gmsh.model.mesh.getElementFaceNodes(2,3)
    print('Face Nodes')
    print(len(faces))
    nodes, coords, parm = gmsh.model.mesh.getNodes(-1,2)
    print('Nodes with tag = 2')
    print(len(nodes))
    enodes, coords, parms = gmsh.model.mesh.getNodesByElementType(2)
    print('Nodes of type 2')
    print(len(enodes))
    #print(enodes)
    faceNodes = gmsh.model.mesh.getElementFaceNodes(0,3)
    print('Face Node')
    print(len(faceNodes))
    nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes(2)
    print('Get Nodes 2')
    print(len(nodeTags))
    #print(nodeTags)
    #print('Get Elements')
    elem, tags = gmsh.model.mesh.getElementsByType(2)
    #print(len(elem))
    #print(elem)
    #print(len(tags))
    #print(tags)

def printMeshInfo() :
    entities = gmsh.model.getEntities()
    for e in entities:
        print("Entity " + str(e) + " of type " + \
               gmsh.model.getType(e[0], e[1]))
        # get the mesh nodes for each elementary entity
        nodeTags, nodeCoords, nodeParams = \
               gmsh.model.mesh.getNodes(e[0], e[1])
        # get the mesh elements for each elementary entity
        elemTypes, elemTags, elemNodeTags = \
               gmsh.model.mesh.getElements(e[0], e[1])
        # count number of elements
        numElem = sum(len(i) for i in elemTags)
        print(" - mesh has " + str(len(nodeTags)) + " nodes and " + \
              str(numElem) + " elements")
        boundary = gmsh.model.getBoundary([e])
        print(" - boundary entities " + str(boundary))
        partitions = gmsh.model.getPartitions(e[0], e[1])
        if len(partitions):
           print(" - Partition tag(s): " + str(partitions) + \
               " - parent entity " + str(iself.Gmsh.model.getParent(e[0], e[1])))
        for t in elemTypes:
            name, dim, order, numv, parv, _ =  \
                     gmsh.model.mesh.getElementProperties(t) 
            print(" - Element type: " + name + ", order " + str(order) + \
                    " (" + str(numv) + " nodes in param coord: " + \
                     str(parv) + ")")

    # all mesh node coordinates
    nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes()
    x = dict(zip(nodeTags, nodeCoords[0::3]))
    y = dict(zip(nodeTags, nodeCoords[1::3]))
    z = dict(zip(nodeTags, nodeCoords[2::3]))
    #print(x)
    #print(y)
    #print(z)
