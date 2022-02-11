# -*- mode: Python; python-indent-offset: 4; python-guess-indent: nil -*-
# Mon Dec  6 08:49:56 AM PST 2021
# **************************************************************************pp
# *                                                                        *
# *   Copyright (c) 2019 Keith Sloan <keith@sloan-home.co.uk>              *
# *             (c) 2020 Dam Lambert                                       *
# *             (c) 2021 Munther Hindi
# *
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
__title__ = "FreeCAD - GDML Extrude exporter Version"
__author__ = "Keith Sloan <keith@sloan-home.co.uk>"
__url__ = ["https://github.com/KeithSloan/FreeCAD_Geant4"]

import FreeCAD, Part, math
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

#############################################
# Helper functions for extrude construction

# One of the closed curves (list of edges) representing a part
# of the sketch


class ClosedCurve:
    def __init__(self, name, edgeList):
        self.name = name
        self.face = Part.Face(Part.Wire(edgeList))
        self.edgeList = edgeList

    def isInside(self, otherCurve):
        # ClosedCurves are closed: so if ANY vertex of the otherCurve
        # is inside, then the whole curve is inside
        return self.face.isInside(otherCurve.edgeList[0].Vertexes[0].Point, 0.001, True)


class ExtrudedClosedCurve(ClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist)
        self.height = height
        self.position = Vector(0, 0, 0)
        self.rotation = [0, 0, 0]  # TBD

    def export(self):
        print('export not implemented')


class ExtrudedCircle(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)
        self.position = edgelist[0].Curve.Center + Vector(0, 0, height/2)

    def export(self):
        edge = self.edgeList[0]
        exportTube(self.name, edge.Curve.Radius, self.height)


class ExtrudedArcSection(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)
        # Note extrusion polyogn will be in absolute coordinates
        # since arc section is relative to that, position is actually (0,0,0)
        # same goes for rotation

    # return midpoint of arc, relative to center
    def midPoint(self):
        edge = self.edgeList[0]
        radius = edge.Curve.Radius
        thetmid = (edge.FirstParameter+edge.LastParameter)/2
        arcAngle = edge.LastParameter - edge.FirstParameter
        v0 = edge.Vertexes[0].Point
        v1 = edge.Vertexes[1].Point
        vc = (v0+v1)/2  # chord center
        vc_vcenter = vc - edge.Curve.Center
        if vc_vcenter.Length < 0.001:  # arc chord = diameter
            # Although it seems that this should always work, I've seen cases in which
            # each of the first, last parameters were shifter by pi and thetmid
            # was off by pi
            vmid = edge.Curve.Center + radius*Vector(math.cos(thetmid), math.sin(thetmid), 0)
        else:
            u_vc_vcenter = vc_vcenter.normalize()  # unit vector fom center of circle to center of chord
            if arcAngle < math.pi:  # shorter of two arc segments, mid point and center are on opposite side
                vmid = edge.Curve.Center + edge.Curve.Radius*u_vc_vcenter
            else:  #longer of two arc segments: midpoint is on opposite side of chord
                vmid = edge.Curve.Center - edge.Curve.Radius*u_vc_vcenter

        return vmid

    def export(self):
        global solids
        from .exportGDML import exportPosition

        edge = self.edgeList[0]
        radius = edge.Curve.Radius
        # First form a bounding rectangle (polygon) for the arc.
        # Arc edges
        v1 = edge.Vertexes[0].Point
        v2 = edge.Vertexes[1].Point
        vmid = self.midPoint()

        # midpoint of chord
        vc = (v1+v2)/2
        v = v2-v1
        u = v.normalize()
        # extend the ends of the chord so extrusion can cut all of circle, if needed
        v1 = vc + radius*u
        v2 = vc - radius*u
        # component of vmid perpendicular to u
        vc_vmid = vmid - vc
        n = vc_vmid - u.dot(vc_vmid)*u
        n.normalize()
        # complete edges of box paerpendicular to chord, toward mid arc point
        v3 = v2 + 2*radius*n
        v4 = v1 + 2*radius*n

        xtruName = self.name+'_xtru'
        exportXtru(xtruName, [v1, v2, v3, v4], self.height)

        # tube to be cut1
        tubeName = self.name+'_tube'
        exportTube(tubeName, edge.Curve.Radius, self.height)

        # note, it is mandatory that name be that of ClosedCurve
        intersect = ET.SubElement(solids, 'intersection', {'name': self.name})
        ET.SubElement(intersect, 'first', {'ref': xtruName})
        ET.SubElement(intersect, 'second', {'ref': tubeName})
        pos = edge.Curve.Center + Vector(0, 0, self.height/2)
        exportPosition(tubeName, intersect, pos)


