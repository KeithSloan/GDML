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
FreeCAD GDML Workbench - BRep -> GDML deconstruction

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

import math

import FreeCAD
import Part

__title__ = "FreeCAD GDML Workbench - BRep Deconstruction"
__author__ = "Keith Sloan"
__url__ = ["http://www.freecadweb.org"]

# Tolerance for geometric comparisons (mm / unit-vector dot products).
EPS = 1e-7

# Placeholder material for recovered primitives; _dispatch_solid in
# the calling command overrides it with the shape's real material when known.
DEFAULT_MATERIAL = "G4_Galactic"

# When True, regular hole patterns build as Draft arrays (Draft.make_array);
# when False they build as a Part::MultiFuse of tubes.  Both export as a
# GDML <multiUnion>.
USE_DRAFT_ARRAYS = True

# Minimum number of members a regular pattern must have before it is built as a
# Draft array (smaller patterns stay a MultiFuse).  Will become a workbench
# preference; constant for now.
MIN_ARRAY_NUMBER = 4


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
# Geometry + GDML-object helpers (primitive recognition)
# --------------------------------------------------------------------------


def _unit(v):
    """Return a normalised copy of a FreeCAD vector."""
    n = v.Length
    if n <= EPS:
        return FreeCAD.Vector(v)
    return FreeCAD.Vector(v.x / n, v.y / n, v.z / n)


def _distinct_axes(normals):
    """Collapse face normals to distinct directions, ignoring sign."""
    axes = []
    for n in normals:
        if all(abs(n.dot(a)) < 1.0 - 1e-4 for a in axes):
            axes.append(n)
    return axes


def _mutually_orthogonal(axes):
    """True if all three axes are pairwise perpendicular."""
    a, b, c = axes
    return (
        abs(a.dot(b)) < 1e-4
        and abs(a.dot(c)) < 1e-4
        and abs(b.dot(c)) < 1e-4
    )


def _right_handed(axes):
    """Return the axes as a right-handed orthonormal triple (e0, e1, e2)."""
    e0, e1, e2 = (_unit(a) for a in axes)
    if e0.cross(e1).dot(e2) < 0:
        e2 = FreeCAD.Vector(-e2.x, -e2.y, -e2.z)
    return e0, e1, e2


def _axis_extent(points, axis, ref=None):
    """Return (span, mid) of point projections onto an axis.

    ``mid`` is measured from ``ref`` (world origin when ref is None).
    """
    if ref is None:
        coords = [p.dot(axis) for p in points]
    else:
        coords = [(p - ref).dot(axis) for p in points]
    lo, hi = min(coords), max(coords)
    return (hi - lo, (hi + lo) / 2.0)


def _frame_placement(e0, e1, e2, base):
    """Placement whose local X/Y/Z map to e0/e1/e2, positioned at ``base``."""
    m = FreeCAD.Matrix(
        e0.x, e1.x, e2.x, base.x,
        e0.y, e1.y, e2.y, base.y,
        e0.z, e1.z, e2.z, base.z,
        0.0, 0.0, 0.0, 1.0,
    )
    return FreeCAD.Placement(m)


def _apex_vertex(shape, base_center):
    """Cone apex: the vertex farthest from the base-circle centre."""
    best, best_d = None, -1.0
    for v in shape.Vertexes:
        d = (v.Point - base_center).Length
        if d > best_d:
            best, best_d = v.Point, d
    return best


