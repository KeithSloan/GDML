import FreeCAD, FreeCADGui, Part
from pivy import coin
import math
import GDMLShared

# Global Material List
global MaterialsList
MaterialsList = []

def checkFullCircle(aunit, angle) :
    if aunit == 'deg' and angle == 360 :
       return True
    if aunit == 'rad' and angle == math.pi :
       return True
    return False

# Get angle in Radians
def getAngle(aunit,angle) :
   print("aunit : "+str(aunit))
   if aunit == 'deg' :   # 0 radians 1 Degrees
      return(angle*math.pi/180)
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
    print("Make Frustrum : "+str(num)+" Faces")
    faces = []
    for i in range(num) :
       j = i + 1
       print([poly0[i],poly0[j],poly1[j],poly1[i]])
       w = Part.makePolygon([poly0[i],poly0[j],poly1[j],poly1[i],poly0[i]])
       faces.append(Part.Face(w))
    print("Number of Faces : "+str(len(faces)))
    return(faces)

def angleSectionSolid(fp, rmax, z, shape) :
    # Different Solids have different rmax and height
    import math
    print("aunit : "+fp.aunit)
    print("startphi : "+str(fp.startphi))
    print("deltaphi : "+str(fp.deltaphi))
    startphirad = getAngle(fp.aunit,fp.startphi)
    deltaphirad = getAngle(fp.aunit,fp.deltaphi)
    print("startphirad : "+str(startphirad))
    print("deltaphirad : "+str(deltaphirad))
    x1 = rmax*math.cos(startphirad)
    y1 = rmax*math.sin(startphirad)
    x2 = rmax*math.cos(startphirad+deltaphirad)
    y2 = rmax*math.sin(startphirad+deltaphirad)
    v1 = FreeCAD.Vector(0,0,0)
    v2 = FreeCAD.Vector(x1,y1,0)
    v3 = FreeCAD.Vector(x2,y2,0)
    v4 = FreeCAD.Vector(0,0,z)
    v5 = FreeCAD.Vector(x1,y1,z)
    v6 = FreeCAD.Vector(x2,y2,z)

    # Make the wires/faces
    f1 = make_face3(v1,v2,v3)
    f2 = make_face4(v1,v3,v6,v4)
    f3 = make_face3(v4,v6,v5)
    f4 = make_face4(v5,v2,v1,v4)
    shell=Part.makeShell([f1,f2,f3,f4])
    solid=Part.makeSolid(shell)
    if deltaphirad < math.pi :
       return(shape.common(solid))
    else :   
       return(shape.cut(solid))

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
   def __init__(self, obj, x, y, z, lunit, material):
      '''Add some custom properties to our Box feature'''
      GDMLShared.trace("GDMLBox init")
      obj.addProperty("App::PropertyLength","x","GDMLBox","Length x").x=x
      obj.addProperty("App::PropertyLength","y","GDMLBox","Length y").y=y
      obj.addProperty("App::PropertyLength","z","GDMLBox","Length z").z=z
      obj.addProperty("App::PropertyString","lunit","GDMLBox","lunit").lunit=lunit
      obj.addProperty("App::PropertyEnumeration","material","GDMLBox","Material")
      obj.material = MaterialsList
      obj.material = 0
      if material != 0 : obj.material = MaterialsList.index(material)
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLBox", "Shape of the Box")
      obj.Proxy = self
      self.Type = 'GDMLBox'

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if not ('Restore' in fp.State) :
          #if prop in ['x','y','z','lunit']  :
          if prop in ['x','y','z']  :
             self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)

   def createGeometry(self,fp):
       print(fp)
       if all((fp.x,fp.y,fp.z)) :
       #if (hasattr(fp,'x') and hasattr(fp,'y') and hasattr(fp,'z')) :
          box = Part.makeBox(fp.x,fp.y,fp.z)
          base = FreeCAD.Vector(-fp.x/2,-fp.y/2,-fp.z/2)
          fp.Shape = translate(box,base)

