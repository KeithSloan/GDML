# Shared file
# single access to globals
# anything requiring access to globals needs to call a function in this file
# anything needing to call eval needs to be in this file
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

from math import *
import FreeCAD, Part
from PySide import QtCore, QtGui

# from lxml import etree as ET

global define
global tracefp

global printverbose
printverbose = False


def setTrace(flag):
    global tracefp
    print("Trace set to : " + str(flag))
    global printverbose
    printverbose = flag
    if flag is True:
        tracePath = FreeCAD.getUserAppDataDir()
        tracefp = open(tracePath + "FC-trace", "w")
        print("Trace path : " + tracePath)


def getTrace():
    global printverbose
    # print('Get Trace : '+str(printverbose))
    return printverbose


def trace(s):
    global tracefp
    if printverbose is True:
        print(s)
        print(s, file=tracefp)
        tracefp.flush()
    return


def errorDialog(msg, title="Warning", type=2):
    # Create a simple dialog QMessageBox
    # type indicates the icon used: one of QtGui.QMessageBox.{NoIcon, Information, Warning, Critical, Question}
    typeDict = {
        0: QtGui.QMessageBox.NoIcon,
        1: QtGui.QMessageBox.Information,
        2: QtGui.QMessageBox.Warning,
        3: QtGui.QMessageBox.Critical,
        4: QtGui.QMessageBox.Question,
    }
    diag = QtGui.QMessageBox(Dict(type), title, msg)
    diag.setWindowModality(QtCore.Qt.ApplicationModal)
    diag.exec_()


def getFloatVal(expr):
    try:
        ret = float(eval(expr))
    except:
        # eval might fail on constants with leading zeros in python3
        # so we try direct conversion
        try:
            ret = float(expr)
        except:
            ret = 0.0
            print("Illegal float value: {}".format(expr))
    return ret


def setDefine(val):
    # print("Set Define")
    global define
    define = val


def processConstants(doc):
    # all of math must be imported at global level
    # setTrace(True)
    trace("Process Constants")
    constantGrp = doc.getObject("Constants")
    if constantGrp is None:
        constantGrp = doc.addObject(
            "App::DocumentObjectGroupPython", "Constants"
        )
    from .GDMLObjects import GDMLconstant

    for cdefine in define.findall("constant"):
        # print cdefine.attrib
        name = str(cdefine.attrib.get("name"))
        trace("name : " + name)
        value = cdefine.attrib.get("value")
        trace("value : " + value)
        # constDict[name] = value
        # trace(name)
        # print(dir(name))
        try:
            globals()[name] = eval(value)
        except:  # eg 5*cm
            globals()[name] = value
        constObj = constantGrp.newObject(
            "App::DocumentObjectGroupPython", name
        )
        GDMLconstant(constObj, name, value)

    # print("Globals")
    # print(str(globals()))


def processVariables(doc):
    # all of math must be imported at global level
    trace("Process Variables")
    variablesGrp = doc.getObject("Variables")
    if variablesGrp is None:
        variablesGrp = doc.addObject(
            "App::DocumentObjectGroupPython", "Variables"
        )
    from .GDMLObjects import GDMLconstant
    from .GDMLObjects import GDMLvariable

    globals()["false"] = False
    globals()["true"] = True

    for cdefine in define.findall("variable"):
        # print cdefine.attrib
        name = str(cdefine.attrib.get("name"))
        trace("name : " + name)
        value = cdefine.attrib.get("value")
        trace("value : " + value)
        # constDict[name] = value
        trace(name)
        # print(dir(name))
        # print('Name  : '+name)
        try:
            globals()[name] = eval(value)
            # print('Value : '+value)
        except:
            globals()[name] = value
            # print('Value String : '+value)
        variableObj = variablesGrp.newObject(
            "App::DocumentObjectGroupPython", name
        )
        GDMLvariable(variableObj, name, value)
    # print("Globals")
    # print(str(globals()))


