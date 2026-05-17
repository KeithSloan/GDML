#
# First select the World volume and then execute this macro
#

import sys
import random
import time
import math
import FreeCADGui
import FreeCAD

from PySide import QtWidgets, QtGui

import FreeCAD as App
from FreeCAD import Vector, Rotation
import Part
from FreeCAD import Matrix
import MeshPart

from dataclasses import dataclass

@dataclass
class Moments:
    Volume: float
    cm: Vector  # center of mass location
    M: Matrix   # Inertia about the center of mass

    def inertiaAboutOrigin(self) -> Matrix:
        v = self.cm
        Ixx = self.M.A11 + self.Volume*(v.z * v.z + v.y * v.y)
        Ixy = self.M.A12 - self.Volume*v.x * v.y
        Ixz = self.M.A13 - self.Volume*v.x * v.z
        Iyy = self.M.A22 + self.Volume*(v.x * v.x + v.z * v.z)
        Iyz = self.M.A23 - self.Volume*v.y * v.z
        Izz = self.M.A33 + self.Volume*(v.x * v.x + v.y * v.y)

        mat: Matrix = Matrix(Ixx, Ixy, Ixz, 0,
                             Ixy, Iyy, Iyz, 0,
                             Ixz, Iyz, Izz, 0, 0, 0, 0, 1)

        return mat

    def inertiaRotated(self, rot: Rotation) -> Matrix:
        rinv = rot.inverted()
        return rot*self.M*rinv


def buildDocTree():

    global childObjects


    # TypeIds that should not go in to the tree
    skippedTypes = ["App::Origin", "Sketcher::SketchObject", "Part::Compound"]

    def addDaughters(item: QtWidgets.QTreeWidgetItem):
        objectLabel = item.text(0)
        object = App.ActiveDocument.getObjectsByLabel(objectLabel)[0]
        if object not in childObjects:
            childObjects[object] = []
        for i in range(item.childCount()):
            childItem = item.child(i)
            treeLabel = childItem.text(0)
            try:
                childObject = App.ActiveDocument.getObjectsByLabel(treeLabel)[0]
                objType = childObject.TypeId
                if objType not in skippedTypes:
                    childObjects[object].append(childObject)
                    # print(f"added {treeLabel}")
                    addDaughters(childItem)
            except Exception as e:
                print(e)
        return

    # Get world volume from document tree widget
    worldObj = FreeCADGui.Selection.getSelection()[0]
    tree = FreeCADGui.getMainWindow().findChildren(QtGui.QTreeWidget)[0]
    it = QtGui.QTreeWidgetItemIterator(tree)
    doc = FreeCAD.ActiveDocument
    found = False

    for nextObject in it:
        item = nextObject.value()
        treeLabel = item.text(0)
        if not found:
            # print(f"treeLabel {treeLabel} odcLabel {doc.Label}")
            if treeLabel != doc.Label:
                continue

        found = True
        try:
            objs = doc.getObjectsByLabel(treeLabel)
            if len(objs) == 0:
                continue

            obj = objs[0]
            if obj == worldObj:
                # we presume first app part is world volume
                addDaughters(item)
                break
        except Exception as e:
            print(e)
            FreeCADobject = None


def MonteCarloMoments(shape, nsim: int) -> Moments:
    moments = Moments(0, Vector(0, 0, 0), Matrix())
    b = shape.BoundBox
    print(f"xmin={b.XMin} xmax={b.XMax}")
    pmin = Vector(b.XMin, b.YMin, b.ZMin)
    pmax = Vector(b.XMax, b.YMax, b.ZMax)

    cm = Vector(0, 0, 0)
    Ixx = 0.
    Ixy = 0.
    Ixz = 0.
    Iyy = 0.
    Iyz = 0.
    Izz = 0.

    numIn: int = 0

    start = time.perf_counter()
    for i in range(nsim):
        x = pmin.x + random.random() * (pmax.x - pmin.x)
        y = pmin.y + random.random() * (pmax.y - pmin.y)
        z = pmin.z + random.random() * (pmax.z - pmin.z)
        r = Vector(x, y, z)
        if shape.isInside(r, 0.1, True):
            numIn += 1
            cm += r

            Ixx += z * z + y * y
            Ixy += -x * y
            Ixz += -x * z
            Iyy += x * x + z * z
            Iyz += -y * z
            Izz += x * x + y * y
    end = time.perf_counter()
    print(f" Monte Carlo time = {end-start} seconds")

    # calculate moments about center of mass, using parallel axis theorem.
    cm /= numIn
    Ixx -= numIn * (cm.y * cm.y + cm.z * cm.z)
    Iyy -= numIn * (cm.x * cm.x + cm.z * cm.z)
    Izz -= numIn * (cm.x * cm.x + cm.y * cm.y)
    Ixy += numIn * cm.x * cm.y
    Ixz += numIn * cm.x * cm.z
    Iyz += numIn * cm.y * cm.z

    moments.cm = cm
    moments.M = Matrix(Ixx, Ixy, Ixz, 0,
                       Ixy, Iyy, Iyz, 0,
                       Ixz, Iyz, Izz, 0,
                       0, 0, 0, 1)

    A = moments.M.A
    B = (A[i] / numIn for i in range(len(A)))
    moments.M = Matrix(*B)

    MCVolume = b.XLength * b.YLength * b.ZLength
    print(f"numIn= {numIn} nsim={nsim}")
    MCVolume *= float(numIn) / nsim
    moments.Volume = MCVolume

    return moments