class GDMLCone(GDMLcommon) :
   def __init__(self, obj, rmin1,rmax1,rmin2,rmax2,z,startphi,deltaphi,aunit, \
                lunit, material):
      '''Add some custom properties to our Cone feature'''
      obj.addProperty("App::PropertyDistance","rmin1","GDMLCone","Min Radius 1").rmin1=rmin1
      obj.addProperty("App::PropertyDistance","rmax1","GDMLCone","Max Radius 1").rmax1=rmax1
      obj.addProperty("App::PropertyDistance","rmin2","GDMLCone","Min Radius 2").rmin2=rmin2
      obj.addProperty("App::PropertyDistance","rmax2","GDMLCone","Max Radius 2").rmax2=rmax2
      obj.addProperty("App::PropertyLength","z","GDMLCone","Height of Cone").z=z
      obj.addProperty("App::PropertyFloat","startphi","GDMLCone","Start Angle").startphi=startphi
      obj.addProperty("App::PropertyFloat","deltaphi","GDMLCone","Delta Angle").deltaphi=deltaphi
      obj.addProperty("App::PropertyEnumeration","aunit","GDMLCone","aunit")
      obj.aunit=["rad", "deg"]
      obj.aunit=['rad','deg'].index(aunit[0:3])
      obj.addProperty("App::PropertyString","lunit","GDMLCone","lunit").lunit=lunit
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLCone", \
                      "Shape of the Cone")
      obj.addProperty("App::PropertyEnumeration","material","GDMLCone", \
                       "Material")
      obj.material = MaterialsList
      obj.material = 0
      if material != 0 : obj.material = MaterialsList.index(material)
      self.Type = 'GDMLCone'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if not ('Restore' in fp.State) :
          if prop in ['rmin1','rmax1','rmin2','rmax2','z','startphi','deltaphi' \
               ,'aunit', 'lunit'] :
             self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)

   def createGeometry(self,fp):
       print("fp : ")
       print(vars(fp))
       #if all((fp.rmin1,fp.rmin2,fp.rmax1,fp.rmax2,fp.z)) :
       if (hasattr(fp,'rmin1') and hasattr(fp,'rmax1') and \
           hasattr(fp,'rmin2') and hasattr(fp,'rmax2') and \
           hasattr(fp,'z')) :
       # Need to add code to check variables will make a valid cone
       # i.e.max > min etc etc
          print("execute cone")
          print(fp.rmax1)
          print(fp.rmax2)
          print(fp.z)
       
          cone1 = Part.makeCone(fp.rmin1,fp.rmax1,fp.z)
          if (fp.rmin1 != fp.rmin2 or fp.rmax1 != fp.rmax2 ) :
             cone2 = Part.makeCone(fp.rmin2,fp.rmax2,fp.z)
             if fp.rmax1 > fp.rmax2 :                
                cone3 = cone1.cut(cone2)
             else :
                cone3 = cone2.cut(cone1)
          else :
             cone3 = cone1
          base = FreeCAD.Vector(0,0,-fp.z/2)
          if checkFullCircle(fp.aunit,fp.deltaphi) == False :
             rmax = max(fp.rmax1, fp.rmax2)
             cone = angleSectionSolid(fp, rmax, fp.z, cone3)
             fp.Shape = translate(cone,base)
          else :   
             fp.Shape = translate(cone3,base)

