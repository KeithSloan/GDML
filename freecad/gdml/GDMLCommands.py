# **************************************************************************
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

'''
This Script includes the GUI Commands of the GDML module
'''

import FreeCAD, FreeCADGui
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
        importButton = QtGui.QPushButton('Import')
        importButton.clicked.connect(self.onImport)
        scanButton = QtGui.QPushButton('Scan Vol')
        scanButton .clicked.connect(self.onScan)
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


def getSelectedMaterial():
    from .exportGDML import nameFromLabel
    from .GDMLObjects import GDMLmaterial

    list = FreeCADGui.Selection.getSelection()
    if list is not None:
        for obj in list:
            if hasattr(obj, 'Proxy'):
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
            if hasattr(obj, 'Proxy'):
                if isinstance(obj.Proxy, GDMLmaterial) is True and \
                   material == 0:
                    material = nameFromLabel(obj.Label)

            if obj.TypeId == 'App::Part' and objPart is None:
                objPart = obj

            if objPart is not None and material != 0:
                return objPart, material

    return objPart, material


def createPartVol(obj):
    # Create Part(GDML Vol) Shared with a number of Features
    LVname = 'LV-'+obj.Label
    if hasattr(obj, 'InList'):
        if len(obj.InList) > 0:
            parent = obj.InList[0]
            vol = parent.newObject("App::Part", LVname)
        else:
            vol = FreeCAD.ActiveDocument.addObject("App::Part", LVname)
        return vol
    return None


class ColourMapFeature:

    def Activated(self):
        from PySide import QtGui, QtCore
        # import sys
        from .GDMLColourMap import resetGDMLColourMap, showGDMLColourMap

        print('Add colour Map')
        resetGDMLColourMap()
        showGDMLColourMap()
        return

        # myWidget = QtGui.QDockWidget()
        # mainWin = FreeCADGui.getMainWindow()
        # mainWin.addDockWidget(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.TopDockWidgetArea, \
        mainWin.addDockWidget(QtCore.Qt.LeftDockWidgetArea or QtCore.Qt.TopDockWidgetArea, \
                              myWidget)
        # mainWin.addDockWidget(Qt::LeftDockWidgetArea or Qt::TopDockWidgetArea, myWidget)
        # myWidget.setObjectName("ColourMap")
        # myWidget.resize(QtCore.QSize(300,100))
        # title = QtGui.QLabel("Colour Mapping to GDML Materials")
        # title.setIndent(100)
        # myWidget.setTitleBarWidget(title)
        # label = QtGui.QLabel("Colour Mapping to GDML Materials",myWidget)

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {'Pixmap': 'GDMLColourMapFeature', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDMLColourMapFeature',
                                         'Add Colour Map'), 'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('GDMLColourMapFeature',
                                         'Add Colour Map')}


class GDMLSetMaterial(QtGui.QDialog):
    def __init__(self, selList):
        super(GDMLSetMaterial, self).__init__()
        self.SelList = selList
        self.initUI()

    def initUI(self):
        from .GDMLMaterials import GDMLMaterial, newGetGroupedMaterials
        print('initUI')
        self.setGeometry(150, 150, 250, 250)
        self.setWindowTitle("Set GDML Material")
        self.setMouseTracking(True)
        self.buttonSet = QtGui.QPushButton(translate('GDML', 'Set Material'))
        self.buttonSet.clicked.connect(self.onSet)
        self.groupedMaterials = newGetGroupedMaterials()  # this build, then returns all materials
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
        print(len(self.matList))
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
        if hasattr(obj, 'material'):
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
        from .GDMLObjects import GroupedMaterials
        self.materialComboBox.blockSignals(True)
        self.materialComboBox.clear()
        group = self.groupsCombo.currentText()
        self.materialComboBox.addItems(GroupedMaterials[group])
        self.materialComboBox.blockSignals(False)

    def materialChanged(self, text):
        self.lineedit.setText(text)

    def onSet(self):
        # mat = self.materialComboBox.currentText()
        mat = self.lineedit.text()
        if mat not in self.matList:
            print(f'Material {mat} not defined')
            return

        print(f'Set Material {mat}')
        for sel in self.SelList:
            obj = sel.Object
            if hasattr(obj, 'material'):
                obj.material = mat
            else:
                obj.addProperty("App::PropertyEnumeration", "material",
                                "GDML", "Material")
                obj.material = self.matList
                obj.material = self.matList.index(mat)


class SetMaterialFeature:

    def Activated(self):
        from PySide import QtGui, QtCore

        print('Add SetMaterial')
        cnt = 0
        sel = FreeCADGui.Selection.getSelectionEx()
        # print(sel)
        set = []
        for s in sel:
            # print(s)
            # print(dir(s))
            if hasattr(s.Object, 'Shape'):
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
        return {'Pixmap': 'GDML_SetMaterial', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDML_SetMaterial',
                                         'Set Material'), 'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('GDML_SetMaterial',
                                         'Set Material')}