def _add_gdml(doc, class_name, *args):
    """Instantiate a GDML primitive object on ``doc`` (with a ViewProvider)."""
    from freecad.gdml import GDMLObjects

    obj = doc.addObject("Part::FeaturePython", class_name)
    if obj is None:
        return None
    getattr(GDMLObjects, class_name)(obj, *args)
    try:
        GDMLObjects.ViewProvider(obj.ViewObject)
    except Exception:
        pass  # headless / no GUI available
    try:
        obj.recompute()
    except Exception as exc:
        FreeCAD.Console.PrintWarning(
            f"[BRepdeconstruction] {class_name} recompute failed: {exc}\n"
        )
    return obj


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
        f"[BRepdeconstruction] Solid with {len(shape.Faces)} faces {hist}\n"
    )

    obj = recognise_primitive(doc, shape, hist)
    if obj is not None:
        FreeCAD.Console.PrintMessage(
            f"[BRepdeconstruction] -> recognised primitive: {obj.Label}\n"
        )
        return obj

    obj = recover_csg_tree(doc, shape, hist)
    if obj is not None:
        FreeCAD.Console.PrintMessage(
            f"[BRepdeconstruction] -> recovered CSG tree: {obj.Label}\n"
        )
        return obj

    # Tessellation fallback deliberately deferred -- just report it.
    FreeCAD.Console.PrintWarning(
        "[BRepdeconstruction] No analytical match; tessellation fallback "
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

    if _is_cone(shape, hist):
        return _make_cone(doc, shape)

    # TODO: torus, ell, para ... as needed
    return None


# ---- box -----------------------------------------------------------------


def _is_box(shape, hist):
    """True if the solid is a box: exactly 6 planar faces (3 opposed pairs)."""
    return (
        len(shape.Faces) == 6
        and hist.get(PLANE, 0) == 6
        and len(hist) == 1
    )


def _make_box(doc, shape):
    """Create a GDML box from a recognised box solid.

    The three mutually perpendicular face normals define the local frame; the
    extents along them give x/y/z; the frame + centre become the Placement.
    A GDMLBox is centred on its Placement, so base = box centre.
    """
    normals = [_unit(f.Surface.Axis) for f in shape.Faces]
    axes = _distinct_axes(normals)
    if len(axes) != 3 or not _mutually_orthogonal(axes):
        return None  # six planes, but not a rectangular box
    e0, e1, e2 = _right_handed(axes)

    pts = [v.Point for v in shape.Vertexes]
    dx, mx = _axis_extent(pts, e0)
    dy, my = _axis_extent(pts, e1)
    dz, mz = _axis_extent(pts, e2)
    centre = e0 * mx + e1 * my + e2 * mz

    obj = _add_gdml(doc, "GDMLBox", dx, dy, dz, "mm", DEFAULT_MATERIAL)
    if obj is not None:
        obj.Placement = _frame_placement(e0, e1, e2, centre)
    return obj


# ---- tube / cylinder -----------------------------------------------------


def _is_tube(shape, hist):
    """True only for a clean rod/pipe: one or two coaxial cylindrical faces plus
    EXACTLY two planar caps and nothing else.  A cylinder carrying extra planar
    faces (flats, milled features, mounting pads) is not a tube -- it is left
    for CSG recovery."""
    return (
        hist.get(CYLINDER, 0) in (1, 2)
        and hist.get(PLANE, 0) == 2
        and set(hist) <= {CYLINDER, PLANE}
    )


def _make_tube(doc, shape):
    """Create a GDML tube (solid rod rmin=0, or hollow pipe) from a cylinder
    solid: rmax/rmin from the cylinder radii, z from the axial extent."""
    cyls = [f for f in shape.Faces if _surface_type(f) == CYLINDER]
    radii = [f.Surface.Radius for f in cyls]
    axis = _unit(cyls[0].Surface.Axis)
    ref = cyls[0].Surface.Center

    # All cylindrical faces must share the axis (coaxial rod / pipe).
    for f in cyls[1:]:
        if abs(abs(_unit(f.Surface.Axis).dot(axis)) - 1.0) > 1e-4:
            return None

    rmax = max(radii)
    rmin = min(radii) if len(radii) == 2 else 0.0

    pts = [v.Point for v in shape.Vertexes]
    z, mid = _axis_extent(pts, axis, ref)
    centre = ref + axis * mid

    obj = _add_gdml(
        doc, "GDMLTube",
        rmin, rmax, z, 0.0, 2 * math.pi, "rad", "mm", DEFAULT_MATERIAL,
    )
    if obj is not None:
        obj.Placement = FreeCAD.Placement(
            centre, FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), axis)
        )
    return obj


# ---- sphere --------------------------------------------------------------


def _is_sphere(shape, hist):
    """True if the solid is a single closed spherical face."""
    return hist.get(SPHERE, 0) == 1 and len(hist) == 1


def _make_sphere(doc, shape):
    """Create a native GDMLSphere from a recognised spherical solid.

    Spheres, like cylinders, are always preferred over tessellation.
    """
    face = next((f for f in shape.Faces if _surface_type(f) == SPHERE), None)
    if face is None:
        return None
    surf = face.Surface
    obj = _add_gdml(
        doc, "GDMLSphere",
        0.0, surf.Radius, 0.0, 2 * math.pi, 0.0, math.pi,
        "rad", "mm", DEFAULT_MATERIAL,
    )
    if obj is not None:
        obj.Placement = FreeCAD.Placement(
            FreeCAD.Vector(surf.Center), FreeCAD.Rotation()
        )
    return obj


# ---- cone ----------------------------------------------------------------


def _is_cone(shape, hist):
    """True only for a clean cone/frustum: exactly one conical face plus one or
    two planar caps and nothing else.  A cone with extra planar features is
    left for CSG recovery."""
    return (
        hist.get(CONE, 0) == 1
        and hist.get(PLANE, 0) in (1, 2)
        and set(hist) <= {CONE, PLANE}
    )


