# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2017 Keith Sloan <keith@sloan-home.co.uk>              *
# *             (c) Dam Lambert 2020                                          *
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
# *                                                                        *
# **************************************************************************

__title__ = "FreeCAD GDML Workbench - GDMLColourMap"
__author__ = "Keith Sloan"
__url__ = ["http://www.freecadweb.org"]

import FreeCAD
import FreeCADGui

# from PySide2 import QtGui, QtCore
from PySide import QtGui, QtCore

if FreeCADGui:
    try:
        _encoding = QtGui.QApplication.UnicodeUTF8

        def translate(context, text):
            "convenience function for Qt translator"
            return QtGui.QApplication.translate(context, text, None, _encoding)
    except AttributeError:
        def translate(context, text):
            "convenience function for Qt translator"
            return QtGui.QApplication.translate(context, text, None)


def resetGDMLColourMap():
    print('Reset Colour Map')
    global workBenchColourMap
    try:
        del workBenchColourMap
    except NameError:
        pass

    workBenchColourMap = GDMLColourMap(FreeCADGui.getMainWindow())


def showGDMLColourMap():
    print('Display Colour Map')
    workBenchColourMap.show()


def lookupColour(col):
    global workBenchColourMap
    print('Lookup Colour')
    try:
        mat = workBenchColourMap.lookupColour(col)

    except NameError:
        workBenchColourMap = GDMLColourMap(FreeCADGui.getMainWindow())
        mat = workBenchColourMap.lookupColour(col)

    return mat


# class GDMLColour(QtGui.QWidget):
# class GDMLColour(QtGui.QPushButton):
class GDMLColour(QtGui.QLineEdit):

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
        # self.setFlat(True)
        self.update()


class GDMLColourHex(QtGui.QLineEdit):

    def __init__(self, colhex):
        super().__init__()
        self.insert(colhex)
        self.setReadOnly(True)


class GDMLColourMapEntry(QtGui.QWidget):

    def __init__(self, colour, colhex, material):
        super().__init__()
        print('Map Entry : '+str(colour))
        self.colour = colour
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(GDMLColour(colour))
        self.hbox.addWidget(GDMLColourHex(colhex))
        self.hbox.addWidget(material)
        self.setLayout(self.hbox)

    def dataPicker(self):
        print('DataPicker')


class GDMLColourMapList(QtGui.QScrollArea):

    def __init__(self, matList):
        super().__init__()
        # Scroll Area which contains the widgets, set as the centralWidget
        # Widget that contains the collection of Vertical Box
        self.widget = QtGui.QWidget()
        self.matList = matList
        # The Vertical Box that contains the Horizontal Boxes of  labels and buttons
        self.vbox = QtGui.QVBoxLayout()
        self.widget.setLayout(self.vbox)

        # Scroll Area Properties
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(self.widget)

    def addEntry(self, colour, colhex, mat):
        from .GDMLMaterials import GDMLMaterial
        print('Add Entry')
        matWidget = GDMLMaterial(self.matList, mat)
        self.vbox.addWidget(GDMLColourMapEntry(colour, colhex, matWidget))

    def getMaterial(self, index):
        # print(dir(self.vbox))
        item = self.vbox.itemAt(index).widget()
        # item.dumpObjectTree()
        # cb = item.findChild(QtGui.QComboBox,'GDMLMaterial')
        cb = item.findChildren(QtGui.QComboBox)[0]
        m = cb.currentText()
        print(m)
        return(m)

    def setMaterial(self, index, mat):
        item = self.vbox.itemAt(index).widget()
        cb = item.findChildren(QtGui.QComboBox)[0]
        matIndex = cb.findText(mat)
        if matIndex != -1:
            cb.setCurrentIndex(matIndex)


