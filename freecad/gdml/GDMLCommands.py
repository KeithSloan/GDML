# **************************************************************************d
# *                                                                        *
# *   Copyright (c) 2017 Keith Sloan <keith@sloan-home.co.uk>              *
# *             (c) Dam Lambert 2020                                       *
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

__title__ = "FreeCAD GDML Workbench - GUI Commands"
__author__ = "Keith Sloan"
__url__ = ["http://www.freecadweb.org"]

"""
This Script includes the GUI Commands of the GDML module
"""

import FreeCAD, FreeCADGui
import Part
from PySide import QtGui, QtCore


if FreeCAD.GuiUp:
    try:
        _encoding = QtGui.QApplication.UnicodeUTF8

        def translate(context, text):
            "convenience function for Qt translator"
            return QtGui.QApplication.translate(context, text, None, _encoding)

    except AttributeError:

        def translate(context, text):
            "convenience function for Qt translator"
            return QtGui.QApplication.translate(context, text, None)


class importPrompt(QtGui.QDialog):
    def __init__(self, *args):
        super(importPrompt, self).__init__()
        self.initUI()

    def initUI(self):
        importButton = QtGui.QPushButton("Import")
        importButton.clicked.connect(self.onImport)
        scanButton = QtGui.QPushButton("Scan Vol")
        scanButton.clicked.connect(self.onScan)
        #
        buttonBox = QtGui.QDialogButtonBox()
        buttonBox.setFixedWidth(400)
        # buttonBox = Qt.QDialogButtonBox(QtCore.Qt.Vertical)
        buttonBox.addButton(importButton, QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(scanButton, QtGui.QDialogButtonBox.ActionRole)
        #
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
        # self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        # define window xLoc,yLoc,xDim,yDim
        self.setGeometry(650, 650, 0, 50)
        self.setWindowTitle("Choose an Option    ")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.retStatus = 0

    def onImport(self):
        self.retStatus = 1
        self.close()

    def onScan(self):
        self.retStatus = 2
        self.close()


def getSelectedMaterial():
    from .exportGDML import nameFromLabel
    from .GDMLObjects import GDMLmaterial

    list = FreeCADGui.Selection.getSelection()
    if list is not None:
        for obj in list:
            if hasattr(obj, "Proxy"):
                if isinstance(obj.Proxy, GDMLmaterial) is True:
                    return nameFromLabel(obj.Label)

    return 0


def getSelectedPM():
    from .exportGDML import nameFromLabel
    from .GDMLObjects import GDMLmaterial

    objPart = None
    material = 0
    list = FreeCADGui.Selection.getSelection()
    if list is not None:
        for obj in list:
            if hasattr(obj, "Proxy"):
                if (
                    isinstance(obj.Proxy, GDMLmaterial) is True
                    and material == 0
                ):
                    material = nameFromLabel(obj.Label)

            if obj.TypeId == "App::Part" and objPart is None:
                objPart = obj

            if objPart is not None and material != 0:
                return objPart, material

    if objPart is None:
        # objPart = FreeCAD.ActiveDocument.getObject('worldVOL')
        objPart = getWorldVol()

    return objPart, material


def createPartVol(obj):
    from .importGDML import addSurfList

    # Create Part(GDML Vol) Shared with a number of Features
    LVname = "LV-" + obj.Label
    doc = FreeCAD.ActiveDocument
    if hasattr(obj, "InList"):
        if len(obj.InList) > 0:
            parent = obj.InList[0]
            vol = parent.newObject("App::Part", LVname)
        else:
            vol = doc.addObject("App::Part", LVname)
        if hasattr(vol, "Material"):
            print("Hide Material")
            vol.setEditorMode("Material", 2)
        addSurfList(doc, vol)
        return vol
    return None


def insertPartVol(objPart, LVname, solidName):
    from .importGDML import addSurfList

    doc = FreeCAD.ActiveDocument
    if objPart is None:
        vol = doc.addObject("App::Part", LVname)
    else:
        vol = objPart.newObject("App::Part", LVname)
    if hasattr(vol, "Material"):
        print("Hide Material")
        vol.setEditorMode("Material", 2)

    obj = vol.newObject("Part::FeaturePython", solidName)
    addSurfList(doc, vol)
    return obj


class ColourMapFeature:
    def Activated(self):
        from PySide import QtGui, QtCore

        # import sys
        from .GDMLColourMap import resetGDMLColourMap, showGDMLColourMap

        print("Add colour Map")
        resetGDMLColourMap()
        showGDMLColourMap()
        return

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDMLColourMapFeature",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDMLColourMapFeature", "Add Colour Map"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDMLColourMapFeature", "Add Colour Map"
            ),
        }


class GDMLSetSkinSurface(QtGui.QDialog):
    def __init__(self, sel):
        super(GDMLSetSkinSurface, self).__init__()
        self.select = sel
        self.initUI()

    def initUI(self):
        print("initUI")
        self.setGeometry(150, 150, 250, 250)
        self.setWindowTitle("Set Skin Surface")
        self.surfacesCombo = QtGui.QComboBox()
        # May have been moved
        opticals = FreeCAD.ActiveDocument.getObject("Opticals")
        print(opticals.Group)
        for g in opticals.Group:
            if g.Name == "Surfaces":
                self.surfList = []
                for s in g.Group:
                    print(s.Name)
                    self.surfList.append(s.Name)
        self.surfList.append("None")
        self.surfacesCombo.addItems(self.surfList)
        # self.surfacesCombo.currentIndexChanged.connect(self.surfaceChanged)
        self.buttonSet = QtGui.QPushButton(
            translate("GDML", "Set SkinSurface")
        )
        self.buttonSet.clicked.connect(self.onSet)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.surfacesCombo)
        layout.addWidget(self.buttonSet)
        self.setLayout(layout)

    def onSet(self):
        surf = self.surfacesCombo.currentText()
        obj = self.select[0].Object
        print(self.select[0].Object)
        print(surf)
        if hasattr(obj, "SkinSurface"):
            obj.SkinSurface = surf
        else:
            obj.addProperty(
                "App::PropertyEnumeration",
                "SkinSurface",
                "GDML",
                "SkinSurface",
            )
            obj.SkinSurface = self.surfLst
            obj.SkinSurface = self.surfList.index(surf)
        self.close()

    def surfaceChanged(self, index):
        self.surfacesCombo.blockSignals(True)
        self.surfacesCombo.clear()
        surface = self.surfacesCombo.currentText()
        print(surface)


class SetSkinSurfaceFeature:
    def Activated(self):
        from PySide import QtGui, QtCore

        print("Add SetSkinSurface")
        sel = FreeCADGui.Selection.getSelectionEx()
        # print(sel)
        for s in sel:
            # print(s)
            # print(dir(s))
            if hasattr(s.Object, "LinkedObject"):
                obj = s.Object.LinkedObject
            else:
                obj = s.Object
            if obj.TypeId == "App::Part":
                dialog = GDMLSetSkinSurface(sel)
                dialog.exec_()
        return

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_SetSkinSurface",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_SetSkinSurface", "Set Skin Surface"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDML_SetSkinSurface", "Set Skin Surface"
            ),
        }


class GDMLSetSensDet(QtGui.QDialog):
    def __init__(self, sel):
        super(GDMLSetSensDet, self).__init__()
        self.select = sel
        self.initUI()

    def initUI(self):
        print("initUI")
        self.setGeometry(150, 150, 250, 250)
        self.setWindowTitle("Set SensDet")
        self.auxvalue = QtGui.QLineEdit()
        self.buttonSet = QtGui.QPushButton(translate("GDML", "Set SensDet"))
        self.buttonSet.clicked.connect(self.onSet)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.auxvalue)
        layout.addWidget(self.buttonSet)
        self.setLayout(layout)

    def onSet(self):
        obj = self.select[0].Object
        auxvalue = self.auxvalue.text()
        print(f"auxvalue {auxvalue}")
        if hasattr(obj, "SensDet"):
            obj.SensDet = auxvalue
        else:
            obj.addProperty(
                "App::PropertyString", "SensDet", "GDML", "SensDet"
            ).SensDet = auxvalue
        self.close()


class SetSensDetFeature:
    def Activated(self):
        from PySide import QtGui, QtCore

        print("Add SetSensDet")
        sel = FreeCADGui.Selection.getSelectionEx()
        # print(sel)
        for s in sel:
            # print(s)
            # print(dir(s))
            if hasattr(s.Object, "LinkedObject"):
                obj = s.Object.LinkedObject
            else:
                obj = s.Object
            if obj.TypeId == "App::Part":
                dialog = GDMLSetSensDet(sel)
                dialog.exec_()
        return

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_SetSensDet",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_SetSensDet", "Set SensDet"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDML_SetSensDet", "Set SensDet"
            ),
        }


class noCommonFacePrompt(QtGui.QDialog):
    def __init__(self, *args):
        super(noCommonFacePrompt, self).__init__()
        self.initUI()

    def initUI(self):
        overrideButton = QtGui.QPushButton("Override")
        overrideButton.clicked.connect(self.onOverride)
        cancelButton = QtGui.QPushButton("Cancel")
        cancelButton.clicked.connect(self.onCancel)
        #
        buttonBox = QtGui.QDialogButtonBox()
        buttonBox.setFixedWidth(400)
        # buttonBox = Qt.QDialogButtonBox(QtCore.Qt.Vertical)
        buttonBox.addButton(overrideButton, QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(cancelButton, QtGui.QDialogButtonBox.ActionRole)
        #
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
        # self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        # define window         xLoc,yLoc,xDim,yDim
        self.setGeometry(650, 650, 0, 50)
        self.setWindowTitle("No Common Face Found")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.retStatus = 0

    def onOverride(self):
        self.retStatus = 1
        self.close()

    def onCancel(self):
        # self.retStatus = 2
        self.close()


class SetBorderSurfaceFeature:
    def Activated(self):
        from PySide import QtGui, QtCore
        from .exportGDML import getSubVols, checkFaces

        print("Add SetBorderSurface")
        sel = FreeCADGui.Selection.getSelectionEx()
        # print(len(sel))
        if len(sel) != 3:
            return

        surfaceObj = None
        partList = []
        for s in sel:
            if hasattr(s, "Object"):
                # print(s.Object)
                obj = s.Object
                # print(obj.TypeId)
                if obj.TypeId == "App::Part":
                    # print('Part Added')
                    partList.append(obj)

                elif obj.TypeId == "App::Link":
                    if obj.LinkedObject.TypeId == "App::Part":
                        # print('Linked Part Added')
                        partList.append(obj)

                elif obj.TypeId == "App::DocumentObjectGroupPython":
                    # print(dir(obj))
                    if hasattr(obj, "InList"):
                        # print(obj.InList)
                        parent = obj.InList[0]
                        # print(parent.Name)
                        if parent.Name == "Surfaces":
                            surfaceObj = obj

        doc = FreeCAD.ActiveDocument
        print(f"Surface Obj {surfaceObj.Name}")
        # print(f'Part List {partList}')
        if surfaceObj is not None and len(partList) == 2:
            print("Action set Border Surface")
            #            commonFaceFlag, commonFaces = self.checkCommonFace(partList)
            dict1 = getSubVols(partList[0], FreeCAD.Placement())
            dict2 = getSubVols(partList[1], FreeCAD.Placement())
            commonFaceFlag = False
            for assem1, list1 in dict1.items():
                for assem2, list2 in dict2.items():
                    for pair1 in list1:
                        for pair2 in list2:
                            obj1 = pair1[0]
                            obj2 = pair2[0]
                            if hasattr(obj1, "Shape") and hasattr(
                                obj2, "Shape"
                            ):
                                commonFaceFlag = checkFaces(pair1, pair2)
                                if commonFaceFlag is True:
                                    break
            if commonFaceFlag is True:
                self.SetBorderSurface(
                    doc, surfaceObj, partList, commonFaceFlag
                )

            else:
                print("No Valid common Face")
                dialog = noCommonFacePrompt()
                dialog.exec_()
                if dialog.retStatus == 1:
                    self.SetBorderSurface(doc, surfaceObj, partList, False)

        return

    def SetBorderSurface(self, doc, surfaceObj, partList, commonFaceFlg):
        from .GDMLObjects import GDMLbordersurface

        print("Action set Border Surface")
        print(f"Generate Name from {surfaceObj.Name}")
        surfaceName = self.SurfaceName(doc, surfaceObj.Name)
        print(f"Surface Name {surfaceName}")
        obj = doc.addObject("App::FeaturePython", surfaceName)
        GDMLbordersurface(
            obj,
            surfaceName,
            surfaceObj.Name,
            partList[0],
            partList[1],
            commonFaceFlg,
        )

    def SurfaceName(self, doc, name):
        index = 1
        while doc.getObject(name + str(index)) is not None:
            index += 1
        return name + str(index)

    def checkCommonFace(self, partList):
        print("Check Common Face")
        shape0 = self.adjustShape(partList[0])
        shape1 = self.adjustShape(partList[1])
        return self.commonFace(shape0, shape1)

    def commonFace(self, shape0, shape1):
        print(f"Common Face : {len(shape0.Faces)} : {len(shape1.Faces)}")
        tolerence = 1e-7
        commonList = []
        for i, face0 in enumerate(shape0.Faces):
            for j, face1 in enumerate(shape1.Faces):
                comShape = face0.common(face1, tolerence)
                if len(comShape.Faces) > 0:
                    # Append Tuple
                    commonList.append((i, j))
                    print(f"Common Face shape0 {i} shape1 {j}")
        num = len(commonList)
        print(f"{num} common Faces")
        if num > 0:
            return True, commonList
        else:
            return False, None

    def getGDMLObject(self, list):
        # need to make more robust check types etc
        if len(list) > 1:
            return list[1]
        else:
            return list[0]

    def adjustShape(self, part):
        # print("Adjust Shape")
        # print(part.Name)
        # print(part.OutList)
        # print(f'Placement {part.Placement.Base}')
        # Use Matrix rather than Placement in case rotated
        # placement = part.Placement.Base
        matrix = part.Placement.toMatrix()
        if hasattr(part, "LinkedObject"):
            # print(f'Linked Object {part.LinkedObject}')
            part = part.getLinkedObject()
            # print(part.Name)
            # print(part.OutList)
            # print(f'Linked Placement {part.Placement.Base}')
        obj = self.getGDMLObject(part.OutList)
        obj.recompute()
        # Shape is immutable so have to copy
        # Realthunder recommends avoid deep copy
        shape = Part.Shape(obj.Shape)
        # print(f'Shape Valid {shape.isValid()}')
        # print(dir(shape))
        # Use saved Matrix in case of linked Object
        return shape.transformGeometry(matrix)

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_SetBorderSurface",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_SetBorderSurface", "Set Border Surface"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDML_SetBorderSurface", "Set Border Surface"
            ),
        }