class ExtrudedEllipse(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)
        curve = edgelist[0].Curve
        self.position = curve.Center + Vector(0, 0, height/2)
        angle = math.degrees(curve.AngleXU)
        self.rotation = [0, 0, angle]

    def export(self):
        edge = self.edgeList[0]
        exportEllipticalTube(self.name, edge.Curve.MajorRadius,
                             edge.Curve.MinorRadius,
                             self.height)


class ExtrudedEllipticalSection(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)
        # Note extrusion polyogn will be in absolute coordinates
        # since arc section is relative to that, position is actually (0,0,0)
        # same goes for rotation

    def midPoint(self):
        edge = self.edgeList[0]
        a = edge.Curve.MajorRadius
        b = edge.Curve.MinorRadius
        angleXU = edge.Curve.AngleXU
        thet1 = edge.FirstParameter  # in radians, in unorated ellipse
        thet2 = edge.LastParameter  # in radians, in onrated ellipse
        thetmid = (thet1+thet2)/2 + angleXU

        # Major axis angle seems to be off by pi for some ellipse. Restrict it to be
        # be between 0 an pi
        if angleXU < 0:
            angleXU += 180
        v0 = edge.Vertexes[0].Point
        v1 = edge.Vertexes[1].Point

        # TODO must deal with case where cutting chord is along major axis
        # u_vc_vcenter = vc_vcenter.normalize()  # unit vector fom center of circle to center of chord

        # vertexes of triangle formed by chord ends and ellise mid point
        # In polar coordinates equation of ellipse is r(thet) = a*(1-eps*eps)/(1+eps*cos(thet))
        # if the ellipse is rotatated by an angle AngleXU, then
        # x = r*cos(thet+angleXU), y = r*sin(thet+angleXU), for thet in frame of unrotated ellipse
        # now edge.FirstParameter is begining angle of unrotaeted ellipse

        def sqr(x):
            return x*x

        def r(thet):
            return math.sqrt(1.0/(sqr(math.cos(thet)/a) + sqr(math.sin(thet)/b)))

        rmid = r(thetmid)
        vmid = Vector(rmid*math.cos(thetmid), rmid*math.sin(thetmid), 0)

        vmid += edge.Curve.Center

        '''
        uxaxis = Vector(math.cos(angleXU), math.sin(angleXU), 0)
        costhet = uxaxis.dot(u_vc_vcenter)    # angle between major axis and center of chor
        sinthet = math.sqrt(1-costhet*costhet)
        # polar equation of ellipse, with r measured from FOCUS. Focus at a*eps
        # r = lambda thet: a*(1-eps*eps)/(1+eps*math.cos(thet))
        # polar equation of ellipse, with r measured from center a*eps
        sqr = lambda x: x*x
        rmid = math.sqrt(1.0/(sqr(costhet/a) + sqr(sinthet/b)))        
        if arcAngle < math.pi:  # shorter of two arc segments, mid point and center are on opposite side
            vmid = edge.Curve.Center + rmid*u_vc_vcenter
        else:  #longer of two arc segments: midpoint is on opposite side of chord
            vmid = edge.Curve.Center - rmid*u_vc_vcenter
        '''

        return vmid

    def export(self):
        global solids
        from .exportGDML import exportPosition

        edge = self.edgeList[0]
        a = dx = edge.Curve.MajorRadius
        b = dy = edge.Curve.MinorRadius

        # vertexes of triangle formed by chord ends and ellise mid point
        # In polar coordinates equation of ellipse is r(thet) = a*(1-eps*eps)/(1+eps*cos(thet))
        # if the ellipse is rotatated by an angle AngleXU, then
        # x = r*cos(thet+angleXU), y = r*sin(thet+angleXU), for thet in frame of unrotated ellipse
        # now edge.FirstParameter is begining angle of unrotaeted ellipse
        # polar equation of ellipse, with r measured from FOCUS. Focus at a*eps
        # r = lambda thet: a*(1-eps*eps)/(1+eps*math.cos(thet))
        # polar equation of ellipse, with r measured from center a*eps

        def sqr(x):
            return x*x

        def r(thet):
            return math.sqrt(1.0/(sqr(math.cos(thet)/a) + sqr(math.sin(thet)/b)))

        v1 = edge.Vertexes[0].Point
        v2 = edge.Vertexes[1].Point
        vmid = self.midPoint()

        # midpoint of chord
        vc = (v1+v2)/2
        v = v2-v1
        u = v.normalize()  # unit vector from v1 to v2
        # extend the ends of the chord so extrusion can cut all of ellipse, if needed
        v1 = vc + 2*a*u
        v2 = vc - 2*a*u

        # component of vmid perpendicular to u
        vc_vmid = vmid - vc
        n = vc_vmid - u.dot(vc_vmid)*u
        n.normalize()
        v3 = v2 + 2*a*n
        v4 = v1 + 2*a*n

        xtruName = self.name+'_xtru'
        exportXtru(xtruName, [v1, v2, v3, v4], self.height)

        # tube to be cut1
        tubeName = self.name+'_tube'
        exportEllipticalTube(tubeName, dx, dy, self.height)

        # note, it is mandatory that name be that of ClosedCurve
        intersect = ET.SubElement(solids, 'intersection', {'name': self.name})
        ET.SubElement(intersect, 'first', {'ref': xtruName})
        ET.SubElement(intersect, 'second', {'ref': tubeName})
        pos = edge.Curve.Center + Vector(0, 0, self.height/2)
        exportPosition(tubeName, intersect, pos)
        rotName = tubeName+'_rot'
        # zAngle = math.degrees(edge.Curve.AngleXU)
        # Focus1 is on the positive x side, Focus2 on the negative side
        dy = edge.Curve.Focus1[1] - edge.Curve.Focus2[1]
        dx = edge.Curve.Focus1[0] - edge.Curve.Focus2[0]
        zAngle = math.degrees(math.atan2(dy, dx))
        print(f'{self.name} zAngle = {zAngle}')
        # if zAngle < 0:
        #    zAngle += 180
        ET.SubElement(define, 'rotation', {'name': rotName, 'unit': 'deg',
                                           'x': '0', 'y': '0', 'z': str(zAngle)})

        ET.SubElement(intersect, 'rotationref', {'ref': rotName})


