# Migration Plan: Port JSON Artifacts → PostgreSQL

**Status:** Draft for review — 2026-06-18
**Companion docs:** `docs/json_artifact_catalogue.md` (producer→file→consumer matrix,
deliverable 0.1) · `docs/json_to_postgres_file_plan.md` (file-by-file change list, 88 src
+ 149 test files) · `docs/db_users_and_permissions.md` (Admin-managed RBAC, feeds WP5.1)
**Goal:** Replace the per-catchment JSON file tree with a single PostgreSQL database
holding all catchments, giving production-grade security (roles, auth, RLS, audit,
backups) and a look-and-feel closer to a real risk system.

## Locked decisions

| Decision | Choice |
|---|---|
| Engine | **PostgreSQL** (single instance, `catchment_id` as a column — not schema-per-catchment) |
| Large blobs (typhoon particles ~69 MB each) | **Hybrid** — metadata + URI in Postgres, blob in object store (S3 / MinIO) |
| Scope | **Port artifacts only** — governance files (`model_inventory.json`, `data_lineage.json`, audit log) stay version-controlled |
| **Data access (NON-NEGOTIABLE)** | **ALL database access goes through ONE utility package. ZERO direct SQL, ORM sessions, or connection objects anywhere else in the codebase.** Enforced by a zero-tolerance CI audit. See §2.0. |

> ## ⚠️ Hard rule — single data-access utility
>
> There is exactly **one** package that may import a DB driver / ORM, open a
> connection, or contain SQL: the data-access utility (`src/repository/`). Every other
> module — routes, port generators, tools, tests — calls the utility's typed functions
> and **never** sees SQL, a cursor, a session, or a connection string. This is the same
> discipline already enforced for filesystem paths by the path-definition audit, applied
> to data access. A CI gate fails the build if any `SELECT/INSERT/UPDATE/DELETE`,
> `.execute(`, `sqlalchemy`/`psycopg` import, or connection handle appears outside the
> utility package (see task 0.8 / WP1.6). No exceptions, no "just this once".

---

## 1. Current state (the thing we are replacing)

- **~16,700 JSON files, ~4.6 GB**, across 3 active catchments (thames, halong, mekong)
  + empty rhine. Stored on an external SSD reached via the `data/` symlink.
- **Generation:** 4-layer orchestrator (`app/commands/port/orchestrator.py`):
  Portfolios → Hazards → Hazard Curves → Trading. ~25 writer modules under `src/port/`
  each `json.dump` to a path obtained from `config/path/`.
- **Paths are already centralized** in the `config/path/` package
  (`_portfolio_paths.py`, `_config_paths.py`, `registry.py`), enforced by the
  path-definition audit. This is the foundation the migration builds on.
- **Reads are NOT centralized:** ~63 call-sites in ~25 route modules call
  `json.load(open(config.get_input_path(...)))` directly. Only the stress-storm
  index has an mtime cache; everything else hits disk per request.
- **Catchment selection is global process state** (`MKM_CATCHMENT`, default `thames`),
  refreshed via `config._init_paths()`. Concurrent multi-catchment requests already race.

### File-count drivers (what actually makes it 16k files)

| Driver | ~Files | Storage tier in target |
|---|---|---|
| `typhoon/` particle/event blobs (halong) | 6,300 (≤69 MB each) | **Object store + metadata row** |
| `stress_storms/*` + `_index.json` | 3,000+ | JSONB rows |
| per-asset timeseries (`propertyts`, `*tsd/e/b`, wind ×5; `commercialts*`) | 2,200+ | JSONB rows |
| `gaugets`, `gaugehd`, `sequence_gauge` (per gauge) | ~150 ea / catchment | JSONB rows |
| EOD blotter snapshots | ~90 / catchment | relational table |
| root aggregates (`gauge/property/loan/commercial/counterparty/*hc.json`) | ~20 / catchment | relational tables |

---

## 2. Target architecture

### 2.0 The data-access utility package — the ONLY place SQL exists