def _make_cone(doc, shape):
    """Create a GDML cone/frustum from a recognised conical solid.

    Radii and length come from the solid's circular edges: a frustum has two
    rings, a full cone has one ring plus an apex vertex.  rmin is 0 (solid).
    """
    cone = next(f for f in shape.Faces if _surface_type(f) == CONE)
    axis = _unit(cone.Surface.Axis)

    circles = []
    for e in shape.Edges:
        curve = e.Curve
        if type(curve).__name__ == "Circle":
            circles.append((curve.Radius, curve.Center))

    if len(circles) >= 2:
        circles.sort(key=lambda rc: rc[1].dot(axis))
        (r_lo, c_lo), (r_hi, c_hi) = circles[0], circles[-1]
    elif len(circles) == 1:
        r_lo, c_lo = circles[0]
        c_hi = _apex_vertex(shape, c_lo)
        if c_hi is None:
            return None
        r_hi = 0.0
    else:
        return None

    span = c_hi - c_lo
    length = span.Length
    if length < EPS:
        return None
    axis_dir = _unit(span)
    centre = (c_lo + c_hi) * 0.5

    obj = _add_gdml(
        doc, "GDMLCone",
        0.0, r_lo,   # rmin1, rmax1  (low end -> local -z/2)
        0.0, r_hi,   # rmin2, rmax2  (high end -> local +z/2)
        length, 0.0, 2 * math.pi, "rad", "mm", DEFAULT_MATERIAL,
    )
    if obj is not None:
        obj.Placement = FreeCAD.Placement(
            centre, FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), axis_dir)
        )
    return obj


# --------------------------------------------------------------------------
# 2. CSG tree recovery  (composite solids -- body minus features)
# --------------------------------------------------------------------------


def recover_csg_tree(doc, shape, hist):
    """Analyse a composite solid as a body primitive minus cylindrical holes,
    and PRINT the recovered high-level hierarchy.

    First pass -- analysis + reporting only.  It establishes an axis-aligned
    body box, finds internal (REVERSED-orientation) cylindrical faces as
    drilled holes, recovers each hole's axis/radius/length, and logs the
    recovered ``<subtraction>`` hierarchy.  It does NOT yet emit GDML boolean
    objects; it returns a description dict (see ``_build_subtraction_tree`` for
    the next step).  Returning a dict is truthy, so the caller can report that
    an analysis was produced.
    """
    holes = _find_internal_cylinders(shape)
    patterns = _detect_hole_patterns(holes)
    bosses = _find_external_cylinders(shape)
    filled = _fill_holes(shape, holes)
    body = _recover_body_primitive(shape, filled)
    report = _format_csg_hierarchy(shape, body, holes, patterns, bosses)
    FreeCAD.Console.PrintMessage(report + chr(10))
    return {"body": body, "holes": holes, "patterns": patterns,
            "bosses": bosses, "filled": filled, "report": report}


def _oriented_bounding_box(shape):
    """Axis-aligned bounding box as a first-pass body frame.

    Returns ``(dims, centre)`` with ``dims = (dx, dy, dz)`` and ``centre`` a
    ``FreeCAD.Vector``.  A true oriented box (OCCT ``Bnd_OBB``) is a later
    refinement; axis-aligned is correct for axis-aligned parts and a usable
    approximation otherwise.
    """
    bb = shape.BoundBox
    return (bb.XLength, bb.YLength, bb.ZLength), FreeCAD.Vector(bb.Center)


def _fill_holes(shape, holes):
    """Return the outer body envelope: the solid with its recovered holes filled
    (solid fused with a solid cylinder per hole).  Used to recognise the body."""
    import Part
    fills = []
    for h in holes:
        length = h["length"]          # flush fill -- no protrusion
        axis = FreeCAD.Vector(h["axis"])
        base = FreeCAD.Vector(h["origin"]) - axis * (length / 2.0)
        try:
            fills.append(Part.makeCylinder(h["radius"], length, base, axis))
        except Exception:
            pass
    if not fills:
        return shape
    try:
        return shape.fuse(fills)
    except Exception:
        return shape


def _boss_cut_shapes(bosses):
    """Part cylinder shapes for each boss, used to cut the bosses out of the
    body core before tessellation (they are added back as native cylinders)."""
    import Part
    shapes = []
    for b in bosses:
        length = b["length"]
        axis = FreeCAD.Vector(b["axis"])
        base = FreeCAD.Vector(b["origin"]) - axis * (length / 2.0)
        try:
            shapes.append(Part.makeCylinder(b["radius"], length, base, axis))
        except Exception:
            pass
    return shapes


def _make_tessellated(doc, shape, name):
    """Create a GDMLTessellated from a Part shape (mesh only the body core;
    bosses and holes stay native).  Returns the object or None."""
    if shape is None or shape.isNull():
        return None
    try:
        import MeshPart
        from freecad.gdml import GDMLObjects
        mesh = MeshPart.meshFromShape(
            Shape=shape, LinearDeflection=0.1,
            AngularDeflection=0.523599, Relative=False,
        )
        obj = doc.addObject("Part::FeaturePython", name)
        GDMLObjects.GDMLTessellated(
            obj, mesh.Topology[0], mesh.Facets, True, "mm", DEFAULT_MATERIAL
        )
        obj.Proxy.createGeometry(obj)
        try:
            GDMLObjects.ViewProvider(obj.ViewObject)
        except Exception:
            pass
        return obj
    except Exception as exc:
        FreeCAD.Console.PrintWarning(
            "[BRepdeconstruction] tessellation failed (" + str(exc) + ")" + chr(10))
        return None