class GDMLSetMaterial(QtGui.QDialog):
    def __init__(self, selList):
        super(GDMLSetMaterial, self).__init__()
        self.SelList = selList
        self.initUI()

    def initUI(self):
        from .GDMLMaterials import GDMLMaterial, newGetGroupedMaterials

        print("initUI")
        self.setGeometry(150, 150, 250, 250)
        self.setWindowTitle("Set GDML Material")
        self.setMouseTracking(True)
        self.buttonSet = QtGui.QPushButton(translate("GDML", "Set Material"))
        self.buttonSet.clicked.connect(self.onSet)
        self.groupedMaterials = (
            newGetGroupedMaterials()
        )  # this build, then returns all materials
        self.groupsCombo = QtGui.QComboBox()
        groups = [group for group in self.groupedMaterials]
        self.groupsCombo.addItems(groups)
        self.groupsCombo.currentIndexChanged.connect(self.groupChanged)
        self.materialComboBox = QtGui.QComboBox()
        self.materialComboBox.addItems(self.groupedMaterials[groups[0]])
        self.matList = []
        for group in self.groupedMaterials:
            print(group)
            self.matList += self.groupedMaterials[group]
        # print(len(self.matList))
        self.completer = QtGui.QCompleter(self.matList, self)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.materialComboBox.setCompleter(self.completer)
        self.materialComboBox.setEditable(True)
        self.materialComboBox.currentTextChanged.connect(self.materialChanged)
        self.lineedit = QtGui.QLineEdit()
        self.lineedit.setCompleter(self.completer)
        self.completer.activated.connect(self.completionActivated)
        # self.materialComboBox.setEditable(False)
        combosLayout = QtGui.QHBoxLayout()
        combosLayout.addWidget(self.groupsCombo)
        combosLayout.addWidget(self.materialComboBox)
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.lineedit)
        mainLayout.addItem(combosLayout)
        mainLayout.addWidget(self.buttonSet)
        self.setLayout(mainLayout)
        obj = self.SelList[0].Object
        if hasattr(obj, "material"):
            mat = obj.material
            self.lineedit.setText(mat)
            self.setMaterial(mat)
        self.show()

    def setMaterial(self, text):
        from .GDMLObjects import GroupedMaterials

        for i, group in enumerate(GroupedMaterials):
            if text in GroupedMaterials[group]:
                self.groupsCombo.blockSignals(True)
                self.groupsCombo.setCurrentIndex(i)
                self.groupsCombo.blockSignals(False)
                self.groupChanged(i)
                self.materialComboBox.blockSignals(True)
                self.materialComboBox.setCurrentText(text)
                self.materialComboBox.blockSignals(False)

    def completionActivated(self, text):
        self.setMaterial(text)

    def groupChanged(self, index):
        print("Group Changed")
        from .GDMLObjects import GroupedMaterials

        print(self.materialComboBox.currentText())
        self.materialComboBox.blockSignals(True)
        self.materialComboBox.clear()
        group = self.groupsCombo.currentText()
        self.materialComboBox.addItems(GroupedMaterials[group])
        print(self.materialComboBox.currentText())
        self.lineedit.setText(self.materialComboBox.currentText())
        self.materialComboBox.blockSignals(False)

    def materialChanged(self, text):
        self.lineedit.setText(text)

    def onSet(self):
        # mat = self.materialComboBox.currentText()
        mat = self.lineedit.text()
        if mat not in self.matList:
            print(f"Material {mat} not defined")
            return

        print(f"Set Material {mat}")
        for sel in self.SelList:
            obj = sel.Object
            if hasattr(obj, "material"):
                #  May have an invalid enumeration from previous versions
                try:
                    obj.material = mat

                except ValueError:
                    pass

            else:
                obj.addProperty(
                    "App::PropertyEnumeration", "material", "GDML", "Material"
                )
                obj.material = self.matList
                obj.material = self.matList.index(mat)


class GDMLScale(QtGui.QDialog):
    def __init__(self, selList):
        super(GDMLScale, self).__init__()
        self.SelList = selList
        self.initialState = {}
        self.saveState()
        self.setupUi()
        self.xScale.valueChanged.connect(self.scaleChanged)
        self.yScale.valueChanged.connect(self.scaleChanged)
        self.zScale.valueChanged.connect(self.scaleChanged)
        self.scaleButton.clicked.connect(self.onSet)
        self.cancelButton.clicked.connect(self.onCancel)
        self.initUI()

    def initUI(self):
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setMouseTracking(True)
        self.show()

    def setupUi(self):
        self.setGeometry(150, 150, 400, 250)
        self.checkBox = QtGui.QCheckBox(self)
        self.checkBox.setGeometry(QtCore.QRect(40, 160, 141, 22))
        self.checkBox.setObjectName("checkBox")
        self.verticalLayoutWidget = QtGui.QWidget(self)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(40, 20, 341, 116))
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.xlabel = QtGui.QLabel(self.verticalLayoutWidget)
        self.horizontalLayout.addWidget(self.xlabel)
        self.xScale = QtGui.QDoubleSpinBox(self.verticalLayoutWidget)
        self.xScale.setMinimum(0.01)
        self.xScale.setMaximum(100.0)
        self.xScale.setProperty("value", 1.0)
        self.horizontalLayout.addWidget(self.xScale)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.yLabel = QtGui.QLabel(self.verticalLayoutWidget)
        self.horizontalLayout_3.addWidget(self.yLabel)
        self.yScale = QtGui.QDoubleSpinBox(self.verticalLayoutWidget)
        self.yScale.setMinimum(0.01)
        self.yScale.setMaximum(100.0)
        self.yScale.setProperty("value", 1.0)
        self.horizontalLayout_3.addWidget(self.yScale)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.zLabel = QtGui.QLabel(self.verticalLayoutWidget)
        self.horizontalLayout_4.addWidget(self.zLabel)
        self.zScale = QtGui.QDoubleSpinBox(self.verticalLayoutWidget)
        self.zScale.setMinimum(0.01)
        self.zScale.setMaximum(100.0)
        self.zScale.setProperty("value", 1.0)
        self.horizontalLayout_4.addWidget(self.zScale)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.scaleButton = QtGui.QPushButton(self)
        self.scaleButton.setGeometry(QtCore.QRect(90, 210, 88, 34))
        self.cancelButton = QtGui.QPushButton(self)
        self.cancelButton.setGeometry(QtCore.QRect(200, 210, 88, 34))

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("GDMLScale", "Scale GDML solids"))
        self.checkBox.setText(_translate("GDMLScale", "Uniform scaling"))
        self.xlabel.setText(_translate("GDMLScale", "X factor"))
        self.yLabel.setText(_translate("GDMLScale", "Y factor"))
        self.zLabel.setText(_translate("GDMLScale", "Z factor"))
        self.xScale.setToolTip(
            _translate("GDMLScale", "Scaling factor (0.01 to 100)")
        )
        self.yScale.setToolTip(
            _translate("GDMLScale", "Scaling factor (0.01 to 100)")
        )
        self.zScale.setToolTip(
            _translate("GDMLScale", "Scaling factor (0.01 to 100)")
        )
        self.scaleButton.setText(_translate("GDMLScale", "OK"))
        self.cancelButton.setText(_translate("GDMLScale", "Cancel"))

    def scaleChanged(self, value):
        self.xScale.blockSignals(True)
        self.yScale.blockSignals(True)
        self.zScale.blockSignals(True)
        if self.checkBox.isChecked():
            self.xScale.setValue(value)
            self.yScale.setValue(value)
            self.zScale.setValue(value)
        self.setScales()

        self.xScale.blockSignals(False)
        self.yScale.blockSignals(False)
        self.zScale.blockSignals(False)

    def setScales(self):
        from .GDMLObjects import GDMLsolid

        scale = FreeCAD.Vector(
            self.xScale.value(), self.yScale.value(), self.zScale.value()
        )
        print(f"Set scale {scale}")
        errShown = False
        for sel in self.SelList:
            obj = sel.Object
            if hasattr(obj, "Proxy") and isinstance(obj.Proxy, GDMLsolid):
                if hasattr(obj, "scale"):
                    obj.scale = scale
                else:
                    obj.addProperty(
                        "App::PropertyVector", "scale", "Base", "scale"
                    ).scale = scale
                    obj.recompute()
            else:
                if not errShown:
                    QtGui.QMessageBox.critical(
                        None,
                        "Not a GDML solid",
                        f"{obj.Label} is not a GDML Solid.\nUse Draft scale instead",
                    )
                    errShown = True

    def onSet(self):
        self.setScales()
        self.accept()
        return

    def onCancel(self):
        # should undo any scaling we have set here
        self.restoreState()
        self.reject()
        return

    def closeEvent(self, event):
        print("Close button")
        self.restoreState()
        event.accept()

    def saveState(self):
        from .GDMLObjects import GDMLsolid

        for sel in self.SelList:
            obj = sel.Object
            if hasattr(obj, "Proxy") and isinstance(obj.Proxy, GDMLsolid):
                if hasattr(obj, "scale"):
                    self.initialState[obj] = {
                        "hadScale": True,
                        "scale": obj.scale,
                    }
                else:
                    self.initialState[obj] = {"hadScale": False}

    def restoreState(self):
        from .GDMLObjects import GDMLsolid

        for sel in self.SelList:
            obj = sel.Object
            if hasattr(obj, "Proxy") and isinstance(obj.Proxy, GDMLsolid):
                savedPars = self.initialState[obj]
                if savedPars["hadScale"] is True:
                    obj.scale = savedPars["scale"]
                else:
                    obj.removeProperty("scale")
                obj.recompute()


class SetMaterialFeature:
    def Activated(self):
        from PySide import QtGui, QtCore

        print("Add SetMaterial")
        cnt = 0
        sel = FreeCADGui.Selection.getSelectionEx()
        # print(sel)
        set = []
        for s in sel:
            # print(s)
            # print(dir(s))
            if hasattr(s.Object, "Shape"):
                cnt += 1
                set.append(s)
        if cnt > 0:
            dialog = GDMLSetMaterial(set)
            dialog.exec_()
        return

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_SetMaterial",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_SetMaterial", "Set Material"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDML_SetMaterial", "Set Material"
            ),
        }


