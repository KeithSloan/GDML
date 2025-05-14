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

import FreeCAD
import FreeCADGui
from PySide import QtGui

import sys
from pathlib import Path


def exportFCMacro(first, filepath, fileExt):
	print(f"Export Macro Object {first} as FCMacro file")
	pass

def export(exportList, filepath):
    "called when FreeCAD exports a file"
    first = exportList[0]
    print(f"Export Macro Object: {first.Label}")

    import os

    path, fileExt = os.path.splitext(filepath)
    print("filepath : " + path)
    print("file extension : " + fileExt)

    if fileExt == ".FCMacro":
      exportFCMacro(first, filepath, ".FCMacro")
