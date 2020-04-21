# Shared file
# single access to globals
# anything requiring access to globals needs to call a function in this file
# anything needing to call eval needs to be in this file

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


### modif
def processPosition(doc):
    # need to be done
    trace("Process Position (not taken into account in this version)")

def processExpression(doc):
    # need to be done
    trace("Process expression (not taken into account in this version)")

def processRotation(doc):
    # need to be done
    trace("Process rotation (not taken into account in this version)")

def processQuantity(doc):
    # need to be done 
    trace("Process quantity (not taken into account in this version)" )
###  end modif

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

def getMult(unit) :
    # Watch for unit and lunit
    trace('unit : '+unit)
    if unit == 'mm' or unit == None :
       return(1)
    elif unit == 'cm' :
       return(10)
    elif unit == 'm' :
       return(1000)
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
    #if hasattr(pos.attrib, 'unit') :        # Note unit NOT lunit
    if 'unit' in  pos.attrib :
        mul = getMult(pos.get('unit'))
        px = mul * getVal(pos,'x')
        py = mul * getVal(pos,'y')
        pz = mul * getVal(pos,'z')
    else :     
        px = getVal(pos,'x')
        py = getVal(pos,'y')
        pz = getVal(pos,'z')
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

def getDefinedRotation(name) :
    # Just get defintion - used by parseMultiUnion passed to create solids
    return(define.find("rotation[@name='%s']" % name ))

def getRotation(xmlEntity) :
    trace('GetRotation')
    rotref = getRef(xmlEntity,"rotationref")
    print(rotref)
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

def getVertex(v):
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
    fc1 = getVertex(v1)
    fc2 = getVertex(v2)
    fc3 = getVertex(v3)
    w1 = Part.makePolygon([fc1,fc2,fc3,fc1])
    f1 = Part.Face(w1)
    return(f1)

def quad(v1,v2,v3,v4) :
    # passsed vertex return face
    fc1 = getVertex(v1)
    fc2 = getVertex(v2)
    fc3 = getVertex(v3)
    fc4 = getVertex(v4)
    w1 = Part.makePolygon([fc1,fc2,fc3,fc4,fc1])
    f1 = Part.Face(w1)
    return(f1)

