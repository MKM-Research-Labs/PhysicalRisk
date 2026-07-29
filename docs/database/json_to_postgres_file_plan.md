# File-by-File Migration Plan — Port JSON → PostgreSQL

**Status:** Draft — 2026-06-18. Companion to `docs/json_to_postgres_migration.md` (WBS),
`docs/json_artifact_catalogue.md` (artifact↔table mapping), `docs/db_users_and_permissions.md`.

This is the concrete change list: **every source file** that reads or writes
`data/input/<catchment>/…` JSON today, and the edit it gets. Derived from **four
complementary sweeps** — config path accessors, the `JSON_FILES` registry, literal
artifact filenames, and raw `.glob()` / `read_json` / `INPUT_DIR` constants — to catch
files that bypass the accessors. **~112 non-test source files + ~149 test files.**

> **Completeness note.** An accessor-only sweep found 88; three extra sweeps
> (`JSON_FILES`, literal filenames, globs) found ~24 more (Group H); a final sweep of
> frontend JS, entry points, static serving, `scripts/`, and a read_text/open catch-all
> across all code dirs added 1 more (`scripts/beta_sweep_analyze.py`) and confirmed the
> exclusions below. **Total ≈ 113 source files.** High confidence this is the full set,
> but not a mathematical guarantee — deeply indirect access could exist. The 0.8 audit is
> the real backstop: once green, *nothing* outside `src/repository/` touches the data, by
> construction.

## How to read

- **Role:** `WRITE` = produces JSON during port; `READ` = consumes it at runtime;
  `R/W` = both; `PATH` = path layer; `LOADER` = existing loader/cache to absorb;
  `TOOL` = standalone tool; `ANCHOR` = foundational, change first.
- **Change** = what the file's edit is. The overwhelmingly common edit is the
  **standard pattern** below; only deviations are spelled out.

## The standard pattern (applies to almost every READ/WRITE file)

```
BEFORE:  with open(config.get_input_path('property.json')) as f:  data = json.load(f)
AFTER:   data = repo.load('property', catchment)            # from src.repository import repo

BEFORE:  json.dump(payload, open(path, 'w'), indent=2)
AFTER:   repo.save('gauge', catchment, payload)

BEFORE:  for p in config.get_gaugets_dir().glob('*.json'): ...
AFTER:   for key in repo.iter_keys('gauge_timeseries', catchment): ...
```

No file outside `src/repository/` keeps a `json.load`/`json.dump`/`glob` against
`data/input`, an `open()` of it, or (post-WP1) any SQL. Enforced by audit task 0.8.

---

## Group A — Anchors & path layer (change FIRST, WP0.2–0.4)

