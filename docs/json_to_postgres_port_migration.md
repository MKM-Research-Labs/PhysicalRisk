# Migration Plan: `src/port` JSON Artifacts → PostgreSQL seam

**Status:** Plan written 2026-06-26. **Phase 1a (gauge book) DONE** — scanner
`src/port` 26→23 I/O files, 41→37 reads. Part of the wider json→postgres
programme (see `docs/json_to_postgres_migration.md`).

### Progress log
- **2026-06-26 — Phase 1a (gauge market-making + Thames-central book).** Both
  gauge-book generators read gauge hazard curves + counterparties through the
  seam; retired the `gaugehc_path`/`counterparty_path` params; deduped book.py's
  inline counterparty loop into `_load_counterparties` (now catchment-keyed).
  Callers + 6 test files migrated to seam-seeding via `tmp_catchment`. 106 tests
  green on the file backend; ruff-neutral. **Next: Phase 1b property book**
  (`book_property/_core.py` — propertyhc/propertybri/property reads).

> **Why `src/port` is the biggest line in the JSON-file audit (26 I/O files,
> 41 reads, 14 writes) — but mostly low-risk.** The earlier migration prioritised
> the **live-app read path** (`src/loaders/*`, now fully seam-backed). `src/port`
> is the *generation* pipeline: the modules that create the JSON in the first
> place, plus the generator-side loaders that feed them. The seam already has a
> function for almost every artifact these files touch, so ~85% of this backlog is
> a **mechanical swap** (`open()+json.load` → `database.get_*`), not new
> infrastructure.

## Ground truth

Numbers from the live scanner (`docs.models.full_audit.sections_tests.json_files.scan_repo`),
not the summarised PDF. Re-run after each commit:

```bash
PYTHONPATH=. .venv/bin/python -c "from docs.models.full_audit.sections_tests.json_files import scan_repo; \
s=scan_repo('.'); io=[f for f in s['findings'] if f['file'].startswith('src/port') and f['kind'] in ('read','write')]; \
print(len({f['file'] for f in io}),'files', sum(f['kind']=='read' for f in io),'read', sum(f['kind']=='write' for f in io),'write')"
```

**Shape parity is guaranteed.** `FileRepository.load` returns
`json.loads(p.read_text())` — byte-identical to the current `json.load(f)`. So a
getter swap returns the *same* dict; existing `.get('hazard_curves', {})`-style
access is unchanged. This is what makes Category A/B mechanical.

**Proven recipe** (already used in `src/port/src/property/main/generator.py`):

```python
import database
catchment = catchment or database.active_catchment()
data = database.get_gauge_portfolio(catchment)        # read
database.save_properties(catchment, output_data)      # write
```

The backend is bound once at the entry point (`app.py port` →
`configure_backend`); per-call code just uses the public `database.*` API. Under
the file backend the swap is a no-op behaviourally; under `MKM_REPO_BACKEND=pg`
the same code serves from Postgres.

---

## Category A — read swaps onto an existing seam getter (≈14 files)

Lowest risk: pure `json.load` → `database.get_*`. No schema change.

| Domain | Seam getter | File:line |
|---|---|---|
| Gauge hazard curves | `get_gauge_hazard_curves` | book.py:111, book_thames.py:177 |
| Property hazard curves (peril `mode=`) | `get_property_hazard_curves(c, mode=…)` | book_property/_core.py:103,114; hc/generator/_decomposition.py:59,64,69,77,88,91,94,103,106; hc/pricing/_process.py:43 |
| Counterparty | `get_counterparty_portfolio` | book.py:128, book_common/_records.py:155 |
| Property portfolio | `get_property_portfolio` | book_property/_core.py:118, property/ts/loader.py:60 |
| Gauge portfolio | `get_gauge_portfolio` | property/ts/loader.py:67, stressm/pipeline/orchestrator/_core.py:117, stressm/summary.py:85, storm_multi/models/spatial_correlation.py:278 |
| Storm sequences | `get_storm_sequences` | _typhoon_join.py:85, property/hc/loader.py:51, property/ts/loader.py:44, storm_typhoon_pairing.py:106 |
| Sequence-gauge | `get_sequence_gauge` | property/hc/loader.py:69 |
| Typhoon damage events | `iter/get_typhoon_event` | _typhoon_join.py:51,54; storm_typhoon_pairing.py:73,76 |
| Gauge timeseries | `iter/get_gauge_timeseries` | gauge/_stress_storms_stages.py:135, property/ts/loader.py:75,77 |

