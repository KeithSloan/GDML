# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2026 Keith Sloan <keithsloan52@icloud.com>             *
# *                                                                        *
# *   This program is free software; you can redistribute it and/or modify *
# *   it under the terms of the GNU Lesser General Public License (LGPL)   *
# *   as published by the Free Software Foundation; either version 2 of    *
# *   the License, or (at your option) any later version.                  *
# *   for detail see the LICENCE text file.                                *
# *                                                                        *
# **************************************************************************
"""GDMLDesign - a scripting API for building GDML geometry in FreeCAD.

Written so that a person or an AI assistant (e.g. via the FreeCAD MCP
execute_code tool) can build a Geant4 geometry with short, checked calls.
Every function validates its input and raises ValueError/RuntimeError with
a message saying what to do instead - nothing is silently defaulted.

Quick start::

    from freecad.gdml import GDMLDesign as gd

    gd.newDocument("Calorimeter")
    gd.listMaterials("PbWO")                      # -> ['G4_PbWO4']
    gd.addMaterial("Scint", "1.032 g/cm3", formula="C9H10")

    # 5 x 5 array of crystals in an assembly
    calo = gd.makeAssembly("Calo")
    xtal = gd.makeBox(22, 22, 230, material="G4_PbWO4", name="Crystal",
                      parent=calo, position=(-48, -48, 0))
    for i in range(5):
        for j in range(5):
            if i or j:
                gd.placeCopy(xtal, parent=calo,
                             position=(-48 + 24 * i, -48 + 24 * j, 0),
                             copynumber=5 * i + j)

    # A lead block with a hole through it
    block = gd.makeBox(100, 100, 50, material="G4_Pb", name="Collimator",
                       position=(0, 0, 300))
    hole = gd.makeTube(0, 5, 60, material="G4_Pb")
    gd.makeSubtraction(block, hole)             # hole keeps its placement

    print(gd.designTree())
    gd.exportGDML("~/calorimeter.gdml")          # grows world to fit

Conventions:
  * Solid dimensions follow the GDML element of the same name (box x/y/z are
    FULL lengths, eltube dx/dy/dz HALF lengths - see each make* docstring).
  * lunit defaults to "mm", aunit to "deg". position uses the call's lunit.
  * rotation=(rx, ry, rz) degrees about fixed X, then Y, then Z, or
    ((ax, ay, az), angle_deg), or a FreeCAD.Rotation.  It is the rotation
    you see in FreeCAD; the exporter converts to GDML's convention.
  * make* return the solid; getVolume(solid) gives its logical volume.
  * apiSummary() lists every function with its signature.
"""

import os
import re

import FreeCAD

from . import GDMLObjects as _G
from .GDMLObjects import (  # noqa: F401  (re-exported for one-import use)
    getWorld,
    getVolume,
    getSolid,
    makeArb8,
    makeBox,
    makeCone,
    makeCutTube,
    makeElCone,
    makeEllipsoid,
    makeElTube,
    makeGenericPolycone,
    makeGenericPolyhedra,
    makeHype,
    makeOrb,
    makePara,
    makeParaboloid,
    makePolycone,
    makePolyhedra,
    makeSphere,
    makeTessellated,
    makeTetra,
    makeTorus,
    makeTrap,
    makeTrd,
    makeTube,
    makeTwistedBox,
    makeTwistedTrap,
    makeTwistedTrd,
    makeTwistedTubs,
    makeXtru,
)

__all__ = [
    # document / world
    "newDocument", "getWorld", "setWorldSize", "fitWorld",
    # solids (each in its own logical volume)
    "makeArb8", "makeBox", "makeCone", "makeCutTube", "makeElCone",
    "makeEllipsoid", "makeElTube", "makeGenericPolycone",
    "makeGenericPolyhedra", "makeHype", "makeOrb", "makePara",
    "makeParaboloid", "makePolycone", "makePolyhedra", "makeSphere",
    "makeTessellated", "makeTetra", "makeTorus", "makeTrap", "makeTrd",
    "makeTube", "makeTwistedBox", "makeTwistedTrap", "makeTwistedTrd",
    "makeTwistedTubs", "makeXtru",
    # booleans
    "makeSubtraction", "makeUnion", "makeIntersection",
    # structure
    "makeAssembly", "placeCopy", "removeVolume", "setSensitive",
    "getVolume", "getSolid",
    # materials
    "listMaterials", "addMaterial", "assignMaterial",
    # inspection / output
    "describe", "designTree", "exportGDML", "apiSummary",
]

