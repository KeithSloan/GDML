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
#
#                       Opens any FC file in source directory
#                       Selects any GDML root Part
#                       Perform COG calcs 
#                       file in target directory
#
#***************************************************************************
import sys, os
import glob

import importlib.util

from PySide import QtGui, QtCore, QtWidgets

class directory(QtGui.QWidget):
    def __init__(self, label):
        super(directory, self).__init__()
        print(f"Directory {label}")
        self.layout = QtGui.QHBoxLayout()
        self.label = QtGui.QLabel(label)
        self.layout.addWidget(self.label)
        self.directoryPath =  QtGui.QLineEdit("Path Not Set")
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
        #from PySide2 import QtGui, QtCore, QtWidgets
        super(importPrompt, self).__init__()
        self.initUI()

    def initUI(self):
        print(f"Init Prompt")       
        mainLayout = QtGui.QVBoxLayout()
        #mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
        self.setGeometry(650, 650, 600, 200)
        self.setWindowTitle("COG Calculations for directory of FC files    ")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.sourcePath=directory("Source")
        mainLayout.addWidget(self.sourcePath)
        self.targetPath =directory("Target")
        mainLayout.addWidget(self.targetPath)
        cogButton = QtGui.QPushButton('Perform COG calculations')
        cogButton.clicked.connect(self.onCOGcalc)
        mainLayout.addWidget(cogButton)
        self.show()

    def join(self, path, name):
        return(os.path.join(path, name))

    def processFile(self, filePath, targetPath):
        # from . import calcCenterOfMass
        
        macroDir = FreeCAD.getUserMacroDir(True)
        spec = importlib.util.spec_from_file_location("calcCenterOfMass", macroDir+"/calcCenterOfMass.py")
        foo = importlib.util.module_from_spec(spec)
        sys.modules["calcCenterOfMass"] = foo
        spec.loader.exec_module(foo)
        
        # from macroDir import calcCenterOfMass
        # from importlib.machinery import SourceFileLoader
        # macroPath = os.path.join(macroDir, 'calcCenterOfMass.py')
        # Load your module using the module's path
        # calcCenterOfMass = SourceFileLoader('calcCenterOfMass', macroPath).load_module()

        # Now you can access the module's functions by using the dot operator
        #my_module.my_function()
        # Using os.path.splitext()
        filePathNoExt = os.path.splitext(os.path.basename(filePath))[0]
        fileName = os.path.basename(filePath)
        exportName = fileName[:-6] + '.dat'
        exportPath = self.join(targetPath, exportName)
        print(f"Process FC filename {fileName} filepath {filePath} targetPath {targetPath} ")
        FreeCAD.openDocument(filePath)
        print(f"RootObjects len(FreeCAD.ActiveDocument.RootObjects:")
        for obj in FreeCAD.ActiveDocument.RootObjects:
            if obj.TypeId == "App::Part":
                print(f"Found Root Part : {obj.Label}")
                # Add seelction for Munthers Export
                FreeCADGui.Selection.addSelection(obj)
                sel = FreeCADGui.Selection.getSelection()
                print(f" Number of Selections {len(sel)}")  # number of selections. 
                foo.calcCenterOfMass(exportPath)

                break

        FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)


    def onCOGcalc(self):

        print(f"\nProcessing - creating COG calculations for GDML files in directory : {self.sourcePath.getPath()} to {self.targetPath.getPath()}")
        # Assign directory
        inputPath= self.sourcePath.getPath()
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

