cmake_minimum_required(VERSION 3.16)
project(gdml_bench)

find_package(Geant4 REQUIRED gdml)
include(${Geant4_USE_FILE})

# Strip Qt/OpenGL/vis UI libraries — benchmark needs no display
set(BENCH_LIBS)
foreach(lib ${Geant4_LIBRARIES})
    if(NOT lib MATCHES "G4interfaces|G4OpenGL|G4RayTracer|G4vis|G4gl2ps|G4GMocren|G4VRML|G4HepRep")
        list(APPEND BENCH_LIBS ${lib})
    endif()
endforeach()

add_executable(gdml_bench main.cc)
target_link_libraries(gdml_bench ${BENCH_LIBS})