class Extruded2Edges(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)

    def export(self):
        global solids

        # form normals to the edges. For case of two edges, sidedness is irrelevant
        v0 = self.edgeList[0].Vertexes[0].Point
        v1 = self.edgeList[0].Vertexes[1].Point
        e = v1 - v0
        if e.x == 0:
            ny = 0
            nx = 1
        elif e.y == 0:
            nx = 0
            ny = 1
        else:
            nx = 1
            ny = -e.x/e.y
        normal = Vector(nx, ny, 0).normalize()

        edgeCurves = []  # list of ExtrudedClosedCurve's

        for i, e in enumerate(self.edgeList):  # just TWO edges
            while switch(e.Curve.TypeId):
                if case('Part::GeomLineSegment'):
                    break

                if case('Part::GeomLine'):
                    break

                if case('Part::GeomCircle'):
                    print('Arc of Circle')
                    arcXtruName = self.name + '_c'+str(i)
                    arcSection = ExtrudedArcSection(arcXtruName, [e], self.height)
                    arcSection.export()

                    midpnt = arcSection.midPoint()
                    inside = pointInsideEdge(midpnt, v0, normal)
                    edgeCurves.append([arcXtruName, inside])
                    break

                if case('Part::GeomEllipse'):
                    print('Arc of Ellipse')
                    arcXtruName = self.name+'_e'+str(i)
                    arcSection = ExtrudedEllipticalSection(arcXtruName, [e], self.height)
                    arcSection.export()
                    midpnt = arcSection.midPoint()
                    inside = pointInsideEdge(midpnt, v0, normal)
                    edgeCurves.append([arcXtruName, inside])
                    break

                if case('Part::GeomBSplineCurve'):
                    print('BSpline not implemented yet')
                    break

        if len(edgeCurves) == 1:
            # change our name to be that of the constructed curve
            # not a violation of the contract of a unique name, since the curve name is based on ours
            self.position = arcSection.position
            self.rotation = arcSection.rotation
            self.name = edgeCurves[0][0]

        else:
            inside0 = edgeCurves[0][1]
            inside1 = edgeCurves[1][1]
            sameSide = (inside0 == inside1)
            if sameSide is False:
                booleanSolid = ET.SubElement(solids, 'union', {'name': self.name})
            else:
                booleanSolid = ET.SubElement(solids, 'subtraction', {'name': self.name})

            area0 = edgelistBBoxArea([self.edgeList[0]])
            area1 = edgelistBBoxArea([self.edgeList[1]])
            if area0 > area1:
                firstSolid = edgeCurves[0][0]
                secondSolid = edgeCurves[1][0]
            else:
                firstSolid = edgeCurves[1][0]
                secondSolid = edgeCurves[0][0]

            ET.SubElement(booleanSolid, 'first', {'ref': firstSolid})
            ET.SubElement(booleanSolid, 'second', {'ref': secondSolid})


