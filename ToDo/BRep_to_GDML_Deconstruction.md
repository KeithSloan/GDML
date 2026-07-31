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


