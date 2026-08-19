# **************************************************************************
# *   Copyright (c) 2026 Keith Sloan <keithsloan52@icloud.com>              *
# *   LGPL -- see LICENCE.                                                 *
# **************************************************************************
"""FreeCAD GDML Workbench - shape analysis for the Shapes2GDML command.

Given a FreeCAD ``Part.Shape`` this reports the topology depth, subshape
counts and a per-solid GDML-native verdict (analytic primitive / CSG
candidate / freeform-needs-tessellation), reusing the recognisers in
:mod:`BRepdeconstruction`.
"""

import FreeCAD
from freecad.gdml import BRepdeconstruction as brep

__title__ = "FreeCAD GDML Workbench - Shape Analysis"
__author__ = "Keith Sloan"

# Surface-type names that GDML can represent analytically.
_ANALYTIC = {"Plane", "Cylinder", "Cone", "Sphere", "Toroid", "Torus"}


def _container_depth(shape):
    """Levels of Compound / CompSolid nesting above the solids (0 = bare solid)."""
    depth, s = 0, shape
    while s.ShapeType in ("Compound", "CompSolid"):
        subs = s.SubShapes
        if not subs:
            break
        depth += 1
        nested = [x for x in subs if x.ShapeType in ("Compound", "CompSolid")]
        if nested:
            s = nested[0]
        else:
            break
    return depth


def _primitive_kind(solid, hist):
    """Return 'box' / 'tube' / 'cone' if the solid matches a recogniser, else None."""
    if brep._is_box(solid, hist):
        return "box"
    if brep._is_tube(solid, hist):
        return "tube"
    if brep._is_cone(solid, hist):
        return "cone"
    return None


def analyse_solid(solid, idx):
    """Analyse one solid; return a dict of metrics + verdict."""
    hist = brep._face_type_histogram(solid)
    freeform = any(t not in _ANALYTIC for t in hist)
    prim = _primitive_kind(solid, hist)
    if prim:
        verdict = "primitive"
    elif not freeform:
        verdict = "analytic"      # CSG / boolean candidate
    else:
        verdict = "freeform"      # tessellation required
    bb = solid.BoundBox
    return {
        "index": idx,
        "n_faces": len(solid.Faces),
        "hist": hist,
        "primitive": prim,
        "verdict": verdict,
        "bbox": (round(bb.XLength, 3), round(bb.YLength, 3), round(bb.ZLength, 3)),
    }


def analyse_shape(shape):
    """Analyse a whole shape; return metrics, per-solid detail and an overall
    verdict."""
    solids = shape.Solids
    info = {
        "shape_type": shape.ShapeType,
        "depth": _container_depth(shape),
        "n_solids": len(solids),
        "n_shells": len(shape.Shells),
        "n_faces": len(shape.Faces),
        "n_edges": len(shape.Edges),
        "n_vertexes": len(shape.Vertexes),
        "solids": [analyse_solid(s, i) for i, s in enumerate(solids)],
    }
    verdicts = [s["verdict"] for s in info["solids"]]
    if not verdicts:
        info["overall"] = "empty (no solids)"
    elif all(v == "primitive" for v in verdicts):
        info["overall"] = "GDML-native primitives"
    elif all(v in ("primitive", "analytic") for v in verdicts):
        info["overall"] = "analytic (primitive / CSG candidate)"
    elif any(v == "freeform" for v in verdicts):
        info["overall"] = "freeform present (tessellation needed)"
    else:
        info["overall"] = "mixed"
    return info


def is_gdml_native(obj):
    """True if the FreeCAD object is already a GDML* proxy object."""
    proxy = getattr(obj, "Proxy", None)
    cls = getattr(proxy, "__class__", None)
    return bool(cls) and cls.__name__.startswith("GDML")


def format_report(obj, info):
    """Render the analysis of one object as a monospace text block."""
    lines = [
        f"Object: {obj.Label}  ({obj.Name})",
        f"  Already GDML native : {'yes' if is_gdml_native(obj) else 'no'}",
        f"  Shape type          : {info['shape_type']}   "
        f"container depth: {info['depth']}",
        f"  Subshapes           : solids={info['n_solids']} "
        f"shells={info['n_shells']} faces={info['n_faces']} "
        f"edges={info['n_edges']} vertexes={info['n_vertexes']}",
        f"  Overall verdict     : {info['overall']}",
    ]
    for s in info["solids"]:
        hist = ", ".join(f"{k}:{v}" for k, v in sorted(s["hist"].items()))
        lines.append(
            f"    Solid {s['index']}: {s['n_faces']} faces [{hist}]"
        )
        lines.append(
            f"      bbox(mm)={s['bbox']}  primitive={s['primitive'] or '-'}  "
            f"verdict={s['verdict']}"
        )
    return "\n".join(lines)
