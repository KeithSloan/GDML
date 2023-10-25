#
#   PhysVolDict
#
#   Dictionary of Physical Volume
#
#   Used by Border surfaces, expand Command
#

class physVolDict:

    def __init__(self):
        self.volDict = {}

    def addEntry(self, pvName, vol):
        self.volDict[pvName] = vol

    def lookUp(self, pvName):
        return self.volDict[pvName]

    def reBuild(self):
        # Rebuild volDict from current document
        print("Rebuild volDict from current document")

    def printDict(self):
        print(f"PhysVolDict {self.volDict}")