_MASS_UNITS = ("kg", "g", "mg")
_VOLUME_UNITS = ("mm3", "cm3", "m3")


_checkName = _G._checkName


def _round(v, n=6):
    return round(float(v), n) + 0.0  # + 0.0 turns -0.0 into 0.0


def _placementInfo(pl):
    rz, ry, rx = pl.Rotation.toEuler()  # yaw(Z), pitch(Y), roll(X)
    return {
        "position_mm": tuple(_round(c) for c in pl.Base),
        "rotation_xyz_deg": (_round(rx), _round(ry), _round(rz)),
    }


# ---------------------------------------------------------------------------
#   Document and world
# ---------------------------------------------------------------------------
def newDocument(name="GDML_Design", worldSize=None, lunit="mm",
                worldMaterial="G4_AIR"):
    """Create a new GDML document (materials + world volume) and make it
    active.  worldSize=(x, y, z) full lengths in lunit; default keeps the
    100 mm template world - use fitWorld() (exportGDML does it for you)."""
    doc = FreeCAD.newDocument(name)
    doc = _G._getDoc(doc)  # activates and adds the GDML structure
    world = getWorld(doc)
    if worldSize is not None:
        setWorldSize(*worldSize, lunit=lunit, doc=doc)
    if worldMaterial is not None:
        assignMaterial(world, worldMaterial)
    doc.recompute()
    return doc


def _worldSolid(doc):
    world = getWorld(doc)
    solid = getSolid(world) if world is not None else None
    if solid is None or getattr(solid.Proxy, "Type", "") != "GDMLBox":
        raise RuntimeError("World volume has no GDMLBox solid to resize")
    return solid


def setWorldSize(x, y, z, lunit="mm", doc=None):
    """Set the world box to full lengths x, y, z (in lunit)."""
    _G._checkUnit(lunit=lunit)
    _G._checkPositive(x=x, y=y, z=z)
    doc = _G._getDoc(doc)
    box = _worldSolid(doc)
    _G.setLengthQuantity(box, lunit)
    box.x, box.y, box.z = float(x), float(y), float(z)
    box.recompute()
    return box


def _bbox(obj, mat, claimed):
    """BoundBox (in the frame given by matrix mat) of obj and contents."""
    bb = FreeCAD.BoundBox()
    if obj in claimed:  # boolean operand - the boolean result counts
        return bb
    if obj.TypeId == "App::Part":
        m = mat * obj.Placement.toMatrix()
        inner = set(claimed)
        for o in obj.Group:
            if o.TypeId in _G._BOOLEAN_TYPES:
                inner.update([o.Base, o.Tool])
        for o in obj.Group:
            bb.add(_bbox(o, m, inner))
    elif obj.TypeId == "App::Link":
        linked = obj.LinkedObject
        if linked is not None and linked.TypeId == "App::Part":
            m = mat * obj.Placement.toMatrix()
            # The link replaces the linked part's own placement
            inner = set()
            for o in linked.Group:
                if o.TypeId in _G._BOOLEAN_TYPES:
                    inner.update([o.Base, o.Tool])
            for o in linked.Group:
                bb.add(_bbox(o, m, inner))
    elif hasattr(obj, "Shape"):
        shape = obj.Shape
        if shape.isNull() and getattr(obj, "GmshShape", None) is not None:
            shape = obj.GmshShape
        if not shape.isNull():
            bb.add(shape.BoundBox.transformed(mat))
    return bb


def _contentBoundBox(doc):
    world = getWorld(doc)
    wsolid = getSolid(world)
    bb = FreeCAD.BoundBox()
    for o in world.Group:
        if o is wsolid:
            continue
        bb.add(_bbox(o, FreeCAD.Matrix(), set()))
    return bb


