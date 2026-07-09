# Running on PostgreSQL (JSON→Postgres — WP1 / WP2.1 state)

Status as of 2026-06-22. The PostgreSQL backend is **built and proven for the
tier-1 artifacts**, switchable by an env var. This note is the practical guide to
standing it up. It is **not yet a full cutover** — see *Scope* below.

## What works today
- 14-table relational schema (catchment, port_run + 6 portfolio entities +
  gauge_hazard_curve, prs_trade, eod_snapshot + the generic `port_document` /
  `port_record` / `port_blob` tables), live, zero model↔migration drift.
- `PostgresRepository` — the full `Repository` interface across **all artifact
  shapes**: collections (shredded), bespoke keyed tables, whole documents,
  keyed records, and binary blobs (object store). `save→load` parity proven on
  real `thames` data.
- Each entity promotes its identifying/queryable fields to typed, indexed columns
  and keeps the verbatim CDM document in a `cdm` JSONB column (lossless); blobs
  keep their bytes in MinIO with a `port_blob` metadata row.
- One-line switch: `MKM_REPO_BACKEND=pg`.

## Stand it up

```bash
# 1. Start Postgres (postgres:16) and MinIO (object store for the blob tier).
#    Defaults match config/database.py.
docker compose -f docker/docker-compose.yml up -d postgres minio

# 2. Install deps (adds SQLAlchemy/psycopg2/alembic/minio) + apply the schema.
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head            # alembic check should then say "no new operations"

# 3. Import a catchment into Postgres + MinIO, then dual-read-verify it (one step).
#    Exits non-zero on any file-vs-pg mismatch — the WP2 cutover gate.
PYTHONPATH=src python -m database._pg.cutover thames --import
#    (re-verify later without re-importing: drop --import)

# 4. Run the app reading from Postgres (no caller changes).
MKM_REPO_BACKEND=pg python app.py server --thames
```

**Cutover status:** **reads and writes both cut** (WP2.2 + WP2.3 + WP2.5). All
three catchments are imported and dual-read parity-green — `mekong` 53/53,
`halong` 64/64 (incl. 2,100 typhoon events), `thames` 54/54. Reads serve from
Postgres via `MKM_REPO_BACKEND=pg`; and `app.py port` now binds the same switch,
so port **generation** writes to Postgres + MinIO under `pg` (verified: the gauge
generator wrote to PG with the SSD files untouched). File backend stays the
default. Next: WP3 (tools onto the repo), WP4 (E2E + suites on `pg`), WP5
(RBAC + pooling + decommission).

## Configuration (all in `config/database.py`, rule R1)
- `MKM_REPO_BACKEND` — `file` (default) or `pg`. Selects the backend at startup.
- `MKM_DATABASE_URL` — full SQLAlchemy URL override; else composed from
  `MKM_DB_HOST/PORT/NAME/USER/PASSWORD` (defaults match docker-compose).
- `MKM_OBJECT_STORE_ENDPOINT/ACCESS_KEY/SECRET_KEY/BUCKET/SECURE` — the MinIO/S3
  object store for the blob tier (defaults match docker-compose's minio; the
  same S3 API points at cloud storage in production).

## Scope — important
**Every artifact in the registry is now mapped** — all five shapes:

- the **9 tier-1 entity/keyed artifacts** shredded into relational rows;
- **16 whole-document artifacts** (`port_document`) — storm sequences/summaries,
  perils, trading state, property & commercial hazard curves (all modes), the
  flood summary, classifier training metadata;
- **7 keyed-record artifacts** (`port_record`) — property/commercial/gauge
  timeseries, gauge history, stress storms, sequence gauges, typhoon events;
- the **blob tier** (`classifier` → `port_blob` row + MinIO object); typhoon
  particle files reuse the same path when registered.

So `MKM_REPO_BACKEND=pg` can serve the whole artifact surface (given Postgres +
MinIO up and a catchment imported). Remaining migration work is no longer about
artifact coverage:

1. WP2 full cutover — **done**: all three catchments imported + parity-green; reads
   and writes (`app.py port`) both honour `MKM_REPO_BACKEND=pg`.
2. WP4 test/E2E rework (**in progress**, see below), WP5 RBAC + pooling + decommission.

## Running the test suite on Postgres (WP4.2)

The suite can run against Postgres with the same test bodies — set
`MKM_TEST_BACKEND=pg` (default `file`, so normal CI is untouched):

```bash
docker compose -f docker/docker-compose.yml up -d postgres minio   # both must be up
PYTHONPATH=src python -m database._pg.cutover thames --import        # seed the read-path catchments
MKM_TEST_BACKEND=pg python -m pytest tests/port                      # run a dir on Postgres
```

Each test runs inside a single transaction that is rolled back on teardown
(`engine.bind_test_connection`), so there's zero per-table cleanup and no leak.
Read-path tests see the imported catchments; write-path tests (`tmp_catchment`)
get a clean slate that is also rolled back. The triage is dir-by-dir: run, bucket
failures (seed-via-seam / skip-under-pg / output-file rewrite / MinIO-blob), fix,
re-verify both modes. Current state is tracked in the `json_to_postgres_migration`
memory. Note: pg mode is ~4× slower (per-test connect/rollback), and a classifier
write under pg hits real MinIO (not transactional) — purge or skip those.

The **WP1.7 dual-read parity harness** (`src/database/_pg/parity.py`) is the
regression net for the cutover: `check_catchment(catchment)` compares a file
read against a pg read for every mapped artifact (collections normalised by id;
documents, keyed records and blobs per mode) and returns a pass/fail report.

All SQL/ORM/Alembic lives under `src/database/_pg`, kept green by the data-access
audit. The itemised plan + design notes are in the `json_to_postgres_migration`
memory and `docs/json_to_postgres_migration.md`.