class SetScaleFeature:
    def Activated(self):

        print("Set scale")
        cnt = 0
        sel = FreeCADGui.Selection.getSelectionEx()
        # print(sel)
        validSelections = []
        for s in sel:
            # print(s)
            # print(dir(s))
            if hasattr(s.Object, "Shape"):
                cnt += 1
                validSelections.append(s)
        if cnt > 0:
            dialog = GDMLScale(validSelections)
            dialog.exec_()
        return

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_Scale",
            "MenuText": QtCore.QT_TRANSLATE_NOOP("GDMLScale", "Scale"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDMLScale", "Scales the selected GDML solids"
            ),
        }


class BooleanCutFeature:

    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):

        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) == 2:
            print(sel)
            selObj = "Gui::SelectionObject"
            if sel[0].TypeId == selObj and sel[1].TypeId == selObj:
                if (
                    sel[0].Object.TypeId == "App::Part"
                    and sel[1].Object.TypeId == "App::Part"
                ):
                    print("Boolean Cut")
                    if len(sel[0].Object.InList) > 0:
                        parent = sel[0].Object.InList[0]
                        print("Parent : " + parent.Label)
                        baseVol = sel[0].Object
                        print("Base Vol : " + baseVol.Label)
                        toolVol = sel[1].Object
                        print("Tool Vol : " + toolVol.Label)
                        print(sel[0].Object.OutList)
                        base = sel[0].Object.OutList[-1]
                        print("Base : " + base.Label)
                        tool = sel[1].Object.OutList[-1]
                        print("Tool : " + tool.Label)
                        print("Remove Base")
                        baseVol.removeObject(base)
                        print("Adjust Base Links")
                        base.adjustRelativeLinks(baseVol)
                        toolVol.removeObject(tool)
                        tool.adjustRelativeLinks(toolVol)
                        boolVol = parent.newObject("App::Part", "Bool-Cut")
                        boolVol.addObject(base)
                        boolVol.addObject(tool)
                        boolObj = boolVol.newObject("Part::Cut", "Cut")
                        boolObj.Placement = sel[0].Object.Placement
                        boolObj.Base = base
                        boolObj.Tool = tool
                        boolObj.Tool.Placement.Base = (
                            sel[1].Object.Placement.Base
                            - sel[0].Object.Placement.Base
                        )
                        boolObj.Tool.setEditorMode("Placement", 0)
                        print("Remove Base Vol")
                        FreeCAD.ActiveDocument.removeObject(baseVol.Label)
                        FreeCAD.ActiveDocument.removeObject(toolVol.Label)
                        boolObj.recompute()
                else:
                    print("No Parent Volume/Part")

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_Cut",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "gdmlBooleanFeature", "GDML Cut"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "gdmlBooleanFeature", "GDML Cut"
            ),
        }


class BooleanIntersectionFeature:

    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        import Part

        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) == 2:
            print(sel)
            selObj = "Gui::SelectionObject"
            if sel[0].TypeId == selObj and sel[1].TypeId == selObj:
                if (
                    sel[0].Object.TypeId == "App::Part"
                    and sel[1].Object.TypeId == "App::Part"
                ):
                    print("Boolean Intersection")
                    if len(sel[0].Object.InList) > 0:
                        parent = sel[0].Object.InList[0]
                        print("Parent : " + parent.Label)
                        baseVol = sel[0].Object
                        print("Base Vol : " + baseVol.Label)
                        toolVol = sel[1].Object
                        print("Tool Vol : " + toolVol.Label)
                        baseVol = sel[0].Object
                        print(sel[0].Object.OutList)
                        base = sel[0].Object.OutList[-1]
                        print("Base : " + base.Label)
                        tool = sel[1].Object.OutList[-1]
                        print("Tool : " + tool.Label)
                        print("Remove Base")
                        baseVol.removeObject(base)
                        print("Adjust Base Links")
                        base.adjustRelativeLinks(baseVol)
                        toolVol.removeObject(tool)
                        tool.adjustRelativeLinks(toolVol)
                        boolVol = parent.newObject(
                            "App::Part", "Bool-Intersection"
                        )
                        boolVol.addObject(base)
                        boolVol.addObject(tool)
                        boolObj = boolVol.newObject("Part::Common", "Common")
                        boolObj.Placement = sel[0].Object.Placement
                        boolObj.Base = base
                        boolObj.Tool = tool
                        boolObj.Tool.Placement.Base = (
                            sel[1].Object.Placement.Base
                            - sel[0].Object.Placement.Base
                        )
                        boolObj.Tool.setEditorMode("Placement", 0)
                        FreeCAD.ActiveDocument.removeObject(baseVol.Label)
                        FreeCAD.ActiveDocument.removeObject(toolVol.Label)
                        boolObj.recompute()
                    else:
                        print("No Parent Volume/Part")

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_Intersection",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "gdmlBooleanFeature", "GDML Intersection"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "gdmlBooleanFeature", "GDML Intersection"
            ),
        }


class BooleanUnionFeature:

    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        import Part

        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) == 2:
            print(sel)
            selObj = "Gui::SelectionObject"
            if sel[0].TypeId == selObj and sel[1].TypeId == selObj:
                if (
                    sel[0].Object.TypeId == "App::Part"
                    and sel[1].Object.TypeId == "App::Part"
                ):
                    print("Boolean Union")
                    if len(sel[0].Object.InList) > 0:
                        print(sel[0].Object.InList)
                        parent = sel[0].Object.InList[0]
                        print("Parent : " + parent.Label)
                        baseVol = sel[0].Object
                        print("Base Vol : " + baseVol.Label)
                        toolVol = sel[1].Object
                        print("Tool Vol : " + toolVol.Label)
                        baseVol = sel[0].Object
                        print(f"Base OutList {sel[0].Object.OutList}")
                        for o in sel[0].Object.OutList:
                            print(o.Label)
                        print(f"Tool OutList {sel[1].Object.OutList}")
                        for o in sel[1].Object.OutList:
                            print(o.Label)
                        print(f"True Base {sel[0].Object.OutList[-1].Label}")
                        base = sel[0].Object.OutList[-1]
                        print("Base : " + base.Label)
                        print(f"True Tool {sel[1].Object.OutList[-1].Label}")
                        tool = sel[1].Object.OutList[-1]
                        print("Tool : " + tool.Label)
                        print("Remove Base")
                        baseVol.removeObject(base)
                        print("Adjust Base Links")
                        base.adjustRelativeLinks(baseVol)
                        toolVol.removeObject(tool)
                        tool.adjustRelativeLinks(toolVol)
                        boolVol = parent.newObject("App::Part", "Bool-Union")
                        boolVol.addObject(base)
                        boolVol.addObject(tool)
                        boolObj = boolVol.newObject("Part::Fuse", "Union")
                        boolObj.Placement = sel[0].Object.Placement
                        boolObj.Base = base
                        boolObj.Tool = tool
                        boolObj.Tool.Placement.Base = (
                            sel[1].Object.Placement.Base
                            - sel[0].Object.Placement.Base
                        )
                        boolObj.Tool.setEditorMode("Placement", 0)
                        FreeCAD.ActiveDocument.removeObject(baseVol.Label)
                        FreeCAD.ActiveDocument.removeObject(toolVol.Label)
                        boolObj.recompute()
                    else:
                        print("No Parent Volume")

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_Union",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "gdmlBooleanFeature", "GDML Union"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "gdmlBooleanFeature", "GDML Union"
            ),
        }


class BoxFeature:
    #    def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLBox, ViewProvider

        objPart, material = getSelectedPM()
        if objPart is None:
            vol = FreeCAD.ActiveDocument.addObject("App::Part", "LV-Box")
        else:
            vol = objPart.newObject("App::Part", "LV-Box")
        obj = vol.newObject("Part::FeaturePython", "GDMLBox_Box")
        # print("GDMLBox Object - added")
        # obj, x, y, z, lunits, material
        GDMLBox(obj, 10.0, 10.0, 10.0, "mm", material)
        # print("GDMLBox initiated")
        ViewProvider(obj.ViewObject)
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDMLBoxFeature",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDMLBoxFeature", "Box Object"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDMLBoxFeature", "Box Object"
            ),
        }


class ConeFeature:
    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLCone, ViewProvider

        objPart, material = getSelectedPM()
        obj = insertPartVol(objPart, "LV-Cone", "GDMLCone")
        # print("GDMLCone Object - added")
        #  obj,rmin1,rmax1,rmin2,rmax2,z,startphi,deltaphi,aunit,lunits,material
        GDMLCone(obj, 1, 3, 4, 7, 10.0, 0, 2, "rads", "mm", material)
        # print("GDMLCone initiated")
        ViewProvider(obj.ViewObject)
        # print("GDMLCone ViewProvided - added")
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDMLConeFeature",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDMLConeFeature", "Cone Object"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDMLConeFeature", "Cone Object"
            ),
        }


class EllispoidFeature:
    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLEllipsoid, ViewProvider

        objPart, material = getSelectedPM()
        obj = insertPartVol(objPart, "LV-Ellipsoid", "GDMLEllipsoid")
        # print("GDMLEllipsoid Object - added")
        #  obj,ax, by, cz, zcut1, zcut2, lunit,material
        GDMLEllipsoid(obj, 10, 20, 30, 0, 0, "mm", material)
        # print("GDMLEllipsoid initiated")
        ViewProvider(obj.ViewObject)
        # print("GDMLEllipsoid ViewProvided - added")
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDMLEllipsoidFeature",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDMLEllipsoidFeature", "Ellipsoid Object"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDMLEllipsoidFeature", "Ellipsoid Object"
            ),
        }


class ElliTubeFeature:
    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLElTube, ViewProvider

        objPart, material = getSelectedPM()
        obj = insertPartVol(objPart, "LV-EllipticalTube", "GDMLElTube")
        # print("GDMLElTube Object - added")
        #  obj,dx, dy, dz, lunit, material
        GDMLElTube(obj, 10, 20, 30, "mm", material)
        # print("GDMLElTube initiated")
        ViewProvider(obj.ViewObject)
        # print("GDMLElTube ViewProvided - added")
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDMLElTubeFeature",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDMLElTubeFeature", "ElTube Object"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDMLElTubeFeature", "ElTube Object"
            ),
        }


class SphereFeature:
    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLSphere, ViewProvider

        objPart, material = getSelectedPM()
        # print(objPart)
        # print(material)
        obj = insertPartVol(objPart, "LV-Sphere", "GDMLSphere")
        # print("GDMLSphere Object - added")
        # obj, rmin, rmax, startphi, deltaphi, starttheta, deltatheta,
        #       aunit, lunits, material
        GDMLSphere(
            obj, 10.0, 20.0, 0.0, 2.02, 0.0, 2.02, "rad", "mm", material
        )
        # print("GDMLSphere initiated")
        ViewProvider(obj.ViewObject)
        # print("GDMLSphere ViewProvided - added")
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDMLSphereFeature",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDMLSphereFeature", "Sphere Object"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDMLSphereFeature", "Sphere Object"
            ),
        }


class TorusFeature:
    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLTorus, ViewProvider

        objPart, material = getSelectedPM()
        obj = insertPartVol(objPart, "LV-Torus", "GDMLTorus")
        GDMLTorus(obj, 10, 50, 50, 10, 360, "deg", "mm", material)
        if FreeCAD.GuiUp:
            obj.ViewObject.Visibility = True
            ViewProvider(obj.ViewObject)

            FreeCAD.ActiveDocument.recompute()
            FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDMLTorusFeature",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDMLTorusFeature", "Torus Object"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDMLTorusFeature", "Torus Object"
            ),
        }


class TrapFeature:
    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLTrap, ViewProvider

        objPart, material = getSelectedPM()
        obj = insertPartVol(objPart, "LV-Trap", "GDMLTrap")
        print("GDMLTrap Object - added")
        # obj z, theta, phi, x1, x2, x3, x4, y1, y2,
        # pAlp2, aunits, lunits, material
        GDMLTrap(
            obj,
            10.0,
            0.0,
            0.0,
            6.0,
            6.0,
            6.0,
            6.0,
            7.0,
            7.0,
            0.0,
            "rad",
            "mm",
            material,
        )
        print("GDMLTrap initiated")
        ViewProvider(obj.ViewObject)
        print("GDMLTrap ViewProvided - added")
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDMLTrapFeature",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDMLTrapFeature", "Trap Object"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDMLTrapFeature", "Trap Object"
            ),
        }


