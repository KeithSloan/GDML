# -*- coding: utf-8 -*-
# Fri Feb 11 01:11:14 PM PST 2022
# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2021 Keith Sloan <keith@sloan-home.co.uk>              *
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
# *   Acknowledgements :
# *                                                                        *
# *                                                                        *
# **************************************************************************
__title__ = "FreeCAD - OBJ -> GDML Tessellated importer"
__author__ = "Keith Sloan <keith@sloan-home.co.uk>"
__url__ = ["https://github.com/KeithSloan/FreeCAD_GDML"]

import FreeCAD, FreeCADGui
import os, io, sys, re
import Part, Draft


def joinDir(path):
    import os
    __dirname__ = os.path.dirname(__file__)
    return(os.path.join(__dirname__, path))


if open.__module__ == '__builtin__':
    pythonopen = open  # to distinguish python built-in open function from the one declared her


def open(filename):
    "called when freecad opens a file."

    print('Open : '+filename)
    docName = os.path.splitext(os.path.basename(filename))[0]
    print('path : '+filename)
    if filename.lower().endswith('.obj'):
        try:
            doc = FreeCAD.ActiveDocument()
            print('Active Doc')

        except:
            print('New Doc')
            doc = FreeCAD.newDocument(docName)

        processOBJ(doc, filename)
        return doc


def insert(filename, docname):
    "called when freecad imports a file"
    print('Insert filename : '+filename+' docname : '+docname)
    global doc
    groupname = os.path.splitext(os.path.basename(filename))[0]
    try:
        doc = FreeCAD.getDocument(docname)
    except NameError:
        doc = FreeCAD.newDocument(docname)
    if filename.lower().endswith('.obj'):
        processOBJ(doc, filename)


class switch(object):
    value = None

    def __new__(class_, value):
        class_.value = value
        return True


def case(*args):
    return any((arg == switch.value for arg in args))


def getSelectedMaterial():
    from .exportGDML import nameFromLabel
    from .GDMLObjects import GDMLmaterial

    list = FreeCADGui.Selection.getSelection()
    if list is not None:
        for obj in list:
            if hasattr(obj, 'Proxy'):
                if isinstance(obj.Proxy, GDMLmaterial) is True:
                    return nameFromLabel(obj.Label)

    return 0


def getVert(s):
    if '/' in s:
        ret = int(s[:s.index('/')])-1
        # print(ret)
    else:
        ret = int(s)-1
    return(ret)


def processOBJ(doc, filename):

    from .GDMLObjects import GDMLTessellated, ViewProvider
    print("import OBJ as GDML Tessellated")
    obj = doc.addObject("Part::FeaturePython", "GDMLTessellated")
    vertex = []
    faces = []
    f = io.open(filename, 'r', encoding="utf8")
    for line in f:
        # print(line)
        items = line.split(' ')
        il = len(items) - 1
        while switch(items[0]):
            if case('v'):
                # print('Vertex - len : '+str(l))
                if il >= 3:
                    vertex.append(FreeCAD.Vector(float(items[1]),
                                                 float(items[2]),
                                                 float(items[3])))
                else:
                    print('Invalid Vertex')
                    print(items)
                break

            if case('f'):
                # print('Face')
                if il == 3:
                    faces.append([getVert(items[1]), getVert(items[2]),
                                  getVert(items[3])])
                elif il == 4:
                    faces.append([getVert(items[1]), getVert(items[2]),
                                  getVert(items[3]), getVert(items[4])])
                else:
                    print('Warning Polygon : Number of Face Vertex = '+str(il))
                    print('Converting to Triangle Faces')
                    verts = []
                    for i in range(1, il+1):
                        v = vertex[getVert(items[i])]
                        verts.append(v)
                    verts.append(verts[0])
                    poly = Part.makePolygon(verts)
                    c = poly.CenterOfMass
                    ic = len(vertex)
                    vertex.append(c)
                    for i in range(1, il):
                        faces.append([ic, getVert(items[i]),
                                      getVert(items[i+1])])
                    faces.append([ic, getVert(items[i+1]), getVert(items[1])])
                break

            if case('#'):          # Comment ignore
                break

            if case('vt'):
                break

            if case('vn'):
                break

            print('Tag : '+items[0])
            break

    GDMLTessellated(obj, vertex, faces, False, 'mm', getSelectedMaterial())
    ViewProvider(obj.ViewObject)
    obj.recompute()