def processQuantities(doc):
    # all of math must be imported at global level
    trace("Process Quantitities")
    quantityGrp = doc.getObject("Quantities")
    if quantityGrp is None:
        quantityGrp = doc.addObject(
            "App::DocumentObjectGroupPython", "Quantities"
        )
    from .GDMLObjects import GDMLquantity

    for cdefine in define.findall("quantity"):
        # print cdefine.attrib
        name = str(cdefine.attrib.get("name"))
        trace("name : " + name)
        type = cdefine.attrib.get("type")
        trace("type : " + type)
        unit = cdefine.attrib.get("unit")
        trace("unit : " + unit)
        value = cdefine.attrib.get("value")
        trace("value : " + value)
        # constDict[name] = value
        trace(name)
        # print(dir(name))
        # print('Name  : '+name)
        try:
            globals()[name] = eval(value)
            # print('Value : '+value)
        except:
            globals()[name] = value
            # print('Value String : '+value)
        quantityObj = quantityGrp.newObject(
            "App::DocumentObjectGroupPython", name
        )
        GDMLquantity(quantityObj, name, type, unit, value)
    # print("Globals")
    # print(str(globals()))


def processPositions(doc):
    print("Process Positions")
    # need to be done ?
    global positions
    positions = {}
    for elem in define.findall("position"):
        atts = elem.attrib
        if "unit" in atts:
            unit = atts["unit"]
        else:
            unit = "mm"
        if "x" in atts:
            x = getFloatVal(atts["x"])
        else:
            x = 0
        if "y" in atts:
            y = getFloatVal(atts["y"])
        else:
            y = 0
        if "z" in atts:
            z = getFloatVal(atts["z"])
        else:
            z = 0

        positions[atts["name"]] = {"unit": unit, "x": x, "y": y, "z": z}

    trace("Positions processed")


def processExpression(doc):
    # need to be done ?
    trace("Expressions Not processed & Displayed")


def processRotation(doc):
    # need to be done ?
    trace("Rotations Not processed & Displayed")


def getVal(ptr, var, default=0):
    # all of math must be imported at global level
    # print ptr.attrib
    # is the variable defined in passed attribute
    if var in ptr.attrib:
        # if yes get its value
        vval = ptr.attrib.get(var)
        trace(var + " : " + str(vval))
        if vval[0] == "&":  # Is this referring to an HTML entity constant
            chkval = vval[1:]
        else:
            chkval = vval
        trace("chkval : " + str(chkval))
        try:
            ret = float(eval(chkval))
        except:
            try:
                ret = float(chkval)
            except:
                print("Illegal float: {}" % chkval)
                ret = 0.0

        trace("return value : " + str(ret))
        return ret
    return default


# get ref e.g name world, solidref, materialref


def getRef(ptr, name):
    wrk = ptr.find(name)
    if wrk is not None:
        ref = wrk.get("ref")
        trace(name + " : " + ref)
        return ref
    return wrk


def getMult(fp):
    unit = "mm"  # set default
    # Watch for unit and lunit
    # print('getMult : '+str(fp))
    if hasattr(fp, "lunit"):
        trace("lunit : " + fp.lunit)
        unit = fp.lunit
    elif hasattr(fp, "unit"):
        trace("unit : " + fp.unit)
        unit = fp.unit
    elif hasattr(fp, "attrib"):
        if "unit" in fp.attrib:
            unit = fp.attrib["unit"]
        elif "lunit" in fp.attrib:
            unit = fp.attrib["lunit"]
    else:
        return 1

    unitsDict = {
        "mm": 1,
        "cm": 10,
        "m": 1000,
        "um": 0.001,
        "nm": 0.000001,
        "dm": 100,
        "m": 1000,
        "km": 1000000,
    }
    if unit in unitsDict:
        return unitsDict[unit]

    print("unit not handled : " + unit)


def getDegrees(flag, r):
    import math

    if flag is True:
        return r * 180 / math.pi
    else:
        return r


def getRadians(flag, r):
    import math

    if flag is True:
        return r
    else:
        return r * math.pi / 180


