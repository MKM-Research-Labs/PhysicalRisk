# WP2.4 — Catchment context (the writer-migration gate)

> ## ▶ RESUME HERE (session pickup, 2026-06-20)
>
> **Branch:** `claude/quirky-chaplygin-a2a625` — 53 commits ahead of origin, **unpushed**
> (user pushes). Working tree clean. The migration work is NOT on `main`. Worktrees have
> been ephemeral this project — the branch is currently checked out directly in the main
> repo (`/Users/newdavid/Documents/PhysicalRisk`); if you land on `main` or in a fresh
> worktree, `git checkout claude/quirky-chaplygin-a2a625` first.
>
> **Environment:** always activate the venv first:
> `source /Users/newdavid/Documents/PhysicalRisk/.venv/bin/activate`
> (a fresh shell otherwise defaults to system Python 3.9 and conftest import errors).
> Coverage on a port submodule trips the same `tests/helpers` vs `src/visual/layer/helpers.py`
> sys.path collision that `--cov=database.context` does — drive it with `coverage run -m
> pytest … && coverage report --include="…"` (uses pyproject's `source`, no pytest-cov early
> import) rather than `pytest --cov=<submodule>`. **No port runs / mutating audits in a
> worktree** — code + tests here, real regeneration in the main checkout.
>
> **Done (steps of the §5 plan):**
> - §4 decisions locked: retire `config.catchment_id` *setter*; convert port generators
>   **and** trading engines in one pass. [`c0939c69`]
> - Design + plan correction (step 3 deferred into step 6). [`93d5f21a`, `d694d27f`]
> - **Step 1** — `src/database/context.py`: `active_catchment()` + `catchment_context()`
>   (ContextVar; falls back to `config.catchment_id`). db pkg 100%. [`36d84617`]
> - **Step 2** — `tests/conftest/db_helpers.py` (import as `from db_helpers import …`):
>   `tmp_catchment(tmp_path)` / `memory_catchment()`. [`8a82730c`]
> - **Step 4 PREP** — write-guard: autouse test backend refuses `save`/`delete` that
>   resolve under the real `data/input` tree. [`7df143de`]
> - **Step 4 — ALL 6 portfolio writers DONE.** gauge [`8c254871`], property [`e5284e1c`],
>   loan/mortgage [`cc0ca95e`], commercial [`ae4834a4`], commercial_loan [`e5ae89c1`],
>   counterparty [`e82fbb55`]. Every writer now `…(catchment=…)` defaulting to
>   `active_catchment()`; internal sibling reads → `database.get_*(self.catchment)`; writes
>   → `database.save_*`; result returns `"catchment"` not `"file_path"`; the `portfolios.py`
>   /`trading.py` callers drop the positional `ctx.output_dir`. Tests use **per-module**
>   autouse `tmp_catchment` (NOT package-wide where a conftest is shared with unmigrated
>   ts/hc generators); read-backs via `database.get_*_portfolio`; save-error tests patch
>   `database.save_*`. Added getters `get_commercial_loan_portfolio` + `get_counterparty_portfolio`.
>   **Established pattern** (apply to every remaining generator/engine): ctor
>   `output_dir`→`catchment`; reads→`database.get_*`; write→`database.save_*`; drop the
>   directory arg AND any `property_portfolio_path`/`commercial_path` override; return
>   `"catchment"`. Full port suite **2873✓/2skip**; db pkg + every changed module **100%**.
>   Two pre-existing R2 nits flagged (locations.py 304 lines — spawned task).
>
> **Step 5 PROGRESS — gauge timeseries DONE** [`dd52b553`]. `GaugeTimeSeriesGenerator(catchment=…)`;
> gauge read → `get_gauge_portfolio`; per-gauge write → `save_gauge_timeseries`; stale-cleanup →
> `iter_gauge_timeseries_ids` + NEW `delete_gauge_timeseries`. **KEY TEST PATTERN for ts/hd:**
> keyed writes still land physically at `tmp_path/<dir>/<key>.json` under `tmp_catchment`, so
> existing glob read-backs keep working; the generator now NEEDS a gauge portfolio, so the autouse
> fixture both binds `tmp_catchment(tmp_path)` AND seeds one via `GaugePortfolioGenerator(verbose=
> False).generate(count=5)`. Both changed modules 100%.
>
> **Step 5 PROGRESS — gauge timeseries [`dd52b553`] + gaugehd [`502b3349`] DONE.** gaugehd:
> added `delete_gauge_history`; `loader.load_gauge_portfolio`/`synthetic.generate_from_gauge_
> portfolio`/`nrfa.generate_from_nrfa`/`runner.generate_all_gauge_histories`+`process_nrfa_
> directory`/`generator.py` wrapper all on the seam; NRFA csv read stays (external source);
> `runner.py:125` setter left for step 6. The shared `setup_gauge_env` test helper now seeds
> via `database.save_gauges` (callers dropped `monkeypatch`). Every changed module 100%. Also
> resolved the R2 locations.py nit [`181452ad`] — split `_zones.py` out, locations.py now 276 lines.
>
> **Step 5 PROGRESS — hazard DONE** [`bfcb3165`]. `build_hazard_curves(catchment_id)`; reads
> storm_sequences + gauge via `database.get_*`; `save_hazard_curves`→`save_gauge_hazard_curves`;
> `save_gauge_storm_responses` does the keyed `gauge_timeseries` read-modify-write merge
> (`get_gauge_timeseries`→add storm_responses→`save_gauge_timeseries`); `_load.py` loaders now take
> the parsed dict. **Legacy `load_storms` left path-based** (reads legacy storms.json, no production
> caller — deferred legacy-reader decision). All 3 modules 100%. **TEST TRICK confirmed:** under
> `tmp_catchment` the dir-resolver maps EVERY catchment to `tmp_path`, so a test can seed via
> `database.save_*("any", …)` and physical-path assertions (`tmp_path/gaugehc.json`) still hold.
>
> **Step 5 PROGRESS — storm_multi sequences DONE** [`753ee1f2`]. `save_sequences`/`load_sequences`/
> `save_summary` now `(catchment=None→active_catchment())` via `database.save_storm_sequences`/
> `get_storm_sequences`/`save_sequence_summary`. **DECISION resolved:** added `sequence_summary`
> DOCUMENT artifact (`SEQUENCES_SUMMARY_FILE`) + saver/getter. Callers: stressm `_core.py`,
> training route, `batch_train` (pre-checks `storm_sequences_exists`). **`save_spatial_correlation_config`
> left deferred** (no production caller). serialization.py + storms.py 100%. Broad checkpoint
> (port+routes/trading+db+hazard) **3282✓/2skip**. Also fixed a gaugets-slice regression in the
> stressm integration tests (conftest binds `tmp_catchment` for `generate_stressm`) [earlier commits].
>
> **Step 5 PROGRESS — trading engines DONE → STEP 5 COMPLETE.**
> `TradeMarks`/`PnLEngine`/`MarketStateManager` all `ctor(catchment)`; trade marks + market state +
> keyed EOD snapshots via `database`; dropped the dead `prs_dir` arg; EOD-report PDF checks use
> `config.get_eod_dir()` (PDFs stay file-based). **`MarketStateManager._load_base_curves` now also
> handles the `{hazard_curves: {...}}` production format** (the hazard slice's output). Also migrated
> the **historical_eod** consumer (`_series`/`_history`, test-only/dormant): EOD cleanup via new
> `clear_eod_snapshots`; per-day state via `save_market_state`; the two history reports became
> `hazard_curve_history` / `trade_pnl_history` **DOCUMENT artifacts** (new `get/save_*` +
> `delete_eod_snapshot`). Routes (`_helpers`, `prs/blueprint`) drop directory args. db pkg + every
> changed module **100%**; port+routes/trading+models+db **3330✓/2skip**.
>
> **Step 6 — setter removal DONE.** The public `config.catchment_id` **setter is deleted**
> (assignment now raises `AttributeError`); replaced by the scoped **`config.use_catchment(c)`**
> context manager (sets `_catchment_id` + `_init_paths`, **restores on exit**) backed by the
> internal `_set_catchment`. **Design note (safer than the original plan):** `database.catchment_context`
> was left UNTOUCHED — enhancing it would have repointed config paths inside every `tmp_catchment`
> test (it composes `catchment_context`), destabilising the whole step-4/5 suite. Instead: the file
> backend already resolves any catchment to `input_root/<catchment>` purely (config_binding.py:44),
> and production data I/O uses the `active_catchment()→config.catchment_id` fallback — so a scoped
> `use_catchment` is sufficient (it also keeps params/currency/non-migrated readers consistent).
> 5 production sites wrap their run in `with config.use_catchment(c):` (server, book, port
> orchestrator, gaugehd runner) — `cmd_test` uses it too (env var still propagates to subprocesses);
> `server.py:46` comment updated. Tests: `test_catchment_isolation.py` rewritten for scoped/nested
> `use_catchment`; commercial-report fixtures → `use_catchment`; `cdm_all.py` → `_set_catchment`
> (keeps ValueError); `test_gaugehd_runner_part2.py` rewritten for the now-scoped main() (spy proves
> catchment active *during* the run, restored after). catch.py changed lines 100%. **Regression caught
> + fixed:** ~52 errors from `monkeypatch.setattr(config, "catchment_id", …)` sites (a syntax the
> `\.catchment_id =` grep missed — monkeypatch's set + teardown both hit the deleted setter); all
> repointed to `"_catchment_id"` (the private attr, thames==default). Final broad checkpoint (catch+
> config+commands+port+routes+models+reports+db) **8387✓**, only the 17 documented pre-existing reds.
>
> **Step 7 — data-access audit DONE → WP2.4 §5 PLAN COMPLETE.** New
> `docs/models/full_audit/sections_tests/data_access.py` (sibling to path_definitions, §4.4) +
> `tests/commands/test_data_access_report.py` (24 tests, 100% cov). **Per user decision:** the
> **DB-access ban is the zero-tolerance gate** (raw SQL / `.execute(` / sqlalchemy·psycopg·asyncpg
> imports / `create_engine`·`sessionmaker`·`.cursor(` outside `src/database`) — **green by
> construction** (0 findings; no Postgres yet) and stays green as WP1.6 lands the backend in its
> private modules. The **direct-file-I/O-against-data backlog is a tracked REPORT, not a gate**
> (~60 files outside `src/database` still read/write the tree directly — the un-migrated generators;
> shrinks as later WPs migrate them). Wired into `full_audit` §4.4 + `sections_tests/__init__` +
> `full_audit/__init__`; renders in the consolidated report. Commands/audit suite green (only the
> pre-existing path-defs gate red).
>
> **Pre-existing reds (NOT ours; baseline==guard verified):** 11 `tests/routes/storm_stress`,
> 1 path-definition gate (~67-site backlog), 5 `tests/routes/lineage` prs-commit
> (`test_pprs_to_client` ×4 + `test_trade_to_blotter::test_commit_writes_to_temp_dir`) —
> a genuine latent bug: PRS commit writes via `database.save_prs_trade`→`get_input_dir()/prs`
> but those tests only monkeypatch `get_reports_dir`, so the file lands off where they
> assert (and toward real data when un-monkeypatched). Candidate to spin off separately.
>
> Full plan below; §5 is the step list.

This is the design that unblocks **WP0.5 writer migration**. The WP0.6 read path
migrated cleanly because routes always read the *active* catchment via `config`
accessors. Writers did **not**, because they are **directory-injected**, not
catchment-keyed — and the `database` save API has no "write to directory X" primitive
(none is possible for Postgres). WP2.4 closes that gap by giving the codebase a
**run-scoped catchment identity** that generators pass to `database.save_*` /
`database.get_*`, while storage resolution (file root, or Postgres) stays inside the
`database` package.

Resolving this also fixes the **global-catchment race** the migration gotchas flag:
catchment identity today is the mutable env-global `config.catchment_id`
(`config/catch.py:40`, settable property), which is unsafe under concurrent
requests/runs.

---

## 1. The problem, precisely

### 1a. Two things are tangled into one parameter
`output_dir` currently carries **two** unrelated concerns:

| Concern | Today | Where it belongs |
|---|---|---|
| **Which catchment** am I generating? | `output_dir` path (or `config.get_input_dir()`) | the *caller* (run identity) |
| **Where/how** is it stored? | `output_dir` filesystem path | inside `database` (file root vs Postgres) |

In production these collapse: the port pipeline runs **one catchment per invocation**,
so `output_dir` is always `config.get_input_dir()` for that catchment. The abstraction
mismatch only surfaces in tests, where **111 test files** inject a tmp `output_dir` to
isolate — i.e. they're really overriding *storage location*, not catchment identity.

### 1b. Writers read AND write through `output_dir`
A generator's `output_dir` is a **shared run directory**, not just a sink. Example —
`src/port/src/property/main/generator.py`:
- reads `self.output_dir / 'gauge.json'` (`:135`) — a sibling artifact from earlier in the run
- writes `self.output_dir / 'property.json'` (`:185`)

So WP2.4 must convert the **generator-internal reads** too, not just the writes in the
WP0.5 table. (These reads were *not* covered by WP0.6, which only touched route/loader
reads.) Both sides become `database.get_*(catchment)` / `database.save_*(catchment, …)`
against the same catchment.

### 1c. Construction pattern to replace
Every generator/engine looks like:
```python
self.output_dir = Path(output_dir) if output_dir else config.get_input_dir()
self.output_dir.mkdir(parents=True, exist_ok=True)
```
and convenience wrappers thread `output_dir=` down (`generate_gauges(count, output_dir)`,
`PropertyPortfolioGenerator(output_dir=…)`, engines `__init__(self, trading_dir)`).

---

## 2. Design

### 2.1 Catchment identity lives in a `ContextVar` (run/request-scoped)
Add to the `database` package a context primitive backed by `contextvars.ContextVar`
(NOT a module global, NOT the mutable `config.catchment_id`):

```python
# src/database/context.py  (re-exported from database/__init__.py)
_active: ContextVar[str | None] = ContextVar("active_catchment", default=None)

def active_catchment() -> str:
    """The catchment for the current run/request. Falls back to config's
    active catchment when no context is bound (preserves today's behaviour)."""
    cur = _active.get()
    return cur if cur is not None else config.catchment_id

@contextmanager
def catchment_context(catchment: str):
    token = _active.set(catchment)
    try:
        yield catchment
    finally:
        _active.reset(token)
```

Why `ContextVar`:
- **Race fix.** Concurrent Flask requests / parallel port runs each get their own
  catchment without clobbering a shared global — this is the WP2.4 race fix the gotchas
  earmark.
- **Backward compatible.** With no context bound, `active_catchment()` returns
  `config.catchment_id`, so existing single-catchment runs behave identically.
- **Lives in `database`** because it's the value threaded into `save_*`/`get_*`; keeping
  it there avoids a `config` ⇄ `database` import cycle (database already imports config).

### 2.2 Generators take a `catchment`, drop `output_dir`
```python
# before
def __init__(self, output_dir=None, …):
    self.output_dir = Path(output_dir) if output_dir else config.get_input_dir()

# after
def __init__(self, catchment: str | None = None, …):
    self.catchment = catchment or database.active_catchment()
```
- Read:  `database.get_gauges(self.catchment)`        (was `self.output_dir / 'gauge.json'`)
- Write: `database.save_gauges(self.catchment, data)` (was write to `self.output_dir`)
- `mkdir(parents=True, exist_ok=True)` is **deleted** — directory creation is the
  `FileRepository`'s job (it already mkdirs on `save`), and is meaningless for Postgres.

Convenience wrappers (`generate_gauges`, module-level `generate(...)`) swap their
`output_dir=` parameter for `catchment=` with the same default-to-active behaviour.

### 2.3 The orchestrator binds the context once
The port entry point that runs a catchment wraps the run:
```python
with database.catchment_context(catchment):
    generate_gauges(...)        # all generators below see the same catchment
    generate_properties(...)
    ...
```
In production the bound catchment equals `config.catchment_id`, so paths resolve exactly
as today (`config_binding._resolve_catchment_dir` → `config.get_input_dir()`).

### 2.4 Tests isolate by binding storage, not by passing a directory
This is the crux of the 111-file migration and it's **already supported** — no new
primitive needed. `FileRepository` accepts a `dir_resolver` (`src/database/file_repo.py:55`):

```python
# test helper (add to tests/conftest or a database test-utils module)
@contextmanager
def tmp_catchment(tmp_path, catchment="thames"):
    repo = FileRepository(dir_resolver=lambda c: tmp_path)
    configure_backend(repo)
    with catchment_context(catchment):
        yield
    use_file_backend()   # restore prod binding (the autouse fixture also re-binds)
```

Migration per test:
```python
# before
gen = PropertyPortfolioGenerator(output_dir=str(tmp_path))
gen.generate()
assert (tmp_path / "property.json").exists()

# after
with tmp_catchment(tmp_path):
    PropertyPortfolioGenerator().generate()
assert database.get_properties("thames")          # read back through the seam
```
The autouse `_database_file_backend` fixture (`tests/conftest/fixtures_database.py`)
already re-binds the production file backend before each test, so a test that overrides
the backend doesn't leak into the next test.

> **Fixture gotcha (recurring, expect it again):** tests that staged data under
> `output/` had to be repointed to the production `input/<catchment>/…` location during
> WP0.6. With `tmp_catchment` the *resolver* points at `tmp_path`, so this disappears —
> but watch for tests that mix a tmp generator output with a real `config.get_input_dir()`
> read; those must bind **both** sides to the same resolver.

### 2.5 What stays on `output_dir` (genuinely out of scope)
The typhoon ensemble (`events_output_dir`, `windts_output_dir`) and any writer in the
WP0.5 doc's "out of scope" list (PDFs, report `.txt`, lineage manifest, audit log,
intensity stdout, visual JS config, `_admin_auth`) keep their directory parameters —
they are not port-input JSON artifacts. Don't convert them.

---

## 3. Why the rejected options stay rejected
- **"Bind FileRepository to this dir" escape hatch on the public save API** — leaks a
  file-only concept through the seam; no Postgres analogue; defeats the whole point.
  (We *do* use `dir_resolver`, but only in **test setup**, never in production call sites.)
- **Reverse-map `output_dir` → catchment at each writer** — fragile string parsing of a
  path back into an identity we already have at the caller.

---

## 4. Locked decisions (user, 2026-06-19)

### 4a. Retire the `config.catchment_id` **setter**
`active_catchment()` becomes the single source of truth for "which catchment is this
run". The mutable setter (`config/catch.py`) is the race source and is **removed**.
Blast radius is small (verified):
- **Live app does NOT use it.** `src/routes/catchment.py` only *validates* the requested
  catchment and redirects; it never assigns `config.catchment_id`. The active catchment
  is fixed at process start via `MKM_CATCHMENT`. No change needed there.
- **One real production setter site:** `src/port/src/gauge/gaugehd/runner.py:125`
  (`config.catchment_id = args.catchment`, a CLI entry) → becomes
  `with database.catchment_context(args.catchment): …`.
- **Tests:** a few setter uses in `tests/reports/commercial/*` + the setter's own test in
  `tests/catch/*` → migrate to `catchment_context` / delete the setter test.

The **getter** `config.catchment_id` stays (read-only) as the no-context fallback inside
`active_catchment()`. Sequence: add the context primitive (step 1) and migrate all
setter call sites first, then delete the setter in the **orchestrator step (step 6)** so
nothing is left calling it. Drop the `@catchment_id.setter` and the `config/server.py:46`
warning comment that only exists because of it.

### 4b. Scope = port generators **and** trading engines in the same pass
Both share the directory-injection pattern (`output_dir` / `trading_dir`), so they're
converted together to avoid a second sweep. The trading engines
(`models/trading/trade_marks.py`, `market_state/_persistence.py`, `pnl_engine/_pnl.py` —
constructed as `__init__(self, trading_dir)`) get the same treatment: drop the dir
parameter, take `catchment`, read/write via `database`, and run inside
`catchment_context`. They fold into **step 5** below alongside the book-pricing → `prs`
writers.

---

## 5. Sequenced plan (updated for the §4 decisions)

Each step: behaviour-preserving · per-file commit · ≥99% coverage for touched files ·
`database` package stays 100% · **0 new path-audit findings**.

1. **Context primitive** — `src/database/context.py` (`active_catchment`,
   `catchment_context`), re-exported from `__init__.py` (pure re-export, rule 4). Unit
   tests: default-falls-to-config, nesting, reset-on-exit, concurrent isolation. *Lands
   standalone, no caller changes — like the serialization prep did.*
2. **Test helper** — `tmp_catchment(tmp_path)` (+ `InMemoryRepository` variant for
   pure-unit writers). Self-tested.
3. **~~Migrate setter call sites~~ — DEFERRED into step 6** (correction, 2026-06-19).
   The original plan was to swap `config.catchment_id = x` sites to `catchment_context`
   here. Investigation showed this is **unsafe and unnecessary before the writers
   migrate**:
   - **Unsafe:** the `config.catchment_id` setter calls `_init_paths(x)`, which re-caches
     `self.input_dir = data/input/<x>` and every derived dir (gaugehd, gaugets, blotter,
     classifiers, prs, stressm). `catchment_context` does **not** repoint any config path.
     The port orchestrator (`app/commands/port/orchestrator.py:199`) does
     `config.catchment_id = c; output_dir = config.get_input_dir()` and threads that into
     the still-unmigrated generators; the gaugehd runner reads `config.get_gaugehd_dir()`.
     The commercial-report tests set the catchment so the (out-of-DB-scope) report code
     resolves the right paths. Swapping any of these to `catchment_context` alone breaks
     path resolution.
   - **Unnecessary:** a writer migrated to `save_*(active_catchment(), …)` already works
     in production **with the setter in place** — `active_catchment()` falls back to
     `config.catchment_id` (which the orchestrator still sets), and `save_*` resolves
     through `config.get_input_dir()` (the repointed path; honours
     `MKM_CATCHMENT_INPUT_OVERRIDE` too). So writers don't need the setter gone.

   → Setter retirement therefore belongs in **step 6**, together with the orchestrator
   wrap and the config-path/context unification (the orchestrator's
   `with catchment_context(c):` must *also* repoint config paths so the out-of-scope
   report/PDF consumers keep following the active catchment). Full production setter
   sites to handle in step 6: `app/commands/{server,book,port/orchestrator}.py`,
   `app/commands/test/command.py`, `src/port/src/gauge/gaugehd/runner.py`; plus tests
   `tests/catch/test_catchment_isolation.py` (tests the setter itself — rewrite/retire),
   `tests/reports/commercial/test_commercial_report_part{1,2,3}.py`,
   `tests/port/cdm/cdm_all.py`, `tests/port/gauge/test_gaugehd_runner_part2.py`.
4. **Portfolio entities** (WP0.5 Batch 1: gauge, property, loan, commercial,
   commercial_loan, counterparty) — **← NEXT.** Convert constructor + internal reads +
   writes; repoint tests via `tmp_catchment`. Lowest risk, all map to existing savers.
   In production the setter (still present) keeps `active_catchment()`'s fallback correct,
   so no orchestrator change is needed yet.
5. **Hazard / timeseries / storms / book-pricing / gaugehd+typhoon / trading engines** —
   WP0.5 Batches 2–6 **plus the trading engines (§5b)**, each folded with its
   directory→context conversion. Resolve the WP0.5 open decisions (legacy
   seq_gauge/storm writers, `training_summary` dir reconcile, storm-multi port-vs-model,
   typhoon granularity) as each batch is reached.
6. **Orchestrator + setter removal** — wrap the port run(s) and trading run(s) in
   `catchment_context(catchment)`; delete dead `output_dir`/`trading_dir` threading and
   `mkdir` calls; **delete the `config.catchment_id` setter** and its `server.py:46`
   warning comment now that nothing assigns it.
7. **Task 0.8 audits** — sanction `src/database` in the path-audit; build the
   "no SQL/file-I/O outside `database`" gate. With writers migrated, it goes
   green-by-construction.

After WP2.4 + the folded WP0.5, **all** port-artifact file I/O (read and write) is behind
`database`, clearing the way for the `PostgresRepository` swap (WP1.6).
