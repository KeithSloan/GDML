# Testing the GDML Workbench

Testing uses the companion repository
[FreeCAD_GDML_Test_Collection](https://github.com/KeithSloan/FreeCAD_GDML_Test_Collection):
FreeCAD test files, GDML test files, committed baselines (exported GDML and
centres of gravity), and an automated harness under
[`autotest/`](https://github.com/KeithSloan/FreeCAD_GDML_Test_Collection/tree/test_FC_1.1.4/autotest)
(see its README for every option). Each FreeCAD version is tested on its own
branch of the test repo:

| FreeCAD | test repo branch | results below |
|---|---|---|
| 1.1.3 | [`test_FC_1.1.3`](https://github.com/KeithSloan/FreeCAD_GDML_Test_Collection/tree/test_FC_1.1.3) | [FreeCAD 1.1.3](#freecad-113--october-2026) |
| 1.1.4 | [`test_FC_1.1.4`](https://github.com/KeithSloan/FreeCAD_GDML_Test_Collection/tree/test_FC_1.1.4) | [FreeCAD 1.1.4](#freecad-114--october-2026) |
| 26.3 | to do | |

## What is tested

For each FreeCAD test file (`FC_test_files/`), in a fresh FreeCAD instance:

1. **open** and recompute; flag missing addons (Fasteners, Gears), invalid
   objects and red Report View errors;
2. **export** to GDML; read the export log (see below);
3. **COG**: volume, centre of mass and moments of inertia of every exported
   volume with `calcCenterOfMass.py` (objects with `exportFlag = False` are
   skipped, as in export).

For each GDML test file (`test_gdml_files/`): **import**, then **re-export**
(round trip).

Results are compared with the committed baselines and between FreeCAD
versions (`report.md`).

### Geant4

Every exported GDML file is then loaded into Geant4 with Munther Hindi's
`load_gdml_color -printCM` (source in the test repo,
`MH_G4_Example/MH_G01`), which estimates each placed volume's volume, centre
of mass and inertia by Monte Carlo. `autotest/geant4_cog.py` compares the
totals with FreeCAD's (`geant4_cog.md`):

| | tolerance |
|---|---|
| volume | 1 % |
| centre of mass | 1 % of the radius of gyration (never tighter than the printed precision) |
| inertia (diagonal, about the origin) | 2 % of the largest term |

Status per file: `MATCH`, `DIFF`, or `NO_GEANT4` (Geant4 rejected the file or
the checker failed; the reason is in `geant4_out/<file>.out`).

### Export log

Since `fix-export-refs`, every `.gdml` export writes `<file>.gdml.log` beside
the exported file (module `GDMLLog`): start/finish lines plus any warnings
and errors, which also appear in the Report View. If the folder is not
writable the log goes to `<FreeCAD user data>/GDML/logs/`. It can be turned
off with the GDML preference `ExportLogFile`. The harness reads it and marks
files that export with warnings as `OK_WITH_WARNINGS`.

The first warning it carries: a daughter volume extending outside its
mother's solid, which Geant4 would otherwise reject with *Overlap with mother
volume*.

## Running the tests

macOS and Linux (bash). Windows is not supported by the harness yet.

```bash
# 1. FreeCAD's Mod/GDML must be this checkout (symlink), so a test run uses
#    whatever branch is checked out here
cd FreeCAD_GDML_Test_Collection
GDML_REPO=~/Workbenches/GDML autotest/check_setup.sh --link

# 2. list FreeCAD versions in autotest/versions.conf ("label | path"), then
autotest/run_versions.sh                       # all files, all versions
AT_ONLY='Loft*,arrayTest-1.FCStd' autotest/run_versions.sh   # a few files
# Linux without a display: AT_HEADLESS_X=1

# 3. Geant4 load + COG comparison on a finished run
autotest/run_geant4.sh autotest_results/<run>
```

### Geant4 for the comparison

conda-forge has Geant4 with its data sets (macOS arm64 and Linux):

```bash
conda create -n g4 -c conda-forge geant4 cmake make cxx-compiler expat zlib freetype
conda activate g4
cd FreeCAD_GDML_Test_Collection/MH_G4_Example/MH_G01
cmake -S . -B build-conda -DGeant4_DIR=$CONDA_PREFIX/lib/cmake/Geant4 \
      -DCMAKE_PREFIX_PATH=$CONDA_PREFIX -DCMAKE_FIND_FRAMEWORK=LAST \
      -DCMAKE_BUILD_TYPE=Release
cmake --build build-conda -j 8
```

`expat`, `zlib` and `freetype` are needed for the headers (conda-forge splits
them from the runtime libraries); without them CMake finds older copies in the
macOS SDK and stops. With conda's Geant4 the data paths are set by
`conda activate`, not `geant4.sh`; `run_geant4.sh` activates
`~/miniconda3/envs/g4` itself (override with `AT_G4_CONDA`, or `AT_G4_ENV`
for a `geant4.sh` install).

## FreeCAD 1.1.3 — October 2026

macOS 26.1 arm64, FreeCAD 1.1.3 (Python 3.11, OCC 7.8.1), Geant4 11.4.3
(conda-forge); test repo branch
[`test_FC_1.1.3`](https://github.com/KeithSloan/FreeCAD_GDML_Test_Collection/tree/test_FC_1.1.3), GDML branch
`fix-export-refs`. A subset was also run on Linux (conda-forge FreeCAD 1.1.3,
Python 3.14, OCC 7.9.3) with identical results.

**FreeCAD side:** 98/98 files OK (open, export, COG, import, round trip), no
Report View errors. 17 files differ from the committed baselines, which
predate current GDML; the Geant4 comparison is the reference for those.

**Geant4:** 49 MATCH, 24 DIFF, 7 not compared.

Fixed during this round:

| problem | fix |
|---|---|
| `matricesandloops.gdml` import: `KeyError: 'm'` (matrix references in sheet expressions) | GDML `fix-sheet-expression-matrix` |
| `AssemblyTest`: assembly named `Tube1`, placed as `Tube` | assembly named with `getVolumeName()` |
| `arrayTest-1` (array of an array of a Part): multiUnion referring to an unwritten solid | arrays of arrays of Parts exported as nested assemblies |
| `importObjTest-edited`: labels ending in a carriage return gave `solidref "X&#13;"` for solid `X` | names cleaned with `cleanGDMLname()` everywhere |
| `COG_Expanded_simple_array`: glass plate 2 mm above its LYSO mother | test file corrected; exporter now warns |
| `arrayTest-1-a`: Draft array of a Part has no shape in 1.1 | test file repaired; COG script handles arrays of Parts |
| COG counted objects with `exportFlag = False` | COG script skips them |
| `arrayTest-7_scaled`: COG depended on files opened earlier in the session (OCC) | harness uses a fresh FreeCAD per file |

Open:

- `COG_Expanded_simple_array`: duplicated array element, and border surfaces
  that refer to physvols which are not exported or are named differently
  inside assemblies (to discuss with Munther).
- `mirrorTest-*` (reflected placements) and `Target-Unmeshed`: Munther's
  checker divides by zero; geometry loads.
- Large Geant4 differences to investigate: `COG_TestExtrudeSketchBox`
  (volume 64 %), `MultiCommon` (60 %), `orthoArray-of-polarArray-of-Part`
  (13 %), `orthoArray-of-Container` (4 %), the scaled clones
  `arrayTest-6_scaled` / `arrayTest-7_scaled`, `PathArray2` (inertia).
- 0.5–1 mm centre-of-mass differences on nested placements
  (`polarArray-of-Part*`, `importObjTest-*`): check whether the checker
  composes nested transforms (`getMoments()` passes only the local
  transform to daughters) before treating them as export errors.
- Smaller differences (1–3 %) on tessellated / Monte Carlo cases are probably
  within noise; tolerances may need loosening.

## FreeCAD 1.1.4 — October 2026

Same Mac, FreeCAD 1.1.4 (Python 3.11, OCC 7.8.1, as 1.1.3), GDML `Main`
`3b44c561`, test repo branch
[`test_FC_1.1.4`](https://github.com/KeithSloan/FreeCAD_GDML_Test_Collection/tree/test_FC_1.1.4), run `fc114`, compared file by
file with the 1.1.3 run (`fix-refs-all`).

**Same as 1.1.3.** 98/98 files OK, no Report View errors; exported GDML and
COGs byte-identical to 1.1.3 except `COG_Expanded_simple_array` (test file
and COG script changed in between) and last-digit float noise in
`extrudedParabola-2`. Geant4: 49 MATCH, 24 DIFF, 7 not compared, no file
changed status.

**New warnings (from the overlap check, not from 1.1.4):** five files were
`OK_WITH_WARNINGS`. The check was then tightened (branch
`fix-overlap-check`: daughter solids only, confirmed by a boolean cut), which
removed two false warnings (`PathArray2`, where a 2D path was counted as a
daughter, and bounding-box slack on `scaledTube.gdml`). The remaining ones
are real:

| file | warning | confirmed by |
|---|---|---|
| `PathArray` | `Part` 6.4 mm outside the world (25 mm³) | exported world 26×26×31.2 mm; array reaches z = 22 |
| `array-of-array-of-solid` | `Part001` 105 mm outside the world (24 320 mm³) | world ±50 mm; array reaches 155 mm |
| `assembly.gdml` (round trip) | `AssemblyVol` 137.5 mm outside `World` | Geant4: protrusion 13.749 cm, also in the original file |

Geant4 loads `PathArray` and `array-of-array-of-solid` without reporting the
overlap: its check samples surface points and misses these multiUnions, so
the warning is the only signal. Their world boxes need enlarging in the test
files. `assembly.gdml` and `scaledTube.gdml` (sibling overlaps) have the
overlaps in the original files, so the round trip is faithful.

## TODO

- [x] **FreeCAD 1.1.4**: full run, Geant4 comparison, compare with 1.1.3.
- [ ] **FreeCAD 26.3** (rc2 now, then release): full run and Geant4
      comparison.
- [ ] Enlarge the world boxes of `PathArray` and `array-of-array-of-solid`.
- [ ] Export log on Windows (written to be portable; not yet run there).
- [ ] Resolve the open items above; refresh the committed baselines once the
      exports are confirmed against Geant4.
- [ ] Move the remaining exporter `print()` diagnostics to `GDMLLog`.
