#!/usr/bin/env bash
# Manage the native (non-Docker) PostgreSQL 16 dev server whose data directory
# lives on the external SSD. Native pg avoids Docker's VM-disk layer, which was
# unstable when the SSD briefly disconnected.
#
# Usage: scripts/pg-native.sh {start|stop|status|psql|log}
#
# The data dir is read from docker/.env (MKM_PG_DATA_DIR) so it stays in one place;
# falls back to the SSD default. The app/tests need no config change — native pg
# listens on 127.0.0.1:5432, exactly what config/database.py defaults to.
set -euo pipefail

BIN="${PG_BIN:-/opt/homebrew/opt/postgresql@16/bin}"
HERE="$(cd "$(dirname "$0")" && pwd)"

# Resolve the data dir: env override > docker/.env > SSD default.
PGDATA="${MKM_PG_DATA_DIR:-}"
if [ -z "$PGDATA" ] && [ -f "$HERE/../docker/.env" ]; then
  PGDATA="$(grep -E '^MKM_PG_DATA_DIR=' "$HERE/../docker/.env" | head -1 | cut -d= -f2-)"
fi
PGDATA="${PGDATA:-/Volumes/David SSD/Docs/PhysicalRisk/physicalrisk/pgdata}"
LOG="$(dirname "$PGDATA")/pg-native.log"

# macOS: without a valid LC_ALL the postmaster "becomes multithreaded during
# startup" and refuses to boot. The cluster was initdb'd with --locale=C.
export LC_ALL=C

case "${1:-status}" in
  start)  "$BIN/pg_ctl" -D "$PGDATA" -l "$LOG" -w -t 30 start ;;
  stop)   "$BIN/pg_ctl" -D "$PGDATA" -m fast stop ;;
  status) "$BIN/pg_ctl" -D "$PGDATA" status ;;
  psql)   shift; "$BIN/psql" -h 127.0.0.1 -p 5432 -U mkm -d physicalrisk "$@" ;;
  log)    tail -n "${2:-30}" "$LOG" ;;
  *) echo "usage: $0 {start|stop|status|psql|log}"; exit 1 ;;
esac
