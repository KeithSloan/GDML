# testReplica — command, wiring, and test files

A prototype workbench command that **analyses a selected group of placements and
reports** whether it can become a `G4PVReplica` or `G4PVParameterised`, with a
build action for the actionable cases. Geometry is a cut-down subset of one half
of the LHCb VELO R-sensor stack (from `Utils/lhcbvelo.gdml`).

## Install into the workbench

1. Copy `testReplica.py` into `freecad/gdml/`.
2. Replace `freecad/gdml/init_gui.py` with the `init_gui.py` here (three added
   lines, each marked `# testReplica:`): it imports the module (which self-
   registers `GDML_TestReplica`) and adds the command to the **GDML menu** and
   the **GDMLTools toolbar**, next to *Analyse Shape → GDML*.

The command reuses the Analyse-Shape icon for now (`GDMLAnalyseShape`); add a
dedicated icon later.

## The command

Select ≥ 2 placements of (nominally) the same volume, run **Test Replica**. It
classifies and reports:

    Param Replica                  identical daughters + regular lattice
                                     -> enabled action: build + tag <replicavol>
    Param Volume
       identical Daughters         identical daughters, irregular placement
                                     -> enabled action: build + tag <paramvol>
       Complex                     daughters differ (size/shape/material)
                                     -> report only (App::Links need identical shapes)

The dialog shows the result with an **action button enabled for the first two
categories** and a **Close** button; for Complex the action is disabled. The
build reuses copy-0 as the base, consumes the other originals into **locked
App::Links**, and tags the group (`ExportAs`/`Count`/`Pitch`/`Axis`) for export.

Classification lives in the pure, unit-testable `classify(daughters, points)`
(`replica` / `paramvol_identical` / `complex` / `none`); the FreeCAD/Qt glue is
separated below it. `daughter_signature()` builds a shape+material signature so
"identical daughter" is a real geometric test, not a name match.

## Test files

Each is **individual placements**; its header states the category testReplica
should report. Verified by `verify_classification.py`.

| File | Copies | Expected report |
|------|--------|-----------------|
| `VeloFlat.gdml` | 21 identical, full R-side (16 regular + 5 irregular) | Param Volume / identical Daughters |
| `TestReplica.gdml` | 16 identical, uniform 30 mm pitch | **Param Replica** (linear, pitch 30, z) |
| `VeloTestParamVol.gdml` | 9 identical, irregular spacing | Param Volume / identical Daughters |
| `ComplexParamVol.gdml` | 8 graded sensors (rmax varies per copy) | Param Volume / **Complex** |

`TestReplica.gdml` and `ComplexParamVol.gdml` drop the `Velo` prefix: a uniform-
pitch single replica and graded sensor sizes are synthetic — not valid VELO
geometry. Only `VeloFlat` uses the real lhcbvelo.gdml positions.

Sensor: silicon half-disk `tube` rmin 8, rmax 42 (graded in the Complex file),
thickness 0.3 mm, phi 0–180°.

## Verify

    python3 verify_classification.py

Parses each file, rebuilds `(signatures, points)` from its physvols, runs
`classify`, and asserts the reported category matches the file's intent. All four
currently pass.

`gen_velo_tests.py` regenerates the four files. The optional GEANT4 overlap
harness in `validate_geant4/` still builds against any of the files; pyg4ometry
(if you install it — needs CGAL/gmp/mpfr, so a source build) gives an independent
mesh overlap check but is not required here.

## Notes

* App::Links carry per-copy placement but share the base shape → identical
  daughters only; a Complex paramvol (per-copy dimensions/material) needs a
  richer representation, hence report-only.
* Replica/paramvol both keep per-copy identity (copy number), so
  sensitive-detector readout is preserved — unlike a boolean MultiFuse, which
  merges the sensors into one volume and destroys per-station hits.

## Next steps

1. Add a `paramvol`/`replicavol` **emitter** to export — `processArrayPart`
   currently expands arrays back to explicit `<physvol>` and never emits either,
   so this closes the import↔export asymmetry.
2. Add the replica slot-mother synthesis and an inverse **explode** command.
3. Give the command its own icon.