class TubeFeature:
    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLTube, ViewProvider

        objPart, material = getSelectedPM()
        obj = insertPartVol(objPart, "LV-Tube", "GDMLTube")
        # print("GDMLTube Object - added")
        # obj, rmin, rmax, z, startphi, deltaphi, aunit, lunits, material
        GDMLTube(obj, 5.0, 8.0, 10.0, 0.52, 1.57, "rad", "mm", material)
        # print("GDMLTube initiated")
        ViewProvider(obj.ViewObject)
        # print("GDMLTube ViewProvided - added")
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDMLTubeFeature",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDMLTubeFeature", "Tube Object"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDMLTubeFeature", "Tube Object"
            ),
        }


class PolyHedraFeature:
    def Activated(self):

        for obj in FreeCADGui.Selection.getSelection():
            # if len(obj.InList) == 0: # allowed only for for top level objects
            print("Action Poly")
            if hasattr(obj, "Shape"):
                print(obj.Shape.ShapeType)
                if hasattr(obj.Shape, "Vertexes"):
                    numVert = len(obj.Shape.Vertexes)
                    print("Number of Vertex : " + str(numVert))
                    print(obj.Shape.Vertexes)
                if hasattr(obj.Shape, "Faces"):
                    print("Faces")
                    # print(dir(obj.Shape.Faces[0]))
                    print(obj.Shape.Faces)
                    planar = self.checkPlanar(obj.Shape.Faces)
                    print(planar)
                if hasattr(obj.Shape, "Edges"):
                    print("Edges")
                    # print(dir(obj.Shape.Edges[0]))
                    print(obj.Shape.Edges)

    def checkPlanar(self, faces):
        import Part

        print("Check Planar")
        for f in faces:
            if not isinstance(f.Surface, Part.Plane):
                return False
        return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_Polyhedra",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_PolyGroup", "Poly Group"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDML_PolyGroup", "PolyHedra Selected Object"
            ),
        }


class iField(QtGui.QWidget):
    def __init__(self, label, len, value, parent=None):
        super(iField, self).__init__(parent)
        self.label = QtGui.QLabel(label)
        self.value = QtGui.QLineEdit()
        self.value.setMaxLength(len)
        self.value.setGeometry(QtCore.QRect(10, 20, 25, 15))
        self.value.setTextMargins(0, 0, 10, 5)
        self.value.setText(value)
        self.label.setBuddy(self.value)
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.value)
        self.setLayout(layout)


class oField(QtGui.QWidget):
    def __init__(self, label, len, value, parent=None):
        super(oField, self).__init__(parent)
        self.label = QtGui.QLabel(label)
        self.value = QtGui.QLineEdit()
        self.value.setMaxLength(len)
        self.value.setGeometry(QtCore.QRect(0, 0, 10, 5))
        self.value.setReadOnly(True)
        self.value.setText(value)
        self.label.setBuddy(self.value)
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.value)
        self.setLayout(layout)

    def sizeHint(self):
        return QtCore.QSize(10, 5)


class AddDecimateWidget(QtGui.QWidget):
    def __init__(self, Obj, *args):
        QtGui.QWidget.__init__(self, *args)
        # bboxGroup  = QtGui.QGroupBox('Objects Bounding Box')
        # laybbox = QtGui.QHBoxLayout()
        # laybbox.addWidget(QtGui.QLabel('Width : '+str(Shape.BoundBox.XLength)))
        # laybbox.addWidget(QtGui.QLabel('Height : '+str(Shape.BoundBox.YLength)))
        # laybbox.addWidget(QtGui.QLabel('Depth : '+str(Shape.BoundBox.ZLength) ))
        # bboxGroup.setLayout(laybbox)
        # maxl = int((Shape.BoundBox.XLength + Shape.BoundBox.YLength + \
        #            Shape.BoundBox.ZLength) / 15)
        self.type = QtGui.QComboBox()
        # self.type.addItems(['sp4cerat','MeshLab','Blender'])
        self.type.addItems(["sp4cerat"])
        self.group1 = QtGui.QGroupBox("Decimate Reduction")
        self.tolerance = iField("Tolerance", 5, "5.0")
        self.reduction = iField("Reduction", 5, "0.8")
        self.parms1layout = QtGui.QHBoxLayout()
        self.parms1layout.addWidget(self.tolerance)
        self.parms1layout.addWidget(self.reduction)
        self.grpLay1 = QtGui.QVBoxLayout()
        self.grpLay1.addLayout(self.parms1layout)
        self.buttonReduction = QtGui.QPushButton(
            translate("GDML", "Decimate Reduction")
        )
        self.grpLay1.addWidget(self.buttonReduction)
        self.group1.setLayout(self.grpLay1)
        self.group2 = QtGui.QGroupBox("Decimate to Size")
        self.targetSize = iField("Target Size", 5, "100")
        self.grpLay2 = QtGui.QVBoxLayout()
        self.grpLay2.addWidget(self.targetSize)
        self.buttonToSize = QtGui.QPushButton(
            translate("GDML", "Decimate To Size")
        )
        self.grpLay2.addWidget(self.buttonToSize)
        self.group2.setLayout(self.grpLay2)
        self.Vlayout = QtGui.QVBoxLayout()
        self.Vlayout.addWidget(self.type)
        self.Vlayout.addWidget(self.group1)
        self.Vlayout.addWidget(self.group2)
        self.setLayout(self.Vlayout)
        self.setWindowTitle(translate("GDML", "Decimate"))

    def leaveEvent(self, event):
        print("Leave Event")
        QtCore.QTimer.singleShot(0, lambda: FreeCADGui.Control.closeDialog())

    def retranslateUi(self, widget=None):
        self.buttonMesh.setText(translate("GDML", "Decimate"))
        self.setWindowTitle(translate("GDML", "Decimate"))


class AddDecimateTask:
    def __init__(self, Obj):
        self.obj = Obj
        self.form = AddDecimateWidget(Obj)
        self.form.buttonReduction.clicked.connect(self.actionReduction)
        self.form.buttonToSize.clicked.connect(self.actionToSize)

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Close)

    def isAllowedAlterSelection(self):
        return True

    def isAllowedAlterView(self):
        return True

    def isAllowedAlterDocument(self):
        return True

    def actionReduction(self):
        from .GmshUtils import TessellatedShape2Mesh

        print("Action Decimate Reduction : " + self.obj.Name)
        # print(dir(self))
        if hasattr(self.obj, "Mesh"):
            mesh = self.obj.Mesh
        else:
            mesh = TessellatedShape2Mesh(self.obj)
        try:
            tolerance = float(self.form.tolerance.value.text())
            reduction = float(self.form.reduction.value.text())
            print("Tolerance : " + str(tolerance))
            print("Reduction : " + str(reduction))
            mesh.decimate(tolerance, reduction)

        except Exception as e:
            print(e)

        # print(dir(self.obj))
        self.obj.Proxy.updateParams(mesh.Topology[0], mesh.Topology[1], False)
        self.obj.recompute()
        self.obj.ViewObject.Visibility = True
        FreeCADGui.SendMsgToActiveView("ViewFit")
        print("Update Gui")
        FreeCADGui.updateGui()

    def actionToSize(self):
        from .GmshUtils import TessellatedShape2Mesh

        print("Action Decimate To Size : " + self.obj.Name)
        #print(dir(self))
        if hasattr(self.obj, "Mesh"):
            mesh = self.obj.Mesh
        else:
            mesh = TessellatedShape2Mesh(self.obj)

        try:
            targetSize = int(self.form.targetSize.value.text())
            print("Target Size : " + str(targetSize))
            mesh.decimate(targetSize)

        except:
            print("Invalid Float Values")

    def leaveEvent(self, event):
        print("Leave Event II")

    def focusOutEvent(self, event):
        print("Out of Focus II")

#class RecombineFeature:
#
#    def Activated(self):
#        from .GDMLObjects import (
#            GDMLGmshTessellated,
#            #GDMLTriangular,
#            ViewProvider,
#            ViewProviderExtension,
#        )
#        from .GmshUtils import recombineMeshObject, getFacets, getVertex, \
#                getMeshLen


#        for obj in FreeCADGui.Selection.getSelection():
#            # if len(obj.InList) == 0: # allowed only for for top level objects
#            print(f"Action Gmsh Recombine {obj.TypeId}")
#            if obj.TypeId == "Mesh::Feature":
#                print(f"Recombine Mesh")
#                recombineMeshObject(obj.Mesh)
#                vol = createPartVol(obj)
#                if hasattr(obj, "material"):
#                    mat = obj.material
#                else:
#                    mat = getSelectedMaterial()
#                recombObj = vol.newObject("Part::FeaturePython",
#                             "GDMLTessellated_RecombinedMesh"+obj.Label)

#                vertex = getVertex()
#                facets = getFacets()
#                meshLen = 0.1   # We don't know Mesh parameters
#                GDMLGmshTessellated(recombObj, obj,
#                         meshLen, vertex, facets,
#                        "mm", getSelectedMaterial())
#                if FreeCAD.GuiUp:
#                   obj.ViewObject.Visibility = False
#                   ViewProvider(recombObj.ViewObject)
#                   recombObj.ViewObject.DisplayMode = "Wireframe"
#                   recombObj.recompute()
#                   FreeCADGui.SendMsgToActiveView("ViewFit")

#    def IsActive(self):
#        if FreeCAD.ActiveDocument is None:
#            return False
#        else:
#            return True
#
#    def GetResources(self):
#        return {
#            "Pixmap": "GDML_Recombine",
#            "MenuText": QtCore.QT_TRANSLATE_NOOP(
#                "GDML_TessGroup", "Recombine Mesh to GDML Tessellation"
#            ),
#            "Decimate": QtCore.QT_TRANSLATE_NOOP(
#                "GDML_TessGroup", "Recombine Selected Mesh"
#            ),
#        }



class DecimateFeature:
    def Activated(self):
        from .GDMLObjects import (
            GDMLTessellated,
            GDMLTriangular,
            ViewProvider,
            ViewProviderExtension,
        )

        for obj in FreeCADGui.Selection.getSelection():
            # if len(obj.InList) == 0: # allowed only for for top level objects
            print("Action Decimate")
            if self.isDecimatable(obj):
                if FreeCADGui.Control.activeDialog() is False:
                    print("Build panel for Decimate")
                    panel = AddDecimateTask(obj)
                    FreeCADGui.Control.showDialog(panel)
                else:
                    print("Already an Active Task")
            return

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_Decimate",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_TessGroup", "Decimate Selected Object"
            ),
            "Decimate": QtCore.QT_TRANSLATE_NOOP(
                "GDML_TessGroup", "Decimate Selected  Object"
            ),
        }

    def isDecimatable(self, obj):
        if hasattr(obj, "Proxy"):
            print(obj.Proxy.Type)
            if (
                obj.Proxy.Type == "GDMLGmshTessellated"
                or obj.Proxy.Type == "GDMLTessellated"
            ):
                return True
        if hasattr(obj, "Mesh"):
            return True
        return False


