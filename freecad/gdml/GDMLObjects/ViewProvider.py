from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class ViewProvider(GDMLcommon):
    def __init__(self, obj):
        super().__init__(obj)
        """Set this object to the proxy object of the actual view provider"""
        obj.Proxy = self

    def updateData(self, fp, prop):
        """If a property of the handled feature has changed we have the chance to handle this here"""
        # print("updateData")
        # fp is the handled feature, prop is the name of the property that has changed
        # l = fp.getPropertyByName("Length")
        # w = fp.getPropertyByName("Width")
        # h = fp.getPropertyByName("Height")
        # self.scale.scaleFactor.setValue(float(l),float(w),float(h))
        pass

    def setTransparency(self, obj, value):
        obj.ViewObject.Transparency = value

    def getDisplayModes(self, obj):
        """Return a list of display modes."""
        # print("getDisplayModes")
        modes = []
        modes.append("Shaded")
        modes.append("Wireframe")
        modes.append("Points")
        return modes

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode. It must be defined in getDisplayModes."""
        return "Shaded"

    def setDisplayMode(self, mode):
        """Map the display mode defined in attach with those defined in getDisplayModes.\
               Since they have the same names nothing needs to be done. This method is optional"""
        return mode

    def onChanged(self, vp, prop):
        """Here we can do something when a single property got changed"""
        # if hasattr(vp,'Name') :
        #   print("View Provider : "+vp.Name+" State : "+str(vp.State)+" prop : "+prop)
        # else :
        #   print("View Provider : prop : "+prop)
        # GDMLShared.trace("Change property: " + str(prop) + "\n")
        # if prop == "Color":
        #    c = vp.getPropertyByName("Color")
        #    self.color.rgb.setValue(c[0],c[1],c[2])

    def getIcon(self):
        """Return the icon in XPM format which will appear in the tree view. This method is\
               optional and if not defined a default icon is shown."""
        return """
           /* XPM */
           static const char * ViewProviderBox_xpm[] = {
           "16 16 6 1",
           "   c None",
           ".  c #141010",
           "+  c #615BD2",
           "@  c #C39D55",
           "#  c #000000",
           "$  c #57C355",
           "        ........",
           "   ......++..+..",
           "   .@@@@.++..++.",
           "   .@@@@.++..++.",
           "   .@@  .++++++.",
           "  ..@@  .++..++.",
           "###@@@@ .++..++.",
           "##$.@@$#.++++++.",
           "#$#$.$$$........",
           "#$$#######      ",
           "#$$#$$$$$#      ",
           "#$$#$$$$$#      ",
           "#$$#$$$$$#      ",
           " #$#$$$$$#      ",
           "  ##$$$$$#      ",
           "   #######      "};
           """

    def __getstate__(self):
        """When saving the document this object gets stored using Python's json module.\
               Since we have some un-serializable parts here -- the Coin stuff -- we must define this method\
               to return a tuple of all serializable objects or None."""
        return None

    def __setstate__(self, state):
        """When restoring the serialized object from document we have the chance to set some internals here.\
               Since no data were serialized nothing needs to be done here."""
        return None