class BooleanCutFeature:

    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):

        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) == 2:
            print(sel)
            selObj = 'Gui::SelectionObject'
            if sel[0].TypeId == selObj and sel[1].TypeId == selObj:
                if sel[0].Object.TypeId == 'App::Part' and \
                   sel[1].Object.TypeId == 'App::Part':
                    print('Boolean Cut')
                    if len(sel[0].Object.InList) > 0:
                        parent = sel[0].Object.InList[0]
                        print('Parent : '+parent.Label)
                        baseVol = sel[0].Object
                        print('Base Vol : '+baseVol.Label)
                        toolVol = sel[1].Object
                        print('Tool Vol : '+toolVol.Label)
                        print(sel[0].Object.OutList)
                        base = sel[0].Object.OutList[-1]
                        print('Base : '+base.Label)
                        tool = sel[1].Object.OutList[-1]
                        print('Tool : '+tool.Label)
                        print('Remove Base')
                        baseVol.removeObject(base)
                        print('Adjust Base Links')
                        base.adjustRelativeLinks(baseVol)
                        toolVol.removeObject(tool)
                        tool.adjustRelativeLinks(toolVol)
                        boolVol = parent.newObject('App::Part', 'Bool-Cut')
                        boolVol.addObject(base)
                        boolVol.addObject(tool)
                        boolObj = boolVol.newObject('Part::Cut', 'Cut')
                        boolObj.Placement = sel[0].Object.Placement
                        boolObj.Base = base
                        boolObj.Tool = tool
                        boolObj.Tool.Placement.Base = sel[1].Object.Placement.Base \
                            - sel[0].Object.Placement.Base
                        boolObj.Tool.setEditorMode('Placement', 0)
                        print('Remove Base Vol')
                        FreeCAD.ActiveDocument.removeObject(baseVol.Label)
                        FreeCAD.ActiveDocument.removeObject(toolVol.Label)
                        boolObj.recompute()
                else:
                    print('No Parent Volume/Part')

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {'Pixmap': 'GDML_Cut', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('gdmlBooleanFeature',
                                         'GDML Cut'), 'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('gdmlBooleanFeature',
                                         'GDML Cut')}


class BooleanIntersectionFeature:

    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        import Part

        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) == 2:
            print(sel)
            selObj = 'Gui::SelectionObject'
            if sel[0].TypeId == selObj and sel[1].TypeId == selObj:
                if sel[0].Object.TypeId == 'App::Part' and \
                   sel[1].Object.TypeId == 'App::Part' :
                    print('Boolean Intersection')
                    if len(sel[0].Object.InList) > 0:
                        parent = sel[0].Object.InList[0]
                        print('Parent : '+parent.Label)
                        baseVol = sel[0].Object
                        print('Base Vol : '+baseVol.Label)
                        toolVol = sel[1].Object
                        print('Tool Vol : '+toolVol.Label)
                        baseVol = sel[0].Object
                        print(sel[0].Object.OutList)
                        base = sel[0].Object.OutList[-1]
                        print('Base : '+base.Label)
                        tool = sel[1].Object.OutList[-1]
                        print('Tool : '+tool.Label)
                        print('Remove Base')
                        baseVol.removeObject(base)
                        print('Adjust Base Links')
                        base.adjustRelativeLinks(baseVol)
                        toolVol.removeObject(tool)
                        tool.adjustRelativeLinks(toolVol)
                        boolVol = parent.newObject('App::Part', 'Bool-Intersection')
                        boolVol.addObject(base)
                        boolVol.addObject(tool)
                        boolObj = boolVol.newObject('Part::Common', 'Common')
                        boolObj.Placement = sel[0].Object.Placement
                        boolObj.Base = base
                        boolObj.Tool = tool
                        boolObj.Tool.Placement.Base = sel[1].Object.Placement.Base \
                            - sel[0].Object.Placement.Base
                        boolObj.Tool.setEditorMode('Placement', 0)
                        FreeCAD.ActiveDocument.removeObject(baseVol.Label)
                        FreeCAD.ActiveDocument.removeObject(toolVol.Label)
                        boolObj.recompute()
                    else:
                        print('No Parent Volume/Part')

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {'Pixmap': 'GDML_Intersection', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('gdmlBooleanFeature',
                                         'GDML Intersection'), 'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('gdmlBooleanFeature',
                                         'GDML Intersection')}


class BooleanUnionFeature:

    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        import Part

        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) == 2:
            print(sel)
            selObj = 'Gui::SelectionObject'
            if sel[0].TypeId == selObj and sel[1].TypeId == selObj:
                if sel[0].Object.TypeId == 'App::Part' and \
                   sel[1].Object.TypeId == 'App::Part':
                    print('Boolean Union')
                    if len(sel[0].Object.InList) > 0:
                        print(sel[0].Object.InList)
                        parent = sel[0].Object.InList[0]
                        print('Parent : '+parent.Label)
                        baseVol = sel[0].Object
                        print('Base Vol : '+baseVol.Label)
                        toolVol = sel[1].Object
                        print('Tool Vol : '+toolVol.Label)
                        baseVol = sel[0].Object
                        print(f'Base OutList {sel[0].Object.OutList}')
                        for o in sel[0].Object.OutList:
                            print(o.Label)
                        print(f'Tool OutList {sel[1].Object.OutList}')
                        for o in sel[1].Object.OutList:
                            print(o.Label)
                        print(f'True Base {sel[0].Object.OutList[-1].Label}')
                        base = sel[0].Object.OutList[-1]
                        print('Base : '+base.Label)
                        print(f'True Tool {sel[1].Object.OutList[-1].Label}')
                        tool = sel[1].Object.OutList[-1]
                        print('Tool : '+tool.Label)
                        print('Remove Base')
                        baseVol.removeObject(base)
                        print('Adjust Base Links')
                        base.adjustRelativeLinks(baseVol)
                        toolVol.removeObject(tool)
                        tool.adjustRelativeLinks(toolVol)
                        boolVol = parent.newObject('App::Part', 'Bool-Union')
                        boolVol.addObject(base)
                        boolVol.addObject(tool)
                        boolObj = boolVol.newObject('Part::Fuse', 'Union')
                        boolObj.Placement = sel[0].Object.Placement
                        boolObj.Base = base
                        boolObj.Tool = tool
                        boolObj.Tool.Placement.Base = sel[1].Object.Placement.Base \
                            - sel[0].Object.Placement.Base
                        boolObj.Tool.setEditorMode('Placement', 0)
                        FreeCAD.ActiveDocument.removeObject(baseVol.Label)
                        FreeCAD.ActiveDocument.removeObject(toolVol.Label)
                        boolObj.recompute()
                    else:
                        print('No Parent Volume')

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {'Pixmap': 'GDML_Union', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('gdmlBooleanFeature',
                                         'GDML Union'), 'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('gdmlBooleanFeature',
                                         'GDML Union')}


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
        return {'Pixmap': 'GDMLBoxFeature', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDMLBoxFeature',
                                         'Box Object'), 'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('GDMLBoxFeature',
                                         'Box Object')}