class AddTessellateWidget(QtGui.QWidget):
    def __init__(self, Obj, GmshType, *args):
        QtGui.QWidget.__init__(self, *args)
        self.Obj = Obj
        self.setWindowTitle(translate("GDML", "Tessellate with Gmsh"))
        bboxGroup = QtGui.QGroupBox("Objects Bounding Box")
        laybbox = QtGui.QHBoxLayout()
        laybbox.addWidget(
            QtGui.QLabel("Width : " + str(Obj.Shape.BoundBox.XLength))
        )
        laybbox.addWidget(
            QtGui.QLabel("Height : " + str(Obj.Shape.BoundBox.YLength))
        )
        laybbox.addWidget(
            QtGui.QLabel("Depth : " + str(Obj.Shape.BoundBox.ZLength))
        )
        bboxGroup.setLayout(laybbox)
        maxl = int( ( Obj.Shape.BoundBox.XLength + Obj.Shape.BoundBox.YLength \
             + Obj.Shape.BoundBox.ZLength) / 3
        )
        # Current Mesh Info
        self.meshInfoGroup = QtGui.QGroupBox("Mesh Info")
        meshInfo = QtGui.QHBoxLayout()
        vertex = facets = ""
        meshCounts = False
        self.tess = self.Obj
        if hasattr(self.Obj, 'tessellated'):
            if self.Obj.tessellated is not None:
                self.tess = self.Obj.tessellated
        if hasattr(self.tess, 'vertex'):
            vertex = str(self.tess.vertex)
            meshCounts = True
        if hasattr(self.tess, 'facets'):
            facets = str(self.tess.facets)
            meshCounts = True
        self.Vertex = oField("Vertex", 6, vertex)
        self.Facets = oField("Facets", 6, facets)
        meshInfo.addWidget(self.Vertex)
        meshInfo.addWidget(self.Facets)
        self.meshInfoGroup.setLayout(meshInfo)
        #self.maxLen = iField("Max Length", 5, str(maxl))
        # Mesh Parameters
        self.meshParmsGroup = QtGui.QGroupBox("Mesh Characteristics")
        # self.tess is set to Obj or Obj.tessellated or
        if hasattr(self.tess, "meshType"):
            mshType = str(self.tess.meshType)
        else:
            mshType = 'Triangular'
        if hasattr(self.tess, "meshMaxLen"):
            mshMaxLen = str(self.tess.meshMaxLen)
        else:
            mshMaxLen = str(maxl)      # Set from Bounding Box
        if hasattr(self.tess, "meshCurveLen"):
            mshCurveLen = str(self.tess.meshCurveLen)
        else:
            mshCurveLen = "10"
        if hasattr(self.tess, "meshLenFromPoint"):
            mshLenFromPoint = str(self.tess.meshFromPoint)
        else:
            mshLenFromPoint = "10"
        self.meshType = QtGui.QComboBox()
        self.meshType.addItems(["Triangular", "Quadrangular", "Parallelograms"])
        self.maxLen = iField("Max Length", 5, mshMaxLen)
        self.curveLen = iField("Curve Length", 5, mshCurveLen)
        self.pointLen = iField("Length from Point", 5, mshLenFromPoint)
        self.meshParmsLayout = QtGui.QGridLayout()
        self.meshParmsLayout.addWidget(self.meshType, 0, 0)
        self.meshParmsLayout.addWidget(self.maxLen, 0, 1)
        self.meshParmsLayout.addWidget(self.curveLen, 1, 0)
        self.meshParmsLayout.addWidget(self.pointLen, 1, 1)
        self.meshParmsGroup.setLayout(self.meshParmsLayout)
        self.buttonMesh = QtGui.QPushButton(translate("GDML", GmshType))
        layoutAction = QtGui.QHBoxLayout()
        layoutAction.addWidget(self.buttonMesh)
        self.Vlayout = QtGui.QVBoxLayout()
        self.Vlayout.addWidget(bboxGroup)
        self.Vlayout.addWidget(self.meshInfoGroup)
        self.Vlayout.addWidget(self.meshParmsGroup)
        self.Vlayout.addLayout(layoutAction)
        self.setLayout(self.Vlayout)
        if meshCounts == False:
            print(f"Not previously Tessellated")
            self.meshInfoGroup.setVisible(False)

    def leaveEvent(self, event):
        print("Leave Event")
        # FreeCADGui.Control.closeDialog()
        # closeDialog()
        # QtCore.QMetaObject.invokeMethod(FreeCADGui.Control, 'closeDialog', QtCore.Qt.QueuedConnection)
        # QtCore.QTimer.singleShot(0, FreeCADGui.Control, SLOT('closeDialog()'))
        # QtCore.QTimer.singleShot(0, FreeCADGui.Control, QtCore.SLOT('closeDialog()'))
        QtCore.QTimer.singleShot(0, lambda: FreeCADGui.Control.closeDialog())

    def retranslateUi(self, widget=None):
        self.buttonMesh.setText(translate("GDML", "Mesh"))
        self.setWindowTitle(translate("GDML", "Tessellate with Gmsh"))

class AddMinTessellateWidget(QtGui.QWidget):
    def __init__(self, Obj, GmshType, *args):
        QtGui.QWidget.__init__(self, *args)
        self.Obj = Obj
        self.setWindowTitle(translate("GDML", "Tessellate with Gmsh Min"))
        # Bounding Box Infp
        bboxGroup = QtGui.QGroupBox("Objects Bounding Box")
        laybbox = QtGui.QHBoxLayout()
        laybbox.addWidget(
            QtGui.QLabel("Width : " + str(Obj.Shape.BoundBox.XLength))
            )
        laybbox.addWidget(
            QtGui.QLabel("Height : " + str(Obj.Shape.BoundBox.YLength))
            )
        laybbox.addWidget(
            QtGui.QLabel("Depth : " + str(Obj.Shape.BoundBox.ZLength))
            )
        bboxGroup.setLayout(laybbox)
        maxl = int( ( Obj.Shape.BoundBox.XLength + Obj.Shape.BoundBox.YLength \
             + Obj.Shape.BoundBox.ZLength) / 15
        )
        # Current Mesh Info
        self.meshInfoGroup = QtGui.QGroupBox("Mesh Info")
        meshInfo = QtGui.QHBoxLayout()
        vertex = facets = ""
        meshCounts = False
        self.tess = self.Obj
        if hasattr(self.Obj, 'tessellated'):
            if self.Obj.tessellated is not None:
                self.tess = self.Obj.tessellated
        if hasattr(self.tess, 'vertex'):
            vertex = str(self.tess.vertex)
            meshCounts = True
        if hasattr(self.tess, 'facets'):
            facets = str(self.tess.facets)
            meshCounts = True
        self.Vertex = oField("Vertex", 6, vertex)
        self.Facets = oField("Facets", 6, facets)
        meshInfo.addWidget(self.Vertex)
        meshInfo.addWidget(self.Facets)
        self.meshInfoGroup.setLayout(meshInfo)
        #self.maxLen = iField("Max Length", 5, str(maxl))
        # Mesh Parameters
        self.meshParmsGroup = QtGui.QGroupBox("Mesh Characteristics")
        # self.tess is set to Obj or Obj.tessellated or
        if hasattr(self.tess, "surfaceDev"):
            sd = str(self.tess.surfaceDev)
        else:
            sd = ".10"    
        self.surfaceDeviation = iField("Surface Deviation", 5, sd)
        if hasattr(self.tess, "angularDev"):
            ad = str(self.tess.angularDev)
        else:
            ad = "30"
        self.angularDeviation = iField("Angular Deviation", 5, ad)
        self.meshParmsLayout = QtGui.QGridLayout()
        #self.meshParmsLayout.addWidget(self.type, 0, 0)
        #self.meshParmsLayout.addWidget(self.maxLen, 0, 1)
        self.meshParmsLayout.addWidget(self.surfaceDeviation, 1, 0)
        self.meshParmsLayout.addWidget(self.angularDeviation, 1, 1)
        self.meshParmsGroup.setLayout(self.meshParmsLayout)
        # Action Buttons
        self.buttonMesh = QtGui.QPushButton(translate("GDML", GmshType))
        layoutAction = QtGui.QHBoxLayout()
        layoutAction.addWidget(self.buttonMesh)
        # Panel Layout
        self.Vlayout = QtGui.QVBoxLayout()
        self.Vlayout.addWidget(bboxGroup)
        self.Vlayout.addWidget(self.meshInfoGroup)
        self.Vlayout.addWidget(self.meshParmsGroup)
        self.Vlayout.addLayout(layoutAction)
        self.setLayout(self.Vlayout)
        if meshCounts == False:
            print(f"Not previously Tessellated")
            self.meshInfoGroup.setVisible(False)


    def leaveEvent(self, event):
        print("Leave Event")
        # FreeCADGui.Control.closeDialog()
        # closeDialog()
        # QtCore.QMetaObject.invokeMethod(FreeCADGui.Control, 'closeDialog', QtCore.Qt.QueuedConnection)
        # QtCore.QTimer.singleShot(0, FreeCADGui.Control, SLOT('closeDialog()'))
        # QtCore.QTimer.singleShot(0, FreeCADGui.Control, QtCore.SLOT('closeDialog()'))
        QtCore.QTimer.singleShot(0, lambda: FreeCADGui.Control.closeDialog())

    def retranslateUi(self, widget=None):
        self.buttonMesh.setText(translate("GDML", "Mesh"))
        self.setWindowTitle(translate("GDML", "Tessellate with Gmsh Min"))


class AddMinTessellateTask:
    def __init__(self, Obj):
        # Operation Types
        #   1 Mesh      - Object or GDML Object
        #   2 reMesh    - Object or GDML Object
        #   3 reMesh    - GmshTessellate or Tessellated
        self.obj = Obj
        self.form = AddMinTessellateWidget(Obj, "Min Gmsh")
        self.form.buttonMesh.clicked.connect(self.actionMesh)
        # self.form.buttonload.clicked.connect(self.loadelement)
        # self.form.buttonsave.clicked.connect(self.saveelement)
        # self.form.buttonrefresh.clicked.connect(self.refreshelement)

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Close)

    def isAllowedAlterSelection(self):
        return True

    def isAllowedAlterView(self):
        return True

    def isAllowedAlterDocument(self):
        return True

    def processMesh(self, vertex, facets):
        from .GDMLObjects import ViewProvider

        print("Update Tessellated Object Operation Type {self.operationType}")
        #print(dir(self))
        #print("Object Name " + self.obj.Name)
        print("Object Name " + self.obj.Label)
        print("Object Type " + self.obj.TypeId)
        if hasattr(self.obj, "Proxy"):
            print("Proxy")
            if hasattr(self.obj.Proxy, "Type"):
                print(self.obj.Proxy.Type)
                if ( self.obj.Proxy.Type == "GDMLGmshTessellated"
                    or self.obj.Proxy.Type == "GDMLTessellated"):
                    self.tess = self.obj.Proxy
                    #self.tess = self.obj
                    self.obj.Proxy.updateParams(vertex, facets, False)
        # print(dir(self.form))
        print("Vertex : " + str(len(vertex)))
        print("Facets : " + str(len(facets)))
        # Update Info of GDML Tessellated Object
        self.tess = None
        if hasattr(self.obj, "tessellated"):
            if self.obj.tessellated is not None:
                self.tess = self.obj.tessellated
                #print("Tessellated Name " + self.tess.Name)
                #print("Update parms : " + self.tess.Name)
                print("Tessellated Name " + self.tess.Label)
                print("Update parms : " + self.tess.Label)
                if hasattr(self.tess, "Proxy"):  # If GDML object has Proxy
                    #print(dir(self.tess.Proxy))
                    self.tess.Proxy.updateParams(vertex, facets, False)
                else:
                    self.tess.updateParams(vertex, facets, False)
            # print('Update parms : '+self.tess.Name)
            # self.tess.updateParams(vertex,facets,False)
        self.form.Vertex.value.setText(str(len(vertex)))
        self.form.Facets.value.setText(str(len(facets)))

        if FreeCAD.GuiUp:
            if self.operationType in [1, 2]:
                self.obj.ViewObject.Visibility = False
                if self.tess is not None:
                    ViewProvider(self.tess.ViewObject)
                    self.tess.ViewObject.DisplayMode = "Wireframe"
                    self.tess.recompute()
                    # FreeCAD.ActiveDocument.recompute()
            else:
                #print("Recompute : " + self.obj.Name)
                print("Recompute : " + self.obj.Label)
                self.obj.recompute()
                self.obj.ViewObject.Visibility = True
            print(f"View Fit Gmsh Min")
            FreeCADGui.SendMsgToActiveView("ViewFit")
            FreeCADGui.updateGui()

    def actionMesh(self):
        from .GmshUtils import (
            minMeshObject,
            getVertex,
            getFacets,
            getMeshLen,
            printMeshInfo,
            printMyInfo,
            initialize,
        )
        from .GDMLObjects import GDMLGmshTessellated, GDMLTriangular, \
                setLengthQuantity

        #print("Action Min Gmsh : " + self.obj.Name)
        print("Action Min Gmsh : " + self.obj.Label)
        initialize()
        #print("Object " + self.obj.Name)
        print("Object " + self.obj.Label)
        self.operationType = 1
        obj2Mesh = self.obj
        self.tess = None
        if hasattr(self.obj, 'tessellated'):
            if self.obj.tessellated is not None:
                self.tess = self.obj.tessellated
                self.operationType = 2
        surfaceDev = self.form.surfaceDeviation.value.text()
        angularDev = self.form.angularDeviation.value.text()
        if hasattr(self.obj, "Proxy"):
            print(f"Has proxy {self.obj.Proxy}")
            #print(dir(self.obj.Proxy))
            #print(dir(self.obj))
            # Is this a remesh of GDMLGmshTessellated
            if hasattr(self.obj.Proxy, "Type"):
                if self.obj.Proxy.Type == "GDMLGmshTessellated":
                    if hasattr(self.obj.Proxy, "SourceObj"):
                        print("Has source Object - ReMesh")
                        obj2Mesh = self.obj.Proxy.SourceObj
                    self.operationType = 3    
        if minMeshObject(obj2Mesh, float(surfaceDev), float(angularDev)):
            print("get facets and vertex")
            self.facets = getFacets()
            self.vertex = getVertex()
            if not hasattr(obj2Mesh, "tessellated"):
                #name = "GDMLTessellate_" + self.obj.Name
                name = "GDMLTessellate_" + self.obj.Label
                parent = None
                if hasattr(self.obj, "InList"):
                    if len(self.obj.InList) > 0:
                        parent = self.obj.InList[0]
                        if parent.TypeId != "PartDesign::Body" and \
                                parent is not None:
                           self.tess = parent.newObject(
                                 "Part::FeaturePython", name)
                        else:    
                            self.tess = FreeCAD.ActiveDocument.addObject(
                                "Part::FeaturePython", name)
                    GDMLGmshTessellated( self.tess, self.obj,
                         getMeshLen(self.obj), self.vertex, self.facets,
                        "mm", getSelectedMaterial())
                    self.tess.addProperty(
                        "App::PropertyFloat","surfaceDev","GmshParms", \
                        "Surface Deviation")
                    self.tess.addProperty(
                        "App::PropertyFloat","angularDev","GmshParms", \
                        "Angular Deviation")
                    #setLengthQuantity(self.tess, self.obj.lunit)
                    #setLengthQuantity(self.tess, "mm")
                    # Make Mesh Info Visible
                    self.form.meshInfoGroup.setVisible(True)
                    self.tess.surfaceDev = float(surfaceDev)
                    self.tess.angularDev = float(angularDev)
                    # Indicate that Object has been Tessellated
                    self.obj.addProperty("App::PropertyLinkGlobal","tessellated","Base")
                    self.obj.tessellated = self.tess
            #else:
            #    self.processMesh(self.vertex, self.facets)
            self.processMesh(self.vertex, self.facets)
            print(f"MinMsh Operation {self.operationType}")
            if self.operationType == 3:
                self.obj.surfaceDev = float(surfaceDev)
                self.obj.angularDev = float(angularDev)
            elif self.operationType == 2:
                self.obj.tessellated.surfaceDev = float(surfaceDev)
                self.obj.tessellated.angularDev = float(angularDev)
            elif self.operationType == 1:
                FreeCADGui.Selection.clearSelection()
                FreeCADGui.Selection.addSelection(self.tess)
            

    def leaveEvent(self, event):
        print("Leave Event II")

    def focusOutEvent(self, event):
        print("Out of Focus II")


