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
FreeCAD GDML Workbench - B-rep -> GDML deconstruction (OUTLINE / SCAFFOLD)

Takes an exact Boundary-Representation solid (a ``TopoDS_Solid`` / FreeCAD
``Part`` shape) and attempts to express it as native GDML constructive solid
geometry:

    1. Primitive recognition  -> single <box> / <tube> / <sphere> ...
    2. CSG tree recovery       -> <subtraction> of a body primitive and
                                  recovered internal features (holes).

If neither analytical route succeeds the solid would ultimately fall through
to a tessellated <tessellated> solid.  That fallback is NOT implemented at
this stage -- for now it only logs a message so the scan/navigation work can
be developed and tested first.

Blueprint reference:
    ToDo/BRep_to_GDML_Deconstruction.md  (sections 2 and 3)

STATUS: outline only. Function bodies are stubs marked ``# TODO``.
"""

import FreeCAD
import Part

__title__ = "FreeCAD GDML Workbench - B-rep Deconstruction"
__author__ = "Keith Sloan"
__url__ = ["http://www.freecadweb.org"]


# --------------------------------------------------------------------------
# Surface-type classification constants
# --------------------------------------------------------------------------
#
# FreeCAD exposes OCCT surface types as the class name of ``face.Surface``:
#   Part.Plane, Part.Cylinder, Part.Sphere, Part.Cone, Part.Toroid,
#   Part.BSplineSurface, Part.SurfaceOfRevolution, ...
# We classify each face by that type name.

PLANE = "Plane"
CYLINDER = "Cylinder"
SPHERE = "Sphere"
CONE = "Cone"
TOROID = "Toroid"


def _surface_type(face):
    """Return the OCCT surface-type name for a FreeCAD face."""
    return type(face.Surface).__name__


def _face_type_histogram(shape):
    """Return a dict mapping surface-type name -> count for all faces in the
    solid.  This is the primary signal used to decide which recognition
    branch (if any) can apply.
    """
    hist = {}
    for face in shape.Faces:
        t = _surface_type(face)
        hist[t] = hist.get(t, 0) + 1
    return hist


# --------------------------------------------------------------------------
# Top-level dispatch
# --------------------------------------------------------------------------


def deconstruct_solid(doc, shape):
    """Attempt to convert a single B-rep solid into a GDML object.

    Order of attempts:
        1. recognise_primitive()   -- exact single-primitive match
        2. recover_csg_tree()      -- body primitive minus internal features
        3. tessellation fallback   -- NOT YET IMPLEMENTED (logs a message)

    Returns the created FreeCAD/GDML object, or None if nothing could be
    produced (i.e. the solid would need the tessellation fallback).
    """
    hist = _face_type_histogram(shape)
    FreeCAD.Console.PrintMessage(
        f"[BRepDeconstruct] Solid with {len(shape.Faces)} faces {hist}\n"
    )

    obj = recognise_primitive(doc, shape, hist)
    if obj is not None:
        FreeCAD.Console.PrintMessage(
            f"[BRepDeconstruct] -> recognised primitive: {obj.Label}\n"
        )
        return obj

    obj = recover_csg_tree(doc, shape, hist)
    if obj is not None:
        FreeCAD.Console.PrintMessage(
            f"[BRepDeconstruct] -> recovered CSG tree: {obj.Label}\n"
        )
        return obj

    # Tessellation fallback deliberately deferred -- just report it.
    FreeCAD.Console.PrintWarning(
        "[BRepDeconstruct] No analytical match; tessellation fallback "
        "not implemented yet -- solid skipped\n"
    )
    return None


# --------------------------------------------------------------------------
# 1. Primitive recognition
# --------------------------------------------------------------------------


def recognise_primitive(doc, shape, hist):
    """Try to match the whole solid to a single GDML primitive.

    Uses the face-type histogram as a quick filter, then verifies exact
    dimensions before emitting a native GDML solid.  Returns the created
    object or None.

    Recognisable configurations (initial target set):
        * 6 planes, all mutually axis-aligned  -> <box>
        * 2 planes + 1 cylinder (closed tube)  -> <tube>  (rmin=0 solid rod)
        * 2 planes + 2 coaxial cylinders       -> <tube>  (hollow pipe)
        * 1 sphere                             -> <sphere> / <orb>
        * planes + 1 cone                      -> <cone>
    """
    if _is_box(shape, hist):
        return _make_box(doc, shape)

    if _is_tube(shape, hist):
        return _make_tube(doc, shape)

    if _is_sphere(shape, hist):
        return _make_sphere(doc, shape)

    # TODO: cone, torus, ell, para ... as needed
    return None


# ---- box -----------------------------------------------------------------


def _is_box(shape, hist):
    """True if the solid is an axis-aligned (or single-placement) box:
    exactly 6 planar faces forming 3 opposed parallel pairs.
    """
    # TODO: 6 planes; group by normal into 3 antiparallel pairs; confirm
    #       right-angle adjacency.  Non-axis-aligned boxes are allowed but
    #       their orientation is captured as the object Placement.
    return False


def _make_box(doc, shape):
    """Create a GDML box from a recognised box solid.

    Dimensions come from the bounding box in the solid's own local frame;
    the frame itself becomes the object Placement.
    """
    # TODO:
    #   import GDMLObjects
    #   obj = doc.addObject("Part::FeaturePython", "GDMLBox")
    #   GDMLObjects.GDMLBox(obj, dx, dy, dz, "mm", material)
    #   obj.Placement = placement
    #   return obj
    return None


# ---- tube / cylinder -----------------------------------------------------


def _is_tube(shape, hist):
    """True if the solid is a solid rod or hollow pipe: two parallel planar
    caps plus one or two coaxial cylindrical faces.
    """
    # TODO: confirm 1 or 2 Cylinder faces sharing an axis, plus 2 planar
    #       caps perpendicular to that axis.
    return False


def _make_tube(doc, shape):
    """Create a GDML tube from a recognised rod/pipe solid.

    Extract rmax (outer cylinder radius), rmin (inner cylinder radius, 0 for
    a solid rod), z (cap-to-cap distance), and the axis placement.
    """
    # TODO: measure radii from Part.Cylinder.Radius, height from cap
    #       separation, build GDMLObjects.GDMLTube.
    return None


# ---- sphere --------------------------------------------------------------


def _is_sphere(shape, hist):
    """True if the solid is a single closed spherical face."""
    return hist.get(SPHERE, 0) == 1 and len(hist) == 1


def _make_sphere(doc, shape):
    """Create a GDML sphere/orb from a recognised spherical solid."""
    # TODO: radius from Part.Sphere.Radius; centre -> Placement.
    return None


# --------------------------------------------------------------------------
# 2. CSG tree recovery  (composite solids -- body minus features)
# --------------------------------------------------------------------------


def recover_csg_tree(doc, shape, hist):
    """Attempt to recover a subtraction tree for a composite solid, e.g. a
    block punctured by cylindrical holes.

    Approach (per blueprint section 3):
        1. Compute the Oriented Bounding Box (OBB) to establish the main
           body primitive.
        2. Scan for internal cylindrical faces whose normals point inward
           (orientation ``TopAbs_REVERSED``) -- these are drilled holes.
        3. Recover each hole's axis / radius / length and build a GDML
           <subtraction> of the body minus a tube per hole.

    Guardrail: if features cross at irregular angles or exceed what the
    recogniser can classify, return None so the caller reports the
    (not-yet-implemented) tessellation fallback rather than emitting a wrong
    analytical solid.
    """
    body, body_shape = _recover_body_primitive(doc, shape)
    if body is None:
        return None

    holes = _find_internal_cylinders(shape)
    if not holes:
        # Solid body with no recoverable internal features: the body
        # primitive itself is the answer.
        return body

    return _build_subtraction_tree(doc, body, holes)


def _oriented_bounding_box(shape):
    """Return the oriented bounding box (centre, half-extents, axes) for the
    solid.  Used to establish the outer body primitive of a composite.
    """
    # TODO: OCCT Bnd_OBB via BRepBndLib.AddOBB, or FreeCAD optimal-bbox
    #       helper.  Return a small struct / tuple.
    return None


def _recover_body_primitive(doc, shape):
    """Create the outer 'body' GDML primitive (usually a box from the OBB).

    Returns ``(obj, body_shape)`` where ``body_shape`` is the Part solid used
    later for the boolean subtraction, or ``(None, None)`` if the body could
    not be established.
    """
    # TODO: build box from _oriented_bounding_box(); reuse _make_box().
    return None, None


def _find_internal_cylinders(shape):
    """Return a list of recovered internal cylindrical features (holes).

    Each entry describes one hole::

        {"axis": Base.Vector, "origin": Base.Vector,
         "radius": float, "length": float, "blind": bool}

    A cylindrical face is treated as an internal hole when its surface is a
    ``Part.Cylinder`` and the face orientation is REVERSED (material lies
    outside the cylinder -> the cylinder is a void).
    """
    holes = []
    for face in shape.Faces:
        if _surface_type(face) != CYLINDER:
            continue
        if face.Orientation != "Reversed":
            continue
        # TODO: extract axis, origin, radius (face.Surface.Radius) and the
        #       extent along the axis; classify through/blind.
        holes.append({})
    return holes


def _build_subtraction_tree(doc, body, holes):
    """Assemble a sequential GDML <subtraction> tree: body minus one tube per
    recovered hole.
    """
    # TODO:
    #   import GDMLObjects
    #   result = body
    #   for h in holes:
    #       tool = _make_tube_from_hole(doc, h)
    #       result = GDMLObjects.makeSubtraction(doc, result, tool)
    #   return result
    return body


# --------------------------------------------------------------------------
# Tessellation fallback  -- intentionally NOT implemented yet
# --------------------------------------------------------------------------


def tessellation_fallback(doc, shape):
    """Placeholder for the eventual mesh fallback.

    Not implemented at this stage: the priority is reading the STEP file and
    scanning/navigating for recoverable GDML solids.  For now this only logs
    that the solid would need tessellating.
    """
    FreeCAD.Console.PrintWarning(
        "[BRepDeconstruct] tessellation_fallback() not implemented -- "
        "solid would be meshed to a <tessellated> solid here\n"
    )
    return None
