# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2026 Keith Sloan <keith@sloan-home.co.uk>              *
# *                                                                        *
# *   This program is free software; you can redistribute it and/or modify *
# *   it under the terms of the GNU Lesser General Public License (LGPL)   *
# *   as published by the Free Software Foundation; either version 2 of    *
# *   the License, or (at your option) any later version.                  *
# *   for detail see the LICENCE text file.                                *
# *                                                                        *
# *   This program is distributed in the hope that it will be useful,      *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of       *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        *
# *   GNU Library General Public License for more details.                 *
# *                                                                        *
# **************************************************************************
"""
FreeCAD GDML Workbench - AP242 STEP importer (OUTLINE / SCAFFOLD)

Priority at this stage: **read a STEP AP242 file and navigate/scan it for
solids**.  Mapping those solids onto native GDML objects (primitive
recognition / CSG recovery) is delegated to :mod:`STEPdeconstruction`; the
tessellation fallback is deliberately not implemented yet -- unrecognised
solids are simply reported.

Two read paths are supported:

  * **STEPCAFControl_Reader** (preferred) -- the OCCT XCAF data-exchange
    reader.  It preserves shape names, colours and AP242 material strings.
    It requires an OCCT Python binding (``OCC.Core`` / pythonocc, or
    ``OCP``); these are not always present in FreeCAD's interpreter.

  * **FreeCAD Import module** (fallback) -- always available inside FreeCAD.
    Reads the geometry (and, on FreeCAD 1.x, colours / materials as object
    properties) but does not expose the raw XCAF label tree.

Blueprint reference:
    ToDo/BRep_to_GDML_Deconstruction.md  (sections 4 and 5)

STATUS: read + navigation being fleshed out; GDML mapping still outline.
"""

import os

import FreeCAD
import Part

from freecad.gdml import STEPdeconstruction

__title__ = "FreeCAD GDML Workbench - AP242 STEP Importer"
__author__ = "Keith Sloan"
__url__ = ["http://www.freecadweb.org"]


# --------------------------------------------------------------------------
# OCCT XCAF binding resolution
# --------------------------------------------------------------------------
#
# STEPCAFControl_Reader and the XCAF tools live in the OCCT data-exchange
# layer.  Try the common Python binding namespaces in turn.  Returns a small
# module-like namespace holding the classes we need, or None.


def _resolve_occ_xcaf():
    """Locate an OCCT XCAF Python binding.

    Returns a dict of the classes/enums used below, or None if no binding is
    importable in FreeCAD's interpreter.
    """
    # pythonocc-core layout
    try:
        from OCC.Core.STEPCAFControl import STEPCAFControl_Reader
        from OCC.Core.TDocStd import TDocStd_Document
        from OCC.Core.XCAFDoc import XCAFDoc_DocumentTool
        from OCC.Core.TCollection import TCollection_ExtendedString
        from OCC.Core.IFSelect import IFSelect_RetDone
        from OCC.Core.TopAbs import TopAbs_SOLID
        return {
            "STEPCAFControl_Reader": STEPCAFControl_Reader,
            "TDocStd_Document": TDocStd_Document,
            "XCAFDoc_DocumentTool": XCAFDoc_DocumentTool,
            "TCollection_ExtendedString": TCollection_ExtendedString,
            "IFSelect_RetDone": IFSelect_RetDone,
            "TopAbs_SOLID": TopAbs_SOLID,
        }
    except ImportError:
        pass

    # CadQuery OCP layout
    try:
        from OCP.STEPCAFControl import STEPCAFControl_Reader
        from OCP.TDocStd import TDocStd_Document
        from OCP.XCAFDoc import XCAFDoc_DocumentTool
        from OCP.TCollection import TCollection_ExtendedString
        from OCP.IFSelect import IFSelect_RetDone
        from OCP.TopAbs import TopAbs_SOLID
        return {
            "STEPCAFControl_Reader": STEPCAFControl_Reader,
            "TDocStd_Document": TDocStd_Document,
            "XCAFDoc_DocumentTool": XCAFDoc_DocumentTool,
            "TCollection_ExtendedString": TCollection_ExtendedString,
            "IFSelect_RetDone": IFSelect_RetDone,
            "TopAbs_SOLID": TopAbs_SOLID,
        }
    except ImportError:
        return None


