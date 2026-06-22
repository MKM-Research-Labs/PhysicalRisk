# Running on PostgreSQL (JSON→Postgres — WP1 / WP2.1 state)

Status as of 2026-06-22. The PostgreSQL backend is **built and proven for the
tier-1 artifacts**, switchable by an env var. This note is the practical guide to
standing it up. It is **not yet a full cutover** — see *Scope* below.

## What works today
- 11-table relational schema (catchment, port_run + 6 portfolio entities +
  gauge_hazard_curve, prs_trade, eod_snapshot), live, zero model↔migration drift.
- `PostgresRepository` — the full `Repository` interface, with `save→load` parity
  proven on the real `thames` catchment (797 records).
- Each entity promotes its identifying/queryable fields to typed, indexed columns
  and keeps the verbatim CDM document in a `cdm` JSONB column (lossless).
- One-line switch: `MKM_REPO_BACKEND=pg`.

## Stand it up

```bash
# 1. Start Postgres (dev; postgres:16). Defaults match config/database.py.
docker compose -f docker/docker-compose.yml up -d postgres

# 2. Apply the schema.
source .venv/bin/activate
alembic upgrade head            # alembic check should then say "no new operations"

# 3. Import a catchment from files into Postgres (idempotent).
python - <<'PY'
import sys; sys.path.insert(0, 'src')
from database._pg.etl import import_catchment
print(import_catchment("thames"))   # -> {'gauge': 152, 'property': 100, ...}
PY

# 4. Run the app reading from Postgres (no caller changes).
MKM_REPO_BACKEND=pg python app.py server --thames
```

## Configuration (all in `config/database.py`, rule R1)
- `MKM_REPO_BACKEND` — `file` (default) or `pg`. Selects the backend at startup.
- `MKM_DATABASE_URL` — full SQLAlchemy URL override; else composed from
  `MKM_DB_HOST/PORT/NAME/USER/PASSWORD` (defaults match docker-compose).

## Scope — important
Mapped to tables today — **everything except the binary blob tier**:

- the **9 tier-1 entity/keyed artifacts** shredded into relational rows;
- the **16 whole-document artifacts** (`port_document`, one row per
  `(catchment, artifact, mode)`) — storm sequences/summaries, perils, trading
  state (`market_state` / `trade_marks` / history), property & commercial hazard
  curves (all modes), the flood summary, classifier training metadata;
- the **7 keyed-record artifacts** (`port_record`, one row per
  `(catchment, artifact, mode, key)`) — property/commercial/gauge timeseries,
  gauge history, stress storms, sequence gauges, typhoon-damage events.

With `MKM_REPO_BACKEND=pg`, the only still-**unmapped** artifact is the **blob
tier** — classifiers (`.joblib`) and typhoon particle files — which raises
`NotImplementedError`. Remaining migration work:

1. The blob tier → object store (MinIO vs cloud — decision still open).
2. WP2 full cutover (per-catchment, all artifacts), WP4 E2E rework, WP5
   RBAC/pooling/decommission.

The **WP1.7 dual-read parity harness** (`src/database/_pg/parity.py`) is the
regression net for the cutover: `check_catchment(catchment)` compares a file
read against a pg read for every mapped artifact (collections normalised by id,
documents and keyed records per mode) and returns a pass/fail report.

All SQL/ORM/Alembic lives under `src/database/_pg`, kept green by the data-access
audit. The itemised plan + design notes are in the `json_to_postgres_migration`
memory and `docs/json_to_postgres_migration.md`.
