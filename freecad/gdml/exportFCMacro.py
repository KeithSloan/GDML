from __future__ import annotations
# Mon Aug 26 2024
# Sat Mar 28 8:44 AM PDT 2023
# **************************************************************************
# *                                                                        *
# *   Copyright (c) 20259 Keith Sloan <ipad2@keith@sloan-home.co.uk>       *
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
# *   Acknowledgements : Ideas & code copied from                          *
# *                      https://github.com/ignamv/geanTipi                *
# *                                                                        *
# ***************************************************************************
__title__ = "FreeCAD - Macro Object exporter Version"
__author__ = "Keith Sloan <ipad2@keith@sloan-home.co.uk>"
__url__ = ["https://github.com/KeithSloan/FreeCAD_Geant4"]

from sys import breakpointhook

import FreeCAD as App

import os, sys
from pathlib import Path

def check_macro_file(MacroName):
  preference = App.ParamGet("User parameter:BaseApp/Preferences/Macro")
  macroPath = preference.GetString("MacroPath")
  print(f"Macro Path {macroPath}")
  macroFileName = os.path.join(macroPath, MacroName + '.FCMacro')
  print(f"Macro File Name {macroFileName}")
  filePath = Path(macroFileName)
  return filePath.is_file(), macroFileName
  
def read_file_into_buffer(file_path):
	with open(file_path, 'r') as file:
		file_contents = file.read()
	return file_contents

def exportFCMacro(first, filepath, fileExt):
  import FreeCAD
  print(f"Export Macro Object {first} as FCMacro file")
  print(f"Object Type {first.TypeId}")
  if first.TypeId == "App::FeaturePython" or first.TypeId == "Part::FeaturePython":
    #print(dir(first))
    if hasattr(first, "Proxy"):
      print("Proxy")
      #if first.Proxy.Type in ["MacroObject", "MacroGroup", "MacroShape", "MacroCurve"]:
      #    print("Macro Type {first.Proxy,Type}")
      #print(dir(first.Proxy))
      if hasattr(first.Proxy, "initBaseObject"):
          f = open(filepath, "w")
          #f.write("Now the file has more content!")
          print(first.PropertiesList)
          varDict  = {}
          valDict = {}
          for var in first.PropertiesList:
            print(f"prop {var}")
					  #print(dir(var))
            if var.startswith("Variable"):
              value = getattr(first, var)
              print(f"Variable var {var.rsplit('_')} value {value}")
              varName = var.rsplit('_')
              v = getattr(first, var)
              print(f"v {v} type {type(v)} {type(v).__name__}")
              varDict[varName[1]] = type(v).__name__
              valDict[varName[1]] = value
            elif var == "material":
              print(first.material)
              matIdx = first.getEnumerationsOfProperty(var).index(first.material)
              print(f"Material Index {matIdx}")
          print(f"VarDict {varDict}")
          print(f"ValDict {valDict}")
          f.write("#********************* Macro Object *************************\n")
          f.write("#****** Set Variables ***************************************\n")
          Type = "Unknown"
          for i in ["initMacroObject", "initMacroGroup", "initMacroShape", "initMacroCurve"]:
            if hasattr(first.Proxy, i):
              Type = i.removeprefix('init')
          print(f"Type {Type}")    
          f.write('Type = "{0}\n'.format(Type))
          print(f"material {first.material}")
          f.write("material = {0}\n".format(first.material))
          f.write("matIdx = {0}\n".format(matIdx))
          f.write("var = {0}\n".format(varDict))
          f.write("val = {0}\n".format(valDict))
          f.write("#<<<< End Variables >>>>\n")
          f.write("#******** Macro now follows **********************************\n")
          f.write("from freecad.gdml.QtInputVars import checkVariablesSet\n")
          f.write("# checkVariablesSet - will check if variables passed or prompt\n")
          f.write("checkVariablesSet(vars, dir())\n")
          f.write("#********** Rest of Macro Follows ****************************\n")
          #exist, macroFile = check_macro_file(var.MacroName)
          #macroBuff = read_file_into_buffer(macroFile)
          #f.write(macroBuff)
          f.close()

def export(exportList, filepath):
  "called when FreeCAD exports a file"
  first = exportList[0]
  print(f"Export Macro Object: {first.Label}")
  path, fileExt = os.path.splitext(filepath)
  print("filepath : " + path)
  print("file extension : " + fileExt)
  if fileExt == ".FCMacro":
    exportFCMacro(first, filepath, ".FCMacro")
