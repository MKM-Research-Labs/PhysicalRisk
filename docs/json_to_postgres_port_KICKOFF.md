# KICKOFF — `src/port` JSON → Postgres migration (resume here)

**This is the single entry point for resuming the work.** Detailed rationale and
the full per-file triage live in [`json_to_postgres_port_migration.md`](json_to_postgres_port_migration.md);
the wider programme context is in [`json_to_postgres_migration.md`](json_to_postgres_migration.md).

---

## 1. Where we are

Goal: no first-party module loads/creates/updates a `.json` on disk — all such
state lives in PostgreSQL behind the `src/database` seam. Tracked by the
zero-tolerance audit (`docs.models.full_audit.sections_tests.json_files`,
non-gating until the backlog hits zero).

| Scope | Programme start | **Now** |
|---|---|---|
| **`src/port` files** | 26 | **17** |
| **`src/port` reads** | 41 | **19** |
| **`src/port` writes** | 14 | **12** |

**2026-06-27 — Tier 1 (property/commercial hazard-curve I/O) DONE.** Migrated the
HC generator write (`_generator.py`) + the spread-decomposition read/write
(`_decomposition.py`, 9 scenario-mode reads + 1 write) together (writer+reader of
the same artifact → no pg split-brain). Added `AssetTypeConfig.get_hazard_curves`/
`save_hazard_curves` seam accessors (property/commercial dispatch; local `normal`
mode → seam `flood`). 794 tests green. Scanner 19→17 files, 28→19 reads, 14→12 writes.
**⚠️ Gotcha:** broad test runs trigger the self-healing copyright audit which
mutates ~62 unrelated files' headers — stage explicit paths, never `git add -A`.

**Done (committed, green, ruff-clean):** the whole `src/book` area (gauge +
property books), `storm_typhoon_pairing.py`, and the stressm pipeline **reads**.
All **reads**; **no writes migrated yet** — see §4 for why.

Commit range for this work: `255a7ddb..HEAD` on the working branch (10 commits).

---

## 2. The proven recipe (copy this)

**Read swap** — `open()+json.load` → seam getter, keyed on the catchment:

```python
import database
cat = database.active_catchment()          # or an existing catchment_id param
data = database.get_gauge_portfolio(cat)    # returns the SAME dict json.load gave
curves = (data or {}).get('hazard_curves', {})   # guard None (absent → None)
```

**Test migration** — stop writing fixture JSON, seed the seam instead:

```python
from db_helpers import tmp_catchment   # tests/conftest/db_helpers.py
import database

@pytest.fixture
def seam_tmp(tmp_path):
    with tmp_catchment(tmp_path, "thames"):   # file backend by default; pg under MKM_TEST_BACKEND=pg
        yield

def test_x(seam_tmp):
    database.save_gauge_hazard_curves("thames", {"hazard_curves": {...}})
    ...   # call the generator with no path args
```

For a corrupt-record case, **monkeypatch the seam getter** to raise `ValueError`
(backend-agnostic) rather than writing a bad file.

---

## 3. Invariants that make this safe (verified, don't re-derive)

- **Shape parity:** `FileRepository.load` returns `json.loads(p.read_text())` —
  the seam getter returns exactly what `json.load(file)` returned. Downstream
  `.get(...)` access is unchanged.
- **Catchment resolves to the same dir:** the file backend's
  `config_binding._resolve_catchment_dir` maps `active_catchment()` →
  `config.get_input_dir()`, **including the e2e `MKM_CATCHMENT_INPUT_OVERRIDE`**.
  So `input_dir`-threaded code can switch to `get_*(active_catchment())` and read
  the same place.
- **Seam API:** `src/database/__init__.py` — portfolios, hazard curves
  (`mode=` for peril variants), timeseries, storm sequences, sequence_gauge,
  typhoon_event, **gauge_history** (= the `gaugehd` files), classifiers, etc.
- **Backend binding:** `app.py port` calls `configure_backend`; per-call code
  just uses `database.*`. Under the file backend the swap is behaviourally a
  no-op; under `MKM_REPO_BACKEND=pg` it serves from Postgres.

---

## 4. Remaining `src/port` work — prioritized

### Tier 1 — clean reads + writes (do first; mechanical, seam exists)

| File | r/w | Seam fn | Notes |
|---|---|---|---|
| ~~`property/hc/generator/_decomposition.py`~~ | ~~9r 1w~~ | — | **DONE 2026-06-27** (via `AssetTypeConfig.get/save_hazard_curves`). |
| ~~`property/hc/generator/_generator.py`~~ | ~~1w~~ | — | **DONE 2026-06-27**. |
| `property/hc/loader.py` | 3r | `cfg.get_hazard_curves`, `get_storm_sequences`, `get_sequence_gauge` | generator-side loader — **next**; reuse the new AssetTypeConfig accessor |
| `property/hc/pricing/_process.py` | 1r | (confirm: property record vs timeseries) | check before swapping |
| `gauge/synthetic/generator/_core.py` | 1r 1w | `get_gauge_portfolio` / `save_gauges` | read+write pair |
| `cdm/gaugehd/generator.py` | 1w | `save_gauge_history` | gaugehd writer (key = station id) |
| `property/ts/flood/process.py` | 1w | `save_property_timeseries` | per-asset |
| `property/ts/generator.py` | 1w | portfolio-flood-summary | |
| `peril/peril_ts.py` | 1r 1w | `get/save_property_timeseries` | per-asset peril ts |

