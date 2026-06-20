# WP2.4 — Catchment context (the writer-migration gate)

> ## ▶ RESUME HERE (session pickup, 2026-06-20)
>
> **Branch:** `claude/quirky-chaplygin-a2a625` — 29 commits ahead of origin, **unpushed**
> (user pushes). Working tree clean. The migration work is NOT on `main`; this branch is
> currently checked out in the worktree at `.claude/worktrees/heuristic-margulis-61da49`
> (the older `elastic-wozniak-*` worktree is gone — switch whichever worktree you land in
> onto `quirky-chaplygin`).
>
> **Environment:** worktrees have no `.venv` — use the main repo's interpreter and
> always activate it first: `source /Users/newdavid/Documents/PhysicalRisk/.venv/bin/activate`
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
> - **Step 4 — gauge writer (1st of 6 portfolio generators) DONE.** [`8c254871`]
>   `GaugePortfolioGenerator(catchment=…)` defaulting to `active_catchment()`;
>   `_gauge_generate` writes via `database.save_gauges(self.catchment, output_data)`
>   (byte-identical — `database._serialize.dumps` == `indent=2` + datetime/numpy default);
>   result returns `"catchment"` not `"file_path"`; caller `portfolios.py:37` drops the
>   positional `ctx.output_dir`. Tests wrapped in `tmp_catchment`. Full port suite
>   2800✓/2skip, db 71✓, both changed modules 100%.
> - **Step 4 — property writer (2nd generator) DONE.** [`e5284e1c`] The §1b
>   read-AND-write case: both internal gauge reads converted — `generator.py`'s
>   ReferenceGauges read AND `locations.py:_load_synthetic_gauges` →
>   `database.get_gauge_portfolio(self.catchment)` (best-effort); write →
>   `database.save_properties`. Tests use **per-module** autouse `tmp_catchment` (NOT a
>   package-wide conftest fixture — propertyts/propertyhc tests share that conftest and
>   use a different, unmigrated generator). Full port suite 2871✓/2skip; generator.py
>   100%, locations.py 99% (lone miss = pre-existing unreachable `_zone_from_offset`
>   fallback). **R2 nit:** `locations.py` is 304 lines (was 309; net −5) — pre-existing
>   >300 backlog item, [[refactor_300_line_initiative]]; split `_zone_*` helpers into a
>   `_zones.py` when convenient.
>
> **NEXT — step 4 continued, the loan/mortgage writer (3rd generator).**
> `src/port/src/mortgage/` — `MortgagePortfolioGenerator(output_dir=…, …)` takes
> `property_portfolio_path=` and reads `property.json` to size the book, then writes
> `loan.json`. Convert: ctor `output_dir`→`catchment`; the property read →
> `database.get_property_portfolio(self.catchment)` (drop the `property_portfolio_path`
> arg, or keep it as an override — check call sites incl. `portfolios.py:run_mortgages`
> and `tests/port/mortgage/mortgage_generator.py`'s `property_portfolio_in_tmp`, which
> already writes property via `tmp_catchment` and hands over a path); write →
> `database.save_loans(self.catchment, …)`; return `catchment`. Mirror the gauge/property
> test pattern (per-module autouse `tmp_catchment`, read back via
> `database.get_loan_portfolio`). NOTE the loan artifact key is `"loan"` / `loan.json`
> (the mortgage→loan rename, [[mortgage_loan_rename_stage5]]).
>
> Then commercial, commercial_loan, counterparty (rest of step 4). Then step 5
> (hazard/ts/storms/book-pricing/gaugehd/typhoon/trading engines), step 6 (orchestrator
> wrap + setter removal + config/context unification), step 7 (audits).
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