def fitWorld(margin=1.2, growOnly=False, doc=None):
    """Resize the world box (centred on the origin) to enclose every
    volume times margin.  growOnly=True never shrinks it.
    Returns the new (x, y, z) in mm, or None if the world is empty."""
    doc = _G._getDoc(doc)
    box = _worldSolid(doc)
    bb = _contentBoundBox(doc)
    if not bb.isValid():
        return None
    need = [
        2 * max(abs(bb.XMin), abs(bb.XMax)) * margin,
        2 * max(abs(bb.YMin), abs(bb.YMax)) * margin,
        2 * max(abs(bb.ZMin), abs(bb.ZMax)) * margin,
    ]
    mul = _G._LUNIT_TO_MM[box.lunit]
    cur = [box.x * mul, box.y * mul, box.z * mul]
    if growOnly:
        if all(n <= c for n, c in zip(need, cur)):
            return tuple(cur)
        need = [max(n, c) for n, c in zip(need, cur)]
    box.x, box.y, box.z = (v / mul for v in need)
    box.recompute()
    return tuple(need)


# ---------------------------------------------------------------------------
#   Materials
# ---------------------------------------------------------------------------
def listMaterials(pattern=None, doc=None):
    """Names usable as material=... .  pattern: case-insensitive substring,
    or a glob such as 'G4_*GLASS*'."""
    import fnmatch

    _G._getDoc(doc)
    _G._refreshMaterialsList()
    names = list(_G.MaterialsList)
    if pattern:
        p = pattern.lower()
        if any(c in p for c in "*?["):
            names = [n for n in names if fnmatch.fnmatch(n.lower(), p)]
        else:
            names = [n for n in names if p in n.lower()]
    return names


def _parseDensity(density):
    if isinstance(density, (int, float)):
        value, unit = float(density), "g/cm3"
    else:
        words = str(density).split()
        if len(words) == 1:
            value, unit = float(words[0]), "g/cm3"
        elif len(words) == 2:
            value, unit = float(words[0]), words[1]
        else:
            raise ValueError(f"density '{density}': use e.g. '8.96 g/cm3'")
    parts = unit.split("/")
    if len(parts) != 2 or parts[0] not in _MASS_UNITS \
            or parts[1] not in _VOLUME_UNITS:
        raise ValueError(
            f"density unit '{unit}': mass in {_MASS_UNITS} / volume in "
            f"{_VOLUME_UNITS}, e.g. 'g/cm3'"
        )
    if value <= 0:
        raise ValueError("density must be > 0")
    return value, unit


