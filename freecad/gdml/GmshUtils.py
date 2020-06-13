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

#class GmshUtils :

import gmsh
import numpy as np

def initialize() :
    gmsh.initialize()
    gmsh.option.setNumber('Mesh.Algorithm3D',1)
    gmsh.option.setNumber("Geometry.OCCFixDegenerated", 1)
    gmsh.option.setNumber("Mesh.SaveGroupsOfNodes", 1)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 2)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 0)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", 1)
    gmsh.option.setNumber("Mesh.SaveAll", 0)
    gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
    gmsh.option.setNumber("Mesh.MaxNumThreads3D", 4)
    gmsh.option.setString("Geometry.OCCTargetUnit", 'mm');
    gmsh.option.setString("General.ErrorFileName", '/tmp/error.log');


def meshObj(obj, dim) :
    obj.Shape.exportBrep("/tmp/Shape2Mesh.brep")
    ab = gmsh.open('/tmp/Shape2Mesh.brep')
    gmsh.model.occ.synchronize()
    print(dir(ab))
    gmsh.model.mesh.generate(dim)
    print('Mesh Generated')
    gmsh.model.mesh.renumberNodes()

def getVertexFacets() :
    print('Get Vertex Facets')
    # Element type 0 point, 1 line, 2 triangle 3 quadrangle 4 tetrahedron
    # Face types 3 triangle 4 quadrangle
    faceNodes = gmsh.model.mesh.getElementFaceNodes(2,3)
    print('Max : ' +str(np.amax(faceNodes)))
    print('Min : ' +str(np.amin(faceNodes)))
    print(faceNodes)
    nodes, coord, pcords = gmsh.model.mesh.getNodes(2)
    start = int(np.amin(nodes))
    print('Start : '+str(start))
    #faceNodesNorm = np.subtract(faceNodes,1)
    faceNodesNorm = faceNodes
    faceNodesList = faceNodesNorm.tolist()
    facets = [faceNodesList[x:x+3] for x in range(0, len(faceNodesList),3)]
    vertex = []
    print('Coord')
    print(len(coord))
    print(coord[0])
    print(type(coord))
    print(coord)
    for n in coord :
        n3 = 3 * int(n)
        vertex.append(FreeCAD.Vector(coord[n3],coord[n3+1], \
                               coord[n3 + 2]))
    print(vertex)
    print(facets)
    return vertex, facets

def getTetrahedrons():
    print('Get Tetrahedrons')
    tags, nodes = gmsh.model.mesh.getElementsByType(4)
    print('nodes : '+str(len(nodes)))
    print(nodes[0])
    FCnodes = []
    for n in nodes :
        coord, pccord = gmsh.model.mesh.getNode(n)
        FCnodes.append(FreeCAD.Vector(coord[0],coord[1],coord[2]))
    TetList = [FCnodes[x:x+4] for x in range(0, len(FCnodes),4)]
    return TetList

def printMyInfo() :
    # Element type 0 point, 1 line, 2 triangle 3 quadrangle 4 tetrahedron
    # 5 pyramid, 6 hexahedron
    # Face types 3 triangle 4 quadrangle
    faces = gmsh.model.mesh.getElementFaceNodes(2,3)
    print('Face Nodes')
    print(len(faces))
    #print(faces)
    nodes, coords, parm = gmsh.model.mesh.getNodes(-1,2)
    print('Nodes with tag = 2')
    print(len(nodes))
    #print(nodes)
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
    print('Get Elements')
    elem, tags = gmsh.model.mesh.getElementsByType(2)
    print(len(elem))
    print(elem)
    print(len(tags))
    print(tags)

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
