# -*- coding: utf-8 -*-
# testReplica.py  —  PROTOTYPE "testReplica" workbench command.
#
# Analyses a selected group of placements of (nominally) the same volume and
# classifies it, reporting via a dialog:
#
#     Param Replica                 -> regular lattice, identical daughters
#                                      => export as <replicavol> (G4PVReplica)
#     Param Volume
#        identical Daughters        -> irregular placement, identical daughters
#                                      => export as <paramvol> (uniform dims)
#        Complex                    -> daughters vary (size/shape/material)
#                                      => general <paramvol>, per-copy params
#
# The dialog offers an ENABLED action button for the first two categories
# (build base + locked App::Links tagged for export) and a Close button.
# "Complex" is reported only (no auto-build — App::Links need identical shapes).
#
# The classification (sections 1-2) is pure Python and unit-testable without
# FreeCAD; the FreeCAD/Qt glue (sections 3-5) is separated below.

import math

# ==========================================================================
# 1. pure vector helpers
# ==========================================================================
def _sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def _dot(a, b): return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
def _norm(a):   return math.sqrt(_dot(a, a))
def _unit(a):
    n = _norm(a)
    return (a[0]/n, a[1]/n, a[2]/n) if n else (0.0, 0.0, 0.0)


# ==========================================================================
# 2. pure classification
# ==========================================================================
def _linear_equal(points, tol):
    """Collinear + equally spaced -> (pitch, axis) else None."""
    n = len(points)
    if n < 2:
        return None
    p0 = points[0]
    far = max(points, key=lambda p: _norm(_sub(p, p0)))
    axis = _unit(_sub(far, p0))
    if axis == (0.0, 0.0, 0.0):
        return None
    projs = []
    for p in points:
        w = _sub(p, p0)
        t = _dot(w, axis)
        perp = _norm(_sub(w, (axis[0]*t, axis[1]*t, axis[2]*t)))
        if perp > max(tol, 1e-3):
            return None                      # not collinear
        projs.append(t)
    projs.sort()
    gaps = [projs[i+1]-projs[i] for i in range(len(projs)-1)]
    if gaps[0] <= tol or any(abs(g-gaps[0]) > max(tol, 1e-3) for g in gaps):
        return None                          # uneven spacing
    return {"pitch": round(gaps[0], 4), "axis": axis}


def _polar_equal(points, tol_len=1e-2, tol_ang=0.5):
    """Equal radius + equal angular step about the mean centre -> descriptor."""
    n = len(points)
    if n < 3:
        return None
    cx = sum(p[0] for p in points)/n
    cy = sum(p[1] for p in points)/n
    r = [math.hypot(p[0]-cx, p[1]-cy) for p in points]
    if r[0] < tol_len or any(abs(x-r[0]) > max(tol_len, 1e-2) for x in r):
        return None
    ang = sorted(math.degrees(math.atan2(p[1]-cy, p[0]-cx)) % 360.0 for p in points)
    gaps = [ang[i+1]-ang[i] for i in range(len(ang)-1)] + [360.0-ang[-1]+ang[0]]
    if any(abs(g-gaps[0]) > max(tol_ang, 0.5) for g in gaps):
        return None
    return {"angle": round(gaps[0], 3), "centre": (round(cx, 3), round(cy, 3))}


# category constants
REPLICA   = "replica"            # Param Replica         (actionable)
PARAM_ID  = "paramvol_identical" # Param Volume/identical (actionable)
COMPLEX   = "complex"            # Param Volume/Complex   (report only)
NONE      = "none"               # nothing to do


def classify(daughters, points, tol=1e-3):
    """daughters: list of hashable shape signatures; points: list of (x,y,z).
    Returns {"category", "count", ...}."""
    n = len(points)
    if n < 2:
        return {"category": NONE, "count": n, "reason": "need >= 2 placements"}

    identical = len(set(daughters)) == 1
    if not identical:
        return {"category": COMPLEX, "count": n,
                "distinct": len(set(daughters)),
                "reason": "daughters differ in shape/size/material"}

    lin = _linear_equal(points, tol)
    if lin:
        return {"category": REPLICA, "count": n, "kind": "linear", **lin}
    pol = _polar_equal(points)
    if pol:
        return {"category": REPLICA, "count": n, "kind": "polar", **pol}
    return {"category": PARAM_ID, "count": n,
            "reason": "identical daughters, irregular placement"}


# human-readable summary used by the dialog
def report_text(r):
    c = r["category"]
    if c == REPLICA:
        if r.get("kind") == "polar":
            det = f"polar, angle {r['angle']}°, {r['count']} copies"
            gdml = "<replicavol> along phi"
        else:
            det = f"linear, pitch {r['pitch']} mm along {r['axis']}, {r['count']} copies"
            gdml = "<replicavol> along axis  (G4PVReplica)"
        return ("Param Replica", f"Regular lattice detected: {det}.",
                f"Export: {gdml}")
    if c == PARAM_ID:
        return ("Param Volume — identical Daughters",
                f"{r['count']} identical daughters, irregular placement.",
                "Export: <paramvol> with uniform dimensions  (G4PVParameterised)")
    if c == COMPLEX:
        return ("Param Volume — Complex",
                f"{r['count']} copies but daughters vary "
                f"({r.get('distinct','?')} distinct shapes).",
                "Export: general <paramvol> with per-copy parameters "
                "(cannot use App::Links).")
    return ("No group", r.get("reason", ""), "")


