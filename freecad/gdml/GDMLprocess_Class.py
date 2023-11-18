#.from GDMLlxml import gdml_lxml
from GDMLlxml import gdml_lxml

class processGDML(gdml_lxml):
    def __init__(self, filePath, option=1):
        super().__init__(filePath)
        self.filePath = filePath
        self.option = option

    def processFile(self):
        print(f"Process GDML File {self.filePath} Option {self.option}")
        self.parseFile()
        self.setupEtree()
