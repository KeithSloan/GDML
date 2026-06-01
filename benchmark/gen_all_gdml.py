#!/usr/bin/env python3
"""
Generate all 4 benchmark GDML files for the 1485 tubs.

Variants produced:
  1. fc_default  — Gmsh with coarse STL-based mesh (approximates FreeCAD Netgen default)
  2. gmsh        — Gmsh full, new defaults: lm=maxCord/10, lc=10, lp=10
  3. gmsh_min    — STL → Gmsh recombine → non-planar quads split to 2 triangles
  4. gmsh_min_quads — STL → Gmsh recombine → all quads kept as quads

Run with:
    python3 gen_all_gdml.py
  or (if gmsh not in system Python):
    /Applications/FreeCAD.app/Contents/Resources/bin/python3 gen_all_gdml.py
"""

import gmsh
import math
import os
import tempfile
import xml.etree.ElementTree as ET
from xml.dom import minidom

import numpy as np

# ── Config ────────────────────────────────────────────────────────────────
STEP_DIR  = "/Users/ksloan/github/CAD_Files_Git/GDML/1485_step"
MATERIAL  = "G4_STAINLESS-STEEL"
AIR       = "G4_AIR"
WORLD_MM  = 2000    # world box full side length

STEPS = [
    ("1485 Top Tub.STEP",    "TopTub"),
    ("1485 Bottom Tub.STEP", "BottomTub"),
]


# ── Geometry helpers ──────────────────────────────────────────────────────
def get_bbox_maxcord(step_path):
    """Return max(X,Y,Z) extent of a STEP file using Gmsh OCC."""
    gmsh.initialize()
    gmsh.model.add("bbox")
    # OCCTargetUnit omitted — FreeCAD STEP files are already in mm
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.occ.importShapes(step_path)
    gmsh.model.occ.synchronize()
    xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
    gmsh.finalize()
    return max(xmax - xmin, ymax - ymin, zmax - zmin)


def _compact(vertices_by_tag, facets_raw, coord_tol=0.001):
    """
    Return (compact_verts_list, compact_facets_list) with 0-based indices.
    Merges nodes whose coordinates are within coord_tol of each other,
    then filters degenerate facets (any two vertices at the same position).
    """
    all_tags = sorted({t for f in facets_raw for t in f})
    coords_arr = np.array([vertices_by_tag[t] for t in all_tags])  # shape (N,3)

    # Build canonical index: for each node, find the first node with same coords
    canonical = list(range(len(all_tags)))
    for i in range(len(all_tags)):
        if canonical[i] != i:
            continue
        for j in range(i + 1, len(all_tags)):
            if canonical[j] == j:
                if np.linalg.norm(coords_arr[i] - coords_arr[j]) < coord_tol:
                    canonical[j] = i

    # Remap: old tag → canonical compact index
    old2canonical = {tag: canonical[idx] for idx, tag in enumerate(all_tags)}
    # Renumber canonical indices to 0-based dense
    used_canonical = sorted(set(canonical))
    dense = {c: i for i, c in enumerate(used_canonical)}
    old2new = {tag: dense[old2canonical[tag]] for tag in all_tags}

    verts = [vertices_by_tag[all_tags[c]] for c in used_canonical]
    facets = []
    for f in facets_raw:
        nf = tuple(old2new[t] for t in f)
        # Skip degenerate (any two vertices map to same index after merge)
        if len(set(nf)) == len(nf):
            facets.append(nf)
    return verts, facets


