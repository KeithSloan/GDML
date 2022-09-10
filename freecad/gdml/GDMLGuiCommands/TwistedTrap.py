import FreeCAD, FreeCADGui
from PySide import QtGui, QtCore

class TwistedTrapFeature:

    def Activated(self):
        from .propertiesDialog import propertiesDialog
        from ..GDMLCommands import getSelectedPM
        from ..GDMLObjects import GDMLTwistedtrap, ViewProvider
        objPart, material = getSelectedPM()
        if objPart is None:
            vol = FreeCAD.ActiveDocument.addObject("App::Part", "LV-TwistTrap")
        else:
            vol = objPart.newObject("App::Part", "LV-TwistTrap")
        obj = vol.newObject("Part::FeaturePython", "GDMLTwistTrap_Trap")
        # obj, PhiTwist, z, theta, phi, x1, x2, x3, x4, y1, y2,
        #         alpha, aunit, lunit, material
        GDMLTwistedtrap(obj, 30.0, 10.0, 20.0, 20.0, 10.0, 10.0, 10.0, 10.0,
                        10.0, 10.0, 25.0, "deg", "mm", material)
        dialog = propertiesDialog(obj, 'Twisted Trap', 'image.jpg')
        dialog.exec_()
        if dialog.retStatus == 1:
           ViewProvider(obj.ViewObject)
        if dialog.retStatus == 2:
           FreeCAD.ActiveDocument.removeObject(vol.Name)
           FreeCAD.ActiveDocument.removeObject(obj.Name)
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def GetResources(self):
        return {'Pixmap': 'GDMLTwistedTrapFeature', 'MenuText':
                QtCore.QT_TRANSLATE_NOOP('GDMLTwistedTrapFeature',
                                         'Twisted Trap Object'), 'ToolTip':
                QtCore.QT_TRANSLATE_NOOP('GDMLTwistedTrapFeature',
                                         'Twisted Trap Object')}

FreeCADGui.addCommand('TwistedTrap', TwistedTrapFeature())
