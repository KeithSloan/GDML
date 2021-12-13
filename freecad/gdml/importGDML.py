# -*- coding: utf-8 -*-
# Mon Dec  6 08:49:41 AM PST 2021
#**************************************************************************
#*                                                                        *
#*   Copyright (c) 2017 Keith Sloan <keith@sloan-home.co.uk>              *
#*             (c) Dam Lambert 2020                                       *
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
#*                                                                        *
#**************************************************************************
__title__="FreeCAD - GDML importer"
__author__ = "Keith Sloan <keith@sloan-home.co.uk>"
__url__ = ["https://github.com/KeithSloan/FreeCAD_GDML"]

import FreeCAD 
import os, io, sys, re
import Part, Draft

def joinDir(path) :
    import os
    __dirname__ = os.path.dirname(__file__)
    return(os.path.join(__dirname__,path))

from math import *
from . import GDMLShared

##########################
# Globals Dictionaries    #
##########################
#global setup, define, materials, solids, structure, extension
#globals constDict, filesDict 

if FreeCAD.GuiUp:
   import PartGui, FreeCADGui
   gui = True
else:
   print("FreeCAD Gui not present.")
   gui = False

import Part

if open.__module__ == '__builtin__':
    pythonopen = open # to distinguish python built-in open function from the one declared here


#try:
#    _encoding = QtGui.QApplication.UnicodeUTF8
#    def translate(context, text):
#        "convenience function for Qt translator"
#        from PySide import QtGui
#        return QtGui.QApplication.translate(context, text, None, _encoding)
#except AttributeError:
#    def translate(context, text):
#        "convenience function for Qt translator"
#        from PySide import QtGui
#        return QtGui.QApplication.translate(context, text, None)



def open(filename):
    "called when freecad opens a file."
    global doc
    print('Open : '+filename)
    docName  = os.path.splitext(os.path.basename(filename)) [0]
    print('path : '+filename) 
    if filename.lower().endswith('.gdml') :
        #import cProfile, pstats
        #profiler = cProfile.Profile()
        #profiler.enable()
        doc = FreeCAD.newDocument(docName)
        processGDML(doc,filename,True,False)
        #profiler.disable()
        #stats = pstats.Stats(profiler).sort_stats('cumtime')
        #stats.print_stats()

    elif filename.lower().endswith('.xml'):
       try :
           doc = FreeCAD.ActiveDocument()
           print('Active Doc')

       except :
           print('New Doc')
           doc = FreeCAD.newDocument(docName)

       processXML(doc,filename)

    return doc

def insert(filename,docname):
    "called when freecad imports a file"
    print('Insert filename : '+filename+' docname : '+docname)
    global doc
    groupname = os.path.splitext(os.path.basename(filename))[0]
    try:
        doc=FreeCAD.getDocument(docname)
    except NameError:
        doc=FreeCAD.newDocument(docname)
    if filename.lower().endswith('.gdml'):
        processGDML(doc,filename,True,False)

    elif filename.lower().endswith('.xml'):
        processXML(doc,filename)

class switch(object):
    value = None
    def __new__(class_, value):
        class_.value = value
        return True

def case(*args):
    return any((arg == switch.value for arg in args))

def translate(shape,base) :
    # Input Object and displacement vector - return a transformed shape
    myPlacement = FreeCAD.Placement()
    myPlacement.move(base)
    mat1 = myPlacement.toMatrix()
    #print(mat1)
    mat2 = shape.Matrix
    mat  = mat1.multiply(mat2)
    #print(mat)
    retShape = shape.copy()
    retShape.transformShape(mat, True)
    return retShape

def checkConstant(vval):
    GDMLShared.trace(vval)

def getName(ptr) :
    return (ptr.attrib.get('name'))

def getText(ptr,var,default) :
    #print("Get Texti : "+str(ptr.attrib.get(var))+" : "+str(var))
    if var in ptr.attrib :
       return (ptr.attrib.get(var))
    else :
       return default

def setDisplayMode(obj,mode):
    GDMLShared.trace("setDisplayMode : "+str(mode))
    if mode == 2 :
       obj.ViewObject.DisplayMode = 'Hide'

    if mode == 3 :
       obj.ViewObject.DisplayMode = 'Wireframe'

