# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2017 Keith Sloan <keith@sloan-home.co.uk>              *
# *             (c) Dam Lambert 2020                                          *
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
# **************************************************************************

import gmsh
import os
import numpy as np
import sys
import FreeCAD

__title__ = "FreeCAD GDML Workbench - Gmsh Utils"
__author__ = "Keith Sloan"
__url__ = ["http://www.freecadweb.org"]

"""
This Script includes the GUI Commands of the GDML module
"""

sys.path.append(
    "/usr/local/lib/python3.7/site-packages/gmsh-4.5.6-MacOSX-sdk/lib"
)


def Gmsh(obj):
    # Uses FreeCAD FEM
    import ObjectsFem
    from femmesh.gmshtools import GmshTools

    doc = FreeCAD.ActiveDocument
    print("Action Tessellate Mesh")
    femmesh_obj = ObjectsFem.makeMeshGmsh(doc, obj.Name + "_Mesh")
    femmesh_obj.Part = obj
    femmesh_obj.Algorithm2D = "DelQuad"
    doc.recompute()
    gm = GmshTools(femmesh_obj)
    error = gm.create_mesh()
    print(error)
    doc.recompute()


def initialize():
    try:
        gmsh.initialize()
    except:
        print(f"Gmsh shared library must be copied to FreeCAD Resources")    
    print(f"Gmsh version {gmsh.GMSH_API_VERSION}")
    gmsh.clear()
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    # gmsh.option.setNumber("Geometry.OCCFixDegenerated", 1)
    gmsh.option.setNumber("Mesh.SaveGroupsOfNodes", 1)
    gmsh.option.setNumber("Mesh.SaveAll", 0)
    # gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
    # Netgen crashes
    try:
        threads = max(1, os.cpu_count() - 2)
    except:
        threads = 1
    threads = 1
    print("Gmsh to use " + str(threads) + " threads")
    gmsh.option.setNumber("Mesh.MaxNumThreads2D", threads)
    gmsh.option.setNumber("Mesh.MaxNumThreads3D", threads)
    gmsh.option.setString("Geometry.OCCTargetUnit", "mm")
    gmsh.option.setString("General.ErrorFileName", "/tmp/error.log")
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 11)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 10)
    #gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 1e-3)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 1.0)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", 10)


def maxCord(bbox):
    maxList = [bbox.XLength, bbox.YLength, bbox.ZLength]
    # print(maxList)
    return max(maxList)


def getMeshLen(obj):
    if hasattr(obj, "Shape"):
        bbox = obj.Shape.BoundBox

    elif hasattr(obj, "Mesh"):
        bbox = obj.Mesh.BoundBox
    ml = maxCord(bbox) / 10
    print("Mesh length : " + str(ml))
    return ml


def setMinMeshParms(lm, lc, lp):
    gmsh.option.setNumber("Mesh.StlLinearDeflection", 1)
    gmsh.option.setNumber("Mesh.StlLinearDeflectionRelative", 0)
    gmsh.option.setNumber("Mesh.StlAngularDeflection", 0.5)
    gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 0)
    gmsh.option.setNumber("Mesh.RecombineOptimizeTopology", 0)
    gmsh.option.setNumber("Mesh.RecombineNodeRepositioning", 0)
    gmsh.option.setNumber("Mesh.RecombineMinimumQuality", 1e-3)

    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", lm)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", lc)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", lp)


def setMeshParms(algol, lm, lc, lp):
    gmsh.option.setNumber("Mesh.Algorithm", algol)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", lm)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", lc)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", lp)


def setAltMeshParms(meshParms, obj, tessObj):
    if meshParms == False:
        ml = getMeshLen(obj)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", ml)
        gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", ml)
        gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", ml)
    else:
        gmsh.option.setNumber(
            "Mesh.CharacteristicLengthMax", tessObj.m_maxLength
        )
        gmsh.option.setNumber(
            "Mesh.CharacteristicLengthFromCurvature", tessObj.m_curveLen
        )
        gmsh.option.setNumber(
            "Mesh.CharacteristicLengthFromPoints", tessObj.m_pointLen
        )


def meshObjShape(obj, dim):
    import tempfile

    print("Mesh Object Shape")
    tmpFile = tempfile.NamedTemporaryFile(suffix=".brep").name
    obj.Shape.exportBrep(tmpFile)
    gmsh.open(tmpFile)
    gmsh.model.occ.synchronize()
    gmsh.model.mesh.generate(dim)
    print("Mesh Generated")
    gmsh.model.mesh.renumberNodes()
    return True


def meshObjSTL(obj, dim):
    import tempfile

    tmpFile = tempfile.NamedTemporaryFile(suffix=".stl").name
    obj.Mesh.write(tmpFile)
    # gmsh.option.setNumber("Mesh.RecombinationAlgorithm",2)
    # gmsh.option.setNumber("Mesh.Optimize",1)
    # gmsh.option.setNumber("Mesh.QualityType",2)
    gmsh.merge(tmpFile)
    n = gmsh.model.getDimension()
    s = gmsh.model.getEntities(n)
    # l = gmsh.model.geo.addSurfaceLoop([s[i][1] for i in range(len(s))])
    # gmsh.model.geo.addVolume([l])
    # print("Volume added")
    gmsh.model.geo.synchronize()
    gmsh.model.mesh.generate(dim)
    print("Mesh Generated " + str(dim))
    # gmsh.model.mesh.renumberNodes()
    return True


def createGmshModelFromFC(fcMesh):
    print("CreateGsmhModelFromFC")
    # Not currently used
    gmsh.model.add("X2")
    gmsh.logger.start()
    #print(dir(fcMesh.Points[0]))
    print(fcMesh.Points)
    nodes = range(0, fcMesh.CountPoints)
    coords = []
    for p in fcMesh.Points:
        coords.append([p.x, p.y, p.z])

    # gmsh.model.mesh.addNodes(2, 1, nodes, coords)
    for v in fcMesh.Facets:
        print("\n Facet")
        print(dir(v))
        print("Index : " + str(v.Index))
        print("PointIndices : " + str(v.PointIndices))
        print(v.Points)
        print(dir(v.Points))
        # Type 2 for 3-node triangle elements:
        try:
            gmsh.model.mesh.addElementsByType(v.Index, 2, [], v.PointIndices)
        except:
            log = gmsh.logger.get()
            print("Logger has recorded " + str(len(log)) + " lines")
            print(log)
            gmsh.logger.stop()


def meshObjMesh(obj, dim):
    "Create GMSH from Mesh"
    print("Create gmsh from Mesh")
    meshObjSTL(obj, dim)
    return True