class AddTessellateTask:
    def __init__(self, Obj):
        self.obj = Obj
        self.tess = None
        self.form = AddTessellateWidget(Obj, "Gmsh")
        self.form.buttonMesh.clicked.connect(self.actionMesh)
        # self.form.buttonload.clicked.connect(self.loadelement)
        # self.form.buttonsave.clicked.connect(self.saveelement)
        # self.form.buttonrefresh.clicked.connect(self.refreshelement)

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Close)

    def isAllowedAlterSelection(self):
        return True

    def isAllowedAlterView(self):
        return True

    def isAllowedAlterDocument(self):
        return True

    def processMesh(self, vertex, facets):
        from .GDMLObjects import ViewProvider

        print("Update Tessellated Object")
        #print(dir(self))
        print("Object Name " + self.obj.Name)
        print("Object Type " + self.obj.TypeId)
        if hasattr(self.obj, "Proxy"):
            print("Proxy")
            print(self.obj.Proxy.Type)
            if (
                self.obj.Proxy.Type == "GDMLGmshTessellated"
                or self.obj.Proxy.Type == "GDMLTessellated"):
                self.tess = self.obj.Proxy
                self.obj.Proxy.updateParams(vertex, facets, False)
        # print(dir(self.form))
        print("Vertex : " + str(len(vertex)))
        print("Facets : " + str(len(facets)))
        # Update Info of GDML Tessellated Object
        if hasattr(self.obj, "tessellated"):
            if self.obj.tessellated is not None:
                self.tess = self.obj.tessellated
                print("Tessellated Name " + self.tess.Name)
                print("Update parms : " + self.tess.Name)
                if hasattr(self.tess, "Proxy"):  # If GDML object has Proxy
                    self.tess.Proxy.updateParams(vertex, facets, False)
                else:
                    self.tess.updateParams(vertex, facets, False)
        self.form.Vertex.value.setText(str(len(vertex)))
        self.form.Facets.value.setText(str(len(facets)))

        if FreeCAD.GuiUp:
            if self.operationType in [1, 2]:
                self.obj.ViewObject.Visibility = False
                ViewProvider(self.tess.ViewObject)
                self.tess.ViewObject.DisplayMode = "Wireframe"
                self.tess.recompute()
                # FreeCAD.ActiveDocument.recompute()
            else:
                print("Recompute : " + self.obj.Name)
                self.obj.recompute()
                self.obj.ViewObject.Visibility = True
            FreeCADGui.SendMsgToActiveView("ViewFit")
            FreeCADGui.updateGui()

    def actionMesh(self):
        from .GmshUtils import (
            initialize,
            meshObject,
            getVertex,
            getFacets,
            getMeshLen,
            printMeshInfo,
            printMyInfo,
        )
        from .GDMLObjects import GDMLGmshTessellated, GDMLTriangular

        print("Action Gmsh : " + self.obj.Name)
        initialize()
        typeDict = {'Triangular': 6, 'Quadrangular': 8, 'Parallelogram': 9}
        print("Object " + self.obj.Label)
        self.operationType = 1
        obj2Mesh = self.obj
        if hasattr(self.obj, 'tessellated'):
            if self.obj.tessellated is not None:
                self.operationType = 2
        if hasattr(self.obj, "Proxy"):
            print(f"Has proxy {self.obj.Proxy}")
            #print(dir(self.obj.Proxy))
            #print(dir(self.obj))
            mshType = self.form.meshType.currentText()
            mshTy = typeDict[mshType]
            mshML = self.form.maxLen.value.text()
            mshCL = self.form.curveLen.value.text()
            mshPL = self.form.pointLen.value.text()
            # Is this a remesh of GDMLGmshTessellated
            if hasattr(self.obj.Proxy, "Type"):
                if self.obj.Proxy.Type == "GDMLGmshTessellated":
                    if hasattr(self.obj.Proxy, "SourceObj"):
                        print("Has source Object - ReMesh")
                        obj2Mesh = self.obj.Proxy.SourceObj
                    self.operationType = 3


        if meshObject(obj2Mesh, 2, int(mshTy), float(mshML), \
            float(mshCL), float(mshPL)):
            print("get facets and vertex")
            self.facets = getFacets()
            self.vertex = getVertex()
            if not hasattr(obj2Mesh, "tessellated"):
                #name = "GDMLTessellate_" + self.obj.Name
                name = "GDMLTessellate_" + self.obj.Label
                parent = None
                if hasattr(self.obj, "InList"):
                    if len(self.obj.InList) > 0:
                        parent = self.obj.InList[0]
                        if parent.TypeId != "PartDesign::Body" and \
                                parent is not None:
                           self.tess = parent.newObject(
                                 "Part::FeaturePython", name)
                        else:
                            self.tess = FreeCAD.ActiveDocument.addObject(
                            "Part::FeaturePython", name)
                    GDMLGmshTessellated( self.tess, self.obj,
                         getMeshLen(self.obj), self.vertex, self.facets,
                        "mm", getSelectedMaterial())
                    self.tess.addProperty(
                        "App::PropertyEnumeration","meshType","GmshParms", \
                            "Mesh Type")
                    self.tess.meshType = ["Triangular", "Quadrangular", \
                            "Parallelograms"]
                    self.tess.meshType = self.tess.meshType.index(mshType)        
                    self.tess.addProperty(
                        "App::PropertyLength","meshMaxLen","GmshParms", \
                        "Mesh Max Len")
                    self.tess.addProperty(
                        "App::PropertyLength","meshCurveLen","GmshParms", \
                        "Curve Len")
                    self.tess.addProperty(
                        "App::PropertyLength","meshPointFromLen","GmshParms", \
                        "Point From  Len")
                    # Make Mesh Info Visible
                    self.form.meshInfoGroup.setVisible(True)
                    self.tess.meshType = mshType
                    self.tess.meshMaxLen = float(mshML)
                    self.tess.meshCurveLen = float(mshCL)
                    self.tess.meshPointFromLen = float(mshPL)
                    # Indicate that Object has been Tessellated
                    self.obj.addProperty("App::PropertyLinkGlobal","tessellated","Base")
                    self.obj.tessellated = self.tess
            print(f"Number of Facets {len(self.facets)}")
            self.processMesh(self.vertex, self.facets)
            print(f"Operation {self.operationType}")
            if self.operationType == 3:
                self.obj.meshType = mshType
                self.obj.meshMaxLen = float(mshML)
                self.obj.meshCurveLen = float(mshCL)
                self.obj.meshPointFromLen = float(mshPL)
            elif self.operationType == 2:
                self.obj.tessellated.meshType = mshType
                self.obj.tessellated.meshMaxLen = float(mshML)
                self.obj.tessellated.meshCurveLen = float(mshCL)
                self.obj.tessellated.meshPointFromLen = float(mshPL)
            elif self.operationType == 1:
                FreeCADGui.Selection.clearSelection()
                FreeCADGui.Selection.addSelection(self.tess)


    def leaveEvent(self, event):
        print("Leave Event II")

    def focusOutEvent(self, event):
        print("Out of Focus II")


class TessellateFeature:
    def Activated(self):
        import MeshPart
        from .GDMLObjects import (
            GDMLTessellated,
            GDMLTriangular,
            ViewProvider,
            ViewProviderExtension,
        )

        for obj in FreeCADGui.Selection.getSelection():
            # if len(obj.InList) == 0: # allowed only for for top level objects
            print("Action Tessellate")
            if hasattr(obj, "Shape"):
                shape = obj.Shape.copy(False)
                #mesh = MeshPart.meshFromShape( Shape=shape, Fineness=2,
                #    SecondOrder=0, Optimize=1, AllowQuad=0,)
                mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.1,
                    AngularDeflection=0.523599, Relative=False)
                print("Points : " + str(mesh.CountPoints))
                # print(mesh.Points)
                print("Facets : " + str(mesh.CountFacets))
                # print(mesh.Facets)
                name = "GDMLTessellate_" + obj.Label
                vol = createPartVol(obj)
                print(obj.Label)
                print(obj.Placement)
                if hasattr(obj, "material"):
                    mat = obj.material
                else:
                    mat = getSelectedMaterial()
                myTess = vol.newObject("Part::FeaturePython", name)
                # GDMLTessellated(myTess,mesh.Topology[0],mesh.Topology[1], \
                GDMLTessellated(
                    myTess, mesh.Topology[0], mesh.Facets, True, "mm", mat
                )
                # Update Part Placment with source Placement
                vol.Placement = obj.Placement
                base = obj.Placement.Base
                print(type(base))
                myTess.Placement.Base = base.multiply(-1.0)
                FreeCAD.ActiveDocument.recompute()
                if FreeCAD.GuiUp:
                    ViewProvider(myTess.ViewObject)
                    obj.ViewObject.Visibility = False
                    myTess.ViewObject.DisplayMode = "Flat Lines"
                    FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_Tessellate",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_TessGroup", "GDML Tessellate Selected Object"
            ),
            "Tessellate_Planar": QtCore.QT_TRANSLATE_NOOP(
                "GDML_PolyGroup", "Tessellate Selected Planar Object"
            ),
        }


class GmshGroup:
    """Group of Gmsh Commands"""

    def GetCommands(self):
        """Tuple of Commands"""
        return ("TessellateGmshCommand", "TessGmshMinCommand")

    def GetResources(self):
        """Set icon, menu and tooltip."""

        return {
            "Pixmap": "GDML_Gmsh_Group",
            "MenuText": QtCore.QT_TRANSLATE_NOOP("Gmsh Group", "Gmsh Group"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "Gmsh Group", " Group of Gmsh Commands"
            ),
        }

    def IsActive(self):
        """Return True when this command should be available."""
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True


