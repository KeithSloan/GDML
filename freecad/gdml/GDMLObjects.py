import FreeCAD, FreeCADGui, Part
from pivy import coin
import math
from . import GDMLShared

# Global Material List
global MaterialsList
MaterialsList = []

def checkFullCircle(aunit, angle) :
    #print(angle)
    if aunit == 'deg' and angle == 360 :
       return True
    if aunit == 'rad' and angle == 2 * math.pi : 
       return True
    return False

# Get angle in Radians
def getAngleRad(aunit,angle) :
   #print("aunit : "+str(aunit))
   if aunit == 'deg' :   # 0 radians 1 Degrees
      return(angle*math.pi/180)
   else :
      return angle

# Get angle in Degrees
def getAngleDeg(aunit,angle) :
   #print("aunit : "+str(aunit))
   if aunit == 'rad' :   # 0 radians 1 Degrees
      return(angle*180/math.pi)
   else :
      return angle

def makeRegularPolygon(n,r,z):
    from math import cos, sin, pi
    vecs = [FreeCAD.Vector(cos(2*pi*i/n)*r, sin(2*pi*i/n)*r, z) \
            for i in range(n+1)]
    return vecs

def printPolyVec(n,v) :
    print("Polygon : "+n)
    for i in v :
        print("Vertex - x : "+str(i[0])+" y : "+str(i[1])+" z : "+str(i[2]))

def translate(shape,base) :
    # Input Object and displacement vector - return a transformed shape
    #return shape
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

def make_face3(v1,v2,v3):
    # helper mehod to create the faces
    wire = Part.makePolygon([v1,v2,v3,v1])
    face = Part.Face(wire)
    return face

def make_face4(v1,v2,v3,v4):
    # helper mehod to create the faces
    wire = Part.makePolygon([v1,v2,v3,v4,v1])
    face = Part.Face(wire)
    return face

def makeFrustrum(num,poly0,poly1) :
    # return list of faces
    #print("Make Frustrum : "+str(num)+" Faces")
    faces = []
    for i in range(num) :
       j = i + 1
       #print([poly0[i],poly0[j],poly1[j],poly1[i]])
       w = Part.makePolygon([poly0[i],poly0[j],poly1[j],poly1[i],poly0[i]])
       faces.append(Part.Face(w))
    #print("Number of Faces : "+str(len(faces)))
    return(faces)

def angleSectionSolid(fp, rmax, z, shape) :
    # Different Solids have different rmax and height
    import math
    #print("angleSectionSolid")
    #print('rmax : '+str(rmax))
    #print('z : '+str(z))
    #print("aunit : "+fp.aunit)
    startPhiDeg = getAngleDeg(fp.aunit,fp.startphi)
    deltaPhiDeg = getAngleDeg(fp.aunit,fp.deltaphi)
    #print('delta')
    #print(deltaPhiDeg)
    #print('start')
    #print(startPhiDeg)
    v1 = FreeCAD.Vector(0,0,0)
    v2 = FreeCAD.Vector(rmax,0,0)
    v3 = FreeCAD.Vector(rmax,0,z)
    v4 = FreeCAD.Vector(0,0,z)

    f1 = make_face4(v1,v2,v3,v4)
    s1 = f1.revolve(v1,v4,deltaPhiDeg)
    # Problem with FreeCAD 0.18
    #s2 = s1.rotate(v1,v4,startPhiDeg)

    #Part.show(s2)
    #return(shape.cut(s2))
    #return(s2)
    
    #if deltaPhiDeg > 90 :
    #   return(shape.common(s2))
    #else :   
    #   return(shape.cut(s2))

    if deltaPhiDeg > 90 :
        shape = shape.common(s1)
    else :   
        shape = shape.cut(s1)
    if startPhiDeg != 0 :
        shape.rotate(FreeCAD.Vector(0,0,0), \
                            FreeCAD.Vector(0,0,1),startPhiDeg)
    return shape

def setMaterial(obj, m) :
    #print('setMaterial')
    obj.material = MaterialsList
    obj.material = 0
    if len(MaterialsList) > 0 :
       if not ( m == 0 or m == None or m == '') : 
          obj.material = MaterialsList.index(m)

class GDMLcommon :
   def __init__(self, obj):
       '''Init'''

   def __getstate__(self):
        '''When saving the document this object gets stored using Python's json module.\
                Since we have some un-serializable parts here -- the Coin stuff -- we must define this method\
                to return a tuple of all serializable objects or None.'''
        return None
 
   def __setstate__(self,state):
        '''When restoring the serialized object from document we have the chance to set some internals here.\
                Since no data were serialized nothing needs to be done here.'''
        return None

class GDMLBox(GDMLcommon) :
   def __init__(self, obj, x, y, z, lunit, material, flag = False):
      '''Add some custom properties to our Box feature'''
      GDMLShared.trace("GDMLBox init")
      #GDMLShared.trace("material : "+material)
      obj.addProperty("App::PropertyFloat","x","GDMLBox","Length x").x=x
      obj.addProperty("App::PropertyFloat","y","GDMLBox","Length y").y=y
      obj.addProperty("App::PropertyFloat","z","GDMLBox","Length z").z=z
      obj.addProperty("App::PropertyString","lunit","GDMLBox","lunit").lunit=lunit
      obj.addProperty("App::PropertyEnumeration","material","GDMLBox","Material")
      setMaterial(obj, material)
      #obj.addProperty("Part::PropertyPartShape","Shape","GDMLBox", "Shape of the Box")
      self.Type = 'GDMLBox'
      obj.Proxy = self

   ### modif add
   def getMaterial(self):
       return obj.material
   ## end modif

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       # Changing Shape in createGeometry will redrive onChanged
       if ('Restore' in fp.State) :
          return
       
       if prop in ['x','y','z']  :
             self.createGeometry(fp) 

   def execute(self, fp):
       #print('execute')
       self.createGeometry(fp)

   def createGeometry(self,fp):
       #print('createGeometry')
       #print(fp)
       if all((fp.x,fp.y,fp.z)) :
       #if (hasattr(fp,'x') and hasattr(fp,'y') and hasattr(fp,'z')) :
          mul = GDMLShared.getMult(fp)
          GDMLShared.trace('mul : '+str(mul))
          x = mul * fp.x
          y = mul * fp.y
          z = mul * fp.z
          box = Part.makeBox(x,y,z)
          base = FreeCAD.Vector(-x/2,-y/2,-z/2)
          fp.Shape = translate(box,base)
    
   def OnDocumentRestored(self,obj) :
       print('Doc Restored')
          