# --------------------------------------------------------------------------
# FreeCAD importer entry points
# --------------------------------------------------------------------------
#
# FreeCAD's module_io.OpenInsertObject imports this module by its dotted name
# (registered via FreeCAD.addImportType in init_gui.py -- the registered name
# must be "freecad.gdml.importAP242", WITHOUT a trailing ".py") and then calls
# open() for File > Open and insert() for File > Insert.


def open(filename):
    """FreeCAD File > Open handler: create a new document from a STEP file."""
    docname = os.path.splitext(os.path.basename(filename))[0]
    doc = FreeCAD.newDocument(docname)
    doc.Label = docname
    import_ap242(filename, doc)
    return doc


def insert(filename, docname=None):
    """FreeCAD File > Insert handler: import a STEP file into an open document."""
    if docname:
        try:
            doc = FreeCAD.getDocument(docname)
        except NameError:
            doc = FreeCAD.newDocument(docname)
    else:
        doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("GDML_AP242")
    import_ap242(filename, doc)
    return doc


# --------------------------------------------------------------------------
# Top-level entry point
# --------------------------------------------------------------------------


def import_ap242(file_path, doc=None):
    """Import a STEP AP242 file and populate ``doc`` with GDML objects.

    Parameters
    ----------
    file_path : str
        Path to the ``.step`` / ``.stp`` file.
    doc : FreeCAD.Document, optional
        Target document.  Defaults to the active document (created if none).

    Returns
    -------
    list
        The GDML feature objects that were created.
    """
    if not os.path.isfile(file_path):
        raise IOError(f"STEP file not found: {file_path}")

    if doc is None:
        doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("GDML_AP242")

    FreeCAD.Console.PrintMessage(f"[importAP242] Reading {file_path}\n")

    occ = _resolve_occ_xcaf()
    if occ is not None:
        FreeCAD.Console.PrintMessage(
            "[importAP242] Using STEPCAFControl_Reader (XCAF)\n"
        )
        solids = list(read_step_xcaf(file_path, occ))
    else:
        FreeCAD.Console.PrintWarning(
            "[importAP242] OCCT XCAF binding not found -- "
            "falling back to FreeCAD Import module\n"
        )
        solids = list(read_step_freecad(file_path))

    FreeCAD.Console.PrintMessage(
        f"[importAP242] Found {len(solids)} solid(s) in file\n"
    )

    created = []
    for shape, attrs in solids:
        obj = _dispatch_solid(doc, shape, attrs)
        if obj is not None:
            created.append(obj)

    doc.recompute()
    FreeCAD.Console.PrintMessage(
        f"[importAP242] Created {len(created)} GDML object(s) "
        f"from {len(solids)} solid(s)\n"
    )
    return created


# --------------------------------------------------------------------------
# Read path A: STEPCAFControl_Reader (preferred)
# --------------------------------------------------------------------------


def read_step_xcaf(file_path, occ):
    """Read a STEP file with the OCCT XCAF reader and yield every solid.

    Yields ``(Part.Shape, attrs)`` tuples where ``attrs`` carries the
    recovered ``name`` / ``material`` / ``colour`` for the owning shape.
    """
    reader = occ["STEPCAFControl_Reader"]()
    reader.SetNameMode(True)
    reader.SetColorMode(True)
    reader.SetMatMode(True)
    # AP242 semantic PMI / GDT -- harmless if the build ignores it.
    try:
        reader.SetGDTMode(True)
    except Exception:
        pass

    status = reader.ReadFile(file_path)
    if status != occ["IFSelect_RetDone"]:
        raise IOError(f"STEPCAFControl_Reader failed to parse: {file_path}")

    ExtStr = occ["TCollection_ExtendedString"]
    xcaf_doc = occ["TDocStd_Document"](ExtStr("XmlXCAF"))
    reader.Transfer(xcaf_doc)

    shape_tool = occ["XCAFDoc_DocumentTool"].ShapeTool(xcaf_doc.Main())

    for label in _iter_free_shape_labels(shape_tool, occ):
        attrs = _read_label_attrs(label, xcaf_doc, occ)
        occ_shape = shape_tool.GetShape(label)
        for solid in _explode_solids(occ_shape, occ):
            yield _occ_to_part(solid), attrs