def topObjects(part) -> list:
    ''' return a list containing the top shapes contained in part
    a top shape may contain other shapes, but cannot be contained in
    other shapes within Part
    '''
    if part in childObjects:
        return childObjects[part]
    else:
        return []


def partCM(part) -> tuple:
    '''
    Note, what we are calling the total moment of inertia is NOT the total moment
    of inertia at all!
    So as not to over-emphasize large bodies compared to small ones in the "total",
    we actually calculate the moment of inertia PER UNIT VOLUME for each object
    The sum of the moments of inertia per unit volume is a useful tool to see
    if the setup in geant matches the setup in FreeCAD, but IT IS NOT a moment of
    inertia, not even, per unit volume. The latter would be sum( volume_i * inertia_density_i)/total volume
    '''
    outerObjects = topObjects(part)
    cm: Vector = Vector(0, 0, 0)
    totVol: float = 0
    II: Matrix = Matrix(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    for obj in outerObjects:
        if hasattr(obj, 'Shape'):
            vol = obj.Shape.Volume
            shape = obj.Shape
            cm0 = obj.Shape.CenterOfGravity
            if hasattr(shape, 'MatrixOfInertia'):
                II0 = obj.Shape.MatrixOfInertia
            else:
                # print(f"{obj.Label} has no MatrixOfInertia. Calculate using MonteCarlo")
                # moments: Moments = MonteCarloMoments(shape, 50000)
                # print(f"{obj.Label} has no MatrixOfInertia. Calculate using MonteCarlo")
                mesh = MeshPart.meshFromShape(Shape=obj.Shape, LinearDeflection=0.5, AngularDeflection=0.524,
                                              Relative=False)
                shape = Part.Shape()
                shape.makeShapeFromMesh(mesh.Topology, 0.5)
                solid = Part.makeSolid(shape)
                II0 = solid.MatrixOfInertia

            globalPlacement = obj.getGlobalPlacement()
            rotglob = globalPlacement.Rotation

            # Note: There are three placements that have to be taken into account
            # When calculating the moments of inertial relative to the world origin
            # Take an object in the FreeCAD Tree:
            # App::Part
            #   Solid_with_Shape
            # placement0 = App::Part.placement
            # placement1 = solid_with_Shape.placement
            # placement2 = solid_with_Shape.CenterOfGravity
            #
            # Assume we have a solid that is not symmetric about the origin, say a half sphere, with
            # center at the origin and the hemisphere completely in the x>0 quadrants
            # Assume the sphere is placed with its center at the origin, i.e, placement1 = (0, 0, 0)
            # then placement2 = (xcg, 0, 0)
            # If placement1 != (0,0,0), say placement1 = (x1, y1, z1)
            # Then placement2, as reported by the Shape.CenterOfGravity will include placement1:
            # placement2 = (x1+xcg, y1, z1)
            # The global placement includes placement0 + placement1, BUT NOT the unshifted center of mass (xcg, 0, 0)
            # That is globalPlacement = placement1 + placement2
            # Therefore, the global location of the center of mass is
            # globalPlacement.Base + CenterOfGravity - placement1,Base
            rotobj = obj.Placement.Rotation
            cmglob = globalPlacement.Base + rotglob*rotobj.inverted()*(cm0 - obj.Placement.Base)

            mom0: Moments = Moments(vol, cmglob, II0)
            # Note MatrixOfInertial already includes the rotation obj.Placement.Rotation
            # but the global rotation already includes the object's Placement.Rotation
            # So we have to take that rotation out before we apply the global rotation
            mom0.M = mom0.inertiaRotated(rotobj.inverted())
            # do the global rotation
            mom0.M = mom0.inertiaRotated(rotglob)

            IIorigin: Matrix = mom0.inertiaAboutOrigin()
            II += IIorigin
            cm += vol * cmglob
            totVol += vol

            # prettyPrint(obj.Label, vol, cmglob, IIorigin)

        elif obj.TypeId == "Mesh::Feature":
            mesh = obj.Mesh
            shape = Part.Shape()
            shape.makeShapeFromMesh(mesh.Topology, 0.5)
            solid = Part.makeSolid(shape)
            II0 = solid.MatrixOfInertia
            globalPlacement = obj.getGlobalPlacement()
            rotglob = globalPlacement.Rotation
            rotobj = obj.Placement.Rotation
            cm0 = shape.CenterOfGravity
            vol = shape.Volume
            cmglob = globalPlacement.Base + rotglob*rotobj.inverted()*(cm0 - obj.Placement.Base)
            mom0: Moments = Moments(vol, cmglob, II0)
            mom0.M = mom0.inertiaRotated(rotobj.inverted())
            mom0.M = mom0.inertiaRotated(rotglob)
            IIorigin: Matrix = mom0.inertiaAboutOrigin()
            II += IIorigin
            cm += vol * cmglob
            totVol += vol

        elif obj.TypeId == 'App::Part':
            partVol, cm0, II0 = partCM(obj)
            cm += partVol * cm0
            totVol += partVol
            II += II0
            prettyPrint(obj.Label, partVol, cm0, II0)

    cm /= totVol

    return (totVol, cm, II)


def prettyPrint(name, vol, cm0, II0, outfile):
    volunit = "mm^3"
    if vol > 1e9:
        vol /= 1e9
        volunit = " m^3"
    elif vol > 1000:
        vol /= 1000
        volunit = "cm^3"

    cmunit = "mm"
    cm = cm0
    if cm0.Length >= 1000.0:
        cm /= 1000
        cmunit = " m"
    elif cm0.Length >= 100.0:
        cm /= 10
        cmunit = "cm"

    # inertia unit: either powers of cm^5, or powers of mm^5
    # If maxInertia > 0.1 cm^5, unit is cm^5
    # otherwise unit is mm^5
    # 0.1 cm^5 = 0.1*(10^5 mm^5) = 10^4 mm^5
    maxInertia = max(II0.A)  # this is in base unit of freecad = mm^5
    if math.log10(maxInertia) >= 4:
        inertiaUnit = "cm^5"
        maxInertia /= 1e5
    else:
        inertiaUnit = "mm^5"

    k = 0
    while maxInertia > 10:
        k += 1
        maxInertia /= 10

    if inertiaUnit == "mm^5":
        power = k
    else:
        power = 5 + k

    if k > 0:
        inertiaUnit = f"x10^{k} {inertiaUnit}"

    B = (II0.A[i] / 10 ** power for i in range(len(II0.A)))
    II0 = Matrix(*B)

    s = f'{name:20s} Volume: {vol:8.2f} {volunit}'
    s += f' --> center of "mass": ({cm.x:7.2f},{cm.y:7.2f},{cm.z:7.2f}) {cmunit}, '
    s += f'moments of inetria: ({II0.A11:#6.4g}, {II0.A22:#6.4g}, {II0.A33:#6.4g})'
    s += f' {inertiaUnit}'

    print(s, file=outfile)
    if outfile != sys.stdout:
        print(s)


def calcCenterOfMass(outfile=sys.stdout):
    global childObjects

    if outfile != sys.stdout:
        outfile = open(outfile, 'w')

    wv = App.Gui.Selection.getSelection()[0]
    cm = Vector(0, 0, 0)
    totVol = 0
    II: Matrix = Matrix(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    childObjects = {}
    buildDocTree()

    # for debugging doc tree
    for obj in childObjects:
        s = ""
        for child in childObjects[obj]:
            s += child.Label + ", "
        print(f"{obj.Label} [{s}]")

    for part in childObjects[wv]:
        if part.TypeId == 'App::Part':
            vol, cm0, II0 = partCM(part)
            prettyPrint(part.Label, vol, cm0, II0, outfile)

            cm += vol * cm0
            totVol += vol
            II += II0

    cm = cm / totVol

    print(file=outfile)
    prettyPrint("Total ", totVol, cm, II, outfile)

if __name__ == '__main__':
    calcCenterOfMass()


