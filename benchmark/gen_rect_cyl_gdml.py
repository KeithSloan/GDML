#!/usr/bin/env python3
"""
Generate 4 GDML tessellation variants for a synthetic test geometry designed
to highlight the difference between triangle and quad meshes:

  Plate        — rectangular box (200×150×20 mm)
                 Flat faces → quads should be very efficient (few large elements)
  CylFull      — full cylinder (r=15, h=60 mm)
                 Sides → regular quads; caps → triangles
  CylHalf      — half cylinder, 180° arc (r=30, h=40 mm)
                 Curved side + two flat cut faces
  CylQuarter   — quarter cylinder, 90° arc (r=20, h=30 mm)
                 Tightest curvature; smallest quad panels on curved side

The world contains: 1 plate, 4 full cylinders (at plate corners), 2 half
cylinders, and 2 quarter cylinders — 9 logical volumes total.

All geometry is created directly in Gmsh OCC (no STEP files needed).

Four GDML variants produced (same naming convention as gen_all_gdml.py):
  rc_fc_default      — Gmsh OCC, lm=maxCord/10, lc=10, triangles only
  rc_gmsh            — same as fc_default (both use Gmsh OCC)
  rc_gmsh_min        — STL → recombine → non-planar quads split to triangles
  rc_gmsh_min_quads  — STL → recombine → all quads kept

Run with:
    python3 gen_rect_cyl_gdml.py
"""

import gmsh
import math
import os
import json
import tempfile
import xml.etree.ElementTree as ET
from xml.dom import minidom

import numpy as np

# ── Config ────────────────────────────────────────────────────────────────────
OUT_DIR   = "/Users/ksloan/github/CAD_Files_Git/GDML/rect_cyl"
MATERIAL  = "G4_STAINLESS-STEEL"
AIR       = "G4_AIR"
WORLD_MM  = 2000    # world box full side length

os.makedirs(OUT_DIR, exist_ok=True)

# ── Shape definitions ─────────────────────────────────────────────────────────
# Each entry: (label, creator_fn)
# creator_fn(gmsh_model) adds OCC shapes and returns after synchronize().

def _add_plate(model):
    """200×150×20 mm rectangular box, centred at origin."""
    model.occ.addBox(-100, -75, 0, 200, 150, 20)

def _add_cyl_full(model):
    """Full cylinder r=15 h=60 mm, axis along Z."""
    model.occ.addCylinder(0, 0, 0, 0, 0, 60, 15)

def _add_cyl_half(model):
    """Half cylinder 180° r=30 h=40 mm."""
    model.occ.addCylinder(0, 0, 0, 0, 0, 40, 30, angle=math.pi)

def _add_cyl_quarter(model):
    """Quarter cylinder 90° r=20 h=30 mm."""
    model.occ.addCylinder(0, 0, 0, 0, 0, 30, 20, angle=math.pi / 2)

# (label, add_fn, placement (dx,dy,dz) in world)
# Plate at origin; cylinders arranged around it
SHAPES = [
    ("Plate",       _add_plate,       (   0,    0,   0)),
    ("CylFull_A",   _add_cyl_full,    (-120,  -90,  20)),
    ("CylFull_B",   _add_cyl_full,    ( 120,  -90,  20)),
    ("CylFull_C",   _add_cyl_full,    (-120,   90,  20)),
    ("CylFull_D",   _add_cyl_full,    ( 120,   90,  20)),
    ("CylHalf_A",   _add_cyl_half,    (   0,  -90,  20)),
    ("CylHalf_B",   _add_cyl_half,    (   0,   90,  20)),
    ("CylQuarter_A",_add_cyl_quarter, (  60,    0,  20)),
    ("CylQuarter_B",_add_cyl_quarter, ( -60,    0,  20)),
]

# ── Mesh helpers (shared with gen_all_gdml.py logic) ──────────────────────────

def _nodes_from_gmsh():
    tags, coords, _ = gmsh.model.mesh.getNodes()
    return {int(t): (float(coords[3*i]), float(coords[3*i+1]), float(coords[3*i+2]))
            for i, t in enumerate(tags)}


