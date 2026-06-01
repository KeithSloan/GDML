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
try:
    from draftguitools import gui_arrays
except:
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

    processGDML(doc, joinDir("Mod/GDML/Resources/Default.gdml"), False, 1, True)


class GDML_Workbench(FreeCADGui.Workbench):

    #    import FreeCAD

    class MyObserver:
        def __init__(self):
            self.signal = []
            self._warned_docs = set()   # track docs already warned this session

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
                    False,          # Prompt
                    1,              # processType
                    True,
                )

        def _checkReactorMigration(self, doc):
            """Check whether reactor elements sit directly in the top-level
            'Elements' group instead of in a 'ReactorMaterials' sub-group.
            Warns once per document per session."""
            try:
                if doc.Name in self._warned_docs:
                    return
                elementsGrp = doc.getObject("Elements")
                if elementsGrp is None:
                    return
                # Quick probe: enriched_U1 is always present in the old
                # (flat) structure written by processReactor.
                needs_migration = any(
                    obj.Label == "enriched_U1"
                    for obj in elementsGrp.Group
                )
                if not needs_migration:
                    return

                self._warned_docs.add(doc.Name)
                from PySide import QtWidgets
                msg = (
                    "This document contains reactor elements (e.g. 'enriched_U1') "
                    "directly in the top-level Elements group.\n\n"
                    "These should be in a 'ReactorMaterials' sub-group so that "
                    "GDML export works correctly.\n\n"
                    "Run  GDML → Migrate Reactor Sub-Groups  to fix this."
                )
                QtWidgets.QMessageBox.warning(
                    None,
                    "Reactor Sub-Groups Migration Needed",
                    msg,
                )
            except Exception as e:
                print(f"[GDML] reactor migration check failed: {e}")

        def slotOpenDocument(self, doc):
            """Fires when a file is opened from disk."""
            self._checkReactorMigration(doc)

        def slotActivateDocument(self, doc):
            """Fires whenever a document becomes active."""
            self._checkReactorMigration(doc)

        def slotFinishRestoreDocument(self, doc):
            """Fires after full restore on newer FreeCAD."""
            self._checkReactorMigration(doc)

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
            "MigrateReactorSubGroupsCommand",
            "SetMaterialCommand",
            "AddMaterialCommand",
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
            "CutTubeCommand",
            #"Sketcher_NewSketch",
            #"Part_Extrude",
            #"Part_Revolve",
            #"Part_Mirror",
            #"Draft_ArrayTools",
            "BooleanCutCommand",
            "BooleanIntersectionCommand",
            "BooleanUnionCommand",
            "SetScaleCommand",
            "TessellateCommand",
            "TessellateGmshCommand",
            "TessGmshMinCommand",
            "TessGmshMinQuadCommand",
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

        tbSolidsCmds = [
            "CycleCommand",
            "ColourMapCommand",
            "ExpandCommand",
            "ExpandMaxCommand",
            "ResetWorldCommand",
            "SetMaterialCommand",
            "AddMaterialCommand",
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
            "CutTubeCommand",
            "BooleanCutCommand",
            "BooleanIntersectionCommand",
            "BooleanUnionCommand",
            "SetScaleCommand",
        ]

        tbPartCmds = [
            "Separator",
            "Draft_ArrayTools",
            "Part_Mirror",
            "Separator",
            "Sketcher_NewSketch",
            "Part_Extrude",
            "Part_Revolve",
            "Separator",
            "Part_Fillet",
            "Part_Chamfer",
            "Part_Loft",
            "Part_Sweep",
        ]    

        tbTessCmds = [    
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

        toolbarCmds = tbSolidsCmds + tbPartCmds + tbTessCmds
        self.appendToolbar(
            QT_TRANSLATE_NOOP("Workbench", "GDMLTools"), toolbarCmds
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
        # Check any document that is already open/active at the moment the
        # workbench activates — the observer would miss events that fired
        # before it was registered.
        doc = FreeCAD.ActiveDocument
        if doc is not None:
            self.obs._checkReactorMigration(doc)
        return

    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        FreeCAD.removeDocumentObserver(self.obs)
        return

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(GDML_Workbench())