class TessGmshMinFeature:
    def Activated(self):

        from .GmshUtils import (
            initialize,
            meshObject,
            getVertex,
            getFacets,
            getMeshLen,
            printMeshInfo,
            printMyInfo,
        )

        from .GDMLObjects import (
            GDMLGmshTessellated,
            GDMLTriangular,
            ViewProvider,
            ViewProviderExtension,
        )

        print("Action Min Gmsh Activated")
        for obj in FreeCADGui.Selection.getSelection():
            # if len(obj.InList) == 0: # allowed only for for top level objects
            print("Action Min Gmsh Tessellate")
            # print(dir(obj))
            #print(obj.Name)
            print(obj.Label)
            if hasattr(obj, "Shape") and obj.TypeId != "App::Part":
                if FreeCADGui.Control.activeDialog() is False:
                    print("Build panel for TO BE Gmeshed")
                    panel = AddMinTessellateTask(obj)
                    if hasattr(obj, "Proxy"):
                        if hasattr(obj.Proxy, "Type"):
                            print(obj.Proxy.Type)
                            if obj.Proxy.Type == "GDMLGmshTessellated":
                                print("Update panel for EXISTING Gmsh Tessellate")
                                panel.form.meshInfoLayout = QtGui.QHBoxLayout()
                                panel.form.meshInfoLayout.addWidget(
                                    oField("Vertex", 6, str(len(obj.Proxy.Vertex)))
                                )  
                                panel.form.meshInfoLayout.addWidget(
                                    oField("Facets", 6, str(len(obj.Proxy.Facets)))
                                )
                    FreeCADGui.Control.showDialog(panel)
                else:
                    print("Already an Active Task")
            return

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_Tess_Gmsh_Min",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_TessGroup", "Gmsh Min & Tessellate"
            ),
            "Tessellate_Gmsh": QtCore.QT_TRANSLATE_NOOP(
                "GDML_TessGroup", "Mesh & Tessellate Selected Planar Object"
            ),
        }


class TessellateGmshFeature:
    def Activated(self):

        from .GmshUtils import (
            initialize,
            meshObject,
            getVertex,
            getFacets,
            getMeshLen,
            printMeshInfo,
            printMyInfo,
        )

        from .GDMLObjects import (
            GDMLGmshTessellated,
            GDMLTriangular,
            ViewProvider,
            ViewProviderExtension,
        )

        print("Action Gmsh Activated")
        for obj in FreeCADGui.Selection.getSelection():
            # if len(obj.InList) == 0: # allowed only for for top level objects
            print("Action Gmsh Tessellate")
            # print(dir(obj))
            print(obj.Name)
            if hasattr(obj, "Shape") and obj.TypeId != "App::Part":
                if FreeCADGui.Control.activeDialog() is False:
                    print("Build panel for TO BE Gmeshed")
                    panel = AddTessellateTask(obj)
                    if hasattr(obj, "Proxy"):
                        print(obj.Proxy.Type)
                        if obj.Proxy.Type == "GDMLGmshTessellated":
                            print("Build panel for EXISTING Gmsh Tessellate")
                            panel.form.meshInfoLayout = QtGui.QHBoxLayout()
                            panel.form.meshInfoLayout.addWidget(
                                oField("Vertex", 6, str(len(obj.Proxy.Vertex)))
                            )
                            panel.form.meshInfoLayout.addWidget(
                                oField("Facets", 6, str(len(obj.Proxy.Facets)))
                            )
                            panel.form.Vlayout.addLayout(
                                panel.form.meshInfoLayout
                            )
                            panel.form.setLayout(panel.form.Vlayout)
                    FreeCADGui.Control.showDialog(panel)
                else:
                    print("Already an Active Task")
            return

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_Tessellate_Gmsh",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_TessGroup", "Gmsh & Tessellate"
            ),
            "Tessellate_Gmsh": QtCore.QT_TRANSLATE_NOOP(
                "GDML_TessGroup", "Mesh & Tessellate Selected Planar Object"
            ),
        }


class Mesh2TessDialog(QtGui.QDialog):
    def __init__(self, selList):
        super(Mesh2TessDialog, self).__init__()
        self.selList = selList
        self.setupUi()
        self.initUI()

    def initUI(self):
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setMouseTracking(True)
        self.show()

    def setupUi(self):
        self.setObjectName("Dialog")
        self.resize(400, 362)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setGeometry(QtCore.QRect(30, 320, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(
            QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok
        )
        self.buttonBox.setObjectName("buttonBox")
        self.textEdit = QtGui.QTextEdit(self)
        self.textEdit.setGeometry(QtCore.QRect(10, 10, 381, 141))
        self.textEdit.setLocale(
            QtCore.QLocale(
                QtCore.QLocale.English, QtCore.QLocale.UnitedKingdom
            )
        )
        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName("textEdit")
        self.verticalLayoutWidget = QtGui.QWidget(self)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(60, 150, 271, 151))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtGui.QGroupBox(self.verticalLayoutWidget)
        self.groupBox.setObjectName("groupBox")
        self.fullDisplayRadioButton = QtGui.QRadioButton(self.groupBox)
        self.fullDisplayRadioButton.setGeometry(QtCore.QRect(10, 30, 105, 22))
        self.fullDisplayRadioButton.setChecked(True)
        self.fullDisplayRadioButton.setObjectName("fullDisplayRadioButton")
        self.samplesRadioButton = QtGui.QRadioButton(self.groupBox)
        self.samplesRadioButton.setGeometry(QtCore.QRect(10, 60, 105, 22))
        self.samplesRadioButton.setObjectName("samplesRadioButton")
        self.horizontalLayoutWidget = QtGui.QWidget(self.groupBox)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(10, 100, 231, 41))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtGui.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.fractionsLabel = QtGui.QLabel(self.horizontalLayoutWidget)
        self.fractionsLabel.setEnabled(False)
        self.fractionsLabel.setObjectName("fractionsLabel")
        self.horizontalLayout.addWidget(self.fractionsLabel)
        self.fractionSpinBox = QtGui.QSpinBox(self.horizontalLayoutWidget)
        self.fractionSpinBox.setEnabled(False)
        self.fractionSpinBox.setSuffix("")
        self.fractionSpinBox.setMaximum(100)
        self.fractionSpinBox.setSingleStep(5)
        self.fractionSpinBox.setObjectName("fractionSpinBox")
        self.horizontalLayout.addWidget(self.fractionSpinBox)
        self.verticalLayout.addWidget(self.groupBox)

        self.retranslateUi()
        self.buttonBox.accepted.connect(self.tessellate)  # type: ignore
        self.buttonBox.rejected.connect(self.onCancel)  # type: ignore
        self.fullDisplayRadioButton.toggled.connect(
            self.fullDisplayRadioButtonToggled
        )

    def fullDisplayRadioButtonToggled(self):
        self.fullDisplayRadioButton.blockSignals(True)

        if self.fullDisplayRadioButton.isChecked():
            self.fractionSpinBox.setEnabled(False)
            self.fractionsLabel.setEnabled(False)
        else:
            self.fractionSpinBox.setEnabled(True)
            self.fractionsLabel.setEnabled(True)

        self.fullDisplayRadioButton.blockSignals(False)

    def tessellate(self):
        from .GDMLObjects import (
            GDMLTessellated,
            GDMLTriangular,
            ViewProvider,
            ViewProviderExtension,
            GDMLSampledTessellated,
        )

        import cProfile, pstats

        solidFlag = self.fullDisplayRadioButton.isChecked()
        sampledFraction = self.fractionSpinBox.value()

        profiler = cProfile.Profile()
        profiler.enable()
        for obj in self.selList:
            # if len(obj.InList) == 0: # allowed only for for top level objects
            print(obj.TypeId)
            if hasattr(obj, "Mesh"):
                # Mesh Object difficult to determine parent
                print("Action Mesh 2 Tessellate")
                print("Points : " + str(obj.Mesh.CountPoints))
                print("Facets : " + str(obj.Mesh.CountFacets))
                # print(obj.Mesh.Topology[0])
                # print(obj.Mesh.Topology[1])
                vol = createPartVol(obj)
                if hasattr(obj, "material"):
                    mat = obj.material
                else:
                    mat = getSelectedMaterial()
                m2t = vol.newObject(
                    "Part::FeaturePython", "GDMLTessellate_Mesh2Tess"
                )
                GDMLSampledTessellated(
                    m2t,
                    obj.Mesh.Topology[0],
                    obj.Mesh.Facets,
                    "mm",
                    mat,
                    solidFlag,
                    sampledFraction,
                )
                if FreeCAD.GuiUp:
                    obj.ViewObject.Visibility = False
                    # print(dir(obj.ViewObject))
                    ViewProvider(m2t.ViewObject)

                FreeCAD.ActiveDocument.recompute()
                FreeCADGui.SendMsgToActiveView("ViewFit")
        profiler.disable()
        stats = pstats.Stats(profiler).sort_stats("cumtime")
        stats.print_stats()

        self.accept()

    def onCancel(self):
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


class Mesh2TessGroup:
    """Group of Gmsh Commands"""

    def GetCommands(self):
        """Tuple of Commands"""
        return ("Mesh2TessCommand", "RecombineCommand")

    def GetResources(self):
        """Set icon, menu and tooltip."""

        return {
            "Pixmap": "Mesh2Tess_Group",
            "MenuText": QtCore.QT_TRANSLATE_NOOP("Mesh 2 Tess Group", "Mesh 2 Tess Group"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "Mesh 2 Tess Group", " Group of Mesh to Tess Commands"
            ),
        }

    def IsActive(self):
        """Return True when this command should be available."""
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True    


class Mesh2TessFeature:
    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        dialog = Mesh2TessDialog(sel)
        dialog.exec_()

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_Mesh2Tess",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_TessGroup", "Mesh 2 Tess"
            ),
            "Mesh2Tess": QtCore.QT_TRANSLATE_NOOP(
                "GDML_TessyGroup", "Create GDML Tessellate from FC Mesh"
            ),
        }


class Tess2MeshFeature:
    def Activated(self):

        from .GDMLObjects import (
            GDMLTessellated,
            GDMLTriangular,
            ViewProvider,
            ViewProviderExtension,
        )

        from .GmshUtils import TessellatedShape2Mesh, Tetrahedron2Mesh

        for obj in FreeCADGui.Selection.getSelection():
            import MeshPart

            print("Action Tessellate 2 Mesh")
            if hasattr(obj, "Proxy"):
                if hasattr(obj.Proxy, "Type"):
                    if obj.Proxy.Type in [
                        "GDMLTessellated",
                        "GDMLSampledTessellated",
                        "GDMLGmshTessellated",
                        "GDMLTetrahedron",
                    ]:
                        parent = None
                        if hasattr(obj, "InList"):
                            if len(obj.InList) > 0:
                                parent = obj.InList[0]
                                mshObj = parent.newObject(
                                    "Mesh::Feature", obj.Name
                                )
                        if parent is None:
                            mshObj = FreeCAD.ActiveDocument.addObject(
                                "Mesh::Feature", obj.Name
                            )
                        if obj.Proxy.Type == "GDMLSampledTessellated":
                            mshObj.Mesh = obj.Proxy.toMesh(obj)
                        else:
                            mshObj.Mesh = MeshPart.meshFromShape(obj.Shape)

                        if FreeCAD.GuiUp:
                            obj.ViewObject.Visibility = False
                            mshObj.ViewObject.DisplayMode = "Wireframe"
                            FreeCAD.ActiveDocument.recompute()
                            FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_Tess2Mesh",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_TessGroup", "Tess2Mesh"
            ),
            "Tess 2 Mesh": QtCore.QT_TRANSLATE_NOOP(
                "GDML_TessGroup", "Create FC Mesh from GDML Tessellate"
            ),
        }