class GDMLColourMap(QtGui.QDialog):
    def __init__(self, parent):
        super(GDMLColourMap, self).__init__(parent, QtCore.Qt.Tool)
        self.initUI()

    def initUI(self):
        self.result = userCancelled
        # create our window
        # define window           xLoc,yLoc,xDim,yDim
        self.setGeometry(150, 450, 650, 550)
        self.setWindowTitle("Map FreeCAD Colours to GDML Materials")
        self.setMouseTracking(True)
        self.buttonNew = QtGui.QPushButton(translate('GDML', 'New'))
        self.buttonNew.clicked.connect(self.onNew)
        self.buttonLoad = QtGui.QPushButton(translate('GDML', 'Load'))
        self.buttonLoad.clicked.connect(self.onLoad)
        self.buttonSave = QtGui.QPushButton(translate('GDML', 'Save'))
        self.buttonSave.clicked.connect(self.onSave)
        self.buttonScan = QtGui.QPushButton(translate('GDML', 'Scan'))
        self.buttonScan.clicked.connect(self.onScan)
        headerLayout = QtGui.QHBoxLayout()
        headerLayout.addWidget(self.buttonNew)
        headerLayout.addWidget(self.buttonLoad)
        headerLayout.addWidget(self.buttonSave)
        headerLayout.addWidget(self.buttonScan)
        self.coloursLayout = QtGui.QGridLayout()
        mainLayout = QtGui.QVBoxLayout(self)
        mainLayout.addLayout(headerLayout)
        mainLayout.addLayout(self.coloursLayout)
        from .GDMLMaterials import getMaterialsList
        self.matList = getMaterialsList()
        self.mapList = GDMLColourMapList(self.matList)
        self.colorDict = {}
        self.scanDocument(1)
        print(self.colorDict)
        # for c in self.colorList :
        #    self.mapList.addEntry(QtGui.QColor(c[0]*255,c[1]*255,c[2]*255))
        # create Labels
        self.label1 = self.mapList
        self.coloursLayout.addWidget(self.label1, 0, 0)
        #  cancel button
        cancelButton = QtGui.QPushButton('Cancel', self)
        cancelButton.clicked.connect(self.onCancel)
        cancelButton.setAutoDefault(True)
        self.coloursLayout.addWidget(cancelButton, 2, 1)

        # OK button
        okButton = QtGui.QPushButton('Set Materials', self)
        okButton.clicked.connect(self.onOk)
        self.coloursLayout.addWidget(okButton, 2, 0)
        # now make the window visible
        self.setLayout(mainLayout)
        self.show()

    def scanDocument(self, action):
        doc = FreeCAD.ActiveDocument
        print('Active')
        print(doc)
        if doc is None:
            return
        # print(dir(doc))
        if hasattr(doc, 'Objects'):
            # print(doc.Objects)
            # self.colorList = []
            for obj in doc.Objects:
                # print(dir(obj))
                if hasattr(obj, 'ViewObject'):
                    # print(dir(obj.ViewObject))
                    if hasattr(obj.ViewObject, 'isVisible'):
                        if obj.ViewObject.isVisible:
                            if hasattr(obj.ViewObject, 'ShapeColor'):
                                colour = obj.ViewObject.ShapeColor
                                # print(colour)
                                colhex = '#'+''.join('{:02x}'.format(round(v*255))
                                                     for v in colour)
                                if action == 1:  # Build Map
                                    if not(colhex in self.colorDict):
                                        print(f'Add colour {colhex} {colour}')
                                        if hasattr(obj, 'material'):
                                            material = obj.material
                                        else:
                                            material = None
                                        self.addColour2Map(
                                            colour, colhex, material)
                                        self.colorDict.update(
                                            [(colhex, len(self.colorDict))])
                                if action == 2:  # Update Object Material
                                    if hasattr(obj, 'Shape'):
                                        mapIdx = self.colorDict[colhex]
                                        print(f'Found {colhex} : id {mapIdx}')
                                        print(obj.Label)
                                        m = self.mapList.getMaterial(mapIdx)
                                        # Only add
                                        if not hasattr(obj, 'material'):
                                            obj.addProperty("App::PropertyEnumeration",
                                                            "material", "GDML", "Material")
                                            obj.material = self.matList
                                        # Ignore GDML objects which will have Proxy
                                        if not hasattr(obj, 'Proxy'):
                                            obj.material = self.matList.index(
                                                m)

    def addColour2Map(self, c, hex, material):
        self.mapList.addEntry(QtGui.QColor(c[0]*255, c[1]*255,
                                           c[2]*255), hex, material)

    def lookupColour(self, col):
        print('Lookup Colour')
        idx = self.colorList.index(col)
        print(idx)
        entry = self.mapList.vbox.itemAt(idx).widget()
        print(entry)
        mat = entry.hbox.itemAt(1).widget().currentText()
        print(mat)
        return mat

    def onCancel(self):
        self.result = userCancelled
        self.close()

    def onOk(self):
        self.result = userOK
        print('Set Materials')
        self.scanDocument(2)
        # self.close()

    def onNew(self):
        print('onNew')

    def hex_to_rgb(self, value):
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16)
                     for i in range(0, lv, lv // 3))

    def onLoad(self):
        import csv
        from .importGDML import processXML, joinDir
        print('onLoad')
        processXML(FreeCAD.ActiveDocument, joinDir(
            'Resources/MapMaterials.xml'))
        # reset mapList
        self.mapList = GDMLColourMapList(self.matList)
        with open(joinDir('Resources/ColorDict.csv'), 'r') as file:
            reader = csv.reader(file)
            for i, row in enumerate(reader):
                colhex = row[0]
                colour = self.hex_to_rgb(colhex)
                print(f'colour : {colour}')
                material = row[1]
                print(row)
                print(row[1])
                idx = self.matList.index(row[1])
                self.addColour2Map(colour, colhex, material)
                self.colorDict.update([(colhex, idx)])
                self.mapList.setMaterial(i, material)

    def onSave(self):
        print('onSave')
        # Save materials
        from .exportGDML import exportMaterials
        from .init_gui import joinDir
        matGrp = FreeCAD.ActiveDocument.getObject('Materials')
        if matGrp is not None:
            exportMaterials(matGrp, joinDir('Resources/MapMaterials.xml'))
        # Save Color Dictionary
        f = open(joinDir('Resources/ColorDict.csv'), 'w')
        for key, value in self.colorDict.items():
            print(f'key {key} value {value}')
            print(self.mapList.getMaterial(value))
            f.write(f'{key},{self.mapList.getMaterial(value)}\n')
        f.close()

    def onScan(self):
        print('onScan')
        self.scanDocument(1)
        print('Update Layout')
        self.coloursLayout.update()

    def getGDMLMaterials(self):
        print('getGDMLMaterials')
        matList = []
        doc = FreeCAD.activeDocument()
        try:
            materials = doc.Materials
            geant4 = doc.Geant4
            g4Mats = doc.getObject('G4Materials')

        except:
            from .importGDML import processXML
            from .init_gui import joinDir

            print('Load Geant4 Materials XML')
            processXML(doc, joinDir("Resources/Geant4Materials.xml"))
            materials = doc.Materials
        try:
            if materials is not None:
                for m in materials.OutList:
                    matList.append(m.Label)
                # print(matList)
        except:
            pass

        try:
            if g4Mats is not None:
                for m in g4Mats.OutList:
                    matList.append(m.Label)
                # print(matList)
        except:
            pass

        return matList


# Class definitions

# Function definitions

# Constant definitions
global userCancelled, userOK
userCancelled = "Cancelled"
userOK = "OK"
