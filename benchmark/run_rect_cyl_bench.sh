#!/bin/bash
# Benchmark the rect/cyl test geometry against all 4 GDML tessellation variants.
# Run gen_rect_cyl_gdml.py first to produce the GDML files and rc_mesh_stats.json.
#
# Usage (from benchmark directory):
#   python3 gen_rect_cyl_gdml.py
#   ./run_rect_cyl_bench.sh

set -e   # exit on build failures; bench errors are caught by || true below

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GEANT4_INSTALL="/Users/ksloan/geant4-v11.3.2-install"
GDML_DIR="/Users/ksloan/github/CAD_Files_Git/GDML/rect_cyl"
BUILD_DIR="$SCRIPT_DIR/build"
BENCH="$BUILD_DIR/gdml_bench"
STATS_FILE="$SCRIPT_DIR/rc_mesh_stats.json"
RESULTS_FILE="$SCRIPT_DIR/rc_results.txt"

N_EVENTS=1000
PARTICLE="gamma"
ENERGY_MEV=1

# ── Sanity checks ─────────────────────────────────────────────────────────────
if [ ! -f "$BENCH" ]; then
    echo "ERROR: $BENCH not found — run build_and_run.sh first to build gdml_bench"
    exit 1
fi
if [ ! -f "$STATS_FILE" ]; then
    echo "ERROR: $STATS_FILE not found — run gen_rect_cyl_gdml.py first"
    exit 1
fi

# ── Source GEANT4 environment and symlinks ─────────────────────────────────────
source "$GEANT4_INSTALL/bin/geant4.sh"
G4LIB="$GEANT4_INSTALL/lib"
ln -sf /opt/homebrew/lib/libxerces-c-3.3.dylib "$G4LIB/libxerces-c-3.3.dylib" 2>/dev/null || true
for fw in /opt/homebrew/opt/qt@5/lib/Qt*.framework; do
    name=$(basename "$fw" .framework)
    src="$fw/Versions/5/$name"
    if [ -f "$src" ]; then
        ln -sf "$src" "$G4LIB/lib${name}.5.dylib"       2>/dev/null || true
        ln -sf "$src" "$G4LIB/libQt5${name#Qt}.5.dylib" 2>/dev/null || true
    fi
done

# ── Stats helper ──────────────────────────────────────────────────────────────
get_stat() {
    python3 -c "import json,sys; d=json.load(open('$STATS_FILE')); print(d.get('$1',{}).get('$2','-'))" 2>/dev/null || echo "-"
}

# ── Run ───────────────────────────────────────────────────────────────────────
echo "" > "$RESULTS_FILE"

printf "\n%s\n" "====== Rect/Cyl Geometry — GDML Tessellation Benchmark ======" | tee -a "$RESULTS_FILE"
printf "Geometry: plate + 4 full cylinders + 2 half cylinders + 2 quarter cylinders\n" | tee -a "$RESULTS_FILE"
printf "Particle: %s @ %s MeV   Events: %d\n\n" "$PARTICLE" "$ENERGY_MEV" "$N_EVENTS" | tee -a "$RESULTS_FILE"

printf "%-32s %8s %8s %8s %7s %10s %10s %10s\n" \
    "Variant" "Tri" "Quad" "Total" "MB" "Wall(s)" "Steps/evt" "ms/evt" | tee -a "$RESULTS_FILE"
printf "%-32s %8s %8s %8s %7s %10s %10s %10s\n" \
    "--------------------------------" "--------" "--------" "--------" "-------" "----------" "----------" "----------" | tee -a "$RESULTS_FILE"

run_variant() {
    local variant="$1"    # key in rc_mesh_stats.json and GDML file stem
    local label="$2"

    local TRI QUAD TOTAL MB
    TRI=$(get_stat   "$variant" tri)
    QUAD=$(get_stat  "$variant" quad)
    TOTAL=$(get_stat "$variant" total)
    MB=$(get_stat    "$variant" size_mb)

    local FILE="$GDML_DIR/${variant}-worldVOL.gdml"
    if [ ! -f "$FILE" ]; then
        printf "%-32s %8s %8s %8s %7s %10s %10s %10s\n" \
            "$label" "$TRI" "$QUAD" "$TOTAL" "$MB" "MISSING" "-" "-" | tee -a "$RESULTS_FILE"
        return
    fi

    local LOGFILE="/tmp/rc_bench_${variant}.txt"
    echo ""
    echo "--- Running: $label ---"
    "$BENCH" "$FILE" "$N_EVENTS" "$PARTICLE" "$ENERGY_MEV" > "$LOGFILE" 2>&1 || true
    RC=$?
    if [ $RC -ne 0 ]; then
        echo "  ERROR (exit $RC) — last lines:"
        tail -20 "$LOGFILE"
        printf "%-32s %8s %8s %8s %7s %10s %10s %10s\n" \
            "$label" "$TRI" "$QUAD" "$TOTAL" "$MB" "ERROR" "-" "-" | tee -a "$RESULTS_FILE"
        return
    fi

    WALL=$(grep  "Wall time"   "$LOGFILE" | awk '{print $4}')
    STEPS=$(grep "Steps/event" "$LOGFILE" | awk '{print $3}')
    MS=$(grep    "ms/event"    "$LOGFILE" | awk '{print $3}')
    printf "%-32s %8s %8s %8s %7s %10s %10s %10s\n" \
        "$label" "$TRI" "$QUAD" "$TOTAL" "$MB" "$WALL" "$STEPS" "$MS" | tee -a "$RESULTS_FILE"
}

run_variant "rc_fc_default"     "FreeCAD default (tri)"
run_variant "rc_gmsh"           "Gmsh full (tri)"
run_variant "rc_gmsh_min"       "Gmsh Min (quads->tri)"
run_variant "rc_gmsh_min_quads" "Gmsh Min Keep Quads"

printf "\n%s\n" "==============================================================" | tee -a "$RESULTS_FILE"
echo ""
echo "Full results saved to: $RESULTS_FILE"