def _recover_axis_box(shape):
    """Recover an axis-aligned box core from the solid's planar faces.

    For each axis, the two box boundary planes are the two largest-area planar
    faces whose normal lies along that axis (bosses/pads have small tops, so the
    box faces dominate).  Returns ((dx, dy, dz), centre) or None.
    """
    axes = {"x": FreeCAD.Vector(1, 0, 0),
            "y": FreeCAD.Vector(0, 1, 0),
            "z": FreeCAD.Vector(0, 0, 1)}
    bounds = {}
    for key, av in axes.items():
        cand = []
        for f in shape.Faces:
            if _surface_type(f) != PLANE:
                continue
            if abs(_unit(f.Surface.Axis).dot(av)) < 0.99:
                continue
            cand.append((f.CenterOfMass.dot(av), f.Area))
        if len(cand) < 2:
            return None
        by_area = sorted(cand, key=lambda c: -c[1])
        p1 = by_area[0][0]
        opp = [c for c in by_area if abs(c[0] - p1) > 1e-3]
        if not opp:
            return None
        p2 = opp[0][0]
        bounds[key] = (min(p1, p2), max(p1, p2))
    dims = (round(bounds["x"][1] - bounds["x"][0], 3),
            round(bounds["y"][1] - bounds["y"][0], 3),
            round(bounds["z"][1] - bounds["z"][0], 3))
    if min(dims) <= 0:
        return None
    centre = FreeCAD.Vector((bounds["x"][0] + bounds["x"][1]) / 2.0,
                            (bounds["y"][0] + bounds["y"][1]) / 2.0,
                            (bounds["z"][0] + bounds["z"][1]) / 2.0)
    return dims, centre


def _recover_body_primitive(shape, filled):
    """Classify the hole-filled body envelope as box / tube / cone / complex.

    If ``filled`` is a clean primitive the build uses that exact primitive
    (via recognise_primitive); otherwise the body falls back to the bounding
    box (and, later, tessellation of the residual body).
    """
    hist = _face_type_histogram(filled)
    if _is_box(filled, hist):
        kind = "box"
    elif _is_tube(filled, hist):
        kind = "tube"
    elif _is_cone(filled, hist):
        kind = "cone"
    else:
        kind = "complex"
    bb = shape.BoundBox
    return {
        "kind": kind,
        "dims": (round(bb.XLength, 3), round(bb.YLength, 3), round(bb.ZLength, 3)),
        "centre": FreeCAD.Vector(bb.Center),
        "filled_faces": len(filled.Faces),
    }


def _bbox_corners(bb):
    """Return the eight corner points of a bounding box."""
    return [
        FreeCAD.Vector(x, y, z)
        for x in (bb.XMin, bb.XMax)
        for y in (bb.YMin, bb.YMax)
        for z in (bb.ZMin, bb.ZMax)
    ]


def _vkey(v):
    """Rounded (x, y, z) tuple, for de-duplicating coaxial hole faces."""
    return (round(v.x, 2), round(v.y, 2), round(v.z, 2))


def _find_internal_cylinders(shape):
    """Return internal (drilled-hole) cylindrical features.

    A cylindrical face with REVERSED orientation bounds a void -- material lies
    outside the cylinder -- so it is a hole.  Each entry::

        {"axis": Vector, "origin": Vector, "radius": float,
         "length": float, "through": bool}

    A single hole is often split into two cylindrical faces at the seam; these
    are merged by shared axis/radius/origin.
    """
    bb = shape.BoundBox
    corners = _bbox_corners(bb)
    holes = []
    for face in shape.Faces:
        if _surface_type(face) != CYLINDER or face.Orientation != "Reversed":
            continue
        surf = face.Surface
        axis = _unit(surf.Axis)
        pts = [v.Point for v in face.Vertexes]
        if pts:
            length, mid = _axis_extent(pts, axis, surf.Center)
            origin = surf.Center + axis * mid
        else:
            length, origin = 0.0, FreeCAD.Vector(surf.Center)
        body_span, _ = _axis_extent(corners, axis)
        holes.append({
            "axis": axis,
            "origin": origin,
            "radius": round(surf.Radius, 3),
            "length": round(length, 3),
            "through": length >= body_span - 1e-3,
        })
    return _merge_coaxial_holes(holes)


def _merge_coaxial_holes(holes):
    """Merge cylindrical faces that describe the same hole (same axis/radius/
    origin), keeping the largest axial length."""
    merged = {}
    for h in holes:
        key = (h["radius"], _vkey(h["axis"]), _vkey(h["origin"]))
        if key in merged:
            m = merged[key]
            m["length"] = max(m["length"], h["length"])
            m["through"] = m["through"] or h["through"]
        else:
            merged[key] = h
    return list(merged.values())


