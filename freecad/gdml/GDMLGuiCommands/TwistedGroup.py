# ****************************************************************
# * Twisted Group of Commands

from PySide.QtCore import QT_TRANSLATE_NOOP

import FreeCAD, FreeCADGui

from . import TwistedBox
from . import TwistedTrap
#import TwistedTrd
#import TwistedTubs  

class TwistedGroup:
    """ Group of Twisted Commands """

    def GetCommands(self):
        """ Tuple of Commands"""
        return("TwistedTrap","TwistedBox","TwistedTrd","TwistedTubs")
        #return("TwistedBox","TwistedTrap","TwistedTrd","TwistedTubs")

    def GetResources(self):
        """Set icon, menu and tooltip."""

        return {'Pixmap': 'Twisted_Group',
                'MenuText': QT_TRANSLATE_NOOP("Twist Group", "Twist Group"),
                'ToolTip': QT_TRANSLATE_NOOP("Twist Group", " Group of Twisted Commands")}

    def IsActive(self):
        """Return True when this command should be available."""
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

FreeCADGui.addCommand('TwistedCommands', TwistedGroup())