This is the architectural cornerstone and the **non-negotiable rule** above. There is
exactly one package — `src/repository/` — that knows the database exists. Strict layering:

```
src/repository/
├── __init__.py        # PUBLIC API — the ONLY symbols other code may import
├── base.py            # Repository protocol (typed methods, JSON-shaped in/out)
├── file_repo.py       # FileRepository (Phase 0 — wraps today's json.load/glob)
├── pg_repo.py         # PostgresRepository (Phase 1+)
├── _engine.py         # PRIVATE — engine/pool/session; the ONLY connection owner
├── _queries.py        # PRIVATE — every SQL statement / ORM query lives here
├── _models.py         # PRIVATE — table defs (SQLAlchemy Core/ORM), if used
└── artifacts.py       # artifact-name → table/key mapping
```

- **Everything under `_*.py` is private.** Only `src/repository/__init__.py` exports a
  public surface. Routes / port generators / tools / tests import *only* that surface.
- **No SQL string, cursor, session, connection, or `sqlalchemy`/`psycopg` import may
  appear anywhere outside `src/repository/`.** Callers pass domain arguments
  (artifact name, catchment, entity id, payload) and receive plain Python
  dicts/lists/dataclasses. They cannot tell whether the backend is files or Postgres.
- The public API is the typed methods in `base.py` (below) plus a small number of
  intent-named helpers (e.g. `get_property`, `list_stress_storms(catchment)`,
  `commit_prs_trade(...)`) — never a generic "run this SQL" escape hatch. **There is no
  `execute_sql()` / `raw_query()` public function. Deliberately.**

### 2.1 The public interface (the seam)

All reads/writes funnel through this one interface, mirroring how all *paths* already
funnel through `config/path/`:

```python
class Repository(Protocol):
    def load(self, artifact: str, catchment: str, key: str | None = None) -> dict | list: ...
    def save(self, artifact: str, catchment: str, payload, key: str | None = None) -> None: ...
    def iter_keys(self, artifact: str, catchment: str) -> Iterator[str]: ...   # replaces glob()
```

- `FileRepository` — wraps today's exact `json.load` / `glob` behavior (Phase 0).
- `PostgresRepository` — same interface, all SQL confined to `_queries.py` / `_engine.py`.

Once the seam exists, the file→DB swap is invisible to the 63 call-sites, **and** the
"no SQL outside the utility" rule is structurally guaranteed because nothing else can
reach the database. **Build the seam first; it is valuable on its own even if the DB
migration stalls.**

### 2.2 Storage tiers

1. **Relational tables** — entities you filter/join/aggregate:
   `gauge`, `property`, `loan`, `commercial`, `commercial_loan`, `counterparty`,
   `gauge_hazard_curve`, `property_hazard_curve` (+ shd/she/bri/wind variants),
   `commercial_hazard_curve`, `prs_trade`, `eod_snapshot`, `trade_mark`, `market_state`,
   `storm_sequence`.
2. **JSONB columns** — document-shaped timeseries keyed by
   `(catchment_id, entity_id, scenario_mode)`: `property_timeseries`, `gauge_timeseries`,
   `stress_storm`, `sequence_gauge`, `gauge_history`.
3. **Object store + metadata row** — `typhoon_event` (row holds event metadata + a
   `blob_uri`; the particle array lives in S3/MinIO).

### 2.3 Single-DB, multi-catchment

Every table carries `catchment_id` (FK to a `catchment` table). Indexes lead with
`catchment_id`. This satisfies the "single database for all catchments" requirement,
enables cross-catchment queries, and is where PostgreSQL Row-Level Security can enforce
per-catchment access if needed.

### 2.4 Provenance (new capability)

Add `port_run_id`, `generated_at`, `schema_version` to every table. A regenerated port
becomes a new run that versions cleanly instead of silently overwriting the tree — this
is something the current file layout does poorly and pairs naturally with `data_lineage`.

---

## 3. Phased plan

