cmake_minimum_required(VERSION 3.16)
project(loadGDML)

# Requires a GEANT4 install built with -DGEANT4_USE_GDML=ON (needs Xerces-C).
find_package(Geant4 REQUIRED gdml)
include(${Geant4_USE_FILE})

add_executable(loadGDML loadGDML.cc)
target_link_libraries(loadGDML ${Geant4_LIBRARIES})

# Build:
#   cd validate_geant4 && mkdir build && cd build
#   cmake .. && make -j
# Run (from the TestReplica folder):
#   validate_geant4/build/loadGDML velo_flat.gdml
#   validate_geant4/build/loadGDML velo_replica.gdml
#   validate_geant4/build/loadGDML velo_paramvol.gdml