def addMaterial(name, density, formula=None, mixture=None, doc=None):
    """Define a new material (same result as the GDML 'Add material' dialog).

    density : number (g/cm3) or string such as '7.8 g/cm3', '2700 kg/m3'.
    formula : chemical formula by atom count, e.g. 'H2O', 'C9H10',
              '(CH3)2(C8H8)5'.
    mixture : mass fractions of existing materials and/or element symbols,
              as a dict {'G4_Cu': 0.7, 'G4_Zn': 0.3} or a string
              '0.7 G4_Cu + 0.3 G4_Zn'.  Fractions are renormalised to 1.
    Give exactly one of formula / mixture.  Returns the material object."""
    from .formula_parser import parse_chemical_formula, recognized_elements
    from .GDMLObjects import (
        GDMLcomposite,
        GDMLfraction,
        GDMLmaterial,
        markMaterialsListDirty,
    )
    from .importGDML import newGroupPython

    doc = _G._getDoc(doc)
    _checkName(name)
    if (formula is None) == (mixture is None):
        raise ValueError("give exactly one of formula=... or mixture=...")
    if doc.getObjectsByLabel(name):
        raise ValueError(f"'{name}' already exists in {doc.Name}")
    dvalue, dunit = _parseDensity(density)
    matGrp = doc.getObject("Materials")

    if formula is not None:
        comp = parse_chemical_formula(formula)
        if not comp:
            raise ValueError(f"could not parse formula '{formula}'")
        bad = [e for e in comp if e not in recognized_elements]
        if bad:
            raise ValueError(f"unknown element(s) {bad} in '{formula}'")
        mat = newGroupPython(matGrp, name)
        GDMLmaterial(mat, name)
        mat.addProperty("App::PropertyString", "formula", name).formula = \
            formula
        for elem, n in comp.items():
            ref = elem + "_element"
            c = newGroupPython(mat, ref)
            GDMLcomposite(c, "comp", int(n), ref)
            c.Label = f"{ref} : {int(n)}"
    else:
        if isinstance(mixture, str):
            from .GDMLCommands import QMAT_PATTERN

            pairs = re.findall(QMAT_PATTERN, mixture)
            if not pairs:
                raise ValueError(
                    f"could not parse mixture '{mixture}', "
                    "use e.g. '0.7 G4_Cu + 0.3 G4_Zn'"
                )
            mixture = {m: float(f) for f, m in pairs}
        resolved = {}
        usedSymbols = False
        for comp_name, frac in mixture.items():
            frac = float(frac)
            if frac <= 0:
                raise ValueError(f"fraction for {comp_name} must be > 0")
            if doc.getObjectsByLabel(comp_name):
                resolved[comp_name] = frac
            elif comp_name in recognized_elements:
                resolved[comp_name + "_element"] = frac
                usedSymbols = True
            else:
                raise ValueError(
                    f"mixture component '{comp_name}' is not a defined "
                    "material/element or an element symbol; see "
                    "listMaterials()"
                )
        total = sum(resolved.values())
        mat = newGroupPython(matGrp, name)
        GDMLmaterial(mat, name)
        for ref, frac in resolved.items():
            f = frac / total
            fo = newGroupPython(mat, ref)
            GDMLfraction(fo, ref, f)
            fo.Label = f"{ref} : {f:0.3f}"
        if usedSymbols:
            # as the dialog does when element symbols are used
            FreeCAD.ParamGet(
                "User parameter:BaseApp/Preferences/Mod/GDML"
            ).SetBool("exportG4Materials", True)

    mat.addProperty("App::PropertyFloat", "Dvalue", "GDMLmaterial",
                    "value").Dvalue = dvalue
    mat.addProperty("App::PropertyString", "Dunit", "GDMLmaterial",
                    "Dunit").Dunit = dunit
    markMaterialsListDirty()
    return mat


def _materialHolders(obj):
    """GDML solids whose material property defines obj's material."""
    if obj.TypeId in ("App::Part", "App::Link"):
        if obj.TypeId == "App::Link":
            obj = obj.LinkedObject
        solid = getSolid(obj)
        if solid is None:
            raise ValueError(f"'{obj.Label}' has no solid (assembly?)")
        obj = solid
    while obj.TypeId in _G._BOOLEAN_TYPES:
        obj = obj.Base  # exportGDML takes a boolean's material from Base
    if not hasattr(obj, "material"):
        raise ValueError(f"'{obj.Label}' has no material property")
    return obj


def assignMaterial(obj, material):
    """Set the material of a solid, boolean or volume (validated)."""
    target = _materialHolders(obj)
    _G._getDoc(target.Document)
    material = _G._resolveMaterial(material)
    _G.setMaterial(target, material)
    if target.material != material:
        raise RuntimeError(f"could not set material {material}")
    return target


