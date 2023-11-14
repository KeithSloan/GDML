# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2023 Keith Sloan <keith@sloan-home.co.uk>              *
# *                      Munther Hindi                                      *
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
#                                                                          *
#     Takes as input a GDML file directory and creates/updates             *
#          STEP / BREP files from the GDML definitions                     *
#                                                                          *
#             python3 processDirStruct.py <directory>                      *
#                                                                          *
#***************************************************************************
import sys, os

class volAsm_class:
    # ??? volasm in several places aslo different levels?
    def __init__(self, vaName, path, level):
        print(f"New volasm {vaName} path {path} level {level}")
        self.vaName = vaName
        self.path = path
        self.subVolAsmList = []
        self.level = level


    def getName(self):
        return self.vaName


    def addSubVolAsms(self, volasmList):
        self.subVolAsmList = volasmList


    def getSubVolAsms(self):
        return self.subVolAsmList


    def printSubVolAsms(self):
        print(f"Volume {self.vaName}")
        for i in self.subVolAsmList:
            print(i.getName())    


    def processPath(self, path, level, levels, volAsmDict):
        print(f"Processing path {path} level {level}")
        vaName = os.path.splitext(os.path.basename(path))[0]
        print(f"Processing VolAsm {vaName}")
        volAsm = volAsm_class(vaName, path, level)
        #volAsm = volAsm_class(vaName, path)
        # Add volume to dictionary
        volAsmDict[self.vaName] = vaName
        #print(f"new Volume {volAsm.getName()}")
        levels.addVolAsm(volAsm, self.path, level)
        subVolAsms = os.scandir(path)
        for p in subVolAsms:
            if p.is_dir():
                self.processPath(p.path, level+1, levels, volAsmDict)


    def exportStep(self):
        print(f"Export STEP {self.vaName} path {self.path}")
        import FreeCAD, FreeCADGui
        # import FreeCADGui
        #print(f"FreeCAD loaded")
        #import freecad.gdml.importGDML
        #print(f"importGDML loaded")
        #freecad.gdml.importGDML.open(u"/Users/keithsloan/Downloads/CERN-Dipole/Dipole/asHS/asHS.gdml")
        print(dir(FreeCADGui))
        FreeCADGui.activateWorkbench("GDML_Workbench")
        doc = freecad.gdml.importGDML.open(self.path)
        #doc = FreeCAD.open(u"/Users/keithsloan/Downloads/CERN-Dipole/Dipole/asHS/asHS.gdml")
        #doc = FreeCAD.open(u"/Users/keithsloan/Downloads/CERN-Dipole/Dipole/DCoil/DCoil.gdml")
        print(f"GDML file opened")
        obj = FreeCAD.ActiveDocumet.getObject(self.vaName)
        import Import
        if hasattr(Import, "exportOptions"):
            # need to use join
            exportPath = self.path+"/"+self.vaName+".step"
            options = Import.exportOptions(exportPath)
            Import.export(obj, exportPath, options)
            print(f"exported wih Options")
        else:
            Import.export(obj, exportPath)
            print(f"exported")


    def exportBrep(self):
        print(f"Export Brep {self.vaName} path {self.path}")
        print(f"Needs coding")


class levelDet:
    def __init__(self):
        self.volAsmList = []


    def getNumVolAsm(self):
        return len(self.volAsmList)


    def getVolAsms(self):
        return self.volAsmList


    def levelAddVolAsm(self, volAsm, path, level):
        print(f"Add Volume {volAsm.getName()} to level {level}")
        #self.volAsmList.append(volAsm_class(vaName, path, level))    
        self.volAsmList.append(volAsm)   


class levels_class:
    def __init__(self):
        self.levels = []


    def addLevel(self):
        #print(f"levels add level")
        self.levels.append(levelDet())
        #print(f"len self.levels {len(self.levels)}")


    def checkLevel(self, lvlNum):
        #print(f"levels checkLevel lvlNum {lvlNum} levels {len(self.levels)}")
        #print(f"test {lvlNum > len(self.levels)}")
        # Lists index from 0
        lvl = int(lvlNum) - 1
        if lvlNum > len(self.levels):
            self.addLevel()
        #else:
        #    print("No need to add")    

        return self.levels[lvl]


    def addVolAsm(self, volAsm, path, lvlNum):
        #print(f"levels add VolAsm {volAsm.getName()}")
        levelDet = self.checkLevel(lvlNum)
        levelDet.levelAddVolAsm(volAsm, path, lvlNum)


    def print(self):
        # print(f"Levels {self.levels}")
        for i, l in enumerate(self.levels):
            print(f" Level {i} Number of VolAsm {l.getNumVolAsm()}")

    def process(self):
        self.numVolAsm = 3
        # print(f"Levels {self.levels}")
        print(f"/nProcess levels in Reverse order/n")
        for i, l in reversed(list(enumerate(self.levels))):
            numVolAsm = l.getNumVolAsm()
            print(f" Level {i} Number of VolAsm {numVolAsm}")
            if numVolAsm > self.numVolAsm:
                volAsmList = l.getVolAsms()
                for volAsm in volAsmList:
                    print(f"volAsm {volAsm.getName()}")
                    volAsm.exportStep()



class dirBase_class:
    def __init__(self, basePath):
        self.basePath = basePath
        self.volAsmDict = {}
        self.levels = levels_class()

        self.setPathEnv()
        vaName = os.path.splitext(os.path.basename(basePath))[0]

        self.baseVolAsm = volAsm_class(vaName, basePath, 1)
        self.baseVolAsm.processPath(basePath, 1, self.levels, self.volAsmDict)

        print(f"Base Path {self.basePath}\n")
        #print(f"Path List \n")
        #for i in self.pathList:
        #    print(i.getName())
        self.baseVolAsm.printSubVolAsms()
        self.levels.print()
        self.levels.process()


    def setPathEnv(self):
        import sys, platform
        system = platform.system()
        print(f"System {system}")
        if system == "linux" or system == "linux2":
            # linux
            sys.path.append('/usr/lib/freecad/lib')
        elif system == "Darwin":
            # OS X
            print(f"Mac OS X")
            sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
            sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib/python3.10/site-packages')

            #sys.path.append('/usr/lib/freecad/lib')
        elif system == "win32":
            # Windows...
            print(f"Trying FreeCAD path 'C://Program Files/FreeCAD/bin'")
            sys.path.append('C://Program Files/FreeCAD/bin')

print(f"Development switched to ProcessDirStruct.FCMAcro")
print(f"Retaining just in case")
sys.exit(3)

if len(sys.argv) < 2:
    print ("Usage: sys.argv[0] <gdml_directory>")
    sys.exit(1)

basePath = sys.argv[1]
baseVaName = os.path.splitext(os.path.basename(basePath))[0]
levels = levels_class()

print(f"\nProcessing GDML directory : {basePath}")

base = dirBase_class(basePath)