class ConeFeature:
    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLCone, ViewProvider
        objPart, material = getSelectedPM()
        if objPart is None:
            vol = FreeCAD.ActiveDocument.addObject("App::Part", "LV-Cone")
        else:
            vol = objPart.newObject("App::Part", "LV-Cone")
        obj = vol.newObject("Part::FeaturePython", "GDMLCone_Cone")
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
        return {'Pixmap': 'GDMLConeFeature', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDMLConeFeature',
                                         'Cone Object'), 'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('GDMLConeFeature',
                                         'Cone Object')}


class EllispoidFeature:
    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLEllipsoid, ViewProvider
        objPart, material = getSelectedPM()
        if objPart is None:
            vol = FreeCAD.ActiveDocument.addObject("App::Part", "LV-Ellipsoid")
        else:
            vol = objPart.newObject("App::Part", "LV-Ellipsoid")
        obj = vol.newObject("Part::FeaturePython", "GDMLEllipsoid_Ellipsoid")
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
        return {'Pixmap': 'GDMLEllipsoidFeature', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDMLEllipsoidFeature',
                                         'Ellipsoid Object'), 'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('GDMLEllipsoidFeature',
                                         'Ellipsoid Object')}


class ElliTubeFeature:
    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLElTube, ViewProvider
        objPart, material = getSelectedPM()
        if objPart is None:
           vol = FreeCAD.ActiveDocument.addObject("App::Part", "LV-EllipticalTube")
        else:
            vol = objPart.newObject("App::Part", "LV-EllipticalTube")
        obj = vol.newObject("Part::FeaturePython", "GDMLElTube_Eltube")
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
        return {'Pixmap': 'GDMLElTubeFeature', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDMLElTubeFeature',
                                         'ElTube Object'), 'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('GDMLElTubeFeature',
                                         'ElTube Object')}


class SphereFeature:
    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLSphere, ViewProvider
        objPart, material = getSelectedPM()
        # print(objPart)
        # print(material)
        if objPart is None:
            vol = FreeCAD.ActiveDocument.addObject("App::Part", "LV-Sphere")
        else:
            vol = objPart.newObject("App::Part", "LV-Sphere")
        obj = vol.newObject("Part::FeaturePython", "GDMLSphere_Sphere")
        # print("GDMLSphere Object - added")
        # obj, rmin, rmax, startphi, deltaphi, starttheta, deltatheta,
        #       aunit, lunits, material
        GDMLSphere(obj, 10.0, 20.0, 0.0, 2.02, 0.0, 2.02, "rad", "mm", material)
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
        return {'Pixmap': 'GDMLSphereFeature', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDMLSphereFeature',
                                         'Sphere Object'), 'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('GDMLSphereFeature',
                                         'Sphere Object')}


class TorusFeature:
    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLTorus, ViewProvider
        objPart, material = getSelectedPM()
        if objPart is None:
            vol = FreeCAD.ActiveDocument.addObject("App::Part", "LV-Torus")
        else:
            vol = objPart.newObject("App::Part", "LV-Torus")
        myTorus = vol.newObject("Part::FeaturePython", "GDMLTorus_Torus")
        GDMLTorus(myTorus, 10, 50, 50, 10, 360, "deg", "mm", material)
        if FreeCAD.GuiUp:
            myTorus.ViewObject.Visibility = True
            ViewProvider(myTorus.ViewObject)

            FreeCAD.ActiveDocument.recompute()
            FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {'Pixmap': 'GDMLTorusFeature', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDMLTorusFeature',
                                         'Torus Object'), 'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('GDMLTorusFeature',
                                         'Torus Object')}


class TrapFeature:
    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLTrap, ViewProvider
        objPart, material = getSelectedPM()
        if objPart is None:
            vol = FreeCAD.ActiveDocument.addObject("App::Part", "LV-Trap")
        else:
            vol = objPart.newObject("App::Part", "LV-Trap")
        obj = vol.newObject("Part::FeaturePython", "GDMLTrap_Trap")
        print("GDMLTrap Object - added")
        # obj z, theta, phi, x1, x2, x3, x4, y1, y2,
        # pAlp2, aunits, lunits, material
        GDMLTrap(obj, 10.0, 0.0, 0.0, 6.0, 6.0, 6.0, 6.0, 7.0, 7.0, 0.0,
                 "rad", "mm", material)
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
        return {'Pixmap': 'GDMLTrapFeature', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDMLTrapFeature',
                                         'Trap Object'), 'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('GDMLTrapFeature',
                                         'Trap Object')}


class TubeFeature:
    # def IsActive(self):
    #    return FreeCADGui.Selection.countObjectsOfType('Part::Feature') > 0

    def Activated(self):
        from .GDMLObjects import GDMLTube, ViewProvider
        objPart, material = getSelectedPM()
        if objPart is None:
            vol = FreeCAD.ActiveDocument.addObject("App::Part", "LV-Tube")
        else:
            vol = objPart.newObject("App::Part", "LV-Tube")
        obj = vol.newObject("Part::FeaturePython", "GDMLTube_Tube")
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
        return {'Pixmap': 'GDMLTubeFeature', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDMLTubeFeature',
                                         'Tube Object'), 'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('GDMLTubeFeature',
                                         'Tube Object')}


