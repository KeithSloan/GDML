from operator import indexOf
import FreeCAD, FreeCADGui, Part
import math
from . import GDMLShared

class GDMLopticalsurface(GDMLcommon):
    def __init__(self, obj, name, model, finish, typeVal, value):
        super().__init__(obj)
        print(f"passed name {name} model {model} finish {finish} type {typeVal}")
        obj.addProperty(
            "App::PropertyEnumeration", "model", "GDMLoptical", "model"
        )
        self.modelList = [
            "glisur",   # 0 original GEANT3 model
            "unified",  # 1 UNIFIED model
            "LUT",      # 2 Look-Up-Table model (LBNL model)
            "DAVIS",    # 3 DAVIS model
            "dichroic"  # 4 dichroic filter
        ]
        obj.model = self.modelList
        # Set passed value
        if model.isnumeric():
            obj.model = self.modelList[int(model)]
        else:
            obj.model = model

        # finish    
        obj.addProperty(
            "App::PropertyEnumeration", "finish", "GDMLoptical" "finish"
        )
        self.finish = [
            "polished",             # 0  smooth perfectly polished  surface
            "polishedfrontpainted", # 1  smooth top - layer(front)  paint
            "polishedbackpainted",  # 2  same is 'polished' but with a back-paint

            "ground",               # 3 rough surface
            "groundfrontpainted",   # 4 rough top-layer (front) paint
            "groundbackpainted",    # 5 same as 'ground' but with a back-paint

            # for LBNL LUT model
            "polishedlumirrorair",  # 6 mechanically polished surface, with lumirror
            "polishedlumirrorglue", # 7 mechanically polished surface, with lumirror & meltmount
            "polishedair",          # 8 mechanically polished surface
            "polishedteflonair",    # 9 mechanically polished surface, with teflon
            "polishedtioair",       # 10 mechanically polished surface, with tio paint
            "polishedtyvekair",     # 11 mechanically polished surface, with tyvek
            "polishedvm2000air",    # 12 mechanically polished surface, with esr film
            "polishedvm2000glue",   # 13 mechanically polished surface, with esr film & meltmount

            "etchedlumirrorair",    # 14 chemically etched surface, with lumirror
            "etchedlumirrorglue",   # 15 chemically etched surface, with lumirror & meltmount
            "etchedair",            # 16 chemically etched surface
            "etchedteflonair",      # 17 chemically etched surface, with teflon
            "etchedtioair",         # 18 chemically etched surface, with tio paint
            "etchedtyvekair",       # 19 chemically etched surface, with tyvek
            "etchedvm2000air",      # 20 chemically etched surface, with esr film
            "etchedvm2000glue",     # 21 chemically etched surface, with esr film & meltmount

            "groundlumirrorair",    # 22 rough-cut surface, with lumirror
            "groundlumirrorglue",   # 23 rough-cut surface, with lumirror & meltmount
            "groundair",            # 24 rough-cut surface
            "groundteflonair",      # 25 rough-cut surface, with teflon
            "groundtioair",         # 26 rough-cut surface, with tio paint
            "groundtyvekair",       # 27 rough-cut surface, with tyvek
            "groundvm2000air",      # 28 rough-cut surface, with esr film
            "groundvm2000glue",     # 29 rough-cut surface, with esr film & meltmount

            # for DAVIS model
            "Rough_LUT",            # 30 rough surface
            "RoughTeflon_LUT",      # 31 rough surface wrapped in Teflon tape
            "RoughESR_LUT",         # 32 rough surface wrapped with ESR
            "RoughESRGrease_LUT",   # 33 rough surface wrapped with ESR
                                    # and coupled with optical grease
            "Polished_LUT",         # 34 polished surface
            "PolishedTeflon_LUT",   # 35 polished surface wrapped in Teflon tape
            "PolishedESR_LUT",      # 36 polished surface wrapped with ESR
            "PolishedESRGrease_LUT", # 37 polished surface wrapped with ESR
                                     # and coupled with optical grease
            "Detector_LUT"           # 38 polished surface with optical grease
        ]
        obj.finish = self.finish
        if finish.isnumeric():
            obj.finish = self.finish[int(finish)]
        else:
            obj.finish = finish

        obj.addProperty(
            "App::PropertyEnumeration", "type", "GDMLoptical", "type"
        )
        self.type = [                  # enum G4SurfaceType
            "dielectric_metal",       # dielectric-metal interface
            "dielectric_dielectric",  # dielectric-dielectric interface
            "dielectric_LUT",         # dielectric-Look-Up-Table interface
            "dielectric_LUTDAVIS",    # dielectric-Look-Up-Table DAVIS interface
            "dielectric_dichroic",    # dichroic filter interface
            "firsov",                 # for Firsov Process
            "x_ray",                  # for x-ray mirror process
            "coated",                 # coated_dielectric-dielectric interface
        ]
        obj.type = self.type
        if typeVal.isnumeric():
            obj.type = self.type[int(typeVal)]
        else:
            obj.type = typeVal

        obj.addProperty(
            "App::PropertyFloat", "value", "GDMLoptical"
        ).value = value
        obj.Proxy = self

    def onChanged(self, fp, prop):
        if prop in ["finishNum", "typeNum", "modelNum"]:
            print(f"property {prop} is no longer supported. Please adjust property {prop[:-3]}")
