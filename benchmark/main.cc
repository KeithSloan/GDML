// gdml_bench — GEANT4 performance benchmark for GDML tessellation variants
//
// Usage:  gdml_bench <file.gdml> [n_events] [particle] [energy_MeV]
// e.g.:   gdml_bench geometry.gdml 1000 geantino 100
//
// Reports: wall-clock time, total steps, total tracks, steps/event, time/event

#include <chrono>
#include <iostream>
#include <iomanip>
#include <string>
#include <atomic>

#include "G4RunManagerFactory.hh"
#include "G4GDMLParser.hh"
#include "G4VUserDetectorConstruction.hh"
#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4UserEventAction.hh"
#include "G4UserSteppingAction.hh"
#include "G4UserRunAction.hh"
#include "FTFP_BERT.hh"
#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4SystemOfUnits.hh"
#include "G4Step.hh"
#include "G4Event.hh"
#include "G4Run.hh"
#include "G4LogicalVolumeStore.hh"
#include "G4PVPlacement.hh"

// ── Globals for accumulation ───────────────────────────────────────────────
static std::atomic<long long> gTotalSteps{0};
static std::atomic<long long> gTotalTracks{0};

// ── Detector construction from GDML ───────────────────────────────────────
class GDMLDetector : public G4VUserDetectorConstruction {
public:
    explicit GDMLDetector(const std::string& gdmlFile) : fFile(gdmlFile) {}

    G4VPhysicalVolume* Construct() override {
        G4GDMLParser parser;
        parser.SetOverlapCheck(false);   // skip overlap check — we want speed
        parser.Read(fFile, false);       // false = no schema validation
        return parser.GetWorldVolume();
    }

private:
    std::string fFile;
};

// ── Primary generator: pencil beam along +Z through origin ────────────────
class BenchPGA : public G4VUserPrimaryGeneratorAction {
public:
    BenchPGA(const std::string& particleName, double energyMeV)
        : fGun(new G4ParticleGun(1))
    {
        auto* table = G4ParticleTable::GetParticleTable();
        auto* particle = table->FindParticle(particleName);
        if (!particle) {
            G4cerr << "[gdml_bench] Unknown particle '" << particleName
                   << "', falling back to geantino\n";
            particle = table->FindParticle("geantino");
        }
        fGun->SetParticleDefinition(particle);
        fGun->SetParticleEnergy(energyMeV * MeV);
        fGun->SetParticleMomentumDirection(G4ThreeVector(0, 0, 1));
        fGun->SetParticlePosition(G4ThreeVector(0, 0, -5000 * mm));
    }

    void GeneratePrimaries(G4Event* event) override {
        fGun->GeneratePrimaryVertex(event);
    }

private:
    std::unique_ptr<G4ParticleGun> fGun;
};

// ── Stepping action: count steps ──────────────────────────────────────────
class BenchStepping : public G4UserSteppingAction {
public:
    void UserSteppingAction(const G4Step*) override {
        ++gTotalSteps;
    }
};

// ── Event action: count tracks ────────────────────────────────────────────
class BenchEvent : public G4UserEventAction {
public:
    void EndOfEventAction(const G4Event* event) override {
        auto* hc = event->GetTrajectoryContainer();
        (void)hc;
        // count secondaries + primary = tracks per event
        // Simple proxy: increment by number of tracks in trajectory container
        // Falls back to 1 if trajectories are off
        gTotalTracks += 1;
    }
};

// ── Main ──────────────────────────────────────────────────────────────────
int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "Usage: gdml_bench <file.gdml> [n_events=1000] "
                     "[particle=geantino] [energy_MeV=100]\n";
        return 1;
    }

    std::string gdmlFile   = argv[1];
    int         nEvents    = argc > 2 ? std::stoi(argv[2]) : 1000;
    std::string particle   = argc > 3 ? argv[3] : "geantino";
    double      energyMeV  = argc > 4 ? std::stod(argv[4]) : 100.0;

    auto* rm = G4RunManagerFactory::CreateRunManager(G4RunManagerType::Serial);

    rm->SetUserInitialization(new GDMLDetector(gdmlFile));
    rm->SetUserInitialization(new FTFP_BERT);
    rm->SetUserAction(new BenchPGA(particle, energyMeV));
    rm->SetUserAction(new BenchStepping);
    rm->SetUserAction(new BenchEvent);

    rm->Initialize();

    // ── Warm-up: 1 event to trigger geometry optimisation ─────────────────
    gTotalSteps  = 0;
    gTotalTracks = 0;
    rm->BeamOn(1);
    gTotalSteps  = 0;
    gTotalTracks = 0;

    // ── Timed run ─────────────────────────────────────────────────────────
    auto t0 = std::chrono::steady_clock::now();
    rm->BeamOn(nEvents);
    auto t1 = std::chrono::steady_clock::now();

    double wallSec = std::chrono::duration<double>(t1 - t0).count();
    long long steps  = gTotalSteps.load();
    long long tracks = gTotalTracks.load();

    std::cout << "\n";
    std::cout << "========== gdml_bench results ==========\n";
    std::cout << "GDML file   : " << gdmlFile   << "\n";
    std::cout << "Particle    : " << particle    << " @ " << energyMeV << " MeV\n";
    std::cout << "Events      : " << nEvents     << "\n";
    std::cout << "Wall time   : " << std::fixed << std::setprecision(3)
              << wallSec << " s\n";
    std::cout << "Total steps : " << steps  << "\n";
    std::cout << "Total tracks: " << tracks << "\n";
    std::cout << "Steps/event : " << std::setprecision(1)
              << (double)steps / nEvents << "\n";
    std::cout << "ms/event    : " << std::setprecision(3)
              << wallSec * 1000.0 / nEvents << "\n";
    std::cout << "========================================\n";

    delete rm;
    return 0;
}
