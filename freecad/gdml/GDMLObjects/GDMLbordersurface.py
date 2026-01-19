from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLbordersurface(GDMLcommon):
    '''
    In gdml the bordersurface takes the name of a surface and the name of two physvols
    that are the placement of two volumes that contain the solids whose surfaces have
    a common border. In FreeCAD we do not have an object that corresponds directly
    to a physvol. We have an App::Part object that results in the creation of two gdml
    objects: (1) a <volume and (2) a <physvol. Usually, but not always, the name of the
    <volume is the Label of the App::Part. Usually, but not always, the name of the physvol
    is PV- + App::Part.Label. Because it is not always the case that the physvols do not have
    the usual names, the GDMLbordersurface does NOT store the physvol name, but rather
    the App::Part object that will, eventually, on export, result in a <physvol. We do not
    apriori know the name of that physvol. So the properties PV1 and PV2 below are NOT,
    strictly speaking physvols, they are the App::Parts that will result in the export of a physvol
    '''
    def __init__(self, obj, name, surface, pv1, pv2, check):
        super().__init__(obj)
        # print(f'pv1 : {pv1} pv2 : {pv2}')
        obj.addProperty(
            "App::PropertyString", "Surface", "GDMLborder", "surface property"
        ).Surface = surface
        obj.addProperty(
            "App::PropertyBool",
            "CheckCommonFaces",
            "GDMLborder",
            "Perform check of common faces on export",
        )
        obj.CheckCommonFaces = check
        obj.addProperty(
            "App::PropertyLinkGlobal", "PV1", "GDMLborder", "physvol PV1"
        ).PV1 = pv1
        obj.setEditorMode("PV1", 1)
        obj.addProperty(
            "App::PropertyLinkGlobal", "PV2", "GDMLborder", "physvol PV2"
        ).PV2 = pv2
        obj.setEditorMode("PV2", 1)
        obj.Proxy = self
        self.Object = obj
