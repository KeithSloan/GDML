from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLcomposite(GDMLcommon):
    def __init__(self, obj, name, n, ref):
        super().__init__(obj)

        obj.addProperty("App::PropertyInteger", "n", "Base").n = n
        obj.addProperty("App::PropertyString", "ref", "Base").ref = ref

        obj.Proxy = self
        self.Object = obj

        self._updatingLabel = False

        # set initial label
        obj.Label = self.makeLabel(obj)

    def makeLabel(self, obj):
        return f"{obj.ref} : {obj.n}"

    def onChanged(self, obj, prop):
        if prop in ("Label", "n", "ref"):
            if self._updatingLabel:
                return

            self._updatingLabel = True
            try:
                newLabel = self.makeLabel(obj)
                if obj.Label != newLabel:
                    obj.Label = newLabel
            finally:
                self._updatingLabel = False