### Phase 0 — Repository seam (no DB)
- Add `Repository` + `FileRepository`; route all reads (63 sites) and the ~25 writers
  through it. Replace raw `glob()` with `iter_keys()`.
- Characterization tests: assert byte-identical behavior vs. today.
- Add a **data-access audit** (sibling to the path-definition audit) forbidding raw
  `json.load`/`open` of `data/input` outside the repository.
- **De-risks the whole project and ships value standalone.**

### Phase 1 — Schema + dual-read parity
- Stand up Postgres + Alembic migrations; design schema per §2.2.
- ETL importer: load one catchment's files → DB (idempotent, re-runnable).
- `PostgresRepository`; wire object store for typhoon blobs.
- **Dual-read** in CI/E2E: read from file + DB, diff per artifact type, fail on mismatch.

### Phase 2 — Cutover, catchment by catchment
- Flip reads to Postgres, **mekong first** (smallest, 193 MB), files as fallback.
- Then halong, then thames.
- Flip writes: port generator's `Repository.save` targets the DB.
- Give the request layer a **request-scoped catchment context** to replace the global
  `config` singleton (fixes the existing concurrency race).

### Phase 3 — Tooling + production hardening
- Migrate the **CDM Property Editor** (`tools/cdm_property_editor/`, port 5057) and the
  recompute tool — both currently **hardcode `thames`** and write a non-syncing sandbox.
  They need explicit handling, not the transparent route swap.
- Replace E2E isolation (`MKM_CATCHMENT_INPUT_OVERRIDE` tmp file-tree copy) with a
  per-test schema or transaction rollback.
- Add roles/auth, connection pooling, backups, RLS.

### Phase 4 — Decommission files
- Once dual-read parity has held for an agreed window, retire the file readers.

---

## 4. Risks / gotchas

- **External SSD:** ETL must run with the SSD mounted (`data/` symlink). The DB then
  removes this fragility for readers.
- **Concurrency:** global-state catchment selection races today; fix via request-scoped
  context in Phase 2.
- **Standalone tools** bypass `config` and hardcode thames — Phase 3, not transparent.
- **Test architecture:** 6,000+ Python + 53 JS tests, plus E2E that copy file trees.
  Each phase needs the test seam updated alongside.
- **Audit coverage:** without a data-access audit, new code will bypass the repository
  the way reads bypass abstraction today.
- **Governance files out of scope** but are a natural future DB fit — keep the door open.

---

## 5. Effort summary

| Aspect | Effort | Why |
|---|---|---|
| Path resolution | Low | already centralized in `config/path/` |
| Repository seam (Phase 0) | Medium | 63 reads + 25 writers, but mechanical |
| Schema + ETL + dual-read | Medium–High | the real design work |
| Route cutover | Low | transparent behind the seam |
| Tools (CDM editor, recompute) | Medium | hardcoded thames, separate sandbox |
| Test/E2E rework | Medium | isolation model changes |

---

## 6. Itemised work breakdown (project plan)

Effort key: **S** ≈ ½ day · **M** ≈ 1–2 days · **L** ≈ 3–5 days. IDs are stable so they
can be referenced in commits/PRs. "DoD" = Definition of Done.

### WP0 — Repository seam (no DB) — *start here tomorrow*

Goal: every read and write of `data/input/<catchment>/` flows through one interface,
with behavior byte-identical to today. No DB involved. This WP de-risks everything else.