def _find_external_cylinders(shape):
    """Return external (FORWARD-orientation) cylindrical faces -- candidate
    bosses / pins (material lies INSIDE the cylinder), which also picks up edge
    fillets.  Same geometry recovery as holes; classified boss-vs-fillet later.
    """
    ext = []
    for face in shape.Faces:
        if _surface_type(face) != CYLINDER or face.Orientation != "Forward":
            continue
        surf = face.Surface
        axis = _unit(surf.Axis)
        pts = [v.Point for v in face.Vertexes]
        if pts:
            length, mid = _axis_extent(pts, axis, surf.Center)
            origin = surf.Center + axis * mid
        else:
            length, origin = 0.0, FreeCAD.Vector(surf.Center)
        ext.append({
            "axis": axis, "origin": origin, "radius": round(surf.Radius, 3),
            "length": round(length, 3), "through": False,
        })
    return _merge_coaxial_holes(ext)


def _format_csg_hierarchy(shape, body, holes, patterns, bosses=None):
    """Render the recovered body, holes and detected patterns as ASCII."""
    dx, dy, dz = body["dims"]
    c = body["centre"]
    out = [
        "[BRepdeconstruction] CSG analysis (first pass, axis-aligned body):",
        f"  High-level solid : {len(shape.Faces)} faces, "
        f"{len(shape.Solids)} solid(s)",
        f"  Body (holes filled): {body['kind'].upper()}  bbox "
        f"{dx} x {dy} x {dz} mm @ ({c.x:.2f}, {c.y:.2f}, {c.z:.2f}), "
        f"{body.get('filled_faces', '?')} faces",
        f"  Internal cylindrical features (holes): {len(holes)}",
    ]
    if body.get("kind") == "complex":
        out.append(
            "    -> body core tessellated; bosses + holes stay native cylinders"
        )
    for i, h in enumerate(holes):
        a, o = h["axis"], h["origin"]
        kind = "through" if h["through"] else "blind"
        out.append(
            f"    hole {i}: r={h['radius']} len={h['length']} "
            f"axis=({a.x:.2f},{a.y:.2f},{a.z:.2f}) "
            f"origin=({o.x:.2f},{o.y:.2f},{o.z:.2f}) [{kind}]"
        )
    bosses = bosses or []
    out.append(
        f"  External cylinders (candidate bosses/fillets): {len(bosses)}"
    )
    _seen = []
    for b in bosses:
        key = (b["radius"], _vkey(b["axis"]))
        if key in _seen:
            continue
        _seen.append(key)
        cnt = sum(1 for x in bosses
                  if (x["radius"], _vkey(x["axis"])) == key)
        a = b["axis"]
        out.append(
            f"    r={b['radius']} x{cnt} len={b['length']} "
            f"axis=({a.x:.2f},{a.y:.2f},{a.z:.2f})"
        )
    out.append(f"  Detected hole patterns: {len(patterns)}")
    for p in patterns:
        out.append("    " + _describe_pattern(p))
    out.append("  Recovered hierarchy:")
    if patterns:
        out.append("    subtraction")
        out.append(f"    |- Box (body) {dx}x{dy}x{dz}")
        for j, p in enumerate(patterns):
            branch = "`-" if j == len(patterns) - 1 else "|-"
            out.append(f"    {branch} {_pattern_tool(p)}")
    else:
        out.append(
            f"    Box (body) {dx}x{dy}x{dz}  [no internal cylindrical features]"
        )
    return chr(10).join(out)


def _describe_pattern(p):
    m = ",".join(str(i) for i in p["members"])
    r, ln = p["radius"], p["length"]
    t = p["type"]
    if t == "single":
        return f"single  : r={r} len={ln} (hole {m})"
    if t == "linear":
        return (f"linear  : {p['count']} holes r={r} spacing={p['spacing']} "
                f"(holes {m})")
    if t == "grid":
        return (f"grid    : {p['nx']}x{p['ny']} r={r} sx={p['sx']} sy={p['sy']} "
                f"(holes {m})")
    if t == "polar":
        cc = p["centre"]
        return (f"polar   : {p['count']} holes r={r} on ring "
                f"R={p['ring_radius']} angle={p['angle']}deg "
                f"centre=({cc.x:.2f},{cc.y:.2f},{cc.z:.2f}) (holes {m})")
    return f"cluster : {len(p['members'])} holes r={r} irregular (holes {m})"


def _pattern_tool(p):
    """Describe how this pattern will actually be built, honouring
    USE_DRAFT_ARRAYS and MIN_ARRAY_NUMBER so the report matches the tree."""
    r, ln = p["radius"], p["length"]
    t = p["type"]
    n = len(p["members"])
    if t == "single" or n == 1:
        return f"Tube r={r} len={ln}  -> single cut"
    if n < MIN_ARRAY_NUMBER:
        return (f"{n}x Tube r={r}  -> {n} individual cuts "
                f"(< MIN_ARRAY_NUMBER={MIN_ARRAY_NUMBER})")
    if USE_DRAFT_ARRAYS and t == "grid":
        return (f"Draft OrthoArray {p['nx']}x{p['ny']} of Tube r={r}  "
                f"-> multiUnion + one cut")
    if USE_DRAFT_ARRAYS and t == "polar":
        return (f"Draft PolarArray x{p['count']} of Tube r={r}  "
                f"-> multiUnion + one cut")
    if USE_DRAFT_ARRAYS and t == "linear":
        return (f"Draft OrthoArray x{p['count']} of Tube r={r}  "
                f"-> multiUnion + one cut")
    return f"MultiFuse of {n}x Tube r={r}  -> multiUnion + one cut"