class GDMLCone(GDMLcommon) :
   def __init__(self, obj, rmin1,rmax1,rmin2,rmax2,z,startphi,deltaphi,aunit, \
                lunit, material):
      '''Add some custom properties to our Cone feature'''
      obj.addProperty("App::PropertyFloat","rmin1","GDMLCone","Min Radius 1").rmin1=rmin1
      obj.addProperty("App::PropertyFloat","rmax1","GDMLCone","Max Radius 1").rmax1=rmax1
      obj.addProperty("App::PropertyFloat","rmin2","GDMLCone","Min Radius 2").rmin2=rmin2
      obj.addProperty("App::PropertyFloat","rmax2","GDMLCone","Max Radius 2").rmax2=rmax2
      obj.addProperty("App::PropertyFloat","z","GDMLCone","Height of Cone").z=z
      obj.addProperty("App::PropertyFloat","startphi","GDMLCone","Start Angle").startphi=startphi
      obj.addProperty("App::PropertyFloat","deltaphi","GDMLCone","Delta Angle").deltaphi=deltaphi
      obj.addProperty("App::PropertyEnumeration","aunit","GDMLCone","aunit")
      obj.aunit=["rad", "deg"]
      obj.aunit=['rad','deg'].index(aunit[0:3])
      obj.addProperty("App::PropertyString","lunit","GDMLCone","lunit").lunit=lunit
      #obj.addProperty("Part::PropertyPartShape","Shape","GDMLCone", \
      #                "Shape of the Cone")
      obj.addProperty("App::PropertyEnumeration","material","GDMLCone", \
                       "Material")
      setMaterial(obj, material)
      self.Type = 'GDMLCone'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if  'Restore' in fp.State :
           return

       if prop in ['rmin1','rmax1','rmin2','rmax2','z','startphi','deltaphi' \
               ,'aunit', 'lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)

   def createGeometry(self,fp):
       #print("fp : ")
       #print(vars(fp))
       #if all((fp.rmin1,fp.rmin2,fp.rmax1,fp.rmax2,fp.z)) :
       if (hasattr(fp,'rmin1') and hasattr(fp,'rmax1') and \
           hasattr(fp,'rmin2') and hasattr(fp,'rmax2') and \
           hasattr(fp,'z')) :
       # Need to add code to check variables will make a valid cone
       # i.e.max > min etc etc
          #print("execute cone")
          mul = GDMLShared.getMult(fp)
          rmin1 = mul * fp.rmin1
          rmin2 = mul * fp.rmin2
          rmax1 = mul * fp.rmax1
          rmax2 = mul * fp.rmax2
          z = mul * fp.z
          #print(mul)
          #print(rmax1)
          #print(rmax2)
          #print(rmin1)
          #print(rmin2)
          #print(z)
          if rmax1 != rmax2 :
             cone1 = Part.makeCone(rmax1,rmax2,z)
          else :  
             cone1 = Part.makeCylinder(rmax1,z)

          if (rmin1 != 0 and rmin2 != 0 ) :
             if rmin1 != rmin2 :
                cone2 = Part.makeCone(rmin1,rmin2,z)
             else :
                cone2 = Part.makeCylinder(rmin1,z)

             if rmax1 > rmin1 :
                cone3 = cone1.cut(cone2)
             else :
                cone3 = cone2.cut(cone1)
          else :
             cone3 = cone1
          base = FreeCAD.Vector(0,0,-z/2)
          if checkFullCircle(fp.aunit,fp.deltaphi) == False :
             rmax = max(rmax1, rmax2)
             cone = angleSectionSolid(fp, rmax, z, cone3)
             fp.Shape = translate(cone,base)
          else :   
             fp.Shape = translate(cone3,base)

class GDMLElCone(GDMLcommon) :
   def __init__(self, obj, dx, dy, zmax, zcut, lunit, material) :
      '''Add some custom properties to our ElCone feature'''
      obj.addProperty("App::PropertyFloat","dx","GDMLElCone", \
                      "x semi axis").dx = dx
      obj.addProperty("App::PropertyFloat","dy","GDMLElCone", \
                      "y semi axis").dy = dy
      obj.addProperty("App::PropertyFloat","zmax","GDMLElCone", \
                      "z length").zmax = zmax
      obj.addProperty("App::PropertyFloat","zcut","GDMLElCone", \
                      "z cut").zcut = zcut
      obj.addProperty("App::PropertyString","lunit","GDMLElCone", \
                      "lunit").lunit=lunit
      #obj.addProperty("Part::PropertyPartShape","Shape","GDMLElCone", \
      #                "Shape of the Cone")
      obj.addProperty("App::PropertyEnumeration","material","GDMLElCone", \
                       "Material")
      setMaterial(obj, material)
      self.Type = 'GDMLElCone'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return  
       if prop in ['dx','dy','zmax','zcut','lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       cone1 = Part.makeCone(100,0,100)
       mat = FreeCAD.Matrix()
       mat.unity()
       mul = GDMLShared.getMult(fp)
       # Semi axis values so need to double
       dx = fp.dx * mul
       dy = fp.dy * mul
       zcut = fp.zcut * mul
       zmax = fp.zmax * mul
       mat.A11 = dx / 100
       mat.A22 = dy / 100
       mat.A33 = zmax / 100
       mat.A44 = 1
       cone2 = cone1.transformGeometry(mat)
       if zcut != None :
          box = Part.makeBox(2*dx,2*dy,zcut)
          pl = FreeCAD.Placement()
          # Only need to move to semi axis
          pl.move(FreeCAD.Vector(-dx,-dy,zmax-zcut))
          box.Placement = pl
          fp.Shape = cone2.cut(box)
       else :
          fp.Shape = cone2

class GDMLEllipsoid(GDMLcommon) :
   def __init__(self, obj, ax, by, cz, zcut1, zcut2, lunit, material) :
      '''Add some custom properties to our Elliptical Tube feature'''
      obj.addProperty("App::PropertyFloat","ax","GDMLEllipsoid", \
                       "x semi axis").ax=ax
      obj.addProperty("App::PropertyFloat","by","GDMLEllipsoid", \
                       "y semi axis").by=by
      obj.addProperty("App::PropertyFloat","cz","GDMLEllipsoid", \
                       "z semi axis").cz=cz
      obj.addProperty("App::PropertyFloat","zcut1","GDMLEllipsoid", \
                       "z axis cut1").zcut1=zcut1
      obj.addProperty("App::PropertyFloat","zcut2","GDMLEllipsoid", \
                       "z axis1 cut2").zcut2=zcut2
      obj.addProperty("App::PropertyString","lunit","GDMLEllipsoid","lunit"). \
                        lunit=lunit
      #obj.addProperty("Part::PropertyPartShape","Shape","GDMLEllipsoid", \
      #                "Shape of the Ellipsoid")
      obj.addProperty("App::PropertyEnumeration","material","GDMLEllipsoid", \
                       "Material")
      setMaterial(obj, material)
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLEllipsoid", \
                      "Shape of the Ellipsoid")
      self.Type = 'GDMLEllipsoid'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return

       if prop in ['ax','by','cz','zcut1','zcut2','lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       mul = GDMLShared.getMult(fp)
       sphere = Part.makeSphere(100)
       ax = fp.ax * mul
       by = fp.by * mul
       cz = fp.cz * mul
       mat = FreeCAD.Matrix()
       mat.unity()
       # Semi axis values so need to double
       mat.A11 = ax / 100
       mat.A22 = by / 100
       mat.A33 = cz / 100
       mat.A44 = 1
       zcut1 = abs(fp.zcut1*mul)
       zcut2 = abs(fp.zcut2*mul)
       GDMLShared.trace("zcut2 : "+str(zcut2))
       t1ellipsoid = sphere.transformGeometry(mat) 
       if zcut2 != None and zcut2 > 0 :   # Remove from upper z
          box1 = Part.makeBox(2*ax,2*by,zcut2)
          pl = FreeCAD.Placement()
          # Only need to move to semi axis
          pl.move(FreeCAD.Vector(-ax,-by,cz-zcut2))
          box1.Placement = pl
          t2ellipsoid = t1ellipsoid.cut(box1)
       else :
          t2ellipsoid = t1ellipsoid 
       if zcut1 != None and zcut1 > 0 :
          # Remove from lower z, seems to be a negative number
          box2 = Part.makeBox(2*ax,2*by,zcut1)
          pl = FreeCAD.Placement()
          pl.move(FreeCAD.Vector(-ax,-by,-cz))
          box2.Placement = pl
          shape = t2ellipsoid.cut(box2)
       else :  
          shape = t2ellipsoid
       
       base = FreeCAD.Vector(0,0,cz/4)
       fp.Shape = translate(shape,base)   

class GDMLElTube(GDMLcommon) :
   def __init__(self, obj, dx, dy, dz, lunit, material) :
      '''Add some custom properties to our Elliptical Tube feature'''
      obj.addProperty("App::PropertyFloat","dx","GDMLElTube", \
                       "x semi axis1").dx=dx
      obj.addProperty("App::PropertyFloat","dy","GDMLElTube", \
                       "y semi axis1").dy=dy
      obj.addProperty("App::PropertyFloat","dz","GDMLElTube", \
                       "z semi axis1").dz=dz
      obj.addProperty("App::PropertyString","lunit","GDMLElTube","lunit"). \
                        lunit=lunit
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLElTube", \
                      "Shape of the Cone")
      obj.addProperty("App::PropertyEnumeration","material","GDMLElTube", \
                       "Material")
      setMaterial(obj, material)
      #obj.addProperty("Part::PropertyPartShape","Shape","GDMLElTube", \
      #                "Shape of the ElTube")
      self.Type = 'GDMLElTube'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       '''Do something when a property has changed'''
       if 'Restore' in fp.State :
          return

       if prop in ['dx','dy','dz','lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       mul = GDMLShared.getMult(fp)
       tube = Part.makeCylinder(100,100)
       mat = FreeCAD.Matrix()
       mat.unity()
       mat.A11 = (fp.dx * mul) / 100
       mat.A22 = (fp.dy * mul) / 100
       mat.A33 = (fp.dz * mul) / 50
       mat.A44 = 1
       #trace mat
       newtube = tube.transformGeometry(mat)
       base = FreeCAD.Vector(0,0,(fp.dz*mul)/2)
       fp.Shape = translate(newtube,base)

class GDMLPolyhedra(GDMLcommon) :
   def __init__(self, obj, startphi, deltaphi, numsides, aunit, lunit, material) :
      '''Add some custom properties for Polyhedra feature'''
      obj.addProperty("App::PropertyFloat","startphi","GDMLPolyhedra", \
                      "Start Angle").startphi=startphi
      obj.addProperty("App::PropertyFloat","deltaphi","GDMLPolyhedra", \
                      "Delta Angle").deltaphi=deltaphi
      obj.addProperty("App::PropertyInteger","numsides","GDMLPolyhedra", \
                      "Number of Side").numsides=numsides
      obj.addProperty("App::PropertyEnumeration","aunit","GDMLPolyhedra", \
                       "aunit")
      obj.aunit=["rad", "deg"]
      obj.aunit=['rad','deg'].index(aunit[0:3])
      obj.addProperty("App::PropertyString","lunit","GDMLPolyhedra", \
                      "lunit").lunit=lunit
      obj.addProperty("App::PropertyEnumeration","material","GDMLPolyhedra", \
                       "Material")
      setMaterial(obj, material)
      #obj.addProperty("Part::PropertyPartShape","Shape","GDMLPolyhedra", \
      #                 "Shape of the Polyhedra")
      self.Type = 'GDMLPolyhedra'
      self.Object = obj
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return

       if prop in ['startphi', 'deltaphi', 'numsides', 'aunit','lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       #GDMLShared.setTrace(True)
       GDMLShared.trace("Execute Polyhedra")
       parms = fp.OutList
       GDMLShared.trace("Number of parms : "+str(len(parms)))
       numsides = fp.numsides
       GDMLShared.trace("Number of sides : "+str(numsides))
       mul = GDMLShared.getMult(fp)
       z0    = parms[0].z * mul
       rmin0 = parms[0].rmin * mul
       rmax0 = parms[0].rmax * mul
       GDMLShared.trace("Top z    : "+str(z0))
       GDMLShared.trace("Top rmin : "+str(rmin0))
       GDMLShared.trace("Top rmax : "+str(rmax0))
       inner_faces = []
       outer_faces = []
       numsides = int(numsides * 360 / getAngleDeg(fp.aunit,fp.deltaphi))
       # Deal with Inner Top Face
       # Could be point rmin0 = rmax0 = 0
       if rmin0 > 0 :
           inner_poly0 = makeRegularPolygon(numsides,rmin0,z0)
           inner_faces.append(Part.Face(Part.makePolygon(inner_poly0)))
       # Deal with Outer Top Face 
       outer_poly0 = makeRegularPolygon(numsides,rmax0,z0)
       if rmax0 > 0 :        # Only make polygon if not a point
            outer_faces.append(Part.Face(Part.makePolygon(outer_poly0)))
       for ptr in parms[1:] :
           z1 = ptr.z * mul
           rmin1 = ptr.rmin * mul
           rmax1 = ptr.rmax * mul
           GDMLShared.trace("z1    : "+str(z1))
           GDMLShared.trace("rmin1 : "+str(rmin1))
           GDMLShared.trace("rmax1 : "+str(rmax1))
           # Concat face lists
           if rmin0 > 0 :
              inner_poly1 = makeRegularPolygon(numsides,rmin1,z1)
              inner_faces = inner_faces + \
                   makeFrustrum(numsides,inner_poly0,inner_poly1)
              inner_poly0 = inner_poly1
              inner_faces.append(Part.Face(Part.makePolygon(inner_poly1)))
           # Deal with Outer   
           outer_poly1 = makeRegularPolygon(numsides,rmax1,z1)
           outer_faces = outer_faces + \
                   makeFrustrum(numsides,outer_poly0,outer_poly1)
           # update for next zsection
           outer_poly0 = outer_poly1
           z0 = z1
       # add bottom polygon face
       outer_faces.append(Part.Face(Part.makePolygon(outer_poly1)))
       GDMLShared.trace("Total Faces : "+str(len(inner_faces)))
       outer_shell = Part.makeShell(outer_faces)
       outer_solid = Part.makeSolid(outer_shell)
       if rmin0 > 0 :
          inner_shell = Part.makeShell(inner_faces)
          inner_solid = Part.makeSolid(inner_shell)
          shape = outer_solid.cut(inner_solid)
       else :   
          shape = outer_solid 
       #fp.Shape = shell
       base = FreeCAD.Vector(0,0,-z0/2)
       if checkFullCircle(fp.aunit,fp.deltaphi) == False :
          newShape  = angleSectionSolid(fp, rmax1, z0, shape)
          fp.Shape = translate(newShape,base)
       else :
          fp.Shape = translate(shape,base)

class GDMLXtru(GDMLcommon) :
   def __init__(self, obj, lunit, material) :
      obj.addExtension('App::OriginGroupExtensionPython', self)
      obj.addProperty("App::PropertyString","lunit","GDMLXtru", \
                      "lunit").lunit=lunit
      obj.addProperty("App::PropertyEnumeration","material","GDMLXtru", \
                       "Material")
      setMaterial(obj, material)
      #obj.addProperty("Part::PropertyPartShape","Shape","GDMLXtru", \
      #                "Shape of the Xtru")
      self.Type = 'GDMLXtru'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return

       if prop in ['startphi','deltaphi','aunit','lunit'] :
          self.createGeometry(fp)
            
   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       print("Create Geometry")
       parms = fp.OutList
       #print("OutList")
       #print(parms)
       GDMLShared.trace("Number of parms : "+str(len(parms)))
       polyList = []
       sections = []
       mul = GDMLShared.getMult(fp)
       for ptr in parms :
           if hasattr(ptr,'x') :
              x = ptr.x * mul
              y = ptr.y * mul
              GDMLShared.trace('x : '+str(x))
              GDMLShared.trace('y : '+str(y))
              polyList.append([x, y])
           if hasattr(ptr,'zOrder') :
              zOrder = ptr.zOrder
              xOffset = ptr.xOffset * mul
              yOffset = ptr.yOffset * mul
              zPosition = ptr.zPosition * mul
              sf = ptr.scalingFactor
              s = [zOrder,xOffset,yOffset,zPosition,sf]
              sections.append(s)

       faces_list = []
       baseList = []
       topList = []
       # close polygon
       polyList.append(polyList[0])
       #print("Start Range "+str(len(sections)-1))
       for s in range(0,len(sections)-1) :
           xOffset1   = sections[s][1] * mul
           yOffset1   = sections[s][2] * mul
           zPosition1 = sections[s][3] * mul
           sf1        = sections[s][4] * mul
           xOffset2   = sections[s+1][1] * mul
           yOffset2   = sections[s+1][2] * mul
           zPosition2 = sections[s+1][3] * mul
           sf2        = sections[s+1][4] * mul
           #print("polyList")
           for p in polyList :
              #print(p)
              vb=FreeCAD.Vector(p[0]*sf1+xOffset1, p[1]*sf1+yOffset1,zPosition1)
              #vb=FreeCAD.Vector(-20, p[1]*sf1+yOffset1,zPosition1)
              vt=FreeCAD.Vector(p[0]*sf2+xOffset2, p[1]*sf2+yOffset2,zPosition2)
              #vt=FreeCAD.Vector(20, p[1]*sf2+yOffset2,zPosition2)
              baseList.append(vb) 
              topList.append(vt) 
           # close polygons
           baseList.append(baseList[0])
           topList.append(topList[0])
           # deal with base face       
           w1 = Part.makePolygon(baseList)
           f1 = Part.Face(w1)
           #f1.reverse()
           faces_list.append(f1)
           #print("base list")
           #print(baseList)
           #print("Top list")
           #print(topList)
           # deal with side faces
           # remember first point is added to end of list
           #print("Number Sides : "+str(len(baseList)-1))
           for i in range(0,len(baseList)-2) :
               sideList = []
               sideList.append(baseList[i])
               sideList.append(baseList[i+1])
               sideList.append(topList[i+1])
               sideList.append(topList[i])
               # Close SideList polygon
               sideList.append(baseList[i])
               print("sideList")
               print(sideList)
               w1 = Part.makePolygon(sideList)
               f1 = Part.Face(w1)
               faces_list.append(f1)
           # deal with top face
           w1 = Part.makePolygon(topList)
           f1 = Part.Face(w1)
           #f1.reverse()
           faces_list.append(f1)
           #print("Faces List")
           #print(faces_list)
           shell=Part.makeShell(faces_list)
           #solid=Part.Solid(shell).removeSplitter()
           solid=Part.Solid(shell)
           print("Valid Solid : "+str(solid.isValid()))
           if solid.Volume < 0:
              solid.reverse()
       #print(dir(fp))       
       #solid.exportBrep("/tmp/"+fp.Label+".brep")       
       fp.Shape = solid

class GDML2dVertex(GDMLcommon) :
   def __init__(self, obj, x, y):
      obj.addProperty("App::PropertyString","Type","Vertex", \
              "twoDimVertex").Type='twoDimVertex'
      obj.addProperty("App::PropertyFloat","x","Vertex", \
              "x").x=x
      obj.addProperty("App::PropertyFloat","y","Vertex", \
              "y").y=y
      obj.setEditorMode("Type", 1) 
      self.Type = 'Vertex'
      self.Object = obj
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       #if prop in ['x','y'] :
       #   self.execute(fp)
       #GDMLShared.trace("Change property: " + str(prop) + "\n")
       pass

   def execute(self, fp):
       pass
      
class GDMLSection(GDMLcommon) :
   def __init__(self, obj, zOrder,zPosition,xOffset,yOffset,scalingFactor):
      obj.addProperty("App::PropertyString","Type","section", \
              "section").Type='section'
      obj.addProperty("App::PropertyInteger","zOrder","section", \
              "zOrder").zOrder=zOrder
      obj.addProperty("App::PropertyInteger","zPosition","section", \
              "zPosition").zPosition=zPosition
      obj.addProperty("App::PropertyFloat","xOffset","section", \
              "xOffset").xOffset=xOffset
      obj.addProperty("App::PropertyFloat","yOffset","section", \
              "yOffset").yOffset=yOffset
      obj.addProperty("App::PropertyFloat","scalingFactor","section", \
              "scalingFactor").scalingFactor=scalingFactor
      obj.setEditorMode("Type", 1) 
      self.Type = 'section'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       #if prop in ['zOrder','zPosition','xOffset','yOffset','scaleFactor'] :
       #   self.execute(fp)
       #GDMLShared.trace("Change property: " + str(prop) + "\n")
       pass

   def execute(self, fp):
       pass
      
class GDMLzplane(GDMLcommon) :
   def __init__(self, obj, rmin, rmax, z):
      obj.addProperty("App::PropertyFloat","rmin","zplane", \
              "Inside Radius").rmin=rmin
      obj.addProperty("App::PropertyFloat","rmax","zplane", \
              "Outside Radius").rmax=rmax
      obj.addProperty("App::PropertyFloat","z","zplane","z").z=z
      self.Type = 'zplane'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       #if not ('Restore' in fp.State) :
       #if prop in ['rmin','rmax','z'] :
       #   self.execute(fp)
       #GDMLShared.trace("Change property: " + str(prop) + "\n")
       pass

   def execute(self, fp):
       pass
      
class GDMLPolycone(GDMLcommon) :
   def __init__(self, obj, startphi, deltaphi, aunit, lunit, material) :
      '''Add some custom properties to our Polycone feature'''
      obj.addExtension('App::OriginGroupExtensionPython', self)
      obj.addProperty("App::PropertyFloat","startphi","GDMLPolycone", \
              "Start Angle").startphi=startphi
      obj.addProperty("App::PropertyFloat","deltaphi","GDMLPolycone", \
             "Delta Angle").deltaphi=deltaphi
      obj.addProperty("App::PropertyEnumeration","aunit","GDMLPolycone","aunit")
      obj.aunit=["rad", "deg"]
      obj.aunit=['rad','deg'].index(aunit[0:3])
      obj.addProperty("App::PropertyString","lunit","GDMLPolycone", \
                      "lunit").lunit=lunit
      obj.addProperty("App::PropertyEnumeration","material","GDMLPolycone", \
                       "Material")
      setMaterial(obj, material)
      #obj.addProperty("Part::PropertyPartShape","Shape","GDMLPolycone", \
      #                "Shape of the Polycone")
      self.Type = 'GDMLPolycone'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return

       if prop in ['startphi','deltaphi','aunit','lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)

   def createGeometry(self,fp) :

       #GDMLShared.setTrace(True)
       zplanes = fp.OutList
       GDMLShared.trace("Number of zplanes : "+str(len(zplanes)))
       mul = GDMLShared.getMult(fp)
       fullHeight = mul * (zplanes[-1].z - zplanes[0].z) 
       # Running Height
       rh = 0.0
       maxR = 0
       for i in range(0,len(zplanes)-1) :
           GDMLShared.trace('index : '+str(i))
           dh = (zplanes[i+1].z - zplanes[i].z) * mul
           rmin1 = zplanes[i].rmin * mul
           rmin2 = zplanes[i+1].rmin * mul
           rmax1 = zplanes[i].rmax * mul
           rmax2 = zplanes[i+1].rmax * mul
           if rmax1 > maxR : maxR = rmax1
           if rmax2 > maxR : maxR = rmax2
           rmax2 = zplanes[i+1].rmax * mul
           GDMLShared.trace('del height : '+str(dh))
           GDMLShared.trace('rmin1 : '+str(rmin1)+' rmin2 : '+str(rmin2))
           GDMLShared.trace('rmax1 : '+str(rmax1)+' rmax2 : '+str(rmax2))
           if rmax1 != rmax2 :
                cone1 = Part.makeCone(rmax1,rmax2,dh)
           else :
                cone1 = Part.makeCylinder(rmax1,dh)
           if (rmin1 != 0 and rmin2 != 0 ) :
                if rmin1 != rmin2 :
                    cone2 = Part.makeCone(rmin1,rmin2,dh)
                else :
                    cone2 = Part.makeCylinder(rmin1,dh)
                if rmax1 > rmin1 :
                    cone = cone1.cut(cone2)
                else :
                    cone = cone2.cut(cone1)
           else :
                cone = cone1
           #cone = cone1
           vec = FreeCAD.Vector(0,0,rh)
           rh = rh + dh
           if i > 0 :
               fusionCone = fusionCone.fuse(translate(cone,vec))
           else :
               fusionCone = cone

       if checkFullCircle(fp.aunit,fp.deltaphi) == False :
          shape = angleSectionSolid(fp, maxR, fullHeight, fusionCone)
       else :
          shape = fusionCone

       fp.Shape = shape.translate(FreeCAD.Vector(0,0,-fullHeight/2.))
       #fp.Shape = fusionCone

class GDMLSphere(GDMLcommon) :
   def __init__(self, obj, rmin, rmax, startphi, deltaphi, starttheta, \
                deltatheta, aunit, lunit, material):
      '''Add some custom properties to our Sphere feature'''
      GDMLShared.trace("GDMLSphere init")
      obj.addProperty("App::PropertyFloat","rmin","GDMLSphere", \
              "Inside Radius").rmin=rmin
      obj.addProperty("App::PropertyFloat","rmax","GDMLSphere", \
              "Outside Radius").rmax=rmax
      obj.addProperty("App::PropertyFloat","startphi","GDMLSphere", \
              "Start Angle").startphi=startphi
      obj.addProperty("App::PropertyFloat","deltaphi","GDMLSphere", \
             "Delta Angle").deltaphi=deltaphi
      obj.addProperty("App::PropertyFloat","starttheta","GDMLSphere", \
             "Start Theta pos").starttheta=starttheta
      obj.addProperty("App::PropertyFloat","deltatheta","GDMLSphere", \
             "Delta Angle").deltatheta=deltatheta
      obj.addProperty("App::PropertyEnumeration","aunit","GDMLSphere","aunit")
      obj.aunit=["rad", "deg"]
      obj.aunit=['rad','deg'].index(aunit[0:3])
      obj.addProperty("App::PropertyString","lunit","GDMLSphere", \
                      "lunit").lunit=lunit
      obj.addProperty("App::PropertyEnumeration","material","GDMLSphere", \
                       "Material")
      setMaterial(obj, material)
      #obj.addProperty("Part::PropertyPartShape","Shape","GDMLSphere", \
      #                "Shape of the Sphere")
      obj.Proxy = self
      self.Type = 'GDMLSphere'

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return

       if prop in ['rmin','rmax','startphi','deltaphi','starttheta', \
                    'deltatheta','aunit','lunit'] :
          self.createGeometry(fp)
   
   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       # Based on code by Dam Lamb
       import math
       mul = GDMLShared.getMult(fp)
       rmax = mul * fp.rmax
       Rmax = 2 * rmax
       rmin = mul * fp.rmin
       spos = FreeCAD.Vector(0,0,0)
       sdir = FreeCAD.Vector(0,0,1)
       HalfPi = math.pi / 2.0
       TwoPi = 2 * math.pi
       deltaphi = getAngleDeg(fp.aunit, fp.deltaphi)
       if deltaphi != 360 :
            sphere2 = Part.makeSphere(rmax,spos,sdir, \
                     -90.0, 90.0, \
                     getAngleDeg(fp.aunit, fp.deltaphi))
            if fp.startphi != 0 :
                sphere2.rotate(spos, sdir, getAngleDeg(fp.aunit,fp.startphi))
       else :
            sphere2 = Part.makeSphere(rmax)

       # if starttheta > 0 cut the upper cone     
       if fp.starttheta != 0 :
            startthetaRad = getAngleRad(fp.aunit, fp.starttheta)

            if startthetaRad > 0.0 :
                if startthetaRad < HalfPi :
                    sphere2 = sphere2.cut(Part.makeCone(0.0, \
                            rmax/math.cos(startthetaRad), rmax))
                elif startthetaRad == HalfPi :
                    sphere2.cut(Part.makeBox(Rmax,Rmax,Rmax, \
                                FreeCAD.Vector(-rmax,-rmax,-rmax)))
                elif startthetaRad <= math.pi :
                    sphere2 = sphere2.common(Part.makeCone(0.0, \
                        rmax/math.cos(pi-startthetaRad),rmax, spos, \
                        FreeCAD.Vector(0,0,-1.0)))

       # if starttheta > 0 cut upper cone
       startthetaRad = getAngleRad(fp.aunit, fp.starttheta)
       if startthetaRad > 0.0 :
            if startthetaRad < HalfPi :
                sphere2 = sphere2.cut(Part.makeCone(0.0, \
                        rmax/math.cos(startthetaRad),rmax))
            elif startthetaRad == HalfPi :
                sphere2 = sphere2.common(Part.makeCone(0.0, \
                    rmax/math.cos(pi-startthetaRad),rmax, spos, \
                            FreeCAD(0,0,-1.0)))
       # if deltatheta -> cut the down cone
       deltathetaRad = getAngleRad(fp.aunit, fp.deltatheta)
       startthetaRad = getAngleRad(fp.aunit, fp.starttheta)
       thetaSum= startthetaRad + deltathetaRad
       if thetaSum < math.pi :
            if thetaSum > HalfPi :
                sphere2 = sphere2.cut(Part.makeCone(0.0, \
                    rmax/math.cos(math.pi - thetaSum), rmax, \
                    spos, FreeCAD.Vector(0,0,-1.0)))
            elif thetaSum == math.pi :
                sphere2 = sphere.cut(Part.makeBox(Rmax,Rmax,Rmax, \
                                    FreeCAD.Vector(-rmax,-rmax,-Rmax)))
            elif thetaSum > 0 :
                sphere2 = sphere2.common(Part.makeCone(0.0, \
                    rmax/math.cos(math.pi-thetadeltaRad), \
                    rmax, spos,sdir))
       # if rmin -> cut the rmin sphere
       if rmin <= 0 or rmin > rmax :
           fp.Shape = sphere2
       else :
           fp.Shape = sphere2.cut(Part.makeSphere(rmin))
           

class GDMLTrap(GDMLcommon) :
   def __init__(self, obj, z, theta, phi, x1, x2, x3, x4, y1, y2, alpha, \
                aunit, lunit, material):
      "General Trapezoid"
      obj.addProperty("App::PropertyFloat","z","GDMLTrap","z").z=z
      obj.addProperty("App::PropertyFloat","theta","GDMLTrap","theta"). \
                       theta=theta
      obj.addProperty("App::PropertyFloat","phi","GDMLTrap","phi").phi=phi
      obj.addProperty("App::PropertyFloat","x1","GDMLTrap", \
                      "Length x at y= -y1 face -z").x1=x1
      obj.addProperty("App::PropertyFloat","x2","GDMLTrap", \
                      "Length x at y= +y1 face -z").x2=x2
      obj.addProperty("App::PropertyFloat","x3","GDMLTrap", \
                      "Length x at y= -y1 face +z").x3=x3
      obj.addProperty("App::PropertyFloat","x4","GDMLTrap", \
                      "Length x at y= +y1 face +z").x4=x4
      obj.addProperty("App::PropertyFloat","y1","GDMLTrap", \
                      "Length y at face -z").y1=y1
      obj.addProperty("App::PropertyFloat","y2","GDMLTrap", \
                      "Length y at face +z").y2=y2
      obj.addProperty("App::PropertyFloat","alpha","GDMLTrap","alpha"). \
                     alpha=alpha
      obj.addProperty("App::PropertyEnumeration","aunit","GDMLTrap","aunit")
      obj.aunit=["rad", "deg"]
      obj.aunit=['rad','deg'].index(aunit[0:3])
      obj.addProperty("App::PropertyString","lunit","GDMLTrap","lunit"). \
                       lunit=lunit
      obj.addProperty("App::PropertyEnumeration","material","GDMLTrap","Material")
      setMaterial(obj, material)
      #obj.addProperty("Part::PropertyPartShape","Shape","GDMLTrap", \
      #                "Shape of the Trap")
      obj.Proxy = self
      self.Type = 'GDMLTrap'

   def onChanged(self, fp, prop):
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return

       if prop in ['z','theta','phi','x1','x2','x3','x4','y1','y2','alpha', \
                   'aunit', 'lunit'] :
          self.createGeometry(fp)
   
   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       import math
       # Define six vetices for the shape
       alpha = getAngleRad(fp.aunit,fp.alpha)
       theta = getAngleRad(fp.aunit,fp.theta)
       phi   = getAngleRad(fp.aunit,fp.phi)
       mul   = GDMLShared.getMult(fp)
       dx = fp.y1*math.sin(alpha) * mul
       dy = fp.y1*(1.0 - math.cos(alpha)) * mul
       GDMLShared.trace("Delta adjustments")
       GDMLShared.trace("dx : "+str(dx)+" dy : "+str(dy))
       y1m = dy - (fp.y1 * mul)
       y1p = dy + (fp.y1 * mul)
       x1m = dx - (fp.x1 * mul)
       x1p = dx + (fp.x1 * mul)
       z    = fp.z * mul
       GDMLShared.trace("y1m : "+str(y1m))
       GDMLShared.trace("y1p : "+str(y1p))
       GDMLShared.trace("z   : "+str(z))
       GDMLShared.trace("x1  : "+str(fp.x1))
       GDMLShared.trace("x2  : "+str(fp.x2))

       v1    = FreeCAD.Vector(x1m, y1m, -z)
       v2    = FreeCAD.Vector(x1p, y1m, -z)
       v3    = FreeCAD.Vector(x1p, y1p, -z)
       v4    = FreeCAD.Vector(x1m, y1p, -z)

       # x,y of centre of top surface
       dr = z*math.tan(theta)
       tx = dr*math.cos(phi)
       ty = dr*math.cos(phi)
       GDMLShared.trace("Coord of top surface centre")
       GDMLShared.trace("x : "+str(tx)+" y : "+str(ty))
       py2 = ty + (fp.y2 * mul)
       my2 = ty - (fp.y2 * mul)
       px3 = tx + (fp.x3 * mul)
       mx3 = tx - (fp.x3 * mul)
       px4 = tx + (fp.x4 * mul)
       mx4 = tx - (fp.x4 * mul)
       GDMLShared.trace("px3 : "+str(px3))
       GDMLShared.trace("py2 : "+str(py2))
       GDMLShared.trace("my2 : "+str(my2))

       v5 = FreeCAD.Vector(mx3, my2, z)
       v6 = FreeCAD.Vector(px3, my2, z)
       v7 = FreeCAD.Vector(px3, py2, z)
       v8 = FreeCAD.Vector(mx3, py2, z)

       # Make the wires/faces
       f1 = make_face4(v1,v2,v3,v4)
       f2 = make_face4(v1,v2,v6,v5)
       f3 = make_face4(v2,v3,v7,v6)
       f4 = make_face4(v3,v4,v8,v7)
       f5 = make_face4(v1,v4,v8,v5)
       f6 = make_face4(v5,v6,v7,v8)
       shell=Part.makeShell([f1,f2,f3,f4,f5,f6])
       solid=Part.makeSolid(shell)

       #solid = Part.makePolygon([v1,v2,v3,v4,v5,v6,v7,v1])

       fp.Shape = solid

class GDMLTrd(GDMLcommon) :
   def __init__(self, obj, z, x1, x2,  y1, y2, lunit, material) :
      "3.4.15 : Trapezoid – x & y varying along z"
      obj.addProperty("App::PropertyFloat","z","GDMLTrd`","z").z=z
      obj.addProperty("App::PropertyFloat","x1","GDMLTrd", \
                      "Length x at y= -y1 face -z").x1=x1
      obj.addProperty("App::PropertyFloat","x2","GDMLTrd", \
                      "Length x at y= +y1 face -z").x2=x2
      obj.addProperty("App::PropertyFloat","y1","GDMLTrd", \
                      "Length y at face -z").y1=y1
      obj.addProperty("App::PropertyFloat","y2","GDMLTrd", \
                      "Length y at face +z").y2=y2
      obj.addProperty("App::PropertyString","lunit","GDMLTrd","lunit"). \
                       lunit=lunit
      obj.addProperty("App::PropertyEnumeration","material","GDMLTrd","Material") 
      setMaterial(obj, material)
      #obj.addProperty("Part::PropertyPartShape","Shape","GDMLTrd", \
      #                "Shape of the Trap")
      obj.Proxy = self
      self.Type = 'GDMLTrd'

   def onChanged(self, fp, prop):
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return

       if prop in ['z','x1','x2','y1','y2','lunit'] :
          self.createGeometry(fp)
   
   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       import math
       GDMLShared.trace("x2  : "+str(fp.x2))

       mul = GDMLShared.getMult(fp)
       x1 = (fp.x1 * mul)/2
       x2 = (fp.x2 * mul)/2
       y1 = (fp.y1 * mul)/2
       y2 = (fp.y2 * mul)/2
       z  = fp.z * mul
       v1 = FreeCAD.Vector(-x1, -y1, -z)
       v2 = FreeCAD.Vector(-x1, +y1, -z)
       v3 = FreeCAD.Vector(x1,  +y1, -z)
       v4 = FreeCAD.Vector(x1,  -y1, -z)

       v5 = FreeCAD.Vector(-x2, -y2,  z)
       v6 = FreeCAD.Vector(-x2, +y2,  z)
       v7 = FreeCAD.Vector(x2,  +y2,  z)
       v8 = FreeCAD.Vector(x2,  -y2,  z)
       # Make the wires/faces
       f1 = make_face4(v1,v2,v3,v4)
       f2 = make_face4(v1,v2,v6,v5)
       f3 = make_face4(v2,v3,v7,v6)
       f4 = make_face4(v3,v4,v8,v7)
       f5 = make_face4(v1,v4,v8,v5)
       f6 = make_face4(v5,v6,v7,v8)
       shell=Part.makeShell([f1,f2,f3,f4,f5,f6])
       solid=Part.makeSolid(shell)

       #solid = Part.makePolygon([v1,v2,v3,v4,v5,v6,v7,v1])

       fp.Shape = solid

class GDMLTube(GDMLcommon) :
   def __init__(self, obj, rmin, rmax, z, startphi, deltaphi, aunit,  \
                lunit, material):
      '''Add some custom properties to our Tube feature'''
      obj.addProperty("App::PropertyFloat","rmin","GDMLTube","Inside Radius").rmin=rmin
      obj.addProperty("App::PropertyFloat","rmax","GDMLTube","Outside Radius").rmax=rmax
      obj.addProperty("App::PropertyFloat","z","GDMLTube","Length z").z=z
      obj.addProperty("App::PropertyFloat","startphi","GDMLTube","Start Angle").startphi=startphi
      obj.addProperty("App::PropertyFloat","deltaphi","GDMLTube","Delta Angle").deltaphi=deltaphi
      obj.addProperty("App::PropertyEnumeration","aunit","GDMLTube","aunit")
      obj.aunit=['rad','deg']
      obj.aunit=['rad','deg'].index(aunit[0:3])
      obj.addProperty("App::PropertyString","lunit","GDMLTube","lunit").lunit=lunit
      obj.addProperty("App::PropertyEnumeration","material","GDMLTube","Material")
      setMaterial(obj, material)
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLTube", "Shape of the Tube")
      obj.Proxy = self
      self.Type = 'GDMLTube'

   def onChanged(self, fp, prop):
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return

       if prop in ['rmin','rmax','z','startphi','deltaphi','aunit',  \
                  'lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       mul  = GDMLShared.getMult(fp)
       rmax = mul * fp.rmax
       rmin = mul * fp.rmin
       z = mul * fp.z 
       spos = FreeCAD.Vector(0,0,0)
       sdir = FreeCAD.Vector(0,0,1)
       #print('mul : '+str(mul))
       #print('rmax : '+str(rmax))
       #print('z    : '+str(z))
       #print('deltaPhi : '+str(fp.deltaphi))
       tube = Part.makeCylinder(rmax, z, spos, sdir,
                    getAngleDeg(fp.aunit, fp.deltaphi))
       
       if fp.startphi != 0 :
           tube.rotate(spos, sdir, getAngleDeg(fp.aunit,fp.startphi))
       
       if rmin > 0 :
          tube = tube.cut(Part.makeCylinder(rmin, z))
       
       base = FreeCAD.Vector(0,0,-z/2)
       fp.Shape = translate(tube,base)

class GDMLcutTube(GDMLcommon) :
   def __init__(self, obj, rmin, rmax, z, startphi, deltaphi, aunit,  \
                lowX, lowY, lowZ, highX, highY, highZ, \
                lunit, material):
      '''Add some custom properties to our Tube feature'''
      obj.addProperty("App::PropertyFloat","rmin","GDMLcutTube","Inside Radius").rmin=rmin
      obj.addProperty("App::PropertyFloat","rmax","GDMLcutTube","Outside Radius").rmax=rmax
      obj.addProperty("App::PropertyFloat","z","GDMLcutTube","Length z").z=z
      obj.addProperty("App::PropertyFloat","startphi","GDMLcutTube","Start Angle").startphi=startphi
      obj.addProperty("App::PropertyFloat","deltaphi","GDMLcutTube","Delta Angle").deltaphi=deltaphi
      obj.addProperty("App::PropertyEnumeration","aunit","GDMLcutTube","aunit")
      obj.aunit=['rad','deg']
      obj.aunit=['rad','deg'].index(aunit[0:3])
      obj.addProperty("App::PropertyFloat","lowX","GDMLcutTube","low X").lowX=lowX
      obj.addProperty("App::PropertyFloat","lowY","GDMLcutTube","low Y").lowY=lowY
      obj.addProperty("App::PropertyFloat","lowZ","GDMLcutTube","low Z").lowZ=lowZ
      obj.addProperty("App::PropertyFloat","highX","GDMLcutTube","high X").highX=highX
      obj.addProperty("App::PropertyFloat","highY","GDMLcutTube","high Y").highY=highY
      obj.addProperty("App::PropertyFloat","highZ","GDMLcutTube","high Z").highZ=highZ
      obj.addProperty("App::PropertyString","lunit","GDMLcutTube","lunit").lunit=lunit
      obj.addProperty("App::PropertyEnumeration","material","GDMLcutTube","Material")
      #print('Add material')
      #print(material)
      setMaterial(obj, material)
      #print(MaterialsList)
      #obj.addProperty("Part::PropertyPartShape","Shape","GDMLcutTube", "Shape of the Tube")
      obj.Proxy = self
      self.Type = 'GDMLcutTube'

   def onChanged(self, fp, prop):
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return

       if prop in ['rmin','rmax','z','startphi','deltaphi','aunit',  \
                   'lowX', 'lowY', 'lowZ', \
                   'highX','highY','highZ','lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)


   def cutShapeWithPlane(self, shape, plane, depth):
        "Cut a shape with a plane"
        #print('Cut Shape with Plane')
        #print('depth : '+str(depth))
        #so = plane.extrude(plane.*1e10)
        #so = plane.extrude(plane.normalAt(1,1)*1e10)
        #so = plane.extrude(plane.normalAt(1,1)*100)
        so = plane.extrude(plane.normalAt(1,1)*depth)
        #print('Plane extruded')
        #print(plane.normalAt(1,1))
        #return so
        #print('Extrude made - Now Cut')
        cut = shape.cut(so)
        #print('Return Cut')
        return cut

   def createGeometry(self,fp):
        angle = getAngleDeg(fp.aunit,fp.deltaphi)
        pntC = FreeCAD.Vector(0,0,0)
        dirC = FreeCAD.Vector(0,0,1)
        mul  = GDMLShared.getMult(fp)
        #print('mul : '+str(mul))
        rmin = mul * fp.rmin
        #print('rmin : '+str(rmin))
        #print(type(fp.rmin))
        rmax = mul * fp.rmax
        #print('rmax : '+str(rmax))
        z    = mul * fp.z
        #print('z    : '+str(z))
        depth = 2 * max(rmax,z)
        #print('depth : '+str(depth))
        #print(fp.lowX)
        #print(fp.lowY)
        #print(fp.lowZ)
        botDir = FreeCAD.Vector(fp.lowX, fp.lowY, fp.lowZ)
        topDir = FreeCAD.Vector(fp.highX, fp.highY, fp.highZ)

        tube1 = Part.makeCylinder(rmax,z,pntC,dirC,angle)
        tube2 = Part.makeCylinder(rmin,z,pntC,dirC,angle)
        tube = tube1.cut(tube2)
        #Part.show(tube1)
        #print('Create top Plane')
        topPlane = Part.makePlane(depth, depth, \
                FreeCAD.Vector(-rmax,-rmax,z),topDir)
        #Part.show(topPlane)
        #print('Cut top Plane')
        cutTube1 =  self.cutShapeWithPlane(tube, topPlane, depth)
        #Part.show(cutTube1)
        #print('Create BottomPlane')
        botPlane = Part.makePlane(depth, depth, \
                FreeCAD.Vector(rmax,rmax,0.0),botDir)
        #botPlane = Part.makePlane(500, 500, \
        #        FreeCAD.Vector(rmax,rmax,0.0),FreeCAD.Vector(0.0,-0.7,-0.71))
        #Part.show(botPlane)
        #print('Cut Top Plane')
        cutTube2 = self.cutShapeWithPlane(cutTube1,botPlane,depth)
        #print('Return result')
        #fp.Shape = Part.makeBox(2,2,2)
        base = FreeCAD.Vector(0,0,-z/2)
        fp.Shape = translate(cutTube2,base)
        #fp.Shape = topPlane
        #fp.Shape = botPlane

   def createGeometry_hardcoded(self,fp):
        angle = getAngleDeg(fp.aunit,fp.deltaphi)
        pntC = FreeCAD.Vector(0,0,0)
        dirC = FreeCAD.Vector(0,0,1)
        #pntP = FreeCAD.Vector(-5,-5,5)

        tube1 = Part.makeCylinder(20,60,pntC,dirC,angle)
        tube2 = Part.makeCylinder(12,60,pntC,dirC,angle)
        tube = tube1.cut(tube2)
        Part.show(tube1)
        #print('Create top Plane')
        topPlane = Part.makePlane(100, 100, \
                FreeCAD.Vector(-20,-20,60),FreeCAD.Vector(0.7,0,0.71))
        #Part.show(topPlane)
        print('Cut top Plane')
        cutTube1 =  self.cutShapeWithPlane(tube, topPlane)
        #Part.show(cutTube1)
        print('Create BottomPlane')
        botPlane = Part.makePlane(100, 100, \
                FreeCAD.Vector(20,20,0),FreeCAD.Vector(0,-0.7,-0.71))
        Part.show(botPlane)
        print('Cut Top Plane')
        cutTube2 = self.cutShapeWithPlane(cutTube1,botPlane)
        #cutTube2 = self.cutShapeWithPlane(tube,botPlane)
        print('Return result')
        #fp.Shape = Part.makeBox(2,2,2)
        fp.Shape = cutTube2
        #fp.Shape = tube
        #fp.Shape = topPlane

class GDMLVertex(GDMLcommon) :
   def __init__(self, obj, x, y, z, lunit):
      obj.addProperty("App::PropertyFloat","x","GDMLVertex", \
              "x").x=x
      obj.addProperty("App::PropertyFloat","y","GDMLVertex", \
              "y").y=y
      obj.addProperty("App::PropertyFloat","z","GDMLVertex", \
              "z").z=z
      self.Type = 'GDMLVertex'
      self.Object = obj
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       #if not ('Restore' in fp.State) :
       #   if prop in ['x','y', 'z'] :
       #      self.execute(fp)
       #GDMLShared.trace("Change property: " + str(prop) + "\n")
       pass

   def execute(self, fp):
       pass       

class GDMLTriangular(GDMLcommon) :
   def __init__(self, obj, v1, v2, v3, vtype):
      obj.addProperty("App::PropertyString","v1","Triangular", \
              "v1").v1=v1
      obj.addProperty("App::PropertyString","v2","Triangular", \
              "v1").v2=v2
      obj.addProperty("App::PropertyString","v3","Triangular", \
              "v1").v3=v3
      obj.addProperty("App::PropertyEnumeration","vtype","Triangular","vtype")
      obj.vtype=["Absolute", "Relative"]
      obj.vtype=["Absolute", "Relative"].index(vtype)
      self.Type = 'GDMLTriangular'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       #if not ('Restore' in fp.State) :
       #   if prop in ['v1','v2','v3','type'] :
       #      self.execute(fp)
       #GDMLShared.trace("Change property: " + str(prop) + "\n")
       pass

   def execute(self, fp):
       pass
       
class GDMLQuadrangular(GDMLcommon) :
   def __init__(self, obj, v1, v2, v3, v4, vtype):
      obj.addProperty("App::PropertyString","v1","Quadrang", \
              "v1").v1=v1
      obj.addProperty("App::PropertyString","v2","Quadrang", \
              "v2").v2=v2
      obj.addProperty("App::PropertyString","v3","Quadrang", \
              "v3").v3=v3
      obj.addProperty("App::PropertyString","v4","Quadrang", \
              "v4").v4=v4
      obj.addProperty("App::PropertyEnumeration","vtype","Quadrang","vtype")
      obj.vtype=["Absolute", "Relative"]
      obj.vtype=0
      self.Type = 'GDMLQuadrangular'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       #if not ('Restore' in fp.State) :
       #   if prop in ['v1','v2','v3','v4','type'] :
       #      self.execute(fp)
       #GDMLShared.trace("Change property: " + str(prop) + "\n")
       pass

   def execute(self, fp):
       pass
       
class GDMLTessellated(GDMLcommon) :
    
   def __init__(self, obj, material ) :
      obj.addExtension('App::OriginGroupExtensionPython', self)
      #obj.addProperty("Part::PropertyPartShape","Shape","GDMLTessellated", "Shape of the Tesssellation")
      obj.addProperty("App::PropertyEnumeration","material","GDMLTessellated","Material")
      setMaterial(obj, material)
      self.Type = 'GDMLTessellated'
      self.Object = obj
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return

       if prop in ['v1','v2','v3','v4','type'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       print("Tessellated")
       parms = fp.OutList
       GDMLShared.trace("Number of parms : "+str(len(parms)))
       faces = []
       mul = GDMLShared.getMult(fp)
       v1 = ptr.v1 * mul
       v2 = ptr.v2 * mul
       v3 = ptr.v3 * mul
       v4 = ptr.v4 * mul
       for ptr in parms :
           #print(dir(ptr))
           if hasattr(ptr,'v4') :
              print("Quad")
              print(v1)
              print(v2)
              print(v3)
              print(v4)
              faces.append(GDMLShared.quad(v1,v2,v3,v4))

           else :   
              print("Triangle")
              print("Vertex 1")
              print(v1)
              print("Vertex 2")
              print(v2)
              print("Vertex 3")
              print(v3)
              faces.append(GDMLShared.triangle(ptr.v1,ptr.v2,ptr.v3))
     
       print(faces)
       shell=Part.makeShell(faces)
       print("Is Valid")
       print(shell.isValid())
       shell.check()
       #solid=Part.Solid(shell).removeSplitter()
       solid=Part.Solid(shell)
       if solid.Volume < 0:
          solid.reverse()
       print(dir(solid))   
       bbox = solid.BoundBox
       print(bbox)
       print(bbox.XMin)
       print(bbox.YMin)
       print(bbox.ZMin)
       #print(bbox.XLength)
       #print(bbox.YLength)
       #print(bbox.ZLength)
       print(bbox.XMax)
       print(bbox.YMax)
       print(bbox.ZMax)
       base = FreeCAD.Vector(-(bbox.XMin+bbox.XMax)/2, \
                             -(bbox.YMin+bbox.YMax)/2 \
                             -(bbox.ZMin+bbox.ZMax)/2)
       print(base)

       fp.Shape = translate(solid,base)
       #fp.Shape = faces[0]
       #fp.Shape = Part.makeBox(10,10,10)

class GDMLFiles(GDMLcommon) :
   def __init__(self,obj,FilesEntity,sectionDict) :
      '''Add some custom properties to our Cone feature'''
      GDMLShared.trace("GDML Files")
      GDMLShared.trace(FilesEntity)
      obj.addProperty("App::PropertyBool","active","GDMLFiles", \
                    "split option").active=FilesEntity
      obj.addProperty("App::PropertyString","define","GDMLFiles", \
                    "define section").define=sectionDict.get('define',"")
      obj.addProperty("App::PropertyString","materials","GDMLFiles", \
                    "materials section").materials=sectionDict.get('materials',"")
      obj.addProperty("App::PropertyString","solids","GDMLFiles", \
                    "solids section").solids=sectionDict.get('solids',"")
      obj.addProperty("App::PropertyString","structure","GDMLFiles", \
                    "sructure section").structure=sectionDict.get('structure',"")
      self.Type = 'GDMLFiles'
      obj.Proxy = self

   def execute(self, fp):
      '''Do something when doing a recomputation, this method is mandatory'''
      pass

   def onChanged(self, fp, prop):
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       #if not ('Restore' in fp.State) :
       #   if not hasattr(fp,'onchange') or not fp.onchange : return
       pass

class GDMLvolume :
   def __init__(self,obj) :
      obj.Proxy = self
      self.Object = obj

class GDMLconstant(GDMLcommon) :
   def __init__(self,obj,name,value) :
      obj.addProperty("App::PropertyString","name",'GDMLconstant','name').name = name
      obj.addProperty("App::PropertyString","value",'GDMLconstant','value').value = value
      obj.Proxy = self
      self.Object = obj

class GDMLmaterial(GDMLcommon) :
   def __init__(self,obj,name,density=1.0,conduct=2.0,expand=3.0,specific=4.0) :
      # Add most properties later 
      obj.addProperty("App::PropertyString","name",'GDMLmaterial','name').name = name
      obj.addProperty("App::PropertyFloat","density","GDMLmaterial", \
                      "Density kg/m^3").density = density
      obj.addProperty("App::PropertyFloat","conduct","GDMLmaterial", \
                       "Thermal Conductivity W/m/K").conduct = conduct
      obj.addProperty("App::PropertyFloat","expand","GDMLmaterial", \
                      "Expansion Coefficient m/m/K").expand = expand
      obj.addProperty("App::PropertyFloat","specific","GDMLmaterial",
                      "Specific Heat J/kg/K").specific = specific

      obj.Proxy = self
      self.Object = obj

class GDMLfraction(GDMLcommon) :
   def __init__(self,obj,ref,n) :
      obj.addProperty("App::PropertyFloat",'n',ref).n = n 
      obj.Proxy = self
      self.Object = obj

class GDMLcomposite(GDMLcommon) :
   def __init__(self,obj,name,n,ref) :
      obj.addProperty("App::PropertyInteger","n",name).n = n 
      obj.addProperty("App::PropertyString","ref",name).ref = ref 
      obj.Proxy = self
      self.Object = obj

class GDMLelement(GDMLcommon) :
   def __init__(self,obj,name) :
      obj.addProperty("App::PropertyString","name",name).name = name 
      obj.Proxy = self
      self.Object = obj

class GDMLisotope(GDMLcommon) :
   def __init__(self,obj,name,N,Z,unit,value) :
      obj.addProperty("App::PropertyString","name",name).name = name 
      obj.addProperty("App::PropertyInteger","N",name).N=N
      obj.addProperty("App::PropertyInteger","Z",name).Z=Z
      obj.addProperty("App::PropertyString","unit",name).unit = unit 
      obj.addProperty("App::PropertyFloat","value",name).value = value 
      obj.Proxy = self
      self.Object = obj

class ViewProviderExtension(GDMLcommon) :
   def __init__(self, obj):
       obj.addExtension("Gui::ViewProviderGeoFeatureGroupExtensionPython", self)
       obj.Proxy = self

   def getDisplayModes(self,obj):
       '''Return a list of display modes.'''
       modes=[]
       modes.append("Shaded")
       modes.append("Wireframe")
       return modes

   def updateData(self, fp, prop):
       '''If a property of the handled feature has changed we have the chance to handle this here'''
       # fp is the handled feature, prop is the name of the property that has changed
       #l = fp.getPropertyByName("Length")
       #w = fp.getPropertyByName("Width")
       #h = fp.getPropertyByName("Height")
       #self.scale.scaleFactor.setValue(float(l),float(w),float(h))
       pass

   def getDefaultDisplayMode(self):
       '''Return the name of the default display mode. It must be defined in getDisplayModes.'''
       return "Shaded"
 

# use general ViewProvider if poss
class ViewProvider(GDMLcommon):
   def __init__(self, obj):
       '''Set this object to the proxy object of the actual view provider'''
       obj.Proxy = self
 
   def updateData(self, fp, prop):
       '''If a property of the handled feature has changed we have the chance to handle this here'''
       #print("updateData")
       # fp is the handled feature, prop is the name of the property that has changed
       #l = fp.getPropertyByName("Length")
       #w = fp.getPropertyByName("Width")
       #h = fp.getPropertyByName("Height")
       #self.scale.scaleFactor.setValue(float(l),float(w),float(h))
       pass
 
   def getDisplayModes(self,obj):
       '''Return a list of display modes.'''
       #print("getDisplayModes")
       modes=[]
       modes.append("Shaded")
       modes.append("Wireframe")
       return modes
 
   def getDefaultDisplayMode(self):
       '''Return the name of the default display mode. It must be defined in getDisplayModes.'''
       return "Shaded"
 
   def setDisplayMode(self,mode):
       '''Map the display mode defined in attach with those defined in getDisplayModes.\
               Since they have the same names nothing needs to be done. This method is optional'''
       return mode
 
   def onChanged(self, vp, prop):
       '''Here we can do something when a single property got changed'''
       #if hasattr(vp,'Name') :
       #   print("View Provider : "+vp.Name+" State : "+str(vp.State)+" prop : "+prop)
       #else :   
       #   print("View Provider : prop : "+prop)
       #GDMLShared.trace("Change property: " + str(prop) + "\n")
       #if prop == "Color":
       #    c = vp.getPropertyByName("Color")
#    self.color.rgb.setValue(c[0],c[1],c[2])    

   def getIcon(self):
       '''Return the icon in XPM format which will appear in the tree view. This method is\
               optional and if not defined a default icon is shown.'''
       return """
           /* XPM */
           static const char * ViewProviderBox_xpm[] = {
           "16 16 6 1",
           "   c None",
           ".  c #141010",
           "+  c #615BD2",
           "@  c #C39D55",
           "#  c #000000",
           "$  c #57C355",
           "        ........",
           "   ......++..+..",
           "   .@@@@.++..++.",
           "   .@@@@.++..++.",
           "   .@@  .++++++.",
           "  ..@@  .++..++.",
           "###@@@@ .++..++.",
           "##$.@@$#.++++++.",
           "#$#$.$$$........",
           "#$$#######      ",
           "#$$#$$$$$#      ",
           "#$$#$$$$$#      ",
           "#$$#$$$$$#      ",
           " #$#$$$$$#      ",
           "  ##$$$$$#      ",
           "   #######      "};
           """
   def __getstate__(self):
       '''When saving the document this object gets stored using Python's json module.\
               Since we have some un-serializable parts here -- the Coin stuff -- we must define this method\
               to return a tuple of all serializable objects or None.'''
       return None

   def __setstate__(self,state):
       '''When restoring the serialized object from document we have the chance to set some internals here.\
               Since no data were serialized nothing needs to be done here.'''
       return None

#
#   Need to add variables to these functions or delete?
#
def makeBox():
    a=FreeCAD.ActiveDocument.addObject("App::FeaturePython","GDMLBox")
    GDMLBox(a)
    ViewProvider(a.ViewObject)

def makeCone():
    a=FreeCAD.ActiveDocument.addObject("App::FeaturePython","GDMLCone")
    GDMLCone(a)
    ViewProvider(a.ViewObject)

def makecSphere():
    a=FreeCAD.ActiveDocument.addObject("App::FeaturePython","GDMLSphere")
    GDMLSphere(a)
    ViewProvider(a.ViewObject)

def makeTube():
    a=FreeCAD.ActiveDocument.addObject("App::FeaturePython","GDMLTube")
    GDMLTube(a)
    ViewProvider(a.ViewObject)

