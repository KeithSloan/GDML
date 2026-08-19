# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2024 Keith Sloan <keithsloan52@icloud.com>              *
# *                      Munther Hindi                                      *
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
#                                                                          *
#     Select source and target directories
#                      Opens any FC file in source directory
#                      Selects any GDML root Part
#                      Exports GDML to file in target directory
#
# ***************************************************************************

import sys, os
import glob

from PySide import QtGui, QtCore, QtWidgets


class directory(QtGui.QWidget):
    def __init__(self, label):
        super(directory, self).__init__()
        print(f"Directory {label}")
        self.layout = QtGui.QHBoxLayout()
        self.label = QtGui.QLabel(label)
        self.layout.addWidget(self.label)
        self.directoryPath = QtGui.QLineEdit("Path Not Set")
        self.directoryPath.setReadOnly(True)
        self.layout.addWidget(self.directoryPath)
        self.selectButton = QtGui.QPushButton('Select')
        self.layout.addWidget(self.selectButton)
        self.setLayout(self.layout)
        self.selectButton.clicked.connect(self.onSelect)

    def onSelect(self):
        Path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        print(f"Directory Path {Path}")
        self.directoryPath.setText(Path)

    def getPath(self):
        return self.directoryPath.text()


class importPrompt(QtGui.QDialog):

    def __init__(self, *args):
        # from PySide2 import QtGui, QtCore, QtWidgets
        super(importPrompt, self).__init__()
        self.initUI()

    def initUI(self):
        print(f"Init Prompt")
        importButton = QtGui.QPushButton('Perform Export of GDMLs')
        importButton.clicked.connect(self.onExport)
        # buttonBox = QtGui.QDialogButtonBox()
        #
        mainLayout = QtGui.QVBoxLayout()
        # mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
        self.setGeometry(650, 650, 600, 200)
        self.setWindowTitle("Create GDML exports - Choose directories    ")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.sourcePath = directory("Source")
        mainLayout.addWidget(self.sourcePath)
        self.targetPath = directory("Target")
        mainLayout.addWidget(self.targetPath)
        exportButton = QtGui.QPushButton('Perform Export of GDMLs')
        exportButton.clicked.connect(self.onExport)
        mainLayout.addWidget(exportButton)
        self.show()

    def join(self, path, name):
        import os
        return(os.path.join(path, name))

    def processFile(self,filePath, targetPath):
        import freecad.gdml.exportGDML, os
        fileName = os.path.basename(filePath)
        FreeCAD.openDocument(filePath)
        print(f"RootObjects len(FreeCAD.ActiveDocument.RootObjects:")
        for obj in FreeCAD.ActiveDocument.RootObjects:
            if obj.TypeId == "App::Part":
                print(f"Found Root Part : {obj.Label}")
                FreeCADGui.Selection.addSelection(obj)
                exportName = fileName[:-6] + f"-{obj.Label}" + '.gdml'
                exportPath = self.join(targetPath, exportName)
                print(
                    f"Process FC filename {fileName} filepath {filePath} targetPath {targetPath} exportPath {exportPath}")
                if hasattr(freecad.gdml.exportGDML, "exportOptions"):
                    options = freecad.gdml.exportGDML.exportOptions(exportPath)
                    # pass list of selected obj
                    freecad.gdml.exportGDML.export([obj], exportPath)
                else:
                    freecad.gdml.exportGDML.export([obj], exportPath)

                break

        FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)


    def onExport(self):

        print(f"\nProcessing - creating GDML files for directory : {self.sourcePath.getPath()} to {self.targetPath.getPath()}")
        # Assign directory
        inputPath = self.sourcePath.getPath()
        targetPath = self.targetPath.getPath()
        # Iterate over files in directory
        for filepath in glob.glob(f"{inputPath}/*.FCStd"):
            print(f"Process FC file {filepath}")
            self.processFile(filepath, targetPath)


if FreeCAD.GuiUp:
    prompt = importPrompt()
    prompt.exec_()
else:
    print("No FreeCAD GUI") 