class ExtrudedNEdges(ExtrudedClosedCurve):
    def __init__(self, name, edgelist, height):
        super().__init__(name, edgelist, height)

    def export(self):
        global solids
        from .exportGDML import exportPosition

        verts = []
        for e in self.edgeList:
            if len(e.Vertexes) > 1:
                verts.append(e.Vertexes[0].Point)
        verts.append(verts[0])

        face = Part.Face(Part.makePolygon(verts))

        edgeCurves = []  # list of ExtrudedClosedCurve's
        for i, e in enumerate(self.edgeList):

            while switch(e.Curve.TypeId):
                if case('Part::GeomLineSegment'):
                    break

                if case('Part::GeomLine'):
                    break

                if case('Part::GeomCircle'):
                    print('Arc of Circle')
                    arcXtruName = self.name + '_c'+str(i)
                    arcSection = ExtrudedArcSection(arcXtruName, [e], self.height)
                    midpnt = arcSection.midPoint()
                    inside = face.isInside(midpnt, 0.001, True)
                    if inside is True:
                        arcSection.height = 1.02*self.height  # for a cutting solid, increase its height 
                    arcSection.export()
                    # this is not general. Needs to be changed
                    # to a test against sidedness of edge of section
                    edgeCurves.append([arcXtruName, inside])
                    break

                if case('Part::GeomEllipse'):
                    print('Arc of Ellipse')
                    arcXtruName = self.name+'_e'+str(i)
                    arcSection = ExtrudedEllipticalSection(arcXtruName, [e], self.height)
                    midpnt = arcSection.midPoint()
                    inside = face.isInside(midpnt, 0.001, True)
                    if inside is True:
                        arcSection.height = 1.02*self.height  # for a cutting solid, increase its height 
                    arcSection.export()
                    edgeCurves.append([arcXtruName, inside])
                    break

                if case('Part::GeomBSplineCurve'):
                    print('BSpline not implemented yet')
                    break

        xtruName = self.name
        if len(edgeCurves) > 0:
            xtruName += '_xtru'
        exportXtru(xtruName, verts, self.height)

        currentSolid = xtruName
        if len(edgeCurves) > 0:
            for i, c in enumerate(edgeCurves):
                if i == len(edgeCurves) - 1:
                    name = self.name  # last boolean must have this classes name
                else:
                    name = 'bool' + c[0]
                if c[1] is False:
                    booleanSolid = ET.SubElement(solids, 'union', {'name': name})
                    ET.SubElement(booleanSolid, 'first', {'ref': currentSolid})
                    ET.SubElement(booleanSolid, 'second', {'ref': c[0]})
                else:
                    booleanSolid = ET.SubElement(solids, 'subtraction', {'name': name})
                    pos = Vector(0,0, -0.01*self.height)  # move subtracted solid down a bit 
                    ET.SubElement(booleanSolid, 'first', {'ref': currentSolid})
                    ET.SubElement(booleanSolid, 'second', {'ref': c[0]})
                    exportPosition(c[0], booleanSolid, pos)
                currentSolid = name