# ---------------------------------------------------------------------------
#   Booleans
# ---------------------------------------------------------------------------
def _boolean(typeId, opName, base, tool, name, position, rotation, lunit):
    for o, role in ((base, "base"), (tool, "tool")):
        if not _G._isSolidLike(o):
            raise ValueError(
                f"{role} '{o.Label}' must be a solid returned by a make* "
                "function or a previous boolean"
            )
    doc = _G._getDoc(base.Document)
    baseVol, toolVol = getVolume(base), getVolume(tool)
    if baseVol is toolVol:
        raise ValueError("base and tool are already in the same volume")
    for solid, vol in ((base, baseVol), (tool, toolVol)):
        if getSolid(vol) is not solid:
            raise ValueError(f"'{solid.Label}' is not the top solid of "
                             f"volume '{vol.Label}'")
        if any(o.TypeId in ("App::Part", "App::Link") for o in vol.Group):
            raise ValueError(
                f"volume '{vol.Label}' has daughter volumes; do booleans "
                "before adding daughters"
            )
    links = [o.Label for o in toolVol.InList if o.TypeId == "App::Link"]
    if links:
        raise ValueError(f"tool volume '{toolVol.Label}' is used by copies "
                         f"{links}; it would be deleted")
    if name is not None:
        _checkName(name)
        if doc.getObjectsByLabel(name):
            raise ValueError(f"'{name}' is already used in {doc.Name}")

    if position is None and rotation is None:
        # keep the tool where it is now (what you see is what you get)
        rel = baseVol.getGlobalPlacement().inverse() \
            * toolVol.getGlobalPlacement()
        toolPl = rel * tool.Placement
    else:
        # position/rotation of the tool relative to the base (GDML style)
        toolPl = base.Placement * _G._toPlacement(position, rotation,
                                                  lunit)

    baseVol.addObject(tool)  # moves tool out of toolVol
    if tool.getParentGeoFeatureGroup() is not baseVol:
        toolVol.removeObject(tool)
        baseVol.addObject(tool)
    tool.Placement = toolPl
    if name is not None:
        baseVol.Label = name
    result = baseVol.newObject(typeId, opName.capitalize())
    result.Label = f"{baseVol.Label}_{opName}"
    result.Base = base
    result.Tool = tool
    if FreeCAD.GuiUp:
        result.ViewObject.ShapeColor = base.ViewObject.ShapeColor
        base.ViewObject.Visibility = False
        tool.ViewObject.Visibility = False
    for o in list(toolVol.Group):  # e.g. zplanes of a polycone tool
        baseVol.addObject(o)
    doc.removeObject(toolVol.Name)
    doc.recompute()
    return result


def makeSubtraction(base, tool, name=None, position=None, rotation=None,
                    lunit="mm"):
    """GDML <subtraction>: base minus tool.  base/tool are solids from
    make* (or earlier booleans), each in its own volume.  Without
    position/rotation the tool keeps its current placement; with them the
    tool is placed relative to the base, as in GDML.  The base's volume
    (renamed to name if given) holds the result; the tool's volume is
    deleted.  Returns the boolean solid."""
    return _boolean("Part::Cut", "subtraction", base, tool, name,
                    position, rotation, lunit)


def makeUnion(base, tool, name=None, position=None, rotation=None,
              lunit="mm"):
    """GDML <union> of base and tool - see makeSubtraction."""
    return _boolean("Part::Fuse", "union", base, tool, name, position,
                    rotation, lunit)


def makeIntersection(base, tool, name=None, position=None, rotation=None,
                     lunit="mm"):
    """GDML <intersection> of base and tool - see makeSubtraction."""
    return _boolean("Part::Common", "intersection", base, tool, name,
                    position, rotation, lunit)


# ---------------------------------------------------------------------------
#   Structure: assemblies, copies, sensitive detectors
# ---------------------------------------------------------------------------
def makeAssembly(name, parent=None, position=None, rotation=None,
                 lunit="mm", doc=None):
    """A volume with no solid of its own (GDML <assembly>) to group and
    move daughters together.  Give it at least one daughter."""
    _checkName(name)
    doc = _G._getDoc(doc)
    placement = _G._toPlacement(position, rotation, lunit)
    return _G._newVolume(doc, parent, name, placement)


def placeCopy(volume, parent=None, position=None, rotation=None,
              lunit="mm", name=None, copynumber=None):
    """Place another copy (GDML physvol) of an existing volume, e.g. a
    detector module.  volume: a volume, its solid or a copy of it.
    The original stays where it was created; returns the App::Link."""
    if volume.TypeId == "App::Link":
        volume = volume.LinkedObject
    vol = getVolume(volume)
    doc = _G._getDoc(vol.Document)
    parentVol = _G._resolveVolume(parent, doc)
    p = parentVol
    while p is not None:
        if p is vol:
            raise ValueError("cannot place a volume inside itself")
        p = p.getParentGeoFeatureGroup()
    if name is None:
        i = 1
        while doc.getObjectsByLabel(f"{vol.Label}_copy{i}"):
            i += 1
        name = f"{vol.Label}_copy{i}"
    else:
        _checkName(name)
        if doc.getObjectsByLabel(name):
            raise ValueError(f"'{name}' is already used in {doc.Name}")
    link = parentVol.newObject("App::Link", "Link")
    link.LinkedObject = vol
    link.Label = name
    link.Placement = _G._toPlacement(position, rotation, lunit)
    link.addProperty("App::PropertyString", "VolRef", "GDML",
                     "volref name").VolRef = vol.Label
    if copynumber is not None:
        link.addProperty("App::PropertyInteger", "CopyNumber", "GDML",
                         "copynumber").CopyNumber = int(copynumber)
    if hasattr(link, "Material"):
        link.setEditorMode("Material", 2)
    return link


