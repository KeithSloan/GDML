# Shared file
# single access to globals
# anything requiring access to globals needs to call a function in this file
# anything needing to call eval needs to be in this file
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

from math import *
import FreeCAD, Part

global define

global printverbose
printverbose = False

def setTrace(flag) :
    print('Trace set to : '+str(flag))
    global printverbose
    printverbose = flag

def getTrace() :
    global printverbose
    #print('Get Trace : '+str(printverbose))
    return(printverbose)

def trace(s):
    if printverbose == True : print(s)
    return

def setDefine(val) :
    #print("Set Define")
    global define
    define = val

def processConstants(doc):
    # all of math must be imported at global level
    trace("Process Constants")
    constantGrp = doc.addObject("App::DocumentObjectGroupPython","Constants")
    from .GDMLObjects import GDMLconstant
    for cdefine in define.findall('constant') :
        #print cdefine.attrib
        name  = str(cdefine.attrib.get('name'))
        trace('name : '+name)
        value = cdefine.attrib.get('value')
        trace('value : '+ value)
        #constDict[name] = value
        trace(name)
        #print(dir(name))
        globals()[name] = eval(value)
        constObj = constantGrp.newObject("App::DocumentObjectGroupPython", \
                     name)
        GDMLconstant(constObj,name,value)
    #print("Globals")
    #print(globals())


def processPosition(doc):
    # need to be done ?
    trace("Position Not processed & Displayed")

def processExpression(doc):
    # need to be done ?
    trace("Expressions Not processed & Displayed")

def processRotation(doc):
    # need to be done ?
    trace("Rotations Not processed & Displayed")

def processQuantity(doc):
    # need to be done 
    trace("Process quantity (not taken into account in this version)" )

def getVal(ptr,var,vtype = 1) :
    # vtype 1 - float vtype 2 int
    # get value for var variable var
    # all of math must be imported at global level
    #print ptr.attrib
    # is the variable defined in passed attribute
    if var in ptr.attrib :
       # if yes get its value
       vval = ptr.attrib.get(var)
       trace("vval : "+str(vval))
       if vval[0] == '&' :  # Is this refering to an HTML entity constant
         chkval = vval[1:]
       else :
          chkval = vval
       # check if defined as a constant
       #if vval in constDict :
       #   c = constDict.get(vval)
       #   #print c
       #   return(eval(c))
       #
       #else :
       trace("chkval : "+str(chkval))
       if vtype == 1 :
          ret = float(eval(chkval))
       else :
          ret = int(eval(chkval))
       trace('return value : '+str(ret))
       return(ret)
    else :
       if vtype == 1 :
          return (0.0)
       else :
          return(0)

# get ref e.g name world, solidref, materialref
def getRef(ptr, name) :
    wrk = ptr.find(name)
    if wrk != None :
       ref = wrk.get('ref')
       trace(name + ' : ' + ref)
       return ref
    return wrk

def getMult(fp) :
    # Watch for unit and lunit
    if hasattr(fp,'lunit') :
        trace('lunit : '+fp.lunit)
        unit = fp.lunit
    elif hasattr(fp,'unit') :
        trace('unit : '+fp.unit)
        unit = fp.unit
    else :
        return 1
    if unit == 'mm' : return(1)
    elif unit == 'cm' : return(10)
    elif unit == 'm' : return(1000)
    elif unit == 'um' : return(0.001)
    elif unit == 'nm' : return(0.000001)
    elif unit == 'dm' : return(100)
    elif unit == 'm' : return(1000)
    elif unit == 'km' : return(1000000)
    print('unit not handled : '+lunit)

def getDegrees(flag, r) :
    import math
    if flag == True :
       return r * 180/math.pi
    else :
       return r

def getRadians(flag,r) :
    import math
    if flag == True :
        return r
    else :
        return r * math.pi / 180

