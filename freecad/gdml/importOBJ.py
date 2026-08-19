# -*- coding: utf-8 -*-
# Fri Feb 11 01:11:14 PM PST 2022
# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2024 Keith Sloan <keithsloan52@icloud.com>              *
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
# *   Acknowledgements :
# *                                                                        *
# *                                                                        *
# **************************************************************************
__title__ = "FreeCAD - OBJ -> GDML Tessellated importer"
__author__ = "Keith Sloan <keithsloan52@icloud.com>"
__url__ = ["https://github.com/KeithSloan/FreeCAD_GDML"]

import FreeCAD, FreeCADGui
import os, io, sys, re
import Part, Draft

from PySide import QtGui, QtCore

def joinDir(path):
    import os
    __dirname__ = os.path.dirname(__file__)
    return(os.path.join(__dirname__, path))

# Save the native open function to avoid collisions
if open.__module__ in ['__builtin__', 'io']:
    pythonopen = open  # to distinguish python built-in open function from the one declared her


def open(filename):
    "called when freecad opens a file."

    print('Open : '+filename)
    docName = os.path.splitext(os.path.basename(filename))[0]
    print('path : '+filename)
    if filename.lower().endswith('.obj'):
        try:
            doc = FreeCAD.ActiveDocument()
            print('Active Doc')

        except:
            print('New Doc')
            doc = FreeCAD.newDocument(docName)

        processOBJ(doc, filename)
        return doc


def insert(filename, docname):
    "called when freecad imports a file"
    print('Insert filename : '+filename+' docname : '+docname)
    global doc
    groupname = os.path.splitext(os.path.basename(filename))[0]
    try:
        doc = FreeCAD.getDocument(docname)
    except NameError:
        doc = FreeCAD.newDocument(docname)
    if filename.lower().endswith('.obj'):
        processOBJ(doc, filename)


class ColourWidget(QtGui.QLineEdit):

    def __init__(self, colour):
        super().__init__()
        palette = self.palette()
        # palette.setColor(QtGui.QPalette.Button, QtGui.QColor(colour))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(colour))
        # palette.setColor(QtGui.QPalette.Window, QtGui.QColor(colour))
        self.setAutoFillBackground(True)
        # palette.setColor(QtGui.QPalette.Window, QtGui.QColor(QtGui.qRed))
        # palette.setColor(QtGui.QPalette.Window, QtGui.qRed)
        self.setStyleSheet("QPushButton {border-color: black; border: 2px;}")
        self.setPalette(palette)
        self.setReadOnly(True)
        self.setMaxLength = 5
        # self.setFlat(True)
        self.update()


class TextWidget(QtGui.QLineEdit):

    def __init__(self, text):
        super().__init__()
        #print(f"Text Widget {text}")
        self.insert(text)
        self.setReadOnly(True)

#class Headings(QtGui.QWidget):


# Use two scoll areas pass valueChange
class Headings(QtGui.QScrollArea):

    def __init__(self):
        super().__init__()
        self.widget = QtGui.QWidget()
        self.setGeometry(30, 30, 800, 250)
        # Scroll Area Properties
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        #self.setVerticalScrollBarPolicy(QtGui.QSizePolicy.setHorizontalPolicy.Fixed)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        #self.setWidgetResizable(True)
        self.setFixedHeight(80)
        self.setWidgetResizable(False)
        self.setWidget(self.widget)
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(TextWidget('Object Name'))
        self.hbox.addWidget(TextWidget('Object Material'))
        self.hbox.addWidget(TextWidget('GDML Material'))
        self.hbox.addWidget(TextWidget('GDML Colour'))
        self.setLayout(self.hbox) 


class MapMaterialObj2GDML(QtGui.QWidget):

    def __init__(self, objName, objMat, gdmlWidget, colour):
        super().__init__()
        #print('Map Material Entry Obj ->  GDML: ')
        #print(f'Name {objName} Material {objMat}')
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(TextWidget(objName))
        self.hbox.addWidget(TextWidget(objMat))
        self.hbox.addWidget(gdmlWidget)
        self.hbox.addWidget(ColourWidget(colour))
        self.setLayout(self.hbox)


