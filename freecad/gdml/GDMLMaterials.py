# Sun Jan 30 11:32:46 AM PST 2022
# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2021 Keith Sloan <keith@sloan-home.co.uk>              *
# *             (c) Munther Hindi                                          *
# *             (c) Dam Lambert                                            *
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
# **************************************************************************
__title__ = "FreeCAD GDML Workbench - GUI Commands"
__author__ = "Keith Sloan"
__url__ = ["http://www.freecadweb.org"]

import FreeCAD

from PySide import QtGui, QtCore

class GDMLMaterialsClass():
    def __init__(self):
        self.empty = True
        self.List = []
        self.GroupDict = {}  # dictionary of material lists by type
        self.G4Names = ['NIST', 'Element', 'HEP', 'Space', 'BioChemical']
        self.GroupNames = self.G4Names + ['Normal']
        print(self.GroupNames)
        for grp in self.GroupNames:
            self.GroupDict[grp] = []

    def loadFromDoc(self):
        print('Load Materials Defintions from Doc')
        doc = FreeCAD.ActiveDocument
        if doc is not None:
           if hasattr(doc,'Materials'):
              mats = doc.Materials
              if hasattr(mats,'Group'):
                 for mg in mats.Group:
                     m = mg.Label
                     print(m)
                     if m != 'Geant4':
                         self.List.append(m)
                         self.GroupDict['Normal'].append(m)
                     else:
                         for g4g in mg.Group:
                             print(g4g.Label)
                             if g4g.Label == 'G4Materials':
                                for sg in g4g.Group:
                                    print(sg.Label)
                                    for m in sg.Group:
                                        print(m.Label)
                                        self.GroupDict[sg.Label].append(m.Label)
                                        self.List.append(m.Label)
                     self.empty = False

global GDMLMaterials
GDMLMaterials = GDMLMaterialsClass()

#class GDMLMaterial(QtGui.QComboBox):

#    def __init__(self, matList, mat):
#        super().__init__()
#        self.addItems(matList)
#        self.setEditable(False)
#        if mat is not None:
#            self.setCurrentIndex(matList.index(mat))

#    def getItem(self):
#        return str(self.currentText())

class GDMLMaterialWidget(QtGui.QWidget):

   def __init__(self, Materials):
       super().__init__()
    
       self.Materials = Materials 
       self.groupsCombo = QtGui.QComboBox()
       groups = [group for group in self.Materials.GroupNames]
       self.groupsCombo.addItems(groups)
       self.groupsCombo.currentIndexChanged.connect(self.groupChanged)
       self.materialComboBox = QtGui.QComboBox()
       #self.materialComboBox.addItems(self.groupedMaterials[groups[0]])
       self.materialComboBox.addItems(self.Materials.GroupDict[groups[0]])
       self.completer = QtGui.QCompleter(self.Materials.List, self)
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
       self.mainLayout = QtGui.QVBoxLayout()
       self.mainLayout.addWidget(self.lineedit)
       self.mainLayout.addItem(combosLayout)
       self.setLayout(self.mainLayout)
       # obj = self.SelList[0].Object
       # if hasattr(obj, 'material'):
       #     mat = obj.material
       #     self.lineedit.setText(mat)
       #     self.setMaterial(mat)
       # self.show()

   def setMaterial(self, text):
       for i, group in enumerate(self.Materials.GroupDict):
           if text in self.Materials.GroupDict[group]:
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
       self.materialComboBox.blockSignals(True)
       self.materialComboBox.clear()
       group = self.groupsCombo.currentText()
       self.materialComboBox.addItems(GroupedMaterials[group])
       self.materialComboBox.blockSignals(False)

   def materialChanged(self, text):
       self.lineedit.setText(text)


def getMaterialsList():
    matList = []
    doc = FreeCAD.activeDocument()
    try:
        materials = doc.Materials
        g4Mats = doc.getObject('G4Materials')

    except:
        from .importGDML import processGEANT4
        from .init_gui import joinDir

        print('Load Geant4 Materials XML')
        processGEANT4(doc, joinDir("Resources/Geant4Materials.xml"))
        materials = doc.Materials
        g4Mats = doc.getObject('G4Materials')

    try:
        if materials is not None:
            for m in materials.OutList:
                if m.Label != "Geant4":
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


def refreshG4Materials(doc):
    from .importGDML import joinDir, setupEtree, processMaterialsG4, newGroupPython, processNewG4
    print('Get latest G4 Materials')
    etree, root = setupEtree(joinDir('Resources/Geant4Materials.xml'))
    mats_xml = root.find('materials')
    for m in doc.G4Materials.Group:
        for n in m.Group:
            doc.removeObject(n.Name)
        doc.removeObject(m.Name)
    doc.removeObject(doc.G4Materials.Name)
    G4matGrp = newGroupPython(doc.Geant4, 'G4Materials')
    doc.recompute()
    processNewG4(G4matGrp, mats_xml)
    doc.recompute()


def newGetGroupedMaterials():
    from .importGDML import joinDir, processGEANT4
    print('New getGroupedMaterials')
    return
    #from .GDMLObjects import GroupedMaterials
    if len(GroupedMaterials) == 0:
        doc = FreeCAD.activeDocument()
        if not hasattr(doc, 'Materials') or not hasattr(doc, 'G4Materials'):
            processGEANT4(doc, joinDir("Resources/Geant4Materials.xml"))
            docG4Materials = doc.G4Materials
            if not hasattr(docG4Materials, 'version'):
                refreshG4Materials(doc)
        docG4Materials = doc.G4Materials
        for g in docG4Materials.Group:
            # print(f'g : {g.Label}')
            for s in g.Group:
                # print(f's : {s.Label}')
                if g.Name in GroupedMaterials:
                    GroupedMaterials[g.Label].append(s.Label)
                else:
                    GroupedMaterials[g.Label] = [s.Label]
        matList = []
        docMaterials = doc.Materials
        if docMaterials is not None:
            for m in docMaterials.OutList:
                if m.Label != "Geant4":
                    if m.Label not in matList:
                        matList.append(m.Label)

        if len(matList) > 0:
            GroupedMaterials['Normal'] = matList

    return GroupedMaterials


def getGroupedMaterials():
    print('getGroupedMaterials')
    from .GDMLObjects import GroupedMaterials
    from .importGDML import setupEtree
    from .init_gui import joinDir

    if len(GroupedMaterials) == 0:
        etree, root = setupEtree(joinDir("Resources/Geant4Materials.xml"))
        materials = root.find('materials')

        for material in materials.findall('material'):
            name = material.get('name')
            print(name)
            if name is None:
                print("Missing Name")
            else:
                for auxiliary in material.findall('auxiliary'):
                    auxtype = auxiliary.get('auxtype')
                    if auxtype == 'Material-type':
                        auxvalue = auxiliary.get('auxvalue')
                        if auxvalue in GroupedMaterials:
                            GroupedMaterials[auxvalue].append(name)
                        else:
                            GroupedMaterials[auxvalue] = [name]

    doc = FreeCAD.activeDocument()
    docMaterials = doc.Materials
    matList = []

    if doc.Materials is not None:
        for m in docMaterials.OutList:
            if m.Label != "Geant4":
                if m.Label not in matList:
                    matList.append(m.Label)

    if len(matList) > 0:
        GroupedMaterials['Normal'] = matList

    return GroupedMaterials