#def minMeshObject(obj, lm, lc, lp):
def minMeshObject(obj, sd, ad):
    import gmsh, math, MeshPart, tempfile

    # Create gmsh from shape or mesh
    # Clear any previous models
    # print('mesh Object - first Clear')
    print(f"minMeshObject sd {sd} ad {ad}")
    gmsh.clear()
    if hasattr(obj, "Shape"):
        print("minMesh Shape")
        tmpFile = tempfile.NamedTemporaryFile(suffix=".stl").name
        shape = obj.Shape.copy(False)
        #mesh = MeshPart.meshFromShape( Shape=shape, Fineness=2,
        #    SecondOrder=0, Optimize=1, AllowQuad=0,)
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=sd,
               AngularDeflection = math.radians(ad), Relative=False)
        mesh.write(tmpFile)
        #mesh.write("/tmp/meshFile.stl")
        gmsh.initialize()
        #gmsh.open(tmpFile)
        #setMinMeshParms(lm, lc, lp)
        #gmsh.model.mesh.importStl()
        gmsh.merge(tmpFile)
        gmsh.model.mesh.removeDuplicateNodes()  # optional
        gmsh.model.mesh.recombine()
        # gmsh.finalize()
        return True


def meshObject(obj, dim, algol, lm, lc, lp):
    # Create gmsh from shape or mesh
    # Clear any previous models
    print(f"mesh Object dim {dim} algol {algol} lm {lm} lc {lc} lp {lp}")
    gmsh.clear()
    setMeshParms(algol, lm, lc, lp)
    if hasattr(obj, "Shape"):
        return meshObjShape(obj, dim)

    elif hasattr(obj, "Mesh"):
        return meshObjMesh(obj, dim)


def meshObj(obj, dim, meshParms=False, tessObj=None):
    # Used by Tetrahedron - Retire
    # Create gmsh from shape or mesh
    # Clear any previous models
    gmsh.clear()
    setAltMeshParms(meshParms, obj, tessObj)
    if hasattr(obj, "Shape"):
        return meshObjShape(obj, dim)

    elif hasattr(obj, "Mesh"):
        return meshObjMesh(obj, dim)


def getVertex():
    # Attempt at bulk getting coordinate
    print("Gmsh - GetNodes")
    nodes, coordLst, pcords = gmsh.model.mesh.getNodes()
    # print('coords datatype : '+str(coordLst.dtype))
    # int does not work needs to be float at least
    # coordLst = coordLst.astype('int32')
    coords = [coordLst[x : x + 3] for x in range(0, len(coordLst), 3)]
    print("Number coords : " + str(len(coords)))
    vertex = []
    # print('Coords')
    for n in coords:
        # print(n)
        # print(n[0],n[1],n[2])
        vertex.append(FreeCAD.Vector(n[0], n[1], n[2]))
    return vertex


def getFacetsByType0(elementType):
    print(f"Get Facets By Type {elementType}")
    # Element type 0 point, 1 line, 2 triangle 3 quadrangle 4 tetrahedron
    # Face types 3 triangle 4 quadrangle
    # Get Triangle Facets
    # Get Elements
    # eTypes, tags, faceNodes = gmsh.model.mesh.getElements(-1,-1)
    # print(eTypes[0:3])
    tags, faceNodes = gmsh.model.mesh.getElementsByType(elementType)
    # print('faceNodes datatype : '+str(faceNodes.dtype))
    # nodes, coords are numpy arrays
    faceNodes = faceNodes.astype("int32")
    print(faceNodes)
    if len(faceNodes) > 1:
        maxIdx = np.amax(faceNodes)
        print("Max : " + str(np.amax(faceNodes)))
        minIdx = int(np.amin(faceNodes))
        print("Min : " + str(minIdx))
        print("faceNodes : " + str(len(faceNodes)))
        # gmsh index starts 1
        # fc index starts 0
        # if minIdx > 1 :
        #   facetList = np.subtract(faceNodes,minIdx-1)
        # else :
        #   facetList = faceNodes
        #
        facetList = np.subtract(faceNodes, minIdx)
        facePoints = elementType + 1

        facets = [
            facetList[x : x + facePoints]
            for x in range(0, len(facetList), facePoints)
        ]
        print("Number of facets : " + str(len(facets)))
        # print('Facets')
        # for f in facets :
        #   print(f)
        return facets

    else:
        return []


def getFacetsByType(elementType):
    print(f"Get Facets By Type {elementType}")
    # Element type 0 point, 1 line, 2 triangle 3 quadrangle 4 tetrahedron
    # Face types 3 triangle 4 quadrangle
    # Get Triangle Facets
    # Get Elements
    # eTypes, tags, faceNodes = gmsh.model.mesh.getElements(-1,-1)
    # print(eTypes[0:3])
    tags, faceNodes = gmsh.model.mesh.getElementsByType(elementType)
    # print('faceNodes datatype : '+str(faceNodes.dtype))
    # nodes, coords are numpy arrays
    faceNodes = faceNodes.astype("int32")
    #print(faceNodes)
    if len(faceNodes) > 1:
        maxIdx = np.amax(faceNodes)
        print("Max : " + str(np.amax(faceNodes)))
        minIdx = int(np.amin(faceNodes))
        print("Min : " + str(minIdx))
        print("faceNodes : " + str(len(faceNodes)))
        # gmsh index starts 1
        # fc index starts 0
        if minIdx > 0:
            facetList = np.subtract(faceNodes, 1)
        else:
            facetList = faceNodes

        # facetList = np.subtract(faceNodes, minIdx)
        facePoints = elementType + 1

        facets = [
            facetList[x : x + facePoints]
            for x in range(0, len(facetList), facePoints)
        ]
        print("Number of facets : " + str(len(facets)))
        # print('Facets')
        # for f in facets :
        #   print(f)
        return facets

    else:
        return []


def getFacets():
    fct2 = getFacetsByType(2)
    print(f"type 2 {type(fct2)} {len(fct2)}")
    fct3 = getFacetsByType(3)
    print(f"type 3 {type(fct3)} {len(fct3)}")
    return fct2 + fct3


def getTetrahedrons():
    print("Get Tetrahedrons")
    tags, nodesLst = gmsh.model.mesh.getElementsByType(4)
    nodes = np.subtract(nodesLst, 1)

    vertex = getVertex()
    if len(nodes) > 0:
        print("nodes : " + str(len(nodes)))
        FCnodes = []
        for n in nodes:
            # print('n : '+str(n))
            FCnodes.append(vertex[n])
        TetList = [FCnodes[x : x + 4] for x in range(0, len(FCnodes), 4)]
        return TetList
    else:
        FreeCAD.Console.PrintWarning(
            "Unable to create quad faces for this shape"
        )
        return None


def vertex2Vector(v):
    return FreeCAD.Vector(v.X, v.Y, v.Z)


def addFacet(msh, v0, v1, v2):
    # print('Add Facet')
    # msh.addFacet(v0[0],v0[1],v0[2],v1[0],v1[1],v1[2],v2[0],v2[1],v2[2])
    # print(v0)
    # print(v1)
    # print(v2)
    # msh.addFacet(FreeCAD.Vector(v0),FreeCAD.Vector(v1),FreeCAD.Vector(v2))
    msh.addFacet(vertex2Vector(v0), vertex2Vector(v1), vertex2Vector(v2))