# Node of a tree that represents the topology of the sketch being exported
# a left_child is a ClosedCurve that is inside of its parent
# a right_sibling is a closedCurve that is outside of its parent


class Node:
    def __init__(self, closedCurve, parent, parity):
        # the nomenclature is redundant, but a reminder that left is a child and right
        # a sibling
        self.parent = parent
        if parent is None:
            self.parity = 0  # if parity is 0, print as union with current solid
            # if parity is 1, print as subtraction from other solid
        else:
            self.parity = parity

        self.left_child = None
        self.right_sibling = None
        self.closedCurve = closedCurve

    def insert(self, closedCurve):
        if self.closedCurve:  # not sure why this test is necessary
            if self.closedCurve.isInside(closedCurve):
                # given curve is inside this curve:
                # if this node does not have a child, insert it as the left_child
                # otherwise check if it is a child of the child
                if self.left_child is None:
                    self.left_child = Node(closedCurve, self, 1-self.parity)
                else:
                    self.left_child.insert(closedCurve)
            else:  # Since we have no intersecting curves (for well constructed sketch
                   # if the given curve is not inside this node, it must be outside
                if self.right_sibling is None:
                    self.right_sibling = Node(closedCurve, self, self.parity)
                else:
                    self.right_sibling.insert(closedCurve)
        else:
            self.closedCurve = closedCurve

    def preOrderTraversal(self, root):
        res = []
        if root:
            res.append([root, root.parity])
            res = res + self.preOrderTraversal(root.left_child)
            res = res + self.preOrderTraversal(root.right_sibling)

        return res

# arrange a list of edges in the x-y plane in Counter Clock Wise direction
# This can be easily generalized for points in ANY plane: if the normal
# defining the desired direction of the plane is given, then the z component
# below should be changed a dot prduct with the normal


def arrangeCCW(verts, normal=Vector(0, 0, 1)):
    reverse = False
    v0 = verts[0]
    rays = [(v - v0) for v in verts[1:]]
    area = 0
    for i, ray in enumerate(rays[:-1]):
        area += (rays[i].cross(rays[i+1])).dot(normal)
    if area < 0:
        verts.reverse()
        reverse = True

    return reverse

# Utility to determine if vector from point v0 to point v1 (v1-v0)
# is on sime side of normal or opposite. Return true if v ploints along normal


def pointInsideEdge(v0, v1, normal):
    v = v1 - v0
    if v.dot(normal) < 0:
        return False
    else:
        return True


def edgelistBB(edgelist):
    # get edge list bounding box
    bb = FreeCAD.BoundBox(0, 0, 0, 0, 0, 0)
    for e in edgelist:
        bb.add(e.BoundBox)
    return bb


def edgelistBBoxArea(edgelist):
    bb = edgelistBB(edgelist)
    return bb.XLength * bb.YLength


def sortEdgelistsByBoundingBoxArea(listoflists):
    listoflists.sort(reverse=True, key=edgelistBBoxArea)


def exportEllipticalTube(name, dx, dy, height):
    global solids

    ET.SubElement(solids, 'eltube', {'name': name,
                                     'dx': str(dx),
                                     'dy': str(dy),
                                     'dz': str(height/2),
                                     'lunit': 'mm'})


def exportTube(name, radius, height):
    global solids

    ET.SubElement(solids, 'tube', {'name': name,
                                   'rmax': str(radius),
                                   'z': str(height),
                                   'startphi': '0',
                                   'deltaphi': '360',
                                   'aunit': 'deg', 'lunit': 'mm'})


def exportXtru(name, vlist, height, zoffset=0):
    global solids

    xtru = ET.SubElement(solids, 'xtru', {'name': name, 'lunit': 'mm'})
    for v in vlist:
        ET.SubElement(xtru, 'twoDimVertex', {'x': str(v.x),
                                             'y': str(v.y)})
    ET.SubElement(xtru, 'section', {'zOrder': '0',
                                    'zPosition': str(zoffset),
                                    'xOffset': '0', 'yOffset': '0',
                                    'scalingFactor': '1'})
    ET.SubElement(xtru, 'section', {'zOrder': '1',
                                    'zPosition': str(height+zoffset),
                                    'xOffset': '0', 'yOffset': '0',
                                    'scalingFactor': '1'})