class PolyHedraFeature:

    def Activated(self):

        for obj in FreeCADGui.Selection.getSelection():
            # if len(obj.InList) == 0: # allowed only for for top level objects
            print('Action Poly')
            if hasattr(obj, 'Shape'):
                print(obj.Shape.ShapeType)
                if hasattr(obj.Shape, 'Vertexes'):
                    numVert = len(obj.Shape.Vertexes)
                    print('Number of Vertex : '+str(numVert))
                    print(obj.Shape.Vertexes)
                if hasattr(obj.Shape, 'Faces'):
                    print('Faces')
                    # print(dir(obj.Shape.Faces[0]))
                    print(obj.Shape.Faces)
                    planar = self.checkPlanar(obj.Shape.Faces)
                    print(planar)
                if hasattr(obj.Shape, 'Edges'):
                    print('Edges')
                    # print(dir(obj.Shape.Edges[0]))
                    print(obj.Shape.Edges)

    def checkPlanar(self, faces):
        import Part
        print('Check Planar')
        for f in faces:
            if not isinstance(f.Surface, Part.Plane):
                return False
        return True

    def GetResources(self):
        return {'Pixmap': 'GDML_Polyhedra', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDML_PolyGroup',
                                         'Poly Group'), 'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('GDML_PolyGroup',
                                         'PolyHedra Selected Object')}


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
        return(QtCore.QSize(10, 5))


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
        self.type.addItems(['sp4cerat'])
        self.group1 = QtGui.QGroupBox('Decimate Reduction')
        self.tolerance = iField('Tolerance', 5, '5.0')
        self.reduction = iField('Reduction', 5, '0.8')
        self.parms1layout = QtGui.QHBoxLayout()
        self.parms1layout.addWidget(self.tolerance)
        self.parms1layout.addWidget(self.reduction)
        self.grpLay1 = QtGui.QVBoxLayout()
        self.grpLay1.addLayout(self.parms1layout)
        self.buttonReduction = QtGui.QPushButton(translate('GDML', 'Decimate Reduction'))
        self.grpLay1.addWidget(self.buttonReduction)
        self.group1.setLayout(self.grpLay1)
        self.group2 = QtGui.QGroupBox('Decimate to Size')
        self.targetSize = iField('Target Size', 5, '100')
        self.grpLay2 = QtGui.QVBoxLayout()
        self.grpLay2.addWidget(self.targetSize)
        self.buttonToSize = QtGui.QPushButton(translate('GDML', 'Decimate To Size'))
        self.grpLay2.addWidget(self.buttonToSize)
        self.group2.setLayout(self.grpLay2)
        self.Vlayout = QtGui.QVBoxLayout()
        self.Vlayout.addWidget(self.type)
        self.Vlayout.addWidget(self.group1)
        self.Vlayout.addWidget(self.group2)
        self.setLayout(self.Vlayout)
        self.setWindowTitle(translate('GDML', 'Decimate'))

    def leaveEvent(self, event):
        print('Leave Event')
        QtCore.QTimer.singleShot(0, lambda: FreeCADGui.Control.closeDialog())

    def retranslateUi(self, widget=None):
        self.buttonMesh.setText(translate('GDML', 'Decimate'))
        self.setWindowTitle(translate('GDML', 'Decimate'))


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

        print('Action Decimate Reduction : '+self.obj.Name)
        # print(dir(self))
        if hasattr(self.obj, 'Mesh'):
            mesh = self.obj.Mesh
        else:
            mesh = TessellatedShape2Mesh(self.obj)
        try:
            tolerance = float(self.form.tolerance.value.text())
            reduction = float(self.form.reduction.value.text())
            print('Tolerance : '+str(tolerance))
            print('Reduction : '+str(reduction))
            mesh.decimate(tolerance, reduction)

        except Exception as e:
            print(e)

        # print(dir(self.obj))
        self.obj.Proxy.updateParams(mesh.Topology[0], mesh.Topology[1], False)
        self.obj.recompute()
        self.obj.ViewObject.Visibility = True
        FreeCADGui.SendMsgToActiveView("ViewFit")
        print('Update Gui')
        FreeCADGui.updateGui()

    def actionToSize(self):
        from .GmshUtils import TessellatedShape2Mesh

        print('Action Decimate To Size : '+self.obj.Name)
        print(dir(self))
        if hasattr(self.obj, 'Mesh'):
            mesh = self.obj.Mesh
        else:
            mesh = TessellatedShape2Mesh(self.obj)

        try:
            targetSize = int(self.form.targetSize.value.text())
            print('Target Size : '+str(targetSize))
            mesh.decimate(targetSize)

        except:
            print('Invalid Float Values')

    def leaveEvent(self, event):
        print('Leave Event II')

    def focusOutEvent(self, event):
        print('Out of Focus II')


class DecimateFeature:

    def Activated(self):
        from .GDMLObjects import GDMLTessellated, GDMLTriangular, \
                  ViewProvider, ViewProviderExtension

        for obj in FreeCADGui.Selection.getSelection():
            # if len(obj.InList) == 0: # allowed only for for top level objects
            print('Action Decimate')
            if self.isDecimatable(obj):
                if FreeCADGui.Control.activeDialog() is False:
                    print('Build panel for Decimate')
                    panel = AddDecimateTask(obj)
                    FreeCADGui.Control.showDialog(panel)
                else:
                    print('Already an Active Task')
            return

    def GetResources(self):
        return {'Pixmap': 'GDML_Decimate', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDML_TessGroup',
                                         'Decimate Selected Object'), 'Decimate':
                QtCore.QT_TRANSLATE_NOOP('GDML_TessGroup',
                                         'Decimate Selected  Object')}

    def isDecimatable(self, obj):
        if hasattr(obj, 'Proxy'):
            print(obj.Proxy.Type)
            if obj.Proxy.Type == 'GDMLGmshTessellated' or \
               obj.Proxy.Type == 'GDMLTessellated':
                return True
        if hasattr(obj, 'Mesh'):
            return True
        return False