def _inplane_basis(axis):
    """Two orthonormal vectors spanning the plane perpendicular to axis."""
    a = _unit(axis)
    ref = FreeCAD.Vector(1.0, 0.0, 0.0)
    if abs(a.dot(ref)) > 0.9:
        ref = FreeCAD.Vector(0.0, 1.0, 0.0)
    u = _unit(a.cross(ref))
    v = _unit(a.cross(u))
    return u, v


def _detect_hole_patterns(holes, pos_tol=1e-2, ang_tol=0.5):
    """Group identical holes (same radius/length/axis) and classify each group
    as single / linear / grid / polar / cluster."""
    groups, order = {}, []
    for i, h in enumerate(holes):
        key = (h["radius"], h["length"], _vkey(h["axis"]))
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(i)
    patterns = []
    for key in order:
        idxs = groups[key]
        pts = [holes[i]["origin"] for i in idxs]
        axis = holes[idxs[0]]["axis"]
        patterns.append(_classify_group(idxs, pts, axis, holes, pos_tol, ang_tol))
    return patterns


def _classify_group(idxs, pts, axis, holes, pos_tol, ang_tol):
    base = {
        "members": list(idxs),
        "radius": holes[idxs[0]]["radius"],
        "length": holes[idxs[0]]["length"],
        "axis": axis,
    }
    if len(idxs) == 1:
        base["type"] = "single"
        base["origin"] = pts[0]
        return base
    u, v = _inplane_basis(axis)
    coords = [(p.dot(u), p.dot(v)) for p in pts]
    for detector in (_try_linear, _try_grid):
        res = detector(coords, pos_tol)
        if res:
            base.update(res)
            return base
    pol = _try_polar(coords, pts, ang_tol, pos_tol)
    if pol:
        base.update(pol)
        return base
    base["type"] = "cluster"
    return base


def _try_linear(coords, tol):
    """Collinear, equally-spaced points -> linear array descriptor, else None."""
    import math
    n = len(coords)
    if n < 2:
        return None
    x0, y0 = coords[0]
    far = max(coords, key=lambda c: (c[0] - x0) ** 2 + (c[1] - y0) ** 2)
    dx, dy = far[0] - x0, far[1] - y0
    dlen = math.hypot(dx, dy)
    if dlen < tol:
        return None
    ux, uy = dx / dlen, dy / dlen
    projs = []
    for (x, y) in coords:
        wx, wy = x - x0, y - y0
        if abs(wx * (-uy) + wy * ux) > max(tol, 1e-3):
            return None
        projs.append(wx * ux + wy * uy)
    projs.sort()
    gaps = [projs[i + 1] - projs[i] for i in range(len(projs) - 1)]
    if gaps[0] < tol or any(abs(g - gaps[0]) > max(tol, 1e-3) for g in gaps):
        return None
    return {"type": "linear", "count": n, "spacing": round(gaps[0], 3)}


def _try_grid(coords, tol):
    """Rectangular m x n grid, equal spacing -> grid descriptor, else None."""
    n = len(coords)
    if n < 4:
        return None
    xs = _cluster_1d([c[0] for c in coords], tol)
    ys = _cluster_1d([c[1] for c in coords], tol)
    if len(xs) < 2 or len(ys) < 2 or len(xs) * len(ys) != n:
        return None
    sx, sy = _uniform_spacing(xs, tol), _uniform_spacing(ys, tol)
    if sx is None or sy is None:
        return None
    return {"type": "grid", "nx": len(xs), "ny": len(ys),
            "sx": round(sx, 3), "sy": round(sy, 3)}


def _try_polar(coords, pts, ang_tol, pos_tol):
    """Equal-radius, equal-angle points -> polar array descriptor, else None."""
    import math
    n = len(coords)
    if n < 3:
        return None
    cx = sum(c[0] for c in coords) / n
    cy = sum(c[1] for c in coords) / n
    radii = [math.hypot(c[0] - cx, c[1] - cy) for c in coords]
    if radii[0] < pos_tol or any(abs(r - radii[0]) > max(pos_tol, 1e-2) for r in radii):
        return None
    angs = sorted(math.degrees(math.atan2(c[1] - cy, c[0] - cx)) % 360.0
                  for c in coords)
    gaps = [angs[i + 1] - angs[i] for i in range(len(angs) - 1)]
    gaps.append(360.0 - angs[-1] + angs[0])
    if any(abs(g - gaps[0]) > max(ang_tol, 0.5) for g in gaps):
        return None
    centre = FreeCAD.Vector(sum(p.x for p in pts) / n,
                            sum(p.y for p in pts) / n,
                            sum(p.z for p in pts) / n)
    return {"type": "polar", "count": n, "ring_radius": round(radii[0], 3),
            "angle": round(gaps[0], 2), "centre": centre}