class GDMLElCone(GDMLcommon) :
   def __init__(self, obj, dx, dy, zmax, zcut, lunit, material) :
      '''Add some custom properties to our ElCone feature'''
      obj.addProperty("App::PropertyDistance","dx","GDMLElCone", \
                      "x semi axis").dx = dx
      obj.addProperty("App::PropertyDistance","dy","GDMLElCone", \
                      "y semi axis").dy = dy
      obj.addProperty("App::PropertyDistance","zmax","GDMLElCone", \
                      "z length").zmax = zmax
      obj.addProperty("App::PropertyDistance","zcut","GDMLElCone", \
                      "z cut").zcut = zcut
      obj.addProperty("App::PropertyString","lunit","GDMLElCone", \
                      "lunit").lunit=lunit
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLElCone", \
                      "Shape of the Cone")
      obj.addProperty("App::PropertyEnumeration","material","GDMLElCone", \
                       "Material")
      obj.material = MaterialsList
      obj.material = 0
      if material != 0 : obj.material = MaterialsList.index(material)
      self.Type = 'GDMLElCone'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if not ('Restore' in fp.State) :
          if prop in ['dx','dy','zmax','zcut','lunit'] :
             self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       cone1 = Part.makeCone(100,0,100)
       mat = FreeCAD.Matrix()
       mat.unity()
       # Semi axis values so need to double
       dx = 2*fp.dx
       dy = 2*fp.dy
       zcut = fp.zcut
       zmax = fp.zmax
       mat.A11 = dx / 100
       mat.A22 = dy / 100
       mat.A33 = zmax / 100
       mat.A44 = 1
       cone2 = cone1.transformGeometry(mat)
       if zcut != None :
          box = Part.makeBox(dx,dy,zcut)
          pl = FreeCAD.Placement()
          # Only need to move to semi axis
          pl.move(FreeCAD.Vector(-fp.dx,-fp.dy,zmax-zcut))
          box.Placement = pl
          fp.Shape = cone2.cut(box)
       else :
          fp.Shape = cone2
       GDMLShared.trace("Recompute GDML ElCone Object \n")

class GDMLEllipsoid(GDMLcommon) :
   def __init__(self, obj, ax, by, cz, zcut1, zcut2, lunit, material) :
      '''Add some custom properties to our Elliptical Tube feature'''
      obj.addProperty("App::PropertyDistance","ax","GDMLEllipsoid", \
                       "x semi axis").ax=ax
      obj.addProperty("App::PropertyDistance","by","GDMLEllipsoid", \
                       "y semi axis").by=by
      obj.addProperty("App::PropertyDistance","cz","GDMLEllipsoid", \
                       "z semi axis").cz=cz
      obj.addProperty("App::PropertyDistance","zcut1","GDMLEllipsoid", \
                       "z axis cut1").zcut1=zcut1
      obj.addProperty("App::PropertyDistance","zcut2","GDMLEllipsoid", \
                       "z axis1 cut2").zcut2=zcut2
      obj.addProperty("App::PropertyString","lunit","GDMLEllipsoid","lunit"). \
                        lunit=lunit
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLEllipsoid", \
                      "Shape of the Ellipsoid")
      obj.addProperty("App::PropertyEnumeration","material","GDMLEllipsoid", \
                       "Material")
      obj.material = MaterialsList
      obj.material = 0
      if material != 0 : obj.material = MaterialsList.index(material)
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLEllipsoid", \
                      "Shape of the Ellipsoid")
      self.Type = 'GDMLEllipsoid'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if not ('Restore' in fp.State) :
          if prop in ['ax','by','cz','zcut1','zcut2','lunit'] :
             self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       sphere = Part.makeSphere(100)
       ax = fp.ax
       by = fp.by
       cz = fp.cz
       mat = FreeCAD.Matrix()
       mat.unity()
       # Semi axis values so need to double
       mat.A11 = ax / 100
       mat.A22 = by / 100
       mat.A33 = cz / 100
       mat.A44 = 1
       zcut1 = abs(fp.zcut1)
       zcut2 = abs(fp.zcut2)
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
       GDMLShared.trace("Recompute GDML Ellipsoid Object \n")