class AddTessellateWidget(QtGui.QWidget):
    def __init__(self, Shape, *args):
        QtGui.QWidget.__init__(self, *args)
        bboxGroup  = QtGui.QGroupBox('Objects Bounding Box')
        laybbox = QtGui.QHBoxLayout()
        laybbox.addWidget(QtGui.QLabel('Width : '+str(Shape.BoundBox.XLength)))
        laybbox.addWidget(QtGui.QLabel('Height : '+str(Shape.BoundBox.YLength)))
        laybbox.addWidget(QtGui.QLabel('Depth : '+str(Shape.BoundBox.ZLength)))
        bboxGroup.setLayout(laybbox)
        maxl = int((Shape.BoundBox.XLength + Shape.BoundBox.YLength +
                    Shape.BoundBox.ZLength) / 15)
        self.type = QtGui.QComboBox()
        self.type.addItems(['Triangular', 'Quadrangular', 'Parallelograms'])
        self.group = QtGui.QGroupBox('Mesh Characteristics')
        self.maxLen = iField('Max Length', 5, str(maxl))
        self.curveLen = iField('Curve Length', 5, '10')
        self.pointLen = iField('Length from Point', 5, '10')
        self.Vertex = oField('Vertex', 6, '')
        self.Facets = oField('Facets', 6, '')
        self.meshParmsLayout = QtGui.QGridLayout()
        self.meshParmsLayout.addWidget(self.type, 0, 0)
        self.meshParmsLayout.addWidget(self.maxLen, 0, 1)
        self.meshParmsLayout.addWidget(self.curveLen, 1, 0)
        self.meshParmsLayout.addWidget(self.pointLen, 1, 1)
        self.group.setLayout(self.meshParmsLayout)
        self.buttonMesh = QtGui.QPushButton(translate('GDML', 'Mesh'))
        layoutAction = QtGui.QHBoxLayout()
        layoutAction.addWidget(self.buttonMesh)
        self.Vlayout = QtGui.QVBoxLayout()
        self.Vlayout.addWidget(bboxGroup)
        self.Vlayout.addWidget(self.group)
        self.Vlayout.addLayout(layoutAction)
        self.setLayout(self.Vlayout)
        self.setWindowTitle(translate('GDML', 'Tessellate with Gmsh'))

    def leaveEvent(self, event):
        print('Leave Event')
        # FreeCADGui.Control.closeDialog()
        # closeDialog()
        # QtCore.QMetaObject.invokeMethod(FreeCADGui.Control, 'closeDialog', QtCore.Qt.QueuedConnection)
        # QtCore.QTimer.singleShot(0, FreeCADGui.Control, SLOT('closeDialog()'))
        # QtCore.QTimer.singleShot(0, FreeCADGui.Control, QtCore.SLOT('closeDialog()'))
        QtCore.QTimer.singleShot(0, lambda: FreeCADGui.Control.closeDialog())

    def retranslateUi(self, widget=None):
        self.buttonMesh.setText(translate('GDML', 'Mesh'))
        self.setWindowTitle(translate('GDML', 'Tessellate with Gmsh'))


class AddTessellateTask:

    def __init__(self, Obj):
        self.obj = Obj
        self.tess = None
        self.form = AddTessellateWidget(Obj.Shape)
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

        print('Update Tessellated Object')
        print(dir(self))
        print('Object Name ' + self.obj.Name)
        print('Object Type ' + self.obj.TypeId)
        if hasattr(self.obj, 'Proxy'):
            print('Proxy')
            print(self.obj.Proxy.Type)
            if self.obj.Proxy.Type == 'GDMLGmshTessellated' or \
               self.obj.Proxy.Type == 'GDMLTessellated':
                self.obj.Proxy.updateParams(vertex, facets, False)
        # print(dir(self.form))
        print('Vertex : '+str(len(vertex)))
        print('Facets : '+str(len(facets)))
        # Update Info of GDML Tessellated Object
        if self.tess is not None:
            print('Tesselated Name '+self.tess.Name)
            print('Update parms : '+self.tess.Name)
            if hasattr(self.tess, 'Proxy'):  # If GDML object has Proxy
                print(dir(self.tess.Proxy))
                self.tess.Proxy.updateParams(vertex, facets, False)
            else:
                self.tess.updateParams(vertex, facets, False)
            # print('Update parms : '+self.tess.Name)
            # self.tess.updateParams(vertex,facets,False)
        # self.form.Vertex.value.setText(QtCore.QString(len(vertex)))
        self.form.Vertex.value.setText(str(len(vertex)))
        # self.form.Facets.value.setText(QtCore.QString(len(facets)))
        self.form.Facets.value.setText(str(len(facets)))

        if FreeCAD.GuiUp:
            if self.tess is not None:
                self.obj.ViewObject.Visibility = False
                ViewProvider(self.tess.ViewObject)
                self.tess.ViewObject.DisplayMode = "Wireframe"
                self.tess.recompute()
                # FreeCAD.ActiveDocument.recompute()
            else:
                print('Recompute : '+self.obj.Name)
                self.obj.recompute()
                self.obj.ViewObject.Visibility = True
            FreeCADGui.SendMsgToActiveView("ViewFit")
            FreeCADGui.updateGui()

    def actionMesh(self):
        from .GmshUtils import initialize, meshObject, \
          getVertex, getFacets, getMeshLen, printMeshInfo, printMyInfo
        from .GDMLObjects import GDMLGmshTessellated, GDMLTriangular
        print('Action Gmsh : '+self.obj.Name)
        initialize()
        typeDict = {0: 6, 1: 8, 2: 9}
        print(dir(self))
        print('Object '+self.obj.Name)
        if self.tess is not None:
            print('Tessellated '+self.tess.Name)
        ty = typeDict[self.form.type.currentIndex()]
        ml = self.form.maxLen.value.text()
        cl = self.form.curveLen.value.text()
        pl = self.form.pointLen.value.text()
        print('type :  '+str(ty)+' ml : '+ml+' cl : '+cl+' pl : '+pl)
        if hasattr(self.obj, 'Proxy'):
            print('has proxy')
            if hasattr(self.obj.Proxy, 'SourceObj'):
                print('Has source Object')
                if meshObject(self.obj.Proxy.SourceObj, 2, ty,
                              float(ml), float(cl), float(pl)) is True:
                    facets = getFacets()
                    vertex = getVertex()
                    self.processMesh(vertex, facets)
                    return

        if meshObject(self.obj, 2, ty,
                      float(ml), float(cl), float(pl)) is True:
            facets = getFacets()
            vertex = getVertex()
            if self.tess is None:
                name = 'GDMLTessellate_'+self.obj.Name
                parent = None
                if hasattr(self.obj, 'InList'):
                    if len(self.obj.InList) > 0:
                        parent = self.obj.InList[0]
                        self.tess = parent.newObject('Part::FeaturePython', name)
                    if parent is None:
                        self.tess = FreeCAD.ActiveDocument.addObject(
                            'Part::FeaturePython', name)
                    GDMLGmshTessellated(self.tess, self.obj,
                                        getMeshLen(self.obj), vertex, facets,
                                        "mm", getSelectedMaterial())
            else:
                self.processMesh(vertex, facets)

        print('Check Form')
        # print(dir(self.form))
        if not hasattr(self.form, 'infoGroup'):
            self.form.infoGroup = QtGui.QGroupBox('Mesh Information')
            print('Mesh Info Layout')
            layMeshInfo = QtGui.QHBoxLayout()
            layMeshInfo.addWidget(self.form.Vertex)
            layMeshInfo.addWidget(self.form.Facets)
            # layMeshInfo.addWidget(self.form.Nodes)
            self.form.infoGroup.setLayout(layMeshInfo)
            self.form.Vlayout.addWidget(self.form.infoGroup)
            # self.form.setLayout(self.form.Vlayout)
            self.processMesh(vertex, facets)

    def leaveEvent(self, event):
        print('Leave Event II')

    def focusOutEvent(self, event):
        print('Out of Focus II')