def setSensitive(volume, detName):
    """Mark a volume as a Geant4 sensitive detector (auxiliary SensDet)."""
    vol = getVolume(volume)
    if not hasattr(vol, "SensDet"):
        vol.addProperty("App::PropertyString", "SensDet", "Base", "SensDet")
    vol.SensDet = str(detName)
    return vol


def removeVolume(volume, force=False):
    """Delete a volume (or copy) and everything inside it.  Refuses if
    copies elsewhere link to it unless force=True (copies removed too)."""
    doc = volume.Document
    if volume.TypeId == "App::Link":
        doc.removeObject(volume.Name)
        return
    vol = getVolume(volume)
    if vol is getWorld(doc):
        raise ValueError("cannot remove the world volume")
    links = [o for o in vol.InList if o.TypeId == "App::Link"]
    if links and not force:
        raise ValueError(
            f"'{vol.Label}' is used by copies "
            f"{[o.Label for o in links]}; pass force=True to remove them"
        )
    for link in links:
        doc.removeObject(link.Name)
    vol.removeObjectsFromDocument()
    doc.removeObject(vol.Name)
    doc.recompute()


# ---------------------------------------------------------------------------
#   Inspection and export
# ---------------------------------------------------------------------------
_SKIP_PROPS = {"material", "lunit", "aunit"}


def _solidParams(obj):
    params = {}
    for p in obj.PropertiesList:
        if p in _SKIP_PROPS or not obj.getGroupOfProperty(p).startswith(
                "GDML"):
            continue
        v = getattr(obj, p)
        if isinstance(v, FreeCAD.Vector):
            v = tuple(_round(c) for c in v)
        elif isinstance(v, float):
            v = _round(v)
        params[p] = v
    zplanes, rz, verts, secs = [], [], [], []
    for c in getattr(obj, "Group", []):
        if hasattr(c, "rmax") and hasattr(c, "z"):
            zplanes.append((c.rmin, c.rmax, c.z))
        elif hasattr(c, "r") and hasattr(c, "z"):
            rz.append((c.r, c.z))
        elif hasattr(c, "zOrder"):
            secs.append((c.zPosition, c.xOffset, c.yOffset,
                         c.scalingFactor))
        elif hasattr(c, "x") and hasattr(c, "y"):
            verts.append((c.x, c.y))
    for key, val in (("zplanes", zplanes), ("rzpoints", rz),
                     ("vertices", verts), ("sections", secs)):
        if val:
            params[key] = val
    return params


def describe(obj):
    """Dict describing a solid, boolean, volume or copy - parameters,
    units, material and placement - for checking what was built."""
    if obj.TypeId == "App::Link":
        d = {"kind": "copy", "name": obj.Label,
             "of": obj.LinkedObject.Label}
        if hasattr(obj, "CopyNumber"):
            d["copynumber"] = obj.CopyNumber
        d.update(_placementInfo(obj.Placement))
        return d
    if obj.TypeId == "App::Part":
        solid = getSolid(obj)
        world = getWorld(obj.Document)
        kind = "world" if obj is world else (
            "volume" if solid is not None else "assembly")
        d = {"kind": kind, "name": obj.Label}
        d.update(_placementInfo(obj.Placement))
        if solid is not None:
            d["solid"] = describe(solid)
        d["daughters"] = [o.Label for o in obj.Group
                          if o.TypeId in ("App::Part", "App::Link")]
        if getattr(obj, "SensDet", "None") not in ("", "None"):
            d["SensDet"] = obj.SensDet
        return d
    if obj.TypeId in _G._BOOLEAN_TYPES:
        return {
            "kind": "boolean",
            "op": {"Part::Cut": "subtraction", "Part::Fuse": "union",
                   "Part::Common": "intersection"}[obj.TypeId],
            "name": obj.Label,
            "base": describe(obj.Base),
            "tool": describe(obj.Tool),
            "tool_relative": _placementInfo(
                obj.Base.Placement.inverse() * obj.Tool.Placement),
        }
    d = {
        "kind": "solid",
        "type": getattr(obj.Proxy, "Type", obj.TypeId),
        "name": obj.Label,
        "material": getattr(obj, "material", None),
        "lunit": getattr(obj, "lunit", None),
    }
    if hasattr(obj, "aunit"):
        d["aunit"] = obj.aunit
    d["params"] = _solidParams(obj)
    if not obj.Placement.isIdentity():
        d.update(_placementInfo(obj.Placement))
    if hasattr(obj, "Shape") and not obj.Shape.isNull():
        bb = obj.Shape.BoundBox
        d["size_mm"] = (_round(bb.XLength, 3), _round(bb.YLength, 3),
                        _round(bb.ZLength, 3))
    return d


