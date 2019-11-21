# GDML wrkbench gui init module
#
# Gathering all the information to start FreeCAD
# This is the second one of three init scripts, the third one
# runs when the gui is up

#***************************************************************************
#*   (c) Juergen Riegel (juergen.riegel@web.de) 2002                       *
#*                                                                         *
#*   This file is part of the FreeCAD CAx development system.              *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   FreeCAD is distributed in the hope that it will be useful,            *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Lesser General Public License for more details.                   *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with FreeCAD; if not, write to the Free Software        *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#*   Juergen Riegel 2002                                                   *
#*                                                                         *
#* Also copyright Keith Sloan                                              * 
#***************************************************************************/

#import FreeCAD
from FreeCAD import *
import PartGui
import GDMLCommands, GDMLResources

def processDefault(doc) :
    from importGDML import processGDML
    processGDML(doc,FreeCAD.getResourceDir() + \
                "Mod/GDML/Resources/Default.gdml",False)

class GDML_Workbench ( Workbench ):

    class MyObserver():
       def __init__(self):
           self.signal = []

       def slotCreatedDocument(self, doc):
           from importGDML import processGDML
           processGDML(doc,FreeCAD.getResourceDir() + \
                "Mod/GDML/Resources/Default.gdml",False)
    
    "GDML workbench object"
    def __init__(self):
        self.__class__.Icon = FreeCAD.getResourceDir() + "Mod/GDML/Resources/icons/GDMLWorkbench.svg"
        self.__class__.MenuText = "GDML"
        self.__class__.ToolTip = "GDML workbench"

    def Initialize(self):
        def QT_TRANSLATE_NOOP(scope, text):
            return text
        
        #import GDMLCommands, GDMLResources
        commands=['CycleCommand','ExpandCommand', \
                 'BoxCommand','ConeCommand','ElTubeCommand', \
                  'EllipsoidCommand','SphereCommand', \
                  'TrapCommand','TubeCommand','AddCompound']
        toolbarcommands=['CycleCommand','ExpandCommand', \
                         'BoxCommand','ConeCommand', \
                  'ElTubeCommand', 'EllipsoidCommand','SphereCommand', \
                  'TrapCommand','TubeCommand','AddCompound']

        parttoolbarcommands = ['Part_Cut','Part_Fuse','Part_Common']

        self.appendToolbar(QT_TRANSLATE_NOOP('Workbench','GDMLTools'),toolbarcommands)
        self.appendMenu('GDML',commands)
        self.appendToolbar(QT_TRANSLATE_NOOP('Workbech','GDML Part tools'),parttoolbarcommands)
        ResourcePath = FreeCAD.getHomePath() + "Mod/GDML/Resources/"
        print("Resource Path : "+ResourcePath)
        #FreeCADGui.addIconPath(FreeCAD.getResourceDir() + \
        #FreeCADGui.addIconPath(":/icons")
        FreeCADGui.addIconPath(ResourcePath + "icons")
        #FreeCADGui.addLanguagePath(":/translations")
        FreeCADGui.addLanguagePath(ResourcePath + "/translations")
        FreeCADGui.addPreferencePage(ResourcePath + "/ui/GDML-base.ui","GDML")

    def Activated(self):
        "This function is executed when the workbench is activated"
        print ("Activated")
        self.obs = self.MyObserver()
        App.addDocumentObserver(self.obs)
        doc = FreeCAD.activeDocument()
        if doc != None :
           #print(dir(doc)) 
           if len(doc.Objects) > 0 :
              if doc.Objects[0].Name != "Constants" : 
                 #self.processDefault(doc)
                 #processDefault(doc)
                 self.MyObserver.slotCreatedDocument(self,doc)
           else :
              self.MyObserver.slotCreatedDocument(self,doc) 
        return

    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        App.removeDocumentObserver(self.obs)
        return
    
    def GetClassName(self):
        return "Gui::PythonWorkbench"

Gui.addWorkbench(GDML_Workbench())