def TessellatedShape2Mesh(obj):
    import Mesh

    msh = Mesh.Mesh()
    # v = obj.Shape.Vertexes
    # print(dir(obj.Shape.Faces))
    for f in obj.Shape.Faces:
        # print('Deal with Triangular Faces')
        # addFacet(msh,v[f.Vertexes[0]], v[f.Vertexes[1]],  v[f.Vertexes[2]])
        addFacet(msh, f.Vertexes[0], f.Vertexes[1], f.Vertexes[2])
        if len(f.Edges) == 4:
            # print('Deal with Quad Faces')
            # addFacet(msh,v[f.Vertexes[0]], v[f.vertexes[2]],  v[f.vertexes[3]])
            addFacet(msh, f.Vertexes[0], f.vertexes[2], f.vertexes[3])
    return msh


def Tessellated2Mesh(obj):
    # Should now be redundant as replaced by TessellatedShape2Mesh
    import Mesh

    print("Tessellated 2 Mesh : " + obj.Label)
    if hasattr(obj.Proxy, "Facets"):
        print("Has proxy - Create Mesh")
        msh = Mesh.Mesh()
        v = obj.Proxy.Vertex
        # print(v)
        for f in obj.Proxy.Facets:
            # print(f)
            # print(type(v[0]))
            addFacet(msh, v[f[0]], v[f[1]], v[f[2]])
            if len(f) == 4:
                addFacet(msh, v[f[0]], v[f[2]], v[f[3]])
        return msh
    else:
        print(dir(obj))


def Tetrahedron2Mesh(obj):
    import Mesh

    print("Tetrahedron 2 Mesh")
    #print(dir(obj.Proxy))
    print(obj.Proxy.Tetra[:10])
    tetList = obj.Proxy.Tetra
    # print('Len tetra : '+str(len(tetList)))
    # print(tetList[:8])
    # print('Create Mesh')
    msh = Mesh.Mesh()
    for tet in tetList:
        # print('tet')
        # print(tet)
        addFacet(msh, tet[0], tet[1], tet[2])
        if len(tet) == 4:
            addFacet(msh, tet[0], tet[2], tet[3])
    return msh


def printMyInfo():
    # Element type 0 point, 1 line, 2 triangle 3 quadrangle 4 tetrahedron
    # 5 pyramid, 6 hexahedron
    # Face types 3 triangle 4 quadrangle
    faces = gmsh.model.mesh.getElementFaceNodes(2, 3)
    print("Face Nodes")
    print(len(faces))
    nodes, coords, parm = gmsh.model.mesh.getNodes(-1, 2)
    print("Nodes with tag = 2")
    print(len(nodes))
    enodes, coords, parms = gmsh.model.mesh.getNodesByElementType(2)
    print("Nodes of type 2")
    print(len(enodes))
    # print(enodes)
    faceNodes = gmsh.model.mesh.getElementFaceNodes(0, 3)
    print("Face Node")
    print(len(faceNodes))
    nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes(2)
    print("Get Nodes 2")
    print(len(nodeTags))
    # print(nodeTags)
    # print('Get Elements')
    elem, tags = gmsh.model.mesh.getElementsByType(2)
    # print(len(elem))
    # print(elem)
    # print(len(tags))
    # print(tags)


def printMeshInfo():
    entities = gmsh.model.getEntities()
    for e in entities:
        print(
            "Entity " + str(e) + " of type " + gmsh.model.getType(e[0], e[1])
        )
        # get the mesh nodes for each elementary entity
        nodeTags, nodeCoords, nodeParams = gmsh.model.mesh.getNodes(e[0], e[1])
        # get the mesh elements for each elementary entity
        elemTypes, elemTags, elemNodeTags = gmsh.model.mesh.getElements(
            e[0], e[1]
        )
        # count number of elements
        numElem = sum(len(i) for i in elemTags)
        print(
            " - mesh has "
            + str(len(nodeTags))
            + " nodes and "
            + str(numElem)
            + " elements"
        )
        boundary = gmsh.model.getBoundary([e])
        print(" - boundary entities " + str(boundary))
        partitions = gmsh.model.getPartitions(e[0], e[1])
        if len(partitions):
            print(
                " - Partition tag(s): "
                + str(partitions)
                + " - parent entity "
                + str(self.Gmsh.model.getParent(e[0], e[1]))
            )
        for t in elemTypes:
            (
                name,
                dim,
                order,
                numv,
                parv,
                _,
            ) = gmsh.model.mesh.getElementProperties(t)
            print(
                " - Element type: "
                + name
                + ", order "
                + str(order)
                + " ("
                + str(numv)
                + " nodes in param coord: "
                + str(parv)
                + ")"
            )

    # all mesh node coordinates
    nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes()
    x = dict(zip(nodeTags, nodeCoords[0::3]))
    y = dict(zip(nodeTags, nodeCoords[1::3]))
    z = dict(zip(nodeTags, nodeCoords[2::3]))
    # print(x)
    # print(y)
    # print(z)
# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2017 Keith Sloan <keith@sloan-home.co.uk>              *
# *             (c) Dam Lambert 2020                                          *
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
# **************************************************************************

import gmsh
import os
import numpy as np
import sys
import FreeCAD

__title__ = "FreeCAD GDML Workbench - Gmsh Utils"
__author__ = "Keith Sloan"
__url__ = ["http://www.freecadweb.org"]

"""
This Script includes the GUI Commands of the GDML module
"""

sys.path.append(
    "/usr/local/lib/python3.7/site-packages/gmsh-4.5.6-MacOSX-sdk/lib"
)


def Gmsh(obj):
    # Uses FreeCAD FEM
    import ObjectsFem
    from femmesh.gmshtools import GmshTools

    doc = FreeCAD.ActiveDocument
    print("Action Tessellate Mesh")
    femmesh_obj = ObjectsFem.makeMeshGmsh(doc, obj.Name + "_Mesh")
    femmesh_obj.Part = obj
    femmesh_obj.Algorithm2D = "DelQuad"
    doc.recompute()
    gm = GmshTools(femmesh_obj)
    error = gm.create_mesh()
    print(error)
    doc.recompute()


def initialize():
    gmsh.initialize()
    print(f"Gmsh version {gmsh.GMSH_API_VERSION}")
    gmsh.clear()
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    # gmsh.option.setNumber("Geometry.OCCFixDegenerated", 1)
    gmsh.option.setNumber("Mesh.SaveGroupsOfNodes", 1)
    gmsh.option.setNumber("Mesh.SaveAll", 0)
    # gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
    # Netgen crashes
    try:
        threads = max(1, os.cpu_count() - 2)
    except:
        threads = 1
    threads = 1
    print("Gmsh to use " + str(threads) + " threads")
    gmsh.option.setNumber("Mesh.MaxNumThreads2D", threads)
    gmsh.option.setNumber("Mesh.MaxNumThreads3D", threads)
    gmsh.option.setString("Geometry.OCCTargetUnit", "mm")
    gmsh.option.setString("General.ErrorFileName", "/tmp/error.log")
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 11)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 10)
    #gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 1e-3)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 1.0)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", 10)


def maxCord(bbox):
    maxList = [bbox.XLength, bbox.YLength, bbox.ZLength]
    # print(maxList)
    return max(maxList)


