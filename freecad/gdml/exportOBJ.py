
#**************************************************************************
#*                                                                        *
#*   Copyright (c) 2021 Keith Sloan <keith@sloan-home.co.uk>              *
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
#***************************************************************************
__title__="FreeCAD - GDML Tessellated OBJ exporter Version"
__author__ = "Keith Sloan <keith@sloan-home.co.uk>"
__url__ = ["https://github.com/KeithSloan/FreeCAD_GDML"]

import FreeCAD, os


def exportTess2Obj(obj, filepath ) :
    print('Export GDML Tessellatted to OBJ')
    #print(dir(obj))
    #print(dir(obj.Proxy))
    try :
       with open(filepath,"w") as fp :
           print('Vertex : '+str(len(obj.Proxy.Vertex)))
           for v in obj.Proxy.Vertex :
               fp.write("v %5.4f %5.4f %5.4f\n" % (v[0], v[1], v[2]))
           print('Facets : '+str(len(obj.Proxy.Facets)))
           for f in obj.Proxy.Facets :
               l = len(f)
               if l == 3 :
                  fp.write("f %d %d %d\n" % (f[0]+1, f[1]+1, f[2]+1))
               elif l == 4 :
                  fp.write("f %d %d %d %d\n" % (f[0]+1, f[1]+1, f[2]+1, f[3]+1))
               else :
                  print('Invalid number of Vertex')
           print('Tessellated Object Exported')
           fp.close()

    except IOError as e:
       print('Failed to open : '+filepath+" Error (%s)." %e)
 
def export(exportList, filepath) :
    #path, fileExt = os.path.splitext(filepath)
    #print('filepath : '+path)
    #print('file extension : '+fileExt)
    for obj in exportList :
        print(obj.Name)
        print(obj.TypeId)
        if obj.TypeId == "Part::FeaturePython" :
           print('Python Feature')
           if hasattr(obj,'Proxy') :
              print(obj.Proxy.Type)
              if obj.Proxy.Type == "GDMLTessellated" :
                 exportTess2Obj(obj,filepath)
