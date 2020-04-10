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

def radians2deg(r) :
    import math
    return(r * 180/math.pi)

def processPlacement(base,rot) :
    printverbose = True
    trace('processPlacement')
    print('processPlacement')
    # Different Objects will have adjusted base GDML-FreeCAD
    # rot is rotation or None if default 
    # set angle & axis in case not set by rotation attribute
    #axis = FreeCAD.Vector(1,0,0)
    #angle = 0
    Xangle = Yangle = Zangle = 0.0
    if rot != None :
        trace("Rotation : ")
        print("Rotation : ")
        print(rot)
        trace(rot.attrib)
        if 'y' in rot.attrib :
            #axis = FreeCAD.Vector(0,1,0)
            Yangle = radians2deg(float(eval(rot.attrib['y'])))
            print('Y angle : '+str(Yangle))
        if 'x' in rot.attrib :
            print(rot.attrib['x'])
            print(eval(rot.attrib['x']))
            Xangle = radians2deg(float(eval(rot.attrib['x'])))
            print('X angle : '+str(Xangle))
        if 'z' in rot.attrib :
            Zangle = radians2deg(float(eval(rot.attrib['z'])))
            print('Z angle : '+str(Zangle))
            # Use only three float values for Rotation
        return FreeCAD.Placement(base,FreeCAD.Rotation(Xangle,Yangle,Zangle))

    else :
        print('No rotation')
        rot = FreeCAD.Rotation(0,0,0)
        return FreeCAD.Placement(base,rot)

# Return a FreeCAD placement for positionref & rotateref
def getBaseFromRefs(ptr) :
    printverbose = True
    trace("getBaseFromRef")
    pos = define.find("position[@name='%s']" % getRef(ptr,'positionref'))
    trace(pos)
    x = y = z = 0 
    if pos != None :
       trace(pos.attrib)
       x = getVal(pos,'x')
       trace(x)
       y = getVal(pos,'y')
       z = getVal(pos,'z')
    return x,y,z

def getRotFromRefs(ptr) :
    printverbose = True
    trace("getRotFromRef")
    rot = define.find("rotation[@name='%s']" % getRef(ptr,'rotationref'))
    print(rot)
    return rot

def getVertex(v):
    trace("Vertex")
    #print(dir(v))

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

