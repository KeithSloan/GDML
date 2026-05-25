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

from freecad.gdml.importGDML import processReactor


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

    # Ensure Geant4 materials are loaded
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

    # User-defined materials (exclude OpenMC-only containers)
    _SKIP_LABELS = {"Geant4", "ReactorMaterials"}
    try:
        if materials is not None:
            for m in materials.OutList:
                if m.Label not in _SKIP_LABELS:
                    matList.append(m.Label)
    except:
        pass

    # Geant4 NIST / HEP / Space / … materials
    try:
        if g4Mats is not None:
            for m in g4Mats.OutList:
                for n in m.OutList:
                    matList.append(n.Label)
    except:
        pass

    # Note: ReactorMaterials are intentionally excluded — they are OpenMC-only
    # and must not appear as selectable materials for GDML objects.

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
    from .importGDML import joinDir, processGEANT4, processReactor
    from .GDMLObjects import GroupedMaterials
    print(f'New getGroupedMaterials len GroupMaterials {len(GroupedMaterials)}')
    # if len(GroupedMaterials) == 0:
    mlen = len(GroupedMaterials)
    if mlen >= 0:
        doc = FreeCAD.activeDocument()
        if not hasattr(doc, 'Materials') or not hasattr(doc, 'G4Materials') or not hasattr(doc, 'ReactorMaterials'):
            processGEANT4(doc, joinDir("Resources/Geant4Materials.xml"))
            processReactor(doc, joinDir("Resources/ReactorMaterials.xml"))
            docG4Materials = doc.G4Materials
            if not hasattr(docG4Materials, 'version'):
                refreshG4Materials(doc)
        docG4Materials = doc.G4Materials
        reactorMaterials = doc.ReactorMaterials
        print(f'doc.G4Materials {docG4Materials}')
        print(f'doc.ReactorMaterials {reactorMaterials}')
        for g in docG4Materials.Group:
            # print(f'g : {g.Label}')
            for s in g.Group:
                # print(f's : {s.Label}')
                if g.Name in GroupedMaterials:
                    GroupedMaterials[g.Label].append(s.Label)
                else:
                    GroupedMaterials[g.Label] = [s.Label]

        GroupedMaterials[reactorMaterials.Label] = [g.Label for g in reactorMaterials.Group]

        matList = []
        docMaterials = doc.Materials
        print(f'doc.Materials {docMaterials}')
        # Exclude sub-group containers that are not selectable materials.
        # "Geant4" holds G4_* pre-defined materials (handled via G4Materials group above).
        # "ReactorMaterials" is an OpenMC-only container; its contents are
        # already added as a separate group via GroupedMaterials[reactorMaterials.Label].
        _NORMAL_SKIP = {"Geant4", "ReactorMaterials"}
        if docMaterials is not None:
            for m in docMaterials.OutList:
                print(m.Label)
                if m.Label not in _NORMAL_SKIP:
                    if m.Label not in matList:
                        matList.append(m.Label)

        if len(matList) > 0:
            GroupedMaterials['Normal'] = matList

    return GroupedMaterials