def processPlacement(base, rot):
    # setTrace(True)
    # trace('processPlacement')
    # Different Objects will have adjusted base GDML-FreeCAD
    # rot is rotation or None if default
    # set rotation matrix
    # print('process Placement : '+str(base))
    if rot is None:
        return FreeCAD.Placement(base, FreeCAD.Rotation(0, 0, 0, 1))

    else:
        trace("Rotation : ")
        trace(rot.attrib)
        x = y = z = 0

        if "name" in rot.attrib:
            if rot.attrib["name"] == "identity":
                trace("identity")
                return FreeCAD.Placement(base, FreeCAD.Rotation(0, 0, 0, 1))

        radianFlg = True
        if "unit" in rot.attrib:
            # print(rot.attrib['unit'][:3])
            if rot.attrib["unit"][:3] == "deg":
                radianFlg = False

        if "x" in rot.attrib:
            trace("x : " + rot.attrib["x"])
            # print(eval('HALFPI'))
            trace(eval(rot.attrib["x"]))
            x = getDegrees(radianFlg, float(eval(rot.attrib["x"])))
            trace("x deg : " + str(x))

        if "y" in rot.attrib:
            trace("y : " + rot.attrib["y"])
            y = getDegrees(radianFlg, float(eval(rot.attrib["y"])))
            trace("y deg : " + str(y))

        if "z" in rot.attrib:
            trace("z : " + rot.attrib["z"])
            z = getDegrees(radianFlg, float(eval(rot.attrib["z"])))
            trace("z deg : " + str(z))

        rotX = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), -x)
        rotY = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), -y)
        rotZ = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), -z)

        rot = rotX * rotY * rotZ
        # rot = rotX.multiply(rotY).multiply(rotZ)
        # rot = rotX
        # c_rot =  FreeCAD.Vector(0,0,0)  # Center of rotation
        # print('base : '+str(base))
        # print('rot  : '+str(rot))
        # return FreeCAD.Placement(base, rot,  c_rot)

        # placement = FreeCAD.Placement(base, FreeCAD.Rotation(-x,-y,-z))
        # placement = FreeCAD.Placement(base, FreeCAD.Rotation(-z,-y,-x), \
        #            base)
        placement = FreeCAD.Placement(base, FreeCAD.Rotation(rot))
        # print('placement : '+str(placement))
        return placement


def getPositionFromAttrib(pos):
    # print('getPositionFromAttrib')
    # print('pos : '+str(ET.tostring(pos)))
    # print(pos.attrib)
    # if hasattr(pos.attrib, 'unit') :        # Note unit NOT lunit
    # if hasattr(pos.attrib,'name') :
    #   name = pos.get('name')
    #   if name == 'center' :
    #      return(0,0,0)
    mul = getMult(pos)
    px = mul * getVal(pos, "x")
    py = mul * getVal(pos, "y")
    pz = mul * getVal(pos, "z")
    return px, py, pz


def getPositionFromDict(pos):
    # print('getPositionFromAttrib')
    # print('pos : '+str(ET.tostring(pos)))
    # print(pos.attrib)
    # if hasattr(pos.attrib, 'unit') :        # Note unit NOT lunit
    # if hasattr(pos.attrib,'name') :
    #   name = pos.get('name')
    #   if name == 'center' :
    #      return(0,0,0)
    unit = pos["unit"]
    mul = 1

    unitsDict = {
        "mm": 1,
        "cm": 10,
        "m": 1000,
        "um": 0.001,
        "nm": 0.000001,
        "dm": 100,
        "m": 1000,
        "km": 1000000,
    }

    if unit in unitsDict:
        mul = unitsDict[unit]

    try:
        px = mul * float(pos["x"])
        py = mul * float(pos["y"])
        pz = mul * float(pos["z"])
    except:
        px = py = pz = 0

    return px, py, pz


# Return x,y,z from position definition
def getElementPosition(xmlElem):
    # get Position from local element
    # setTrace(True)
    trace("Get Element Position : ")
    pos = xmlElem.find("position")
    if pos is not None:
        trace(pos.attrib)
        return getPositionFromAttrib(pos)
    else:
        return 0, 0, 0


def getDefinedPosition(name):
    # get Position from define section
    # pos = define.find("position[@name='%s']" % name )
    pos = positions[name]
    if pos is not None:
        # print('Position : '+str(pos))
        trace(pos)
        # return(getPositionFromAttrib(pos))
        return getPositionFromDict(pos)
    else:
        return 0, 0, 0


