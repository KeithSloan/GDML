# GDML Workbench — Developer Guide (CLAUDE.md)

This file is the primary orientation document for AI coding assistants working in this repo.

---

## Project Overview

A FreeCAD workbench for viewing, creating, editing, and exporting geometry described in GDML (Geometry Description Markup Language) for use in GEANT4, ROOT, and OpenMC Monte Carlo simulation frameworks.

All Python lives under `freecad/gdml/`.

---

## Key Files

| File | Role |
|------|------|
| `importGDML.py` | GDML import, document structure creation, `processGDML`, `processGEANT4`, `processReactor`, `migrateReactorSubGroups` |
| `exportGDML.py` | GDML export — solids, materials, tessellation, Gmsh shapes |
| `exportOpenMC.py` | OpenMC XML export (alpha) |
| `GDMLObjects.py` | Proxy classes for all GDML solid types; `MaterialsList`, `GroupedMaterials`, `addMaterialsFromGroup`, `rebuildMaterialsList` |
| `GDMLMaterials.py` | `getMaterialsList`, `newGetGroupedMaterials` — material lists for UI |
| `GDMLCommands.py` | All FreeCAD GUI commands and dialogs (toolbar, menus) |
| `GmshUtils.py` | Gmsh tessellation helpers (`GmshTessellate`, `GmshMinTessellate`) |
| `init_gui.py` | Workbench activation, toolbar/menu registration, `MyObserver` |
| `GDMLShared.py` | Shared globals (trace, define, printverbose) |
| `Resources/` | Icons, `Default.gdml`, `Geant4Materials.xml`, `NIST_Isotopes.xml`, `ReactorMaterials.xml` |

---

## FreeCAD Document Structure

When a GDML document is created or opened the workbench populates these top-level FreeCAD groups:

```
Isotopes/
    ReactorMaterials/    ← OpenMC-only: U234, U235, U238
Elements/
    ReactorMaterials/    ← OpenMC-only: enriched_U1 … enriched_U20
Materials/
    Geant4/              ← G4_* NIST / HEP / Space pre-defined materials
    ReactorMaterials/    ← OpenMC-only: TMZ, U_Cr, LBE, Tungsten_Carbide …
```

User-defined materials sit directly inside `Materials/` (not in a sub-group).

---

## Materials Architecture — Critical Rules

**Geant4 GDML export (`exportGDML.py`)**

1. `createIsotopes()`, `createElements()`, `createMaterials()` each **skip** any child whose label is `"ReactorMaterials"`.
2. `createMaterials()` also skips `"Geant4"` — Geant4 resolves `G4_*` materials internally; no explicit definitions are needed in the GDML file.
3. `getMaterial(obj)` classifies each solid's material:
   - `G4_*` prefix → adds to `usedGeant4Materials`
   - label `"ReactorMaterials"` (the container, not a material) → substitutes default with a warning
   - found inside `Materials/ReactorMaterials` → adds to `usedReactorMaterials`
4. `postCreateGeantMaterials()` emits `<material name="G4_…">` tags (no element/isotope decomposition — Geant4 NIST manager handles that internally).
5. `postCreateReactorMaterials()` runs only when `usedReactorMaterials` is non-empty — exports reactor material definitions on demand.
6. `_fixMissingIsotopes()` post-pass fills any isotope gaps from `NIST_Isotopes.xml`.

**OpenMC export (`exportOpenMC.py`)**

- `elementGroup()`, `materialGroup()`, and `createElement()` all **recurse into sub-groups**, so they find reactor elements/materials inside their `ReactorMaterials` sub-groups transparently.
- `FreeCAD.ActiveDocument.getObject(name)` is sub-group-transparent (FreeCAD stores all objects in a flat internal namespace even when grouped in the UI).

**UI material selectors**

- `addMaterialsFromGroup()` (`GDMLObjects.py`) — skips `"Geant4"` and `"ReactorMaterials"` containers. This populates the `material` `App::PropertyEnumeration` on GDMLObjects (the Properties panel dropdown).
- `getMaterialsList()` (`GDMLMaterials.py`) — skips `"Geant4"` and `"ReactorMaterials"`. Used by `exportOpenMC.getMaterial()`.
- `newGetGroupedMaterials()` (`GDMLMaterials.py`) — includes reactor materials as a separate group (`GroupedMaterials["ReactorMaterials"]`). Used by the **Set Material** command dialog. Normal user-defined materials appear under `"Normal"` — the `"ReactorMaterials"` container label is excluded from `"Normal"` via `_NORMAL_SKIP`.

**The result:** Reactor materials can never accidentally become the default material for a new GDML object. They remain accessible for deliberate assignment via the Set Material dialog (for OpenMC workflows).

---

## Reactor Sub-Group Migration

Documents saved before May 2026 may have reactor isotopes/elements directly in the top-level `Isotopes` and `Elements` groups rather than in the `ReactorMaterials` sub-groups. Detection and repair:

- `MyObserver._checkReactorMigration(doc)` in `init_gui.py` — fires on `Activated`, `slotOpenDocument`, `slotActivateDocument`, and `slotFinishRestoreDocument`. Detects `enriched_U1` directly in `Elements`. Shows a warning dialog at most once per doc per session.
- **GDML → Migrate Reactor Sub-Groups** (`MigrateReactorSubGroupsCommand`) — calls `importGDML.migrateReactorSubGroups()` to move objects into sub-groups. Safe to re-run on already-correct documents.

---

## Gmsh Tessellation

Two Gmsh-based commands:

- **Gmsh Tessellate** — full Gmsh panel; user controls mesh type and characteristic lengths, iterative re-meshing before commit.
- **Gmsh Min Tessellate** — STL-based recombination; produces minimal quad-dominant mesh (e.g. 6 quads for a cube vs 12 triangles).

Both commands:
1. Create a `GmshTessellated` sibling object in the document tree.
2. Set `exportFlag = False` on the original source object so it is suppressed from GDML export.
3. Re-running on the same source object updates the existing tessellation in place.

`GmshUtils.py` contains the shared helpers. Gmsh must be installed for the **same Python interpreter that FreeCAD uses** — a version mismatch will produce a clear error message with the correct install command.

---

## Python Version Constraint

The project instructions require that Gmsh be installed for the same Python version that FreeCAD uses. When adding Gmsh-related code, check that the Python version used by both matches. The workbench enforces this at runtime and shows the correct `pip install` command if a mismatch is detected.

---

## Export Flag

Every GDMLObject has an `exportFlag` boolean property. When `False` the object (and its sub-tree) is skipped during GDML export. Gmsh tessellation sets this on the source object automatically. Users can also set it manually to exclude objects from export without deleting them.

---

## Coding Style Observed in This Project

- Short, focused functions; logic shared via module-level helpers.
- Skip-list pattern: `_SKIP_LABELS = {"Geant4", "ReactorMaterials"}` before loops.
- Recursive inner functions (`_search`, `_findElement`) for sub-group traversal.
- `global` declarations at the top of functions that modify module-level state.
- FreeCAD `App::PropertyEnumeration` for material dropdowns; set allowed values by assigning a list, then set current value by assigning the string.
- Avoid diagnostic `print` calls in shipped code unless they serve as meaningful progress indicators.