class TessellateFeature:

    def Activated(self):
        import MeshPart
        from .GDMLObjects import GDMLTessellated, GDMLTriangular, \
                  ViewProvider, ViewProviderExtension

        for obj in FreeCADGui.Selection.getSelection():
            # if len(obj.InList) == 0: # allowed only for for top level objects
            print('Action Tessellate')
            if hasattr(obj, 'Shape'):
                shape = obj.Shape.copy(False)
                mesh = MeshPart.meshFromShape(Shape=shape, Fineness=2,
                                              SecondOrder=0, Optimize=1,
                                              AllowQuad=0)
                print('Points : '+str(mesh.CountPoints))
                # print(mesh.Points)
                print('Facets : '+str(mesh.CountFacets))
                # print(mesh.Facets)
                name = 'GDMLTessellate_'+obj.Label
                vol = createPartVol(obj)
                print(obj.Label)
                print(obj.Placement)
                if hasattr(obj, 'material'):
                    mat = obj.material
                else:
                    mat = getSelectedMaterial()
                myTess = vol.newObject('Part::FeaturePython', name)
                # GDMLTessellated(myTess,mesh.Topology[0],mesh.Topology[1], \
                GDMLTessellated(myTess, mesh.Topology[0], mesh.Facets, True,
                                "mm", mat)
                # Update Part Placment with source Placement
                vol.Placement = obj.Placement
                base = obj.Placement.Base
                print(type(base))
                myTess.Placement.Base = base.multiply(-1.0)
                FreeCAD.ActiveDocument.recompute()
                if FreeCAD.GuiUp:
                    ViewProvider(myTess.ViewObject)
                    obj.ViewObject.Visibility = False
                    myTess.ViewObject.DisplayMode = 'Flat Lines'
                    FreeCADGui.SendMsgToActiveView("ViewFit")

    def GetResources(self):
        return {'Pixmap': 'GDML_Tessellate',
                'MenuText': QtCore.QT_TRANSLATE_NOOP('GDML_TessGroup',
                                                     'GDML Tessellate Selected Object'),
                'Tessellate_Planar': QtCore.QT_TRANSLATE_NOOP('GDML_PolyGroup',
                                                              'Tesselate Selected Planar Object')}


class TessellateGmshFeature:

    def Activated(self):

        from .GmshUtils import initialize, meshObject, \
              getVertex, getFacets, getMeshLen, printMeshInfo, printMyInfo

        from .GDMLObjects import GDMLGmshTessellated, GDMLTriangular, \
                  ViewProvider, ViewProviderExtension

        print('Action Gmsh Activated')
        for obj in FreeCADGui.Selection.getSelection():
            # if len(obj.InList) == 0: # allowed only for for top level objects
            print('Action Gmsh Tessellate')
            # print(dir(obj))
            print(obj.Name)
            if hasattr(obj, 'Shape') and obj.TypeId != 'App::Part':
                if FreeCADGui.Control.activeDialog() is False:
                    print('Build panel for TO BE Gmeshed')
                    panel = AddTessellateTask(obj)
                    if hasattr(obj, 'Proxy'):
                        print(obj.Proxy.Type)
                        if obj.Proxy.Type == 'GDMLGmshTessellated':
                            print('Build panel for EXISTING Gmsh Tessellate')
                            panel.form.meshInfoLayout = QtGui.QHBoxLayout()
                            panel.form.meshInfoLayout.addWidget(oField('Vertex', 6,
                                                                       str(len(obj.Proxy.Vertex))))
                            panel.form.meshInfoLayout.addWidget(oField('Facets', 6,
                                                                       str(len(obj.Proxy.Facets))))
                            panel.form.Vlayout.addLayout(panel.form.meshInfoLayout)
                            panel.form.setLayout(panel.form.Vlayout)
                    FreeCADGui.Control.showDialog(panel)
                else:
                    print('Already an Active Task')
            return

    def GetResources(self):
        return {'Pixmap': 'GDML_Tessellate_Gmsh',
                'MenuText': QtCore.QT_TRANSLATE_NOOP('GDML_TessGroup',
                                                     'Gmsh & Tessellate'),
                'Tessellate_Gmsh': QtCore.QT_TRANSLATE_NOOP('GDML_TessGroup',
                                                            'Mesh & Tessellate Selected Planar Object')}


