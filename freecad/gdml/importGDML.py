# -*- coding: utf-8 -*-
# Mon Apr 18 09:46:41 AM PDT 2022
# emacs insert date command: Ctrl-U ESC-! date
# Sun Mar 27 12:57:07 PM PDT 2022
# Mon Feb 28 12:47:38 PM PST 2022
# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2017 Keith Sloan <keith@sloan-home.co.uk>              *
# *             (c) Dam Lambert 2020                                       *
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
# *                                                                        *
# **************************************************************************
__title__ = "FreeCAD - GDML importer"
__author__ = "Keith Sloan <keith@sloan-home.co.uk>"
__url__ = ["https://github.com/KeithSloan/FreeCAD_GDML"]

import FreeCAD
from PySide import QtGui
import os, io, sys, re
import Part, Draft


def joinDir(path):
    import os

    __dirname__ = os.path.dirname(__file__)
    return os.path.join(__dirname__, path)


from math import *
from . import GDMLShared

##########################
# Globals Dictionaries    #
##########################

# global setup, define, mats_xml, solids, structure, extension
# globals constDict, filesDict

if FreeCAD.GuiUp:
    import PartGui, FreeCADGui

    gui = True
else:
    print("FreeCAD Gui not present.")
    gui = False


if open.__module__ == "__builtin__":
    pythonopen = open  # to distinguish python built-in open function from the one declared here


# try:
#    _encoding = QtGui.QApplication.UnicodeUTF8
#    def translate(context, text):
#        "convenience function for Qt translator"
#        from PySide import QtGui
#        return QtGui.QApplication.translate(context, text, None, _encoding)
# except AttributeError:
#    def translate(context, text):
#        "convenience function for Qt translator"
#        from PySide import QtGui
#        return QtGui.QApplication.translate(context, text, None)


def open(filename):
    "called when freecad opens a file."
    global doc
    print("Open : " + filename)
    docName = os.path.splitext(os.path.basename(filename))[0]
    print("path : " + filename)
    if filename.lower().endswith(".gdml"):

        # import cProfile, pstats
        # profiler = cProfile.Profile()
        # profiler.enable()
        doc = FreeCAD.newDocument(docName)
        processGDML(doc, True, filename, True, False)
        # profiler.disable()
        # stats = pstats.Stats(profiler).sort_stats('cumtime')
        # stats.print_stats()

    elif filename.lower().endswith(".xml"):
        try:
            doc = FreeCAD.ActiveDocument()
            print("Active Doc")

        except:
            print("New Doc")
            doc = FreeCAD.newDocument(docName)

        processXML(doc, filename)

    return doc


def insert(filename, docname):
    "called when freecad imports a file"
    print("Insert filename : " + filename + " docname : " + docname)
    global doc

    # print(f'volDict : {volDict}')
    groupname = os.path.splitext(os.path.basename(filename))[0]
    try:
        doc = FreeCAD.getDocument(docname)
    except NameError:
        doc = FreeCAD.newDocument(docname)
    if filename.lower().endswith(".gdml"):
        # False flag indicates import
        processGDML(doc, False, filename, True, False)

    elif filename.lower().endswith(".xml"):
        processXML(doc, filename)


class switch(object):
    value = None

    def __new__(class_, value):
        class_.value = value
        return True


def case(*args):
    return any((arg == switch.value for arg in args))


def translate(shape, base):
    # Input Object and displacement vector - return a transformed shape
    myPlacement = FreeCAD.Placement()
    myPlacement.move(base)
    mat1 = myPlacement.toMatrix()
    # print(mat1)
    mat2 = shape.Matrix
    mat = mat1.multiply(mat2)
    # print(mat)
    retShape = shape.copy()
    retShape.transformShape(mat, True)
    return retShape


def checkConstant(vval):
    GDMLShared.trace(vval)


def getName(ptr):
    return ptr.attrib.get("name")


def getText(ptr, var, default):
    # print("Get Texti : "+str(ptr.attrib.get(var))+" : "+str(var))
    if var in ptr.attrib:
        return ptr.attrib.get(var)
    else:
        return default


def setDisplayMode(obj, mode):
    GDMLShared.trace("setDisplayMode : " + str(mode))
    if mode == 2:
        obj.ViewObject.DisplayMode = "Hide"

    if mode == 3:
        obj.ViewObject.DisplayMode = "Wireframe"


def newPartFeature(obj, name):
    newobj = obj.newObject("Part::FeaturePython", name)
    # FreeCAD can change the name i.e. hyphen to underscore
    # So also set the Objects Label
    newobj.Label = name
    return newobj


def newGroupPython(obj, name):
    newobj = obj.newObject("App::DocumentObjectGroupPython", name)
    # FreeCAD can change the name i.e. hyphen to underscore
    # So also set the Objects Label
    newobj.Label = name
    return newobj


