#**************************************************************************
#*                                                                        *
#*   Copyright (c) 2021 Keith Sloan <keith@sloan-home.co.uk>              *
#*             (c) Munther Hindi                                          *
#*             (c) Dam Lambert                                            *
#*                                                                        *
#*   This program is free software; you can redistribute it and/or modify *
#*   it under the terms of the GNU Lesser General Public License (LGPL)   *
#*   as published by the Free Software Foundation; either version 2 of    *
#*   the License, or (at your option) any later version.                  *
#*   for detail see the LICENCE text file.                                *
#*                                                                        *
#*   This program is distributed in the hope that it will be useful,      *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of       *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        *
#*   GNU Library General Public License for more details.                 *
#*                                                                        *
#*   You should have received a copy of the GNU Library General Public    *
#*   License along with this program; if not, write to the Free Software  *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 *
#*   USA                                                                  *
#*                                                                        *
#*   Acknowledgements :                                                   *
#**************************************************************************
__title__="FreeCAD GDML Workbench - GUI Commands"
__author__ = "Keith Sloan"
__url__ = ["http://www.freecadweb.org"]

import FreeCAD

from PySide import QtGui, QtCore

class GDMLMaterial(QtGui.QComboBox):

   def __init__(self,matList,mat) :
      super().__init__()
      self.addItems(matList)
      self.setEditable(False)
      if mat is not None :
         self.setCurrentIndex(matList.index(mat))

   def getItem(self):
      return str(self.currentText())

def getMaterialsList() :
    matList = []
    doc = FreeCAD.activeDocument()
    try :
       materials = doc.Materials
       geant4 = doc.Geant4
       g4Mats = doc.getObject('G4Materials')

    except :
       from .importGDML import processGEANT4
       from .init_gui   import joinDir

       print('Load Geant4 Materials XML')
       processGEANT4(doc,joinDir("Resources/Geant4Materials.xml"))
       materials = doc.Materials
       geant4 = doc.Geant4
       g4Mats = doc.getObject('G4Materials')
    try :
       if materials is not None :
          for m in materials.OutList :
              if m.Label  != "Geant4" :
                 matList.append(m.Label)
         #print(matList)

    except :
       pass

    try :
       if g4Mats is not None :
          for m in g4Mats.OutList :
              matList.append(m.Label)
          #print(matList)
    except :
       pass

    return matList