def getMeshLen(obj):
    if hasattr(obj, "Shape"):
        bbox = obj.Shape.BoundBox

    elif hasattr(obj, "Mesh"):
        bbox = obj.Mesh.BoundBox
    ml = maxCord(bbox) / 10
    print("Mesh length : " + str(ml))
    return ml


def setMinMeshParms(lm, lc, lp):
    gmsh.option.setNumber("Mesh.StlLinearDeflection", 1)
    gmsh.option.setNumber("Mesh.StlLinearDeflectionRelative", 0)
    gmsh.option.setNumber("Mesh.StlAngularDeflection", 0.5)
    gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 0)
    gmsh.option.setNumber("Mesh.RecombineOptimizeTopology", 0)
    gmsh.option.setNumber("Mesh.RecombineNodeRepositioning", 0)
    gmsh.option.setNumber("Mesh.RecombineMinimumQuality", 1e-3)

    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", lm)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", lc)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", lp)


def setMeshParms(algol, lm, lc, lp):
    gmsh.option.setNumber("Mesh.Algorithm", algol)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", lm)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", lc)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", lp)


def setAltMeshParms(meshParms, obj, tessObj):
    if meshParms == False:
        ml = getMeshLen(obj)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", ml)
        gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", ml)
        gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", ml)
    else:
        gmsh.option.setNumber(
            "Mesh.CharacteristicLengthMax", tessObj.m_maxLength
        )
        gmsh.option.setNumber(
            "Mesh.CharacteristicLengthFromCurvature", tessObj.m_curveLen
        )
        gmsh.option.setNumber(
            "Mesh.CharacteristicLengthFromPoints", tessObj.m_pointLen
        )


def meshObjShape(obj, dim):
    import tempfile

    print("Mesh Object Shape")
    tmpFile = tempfile.NamedTemporaryFile(suffix=".brep").name
    obj.Shape.exportBrep(tmpFile)
    gmsh.open(tmpFile)
    gmsh.model.occ.synchronize()
    gmsh.model.mesh.generate(dim)
    print("Mesh Generated")
    gmsh.model.mesh.renumberNodes()
    return True


def meshObjSTL(obj, dim):
    import tempfile

    tmpFile = tempfile.NamedTemporaryFile(suffix=".stl").name
    obj.Mesh.write(tmpFile)
    # gmsh.option.setNumber("Mesh.RecombinationAlgorithm",2)
    # gmsh.option.setNumber("Mesh.Optimize",1)
    # gmsh.option.setNumber("Mesh.QualityType",2)
    gmsh.merge(tmpFile)
    n = gmsh.model.getDimension()
    s = gmsh.model.getEntities(n)
    # l = gmsh.model.geo.addSurfaceLoop([s[i][1] for i in range(len(s))])
    # gmsh.model.geo.addVolume([l])
    # print("Volume added")
    gmsh.model.geo.synchronize()
    gmsh.model.mesh.generate(dim)
    print("Mesh Generated " + str(dim))
    # gmsh.model.mesh.renumberNodes()
    return True


def createGmshModelFromFC(fcMesh):
    print("CreateGsmhModelFromFC")
    # Not currently used
    gmsh.model.add("X2")
    gmsh.logger.start()
    #print(dir(fcMesh.Points[0]))
    print(fcMesh.Points)
    nodes = range(0, fcMesh.CountPoints)
    coords = []
    for p in fcMesh.Points:
        coords.append([p.x, p.y, p.z])

    # gmsh.model.mesh.addNodes(2, 1, nodes, coords)
    for v in fcMesh.Facets:
        print("\n Facet")
        #print(dir(v))
        print("Index : " + str(v.Index))
        print("PointIndices : " + str(v.PointIndices))
        print(v.Points)
        #print(dir(v.Points))
        # Type 2 for 3-node triangle elements:
        try:
            gmsh.model.mesh.addElementsByType(v.Index, 2, [], v.PointIndices)
        except:
            log = gmsh.logger.get()
            print("Logger has recorded " + str(len(log)) + " lines")
            print(log)
            gmsh.logger.stop()


def meshObjMesh(obj, dim):
    "Create GMSH from Mesh"
    print("Create gmsh from Mesh")
    meshObjSTL(obj, dim)
    return True


#def minMeshObject(obj, lm, lc, lp):
def minMeshObject(obj, sd, ad):
    import gmsh, math, MeshPart, tempfile

    # Create gmsh from shape or mesh
    # Clear any previous models
    # print('mesh Object - first Clear')
    print(f"minMeshObject")
    gmsh.clear()
    if hasattr(obj, "Shape"):
        print("minMesh Shape")
        tmpFile = tempfile.NamedTemporaryFile(suffix=".stl").name
        shape = obj.Shape.copy(False)
        #mesh = MeshPart.meshFromShape( Shape=shape, Fineness=2,
        #    SecondOrder=0, Optimize=1, AllowQuad=0,)
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=sd,
               AngularDeflection = math.radians(ad), Relative=False)
        mesh.write(tmpFile)
        #mesh.write("/tmp/meshFile.stl")
        gmsh.initialize()
        #gmsh.open(tmpFile)
        #setMinMeshParms(lm, lc, lp)
        #gmsh.model.mesh.importStl()
        gmsh.merge(tmpFile)
        gmsh.model.mesh.removeDuplicateNodes()  # optional
        gmsh.model.mesh.recombine()
        # gmsh.finalize()
        return True



def meshObj(obj, dim, meshParms=False, tessObj=None):
    # Used by Tetrahedron - Retire
    # Create gmsh from shape or mesh
    # Clear any previous models
    gmsh.clear()
    setAltMeshParms(meshParms, obj, tessObj)
    if hasattr(obj, "Shape"):
        return meshObjShape(obj, dim)

    elif hasattr(obj, "Mesh"):
        return meshObjMesh(obj, dim)


def getVertex():
    # Attempt at bulk getting coordinate
    print("Gmsh - GetNodes")
    nodes, coordLst, pcords = gmsh.model.mesh.getNodes()
    # print('coords datatype : '+str(coordLst.dtype))
    # int does not work needs to be float at least
    # coordLst = coordLst.astype('int32')
    coords = [coordLst[x : x + 3] for x in range(0, len(coordLst), 3)]
    print("Number coords : " + str(len(coords)))
    vertex = []
    # print('Coords')
    for n in coords:
        # print(n)
        # print(n[0],n[1],n[2])
        vertex.append(FreeCAD.Vector(n[0], n[1], n[2]))
    return vertex


