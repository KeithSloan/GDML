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
from PySide import QtGui
import os, io, sys, re
import Part, Draft


def joinDir(path):
    import os

    __dirname__ = os.path.dirname(__file__)
    return os.path.join(__dirname__, path)


if open.__module__ == "__builtin__":
    pythonopen = open  # to distinguish python built-in open function from the one declared here


def open(filename):
    "called when freecad opens a file."
    print(f"Open : {filename} {processType}")
    fileName = os.path.splitext(os.path.basename(filename))[0]
    print(f"path : {filename}")
    if filename.endswith(".FCMacro"):
        processFCMacro(filename)
        # profiler.disable()
        # stats = pstats.Stats(profiler).sort_stats('cumtime')
        # stats.print_stats()

def insert(filename, docname):
    "called when freecad imports a file"
    print("Insert filename : " + filename + " docname : " + docname)
    try:
        doc = FreeCAD.getDocument(docname)
    except NameError:
        doc = FreeCAD.newDocument(docname)
    if filename.endswith(".FCMacro"):
        processFCMacro(filename)

def processFCMacro(filename):
	print(f"Process FCMacro file {filename} to Macro Object")	
