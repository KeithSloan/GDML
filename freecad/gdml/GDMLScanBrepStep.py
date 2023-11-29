# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2023 Keith Sloan <keith@sloan-home.co.uk>              *
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
# **************************************************************************
import os
import FreeCAD

def getPath(path, parent, volRef):
    print(f"==== Get Path : {path} : Parent {parent.Label} : name {volRef}")
    par = parent.Parents
    print(f"Parents {par}")
    if len(par) > 0:
        nl = par[0]
        print(f"nl {nl}")
        nlst = nl[1]
        print(f"nlst {nlst}")
        for i, s in enumerate(nlst.rsplit('.')):
            # Need to ignore first as already in path
            if i > 0 :
               path = os.path.join(path,s)
    return os.path.join(path, volRef)

def getStepPath(path, parent, volRef):
    path = getPath(path, parent, volRef)+".step"
    print(f"== Step Path ==> {path}")
    return path


def getBrepPath(path, parent, volRef):
    path = getPath(path, parent, volRef)+".brep"
    print(f"== Brep Path ==> {path}")
    return path


def getBrepStepPath(importType, path, parent, volRef):
    if importType == 2:
        return getBrepPath(path, parent, volRef)


    elif importType == 3:
        return getStepPath(path, parent, volRef)


    else:
        return None


def createSavedVolume(importType, volDict, parent, name, path):
    from .GDMLObjects import GDMLPartStep, GDMLPartBrep, ViewProvider
    from .importGDML import newPartFeature

    part = None
    if importType == 2:     # Is Brep
        part = newPartFeature(parent, "GDMLPartBrep_" + name)
        GDMLPartBrep(part, path)

    elif importType == 3:    # Is Step
        part = newPartFeature(parent, "GDMLPartStep_" + name)
        GDMLPartStep(part, path)

    else:
        print(f"Not a valid import Type")

    if part is not None:
        volDict.addEntry(name, part)
        if FreeCAD.GuiUp:
            ViewProvider(part.ViewObject)