def _repair_mesh(verts, facets, min_edge=0.1):
    """
    Fallback mesh repair: iteratively collapse edges shorter than min_edge mm.

    Preferred fix: gmsh.model.occ.healShapes(fixSmallEdges=True,
                                              minimumEdgeLength=0.1)
    called BEFORE gmsh.model.occ.synchronize(). healShapes runs in the OCC
    C++ kernel and removes short CAD edges before meshing, so Gmsh never
    creates forced boundary nodes at their endpoints in the first place.
    That is both faster and cleaner than post-mesh repair.

    This function exists as a fallback for cases where healShapes is not
    available (older Gmsh versions) or where a STEP file still produces
    near-degenerate triangles despite healing.

    Algorithm (union-find edge collapse, sorted by length):
      - Build the complete edge set from all facets.
      - Sort edges shortest-first and collapse any edge shorter than min_edge
        by merging both endpoints to their midpoint (union-find).
      - Because edges are processed shortest-first in a single pass, each
        collapse immediately updates the union-find structure so subsequent
        edges referencing the same vertices see the new midpoint. This
        converges in one pass rather than requiring iteration.
      - All facets that referenced either endpoint are automatically remapped
        to the merged midpoint vertex — the mesh stays closed with no holes.
      - Facets whose vertices all collapsed to the same point (the tiny
        triangle itself) become degenerate and are dropped.

    min_edge should be well below the smallest legitimate mesh edge.
    With CharacteristicLengthMin=1.0 mm the default of 0.1 mm is safe.
    """
    verts = [list(v) for v in verts]   # mutable
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
            verts[ri] = mid
            parent[rj] = ri
        else:
            verts[rj] = mid
            parent[ri] = rj

    # Build edge set (unique unordered pairs) from all facets
    edges = set()
    for f in facets:
        n = len(f)
        for k in range(n):
            a, b = f[k], f[(k + 1) % n]
            edges.add((min(a, b), max(a, b)))

    # Sort by current length, collapse shortest first — single pass convergence
    def edge_len(e):
        ra, rb = find(e[0]), find(e[1])
        return np.linalg.norm(np.array(verts[ra]) - np.array(verts[rb]))

    sorted_edges = sorted(edges, key=edge_len)
    collapsed = 0
    for a, b in sorted_edges:
        ra, rb = find(a), find(b)
        if ra == rb:
            continue
        if np.linalg.norm(np.array(verts[ra]) - np.array(verts[rb])) < min_edge:
            union(ra, rb)
            collapsed += 1

    # Compact: map root → new dense index
    all_roots = [find(i) for i in range(len(verts))]
    unique = sorted(set(all_roots))
    to_new = {r: i for i, r in enumerate(unique)}
    new_verts = [verts[r] for r in unique]
    new_facets = []
    for f in facets:
        nf = tuple(to_new[find(f[k])] for k in range(len(f)))
        if len(set(nf)) == len(f):   # not degenerate after collapse
            new_facets.append(nf)

    dropped = len(facets) - len(new_facets)
    if collapsed:
        print(f"    repair: collapsed {collapsed} short edges → dropped {dropped} "
              f"degenerate facets, {len(new_verts)} verts remain")
    return new_verts, new_facets


def _nodes_from_gmsh():
    """Return dict {tag: (x,y,z)} from current Gmsh model."""
    tags, coords, _ = gmsh.model.mesh.getNodes()
    return {int(t): (float(coords[3*i]), float(coords[3*i+1]), float(coords[3*i+2]))
            for i, t in enumerate(tags)}


# ── Planarity check (for gmsh_min quad splitting) ─────────────────────────
def is_planar_quad(v0, v1, v2, v3, tol=1e-2):
    """True if v3 lies in the plane defined by v0,v1,v2 within tol mm."""
    a = np.array(v1) - np.array(v0)
    b = np.array(v2) - np.array(v0)
    n = np.cross(a, b)
    norm = np.linalg.norm(n)
    if norm < 1e-10:
        return False
    return abs(np.dot(np.array(v3) - np.array(v0), n / norm)) < tol


# ── Variant 1: FC-default approximation ──────────────────────────────────
def mesh_fc_default(step_path, label):
    """
    Approximate FreeCAD Netgen default:
      STL via Gmsh OCC with angular deflection ~0.5 rad → triangles only.
      Uses the same STL + no-recombine pipeline but with coarse settings.
    """
    print(f"\n[fc_default/{label}] meshing...")
    max_cord = get_bbox_maxcord(step_path)
    # FreeCAD default: LinearDeflection ≈ 0.5% of maxCord, AngularDeflection 0.5 rad
    lin_def = max_cord * 0.005
    ang_def = 0.5   # radians

    gmsh.initialize()
    # OCCTargetUnit omitted — FreeCAD STEP files are already in mm
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add(label)
    gmsh.model.occ.importShapes(step_path)
    # Note: gmsh.model.occ.healShapes() would be the preferred way to remove
    # short CAD edges before meshing, but it corrupts surface 58 of BottomTub
    # ("Could not fix wire in surface 58") on these STEP files.
    # Post-mesh repair via _repair_mesh() is used instead.
    gmsh.model.occ.synchronize()

    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", max_cord / 10)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 10)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", 10)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 1.0)
    gmsh.option.setNumber("Mesh.StlLinearDeflection", lin_def)
    gmsh.option.setNumber("Mesh.StlAngularDeflection", ang_def)
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
    print(f"  → {len(verts)} verts, {len(facets)} triangles")
    return verts, facets