def getExtrudedCurve(name, edges, height):
    # Return an ExtrudedClosedCurve object of the list of edges

    if len(edges) == 1:  # single edge ==> a closed curve, or curve section
        e = edges[0]
        if len(e.Vertexes) == 1:  # a closed curve
            closed = True
        else:
            closed = False  # a section of a curve

        while switch(e.Curve.TypeId):
            if case('Part::GeomLineSegment'):
                print(' Sketch not closed')
                return ExtrudedClosedCurve(edges, name, height)

            if case('Part::GeomLine'):
                print(' Sketch not closed')
                return ExtrudedClosedCurve(name, edges, height)

            if case('Part::GeomCircle'):
                if closed is True:
                    print('Circle')
                    return ExtrudedCircle(name, edges, height)
                else:
                    print('Arc of Circle')
                    return ExtrudedArcSection(name, edges, height)

            if case('Part::GeomEllipse'):
                if closed is True:
                    print('Ellipse')
                    return ExtrudedEllipse(name, edges, height)
                else:
                    print('Arc of Ellipse')
                    return ExtrudedEllipticalSection(name, edges, height)

            if case('Part::GeomBSplineCurve'):
                print(' B spline extrusion not implemented yet')
                return ExtrudedClosedCurve(name, edges, height)

    elif len(edges) == 2:  # exactly two edges
        return Extruded2Edges(name, edges, height)
    else:  #  three or more edges
        return ExtrudedNEdges(name, edges, height)


def setGlobals(defineV, materialsV, solidsV):
    global define, materials, solids
    define = defineV
    materials = materialsV
    solids = solidsV


# duplicate of exportDefine in exportGDML
def exportDefine(name, v):
    global define
    # print('define : '+name)
    # print(v)
    # print(v[0])
    ET.SubElement(define, 'position', {'name': name, 'unit': 'mm',
                                       'x': str(v[0]),
                                       'y': str(v[1]),
                                       'z': str(v[2])})


# scale up a solid that will be subtracted so it ounched thru parent
def scaleUp(scaledName, originalName, zFactor):
    ss = ET.SubElement(solids, 'scaledSolid', {'name': scaledName})
    ET.SubElement(ss, 'solidref', {'ref': originalName})
    ET.SubElement(ss, 'scale', {'name': originalName+'_ss',
                                'x': '1', 'y': '1', 'z': str(zFactor)})


def rotatedPos(closedCurve, rot):
    # Circles and ellipses (tubes and elliptical tubes) are referenced to origin
    # in GDML and have to be translated to their position via a position reference
    # when placed as a physical volume. This is done by adding the translation
    # to the Part::Extrusion Placement. However, if the placement includes
    # a rotation, Geant4 GDML would rotate the Origin-based curve THEN translate.
    # This would not work. We have to translate first THEN rotate. This method
    # just does the needed rotation of the poisition vector
    #
    pos = closedCurve.position
    if isinstance(closedCurve, ExtrudedCircle) or \
       isinstance(closedCurve, ExtrudedEllipse):
        pos = rot*closedCurve.position

    return pos


