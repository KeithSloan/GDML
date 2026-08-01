# Shapes2GDML (Experimental)

> **Status: EXPERIMENTAL.** Shapes2GDML converts imported CAD solids into
> native GDML. It works on a growing set of parts but is **not yet validated
> end-to-end**. In particular the **GDML export to Geant4 is currently
> untested** — it assumes the workbench's existing exporter is sufficient for
> the objects produced (GDMLBox / GDMLTube / GDMLCone / GDMLSphere,
> Part::Cut / Part::MultiFuse / Draft arrays, GDMLTessellated). Treat all
> output as provisional until it has been round-tripped through Geant4.

## What it does

Imported STEP/IGES/BREP parts arrive as boundary-representation (B-rep)
solids. The GDML/Geant4 world prefers **constructive solid geometry** built
from analytic primitives. Shapes2GDML analyses a selected solid and
reconstructs it, as far as possible, from native GDML primitives, falling
back to a tessellated (meshed) solid only for the parts it cannot recognise.

Command: **GDML -> Analyse Shape -> GDML** (also in the GDML toolbar).
Select one or more objects and run it. The dialog reports the analysis and
offers actions, enabled according to what was found:

- **Convert to Native** — build native GDML primitives (enabled when every
  solid is directly a box / tube / cone / sphere, or after Recover CSG).
- **Recover CSG** — decompose a composite analytic solid into a body plus
  cylindrical features, then build it (enabled for composite analytic solids).
- **Tessellate** — fall back to the workbench's mesh path (always available).

## Guiding principle: prefer native primitives over tessellation

Native primitives (box, **tube/cylinder**, cone, **sphere**) are always
preferred over a tessellated representation, **even when the surrounding body
must itself be tessellated**. A part is decomposed into its analytic features
plus, as a last resort, a tessellated remainder.

Order of preference for any solid or feature:

1. A single native primitive.
2. CSG of native primitives (body +/- cylinders/spheres via boolean).
3. Tessellation — only the residual that is genuinely not analytic.

## Recovery pipeline

1. **Primitive recognition** — the whole solid is one box / tube / cone / sphere.
2. **CSG recovery** (composite analytic solids):
   - internal cylinders (reversed orientation) -> holes -> native tube, subtracted;
   - external cylinders (forward orientation) -> bosses -> native tube, unioned;
   - the body envelope (holes filled) is recognised as a primitive if it is one,
     otherwise the **de-bossed core is tessellated** and the bosses/holes are
     kept native (nothing native is ever fused into the mesh);
   - repeated identical holes are detected as patterns (linear / grid / polar /
     cluster) and built as a Draft array (>= `MIN_ARRAY_NUMBER`) or a
     Part::MultiFuse -> one boolean cut per pattern.
3. **Tessellation fallback** — the residual body/feature that is not analytic.

Built objects are named from the source label: `GDML_<Label>` (top),
`GDML_<Label>_<n>_Cut`, `GDML_<Label>_Body`, and `GDML_MultUnion`.

## Tessellation versus boolean (CSG) — trade-offs

Both are valid GDML/Geant4 representations; they behave differently:

- **Analytic primitives** (`G4Box`, `G4Tubs`, `G4Cons`, `G4Sphere`) have
  closed-form inside/distance queries. They are **exact** and fast for Geant4
  navigation.
- **Booleans** (`G4SubtractionSolid`, `G4UnionSolid`) are exact but each query
  recurses into the constituents. A shallow tree (a body and a few features) is
  typically faster and far more compact than a fine mesh; a **deep** boolean
  tree (dozens of nested booleans) can erode that advantage and can provoke
  tracking issues near coincident surfaces. Shapes2GDML keeps the tree shallow
  by collapsing patterned features into one cut per pattern (array / multiUnion).
- **Tessellated solids** (`G4TessellatedSolid`) approximate curved surfaces
  with flat facets. They are the most general but the slowest to track
  (many-facet point/distance tests, even with voxelisation) and introduce
  **faceting error**. They are used only where no analytic form is recovered.

Rule of thumb: for a part that reduces to a handful of primitive booleans the
CSG form usually wins on both **accuracy and speed**; for a genuinely freeform
body a tessellated core is unavoidable, but its analytic features (cylinders,
spheres, holes, bosses) are still kept native.

## Accuracy — cylinders and spheres

A tessellated cylinder or sphere is a facet approximation: its volume and
surface deviate from the true shape, and the stair-stepped surface can perturb
tracking and surface-area-dependent quantities. A `G4Tubs` / `G4Sphere` is
exact. This is why **cylinders and spheres are always recovered natively when
possible** — a part dominated by curved faces both meshes expensively and loses
accuracy, so keeping those faces analytic is a double win. The remaining
tessellated core carries only the faces that are genuinely freeform.

## Current limitations / TODO

- **Geant4 export is untested.** The produced objects are assumed to export
  through the existing GDML exporter; this must be validated by round-tripping
  through Geant4.
- **More test cases needed.** Validated so far on a small set (box covers;
  a bossed connector; a cylinder-with-flats connector). Needs a broader suite
  across primitive, CSG and freeform parts.
- **Geant4 performance comparison runs needed** — measure tracking
  speed / memory for native-CSG vs tessellated versions of the same parts to
  confirm the trade-offs above in real workloads.
- Body recovery: a cylinder that is the body's own surface (not a separable
  feature) is tessellated with the body; recognising e.g. a
  cylinder-with-flats as `tube & box` analytically is future work.
- Draft **polar** arrays rotate about the working-plane normal; polar patterns
  not on that axis need verification.
- `MIN_ARRAY_NUMBER`, `USE_DRAFT_ARRAYS`, `DEFAULT_MATERIAL` are module
  constants; they should become workbench preferences.

## Related files

- `freecad/gdml/BRepdeconstruction.py` — recognition + CSG recovery + build.
- `freecad/gdml/shapeAnalysis.py` — per-solid analysis.
- `freecad/gdml/GDMLCommands.py` — the Analyse Shape -> GDML command + dialog.
- `Developer_Notes/Shapes2GDML_Design.md` — design notes.