def _cluster_1d(values, tol):
    """Sorted representative values, merging those within tol."""
    vals = sorted(values)
    reps = [vals[0]]
    for x in vals[1:]:
        if abs(x - reps[-1]) > max(tol, 1e-3):
            reps.append(x)
    return reps


def _uniform_spacing(reps, tol):
    """Common spacing of sorted reps, or None if not uniform."""
    if len(reps) < 2:
        return None
    gaps = [reps[i + 1] - reps[i] for i in range(len(reps) - 1)]
    if gaps[0] < tol or any(abs(g - gaps[0]) > max(tol, 1e-3) for g in gaps):
        return None
    return gaps[0]

def _make_tube_tool(doc, hole):
    """Create a GDMLTube cutting tool for one hole (rmin=0), placed on its
    axis.  Through holes are extended slightly so the cut is clean."""
    length = hole["length"]
    if hole.get("through"):
        length = length + 0.4
    tube = _add_gdml(
        doc, "GDMLTube",
        0.0, hole["radius"], max(length, 1e-3), 0.0, 2 * math.pi,
        "rad", "mm", DEFAULT_MATERIAL,
    )
    if tube is not None:
        tube.Placement = FreeCAD.Placement(
            FreeCAD.Vector(hole["origin"]),
            FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), hole["axis"]),
        )
    return tube


def _try_build_array(doc, pattern, members):
    """Build a Draft array tool for a regular pattern, reconstructing the array
    vectors from the member hole origins.  Uses Draft.make_array (the same call
    the workbench uses in importGDML).  Returns the array object, or None to
    fall back to a MultiFuse.

      linear : step vector between adjacent holes, base at the line end
      grid   : in-plane u/v steps (sx, sy), base at the min-corner hole
      polar  : centre + total angle, base at the first hole
    """
    try:
        import Draft
        t = pattern["type"]
        axis = members[0]["axis"]
        origins = [FreeCAD.Vector(h["origin"]) for h in members]
        zero = FreeCAD.Vector(0, 0, 0)

        if t == "linear":
            d = _unit(origins[-1] - origins[0])
            ordered = sorted(members,
                             key=lambda h: FreeCAD.Vector(h["origin"]).dot(d))
            step = FreeCAD.Vector(ordered[1]["origin"]) - FreeCAD.Vector(ordered[0]["origin"])
            base = _make_tube_tool(doc, ordered[0])
            if base is None:
                return None
            return Draft.make_array(base, step, zero, zero, len(members), 1, 1)

        if t == "grid":
            u, v = _inplane_basis(axis)
            ustep = u * pattern["sx"]
            vstep = v * pattern["sy"]
            corner = min(members, key=lambda h: (
                round(FreeCAD.Vector(h["origin"]).dot(u), 4),
                round(FreeCAD.Vector(h["origin"]).dot(v), 4)))
            base = _make_tube_tool(doc, corner)
            if base is None:
                return None
            return Draft.make_array(base, ustep, vstep, zero,
                                    int(pattern["nx"]), int(pattern["ny"]), 1)

        if t == "polar":
            base = _make_tube_tool(doc, members[0])
            if base is None:
                return None
            total = pattern["angle"] * pattern["count"]
            return Draft.make_array(base, FreeCAD.Vector(pattern["centre"]),
                                    total, int(pattern["count"]))
    except Exception as exc:
        FreeCAD.Console.PrintWarning(
            "[BRepdeconstruction] Draft array failed (" + str(exc)
            + "); using MultiFuse" + chr(10)
        )
    return None


def _build_pattern_tool(doc, pattern, holes):
    """Build the cutting tool for one detected pattern.

    single                     -> one GDMLTube
    regular pattern >= MIN_ARRAY_NUMBER (and USE_DRAFT_ARRAYS) -> Draft array
    otherwise                  -> Part::MultiFuse of tubes
    A MultiFuse and a Draft array both export as a GDML <multiUnion>, so the
    pattern subtracts with a single cut either way.
    """
    members = [holes[i] for i in pattern["members"]]
    if not members:
        return None
    n = len(members)
    if n == 1:
        return _make_tube_tool(doc, members[0])
    if USE_DRAFT_ARRAYS and n >= MIN_ARRAY_NUMBER:
        arr = _try_build_array(doc, pattern, members)
        if arr is not None:
            try:
                arr.Label = "GDML_MultUnion"
            except Exception:
                pass
            return arr
    tools = [t for t in (_make_tube_tool(doc, h) for h in members) if t is not None]
    if not tools:
        return None
    if len(tools) == 1:
        return tools[0]
    fuse = doc.addObject("Part::MultiFuse", "GDML_MultUnion")
    fuse.Label = "GDML_MultUnion"
    fuse.Shapes = tools
    return fuse

