# -*- coding: utf-8 -*-
# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2025 Keith Sloan <keith@sloan-home.co.uk>              *
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
# *                                                                        *
# **************************************************************************
__title__ = "FreeCAD - Macro Object importer"
__author__ = "Keith Sloan <ipad2@keith@sloan-home.co.uk>"
__url__ = ["https://github.com/KeithSloan/FreeCAD_GDML"]

import FreeCAD

def joinDir(path):
    import os

    __dirname__ = os.path.dirname(__file__)
    return os.path.join(__dirname__, path)

def open(filename):
    import os
    "called when freecad opens a file."
    print(f"Open : {filename}")
    docName = os.path.splitext(os.path.basename(filename))[0]
    doc = FreeCAD.newDocument(docName)
    print(f"path : {filename}")
    if filename.endswith(".FCMacro"):
        processFCMacro(doc, filename)
        # profiler.disable()
        # stats = pstats.Stats(profiler).sort_stats('cumtime')
        # stats.print_stats()

def insert(filename, docname):
    "called when freecad imports a file"
    print("Insert filename : " + filename + " docname : " + docname)
    doc = FreeCAD.ActiveDocument
    try:
        doc = FreeCAD.getDocument(docname)
    except NameError:
        doc = FreeCAD.newDocument(docname)
    if filename.endswith(".FCMacro"):
        processFCMacro(doc, filename)

def processFCMacro(doc, filename):
    import builtins
    from freecad.gdml.MacroObject import MacroObjectClass

    print(f"Procces Import FCMacro file {filename} to Doc {doc.Label}")
    file = builtins.open(filename, "r")
    for line in file:
        #print("Line : {}".format(line.strip()))
        if line.startswith("#<<< End Variables >>>>"):
            break
        elif line.startswith("#*****"):
            pass
        else:     
            # Split at the first comma using partition
            var, _, val = line.partition('=')
            print(f"Var {var} Value {val}")
            # Safer than using Exec
            if var == "macroType":
                print(f"MacroType {val}")
                macroType = val
            elif var == "varDict":
                print(f"varDict {val}")
                varDict = val
            elif var == "valDict":
                print(f"valDict {val}")
                valDict = val
            elif var == "material":
                print(f"material {val}")
                material = val
            elif var == "matIdx":
                print(f"matidx {val}")
                matIdx = val
    print(f"Macro Type {macroType}")
    obj = newMacroObject(doc, macroType)

def newMacroObject(doc, Type):
    from freecad.gdml.MacroGroup import MacroObject, MacroShape, MacroGroup
    if Type == "MacroObject":
        obj = doc.addObject("App::FeaturePython", Type)
        MacroObject(obj)
    elif Type == "MacroShape":
        obj = doc.addObject("App::PartFeaturePython", Type)
        MacroShape(obj)
    elif Type == "MacroGroup":
        obj = doc.addObject("App::GroupFeaturePython", Type)
        MacroGroup(obj)
    else:
        print(f"{Type} Not a Valid Macro Group")
    return obj

       