#.from GDMLlxml import gdml_lxml
from GDMLlxml import gdml_lxml
import os

class processGDML(gdml_lxml):
    def __init__(self, filePath, option=1):
        super().__init__(filePath)
        self.filePath = filePath
        self.option = option


    def processFile(self):
        print(f"Process GDML File {self.filePath} Option {self.option}")
        pathDet = os.path.split(self.filePath)
        self.path = pathDet[0]
        self.fileName = pathDet[1]
        print(f"Path : {self.path} FileName : {self.fileName}")
        self.parseFile()
        self.setupEtree()
        self.processSetup()
        self.parseVolAsm(self.worldName)


    def processSetup(self):
        wrk = self.setup.find("world")
        self.worldName = wrk.get("ref")
        print(f"World Volume : {self.worldName}")


    def parseVolAsm(self, vaName):
        print(f"Parse VolAsm {vaName}")
        volasm = self.structure.find("*[@name='%s']" % vaName)
        if volasm is not None:
            print(f"{vaName} is a {volasm.tag}")
            if volasm.tag == "volume":
                self.parseVol(volasm, vaName)
            elif volasm.tag == "assemble":
                self.parseAsm(volasm, vaName)


    def parseVol(self, volasm, vaName):
        print(f"Parse Volume {vaName}")


    def parseAsm(self, volasm, vaName):
        print(f"Parse Assembly {vaName}")