class GDMLElTube(GDMLcommon) :
   def __init__(self, obj, dx, dy, dz, lunit, material) :
      '''Add some custom properties to our Elliptical Tube feature'''
      obj.addProperty("App::PropertyDistance","dx","GDMLElTube", \
                       "x semi axis1").dx=dx
      obj.addProperty("App::PropertyDistance","dy","GDMLElTube", \
                       "y semi axis1").dy=dy
      obj.addProperty("App::PropertyDistance","dz","GDMLElTube", \
                       "z semi axis1").dz=dz
      obj.addProperty("App::PropertyString","lunit","GDMLElTube","lunit"). \
                        lunit=lunit
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLElTube", \
                      "Shape of the Cone")
      obj.addProperty("App::PropertyEnumeration","material","GDMLElTube", \
                       "Material")
      obj.material = MaterialsList
      obj.material = 0
      if material != 0 : obj.material = MaterialsList.index(material)
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLElTube", \
                      "Shape of the ElTube")
      self.Type = 'GDMLElTube'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       '''Do something when a property has changed'''
       if not ('Restore' in fp.State) :
          if prop in ['dx','dy','dz','lunit'] :
             self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       tube = Part.makeCylinder(100,100)
       mat = FreeCAD.Matrix()
       mat.unity()
       mat.A11 = fp.dx / 100
       mat.A22 = fp.dy / 100
       mat.A33 = fp.dz / 50
       mat.A44 = 1
       #trace mat
       newtube = tube.transformGeometry(mat)
       base = FreeCAD.Vector(0,0,-fp.dz/2)
       fp.Shape = translate(newtube,base)
       GDMLShared.trace("Recompute GDML ElTube Object \n")

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
      obj.material = MaterialsList
      obj.material = 0
      if material != 0 : obj.material = MaterialsList.index(material)
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLPolyhedra", \
                      "Shape of the Polyhedra")
      self.Type = 'GDMLPolyhedra'
      self.Object = obj
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if not ('Restore' in fp.State) :
          if prop in ['startphi', 'deltaphi', 'numsides', 'aunit','lunit'] :
             self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       print("Execute Polyhedra")
       parms = fp.OutList
       GDMLShared.trace("Number of parms : "+str(len(parms)))
       numsides = fp.numsides
       GDMLShared.trace("Number of sides : "+str(numsides))
       z0    = parms[0].z
       rmin0 = parms[0].rmin
       rmax0 = parms[0].rmax
       GDMLShared.trace("Top z    : "+str(z0))
       GDMLShared.trace("Top rmin : "+str(rmin0))
       GDMLShared.trace("Top rmax : "+str(rmax0))
       inner_faces = []
       outer_faces = []
       # Deal with Inner Top Face
       if rmin0 > 0 :
          inner_poly0 = makeRegularPolygon(numsides,rmin0,z0)
          inner_faces.append(Part.Face(Part.makePolygon(inner_poly0)))
       # Deal with Outer Top Face 
       outer_poly0 = makeRegularPolygon(numsides,rmax0,z0)
       outer_faces.append(Part.Face(Part.makePolygon(outer_poly0)))
       for ptr in parms[1:] :
           z1 = ptr.z
           rmin1 = ptr.rmin
           rmax1 = ptr.rmax
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
       GDMLShared.trace("Recompute GDML Polyhedra")

