from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLFiles(GDMLcommon):
    def __init__(self, obj, FilesEntity, sectionDict):
        super().__init__(obj)
        """Add some custom properties to our Cone feature"""
        GDMLShared.trace("GDML Files")
        GDMLShared.trace(FilesEntity)
        obj.addProperty(
            "App::PropertyBool", "active", "GDMLFiles", "split option"
        ).active = FilesEntity
        obj.addProperty(
            "App::PropertyString", "define", "GDMLFiles", "define section"
        ).define = sectionDict.get("define", "")
        obj.addProperty(
            "App::PropertyString",
            "materials",
            "GDMLFiles",
            "materials section",
        ).materials = sectionDict.get("materials", "")
        obj.addProperty(
            "App::PropertyString", "solids", "GDMLFiles", "solids section"
        ).solids = sectionDict.get("solids", "")
        obj.addProperty(
            "App::PropertyString",
            "structure",
            "GDMLFiles",
            "structure section",
        ).structure = sectionDict.get("structure", "")
        self.Type = "GDMLFiles"
        obj.Proxy = self
        obj.Proxy.Type = "GDMLFiles"

    def execute(self, fp):
        """Do something when doing a recomputation, this method is mandatory"""
        pass

    def onChanged(self, fp, prop):
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # if not ('Restore' in fp.State) :
        #   if not hasattr(fp,'onchange') or not fp.onchange : return
        pass
