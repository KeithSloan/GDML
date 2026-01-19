from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLPartShell(GDMLsolid):  # GDMLsolid ?

    def __init__(self, obj, path):
        super().__init__(obj)
        import os
        obj.addProperty(
            "App::PropertyString", "path", "GDMLShellPart", "directory path"
        ).path = path
        obj.Proxy = self
        self.Type = "GDMLPartShell"
        obj.Proxy.Type = "GDMLPartShell"
        self.Object = obj
        loadShape = Part.Shape()
        loadShape.read(path)
        self.Object.Shape = loadShape


    # def execute(self, fp): in GDMLsolid

    def onChanged(self, fp, prop):
        """Do something when a property has changed"""
        # print(fp.Label+" State : "+str(fp.State)+" prop : "+prop)
        # Changing Shape in createGeometry will redrive onChanged
        if "Restore" in fp.State:
            return

        if prop in ["path"]:
            print(f"path changed : {fp.path}")

    def createGeometry(self, fp):
        print('createGeometry')
