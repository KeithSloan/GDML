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
#**************************************************************************

__title__="FreeCAD GDML Workbench - GUI Commands"
__author__ = "Keith Sloan"
__url__ = ["http://www.freecadweb.org"]

'''
This Script includes the GUI Commands of the GDML module
'''

import FreeCAD,FreeCADGui
from PySide import QtGui, QtCore

class importPrompt(QtGui.QDialog):
    def __init__(self, *args):
        super(importPrompt, self).__init__()
        self.initUI()
                
    def initUI(self):
        importButton = QtGui.QPushButton('Import')
        importButton.clicked.connect(self.onImport)
        scanButton = QtGui.QPushButton('Scan Vol')
        scanButton .clicked.connect(self.onScan)
        #
        buttonBox = QtGui.QDialogButtonBox()
        buttonBox.setFixedWidth(400)
        #buttonBox = Qt.QDialogButtonBox(QtCore.Qt.Vertical)
        buttonBox.addButton(importButton, QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(scanButton, QtGui.QDialogButtonBox.ActionRole)
        #
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
        #self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
	# define window		xLoc,yLoc,xDim,yDim
        self.setGeometry(	650, 650, 0, 50)
        self.setWindowTitle("Choose an Option    ")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.retStatus = 0

    def onImport(self):
        self.retStatus = 1
        self.close()

    def onScan(self):
        self.retStatus = 2
        self.close()

def getSelectedMaterial() :
    from .exportGDML import nameFromLabel
    from .GDMLObjects import GDMLmaterial

    list = FreeCADGui.Selection.getSelection()
    if list != None :
       for obj in list :
          if isinstance(obj.Proxy,GDMLmaterial) == True :
             return nameFromLabel(obj.Label)

    return 0

class BoxFeature:
    #    def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLBox, ViewProvider
        a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","GDMLBox_Box")
        #print("GDMLBox Object - added")
        # obj, x, y, z, lunits, material
        GDMLBox(a,10.0,10.0,10.0,"mm",getSelectedMaterial())
        #print("GDMLBox initiated")
        ViewProvider(a.ViewObject)
        #print("GDMLBox ViewProvided - added")
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument == None:
           return False
        else:
           return True

    def GetResources(self):
        return {'Pixmap'  : 'GDMLBoxFeature', 'MenuText': \
                QtCore.QT_TRANSLATE_NOOP('GDMLBoxFeature',\
                'Box Object'), 'ToolTip': \
                QtCore.QT_TRANSLATE_NOOP('GDMLBoxFeature',\
                'Box Object')}

class ConeFeature:
    #def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLCone, ViewProvider
        a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","GDMLCone_Cone")
        #print("GDMLCone Object - added")
        #  obj,rmin1,rmax1,rmin2,rmax2,z,startphi,deltaphi,aunit,lunits,material
        GDMLCone(a,1,3,4,7,10.0,0,2,"rads","mm",getSelectedMaterial())
        #print("GDMLCone initiated")
        ViewProvider(a.ViewObject)
        #print("GDMLCone ViewProvided - added")
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument == None:
           return False
        else:
           return True

    def GetResources(self):
        return {'Pixmap'  : 'GDMLConeFeature', 'MenuText': \
                QtCore.QT_TRANSLATE_NOOP('GDMLConeFeature',\
                'Cone Object'), 'ToolTip': \
                QtCore.QT_TRANSLATE_NOOP('GDMLConeFeature',\
                'Cone Object')}

class EllispoidFeature:
    #def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLEllipsoid, ViewProvider
        a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython", \
                  "GDMLEllipsoid_Ellipsoid")
        #print("GDMLEllipsoid Object - added")
        #  obj,ax, by, cz, zcut1, zcut2, lunit,material
        GDMLEllipsoid(a,10,20,30,0,0,"mm",getSelectedMaterial())
        #print("GDMLEllipsoid initiated")
        ViewProvider(a.ViewObject)
        #print("GDMLEllipsoid ViewProvided - added")
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument == None:
           return False
        else:
           return True

    def GetResources(self):
        return {'Pixmap'  : 'GDMLEllipsoidFeature', 'MenuText': \
                QtCore.QT_TRANSLATE_NOOP('GDMLEllipsoidFeature',\
                'Ellipsoid Object'), 'ToolTip': \
                QtCore.QT_TRANSLATE_NOOP('GDMLEllipsoidFeature',\
                'Ellipsoid Object')}

class ElliTubeFeature:
    #def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLElTube, ViewProvider
        a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython", \
                  "GDMLElTube_Eltube")
        #print("GDMLElTube Object - added")
        #  obj,dx, dy, dz, lunit, material
        GDMLElTube(a,10,20,30,"mm",getSelectedMaterial())
        #print("GDMLElTube initiated")
        ViewProvider(a.ViewObject)
        #print("GDMLElTube ViewProvided - added")
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument == None:
           return False
        else:
           return True

    def GetResources(self):
        return {'Pixmap'  : 'GDMLElTubeFeature', 'MenuText': \
                QtCore.QT_TRANSLATE_NOOP('GDMLElTubeFeature',\
                'ElTube Object'), 'ToolTip': \
                QtCore.QT_TRANSLATE_NOOP('GDMLElTubeFeature',\
                'ElTube Object')}

class SphereFeature:
    #def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLSphere, ViewProvider
        a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython", \
                    "GDMLSphere_Sphere")
        #print("GDMLSphere Object - added")
        # obj, rmin, rmax, startphi, deltaphi, starttheta, deltatheta,
        #       aunit, lunits, material
        GDMLSphere(a,10.0, 20.0, 0.0, 2.02, 0.0, 2.02,"rad","mm", \
                  getSelectedMaterial())
        #print("GDMLSphere initiated")
        ViewProvider(a.ViewObject)
        #print("GDMLSphere ViewProvided - added")
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument == None:
           return False
        else:
           return True

    def GetResources(self):
        return {'Pixmap'  : 'GDMLSphereFeature', 'MenuText': \
                QtCore.QT_TRANSLATE_NOOP('GDMLSphereFeature',\
                'Sphere Object'), 'ToolTip': \
                QtCore.QT_TRANSLATE_NOOP('GDMLSphereFeature',\
                'Sphere Object')}

class TrapFeature:
    #def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLTrap, ViewProvider
        a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython", \
                "GDMLTrap_Trap")
        print("GDMLTrap Object - added")
        # obj z, theta, phi, x1, x2, x3, x4, y1, y2,
        # pAlp2, aunits, lunits, material
        GDMLTrap(a,10.0,0.0,0.0,6.0,6.0,6.0,6.0,7.0,7.0,0.0,"rad","mm", \
                 getSelectedMaterial())
        print("GDMLTrap initiated")
        ViewProvider(a.ViewObject)
        print("GDMLTrap ViewProvided - added")
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument == None:
           return False
        else:
           return True

    def GetResources(self):
        return {'Pixmap'  : 'GDMLTrapFeature', 'MenuText': \
                QtCore.QT_TRANSLATE_NOOP('GDMLTrapFeature',\
                'Trap Object'), 'ToolTip': \
                QtCore.QT_TRANSLATE_NOOP('GDMLTrapFeature',\
                'Trap Object')}


class TubeFeature:
    #def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLTube, ViewProvider
        a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython", \
                "GDMLTube_Tube")
        #print("GDMLTube Object - added")
        # obj, rmin, rmax, z, startphi, deltaphi, aunit, lunits, material
        GDMLTube(a,5.0,8.0,10.0,0.52,1.57,"rad","mm",getSelectedMaterial())
        #print("GDMLTube initiated")
        ViewProvider(a.ViewObject)
        #print("GDMLTube ViewProvided - added")
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument == None:
           return False
        else:
           return True

    def GetResources(self):
        return {'Pixmap'  : 'GDMLTubeFeature', 'MenuText': \
                QtCore.QT_TRANSLATE_NOOP('GDMLTubeFeature',\
                'Tube Object'), 'ToolTip': \
                QtCore.QT_TRANSLATE_NOOP('GDMLTubeFeature',\
                'Tube Object')}

class PolyHedraFeature :
      
    def Activated(self) :

        for obj in FreeCADGui.Selection.getSelection():
            #if len(obj.InList) == 0: # allowed only for for top level objects
            print('Action Poly')
            if hasattr(obj,'Shape') :
               print(obj.Shape.ShapeType)
               if hasattr(obj.Shape,'Vertexes') :
                  numVert = len(obj.Shape.Vertexes)
                  print('Number of Vertex : '+str(numVert))
                  #print(obj.Shape.Vertexes)
               if hasattr(obj.Shape,'Faces') :
                  print('Faces')
                  print(dir(obj.Shape.Faces[0]))
                  print(obj.Shape.Faces)
                  planar = self.checkPlanar(obj.Shape.Faces)
                  print(planar)
               if hasattr(obj.Shape,'Edges') :
                  print('Edges')
                  #print(dir(obj.Shape.Edges[0]))
                  #print(obj.Shape.Edges)

    def checkPlanar(self,faces):
        import Part
        print('Check Planar')
        for f in faces :
            if not isinstance(f.Surface, Part.Plane) :
               return False
        return True

    def GetResources(self):
        return {'Pixmap'  : 'GDML_Polyhedra', 'MenuText': \
                QtCore.QT_TRANSLATE_NOOP('GDML_PolyGroup',\
                'Poly Group'), 'ToolTip': \
                QtCore.QT_TRANSLATE_NOOP('GDML_PolyGroup', \
                'PolyHedra Selected Object')}    

class TessellatePlanarFeature :
      
    def Activated(self) :
        from .GDMLObjects import GDMLTessellated, GDMLTriangular, \
                  ViewProvider, ViewProviderExtension

        for obj in FreeCADGui.Selection.getSelection():
            #if len(obj.InList) == 0: # allowed only for for top level objects
            print('Action Tessellate')
            if hasattr(obj,'Shape') :
               print(obj.Shape.ShapeType)
               if hasattr(obj.Shape,'Vertexes') :
                  numVert = len(obj.Shape.Vertexes)
                  print('Number of Vertex : '+str(numVert))
                  if numVert > 2 :
                     if hasattr(obj,'InList') :
                        parent = obj.InList[0]
                        #print(dir(parent))
                        myTess=parent.newObject("Part::FeaturePython", \
                                         "GDMLTessellate_Tessellate")
                        tess = GDMLTessellated(myTess,0)
                        print(dir(tess))
                        if FreeCAD.GuiUp :
                           ViewProviderExtension(myTess.ViewObject)
                           ViewProvider(myTess.ViewObject)
                        print('About to Tessellate')
                        list = obj.Shape.tessellate(1)
                        print(len(list))
                        print(list)
                        # vertex = list[0] :
                        if len(list) == 2 :
                           for tri in list[1] :
                              print(list[0][tri[0]])
                              v1 = list[0][tri[0]]
                              v2 = list[0][tri[1]]
                              v3 = list[0][tri[2]]
                              myTri = FreeCAD.ActiveDocument.addObject \
                                    ('App::FeaturePython','GDMLTriangular')
                              GDMLTriangular(myTri,v1,v2,v3,'ABSOLUTE')
                              myTess.addObject(myTri)
                              if FreeCAD.GuiUp :
                                 ViewProvider(myTri)
                              else :
                                 print('Just list of vertext')
                        myTess.Placement = obj.Placement
                        FreeCAD.ActiveDocument.removeObject(obj.Name)
                        FreeCAD.ActiveDocument.recompute()
                        FreeCADGui.SendMsgToActiveView("ViewFit")
    
                  else :
                      print('Use Mesh & Tessellate')

    def GetResources(self):
        return {'Pixmap'  : 'GDML_Tessellate_Planar', 'MenuText': \
                QtCore.QT_TRANSLATE_NOOP('GDML_TessGroup',\
                'Tess Group'), 'Tessellate_Planar': \
                QtCore.QT_TRANSLATE_NOOP('GDML_PolyGroup', \
                'Tesselate Selected Planar Object')}    

class TessellateMeshFeature :
     
    def Activated(self) :
        import ObjectsFem
        from femmesh.gmshtools import GmshTools
 
        from .GDMLObjects import GDMLTessellated, GDMLTriangular, \
                  ViewProvider, ViewProviderExtension

        for obj in FreeCADGui.Selection.getSelection():
            #if len(obj.InList) == 0: # allowed only for for top level objects
            doc = FreeCAD.ActiveDocument
            print('Action Tessellate Mesh')
            femmesh_obj = ObjectsFem.makeMeshGmsh(doc, obj.Name + "_Mesh")
            femmesh_obj.Part = obj
            doc.recompute()
            gm = GmshTools(femmesh_obj)
            error = gm.create_mesh()
            print(error)
            doc.recompute()


    def GetResources(self):
        return {'Pixmap'  : 'GDML_Tessellate_Mesh', 'MenuText': \
                QtCore.QT_TRANSLATE_NOOP('GDML_TessGroup',\
                'Tess Group'), 'Tessellate_Mesh': \
                QtCore.QT_TRANSLATE_NOOP('GDML_PolyGroup', \
                'Mesh & Tesselate Selected Planar Object')}    

class CycleFeature :

    def Activated(self) :
       
        def toggle(obj) :
            #print ("Toggle "+obj.Label)
            #print (obj.ViewObject.DisplayMode)
            #print (obj.ViewObject.Visibility)
            if obj.ViewObject.Visibility == False :
               obj.ViewObject.DisplayMode = 'Shaded'
               obj.ViewObject.Visibility = True
            else :
               if obj.ViewObject.DisplayMode == 'Shaded' :
                  obj.ViewObject.DisplayMode = 'Wireframe'
               else :
                  obj.ViewObject.Visibility = False 

        def cycle(obj) :
            #print ("Toggle : "+ obj.Label)
            #print (dir(obj))
            #print("TypeId : "+str(obj.TypeId))
            if obj.TypeId == "App::Part" :
               for i in obj.OutList :
                   #print(i)
                   #print(dir(i))
                   #print (i.TypeId)
                   if i.TypeId != "App::Origin" :
                      cycle(i) 
            elif obj.TypeId =="App::Origin" :
                return
            #print obj.isDerivedFrom('App::DocumentObjectGroupPython')
            # Is this a genuine group i.e. Volumes
            # Not Parts with Groups i.e. GDMLPolycone
            elif obj.isDerivedFrom('App::DocumentObjectGroupPython') :
               #print "Toggle Group" 
               for s in obj.Group :
                   #print s
                   cycle(s)

            # Cycle through display options
            elif hasattr(obj,'ViewObject') :
               toggle(obj)

            if hasattr(obj,'Base') and hasattr(obj,'Tool') :
               print ("Boolean") 
               cycle(obj.Base)
               cycle(obj.Tool)
            

        for obj in FreeCADGui.Selection.getSelection():
            #if len(obj.InList) == 0: # allowed only for for top level objects
            cycle(obj)


    def GetResources(self):
        return {'Pixmap'  : 'GDML_Cycle', 'MenuText': \
                QtCore.QT_TRANSLATE_NOOP('GDML_CycleGroup',\
                'Cycle Group'), 'ToolTip': \
                QtCore.QT_TRANSLATE_NOOP('GDML_CycleGroup', \
                'Cycle Object and all children display')}    

class ExpandFeature :

    def Activated(self) :
       
        for obj in FreeCADGui.Selection.getSelection():
            from .importGDML import expandVolume
            #if len(obj.InList) == 0: # allowed only for for top level objects
            # add check for Part i.e. Volume
            print("Selected")
            print(obj.Label[:12])
            if obj.Label[:12] == "NOT_Expanded" :
               import lxml.etree  as ET 
               #parent = obj.InList[0]
               name = obj.Label[13:]
               obj.Label = name
               # Get original volume name i.e. loose _ or _nnn
               print('Name : '+name)
               l = len(name) - 1
               print(name[l])
               if name[l] == '_' :
                   name = name[:-1]
               else :   
                   name = name[:-4]
               print("Name : "+name)
               x = obj.Placement.Base[0]
               y = obj.Placement.Base[1]
               z = obj.Placement.Base[2]
               # Need to update importGDML to use Placement.Rotation
               # bot for now create a appropriate GDML rotation
               angles = obj.Placement.Rotation.toEuler()
               rot = ET.Element('rotation',{'name':'dummy', \
                       'x':str(angles[0]), \
                       'y':str(angles[1]), \
                       'z':str(angles[2]), \
                       'aunit' : 'deg'})
               expandVolume(obj,name,x,y,z,rot,0,3)

    def GetResources(self):
        return {'Pixmap'  : 'GDML_ExpandVol', 'MenuText': \
                QtCore.QT_TRANSLATE_NOOP('GDML_ExpandVol',\
                'Expand Volume'), 'ToolTip': \
                QtCore.QT_TRANSLATE_NOOP('GDML_ExpandVol', \
                'Expand Volume')}    

class CompoundFeature :
    
    def Activated(self) :

        from .GDMLObjects import GDMLcommon
        import ObjectsFem
   
        def allocateMaterial(doc, analObj, materials, material) :
            print("Allocate Material : ",material)
            for n in materials.OutList :
                if n.Label == material :
                   print("Found Material") 
                   matObj = ObjectsFem.makeMaterialSolid(doc, material)
                   mat = matObj.Material
                   mat['Name'] = material
                   mat['Density'] = str(n.density) + " kg/m^3"
                   mat['ThermalConductivity'] = str(n.conduct) + " W/m/K"
                   mat['ThermalExpansionCoefficient'] = str(n.expand) + " m/m/K"
                   mat['SpecificHeat'] = str(n.specific) + " J/kg/K"
                   print(mat)
                   print(mat['Density'])
                   matObj.Material = mat
                   analObj.addObject(matObj)

        def addToList(objList, matList, obj) :
            print(obj.Name) 
            if hasattr(obj,'Proxy') :
               #print("Has proxy")
               #material_object = ObjectsFem.makeMaterialSolid \
               #                  (doc,obj.Name+"-Material")
               #allocateMaterial(material_object, obj.Material)
               if isinstance(obj.Proxy,GDMLcommon) :
                  objList.append(obj)
                  if obj.material not in matList :
                     matList.append(obj.material) 
       
            if obj.TypeId == 'App::Part' and hasattr(obj,'OutList') :
               #if hasattr(obj,'OutList') :
               #print("Has OutList + len "+str(len(obj.OutList)))
               for i in obj.OutList : 
                  #print('Call add to List '+i.Name)
                  addToList(objList, matList, i)

        def myaddCompound(obj,count) :
            # count == 0 World Volume
            print ("Add Compound "+obj.Label)
            volList = []
            matList = []
            addToList(volList, matList, obj)
            if count == 0 :
               del volList[0]
               del matList[0]
            # DO not delete World Material as it may be repeat
            print('vol List')   
            print(volList)
            print('Material List')
            print(matList)
            doc = FreeCAD.activeDocument()
            analysis_object = ObjectsFem.makeAnalysis(doc,"Analysis")
            materials = FreeCAD.ActiveDocument.Materials
            for m in matList :
                allocateMaterial(doc, analysis_object, materials, m)
            comp = obj.newObject("Part::Compound","Compound")
            comp.Links = volList
            FreeCAD.ActiveDocument.recompute()


        objs = FreeCADGui.Selection.getSelection()
        #if len(obj.InList) == 0: # allowed only for for top level objects
        print(len(objs))
        if len(objs) > 0 :
           obj = objs[0]
           if obj.TypeId == 'App::Part' :
              myaddCompound(obj,len(obj.InList))

    def GetResources(self):
        return {'Pixmap'  : 'GDML_Compound', 'MenuText': \
                QtCore.QT_TRANSLATE_NOOP('GDML_Compound',\
                'Add compound to Volume'), 'ToolTip': \
                QtCore.QT_TRANSLATE_NOOP('GDML_Compound', \
                'Add a Compound of Volume')}    

FreeCADGui.addCommand('AddCompound',CompoundFeature())
FreeCADGui.addCommand('ExpandCommand',ExpandFeature())
FreeCADGui.addCommand('CycleCommand',CycleFeature())
FreeCADGui.addCommand('BoxCommand',BoxFeature())
FreeCADGui.addCommand('EllipsoidCommand',EllispoidFeature())
FreeCADGui.addCommand('ElTubeCommand',ElliTubeFeature())
FreeCADGui.addCommand('ConeCommand',ConeFeature())
FreeCADGui.addCommand('SphereCommand',SphereFeature())
FreeCADGui.addCommand('TrapCommand',TrapFeature())
FreeCADGui.addCommand('TubeCommand',TubeFeature())
FreeCADGui.addCommand('PolyHedraCommand',PolyHedraFeature())
FreeCADGui.addCommand('TessellatePlanarCommand',TessellatePlanarFeature())
FreeCADGui.addCommand('TessellateMeshCommand',TessellateMeshFeature())