def _build_subtraction_tree(doc, structure, name_base="GDML_Solid"):
    """Build the recovered CSG as native objects: a GDMLBox body minus one
    tool per detected pattern, chained with Part::Cut.

    Naming (name_base e.g. "GDML_TopCover"): top-level result -> name_base,
    inner cuts -> name_base + "_<n>_Cut" (numbered descending from the top),
    body -> name_base + "_Body", tube unions -> "GDML_MultUnion".

    One cut per pattern keeps the boolean tree shallow; each patterned tool is
    a Draft array / MultiFuse that exports as a <multiUnion>.  The body is the
    axis-aligned bounding box -- exact only when the solid really is a box.
    """
    body_desc = structure["body"]
    patterns = structure.get("patterns") or []
    holes = structure["holes"]
    bosses = structure.get("bosses") or []
    filled = structure.get("filled")

    # --- body: recognised primitive from the filled envelope, else box core,
    #     else bounding box (residual to be tessellated) ---
    body = None
    # 1. native primitive from the filled envelope (clean box/tube/cone/sphere).
    if filled is not None:
        try:
            body = recognise_primitive(doc, filled, _face_type_histogram(filled))
        except Exception as exc:
            FreeCAD.Console.PrintWarning(
                "[BRepdeconstruction] body recognise failed (" + str(exc)
                + ")" + chr(10))
            body = None
    # 2. complex body -> tessellate the DE-BOSSED core (cut the boss cylinders
    #    out first) so the mesh excludes the bosses; they are unioned back as
    #    native cylinders below.  Nothing native is ever fused into the mesh.
    if body is None and filled is not None:
        core_shape = filled
        cuts = _boss_cut_shapes(bosses)
        deboss_ok = False
        if cuts:
            try:
                cut_shape = filled.cut(cuts)
                if (cut_shape is not None and not cut_shape.isNull()
                        and cut_shape.Volume > 1e-6):
                    core_shape = cut_shape
                    deboss_ok = True
            except Exception:
                pass
        if not deboss_ok:
            # the external cylinders are the body's own surface, not separable
            # bosses (cutting them empties the shape) -- tessellate the whole
            # envelope and do not union them back.
            bosses = []
        body = _make_tessellated(doc, core_shape, name_base + "_Body")
    # 3. last-resort fallback: bounding box.
    if body is None:
        dx, dy, dz = body_desc["dims"]
        body = _add_gdml(doc, "GDMLBox", dx, dy, dz, "mm", DEFAULT_MATERIAL)
        if body is None:
            return None
        body.Placement = FreeCAD.Placement(
            FreeCAD.Vector(body_desc["centre"]), FreeCAD.Rotation()
        )
        FreeCAD.Console.PrintWarning(
            "[BRepdeconstruction] body fallback to bounding box" + chr(10))
    body.Label = name_base + "_Body"

    # --- union native cylinder bosses onto the body ---
    result = body
    if bosses:
        boss_tubes = [t for t in (_make_tube_tool(doc, b) for b in bosses)
                      if t is not None]
        if boss_tubes:
            fuse = doc.addObject("Part::MultiFuse", name_base + "_Bosses")
            fuse.Label = name_base + "_Bosses"
            fuse.Shapes = [result] + boss_tubes
            result = fuse

    cuts = []
    tools = []
    for pattern in patterns:
        members = pattern["members"]
        n = len(members)
        if n == 1:
            tools.append(_make_tube_tool(doc, holes[members[0]]))
        elif n >= MIN_ARRAY_NUMBER:
            tools.append(_build_pattern_tool(doc, pattern, holes))
        else:
            # a group below MIN_ARRAY_NUMBER is not a genuine array -- cut each
            # hole individually rather than bundle a meaningless MultUnion.
            for idx in members:
                tools.append(_make_tube_tool(doc, holes[idx]))
    for tool in tools:
        if tool is None:
            continue
        cut = doc.addObject("Part::Cut", "GDML_Cut")
        cut.Base = result
        cut.Tool = tool
        cuts.append(cut)
        result = cut
    total = len(cuts)
    for i, cut in enumerate(cuts, start=1):
        cut.Label = name_base if i == total else f"{name_base}_{total - i}_Cut"
    if total == 0:
        body.Label = name_base
    doc.recompute()
    return result


# --------------------------------------------------------------------------
# Tessellation fallback  -- intentionally NOT implemented yet
# --------------------------------------------------------------------------


def tessellation_fallback(doc, shape):
    """Placeholder for the eventual mesh fallback.

    Not implemented in this module yet -- the Shapes2GDML command wires this
    fallback to the workbench's existing TessellateFeature path.  For now this
    only logs that the solid would need tessellating.
    """
    FreeCAD.Console.PrintWarning(
        "[BRepdeconstruction] tessellation_fallback() not implemented -- "
        "solid would be meshed to a <tessellated> solid here\n"
    )
    return None
