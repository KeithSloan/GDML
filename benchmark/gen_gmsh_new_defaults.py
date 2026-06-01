#!/usr/bin/env python3
"""
Generate 1485_gmsh_new_defaults_both-worldVOL.gdml
Uses Gmsh to mesh both STEP files with object-relative characteristic length
(maxCord/10) matching FreeCAD's default mesher density.

Run with FreeCAD's Python so Gmsh is the same version as the workbench:
    /Applications/FreeCAD.app/Contents/Resources/bin/python3 gen_gmsh_new_defaults.py
Or with system Python if gmsh is installed there:
    python3 gen_gmsh_new_defaults.py
"""

import gmsh
import math
import xml.etree.ElementTree as ET
from xml.dom import minidom

STEP_DIR  = "/Users/ksloan/github/CAD_Files_Git/GDML/1485_step"
OUT_FILE  = f"{STEP_DIR}/1485_gmsh_new_defaults_both-worldVOL.gdml"
MATERIAL  = "G4_STAINLESS-STEEL"
AIR       = "G4_AIR"
WORLD_DIM = 1000   # mm half-lengths of world box

STEPS = [
    ("1485 Top Tub.STEP",    "TopTub"),
    ("1485 Bottom Tub.STEP", "BottomTub"),
]


def mesh_step(step_path, label):
    """Mesh a STEP file with Gmsh and return (vertices, facets)."""
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setString("Geometry.OCCTargetUnit", "mm")
    gmsh.model.add(label)
    gmsh.model.occ.importShapes(step_path)
    gmsh.model.occ.synchronize()

    # Compute bounding box to get characteristic length
    xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
    max_cord = max(xmax - xmin, ymax - ymin, zmax - zmin)
    lm = max_cord / 10.0   # same as GmshUtils.getMeshLen()
    lc = 10                 # elements per 2π (curvature refinement)
    print(f"[{label}] bbox max={max_cord:.1f} mm → lm={lm:.1f} mm, lc={lc}")

    gmsh.option.setNumber("Mesh.Algorithm",  6)       # Frontal-Delaunay
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", lm)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", lc)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints",    lc)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 1.0)

    gmsh.model.mesh.generate(2)
    gmsh.model.mesh.renumberNodes()

    # Extract nodes
    node_tags, coords, _ = gmsh.model.mesh.getNodes()
    # Build 0-indexed vertex list in tag order
    max_tag = max(node_tags)
    vertices = [None] * (max_tag + 1)
    for tag, (x, y, z) in zip(node_tags, zip(coords[0::3], coords[1::3], coords[2::3])):
        vertices[tag] = (x, y, z)

    # Extract triangles (type 2)
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(2)
    facets = []
    for etype, nodes in zip(elem_types, elem_node_tags):
        if etype == 2:   # triangle
            for i in range(0, len(nodes), 3):
                facets.append((int(nodes[i]), int(nodes[i+1]), int(nodes[i+2])))

    # Compact vertices to only used ones
    used_tags = set()
    for f in facets:
        used_tags.update(f)
    sorted_tags = sorted(used_tags)
    old2new = {old: new for new, old in enumerate(sorted_tags)}
    compact_verts = [vertices[t] for t in sorted_tags]
    compact_facets = [(old2new[a], old2new[b], old2new[c]) for a, b, c in facets]

    print(f"[{label}] {len(compact_verts)} verts, {len(compact_facets)} triangles")
    gmsh.finalize()
    return compact_verts, compact_facets


def write_gdml(meshes, out_path):
    """Write a minimal GDML with tessellated solids for each mesh."""
    gdml = ET.Element("gdml", {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation":
            "http://service-spi.web.cern.ch/service-spi/app/releases/GDML/"
            "schema/gdml.xsd"
    })

    define = ET.SubElement(gdml, "define")
    materials = ET.SubElement(gdml, "materials")
    solids    = ET.SubElement(gdml, "solids")
    structure = ET.SubElement(gdml, "structure")

    # World box
    ET.SubElement(solids, "box", {
        "name": "WorldBox", "x": str(WORLD_DIM*2),
        "y": str(WORLD_DIM*2), "z": str(WORLD_DIM*2), "lunit": "mm"
    })

    world_lv = ET.SubElement(structure, "volume", {"name": "WorldLV"})
    ET.SubElement(world_lv, "materialref", {"ref": AIR})
    ET.SubElement(world_lv, "solidref",    {"ref": "WorldBox"})

    for label, verts, facets in meshes:
        solid_name = f"Tess_{label}"
        vname = f"v{label}_"

        # Define vertices
        for i, (x, y, z) in enumerate(verts):
            ET.SubElement(define, "position", {
                "name": vname + str(i), "unit": "mm",
                "x": f"{x:.6g}", "y": f"{y:.6g}", "z": f"{z:.6g}"
            })

        # Tessellated solid
        tess = ET.SubElement(solids, "tessellated", {"name": solid_name})
        for a, b, c in facets:
            ET.SubElement(tess, "triangular", {
                "vertex1": vname + str(a),
                "vertex2": vname + str(b),
                "vertex3": vname + str(c),
                "type": "ABSOLUTE"
            })

        # Logical volume + placement
        lv = ET.SubElement(structure, "volume", {"name": f"LV_{label}"})
        ET.SubElement(lv, "materialref", {"ref": MATERIAL})
        ET.SubElement(lv, "solidref",    {"ref": solid_name})

        pv = ET.SubElement(world_lv, "physvol", {"name": f"PV_{label}"})
        ET.SubElement(pv, "volumeref", {"ref": f"LV_{label}"})

    # World setup
    setup = ET.SubElement(gdml, "setup", {"name": "Default", "version": "1.0"})
    ET.SubElement(setup, "world", {"ref": "WorldLV"})

    # Pretty-print
    raw = ET.tostring(gdml, encoding="unicode")
    pretty = minidom.parseString(raw).toprettyxml(indent="  ")
    with open(out_path, "w") as f:
        f.write(pretty)
    import os
    size_mb = os.path.getsize(out_path) / 1e6
    print(f"\nWritten: {out_path}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    meshes = []
    for fname, label in STEPS:
        path = f"{STEP_DIR}/{fname}"
        verts, facets = mesh_step(path, label)
        meshes.append((label, verts, facets))

    write_gdml(meshes, OUT_FILE)
    total_facets = sum(len(f) for _, _, f in meshes)
    print(f"Total triangles: {total_facets}")
