#!/usr/bin/env bash
# Manage the native (non-Docker) MinIO dev object store. Data dir lives on the
# external SSD, same path the Docker MinIO used. Serves the pg backend's blob tier
# (classifier .joblib etc.). App/tests need no config change — it listens on
# 127.0.0.1:9000 with minioadmin/minioadmin, exactly config/database.py defaults.
#
# Usage: scripts/minio-native.sh {start|stop|status|log}
set -euo pipefail

BIN="${MINIO_BIN:-/opt/homebrew/bin/minio}"
HERE="$(cd "$(dirname "$0")" && pwd)"

# Data dir: env override > docker/.env (MKM_MINIO_DATA_DIR) > SSD default.
MINIODATA="${MKM_MINIO_DATA_DIR:-}"
if [ -z "$MINIODATA" ] && [ -f "$HERE/../docker/.env" ]; then
  MINIODATA="$(grep -E '^MKM_MINIO_DATA_DIR=' "$HERE/../docker/.env" | head -1 | cut -d= -f2-)"
fi
MINIODATA="${MINIODATA:-/Volumes/David SSD/Docs/PhysicalRisk/physicalrisk/miniodata}"
LOG="$(dirname "$MINIODATA")/minio-native.log"
PIDFILE="$(dirname "$MINIODATA")/minio-native.pid"

export MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin

case "${1:-status}" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "already running (pid $(cat "$PIDFILE"))"; exit 0; fi
    nohup "$BIN" server "$MINIODATA" \
      --address 127.0.0.1:9000 --console-address 127.0.0.1:9001 > "$LOG" 2>&1 &
    echo $! > "$PIDFILE"; sleep 2
    echo "started (pid $(cat "$PIDFILE")) — api :9000, console :9001" ;;
  stop)
    if [ -f "$PIDFILE" ] && kill "$(cat "$PIDFILE")" 2>/dev/null; then
      rm -f "$PIDFILE"; echo stopped; else echo "not running"; rm -f "$PIDFILE"; fi ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "running (pid $(cat "$PIDFILE"))"; else echo "not running"; fi ;;
  log) tail -n "${2:-30}" "$LOG" ;;
  *) echo "usage: $0 {start|stop|status|log}"; exit 1 ;;
esac
