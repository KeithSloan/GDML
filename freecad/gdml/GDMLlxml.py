# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2017 Keith Sloan <keith@sloan-home.co.uk>              *
# *             (c) Munther Hindi 2020                                     *
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

import sys, os
from lxml import etree
import copy

class gdml_lxml() :
    def __init__(self, filename):
        self.filename = filename


    def parseFile(self):
        try:
            from lxml import etree
            print('Running with lxml.etree\n')
            print(f"Parsing {self.filename}")
            parser = etree.XMLParser(resolve_entities=True)
            self.root = etree.parse(self.filename, parser=parser)

        except ImportError:
            try:
                import xml.etree.ElementTree as etree
                print("Rnning with etree.ElementTree (import limitations)\n")
                self.tree = etree.parse(self.filename)
                self.root = self.tree.getroot()
            except:
                print('No lxml or xml')

    def parseEtreeIncludes(self):
        import builtins
        from lxml import etree
        self.root = lxml.etree.fromstring('<xml>' + \
                builtins.open(self.filename).read() +'</xml>')


    def setupEtree(self):
        self.define    = self.root.find('define')
        self.materials = self.root.find('materials')
        self.solids    = self.root.find('solids')
        self.structure = self.root.find('structure')
        self.setup = self.root.find('setup')
        #self.volAsmDict = {}  # Can have number of PhysVols that refer to same
        # Needs to be in VolAsm
        self.VolAsmStructDict = {}


    def printElement(self, elem):
        import lxml.html as html
        print(html.tostring(elem))


    def printMaterials(self):
        import lxml.html as html
        print(html.tostring(self.materials))


    #def printMaterial(self, mat):
    #    import lxml.html as html
    #    print(html.tostring(mat))

    #def checkVolAsmDict(self, name):
    #    # print(f"Check Vol Asm Dict {self.volAsmDict}")
    #    if name in self.volAsmDict.keys():
    #        return False        # No need to process
    #    return True             # NEED to process

    def addVolAsmStructDict(self, name, elem):
        self.VolAsmStructDict[name] = elem


    def getRawVolAsmStruct(self, vaname):
        newStruct = copy.deepcopy(self.structure)
        struct = newStruct.find(f"*[@name='{vaname}']")
        return struct


    def getVolAsmStruct(self, vaname):
        # Needs to be structure and sub volumes
        # So cannot just use structure in source#
        print(f"VolAsmStructDict {self.VolAsmStructDict.keys()}")
        ret = self.VolAsmStructDict[vaname]
        if ret is not None:
            return ret
        else:
            print(f"{vaname} not found in Dict")


    def getPosition(self, posName):
        return self.define.find(f"position[@name='{posName}']")


    def getRotation(self, rotName):
        return self.define.find(f"rotation[@name='{rotName}']")


    def getSolid(self, sname):
        self.solids = self.root.find('solids')
        print(f"getSolid : {self.solids} {len(self.solids)} {sname}")
        # self.printElement(self.solids)
        # return self.solids.find(f"*[@name='{sname}']")
        ret = self.solids.find(f"*[@name='{sname}']")
        print(f"getSolid : {self.solids} {len(self.solids)} {sname}")
        if ret is not None:
            self.printElement(ret)
        print(ret)
        return ret

