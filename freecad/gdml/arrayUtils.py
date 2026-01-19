import FreeCAD
from FreeCAD import Vector


def typeOfArray(obj):
    obj1 = obj
    if obj.TypeId == "App::Link":
        obj1 = obj.LinkedObject
    if obj1.TypeId == "Part::FeaturePython":
        typeId = obj1.Proxy.Type
        if typeId == "Array":
            return obj1.ArrayType
        elif typeId == "PathArray":
            return "PathArray"
        elif typeId == "PointArray":
            return "PointArray"
        elif typeId == "Clone":
            clonedObj = obj1.Objects[0]
            return typeOfArray(clonedObj)

        else:
            return None
    else:
        return None


def orthoIndexes(i, array):
    ''' Return a triplet ix, iy, iz of the ith element on an nx x ny x nz grid '''
    nx = array.NumberX
    ny = array.NumberY
    # nz = array.IntervalZ not needed
    # The forward mapping of ix, iy, iz -> i:
    # i = ix + iy * nx + iz * nx * ny
    # The inverse is:
    iz = int(i/(nx*ny))
    i1 = i % (nx * ny)
    iy = int(i1/nx)
    ix = i1 % nx
    return ix, iy, iz


def placementList(array, offsetVector=Vector(0, 0, 0), rot=FreeCAD.Rotation()):
    ''' return list of placements for an array '''
    arrayType = typeOfArray(array)
    if arrayType == "ortho":
        return [FreeCAD.Placement(offsetVector +
                                  ix * array.IntervalX
                                  + iy * array.IntervalY
                                  + iz * array.IntervalZ, rot)
                for iz in range(array.NumberZ)
                for iy in range(array.NumberY)
                for ix in range(array.NumberX)]

    elif arrayType == "polar":
        placementList = []
        if array.Angle == 360:
            dthet = 360 / array.NumberPolar
        else:
            dthet = array.Angle / (array.NumberPolar - 1)
        axis = array.Axis
        for i in range(array.NumberPolar):
            roti = FreeCAD.Rotation(axis, i * dthet)
            pos1 = rot * offsetVector
            pos2 = array.Center + roti * (pos1 - array.Center)
            placementList.append(FreeCAD.Placement(pos2, rot*roti))
        return placementList

    elif arrayType == "PathArray":
        placementList = []
        pathObj = array.PathObject
        path = pathObj.Shape.Edges[0]
        # TODO take start offset and offset into account
        # TODO, take VerticalVector into account
        points = path.discretize(Number=array.Count)
        extraTranslation = array.ExtraTranslation
        for i, point in enumerate(points):
            pos = point + offsetVector + extraTranslation
            placementList.append(FreeCAD.Placement(pos, rot))
        return placementList

    elif arrayType == "PointArray":
        placementList = []
        pointObj = array.PointObject
        points = pointObj.Points.Points
        extraTranslation = array.ExtraPlacement.Base
        for i, point in enumerate(points):
            pos = point + offsetVector + extraTranslation
            placementList.append(FreeCAD.Placement(pos, rot))
        return placementList