class MaterialMapList(QtGui.QScrollArea):

    def __init__(self, objMtlDict):
        super().__init__()
        self.objMtlDict = objMtlDict
        from .GDMLMaterials import getMaterialsList
        # Scroll Area which contains the widgets, set as the centralWidget
        # Widget that contains the collection of Vertical Box
        self.widget = QtGui.QWidget()
        self.matList = getMaterialsList()
        #print(f"Material List {self.matList}")
        # The Vertical Box that contains the Horizontal Boxes of  labels and buttons
        self.vbox = QtGui.QVBoxLayout()
        self.widget.setLayout(self.vbox)

        # Scroll Area Properties
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(self.widget)
        self.NameMatWdgDict = {}
        self.NameColourDict = {}


    def getMatColour(self, objMat):
        from PySide.QtGui import QColor

        #print(f"objMtlDict {self.objMtlDict}")
        #print(f"objMat {objMat} {self.objMtlDict[objMat]}")
        r = 5
        g = 0
        b = 10
        mtlDict = self.objMtlDict.get(objMat)
        if mtlDict is not None:
            Ka = mtlDict.get("Ka")
            if Ka is not None:
                # Variable with RGB values as a tuple
                # print(f"Ka {Ka}")
                # Convert values to the 0-255 range expected by QColor
                r, g, b = [int(x * 255) for x in Ka]
                # Return QColor object
                # color = QColor(r, g, b)
        return QColor(r, g, b)


    def addEntry(self, objName, objMat, gdmlMat):
        from .GDMLMaterials import GDMLMaterial
        #print('Add Entry')
        colour = self.getMatColour(objMat)
        matWidget = GDMLMaterial(self.matList, gdmlMat)
        self.NameMatWdgDict[objName] = matWidget
        self.NameColourDict[objName] = colour
        self.vbox.addWidget(MapMaterialObj2GDML(objName, objMat,  matWidget, colour))


    def getColourMaterial4Name(self, objName):
        print(f"getColourMaterial4Name {objName}")
        entry = self.NameMatWdgDict.get(objName)
        fcColour = (0.4, 0.0, 0.8)
        Material = "G4_A-150_TISSUE"
        if entry is not None:
            qtColor = self.NameColourDict.get(objName)
            if qtColor is not None:
                fcColour = (
                    qtColor.red() / 255.0,
                    qtColor.green() / 255.0,
                    qtColor.blue() / 255.0
                    )
                #vcColour = FreeCAD.Vector(*fcColour)
                #print(f"Entry {entry} {entry.getItem()}")
                Material = entry.getItem()
        return fcColour, Material