class Mesh2TessFeature:

    def Activated(self):

        from .GDMLObjects import GDMLTessellated, GDMLTriangular, \
                  ViewProvider, ViewProviderExtension

        for obj in FreeCADGui.Selection.getSelection():
            # if len(obj.InList) == 0: # allowed only for for top level objects
            print(obj.TypeId)
            if hasattr(obj, 'Mesh'):
                # Mesh Object difficult to determine parent
                print('Action Mesh 2 Tessellate')
                print('Points : '+str(obj.Mesh.CountPoints))
                print('Facets : '+str(obj.Mesh.CountFacets))
                # print(obj.Mesh.Topology[0])
                # print(obj.Mesh.Topology[1])
                vol = createPartVol(obj)
                if hasattr(obj, 'material'):
                    mat = obj.material
                else:
                    mat = getSelectedMaterial()
                m2t = vol.newObject('Part::FeaturePython',
                                    "GDMLTessellate_Mesh2Tess")
                GDMLTessellated(m2t, obj.Mesh.Topology[0], obj.Mesh.Facets, True,
                                "mm", mat)
                if FreeCAD.GuiUp:
                    obj.ViewObject.Visibility = False
                    # print(dir(obj.ViewObject))
                    ViewProvider(m2t.ViewObject)

                FreeCAD.ActiveDocument.recompute()
                FreeCADGui.SendMsgToActiveView("ViewFit")

    def GetResources(self):
        return {'Pixmap': 'GDML_Mesh2Tess', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDML_TessGroup',
                                         'Mesh 2 Tess'), 'Mesh2Tess':
                QtCore.QT_TRANSLATE_NOOP('GDML_TessyGroup',
                                         'Create GDML Tessellate from FC Mesh')}


class Tess2MeshFeature:

    def Activated(self):

        from .GDMLObjects import GDMLTessellated, GDMLTriangular, \
                  ViewProvider, ViewProviderExtension

        from .GmshUtils import TessellatedShape2Mesh, Tetrahedron2Mesh

        for obj in FreeCADGui.Selection.getSelection():
            import MeshPart
            print('Action Tessellate 2 Mesh')
            if hasattr(obj, 'Proxy'):
                if hasattr(obj.Proxy, 'Type'):
                    if obj.Proxy.Type in ['GDMLTessellated',
                                          'GDMLGmshTessellated',
                                          'GDMLTetrahedron']:
                        parent = None
                        if hasattr(obj, 'InList'):
                            if len(obj.InList) > 0:
                                parent = obj.InList[0]
                                mshObj = parent.newObject('Mesh::Feature', obj.Name)
                        if parent is None:
                            mshObj = FreeCAD.ActiveDocument.addObject(
                                'Mesh::Feature', obj.Name)
                        mshObj.Mesh = MeshPart.meshFromShape(obj.Shape)
    
                        if FreeCAD.GuiUp:
                            obj.ViewObject.Visibility = False
                            mshObj.ViewObject.DisplayMode = "Wireframe"
                            FreeCAD.ActiveDocument.recompute()
                            FreeCADGui.SendMsgToActiveView("ViewFit")

    def GetResources(self):
        return {'Pixmap': 'GDML_Tess2Mesh', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDML_TessGroup',
                                         'Tess2Mesh'), 'Tess 2 Mesh':
                QtCore.QT_TRANSLATE_NOOP('GDML_TessGroup',
                                         'Create FC Mesh from GDML Tessellate')} 


class TetrahedronFeature:

    def Activated(self):

        from .GDMLObjects import GDMLTetrahedron, ViewProvider
        from .GmshUtils import initialize, meshObj, \
              getTetrahedrons, printMeshInfo, printMyInfo

        for obj in FreeCADGui.Selection.getSelection():
            print('Action Tetrahedron')
            initialize()
            if meshObj(obj, 3) is True:
                tetraheds = getTetrahedrons()
                if tetraheds is not None:
                    print('tetraheds : '+str(len(tetraheds)))
                    name = 'GDMLTetrahedron_'+obj.Name
                    parent = None
                    if hasattr(obj, 'InList'):
                        if len(obj.InList) > 0:
                            parent = obj.InList[0]
                            myTet = parent.newObject('Part::FeaturePython', name)
                    if parent is None:
                        myTet = FreeCAD.ActiveDocument.addObject(
                            'Part::FeaturePython', name)
                    GDMLTetrahedron(myTet, tetraheds, "mm", getSelectedMaterial())
                    if FreeCAD.GuiUp:
                        obj.ViewObject.Visibility = False
                        ViewProvider(myTet.ViewObject)
                        myTet.ViewObject.DisplayMode = "Wireframe"
                        FreeCAD.ActiveDocument.recompute()
                        FreeCADGui.SendMsgToActiveView("ViewFit")
                    else:
                        FreeCAD.Console.PrintMessage('Not able to produce quandrants for this shape')

    def GetResources(self):
        return {'Pixmap': 'GDML_Tetrahedron',
                'MenuText': QtCore.QT_TRANSLATE_NOOP('GDML_TessGroup',
                                                     'Tetrahedron'),
                'Tetrehedron': QtCore.QT_TRANSLATE_NOOP('GDML_TessGroup',
                                                        'Create Tetrahedron from FC Shape')}


class CycleFeature:

    def Activated(self):

        def toggle(obj):
            # print ("Toggle "+obj.Label)
            # print (obj.ViewObject.DisplayMode)
            # print (obj.ViewObject.Visibility)
            if obj.ViewObject.Visibility is False:
                try:
                    obj.ViewObject.DisplayMode = 'Shaded'
                except:
                    print(obj.Label+' No Shaded')
                obj.ViewObject.Visibility = True
            else:
                if obj.ViewObject.DisplayMode == 'Shaded':
                    obj.ViewObject.DisplayMode = 'Wireframe'
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
            elif obj.isDerivedFrom('App::DocumentObjectGroupPython'):
                # print "Toggle Group"
                for s in obj.Group:
                    # print s
                    cycle(s)

            # Cycle through display options
            elif hasattr(obj, 'ViewObject'):
                toggle(obj)

            if hasattr(obj, 'Base') and hasattr(obj, 'Tool'):
                print("Boolean")
                cycle(obj.Base)
                cycle(obj.Tool)

        for obj in FreeCADGui.Selection.getSelection():
            # if len(obj.InList) == 0: # allowed only for for top level objects
            cycle(obj)

    def GetResources(self):
        return {'Pixmap': 'GDML_Cycle',
                'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDML_CycleGroup',
                                         'Cycle Group'),
                'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('GDML_CycleGroup',
                                         'Cycle Object and all children display')}  

