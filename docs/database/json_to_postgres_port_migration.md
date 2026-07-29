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
  green on the file backend; ruff-neutral.
- **2026-06-26 — Phase 1b (property book).** `book_property/_core.py` reads
  property hazard curves (default + `bri` mode) and the property portfolio via
  the seam; retired all four `*_path` params (counterparty_path was already
  dead); replaced the `propertybri_path` opt-in with `include_resilient: bool`.
  Caller + property coverage part2/part3 migrated (autouse `tmp_catchment`
  backend, seed the `bri` mode for resilient tests). 106 tests green.
  **The whole `src/book` area is now off loose JSON.**

  Scanner so far: **26 → 22 I/O files, 41 → 34 reads** (writes still 14).

- **2026-06-26 — Phase 1b (storm↔typhoon pairing).** `storm_typhoon_pairing.py`
  reads typhoon damage events + storm sequences via the seam
  (`iter_typhoon_event_ids`/`get_typhoon_event`, `get_storm_sequences`), keyed on
  `database.active_catchment()`. Public API unchanged → route callers untouched.
  Tests seed the seam; corrupt cases re-expressed via monkeypatching the getter.
  16 tests green.

  Scanner so far: **26 → 21 I/O files, 41 → 31 reads** (writes still 14).

### Triage of the remaining Phase 1b readers (2026-06-26)

The clean, standalone reads (config-keyed or singleton — the book area and the
storm↔typhoon pairing) are **done**. The remaining ~9 reads are **not** simple
swaps; they fall into three groups, each needing a deliberate approach rather
than a one-line getter substitution:

1. **`input_dir`-threaded generator internals** — `stressm/summary.py`
   (`load_gauge_training_context(input_dir)`), `stressm/pipeline/orchestrator/
   _core.py`, `stressm/gauge_parser.py` (`_load_gaugehd_baselines(gaugehd_dir)`),
   `_typhoon_join.py` (`load_*(output_dir)`). These take a **directory parameter**
   threaded from the orchestrator (`ctx.output_dir`), not a catchment. Migrating
   means switching the read to `database.get_*(active_catchment())` and trusting
   that `input_dir` always corresponds to the active catchment (incl. the e2e
   `MKM_CATCHMENT_INPUT_OVERRIDE` path). Best done as **one coherent
   catchment-threading change across the stressm + peril pipelines**, alongside
   their write-side (Phase 2), not piecemeal. `gauge_*_hd.json` → `gauge_history`
   seam; `gauge.json` → `get_gauge_portfolio`; `storm_sequences` → already have it.

2. **Intentional dual-path (backend-aware)** — `_stress_storms_stages.py`
   `scan_gauge_responses(gaugets_dir)` **already** falls back to the seam; the
   `glob("GAUGE-*.json")` is a deliberate file-backend fast path with *different*
   corrupt-tolerance + raise semantics than the seam path. Collapsing to
   seam-only is desirable but is a **behaviour change** (corrupt files raise
   instead of being skipped), so it needs its own decision + test review.

3. **Dead / test-only classmethods** — `spatial_correlation.py`
   `from_gauge_portfolio_file(path)` and `SpatialCorrelationParams.load(path)`
   have **no production callers** (grep-confirmed). Low value; the `.load` one
   reads the spatial-correlation **config** (Category C, deferred). Likely just
   delete or leave until the Category-C spatial-config WP.

**Recommendation:** treat group 1 as a dedicated sub-phase (**Phase 1c —
pipeline catchment threading**) done with the Phase 2 writes for the same
modules, so each pipeline flips read+write together and the e2e override path is
verified once. Groups 2 and 3 are small, isolated decisions.

### Phase 1c progress — stressm pipeline reads (2026-06-26)

Verified the seam's file backend resolves `active_catchment()` →
`config.get_input_dir()` (e2e override included) via
`config_binding._resolve_catchment_dir`, so catchment-keyed reads hit the same
dir as the old `input_dir`-based reads. Migrated the stressm **reads**:
`gauge_parser._load_gaugehd_baselines` → `gauge_history` seam;
`summary.load_gauge_training_context` + `orchestrator/_core.generate_stressm`
gauge.json → `get_gauge_portfolio`, gaugehd → the seam. 131 stressm tests green.

**Stressm writes — deferred, with reasons (these are real design decisions, not
mechanical swaps):**

- **`training_summary.json` is two distinct files.** `batch_train` writes
  `<catchment>/stressm/training_summary.json` (via
  `summary.update_training_summary(stressm_dir)`); `gaugets_writer` + the
  `src/routes` trading-stress flow write `<catchment>/classifiers/training_summary
  .json`. Only the **classifiers** one has a seam artifact
  (`classifier_training_summary`). Migrating needs either a **new seam artifact**
  for the stressm-dir file, or a decision to consolidate the two. Also note
  `update_training_summary` is **shared with `src/routes`** — migrating it widens
  scope into the routes layer.
- **`sequence_gauge` writes are filesystem-coupled.** `stages.write_split_output`
  does `rmtree` + `mkdir` + per-file `stat()` size reporting + `iterdir` +
  legacy-file `unlink` — none of which the seam exposes, and there is **no
  bulk-clear** for the `sequence_gauge` artifact. Needs a seam capability
  (clear-collection) or a redesign of the size/cleanup reporting before the
  `save_sequence_gauge` swap is safe.

Remaining stressm read `summary.py:41` is the `training_summary` read **inside**
`update_training_summary`, i.e. part of that deferred write-side — left until the
training_summary decision above.

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

The backend is bound once at the entry point (`phys.py port` →
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