def getFacetsByType0(elementType):
    print(f"Get Facets By Type {elementType}")
    # Element type 0 point, 1 line, 2 triangle 3 quadrangle 4 tetrahedron
    # Face types 3 triangle 4 quadrangle
    # Get Triangle Facets
    # Get Elements
    # eTypes, tags, faceNodes = gmsh.model.mesh.getElements(-1,-1)
    # print(eTypes[0:3])
    tags, faceNodes = gmsh.model.mesh.getElementsByType(elementType)
    # print('faceNodes datatype : '+str(faceNodes.dtype))
    # nodes, coords are numpy arrays
    faceNodes = faceNodes.astype("int32")
    print(faceNodes)
    if len(faceNodes) > 1:
        maxIdx = np.amax(faceNodes)
        print("Max : " + str(np.amax(faceNodes)))
        minIdx = int(np.amin(faceNodes))
        print("Min : " + str(minIdx))
        print("faceNodes : " + str(len(faceNodes)))
        # gmsh index starts 1
        # fc index starts 0
        # if minIdx > 1 :
        #   facetList = np.subtract(faceNodes,minIdx-1)
        # else :
        #   facetList = faceNodes
        #
        facetList = np.subtract(faceNodes, minIdx)
        facePoints = elementType + 1

        facets = [
            facetList[x : x + facePoints]
            for x in range(0, len(facetList), facePoints)
        ]
        print("Number of facets : " + str(len(facets)))
        # print('Facets')
        # for f in facets :
        #   print(f)
        return facets

    else:
        return []


def getFacetsByType(elementType):
    print(f"Get Facets By Type {elementType}")
    # Element type 0 point, 1 line, 2 triangle 3 quadrangle 4 tetrahedron
    # Face types 3 triangle 4 quadrangle
    # Get Triangle Facets
    # Get Elements
    # eTypes, tags, faceNodes = gmsh.model.mesh.getElements(-1,-1)
    # print(eTypes[0:3])
    tags, faceNodes = gmsh.model.mesh.getElementsByType(elementType)
    # print('faceNodes datatype : '+str(faceNodes.dtype))
    # nodes, coords are numpy arrays
    faceNodes = faceNodes.astype("int32")
    #print(faceNodes)
    if len(faceNodes) > 1:
        maxIdx = np.amax(faceNodes)
        print("Max : " + str(np.amax(faceNodes)))
        minIdx = int(np.amin(faceNodes))
        print("Min : " + str(minIdx))
        print("faceNodes : " + str(len(faceNodes)))
        # gmsh index starts 1
        # fc index starts 0
        if minIdx > 0:
            facetList = np.subtract(faceNodes, 1)
        else:
            facetList = faceNodes

        # facetList = np.subtract(faceNodes, minIdx)
        facePoints = elementType + 1

        facets = [
            facetList[x : x + facePoints]
            for x in range(0, len(facetList), facePoints)
        ]
        print("Number of facets : " + str(len(facets)))
        # print('Facets')
        # for f in facets :
        #   print(f)
        return facets

    else:
        return []


def getFacets():
    fct2 = getFacetsByType(2)
    print(f"type 2 {type(fct2)} {len(fct2)}")
    fct3 = getFacetsByType(3)
    print(f"type 3 {type(fct3)} {len(fct3)}")
    return fct2 + fct3


def getTetrahedrons():
    print("Get Tetrahedrons")
    tags, nodesLst = gmsh.model.mesh.getElementsByType(4)
    nodes = np.subtract(nodesLst, 1)

    vertex = getVertex()
    if len(nodes) > 0:
        print("nodes : " + str(len(nodes)))
        FCnodes = []
        for n in nodes:
            # print('n : '+str(n))
            FCnodes.append(vertex[n])
        TetList = [FCnodes[x : x + 4] for x in range(0, len(FCnodes), 4)]
        return TetList
    else:
        FreeCAD.Console.PrintWarning(
            "Unable to create quad faces for this shape"
        )
        return None


def vertex2Vector(v):
    return FreeCAD.Vector(v.X, v.Y, v.Z)


def addFacet(msh, v0, v1, v2):
    # print('Add Facet')
    # msh.addFacet(v0[0],v0[1],v0[2],v1[0],v1[1],v1[2],v2[0],v2[1],v2[2])
    # print(v0)
    # print(v1)
    # print(v2)
    # msh.addFacet(FreeCAD.Vector(v0),FreeCAD.Vector(v1),FreeCAD.Vector(v2))
    msh.addFacet(vertex2Vector(v0), vertex2Vector(v1), vertex2Vector(v2))


def TessellatedShape2Mesh(obj):
    import Mesh

    msh = Mesh.Mesh()
    # v = obj.Shape.Vertexes
    # print(dir(obj.Shape.Faces))
    for f in obj.Shape.Faces:
        # print('Deal with Triangular Faces')
        # addFacet(msh,v[f.Vertexes[0]], v[f.Vertexes[1]],  v[f.Vertexes[2]])
        addFacet(msh, f.Vertexes[0], f.Vertexes[1], f.Vertexes[2])
        if len(f.Edges) == 4:
            # print('Deal with Quad Faces')
            # addFacet(msh,v[f.Vertexes[0]], v[f.vertexes[2]],  v[f.vertexes[3]])
            addFacet(msh, f.Vertexes[0], f.vertexes[2], f.vertexes[3])
    return msh


def Tessellated2Mesh(obj):
    # Should now be redundant as replaced by TessellatedShape2Mesh
    import Mesh

    print("Tessellated 2 Mesh : " + obj.Label)
    if hasattr(obj.Proxy, "Facets"):
        print("Has proxy - Create Mesh")
        msh = Mesh.Mesh()
        v = obj.Proxy.Vertex
        # print(v)
        for f in obj.Proxy.Facets:
            # print(f)
            # print(type(v[0]))
            addFacet(msh, v[f[0]], v[f[1]], v[f[2]])
            if len(f) == 4:
                addFacet(msh, v[f[0]], v[f[2]], v[f[3]])
        return msh
    else:
        print(dir(obj))


def Tetrahedron2Mesh(obj):
    import Mesh

    print("Tetrahedron 2 Mesh")
    #print(dir(obj.Proxy))
    print(obj.Proxy.Tetra[:10])
    tetList = obj.Proxy.Tetra
    # print('Len tetra : '+str(len(tetList)))
    # print(tetList[:8])
    # print('Create Mesh')
    msh = Mesh.Mesh()
    for tet in tetList:
        # print('tet')
        # print(tet)
        addFacet(msh, tet[0], tet[1], tet[2])
        if len(tet) == 4:
            addFacet(msh, tet[0], tet[2], tet[3])
    return msh


def printMyInfo():
    # Element type 0 point, 1 line, 2 triangle 3 quadrangle 4 tetrahedron
    # 5 pyramid, 6 hexahedron
    # Face types 3 triangle 4 quadrangle
    faces = gmsh.model.mesh.getElementFaceNodes(2, 3)
    print("Face Nodes")
    print(len(faces))
    nodes, coords, parm = gmsh.model.mesh.getNodes(-1, 2)
    print("Nodes with tag = 2")
    print(len(nodes))
    enodes, coords, parms = gmsh.model.mesh.getNodesByElementType(2)
    print("Nodes of type 2")
    print(len(enodes))
    # print(enodes)
    faceNodes = gmsh.model.mesh.getElementFaceNodes(0, 3)
    print("Face Node")
    print(len(faceNodes))
    nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes(2)
    print("Get Nodes 2")
    print(len(nodeTags))
    # print(nodeTags)
    # print('Get Elements')
    elem, tags = gmsh.model.mesh.getElementsByType(2)
    # print(len(elem))
    # print(elem)
    # print(len(tags))
    # print(tags)