# ── Variant 2: Gmsh full, new defaults ───────────────────────────────────
def mesh_gmsh_full(step_path, label):
    """Gmsh full with updated defaults: lm=maxCord/10, lc=10 (per 2π), lp=10."""
    print(f"\n[gmsh_full/{label}] meshing...")
    gmsh.initialize()
    # OCCTargetUnit omitted — FreeCAD STEP files are already in mm
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add(label)
    gmsh.model.occ.importShapes(step_path)
    # Note: gmsh.model.occ.healShapes() would be the preferred way to remove
    # short CAD edges before meshing, but it corrupts surface 58 of BottomTub
    # ("Could not fix wire in surface 58") on these STEP files.
    # Post-mesh repair via _repair_mesh() is used instead.
    gmsh.model.occ.synchronize()

    xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
    lm = max(xmax-xmin, ymax-ymin, zmax-zmin) / 10.0
    lc = 10
    print(f"  lm={lm:.1f} mm, lc={lc} (elements/2π)")

    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", lm)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", lc)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", lc)
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
    print(f"  → {len(verts)} verts, {len(facets)} triangles")
    return verts, facets


# ── Variants 3 & 4: Gmsh Min (STL → recombine) ───────────────────────────
def mesh_gmsh_min(step_path, label, keep_quads=False):
    """
    STL → Gmsh recombine.
    keep_quads=False: split non-planar quads into 2 triangles (gmsh_min)
    keep_quads=True:  keep all quads as-is (gmsh_min_quads)
    """
    tag = "gmsh_min_quads" if keep_quads else "gmsh_min"
    print(f"\n[{tag}/{label}] meshing...")

    # Step 1: produce STL via Gmsh OCC with fine tessellation
    max_cord = get_bbox_maxcord(step_path)
    lin_def = max_cord * 0.005
    ang_def = 0.5

    tmpstl = tempfile.NamedTemporaryFile(suffix=".stl", delete=False).name

    gmsh.initialize()
    # OCCTargetUnit omitted — FreeCAD STEP files are already in mm
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("stl_gen")
    gmsh.model.occ.importShapes(step_path)
    # Note: gmsh.model.occ.healShapes() would be the preferred way to remove
    # short CAD edges before meshing, but it corrupts surface 58 of BottomTub
    # ("Could not fix wire in surface 58") on these STEP files.
    # Post-mesh repair via _repair_mesh() is used instead.
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", max_cord / 10)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 10)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 1.0)
    gmsh.model.mesh.generate(2)
    gmsh.write(tmpstl)
    gmsh.finalize()

    # Step 2: load STL, remove duplicates, recombine
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

    # Collect triangles (type 2) and quads (type 3)
    etypes, _, enodes = gmsh.model.mesh.getElements(-1, -1)
    tri_raw  = []
    quad_raw = []
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
    planar_quads = non_planar = 0

    for q in quad_raw:
        v0, v1, v2, v3 = vtx[q[0]], vtx[q[1]], vtx[q[2]], vtx[q[3]]
        if keep_quads or is_planar_quad(v0, v1, v2, v3):
            facets_raw.append(q)
            planar_quads += 1
        else:
            # Split into 2 triangles
            facets_raw.append((q[0], q[1], q[2]))
            facets_raw.append((q[0], q[2], q[3]))
            non_planar += 1

    verts, facets = _compact(vtx, facets_raw)
    verts, facets = _repair_mesh(verts, facets)
    tri  = sum(1 for f in facets if len(f) == 3)
    quad = sum(1 for f in facets if len(f) == 4)
    print(f"  → {len(verts)} verts, {tri} tri, {quad} quad "
          f"(planar quads kept={planar_quads}, split={non_planar})")
    return verts, facets


