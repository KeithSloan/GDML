import FreeCAD
from FreeCAD import Vector


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
    if array.ArrayType == "ortho":
        return [FreeCAD.Placement(offsetVector +
                                  ix * array.IntervalX
                                  + iy * array.IntervalY
                                  + iz * array.IntervalZ, rot)
                for iz in range(array.NumberZ)
                for iy in range(array.NumberY)
                for ix in range(array.NumberX)]

    elif array.ArrayType == "polar":
        placementList = []
        if array.Angle == 360:
            dthet = 360 / array.NumberPolar
        else:
            dthet = array.Angle / (array.NumberPolar - 1)
        axis = array.Axis
        for i in range(array.NumberPolar):
            rot = FreeCAD.Rotation(axis, i * dthet)
            pos = array.Center + rot * (offsetVector - array.Center)
            placementList.append(FreeCAD.Placement(pos, rot))
        return placementList


