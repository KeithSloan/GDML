# Documentation: B-rep CAD Deconstruction to GDML Solids & Tessellation Fallbacks

This document outlines the technical discussion and architectural blueprints for deconstructing exact Boundary Representation (B-rep) data structures—originating from STEP or `.brep` files—into schema-compliant Geometry Description Markup Language (GDML) datasets for particle physics frameworks like Geant4.

---

## 1. Core Background: Analysis Situs & B-rep Debugging
Analysis Situs serves as a foundational reference point for visualising and debugging low-level B-rep data structures. Built on the **Open CASCADE Technology (OCCT)** geometry kernel, its architecture highlights key strategies for parsing raw topology:

*   **Attributed Adjacency Graphs (AAG):** Translates CAD topology into a mathematical network where **Nodes** represent individual faces, **Arcs** represent shared boundary edges, and **Attributes** define geometric traits (e.g., *convex*, *concave*, *smooth*).
*   **Feature Isolation:** By querying subgraphs within the AAG via the modern C++ SDK (`asiAlgo_AAG`), developers can programmatically isolate distinct topological features like blend fillets, pockets, or drilled hole networks.

---

## 2. The B-rep to GDML Conversion Pipeline
Converting exact analytical CAD geometry to standard constructive solid geometry (CSG) primitives (`<box>`, `<tube>`, `<sphere>`) requires a strict processing loop paired with a guaranteed mesh fallback algorithm.

<img width="1342" height="854" alt="Image 31-07-2026 at 22 10" src="https://github.com/user-attachments/assets/1d5e2534-5439-406b-bb69-516a095de7b5" />

### Pipeline Execution Framework
1.  **Traverse Solids:** Loop through the imported assembly using tools like `TopExp_Explorer` to isolate closed, independent volumes (`TopoDS_Solid`).
2.  **Evaluate Surfaces:** Check individual surface types using `GeomAdaptor_Surface` or `BRepAdaptor_Surface`. If all surfaces match strict primitive configurations, extract bounding dimensions (lengths, radii, heights) and output native GDML nodes.
3.  **Tessellation Fallback (`tse`):** When encountering freeform surfaces (NURBS, BSplines) or unresolvable intersections, the shape must *fall through* to a mesh. Discretise the geometry using `BRepMesh_IncrementalMesh` based on explicit linear and angular chord deflection tolerances.
4.  **Export Structural Facets:** Map the resulting unique spatial vertices to `<position>` tags and map index triangles to `<triangular>` elements nested inside a closed `<tessellated>` solid block.

---

## 3. Resolving Composite Solids and Featureless Formats
A common challenge arises with complex composite bodies (e.g., a rectangular block punctured by multiple cylindrical holes). 

### The Flat Data Problem
Standard CAD exchange protocols (like STEP AP203/214) destroy the design history tree. The file retains no native memory of a "subtraction" operation—it only contains a collection of unclassified, frozen faces stitched together at the boundaries.

### Resolution Methods
*   **CSG Tree Recovery:** Algorithms can compute the Oriented Bounding Box (OBB) of the solid to establish the main body primitive, scan for internal cylindrical surfaces where the normal vectors point inward (`TopAbs_REVERSED`), calculate their axes, and reconstruct a sequential GDML `<subtraction>` tree.
*   **The Guardrail Rule:** If the geometric boundaries cross at irregular angles or exceed the limits of your feature recognition script, the solid bypasses analytical recovery and generates a single `<tessellated>` volume. Planar regions receive large, highly optimized triangles, while curved regions receive fine triangle strips dictated by the mesh deflection tolerance.

---

## 4. CAD Ecosystem & STEP AP242 Compatibility
The **STEP AP242** (Managed Model Based 3D Engineering) standard offers a pathway to preserve rich geometric semantic information, Product Manufacturing Information (PMI), and 3D annotations directly within the file syntax.

### System Support Matrix
*   **Enterprise Tier (Full Support):** Siemens NX, Dassault Systèmes CATIA, and PTC Creo fully support AP242. They map live dimensions to semantic PMI, though enterprise packages may require dedicated MBD or validation licensing modules.
*   **Mainstream Tier:** Autodesk Inventor and SOLIDWORKS offer native translation paths, but users must explicitly enable "Export 3D Annotations/PMI" options in their export profile maps to avoid stripping metadata.
*   **Cloud Tier:** Autodesk Fusion 360 uses AP242 as its baseline default file wrapper, and Onshape fully parses AP242 layers.

### FreeCAD Integration Context
FreeCAD natively reads and writes the geometric layers of AP242 via its underlying OCCT framework. However, because FreeCAD lacks an internal data model structure for 3D PMI, tolerances, or kinematic constraints, it treats AP242 similarly to a standard AP214 file. Advanced metadata layers are skipped on import and omitted on export.

---

## 5. Blueprint: Implementing a Custom AP242 Importer in FreeCAD
To build an open-source automation workflow, you can develop a custom STEP AP242 importer macro or plugin that instantiates native Python feature objects from **Keith Sloan's GDML Workbench**.

By bypassing FreeCAD's desktop GUI layout, a Python script can invoke Open CASCADE's `STEPCAFControl_Reader` directly to evaluate shapes, look up embedded material naming strings, and map them to targeted workbench objects.

### Conceptual Implementation Structure

```python
import FreeCAD as App
from STEPCAFControl import STEPCAFControl_Reader
import GDMLObjects
import MeshPart

def custom_ap242_to_gdml_importer(file_path):
    # 1. Initialize the OCCT assembly data exchange reader with GDT activated
    reader = STEPCAFControl_Reader()
    reader.SetGDTMode(True)
    
    if reader.ReadFile(file_path) != 1:
        raise IOError("Failed to parse STEP file geometry.")
        
    reader.Transfer(App.ActiveDocument)
    
    # 2. Iterate through shapes and sort analytical vs complex bodies
    # [Placeholder for geometric classification loop]
    
    # Example Path A: Shape matches primitive parameters
    new_primitive = GDMLObjects.makeTube()
    new_primitive.Label = "Extracted_Beam_Pipe"
    new_primitive.rmax = 50.0
    new_primitive.rmin = 45.0
    new_primitive.z = 500.0
    new_primitive.Material = "G4_Al" # Map from internal STEP attribute strings
    
    # Example Path B: Complex shape fallback to tessellation
    # mesh_part = MeshPart.meshFromShape(Shape=complex_shape, LinearDeflection=0.1)
    new_tessellated = GDMLObjects.makeTessellated()
    new_tessellated.Label = "Complex_Flange_Tessellated"
    
    App.ActiveDocument.recompute()
```


