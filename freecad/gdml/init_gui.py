# GDML wrkbench gui init module
#
# Gathering all the information to start FreeCAD
# This is the second one of three init scripts, the third one
# runs when the gui is up

# ***************************************************************************
# *   (c) Juergen Riegel (juergen.riegel@web.de) 2002                       *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   FreeCAD is distributed in the hope that it will be useful,            *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Lesser General Public License for more details.                   *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with FreeCAD; if not, write to the Free Software        *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# *   Juergen Riegel 2002                                                   *
# *                                                                         *
# * Also copyright Keith Sloan                                              *
# ***************************************************************************/

# import FreeCAD
# from FreeCAD import *
import FreeCAD
import PartGui
import DraftTools
import SketcherGui
import MeshGui
import FreeCADGui
from freecad.gdml import GDMLCommands, GDMLResources


def joinDir(path):
    import os

    __dirname__ = os.path.dirname(__file__)
    return os.path.join(__dirname__, path)


def processDefault(doc):
    from .importGDML import processGDML

    processGDML(doc, joinDir("Mod/GDML/Resources/Default.gdml"), False, True)


class GDML_Workbench(FreeCADGui.Workbench):

    #    import FreeCAD

    class MyObserver:
        def __init__(self):
            self.signal = []

        def slotCreatedDocument(self, doc):
            from .importGDML import processGDML

            # print(doc.Name)
            # print(doc.Label)
            # print(doc.FileName)
            # print(dir(doc))
            if doc.Name == "Unnamed":
                processGDML(
                    doc,
                    True,
                    joinDir("Resources/Default.gdml"),
                    False,
                    True,
                )

    "GDML workbench object"

    def __init__(self):
        self.__class__.Icon = joinDir("Resources/icons/GDMLWorkbench.svg")
        self.__class__.MenuText = "GDML"
        self.__class__.ToolTip = "GDML workbench"

    def Initialize(self):
        def QT_TRANSLATE_NOOP(scope, text):
            return text

        # import GDMLCommands, GDMLResources
        commands = [
            "CycleCommand",
            "ColourMapCommand",
            "ExpandCommand",
            "ExpandMaxCommand",
            "ResetWorldCommand",
            "SetMaterialCommand",
            "SetSensDetCommand",
            "SetSkinSurfaceCommand",
            "SetBorderSurfaceCommand",
            "BoxCommand",
            "ConeCommand",
            "ElTubeCommand",
            "EllipsoidCommand",
            "SphereCommand",
            "TorusCommand",
            "TrapCommand",
            "TubeCommand",
            "Sketcher_NewSketch",
            "Part_Extrude",
            "Part_Revolve",
            "Part_Mirror",
            "Draft_ArrayTools",
            "SetScaleCommand",
            "BooleanCutCommand",
            "BooleanIntersectionCommand",
            "BooleanUnionCommand",
            "TessellateCommand",
            "TessellateGmshCommand",
            "TessGmshMinCommand",
            "GmshGroupCommand",
            "DecimateCommand",
            "Mesh_FromPartShape",
            "Mesh_Evaluation",
            "Mesh2TessGroupCommand",
            "Mesh2TessCommand",
            "Tess2MeshCommand",
            "TetrahedronCommand",
            "AddCompound",
        ]

        toolbarcommands = [
            "CycleCommand",
            "ColourMapCommand",
            "ExpandCommand",
            "ExpandMaxCommand",
            "ResetWorldCommand",
            "SetMaterialCommand",
            "SetSensDetCommand",
            "SetSkinSurfaceCommand",
            "SetBorderSurfaceCommand",
            "Separator",
            "Std_Part",
            "BoxCommand",
            "ConeCommand",
            "ElTubeCommand",
            "EllipsoidCommand",
            "SphereCommand",
            "TorusCommand",
            "TrapCommand",
            "TubeCommand",
            "Sketcher_NewSketch",
            "Part_Extrude",
            "Part_Revolve",
            "Part_Mirror",
            "Draft_ArrayTools",
            "SetScaleCommand",
            "Separator",
            "BooleanCutCommand",
            "BooleanIntersectionCommand",
            "BooleanUnionCommand",
            "Separator",
            "TessellateCommand",
            "GmshGroupCommand",
            "DecimateCommand",
            "Mesh_FromPartShape",
            "Mesh_Evaluation",
            "Mesh2TessGroupCommand",
            #"Tess2MeshCommand",
            "TetrahedronCommand",
            "AddCompound",
        ]

        # parttoolbarcommands = ['Part_Cut','Part_Fuse','Part_Common']
        # meshtoolbarcommands = ['Mesh_FromPartShape','Mesh_Evaluation']

        self.appendToolbar(
            QT_TRANSLATE_NOOP("Workbench", "GDMLTools"), toolbarcommands
        )
        self.appendMenu("GDML", commands)
        # self.appendToolbar(QT_TRANSLATE_NOOP('Workbech','GDML Part tools'),parttoolbarcommands)
        # self.appendToolbar(QT_TRANSLATE_NOOP('Workbech','GDML Mesh Tools'),meshtoolbarcommands)
        FreeCADGui.addIconPath(joinDir("Resources/icons"))
        FreeCADGui.addLanguagePath(joinDir("Resources/translations"))
        FreeCADGui.addPreferencePage(
            joinDir("Resources/ui/GDML-base.ui"), "GDML"
        )

    def Activated(self):
        "This function is executed when the workbench is activated"
        print("Activated")
        self.obs = self.MyObserver()
        FreeCAD.addDocumentObserver(self.obs)
        return

    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        FreeCAD.removeDocumentObserver(self.obs)
        return

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(GDML_Workbench())