def printMeshInfo():
    entities = gmsh.model.getEntities()
    for e in entities:
        print(
            "Entity " + str(e) + " of type " + gmsh.model.getType(e[0], e[1])
        )
        # get the mesh nodes for each elementary entity
        nodeTags, nodeCoords, nodeParams = gmsh.model.mesh.getNodes(e[0], e[1])
        # get the mesh elements for each elementary entity
        elemTypes, elemTags, elemNodeTags = gmsh.model.mesh.getElements(
            e[0], e[1]
        )
        # count number of elements
        numElem = sum(len(i) for i in elemTags)
        print(
            " - mesh has "
            + str(len(nodeTags))
            + " nodes and "
            + str(numElem)
            + " elements"
        )
        boundary = gmsh.model.getBoundary([e])
        print(" - boundary entities " + str(boundary))
        partitions = gmsh.model.getPartitions(e[0], e[1])
        if len(partitions):
            print(
                " - Partition tag(s): "
                + str(partitions)
                + " - parent entity "
                + str(self.Gmsh.model.getParent(e[0], e[1]))
            )
        for t in elemTypes:
            (
                name,
                dim,
                order,
                numv,
                parv,
                _,
            ) = gmsh.model.mesh.getElementProperties(t)
            print(
                " - Element type: "
                + name
                + ", order "
                + str(order)
                + " ("
                + str(numv)
                + " nodes in param coord: "
                + str(parv)
                + ")"
            )

    # all mesh node coordinates
    nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes()
    x = dict(zip(nodeTags, nodeCoords[0::3]))
    y = dict(zip(nodeTags, nodeCoords[1::3]))
    z = dict(zip(nodeTags, nodeCoords[2::3]))
    # print(x)
    # print(y)
    # print(z)
# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2017 Keith Sloan <keith@sloan-home.co.uk>              *
# *             (c) Dam Lambert 2020                                          *
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
# **************************************************************************

import gmsh
import os
import numpy as np
import sys
import FreeCAD

__title__ = "FreeCAD GDML Workbench - Gmsh Utils"
__author__ = "Keith Sloan"
__url__ = ["http://www.freecadweb.org"]

"""
This Script includes the GUI Commands of the GDML module
"""

sys.path.append(
    "/usr/local/lib/python3.7/site-packages/gmsh-4.5.6-MacOSX-sdk/lib"
)


def Gmsh(obj):
    # Uses FreeCAD FEM
    import ObjectsFem
    from femmesh.gmshtools import GmshTools

    doc = FreeCAD.ActiveDocument
    print("Action Tessellate Mesh")
    femmesh_obj = ObjectsFem.makeMeshGmsh(doc, obj.Name + "_Mesh")
    femmesh_obj.Part = obj
    femmesh_obj.Algorithm2D = "DelQuad"
    doc.recompute()
    gm = GmshTools(femmesh_obj)
    error = gm.create_mesh()
    print(error)
    doc.recompute()


def initialize():
    gmsh.initialize()
    print(f"Gmsh version {gmsh.GMSH_API_VERSION}")
    gmsh.clear()
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    # gmsh.option.setNumber("Geometry.OCCFixDegenerated", 1)
    gmsh.option.setNumber("Mesh.SaveGroupsOfNodes", 1)
    gmsh.option.setNumber("Mesh.SaveAll", 0)
    # gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
    # Netgen crashes
    try:
        threads = max(1, os.cpu_count() - 2)
    except:
        threads = 1
    threads = 1
    print("Gmsh to use " + str(threads) + " threads")
    gmsh.option.setNumber("Mesh.MaxNumThreads2D", threads)
    gmsh.option.setNumber("Mesh.MaxNumThreads3D", threads)
    gmsh.option.setString("Geometry.OCCTargetUnit", "mm")
    gmsh.option.setString("General.ErrorFileName", "/tmp/error.log")
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 11)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 10)
    #gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 1e-3)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 1.0)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", 10)


def maxCord(bbox):
    maxList = [bbox.XLength, bbox.YLength, bbox.ZLength]
    # print(maxList)
    return max(maxList)


def getMeshLen(obj):
    if hasattr(obj, "Shape"):
        bbox = obj.Shape.BoundBox

    elif hasattr(obj, "Mesh"):
        bbox = obj.Mesh.BoundBox
    ml = maxCord(bbox) / 10
    print("Mesh length : " + str(ml))
    return ml


def setMinMeshParms(lm, lc, lp):
    gmsh.option.setNumber("Mesh.StlLinearDeflection", 1)
    gmsh.option.setNumber("Mesh.StlLinearDeflectionRelative", 0)
    gmsh.option.setNumber("Mesh.StlAngularDeflection", 0.5)
    gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 0)
    gmsh.option.setNumber("Mesh.RecombineOptimizeTopology", 0)
    gmsh.option.setNumber("Mesh.RecombineNodeRepositioning", 0)
    gmsh.option.setNumber("Mesh.RecombineMinimumQuality", 1e-3)

    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", lm)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", lc)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", lp)


def setMeshParms(algol, lm, lc, lp):
    gmsh.option.setNumber("Mesh.Algorithm", algol)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", lm)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", lc)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", lp)


def setAltMeshParms(meshParms, obj, tessObj):
    if meshParms == False:
        ml = getMeshLen(obj)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", ml)
        gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", ml)
        gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", ml)
    else:
        gmsh.option.setNumber(
            "Mesh.CharacteristicLengthMax", tessObj.m_maxLength
        )
        gmsh.option.setNumber(
            "Mesh.CharacteristicLengthFromCurvature", tessObj.m_curveLen
        )
        gmsh.option.setNumber(
            "Mesh.CharacteristicLengthFromPoints", tessObj.m_pointLen
        )


def meshObjShape(obj, dim):
    import tempfile

    print("Mesh Object Shape")
    tmpFile = tempfile.NamedTemporaryFile(suffix=".brep").name
    obj.Shape.exportBrep(tmpFile)
    gmsh.open(tmpFile)
    gmsh.model.occ.synchronize()
    gmsh.model.mesh.generate(dim)
    print("Mesh Generated")
    gmsh.model.mesh.renumberNodes()
    return True


def meshObjSTL(obj, dim):
    import tempfile

    tmpFile = tempfile.NamedTemporaryFile(suffix=".stl").name
    obj.Mesh.write(tmpFile)
    # gmsh.option.setNumber("Mesh.RecombinationAlgorithm",2)
    # gmsh.option.setNumber("Mesh.Optimize",1)
    # gmsh.option.setNumber("Mesh.QualityType",2)
    gmsh.merge(tmpFile)
    n = gmsh.model.getDimension()
    s = gmsh.model.getEntities(n)
    # l = gmsh.model.geo.addSurfaceLoop([s[i][1] for i in range(len(s))])
    # gmsh.model.geo.addVolume([l])
    # print("Volume added")
    gmsh.model.geo.synchronize()
    gmsh.model.mesh.generate(dim)
    print("Mesh Generated " + str(dim))
    # gmsh.model.mesh.renumberNodes()
    return True