ACTIONABLE = (REPLICA, PARAM_ID)


# ==========================================================================
# 3. FreeCAD analysis glue
# ==========================================================================
def _global_base(obj):
    try:
        return tuple(obj.getGlobalPlacement().Base)
    except Exception:
        return tuple(obj.Placement.Base)


def daughter_signature(obj):
    """A hashable shape/material signature; equal => 'identical daughter'."""
    base = obj.LinkedObject if obj.TypeId == "App::Link" else obj
    mat = getattr(base, "material", getattr(base, "Material", ""))
    shp = getattr(base, "Shape", None)
    if shp is not None and hasattr(shp, "BoundBox"):
        bb = shp.BoundBox
        return ("shape", str(mat), round(shp.Volume, 3),
                round(bb.XLength, 3), round(bb.YLength, 3), round(bb.ZLength, 3))
    return ("name", str(mat), base.Name)


def gather_selection():
    """Return (objs, signatures, points) for the current selection."""
    import FreeCADGui
    objs = [o for o in FreeCADGui.Selection.getSelection()
            if hasattr(o, "Placement")]
    sigs = [daughter_signature(o) for o in objs]
    pts = [_global_base(o) for o in objs]
    return objs, sigs, pts


# ==========================================================================
# 4. build (base + locked App::Links), tagged for export
# ==========================================================================
def build_group(result, objs):
    import FreeCAD
    doc = FreeCAD.ActiveDocument
    axis = result.get("axis", (0.0, 0.0, 1.0))
    ordered = sorted(objs, key=lambda o: _dot(_global_base(o), axis))
    base = ordered[0]
    base_target = base.LinkedObject if base.TypeId == "App::Link" else base

    group = doc.addObject("App::Part", "ReplicaGroup")
    group.addProperty("App::PropertyString", "ExportAs", "Replica").ExportAs = (
        "replicavol" if result["category"] == REPLICA else "paramvol")
    group.addProperty("App::PropertyInteger", "Count", "Replica").Count = result["count"]
    if result["category"] == REPLICA and result.get("kind") == "linear":
        group.addProperty("App::PropertyFloat", "Pitch", "Replica").Pitch = result["pitch"]
        group.addProperty("App::PropertyVector", "Axis", "Replica").Axis = FreeCAD.Vector(*axis)

    group.addObject(base)
    for src in ordered[1:]:
        link = doc.addObject("App::Link", base_target.Label + "_lnk")
        link.LinkedObject = base_target
        link.Placement = src.Placement
        for p in ("Placement", "LinkedObject"):
            try: link.setEditorMode(p, 1)          # read-only: edit only the base
            except Exception: pass
        group.addObject(link)
        doc.removeObject(src.Name)                  # consume original (inverse = explode)
    doc.recompute()
    FreeCAD.Console.PrintMessage(
        f"testReplica: built base + {len(ordered)-1} links, ExportAs={group.ExportAs}\n")
    return group


# ==========================================================================
# 5. Qt dialog + command
# ==========================================================================
def show_dialog(result, objs):
    from PySide import QtGui, QtCore
    title, line1, line2 = report_text(result)

    dlg = QtGui.QDialog()
    dlg.setWindowTitle("testReplica — analyse group")
    dlg.setMinimumWidth(420)
    lay = QtGui.QVBoxLayout(dlg)

    head = QtGui.QLabel("<b>%s</b>" % title); lay.addWidget(head)
    lay.addWidget(QtGui.QLabel(line1))
    if line2:
        sub = QtGui.QLabel(line2); sub.setStyleSheet("color:#555"); lay.addWidget(sub)

    btns = QtGui.QHBoxLayout(); btns.addStretch(1)
    actionable = result["category"] in ACTIONABLE
    act = QtGui.QPushButton("Create Replica" if result["category"] == REPLICA
                            else "Create Param Volume")
    act.setEnabled(actionable)
    act.setDefault(actionable)
    close = QtGui.QPushButton("Close")
    btns.addWidget(act); btns.addWidget(close); lay.addLayout(btns)

    def on_action():
        try:
            build_group(result, objs)
        finally:
            dlg.accept()
    act.clicked.connect(on_action)
    close.clicked.connect(dlg.reject)
    dlg.exec_()


class TestReplicaCommand:
    def GetResources(self):
        # Reuses the Analyse-Shape icon for now; add a dedicated icon later.
        return {"Pixmap": "GDMLAnalyseShape",
                "MenuText": "Test Replica",
                "ToolTip": "Analyse selected placements: Replica / Param Volume / Complex"}

    def IsActive(self):
        import FreeCAD
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        import FreeCAD
        objs, sigs, pts = gather_selection()
        if len(objs) < 2:
            FreeCAD.Console.PrintError(
                "testReplica: select >= 2 placements of the same volume\n")
            return
        result = classify(sigs, pts)
        FreeCAD.Console.PrintMessage(f"testReplica: {result}\n")
        show_dialog(result, objs)


# register when imported inside FreeCAD (guarded so the module imports headless)
try:
    import FreeCADGui
    FreeCADGui.addCommand("GDML_TestReplica", TestReplicaCommand())
except Exception:
    pass