def processPlacement(base,rot) :
    #setTrace(True)
    #trace('processPlacement')
    # Different Objects will have adjusted base GDML-FreeCAD
    # rot is rotation or None if default 
    # set rotation matrix
    noRotate = FreeCAD.Placement(base,FreeCAD.Rotation(0,0,0))
    if rot == None :
        return noRotate
    
    else :
        trace("Rotation : ")
        trace(rot.attrib)
        x = y = z = 0

        if 'name' in rot.attrib :
            if rot.attrib['name'] == 'identity' :
                trace('identity')
                return noRotate

        radianFlg = True
        if 'unit' in rot.attrib :
            #print(rot.attrib['unit'][:3])
            if rot.attrib['unit'][:3] == 'deg' :
                radianFlg = False

        if 'x' in rot.attrib :
            trace('x : '+rot.attrib['x'])
            #print(eval('HALFPI'))
            trace(eval(rot.attrib['x']))
            x = getDegrees(radianFlg,float(eval(rot.attrib['x'])))
            trace('x deg : '+str(x))

        if 'y' in rot.attrib :
            trace('y : '+rot.attrib['y'])
            y = getDegrees(radianFlg,float(eval(rot.attrib['y'])))
            trace('y deg : '+str(y))
        
        if 'z' in rot.attrib :
            trace('z : '+rot.attrib['z'])
            z = getDegrees(radianFlg,float(eval(rot.attrib['z'])))
            trace('z deg : '+str(z))

        rotX = FreeCAD.Rotation(FreeCAD.Vector(1,0,0), -x)
        rotY = FreeCAD.Rotation(FreeCAD.Vector(0,1,0), -y)
        rotZ = FreeCAD.Rotation(FreeCAD.Vector(0,0,1), -z)

        rot = rotX.multiply(rotY).multiply(rotZ)
        #rot = rotX
        c_rot =  FreeCAD.Vector(0,0,0)  # Center of rotation
        return FreeCAD.Placement(base, rot,  c_rot)


def getPositionFromAttrib(pos) :
    #print(pos.attrib)
    #if hasattr(pos.attrib, 'unit') :        # Note unit NOT lunit
    mul = getMult(pos)
    px = mul * getVal(pos,'x')
    py = mul * getVal(pos,'y')
    pz = mul * getVal(pos,'z')
    return px, py, pz     

# Return x,y,z from position definition 
def getElementPosition(xmlElem) :
    # get Position from local element 
    #setTrace(True)
    trace("Get Element Position : ")
    pos = xmlElem.find("position")
    if pos != None :
        trace(pos.attrib)
        return(getPositionFromAttrib(pos))
    else :
       return 0,0,0

def getDefinedPosition(name) :
    # get Position from define section 
    pos = define.find("position[@name='%s']" % name )
    if pos != None :
        trace(pos.attrib)
        return(getPositionFromAttrib(pos))
    else :
       return 0,0,0

def getPosition(xmlEntity) :
    # Get position via reference
    #setTrace(True)
    trace('GetPosition via Reference if any')
    posName = getRef(xmlEntity,"positionref")
    if posName is not None :
       trace("positionref : "+posName)
       return(getDefinedPosition(posName))
    else :
       return(getElementPosition(xmlEntity))

def testPosition(xmlEntity,px,py,pz) :
    posName = getRef(xmlEntity,"positionref")
    if posName is not None :
       trace("positionref : "+posName)
       return(getDefinedPosition(posName))
    pos = xmlEntity.find("position")
    if pos != None :
        trace(pos.attrib)
        return(getPositionFromAttrib(pos))
    else :
       return px,py,pz 

def getDefinedRotation(name) :
    # Just get defintion - used by parseMultiUnion passed to create solids
    return(define.find("rotation[@name='%s']" % name ))

def getRotation(xmlEntity) :
    trace('GetRotation')
    rotref = getRef(xmlEntity,"rotationref")
    trace(rotref)
    if rotref is not None :
       rot = define.find("rotation[@name='%s']" % rotref )
    else :
       rot = xmlEntity.find("rotation")
    if rot != None :
       trace(rot.attrib)
    return rot

def getRotFromRefs(ptr) :
    printverbose = True
    trace("getRotFromRef")
    rot = define.find("rotation[@name='%s']" % getRef(ptr,'rotationref'))
    if rot != None :
        trace(rot.attrib)
    return rot

def getDefinedVector(solid, v) :
    global define
    #print('get Defined Vector : '+v)
    name = solid.get(v)
    pos = define.find("position[@name='%s']" % name)
    #print(pos.attrib)
    x = getVal(pos,'x')
    y = getVal(pos,'y')
    z = getVal(pos,'z')
    return(FreeCAD.Vector(x,y,z))

def getVertex(v):
    global define
    trace("Vertex")
    #print(dir(v))
    pos = define.find("position[@name='%s']" % v)
    #print("Position")
    #print(dir(pos))
    x = getVal(pos,'x')
    trace('x : '+str(x))
    y = getVal(pos,'y')
    trace('y : '+str(y))
    z = getVal(pos,'z')
    trace('z : '+str(z))
    return(FreeCAD.Vector(x,y,z))

def triangle(v1,v2,v3) :
    # passsed vertex return face
    w1 = Part.makePolygon([v1,v2,v3,v1])
    f1 = Part.Face(w1)
    return(f1)

def quad(v1,v2,v3,v4) :
    # passsed vertex return face
    w1 = Part.makePolygon([v1,v2,v3,v4,v1])
    f1 = Part.Face(w1)
    return(f1)

