# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2025 Keith Sloan <ipad2@sloan-home.co.uk>               *
# *                                                                         *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# *   Acknowledgements :                                                    *
# *                                                                         *
# *   Takes as input a Volume Name, GDML file  and outputs                  *
# *             a directory structure starting at the specified Volume Name *
# *                                                                         *
# *                                                                         *
# *                                                                         *
# *                                                                         *
############################################################################*
import FreeCAD as App
import FreeCADGui

from PySide import QtGui, QtCore
from PySide.QtCore import Qt

class BaseClass():
	def __init__(self, obj, type_):
		super().__init__()
		self.obj = obj
		obj.Proxy = self
		obj.Proxy.Type = type_

class MacroObjectClass(BaseClass):
	def __init__(self, obj):
		super().__init__(obj, "MacroObject")
		self.initMacroObject()
		self.sketch = None
				
	def initMacroObject(self):
		print(f"Init Macro  Object")
		self.Macro = self.obj.addProperty("App::PropertyString","MacroName","Base","Macro to be invoked")
		self.ListFloatVars = self.obj.addProperty("App::PropertyStringList","ListFloatVars","Base","List of Macro Float Variables")
		self.ListFloatVars = []
		self.ListOfIntVars = self.obj.addProperty("App::PropertyStringList","ListOfIntVars","Base","List of Macro Int Variables")
		self.ListOfIntVars = []
		self.Execute = self.obj.addProperty("App::PropertyBool","Execute","Base","Execute Macro")
		self.Execute = False
		self.Parameters = self.obj.addProperty("App::PropertyBool","Parameters","Base","Set Variable Parameters")
		self.Parameters = False

	def onChanged(self, fp, prop):
		# print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
		if "Restore" in fp.State:
			return

		if prop in ["ListFloatVars"]:
			if App.GuiUp:
				for var in self.obj.ListFloatVars:
					if not hasattr(self.obj, var): 
						self.obj.addProperty("App::PropertyFloat", var, "Base", var)
						
		if prop in ["ListIntVars"]:
			if App.GuiUp:
				for var in self.obj.ListIntVars:
					if not hasattr(self.obj, var): 
						self.obj.addProperty("App::PropertyFloat", var, "Base", var)
						
		
		if prop in ["Execute"]:
			print("Execute")
			if self.Execute:
				for var in self.obj.ListIntVars:
					print(f"Write {var}")
				for var in self.obj.ListFloatVars:
					print(f"Write {var}")
				print("Execute")
			self.Execute = False

		if prop in ["Parameters"]:
			print("Setup Variables")
			if self.Execute:
				for var in self.obj.ListIntVars:
					print(f"Write {var}")
				for var in self.obj.ListFloatVars:
					print(f"Write {var}")
				print("Execute")
			self.Execute = False

class MacroObjectFeature:
	def Activated(self):
		print("Macro Object Feature")
		doc = App.ActiveDocument
		obj = doc.addObject("App::FeaturePython","MacroObject")
		MacroObjectClass(obj)
		doc.recompute
		return

	def IsActive(self):
		if App.ActiveDocument is None:
			return False
		else:
			return True

	def GetResources(self):
		return {
            "Pixmap": "MacroObject",
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "MacroObject", "Macro Object"
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "MacroObject", "Macfro Object"
            ),
        }

FreeCADGui.addCommand("MacroObjectCmd", MacroObjectFeature())