def createArb8(part, solid, material, colour, px, py, pz, rot, displayMode):
    # parent, sold
    from .GDMLObjects import GDMLArb8, ViewProvider

    # GDMLShared.setTrace(True)
    GDMLShared.trace("CreateArb8 : ")
    # GDMLShared.trace("material : "+material)
    GDMLShared.trace(solid.attrib)

    myArb8 = newPartFeature(part, "GDMLArb8_" + getName(solid))
    v1x = GDMLShared.getVal(solid, "v1x")
    v1y = GDMLShared.getVal(solid, "v1y")
    v2x = GDMLShared.getVal(solid, "v2x")
    v2y = GDMLShared.getVal(solid, "v2y")
    v3x = GDMLShared.getVal(solid, "v3x")
    v3y = GDMLShared.getVal(solid, "v3y")
    v4x = GDMLShared.getVal(solid, "v4x")
    v4y = GDMLShared.getVal(solid, "v4y")
    v5x = GDMLShared.getVal(solid, "v5x")
    v5y = GDMLShared.getVal(solid, "v5y")
    v6x = GDMLShared.getVal(solid, "v6x")
    v6y = GDMLShared.getVal(solid, "v6y")
    v7x = GDMLShared.getVal(solid, "v7x")
    v7y = GDMLShared.getVal(solid, "v7y")
    v8x = GDMLShared.getVal(solid, "v8x")
    v8y = GDMLShared.getVal(solid, "v8y")
    dz = GDMLShared.getVal(solid, "dz")
    lunit = getText(solid, "lunit", "mm")

    GDMLArb8(
        myArb8,
        v1x,
        v1y,
        v2x,
        v2y,
        v3x,
        v3y,
        v4x,
        v4y,
        v5x,
        v5y,
        v6x,
        v6y,
        v7x,
        v7y,
        v8x,
        v8y,
        dz,
        lunit,
        material,
        colour,
    )
    GDMLShared.trace(
        "Logical Position : " + str(px) + "," + str(py) + "," + str(pz)
    )
    base = FreeCAD.Vector(px, py, pz)
    myArb8.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(myArb8.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(myArb8.ViewObject)
        setDisplayMode(myArb8, displayMode)
    return myArb8


def createBox(
    part, solid, material, colour, px, py, pz, rot, displayMode, solidName=None
):
    # parent, sold
    from .GDMLObjects import GDMLBox, ViewProvider

    # GDMLShared.setTrace(True)
    GDMLShared.trace("CreateBox : ")
    # GDMLShared.trace("material : "+material)
    GDMLShared.trace(solid.attrib)

    # modifs lambda (otherwise each time we open the gdml file,
    # the part name will have one more GDMLBox added
    # No - need to remove leading GDMLBox on export

    if solidName is None:
        solidName = getName(solid)
    mycube = newPartFeature(part, "GDMLBox_" + solidName)
    x = GDMLShared.getVal(solid, "x")
    y = GDMLShared.getVal(solid, "y")
    z = GDMLShared.getVal(solid, "z")
    lunit = getText(solid, "lunit", "mm")
    # print(f'Cube colour : {colour}')
    GDMLBox(mycube, x, y, z, lunit, material, colour)
    GDMLShared.trace(
        "Logical Position : " + str(px) + "," + str(py) + "," + str(pz)
    )
    base = FreeCAD.Vector(px, py, pz)
    mycube.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mycube.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(mycube.ViewObject)
        setDisplayMode(mycube, displayMode)
    # myCube.Shape = translate(mycube.Shape,base)
    return mycube


def createCone(
    part, solid, material, colour, px, py, pz, rot, displayMode, solidName=None
):
    from .GDMLObjects import GDMLCone, ViewProvider

    GDMLShared.trace("CreateCone : ")
    GDMLShared.trace(solid.attrib)
    rmin1 = GDMLShared.getVal(solid, "rmin1", 0)
    rmax1 = GDMLShared.getVal(solid, "rmax1")
    rmin2 = GDMLShared.getVal(solid, "rmin2", 0)
    rmax2 = GDMLShared.getVal(solid, "rmax2")
    z = GDMLShared.getVal(solid, "z")
    startphi = GDMLShared.getVal(solid, "startphi")
    deltaphi = GDMLShared.getVal(solid, "deltaphi")
    aunit = getText(solid, "aunit", "rad")
    lunit = getText(solid, "lunit", "mm")
    if solidName is None:
        solidName = getName(solid)
    mycone = newPartFeature(part, "GDMLCone_" + solidName)
    GDMLCone(
        mycone,
        rmin1,
        rmax1,
        rmin2,
        rmax2,
        z,
        startphi,
        deltaphi,
        aunit,
        lunit,
        material,
        colour,
    )
    GDMLShared.trace("CreateCone : ")
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    mycone.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mycone.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set "ViewProvider before setDisplay
        ViewProvider(mycone.ViewObject)
        setDisplayMode(mycone, displayMode)
    return mycone


def createElcone(part, solid, material, colour, px, py, pz, rot, displayMode):
    from .GDMLObjects import GDMLElCone, ViewProvider

    GDMLShared.trace("CreateElCone : ")
    dx = GDMLShared.getVal(solid, "dx")
    dy = GDMLShared.getVal(solid, "dy")
    zmax = GDMLShared.getVal(solid, "zmax")
    zcut = GDMLShared.getVal(solid, "zcut")
    lunit = getText(solid, "lunit", "mm")
    myelcone = newPartFeature(part, "GDMLElCone_" + getName(solid))
    GDMLElCone(myelcone, dx, dy, zmax, zcut, lunit, material, colour)
    GDMLShared.trace("CreateElCone : ")
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    # base = FreeCAD.Vector(0,0,0)
    myelcone.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(myelcone.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(myelcone.ViewObject)
        setDisplayMode(myelcone, displayMode)
    return myelcone


def createEllipsoid(
    part, solid, material, colour, px, py, pz, rot, displayMode, solidName=None
):
    from .GDMLObjects import GDMLEllipsoid, ViewProvider

    GDMLShared.trace("CreateElTube : ")
    GDMLShared.trace(solid.attrib)
    ax = GDMLShared.getVal(solid, "ax")
    by = GDMLShared.getVal(solid, "by")
    cz = GDMLShared.getVal(solid, "cz")
    zcut1 = GDMLShared.getVal(solid, "zcut1")
    zcut2 = GDMLShared.getVal(solid, "zcut2")
    lunit = getText(solid, "lunit", "mm")
    if solidName is None:
        solidName = getName(solid)
    myelli = newPartFeature(part, "GDMLEllipsoid_" + solidName)
    # cuts 0 for now
    GDMLEllipsoid(myelli, ax, by, cz, zcut1, zcut2, lunit, material, colour)
    GDMLShared.trace("CreateEllipsoid : ")
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    myelli.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(myelli.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(myelli.ViewObject)
        setDisplayMode(myelli, displayMode)
    return myelli


def createEltube(part, solid, material, colour, px, py, pz, rot, displayMode):
    from .GDMLObjects import GDMLElTube, ViewProvider

    GDMLShared.trace("CreateElTube : ")
    GDMLShared.trace(solid.attrib)
    dx = GDMLShared.getVal(solid, "dx")
    dy = GDMLShared.getVal(solid, "dy")
    dz = GDMLShared.getVal(solid, "dz")
    lunit = getText(solid, "lunit", "mm")
    myeltube = newPartFeature(part, "GDMLElTube_" + getName(solid))
    GDMLElTube(myeltube, dx, dy, dz, lunit, material, colour)
    GDMLShared.trace("CreateElTube : ")
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    myeltube.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(myeltube.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDispla
        ViewProvider(myeltube.ViewObject)
        setDisplayMode(myeltube, displayMode)
    return myeltube


def createGenericPolycone(
    part, solid, material, colour, px, py, pz, rot, displayMode
):
    from .GDMLObjects import (
        GDMLGenericPolycone,
        GDMLrzpoint,
        ViewProvider,
        ViewProviderExtension,
    )

    GDMLShared.trace("Create GenericPolycone : ")
    GDMLShared.trace(solid.attrib)
    startphi = GDMLShared.getVal(solid, "startphi")
    deltaphi = GDMLShared.getVal(solid, "deltaphi")
    aunit = getText(solid, "aunit", "rad")
    lunit = getText(solid, "lunit", "mm")
    mypolycone = newPartFeature(part, "GDMLGenericPolycone_" + getName(solid))
    mypolycone.addExtension("App::GroupExtensionPython")
    GDMLGenericPolycone(
        mypolycone, startphi, deltaphi, aunit, lunit, material, colour
    )
    if FreeCAD.GuiUp:
        ViewProviderExtension(mypolycone.ViewObject)

    # mypolycone.ViewObject.DisplayMode = "Shaded"
    GDMLShared.trace(solid.findall("rzpoint"))
    for zplane in solid.findall("rzpoint"):
        GDMLShared.trace(zplane)
        r = GDMLShared.getVal(zplane, "r", 0)
        z = GDMLShared.getVal(zplane, "z")
        myrzpoint = FreeCAD.ActiveDocument.addObject(
            "App::FeaturePython", "rzpoint"
        )
        mypolycone.addObject(myrzpoint)
        GDMLrzpoint(myrzpoint, r, z)
        if FreeCAD.GuiUp:
            ViewProvider(myrzpoint)

    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    mypolycone.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mypolycone.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        setDisplayMode(mypolycone, displayMode)
    return mypolycone


def createGenericPolyhedra(
    part, solid, material, colour, px, py, pz, rot, displayMode
):
    from .GDMLObjects import (
        GDMLGenericPolyhedra,
        GDMLrzpoint,
        ViewProvider,
        ViewProviderExtension,
    )

    GDMLShared.trace("Create GenericPolyhedra : ")
    GDMLShared.trace(solid.attrib)
    startphi = GDMLShared.getVal(solid, "startphi")
    deltaphi = GDMLShared.getVal(solid, "deltaphi")
    numsides = int(GDMLShared.getVal(solid, "numsides"))
    aunit = getText(solid, "aunit", "rad")
    lunit = getText(solid, "lunit", "mm")
    mypolyhedra = newPartFeature(
        part, "GDMLGenericPolyhedra_" + getName(solid)
    )
    mypolyhedra.addExtension("App::GroupExtensionPython")
    GDMLGenericPolyhedra(
        mypolyhedra,
        startphi,
        deltaphi,
        numsides,
        aunit,
        lunit,
        material,
        colour,
    )
    if FreeCAD.GuiUp:
        ViewProviderExtension(mypolyhedra.ViewObject)

    # mypolycone.ViewObject.DisplayMode = "Shaded"
    GDMLShared.trace(solid.findall("rzpoint"))
    for zplane in solid.findall("rzpoint"):
        GDMLShared.trace(zplane)
        r = GDMLShared.getVal(zplane, "r", 0)
        z = GDMLShared.getVal(zplane, "z")
        myrzpoint = FreeCAD.ActiveDocument.addObject(
            "App::FeaturePython", "rzpoint"
        )
        mypolyhedra.addObject(myrzpoint)
        GDMLrzpoint(myrzpoint, r, z)
        if FreeCAD.GuiUp:
            ViewProvider(myrzpoint)

    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    mypolyhedra.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mypolyhedra.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        setDisplayMode(mypolyhedra, displayMode)
    return mypolyhedra


def createOrb(
    part, solid, material, colour, px, py, pz, rot, displayMode, solidName=None
):
    from .GDMLObjects import GDMLOrb, ViewProvider

    GDMLShared.trace("CreateOrb : ")
    GDMLShared.trace(solid.attrib)
    r = GDMLShared.getVal(solid, "r")
    lunit = getText(solid, "lunit", "mm")
    if solidName is None:
        solidName = getName(solid)
    myorb = newPartFeature(part, "GDMLOrb_" + solidName)
    GDMLOrb(myorb, r, lunit, material, colour)
    GDMLShared.trace("CreateOrb : ")
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    myorb.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(myorb.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(myorb.ViewObject)
        setDisplayMode(myorb, displayMode)
    return myorb


def createPara(
    part, solid, material, colour, px, py, pz, rot, displayMode, solidName=None
):
    from .GDMLObjects import GDMLPara, ViewProvider

    GDMLShared.trace("CreatePara : ")
    GDMLShared.trace(solid.attrib)
    aunit = getText(solid, "aunit", "rad")
    lunit = getText(solid, "lunit", "mm")
    x = GDMLShared.getVal(solid, "x")
    y = GDMLShared.getVal(solid, "y")
    z = GDMLShared.getVal(solid, "z")
    alpha = GDMLShared.getVal(solid, "alpha")
    theta = GDMLShared.getVal(solid, "theta")
    phi = GDMLShared.getVal(solid, "phi")
    if solidName is None:
        solidName = getName(solid)
    mypara = newPartFeature(part, "GDMLPara_" + solidName)
    GDMLPara(
        mypara, x, y, z, alpha, theta, phi, aunit, lunit, material, colour
    )
    GDMLShared.trace("CreatePara : ")
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    mypara.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mypara.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(mypara.ViewObject)
        setDisplayMode(mypara, displayMode)
    return mypara


def createHype(
    part, solid, material, colour, px, py, pz, rot, displayMode, solidName=None
):
    from .GDMLObjects import GDMLHype, ViewProvider

    GDMLShared.trace("CreateHype : ")
    GDMLShared.trace(solid.attrib)
    aunit = getText(solid, "aunit", "rad")
    lunit = getText(solid, "lunit", "mm")
    rmin = GDMLShared.getVal(solid, "rmin")
    rmax = GDMLShared.getVal(solid, "rmax")
    z = GDMLShared.getVal(solid, "z")
    inst = GDMLShared.getVal(solid, "inst")
    outst = GDMLShared.getVal(solid, "outst")
    if solidName is None:
        solidName = getName(solid)
    myhype = newPartFeature(part, "GDMLHype_" + solidName)
    GDMLHype(
        myhype, rmin, rmax, z, inst, outst, aunit, lunit, material, colour
    )
    GDMLShared.trace("CreateHype : ")
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    myhype.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(myhype.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(myhype.ViewObject)
        setDisplayMode(myhype, displayMode)
    return myhype


def createParaboloid(
    part, solid, material, colour, px, py, pz, rot, displayMode
):
    from .GDMLObjects import GDMLParaboloid, ViewProvider

    GDMLShared.trace("CreateParaboloid : ")
    GDMLShared.trace(solid.attrib)
    lunit = getText(solid, "lunit", "mm")
    rlo = GDMLShared.getVal(solid, "rlo")
    rhi = GDMLShared.getVal(solid, "rhi")
    dz = GDMLShared.getVal(solid, "dz")
    myparaboloid = newPartFeature(part, "GDMLParaboloid_" + getName(solid))
    GDMLParaboloid(myparaboloid, rlo, rhi, dz, lunit, material, colour)
    GDMLShared.trace("CreateParaboloid : ")
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    myparaboloid.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(myparaboloid.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(myparaboloid.ViewObject)
        setDisplayMode(myparaboloid, displayMode)
    return myparaboloid


def createPolycone(
    part, solid, material, colour, px, py, pz, rot, displayMode
):
    from .GDMLObjects import (
        GDMLPolycone,
        GDMLzplane,
        ViewProvider,
        ViewProviderExtension,
    )

    GDMLShared.trace("Create Polycone : ")
    GDMLShared.trace(solid.attrib)
    startphi = GDMLShared.getVal(solid, "startphi")
    deltaphi = GDMLShared.getVal(solid, "deltaphi")
    aunit = getText(solid, "aunit", "rad")
    lunit = getText(solid, "lunit", "mm")
    mypolycone = newPartFeature(part, "GDMLPolycone_" + getName(solid))
    mypolycone.addExtension("App::GroupExtensionPython")
    GDMLPolycone(
        mypolycone, startphi, deltaphi, aunit, lunit, material, colour
    )
    if FreeCAD.GuiUp:
        ViewProviderExtension(mypolycone.ViewObject)

    # mypolycone.ViewObject.DisplayMode = "Shaded"
    GDMLShared.trace(solid.findall("zplane"))
    for zplane in solid.findall("zplane"):
        GDMLShared.trace(zplane)
        rmin = GDMLShared.getVal(zplane, "rmin", 0)
        rmax = GDMLShared.getVal(zplane, "rmax")
        z = GDMLShared.getVal(zplane, "z")
        myzplane = FreeCAD.ActiveDocument.addObject(
            "App::FeaturePython", "zplane"
        )
        mypolycone.addObject(myzplane)
        # myzplane=mypolycone.newObject('App::FeaturePython', 'zplane')
        GDMLzplane(myzplane, rmin, rmax, z)
        if FreeCAD.GuiUp:
            ViewProvider(myzplane)

    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    mypolycone.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mypolycone.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        setDisplayMode(mypolycone, displayMode)
    return mypolycone


def createPolyhedra(
    part, solid, material, colour, px, py, pz, rot, displayMode
):
    from .GDMLObjects import (
        GDMLPolyhedra,
        GDMLzplane,
        ViewProvider,
        ViewProviderExtension,
    )

    GDMLShared.trace("Create Polyhedra : ")
    GDMLShared.trace(solid.attrib)
    startphi = GDMLShared.getVal(solid, "startphi")
    deltaphi = GDMLShared.getVal(solid, "deltaphi")
    numsides = int(GDMLShared.getVal(solid, "numsides"))
    aunit = getText(solid, "aunit", "rad")
    lunit = getText(solid, "lunit", "mm")
    mypolyhedra = newPartFeature(part, "GDMLPolyhedra_" + getName(solid))
    mypolyhedra.addExtension("App::GroupExtensionPython")
    GDMLPolyhedra(
        mypolyhedra,
        startphi,
        deltaphi,
        numsides,
        aunit,
        lunit,
        material,
        colour,
    )
    if FreeCAD.GuiUp:
        ViewProviderExtension(mypolyhedra.ViewObject)

    # mypolyhedra.ViewObject.DisplayMode = "Shaded"
    GDMLShared.trace(solid.findall("zplane"))
    for zplane in solid.findall("zplane"):
        GDMLShared.trace(zplane)
        rmin = GDMLShared.getVal(zplane, "rmin", 0)
        rmax = GDMLShared.getVal(zplane, "rmax")
        z = GDMLShared.getVal(zplane, "z")
        myzplane = FreeCAD.ActiveDocument.addObject(
            "App::FeaturePython", "zplane"
        )
        mypolyhedra.addObject(myzplane)
        # myzplane=mypolyhedra.newObject('App::FeaturePython', 'zplane')
        GDMLzplane(myzplane, rmin, rmax, z)
        if FreeCAD.GuiUp:
            ViewProvider(myzplane)

    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    mypolyhedra.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mypolyhedra.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        setDisplayMode(mypolyhedra, displayMode)
    return mypolyhedra


def createScaledSolid(
    part, solid, material, colour, px, py, pz, rot, displayMode
):
    print("ScaledSolid")
    global solids
    solidref = GDMLShared.getRef(solid, "solidref")
    newSolid = solids.find("*[@name='%s']" % solidref)
    scaledObj = createSolid(
        part, newSolid, material, colour, px, py, pz, rot, displayMode
    )
    scale = solid.find("scale")
    scaleName = scale.get("name")
    sx = GDMLShared.getVal(scale, "x")
    sy = GDMLShared.getVal(scale, "y")
    sz = GDMLShared.getVal(scale, "z")
    scaleVec = FreeCAD.Vector(sx, sy, sz)
    mat = FreeCAD.Matrix()
    mat.scale(scaleVec)
    scaledObj.recompute()
    scaledObj.Shape.transformGeometry(mat)
    scaledObj.recompute()
    scaledObj.addProperty(
        "App::PropertyVector", "scale", "Base", "scale"
    ).scale = scaleVec
    return scaledObj


def createSphere(
    part, solid, material, colour, px, py, pz, rot, displayMode, solidName=None
):
    from .GDMLObjects import GDMLSphere, ViewProvider

    # GDMLShared.setTrace(True)
    GDMLShared.trace("CreateSphere : ")
    GDMLShared.trace("Display Mode : " + str(displayMode))
    GDMLShared.trace(solid.attrib)
    rmin = GDMLShared.getVal(solid, "rmin", 0)
    rmax = GDMLShared.getVal(solid, "rmax")
    startphi = GDMLShared.getVal(solid, "startphi")
    deltaphi = GDMLShared.getVal(solid, "deltaphi")
    aunit = getText(solid, "aunit", "rad")
    lunit = getText(solid, "lunit", "mm")
    starttheta = GDMLShared.getVal(solid, "starttheta")
    deltatheta = GDMLShared.getVal(solid, "deltatheta")
    if solidName is None:
        solidName = getName(solid)
    mysphere = newPartFeature(part, "GDMLSphere_" + solidName)
    GDMLSphere(
        mysphere,
        rmin,
        rmax,
        startphi,
        deltaphi,
        starttheta,
        deltatheta,
        aunit,
        lunit,
        material,
        colour,
    )
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    mysphere.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mysphere.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(mysphere.ViewObject)
        setDisplayMode(mysphere, displayMode)
    return mysphere


def createTetra(part, solid, material, colour, px, py, pz, rot, displayMode):
    from .GDMLObjects import GDMLTetra, ViewProvider

    # GDMLShared.setTrace(True)
    GDMLShared.trace("CreateTet : ")
    GDMLShared.trace(solid.attrib)
    v1 = GDMLShared.getDefinedVector(solid, "vertex1")
    v2 = GDMLShared.getDefinedVector(solid, "vertex2")
    v3 = GDMLShared.getDefinedVector(solid, "vertex3")
    v4 = GDMLShared.getDefinedVector(solid, "vertex4")
    lunit = getText(solid, "lunit", "mm")
    mytetra = newPartFeature(part, "GDMLTetra_" + getName(solid))
    GDMLTetra(mytetra, v1, v2, v3, v4, lunit, material, colour)
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    mytetra.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mytetra.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(mytetra.ViewObject)
        setDisplayMode(mytetra, displayMode)
    return mytetra


def createTorus(
    part, solid, material, colour, px, py, pz, rot, displayMode, solidName=None
):
    from .GDMLObjects import GDMLTorus, ViewProvider

    # GDMLShared.setTrace(True)
    GDMLShared.trace("CreateTorus : ")
    GDMLShared.trace(solid.attrib)
    rmin = GDMLShared.getVal(solid, "rmin", 0)
    rmax = GDMLShared.getVal(solid, "rmax")
    rtor = GDMLShared.getVal(solid, "rtor")
    startphi = GDMLShared.getVal(solid, "startphi")
    deltaphi = GDMLShared.getVal(solid, "deltaphi")
    aunit = getText(solid, "aunit", "rad")
    lunit = getText(solid, "lunit", "mm")
    if solidName is None:
        solidName = getName(solid)
    mytorus = newPartFeature(part, "GDMLTorus_" + solidName)
    GDMLTorus(
        mytorus,
        rmin,
        rmax,
        rtor,
        startphi,
        deltaphi,
        aunit,
        lunit,
        material,
        colour,
    )
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    mytorus.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mytorus.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(mytorus.ViewObject)
        setDisplayMode(mytorus, displayMode)
    return mytorus


def createTrap(part, solid, material, colour, px, py, pz, rot, displayMode):
    from .GDMLObjects import GDMLTrap, ViewProvider

    GDMLShared.trace("CreateTrap : ")
    GDMLShared.trace(solid.attrib)
    z = GDMLShared.getVal(solid, "z")
    x1 = GDMLShared.getVal(solid, "x1")
    x2 = GDMLShared.getVal(solid, "x2")
    x3 = GDMLShared.getVal(solid, "x3")
    x4 = GDMLShared.getVal(solid, "x4")
    y1 = GDMLShared.getVal(solid, "y1")
    y2 = GDMLShared.getVal(solid, "y2")
    theta = GDMLShared.getVal(solid, "theta")
    phi = GDMLShared.getVal(solid, "phi")
    alpha1 = GDMLShared.getVal(solid, "alpha1")
    aunit = getText(solid, "aunit", "rad")
    lunit = getText(solid, "lunit", "mm")
    # print z
    mytrap = newPartFeature(part, "GDMLTrap_" + getName(solid))
    GDMLTrap(
        mytrap,
        z,
        theta,
        phi,
        x1,
        x2,
        x3,
        x4,
        y1,
        y2,
        alpha1,
        aunit,
        lunit,
        material,
        colour,
    )
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    mytrap.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mytrap.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(mytrap.ViewObject)
        setDisplayMode(mytrap, displayMode)
    return mytrap


def createTrd(
    part, solid, material, colour, px, py, pz, rot, displayMode, solidName=None
):
    from .GDMLObjects import GDMLTrd, ViewProvider

    GDMLShared.trace("CreateTrd : ")
    GDMLShared.trace(solid.attrib)
    z = GDMLShared.getVal(solid, "z")
    x1 = GDMLShared.getVal(solid, "x1")
    x2 = GDMLShared.getVal(solid, "x2")
    y1 = GDMLShared.getVal(solid, "y1")
    y2 = GDMLShared.getVal(solid, "y2")
    lunit = getText(solid, "lunit", "mm")
    # print z
    if solidName is None:
        solidName = getName(solid)
    mytrd = newPartFeature(part, "GDMLTrd_" + solidName)
    GDMLTrd(mytrd, z, x1, x2, y1, y2, lunit, material, colour)
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    mytrd.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mytrd.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(mytrd.ViewObject)
        setDisplayMode(mytrd, displayMode)
    return mytrd


def createTwistedbox(
    part, solid, material, colour, px, py, pz, rot, displayMode
):
    # parent, sold
    from .GDMLObjects import GDMLTwistedbox, ViewProvider

    # GDMLShared.setTrace(True)
    GDMLShared.trace("CreateTwisted : ")
    # GDMLShared.trace("material : "+material)
    GDMLShared.trace(solid.attrib)

    # modifs lambda (otherwise each time we open the gdml file,
    # the part name will have one more GDMLBox added
    # No - need to remove leading GDMLBox on export
    mypart = newPartFeature(part, "GDMLTwistedbox_" + getName(solid))
    x = GDMLShared.getVal(solid, "x")
    y = GDMLShared.getVal(solid, "y")
    z = GDMLShared.getVal(solid, "z")
    lunit = getText(solid, "lunit", "mm")
    angle = GDMLShared.getVal(solid, "PhiTwist")
    aunit = getText(solid, "aunit", "rad")

    # print(f'Cube colour : {colour}')
    GDMLTwistedbox(mypart, angle, x, y, z, aunit, lunit, material, colour)
    GDMLShared.trace(
        "Logical Position : " + str(px) + "," + str(py) + "," + str(pz)
    )
    base = FreeCAD.Vector(px, py, pz)
    mypart.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mypart.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(mypart.ViewObject)
        setDisplayMode(mypart, displayMode)
    # myCube.Shape = translate(mycube.Shape, base)
    return mypart


def createTwistedtrap(
    part, solid, material, colour, px, py, pz, rot, displayMode
):
    from .GDMLObjects import GDMLTwistedtrap, ViewProvider

    GDMLShared.trace("CreateTwistedtrap : ")
    GDMLShared.trace(solid.attrib)
    PhiTwist = GDMLShared.getVal(solid, "PhiTwist")
    z = GDMLShared.getVal(solid, "z")
    x1 = GDMLShared.getVal(solid, "x1")
    x2 = GDMLShared.getVal(solid, "x2")
    x3 = GDMLShared.getVal(solid, "x3")
    x4 = GDMLShared.getVal(solid, "x4")
    y1 = GDMLShared.getVal(solid, "y1")
    y2 = GDMLShared.getVal(solid, "y2")
    theta = GDMLShared.getVal(solid, "Theta")
    phi = GDMLShared.getVal(solid, "Phi")
    alpha = GDMLShared.getVal(solid, "Alph")
    aunit = getText(solid, "aunit", "rad")
    lunit = getText(solid, "lunit", "mm")
    # print z
    mytrap = newPartFeature(part, "GDMLTwistedtrap_" + getName(solid))
    GDMLTwistedtrap(
        mytrap,
        PhiTwist,
        z,
        theta,
        phi,
        x1,
        x2,
        x3,
        x4,
        y1,
        y2,
        alpha,
        aunit,
        lunit,
        material,
        colour,
    )
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    mytrap.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mytrap.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(mytrap.ViewObject)
        setDisplayMode(mytrap, displayMode)
    return mytrap


def createTwistedtrd(
    part, solid, material, colour, px, py, pz, rot, displayMode
):
    from .GDMLObjects import GDMLTwistedtrd, ViewProvider

    GDMLShared.trace("CreateTwistedtrd : ")
    GDMLShared.trace(solid.attrib)
    z = GDMLShared.getVal(solid, "z")
    x1 = GDMLShared.getVal(solid, "x1")
    x2 = GDMLShared.getVal(solid, "x2")
    y1 = GDMLShared.getVal(solid, "y1")
    y2 = GDMLShared.getVal(solid, "y2")
    lunit = getText(solid, "lunit", "mm")
    angle = GDMLShared.getVal(solid, "PhiTwist")
    aunit = getText(solid, "aunit", "rad")
    # print z
    mytrd = newPartFeature(part, "GDMLTwistedtrd_" + getName(solid))
    GDMLTwistedtrd(
        mytrd, angle, z, x1, x2, y1, y2, aunit, lunit, material, colour
    )
    GDMLShared.trace("Position : " + str(px) + ", " + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    mytrd.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mytrd.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(mytrd.ViewObject)
        setDisplayMode(mytrd, displayMode)
    return mytrd


def createTwistedtubs(
    part, solid, material, colour, px, py, pz, rot, displayMode
):
    from .GDMLObjects import GDMLTwistedtubs, ViewProvider

    GDMLShared.trace("CreateTwistedtubs : ")
    GDMLShared.trace(solid.attrib)
    zlen = GDMLShared.getVal(solid, "zlen")
    endinnerrad = GDMLShared.getVal(solid, "endinnerrad")
    endouterrad = GDMLShared.getVal(solid, "endouterrad")
    lunit = getText(solid, "lunit", "mm")
    twistedangle = GDMLShared.getVal(solid, "twistedangle")
    phi = GDMLShared.getVal(solid, "phi")
    aunit = getText(solid, "aunit", "rad")
    mypart = newPartFeature(part, "GDMLTwistedtubs_" + getName(solid))
    GDMLTwistedtubs(
        mypart,
        endinnerrad,
        endouterrad,
        zlen,
        twistedangle,
        phi,
        aunit,
        lunit,
        material,
        colour,
    )
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    mypart.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mypart.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(mypart.ViewObject)
        setDisplayMode(mypart, displayMode)
    return mypart


def createXtru(part, solid, material, colour, px, py, pz, rot, displayMode):
    from .GDMLObjects import (
        GDMLXtru,
        GDML2dVertex,
        GDMLSection,
        ViewProvider,
        ViewProviderExtension,
    )

    GDMLShared.trace("CreateXtru : ")
    # print(solid)
    # print(getName(solid))
    myXtru = newPartFeature(part, "GDMLXtru_" + getName(solid))
    # myXtru.addExtension("App::GroupExtensionPython")
    lunit = getText(solid, "lunit", "mm")
    GDMLXtru(myXtru, lunit, material, colour)
    if FreeCAD.GuiUp:
        ViewProviderExtension(myXtru.ViewObject)
    for vert2d in solid.findall("twoDimVertex"):
        x = GDMLShared.getVal(vert2d, "x")
        y = GDMLShared.getVal(vert2d, "y")
        my2dVert = FreeCAD.ActiveDocument.addObject(
            "App::FeaturePython", "GDML2DVertex"
        )
        # myzplane=mypolycone.newObject('App::FeaturePython', 'zplane')
        GDML2dVertex(my2dVert, x, y)
        myXtru.addObject(my2dVert)
        if FreeCAD.GuiUp:
            ViewProvider(my2dVert)
    for section in solid.findall("section"):
        zOrder = int(GDMLShared.getVal(section, "zOrder"))  # Get Int
        zPosition = GDMLShared.getVal(section, "zPosition")  # Get Float
        xOffset = GDMLShared.getVal(section, "xOffset")
        yOffset = GDMLShared.getVal(section, "yOffset")
        scalingFactor = GDMLShared.getVal(section, "scalingFactor")
        mysection = FreeCAD.ActiveDocument.addObject(
            "App::FeaturePython", "GDMLSection"
        )
        GDMLSection(
            mysection, zOrder, zPosition, xOffset, yOffset, scalingFactor
        )
        myXtru.addObject(mysection)
        if FreeCAD.GuiUp:
            ViewProvider(mysection)

    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    myXtru.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(myXtru.Placement.Rotation)
    # Shape is still Null at this point
    # print("Xtru Shape : ")
    # print("Is Null : "+str(myXtru.Shape.isNull()))
    return myXtru


def createTube(part, solid, material, colour, px, py, pz, rot, displayMode):
    from .GDMLObjects import GDMLTube, ViewProvider

    GDMLShared.trace("CreateTube : ")
    GDMLShared.trace(solid.attrib)
    rmin = GDMLShared.getVal(solid, "rmin", 0)
    rmax = GDMLShared.getVal(solid, "rmax")
    z = GDMLShared.getVal(solid, "z")
    startphi = GDMLShared.getVal(solid, "startphi")
    deltaphi = GDMLShared.getVal(solid, "deltaphi")
    aunit = getText(solid, "aunit", "rad")
    lunit = getText(solid, "lunit", "mm")
    GDMLShared.trace(rmin)
    GDMLShared.trace(rmax)
    GDMLShared.trace(z)
    mytube = newPartFeature(part, "GDMLTube_" + getName(solid))
    GDMLTube(
        mytube,
        rmin,
        rmax,
        z,
        startphi,
        deltaphi,
        aunit,
        lunit,
        material,
        colour,
    )
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    # base = FreeCAD.Vector(0, 0, 0)
    base = FreeCAD.Vector(px, py, pz)
    mytube.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mytube.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(mytube.ViewObject)
        setDisplayMode(mytube, displayMode)
    return mytube


def createCutTube(part, solid, material, colour, px, py, pz, rot, displayMode):
    from .GDMLObjects import GDMLcutTube, ViewProvider

    GDMLShared.trace("CreateCutTube : ")
    GDMLShared.trace(solid.attrib)
    rmin = GDMLShared.getVal(solid, "rmin", 0)
    rmax = GDMLShared.getVal(solid, "rmax")
    z = GDMLShared.getVal(solid, "z")
    startphi = GDMLShared.getVal(solid, "startphi")
    deltaphi = GDMLShared.getVal(solid, "deltaphi")
    aunit = getText(solid, "aunit", "rad")
    GDMLShared.trace("aunit : " + aunit)
    lowX = GDMLShared.getVal(solid, "lowX")
    lowY = GDMLShared.getVal(solid, "lowY")
    lowZ = GDMLShared.getVal(solid, "lowZ")
    highX = GDMLShared.getVal(solid, "highX")
    highY = GDMLShared.getVal(solid, "highY")
    highZ = GDMLShared.getVal(solid, "highZ")
    lunit = getText(solid, "lunit", "mm")
    GDMLShared.trace(rmin)
    GDMLShared.trace(rmax)
    GDMLShared.trace(z)
    GDMLShared.trace(lowX)
    GDMLShared.trace(lowY)
    GDMLShared.trace(lowZ)
    GDMLShared.trace(highX)
    GDMLShared.trace(highY)
    GDMLShared.trace(highZ)
    mycuttube = newPartFeature(part, "GDMLcutTube_" + getName(solid))
    GDMLcutTube(
        mycuttube,
        rmin,
        rmax,
        z,
        startphi,
        deltaphi,
        aunit,
        lowX,
        lowY,
        lowZ,
        highX,
        highY,
        highZ,
        lunit,
        material,
        colour,
    )
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    # base = FreeCAD.Vector(0, 0, 0)
    base = FreeCAD.Vector(px, py, pz)
    mycuttube.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mycuttube.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(mycuttube.ViewObject)
        setDisplayMode(mycuttube, displayMode)
    return mycuttube


def createParameterisedTube(
    part, solid, material, colour, px, py, pz, rot, displayMode, solidName=None
):
    from .GDMLObjects import GDMLTube, ViewProvider

    GDMLShared.trace("CreateTube : ")
    GDMLShared.trace(solid.attrib)
    rmin = GDMLShared.getVal(solid, "InR", 0)
    rmax = GDMLShared.getVal(solid, "OutR")
    z = GDMLShared.getVal(solid, "hz")
    startphi = GDMLShared.getVal(solid, "StartPhi")
    deltaphi = GDMLShared.getVal(solid, "DeltaPhi")
    aunit = getText(solid, "aunit", "rad")
    lunit = getText(solid, "lunit", "mm")
    GDMLShared.trace(rmin)
    GDMLShared.trace(rmax)
    GDMLShared.trace(z)
    if solidName is None:
        solidName = getName(solid)
    mytube = newPartFeature(part, "GDMLTube_" + solidName)
    GDMLTube(
        mytube,
        rmin,
        rmax,
        z,
        startphi,
        deltaphi,
        aunit,
        lunit,
        material,
        colour,
    )
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    # base = FreeCAD.Vector(0, 0, 0)
    base = FreeCAD.Vector(px, py, pz)
    mytube.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mytube.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(mytube.ViewObject)
        setDisplayMode(mytube, displayMode)
    return mytube


def createParameterisedPolycone(
    part, solid, material, colour, px, py, pz, rot, displayMode, solidName=None
):
    from .GDMLObjects import (
        GDMLPolycone,
        GDMLzplane,
        ViewProvider,
        ViewProviderExtension,
    )

    GDMLShared.trace("Create Polycone : ")
    GDMLShared.trace(solid.attrib)
    startphi = GDMLShared.getVal(solid, "startPhi")
    deltaphi = GDMLShared.getVal(solid, "openPhi")
    aunit = getText(solid, "aunit", "rad")
    lunit = getText(solid, "lunit", "mm")
    if solidName is None:
        solidName = getName(solid)
    mypolycone = newPartFeature(part, "GDMLPolycone_" + solidName)
    mypolycone.addExtension("App::GroupExtensionPython")
    numRZ = GDMLShared.getVal(solid, "numRZ")
    # TODO: should add numRZ to GDMLParameterisedPolycone, when we get to it
    GDMLPolycone(
        mypolycone, startphi, deltaphi, aunit, lunit, material, colour
    )
    if FreeCAD.GuiUp:
        ViewProviderExtension(mypolycone.ViewObject)

    # mypolycone.ViewObject.DisplayMode = "Shaded"
    GDMLShared.trace(solid.findall("zplane"))
    for zplane in solid.findall("zplane"):
        GDMLShared.trace(zplane)
        rmin = GDMLShared.getVal(zplane, "rmin", 0)
        rmax = GDMLShared.getVal(zplane, "rmax")
        z = GDMLShared.getVal(zplane, "z")
        myzplane = FreeCAD.ActiveDocument.addObject(
            "App::FeaturePython", "zplane"
        )
        mypolycone.addObject(myzplane)
        # myzplane=mypolycone.newObject('App::FeaturePython', 'zplane')
        GDMLzplane(myzplane, rmin, rmax, z)
        if FreeCAD.GuiUp:
            ViewProvider(myzplane)

    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    mypolycone.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mypolycone.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        setDisplayMode(mypolycone, displayMode)
    return mypolycone


def createParameterisedPolyhedra(
    part, solid, material, colour, px, py, pz, rot, displayMode, solidName=None
):
    from .GDMLObjects import (
        GDMLPolyhedra,
        GDMLzplane,
        ViewProvider,
        ViewProviderExtension,
    )

    GDMLShared.trace("Create Polyhedra : ")
    GDMLShared.trace(solid.attrib)
    startphi = GDMLShared.getVal(solid, "startPhi")
    deltaphi = GDMLShared.getVal(solid, "openPhi")
    numsides = int(GDMLShared.getVal(solid, "numSide"))
    aunit = getText(solid, "aunit", "rad")
    lunit = getText(solid, "lunit", "mm")
    if solidName is None:
        solidName = getName(solid)
    mypolyhedra = newPartFeature(part, "GDMLPolyhedra_" + solidName)
    mypolyhedra.addExtension("App::GroupExtensionPython")
    numRZ = GDMLShared.getVal(solid, "numRZ")
    # TODO: should add numRZ to GDMLParameterisedPolyhedra, when we get to it
    GDMLPolyhedra(
        mypolyhedra,
        startphi,
        deltaphi,
        numsides,
        aunit,
        lunit,
        material,
        colour,
    )
    if FreeCAD.GuiUp:
        ViewProviderExtension(mypolyhedra.ViewObject)

    # mypolyhedra.ViewObject.DisplayMode = "Shaded"
    GDMLShared.trace(solid.findall("zplane"))
    for zplane in solid.findall("zplane"):
        GDMLShared.trace(zplane)
        rmin = GDMLShared.getVal(zplane, "rmin", 0)
        rmax = GDMLShared.getVal(zplane, "rmax")
        z = GDMLShared.getVal(zplane, "z")
        myzplane = FreeCAD.ActiveDocument.addObject(
            "App::FeaturePython", "zplane"
        )
        mypolyhedra.addObject(myzplane)
        # myzplane=mypolyhedra.newObject('App::FeaturePython', 'zplane')
        GDMLzplane(myzplane, rmin, rmax, z)
        if FreeCAD.GuiUp:
            ViewProvider(myzplane)

    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    mypolyhedra.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(mypolyhedra.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        setDisplayMode(mypolyhedra, displayMode)
    return mypolyhedra


def indexVertex(list, name):
    try:
        i = list.index(name)
    except:
        return -1
    return i


from . import importTess_ui


class TessSampleDialog(QtGui.QDialog, importTess_ui.Ui_Dialog):
    maxFaces = 2000
    applyToAll = False
    samplingFraction = 0
    fullSolid = True

    def __init__(self, solidName, numVertexes, numFaces):
        super(TessSampleDialog, self).__init__()
        self.setupUi(self)
        self.solidName = solidName
        self.numVertexes = numVertexes
        self.numFaces = numFaces
        self.fullDisplayRadioButton.toggled.connect(
            self.fullDisplayRadioButtonToggled
        )
        self.initUI()

    def initUI(self):
        self.solidLabel.setText(self.solidName)
        self.vertexesLabel.setText(str(self.numVertexes))
        self.facesLabel.setText(str(self.numFaces))
        self.thresholdSpinBox.setValue(TessSampleDialog.maxFaces)
        self.applyToAllCheckBox.setChecked(TessSampleDialog.applyToAll)
        self.fractionSpinBox.setValue(TessSampleDialog.samplingFraction)
        self.fullDisplayRadioButton.setChecked(TessSampleDialog.fullSolid)
        self.buttonBox.accepted.connect(self.okClicked)  # type: ignore
        self.buttonBox.rejected.connect(self.cancelClicked)  # type: ignore

    def fullDisplayRadioButtonToggled(self):
        self.fullDisplayRadioButton.blockSignals(True)

        if self.fullDisplayRadioButton.isChecked():
            self.fractionSpinBox.setEnabled(False)
            self.fractionsLabel.setEnabled(False)
        else:
            self.fractionSpinBox.setEnabled(True)
            self.fractionsLabel.setEnabled(True)

        self.fullDisplayRadioButton.blockSignals(False)

    def okClicked(self):
        TessSampleDialog.maxFaces = self.thresholdSpinBox.value()
        TessSampleDialog.applyToAll = self.applyToAllCheckBox.isChecked()
        TessSampleDialog.samplingFraction = self.fractionSpinBox.value()
        TessSampleDialog.fullSolid = self.fullDisplayRadioButton.isChecked()
        print("TessellationDialog accepted")
        self.accept()

    def cancelClicked(self):
        print("TessellationDialog rejected")
        self.reject()


def createTessellated(
    part, solid, material, colour, px, py, pz, rot, displayMode
):
    global maxTessellationFaces
    from .GDMLObjects import (
        GDMLSampledTessellated,
        GDMLTriangular,
        GDMLQuadrangular,
        ViewProvider,
        ViewProviderExtension,
    )

    # GDMLShared.setTrace(True)
    GDMLShared.trace("CreateTessellated : ")
    GDMLShared.trace(solid.attrib)
    vertex = []
    faces = []
    lunit = getText(solid, "lunit", "mm")

    # form a set of vertexes. a set has no duplicates,
    # so we don't need to perform the time-costly list.index method
    vertsSet = set()
    for elem in solid.getchildren():
        v1name = elem.get("vertex1")
        v1 = GDMLShared.getDefinedPosition(v1name)
        vertsSet.add(v1)
        v2name = elem.get("vertex2")
        v2 = GDMLShared.getDefinedPosition(v2name)
        vertsSet.add(v2)
        v3name = elem.get("vertex3")
        v3 = GDMLShared.getDefinedPosition(v3name)
        vertsSet.add(v3)
        if elem.tag == "quadrangular":
            v4name = elem.get("vertex4")
            v4 = GDMLShared.getDefinedPosition(v4name)
            vertsSet.add(v3)
    # make a list out of the set
    vertsList = list(vertsSet)

    # create list of indexes for each face
    Dict = {}
    for i, v in enumerate(vertsList):
        vertex.append(v)
        Dict[v] = i

    for elem in solid.getchildren():
        v1name = elem.get("vertex1")
        v1 = GDMLShared.getDefinedPosition(v1name)
        v1pos = Dict[v1]
        v2name = elem.get("vertex2")
        v2 = GDMLShared.getDefinedPosition(v2name)
        v2pos = Dict[v2]
        v3name = elem.get("vertex3")
        v3 = GDMLShared.getDefinedPosition(v3name)
        v3pos = Dict[v3]
        if elem.tag == "triangular":
            faces.append([v1pos, v2pos, v3pos])
        if elem.tag == "quadrangular":
            v4name = elem.get("vertex4")
            v4 = GDMLShared.getDefinedPosition(v4name)
            v4pos = Dict[v4]
            faces.append([v1pos, v2pos, v3pos, v4pos])

    # print(vertNames)
    solidName = getName(solid)
    myTess = newPartFeature(part, "GDMLSampledTessellated_" + solidName)
    print(f"processing tessellation {solidName}")
    if FreeCAD.GuiUp:
        if len(faces) > TessSampleDialog.maxFaces:
            if TessSampleDialog.applyToAll is False:
                dialog = TessSampleDialog(solidName, len(vertex), len(faces))
                dialog.exec_()
            solidFlag = TessSampleDialog.fullSolid
            sampledFraction = TessSampleDialog.samplingFraction
        else:
            solidFlag = True
            sampledFraction = 0
    else:
        solidFlag = True
        sampledFraction = 0

    GDMLSampledTessellated(
        myTess,
        vertex,
        faces,
        lunit,
        material,
        solidFlag,
        sampledFraction,
        colour,
        flag=False,
    )

    # GDMLTessellated(myTess, vertex, faces, False, lunit, material,
    #                 colour)
    GDMLShared.trace("Position : " + str(px) + "," + str(py) + "," + str(pz))
    base = FreeCAD.Vector(px, py, pz)
    myTess.Placement = GDMLShared.processPlacement(base, rot)
    GDMLShared.trace(myTess.Placement.Rotation)
    if FreeCAD.GuiUp:
        # set ViewProvider before setDisplay
        ViewProvider(myTess.ViewObject)
        setDisplayMode(myTess, displayMode)
    return myTess


def parseMultiUnion(
    part, solid, material, colour, px, py, pz, rot, displayMode
):
    global solids
    # GDMLShared.setTrace(True)
    GDMLShared.trace("Multi Union - MultiFuse")
    muName = solid.attrib.get("name")
    GDMLShared.trace("multi Union : " + muName)
    myMUobj = part.newObject("Part::MultiFuse", muName)
    myMUobj.Label = muName
    # for s in solid.findall('multiUnionNode') :
    objList = []
    base = FreeCAD.Vector(px, py, pz)
    placement = GDMLShared.processPlacement(base, rot)
    for s in solid:
        # each solid may change x, y, z, rot
        nx = 0
        ny = 0
        nz = 0
        nrot = None
        if s.tag == "multiUnionNode":
            for t in s:
                if t.tag == "solid":
                    sname = t.get("ref")
                    GDMLShared.trace("solid : " + sname)
                    ssolid = solids.find("*[@name='%s']" % sname)
                if t.tag == "positionref":
                    pname = t.get("ref")
                    nx, ny, nz = GDMLShared.getDefinedPosition(pname)
                    GDMLShared.trace("nx : " + str(nx))
                if t.tag == "position":
                    nx, ny, nz = GDMLShared.getPositionFromAttrib(t)
                    GDMLShared.trace("nx : " + str(nx))
                if t.tag == "rotation":
                    #nrot = GDMLShared.getRotation(t.tag)
                    nrot = GDMLShared.getRotation(t)
                if t.tag == "rotationref":
                    rname = t.get("ref")
                    GDMLShared.trace("rotation ref : " + rname)
                    nrot = GDMLShared.getDefinedRotation(rname)
            if sname is not None:  # Did we find at least one solid
                objList.append(
                    createSolid(
                        part,
                        ssolid,
                        material,
                        colour,
                        nx,
                        ny,
                        nz,
                        nrot,
                        displayMode,
                    )
                )
                objList[-1].Placement.Rotation.Angle = -objList[
                    -1
                ].Placement.Rotation.Angle
    # myMUobj = part.newObject('Part::MultiFuse', muName)
    myMUobj.Shapes = objList
    myMUobj.Placement = placement
    return myMUobj


def parseBoolean(
    part, solid, objType, material, colour, px, py, pz, rot, displayMode
):
    # parent,  solid,  boolean Type,
    from .GDMLObjects import ViewProvider

    global solids
    # GDMLShared.setTrace(True)
    GDMLShared.trace("Parse Boolean : " + str(solid.tag))
    GDMLShared.trace(solid.tag)
    GDMLShared.trace(solid.attrib)
    if solid.tag in ["subtraction", "union", "intersection"]:
        GDMLShared.trace("Boolean : " + solid.tag)
        name1st = GDMLShared.getRef(solid, "first")
        base = solids.find("*[@name='%s']" % name1st)
        GDMLShared.trace("first : " + name1st)
        # parseObject(root, base)
        name2nd = GDMLShared.getRef(solid, "second")
        tool = solids.find("*[@name='%s']" % name2nd)
        GDMLShared.trace("second : " + name2nd)
        x, y, z = GDMLShared.getPosition(solid)
        # rot = GDMLShared.getRotFromRefs(solid)
        rotBool = GDMLShared.getRotation(solid)
        mybool = part.newObject(objType, solid.tag + ":" + getName(solid))
        # mybool = part.newObject('Part::Fuse', solid.tag+':'+getName(solid))
        GDMLShared.trace("Create Base Object")
        mybool.Base = createSolid(
            part, base, material, colour, 0, 0, 0, None, displayMode
        )
        # second solid is placed at position and rotation relative to first
        GDMLShared.trace("Create Tool Object")
        mybool.Tool = createSolid(
            part, tool, material, None, x, y, z, rotBool, displayMode
        )
        # For some unknown reasons,  inversionof angle in processRotation
        # should not be performed for boolean Tool
        mybool.Tool.Placement.Rotation.Angle = (
            -mybool.Tool.Placement.Rotation.Angle
        )
        # Okay deal with position of boolean
        GDMLShared.trace("Boolean Position and rotation")
        GDMLShared.trace(
            "Position : " + str(px) + "," + str(py) + "," + str(pz)
        )
        # base = FreeCAD.Vector(0, 0, 0)
        base = FreeCAD.Vector(px, py, pz)
        mybool.Placement = GDMLShared.processPlacement(base, rot)
        # if FreeCAD.GuiUp :
        #     ViewProvider(mybool.ViewObject)
        return mybool


def createSolid(part, solid, material, colour, px, py, pz, rot, displayMode):
    # parent, solid,  material
    # returns created Object
    GDMLShared.trace("createSolid " + solid.tag)
    GDMLShared.trace("px : " + str(px))
    while switch(solid.tag):
        if case("arb8"):
            return createArb8(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("box"):
            return createBox(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("cone"):
            return createCone(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("elcone"):
            return createElcone(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("ellipsoid"):
            return createEllipsoid(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("eltube"):
            return createEltube(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("hype"):
            return createHype(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("orb"):
            return createOrb(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("para"):
            return createPara(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("paraboloid"):
            return createParaboloid(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("polycone"):
            return createPolycone(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("genericPolycone"):
            return createGenericPolycone(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("polyhedra"):
            return createPolyhedra(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("genericPolyhedra"):
            return createGenericPolyhedra(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("scaledSolid"):
            return createScaledSolid(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("sphere"):
            return createSphere(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("tet"):
            return createTetra(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("torus"):
            return createTorus(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("trap"):
            return createTrap(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("trap_dimensions"):
            return createTrap(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("trd"):
            return createTrd(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("twistedbox"):
            return createTwistedbox(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("twistedtrap"):
            return createTwistedtrap(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("twistedtrd"):
            return createTwistedtrd(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("twistedtubs"):
            return createTwistedtubs(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("tube"):
            return createTube(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("cutTube"):
            return createCutTube(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("tessellated"):
            return createTessellated(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("xtru"):
            return createXtru(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        if case("intersection"):
            return parseBoolean(
                part,
                solid,
                "Part::Common",
                material,
                colour,
                px,
                py,
                pz,
                rot,
                displayMode,
            )

        if case("union"):
            GDMLShared.trace(f"union colour : {colour}")
            return parseBoolean(
                part,
                solid,
                "Part::Fuse",
                material,
                colour,
                px,
                py,
                pz,
                rot,
                displayMode,
            )

        if case("subtraction"):
            return parseBoolean(
                part,
                solid,
                "Part::Cut",
                material,
                colour,
                px,
                py,
                pz,
                rot,
                displayMode,
            )

        if case("multiUnion"):
            return parseMultiUnion(
                part, solid, material, colour, px, py, pz, rot, displayMode
            )

        print("Solid : " + solid.tag + " Not yet supported")
        return


#def getVolSolid(name):
#    GDMLShared.trace("Get Volume Solid")
#    vol = structure.find("/volume[@name='%s']" % name)
#    sr = vol.find("solidref")
#    GDMLShared.trace(sr.attrib)
#    name = GDMLShared.getRef(sr, "name")
#    solid = solids.find("*[@name='%s']" % name)
#    return solid


def addSurfList(doc, part):
    from .GDMLObjects import getSurfsListFromGroup

    # print("Add Surflist : "+part.Name)
    surfLst = getSurfsListFromGroup(doc)
    # print(surfLst)
    if surfLst is not None:
        part.addProperty(
            "App::PropertyEnumeration", "SkinSurface", "GDML", "SkinSurface"
        )
        part.SkinSurface = surfLst
        part.SkinSurface = 0


def parsePhysVol(
    doc, volDict, volAsmFlg, parent, physVol, phylvl, displayMode
):
    # if volAsmFlag == True : Volume
    # if volAsmFlag == False : Assembly
    # physvol is xml entity
    # GDMLShared.setTrace(True)
    GDMLShared.trace("ParsePhyVol : level : " + str(phylvl))
    # Test if any physvol file imports
    filePtr = physVol.find("file")
    if filePtr is not None:
        fname = filePtr.get("name")
        processPhysVolFile(doc, parent, fname)
    volRef = GDMLShared.getRef(physVol, "volumeref")
    GDMLShared.trace("Volume Ref : " + str(volRef))
    if volRef is not None:
        copyNum = physVol.get("copynumber")
        GDMLShared.trace("Copynumber : " + str(copyNum))
        # lhcbvelo has duplicate with no copynumber
        # Test if exists
        namedObj = FreeCAD.ActiveDocument.getObject(volRef)
        PVName = physVol.get("name")
        if namedObj is None:
            part = parent.newObject("App::Part", volRef)
            # print(f'Physvol : {PVName} : Vol:Part {part.Name}')
            volDict[PVName] = part
            addSurfList(doc, part)
            expandVolume(doc, volDict, part, volRef, phylvl, displayMode)

        else:  # Object exists create a Linked Object
            GDMLShared.trace("====> Create Link to : " + volRef)
            part = parent.newObject("App::Link", volRef)
            volDict[PVName] = part
            part.LinkedObject = namedObj
            if part.Name is not volRef:
                ln = len(volRef)
                part.Label = volRef + "_" + part.Name[ln:]
            try:  # try as not working FC 0.18
                part.addProperty(
                    "App::PropertyString", "VolRef", "GDML"
                ).VolRef = volRef
            except:
                pass

            scale = GDMLShared.getScale(physVol)
            # print(scale)
            part.ScaleVector = scale
            # if scale is not FreeCAD.Vector(1., 1., 1.) :
            #   try :  # try as not working FC 0.18
            #      part.addProperty("App::PropertyVector", "GDMLscale", "Link",
            #         "GDML Scale Vector").GDMLscale = scale
            #   except:
            #      print('Scale not supported with FreeCAD 0.18')

        # This would be for Placement of Part need FC 0.19 Fix
        part.Placement = GDMLShared.getPlacement(physVol)

        # Hide FreeCAD Part Material
        if hasattr(part, "Material"):
            part.setEditorMode("Material", 2)
        # Louis gdml file copynumber on non duplicate
        if copyNum is not None:
            try:  # try as not working FC 0.18
                part.addProperty(
                    "App::PropertyInteger", "CopyNumber", "GDML"
                ).CopyNumber = int(copyNum)
            except:
                print("Copynumber not supported in FreeCAD 0.18")

    # GDMLShared.setTrace(False)


def getColour(colRef):
    # print(f'colRef : {colRef}')
    # print(str(extension))
    if extension is not None:
        colxml = extension.find("*[@name='%s']" % colRef)
        # print(str(colxml))
        R = G = B = A = 0.0
        if colxml is not None:
            R = G = B = A = 0.0
            R = colxml.get("R")
            G = colxml.get("G")
            B = colxml.get("B")
            A = colxml.get("A")
    print(f"R : {R} - G : {G} - B : {B} - A : {A}")
    return (float(R), float(G), float(B), 1.0 - float(A))


# ParseVolume name - structure is global
# displayMode 1 normal 2 hide 3 wireframe
def parseVolume(doc, volDict, parent, name, phylvl, displayMode):
    GDMLShared.trace("ParseVolume : " + name)
    expandVolume(doc, volDict, parent, name, phylvl, displayMode)


def processParamvol(vol, parent, paramvol):
    from .GDMLObjects import checkMaterial

    name = vol.get("name")
    sncopies = paramvol.get("ncopies")
    try:
        ncopies = int(sncopies)
    except:
        print("parameterized volume has illegal number of copies")
        return
    print(f"Number of copies={ncopies}")
    refName = GDMLShared.getRef(paramvol, "volumeref")
    refvol = structure.find("volume[@name='%s']" % refName)
    material = GDMLShared.getRef(refvol, "materialref")
    part = parent.newObject("App::Part", "Paramvol_" + refName)
    colour = None
    for aux in refvol.findall("auxiliary"):  # could be more than one auxiliary
        if aux is not None:
            # print('auxiliary')
            aType = aux.get("auxtype")
            aValue = aux.get("auxvalue")
            if aValue is not None:
                if aType == "SensDet":
                    parent.addProperty(
                        "App::PropertyString", "SensDet", "Base", "SensDet"
                    ).SensDet = aValue
                if aType == "Color":
                    # print('auxtype Color')
                    # print(aValue)
                    # print(aValue[1:3])
                    # print(int(aValue[1:3],16))
                    if aValue[0] == "#":  # Hex values
                        # colour = (int(aValue[1:3],16)/256, \
                        #          int(aValue[3:5],16)/256, \
                        #          int(aValue[5:7],16)/256, \
                        #          int(aValue[7:],16)/256)
                        lav = len(aValue)
                        # print(f'Aux col len : {lav}')
                        if lav == 7:
                            try:
                                colour = tuple(
                                    int(aValue[n : n + 2], 16) / 256
                                    for n in range(1, 7, 2)
                                ) + (0)
                            except:
                                print("Invalid Colour definition #RRGGBB")

                        elif lav == 9:
                            try:
                                colour = tuple(
                                    int(aValue[n : n + 2], 16) / 256
                                    for n in range(1, 9, 2)
                                )
                            except:
                                print("Invalid Colour definition #RRGGBBAA")
                        else:
                            print("Invalid Colour definition")
                            # print('Aux colour set'+str(colour))
                    else:
                        colDict = {
                            "Black": (0.0, 0.0, 0.0, 0.0),
                            "Blue": (0.0, 0.0, 1.0, 0.0),
                            "Brown": (0.45, 0.25, 0.0, 0.0),
                            "Cyan": (0.0, 1.0, 1.0, 0.0),
                            "Gray": (0.5, 0.5, 0.5, 0.0),
                            "Grey": (0.5, 0.5, 0.5, 0.0),
                            "Green": (0.0, 1.0, 0.0, 0.0),
                            "Magenta": (1.0, 0.0, 1.0, 0.0),
                            "Red": (1.0, 0.0, 0.0, 0.0),
                            "White": (1.0, 1.0, 1.0, 0.0),
                            "Yellow": (1.0, 1.0, 0.0, 0.0),
                        }
                        colour = colDict.get(aValue, (0.0, 0.0, 0.0, 0.0))
                        # print(colour)
        else:
            print("No auxvalue")
    coloref = GDMLShared.getRef(refvol, "colorref")
    if coloref is not None:
        colour = getColour(coloref)

    psize = paramvol.find("parameterised_position_size")
    if psize is None:
        print(f"Expected parameterised_position_size tag not found in {name}")
        return
    for parameters in psize.findall("parameters"):
        cpyNumber = parameters.get("number")  # note this is a string
        nx, ny, nz = GDMLShared.getPosition(parameters)
        for child in parameters:
            if child.tag.find("_dimensions") != -1:
                solid = child
                break
        print(solid.tag)
        solid_type = solid.tag[:-11]
        solidName = refName + cpyNumber
        if solid_type == "box":
            createBox(
                part, solid, material, colour, nx, ny, nz, None, 1, solidName
            )
        elif solid_type == "tube":
            createParameterisedTube(
                part, solid, material, colour, nx, ny, nz, None, 1, solidName
            )
        elif solid_type == "cone":
            createCone(
                part, solid, material, colour, nx, ny, nz, None, 1, solidName
            )
        elif solid_type == "orb":
            createOrb(
                part, solid, material, colour, nx, ny, nz, None, 1, solidName
            )
        elif solid_type == "sphere":
            createSphere(
                part, solid, material, colour, nx, ny, nz, None, 1, solidName
            )
        elif solid_type == "torus":
            createTorus(
                part, solid, material, colour, nx, ny, nz, None, 1, solidName
            )
        elif solid_type == "hype":
            createHype(
                part, solid, material, colour, nx, ny, nz, None, 1, solidName
            )
        elif solid_type == "para":
            createPara(
                part, solid, material, colour, nx, ny, nz, None, 1, solidName
            )
        elif solid_type == "trd":
            createTrd(
                part, solid, material, colour, nx, ny, nz, None, 1, solidName
            )
        elif solid_type == "trap":
            createTrap(
                part, solid, material, colour, nx, ny, nz, None, 1, solidName
            )
        elif solid_type == "polycone":
            createParameterisedPolycone(
                part, solid, material, colour, nx, ny, nz, None, 1, solidName
            )
        elif solid_type == "polyhedra":
            createParameterisedPolyhedra(
                part, solid, material, colour, nx, ny, nz, None, 1, solidName
            )
        elif solid_type == "ellipsoid":
            createEllipsoid(
                part, solid, solidName, material, colour, nx, ny, nz, None, 1
            )
        else:
            print(
                f"GDML does not provide a parameterized {solid_type}_dimensions"
            )


def processVol(doc, vol, volDict, parent, phylvl, displayMode):
    # GDMLShared.setTrace(True)
    from .GDMLObjects import checkMaterial

    colour = None
    for aux in vol.findall("auxiliary"):  # could be more than one auxiliary
        if aux is not None:
            # print('auxiliary')
            aType = aux.get("auxtype")
            aValue = aux.get("auxvalue")
            if aValue is not None:
                if aType == "SensDet":
                    parent.addProperty(
                        "App::PropertyString", "SensDet", "Base", "SensDet"
                    ).SensDet = aValue
                if aType == "Color":
                    # print('auxtype Color')
                    # print(aValue)
                    # print(aValue[1:3])
                    # print(int(aValue[1:3],16))
                    if aValue[0] == "#":  # Hex values
                        # colour = (int(aValue[1:3],16)/256, \
                        #          int(aValue[3:5],16)/256, \
                        #          int(aValue[5:7],16)/256, \
                        #          int(aValue[7:],16)/256)
                        lav = len(aValue)
                        # print(f'Aux col len : {lav}')
                        if lav == 7:
                            try:
                                colour = tuple(
                                    int(aValue[n : n + 2], 16) / 256
                                    for n in range(1, 7, 2)
                                ) + (0)
                            except:
                                print("Invalid Colour definition #RRGGBB")

                        elif lav == 9:
                            try:
                                colour = tuple(
                                    int(aValue[n : n + 2], 16) / 256
                                    for n in range(1, 9, 2)
                                )
                            except:
                                print("Invalid Colour definition #RRGGBBAA")
                        else:
                            print("Invalid Colour definition")
                            # print('Aux colour set'+str(colour))
                    else:
                        colDict = {
                            "Black": (0.0, 0.0, 0.0, 0.0),
                            "Blue": (0.0, 0.0, 1.0, 0.0),
                            "Brown": (0.45, 0.25, 0.0, 0.0),
                            "Cyan": (0.0, 1.0, 1.0, 0.0),
                            "Gray": (0.5, 0.5, 0.5, 0.0),
                            "Grey": (0.5, 0.5, 0.5, 0.0),
                            "Green": (0.0, 1.0, 0.0, 0.0),
                            "Magenta": (1.0, 0.0, 1.0, 0.0),
                            "Red": (1.0, 0.0, 0.0, 0.0),
                            "White": (1.0, 1.0, 1.0, 0.0),
                            "Yellow": (1.0, 1.0, 0.0, 0.0),
                        }
                        colour = colDict.get(aValue, (0.0, 0.0, 0.0, 0.0))
                        # print(colour)
        else:
            print("No auxvalue")
    coloref = GDMLShared.getRef(vol, "colorref")
    if coloref is not None:
        colour = getColour(coloref)
    solidref = GDMLShared.getRef(vol, "solidref")
    print(f"solidref : {solidref}")
    name = vol.get("name")
    if solidref is not None:
        solid = solids.find("*[@name='%s']" % solidref)
        if solid is not None:
            GDMLShared.trace(solid.tag)
            # Material is the materialref value
            # need to add default
            material = GDMLShared.getRef(vol, "materialref")
            if material is not None:
                if checkMaterial(material) is True:
                    createSolid(
                        parent,
                        solid,
                        material,
                        colour,
                        0,
                        0,
                        0,
                        None,
                        displayMode,
                    )
                else:
                    print(
                        "ERROR - Material : "
                        + material
                        + " Not defined for solid : "
                        + str(solid)
                        + " Volume : "
                        + name
                    )
                    return None
            else:
                print(
                    "ERROR - Materialref Not defined for solid : "
                    + str(solid)
                    + " Volume : "
                    + name
                )
                return None
        else:
            print("ERROR - Solid  : " + solidref + " Not defined")
            return None
    else:
        print("ERROR - solidref Not defined in Volume : " + name)
        return None
    # Volume may or maynot contain physvol's
    displayMode = 1
    part = None
    for pv in vol.findall("physvol"):
        # Need to clean up use of phylvl flag
        # create solids at pos & rot in physvols
        # if phylvl < 1 :
        if phylvl < 0:
            # if phylvl >= 0 :
            #   phylvl += 1
            # If negative always parse otherwise increase level
            part = parsePhysVol(
                doc, volDict, True, parent, pv, phylvl, displayMode
            )

        else:  # Just Add to structure
            volRef = GDMLShared.getRef(pv, "volumeref")
            print("volRef : " + str(volRef))
            nx, ny, nz = GDMLShared.getPosition(pv)
            nrot = GDMLShared.getRotation(pv)
            cpyNum = pv.get("copynumber")
            # print('copyNumber : '+str(cpyNum))
            # Is volRef already defined
            linkObj = FreeCAD.ActiveDocument.getObject(volRef)
            if linkObj is not None:
                # already defined so link
                # print('Already defined')
                try:
                    part = parent.newObject("App::Link", volRef)
                    part.LinkedObject = linkObj
                    part.Label = "Link_" + part.Name
                except:
                    print(volRef + " : volref not supported with FreeCAD 0.18")
            else:
                # Not already defined so create
                # print('Is new : '+volRef)
                part = parent.newObject("App::Part", volRef)
                addSurfList(doc, part)
                part.Label = "NOT_Expanded_" + part.Name
            part.addProperty(
                "App::PropertyString", "VolRef", "GDML", "volref name"
            ).VolRef = volRef
            if cpyNum is not None:
                part.addProperty(
                    "App::PropertyInteger", "CopyNumber", "GDML", "copynumber"
                ).CopyNumber = int(cpyNum)
            base = FreeCAD.Vector(nx, ny, nz)
            part.Placement = GDMLShared.processPlacement(base, nrot)
            if hasattr(part, "Material"):
                part.setEditorMode("Material", 2)
    #
    # check for parameterized volumes
    #
    paramvol = vol.find("paramvol")
    doc = FreeCAD.ActiveDocument
    if doc is not None:
        parentpart = doc.getObject(name)
        print(f"name: {name} parentpart = {parentpart}")
        print(f"paramvol = {paramvol}")
        if (parentpart is not None) and (paramvol is not None):
            print(f"volume {name} contains a parameterized volume")
            processParamvol(vol, parentpart, paramvol)


def expandVolume(doc, volDict, parent, name, phylvl, displayMode):
    import FreeCAD as App

    # also used in ScanCommand
    # GDMLShared.setTrace(True)
    GDMLShared.trace("expandVolume : " + name)
    vol = structure.find("volume[@name='%s']" % name)
    if vol is not None:  # If not volume test for assembly
        processVol(doc, vol, volDict, parent, phylvl, displayMode)

    else:
        asm = structure.find("assembly[@name='%s']" % name)
        if asm is not None:
            print("Assembly : " + name)
            for pv in asm.findall("physvol"):
                # obj = parent.newObject("App::Part", name)
                parsePhysVol(
                    doc, volDict, False, parent, pv, phylvl, displayMode
                )
        else:
            print(name + " is Not a defined Volume or Assembly")


def getItem(element, attribute):
    # returns None if not found
    return element.get(attribute)


def processIsotopes(isotopesGrp, mats_xml):
    from .GDMLObjects import GDMLisotope, ViewProvider

    for isotope in mats_xml.findall("isotope"):
        N = int(isotope.get("N"))
        Z = int(float(isotope.get("Z")))  # annotated.gdml file has Z=8.0
        name = isotope.get("name")
        isObj = newGroupPython(isotopesGrp, name)
        GDMLisotope(isObj, name, N, Z)
        atom = isotope.find("atom")
        if atom is not None:
            unit = atom.get("unit")
            if unit is not None:
                isObj.addProperty(
                    "App::PropertyString", "unit", "Unit"
                ).unit = unit
            type = atom.get("type")
            if type is not None:
                isObj.addProperty(
                    "App::PropertyString", "type", "Type"
                ).type = type
            if atom.get("value") is not None:
                value = GDMLShared.getVal(atom, "value")
                isObj.addProperty(
                    "App::PropertyFloat", "value", "Value"
                ).value = value


def processElements(elementsGrp, mats_xml):
    from .GDMLObjects import GDMLelement, GDMLfraction, GDMLcomposite

    for element in mats_xml.findall("element"):
        name = element.get("name")
        # print('element : '+name)
        elementObj = newGroupPython(elementsGrp, name)
        Z = element.get("Z")
        if Z is not None:
            elementObj.addProperty("App::PropertyInteger", "Z", name).Z = int(
                float(Z)
            )
        N = element.get("N")
        if N is not None:
            elementObj.addProperty("App::PropertyInteger", "N", name).N = int(
                N
            )

        formula = element.get("formula")
        if formula is not None:
            elementObj.addProperty(
                "App::PropertyString", "formula", name
            ).formula = formula

        atom = element.find("atom")
        if atom is not None:
            unit = atom.get("unit")
            if unit is not None:
                elementObj.addProperty(
                    "App::PropertyString", "atom_unit", name
                ).atom_unit = unit
            a_value = GDMLShared.getVal(atom, "value")
            if a_value is not None:
                elementObj.addProperty(
                    "App::PropertyFloat", "atom_value", name
                ).atom_value = a_value

        GDMLelement(elementObj, name)
        if len(element.findall("fraction")) > 0:
            for fraction in element.findall("fraction"):
                ref = fraction.get("ref")
                # print(f'ref {ref}')
                # n = float(fraction.get('n'))
                n = GDMLShared.getVal(fraction, "n")
                # print(f'n {n}')
                fractObj = newGroupPython(elementObj, ref)
                GDMLfraction(fractObj, ref, n)
                fractObj.Label = ref + " : " + "{0:0.3f}".format(n)
        elif len(element.findall("composite")) > 0:
            for composite in element.findall("composite"):
                ref = composite.get("ref")
                n = int(composite.get("n"))
                compositeObj = newGroupPython(elementObj, ref)
                GDMLcomposite(compositeObj, ref, n)
                compositeObj.Label = ref + " : " + str(n)


def processMaterials(materialGrp, mats_xml, subGrp=None):
    from .GDMLObjects import (
        GDMLmaterial,
        GDMLfraction,
        GDMLcomposite,
        MaterialsList,
    )

    # print(f'Process Materials : {materialGrp.Name} SubGrp{subGrp}')
    print(f"Process Materials : {materialGrp.Name}")
    for material in mats_xml.findall("material"):
        name = material.get("name")
        # print(name)
        if name is None:
            print("Missing Name")
        else:
            MaterialsList.append(name)
            mGrp = materialGrp
            aux = material.find("auxiliary")
            # print(f'Aux {aux}')
            if aux is not None:
                auxType = aux.get("auxtype")
                # print(f'Aux Type {auxType}')
                if auxType == "Material-type":
                    matType = aux.get("auxvalue")
                    # print(matType)
                    # print(materialGrp.Group)
                    mGrp = materialGrp.Group[subGrp.index(matType)]

            materialObj = newGroupPython(mGrp, name)
            GDMLmaterial(materialObj, name)
            formula = material.get("formula")
            if formula is not None:
                materialObj.addProperty(
                    "App::PropertyString", "formula", name
                ).formula = formula
            D = material.find("D")
            if D is not None:
                Dunit = getItem(D, "unit")
                # print(Dunit)
                if Dunit is not None:
                    materialObj.addProperty(
                        "App::PropertyString", "Dunit", "GDMLmaterial", "Dunit"
                    ).Dunit = Dunit
                Dvalue = GDMLShared.getVal(D, "value")
                if Dvalue is not None:
                    materialObj.addProperty(
                        "App::PropertyFloat", "Dvalue", "GDMLmaterial", "value"
                    ).Dvalue = Dvalue

            Z = material.get("Z")
            if Z is not None:
                materialObj.addProperty("App::PropertyString", "Z", name).Z = Z
            atom = material.find("atom")
            if atom is not None:
                # print("Found atom in : "+name)
                aUnit = atom.get("unit")
                if aUnit is not None:
                    materialObj.addProperty(
                        "App::PropertyString", "atom_unit", name
                    ).atom_unit = aUnit
                aValue = GDMLShared.getVal(atom, "value")
                if aValue is not None:
                    materialObj.addProperty(
                        "App::PropertyFloat", "atom_value", name
                    ).atom_value = aValue

            T = material.find("T")
            if T is not None:
                Tunit = T.get("unit")
                if Tunit is None:  # Default Kelvin
                    Tunit = "K"
                materialObj.addProperty(
                    "App::PropertyString", "Tunit", "GDMLmaterial", "T ZZZUnit"
                ).Tunit = Tunit
            MEE = material.find("MEE")
            if MEE is not None:
                Munit = MEE.get("unit")
                Mvalue = GDMLShared.getVal(MEE, "value")
                materialObj.addProperty(
                    "App::PropertyString",
                    "MEEunit",
                    "GDMLmaterial",
                    "MEE unit",
                ).MEEunit = Munit
                materialObj.addProperty(
                    "App::PropertyFloat",
                    "MEEvalue",
                    "GDMLmaterial",
                    "MEE value",
                ).MEEvalue = Mvalue
            for fraction in material.findall("fraction"):
                n = GDMLShared.getVal(fraction, "n")
                # print(n)
                ref = fraction.get("ref")
                # print('fraction : '+ref)
                fractionObj = newGroupPython(materialObj, ref)
                # print('fractionObj Name : '+fractionObj.Name)
                GDMLfraction(fractionObj, ref, n)
                # problems with changing labels if more than one
                #
                fractionObj.Label = ref + " : " + "{0:0.3f}".format(n)
                # print('Fract Label : ' +fractionObj.Label)

            for composite in material.findall("composite"):
                # print('Composite')
                n = int(composite.get("n"))
                # print('n = '+str(n))
                ref = composite.get("ref")
                # print('ref : '+ref)
                compObj = newGroupPython(materialObj, ref)
                GDMLcomposite(compObj, "comp", n, ref)
                # problems with changing labels if more than one
                #
                # print('Comp Label : ' +compObj.Label)
                compObj.Label = ref + " : " + str(n)
                # print('Comp Label : ' +compObj.Label)

            for prop in material.findall("property"):
                name = prop.get("name")
                print(f"Property Name {name}")
                ref = prop.get("ref")
                print(f"Property Ref {ref}")
                materialObj.addProperty(
                    "App::PropertyString", name, "Properties", "Property Name"
                )
                setattr(materialObj, name, ref)

    GDMLShared.trace("Materials List :")
    GDMLShared.trace(MaterialsList)


def setupEtree(filename):
    # modifs
    # before from lxml import etree
    print("Parse : " + filename)
    try:
        from lxml import etree

        FreeCAD.Console.PrintMessage("running with lxml.etree \n")
        parser = etree.XMLParser(resolve_entities=True)
        root = etree.parse(filename, parser=parser)
        # print('error log')
        # print(parser.error_log)

    except ImportError:
        try:
            import xml.etree.ElementTree as etree

            FreeCAD.Console.PrintMessage(
                "running with etree.ElementTree (import limitations)\n"
            )
            FreeCAD.Console.PrintMessage(
                " for full import add lxml library \n"
            )
            tree = etree.parse(filename)
            FreeCAD.Console.PrintMessage(tree)
            FreeCAD.Console.PrintMessage("\n")
            root = tree.getroot()

        except ImportError:
            print("pb xml lib not found")
            sys.exit()
    # end modifs
    return etree, root

def findPart(doc, name):
    #for obj in doc.Objects:
    #    if obj.TypeId == "App::Part" and obj.Name == name:
    #        return obj
    return doc.addObject("App::Part", name)


def processXMLVolumes(doc, root):
    from .GDMLObjects import checkMaterial
    solids_xml = root.find("solids")
    if solids_xml is not None:
        for vol in root.findall("volume"):
            vName = vol.get("name")
            if vName is not None:
                volObj = findPart(doc, vName)
            print(f"Vol name {vName}")
            material = GDMLShared.getRef(vol, "materialref")
            print(f"Material {material}")
            solidref = GDMLShared.getRef(vol, "solidref")
            print(f"Solid  {solidref}")
            solid = solids_xml.find("*[@name='%s']" % solidref)
            if checkMaterial(material) is True:
                createSolid( volObj, solid, material, None,
                        0, 0, 0, None, None)
            else:
                print(f"Material {material} not defined")
    doc.recompute()

def processXML(doc, filename):
    print("process XML : " + filename)
    etree, root = setupEtree(filename)
    # etree.ElementTree(root).write("/tmp/test2", 'utf-8', True)
    processMaterialsDocSet(doc, root)
    processXMLVolumes(doc, root)


def processPhysVolFile(doc, volDict, parent, fname):
    global pathName
    print("Process physvol file import")
    print(pathName)
    filename = os.path.join(pathName, fname)
    print("Full Path : " + filename)
    etree, root = setupEtree(filename)
    # etree.ElementTree(root).write("/tmp/test2", 'utf-8', True)
    processMaterialsDocSet(doc, root)
    print("Now process Volume")
    define = root.find("define")
    # print(str(define))
    GDMLShared.setDefine(define)
    if define is not None:
        processDefines(root, doc)
    global solids
    solids = root.find("solids")
    # print(str(solids))
    structure = root.find("structure")
    if structure is None:
        vol = root.find("volume")
    else:
        vol = structure.find("volume")
    # print(str(vol))
    if vol is not None:
        vName = vol.get("name")
        if vName is not None:
            part = parent.newObject("App::Part", vName)
            if hasattr(part, "Material"):
                part.setEditorMode("Material", 2)
            # expandVolume(None,vName,-1,1)
            processVol(doc, vol, volDict, part, -1, 1)

    processSurfaces(doc, volDict, structure)


def setSkinSurface(doc, vol, surface):
    print("set SkinSurface : {vol} : {surface}")
    volObj = doc.getObject(vol)
    volObj.SkinSurface = surface


def processSurfaces(doc, volDict, structure):
    from .GDMLObjects import GDMLbordersurface

    # find all ???
    print("Process Surfaces")
    print("skinsurface")
    skinsurface = structure.find("skinsurface")
    if skinsurface is not None:
        surface = skinsurface.get("surfaceproperty")
        volRef = GDMLShared.getRef(skinsurface, "volumeref")
        print(f"Vol {volRef} surface {surface}")
        setSkinSurface(doc, volRef, surface)

    print("bordersurface")
    # print(f'volDict {volDict}')
    for borderSurf in structure.findall("bordersurface"):
        if borderSurf is not None:
            name = borderSurf.get("name")
            surface = borderSurf.get("surfaceproperty")
            volLst = []
            for i, pv in enumerate(borderSurf.findall("physvolref")):
                if pv is not None:
                    pvRef = pv.get("ref")
                    # print(f"{i} : {pvRef}")
                    volRef = volDict[pvRef]
                    print(f"Vol : {volRef.Label}")
                    if volRef is not None:
                        volLst.append(volRef)
                    else:
                        print(f"Volume {pvRef} not found")
            if len(volLst) == 2:
                obj = doc.addObject("App::FeaturePython", name)
                GDMLbordersurface(
                    obj, name, surface, volLst[0], volLst[1], False
                )
            else:
                print(f"Invalid bordersurface {name}")


def processGEANT4(doc, filename):
    print("process GEANT4 Materials : " + filename)
    etree, root = setupEtree(filename)
    # etree.ElementTree(root).write("/tmp/test2", 'utf-8', True)
    materials = doc.getObject("Materials")
    if materials is None:
        materials = doc.addObject(
            "App::DocumentObjectGroupPython", "Materials"
        )
    # Avoid duplicate Geant4 group - Palo import of GDML
    geant4Grp = doc.getObject("Geant4")
    if geant4Grp is None:
        geant4Grp = newGroupPython(materials, "Geant4")
        processMaterialsG4(geant4Grp, root)


def processMaterialsDocSet(doc, root):
    print("Process Materials DocSet")
    define_xml = root.find("define")
    print(f"define xml {define_xml}")
    mats_xml = root.find("materials")
    solids_xml = root.find("solids")
    struct_xml = root.find("structure")
    if mats_xml is not None:
        try:
            isotopesGrp = FreeCAD.ActiveDocument.Isotopes
        except:
            isotopesGrp = doc.addObject(
                "App::DocumentObjectGroupPython", "Isotopes"
            )
        processIsotopes(isotopesGrp, mats_xml)
        try:
            elementsGrp = FreeCAD.ActiveDocument.Elements
        except:
            elementsGrp = doc.addObject(
                "App::DocumentObjectGroupPython", "Elements"
            )
        processElements(elementsGrp, mats_xml)
        try:
            materialsGrp = FreeCAD.ActiveDocument.Materials
        except:
            materialsGrp = doc.addObject(
                "App::DocumentObjectGroupPython", "Materials"
            )
        processMaterials(materialsGrp, mats_xml)
    # Process Opticals
    try:
        opticalsGrp = FreeCAD.ActiveDocument.Opticals
    except:
        opticalsGrp = doc.addObject(
            "App::DocumentObjectGroupPython", "Opticals"
        )
    processOpticals(doc, opticalsGrp, define_xml, solids_xml, struct_xml)


def processMatrixSpreadsheet(name, spreadsheet, coldim, values):
    ncols = int(coldim)
    valueTuples = values.split()
    size = len(valueTuples)
    if size % ncols != 0:
        print(f"***Matrix {name} is not filled correctly")
        print(f"number of entries is not multiple of {ncols}")
        return

    if size == coldim or coldim == 1:  # one dimensioma; "matrix"
        for i in range(0, size):
            spreadsheet.set("A" + str(i), valueTuples[i])
        return

    nrows = int(size / ncols)
    for row in range(0, nrows):
        for col in range(ncols):
            cell = chr(ord("A") + col) + str(row + 1)
            print(f"cell {cell}")
            spreadsheet.set(cell, valueTuples[ncols * row + col])
    return


def processOpticals(doc, opticalsGrp, define_xml, solids_xml, struct_xml):
    from .GDMLObjects import GDMLmatrix, GDMLopticalsurface, GDMLskinsurface

    print("Process - Opticals: matrix_spreadsheet")
    print(f"define xml {define_xml}")
    if define_xml is not None:
        matrixGrp = doc.getObject("Matrix")
        if matrixGrp is None:
            matrixGrp = newGroupPython(opticalsGrp, "Matrix")
        print("Find all Matrix")
        for matrix in define_xml.findall("matrix"):
            name = matrix.get("name")
            print(name)
            if name is not None:
                coldim = matrix.get("coldim")
                values = matrix.get("values")
                nvalues = len(values.split())
                if int(coldim) > 1 or nvalues > 1:
                    spreadsheet = matrixGrp.newObject(
                        "Spreadsheet::Sheet", name
                    )
                    processMatrixSpreadsheet(name, spreadsheet, coldim, values)
                else:
                    matrixObj = newGroupPython(matrixGrp, name)
                    GDMLmatrix(matrixObj, name, int(coldim), values)

    if solids_xml is not None:
        surfaceGrp = doc.getObject("Surfaces")
        if surfaceGrp is None:
            surfaceGrp = newGroupPython(opticalsGrp, "Surfaces")
        for opSurface in solids_xml.findall("opticalsurface"):
            name = opSurface.get("name")
            if name is not None:
                surfaceObj = newGroupPython(surfaceGrp, name)
                model = opSurface.get("model")
                finish = opSurface.get("finish")
                print(f"scanned finish : {finish}")
                type = opSurface.get("type")
                value = opSurface.get("value")
                GDMLopticalsurface(
                    surfaceObj, name, model, finish, type, float(value)
                )
                for prop in opSurface.findall("property"):
                    name = prop.get("name")
                    print(f"Property Name {name}")
                    ref = prop.get("ref")
                    print(f"Property Ref {ref}")
                    surfaceObj.addProperty(
                        "App::PropertyString",
                        name,
                        "Properties",
                        "Property Name",
                    )
                    setattr(surfaceObj, name, ref)

    # Do not set in Doc, export from Part with SkinSurf
    # skinGrp = newGroupPython(opticalsGrp, "SkinSurfaces")
    # for skinSurface in struct_xml.findall('skinsurface'):
    #    name = skinSurface.get('name')
    #    if name is not None:
    #       skinSurfaceObj = newGroupPython(skinGrp, name)
    #    prop = skinSurface.get('surfaceproperty')
    #    GDMLskinsurface(skinSurfaceObj, name, prop)


def processNewG4(materialsGrp, mats_xml):
    print("process new G4")
    matTypes = ["NIST", "Element", "HEP", "Space", "BioChemical"]
    for t in matTypes:
        newGroupPython(materialsGrp, t)
    processMaterials(materialsGrp, mats_xml, matTypes)


def processMaterialsG4(G4rp, root):
    mats_xml = root.find("materials")
    if mats_xml is not None:
        isotopesGrp = newGroupPython(G4rp, "G4Isotopes")
        processIsotopes(isotopesGrp, mats_xml)
        elementsGrp = newGroupPython(G4rp, "G4Elements")
        processElements(elementsGrp, mats_xml)
        materialsGrp = newGroupPython(G4rp, "G4Materials")
        materialsGrp.addProperty(
            "App::PropertyFloat", "version", "Base"
        ).version = 1.0
        processNewG4(materialsGrp, mats_xml)


def processDefines(root, doc):
    GDMLShared.trace("Call set Define")
    GDMLShared.setDefine(root.find("define"))
    GDMLShared.processConstants(doc)
    GDMLShared.processVariables(doc)
    GDMLShared.processQuantities(doc)
    GDMLShared.processPositions(doc)
    GDMLShared.processExpression(doc)


def findWorldVol():
    for obj in doc.Objects:
        if obj.TypeId == "App::Part":
            print(f"World Volume {obj.Name}")
            return obj
    print("World Volume Not Found")
    return None


def processGDML(doc, flag, filename, prompt, initFlg):
    # flag == True open, flag == False import
    from FreeCAD import Base
    from . import preProcessLoops

    # Process GDML
    volDict = {}

    import time
    from . import GDMLShared

    # GDMLShared.setTrace(True)

    phylvl = -1  # Set default
    if FreeCAD.GuiUp:
        from . import GDMLCommands

        if prompt:
            from .GDMLQtDialogs import importPrompt

            dialog = importPrompt()
            dialog.exec_()
            # FreeCADGui.Control.showDialog(dialog)
            # if dialog.retStatus == 1 :
            #   print('Import')
            #   phylvl = -1

            if dialog.retStatus == 2:
                print("Scan Vol")
                phylvl = 0

            params = FreeCAD.ParamGet(
                "User parameter:BaseApp/Preferences/Mod/GDML"
            )
            # GDMLShared.setTrace(printverbose = params.GetBool('printVerbose',False))
    else:
        # For Non Gui default Trace to on
        GDMLShared.setTrace(True)

    print("Print Verbose : " + str(GDMLShared.getTrace()))

    FreeCAD.Console.PrintMessage("Import GDML file : " + filename + "\n")
    FreeCAD.Console.PrintMessage("ImportGDML Version 1.9a\n")
    startTime = time.perf_counter()

    global pathName
    pathName = os.path.dirname(os.path.normpath(filename))
    FilesEntity = False

    global setup, define, materials, solids, structure, extension, groupMaterials

    # reset parameters for tessellation dialog:
    TessSampleDialog.maxFaces = 2000
    TessSampleDialog.applyToAll = False
    TessSampleDialog.samplingFraction = 0
    TessSampleDialog.fullSolid = True

    # Add files object so user can change to organise files
    #  from GDMLObjects import GDMLFiles, ViewProvider
    #  myfiles = doc.addObject("App::FeaturePython","Export_Files")
    # myfiles = doc.addObject("App::DocumentObjectGroupPython","Export_Files")
    # GDMLFiles(myfiles,FilesEntity,sectionDict)

    # Reserve place for Colour Map at start of Document
    # FreeCAD.ActiveDocument.addObject("App::FeaturePython","ColourMap")

    etree, root = setupEtree(filename)
    setup = root.find("setup")
    extension = root.find("extension")
    define = root.find("define")
    if define is not None:
        processDefines(root, doc)
        GDMLShared.trace(setup.attrib)
        preProcessLoops.preprocessLoops(root)

    from .GDMLMaterials import getGroupedMaterials
    from .GDMLMaterials import newGetGroupedMaterials

    processMaterialsDocSet(doc, root)
    processGEANT4(doc, joinDir("Resources/Geant4Materials.xml"))
    groupMaterials = newGetGroupedMaterials()

    solids = root.find("solids")
    structure = root.find("structure")
    world = GDMLShared.getRef(setup, "world")
    if flag is True:
        part = doc.addObject("App::Part", world)
    else:
        part = findWorldVol()
        if part is None:
            part = doc.addObject("App::Part", world)
    if hasattr(part, "Material"):
        part.setEditorMode("Material", 2)
    parseVolume(doc, volDict, part, world, phylvl, 3)
    processSurfaces(doc, volDict, structure)
    # If only single volume reset Display Mode
    if len(part.OutList) == 2 and initFlg is False:
        worldGDMLobj = part.OutList[1]
        worldGDMLobj.ViewObject.DisplayMode = "Shaded"
    FreeCAD.ActiveDocument.recompute()
    if FreeCAD.GuiUp:
        FreeCADGui.SendMsgToActiveView("ViewFit")
    FreeCAD.Console.PrintMessage("End processing GDML file\n")
    endTime = time.perf_counter()
    # print(f'time : {endTime - startTime:0.4f} seconds')
    FreeCAD.Console.PrintMessage(
        f"time : {endTime - startTime:0.4f} seconds\n"
    )
