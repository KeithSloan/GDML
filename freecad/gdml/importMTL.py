# -*- coding: utf-8 -*-
# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2024 Keith Sloan <keithsloan52@icloud.com>              *
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
# *   Acknowledgements :
# *                                                                        *
# *                                                                        *
# **************************************************************************
__title__ = "FreeCAD - MTL -> Spreadsheet importer"
__author__ = "Keith Sloan <keithsloan52@icloud.com>"
__url__ = ["https://github.com/KeithSloan/FreeCAD_GDML"]

import FreeCAD, FreeCADGui
import os, io, sys, re
import Part, Draft

from PySide import QtGui, QtCore

def joinDir(path):
    import os
    __dirname__ = os.path.dirname(__file__)
    return(os.path.join(__dirname__, path))

# Save the native open function to avoid collisions
if open.__module__ in ['__builtin__', 'io']:
    pythonopen = open  # to distinguish python built-in open function from the one declared her

class switch(object):
    value = None

    def __new__(class_, value):
        class_.value = value
        return True


def case(*args):
    return any((arg == switch.value for arg in args))

def open(filePath):
    "called when freecad opens a file."

    print('Open : '+filePath)
    docName = os.path.splitext(os.path.basename(filePath))[0]
    print('path : '+filePath)
    if filePath.lower().endswith('.mtl'):
        try:
            doc = FreeCAD.ActiveDocument()
            print('Active Doc')

        except:
            print('New Doc')
            doc = FreeCAD.newDocument(docName)

        processMTL(doc, filePath)
        return doc


def insert(filePath, docname):
    "called when freecad imports a file"
    print('Insert filePath : '+filePath+' docname : '+docname)
    global doc
    groupname = os.path.splitext(os.path.basename(filePath))[0]
    try:
        doc = FreeCAD.getDocument(docname)
    except NameError:
        doc = FreeCAD.newDocument(docname)
    if filePath.lower().endswith('.mtl'):
        processMTL(doc, filePath)


def processMTL(doc, filePath, matDict=None):
    import os, Spreadsheet

    #print(f"process MTL matDict {matDict}")
    fileName = os.path.basename(filePath)
    sheetName = os.path.splitext(fileName)[0]
    # Create a new spreadsheet in the document
    spreadsheet = doc.addObject("Spreadsheet::Sheet", sheetName)
    spreadsheet.Label = sheetName +"_mtl"
    materialsGrp = doc.getObject("Materials")
    if materialsGrp is not None:
        materialsGrp.addObject(spreadsheet)

     # Set the headers for the spreadsheet
    headers = ["Name", "Ka", "Kd", "Ks", "Ns", "d", "Tr", "Tf", "illum"]
    columnLetters = ["A", "B", "C", "D", "E", "F", "G","H","I"]

    for col, header in zip(columnLetters, headers):
        spreadsheet.set(col + '1', header)

    # Read the input file and parse the data
    with pythonopen(filePath, 'r') as file:
        current_material = None
        data = {}

        for line in file:
            line = line.strip()
            if line.startswith("newmtl"):
                if current_material:  # Save the previous material data if any
                    data[current_material] = material_data

                current_material = line.split()[1]
                material_data = {'name': current_material}

            elif current_material and line:
                key, *values = line.split()
                value_str = ' '.join(values)

                if key in ["Ka", "Kd", "Ks"]:
                    material_data[key] = tuple(map(float, value_str.split()))
                elif key in ["Tf"]:
                    material_data[key] = tuple(map(int, value_str.split()))
                elif key in ["Ns", "d", "Tr", "illum"]:
                    material_data[key] = float(value_str) if '.' in value_str else int(value_str)

        # Save the last material data if present
        if current_material:
            data[current_material] = material_data

    # Populate matDict if supplied
    if matDict is not None:
        for mat_name, mat_props in data.items():
            matDict[mat_name] = mat_props
        #print(f"Map Dict {matDict}")

    # Populate the spreadsheet
    row = 2  # Start from row 2 (row 1 can be headers if needed)
    for mat_name, mat_props in data.items():
        # Set name
        spreadsheet.set('A' + str(row), mat_name)
        spreadsheet.setAlias('A' + str(row), f"name_{mat_name}")

        # Set Ka
        if 'Ka' in mat_props:
            spreadsheet.set('B' + str(row), ' '.join(map(str, mat_props['Ka'])))
            spreadsheet.setAlias('B' + str(row), f"Ka_{mat_name}")

        # Set Kd
        if 'Kd' in mat_props:
            spreadsheet.set('C' + str(row), ' '.join(map(str, mat_props['Kd'])))
            spreadsheet.setAlias('C' + str(row), f"Kd_{mat_name}")

        # Set Ks
        if 'Ks' in mat_props:
            spreadsheet.set('D' + str(row), ' '.join(map(str, mat_props['Ks'])))
            spreadsheet.setAlias('D' + str(row), f"Ks_{mat_name}")

        # Set Ns
        if 'Ns' in mat_props:
            spreadsheet.set('E' + str(row), str(mat_props['Ns']))
            spreadsheet.setAlias('E' + str(row), f"Ns_{mat_name}")

        # Set d
        if 'd' in mat_props:
            spreadsheet.set('F' + str(row), str(mat_props['d']))
            spreadsheet.setAlias('F' + str(row), f"d_{mat_name}")

        # Set Tr
        if 'Tr' in mat_props:
            spreadsheet.set('G' + str(row), str(mat_props['Tr']))
            spreadsheet.setAlias('G'+ str(row), f"Tr_{mat_name}")
        
        # Set Tf
        if 'Tf' in mat_props:
            spreadsheet.set('H' + str(row), str(mat_props['Tf']))
            spreadsheet.setAlias('H'+ str(row), f"Tf_{mat_name}")

        # Set illum
        if 'illum' in mat_props:
            spreadsheet.set('I' + str(row), str(mat_props['illum']))
            spreadsheet.setAlias('I'+ str(row), f"illum_{mat_name}")
        row += 1

    # Recompute and save the document
    doc.recompute()
    # Recompute
    doc.recompute()
