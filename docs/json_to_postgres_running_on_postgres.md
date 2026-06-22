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
Only the **9 tier-1 artifacts** are mapped to tables. With `MKM_REPO_BACKEND=pg`,
any code path that reads an **unmapped** artifact (timeseries, stress sequences,
property/commercial hazard curves, `market_state`/`trade_marks`, typhoon blobs,
classifiers, …) raises `NotImplementedError`. So the pg backend is suitable for
**tier-1 reads and demos**, not yet for running the whole app. Completing it is
the remaining migration work:

1. Remaining artifacts/tiers — hazard-curve *modes*, single-doc trading
   artifacts, the JSONB tier (timeseries/stress/sequence), the blob tier
   (typhoon → MinIO, classifiers).
2. WP1.7 CI dual-read parity harness (normalise record lists by id — pg
   reassembles in id order, not source-file order).
3. WP2 full cutover (per-catchment, all artifacts), WP4 E2E rework, WP5
   RBAC/pooling/decommission.

All SQL/ORM/Alembic lives under `src/database/_pg`, kept green by the data-access
audit. The itemised plan + design notes are in the `json_to_postgres_migration`
memory and `docs/json_to_postgres_migration.md`.
