// loadGDML.cc — minimal GEANT4 validator for the VELO-subset test files.
//
// Reads a GDML file with G4GDMLParser and runs CheckOverlaps() on every
// physical volume in the store. No run manager / physics list required.
//
// Usage:   ./loadGDML velo_replica.gdml
// Build:   see CMakeLists.txt in this folder.
//
// Exit code 0 = file parsed and no overlaps reported.

#include "G4GDMLParser.hh"
#include "G4PhysicalVolumeStore.hh"
#include "G4VPhysicalVolume.hh"
#include <iostream>
#include <string>

int main(int argc, char** argv)
{
    if (argc < 2) {
        std::cerr << "usage: " << argv[0] << " <file.gdml>\n";
        return 2;
    }
    const std::string gdmlFile = argv[1];

    G4GDMLParser parser;
    parser.SetOverlapCheck(true);          // check overlaps as volumes are read
    parser.Read(gdmlFile, /*validate=*/false);

    G4VPhysicalVolume* world = parser.GetWorldVolume();
    if (!world) {
        std::cerr << "ERROR: no world volume in " << gdmlFile << "\n";
        return 1;
    }
    std::cout << "Parsed OK. World = " << world->GetName() << "\n";

    // Explicit second pass: 10000 points, 0 mm tolerance, verbose.
    int nBad = 0;
    auto* store = G4PhysicalVolumeStore::GetInstance();
    std::cout << "Physical volumes: " << store->size() << "\n";
    for (auto* pv : *store) {
        // G4PVReplica copies are non-overlapping by construction; skip the
        // (unsupported) explicit check on them, GEANT4 validates the division.
        if (pv->IsReplicated()) continue;
        if (pv->CheckOverlaps(10000, 0.0, /*verbose=*/true)) ++nBad;
    }

    if (nBad == 0) std::cout << "RESULT: PASS (no overlaps)\n";
    else           std::cout << "RESULT: FAIL (" << nBad << " volume(s) with overlaps)\n";
    return nBad == 0 ? 0 : 1;
}
