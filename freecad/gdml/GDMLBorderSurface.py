def printVertexes(i, v1, v2, tol):
    #print(f'{i} v1 {v1.X} {v1.Y} {v1.Z} v2 {v2.X} {v2.Y} {v2.Z} {v1.Point.isEqual(v2.Point, tol)}')
    if v1.Point.isEqual(v2.Point, tol):
       print(f'{i} v1 {v1.X} {v1.Y} {v1.Z} v2 {v2.X} {v2.Y} {v2.Z} {v1.Point.isEqual(v2.Point, tol)}')

def compareVertex(i, v1, v2, tol = 1e-7):
    printVertexes(i, v1, v2, tol)
    return v1.Point.isEqual(v2.Point, tol)

def checkFaces(i, face1, face2):
#    Does not work vertexes not necessary in same order
#    for v1 in face1.Vertexes:
#        for v2 in face2.Vertexes:
#            if compareVertex(i, v1, v2) == False:
#               return False
#        return True
    v1 = [v.Point for v in face1.Vertexes]
    v2 = [v.Point for v in face2.Vertexes]
    vcommon1 = [v for v in v1 if any([w.isEqual(v, 1e-7) for w in v2])]
    if len(vcommon1) == len(face1.Vertexes):
       print (vcommon1)
       return (i, vcommon1)
    else:
       return None

def commonFace4(shape1, shape2, tol = 1e-7):
    print('CommonFace 4')
    for i, face1 in enumerate(shape1.Faces):
        for face2 in shape2.Faces:
            retFace = checkFaces(i, face1, face2)
            if retFace is not None:
               print(retFace)
               print(type(retFace))
               print(len(retFace))
               if len(retFace) == 2:
                  createBorderSurfaceObj(retFace[0], retFace[1])

def createBorderSurfaceObj(i, faces):
    doc = FreeCAD.ActiveDocument
    print(f'Create Border Surface {i}')
    print(f'Faces {faces}')
    bsObj = doc.addObject("Part::FeaturePython","BorderSurface")


def adjustShape(part):
    print("Adjust Shape")
    print(part.Name)
    print(part.Label)
    print(part.OutList)
    print(f'Before Placement Base {part.Placement.Base}')
    beforeBase = part.Placement.Base
    if hasattr(part,'LinkedObject'):
       print(f'Linked Object {part.LinkedObject}')
       part = part.getLinkedObject()
       print(part.Name)
       print(part.Label)
       print(part.OutList)
    obj = getGDMLObject(part.OutList)
    obj.recompute()
    # Shape is immutable so have to copy
    shape = getShape(obj)
    print(f'Shape Valid {shape.isValid()}')
    print(dir(shape))
    #return shape
    print(f'After Placement Base {part.Placement.Base}')
    #return translate(part, part.Placement.Base)


def getGDMLObject(list):
    print('getGDMLObject')
    print(list[0].TypeId)
    if list[0].TypeId == "App::Origin":
       print(f'Vertex {list[1].Shape.Vertexes}')
       return list[1]
    else:
       print(f'Vertex {list[0].Shape.Vertexes}')
       return list[0]

def getShape(obj):
    print(obj.TypeId)
    print(obj.Name)
    if hasattr(obj,'Shape'):
       return obj.Shape.copy()
    print(dir(obj))
    return obj

def createBorderSurfObject(part0, part1, property):
    print('createBorderSurfObject')
    print(part0.TypeId)
    print(part0.Name)
    print(dir(part0))
    print(part0.Placement)
    print(part1.Name)
    print(part1.Placement)
    print(dir(part1))
    #print(property)
    #adjustShape(part0)
    #adjustShape(part1)
    commonFace4(adjustShape(part0), adjustShape(part1))
    #print(commonFaces2(adjustShape(part0), adjustShape(part1)))