def getPosition(xmlEntity):
    # Get position via reference
    # setTrace(True)
    trace("GetPosition via Reference if any")
    posName = getRef(xmlEntity, "positionref")
    if posName is not None:
        trace("positionref : " + posName)
        return getDefinedPosition(posName)
    else:
        return getElementPosition(xmlEntity)


def testPosition(xmlEntity, px, py, pz):
    posName = getRef(xmlEntity, "positionref")
    if posName is not None:
        trace("positionref : " + posName)
        return getDefinedPosition(posName)
    pos = xmlEntity.find("position")
    if pos is not None:
        trace(pos.attrib)
        return getPositionFromAttrib(pos)
    else:
        return px, py, pz


def getDefinedRotation(name):
    # Just get definition - used by parseMultiUnion passed to create solids
    return define.find("rotation[@name='%s']" % name)


def getRotation(xmlEntity):
    trace("GetRotation")
    rotref = getRef(xmlEntity, "rotationref")
    trace("rotref : " + str(rotref))
    if rotref is not None:
        rot = define.find("rotation[@name='%s']" % rotref)
    else:
        rot = xmlEntity.find("rotation")
    if rot is not None:
        trace(rot.attrib)
    return rot


def getRotFromRefs(ptr):
    printverbose = True
    trace("getRotFromRef")
    rot = define.find("rotation[@name='%s']" % getRef(ptr, "rotationref"))
    if rot is not None:
        trace(rot.attrib)
    return rot


def getDefinedVector(solid, v):
    global define
    # print('get Defined Vector : '+v)
    name = solid.get(v)
    pos = define.find("position[@name='%s']" % name)
    # print(pos.attrib)
    x = getVal(pos, "x")
    y = getVal(pos, "y")
    z = getVal(pos, "z")
    return FreeCAD.Vector(x, y, z)


def getPlacement(pvXML):
    base = FreeCAD.Vector(getPosition(pvXML))
    # print('base: '+str(base))
    rot = getRotation(pvXML)
    return processPlacement(base, rot)


def getScale(pvXML):
    # print(ET.tostring(pvXML))
    scale = pvXML.find("scale")
    x = y = z = 1.0
    if scale is not None:
        # print(ET.tostring(scale))
        x = getVal(scale, "x")
        y = getVal(scale, "y")
        z = getVal(scale, "z")
    return FreeCAD.Vector(x, y, z)


def getVertex(v):
    global define
    trace("Vertex")
    # print(dir(v))
    pos = define.find("position[@name='%s']" % v)
    # print("Position")
    # print(dir(pos))
    x = getVal(pos, "x")
    trace("x : " + str(x))
    y = getVal(pos, "y")
    trace("y : " + str(y))
    z = getVal(pos, "z")
    trace("z : " + str(z))
    return FreeCAD.Vector(x, y, z)


def facet(f):
    # vec = FreeCAD.Vector(1.0,1.0,1.0)
    # print(f"Facet {f}")
    # print(f.Points)
    if len(f.Points) == 3:
        return triangle(f.Points[0], f.Points[1], f.Points[2])
        # if f.Normal.dot(vec) > 0 :
        #   return(triangle(f.Points[0],f.Points[1],f.Points[2]))
        # else :
        #   return(triangle(f.Points[2],f.Points[1],f.Points[0]))
    else:
        return quad(f.Points[0], f.Points[1], f.Points[2], f.Points[3])
        # if f.Normal.dot(vec) > 0 :
        #   return(quad(f.Points[0],f.Points[1],f.Points[2],f.Points[3]))
        # else :
        #   return(quad(f.Points[3],f.Points[2],f.Points[1],f.Points[0]))


def triangle(v1, v2, v3):
    # passed vertex return face
    # print('v1 : '+str(v1)+' v2 : '+str(v2)+' v3 : '+str(v3))
    try:
        w1 = Part.makePolygon([v1, v2, v3, v1])
        f1 = Part.Face(w1)
        return f1
    except:
        return None


def quad(v1, v2, v3, v4):
    # passed vertex return face
    w1 = Part.makePolygon([v1, v2, v3, v4, v1])
    try:
        f1 = Part.Face(w1)
        return f1
    except:
        print(f"Failed to create Face {v1} {v2} {v3} {v4}")
        return None