| ID | Task | Target files | DoD | Dep | Effort |
|---|---|---|---|---|---|
| 0.1 | Inventory & freeze the artifact catalogue | new `docs/json_artifact_catalogue.md` | One row per artifact type: name, path pattern, key (entity id / mode), reader sites, writer module, cardinality, target tier. ~30 rows. | — | S |
| 0.2 | Define `Repository` protocol + artifact registry | new `src/repository/__init__.py`, `base.py`, `artifacts.py` | `Repository` protocol (`load/save/iter_keys/exists`); `artifacts.py` maps artifact name → path template (delegating to `config/path/`) + key rule. Unit-tested. | 0.1 | M |
| 0.3 | Implement `FileRepository` | `src/repository/file_repo.py` | Wraps today's `json.load`/`json.dump`/`glob`. `iter_keys` replaces glob. Round-trip tests prove byte-identical output. | 0.2 | M |
| 0.4 | Singleton/accessor + catchment binding | `src/repository/__init__.py`, touch `config/__init__.py` | `get_repository()` returns process repo bound to active catchment; honours `MKM_CATCHMENT`. No behavior change. | 0.3 | S |
| 0.5 | Migrate the ~25 writers in `src/port/` | `src/port/**` (gauge, property, mortgage→loan, commercial, hc generators, peril_ts, historical_eod, book, counterparty, stress) | Every `json.dump` to `data/input` replaced by `repo.save(...)`. Port `--all` run produces identical tree (diff check). | 0.4 | L |
| 0.6 | Migrate the ~63 route reads | `src/routes/propertyts/**`, `commercial/**`, `trading/stress/**`, `counterparty.py` | Every `json.load(open(get_input_path()))` replaced by `repo.load(...)`; every `glob` by `iter_keys`. App behaves identically. | 0.4 | L |
| 0.7 | Fold the stress-storm mtime cache into the repo | `src/routes/trading/stress/_helpers.py`, `src/repository/file_repo.py` | Cache moves behind repo so it survives the DB swap; mtime semantics preserved. | 0.6 | S |
| 0.8 | **Data-access audit (zero-tolerance gate)** — sibling to the path-definition audit | new `docs/models/data_access.py` audit + `tests/audit/` | Scanner fails CI if **anything outside `src/repository/`** contains: a SQL keyword (`SELECT/INSERT/UPDATE/DELETE/CREATE/ALTER`), `.execute(` / `.executemany(`, a `sqlalchemy` / `psycopg` / `asyncpg` import, a connection/session/cursor handle, or `json.load`/`open` targeting `data/input`. Allowlist = `src/repository/` only. Backlog = 0. Wired into the full-audit suite. | 0.5, 0.6 | M |
| 0.9 | Characterization test suite | `tests/repository/` | Golden-tree comparison: generate small port, snapshot tree, assert repo round-trips identically. Runs in CI. | 0.3 | M |

### WP1 — PostgreSQL schema + ETL + dual-read

| ID | Task | Target files | DoD | Dep | Effort |
|---|---|---|---|---|---|
| 1.1 | Provision Postgres + migration tooling | `docker/`, `pyproject.toml`, new `db/` | Local Postgres via docker-compose; Alembic wired; `catchment` seed table. | — | M |
| 1.2 | Design relational schema (entities/curves/trades/EOD) | `db/models/`, Alembic rev | Tables per §2.2 tier 1, all with `catchment_id`, `port_run_id`, `generated_at`, `schema_version`; FKs + indexes leading on `catchment_id`. | 1.1, 0.1 | L |
| 1.3 | Design JSONB tables (timeseries/stress/sequence) | `db/models/`, Alembic rev | `(catchment_id, entity_id, scenario_mode)` keyed JSONB tables; GIN indexes where queried. | 1.2 | M |
| 1.4 | Object-store integration for typhoon blobs | `db/blob_store.py`, `docker/` (MinIO) | `typhoon_event` row holds metadata + `blob_uri`; put/get against S3/MinIO; ≤69 MB blobs round-trip. | 1.1 | M |
| 1.5 | ETL importer (files → DB), idempotent | `db/etl/` | `import_catchment <name>` loads a full catchment, re-runnable (upsert by run), reports counts. Reconciles to file counts. | 1.2, 1.3, 1.4 | L |
| 1.6 | `PostgresRepository` | `src/repository/pg_repo.py`, `_engine.py`, `_queries.py`, `_models.py` | Same `Repository` interface, backed by DB; passes the WP0 characterization suite. **All SQL/ORM/connection code confined to these private modules** — the 0.8 audit stays green. | 1.2–1.4, 0.2 | L |
| 1.7 | Dual-read parity harness | `tests/repository/test_parity.py`, CI job | For each artifact type, file-read vs DB-read deep-diff; fails on mismatch. Wired into CI + E2E. | 1.5, 1.6 | M |