def expandFunction(obj, eNum):
    from .importGDML import expandVolume
    print('Expand Function')
    # Get original volume name i.e. loose _ or _nnn
    name = obj.Label[13:]
    if hasattr(obj, 'VolRef'):
        volRef = obj.VolRef
    else:
        volRef = name
    if obj.TypeId != 'App::Link':
        expandVolume(obj, volRef, eNum, 3)
        obj.Label = name


class ExpandFeature:

    def Activated(self):

        print('Expand Feature')
        for obj in FreeCADGui.Selection.getSelection():
            # if len(obj.InList) == 0: # allowed only for for top level objects
            #   add check for Part i.e. Volume
            print("Selected")
            print(obj.Label[:13])
            if obj.Label[:13] == "NOT_Expanded_":
                expandFunction(obj, 0)
            if obj.Label[:5] == "Link_":
                if hasattr(obj, 'LinkedObject'):
                    if obj.LinkedObject.Label[0:13] == 'NOT_Expanded_':
                        expandFunction(obj.LinkedObject, 0)

    def GetResources(self):
        return {'Pixmap': 'GDML_Expand_One',
                'MenuText': QtCore.QT_TRANSLATE_NOOP('GDML_Expand_One',
                                                     'Expand Volume'),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP('GDML_Expand_One',
                                                    'Expand Volume')}


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
                if hasattr(obj, 'LinkedObject'):
                    if obj.LinkedObject.Label[0:13] == 'NOT_Expanded_':
                        expandFunction(obj.LinkedObject, -1)

    def GetResources(self):
        return {'Pixmap': 'GDML_Expand_Max',
                'MenuText': QtCore.QT_TRANSLATE_NOOP('GDML_Expand_Max',
                                                     'Max Expand Volume'),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP('GDML_Expand_Max',
                                                    'Max Expand Volume')}


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
                    mat['Name'] = material
                    mat['Density'] = str(n.density) + " kg/m^3"
                    mat['ThermalConductivity'] = str(n.conduct) + " W/m/K"
                    mat['ThermalExpansionCoefficient'] = str(n.expand) + " m/m/K"
                    mat['SpecificHeat'] = str(n.specific) + " J/kg/K"
                    # print(mat)
                    # print(mat['Density'])
                    matObj.Material = mat
                    analObj.addObject(matObj)

        def addToList(objList, matList, obj):
            print(obj.Name)
            if hasattr(obj, 'Proxy'):
                # print("Has proxy")
                # material_object = ObjectsFem.makeMaterialSolid \
                #                  (doc,obj.Name+"-Material")
                # allocateMaterial(material_object, obj.Material)
                if isinstance(obj.Proxy, GDMLcommon):
                    objList.append(obj)
                    if obj.material not in matList:
                        matList.append(obj.material)

            if obj.TypeId == 'App::Part' and hasattr(obj, 'OutList'):
                # if hasattr(obj,'OutList') :
                # print("Has OutList + len "+str(len(obj.OutList)))
                for i in obj.OutList:
                    # print('Call add to List '+i.Name)
                    addToList(objList, matList, i)

        def myaddCompound(obj, count):
            # count == 0 World Volume
            print("Add Compound "+obj.Label)
            volList = []
            matList = []
            addToList(volList, matList, obj)
            if count == 0:
                del volList[0]
                del matList[0]
            # DO not delete World Material as it may be repeat
            print('vol List')
            print(volList)
            print('Material List')
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
            if obj.TypeId == 'App::Part':
                myaddCompound(obj, len(obj.InList))

    def GetResources(self):
        return {'Pixmap': 'GDML_Compound',
                'MenuText': QtCore.QT_TRANSLATE_NOOP('GDML_Compound',
                                                     'Add compound to Volume'),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP('GDML_Compound',
                                                    'Add a Compound of Volume')}


FreeCADGui.addCommand('CycleCommand', CycleFeature())
FreeCADGui.addCommand('ExpandCommand', ExpandFeature())
FreeCADGui.addCommand('ExpandMaxCommand', ExpandMaxFeature())
FreeCADGui.addCommand('ColourMapCommand', ColourMapFeature())
FreeCADGui.addCommand('SetMaterialCommand', SetMaterialFeature())
FreeCADGui.addCommand('BooleanCutCommand', BooleanCutFeature())
FreeCADGui.addCommand('BooleanIntersectionCommand', BooleanIntersectionFeature())
FreeCADGui.addCommand('BooleanUnionCommand', BooleanUnionFeature())
FreeCADGui.addCommand('BoxCommand', BoxFeature())
FreeCADGui.addCommand('EllipsoidCommand', EllispoidFeature())
FreeCADGui.addCommand('ElTubeCommand', ElliTubeFeature())
FreeCADGui.addCommand('ConeCommand', ConeFeature())
FreeCADGui.addCommand('SphereCommand', SphereFeature())
FreeCADGui.addCommand('TorusCommand', TorusFeature())
FreeCADGui.addCommand('TrapCommand', TrapFeature())
FreeCADGui.addCommand('TubeCommand', TubeFeature())
FreeCADGui.addCommand('PolyHedraCommand', PolyHedraFeature())
FreeCADGui.addCommand('AddCompound', CompoundFeature())
FreeCADGui.addCommand('TessellateCommand', TessellateFeature())
FreeCADGui.addCommand('TessellateGmshCommand', TessellateGmshFeature())
FreeCADGui.addCommand('DecimateCommand', DecimateFeature())
FreeCADGui.addCommand('Mesh2TessCommand', Mesh2TessFeature())
FreeCADGui.addCommand('Tess2MeshCommand', Tess2MeshFeature())
FreeCADGui.addCommand('TetrahedronCommand', TetrahedronFeature())
