#########################################################
#
#   Assembly dictionary
#
#########################################################
# Geant4 generates its own internal names for the
# physical volumes that are included in the assembly.
# The names are of the form
#
# av_WWW_impr_XXX_YYY_ZZZ
#
# where:
# WWW - assembly volume instance number. I gather this is a number that starts
#       at 1 when the first assembly structure is encountered in the gdml file
#       and then is incremented by one every time a new <assembly structure
#       is encounterd
# XXX - assembly volume imprint number. I am not sure what this is. I assume that
#       a given assembly can be placed inside several logical volume mothers
#       and that the imprint number keeps track of how many times the one and same
#       assembly has been placed. For now I am going to take this as 1. I.e, no more
#       than one placement for each assembly
# YYY - the name of the placed logical volume. geant seems to append an '_pv'
#       to out generated logical volume names, which for current exportGDML is
#        'V-' + copied solid name
# ZZZ - the logical volume index inside the assembly volume. This is a counter
#       that increases sequentially with the number of solids in the assembly
# to keep track of what a bordersurface is replaced by we use the following
# dictionaries. Each has as key the name of the App::Part  that appears
# in the PV1, PV2 properties of the bordersurface


class Assembly:
    instCount = 0
    imprCount = 0
    ignore = ["App::Origin"]

    def __init__(self, name, ObjList):
        Assembly.instCount += 1
        Assembly.imprCount += 1
        print(f"Assemmbly {name} {Assembly.instCount} {Assembly.imprCount}")
        self.name = name
        self.list = ObjList
        self.xxx = Assembly.imprCount
        self.www = Assembly.instCount

    def resetCounts(self):
        Assembly.instCount = 0
        Assembly.imprCount = 0

    def incrementImpression(self):
        Assembly.imprCount += 1

    def indexName(self, name):
        idx = 0
        for obj in self.list:
            if obj.Name == name:
                return idx
            if obj.TypeId not in Assembly.ignore:
                idx += 1
        return None

    def printList(self):
        print(f"List {self.name} >>>>>>>")
        for obj in self.list:
            print(obj.Name)
        print(f"List {self.name} <<<<<<<<")

    def printInfo(self):
        print(f"Entry {self.name} www {self.www} xxx {self.xxx}")

    def getPVname(self, obj):
        from .exportGDML import getVolumeName

        self.printInfo()
        # self.printList()
        idx = self.indexName(obj.Name)
        if hasattr(obj, "LinkedObject"):
            obj = obj.LinkedObject
        print(f"zzz {idx} should be one less than CopyNumber")
        return (
            "av_"
            + str(self.www)
            + "_impr_"
            + str(self.xxx)
            + "_"
            + getVolumeName(obj)
            + "_pv_"
            + str(idx)
        )
