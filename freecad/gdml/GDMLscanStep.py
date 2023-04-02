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

def getStepPath(path, parent, volRef):
    print(f"==== Get Step Path : {path} {parent.Label} {volRef}")
    print(f"Parents {parent.Parents}")
    for t in parent.Parents:
        print(f"==== tuple {t}")
        #path = os.path.join(path, t[0].Label)
        #print(f"== Path ==> {path}")
        #print(f"==== Parent {t[0]} Label {t[0].Label}")
        for s in str(t[1]).split('.'):
            path = os.path.join(path,s)
    path = os.path.join(path, volRef)
    path = os.path.join(path, volRef+".step")
    print(f"== Path ==> {path}")
    return path


def getPath(path, obj):
    print(f"==== Get Path : {path} {obj.Label}")
    #pList = []
    #print(f"Parent {obj.Parents}")
    for t in obj.Parents:
        print(f"==== tuple {t}")
        path = os.path.join(path, t[0].Label)
        #print(f"== Path ==> {path}")
        #print(f"==== Parent {t[0]} Label {t[0].Label}")
        for s in str(t[1]).split('.'):
            path = os.path.join(path,s)
        #pList.append(t[1])
    print(f"== Path ==> {path}")
    print(f"==== End Get Path")
    #print(f" Path {pList}")
    #return pList


