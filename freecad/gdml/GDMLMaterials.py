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


class GDMLMaterial(QtGui.QComboBox):

    def __init__(self, matList, mat):
        super().__init__()
        self.addItems(matList)
        self.setEditable(False)
        if mat is not None:
            self.setCurrentIndex(matList.index(mat))

    def getItem(self):
        return str(self.currentText())


def getMaterialsList():
    print('getMaterialsList')
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
                    print(matList)
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
    from .GDMLObjects import GroupedMaterials
    print(f'New getGroupedMaterials len GroupMaterials {len(GroupedMaterials)}')
    # if len(GroupedMaterials) == 0:
    mlen = len(GroupedMaterials)
    if mlen >= 0:
        doc = FreeCAD.activeDocument()
        if not hasattr(doc, 'Materials') or not hasattr(doc, 'G4Materials'):
            processGEANT4(doc, joinDir("Resources/Geant4Materials.xml"))
            docG4Materials = doc.G4Materials
            if not hasattr(docG4Materials, 'version'):
                refreshG4Materials(doc)
        docG4Materials = doc.G4Materials
        print(f'doc.G4Materials {docG4Materials}')
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
        print(f'doc.Materials {docMaterials}')
        if docMaterials is not None:
            for m in docMaterials.OutList:
                print(m.Label)
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