def processExtrudedSketch(extrudeObj, sketchObj, xmlVol):
    from .exportGDML import insertXMLvolume, exportPosition, addVolRef, \
              quaternion2XYZ

    sortededges = Part.sortEdges(sketchObj.Shape.Edges)
    # sort by largest area to smallest area
    sortEdgelistsByBoundingBoxArea(sortededges)
    # getCurve returns one of the sub classes of ClosedCurve that
    # knows how to export the specifc closed edges
    # Make names based on Extrude name
    # curves = [getCurve(edges, extrudeObj.Label + str(i)) for i, edges in enumerate(sortededges)]
    if extrudeObj.Symmetric is True:
        height = extrudeObj.LengthFwd.Value
    else:
        height = extrudeObj.LengthFwd.Value + extrudeObj.LengthRev.Value
    eName = extrudeObj.Label
    # get a list of curves (instances of class ClosedCurve) for each set of closed edges
    curves = [getExtrudedCurve(eName+str(i), edges, height)
              for i, edges in enumerate(sortededges)]
    # build a generalized binary tree of closed curves.
    root = Node(curves[0], None, 0)
    for c in curves[1:]:
        root.insert(c)

    # Traverse the tree. The list returned is a list of [Node, parity], where parity = 0, says add to parent, 1 mean subtract
    lst = root.preOrderTraversal(root)
    rootnode = lst[0][0]
    rootCurve = rootnode.closedCurve
    rootCurve.export()  # a curve is created with a unique name
    firstName = rootCurve.name
    booleanName = firstName

    rootPos = rootCurve.position
    rootRot = rootCurve.rotation  # for now consider only angle of rotation about z-axis

    for c in lst[1:]:
        node = c[0]
        parity = c[1]
        curve = node.closedCurve
        curve.export()
        if parity == 0:
            boolType = 'union'
            secondName = curve.name
            secondPos = curve.position
        else:
            boolType = 'subtraction'
            secondName = curve.name+'_s'  # scale solids along z, so it punches thru
            scaleUp(secondName, curve.name, 1.10)
            secondPos = curve.position - Vector(0, 0, 0.01*height)

        booleanName = curve.name + '_bool'
        boolSolid = ET.SubElement(solids, boolType, {'name': booleanName})
        ET.SubElement(boolSolid, 'first', {'ref': firstName})
        ET.SubElement(boolSolid, 'second', {'ref': secondName})
        relativePosition = secondPos - rootPos
        zAngle = curve.rotation[2] - rootRot[2]
        posName = curve.name+'_pos'
        rotName = curve.name+'_rot'
        exportDefine(posName, relativePosition)  # position of second relative to first
        ET.SubElement(define, 'rotation', {'name': rotName, 'unit': 'deg',
                                           'x': '0', 'y': '0',
                                           'z': str(zAngle)})

        ET.SubElement(boolSolid, 'positionref', {'ref': posName})
        ET.SubElement(boolSolid, 'rotationref', {'ref': rotName})
        firstName = booleanName

    # now create logical and physical volumes for the last boolean.
    # Because the position of each closed curve might not be at the
    # origin, whereas primitives (tubes, cones, etc, are created centered at
    # the origin, we need to shift the position of the very first node by its
    # position, in addition to the shift by the Extrusion placement
    volName = booleanName+'Vol'  # booleanName is name of last boolean
    newvol = insertXMLvolume(volName)

    addVolRef(newvol, volName, extrudeObj, booleanName)
    # ET.SubElement(newvol,'materialref',{'ref': 'G4_Si'})
    # ET.SubElement(newvol,'solidref',{'ref': booleanName})

    pvol = ET.SubElement(xmlVol, 'physvol', {'name': 'PV'+volName})
    ET.SubElement(pvol, 'volumeref', {'ref': volName})
    extrudePosition = extrudeObj.Placement.Base
    if extrudeObj.Symmetric is False:
        if extrudeObj.Reversed is False:
            zoffset = Vector(0, 0, extrudeObj.LengthRev.Value)
        else:
            zoffset = Vector(0, 0, extrudeObj.LengthFwd.Value)
    else:
        zoffset = Vector(0, 0, extrudeObj.LengthFwd.Value/2)

    angles = quaternion2XYZ(extrudeObj.Placement.Rotation)
    # need to add rotations of elliptical tubes. Assume extrusion is on z-axis
    # Probably wil not work in general
    zAngle = angles[2] + rootRot[2]
    print(rootPos)
    print(rootCurve.name)
    print(rootCurve.position)
    rootPos = rotatedPos(rootCurve, extrudeObj.Placement.Rotation)
    print(rootPos)
    volPos = extrudePosition + rootPos - zoffset

    print(volPos)
    exportPosition(volName, pvol, volPos)

    rotName = booleanName + '_rot'
    ET.SubElement(define, 'rotation', {'name': rotName, 'unit': 'deg',
                                       'x': str(-angles[0]),
                                       'y': str(-angles[1]),
                                       'z': str(-zAngle)})
    ET.SubElement(pvol, 'rotationref', {'ref': rotName})