def createArb8(part,solid,material,colour,px,py,pz,rot,displayMode) :
    # parent, sold
    from .GDMLObjects import GDMLArb8, ViewProvider
    #GDMLShared.setTrace(True)
    GDMLShared.trace("CreateArb8 : ")
    #GDMLShared.trace("material : "+material)
    GDMLShared.trace(solid.attrib)

    myArb8=part.newObject("Part::FeaturePython","GDMLArb8:"+getName(solid))
    v1x = GDMLShared.getVal(solid,'v1x')
    v1y = GDMLShared.getVal(solid,'v1y')
    v2x = GDMLShared.getVal(solid,'v2x')
    v2y = GDMLShared.getVal(solid,'v2y')
    v3x = GDMLShared.getVal(solid,'v3x')
    v3y = GDMLShared.getVal(solid,'v3y')
    v4x = GDMLShared.getVal(solid,'v4x')
    v4y = GDMLShared.getVal(solid,'v4y')
    v5x = GDMLShared.getVal(solid,'v5x')
    v5y = GDMLShared.getVal(solid,'v5y')
    v6x = GDMLShared.getVal(solid,'v6x')
    v6y = GDMLShared.getVal(solid,'v6y')
    v7x = GDMLShared.getVal(solid,'v7x')
    v7y = GDMLShared.getVal(solid,'v7y')
    v8x = GDMLShared.getVal(solid,'v8x')
    v8y = GDMLShared.getVal(solid,'v8y')
    dz = GDMLShared.getVal(solid,'dz')
    lunit = getText(solid,'lunit',"mm")

    GDMLArb8(myArb8,v1x, v1y, v2x, v2y, v3x, v3y, v4x, v4y,  \
                v5x, v5y, v6x, v6y, v7x, v7y, v8x, v8y, dz, \
                lunit, material, colour)
    GDMLShared.trace("Logical Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    myArb8.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(myArb8.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(myArb8.ViewObject)
       setDisplayMode(myArb8,displayMode)
    return myArb8

def createBox(part,solid,material,colour,px,py,pz,rot,displayMode) :
    # parent, sold
    from .GDMLObjects import GDMLBox, ViewProvider
    #GDMLShared.setTrace(True)
    GDMLShared.trace("CreateBox : ")
    #GDMLShared.trace("material : "+material)
    GDMLShared.trace(solid.attrib)

    # modifs lambda (otherwise each time we open the gdml file, 
    # the part name will have one more GDMLBox added
    # No - need to remove leading GDMLBox on export
    mycube=part.newObject("Part::FeaturePython","GDMLBox:"+getName(solid))
    #mycube=part.newObject("Part::FeaturePython",getName(solid))
    x = GDMLShared.getVal(solid,'x')
    y = GDMLShared.getVal(solid,'y')
    z = GDMLShared.getVal(solid,'z')
    lunit = getText(solid,'lunit',"mm")
    #print(f'Cube colour : {colour}')
    GDMLBox(mycube,x,y,z,lunit,material,colour)
    GDMLShared.trace("Logical Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mycube.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mycube.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mycube.ViewObject)
       setDisplayMode(mycube,displayMode)
    #myCube.Shape = translate(mycube.Shape,base)
    return mycube

def createCone(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLCone, ViewProvider
    GDMLShared.trace("CreateCone : ")
    GDMLShared.trace(solid.attrib)
    rmin1 = GDMLShared.getVal(solid,'rmin1',0)
    rmax1 = GDMLShared.getVal(solid,'rmax1')
    rmin2 = GDMLShared.getVal(solid,'rmin2',0)
    rmax2 = GDMLShared.getVal(solid,'rmax2')
    z = GDMLShared.getVal(solid,'z')
    startphi = GDMLShared.getVal(solid,'startphi')
    deltaphi = GDMLShared.getVal(solid,'deltaphi')
    aunit = getText(solid,'aunit','rad')
    lunit = getText(solid,'lunit',"mm")
    mycone=part.newObject("Part::FeaturePython","GDMLCone:"+getName(solid))
    GDMLCone(mycone,rmin1,rmax1,rmin2,rmax2,z, \
             startphi,deltaphi,aunit,lunit,material,colour)
    GDMLShared.trace("CreateCone : ")
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mycone.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mycone.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set "ViewProvider before setDisplay
       ViewProvider(mycone.ViewObject)
       setDisplayMode(mycone,displayMode)
    return(mycone)

def createElcone(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLElCone, ViewProvider
    GDMLShared.trace("CreateElCone : ")
    dx = GDMLShared.getVal(solid,'dx')
    dy = GDMLShared.getVal(solid,'dy')
    zmax = GDMLShared.getVal(solid,'zmax')
    zcut = GDMLShared.getVal(solid,'zcut')
    lunit = getText(solid,'lunit',"mm")
    myelcone=part.newObject("Part::FeaturePython","GDMLElCone:"+getName(solid))
    GDMLElCone(myelcone,dx,dy,zmax,zcut,lunit,material,colour)
    GDMLShared.trace("CreateElCone : ")
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    #base = FreeCAD.Vector(0,0,0)
    myelcone.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(myelcone.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(myelcone.ViewObject)
       setDisplayMode(myelcone,displayMode)
    return(myelcone)

def createEllipsoid(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLEllipsoid, ViewProvider
    GDMLShared.trace("CreateElTube : ")
    GDMLShared.trace(solid.attrib)
    ax = GDMLShared.getVal(solid,'ax')
    by = GDMLShared.getVal(solid,'by')
    cz = GDMLShared.getVal(solid,'cz')
    zcut1 = GDMLShared.getVal(solid,'zcut1')
    zcut2 = GDMLShared.getVal(solid,'zcut2')
    lunit = getText(solid,'lunit',"mm")
    myelli=part.newObject("Part::FeaturePython","GDMLEllipsoid:"+getName(solid))
    # cuts 0 for now
    GDMLEllipsoid(myelli,ax, by, cz,zcut1,zcut2,lunit,material,colour)
    GDMLShared.trace("CreateEllipsoid : ")
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    myelli.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(myelli.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(myelli.ViewObject)
       setDisplayMode(myelli,displayMode)
    return myelli

def createEltube(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLElTube, ViewProvider
    GDMLShared.trace("CreateElTube : ")
    GDMLShared.trace(solid.attrib)
    dx = GDMLShared.getVal(solid,'dx')
    dy = GDMLShared.getVal(solid,'dy')
    dz = GDMLShared.getVal(solid,'dz')
    lunit = getText(solid,'lunit',"mm")
    myeltube=part.newObject("Part::FeaturePython","GDMLElTube:"+getName(solid))
    GDMLElTube(myeltube,dx, dy, dz,lunit,material,colour)
    GDMLShared.trace("CreateElTube : ")
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    myeltube.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(myeltube.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDispla
       ViewProvider(myeltube.ViewObject)
       setDisplayMode(myeltube,displayMode)
    return myeltube

def createGenericPolycone(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLGenericPolycone, GDMLrzpoint, \
            ViewProvider, ViewProviderExtension
    GDMLShared.trace("Create GenericPolycone : ")
    GDMLShared.trace(solid.attrib)
    startphi = GDMLShared.getVal(solid,'startphi')
    deltaphi = GDMLShared.getVal(solid,'deltaphi')
    aunit = getText(solid,'aunit','rad')
    lunit = getText(solid,'lunit',"mm")
    mypolycone=part.newObject("Part::FeaturePython","GDMLGenericPolycone:"+getName(solid))
    mypolycone.addExtension("App::GroupExtensionPython")
    GDMLGenericPolycone(mypolycone,startphi,deltaphi,aunit,lunit,material,colour)
    if FreeCAD.GuiUp :
       ViewProviderExtension(mypolycone.ViewObject)

    #mypolycone.ViewObject.DisplayMode = "Shaded"
    GDMLShared.trace(solid.findall('rzpoint'))
    for zplane in solid.findall('rzpoint') : 
        GDMLShared.trace(zplane)
        r = GDMLShared.getVal(zplane,'r',0)
        z = GDMLShared.getVal(zplane,'z')
        myrzpoint=FreeCAD.ActiveDocument.addObject('App::FeaturePython','rzpoint') 
        mypolycone.addObject(myrzpoint)
        GDMLrzpoint(myrzpoint,r,z)
        if FreeCAD.GuiUp :
           ViewProvider(myrzpoint)

    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mypolycone.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mypolycone.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       setDisplayMode(mypolycone,displayMode)
    return mypolycone


def createGenericPolyhedra(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLGenericPolyhedra, GDMLrzpoint, \
            ViewProvider, ViewProviderExtension
    GDMLShared.trace("Create GenericPolyhedra : ")
    GDMLShared.trace(solid.attrib)
    startphi = GDMLShared.getVal(solid,'startphi')
    deltaphi = GDMLShared.getVal(solid,'deltaphi')
    numsides = int(GDMLShared.getVal(solid,'numsides'))
    aunit = getText(solid,'aunit','rad')
    lunit = getText(solid,'lunit',"mm")
    mypolyhedra=part.newObject("Part::FeaturePython","GDMLGenericPolyhedra:"+getName(solid))
    mypolyhedra.addExtension("App::GroupExtensionPython")
    GDMLGenericPolyhedra(mypolyhedra,startphi,deltaphi,numsides,aunit,lunit,material,colour)
    if FreeCAD.GuiUp :
       ViewProviderExtension(mypolyhedra.ViewObject)

    #mypolycone.ViewObject.DisplayMode = "Shaded"
    GDMLShared.trace(solid.findall('rzpoint'))
    for zplane in solid.findall('rzpoint') : 
        GDMLShared.trace(zplane)
        r = GDMLShared.getVal(zplane,'r',0)
        z = GDMLShared.getVal(zplane,'z')
        myrzpoint=FreeCAD.ActiveDocument.addObject('App::FeaturePython','rzpoint') 
        mypolyhedra.addObject(myrzpoint)
        GDMLrzpoint(myrzpoint,r,z)
        if FreeCAD.GuiUp :
           ViewProvider(myrzpoint)

    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mypolyhedra.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mypolyhedra.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       setDisplayMode(mypolyhedra,displayMode)
    return mypolyhedra


def createOrb(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLOrb, ViewProvider
    GDMLShared.trace("CreateOrb : ")
    GDMLShared.trace(solid.attrib)
    r = GDMLShared.getVal(solid,'r')
    lunit = getText(solid,'lunit',"mm")
    myorb=part.newObject("Part::FeaturePython","GDMLOrb:"+getName(solid))
    GDMLOrb(myorb,r,lunit,material,colour)
    GDMLShared.trace("CreateOrb : ")
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    myorb.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(myorb.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(myorb.ViewObject)
       setDisplayMode(myorb,displayMode)
    return myorb

def createPara(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLPara, ViewProvider
    GDMLShared.trace("CreatePara : ")
    GDMLShared.trace(solid.attrib)
    aunit = getText(solid,'aunit',"rad")
    lunit = getText(solid,'lunit',"mm")
    x = GDMLShared.getVal(solid,'x')
    y = GDMLShared.getVal(solid,'y')
    z = GDMLShared.getVal(solid,'z')
    alpha = GDMLShared.getVal(solid,'alpha')
    theta = GDMLShared.getVal(solid,'theta')
    phi = GDMLShared.getVal(solid,'phi')
    mypara=part.newObject("Part::FeaturePython","GDMLPara:"+getName(solid))
    GDMLPara(mypara,x,y,z,alpha,theta,phi,aunit,lunit,material,colour)
    GDMLShared.trace("CreatePara : ")
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mypara.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mypara.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mypara.ViewObject)
       setDisplayMode(mypara,displayMode)
    return mypara

def createHype(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLHype, ViewProvider
    GDMLShared.trace("CreateHype : ")
    GDMLShared.trace(solid.attrib)
    aunit = getText(solid,'aunit',"rad")
    lunit = getText(solid,'lunit',"mm")
    rmin = GDMLShared.getVal(solid,'rmin')
    rmax = GDMLShared.getVal(solid,'rmax')
    z = GDMLShared.getVal(solid,'z')
    inst = GDMLShared.getVal(solid,'inst')
    outst = GDMLShared.getVal(solid,'outst')
    myhype=part.newObject("Part::FeaturePython","GDMLHype:"+getName(solid))
    GDMLHype(myhype,rmin,rmax,z,inst,outst,aunit,lunit,material,colour)
    GDMLShared.trace("CreateHype : ")
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    myhype.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(myhype.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(myhype.ViewObject)
       setDisplayMode(myhype,displayMode)
    return myhype

def createParaboloid(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLParaboloid, ViewProvider
    GDMLShared.trace("CreateParaboloid : ")
    GDMLShared.trace(solid.attrib)
    lunit = getText(solid,'lunit',"mm")
    rlo = GDMLShared.getVal(solid,'rlo')
    rhi = GDMLShared.getVal(solid,'rhi')
    dz = GDMLShared.getVal(solid,'dz')
    myparaboloid=part.newObject("Part::FeaturePython","GDMLParaboloid:"+getName(solid))
    GDMLParaboloid(myparaboloid,rlo,rhi,dz,lunit,material,colour)
    GDMLShared.trace("CreateParaboloid : ")
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    myparaboloid.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(myparaboloid.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(myparaboloid.ViewObject)
       setDisplayMode(myparaboloid,displayMode)
    return myparaboloid

def createPolycone(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLPolycone, GDMLzplane, \
            ViewProvider, ViewProviderExtension
    GDMLShared.trace("Create Polycone : ")
    GDMLShared.trace(solid.attrib)
    startphi = GDMLShared.getVal(solid,'startphi')
    deltaphi = GDMLShared.getVal(solid,'deltaphi')
    aunit = getText(solid,'aunit','rad')
    lunit = getText(solid,'lunit',"mm")
    mypolycone=part.newObject("Part::FeaturePython","GDMLPolycone:"+getName(solid))
    mypolycone.addExtension("App::GroupExtensionPython")
    GDMLPolycone(mypolycone,startphi,deltaphi,aunit,lunit,material,colour)
    if FreeCAD.GuiUp :
       ViewProviderExtension(mypolycone.ViewObject)

    #mypolycone.ViewObject.DisplayMode = "Shaded"
    GDMLShared.trace(solid.findall('zplane'))
    for zplane in solid.findall('zplane') : 
        GDMLShared.trace(zplane)
        rmin = GDMLShared.getVal(zplane,'rmin',0)
        rmax = GDMLShared.getVal(zplane,'rmax')
        z = GDMLShared.getVal(zplane,'z')
        myzplane=FreeCAD.ActiveDocument.addObject('App::FeaturePython','zplane') 
        mypolycone.addObject(myzplane)
        #myzplane=mypolycone.newObject('App::FeaturePython','zplane') 
        GDMLzplane(myzplane,rmin,rmax,z)
        if FreeCAD.GuiUp :
           ViewProvider(myzplane)

    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mypolycone.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mypolycone.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       setDisplayMode(mypolycone,displayMode)
    return mypolycone

def createPolyhedra(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLPolyhedra, GDMLzplane, \
            ViewProvider, ViewProviderExtension
    GDMLShared.trace("Create Polyhedra : ")
    GDMLShared.trace(solid.attrib)
    startphi = GDMLShared.getVal(solid,'startphi')
    deltaphi = GDMLShared.getVal(solid,'deltaphi')
    numsides = int(GDMLShared.getVal(solid,'numsides'))
    aunit = getText(solid,'aunit','rad')
    lunit = getText(solid,'lunit',"mm")
    mypolyhedra=part.newObject("Part::FeaturePython","GDMLPolyhedra:"+ \
                getName(solid))
    mypolyhedra.addExtension("App::GroupExtensionPython")
    GDMLPolyhedra(mypolyhedra,startphi,deltaphi,numsides,aunit,lunit, \
                  material,colour)
    if FreeCAD.GuiUp :
       ViewProviderExtension(mypolyhedra.ViewObject)

    #mypolyhedra.ViewObject.DisplayMode = "Shaded"
    GDMLShared.trace(solid.findall('zplane'))
    for zplane in solid.findall('zplane') : 
        GDMLShared.trace(zplane)
        rmin = GDMLShared.getVal(zplane,'rmin',0)
        rmax = GDMLShared.getVal(zplane,'rmax')
        z = GDMLShared.getVal(zplane,'z')
        myzplane=FreeCAD.ActiveDocument.addObject('App::FeaturePython','zplane') 
        mypolyhedra.addObject(myzplane)
        #myzplane=mypolyhedra.newObject('App::FeaturePython','zplane') 
        GDMLzplane(myzplane,rmin,rmax,z)
        if FreeCAD.GuiUp :
           ViewProvider(myzplane)

    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mypolyhedra.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mypolyhedra.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       setDisplayMode(mypolyhedra,displayMode)
    return mypolyhedra

def createSphere(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLSphere, ViewProvider
    #GDMLShared.setTrace(True)
    GDMLShared.trace("CreateSphere : ")
    GDMLShared.trace("Display Mode : "+str(displayMode))
    GDMLShared.trace(solid.attrib)
    rmin = GDMLShared.getVal(solid,'rmin',0)
    rmax = GDMLShared.getVal(solid,'rmax')
    startphi = GDMLShared.getVal(solid,'startphi')
    deltaphi = GDMLShared.getVal(solid,'deltaphi')
    aunit = getText(solid,'aunit','rad')
    lunit = getText(solid,'lunit',"mm")
    starttheta = GDMLShared.getVal(solid,'starttheta')
    deltatheta = GDMLShared.getVal(solid,'deltatheta')
    mysphere=part.newObject("Part::FeaturePython","GDMLSphere:"+getName(solid))
    GDMLSphere(mysphere,rmin,rmax,startphi,deltaphi,starttheta, \
            deltatheta,aunit, lunit,material,colour)
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mysphere.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mysphere.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mysphere.ViewObject)
       setDisplayMode(mysphere,displayMode)
    return mysphere

def createTetra(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLTetra, ViewProvider
    #GDMLShared.setTrace(True)
    GDMLShared.trace("CreateTet : ")
    GDMLShared.trace(solid.attrib)
    v1 = GDMLShared.getDefinedVector(solid,'vertex1')
    v2 = GDMLShared.getDefinedVector(solid,'vertex2')
    v3 = GDMLShared.getDefinedVector(solid,'vertex3')
    v4 = GDMLShared.getDefinedVector(solid,'vertex4')
    lunit = getText(solid,'lunit',"mm")
    mytetra=part.newObject("Part::FeaturePython","GDMLTetra:"+getName(solid))
    GDMLTetra(mytetra,v1,v2,v3,v4,lunit,material,colour)
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mytetra.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mytetra.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mytetra.ViewObject)
       setDisplayMode(mytetra,displayMode)
    return mytetra

def createTorus(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLTorus, ViewProvider
    #GDMLShared.setTrace(True)
    GDMLShared.trace("CreateTorus : ")
    GDMLShared.trace(solid.attrib)
    rmin = GDMLShared.getVal(solid,'rmin',0)
    rmax = GDMLShared.getVal(solid,'rmax')
    rtor = GDMLShared.getVal(solid,'rtor')
    startphi = GDMLShared.getVal(solid,'startphi')
    deltaphi = GDMLShared.getVal(solid,'deltaphi')
    aunit = getText(solid,'aunit','rad')
    lunit = getText(solid,'lunit',"mm")
    mytorus=part.newObject("Part::FeaturePython","GDMLTorus:"+getName(solid))
    GDMLTorus(mytorus,rmin,rmax,rtor,startphi,deltaphi, \
              aunit, lunit,material,colour)
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mytorus.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mytorus.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mytorus.ViewObject)
       setDisplayMode(mytorus,displayMode)
    return mytorus

def createTrap(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLTrap, ViewProvider
    GDMLShared.trace("CreateTrap : ")
    GDMLShared.trace(solid.attrib)
    z  = GDMLShared.getVal(solid,'z')
    x1 = GDMLShared.getVal(solid,'x1')
    x2 = GDMLShared.getVal(solid,'x2')
    x3 = GDMLShared.getVal(solid,'x3')
    x4 = GDMLShared.getVal(solid,'x4')
    y1 = GDMLShared.getVal(solid,'y1')
    y2 = GDMLShared.getVal(solid,'y2')
    theta = GDMLShared.getVal(solid,'theta')
    phi = GDMLShared.getVal(solid,'phi')
    alpha1 = GDMLShared.getVal(solid,'alpha1')
    aunit = getText(solid,'aunit','rad')
    lunit = getText(solid,'lunit',"mm")
    #print z
    mytrap=part.newObject("Part::FeaturePython","GDMLTrap:"+getName(solid))
    GDMLTrap(mytrap,z,theta,phi,x1,x2,x3,x4,y1,y2,alpha1,aunit,lunit, \
             material,colour)
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mytrap.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mytrap.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mytrap.ViewObject)
       setDisplayMode(mytrap,displayMode)
    return mytrap

def createTrd(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLTrd, ViewProvider
    GDMLShared.trace("CreateTrd : ")
    GDMLShared.trace(solid.attrib)
    z  = GDMLShared.getVal(solid,'z')
    x1 = GDMLShared.getVal(solid,'x1')
    x2 = GDMLShared.getVal(solid,'x2')
    y1 = GDMLShared.getVal(solid,'y1')
    y2 = GDMLShared.getVal(solid,'y2')
    lunit = getText(solid,'lunit',"mm")
    #print z
    mytrd=part.newObject("Part::FeaturePython","GDMLTrd:"+getName(solid))
    GDMLTrd(mytrd,z,x1,x2,y1,y2,lunit,material,colour)
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mytrd.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mytrd.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mytrd.ViewObject)
       setDisplayMode(mytrd,displayMode)
    return mytrd

def createTwistedbox(part,solid,material,colour,px,py,pz,rot,displayMode) :
    # parent, sold
    from .GDMLObjects import GDMLTwistedbox, ViewProvider
    #GDMLShared.setTrace(True)
    GDMLShared.trace("CreateTwisted : ")
    #GDMLShared.trace("material : "+material)
    GDMLShared.trace(solid.attrib)

    # modifs lambda (otherwise each time we open the gdml file, 
    # the part name will have one more GDMLBox added
    # No - need to remove leading GDMLBox on export
    mypart = part.newObject("Part::FeaturePython","GDMLTwistedbox:"+getName(solid))
    #mycube=part.newObject("Part::FeaturePython",getName(solid))
    x = GDMLShared.getVal(solid,'x')
    y = GDMLShared.getVal(solid,'y')
    z = GDMLShared.getVal(solid,'z')
    lunit = getText(solid,'lunit',"mm")
    angle = GDMLShared.getVal(solid,'PhiTwist')
    aunit = getText(solid,'aunit','rad')
    
    #print(f'Cube colour : {colour}')
    GDMLTwistedbox(mypart,angle,x,y,z,aunit,lunit,material,colour)
    GDMLShared.trace("Logical Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mypart.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mypart.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mypart.ViewObject)
       setDisplayMode(mypart,displayMode)
    #myCube.Shape = translate(mycube.Shape,base)
    return mypart

def createTwistedtrap(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLTwistedtrap, ViewProvider
    GDMLShared.trace("CreateTwistedtrap : ")
    GDMLShared.trace(solid.attrib)
    PhiTwist = GDMLShared.getVal(solid,'PhiTwist')
    z  = GDMLShared.getVal(solid,'z')
    x1 = GDMLShared.getVal(solid,'x1')
    x2 = GDMLShared.getVal(solid,'x2')
    x3 = GDMLShared.getVal(solid,'x3')
    x4 = GDMLShared.getVal(solid,'x4')
    y1 = GDMLShared.getVal(solid,'y1')
    y2 = GDMLShared.getVal(solid,'y2')
    theta = GDMLShared.getVal(solid,'Theta')
    phi = GDMLShared.getVal(solid,'Phi')
    alpha = GDMLShared.getVal(solid,'Alph')
    aunit = getText(solid,'aunit','rad')
    lunit = getText(solid,'lunit',"mm")
    #print z
    mytrap=part.newObject("Part::FeaturePython","GDMLTwistedtrap:"+getName(solid))
    GDMLTwistedtrap(mytrap,PhiTwist,z,theta,phi,x1,x2,x3,x4,y1,y2,alpha,aunit,lunit, \
             material,colour)
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mytrap.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mytrap.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mytrap.ViewObject)
       setDisplayMode(mytrap,displayMode)
    return mytrap

def createTwistedtrd(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLTwistedtrd, ViewProvider
    GDMLShared.trace("CreateTwistedtrd : ")
    GDMLShared.trace(solid.attrib)
    z  = GDMLShared.getVal(solid,'z')
    x1 = GDMLShared.getVal(solid,'x1')
    x2 = GDMLShared.getVal(solid,'x2')
    y1 = GDMLShared.getVal(solid,'y1')
    y2 = GDMLShared.getVal(solid,'y2')
    lunit = getText(solid,'lunit',"mm")
    angle = GDMLShared.getVal(solid,'PhiTwist')
    aunit = getText(solid,'aunit','rad')
    #print z
    mytrd=part.newObject("Part::FeaturePython","GDMLTwistedtrd:"+getName(solid))
    GDMLTwistedtrd(mytrd,angle,z,x1,x2,y1,y2,aunit,lunit,material,colour)
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mytrd.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mytrd.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mytrd.ViewObject)
       setDisplayMode(mytrd,displayMode)
    return mytrd

def createTwistedtubs(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLTwistedtubs, ViewProvider
    GDMLShared.trace("CreateTwistedtubs : ")
    GDMLShared.trace(solid.attrib)
    zlen  = GDMLShared.getVal(solid,'zlen')
    endinnerrad = GDMLShared.getVal(solid,'endinnerrad')
    endouterrad = GDMLShared.getVal(solid,'endouterrad')
    lunit = getText(solid,'lunit',"mm")
    twistedangle = GDMLShared.getVal(solid,'twistedangle')
    phi = GDMLShared.getVal(solid,'phi')
    aunit = getText(solid,'aunit','rad')
    mypart=part.newObject("Part::FeaturePython","GDMLTwistedtubs:"+getName(solid))
    GDMLTwistedtubs(mypart,endinnerrad,endouterrad,zlen,twistedangle,phi,aunit,lunit,material,colour)
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    mypart.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mypart.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mypart.ViewObject)
       setDisplayMode(mypart,displayMode)
    return mypart

def createXtru(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLXtru, GDML2dVertex, GDMLSection, \
             ViewProvider, ViewProviderExtension
    GDMLShared.trace("CreateXtru : ")
    #print(solid)
    #print(getName(solid))
    myXtru=part.newObject("Part::FeaturePython","GDMLXtru-"+getName(solid))
    #myXtru.addExtension("App::GroupExtensionPython")
    lunit = getText(solid,'lunit',"mm")
    GDMLXtru(myXtru,lunit,material,colour)
    if FreeCAD.GuiUp :
       ViewProviderExtension(myXtru.ViewObject)
    for vert2d in solid.findall('twoDimVertex') : 
        x = GDMLShared.getVal(vert2d,'x')
        y = GDMLShared.getVal(vert2d,'y')
        my2dVert=FreeCAD.ActiveDocument.addObject('App::FeaturePython','GDML2DVertex') 
        #myzplane=mypolycone.newObject('App::FeaturePython','zplane') 
        GDML2dVertex(my2dVert,x,y)
        myXtru.addObject(my2dVert)
        if FreeCAD.GuiUp :
           ViewProvider(my2dVert)
    for section in solid.findall('section') : 
        zOrder = int(GDMLShared.getVal(section,'zOrder'))  # Get Int
        zPosition = GDMLShared.getVal(section,'zPosition') # Get Float
        xOffset = GDMLShared.getVal(section,'xOffset')
        yOffset = GDMLShared.getVal(section,'yOffset')
        scalingFactor = GDMLShared.getVal(section,'scalingFactor')
        mysection=FreeCAD.ActiveDocument.addObject('App::FeaturePython','GDMLSection')
        GDMLSection(mysection,zOrder,zPosition,xOffset,yOffset,scalingFactor)
        myXtru.addObject(mysection)
        if FreeCAD.GuiUp :
           ViewProvider(mysection)

    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    myXtru.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(myXtru.Placement.Rotation)
    # Shape is still Null at this point
    #print("Xtru Shape : ")
    #print("Is Null : "+str(myXtru.Shape.isNull()))
    return(myXtru)

def createTube(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLTube, ViewProvider
    GDMLShared.trace("CreateTube : ")
    GDMLShared.trace(solid.attrib)
    rmin = GDMLShared.getVal(solid,'rmin',0)
    rmax = GDMLShared.getVal(solid,'rmax')
    z = GDMLShared.getVal(solid,'z')
    startphi = GDMLShared.getVal(solid,'startphi')
    deltaphi = GDMLShared.getVal(solid,'deltaphi')
    aunit = getText(solid,'aunit','rad')
    lunit = getText(solid,'lunit',"mm")
    GDMLShared.trace(rmin)
    GDMLShared.trace(rmax)
    GDMLShared.trace(z)
    mytube=part.newObject("Part::FeaturePython","GDMLTube:"+getName(solid))
    GDMLTube(mytube,rmin,rmax,z,startphi,deltaphi,aunit,lunit,material,colour)
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    #base = FreeCAD.Vector(0,0,0)
    base = FreeCAD.Vector(px,py,pz)
    mytube.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mytube.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mytube.ViewObject)
       setDisplayMode(mytube,displayMode)
    return mytube

def createCutTube(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLcutTube, ViewProvider
    GDMLShared.trace("CreateCutTube : ")
    GDMLShared.trace(solid.attrib)
    rmin = GDMLShared.getVal(solid,'rmin',0)
    rmax = GDMLShared.getVal(solid,'rmax')
    z = GDMLShared.getVal(solid,'z')
    startphi = GDMLShared.getVal(solid,'startphi')
    deltaphi = GDMLShared.getVal(solid,'deltaphi')
    aunit = getText(solid,'aunit','rad')
    GDMLShared.trace("aunit : "+aunit)
    lowX = GDMLShared.getVal(solid,'lowX')
    lowY = GDMLShared.getVal(solid,'lowY')
    lowZ = GDMLShared.getVal(solid,'lowZ')
    highX = GDMLShared.getVal(solid,'highX')
    highY = GDMLShared.getVal(solid,'highY')
    highZ = GDMLShared.getVal(solid,'highZ')
    lunit = getText(solid,'lunit',"mm")
    GDMLShared.trace(rmin)
    GDMLShared.trace(rmax)
    GDMLShared.trace(z)
    GDMLShared.trace(lowX)
    GDMLShared.trace(lowY)
    GDMLShared.trace(lowZ)
    GDMLShared.trace(highX)
    GDMLShared.trace(highY)
    GDMLShared.trace(highZ)
    mycuttube=part.newObject("Part::FeaturePython","GDMLcutTube:"+getName(solid))
    GDMLcutTube(mycuttube,rmin,rmax,z,startphi,deltaphi,aunit, \
                lowX, lowY, lowZ, highX, highY, highZ, lunit, material,colour)
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    #base = FreeCAD.Vector(0,0,0)
    base = FreeCAD.Vector(px,py,pz)
    mycuttube.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(mycuttube.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(mycuttube.ViewObject)
       setDisplayMode(mycuttube,displayMode)
    return mycuttube

def indexVertex(list,name) :
    try :
        i = list.index(name)
    except:
        return -1
    return i 

def createTessellated(part,solid,material,colour,px,py,pz,rot,displayMode) :
    from .GDMLObjects import GDMLTessellated, GDMLTriangular, \
          GDMLQuadrangular, ViewProvider, ViewProviderExtension
    #GDMLShared.setTrace(True)
    GDMLShared.trace("CreateTessellated : ")
    GDMLShared.trace(solid.attrib)
    vertNames = []
    vertex = []
    faces  = []
    lunit = getText(solid,'lunit',"mm")
    for elem in solid.getchildren() :
        v1name = elem.get('vertex1')
        #print(v1name)
        v1 = GDMLShared.getDefinedPosition(v1name)
        #print(v1)
        v1pos = indexVertex(vertNames,v1name)
        if v1pos < 0 :
           vertNames.append(v1name)
           v1pos = len(vertNames) - 1
           vertex.append(v1)
        #print(v1pos)
        v2name = elem.get('vertex2')
        #print(v2name)
        v2 = GDMLShared.getDefinedPosition(v2name)
        #print(v2)
        v2pos = indexVertex(vertNames,v2name)
        if v2pos < 0 :
           vertNames.append(v2name)
           v2pos = len(vertNames) - 1
           vertex.append(v2)
        #print(v2pos)
        v3name = elem.get('vertex3')
        #print(v3name)
        v3 = GDMLShared.getDefinedPosition(v3name)
        #print(v3)
        v3pos = indexVertex(vertNames,v3name)
        if v3pos < 0 :
           vertNames.append(v3name)
           v3pos = len(vertNames) - 1
           vertex.append(v3)
        #print(v3pos)
        vType = elem.get('type')
        if elem.tag == 'triangular' :
           faces.append([v1pos,v2pos,v3pos])
        if elem.tag == 'quadrangular' :
           v4name = elem.get('vertex4')
           #print(v4name)
           v4 = GDMLShared.getDefinedPosition(v4name)
           #print(v4)
           v4pos = indexVertex(vertNames,v4name)
           if v4pos < 0 :
              vertNames.append(v4name)
              v4pos = len(vertNames) - 1
              #print(v4pos)
              vertex.append(v4)
           faces.append([v1pos,v2pos,v3pos,v4pos])
    #print(vertNames)
    myTess=part.newObject("Part::FeaturePython","GDMLTessellated:" \
                          +getName(solid))
    tess = GDMLTessellated(myTess,vertex,faces,False,lunit,material,colour)
    if FreeCAD.GuiUp :
       ViewProvider(myTess.ViewObject)
    GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
    base = FreeCAD.Vector(px,py,pz)
    myTess.Placement = GDMLShared.processPlacement(base,rot)
    GDMLShared.trace(myTess.Placement.Rotation)
    if FreeCAD.GuiUp :
       # set ViewProvider before setDisplay
       ViewProvider(myTess.ViewObject)
       setDisplayMode(myTess,displayMode)
    return myTess

def parseMultiUnion(part,solid,material,colour,px,py,pz,rot,displayMode) :
    #GDMLShared.setTrace(True)
    GDMLShared.trace('Multi Union - MultiFuse')
    muName = solid.attrib.get('name')
    GDMLShared.trace('multi Union : '+muName)
    myMUobj = part.newObject('Part::MultiFuse',muName)
    #for s in solid.findall('multiUnionNode') :
    objList = []
    for s in solid :
        # each solid may change x,y,z,rot
        nx = px
        ny = py
        nz = pz
        nrot = rot
        if s.tag == 'multiUnionNode' :
            for t in s :
                if t.tag == 'solid' :
                    sname = t.get('ref')
                    GDMLShared.trace('solid : '+sname)
                    ssolid  = solids.find("*[@name='%s']" % sname )
                if t.tag == 'positionref' :
                    pname = t.get('ref')
                    nx, ny, nz = GDMLShared.getDefinedPosition(pname)
                    GDMLShared.trace('nx : '+str(nx))
                if t.tag == 'rotationref' :
                    rname = t.get('ref')
                    GDMLShared.trace('rotation ref : '+rname)
                    nrot = GDMLShared.getDefinedRotation(rname)
            if sname is not None :        # Did we find at least one solid
                objList.append(createSolid(part,ssolid,material,colour,nx,ny,nz, \
                    nrot,displayMode))
    #myMUobj = part.newObject('Part::MultiFuse',muName)
    myMUobj.Shapes = objList


def parseBoolean(part,solid,objType,material,colour,px,py,pz,rot,displayMode) :
    # parent, solid, boolean Type,
    from .GDMLObjects import ViewProvider

    #GDMLShared.setTrace(True)
    GDMLShared.trace('Parse Boolean : '+str(solid.tag))
    GDMLShared.trace(solid.tag)
    GDMLShared.trace(solid.attrib)
    if solid.tag in ["subtraction","union","intersection"] :
       GDMLShared.trace("Boolean : "+solid.tag)
       name1st = GDMLShared.getRef(solid,'first')
       base = solids.find("*[@name='%s']" % name1st )
       GDMLShared.trace("first : "+name1st)
       #parseObject(root,base)
       name2nd = GDMLShared.getRef(solid,'second')
       tool = solids.find("*[@name='%s']" % name2nd )
       GDMLShared.trace("second : "+name2nd)
       x,y,z = GDMLShared.getPosition(solid)
       #rot = GDMLShared.getRotFromRefs(solid)
       rotBool = GDMLShared.getRotation(solid)
       mybool = part.newObject(objType,solid.tag+':'+getName(solid))
       #mybool = part.newObject('Part::Fuse',solid.tag+':'+getName(solid))
       GDMLShared.trace('Create Base Object')
       mybool.Base = createSolid(part,base,material,colour,0,0,0,None,displayMode)
       # second solid is placed at position and rotation relative to first
       GDMLShared.trace('Create Tool Object')
       mybool.Tool = createSolid(part,tool,material,None,x,y,z,rotBool,displayMode)
       # For some unknown reasons, inversionof angle in processRotation
       # should not be peformed for boolean Tool
       mybool.Tool.Placement.Rotation.Angle = \
                  -mybool.Tool.Placement.Rotation.Angle
       # Okay deal with position of boolean
       GDMLShared.trace('Boolean Position and rotation')
       GDMLShared.trace("Position : "+str(px)+','+str(py)+','+str(pz))
       #base = FreeCAD.Vector(0,0,0)
       base = FreeCAD.Vector(px,py,pz)
       mybool.Placement = GDMLShared.processPlacement(base,rot)
       #if FreeCAD.GuiUp :
       #     ViewProvider(mybool.ViewObject)
       return mybool

def createSolid(part,solid,material,colour,px,py,pz,rot,displayMode) :
    # parent,solid, material
    # returns created Object
    GDMLShared.trace('createSolid '+solid.tag)
    GDMLShared.trace('px : '+str(px))
    while switch(solid.tag) :
        if case('arb8'):
            return(createArb8(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('box'):
            return(createBox(part,solid,material,colour,px,py,pz,rot,displayMode)) 
        
        if case('cone'):
            return(createCone(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('elcone'):
            return(createElcone(part,solid,material,colour,px,py,pz,rot,displayMode)) 
        
        if case('ellipsoid'):
            return(createEllipsoid(part,solid,material,colour,px,py,pz,rot,displayMode)) 
        
        if case('eltube'):
            return(createEltube(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('hype'):
            return(createHype(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('orb'):
            return(createOrb(part,solid,material,colour,px,py,pz,rot,displayMode)) 
        
        if case('para'):
           return(createPara(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('paraboloid'):
           return(createParaboloid(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('polycone'):
            return(createPolycone(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('genericPolycone'):
            return(createGenericPolycone(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('polyhedra'):
            return(createPolyhedra(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('genericPolyhedra'):
            return(createGenericPolyhedra(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('sphere'):
            return(createSphere(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('tet'):
            return(createTetra(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('torus'):
            return(createTorus(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('trap'):
            return(createTrap(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('trap_dimensions'):
            return(createTrap(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('trd'):
            return(createTrd(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('twistedbox'):
            return(createTwistedbox(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('twistedtrap'):
            return(createTwistedtrap(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('twistedtrd'):
            return(createTwistedtrd(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('twistedtubs'):
            return(createTwistedtubs(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('tube'):
            return(createTube(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('cutTube'):
            return(createCutTube(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('tessellated'):
            return(createTessellated(part,solid,material,colour,px,py,pz,rot,displayMode)) 

        if case('xtru'):
           return(createXtru(part,solid,material,colour,px,py,pz,rot,displayMode)) 
           break

        if case('intersection'):
            return(parseBoolean(part,solid,'Part::Common', \
                  material,colour,px,py,pz,rot,displayMode)) 

        if case('union'):
            GDMLShared.trace(f'union colour : {colour}')
            return(parseBoolean(part,solid,'Part::Fuse', \
                  material,colour,px,py,pz,rot,displayMode))

        if case('subtraction'):
            return(parseBoolean(part,solid,'Part::Cut', \
                                material,colour,px,py,pz,rot,displayMode)) 

        if case('multiUnion'):
            return(parseMultiUnion(part,solid,material,colour, \
                                   px,py,pz,rot,displayMode))

        print("Solid : "+solid.tag+" Not yet supported")
        return

def getVolSolid(name):
    GDMLShared.trace("Get Volume Solid")
    vol = structure.find("/volume[@name='%s']" % name )
    sr = vol.find("solidref")
    GDMLShared.trace(sr.attrib)
    name = GDMLShared.getRef(sr,'name')
    solid = solids.find("*[@name='%s']" % name )
    return solid

def parsePhysVol(volAsmFlg, parent,physVol,phylvl,displayMode):
    # if volAsmFlag == True : Volume
    # if volAsmFlag == False : Assembly 
    # physvol is xml entity
    #GDMLShared.setTrace(True)
    GDMLShared.trace("ParsePhyVol : level : "+str(phylvl))
    # Test if any physvol file imports
    filePtr = physVol.find('file')
    if filePtr is not None :
       fname = filePtr.get('name')
       processPhysVolFile(doc,parent,fname)
    volRef = GDMLShared.getRef(physVol,"volumeref")
    GDMLShared.trace("Volume Ref : "+str(volRef))
    if volRef is not None :
       copyNum = physVol.get('copynumber')
       GDMLShared.trace('Copynumber : '+str(copyNum))
       # lhcbvelo has duplicate with no copynumber
       # Test if exists
       namedObj = FreeCAD.ActiveDocument.getObject(volRef)
       if namedObj is None :
          print(f'New Vol : {volRef}')
          part = parent.newObject("App::Part",volRef)
          expandVolume(part,volRef,phylvl,displayMode)

       else :  # Object exists create a Linked Object
          GDMLShared.trace('====> Create Link to : '+volRef)
          print('====> Create Link to : '+volRef)
          part = parent.newObject('App::Link',volRef)
          part.LinkedObject = namedObj
          if part.Name is not volRef :
             ln = len(volRef)
             part.Label = volRef + '_' + part.Name[ln:]
          try : # try as not working FC 0.18
             part.addProperty("App::PropertyString","VolRef", \
                               "GDML").VolRef=volRef
          except:
             pass

          scale = GDMLShared.getScale(physVol)
          #print(scale)
          part.ScaleVector = scale
          #if scale is not FreeCAD.Vector(1.,1.,1.) :
          #   try :  # try as not working FC 0.18
          #      part.addProperty("App::PropertyVector","GDMLscale","Link", \
          #         "GDML Scale Vector").GDMLscale = scale
          #   except:
          #      print('Scale not supported with FreeCAD 0.18')
    
       # This would be for Placement of Part need FC 0.19 Fix       
       part.Placement = GDMLShared.getPlacement(physVol)
          
       # Louis gdml file copynumber on non duplicate   
       if copyNum is not None :
          try : # try as not working FC 0.18
             part.addProperty("App::PropertyInteger","CopyNumber", \
                               "GDML").CopyNumber=int(copyNum)
          except:
             print('Copynumber not supported in FreeCAD 0.18')

    #GDMLShared.setTrace(False)

def getColour(colRef) :
    #print(f'colRef : {colRef}')
    #print(str(extension))
    if extension is not None :
       colxml = extension.find("*[@name='%s']" % colRef )
       #print(str(colxml))
       R = G = B = A = 0.0
       if colxml is not None :
          R = G = B = A = 0.0
          R = colxml.get("R")
          G = colxml.get("G")
          B = colxml.get("B")
          A = colxml.get("A")
    print(f'R : {R} - G : {G} - B : {B} - A : {A}') 
    return (float(R),float(G),float(B),1.0 - float(A))
 
# ParseVolume name - structure is global
# displayMode 1 normal 2 hide 3 wireframe
def parseVolume(parent,name,phylvl,displayMode) :
    GDMLShared.trace("ParseVolume : "+name)
    expandVolume(parent,name,phylvl,displayMode)

def processVol(vol, parent, phylvl, displayMode) :
    #GDMLShared.setTrace(True)
    from .GDMLObjects import checkMaterial
    colour = None
    for aux in vol.findall('auxiliary') : # could be more than one auxiliary
        if aux is not None :
           #print('auxiliary')
           aType = aux.get('auxtype')
           aValue = aux.get('auxvalue')
           if aValue is not None :
              if aType == 'SensDet' :
                 parent.addProperty("App::PropertyString","SensDet","Base", \
                       "SensDet").SensDet = aValue
              if aType == 'Color' :
                 #print('auxtype Color')
                 #print(aValue)
                 #print(aValue[1:3])
                 #print(int(aValue[1:3],16))
                 if aValue[0] == '#' :   # Hex values
                    #colour = (int(aValue[1:3],16)/256, \
                    #          int(aValue[3:5],16)/256, \
                    #          int(aValue[5:7],16)/256, \
                    #          int(aValue[7:],16)/256)
                    lav = len(aValue)
                    #print(f'Aux col len : {lav}')
                    if lav == 7 :
                       try : 
                          colour = tuple(int(aValue[n:n+2],16)/256 for \
                                   n in range(1,7,2))+(0)
                       except :
                          print("Invalid Colour definition #RRGGBB")

                    elif lav == 9 :
                       try :
                          colour = tuple(int(aValue[n:n+2],16)/256 for \
                                   n in range(1,9,2))
                       except :
                          print("Invalid Colour definition #RRGGBBAA")
                    else :
                       print("Invalid Colour definition")
                    #print('Aux colour set'+str(colour))
                 else :
                    colDict ={'Black'   :(0.0, 0.0, 0.0, 0.0), \
                                'Blue'    :(0.0, 0.0, 1.0, 0.0), \
                                'Brown'   :(0.45, 0.25, 0.0, 0.0), \
                                'Cyan'    :(0.0, 1.0, 1.0, 0.0), \
                                'Gray'    :(0.5, 0.5, 0.5, 0.0), \
                                'Grey'    :(0.5, 0.5, 0.5, 0.0), \
                                'Green'   :(0.0, 1.0, 0.0, 0.0), \
                                'Magenta' :(1.0, 0.0, 1.0, 0.0), \
                                'Red'     :(1.0, 0.0, 0.0, 0.0), \
                                'White'   :(1.0, 1.0, 1.0, 0.0), \
                                'Yellow'  :(1.0, 1.0, 0.0, 0.0)  }
                    colour = colDict.get(aValue,(0.0, 0.0, 0.0, 0.0))
                    #print(colour)
        else :
           print('No auxvalue')
    coloref = GDMLShared.getRef(vol,"colorref")
    if coloref is not None :
       colour = getColour(coloref)
    solidref = GDMLShared.getRef(vol,"solidref")
    #print(f"solidref : {solidref}")
    name = vol.get("name")
    if solidref is not None :
       solid  = solids.find("*[@name='%s']" % solidref )
       if solid is not None :
          GDMLShared.trace(solid.tag)
          # Material is the materialref value
          # need to add default
          material = GDMLShared.getRef(vol,"materialref")
          if material is not None :
             if checkMaterial(material) == True :
                obj = createSolid(parent,solid,material,colour,0,0,0,None, \
                                 displayMode)
             else :
                print('ERROR - Material : '+material+ \
                         ' Not defined for solid : '  +str(solid)+ \
                         ' Volume : '+name)
                return None
          else :
             print('ERROR - Materialref Not defined for solid : ' \
                         +str(solid)+' Volume : '+name)
             return None
       else :
           print('ERROR - Solid  : '+solidref+' Not defined')
           return None
    else :
       print('ERROR - solidref Not defined in Volume : '+name)
       return None 
    # Volume may or maynot contain physvol's
    displayMode = 1
    for pv in vol.findall("physvol") :
        # Need to clean up use of phylvl flag
        # create solids at pos & rot in physvols
        #if phylvl < 1 :
        if phylvl < 0 :
           #if phylvl >= 0 :
           #   phylvl += 1 
           # If negative always parse otherwise increase level    
           parsePhysVol(True,parent,pv,phylvl,displayMode)

        else :  # Just Add to structure 
            volRef = GDMLShared.getRef(pv,"volumeref")
            print('volRef : '+str(volRef))
            nx, ny, nz = GDMLShared.getPosition(pv)
            nrot = GDMLShared.getRotation(pv)
            cpyNum = pv.get('copynumber')
            #print('copyNumber : '+str(cpyNum))
            # Is volRef already defined
            linkObj = FreeCAD.ActiveDocument.getObject(volRef)
            if linkObj is not None :
               # already defined so link
               #print('Already defined')
               try : 
                  part = parent.newObject("App::Link",volRef)
                  part.LinkedObject = linkObj
                  part.Label = "Link_"+part.Name
               except:
                  print(volRef+' : volref not supported with FreeCAD 0.18')
            else :
               # Not already defined so create
               print('Is new : '+volRef)
               part = parent.newObject("App::Part",volRef)
               part.Label = "NOT_Expanded_"+part.Name
            part.addProperty("App::PropertyString","VolRef","GDML", \
                   "volref name").VolRef = volRef
            if cpyNum is not None :
               part.addProperty("App::PropertyInteger","CopyNumber", \
                     "GDML", "copynumber").CopyNumber = int(cpyNum)
            base = FreeCAD.Vector(nx,ny,nz)
            part.Placement = GDMLShared.processPlacement(base,nrot)

def expandVolume(parent,name,phylvl,displayMode) :
    import FreeCAD as App
    # also used in ScanCommand
    #GDMLShared.setTrace(True)
    GDMLShared.trace("expandVolume : "+name)
    vol = structure.find("volume[@name='%s']" % name )
    if vol is not None : # If not volume test for assembly
       processVol(vol,parent,phylvl,displayMode)

    else :
       asm = structure.find("assembly[@name='%s']" % name)
       if asm is not None :
          print("Assembly : "+name)
          for pv in asm.findall("physvol") :
              #obj = parent.newObject("App::Part",name)
              parsePhysVol(False,parent,pv,phylvl,displayMode)
       else :
           print(name+' is Not a defined Volume or Assembly') 

def getItem(element, attribute) :
    # returns None if not found
    return element.get(attribute)

def processIsotopes(isotopesGrp) :
    from .GDMLObjects import GDMLisotope, ViewProvider
    for isotope in materials.findall('isotope') :
        N = int(isotope.get('N'))
        Z = int(float(isotope.get('Z')))    # annotated.gdml file has Z=8.0 
        name = isotope.get('name')
        isObj = isotopesGrp.newObject("App::DocumentObjectGroupPython",name)
        GDMLisotope(isObj,name,N,Z)
        atom = isotope.find('atom')
        if atom is not None :
           unit = atom.get('unit')
           if unit is not None :
              isObj.addProperty('App::PropertyString','unit','Unit').unit = unit
           type = atom.get('type')           
           if type is not None :
              isObj.addProperty('App::PropertyString','type','Type').type = type
           if atom.get('value') is not None :
              value = GDMLShared.getVal(atom,'value')
              isObj.addProperty('App::PropertyFloat','value','Value').value = value

def processElements(elementsGrp) :
    from .GDMLObjects import GDMLelement, GDMLfraction
    for element in materials.findall('element') :
        name = element.get('name')
        print('element : '+name)
        elementObj = elementsGrp.newObject("App::DocumentObjectGroupPython",  \
                     name)
        Z = element.get('Z')
        if (Z is not None ) :
           elementObj.addProperty("App::PropertyInteger","Z",name).Z=int(float(Z))
        N = element.get('N')
        if (N is not None ) :
           elementObj.addProperty("App::PropertyInteger","N",name).N=int(N)
            
        formula = element.get('formula')
        if (formula is not None ) :
           elementObj.addProperty("App::PropertyString","formula",name). \
                   formula = formula
            
        atom = element.find('atom') 
        if atom is not None :
           unit = atom.get('unit')
           if unit is not None :
              elementObj.addProperty("App::PropertyString","atom_unit",name). \
                                      atom_unit = unit
           a_value = GDMLShared.getVal(atom,'value')
           if a_value is not None :
              elementObj.addProperty("App::PropertyFloat","atom_value",name). \
                                      atom_value = a_value

        GDMLelement(elementObj,name)
        if( len(element.findall('fraction'))>0 ):
           for fraction in element.findall('fraction') :
               ref = fraction.get('ref')
               print(f'ref {ref}')
               #n = float(fraction.get('n'))
               n = GDMLShared.getVal(fraction,'n')
               print(f'n {n}')
               #fractObj = elementObj.newObject("App::FeaturePython",ref)
               fractObj = elementObj.newObject("App::DocumentObjectGroupPython",ref)
               GDMLfraction(fractObj,ref,n)
               fractObj.Label = ref+' : ' + '{0:0.3f}'.format(n)
        elif(len(element.findall('composite'))>0 ):
           for composite in element.findall('composite') :
               ref = composite.get('ref')
               n = int(composite.get('n'))
               #fractObj = elementObj.newObject("App::FeaturePython",ref)
               compositeObj = elementObj.newObject("App::DocumentObjectGroupPython",ref)
               GDMLcomposite(compositeObj,ref,n)
               compositeObj.Label = ref+' : ' + str(n) 

def processMaterials(materialGrp) :
    from .GDMLObjects import GDMLmaterial, GDMLfraction, GDMLcomposite, \
                            MaterialsList

    for material in materials.findall('material') :
        name = material.get('name')
        #print(name)
        if name is None :
           print("Missing Name")
        else :
           MaterialsList.append(name)
           materialObj = materialGrp.newObject("App::DocumentObjectGroupPython", \
                      name)
           GDMLmaterial(materialObj,name)
           formula = material.get('formula')
           if formula is not None :
              materialObj.addProperty("App::PropertyString",'formula', \
                      name).formula = formula
           D = material.find('D')
           if D is not None :
              Dunit = getItem(D,'unit')
              #print(Dunit)
              if Dunit is not None :
                    materialObj.addProperty("App::PropertyString",'Dunit', \
                                'GDMLmaterial','Dunit').Dunit = Dunit
              Dvalue = GDMLShared.getVal(D,'value')
              if Dvalue is not None :
                 materialObj.addProperty("App::PropertyFloat", \
                         'Dvalue','GDMLmaterial','value').Dvalue = Dvalue

           Z = material.get('Z')
           if Z is not None :
              materialObj.addProperty("App::PropertyString",'Z',name).Z = Z
           atom = material.find('atom')
           if atom is not None :
              #print("Found atom in : "+name) 
              aUnit = atom.get('unit')
              if aUnit is not None :
                 materialObj.addProperty("App::PropertyString",'atom_unit', \
                         name).atom_unit = aUnit
              aValue = GDMLShared.getVal(atom,'value')
              if aValue is not None :
                 materialObj.addProperty("App::PropertyFloat",'atom_value', \
                         name).atom_value = aValue
 
           T = material.find('T')
           if T is not None :
              Tunit = T.get('unit')
              if Tunit is None :	# Default Kelvin
                 Tunit = 'K'
              materialObj.addProperty("App::PropertyString",'Tunit','GDMLmaterial',"T ZZZUnit").Tunit = Tunit
              Tvalue = GDMLShared.getVal(T,'value')
           MEE = material.find('MEE')
           if MEE is not None :
              Munit = MEE.get('unit')
              Mvalue = GDMLShared.getVal(MEE,'value')
              materialObj.addProperty("App::PropertyString",'MEEunit','GDMLmaterial','MEE unit').MEEunit = Munit
              materialObj.addProperty("App::PropertyFloat",'MEEvalue','GDMLmaterial','MEE value').MEEvalue = Mvalue
           for fraction in material.findall('fraction') :
               n = GDMLShared.getVal(fraction,'n')
               #print(n)
               ref = fraction.get('ref')
               #print('fraction : '+ref)
               fractionObj = materialObj.newObject('App::DocumentObjectGroupPython', ref)
               #print('fractionObj Name : '+fractionObj.Name)
               GDMLfraction(fractionObj,ref,n)
               # problems with changing labels if more than one
               #
               fractionObj.Label = ref+' : '+'{0:0.3f}'.format(n)
               #print('Fract Label : ' +fractionObj.Label)

           for composite in material.findall('composite') :
               #print('Composite')
               n = int(composite.get('n'))
               #print('n = '+str(n))
               ref = composite.get('ref')
               #print('ref : '+ref)
               compObj = materialObj.newObject("App::DocumentObjectGroupPython", \
                                                 ref)
               GDMLcomposite(compObj,'comp',n,ref)
               # problems with changing labels if more than one
               #
               #print('Comp Label : ' +compObj.Label)
               compObj.Label = ref +' : '+str(n)
               #print('Comp Label : ' +compObj.Label)

    GDMLShared.trace("Materials List :")
    GDMLShared.trace(MaterialsList)

def setupEtree(filename) :
    # modifs
    #before from lxml import etree
    print('Parse : '+filename)
    try:
       from lxml import etree
       FreeCAD.Console.PrintMessage("running with lxml.etree \n")
       parser = etree.XMLParser(resolve_entities=True)
       root= etree.parse(filename, parser=parser)
       #print('error log')
       #print(parser.error_log)

    except ImportError:
       try:
           import xml.etree.ElementTree as etree
           FreeCAD.Console.PrintMessage("running with etree.ElementTree (import limitations)\n")
           FreeCAD.Console.PrintMessage(" for full import add lxml library \n")
           tree = etree.parse(filename)
           FreeCAD.Console.PrintMessage(tree)
           FreeCAD.Console.PrintMessage('\n')
           root = tree.getroot()

       except ImportError:
           print('pb xml lib not found')
           sys.exit()
    # end modifs 
    return etree, root

def processXML(doc,filename):
    print('process XML : '+filename)
    etree, root = setupEtree(filename)
    #etree.ElementTree(root).write("/tmp/test2", 'utf-8', True)
    processMaterialsDocSet(doc, root)

def processPhysVolFile(doc, parent, fname):
    print('Process physvol file import')
    print(pathName)
    filename = os.path.join(pathName,fname)
    print('Full Path : '+filename)
    etree, root = setupEtree(filename)
    #etree.ElementTree(root).write("/tmp/test2", 'utf-8', True)
    processMaterialsDocSet(doc, root)
    print('Now process Volume')
    define = root.find('define')
    #print(str(define))
    GDMLShared.setDefine(define)
    if define is not None :
       processDefines(root,doc)
    global solids
    solids = root.find('solids')
    #print(str(solids))
    structure = root.find('structure')
    if structure is None :
       vol = root.find('volume')
    else :
       vol = structure.find('volume')
    #print(str(vol))
    if vol is not None :
       vName = vol.get('name')
       if vName is not None :
          print(f'Vol in Physvol file = Vol{vName}')
          part = parent.newObject("App::Part",vName)
          #expandVolume(None,vName,-1,1)
          processVol(vol,part,-1,1)

def processGEANT4(doc,filename):
    print('process GEANT4 Materials : '+filename)
    etree, root = setupEtree(filename)
    #etree.ElementTree(root).write("/tmp/test2", 'utf-8', True)
    materials = doc.getObject('Materials')
    if materials is None :
       materials = doc.addObject("App::DocumentObjectGroupPython","Materials")
    geant4Grp = materials.newObject("App::DocumentObjectGroupPython","Geant4")
    processMaterialsG4(geant4Grp,root)

def processMaterialsDocSet(doc, root) :
    print('Process Materials')
    global materials
    materials = root.find('materials')
    if materials is not None :
       try :
          isotopesGrp = FreeCAD.ActiveDocument.Isotopes
       except :
          isotopesGrp = doc.addObject("App::DocumentObjectGroupPython","Isotopes")
       processIsotopes(isotopesGrp)
       try :
          elementsGrp = FreeCAD.ActiveDocument.Elements
       except :
          elementsGrp = doc.addObject("App::DocumentObjectGroupPython","Elements")
       processElements(elementsGrp)
       try :
          materialsGrp = FreeCAD.ActiveDocument.Materials
       except :
          materialsGrp = doc.addObject("App::DocumentObjectGroupPython","Materials")
       processMaterials(materialsGrp)


def processMaterialsG4(G4rp, root) :
    global materials
    materials = root.find('materials')
    if materials is not None :
       isotopesGrp = G4rp.newObject("App::DocumentObjectGroupPython","G4Isotopes")
       processIsotopes(isotopesGrp)
       elementsGrp = G4rp.newObject("App::DocumentObjectGroupPython","G4Elements")
       processElements(elementsGrp)
       materialsGrp = G4rp.newObject("App::DocumentObjectGroupPython","G4Materials")
       processMaterials(materialsGrp)

def processDefines(root, doc) :
    GDMLShared.trace("Call set Define")
    GDMLShared.setDefine(root.find('define'))
    GDMLShared.processConstants(doc)
    GDMLShared.processVariables(doc)
    GDMLShared.processQuantities(doc)
    GDMLShared.processPositions(doc)
    GDMLShared.processExpression(doc)

def processGDML(doc,filename,prompt,initFlg):
    # Process GDML 

    import time
    from . import GDMLShared
    from . import GDMLObjects
    #GDMLShared.setTrace(True)

    phylvl = -1 # Set default
    if FreeCAD.GuiUp :
       from . import GDMLCommands
       if prompt :
          from   .GDMLQtDialogs import importPrompt
          dialog = importPrompt()
          dialog.exec_()
          #FreeCADGui.Control.showDialog(dialog)
          #if dialog.retStatus == 1 :
          #   print('Import')
          #   phylvl = -1

          if dialog.retStatus == 2 :
             print('Scan Vol') 
             phylvl = 0 

          params = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/GDML")
          #GDMLShared.setTrace(printverbose = params.GetBool('printVerbose',False))
   
    else :
        # For Non Gui default Trace to on
        GDMLShared.setTrace(True)

    print("Print Verbose : "+ str(GDMLShared.getTrace()))

    FreeCAD.Console.PrintMessage('Import GDML file : '+filename+'\n')
    FreeCAD.Console.PrintMessage('ImportGDML Version 1.5\n')
    startTime = time.perf_counter()
    
    global pathName
    pathName = os.path.dirname(os.path.normpath(filename))
    FilesEntity = False

    global setup, define, materials, solids, structure, extension
  
    # Add files object so user can change to organise files
    #  from GDMLObjects import GDMLFiles, ViewProvider
    #  myfiles = doc.addObject("App::FeaturePython","Export_Files")
    #myfiles = doc.addObject("App::DocumentObjectGroupPython","Export_Files")
    #GDMLFiles(myfiles,FilesEntity,sectionDict)

    # Reserve place for Colour Map at start of Document
    #FreeCAD.ActiveDocument.addObject("App::FeaturePython","ColourMap")

    etree, root = setupEtree(filename)
    setup     = root.find('setup')
    extension = root.find('extension')
    define    = root.find('define')
    if define is not None :
       processDefines(root,doc)
       GDMLShared.trace(setup.attrib)

    processMaterialsDocSet(doc,root)
    processGEANT4(doc,joinDir("Resources/Geant4Materials.xml"))

    solids    = root.find('solids')
    structure = root.find('structure')

    world = GDMLShared.getRef(setup,"world")
    part =doc.addObject("App::Part",world)
    parseVolume(part,world,phylvl,3)
    # If only single volume reset Display Mode
    if len(part.OutList) == 2 and initFlg == False :
        worldGDMLobj = part.OutList[1]
        worldGDMLobj.ViewObject.DisplayMode = 'Shaded'
    FreeCAD.ActiveDocument.recompute()
    if FreeCAD.GuiUp :
       FreeCADGui.SendMsgToActiveView("ViewFit")
    FreeCAD.Console.PrintMessage('End processing GDML file\n')
    endTime = time.perf_counter()
    #print(f'time : {endTime - startTime:0.4f} seconds')
    FreeCAD.Console.PrintMessage(f'time : {endTime - startTime:0.4f} seconds\n')