def createGmshModelFromFC(fcMesh):
    print("CreateGsmhModelFromFC")
    # Not currently used
    gmsh.model.add("X2")
    gmsh.logger.start()
    #print(dir(fcMesh.Points[0]))
    print(fcMesh.Points)
    nodes = range(0, fcMesh.CountPoints)
    coords = []
    for p in fcMesh.Points:
        coords.append([p.x, p.y, p.z])

    # gmsh.model.mesh.addNodes(2, 1, nodes, coords)
    for v in fcMesh.Facets:
        print("\n Facet")
        #print(dir(v))
        print("Index : " + str(v.Index))
        print("PointIndices : " + str(v.PointIndices))
        print(v.Points)
        #print(dir(v.Points))
        # Type 2 for 3-node triangle elements:
        try:
            gmsh.model.mesh.addElementsByType(v.Index, 2, [], v.PointIndices)
        except:
            log = gmsh.logger.get()
            print("Logger has recorded " + str(len(log)) + " lines")
            print(log)
            gmsh.logger.stop()


def meshObjMesh(obj, dim):
    "Create GMSH from Mesh"
    print("Create gmsh from Mesh")
    meshObjSTL(obj, dim)
    return True


#def minMeshObject(obj, lm, lc, lp):
def minMeshObject(obj, sd, ad):
    import gmsh, math, MeshPart, tempfile

    # Create gmsh from shape or mesh
    # Clear any previous models
    # print('mesh Object - first Clear')
    print(f"minMeshObject sd {sd} ad {ad}")
    gmsh.clear()
    if hasattr(obj, "Shape"):
        print("minMesh Shape")
        tmpFile = tempfile.NamedTemporaryFile(suffix=".stl").name
        shape = obj.Shape.copy(False)
        #mesh = MeshPart.meshFromShape( Shape=shape, Fineness=2,
        #    SecondOrder=0, Optimize=1, AllowQuad=0,)
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=sd,
               AngularDeflection = math.radians(ad), Relative=False)
        mesh.write(tmpFile)
        #mesh.write("/tmp/meshFile.stl")
        gmsh.initialize()
        #gmsh.open(tmpFile)
        #setMinMeshParms(lm, lc, lp)
        #gmsh.model.mesh.importStl()
        gmsh.merge(tmpFile)
        gmsh.model.mesh.removeDuplicateNodes()  # optional
        gmsh.model.mesh.recombine()
        # gmsh.finalize()
        return True


def recombineMeshObject(fcMesh):
    import gmsh, tempfile

    # Create gmsh from shape or mesh
    # Clear any previous models
    # print('mesh Object - first Clear')
    print(f"Recombine Mesh Object")
    gmsh.clear()
    tmpFile = tempfile.NamedTemporaryFile(suffix=".stl").name
    fcMesh.write(tmpFile)
    #fcMesh.write("/tmp/Rmesh.stl")
    gmsh.initialize()
    #gmsh.open(tmpFile)
    #gmsh.model.mesh.importStl()
    gmsh.merge(tmpFile)
    gmsh.model.mesh.removeDuplicateNodes()  # optional
    gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)
    #gmsh.option.setNumber("Mesh.RecombineOptimizeTopology", 0)
    #gmsh.option.setNumber("Mesh.RecombineNodeRepositioning", 0)
    #gmsh.option.setNumber("Mesh.RecombineMinimumQuality", 1e-3)
    gmsh.model.mesh.recombine()
    # gmsh.finalize()
    return True


def meshObj(obj, dim, meshParms=False, tessObj=None):
    # Used by Tetrahedron - Retire
    # Create gmsh from shape or mesh
    # Clear any previous models
    gmsh.clear()
    setAltMeshParms(meshParms, obj, tessObj)
    if hasattr(obj, "Shape"):
        return meshObjShape(obj, dim)

    elif hasattr(obj, "Mesh"):
        return meshObjMesh(obj, dim)


def getVertex():
    # Attempt at bulk getting coordinate
    print("Gmsh - GetNodes")
    nodes, coordLst, pcords = gmsh.model.mesh.getNodes()
    # print('coords datatype : '+str(coordLst.dtype))
    # int does not work needs to be float at least
    # coordLst = coordLst.astype('int32')
    coords = [coordLst[x : x + 3] for x in range(0, len(coordLst), 3)]
    print("Number coords : " + str(len(coords)))
    vertex = []
    # print('Coords')
    for n in coords:
        # print(n)
        # print(n[0],n[1],n[2])
        vertex.append(FreeCAD.Vector(n[0], n[1], n[2]))
    return vertex


def getFacetsByType0(elementType):
    print(f"Get Facets By Type {elementType}")
    # Element type 0 point, 1 line, 2 triangle 3 quadrangle 4 tetrahedron
    # Face types 3 triangle 4 quadrangle
    # Get Triangle Facets
    # Get Elements
    # eTypes, tags, faceNodes = gmsh.model.mesh.getElements(-1,-1)
    # print(eTypes[0:3])
    tags, faceNodes = gmsh.model.mesh.getElementsByType(elementType)
    # print('faceNodes datatype : '+str(faceNodes.dtype))
    # nodes, coords are numpy arrays
    faceNodes = faceNodes.astype("int32")
    print(faceNodes)
    if len(faceNodes) > 1:
        maxIdx = np.amax(faceNodes)
        print("Max : " + str(np.amax(faceNodes)))
        minIdx = int(np.amin(faceNodes))
        print("Min : " + str(minIdx))
        print("faceNodes : " + str(len(faceNodes)))
        # gmsh index starts 1
        # fc index starts 0
        # if minIdx > 1 :
        #   facetList = np.subtract(faceNodes,minIdx-1)
        # else :
        #   facetList = faceNodes
        #
        facetList = np.subtract(faceNodes, minIdx)
        facePoints = elementType + 1

        facets = [
            facetList[x : x + facePoints]
            for x in range(0, len(facetList), facePoints)
        ]
        print("Number of facets : " + str(len(facets)))
        # print('Facets')
        # for f in facets :
        #   print(f)
        return facets

    else:
        return []


def getFacetsByType(elementType):
    print(f"Get Facets By Type {elementType}")
    # Element type 0 point, 1 line, 2 triangle 3 quadrangle 4 tetrahedron
    # Face types 3 triangle 4 quadrangle
    # Get Triangle Facets
    # Get Elements
    # eTypes, tags, faceNodes = gmsh.model.mesh.getElements(-1,-1)
    # print(eTypes[0:3])
    tags, faceNodes = gmsh.model.mesh.getElementsByType(elementType)
    # print('faceNodes datatype : '+str(faceNodes.dtype))
    # nodes, coords are numpy arrays
    faceNodes = faceNodes.astype("int32")
    #print(faceNodes)
    if len(faceNodes) > 1:
        maxIdx = np.amax(faceNodes)
        print("Max : " + str(np.amax(faceNodes)))
        minIdx = int(np.amin(faceNodes))
        print("Min : " + str(minIdx))
        print("faceNodes : " + str(len(faceNodes)))
        # gmsh index starts 1
        # fc index starts 0
        if minIdx > 0:
            facetList = np.subtract(faceNodes, 1)
        else:
            facetList = faceNodes

        # facetList = np.subtract(faceNodes, minIdx)
        facePoints = elementType + 1

        facets = [
            facetList[x : x + facePoints]
            for x in range(0, len(facetList), facePoints)
        ]
        print("Number of facets : " + str(len(facets)))
        # print('Facets')
        # for f in facets :
        #   print(f)
        return facets

    else:
        return []