class GDMLXtru(GDMLcommon) :
   def __init__(self, obj, lunit, material) :
      obj.addExtension('App::OriginGroupExtensionPython', self)
      obj.addProperty("App::PropertyString","lunit","GDMLXtru", \
                      "lunit").lunit=lunit
      obj.addProperty("App::PropertyEnumeration","material","GDMLXtru", \
                       "Material")
      obj.material = MaterialsList
      obj.material = 0
      if material != 0 : obj.material = MaterialsList.index(material)
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLXtru", \
                      "Shape of the Xtru")
      self.Type = 'GDMLXtru'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if not ('Restore' in fp.State) :
          if prop in ['startphi','deltaphi','aunit','lunit'] :
             #self.execute(fp)
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
       for ptr in parms :
           if hasattr(ptr,'x') :
              x = ptr.x
              y = ptr.y
              GDMLShared.trace('x : '+str(x))
              GDMLShared.trace('y : '+str(y))
              polyList.append([x, y])
           if hasattr(ptr,'zOrder') :
              zOrder = ptr.zOrder
              xOffset = ptr.xOffset
              yOffset = ptr.yOffset
              zPosition = ptr.zPosition
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
           xOffset1   = sections[s][1]
           yOffset1   = sections[s][2]
           zPosition1 = sections[s][3]
           sf1        = sections[s][4]
           xOffset2   = sections[s+1][1]
           yOffset2   = sections[s+1][2]
           zPosition2 = sections[s+1][3]
           sf2        = sections[s+1][4]
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
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       #if prop in ['x','y'] :
       #   self.execute(fp)
       GDMLShared.trace("Change property: " + str(prop) + "\n")

   def execute(self, fp):
       GDMLShared.trace("Recompute GDML 2dVertex Object \n")
      
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
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       #if prop in ['zOrder','zPosition','xOffset','yOffset','scaleFactor'] :
       #   self.execute(fp)
       GDMLShared.trace("Change property: " + str(prop) + "\n")

   def execute(self, fp):
       GDMLShared.trace("Recompute GDML 2dVertex Object \n")
      
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
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       #if not ('Restore' in fp.State) :
       #if prop in ['rmin','rmax','z'] :
       #   self.execute(fp)
       GDMLShared.trace("Change property: " + str(prop) + "\n")

   def execute(self, fp):
       GDMLShared.trace("Recompute GDML zplane Object \n")
      
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
      obj.material = MaterialsList
      obj.material = 0
      if material != 0 : obj.material = MaterialsList.index(material)
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLPolycone", \
                      "Shape of the Polycone")
      self.Type = 'GDMLPolycone'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if not ('Restore' in fp.State) :
          if prop in ['startphi','deltaphi','aunit','lunit'] :
             #print(dir(fp)) 
             self.createGeometry(fp)

       GDMLShared.trace("Change property: " + str(prop) + "\n")

   def execute(self, fp):
       self.createGeometry(fp)

   def createGeometry(self,fp) :    
       zplanes = fp.OutList
       cones = []
       GDMLShared.trace("Number of zplanes : "+str(len(zplanes)))
       for i in range(0,len(zplanes)-1) :
           GDMLShared.trace('index : '+str(i))
           h = zplanes[i+1].z - zplanes[i].z
           rm1 = zplanes[i].rmin
           rm2 = zplanes[i+1].rmin
           rM1 = zplanes[i].rmax
           rM2 = zplanes[i+1].rmax
           GDMLShared.trace('height :'+str(h))
           GDMLShared.trace('rm1 :'+str(rm1)+' rm2 :'+str(rm2))
           GDMLShared.trace('rM1 :'+str(rM1)+' rM2 :'+str(rM2))
           if rm1 != rm2 :
              coneInner = Part.makeCone(rm1,rm2,h) 
           else :
              coneInner = Part.makeCylinder(rm1,h)
           if rM1 != rM2 :
              coneOuter = Part.makeCone(rM1,rM2,h) 
           else :
              coneOuter = Part.makeCylinder(rM1,h)
           cones.append(coneOuter.cut(coneInner))

       cone = cones[0]
       GDMLShared.trace("Number of cones : "+str(len(cones)))
       if len(cones) > 1 :
          for merge in cones[1:] :
              cone = cone.fuse(merge)
       if checkFullCircle(fp.aunit,fp.deltaphi) == False :
          fp.Shape = angleSectionSolid(fp, rM1, h, cone)
       else :
          fp.Shape = cone    
       GDMLShared.trace("Recompute GDMLPolycone Object \n")