# ── GDML writer ───────────────────────────────────────────────────────────
def write_gdml(meshes, out_path):
    """meshes = list of (label, verts, facets)"""
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

    # GDML requires volumes to be defined before they are referenced.
    # Component volumes (LV_TopTub etc.) must appear before WorldLV.
    # Build WorldLV last, collecting physvol entries as we go.
    physvols = []   # list of label strings to place into WorldLV

    for label, verts, facets in meshes:
        vname = f"v{label}_"
        solid_name = f"Tess_{label}"

        # Deduplicate vertices by formatted coordinate key, remap facet indices
        coord_key_to_out = {}   # coord_key -> output index
        remap = {}              # original index -> output index
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
            if len(set(rf)) < len(rf):   # degenerate after coord dedup
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
        if skipped:
            print(f"  [{label}] dropped {skipped} degenerate facets after coord dedup")

        lv = ET.SubElement(structure, "volume", {"name": f"LV_{label}"})
        ET.SubElement(lv, "materialref", {"ref": MATERIAL})
        ET.SubElement(lv, "solidref",    {"ref": solid_name})
        physvols.append(label)

    # WorldLV defined last so all component volumes are already defined above
    world_lv = ET.SubElement(structure, "volume", {"name": "WorldLV"})
    ET.SubElement(world_lv, "materialref", {"ref": AIR})
    ET.SubElement(world_lv, "solidref",    {"ref": "WorldBox"})
    for label in physvols:
        pv = ET.SubElement(world_lv, "physvol", {"name": f"PV_{label}"})
        ET.SubElement(pv, "volumeref", {"ref": f"LV_{label}"})

    setup = ET.SubElement(gdml, "setup", {"name": "Default", "version": "1.0"})
    ET.SubElement(setup, "world", {"ref": "WorldLV"})

    raw    = ET.tostring(gdml, encoding="unicode")
    pretty = minidom.parseString(raw).toprettyxml(indent="  ")
    with open(out_path, "w") as fh:
        fh.write(pretty)
    size_mb = os.path.getsize(out_path) / 1e6
    tri  = sum(sum(1 for f in facets if len(f) == 3) for _, _, facets in meshes)
    quad = sum(sum(1 for f in facets if len(f) == 4) for _, _, facets in meshes)
    print(f"  Wrote {out_path}  ({size_mb:.1f} MB)  tri={tri}  quad={quad}")


# ── Main ──────────────────────────────────────────────────────────────────
VARIANTS = [
    ("fc_default",      lambda p, l: mesh_fc_default(p, l)),
    ("gmsh",            lambda p, l: mesh_gmsh_full(p, l)),
    ("gmsh_min",        lambda p, l: mesh_gmsh_min(p, l, keep_quads=False)),
    ("gmsh_min_quads",  lambda p, l: mesh_gmsh_min(p, l, keep_quads=True)),
]

if __name__ == "__main__":
    import json
    stats = {}   # variant_name -> {tri, quad, total, size_mb}

    for variant_name, mesh_fn in VARIANTS:
        print(f"\n{'='*60}")
        print(f"Variant: {variant_name}")
        print('='*60)
        meshes = []
        for fname, label in STEPS:
            path = f"{STEP_DIR}/{fname}"
            verts, facets = mesh_fn(path, label)
            meshes.append((label, verts, facets))

        out = f"{STEP_DIR}/1485_{variant_name}_both-worldVOL.gdml"
        write_gdml(meshes, out)

        tri  = sum(sum(1 for f in facets if len(f) == 3) for _, _, facets in meshes)
        quad = sum(sum(1 for f in facets if len(f) == 4) for _, _, facets in meshes)
        size_mb = os.path.getsize(out) / 1e6
        stats[variant_name] = {"tri": tri, "quad": quad,
                                "total": tri + quad, "size_mb": round(size_mb, 1)}

    stats_path = os.path.join(os.path.dirname(__file__), "mesh_stats.json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"\nMesh stats written to {stats_path}")
    print("\n\nAll done.")
