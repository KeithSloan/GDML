from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class ViewProviderExtension(GDMLcommon):
    def __init__(self, obj):
        super().__init__(obj)
        obj.addExtension("Gui::ViewProviderGroupExtensionPython")
        obj.Proxy = self

    def getDisplayModes(self, obj):
        """Return a list of display modes."""
        modes = []
        modes.append("Shaded")
        modes.append("Wireframe")
        modes.append("Points")
        return modes

    def updateData(self, fp, prop):
        """If a property of the handled feature has changed we have the chance to handle this here"""
        # fp is the handled feature, prop is the name of the property that has changed
        # l = fp.getPropertyByName("Length")
        # w = fp.getPropertyByName("Width")
        # h = fp.getPropertyByName("Height")
        # self.scale.scaleFactor.setValue(float(l),float(w),float(h))
        pass

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode. It must be defined in getDisplayModes."""
        return "Shaded"