class GDMLSphere(GDMLcommon) :
   def __init__(self, obj, rmin, rmax, startphi, deltaphi, starttheta, \
                deltatheta, aunit, lunit, material):
      '''Add some custom properties to our Sphere feature'''
      GDMLShared.trace("GDMLSphere init")
      obj.addProperty("App::PropertyLength","rmin","GDMLSphere", \
              "Inside Radius").rmin=rmin
      obj.addProperty("App::PropertyLength","rmax","GDMLSphere", \
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
      obj.material = MaterialsList
      obj.material = 0
      if material != 0 : obj.material = MaterialsList.index(material)
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLSphere", \
                      "Shape of the Sphere")
      obj.Proxy = self
      self.Type = 'GDMLSphere'

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if not ('Restore' in fp.State) :
          if prop in ['rmin','rmax','startphi','deltaphi','starttheta', \
                    'deltatheta','aunit','lunit'] :
             self.createGeometry(fp)
   
   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       import math
       # Need to add code to check values make a valid sphere
       cp = FreeCAD.Vector(0,0,0)
       axis_dir = FreeCAD.Vector(0,0,1)
       #sphere1 = Part.makeSphere(fp.rmin, cp, axis_dir, fp.startphi, \
       #            fp.startphi+fp.deltaphi, fp.deltatheta)
       #sphere2 = Part.makeSphere(fp.rmax, cp, axis_dir, fp.startphi, \
       #            fp.startphi+fp.deltaphi, fp.deltatheta)
       sphere2 = Part.makeSphere(fp.rmax, cp, axis_dir)
       
       #sphere3 = sphere2.cut(sphere1)
       fp.Shape = sphere2
       GDMLShared.trace("Recompute GDML Sphere Object \n")

class GDMLTrap(GDMLcommon) :
   def __init__(self, obj, z, theta, phi, x1, x2, x3, x4, y1, y2, alpha, \
                aunit, lunit, material):
      "General Trapezoid"
      obj.addProperty("App::PropertyLength","z","GDMLTrap","z").z=z
      obj.addProperty("App::PropertyFloat","theta","GDMLTrap","theta"). \
                       theta=theta
      obj.addProperty("App::PropertyFloat","phi","GDMLTrap","phi").phi=phi
      obj.addProperty("App::PropertyLength","x1","GDMLTrap", \
                      "Length x at y= -y1 face -z").x1=x1
      obj.addProperty("App::PropertyLength","x2","GDMLTrap", \
                      "Length x at y= +y1 face -z").x2=x2
      obj.addProperty("App::PropertyLength","x3","GDMLTrap", \
                      "Length x at y= -y1 face +z").x3=x3
      obj.addProperty("App::PropertyLength","x4","GDMLTrap", \
                      "Length x at y= +y1 face +z").x4=x4
      obj.addProperty("App::PropertyLength","y1","GDMLTrap", \
                      "Length y at face -z").y1=y1
      obj.addProperty("App::PropertyLength","y2","GDMLTrap", \
                      "Length y at face +z").y2=y2
      obj.addProperty("App::PropertyFloat","alpha","GDMLTrap","alpha"). \
                     alpha=alpha
      obj.addProperty("App::PropertyEnumeration","aunit","GDMLTrap","aunit")
      obj.aunit=["rad", "deg"]
      obj.aunit=['rad','deg'].index(aunit[0:3])
      obj.addProperty("App::PropertyString","lunit","GDMLTrap","lunit"). \
                       lunit=lunit
      obj.addProperty("App::PropertyEnumeration","material","GDMLTrap","Material")
      obj.material = MaterialsList
      obj.material = 0
      if material != 0 : obj.material = MaterialsList.index(material)
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLTrap", \
                      "Shape of the Trap")
      obj.Proxy = self
      self.Type = 'GDMLTrap'

   def onChanged(self, fp, prop):
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if not ('Restore' in fp.State) :
          if prop in ['z','theta','phi','x1','x2','x3','x4','y1','y2','alpha', \
                   'aunit', 'lunit'] :
             self.createGeometry(fp)
   
   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       import math
       # Define six vetices for the shape
       alpha = getAngle(fp.aunit,fp.alpha)
       theta = getAngle(fp.aunit,fp.theta)
       phi   = getAngle(fp.aunit,fp.phi)
       dx = fp.y1*math.sin(alpha)
       dy = fp.y1*(1.0 - math.cos(alpha))
       GDMLShared.trace("Delta adjustments")
       GDMLShared.trace("dx : "+str(dx)+" dy : "+str(dy))
       y1m = dy - fp.y1
       y1p = dy + fp.y1
       x1m = dx - fp.x1
       x1p = dx + fp.x1
       z    = fp.z
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
       py2 = ty + fp.y2
       my2 = ty - fp.y2
       px3 = tx + fp.x3
       mx3 = tx - fp.x3
       px4 = tx + fp.x4
       mx4 = tx - fp.x4
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
       GDMLShared.trace("Recompute GDML Trap Object \n")

class GDMLTrd(GDMLcommon) :
   def __init__(self, obj, z, x1, x2,  y1, y2, lunit, material) :
      "3.4.15 : Trapezoid – x & y varying along z"
      obj.addProperty("App::PropertyLength","z","GDMLTrd`","z").z=z
      obj.addProperty("App::PropertyLength","x1","GDMLTrd", \
                      "Length x at y= -y1 face -z").x1=x1
      obj.addProperty("App::PropertyLength","x2","GDMLTrd", \
                      "Length x at y= +y1 face -z").x2=x2
      obj.addProperty("App::PropertyLength","y1","GDMLTrd", \
                      "Length y at face -z").y1=y1
      obj.addProperty("App::PropertyLength","y2","GDMLTrd", \
                      "Length y at face +z").y2=y2
      obj.addProperty("App::PropertyString","lunit","GDMLTrd","lunit"). \
                       lunit=lunit
      obj.addProperty("App::PropertyEnumeration","material","GDMLTrd","Material") 
      obj.material = MaterialsList
      obj.material = 0
      if material != 0 : obj.material = MaterialsList.index(material)
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLTrd", \
                      "Shape of the Trap")
      obj.Proxy = self
      self.Type = 'GDMLTrd'

   def onChanged(self, fp, prop):
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if not ('Restore' in fp.State) :
          if prop in ['z','x1','x2','y1','y2','lunit'] :
             self.createGeometry(fp)
   
   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       import math
       GDMLShared.trace("x2  : "+str(fp.x2))

       x1 = fp.x1/2
       x2 = fp.x2/2
       y1 = fp.y1/2
       y2 = fp.y2/2
       z  = fp.z
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
       GDMLShared.trace("Recompute GDML Trd Object \n")

class GDMLTube(GDMLcommon) :
   def __init__(self, obj, rmin, rmax, z, startphi, deltaphi, aunit,  \
                lunit, material):
      '''Add some custom properties to our Tube feature'''
      obj.addProperty("App::PropertyLength","rmin","GDMLTube","Inside Radius").rmin=rmin
      obj.addProperty("App::PropertyLength","rmax","GDMLTube","Outside Radius").rmax=rmax
      obj.addProperty("App::PropertyLength","z","GDMLTube","Length z").z=z
      obj.addProperty("App::PropertyFloat","startphi","GDMLTube","Start Angle").startphi=startphi
      obj.addProperty("App::PropertyFloat","deltaphi","GDMLTube","Delta Angle").deltaphi=deltaphi
      obj.addProperty("App::PropertyEnumeration","aunit","GDMLTube","aunit")
      obj.aunit=['rad','deg']
      obj.aunit=['rad','deg'].index(aunit[0:3])
      obj.addProperty("App::PropertyString","lunit","GDMLTube","lunit").lunit=lunit
      obj.addProperty("App::PropertyEnumeration","material","GDMLTube","Material")
      obj.material = MaterialsList
      obj.material = 0
      if material != 0 : obj.material = MaterialsList.index(material)
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLTube", "Shape of the Tube")
      obj.Proxy = self
      self.Type = 'GDMLTube'

   def onChanged(self, fp, prop):
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if not ('Restore' in fp.State) :
          if prop in ['rmin','rmax','z','startphi','deltaphi','aunit',  \
                   'lunit'] :
             self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       # Need to add code to check values make a valid Tube
       # Define six vetices for the shape
       cyl1 = Part.makeCylinder(fp.rmax,fp.z)
       cyl2 = Part.makeCylinder(fp.rmin,fp.z)
       cyl3 = cyl1.cut(cyl2) 

       if checkFullCircle(fp.aunit,fp.deltaphi) == False :
          tube = angleSectionSolid(fp, fp.rmax, fp.z, cyl3)
       else :
          tube = cyl3
       #base = FreeCAD.Vector(0,0,fp.z/2)
       #base = FreeCAD.Vector(0,0,0)
       base = FreeCAD.Vector(0,0,-fp.z/2)
       fp.Shape = translate(tube,base)
       #fp.Shape = solid
       GDMLShared.trace("Recompute GDML Tube Object \n")

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
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       #if not ('Restore' in fp.State) :
       #   if prop in ['x','y', 'z'] :
       #      self.execute(fp)
       GDMLShared.trace("Change property: " + str(prop) + "\n")

   def execute(self, fp):
       GDMLShared.trace("Recompute GDML Vertex Object \n")
       

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
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       #if not ('Restore' in fp.State) :
       #   if prop in ['v1','v2','v3','type'] :
       #      self.execute(fp)
       GDMLShared.trace("Change property: " + str(prop) + "\n")

   def execute(self, fp):
       GDMLShared.trace("Recompute GDML Triangular Object \n")
       
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
       GDMLShared.trace("Change property: " + str(prop) + "\n")

   def execute(self, fp):
       GDMLShared.trace("Recompute GDML Quqdrang\n")
       
class GDMLTessellated(GDMLcommon) :
    
   def __init__(self, obj, material ) :
      obj.addExtension('App::OriginGroupExtensionPython', self)
      obj.addProperty("Part::PropertyPartShape","Shape","GDMLTessellated", "Shape of the Tesssellation")
      obj.addProperty("App::PropertyEnumeration","material","GDMLTessellated","Material")
      obj.material = MaterialsList
      obj.material = 0
      if material != 0 : obj.material = MaterialsList.index(material)
      self.Type = 'GDMLTessellated'
      self.Object = obj
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if not ('Restore' in fp.State) :
          if prop in ['v1','v2','v3','v4','type'] :
             self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       print("Tessellated")
       parms = fp.OutList
       GDMLShared.trace("Number of parms : "+str(len(parms)))
       faces = []
       for ptr in parms :
           #print(dir(ptr))
           if hasattr(ptr,'v4') :
              print("Quad")
              print(ptr.v1)
              print(ptr.v2)
              print(ptr.v3)
              print(ptr.v4)
              faces.append(GDMLShared.quad(ptr.v1,ptr.v2,ptr.v3,ptr.v4))

           else :   
              print("Triangle")
              print("Vertex 1")
              print(ptr.v1)
              print("Vertex 2")
              print(ptr.v2)
              print("Vertex 3")
              print(ptr.v3)
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

   def onChanged(self, fp, prop):
       print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if not ('Restore' in fp.State) :
          if not hasattr(fp,'onchange') or not fp.onchange : return

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
   def __init__(self,obj,ref,n) :
      obj.addProperty("App::PropertyInteger",'n',ref).n = n 
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
       print("updateData")
       # fp is the handled feature, prop is the name of the property that has changed
       #l = fp.getPropertyByName("Length")
       #w = fp.getPropertyByName("Width")
       #h = fp.getPropertyByName("Height")
       #self.scale.scaleFactor.setValue(float(l),float(w),float(h))
       pass
 
   def getDisplayModes(self,obj):
       '''Return a list of display modes.'''
       print("getDisplayModes")
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
       if hasattr(vp,'Name') :
          print("View Provider : "+vp.Name+" State : "+str(vp.State)+" prop : "+prop)
       else :   
          print("View Provider : prop : "+prop)
       GDMLShared.trace("Change property: " + str(prop) + "\n")
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