> The peril variants (`shd/she/bri/win/faw/fow/bow/baw`) are **modes** of
> `property_hazard_curve` (`artifacts.py`: `Spec(DOCUMENT, lambda mode:
> dl.PROPERTY_HAZARD_FILES[mode])`), so `get_property_hazard_curves(c, mode='bri')`
> covers all of `_decomposition.py`'s nine reads.

## Category B — write swaps onto an existing seam `save_*` (≈8 files)

Higher care — these *produce* the data, so a full port regen must still
round-trip (generate → seam → live-app reads identically).

| Domain | Seam saver | File:line |
|---|---|---|
| Property hazard curve writes | `save_property_hazard_curves` | hc/generator/_decomposition.py:228, hc/generator/_generator.py:156 |
| Synthetic gauge write | `save_gauges` | gauge/synthetic/generator/_core.py:168 (read:82 → `get_gauge_portfolio`) |
| Property timeseries (per-asset) | `save_property_timeseries` | property/ts/flood/process.py:226, peril/peril_ts.py:227 (read:202) |
| Portfolio flood summary | portfolio-flood-summary saver | property/ts/generator.py:168 |
| Sequence-gauge writes | `save_sequence_gauge` | stressm/pipeline/stages.py:59,94,118 |
| Classifier training summary | `save_classifier_training_summary` | stressm/gaugets_writer.py:155, stressm/summary.py:41(read),62(write) |

## Category C — needs a new seam artifact first → **deferred to own WPs**

Not mechanical: no registered spec yet. Each is a self-contained work package
(register `artifacts.py` Spec → add `database.get_*/save_*` → swap call sites).

1. **Gauge-HD data** (`gauge_*_hd.json`, `gaugehd_{station}.json`) —
   stressm/gauge_parser.py:52, cdm/gaugehd/generator.py:216. KEYED artifact.
2. **Spatial-correlation config** — storm_multi/models/_spatial_math.py:129 (write),
   spatial_correlation.py:99 (read). Decide: port artifact vs `src/models` scope.
3. **River-polyline geometry cache** — gauge/synthetic/geometry.py:56. Decide:
   port data vs static snap-tool input.
4. **Book swap records** (`{swap_id}.json`) — book_common/_pricing.py:159. Decide:
   `trading` seam (`save_prs_trade`) vs new `book` artifact.

---

## Phased execution

- **Phase 1 — Category A reads.** Domain-grouped commits; verify after each with
  the scanner re-run + the relevant `tests/port` suites on file **and** pg backend.
- **Phase 2 — Category B writes.** Generator saves; verify round-trip. No port
  regen in a worktree — dry-run only, real regen verification by the user.
- **Phase 3 — Category C.** The four WPs above, sequenced gauge-HD first.
- **Phase 4 — cleanup + next area.** Clean the bare-path `ref` lines once
  `src/port` reads zero, then move to `app/commands` (10) and `src/reports` (10).

## Verification recipe (per commit)

1. Scanner re-run (above) — count must drop by the files touched.
2. `MKM_TEST_BACKEND=pg pytest tests/port/<area> -q` and the default (file) run.
3. Grep the touched files for residual `json.load(`/`json.dump(`.
4. Never `git push` (user pushes); never regen port data in the worktree.

## Resume box

- **Next action:** Phase 1a — `book.py`, `book_thames.py`, `book_property/_core.py`,
  `book_common/_records.py` (gaugehc / propertyhc / counterparty / property reads).
- **Pattern:** `import database; c = database.active_catchment(); data =
  database.get_<artifact>(c)`. Drop the `open()+json.load`; keep downstream `.get(...)`.
- **Gotcha:** these are *generator-side* loaders, distinct from the migrated
  live-app `src/loaders/*`. The pg backend must be populated (or file fallback
  valid) for the entry points they run under.
- **Watch:** `hc/pricing/_process.py:43` (`prop_file`) — confirm whether it's a
  property record or timeseries before choosing the getter.
