#!/usr/bin/env bash
# Stage 8 β coupling-strength sensitivity sweep for the halong catchment.
#
# The β-independent base (coupled storms + flood timeseries + gaugehc) must
# already be generated. This script re-runs ONLY the β-dependent legs per β:
# typhoon genesis (--coupling-beta) then the property hazard curves + spread
# decomposition, snapshotting propertyhc.json + the typhoon ensemble into a
# per-β study directory.
#
# Usage: scripts/beta_sweep_halong.sh            (defaults: 0.3 0.5 0.7)
#        scripts/beta_sweep_halong.sh 0.3 0.5 0.7
set -euo pipefail

export MKM_CATCHMENT=halong
: "${MKM_PORT_ADMIN_PASSWORD:?Set MKM_PORT_ADMIN_PASSWORD before running}"

BETAS=("$@")
[ ${#BETAS[@]} -eq 0 ] && BETAS=(0.3 0.5 0.7)

DATA=data/input/halong
STUDY="$DATA/.beta_study"
mkdir -p "$STUDY"

for B in "${BETAS[@]}"; do
    echo "=================================================================="
    echo " β = $B  —  typhoon genesis + property hazard curves"
    echo "=================================================================="
    python phys.py port --halong --typhoon --coupling-beta "$B"
    python phys.py port --halong --propertyhc --propertyshd --propertyshe --propertybri

    DEST="$STUDY/beta_${B}"
    mkdir -p "$DEST"
    cp "$DATA/propertyhc.json"          "$DEST/propertyhc.json"
    cp "$DATA/typhoon/ensemble.json"    "$DEST/ensemble.json"
    # Per-event summaries (q / Vmax / scenario) drive the upper-tail analysis.
    rm -rf "$DEST/events" && mkdir -p "$DEST/events"
    cp "$DATA"/typhoon/events/*.json    "$DEST/events/" 2>/dev/null || true
    echo "  snapshot -> $DEST"
done

echo "Sweep complete. Snapshots under $STUDY/"
