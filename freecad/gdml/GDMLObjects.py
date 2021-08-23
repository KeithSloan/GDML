# -*- coding: utf8 -*-
#**************************************************************************
#*                                                                        *
#*   Copyright (c) 2017 Keith Sloan <keith@sloan-home.co.uk>              *
#*             (c) Dam Lambert 2020                                          *
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

import FreeCAD, FreeCADGui, Part
from pivy import coin
import math
from . import GDMLShared

# Global Material List
global MaterialsList
MaterialsList = []

global LengthQuantityList
LengthQuantityList =  ['nm','um', 'mm','cm', 'dm','m', 'km']
# cf definition https://wiki.freecadweb.org/Quantity


def setLengthQuantity(obj, m) :
    if LengthQuantityList != None :
        obj.lunit = LengthQuantityList
        obj.lunit = 0
        if len(LengthQuantityList) > 0 :
            if not ( m == 0 or m == None ) : 
                obj.lunit = LengthQuantityList.index(m)
    else :
        obj.lunit = 2

def checkMaterial(material) :
    global MaterialsList
    try :
       i = MaterialsList.index(material)
    except ValueError:
       return False
    return True

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
    # helper method to create the faces
    wire = Part.makePolygon([v1,v2,v3,v1])
    face = Part.Face(wire)
    return face

def make_face4(v1,v2,v3,v4):
    # helper method to create the faces
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
    s1 = f1.revolve(v1,v4,360-deltaPhiDeg)
    # Problem with FreeCAD 0.18
    #s2 = s1.rotate(v1,v4,startPhiDeg)

    #Part.show(s2)
    #return(shape.cut(s2))
    #return(s2)
    
    shape = shape.cut(s1)
    if startPhiDeg != 0 :
        shape.rotate(FreeCAD.Vector(0,0,0), \
                            FreeCAD.Vector(0,0,1),startPhiDeg)
    return shape

def setMaterial(obj, m) :
    #print('setMaterial')
    if MaterialsList != None :
        obj.material = MaterialsList
        obj.material = 0
        if len(MaterialsList) > 0 :
            if not ( m == 0 or m == None ) : 
                obj.material = MaterialsList.index(m)
    else :
        obj.Material = 0

def indiceToRay(indiceIn):	# Thanks to Dam
    if indiceIn<1: 
        return 0
    else:
        lray=[0.0, 1.0]
        puissanceDown=2
        while len(lray) <= indiceIn:
            for indiceTmp in range(1,puissanceDown,2):
                lray.append(float(indiceTmp)/float(puissanceDown))
            puissanceDown = 2 * puissanceDown
        return lray[indiceIn]
	
def colorFromRay(rayIn):	# Thanks to Dam
    coeffR=coeffG=coeffB=1.0

    if(rayIn<0.2 and rayIn>=0.0):
        coeffR=1.0
        coeffG=rayIn*5.0
        coeffB=0.0
    elif(rayIn<0.4):
        coeffR=2.0-(5.0*rayIn)
        coeffG=1.0
        coeffB=0.0
    elif(rayIn<0.6):
        coeffR=0.0
        coeffG=1.0
        coeffB=rayIn*5.0-2.0
    elif(rayIn<0.8):
        coeffR=1.0
        coeffG=4.0-(5.0*rayIn)
        coeffB=1.0
    elif(rayIn<=1.0):
        coeffR=(5.0*rayIn)-4.0
        coeffG=0.0
        coeffB=1.0
    return (coeffR,coeffG,coeffB)

def colourMaterial(m):

   if MaterialsList == None :
        return (0.5,0.5,0.5)
   else :
       if ( m == None ) : 
           return (0.5,0.5,0.5)
       elif(len(MaterialsList)<=1):
           return (0.5,0.5,0.5)
       elif m not in MaterialsList :
            return (0.5,0.5,0.5)
       else:
           coeffRGB = MaterialsList.index(m)
           return colorFromRay(indiceToRay(coeffRGB))

class GDMLColourMapEntry :
   def __init__(self,obj,colour,material) :
      obj.addProperty("App::PropertyColor","colour", \
          "GDMLColourMapEntry","colour").colour=colour
      obj.addProperty("App::PropertyEnumeration","material", \
          "GDMLColourMapEntry","Material")
      setMaterial(obj, material)

def indexBoolean(list,ln) :
    #print('Length : '+str(ln))
    if ln > 3 :
       #print(range(ln-3))
       for r in range(ln-2,-1,-1) :
          t = list[r].TypeId
          #print(t)
          if t == 'Part::Cut' or t == 'Part::Fuse' or t == 'Part::Common' :
             return r 
    return -1 
	   
class GDMLsolid :
   def __init__(self, obj):
       '''Init'''
       #print('>>>>>')
       #if hasattr(obj,'Label') :
       #   print('Label : '+obj.Label)
       #print('TypeId : '+obj.TypeId)
       #print(dir(obj))
       #if hasattr(obj,'InList') :
       #   print('InList')
       #   print(obj.InList)
       #   for i in obj.InList :
       #       print(i.TypeId)
       #       if hasattr(i,'Label') :
       #          print('Label : '+i.Label)
       #       if i.TypeId == 'App::Part' :
       #          print(i.OutList)
       #          for j in i.OutList :
       #             print('   ==> Typeid'+str(j.TypeId))
       #             if hasattr(j,'Label') :
       #                print('    ==> Label'+j.Label)
       #                
       #print('<<<<<')    
       if hasattr(obj,'InList') :
          for j in obj.InList :
              if hasattr(j,'OutList') :
                 ln = len(j.OutList)
                 r = indexBoolean(j.OutList,ln)
                 #print('index : '+str(r))
              if r >= 0 : 
                 if (ln - r) >= 2 :
                    #print('Tool : '+obj.Label)
                    return   # Let Placement default to 0
       obj.setEditorMode('Placement',2)

   def __getstate__(self):
      '''When saving the document this object gets stored using Python's json module.\
                Since we have some un-serializable parts here -- the Coin stuff -- we must define this method\
                to return a tuple of all serializable objects or None.'''
      if hasattr(self,'Type') :
         return {'type' : self.Type }
      else :
         pass
 
   def __setstate__(self, arg):
      '''When restoring the serialized object from document we have the chance to set some internals here. Since no data were serialized nothing needs to be done here.'''
      self.Type = arg['type']

class GDMLcommon :
   def __init__(self, obj):
       '''Init'''
   
   def __getstate__(self):
      '''When saving the document this object gets stored using Python's json module.\
                Since we have some un-serializable parts here -- the Coin stuff -- we must define this method\
                to return a tuple of all serializable objects or None.'''
      if hasattr(self,'Type') : # If not saved just return
         return {'type' : self.Type }
      else :
         pass
 
   def __setstate__(self,arg):
      '''When restoring the serialized object from document we have the chance to set some internals here.\
                Since no data were serialized nothing needs to be done here.'''
      if arg is not None :
         self.Type = arg['type']