def _solidSummary(solid):
    if solid is None:
        return "assembly"
    if solid.TypeId in _G._BOOLEAN_TYPES:
        d = describe(solid)
        return (f"{d['op']}({_solidSummary(solid.Base)}, "
                f"{_solidSummary(solid.Tool)})")
    d = describe(solid)
    params = " ".join(
        f"{k}={v}" for k, v in d["params"].items()
        if not isinstance(v, list)
    )
    lists = [k for k, v in d["params"].items() if isinstance(v, list)]
    if lists:
        params += " " + " ".join(f"{k}[{len(d['params'][k])}]"
                                 for k in lists)
    return f"{d['type'][4:]}({params} {d['lunit']}) {d['material']}"


def designTree(doc=None):
    """Readable outline of the geometry tree: volumes, copies, solids,
    materials and placements (mm / deg)."""
    doc = _G._getDoc(doc)
    lines = []

    def walk(obj, depth):
        pad = "  " * depth
        pl = _placementInfo(obj.Placement)
        where = ""
        if pl["position_mm"] != (0.0, 0.0, 0.0):
            where += f" @{pl['position_mm']}"
        if pl["rotation_xyz_deg"] != (0.0, 0.0, 0.0):
            where += f" rot{pl['rotation_xyz_deg']}"
        if obj.TypeId == "App::Link":
            lines.append(f"{pad}- {obj.Label} = copy of "
                         f"{obj.LinkedObject.Label}{where}")
            return
        sens = getattr(obj, "SensDet", "None")
        sens = f" [SensDet={sens}]" if sens not in ("", "None") else ""
        lines.append(f"{pad}- {obj.Label}{where}: "
                     f"{_solidSummary(getSolid(obj))}{sens}")
        for o in obj.Group:
            if o.TypeId in ("App::Part", "App::Link"):
                walk(o, depth + 1)

    walk(getWorld(doc), 0)
    return "\n".join(lines)


def exportGDML(filepath, doc=None, fit=True):
    """Write the design to a .gdml file and return its path.  fit=True
    first grows the world box (never shrinks it) so every volume fits.
    Needs the FreeCAD GUI (the exporter walks the tree view)."""
    import FreeCADGui

    if not FreeCAD.GuiUp:
        raise RuntimeError("GDML export needs FreeCAD running with its GUI")
    filepath = os.path.abspath(os.path.expanduser(filepath))
    if not filepath.lower().endswith(".gdml"):
        raise ValueError("filepath must end with .gdml")
    doc = _G._getDoc(doc)
    if fit:
        fitWorld(margin=1.1, growOnly=True, doc=doc)
    doc.recompute()
    world = getWorld(doc)
    FreeCADGui.Selection.clearSelection()
    FreeCADGui.Selection.addSelection(doc.Name, world.Name)
    from . import exportGDML as _exporter

    _exporter.export([world], filepath)
    if not os.path.isfile(filepath):
        raise RuntimeError(f"export did not write {filepath}; see Report "
                           "view / the .gdml.log file")
    return filepath


def apiSummary():
    """One line per public function: signature and first docstring line."""
    import inspect

    out = []
    for n in __all__:
        f = globals()[n]
        doc = (inspect.getdoc(f) or "").split("\n")[0]
        out.append(f"{n}{inspect.signature(f)}\n    {doc}")
    return "\n".join(out)