class TetrahedronFeature:
    def Activated(self):

        from .GDMLObjects import GDMLTetrahedron, ViewProvider
        from .GmshUtils import (
            initialize,
            meshObj,
            getTetrahedrons,
            printMeshInfo,
            printMyInfo,
        )

        for obj in FreeCADGui.Selection.getSelection():
            print("Action Tetrahedron")
            initialize()
            if meshObj(obj, 3) is True:
                tetraheds = getTetrahedrons()
                if tetraheds is not None:
                    print("tetraheds : " + str(len(tetraheds)))
                    name = "GDMLTetrahedron_" + obj.Name
                    parent = None
                    if hasattr(obj, "InList"):
                        if len(obj.InList) > 0:
                            parent = obj.InList[0]
                            myTet = parent.newObject(
                                "Part::FeaturePython", name
                            )
                    if parent is None:
                        myTet = FreeCAD.ActiveDocument.addObject(
                            "Part::FeaturePython", name
                        )
                    GDMLTetrahedron(
                        myTet, tetraheds, "mm", getSelectedMaterial()
                    )
                    if FreeCAD.GuiUp:
                        obj.ViewObject.Visibility = False
                        ViewProvider(myTet.ViewObject)
                        myTet.ViewObject.DisplayMode = "Wireframe"
                        FreeCAD.ActiveDocument.recompute()
                        FreeCADGui.SendMsgToActiveView("ViewFit")
                    else:
                        FreeCAD.Console.PrintMessage(
                            "Not able to produce quandrants for this shape"
                        )

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_Tetrahedron",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_TessGroup", "Tetrahedron"
            ),
            "Tetrehedron": QtCore.QT_TRANSLATE_NOOP(
                "GDML_TessGroup", "Create Tetrahedron from FC Shape"
            ),
        }


class CycleFeature:
    def Activated(self):
        def toggle(obj):
            # print ("Toggle "+obj.Label)
            # print (obj.ViewObject.DisplayMode)
            # print (obj.ViewObject.Visibility)
            if obj.ViewObject.Visibility is False:
                try:
                    obj.ViewObject.DisplayMode = "Shaded"
                except:
                    print(obj.Label + " No Shaded")
                obj.ViewObject.Visibility = True
            else:
                if obj.ViewObject.DisplayMode == "Shaded":
                    obj.ViewObject.DisplayMode = "Wireframe"
                else:
                    obj.ViewObject.Visibility = False

        def cycle(obj):
            # print ("Toggle : "+ obj.Label)
            # print (dir(obj))
            # print("TypeId : "+str(obj.TypeId))
            if obj.TypeId == "App::Part":
                for i in obj.OutList:
                    # print(i)
                    # print(dir(i))
                    # print (i.TypeId)
                    if i.TypeId != "App::Origin":
                        cycle(i)
            elif obj.TypeId == "App::Origin":
                return
            # print obj.isDerivedFrom('App::DocumentObjectGroupPython')
            # Is this a genuine group i.e. Volumes
            # Not Parts with Groups i.e. GDMLPolycone
            elif obj.isDerivedFrom("App::DocumentObjectGroupPython"):
                # print "Toggle Group"
                for s in obj.Group:
                    # print s
                    cycle(s)

            # Cycle through display options
            elif hasattr(obj, "ViewObject"):
                toggle(obj)

            if hasattr(obj, "Base") and hasattr(obj, "Tool"):
                print("Boolean")
                cycle(obj.Base)
                cycle(obj.Tool)

        for obj in FreeCADGui.Selection.getSelection():
            # if len(obj.InList) == 0: # allowed only for for top level objects
            cycle(obj)

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_Cycle",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_CycleGroup", "Cycle Group"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDML_CycleGroup", "Cycle Object and all children display"
            ),
        }


def expandFunction(obj, eNum):
    from .importGDML import expandVolume

    print("Expand Function")
    # Get original volume name i.e. loose _ or _nnn
    name = obj.Label[13:]
    if hasattr(obj, "VolRef"):
        volRef = obj.VolRef
    else:
        volRef = name
    if obj.TypeId != "App::Link":
        expandVolume(obj, volRef, eNum, 3)
        obj.Label = name


def recomputeVol(obj):
    if hasattr(obj, "OutList"):
        for o in obj.OutList:
            o.recompute()
        obj.recompute()


class ExpandFeature:
    def Activated(self):

        print("Expand Feature")
        for obj in FreeCADGui.Selection.getSelection():
            # if len(obj.InList) == 0: # allowed only for for top level objects
            #   add check for Part i.e. Volume
            print("Selected")
            print(obj.Label[:13])
            if obj.Label[:13] == "NOT_Expanded_":
                expandFunction(obj, 0)
            if obj.Label[:5] == "Link_":
                if hasattr(obj, "LinkedObject"):
                    if obj.LinkedObject.Label[0:13] == "NOT_Expanded_":
                        expandFunction(obj.LinkedObject, 0)
            recomputeVol(obj)

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_Expand_One",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_Expand_One", "Expand Volume"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDML_Expand_One", "Expand Volume"
            ),
        }


class ExpandMaxFeature:
    def Activated(self):

        for obj in FreeCADGui.Selection.getSelection():
            # if len(obj.InList) == 0: # allowed only for for top level objects
            #  add check for Part i.e. Volume
            print("Selected")
            print(obj.Label[:13])
            if obj.Label[:13] == "NOT_Expanded_":
                expandFunction(obj, -1)
            if obj.Label[:5] == "Link_":
                if hasattr(obj, "LinkedObject"):
                    if obj.LinkedObject.Label[0:13] == "NOT_Expanded_":
                        expandFunction(obj.LinkedObject, -1)
            recomputeVol(obj)

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_Expand_Max",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_Expand_Max", "Max Expand Volume"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDML_Expand_Max", "Max Expand Volume"
            ),
        }


def getWorldVol():
    doc = FreeCAD.ActiveDocument
    if doc is not None:
        # Find world Vol
        for obj in doc.Objects:
            if hasattr(obj, "TypeId"):
                if obj.TypeId == "App::Part":
                    return obj


class ResetWorldFeature:
    def Activated(self):
        print("Reset World Coordinates")
        vol = getWorldVol()
        if vol is not None:
            if hasattr(vol, "OutList"):
                if len(vol.OutList) >= 3:
                    worldObj = vol.OutList[1]
                    # self.BoundingBox(vol, worldObj)
                    bb = self.BoundingBox(vol)
                    x = 2 * max(abs(bb.XMin), abs(bb.XMax))
                    y = 2 * max(abs(bb.YMin), abs(bb.YMax))
                    z = 2 * max(abs(bb.ZMin), abs(bb.ZMax))
                    worldObj.x = 1.30 * x
                    worldObj.y = 1.30 * y
                    worldObj.z = 1.30 * z
                    worldObj.recompute()
                    if FreeCAD.GuiUp:
                        FreeCADGui.SendMsgToActiveView("ViewFit")

    def BoundingBox(self, vol):
        if hasattr(vol, "Shape"):
            return vol.Shape.BoundBox
        elif vol.TypeId == "App::Part" or vol.TypeId == "App::Link":
            placement = vol.Placement
            matrix = placement.Matrix
            calcBox = FreeCAD.BoundBox()
            for obj in vol.OutList:
                bb = self.BoundingBox(obj)
                bbtrans = bb.transformed(matrix)
                calcBox.add(bbtrans)
            return calcBox
        else:
            return FreeCAD.BoundBox()

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_ResetWorld",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_ResetWorld", "Resize World to contain all volumes"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDML_ResetWorld", "Resize World to contain all volumes"
            ),
        }


class CompoundFeature:
    def Activated(self):

        from .GDMLObjects import GDMLcommon
        import ObjectsFem

        def allocateMaterial(doc, analObj, materials, material):
            print("Allocate Material : ", material)
            for n in materials.OutList:
                if n.Label == material:
                    print("Found Material")
                    matObj = ObjectsFem.makeMaterialSolid(doc, material)
                    mat = matObj.Material
                    mat["Name"] = material
                    mat["Density"] = str(n.density) + " kg/m^3"
                    mat["ThermalConductivity"] = str(n.conduct) + " W/m/K"
                    mat["ThermalExpansionCoefficient"] = (
                        str(n.expand) + " m/m/K"
                    )
                    mat["SpecificHeat"] = str(n.specific) + " J/kg/K"
                    # print(mat)
                    # print(mat['Density'])
                    matObj.Material = mat
                    analObj.addObject(matObj)

        def addToList(objList, matList, obj):
            print(obj.Name)
            if hasattr(obj, "Proxy"):
                # print("Has proxy")
                # material_object = ObjectsFem.makeMaterialSolid \
                #                  (doc,obj.Name+"-Material")
                # allocateMaterial(material_object, obj.Material)
                if isinstance(obj.Proxy, GDMLcommon):
                    objList.append(obj)
                    if obj.material not in matList:
                        matList.append(obj.material)

            if obj.TypeId == "App::Part" and hasattr(obj, "OutList"):
                # if hasattr(obj,'OutList') :
                # print("Has OutList + len "+str(len(obj.OutList)))
                for i in obj.OutList:
                    # print('Call add to List '+i.Name)
                    addToList(objList, matList, i)

        def myaddCompound(obj, count):
            # count == 0 World Volume
            print("Add Compound " + obj.Label)
            volList = []
            matList = []
            addToList(volList, matList, obj)
            if count == 0:
                del volList[0]
                del matList[0]
            # DO not delete World Material as it may be repeat
            print("vol List")
            print(volList)
            print("Material List")
            # print(matList)
            doc = FreeCAD.activeDocument()
            analysis_object = ObjectsFem.makeAnalysis(doc, "Analysis")
            materials = FreeCAD.ActiveDocument.Materials
            for m in matList:
                allocateMaterial(doc, analysis_object, materials, m)
            comp = obj.newObject("Part::Compound", "Compound")
            comp.Links = volList
            FreeCAD.ActiveDocument.recompute()

        objs = FreeCADGui.Selection.getSelection()
        # if len(obj.InList) == 0: # allowed only for for top level objects
        print(len(objs))
        if len(objs) > 0:
            obj = objs[0]
            if obj.TypeId == "App::Part":
                myaddCompound(obj, len(obj.InList))

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {
            "Pixmap": "GDML_Compound",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "GDML_Compound", "Add compound to Volume"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "GDML_Compound", "Add a Compound of Volume"
            ),
        }


FreeCADGui.addCommand("CycleCommand", CycleFeature())
FreeCADGui.addCommand("ExpandCommand", ExpandFeature())
FreeCADGui.addCommand("ExpandMaxCommand", ExpandMaxFeature())
FreeCADGui.addCommand("ResetWorldCommand", ResetWorldFeature())
FreeCADGui.addCommand("ColourMapCommand", ColourMapFeature())
FreeCADGui.addCommand("SetMaterialCommand", SetMaterialFeature())
FreeCADGui.addCommand("SetSensDetCommand", SetSensDetFeature())
FreeCADGui.addCommand("SetSkinSurfaceCommand", SetSkinSurfaceFeature())
FreeCADGui.addCommand("SetBorderSurfaceCommand", SetBorderSurfaceFeature())
FreeCADGui.addCommand("BooleanCutCommand", BooleanCutFeature())
FreeCADGui.addCommand(
    "BooleanIntersectionCommand", BooleanIntersectionFeature()
)
FreeCADGui.addCommand("BooleanUnionCommand", BooleanUnionFeature())
FreeCADGui.addCommand("BoxCommand", BoxFeature())
FreeCADGui.addCommand("EllipsoidCommand", EllispoidFeature())
FreeCADGui.addCommand("ElTubeCommand", ElliTubeFeature())
FreeCADGui.addCommand("ConeCommand", ConeFeature())
FreeCADGui.addCommand("SphereCommand", SphereFeature())
FreeCADGui.addCommand("TorusCommand", TorusFeature())
FreeCADGui.addCommand("TrapCommand", TrapFeature())
FreeCADGui.addCommand("TubeCommand", TubeFeature())
FreeCADGui.addCommand("PolyHedraCommand", PolyHedraFeature())
FreeCADGui.addCommand("AddCompound", CompoundFeature())
FreeCADGui.addCommand("TessellateCommand", TessellateFeature())
FreeCADGui.addCommand("GmshGroupCommand", GmshGroup())
FreeCADGui.addCommand("TessellateGmshCommand", TessellateGmshFeature())
FreeCADGui.addCommand("TessGmshMinCommand", TessGmshMinFeature())
FreeCADGui.addCommand("DecimateCommand", DecimateFeature())
FreeCADGui.addCommand("Mesh2TessGroupCommand", Mesh2TessGroup())
#FreeCADGui.addCommand("RecombineCommand", RecombineFeature())
FreeCADGui.addCommand("Mesh2TessCommand", Mesh2TessFeature())
FreeCADGui.addCommand("Tess2MeshCommand", Tess2MeshFeature())
FreeCADGui.addCommand("TetrahedronCommand", TetrahedronFeature())
FreeCADGui.addCommand("SetScaleCommand", SetScaleFeature())