### WP2 — Cutover (catchment by catchment)

| ID | Task | DoD | Dep | Effort |
|---|---|---|---|---|
| 2.1 | Read-source switch (env/flag) | `MKM_REPO_BACKEND=file\|pg` selects repo impl; default still `file`. | 1.6 | S |
| 2.2 | Cut **mekong** reads to PG (smallest) | mekong served from DB in a staging run; dual-read green; file fallback retained. | 2.1, 1.7 | M |
| 2.3 | Cut **halong** then **thames** reads to PG | both catchments served from DB; parity green incl. typhoon blobs. | 2.2 | M |
| 2.4 | Request-scoped catchment context | Replace global `config` catchment state with per-request context; removes existing concurrency race. | 2.1 | M |
| 2.5 | Cut writes: port generator targets PG | `python app.py port --all` writes to DB (with `port_run_id`); files optional. | 2.3 | L |

### WP3 — Tools

| ID | Task | DoD | Dep | Effort |
|---|---|---|---|---|
| 3.1 | CDM Property Editor onto repository | `tools/cdm_property_editor/app.py` reads via repo, catchment configurable (drop hardcoded thames). | 1.6 | M |
| 3.2 | Sandbox/recompute path | `recompute.py`, `_recompute_oracle.py` use repo; sandbox writes go to a DB scratch run, not loose JSON. | 3.1 | M |

### WP4 — Test / E2E rework

| ID | Task | DoD | Dep | Effort |
|---|---|---|---|---|
| 4.1 | Replace file-tree isolation | E2E uses per-test schema or txn rollback instead of `MKM_CATCHMENT_INPUT_OVERRIDE` tmp copy. | 1.6 | M |
| 4.2 | Update affected suites | Python (6k+) + JS (53) + E2E green against PG backend. | 4.1, 2.3 | L |

### WP5 — Production hardening + decommission

| ID | Task | DoD | Dep | Effort |
|---|---|---|---|---|
| 5.1 | Admin-managed RBAC + auth (see `docs/db_users_and_permissions.md`) | `app_user`/`permission`/`audit_log` tables; `require(function, cap)` + `require_admin` decorators replace `require_admin_password`; Admin screen to create users & toggle R/W/C/D per function; `.port_admin` retired. App connects as single `svc_app` login; per-user CRUD enforced in app logic via the repository utility (no Postgres per-user roles). | 2.3 | M |
| 5.2 | Connection pooling + backups | Pooler (pgbouncer) + automated backup/restore runbook. | 2.3 | M |
| 5.3 | Decommission file readers | After parity holds N days, remove `FileRepository` from read path (keep export-to-file for archival). | 4.2, 5.1 | M |

---

## 7. Suggested sequence for tomorrow (Day 1)

A single uninterrupted thread that produces something committable by end of day:

1. **0.1** — write the artifact catalogue (forces total clarity on what moves). ~½ day.
2. **0.2 + 0.3** — `Repository` protocol + `FileRepository` with round-trip unit tests.
3. **0.9** — stand up the characterization test so every later change is guarded.

Stop there if needed: at that point the seam exists and is tested, with zero behavior
change and zero DB — the safest possible first commit. **0.5 (writers)** and **0.6
(route reads)** are the larger mechanical follow-ons for day 2+.

### Pre-work checklist before starting
- [ ] Mount the external SSD (`data/` symlink resolves).
- [ ] Work on a feature branch off `main` (not a worktree, per the no-mutating-runs rule — do real port runs in the main checkout).
- [ ] Confirm a small/fast port config exists for the characterization tests (or add one).
- [ ] Decide object-store target for WP1 (local MinIO vs cloud) — not needed for WP0.
