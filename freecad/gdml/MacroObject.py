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

import os, sys, tempfile

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
		self.Material = None
				
	def initMacroObject(self):
		from freecad.gdml.GDMLObjects import setMaterial
		print(f"Init Macro Object")
		self.Macro = self.obj.addProperty("App::PropertyString","MacroName","Base","Macro to be invoked")
		#self.ListVars = self.obj.addProperty("App::PropertyStringList","ListVars","Base","List of Macro Variables")
		#self.ListVars = []
		self.Execute = self.obj.addProperty("App::PropertyBool","Execute","Base","Execute Macro")
		self.Execute = False
		self.material = self.obj.addProperty("App::PropertyEnumeration","material","GDML","GDML Material")
		setMaterial(self.obj, self.material)
		#self.Parameters = self.obj.addProperty("App::PropertyBool","Parameters","Base","Set Variable Parameters")
		#self.Parameters = False

	def read_file_into_buffer(self, file_path):
		with open(file_path, 'r') as file:
			file_contents = file.read()
		return file_contents

	def getMaterial(self):
		return self.Material

	def onChanged(self, fp, prop):
		# print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
		print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
		if "Restore" in fp.State:
			return

		if prop in "material":
			self.material = fp.material

		if prop in ["Execute"]:
			print("Execute")
			#if open.__module__ == "__builtin__":
			#	pythonopen = open  # to distinguish python built-in open function from the one declared here
			#tmpDir = tempfile.gettempdir()
			#print(f"Temp directory {tmpDir}")
			#tmpOutFile = os.path.join(tmpDir, fp.Label+'.FCMacro')
			#file = open(tmpOutFile,"w")
			#'file = pythonopen(tmpOutFile,"w")
			#print(dir(prop))
			if fp.Execute:
				#codeLines = ''
				#commentLines = ''
				print(f"self {dir(self)}")
				varDict = {}
				print(dir(fp))
				print(fp.PropertiesList)
				for var in fp.PropertiesList:
					print(f"prop {var}")
					#print(dir(var))
					if var.startswith("Variable"):
						value = getattr(fp, var)
						print(f"Variable var {var.rsplit('_')} value {value}")
						varName = var.rsplit('_')
						varDict[varName[1]] = value
					elif var == "material":
						print(fp.material)
						varDict[var] = fp.material
						#print(fp.getEnumerationsOfProperty(var))
						matIdx = fp.getEnumerationsOfProperty(var).index(fp.material)
						print(f"Material Index {matIdx}")
						varDict["matIdx"] = matIdx
				print(f"VarDict {varDict}")
				print(f"Execute varDict {varDict}")
				preference = App.ParamGet("User parameter:BaseApp/Preferences/Macro")
				macroPath = preference.GetString("MacroPath")
				print(f"Macro Path {macroPath}")
				macroFileName = os.path.join(macroPath, fp.MacroName + '.FCMacro')
				print(f"Macro File Name {macroFileName}")
				macroTxt = self.read_file_into_buffer(macroFileName)
				exec(macroTxt, varDict)
				#codeLines = codeLines + macroTxt
				#exec(codeLines)
				#f = open(tmpOutFile, 'wt', encoding='utf-8')
				#f.write(commentLines)
				#f.write(codeLines)
				#f.write(macroTxt)
				#f.close()
				#newMacroFile = os.path.join('"' +  macroPath + '"', fp.Label + '.FCMacro')
				#newMacroFile = os.path.join(macroPath, fp.Label + '.FCMacro')
				#print(f"newMacroFile {newMacroFile}")
				#f = open(newMacroFile, 'wt', encoding='utf-8')
				#f.write(codeLines)				
				#f.close()
				fp.Execute = False

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