def _iter_free_shape_labels(shape_tool, occ):
    """Yield the top-level (free) shape labels, recursing into assemblies."""
    # TODO: shape_tool.GetFreeShapes(labels); for each, if IsAssembly then
    #       GetComponents and recurse, else yield the leaf label.
    return iter(())


def _read_label_attrs(label, xcaf_doc, occ):
    """Return {"name":..., "material":..., "colour":...} for one XCAF label."""
    # TODO: TDataStd_Name for the name; XCAFDoc_MaterialTool for the material
    #       string; XCAFDoc_ColorTool for the colour.
    return {"name": None, "material": None, "colour": None}


def _explode_solids(occ_shape, occ):
    """Yield each TopoDS_SOLID contained in an OCCT shape via TopExp_Explorer."""
    # TODO: exp = TopExp_Explorer(occ_shape, occ["TopAbs_SOLID"]);
    #       while exp.More(): yield exp.Current(); exp.Next()
    return iter(())


def _occ_to_part(occ_solid):
    """Wrap a raw OCCT TopoDS_Solid as a FreeCAD ``Part.Shape``.

    OCCT shape handles round-trip through FreeCAD via a BREP buffer, which
    avoids depending on private pointer bridging between the two bindings.
    """
    # TODO: write occ_solid to a BREP string/temp file and Part.Shape().read
    #       it back -- or use Part.__fromPythonOCC__ where available.
    return Part.Shape()


# --------------------------------------------------------------------------
# Read path B: FreeCAD Import module (fallback, always available)
# --------------------------------------------------------------------------


def read_step_freecad(file_path):
    """Read a STEP file with FreeCAD's bundled importer and yield every solid.

    Imports into a scratch document, walks the created objects, and explodes
    each object's Shape into individual solids.  Names come from the object
    Label; material/colour come from object properties on FreeCAD 1.x.
    """
    scratch = FreeCAD.newDocument("AP242_scratch")
    try:
        import Import
        Import.insert(file_path, scratch.Name)
        scratch.recompute()

        for obj in scratch.Objects:
            shape = getattr(obj, "Shape", None)
            if shape is None or shape.isNull():
                continue
            attrs = {
                "name": obj.Label,
                "material": _material_from_object(obj),
                "colour": _colour_from_object(obj),
            }
            for solid in shape.Solids:
                # Copy so the solid survives closing the scratch document.
                yield solid.copy(), attrs
    finally:
        # Keep geometry alive in caller's shapes (already copied) before close.
        FreeCAD.closeDocument(scratch.Name)


def _material_from_object(obj):
    """Best-effort material-name recovery from a FreeCAD import object."""
    # FreeCAD 1.x may expose ShapeMaterial / a material property; older
    # versions carry none.
    for attr in ("ShapeMaterial", "Material", "material"):
        val = getattr(obj, attr, None)
        if val:
            name = getattr(val, "Name", None) or getattr(val, "Label", None)
            return name or (val if isinstance(val, str) else None)
    return None


def _colour_from_object(obj):
    """Best-effort colour recovery from a FreeCAD import object's ViewObject."""
    vo = getattr(obj, "ViewObject", None)
    if vo is not None:
        col = getattr(vo, "ShapeColor", None)
        if col:
            return col
    return None


# --------------------------------------------------------------------------
# Material mapping + per-solid dispatch
# --------------------------------------------------------------------------


def _map_step_material(step_material_name):
    """Map a raw STEP material string to a GDML / Geant4 material name.

    STEP files carry free-text material names ("Aluminium", "Al", "SS304"...)
    that must be resolved to a name the GDML exporter understands, preferably
    a Geant4 NIST identifier such as ``G4_Al``.
    """
    # TODO: lookup table + fuzzy fallback; default to a configurable material.
    return step_material_name


def _dispatch_solid(doc, shape, attrs):
    """Run one solid through the deconstruction scan and attach the recovered
    semantic attributes (label, material) to any GDML object produced.
    """
    if shape is None or shape.isNull():
        return None

    obj = STEPdeconstruction.deconstruct_solid(doc, shape)
    if obj is None:
        return None

    name = attrs.get("name")
    if name:
        obj.Label = name

    material = _map_step_material(attrs.get("material"))
    if material and hasattr(obj, "material"):
        obj.material = material

    return obj