class GDMLArb8(GDMLsolid) :        # Thanks to Dam Lamb
   def __init__(self, obj, v1x, v1y, v2x, v2y, v3x, v3y, v4x, v4y,  \
                v5x, v5y, v6x, v6y, v7x, v7y, v8x, v8y, dz, \
                lunit, material, colour = None):
      '''Add some custom properties to our Tube feature'''
      obj.addProperty("App::PropertyFloat","v1x","GDMLArb8","vertex 1 x position").v1x=v1x
      obj.addProperty("App::PropertyFloat","v1y","GDMLArb8","vertex 1 y position").v1y=v1y
      obj.addProperty("App::PropertyFloat","v2x","GDMLArb8","vertex 2 x position").v2x=v2x
      obj.addProperty("App::PropertyFloat","v2y","GDMLArb8","vertex 2 y position").v2y=v2y
      obj.addProperty("App::PropertyFloat","v3x","GDMLArb8","vertex 3 x position").v3x=v3x
      obj.addProperty("App::PropertyFloat","v3y","GDMLArb8","vertex 3 y position").v3y=v3y
      obj.addProperty("App::PropertyFloat","v4x","GDMLArb8","vertex 4 x position").v4x=v4x
      obj.addProperty("App::PropertyFloat","v4y","GDMLArb8","vertex 4 y position").v4y=v4y
      obj.addProperty("App::PropertyFloat","v5x","GDMLArb8","vertex 5 x position").v5x=v5x
      obj.addProperty("App::PropertyFloat","v5y","GDMLArb8","vertex 5 y position").v5y=v5y
      obj.addProperty("App::PropertyFloat","v6x","GDMLArb8","vertex 6 x position").v6x=v6x
      obj.addProperty("App::PropertyFloat","v6y","GDMLArb8","vertex 6 y position").v6y=v6y
      obj.addProperty("App::PropertyFloat","v7x","GDMLArb8","vertex 7 x position").v7x=v7x
      obj.addProperty("App::PropertyFloat","v7y","GDMLArb8","vertex 7 y position").v7y=v7y
      obj.addProperty("App::PropertyFloat","v8x","GDMLArb8","vertex 8 x position").v8x=v8x
      obj.addProperty("App::PropertyFloat","v8y","GDMLArb8","vertex 8 y position").v8y=v8y
      obj.addProperty("App::PropertyFloat","dz","GDMLArb8","Half z Length").dz=dz
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLArb8","lunit")
      setLengthQuantity(obj, lunit)      
      obj.addProperty("App::PropertyEnumeration","material","GDMLArb8","Material")
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colour
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      obj.Proxy = self
      self.Type = 'GDMLArb8'
      self.colour = colour

   def onChanged(self, fp, prop):
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return

       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['v1x', 'v1y', 'v2x','v2y', 'v3x', 'v3y', 'v4x', 'v4y',  \
                'v5x', 'v5y', 'v6x', 'v6y', 'v7x', 'v7y', 'v8x', 'v8y', 'dz','lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)

# http://geant4-userdoc.web.cern.ch/geant4-userdoc/UsersGuides/ForApplicationDeveloper/html/Detector/Geometry/geomSolids.html
# The order of specification of the coordinates for the vertices in G4GenericTrap is important. The first four points are the vertices sitting on the -hz plane; the last four points are the vertices sitting on the +hz plane.
#
#The order of defining the vertices of the solid is the following:
#
#    point 0 is connected with points 1,3,4
#    point 1 is connected with points 0,2,5
#    point 2 is connected with points 1,3,6
#    point 3 is connected with points 0,2,7
#    point 4 is connected with points 0,5,7
#    point 5 is connected with points 1,4,6
#    point 6 is connected with points 2,5,7
#    point 7 is connected with points 3,4,6

   def createGeometry(self,fp):

        currPlacement = fp.Placement
        mul  = GDMLShared.getMult(fp)

        pt1 = FreeCAD.Vector(fp.v1x*mul,fp.v1y*mul,-fp.dz*mul)
        pt2 = FreeCAD.Vector(fp.v2x*mul,fp.v2y*mul,-fp.dz*mul)
        pt3 = FreeCAD.Vector(fp.v3x*mul,fp.v3y*mul,-fp.dz*mul)
        pt4 = FreeCAD.Vector(fp.v4x*mul,fp.v4y*mul,-fp.dz*mul)
        pt5 = FreeCAD.Vector(fp.v5x*mul,fp.v5y*mul,fp.dz*mul)
        pt6 = FreeCAD.Vector(fp.v6x*mul,fp.v6y*mul,fp.dz*mul)
        pt7 = FreeCAD.Vector(fp.v7x*mul,fp.v7y*mul,fp.dz*mul)
        pt8 = FreeCAD.Vector(fp.v8x*mul,fp.v8y*mul,fp.dz*mul)

        faceZmin = Part.Face(Part.makePolygon([pt1,pt2,pt3,pt4,pt1]))
        faceZmax = Part.Face(Part.makePolygon([pt5,pt6,pt7,pt8,pt5]))

        faceXminA = Part.Face(Part.makePolygon([pt1,pt2,pt6,pt1]))
        faceXminB = Part.Face(Part.makePolygon([pt6,pt5,pt1,pt6]))
        faceXmaxA = Part.Face(Part.makePolygon([pt4,pt3,pt7,pt4])) 
        faceXmaxB = Part.Face(Part.makePolygon([pt8,pt4,pt7,pt8])) 

        faceYminA = Part.Face(Part.makePolygon([pt1,pt8,pt4,pt1]))
        faceYminB = Part.Face(Part.makePolygon([pt1,pt5,pt8,pt1]))

        faceYmaxA = Part.Face(Part.makePolygon([pt2,pt3,pt7,pt2]))
        faceYmaxB = Part.Face(Part.makePolygon([pt2,pt7,pt6,pt2]))
        
        
        fp.Shape = Part.makeSolid(Part.makeShell([faceXminA,faceXminB,faceXmaxA,faceXmaxB,
                                                  faceYminA,faceYminB,faceYmaxA,faceYmaxB,
                                                  faceZmin,faceZmax]))
        fp.Placement = currPlacement 

class GDMLBox(GDMLsolid) :
   def __init__(self, obj, x, y, z, lunit, material, colour=None):
      super().__init__(obj)
      '''Add some custom properties to our Box feature'''
      GDMLShared.trace("GDMLBox init")
      #GDMLShared.trace("material : "+material)
      obj.addProperty("App::PropertyFloat","x","GDMLBox","Length x").x=x
      obj.addProperty("App::PropertyFloat","y","GDMLBox","Length y").y=y
      obj.addProperty("App::PropertyFloat","z","GDMLBox","Length z").z=z
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLBox","lunit")
      setLengthQuantity(obj, lunit)
      obj.addProperty("App::PropertyEnumeration","material","GDMLBox","Material")
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colour
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      self.Type = 'GDMLBox'
      self.colour = colour
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
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)
       
       if prop in ['x','y','z','lunit']  :
             self.createGeometry(fp) 

   def execute(self, fp):
       #print('execute')
       self.createGeometry(fp)

   def createGeometry(self,fp):
       #print('createGeometry')
       #print(fp)

       if all((fp.x,fp.y,fp.z)) :
          currPlacement = fp.Placement

       #if (hasattr(fp,'x') and hasattr(fp,'y') and hasattr(fp,'z')) :
          mul = GDMLShared.getMult(fp)
          GDMLShared.trace('mul : '+str(mul))
          x = mul * fp.x
          y = mul * fp.y
          z = mul * fp.z
          box = Part.makeBox(x,y,z)
          base = FreeCAD.Vector(-x/2,-y/2,-z/2)
          fp.Shape = translate(box,base)
          fp.Placement = currPlacement
    
   def OnDocumentRestored(self,obj) :
       print('Doc Restored')
          