### Tier 2 — `input_dir`/`output_dir`-threaded (Phase-1c style; thread catchment, verify override path)

| File | r/w | Notes |
|---|---|---|
| `property/ts/loader.py` | 5r | sequences / property portfolio / gauge.json / `GAUGE-*` glob (gauge timeseries) |
| `_typhoon_join.py` | 3r | `load_*(output_dir)` consumed by the **output_dir-based peril pipeline** (`peril_ts`, `_wind`); migrate with that pipeline, same recipe as stressm reads |

### Tier 3 — BLOCKED on a design decision (not mechanical; decide first)

- **`stressm/pipeline/stages.py` (3w) — `sequence_gauge` writes.** Uses
  `rmtree`+`mkdir`+per-file `stat()` size reporting+`iterdir`+legacy `unlink`.
  The seam has **no bulk-clear** for `sequence_gauge`. **Decision needed:** add a
  `clear-collection` seam capability, or redesign the cleanup/size reporting.
- **`stressm/gaugets_writer.py` (1w) + `stressm/summary.py` (1r 1w) —
  `training_summary.json`.** There are **two distinct files**:
  `stressm/training_summary.json` (batch_train; **no seam artifact**) and
  `classifiers/training_summary.json` (gaugets_writer + the `src/routes`
  trading-stress flow; **has** the `classifier_training_summary` artifact).
  `update_training_summary` is **shared with `src/routes`**. **Decision needed:**
  new artifact for the stressm-dir file, or consolidate the two; expect to widen
  scope into `src/routes`.
- **`_stress_storms_stages.py` (1r) — deliberate dual-path.** `scan_gauge_responses`
  already falls back to the seam; the `glob("GAUGE-*.json")` is a file-backend
  fast path with **different corrupt-tolerance + raise semantics**. Collapsing to
  seam-only is a **behaviour change** — own decision + test review.

### Tier 4 — Category C (new artifact) / dead code

- `storm_multi/models/_spatial_math.py` (1w) + `spatial_correlation.py:99` (1r) —
  spatial-correlation **config** artifact (none registered). Small; could live in
  `src/models` scope instead.
- `spatial_correlation.py:278` `from_gauge_portfolio_file` (1r) — **no production
  callers** (grep-confirmed); likely just delete.
- `gauge/synthetic/geometry.py` (1r) — river-polyline geometry **cache**; decide
  port-data vs static snap-tool input.
- `book_common/_pricing.py` (1w) — generated **book swap records** (`{swap_id}.json`);
  decide `trading` seam (`save_prs_trade`) vs a new `book` artifact.

**Suggested order next session:** `_decomposition.py` (Tier 1, biggest win) →
the rest of Tier 1 → Tier 2 → then take ONE Tier-3 design decision (recommend the
`sequence_gauge` clear-collection capability, it unblocks 3 writes).

---

## 5. Verify after every change

```bash
# scanner re-run (must drop by the files/reads you touched)
PYTHONPATH=. .venv/bin/python -c "from docs.models.full_audit.sections_tests.json_files import scan_repo; \
s=scan_repo('.'); io=[f for f in s['findings'] if f['file'].startswith('src/port') and f['kind'] in ('read','write')]; \
print(len({f['file'] for f in io}),'files', sum(f['kind']=='read' for f in io),'read', sum(f['kind']=='write' for f in io),'write')"

# tests (file backend) + ruff (CI-gated on src/ and tests/)
.venv/bin/python -m pytest tests/port/<area> -q
.venv/bin/ruff check <changed files> --select E,F,W,I          # must be <= HEAD
.venv/bin/ruff check --fix --select I001 <changed files>       # safe import-order fix
```

Rules: commit per slice (don't push — the user pushes); **never regen port data
in a worktree**; the user runs the e2e suite themselves.

---

## 6. Gotchas learned this session

- The whole-codebase audit measures far more than the live-app migration covered;
  the live read path (`src/loaders/*`) was already done — this work is the
  generate/report/tooling side.
- Many generators are **`output_dir`-parameterised, not catchment-keyed** — that's
  the main reason these aren't one-line swaps. The §3 resolver invariant is what
  makes the switch safe.
- `replace_all` with a leading-newline-trimmed pattern drops indentation / eats
  the trailing space (`out_dir,catchment` → E231); prefer rewriting the call or
  fix spacing after.
- Pre-existing ruff noise (header `W291`, some `F401`/`F541`/`I001` in untouched
  files) exists repo-wide; only ensure your changed files are **≤ HEAD**.
- Tests often have an **autouse fixture that seeds a portfolio** (e.g.
  `tests/port/storm/stressm/conftest.py`); "no data" tests must **override** it
  (`save_*` an empty/bad payload), not rely on file absence.