| File | Role | Change |
|---|---|---|
| `src/repository/` (NEW package) | ANCHOR | Create `base.py` (Protocol), `file_repo.py`, `artifacts.py`, public `__init__.py`; later `pg_repo.py` + private `_engine/_queries/_models`. The only SQL owner. |
| `src/jsonfiles.py` | ANCHOR | Already the `JSON_FILES` filename registry — **fold into** `src/repository/artifacts.py` as the artifact→table/key map. Single source of truth for "what artifacts exist". |
| `src/loaders/timeseries_loader/_loading.py` | LOADER | Existing per-gauge file load + cache. Re-point its loads to `repo.load(...)`; its cache becomes (or defers to) the repo cache. |
| `src/loaders/timeseries_loader/_queries.py` | LOADER | Same package — re-point file access to repo. (Note: rename to avoid confusion with the repo's private `_queries.py`.) |
| `src/loaders/gauge_loader.py` | LOADER | Reads `gauge` — a transitive chokepoint for routes/reports. Re-point to `repo`. |
| `src/loaders/property_loader.py` | LOADER | Reads `property` — chokepoint. Re-point to `repo`. |
| `src/loaders/rloan_loader.py` | LOADER | Reads `loan` (RLOAN-prefixed) — chokepoint. Re-point to `repo`. |

> **The `src/loaders/*` family is leverage.** Many routes/reports read *through* these
> loaders, not directly. Migrating the 4 loader modules transitively covers a chunk of
> Groups C/D — do these early in WP0.6.
| `config/path/_portfolio_paths.py` | PATH | Keep as-is for the file backend; `FileRepository` calls these accessors internally. No caller change. |
| `config/path/_config_paths.py` | PATH | As above. |
| `config/path/registry.py` | PATH | Extend the sanctioned-package concept: add `src/repository` as the only data-access package (mirrors the path audit). |
| `config/catch.py` | PATH | Catchment resolution stays; repo binds to active catchment here. |

---

## Group B — Producers / writers (WP0.5) — `src/port/**` + `app/commands/**`

Each writes one or more artifacts; swap `json.dump`/`write_text` → `repo.save(...)`.

| File | Role | Artifact(s) written |
|---|---|---|
| `src/port/src/gauge/_gauge_generate.py` | WRITE | `gauge` |
| `src/port/src/gauge/gauge.py` | WRITE | gauge orchestration |
| `src/port/src/gauge/synthetic/generator/_core.py` | WRITE | `gauge` (synthetic append) |
| `src/port/src/gauge/gaugehd/nrfa.py` · `synthetic.py` · `runner.py` · `loader.py` | R/W | `gauge_history` (loader reads) |
| `src/port/src/gauge/gaugets.py` | WRITE | `gauge_timeseries` |
| `src/port/src/gauge/stress_storms.py` · `_stress_storms_stages.py` | WRITE | `stress_storm` + index |
| `src/port/src/property/main/generator.py` | WRITE | `property` |
| `src/port/src/property/ts/flood/process.py` · `ts/generator.py` | WRITE | `property_timeseries` (+ summary) |
| `src/port/src/property/ts/loader.py` | READ | `property_timeseries` |
| `src/port/src/property/hc/generator/_generator.py` · `_decomposition.py` | WRITE | `property_hazard_curve` (all modes) |
| `src/port/src/peril/peril_ts.py` | WRITE | `property_timeseries` (wind modes) |
| `src/port/src/mortgage/_generate.py` · `_generator.py` | WRITE | `loan` |
| `src/port/src/commercial/main/generator.py` | WRITE | `commercial` |
| `src/port/src/commercial_loan.py` | WRITE | `commercial_loan` |
| `src/port/src/counterparty/_generator.py` | WRITE | `counterparty` |
| `src/port/src/book/book_common/_pricing.py` | WRITE | `prs_trade` |
| `src/port/src/historical_eod/_history.py` · `_series.py` | WRITE | `eod_snapshot`, `market_state` |
| `src/port/src/storm_multi/utils/serialization.py` · `models/_spatial_math.py` | WRITE | `storm_sequence` (+ summary, config) |
| `src/port/src/stressm/gaugets_writer.py` · `summary.py` · `pipeline/stages.py` · `pipeline/orchestrator/_core.py` · `batch_train.py` · `classifier/_core.py` | R/W | `gauge_timeseries`, `sequence_gauge`, classifiers |
| `src/port/src/gauge/synthetic/…` (remaining) | WRITE | gauge synthetic helpers |
| `src/port/storm_typhoon_pairing.py` | READ | pairing lookup (storm↔typhoon) |
| `src/port/utils/generator_base.py` | R/W | shared writer base — central swap point for many generators |
| `src/port/cdm/gaugehd/generator.py` · `cdm/oed_export/_core.py` | WRITE | `gauge_history`, OED export |
| `app/commands/port/orchestrator.py` | WRITE | pipeline driver — pass `port_run_id` to repo |
| `app/commands/port/stages/trading.py` | WRITE | `trade_mark` |
| `app/commands/port/stages/fire.py` · `seismic.py` | WRITE | `fire_result`, `seismic_result` |
| `app/commands/port/stages/windhazard/_placeholders.py` · `commercial.py` | WRITE | wind hazard placeholders |
| `app/commands/port/stages/storm.py` · `typhoon/_run.py` | WRITE | storm / typhoon stage outputs |
| `app/commands/port/summary.py` · `summary_sections.py` | READ | counts artifacts for the run summary |
| `app/commands/book.py` | READ | reads `gaugehc` for book build |

(Commercial TS + commercial HC generators under `src/port/src/commercial/ts` and
`…/hc/generator` are in the same package — same swap.)

---

## Group C — Consumers: Flask routes (WP0.6) — `src/routes/**`

Swap reads → `repo.load(...)` / `repo.iter_keys(...)`. Artifact per file from the catalogue.

| File | Reads |
|---|---|
| `src/routes/_storm_enrich.py` | `gauge`, `storm_sequence`, `stress_storm`, `gaugehc` |
| `src/routes/counterparty.py` | `counterparty` |
| `src/routes/health.py` | reports dir (status only) |
| `src/routes/perils.py` | `fire_result`, `seismic_result` |
| `src/routes/properties/_routes.py` | `property` |
| `src/routes/gauges/_helpers.py` · `hazard.py` · `history.py` · `reports.py` · `storms.py` | `gauge`, `gauge_hazard_curve`, `gauge_history`, `gauge_timeseries`, `storm_sequence` |
| `src/routes/propertyhc/_helpers.py` | `property_hazard_curve` (all modes) |
| `src/routes/propertyts/_helpers.py` · `animation/_helpers.py` · `claim.py` · `core_storm_list.py` · `core_storms/_helpers.py` · `financial_basis.py` · `financial_loaders.py` · `financial_prs.py` · `risk.py` · `wind_impact.py` | `property`, `loan`, `gauge`, `gaugehc`, `property_timeseries`, `stress_storm`, `storm_sequence`, `prs_trade`, `typhoon_event` |
| `src/routes/commercial/hazard/_helpers.py` · `hazard/_routes.py` · `portfolio/_blotter.py` · `portfolio/_impact.py` · `portfolio/_list.py` · `pricing.py` · `reports.py` · `storms.py` | `commercial`, `commercial_loan`, `commercial_hazard_curve`, `commercial_timeseries`, `fire_result`, `seismic_result` |
| `src/routes/prs/blueprint.py` | `prs_trade` (also a **mutating** endpoint — see Group F) |
| `src/routes/trading/_helpers.py` · `blotter.py` · `client.py` · `eod.py` · `risk.py` · `port_stress/_routes.py` | `prs_trade`, `trade_mark`, `market_state`, `eod_snapshot`, `gaugehc`, `gauge` |
| `src/routes/trading/stress/_helpers.py` · `scenario.py` · `training.py` · `classifiers/batch_training.py` · `classifiers/summary.py` | `stress_storm`, `gauge_timeseries`, `gaugehc`, `gauge`, `storm_sequence`, classifiers |
| `src/routes/governance/lineage/_trace/_data_trace.py` · `_staleness.py` | `gauge`, `counterparty`, `sequence_gauge`, `property_timeseries` (lineage trace) |
| `src/routes/visualization.py` | visualization data feed |

**Special:** `trading/stress/_helpers.py` holds the only cache today (mtime). Fold into
the repo (task 0.7) so `PostgresRepository` provides equivalent caching.

---

## Group D — Other consumers (WP0.6) — reports / models / lineage / visual

Easy to miss; they read `data/input` directly outside the routes.

| File | Role | Reads |
|---|---|---|
| `src/reports/port/data_loader.py` | READ | central report data load — high-value single swap |
| `src/reports/commercial/commercial_report.py` · `commercial/generator.py` | READ | commercial + curves |
| `src/reports/gauge/gauge_page_12_trading.py` | READ | trading marks / curves |
| `src/reports/property/property_page_09_history/_builders.py` | READ | property history / TS |
| `src/reports/risk/generator.py` | READ | risk inputs |
| `src/reports/trading/eod_generator.py` | READ | `eod_snapshot` |
| `src/models/trading/market_state/manager.py` | R/W | `market_state` |
| `src/models/trading/trade_marks.py` | R/W | `trade_mark` |
| `src/models/trading/pnl_engine/_core.py` | READ | marks / curves for PnL |
| `src/lineage/field_usage/_prs.py` · `_fire_seismic.py` | READ | scans artifacts for field lineage |
| `src/lineage/manifest/_core.py` | READ | manifest over artifacts |
| `src/lineage/validation/_helpers.py` · `completeness.py` · `prerequisites.py` | READ | validates artifact presence/shape |
| `src/visual/core/data_loader/_core.py` · `visualizer/coordinator.py` | READ | map/visual data feed |

---

## Group E — Tools (WP3) — NOT a transparent swap

| File | Role | Change |
|---|---|---|
| `tools/cdm_property_editor/app.py` | R/W | Hardcodes `INPUT_DIR=thames`, `FIRE_FILE`, `SEISMIC_FILE`, `storm_sequences`. Re-point to `repo`, make catchment a parameter, replace the sandbox-JSON write with a repo scratch run. |
| `tools/cdm_property_editor/_recompute_oracle.py` · `recompute.py` | R/W | Hardcoded `THAMES/...` reads of `property`, `propertyts`, `gaugets`, etc. → `repo`. |

---

## Group F — Mutating endpoints to wrap with permissions (WP5.1)

Independent of the file/DB swap: tag the ~65 mutating endpoints with `@require(FuncNNN, cap)`.
Map to the live functions in `docs/db_users_and_permissions.md`:

| Function | Endpoints (representative) | Files |
|---|---|---|
| **Func001** Create synthetic portfolio | port generation triggers | `app/commands/port/*`, any app-driven "generate" route |
| **Func002** Upload real portfolio | upload/ingest (to be built) + CDM edits | `tools/cdm_property_editor/app.py`, future upload route |
| **Func003** Trade PRS | `/prs/commit`, `/trading/close/<swap_id>`, `/trading/eod`, yield/hazard curve commit | `src/routes/prs/blueprint.py`, `src/routes/trading/blotter.py`, `eod.py`, `curves_yield.py`, `curves_hazard.py` |
| **Func000** Admin | user/permission CRUD (new) | new admin routes; replaces `src/routes/_admin_auth.py:require_admin_password` |

---

## Group G — Tests (WP4) — ~149 files, mostly via shared fixtures

Do **not** edit 149 files individually. Most route/port tests read data through fixtures
or the `MKM_CATCHMENT_INPUT_OVERRIDE` tmp-tree mechanism. Strategy:

| Area | Files (approx) | Change |
|---|---|---|
| `tests/routes/**` (incl. governance, propertyts, gauges, trading) | ~70 | Point the shared conftest fixture at a per-test DB schema / repo instead of a tmp file tree. Individual tests unchanged. |
| `tests/port/**` | ~20 | Generators write via repo in tests too; assert against repo, not files. |
| `tests/data/**` | ~14 | Data-shape tests → run against importer output (parity harness, WP1.7). |
| `tests/e2e/**` | ~5 | Replace `MKM_CATCHMENT_INPUT_OVERRIDE` file-copy with schema-per-test (WP4.1). |
| `tests/reports/**`, `tests/config/**`, `tests/commands/**`, `tests/visual/**` | ~15 | Follow the fixture change. |
| `tests/repository/**` (NEW) | — | Characterization + dual-read parity suites (tasks 0.9, 1.7). |

---

## Group H — Files added by the completeness re-sweep (were missed by accessor-only pass)

These bypass the path accessors (literal filenames, globs on passed-in dirs, or the
loader family). Same standard pattern applies; slotted into their work package.

| File | Role | Reads/Writes | WP |
|---|---|---|---|
| `src/loaders/gauge_loader.py` · `property_loader.py` · `rloan_loader.py` | LOADER | `gauge` / `property` / `loan` | 0.6 (early) |
| `app/commands/port/context.py` | WRITE | port run context | 0.5 |
| `app/commands/port/stages/hazardcurves.py` | WRITE | `gaugehc` + hc stage driver | 0.5 |
| `app/commands/port/summary_sections.py` | READ | counts artifacts for run summary | 0.5 |
| `app/commands/port/stages/windhazard/_helpers.py` | R/W | wind hazard outputs | 0.5 |
| `app/commands/test/lineage.py` | READ | lineage test command | 0.6 |
| `src/models/trading/market_state/_persistence.py` | WRITE | `market_state` | 0.5 |
| `src/models/trading/pnl_engine/_pnl.py` | READ | marks / curves (sibling of `_core`) | 0.6 |
| `src/models/stress/flood_classifier/_predictor.py` | READ | classifiers | 0.6 |
| `src/models/winddamage/event.py` | READ | typhoon/wind events (glob) | 0.6 |
| `src/port/src/_typhoon_join.py` | R/W | typhoon join | 0.5 |
| `src/port/src/property/hc/loader.py` | READ | `property_hazard_curve` | 0.6 |
| `src/port/src/property/main/locations.py` | READ | property locations | 0.5 |
| `src/port/src/stressm/gauge_parser.py` | READ | `gauge_timeseries` | 0.5 |
| `src/port/cdm/gaugehd/directory.py` | READ | `gauge_history` dir | 0.5 |
| `src/reports/port/prs_report.py` | READ | `prs_trade` | 0.6 |
| `src/routes/propertyhc/_perils.py` | READ | `property_hazard_curve` (modes) | 0.6 |
| `src/routes/propertyts/animation/_routes.py` | READ | animation feed | 0.6 |
| `src/routes/propertyts/financial_impact.py` | READ | `gaugehc`, `property_timeseries` | 0.6 |
| `src/routes/trading/curves.py` | READ | hazard/yield curves | 0.6 |
| `src/visual/core/data_loader/_loaders.py` | READ | visual data feed (sibling of `_core`) | 0.6 |
| `src/visual/core/visualizer/heatmap.py` | READ | visual heatmap data | 0.6 |
| `scripts/beta_sweep_analyze.py` | READ | analysis script, **hardcoded** `data/input/halong/…` (`storm_sequences`, `propertyhc`, event globs) + a non-standard `.beta_study/` tree | 0.6 (low priority) |

---

## Verified NOT impacted / out of scope (final sweep)

Confirmed by sweeping frontend JS, entry points, static-file serving, `scripts/`, and a
read_text/open catch-all across every code dir (`app config scripts src tests tools`
+ `wsgi.py`/`phys.py`).

| Area | Finding | Action |
|---|---|---|
| **Frontend JS** (all `src/**/*.js`) | Every fetch targets `/api/v1/…`; **no JS reads data files directly** | None — DB swap is invisible to the frontend |
| **Entry points** (`wsgi.py`, `phys.py`, `src/server.py`, `app/commands/server.py`) | No JSON IO; they only bind the active catchment (`config.catchment_id`) | Repo initializes/binds catchment here — no data-IO edit |
| **Static/file serving** (`send_file`/`send_from_directory`) | Serve generated **PDFs** (EOD/PRS/MRC), governance docs, HTML, icons — **not port JSON** | None |
| **Generated report PDFs** under `…/blotter/eod/*.pdf` etc. | Binary report outputs, not source data | Stay as files / object store; **not** part of JSON→DB scope. The *data* behind them moves to DB; the PDF generators (Group D) read from the repo |
| **Governance JSON** (`model_inventory.json`, `data_lineage.json`, audit log) | Version-controlled, deliberately excluded | Out of scope (locked decision) |
| **`docker/`** | Deployment config — mounts the `data/` volume, sets `MKM_*` env | Not a data-IO file, but **update at WP1/WP5**: add the Postgres (+MinIO) service and DB connection env |

---

## Counts & ordering

- **Total impacted non-test source files: ~113** (88 accessor + ~24 re-sweep + 1 script). Tests: ~149.
  Frontend JS, entry points, and static file-serving verified **not** impacted (see above).
- **Group A:** 11 (anchors + path + 4-file loader family) — do first.
- **Group B (writers):** ~46 incl. Group H additions. **Group C (routes):** ~44.
  **Group D (other consumers):** ~22. Groups B–D are the bulk of WP0.5/0.6 — one pattern.
- **Group E (tools):** 3. **Group F (permissions):** ~65 endpoints across ~12 files.
- **Group G (tests):** ~149, but ~90% absorbed by fixture changes, not per-file edits.
- **Backstop:** the 0.8 audit, once green, guarantees no missed file remains — it fails CI
  on *any* data access outside `src/repository/`, found by inspection or not.

Sequencing: A → (B ∥ C ∥ D, in parallel) → audit 0.8 green → Group G fixtures → then
WP1 schema/ETL flips the backend behind the now-stable seam.