class MapObjmat2GDMLmatDialog(QtGui.QDialog):
    def __init__(self, doc, *args):
        super(MapObjmat2GDMLmatDialog, self).__init__()
        self.setupUi()
        #self.initUI()
        self.doc = doc
        self.mtlFile = None

    def initUI(self):
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setMouseTracking(True)
        self.show()

    def setupUi(self):
        # Dict objMat Name lookup by Obj Name
        self.nameMatDict = {}
        # Dict mtl defintions for objMat Name
        self.objMtlDict = {}
        self.setObjectName("Dialog")
        self.resize(400, 462)
        mainLayout = QtGui.QVBoxLayout()
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setGeometry(QtCore.QRect(50, 50, 541, 250))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(
            QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok
        )
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.accepted.connect(self.action)
        self.buttonBox.rejected.connect(self.onCancel)
        self.mapList = MaterialMapList(self.objMtlDict)
        self.mapLayout = QtGui.QVBoxLayout()
        self.mapLayout.addWidget(self.mapList)
        self.headings = Headings()
        mainLayout.addWidget(self.headings)
        mainLayout.addLayout(self.mapLayout)
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)
        self.setGeometry(30, 30, 800, 350)
        self.setWindowTitle("Map Materials Obj -> GDML")
        #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.retStatus = 0

    def initMaterials(self):
        from .GDMLMaterials import getMaterialsList, GDMLMaterial
        self.materialsList = getMaterialsList()

    def moveMTL2Materials(self):
        import FreeCADGui
        self.doc.recompute()
        print(f"Move MTFfile {self.mtlFile} to Materials")
        #doc = FreeCADGui.ActiveDocument
        #print(doc)
        matGrp = self.doc.getObject("Materials")
        print(f"Mat Grp {matGrp}")
        if matGrp is not None:
            if self.mtlFile is not None:
                #sheetName = self.mtlFile.split(".")[0]+"_MTL_Materials"
                sheetName = self.mtlFile.split(".")[0]
                sheetName = "test_entire_obj_mtl"
                print(f"Sheet Name {sheetName}")
                mtlObj  = self.doc.getObject(sheetName)
                print(f"mtlObj {mtlObj}")
                matGrp.addObject(mtlObj)
                self.doc.recompute()


    def importMTL(self, filePath, mtlFile):
        import os
        from freecad.gdml.importMTL import processMTL
        print(f"import MTL file {mtlFile}")
        directory = os.path.dirname(filePath)
        mtlPath = os.path.join(directory, mtlFile)
        processMTL(self.doc, mtlPath, matDict=self.objMtlDict)
        #print(f"objMtlDict {self.objMtlDict}")


    def parseObjFile(self, filePath, buildMap=True):
        import os
        fp = pythonopen(filePath)
        data = fp.read()
        lines = data.splitlines()
        for line in lines:
            line.strip()
            if line.startswith('mtllib'):
                mtlFile = line.split(maxsplit=1)[1]
                print(f"mtllib {mtlFile}")
                self.importMTL(filePath, mtlFile)
                br:eak

        #pattern = re.compile(r"^(?:[0g]|usemtl|o)\s.*", re.MULTILINE)
        pattern = re.compile(r"^(?:[0g]|usemtl)\s.*", re.MULTILINE)
        self.objMatList = pattern.findall(data)
        # Need to improve python coding
        # print(f"obj Mat List {self.objMatList}")
        # State 0 - No g/o/usemtl
        # State 1 - one of g/o
        # State 2 - usemtl
        # State 3 - both g/o and usemtl
        state = 0
        objMat = "None"
        # If only one item name is file name
        # This is messy
        if len(self.objMatList) <= 1:
            fileName = os.path.basename(filePath)
            name = os.path.splitext(fileName)[0]
            print(f"filename {os.path.splitext(filePath)}")
            self.objMatList = ["g "+os.path.splitext(fileName)[0]]
            self.addMaterialMapping(name, objMat, "G4_A-150_TISSUE")
            return

        for i in self.objMatList:
            #print(f"i {i}")
            if 'g ' in i:
                if state == 1:
                    self.nameMatDict[name] = objMat
                    if buildMap:
                        self.addMaterialMapping(name, objMat, "G4_A-150_TISSUE")
                name = i.lstrip('g ')
                #print(f"Name {name}")
                state = state + 1
            if 'o ' in i:
                if state == 1:
                    self.nameMatDict[name] = objMat
                    if buildMap:
                        self.addMaterialMapping(name, objMat, "G4_A-150_TISSUE")
                name = i.lstrip('o ').lower()
                #print(f"Name {name}")
                state = state + 1
            if 'usemtl ' in i:
                objMat = i.lstrip('usemtl ')
                #print(f"Material {objMat}")
                state = state + 2
            if state == 3:
                    self.nameMatDict[name] = objMat
                    state = 0
                    if buildMap:
                        self.addMaterialMapping(name, objMat, "G4_A-150_TISSUE")

    def addMaterialMapping(self, name, objMat, gdmlMat):
        #print(f"Add Material Map Obj {name} Material {objMat} to GDML mat {gdmlMat}")        
        self.mapList.addEntry(name, objMat, gdmlMat)
        self.nameMatDict[name] = gdmlMat
        #self.objMatGDMLmat[objMat] = gdmlMat

    def getObjGDMLmaterial(self, objMat):
        cb = self.objMatGDMLmat[objMat]
        return cb.getItem()


    def getColourMaterial4Name(self, name):
        #print(f"Get Material for Name {name}")
        colour, Material = self.mapList.getColourMaterial4Name(name)
        return colour, Material


    def findRootPart(self, doc):
        for obj in doc.RootObjects:
            if obj.TypeId == "App::Part":
                return obj
        return None       

    def processMappingDict(self, matMap, doc, fileName,  Material="G4_A-150_TISSUE"):
        #from .GDMLObjects import setMaterial, updateColour, colorFromRay, setTransparency, setLengthQuantity
        from .GDMLObjects import setMaterial, setTransparency, setLengthQuantity
        #import random

        #print(f"Processing Mapping Dict doc {doc.Name} fileName {fileName}")
        print(f"Processing Mapping Dict : matMap {matMap} Material {Material}")
        rootObj = self.findRootPart(doc)
        if rootObj is not None:
            partObj = rootObj.newObject("App::Part",fileName+"_OBJ")
        else:    
            partObj = doc.addObject("App::Part",fileName+"_OBJ")
        #print(f"PartObj {partObj}")
        # Add entry for file name i.e OBJ from blender
        self.nameMatDict[fileName] = Material
        for i, label in enumerate(self.nameMatDict):
            #print(f"Object Label {label}")
            #name = ObjectLabel2Name(label)
            #obj = doc.getObject(name)
            #obj.adjustRelativeLinks(part)
            objs = doc.getObjectsByLabel(label+'\r')+  \
                    doc.getObjectsByLabel(label)
            #print(objs)
            for obj in objs:
              if obj is not None:
                partObj.addObject(obj)
                if matMap:
                    colour, Material = self.getColourMaterial4Name(label)
                if obj is not None:    
                     obj.addProperty(
                            "App::PropertyEnumeration",
                            "material",
                            "GDMLMesh",
                            "Material",
                    )
                print(f" Name {label} Material {Material}") 
                setMaterial(obj, Material)
                # updateColour(obj, colour, None)
                # Random Colour  now
                # updateColour(obj, colorFromRay(random.random()), Material)
                obj.ViewObject.ShapeColor = colour
                setTransparency(obj, 30)
                obj.addProperty("App::PropertyEnumeration", "lunit", \
                                "GDMLMesh", "lunit")
                setLengthQuantity(obj, "mm")
                obj.setEditorMode('lunit',1)
              else:
                print(f"Not found label{label} name {name}")

    def fullDisplayRadioButtonToggled(self):
        self.fullDisplayRadioButton.blockSignals(True)


    def fullDisplayRadioButtonToggled(self):
        self.fullDisplayRadioButton.blockSignals(True)

        if self.fullDisplayRadioButton.isChecked():
            self.fractionSpinBox.setEnabled(False)
            self.fractionsLabel.setEnabled(False)
        else:
            self.fractionSpinBox.setEnabled(True)
            self.fractionsLabel.setEnabled(True)

        self.fullDisplayRadioButton.blockSignals(False)

    def action(self):
        print(f"Map Materials")
        self.MapMaterials = True
        self.accept()

    def onCancel(self):
        print(f"reject")
        self.MapMaterials = False
        self.reject()

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Mesh2TessellateDialog", "Mesh2Tess"))
        self.textEdit.setHtml(
            _translate(
                "Mesh2TessellateDialog",
                '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">\n'
                '<html><head><meta name="qrichtext" content="1" /><style type="text/css">\n'
                "p, li { white-space: pre-wrap; }\n"
                "</style></head><body style=\" font-family:'Noto Sans'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
                '<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Convert a mesh to a GDML Tessellated solid. For very large meshes, the building of a full solid in python might take a <span style=" font-weight:600;">very long</span> time. To speed up conversion, a sampling of the facets can be displayed, instead of creating a full solid. <span style=" font-weight:600;">On export to GDML, the full solid will be exported</span>. The fraction of faces displayed can be later changed in the Properties paenl.</p></body></html>',
            )
        )

        self.groupBox.setTitle(
            _translate("Mesh2TessellateDialog", "Tessellation display")
        )
        self.fullDisplayRadioButton.setToolTip(
            _translate("Mesh2TessellateDialog", "Display full solid")
        )
        self.fullDisplayRadioButton.setText(
            _translate("Mesh2TessellateDialog", "Full solid")
        )
        self.samplesRadioButton.setToolTip(
            _translate("Mesh2TessellateDialog", "Sample facets")
        )
        self.samplesRadioButton.setText(
            _translate("Mesh2TessellateDialog", "Samples only")
        )
        self.fractionsLabel.setText(
            _translate("Mesh2TessellateDialog", "Sampled fraction (%)")
        )
        self.fractionSpinBox.setToolTip(
            _translate("Mesh2TessellateDialog", "Percent of facets sampled")
        )

