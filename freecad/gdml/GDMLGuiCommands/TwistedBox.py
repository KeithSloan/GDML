import FreeCAD, FreeCADGui
from PySide import QtGui, QtCore

class TwistedBoxFeature:

    def Activated(self):
        from ..GDMLCommands import getSelectedPM
        from ..GDMLObjects import GDMLTwistedbox, ViewProvider
        objPart, material = getSelectedPM()
        if objPart is None:
            vol = FreeCAD.ActiveDocument.addObject("App::Part", "LV-TwistBox")
        else:
            vol = objPart.newObject("App::Part", "LV-TwistBox")
        obj = vol.newObject("Part::FeaturePython", "GDMLTwistBox_Box")
        # self, obj, PhiTwist, x, y, z, aunit, lunit, material, colour=None)
        GDMLTwistedbox(obj, 20.0, 10.0, 10.0, 10.0, "deg", "mm", material)
        # print("GDMLBox initiated")
        ViewProvider(obj.ViewObject)
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {'Pixmap': 'GDMLTwistedBoxFeature', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDMLTwistedBoxFeature',
                                         'Twisted Box Object'), 'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('GDMLTwistedBoxFeature',
                                         'Twisted Box Object')}

FreeCADGui.addCommand('TwistedBox',TwistedBoxFeature())
