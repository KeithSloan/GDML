# -*- coding: utf8 -*-
#**************************************************************************
#*                                                                        *
#*   Copyright (c) 2017 Keith Sloan <keith@sloan-home.co.uk>              *
#*             (c) Dam Lambert 2020                                       *
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
#*                                                                        *
#*                                                                        *
#**************************************************************************
__title__="FreeCAD - GDML workbench ColourMap"
__author__ = "Keith Sloan <keith@sloan-home.co.uk>"
__url__ = ["https://github.com/KeithSloan/FreeCAD_GDML"]

import FreeCAD
#from PySide2 import QtGui, QtCore
#from PySide2.QtCore import QSize, Qt
#from PySide2.QtWidgets import QApplication, QMainWindow, QPushButton

import sys

from PySide import QtGui, QtCore

class GDMLColourMap(QtGui.QDialog) :

   #   from .GDMLObjects import GDMLColourMapEntry

   def __init__(self) :
      #super(GDMLColourMap, self).__init__()
      super().__init__()
      self.initUI()

   def initUI(self):
      #self.result = userCancelled
      # create our window
      # define window		xLoc,yLoc,xDim,yDim
      self.setGeometry(	250, 250, 400, 150)
      self.setWindowTitle("Our Example Nonmodal Program Window")
      self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
      self.setMouseTracking(True)
      # create Labels
      self.label4 = QtGui.QLabel("can you see this?", self)
      self.label4.move(20, 20)
      self.label5 = QtGui.QLabel("Mouse position:", self)
      self.label5.move(20, 70)
      self.label6 = QtGui.QLabel("               ", self)
      self.label6.move(135, 70)
      # toggle visibility button
      pushButton1 = QtGui.QPushButton('Toggle visibility', self)
      pushButton1.clicked.connect(self.onPushButton1)
      pushButton1.setMinimumWidth(150)
      #pushButton1.setAutoDefault(False)
      pushButton1.move(210, 20)
      #  cancel button
      cancelButton = QtGui.QPushButton('Cancel', self)
      cancelButton.clicked.connect(self.onCancel)
      cancelButton.setAutoDefault(True)
      cancelButton.move(150, 110)
      # OK button
      okButton = QtGui.QPushButton('OK', self)
      okButton.clicked.connect(self.onOk)
      okButton.move(260, 110)
      # now make the window visible
      self.show()
      #

   def onPushButton1(self):
      if self.label4.isVisible():
         self.label4.hide()
      else:
         self.label4.show()

   def onCancel(self):
       self.result = userCancelled
       self.close()

   def onOk(self):
       self.result = userOK
       self.close()

   def mouseMoveEvent(self,event):
       self.label6.setText("X: "+str(event.x()) + " Y: "+str(event.y()))

# Class definitions

# Function definitions

# Constant definitions
global userCancelled, userOK
userCancelled		= "Cancelled"
userOK			= "OK"