def getSelectedMaterial():
    from .exportGDML import nameFromLabel
    from .GDMLObjects import GDMLmaterial

    sel = FreeCADGui.Selection.getSelection()
    print(f"list {sel}")
    if sel is not None:
        for obj in sel:
            print(f"name {obj.Label}")
            if hasattr(obj, 'Proxy'):
                if isinstance(obj.Proxy, GDMLmaterial) is True:
                    print(f"Is GDML  Material")
                    return nameFromLabel(obj.Label)

    return None


def findNearestPart(obj):
    if obj.TypeId == "App::Part":
        return obj
    for o in obj.InList:
        return findNearestPart(o)   

def ObjectLabel2Name(label):
    # Return Object name from passed label
    # Needed as doc.getObjectsByLabel does not work for Mesh::Features
    print(f"Label {label}")
    name = '_'+label[1:]+'_'
    name = name.replace('-','_').replace('(','_').replace(")","_")
    return name

def getFileName(filePath):
    from pathlib import Path
    return(Path(filePath).stem)

def processOBJ(doc, filePath):

    import FreeCADGui, Mesh, re, os
    from .GDMLObjects import checkMaterialDefinitionsExist
    from datetime import datetime

    # Use insert from FC importOBJ importers FC 1.0.0
    try:
        from importers.importOBJ import insert as insertObj
    except:
        from importOBJ import insert as insertObj

    #from .GDMLObjects import GDMLTessellated, ViewProvider
    #from .GDMLCommands import Mesh2TessDialog

    print("Check Materials definitions exist")
    checkMaterialDefinitionsExist()
    print("import OBJ as FC meshes")
    startTime = datetime.now()
    mapDialog = MapObjmat2GDMLmatDialog(doc)
    # Preprocess file collecting Object and Material definitions
    mapDialog.parseObjFile(filePath)
    #print(f"Obj Dict {objDict}")
    #print(f"Time for preprocess objects materials {preTime - startTime}")
    # Read OBJ
    # Important : Need to use importOBJ from BIM importers
    # Otherwise problems with mesh objects, especially for multiple Obj
    insertObj(filePath, doc.Name)
    fcMeshTime = datetime.now()
    #print(f"Time for FC mesh load of OBJ file {fcMeshTime - preTime}")
    Material = getSelectedMaterial()
    print(f"====> Selected Material {Material}")
    if Material is None:
        matMap = True
        # As Advised by wmayer to avoid spinning cursor
        QtGui.QGuiApplication.setOverrideCursor(QtGui.Qt.ArrowCursor)
        mapDialog.initUI()
        mapDialog.exec_()
        #preTime = datetime.now()
        # As Advised by wmayer to avoid spinning cursor
        QtGui.QGuiApplication.restoreOverrideCursor()
    else:
        matMap = False
    mapDialog.processMappingDict(matMap, doc, getFileName(filePath), Material)
    doc.recompute()
    #mapDialog.moveMTL2Materials()
    FreeCADGui.setActiveDocument(doc)
    FreeCAD.ActiveDocument.recompute()
    if FreeCAD.GuiUp:
        FreeCADGui.SendMsgToActiveView("ViewFit")
    FreeCAD.Console.PrintMessage("End import OBJ file\n")
