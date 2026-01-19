from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLfraction(GDMLcommon):
    def __init__(self, obj, ref, n):
        super().__init__(obj)

        obj.addProperty("App::PropertyString", "ref", "Base")
        obj.ref = ref
        obj.addProperty("App::PropertyQuantity", "n", "Base")
        obj.n = FreeCAD.Units.Quantity(n)
        obj.Proxy = self
        self.Object = obj

        self._updatingLabel = False

        # set initial label
        obj.Label = self.makeLabel(obj)

    def makeLabel(self, obj):
        return f"{obj.ref} : {float(obj.n):.4f}"

    def onChanged(self, obj, prop):
        # React to both label edits and property edits
        if prop in ("Label", "n"):
            if self._updatingLabel:
                return

            self._updatingLabel = True
            try:
                newLabel = self.makeLabel(obj)
                if obj.Label != newLabel:
                    obj.Label = newLabel
            finally:
                self._updatingLabel = False