def getFacets():
    fct2 = getFacetsByType(2)
    print(f"type 2 {type(fct2)} {len(fct2)}")
    fct3 = getFacetsByType(3)
    print(f"type 3 {type(fct3)} {len(fct3)}")
    return fct2 + fct3


def getTetrahedrons():
    print("Get Tetrahedrons")
    tags, nodesLst = gmsh.model.mesh.getElementsByType(4)
    nodes = np.subtract(nodesLst, 1)

    vertex = getVertex()
    if len(nodes) > 0:
        print("nodes : " + str(len(nodes)))
        FCnodes = []
        for n in nodes:
            # print('n : '+str(n))
            FCnodes.append(vertex[n])
        TetList = [FCnodes[x : x + 4] for x in range(0, len(FCnodes), 4)]
        return TetList
    else:
        FreeCAD.Console.PrintWarning(
            "Unable to create quad faces for this shape"
        )
        return None


def vertex2Vector(v):
    return FreeCAD.Vector(v.X, v.Y, v.Z)


def addFacet(msh, v0, v1, v2):
    # print('Add Facet')
    # msh.addFacet(v0[0],v0[1],v0[2],v1[0],v1[1],v1[2],v2[0],v2[1],v2[2])
    # print(v0)
    # print(v1)
    # print(v2)
    # msh.addFacet(FreeCAD.Vector(v0),FreeCAD.Vector(v1),FreeCAD.Vector(v2))
    msh.addFacet(vertex2Vector(v0), vertex2Vector(v1), vertex2Vector(v2))


def TessellatedShape2Mesh(obj):
    import Mesh

    msh = Mesh.Mesh()
    # v = obj.Shape.Vertexes
    # print(dir(obj.Shape.Faces))
    for f in obj.Shape.Faces:
        # print('Deal with Triangular Faces')
        # addFacet(msh,v[f.Vertexes[0]], v[f.Vertexes[1]],  v[f.Vertexes[2]])
        addFacet(msh, f.Vertexes[0], f.Vertexes[1], f.Vertexes[2])
        if len(f.Edges) == 4:
            # print('Deal with Quad Faces')
            # addFacet(msh,v[f.Vertexes[0]], v[f.vertexes[2]],  v[f.vertexes[3]])
            addFacet(msh, f.Vertexes[0], f.vertexes[2], f.vertexes[3])
    return msh


def Tessellated2Mesh(obj):
    # Should now be redundant as replaced by TessellatedShape2Mesh
    import Mesh

    print("Tessellated 2 Mesh : " + obj.Label)
    if hasattr(obj.Proxy, "Facets"):
        print("Has proxy - Create Mesh")
        msh = Mesh.Mesh()
        v = obj.Proxy.Vertex
        # print(v)
        for f in obj.Proxy.Facets:
            # print(f)
            # print(type(v[0]))
            addFacet(msh, v[f[0]], v[f[1]], v[f[2]])
            if len(f) == 4:
                addFacet(msh, v[f[0]], v[f[2]], v[f[3]])
        return msh
    else:
        print(dir(obj))


def Tetrahedron2Mesh(obj):
    import Mesh

    print("Tetrahedron 2 Mesh")
    #print(dir(obj.Proxy))
    print(obj.Proxy.Tetra[:10])
    tetList = obj.Proxy.Tetra
    # print('Len tetra : '+str(len(tetList)))
    # print(tetList[:8])
    # print('Create Mesh')
    msh = Mesh.Mesh()
    for tet in tetList:
        # print('tet')
        # print(tet)
        addFacet(msh, tet[0], tet[1], tet[2])
        if len(tet) == 4:
            addFacet(msh, tet[0], tet[2], tet[3])
    return msh


def printMyInfo():
    # Element type 0 point, 1 line, 2 triangle 3 quadrangle 4 tetrahedron
    # 5 pyramid, 6 hexahedron
    # Face types 3 triangle 4 quadrangle
    faces = gmsh.model.mesh.getElementFaceNodes(2, 3)
    print("Face Nodes")
    print(len(faces))
    nodes, coords, parm = gmsh.model.mesh.getNodes(-1, 2)
    print("Nodes with tag = 2")
    print(len(nodes))
    enodes, coords, parms = gmsh.model.mesh.getNodesByElementType(2)
    print("Nodes of type 2")
    print(len(enodes))
    # print(enodes)
    faceNodes = gmsh.model.mesh.getElementFaceNodes(0, 3)
    print("Face Node")
    print(len(faceNodes))
    nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes(2)
    print("Get Nodes 2")
    print(len(nodeTags))
    # print(nodeTags)
    # print('Get Elements')
    elem, tags = gmsh.model.mesh.getElementsByType(2)
    # print(len(elem))
    # print(elem)
    # print(len(tags))
    # print(tags)


def printMeshInfo():
    entities = gmsh.model.getEntities()
    for e in entities:
        print(
            "Entity " + str(e) + " of type " + gmsh.model.getType(e[0], e[1])
        )
        # get the mesh nodes for each elementary entity
        nodeTags, nodeCoords, nodeParams = gmsh.model.mesh.getNodes(e[0], e[1])
        # get the mesh elements for each elementary entity
        elemTypes, elemTags, elemNodeTags = gmsh.model.mesh.getElements(
            e[0], e[1]
        )
        # count number of elements
        numElem = sum(len(i) for i in elemTags)
        print(
            " - mesh has "
            + str(len(nodeTags))
            + " nodes and "
            + str(numElem)
            + " elements"
        )
        boundary = gmsh.model.getBoundary([e])
        print(" - boundary entities " + str(boundary))
        partitions = gmsh.model.getPartitions(e[0], e[1])
        if len(partitions):
            print(
                " - Partition tag(s): "
                + str(partitions)
                + " - parent entity "
                + str(self.Gmsh.model.getParent(e[0], e[1]))
            )
        for t in elemTypes:
            (
                name,
                dim,
                order,
                numv,
                parv,
                _,
            ) = gmsh.model.mesh.getElementProperties(t)
            print(
                " - Element type: "
                + name
                + ", order "
                + str(order)
                + " ("
                + str(numv)
                + " nodes in param coord: "
                + str(parv)
                + ")"
            )

    # all mesh node coordinates
    nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes()
    x = dict(zip(nodeTags, nodeCoords[0::3]))
    y = dict(zip(nodeTags, nodeCoords[1::3]))
    z = dict(zip(nodeTags, nodeCoords[2::3]))
    # print(x)
    # print(y)
    # print(z)
