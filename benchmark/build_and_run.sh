#!/bin/bash
# Build gdml_bench against your local GEANT4 install, then benchmark all 4 GDML variants.
#
# Run from anywhere:
#   chmod +x build_and_run.sh
#   ./build_and_run.sh

set -e          # exits on build failures (cmake/make)
# Note: do NOT use set -o pipefail here — it causes silent exit when bench crashes

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GEANT4_INSTALL="/Users/ksloan/geant4-v11.3.2-install"
GDML_DIR="/Users/ksloan/github/CAD_Files_Git/GDML/1485_step"
BUILD_DIR="$SCRIPT_DIR/build"
N_EVENTS=1000
PARTICLE="gamma"
ENERGY_MEV=1

# ── 1. Build ───────────────────────────────────────────────────────────────
echo "=== Building gdml_bench ==="

# Locate Qt5 — try Homebrew, then FreeCAD bundle, then Qt.io install
QT5_PREFIX=""
for candidate in \
    /opt/homebrew/opt/qt@5 \
    /usr/local/opt/qt@5 \
    /opt/homebrew/opt/qt5 \
    /usr/local/opt/qt5 \
    "/Applications/FreeCAD.app/Contents/Resources" \
    "$HOME/Qt/5.*/clang_64" ; do
    # expand globs
    for d in $candidate; do
        if [ -f "$d/lib/cmake/Qt5Core/Qt5CoreConfig.cmake" ] || \
           [ -f "$d/lib/cmake/Qt5/Qt5Config.cmake" ]; then
            QT5_PREFIX="$d"
            break 2
        fi
    done
done

if [ -z "$QT5_PREFIX" ]; then
    echo "ERROR: Qt5 not found. Install with:  brew install qt@5"
    exit 1
fi
echo "Qt5 found at: $QT5_PREFIX"

mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"
cmake "$SCRIPT_DIR" \
    -DGeant4_DIR="$GEANT4_INSTALL/lib/cmake/Geant4" \
    -DCMAKE_PREFIX_PATH="$QT5_PREFIX" \
    -DCMAKE_BUILD_TYPE=Release \
    -Wno-dev -Wno-deprecated \
    > cmake_out.txt 2>&1 || { echo "cmake failed — see $BUILD_DIR/cmake_out.txt"; exit 1; }
make -j$(sysctl -n hw.logicalcpu) > make_out.txt 2>&1 || { echo "make failed — see $BUILD_DIR/make_out.txt"; exit 1; }
echo "Build OK: $BUILD_DIR/gdml_bench"

# ── Source GEANT4 environment ──────────────────────────────────────────────
source "$GEANT4_INSTALL/bin/geant4.sh"

# Symlink missing libs into the GEANT4 install lib dir (where G4 dylibs already look)
G4LIB="$GEANT4_INSTALL/lib"

# xerces
ln -sf /opt/homebrew/lib/libxerces-c-3.3.dylib "$G4LIB/libxerces-c-3.3.dylib" 2>/dev/null || true

# Qt5 frameworks → versioned dylib names GEANT4 expects
for fw in /opt/homebrew/opt/qt@5/lib/Qt*.framework; do
    name=$(basename "$fw" .framework)
    src="$fw/Versions/5/$name"
    if [ -f "$src" ]; then
        ln -sf "$src" "$G4LIB/lib${name}.5.dylib"         2>/dev/null || true
        ln -sf "$src" "$G4LIB/libQt5${name#Qt}.5.dylib"   2>/dev/null || true
    fi
done
echo "Runtime symlinks created in $G4LIB"

BENCH="$BUILD_DIR/gdml_bench"
RESULTS_FILE="$SCRIPT_DIR/results.txt"
echo "" > "$RESULTS_FILE"

# ── 2. Read mesh stats from gen_all_gdml.py output ────────────────────────
STATS_FILE="$SCRIPT_DIR/mesh_stats.json"
get_stat() {
    # get_stat <variant_key> <field>  e.g. get_stat fc_default tri
    python3 -c "import json,sys; d=json.load(open('$STATS_FILE')); print(d.get('$1',{}).get('$2','-'))" 2>/dev/null || echo "-"
}

# ── 3. Run each variant ────────────────────────────────────────────────────
printf "\n%s\n" "========== GDML Tessellation Benchmark ==========" | tee -a "$RESULTS_FILE"
printf "%-30s %8s %8s %8s %8s %7s %10s %10s %10s\n" \
    "Variant" "Tri" "Quad" "Total" "MB" "Events" "Wall(s)" "Steps/evt" "ms/evt" | tee -a "$RESULTS_FILE"
printf "%-30s %8s %8s %8s %8s %7s %10s %10s %10s\n" \
    "------------------------------" "--------" "--------" "--------" "--------" "-------" "----------" "----------" "----------" | tee -a "$RESULTS_FILE"

run_variant() {
    local variant="$1"     # key in mesh_stats.json  e.g. fc_default
    local file_key="$2"    # GDML filename suffix    e.g. fc_default_both
    local label="$3"
    local FILE="$GDML_DIR/1485_${file_key}-worldVOL.gdml"

    local TRI  QUAD TOTAL MB
    TRI=$(get_stat  "$variant" tri)
    QUAD=$(get_stat "$variant" quad)
    TOTAL=$(get_stat "$variant" total)
    MB=$(get_stat   "$variant" size_mb)

    if [ ! -f "$FILE" ]; then
        printf "%-30s %8s %8s %8s %8s %7s %10s %10s %10s\n" \
            "$label" "$TRI" "$QUAD" "$TOTAL" "$MB" "-" "MISSING" "-" "-" | tee -a "$RESULTS_FILE"
        return
    fi
    local LOGFILE="/tmp/gdml_bench_${file_key}.txt"
    echo ""
    echo "--- Running: $label ---"
    "$BENCH" "$FILE" "$N_EVENTS" "$PARTICLE" "$ENERGY_MEV" > "$LOGFILE" 2>&1 || true
    RC=$?
    if [ $RC -ne 0 ]; then
        echo "  ERROR (exit $RC) — last lines of output:"
        tail -20 "$LOGFILE"
        printf "%-30s %8s %8s %8s %8s %7d %10s %10s %10s\n" \
            "$label" "$TRI" "$QUAD" "$TOTAL" "$MB" "$N_EVENTS" "ERROR" "-" "-" | tee -a "$RESULTS_FILE"
        return
    fi
    WALL=$(grep  "Wall time"   "$LOGFILE" | awk '{print $4}')
    STEPS=$(grep "Steps/event" "$LOGFILE" | awk '{print $3}')
    MS=$(grep    "ms/event"    "$LOGFILE" | awk '{print $3}')
    printf "%-30s %8s %8s %8s %8s %7d %10s %10s %10s\n" \
        "$label" "$TRI" "$QUAD" "$TOTAL" "$MB" "$N_EVENTS" "$WALL" "$STEPS" "$MS" | tee -a "$RESULTS_FILE"
}

run_variant "fc_default"     "fc_default_both"     "FreeCAD default (tri)"
run_variant "gmsh"           "gmsh_both"           "Gmsh full"
run_variant "gmsh_min"       "gmsh_min_both"       "Gmsh Min (quads->tri)"
run_variant "gmsh_min_quads" "gmsh_min_quads_both" "Gmsh Min Keep Quads"

printf "\n%s\n" "==================================================" | tee -a "$RESULTS_FILE"
echo ""
echo "Full results also saved to: $RESULTS_FILE"
