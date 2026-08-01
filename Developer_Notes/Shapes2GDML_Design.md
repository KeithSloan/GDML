# Shapes2GDML — Design Notes

_Branch: Shapes2GDML.  Modules: freecad/gdml/BRepdeconstruction.py,
shapeAnalysis.py; command in GDMLCommands.py (AnalyseShape / "Analyse Shape ->
GDML")._

## Guiding principle

**Prefer native GDML primitives over tessellation — always.**

In particular, **native cylinders and spheres are always preferred over a
tessellated (meshed) representation**, even when the surrounding body cannot be
represented analytically and must itself be tessellated.  A part is therefore
decomposed into its analytic features (cylinders, spheres, cones, boxes) plus,
only as a last resort, a tessellated remainder.

Rationale: analytic solids are exact and are cheaper for Geant4 navigation than
a fine mesh; tessellation introduces faceting error and is slower.  So we keep
everything we can recognise analytic and tessellate as little as possible.

Order of preference for any solid / feature:
1. Single native primitive (box / tube / cone / sphere).
2. CSG of native primitives (body +/- cylinders/spheres via boolean).
3. Tessellation — only the residual that is genuinely not analytic.

## Recovery pipeline (per solid)

1. **Primitive recognition** — whole solid is one box / tube / cone / sphere.
2. **CSG recovery** (`recover_csg_tree`):
   - internal cylinders (REVERSED orientation) -> holes -> subtract.
   - external cylinders (FORWARD orientation) -> bosses/pins -> union
     (also picks up edge fillets; classified by axis vs bores/edges).
   - body envelope = solid with holes filled (and bosses stripped) -> recognise
     as a primitive; if not a primitive, tessellate the residual core only.
   - repeated identical holes -> pattern detection (linear/grid/polar) ->
     Draft array (>= MIN_ARRAY_NUMBER) or MultiFuse -> one cut per pattern.
3. **Tessellation fallback** — residual body/features that are not analytic.

## Key parameters (eventually workbench preferences)

- `USE_DRAFT_ARRAYS` (True): regular patterns build as Draft arrays.
- `MIN_ARRAY_NUMBER` (4): min members before a pattern becomes an array;
  smaller groups are individual cuts (not spurious MultUnions).
- `DEFAULT_MATERIAL` ("G4_Galactic"): placeholder for recovered primitives.

## Naming of built objects (source label e.g. "TopCover")

- top-level result: `GDML_TopCover`
- inner cuts (descending): `GDML_TopCover_1_Cut`, `GDML_TopCover_2_Cut`, ...
- body: `GDML_TopCover_Body`
- tube unions / arrays: `GDML_MultUnion`

## Worked example — ConnectorPart1 (Part__Feature044)

22 faces = 11 cylinders + 11 planes.  bbox 18 x 11.5 x 18.
- holes (internal, subtract): r=1.2 x4 (mounting grid, blind), r=4.5 x1 (bore, through).
- external cylinders (all on the Y / bore axis):
  - r=6.0 x2  -> face bosses around the bore (union).
  - r=2.2 x4  -> raised pads around the mounting holes (union).
- Target reconstruction (fully native, no tessellation):
  Box core  UNION  6 cylinder bosses  MINUS  5 cylinder holes.

## Status

- Done: primitive recognition (box/tube/cone/sphere); hole recovery + patterns
  + Draft arrays; fill-and-recognise body (exact primitive for box bodies);
  external-cylinder detection + report; per-source naming.
- Next: strip detected bosses to reveal the core body; build bosses as native
  cylinder unions; tessellate the core only if it is not a recognised primitive.