def _compact(vertices_by_tag, facets_raw, coord_tol=0.001):
    """Merge near-duplicate vertices then compact to 0-based indices."""
    all_tags = sorted({t for f in facets_raw for t in f})
    coords_arr = np.array([vertices_by_tag[t] for t in all_tags])

    canonical = list(range(len(all_tags)))
    for i in range(len(all_tags)):
        if canonical[i] != i:
            continue
        for j in range(i + 1, len(all_tags)):
            if canonical[j] == j:
                if np.linalg.norm(coords_arr[i] - coords_arr[j]) < coord_tol:
                    canonical[j] = i

    old2canonical = {tag: canonical[idx] for idx, tag in enumerate(all_tags)}
    used = sorted(set(canonical))
    dense = {c: i for i, c in enumerate(used)}
    old2new = {tag: dense[old2canonical[tag]] for tag in all_tags}

    verts = [vertices_by_tag[all_tags[c]] for c in used]
    facets = []
    for f in facets_raw:
        nf = tuple(old2new[t] for t in f)
        if len(set(nf)) == len(nf):
            facets.append(nf)
    return verts, facets


def _repair_mesh(verts, facets, min_edge=0.1):
    """
    Fallback post-mesh edge collapse repair.
    See gen_all_gdml.py _repair_mesh docstring for full explanation.
    Preferred approach: gmsh.model.occ.healShapes() before synchronize().
    """
    verts = [list(v) for v in verts]
    parent = list(range(len(verts)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri == rj:
            return
        mid = [(verts[ri][k] + verts[rj][k]) / 2 for k in range(3)]
        if ri < rj:
            verts[ri] = mid; parent[rj] = ri
        else:
            verts[rj] = mid; parent[ri] = rj

    edges = set()
    for f in facets:
        n = len(f)
        for k in range(n):
            a, b = f[k], f[(k+1) % n]
            edges.add((min(a, b), max(a, b)))

    def edge_len(e):
        ra, rb = find(e[0]), find(e[1])
        return np.linalg.norm(np.array(verts[ra]) - np.array(verts[rb]))

    collapsed = 0
    for a, b in sorted(edges, key=edge_len):
        ra, rb = find(a), find(b)
        if ra == rb:
            continue
        if np.linalg.norm(np.array(verts[ra]) - np.array(verts[rb])) < min_edge:
            union(ra, rb)
            collapsed += 1

    all_roots = [find(i) for i in range(len(verts))]
    unique = sorted(set(all_roots))
    to_new = {r: i for i, r in enumerate(unique)}
    new_verts = [verts[r] for r in unique]
    new_facets = []
    for f in facets:
        nf = tuple(to_new[find(f[k])] for k in range(len(f)))
        if len(set(nf)) == len(f):
            new_facets.append(nf)

    if collapsed:
        dropped = len(facets) - len(new_facets)
        print(f"    repair: collapsed {collapsed} short edges → dropped {dropped} "
              f"degenerate facets, {len(new_verts)} verts remain")
    return new_verts, new_facets


def is_planar_quad(v0, v1, v2, v3, tol=1e-2):
    a = np.array(v1) - np.array(v0)
    b = np.array(v2) - np.array(v0)
    n = np.cross(a, b)
    norm = np.linalg.norm(n)
    if norm < 1e-10:
        return False
    return abs(np.dot(np.array(v3) - np.array(v0), n / norm)) < tol


# ── Per-shape meshers ─────────────────────────────────────────────────────────

def _setup_model(label, add_fn):
    """Initialise Gmsh, add shape, heal, synchronize. Returns max cord."""
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add(label)
    add_fn(gmsh.model)
    gmsh.model.occ.synchronize()
    xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
    return max(xmax - xmin, ymax - ymin, zmax - zmin)


def mesh_tri(label, add_fn):
    """Triangle mesh: Gmsh OCC, lm=maxCord/10, lc=10."""
    max_cord = _setup_model(label, add_fn)
    lm = max_cord / 10.0
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", lm)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 10)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 1.0)
    gmsh.model.mesh.generate(2)
    gmsh.model.mesh.removeDuplicateNodes()
    gmsh.model.mesh.renumberNodes()

    vtx = _nodes_from_gmsh()
    etypes, _, enodes = gmsh.model.mesh.getElements(2)
    facets_raw = []
    for etype, nodes in zip(etypes, enodes):
        if etype == 2:
            for i in range(0, len(nodes), 3):
                facets_raw.append((int(nodes[i]), int(nodes[i+1]), int(nodes[i+2])))
    gmsh.finalize()
    verts, facets = _compact(vtx, facets_raw)
    verts, facets = _repair_mesh(verts, facets)
    return verts, facets


def mesh_gmsh_min(label, add_fn, keep_quads=False):
    """STL → recombine → optional quad splitting."""
    max_cord = _setup_model(label, add_fn)
    lm = max_cord / 10.0
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", lm)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 10)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 1.0)
    gmsh.model.mesh.generate(2)
    tmpstl = tempfile.NamedTemporaryFile(suffix=".stl", delete=False).name
    gmsh.write(tmpstl)
    gmsh.finalize()

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.merge(tmpstl)
    gmsh.model.mesh.removeDuplicateNodes()
    gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 0)
    gmsh.option.setNumber("Mesh.RecombineOptimizeTopology", 0)
    gmsh.option.setNumber("Mesh.RecombineNodeRepositioning", 0)
    gmsh.option.setNumber("Mesh.RecombineMinimumQuality", 1e-3)
    gmsh.model.mesh.recombine()

    vtx = _nodes_from_gmsh()
    etypes, _, enodes = gmsh.model.mesh.getElements(-1, -1)
    tri_raw, quad_raw = [], []
    for etype, nodes in zip(etypes, enodes):
        if etype == 2:
            for i in range(0, len(nodes), 3):
                tri_raw.append((int(nodes[i]), int(nodes[i+1]), int(nodes[i+2])))
        elif etype == 3:
            for i in range(0, len(nodes), 4):
                quad_raw.append((int(nodes[i]), int(nodes[i+1]),
                                 int(nodes[i+2]), int(nodes[i+3])))
    gmsh.finalize()
    os.unlink(tmpstl)

    facets_raw = list(tri_raw)
    for q in quad_raw:
        v0, v1, v2, v3 = vtx[q[0]], vtx[q[1]], vtx[q[2]], vtx[q[3]]
        if keep_quads or is_planar_quad(v0, v1, v2, v3):
            facets_raw.append(q)
        else:
            facets_raw.append((q[0], q[1], q[2]))
            facets_raw.append((q[0], q[2], q[3]))

    verts, facets = _compact(vtx, facets_raw)
    verts, facets = _repair_mesh(verts, facets)
    return verts, facets


# ── GDML writer ───────────────────────────────────────────────────────────────

def write_gdml(shape_meshes, out_path):
    """
    shape_meshes: list of (label, dx, dy, dz, verts, facets)
      dx/dy/dz: translation of this volume in the world.
    """
    gdml = ET.Element("gdml", {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation":
            "http://service-spi.web.cern.ch/service-spi/app/releases/GDML/"
            "schema/gdml.xsd"
    })
    define    = ET.SubElement(gdml, "define")
    _         = ET.SubElement(gdml, "materials")
    solids    = ET.SubElement(gdml, "solids")
    structure = ET.SubElement(gdml, "structure")

    ET.SubElement(solids, "box", {
        "name": "WorldBox",
        "x": str(WORLD_MM), "y": str(WORLD_MM), "z": str(WORLD_MM),
        "lunit": "mm"
    })

    # Write each shape's position, solid, and logical volume first.
    # WorldLV must come last so all component volumes are already defined.
    placements = []   # (label, dx, dy, dz)

    for label, dx, dy, dz, verts, facets in shape_meshes:
        vname = f"v{label}_"
        solid_name = f"Tess_{label}"

        # Deduplicate vertices by formatted coordinate string
        coord_key_to_out = {}
        remap = {}
        out_verts = []
        for i, (x, y, z) in enumerate(verts):
            key = (f"{x:.6g}", f"{y:.6g}", f"{z:.6g}")
            if key not in coord_key_to_out:
                coord_key_to_out[key] = len(out_verts)
                out_verts.append(key)
            remap[i] = coord_key_to_out[key]

        for out_i, (sx, sy, sz) in enumerate(out_verts):
            ET.SubElement(define, "position", {
                "name": vname + str(out_i), "unit": "mm",
                "x": sx, "y": sy, "z": sz
            })

        tess = ET.SubElement(solids, "tessellated", {"name": solid_name})
        skipped = 0
        for f in facets:
            rf = tuple(remap[idx] for idx in f)
            if len(set(rf)) < len(rf):
                skipped += 1
                continue
            if len(rf) == 3:
                ET.SubElement(tess, "triangular", {
                    "vertex1": vname + str(rf[0]),
                    "vertex2": vname + str(rf[1]),
                    "vertex3": vname + str(rf[2]),
                    "type": "ABSOLUTE"
                })
            elif len(rf) == 4:
                ET.SubElement(tess, "quadrangular", {
                    "vertex1": vname + str(rf[0]),
                    "vertex2": vname + str(rf[1]),
                    "vertex3": vname + str(rf[2]),
                    "vertex4": vname + str(rf[3]),
                    "type": "ABSOLUTE"
                })

        lv = ET.SubElement(structure, "volume", {"name": f"LV_{label}"})
        ET.SubElement(lv, "materialref", {"ref": MATERIAL})
        ET.SubElement(lv, "solidref",    {"ref": solid_name})
        placements.append((label, dx, dy, dz))

    # WorldLV last
    world_lv = ET.SubElement(structure, "volume", {"name": "WorldLV"})
    ET.SubElement(world_lv, "materialref", {"ref": AIR})
    ET.SubElement(world_lv, "solidref",    {"ref": "WorldBox"})
    for label, dx, dy, dz in placements:
        pos_name = f"pos_{label}"
        ET.SubElement(define, "position", {
            "name": pos_name, "unit": "mm",
            "x": str(dx), "y": str(dy), "z": str(dz)
        })
        pv = ET.SubElement(world_lv, "physvol", {"name": f"PV_{label}"})
        ET.SubElement(pv, "volumeref",  {"ref": f"LV_{label}"})
        ET.SubElement(pv, "positionref", {"ref": pos_name})

    setup = ET.SubElement(gdml, "setup", {"name": "Default", "version": "1.0"})
    ET.SubElement(setup, "world", {"ref": "WorldLV"})

    raw    = ET.tostring(gdml, encoding="unicode")
    pretty = minidom.parseString(raw).toprettyxml(indent="  ")
    with open(out_path, "w") as fh:
        fh.write(pretty)
    size_mb = os.path.getsize(out_path) / 1e6
    tri  = sum(sum(1 for f in facets if len(f) == 3) for *_, facets in shape_meshes)
    quad = sum(sum(1 for f in facets if len(f) == 4) for *_, facets in shape_meshes)
    print(f"  Wrote {out_path}  ({size_mb:.1f} MB)  tri={tri}  quad={quad}")
    return tri, quad, size_mb


# ── Variant runners ───────────────────────────────────────────────────────────

VARIANTS = [
    ("rc_fc_default",     lambda lbl, fn: mesh_tri(lbl, fn),
                          "Gmsh OCC triangles (FC default approx)"),
    ("rc_gmsh",           lambda lbl, fn: mesh_tri(lbl, fn),
                          "Gmsh full triangles"),
    ("rc_gmsh_min",       lambda lbl, fn: mesh_gmsh_min(lbl, fn, keep_quads=False),
                          "Gmsh Min (non-planar quads → tri)"),
    ("rc_gmsh_min_quads", lambda lbl, fn: mesh_gmsh_min(lbl, fn, keep_quads=True),
                          "Gmsh Min Keep Quads"),
]


if __name__ == "__main__":
    stats = {}

    for variant_name, mesh_fn, desc in VARIANTS:
        print(f"\n{'='*60}")
        print(f"Variant: {variant_name}  —  {desc}")
        print('='*60)

        shape_meshes = []
        for label, add_fn, (dx, dy, dz) in SHAPES:
            print(f"  [{label}]")
            verts, facets = mesh_fn(label, add_fn)
            tri  = sum(1 for f in facets if len(f) == 3)
            quad = sum(1 for f in facets if len(f) == 4)
            print(f"    → {len(verts)} verts, {tri} tri, {quad} quad")
            shape_meshes.append((label, dx, dy, dz, verts, facets))

        out = f"{OUT_DIR}/{variant_name}-worldVOL.gdml"
        tri, quad, size_mb = write_gdml(shape_meshes, out)
        stats[variant_name] = {"tri": tri, "quad": quad,
                                "total": tri + quad, "size_mb": round(size_mb, 1)}

    stats_path = os.path.join(os.path.dirname(__file__), "rc_mesh_stats.json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"\nMesh stats written to {stats_path}")
    print("\nAll done.")
