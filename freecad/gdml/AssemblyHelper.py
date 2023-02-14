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
#       is encountered
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

from .exportGDML import isAssembly, assemblyHeads


class AssemblyHelper:
    maxWww = 0

    def __init__(self, assemblyVol, instCount, imprNum):
        self.assemblyVol = assemblyVol
        self.xxx = imprNum
        self.www = instCount
        if self.www > AssemblyHelper.maxWww:
            AssemblyHelper.maxWww = instCount
        self.solids = []

    def addSolid(self, obj):
        self.solids.append(obj)

    def getPVname(self, obj, idx):
        from .exportGDML import getVolumeName

        if hasattr(obj, "LinkedObject"):
            obj = obj.LinkedObject
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


class AssemblyTreeNode:
    from .exportGDML import assemblyHeads

    def __init__(self, assemObj, parent):
        self.parent = parent
        self.assemObj = assemObj
        self.assemHeads = assemblyHeads(assemObj)
        self.left_child = None
        self.right_sibling = None

    def insert(self, assemObj):
        if self.assemObj:
            if assemObj in self.assemblyHeads:
                if self.left_child is None:
                    self.left_child = AssemblyTreeNode(assemObj, self)
                else:
                    self.left_child.insert(assemObj)
            else:
                if self.right_sibling is None:
                    self.right_sibling = AssemblyTreeNode(assemObj, self)
                else:
                    self.right_sibling.insert(assemObj)
        else:
            self.assemObj = assemObj