class GDMLCone(GDMLsolid) :
   def __init__(self, obj, rmin1,rmax1,rmin2,rmax2,z,startphi,deltaphi,aunit, \
                lunit, material, colour = None):
      super().__init__(obj)
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
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLCone","lunit")
      setLengthQuantity(obj, lunit)      

      
      obj.addProperty("App::PropertyEnumeration","material","GDMLCone", \
                       "Material")
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colour
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      self.Type = 'GDMLCone'
      obj.Proxy = self
   
   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if  'Restore' in fp.State :
           return

       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

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
          currPlacement = fp.Placement
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
          fp.Placement = currPlacement   

class GDMLElCone(GDMLsolid) :
   def __init__(self, obj, dx, dy, zmax, zcut, lunit, material, colour = None) :
      super().__init__(obj)
      '''Add some custom properties to our ElCone feature'''
      obj.addProperty("App::PropertyFloat","dx","GDMLElCone", \
                      "x semi axis").dx = dx
      obj.addProperty("App::PropertyFloat","dy","GDMLElCone", \
                      "y semi axis").dy = dy
      obj.addProperty("App::PropertyFloat","zmax","GDMLElCone", \
                      "z length").zmax = zmax
      obj.addProperty("App::PropertyFloat","zcut","GDMLElCone", \
                      "z cut").zcut = zcut
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLElCone","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material","GDMLElCone", \
                       "Material")
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colour
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      self.Type = 'GDMLElCone'
      obj.Proxy = self
   
   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return  
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)
       
       if prop in ['dx','dy','zmax','zcut','lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       currPlacement = fp.Placement
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
       fp.Placement = currPlacement   

class GDMLEllipsoid(GDMLsolid) :
   def __init__(self, obj, ax, by, cz, zcut1, zcut2, lunit, material, colour = None) :
      super().__init__(obj)
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
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLEllipsoid","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material","GDMLEllipsoid", \
                       "Material")
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None : 
            obj.ViewObject.ShapeColor = colour
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      self.Type = 'GDMLEllipsoid'
      self.colour = colour
      obj.Proxy = self
   
   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['ax','by','cz','zcut1','zcut2','lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       currPlacement = fp.Placement
       mul = GDMLShared.getMult(fp)
       sphere = Part.makeSphere(100)
       ax = fp.ax * mul
       by = fp.by * mul
       cz = fp.cz * mul
       mat = FreeCAD.Matrix()
       mat.unity()
       # Semi axis values so need to double
       mat.A11 = ax / 50
       mat.A22 = by / 50
       mat.A33 = cz / 50
       mat.A44 = 1
       zcut1 = abs(fp.zcut1*mul)
       zcut2 = abs(fp.zcut2*mul)
       GDMLShared.trace("zcut2 : "+str(zcut2))
       t1ellipsoid = sphere.transformGeometry(mat) 
       if zcut2 != None and zcut2 > 0 and zcut2 < cz:   # Remove from upper z
          box1 = Part.makeBox(2*ax,2*by,zcut2)
          pl = FreeCAD.Placement()
          # Only need to move to semi axis
          pl.move(FreeCAD.Vector(-ax,-by,cz-zcut2))
          box1.Placement = pl
          t2ellipsoid = t1ellipsoid.cut(box1)
       else :
          t2ellipsoid = t1ellipsoid 
       if zcut1 != None and zcut1 > 0 and zcut1 < cz:
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
       fp.Placement = currPlacement

class GDMLElTube(GDMLsolid) :
   def __init__(self, obj, dx, dy, dz, lunit, material, colour=None) :
      super().__init__(obj)
      '''Add some custom properties to our Elliptical Tube feature'''
      obj.addProperty("App::PropertyFloat","dx","GDMLElTube", \
                       "x semi axis1").dx=dx
      obj.addProperty("App::PropertyFloat","dy","GDMLElTube", \
                       "y semi axis1").dy=dy
      obj.addProperty("App::PropertyFloat","dz","GDMLElTube", \
                       "z semi axis1").dz=dz
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLElTube","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material","GDMLElTube", \
                       "Material")
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colourMaterial(material)
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      self.Type = 'GDMLElTube'
      self.colour = colour
      obj.Proxy = self
   
   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       '''Do something when a property has changed'''
       if 'Restore' in fp.State :
          return

       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['dx','dy','dz','lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       currPlacement = fp.Placement
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
       base = FreeCAD.Vector(0,0,-(fp.dz*mul)/2)
       fp.Shape = translate(newtube,base)
       fp.Placement = currPlacement

class GDMLOrb(GDMLsolid) :
   def __init__(self, obj, r, lunit, material, colour=None) :
      super().__init__(obj)
      '''Add some custom properties for Polyhedra feature'''
      obj.addProperty("App::PropertyFloat","r","GDMLOrb","Radius").r=r
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLOrb","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material","GDMLOrb", \
                       "Material")
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colour
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      self.Type = 'GDMLOrb'
      self.Object = obj
      obj.Proxy = self
   
   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['r', 'lunit'] :
          #print(dir(fp))
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)

   def createGeometry(self,fp):
       currPlacement = fp.Placement
       #GDMLShared.setTrace(True)
       GDMLShared.trace("Execute Orb")
       mul = GDMLShared.getMult(fp.lunit)
       r = mul * fp.r
       fp.Shape = Part.makeSphere(r)
       fp.Placement = currPlacement

class GDMLPara(GDMLsolid) :
   def __init__(self, obj, x, y, z, alpha, theta, phi, aunit, lunit, \
                material, colour= None) :
      super().__init__(obj)
      '''Add some custom properties for Polyhedra feature'''
      obj.addProperty("App::PropertyFloat","x","GDMLParapiped","x").x=x
      obj.addProperty("App::PropertyFloat","y","GDMLParapiped","y").y=y
      obj.addProperty("App::PropertyFloat","z","GDMLParapiped","z").z=z
      obj.addProperty("App::PropertyFloat","alpha","GDMLParapiped", \
                      "Angle with y axis").alpha=alpha
      obj.addProperty("App::PropertyFloat","theta","GDMLParapiped", \
                      "Polar Angle with faces").theta=theta
      obj.addProperty("App::PropertyFloat","phi","GDMLParapiped", \
                      "Azimuthal Angle with faces").phi=phi
      obj.addProperty("App::PropertyEnumeration","aunit","GDMLParapiped", \
                       "aunit")
      obj.aunit=["rad", "deg"]
      obj.aunit=['rad','deg'].index(aunit[0:3])
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLParapiped","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material","GDMLParapiped", \
                       "Material")
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colour
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      self.Type = 'GDMLPara'
      self.colour = colour
      self.Object = obj
      obj.Proxy = self
   
   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['x', 'y', 'z', 'alpha', 'theta', 'phi', 'aunit','lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       currPlacement = fp.Placement
       #GDMLShared.setTrace(True)
       import math
       GDMLShared.trace("Execute Polyparallepiped")
       mul = GDMLShared.getMult(fp)
       x = mul * fp.x
       y = mul * fp.y
       z = mul * fp.z
       alpha = getAngleRad(fp.aunit,fp.alpha)
       theta = getAngleRad(fp.aunit,fp.theta)
       phi   = getAngleRad(fp.aunit,fp.phi)
       #dir1 = FreeCAD.Vector(400,0,0)
       dir1 = FreeCAD.Vector(x,0,0)
       #dir2 = FreeCAD.Vector(400*math.tan(alpha),400,0)
       dir2 = FreeCAD.Vector(y*math.tan(alpha),y,0)
       #dir3 = FreeCAD.Vector(400/math.tan(phi),0,400)
       #dir3 = FreeCAD.Vector(z/math.tan(30*math.pi/180),0,z)
       if phi != 0 :
            dir3 = FreeCAD.Vector(400/math.tan(phi),0,400)
       else : 
            dir3 = FreeCAD.Vector(0,0,z)
       #print(dir1)
       #print(dir2)
       #print(dir3)
       para0 = Part.Vertex(0,0,0)
       para1 = para0.extrude(dir1)
       para2 = para1.extrude(dir2)
       para3 = para2.extrude(dir3)
       base = FreeCAD.Vector(-x/2,-y/2,-z/2)
       fp.Shape = translate(para3,base)
       fp.Placement = currPlacement
   
class GDMLPolyhedra(GDMLsolid) :
   def __init__(self, obj, startphi, deltaphi, numsides, aunit, lunit, \
                material, colour = None) :
      super().__init__(obj)
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
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLPolyhdera","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material","GDMLPolyhedra", \
                       "Material")
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colourMaterial(material)
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      self.Type = 'GDMLPolyhedra'
      self.Object = obj
      obj.Proxy = self
   
   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['startphi', 'deltaphi', 'numsides', 'aunit','lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       currPlacement = fp.Placement
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
       fp.Placement = currPlacement   

class GDMLTorus(GDMLsolid) :
   def __init__(self, obj, rmin, rmax, rtor, startphi, deltaphi, \
                aunit, lunit, material, colour = None) :
      super().__init__(obj)
      obj.addProperty("App::PropertyFloat","rmin","GDMLTorus", \
                      "rmin").rmin=rmin
      obj.addProperty("App::PropertyFloat","rmax","GDMLTorus", \
                      "rmax").rmax=rmax
      obj.addProperty("App::PropertyFloat","rtor","GDMLTorus", \
                      "rtor").rtor=rtor
      obj.addProperty("App::PropertyFloat","startphi","GDMLTorus", \
                      "startphi").startphi=startphi
      obj.addProperty("App::PropertyFloat","deltaphi","GDMLTorus", \
                      "deltaphi").deltaphi=deltaphi
      obj.addProperty("App::PropertyString","aunit","GDMLTorus", \
                      "aunit").aunit=aunit
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLTorus","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material","GDMLTorus", \
                       "Material")
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colourMaterial(material)
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      self.Type = 'GDMLTorus'
      self.colour = colour
      obj.Proxy = self
   
   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is not None :
                fp.ViewObject.ShapeColor = colour
             else :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['rmin', 'rmax', 'rtor','startphi','deltaphi', \
                   'aunit','lunit'] :
          self.createGeometry(fp)
            
   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       currPlacement = fp.Placement
       GDMLShared.trace("Create Torus")
       mul = GDMLShared.getMult(fp)
       rmin = mul*fp.rmin
       rmax = mul*fp.rmax
       rtor = mul*fp.rtor

       spnt = FreeCAD.Vector(0,0,0)
       sdir = FreeCAD.Vector(0,0,1)

       innerTorus = Part.makeTorus(rtor,rmin,spnt,sdir,0,360,  \
                    getAngleDeg(fp.aunit, fp.deltaphi))
       outerTorus = Part.makeTorus(rtor,rmax,spnt,sdir,0,360,  \
                    getAngleDeg(fp.aunit, fp.deltaphi))
       torus = outerTorus.cut(innerTorus)
       if fp.startphi != 0 :
            torus.rotate(spnt,sdir,getAngle(fp.aunit,fp.startphi))
       fp.Shape = torus     
       fp.Placement = currPlacement

class GDMLXtru(GDMLsolid) :
   def __init__(self, obj, lunit, material, colour = None) :
      super().__init__(obj)
      obj.addExtension('App::GroupExtensionPython')
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLXtru","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material","GDMLXtru", \
                       "Material")
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colourMaterial(material)
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      self.Type = 'GDMLXtru'
      obj.Proxy = self

   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self. colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['startphi','deltaphi','aunit','lunit'] :
          self.createGeometry(fp)
            
   def execute(self, fp):
       self.createGeometry(fp)
  
   def layerPoints(self,polyList,sf,xOffset,yOffset,zPosition):
       vl = []
       for p in polyList :
           #print(p)
           vl.append(FreeCAD.Vector(p[0]*sf+xOffset, p[1]*sf+yOffset,zPosition))
       # Close list
       vl.append(vl[0])
       return vl

   def createGeometry(self,fp):
       #GDMLShared.setTrace(True)
       currPlacement = fp.Placement
       #print("Create Geometry")
       parms = fp.OutList
       #print("OutList")
       #print(parms)
       GDMLShared.trace("Number of parms : "+str(len(parms)))
       polyList = []
       faceList = []
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
              sf = ptr.scalingFactor * mul
              s = [zOrder,xOffset,yOffset,zPosition,sf]
              sections.append(s)
       #print('sections : '+str(len(sections)))
       #
       # Deal with Base Face
       #
       #baseList = layerPoints(polyList,sf,xOffset,yOffset,zPosition):
       baseList = self.layerPoints(polyList,sections[0][4],sections[0][1], \
                              sections[0][2],sections[0][3])
       #print('baseList')
       #print(baseList)
       w1 = Part.makePolygon(baseList)
       f1 = Part.Face(w1)
       f1.reverse()
       faceList.append(f1)
       #print("base list")
       # 
       # Deal with Sides 
       #
       #print("Start Range "+str(len(sections)-1))
       for s in range(0,len(sections)-1) :
           xOffset   = sections[s+1][1]
           yOffset   = sections[s+1][2]
           zPosition = sections[s+1][3]
           sf2       = sections[s+1][4]
           #layerList = layerPoints(polyList,sf,xOffset,yOffset,zPosition)
           layerList = self.layerPoints(polyList,sf,xOffset,yOffset,zPosition)
           # deal with side faces
           # remember first point is added to end of list
           #print("Number Sides : "+str(len(baseList)-1))
           for i in range(0,len(baseList)-2) :
               sideList = []
               sideList.append(baseList[i])
               sideList.append(baseList[i+1])
               sideList.append(layerList[i+1])
               sideList.append(layerList[i])
               # Close SideList polygon
               sideList.append(baseList[i])
               #print("sideList")
               #print(sideList)
               w1 = Part.makePolygon(sideList)
               f1 = Part.Face(w1)
               faceList.append(f1)
       #  
       # Deal with Top Face
       #
       w1 = Part.makePolygon(layerList)
       f1 = Part.Face(w1)
       #f1.reverse()
       faceList.append(f1)
       #print("Faces List")
       #print(faceList)
       shell=Part.makeShell(faceList)
       #solid=Part.Solid(shell).removeSplitter()
       solid=Part.Solid(shell)
       #print("Valid Solid : "+str(solid.isValid()))
       if solid.Volume < 0:
          solid.reverse()
       #print(dir(fp))       
       #solid.exportBrep("/tmp/"+fp.Label+".brep")       
       fp.Shape = solid
       fp.Placement = currPlacement

class GDML2dVertex(GDMLcommon) :
   def __init__(self, obj, x, y):
      super().__init__(obj)
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
      super().__init__(obj)
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
      super().__init__(obj)
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

class GDMLPolycone(GDMLsolid) : # Thanks to Dam Lamb
   def __init__(self, obj, startphi, deltaphi, aunit, lunit, material, colour = None) :
      super().__init__(obj)
      '''Add some custom properties to our Polycone feature'''
      obj.addExtension('App::GroupExtensionPython')
      obj.addProperty("App::PropertyFloat","startphi","GDMLPolycone", \
              "Start Angle").startphi=startphi
      obj.addProperty("App::PropertyFloat","deltaphi","GDMLPolycone", \
             "Delta Angle").deltaphi=deltaphi
      obj.addProperty("App::PropertyEnumeration","aunit","GDMLPolycone","aunit")
      obj.aunit=["rad", "deg"]
      obj.aunit=['rad','deg'].index(aunit[0:3])
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLPolycone","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material","GDMLPolycone", \
                       "Material")
      setMaterial(obj, material)
      # For debugging
      #obj.setEditorMode('Placement',0)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colourMaterial(material)
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      self.Type = 'GDMLPolycone'
      self.colour = colour
      obj.Proxy = self

   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['startphi','deltaphi','aunit','lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)

   def createGeometry(self,fp) :

       currPlacement = fp.Placement
       zplanes = fp.OutList
       #GDMLShared.trace("Number of zplanes : "+str(len(zplanes)))
       mul = GDMLShared.getMult(fp.lunit)
       offset = zplanes[0].z * mul
       angleDeltaPhiDeg = 360.0
       if (hasattr(fp,'deltaphi')) :
           angleDeltaPhiDeg = min([getAngleDeg(fp.aunit,fp.deltaphi), angleDeltaPhiDeg])
       if(angleDeltaPhiDeg <=0.0): return

       listShape = [0 for i in range((len(zplanes)-1))]

       sinPhi = 0.0
       cosPhi = 1.0
       if fp.startphi != 0 :
           angleRad = getAngleRad(fp.aunit,fp.startphi)
           sinPhi = math.sin(angleRad)
           cosPhi = math.cos(angleRad)

       # loops on each z level
       for i in range(len(zplanes)-1) :
           GDMLShared.trace('index : '+str(i))
           if i == 0:
               rmin1 = zplanes[i].rmin * mul
               rmax1 = zplanes[i].rmax * mul
               z1 = zplanes[i].z * mul - offset
           else:
               rmin1 = rmin2
               rmax1 = rmax2
               z1 = z2

           rmin2 = zplanes[i+1].rmin * mul
           rmax2 = zplanes[i+1].rmax * mul
           z2 = zplanes[i+1].z * mul - offset

           # def of one face to rotate
           face = Part.Face(Part.makePolygon( [ \
                   FreeCAD.Vector(rmin1*cosPhi,rmin1*sinPhi,z1),
                   FreeCAD.Vector(rmax1*cosPhi,rmax1*sinPhi,z1),
                   FreeCAD.Vector(rmax2*cosPhi,rmax2*sinPhi,z2),
                   FreeCAD.Vector(rmin2*cosPhi,rmin2*sinPhi,z2),
                   FreeCAD.Vector(rmin1*cosPhi,rmin1*sinPhi,z1)]))
           # rotation of the face
           listShape[i] = face.revolve(FreeCAD.Vector(0,0,0),FreeCAD.Vector(0,0,1),angleDeltaPhiDeg)
       # compound of all faces
       fp.Shape = Part.makeCompound(listShape)
       fp.Placement = currPlacement

class GDMLSphere(GDMLsolid) :
   def __init__(self, obj, rmin, rmax, startphi, deltaphi, starttheta, \
                deltatheta, aunit, lunit, material, colour = None ):
      super().__init__(obj)
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
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLSphere","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material","GDMLSphere", \
                       "Material")
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colour
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      obj.Proxy = self
      self.Type = 'GDMLSphere'
      self.colour = colour

   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['rmin','rmax','startphi','deltaphi','starttheta', \
                    'deltatheta','aunit','lunit'] :
          self.createGeometry(fp)
   
   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       # Based on code by Dam Lamb
       import math
       currPlacement = fp.Placement
       mul = GDMLShared.getMult(fp)
       rmax = mul * fp.rmax
       if rmax <= 0.0: return
       Rmax = 2 * rmax
       rmin = mul * fp.rmin
       spos = FreeCAD.Vector(0,0,0)
       sdir = FreeCAD.Vector(0,0,1)
       HalfPi = math.pi / 2.0
       TwoPi = 2 * math.pi
       deltaphi_deg = getAngleDeg(fp.aunit, fp.deltaphi)
       if deltaphi_deg < 360.0 and deltaphi_deg > 0:
            sphere2 = Part.makeSphere(rmax,spos,sdir, \
                     -90.0, 90.0, \
                     deltaphi_deg)
            if fp.startphi != 0 :
                sphere2.rotate(spos, sdir, getAngleDeg(fp.aunit,fp.startphi))
       else :
            sphere2 = Part.makeSphere(rmax)

       # if starttheta > 0 cut the upper cone     
       startthetaRad = getAngleRad(fp.aunit, fp.starttheta)     
       startthetaDeg = getAngleDeg(fp.aunit, fp.starttheta)       
         
       if startthetaDeg > 0.0 :
            if startthetaDeg == 90.0 :
                cylToCut = Part.makeCylinder(2.0*rmax,rmax, \
                                      FreeCAD.Vector(0,0,0))	
                sphere2 = sphere2.cut(cylToCut)
            elif startthetaDeg < 90.0 :	    
                sphere2 = sphere2.cut(Part.makeCone(0.0, \
                            rmax*math.sin(startthetaRad), rmax*math.cos(startthetaRad)))
                
                cylToCut = Part.makeCylinder(2.0*rmax,rmax, \
                                      FreeCAD.Vector(0,0,rmax*math.cos(startthetaRad)))		
                sphere2 = sphere2.cut(cylToCut)				
							    
            elif startthetaDeg < 180.0 :
                sphere2 = sphere2.common(Part.makeCone(0.0, \
                        rmax/math.cos(math.pi-startthetaRad),rmax, spos, \
                        FreeCAD.Vector(0,0,-1.0)))
     
       # if deltatheta -> cut the down cone
       deltathetaRad = getAngleRad(fp.aunit, fp.deltatheta)
       thetaSumRad= startthetaRad + deltathetaRad
       if thetaSumRad < math.pi :
            if thetaSumRad > HalfPi :

                sphere2 = sphere2.cut(Part.makeCone(0.0, \
                            rmax*math.sin(math.pi - thetaSumRad), \
                            rmax*math.cos(math.pi - thetaSumRad), \
                            spos, FreeCAD.Vector(0,0,-1.0)))

                cylToCut = Part.makeCylinder(2.0*rmax,rmax, \
                                      FreeCAD.Vector(0,0,rmax*(-1.0 + math.cos(thetaSumRad)))  )		
                sphere2 = sphere2.cut(cylToCut)	

            elif thetaSumRad == HalfPi :
                cylToCut = Part.makeCylinder(2.0*rmax,rmax, \
                                      FreeCAD.Vector(0,0,-rmax))	
                sphere2 = sphere2.cut(cylToCut)
            elif thetaSumRad > 0 :    
                sphere2 = sphere2.common(Part.makeCone(0.0, \
                                      2*rmax*math.tan( thetaSumRad), \
                                      2*rmax  ))
     
       if rmin <= 0 or rmin > rmax :
           fp.Shape = sphere2
       else :
           fp.Shape = sphere2.cut(Part.makeSphere(rmin))
       fp.Placement = currPlacement 
           

class GDMLTrap(GDMLsolid) :
   def __init__(self, obj, z, theta, phi, x1, x2, x3, x4, y1, y2, alpha, \
                aunit, lunit, material, colour = None):
      super().__init__(obj)
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
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLTrap","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material","GDMLTrap","Material")
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colour
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      obj.Proxy = self
      self.Type = 'GDMLTrap'
      self.colour = colour

   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['z','theta','phi','x1','x2','x3','x4','y1','y2','alpha', \
                   'aunit', 'lunit'] :
          self.createGeometry(fp)
   
   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       import math
       currPlacement = fp.Placement
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
       fp.Placement = currPlacement

class GDMLTrd(GDMLsolid) :
   def __init__(self, obj, z, x1, x2,  y1, y2, lunit, material, colour = None) :
      super().__init__(obj)
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
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLTrd","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material","GDMLTrd","Material") 
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colourMaterial(material)
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      obj.Proxy = self
      self.Type = 'GDMLTrd'
      self.colour = colour

   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['z','x1','x2','y1','y2','lunit'] :
          self.createGeometry(fp)
   
   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       import math
       currPlacement = fp.Placement
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
       fp.Placement = currPlacement

class GDMLTube(GDMLsolid) :
   def __init__(self, obj, rmin, rmax, z, startphi, deltaphi, aunit,  \
                lunit, material, colour = None):
      super().__init__(obj)
      '''Add some custom properties to our Tube feature'''
      obj.addProperty("App::PropertyFloat","rmin","GDMLTube","Inside Radius").rmin=rmin
      obj.addProperty("App::PropertyFloat","rmax","GDMLTube","Outside Radius").rmax=rmax
      obj.addProperty("App::PropertyFloat","z","GDMLTube","Length z").z=z
      obj.addProperty("App::PropertyFloat","startphi","GDMLTube","Start Angle").startphi=startphi
      obj.addProperty("App::PropertyFloat","deltaphi","GDMLTube","Delta Angle").deltaphi=deltaphi
      obj.addProperty("App::PropertyEnumeration","aunit","GDMLTube","aunit")
      obj.aunit=['rad','deg']
      obj.aunit=['rad','deg'].index(aunit[0:3])
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLTube","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material","GDMLTube","Material")
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colourMaterial(material)
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      obj.Proxy = self
      self.Type = 'GDMLTube'
      self.colour = colour

   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['rmin','rmax','z','startphi','deltaphi','aunit',  \
                  'lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       currPlacement = fp.Placement
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
       fp.Placement = currPlacement

class GDMLcutTube(GDMLsolid) :
   def __init__(self, obj, rmin, rmax, z, startphi, deltaphi, aunit,  \
                lowX, lowY, lowZ, highX, highY, highZ, \
                lunit, material, colour = None):
      super().__init__(obj)
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
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLcutTube","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material","GDMLcutTube","Material")
      #print('Add material')
      #print(material)
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colourMaterial(material)
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      #print(MaterialsList)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      obj.Proxy = self
      self.Type = 'GDMLcutTube'
      self.colour = colour

   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

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
        currPlacement = fp.Placement
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
        fp.Placement = currPlacement

   def createGeometry_hardcoded(self,fp):
        angle = getAngleDeg(fp.aunit,fp.deltaphi)
        pntC = FreeCAD.Vector(0,0,0)
        dirC = FreeCAD.Vector(0,0,1)
        #pntP = FreeCAD.Vector(-5,-5,5)

        tube1 = Part.makeCylinder(20,60,pntC,dirC,angle)
        tube2 = Part.makeCylinder(12,60,pntC,dirC,angle)
        tube = tube1.cut(tube2)
        #Part.show(tube1)
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
      super().__init__(obj)
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
      super().__init__(obj)
      obj.addProperty("App::PropertyVector","v1","Triangular", \
              "v1").v1=v1
      obj.addProperty("App::PropertyVector","v2","Triangular", \
              "v1").v2=v2
      obj.addProperty("App::PropertyVector","v3","Triangular", \
              "v1").v3=v3
      obj.addProperty("App::PropertyEnumeration","vtype","Triangular","vtype")
      obj.vtype=["ABSOLUTE", "RELATIVE"]
      obj.vtype=["ABSOLUTE", "RELATIVE"].index(vtype)
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
      super().__init__(obj)
      obj.addProperty("App::PropertyVector","v1","Quadrang", \
              "v1").v1=v1
      obj.addProperty("App::PropertyVector","v2","Quadrang", \
              "v2").v2=v2
      obj.addProperty("App::PropertyVector","v3","Quadrang", \
              "v3").v3=v3
      obj.addProperty("App::PropertyVector","v4","Quadrang", \
              "v4").v4=v4
      obj.addProperty("App::PropertyEnumeration","vtype","Quadrang","vtype")
      obj.vtype=["ABSOLUTE", "RELATIVE"]
      obj.vtype=0
      self.Type = 'GDMLQuadrangular'
      obj.Proxy = self

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
           return

       #if prop in ['v1','v2','v3','v4','type'] :
       #      self.execute(fp)
       #GDMLShared.trace("Change property: " + str(prop) + "\n")
       pass

   def execute(self, fp):
       pass
       
class GDMLGmshTessellated(GDMLsolid) :
    
   def __init__(self, obj, sourceObj,meshLen, vertex, facets, lunit, \
                material, colour = None) :
      super().__init__(obj)
      #obj.addProperty('App::PropertyBool','editable','GDMLGmshTessellated', \
      #                'Editable').editable = False
      obj.addProperty('App::PropertyInteger','facets','GDMLGmshTessellated', \
                      'Facets').facets = len(facets)
      obj.setEditorMode('facets',1)
      obj.addProperty('App::PropertyInteger','vertex','GDMLGmshTessellated', \
                      'Vertex').vertex = len(vertex)
      obj.setEditorMode('vertex',1)
      obj.addProperty('App::PropertyFloat','m_maxLength', \
                      'GDMLGmshTessellated', \
                      'Max Length').m_maxLength = meshLen
      obj.addProperty('App::PropertyFloat','m_curveLen','GDMLGmshTessellated', \
                      'Curve Length').m_curveLen = meshLen
      obj.addProperty('App::PropertyFloat','m_pointLen','GDMLGmshTessellated', \
                      'Point Length').m_pointLen = meshLen
      #obj.addProperty('App::PropertyBool','m_Remesh','GDMLGmshTessellated', \
      #                'ReMesh').m_Remesh = False
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLGmshTessellated","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material", \
                      "GDMLTessellated","Material")
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colourMaterial(material)
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      #print(MaterialsList)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      #obj.addExtension('App::GroupExtensionPython')
      self.Type = 'GDMLGmshTessellated'
      self.SourceObj = sourceObj
      self.Vertex = vertex
      self.Facets = facets
      self.Object = obj
      obj.Proxy = self

   def updateParams(self, vertex, facets) :
      print('Update Params')
      self.Vertex = vertex
      self.Facets = facets
      self.facets  = len(facets)
      self.vertex  = len(vertex)
      print(f"Vertex : {self.vertex} Facets : {self.facets}")

   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['editable'] :
           if fp.editable == True :
              self.addProperties()

       if prop in ['m_Remesh'] :
           if fp.m_Remesh == True :
              self.reMesh(fp)
              self.execute(fp)

       #if prop in ['v1','v2','v3','v4','type','lunit'] :
       #   self.createGeometry(fp)

   def addProperties(self) :
       print('Add Properties')

   def reMesh(self,fp) :
       from .GmshUtils import initialize, meshObj, getVertex, getFacets
 
       initialize()
       meshObj(fp.Proxy.SourceObj,2,True,fp.Proxy.Object)
       facets = getFacets()
       vertex = getVertex()
       fp.Proxy.Vertex = vertex
       self.Object.vertex = len(vertex)
       fp.Proxy.Facets = facets
       self.Object.facets = len(facets)
       FreeCADGui.updateGui()

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       currPlacement = fp.Placement
       print("Tessellated")
       mul = GDMLShared.getMult(fp)
       FCfaces = []
       #print(self.Vertex)
       i = 0
       for f in self.Facets :
          #print('Facet')
          #print(f)
          if len(f) == 3 : 
             FCfaces.append(GDMLShared.triangle( \
                             mul*self.Vertex[f[0]], \
                             mul*self.Vertex[f[1]], \
                             mul*self.Vertex[f[2]]))
          else : # len should then be 4
             FCfaces.append(GDMLShared.quad( \
                             mul*self.Vertex[f[0]], \
                             mul*self.Vertex[f[1]], \
                             mul*self.Vertex[f[2]], \
                             mul*self.Vertex[f[3]]))
       shell=Part.makeShell(FCfaces)
       if shell.isValid == False :
          FreeCAD.Console.PrintWarning('Not a valid Shell/n')
 
       #shell.check()
       #solid=Part.Solid(shell).removeSplitter()
       try :
          solid=Part.Solid(shell)
       except : 
          # make compound rather than just barf
          # visually able to view at least
          FreeCAD.Console.PrintWarning('Problem making Solid/n')
          solid = Part.makeCompound(FCfaces)
       #if solid.Volume < 0:
       #   solid.reverse()
       #print(dir(solid))   
       #bbox = solid.BoundBox
       #base = FreeCAD.Vector(-(bbox.XMin+bbox.XMax)/2, \
       #                      -(bbox.YMin+bbox.YMax)/2 \
       #                      -(bbox.ZMin+bbox.ZMax)/2)
       #print(base)

       #base = FreeCAD.Vector(0,0,0)
       #fp.Shape = translate(solid,base)
       fp.Shape = solid
       fp.Placement = currPlacement
   
class GDMLTessellated(GDMLsolid) :
    
   def __init__(self, obj, vertex, facets, lunit, material, colour = None) :
      super().__init__(obj)
      #obj.addProperty('Part::PropertyPartShape','pshape','GDMLTessellated', \
      #                 'Shape').pshape = self.createShape(vertex,facets)
      #obj.setEditorMode('pshape',1)
      obj.addProperty('App::PropertyInteger','facets','GDMLTessellated', \
                      'Facets').facets = len(facets)
      obj.setEditorMode('facets',1)
      obj.addProperty('App::PropertyInteger','vertex','GDMLTessellated', \
                      'Vertex').vertex = len(vertex)
      obj.setEditorMode('vertex',1)
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLTessellated","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material", \
                      "GDMLTessellated","Material")
      setMaterial(obj, material)
      self.updateParams(vertex, facets)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colourMaterial(material)
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      self.Type = 'GDMLTessellated'
      obj.Proxy = self

   def getMaterial(self):
       return obj.material
   
   def updateParams(self, vertex, facets) :
      print('Update Params & Shape')
      self.pshape = self.createShape(vertex,facets)
      print(f"Pshape vertex {len(self.pshape.Vertexes)}")
      self.facets  = len(facets)
      self.vertex  = len(vertex)
      print(f"Vertex : {self.vertex} Facets : {self.facets}")

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
           return
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['editable'] :
           if fp.editable == True :
              self.addProperties()

       #if prop in ['v1','v2','v3','v4','type','lunit'] :
       #   self.createGeometry(fp)

   def addProperties(self) :
       print('Add Properties')

   def execute(self, fp):
       self.createGeometry(fp)
   
   def createGeometry(self,fp):
       #currPlacement = fp.Placement
       print("Tessellated")
       #print(self.Type)
       #print('self')
       #print(dir(self))
       #print('fp')
       #print(dir(fp))
       if hasattr(self,'pshape') :
          print('Update Shape')
          fp.Shape  = self.pshape
          if hasattr(fp,'pshape') :
             fp.pshape = self.pshape
          fp.vertex = self.vertex
          fp.facets = self.facets
          print(len(fp.Shape.Vertexes))
          print(fp.Shape)
       #else :
       #   if hasattr(fp,'pshape') :
       #      fp.Shape = fp.pshape
       #      print(fp.pshape)
       #      print(dir(fp.pshape))
       #      print(f"pshape Vertextes {len(fp.pshape.Vertexes)}")
       #      print(fp.vertex)
       #      print(fp.Shape)
       #      print(fp.pshape)
       #fp.Placement = currPlacement

   def createShape(self,vertex,facets) :
       # Viewing outside of face vertex must be counter clockwise
       #mul = GDMLShared.getMult(fp)
       mul = GDMLShared.getMult(self)
       print('Create Shape')
       FCfaces = []
       i = 0
       for f in facets :
          #print('Facet')
          #print(f)
          FCfaces.append(GDMLShared.facet(f))
          #if len(f) == 3 : 
          #      FCfaces.append(GDMLShared.triangle( \
          #                   mul*vertex[f[0]], \
          #                   mul*vertex[f[1]], \
          #                   mul*vertex[f[2]]))
          #else : # len should then be 4
          #   FCfaces.append(GDMLShared.quad( \
          #                   mul*vertex[f[0]], \
          #                   mul*vertex[f[1]], \
          #                   mul*vertex[f[2]], \
          #                   mul*vertex[f[3]]))
       #print(FCfaces)
       shell=Part.makeShell(FCfaces)
       if shell.isValid == False :
          FreeCAD.Console.PrintWarning('Not a valid Shell/n')
 
       shell.check()
       #solid=Part.Solid(shell).removeSplitter()
       try :
          solid=Part.Solid(shell)
       except : 
          # make compound rather than just barf
          # visually able to view at least
          FreeCAD.Console.PrintWarning('Problem making Solid/n')
          solid = Part.makeCompound(FCfaces)
       print(f"Solid Volume {solid.Volume}")
       #if solid.Volume < 0:
       #   solid.reverse()
       #print(dir(solid))   
       #bbox = solid.BoundBox
       #base = FreeCAD.Vector(-(bbox.XMin+bbox.XMax)/2, \
       #                      -(bbox.YMin+bbox.YMax)/2 \
       #                      -(bbox.ZMin+bbox.ZMax)/2)
       #print(base)

       #base = FreeCAD.Vector(0,0,0)
       #fp.Shape = translate(solid,base)
       #fp.Shape = solid

       return solid
   
class GDMLTetra(GDMLsolid) :         # 4 point Tetrahedron
    
   def __init__(self, obj, v1, v2, v3, v4, lunit, material, colour = None ):
      super().__init__(obj)
      obj.addProperty("App::PropertyVector","v1","GDMLTra", \
              "v1").v1=v1
      obj.addProperty("App::PropertyVector","v2","GDMLTra", \
              "v2").v2=v2
      obj.addProperty("App::PropertyVector","v3","GDMLTra", \
              "v3").v3=v3
      obj.addProperty("App::PropertyVector","v4","GDMLTra", \
              "v4").v4=v4
      obj.addProperty("App::PropertyEnumeration","lunit","GDMLTra","lunit")
      setLengthQuantity(obj, lunit) 		      
      obj.addProperty("App::PropertyEnumeration","material","GDMLTra","Material")
      setMaterial(obj, material)
      if FreeCAD.GuiUp :
         if colour is not None :
            obj.ViewObject.ShapeColor = colourMaterial(material)
         else :
            obj.ViewObject.ShapeColor = colourMaterial(material)
      # Suppress Placement - position & Rotation via parent App::Part
      # this makes Placement via Phyvol easier and allows copies etc
      self.Type = 'GDMLTetra'
      self.colour = colour
      obj.Proxy = self

   def getMaterial(self):
       return obj.material

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
           return
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['v1','v2','v3','v4','lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)

   def createGeometry(self,fp) :
       currPlacement = fp.Placement
       mul = GDMLShared.getMult(fp)
       pt1 = mul * fp.v1
       pt2 = mul * fp.v2
       pt3 = mul * fp.v3
       pt4 = mul * fp.v4
       face1 = Part.Face(Part.makePolygon([pt1,pt2,pt3,pt1]))
       face2 = Part.Face(Part.makePolygon([pt1,pt2,pt4,pt1]))
       face3 = Part.Face(Part.makePolygon([pt4,pt2,pt3,pt4]))
       face4 = Part.Face(Part.makePolygon([pt1,pt3,pt4,pt1]))
       fp.Shape = Part.makeSolid(Part.makeShell([face1,face2,face3,face4]))
       fp.Placement = currPlacement
       
class GDMLTetrahedron(GDMLsolid) :

   ''' Does not exist as a GDML solid, but export as an Assembly of G4Tet '''
   ''' See paper Poole at al - Fast Tessellated solid navigation in GEANT4 '''
    
   def __init__(self, obj, tetra, lunit, material, colour=None) :
       super().__init__(obj)
       #obj.addProperty('App::PropertyBool','editable','GDMLTetrahedron', \
       #                'Editable').editable = False
       obj.addProperty('App::PropertyInteger','tetra','GDMLTetrahedron', \
                      'Tetra').tetra = len(tetra)
       obj.setEditorMode('tetra',1)
       obj.addProperty("App::PropertyEnumeration","lunit","GDMLTetrahedron","lunit")
       setLengthQuantity(obj, lunit) 		      
       obj.addProperty("App::PropertyEnumeration","material", \
                      "GDMLTetrahedron","Material")
       setMaterial(obj, material)
       if FreeCAD.GuiUp :
          if colour is not None :
             obj.ViewObject.ShapeColor = colour
          else :
             obj.ViewObject.ShapeColor = colourMaterial(material)
       # Suppress Placement - position & Rotation via parent App::Part
       # this makes Placement via Phyvol easier and allows copies etc
       #obj.addExtension('App::GroupExtensionPython')
       self.Tetra = tetra
       self.Object = obj
       self.Type = 'GDMLTetrahedron'
       self.colour = colour
       obj.Proxy = self

   def getMaterial(self):
       return self.material

   def onChanged(self, fp, prop):
       '''Do something when a property has changed'''
       #print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
       if 'Restore' in fp.State :
          return
       
       if prop in ['material'] :
          if FreeCAD.GuiUp :
             if self.colour is None :
                fp.ViewObject.ShapeColor = colourMaterial(fp.material)

       if prop in ['lunit'] :
          self.createGeometry(fp)

   def execute(self, fp):
       self.createGeometry(fp)
  
   def makeTetra(self,pt1,pt2,pt3,pt4) :
       face1 = Part.Face(Part.makePolygon([pt1,pt2,pt3,pt1]))
       face2 = Part.Face(Part.makePolygon([pt1,pt2,pt4,pt1]))
       face3 = Part.Face(Part.makePolygon([pt4,pt2,pt3,pt4]))
       face4 = Part.Face(Part.makePolygon([pt1,pt3,pt4,pt1]))
       return(Part.makeShell([face1,face2,face3,face4]))
       #return(face1,face2,face3,face4)
 
   def createGeometry(self,fp):
       currPlacement = fp.Placement
       print("Tetrahedron")
       mul = GDMLShared.getMult(fp)
       print(len(self.Tetra))
       tetraShells = []
       for t in self.Tetra :
           pt1 = mul * t[0]
           pt2 = mul * t[1]
           pt3 = mul * t[2]
           pt4 = mul * t[3]
           tetraShells.append(self.makeTetra(pt1,pt2,pt3,pt4))
       fp.Shape = Part.makeCompound(tetraShells)
       fp.Placement = currPlacement
       
class GDMLFiles(GDMLcommon) :
   def __init__(self,obj,FilesEntity,sectionDict) :
      super().__init__(obj)
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
                    "structure section").structure=sectionDict.get('structure',"")
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
      super().__init__(obj)
      obj.addProperty("App::PropertyString","name",'GDMLconstant','name').name = name
      obj.addProperty("App::PropertyString","value",'GDMLconstant','value').value = value
      obj.Proxy = self
      self.Object = obj

class GDMLvariable(GDMLcommon) :
   def __init__(self,obj,name,value) :
      super().__init__(obj)
      obj.addProperty("App::PropertyString","name",'GDMLvariable','name').name = name
      obj.addProperty("App::PropertyString","value",'GDMLvariable','value').value = value
      obj.Proxy = self
      self.Object = obj

class GDMLmaterial(GDMLcommon) :
   def __init__(self,obj,name,density=1.0,conduct=2.0,expand=3.0,specific=4.0) :
      super().__init__(obj)
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
      super().__init__(obj)
      obj.addProperty("App::PropertyFloat",'n',ref).n = n 
      obj.Proxy = self
      self.Object = obj

class GDMLcomposite(GDMLcommon) :
   def __init__(self,obj,name,n,ref) :
      super().__init__(obj)
      obj.addProperty("App::PropertyInteger","n",name).n = n 
      obj.addProperty("App::PropertyString","ref",name).ref = ref 
      obj.Proxy = self
      self.Object = obj

class GDMLelement(GDMLcommon) :
   def __init__(self,obj,name) :
      super().__init__(obj)
      obj.addProperty("App::PropertyString","name",name).name = name 
      obj.Proxy = self
      self.Object = obj

class GDMLisotope(GDMLcommon) :
   def __init__(self,obj,name,N,Z,unit,value) :
      super().__init__(obj)
      obj.addProperty("App::PropertyString","name",name).name = name 
      obj.addProperty("App::PropertyInteger","N",name).N=N
      obj.addProperty("App::PropertyInteger","Z",name).Z=Z
      obj.addProperty("App::PropertyString","unit",name).unit = unit 
      obj.addProperty("App::PropertyFloat","value",name).value = value 
      obj.Proxy = self
      self.Object = obj

class ViewProviderExtension(GDMLcommon) :
   def __init__(self, obj):
       super().__init__(obj)
       obj.addExtension("Gui::ViewProviderGroupExtensionPython")
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
       super().__init__(obj)
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

