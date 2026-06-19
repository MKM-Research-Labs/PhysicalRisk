# `database` — the single data-access utility

**The one rule:** every read or write of catchment data goes through a function in this
package. No other module in the codebase contains SQL, a connection, a file path, a
`json.load`, or a `glob`. This package is the *only* place that knows whether the data
lives in JSON files or PostgreSQL — so the database can be migrated without touching a
single caller. (See `docs/json_to_postgres_migration.md`; enforced by the data-access
audit, task 0.8.)

```python
from database import get_property, commit_prs_trade, list_stress_storms

prop = get_property("thames", "PROP-002")          # "give me this property"
commit_prs_trade("thames", trade)                  # "book this trade"
```

There is **no** `execute_sql()` / `raw_query()` — deliberately. If you need data the
functions below don't expose, add a named function here; never reach around the package.

---

## Package layout & coding rules

This package follows the four project coding rules:

1. **All parameters in `config`.** Every filename, directory, scenario-mode suffix and
   id-field list lives in `config/data_layout.py`. This package hardcodes nothing.
2. **No file > 300 lines** — split by concern (each module below is < 130 lines).
3. **≥99% test coverage**, verified each stage (`pytest tests/database --cov=database`;
   currently 100%).
4. **No functions in `__init__.py`** — it is pure re-exports + `__all__`.

```
src/database/
  __init__.py     re-exports only (rule 4)
  base.py         Repository ABC (the contract)
  backend.py      configure_backend / active_backend  (the migration switch)
  artifacts.py    registry — built from config.data_layout, structure only
  file_repo.py    FileRepository      (today's JSON tree; only place json/glob lives)
  memory_repo.py  InMemoryRepository  (PostgreSQL stand-in for tests/demo)
  _helpers.py     private shared helpers (load_or / records / matches / find_record)
  meta.py portfolio.py hazard.py timeseries.py storms.py trading.py classifiers.py
                  the public functions, grouped by domain
  pg_repo.py      PostgresRepository (WP1; SQL confined to its private _engine/_queries)
```

---

## Conventions

- **`catchment`** (e.g. `"thames"`) is the first argument of every data function.
- **`get_*`** → one record (`dict`) or `None`. **`list_*`** → `list[dict]`.
  **`iter_*_ids`** → `Iterator[str]` (streams keys, never loads everything).
- **`save_*`** → bulk replace (used by the port generators). **`upsert_*`** → one record.
  **`delete_*`** → remove one.
- **`mode`** selects a scenario variant for hazard curves / timeseries. Allowed:
  `"flood"` (default), `"shd"`, `"she"`, `"bri"`, `"win"`, `"faw"`, `"fow"`, `"bow"`, `"baw"`.
- Returns are plain Python (`dict`/`list`/`bytes`/dataclass) — never an ORM row or cursor.
- Missing record → `None` (gets) or `[]` (lists); never a raw DB exception leaking out.
- Mutating functions carry a permission gate, shown as `→ @require("FuncNNN", "<cap>")`.

---

## 1. Lifecycle & meta

```python
configure_backend(repo)                  # called ONCE at startup — THE migration switch
active_catchment() -> str                # the run/request-scoped catchment (falls back to config)
catchment_context(catchment)             # `with` block binding the active catchment for writers
catchments() -> list[str]                # ["thames", "halong", "mekong"]
ping() -> bool                           # backend health check
new_port_run(catchment, meta) -> str     # start a versioned generation run, returns run_id
get_active_port_run(catchment) -> dict | None
list_port_runs(catchment) -> list[dict]
```

`active_catchment` / `catchment_context` (see `context.py`) replace the old
`output_dir` injection: a writer takes a `catchment` (defaulting to `active_catchment()`)
instead of a directory, and the orchestrator wraps a run in `with catchment_context(c):`.
Backed by a `ContextVar`, so concurrent runs/requests don't clobber each other.

## 2. Portfolio entities

```python
# Gauges
list_gauges(catchment) -> list[dict]
get_gauge(catchment, gauge_id) -> dict | None
save_gauges(catchment, gauges) -> None                      # → @require("Func001","create")

# Residential properties
list_properties(catchment, *, flood_zone=None, property_type=None) -> list[dict]
get_property(catchment, property_id) -> dict | None
save_properties(catchment, properties) -> None             # → @require("Func001","create")
upsert_property(catchment, property) -> None               # → @require("Func002","write")   (CDM edit / upload)

# Residential loans
list_loans(catchment) -> list[dict]
get_loan(catchment, loan_id) -> dict | None
save_loans(catchment, loans) -> None                       # → @require("Func001","create")

# Commercial assets
list_commercial(catchment, *, asset_type=None) -> list[dict]
get_commercial(catchment, asset_id) -> dict | None
save_commercial(catchment, assets) -> None                 # → @require("Func001","create")
upsert_commercial(catchment, asset) -> None                # → @require("Func002","write")

# Commercial loans
list_commercial_loans(catchment) -> list[dict]
get_commercial_loan(catchment, loan_id) -> dict | None
save_commercial_loans(catchment, loans) -> None            # → @require("Func001","create")

# Counterparties
list_counterparties(catchment) -> list[dict]
get_counterparty(catchment, counterparty_id) -> dict | None
save_counterparties(catchment, counterparties) -> None     # → @require("Func001","create")
```

## 3. Hazard curves

```python
# Gauge-level
get_gauge_hazard_curves(catchment) -> dict                 # whole doc {hazard_curves: {...}}
get_gauge_hazard_curve(catchment, gauge_id) -> dict | None
save_gauge_hazard_curves(catchment, payload) -> None       # → @require("Func001","create")

# Property-level (per mode)
list_property_hazard_curves(catchment, mode="flood") -> list[dict]
get_property_hazard_curve(catchment, property_id, mode="flood") -> dict | None
save_property_hazard_curves(catchment, payload, mode="flood") -> None   # → @require("Func001","create")

# Commercial-level (per mode)
list_commercial_hazard_curves(catchment, mode="flood") -> list[dict]
get_commercial_hazard_curve(catchment, asset_id, mode="flood") -> dict | None
save_commercial_hazard_curves(catchment, payload, mode="flood") -> None # → @require("Func001","create")
```

## 4. Timeseries

```python
# Property flood timeseries (per mode)
iter_property_timeseries_ids(catchment, mode="flood") -> Iterator[str]
get_property_timeseries(catchment, property_id, mode="flood") -> dict | None
save_property_timeseries(catchment, property_id, payload, mode="flood") -> None  # → @require("Func001","create")
get_portfolio_flood_summary(catchment, mode="flood") -> dict | None

# Commercial timeseries (per mode)
iter_commercial_timeseries_ids(catchment, mode="flood") -> Iterator[str]
get_commercial_timeseries(catchment, asset_id, mode="flood") -> dict | None
save_commercial_timeseries(catchment, asset_id, payload, mode="flood") -> None   # → @require("Func001","create")

# Gauge timeseries & history
iter_gauge_timeseries_ids(catchment) -> Iterator[str]
get_gauge_timeseries(catchment, gauge_id) -> dict | None        # used for hydrographs
save_gauge_timeseries(catchment, gauge_id, payload) -> None     # → @require("Func001","create")
get_gauge_history(catchment, gauge_id) -> dict | None           # gaugehd (long record)
save_gauge_history(catchment, gauge_id, payload) -> None        # → @require("Func001","create")
```

## 5. Storms & stress testing

```python
# Storm sequences (multi-storm metadata)
get_storm_sequences(catchment) -> dict | None
save_storm_sequences(catchment, payload) -> None           # → @require("Func001","create")

# Stress storms (index + per storm)
list_stress_storms(catchment) -> list[dict]                # from the index (cached)
get_stress_storm(catchment, storm_id) -> dict | None
save_stress_storms(catchment, storms) -> None              # → @require("Func001","create")

# Sequence→gauge summaries
list_sequence_gauges(catchment) -> list[dict]
get_sequence_gauge(catchment, gauge_id) -> dict | None
save_sequence_gauge(catchment, gauge_id, payload) -> None  # → @require("Func001","create")
```

## 6. Perils (fire / seismic / typhoon)

```python
# Fire & seismic model outputs (commercial)
get_fire_results(catchment) -> dict | None
get_fire_result(catchment, asset_id) -> dict | None
save_fire_results(catchment, payload) -> None              # → @require("Func001","create")
get_seismic_results(catchment) -> dict | None
get_seismic_result(catchment, asset_id) -> dict | None
save_seismic_results(catchment, payload) -> None           # → @require("Func001","create")

# Typhoon events — hybrid: metadata in DB, large particle blob in object store
list_typhoon_events(catchment) -> list[dict]               # metadata only (light)
get_typhoon_event(catchment, event_id) -> dict | None      # metadata
get_typhoon_event_blob(catchment, event_id) -> bytes       # the ~MBs of particle data
save_typhoon_event(catchment, event_id, meta, blob) -> None # → @require("Func001","create")
```

## 7. Trading desk

```python
# PRS trades
list_prs_trades(catchment) -> list[dict]
get_prs_trade(catchment, swap_id) -> dict | None
commit_prs_trade(catchment, trade) -> None                 # → @require("Func003","create")
update_prs_trade(catchment, swap_id, changes) -> None       # → @require("Func003","write")
close_prs_trade(catchment, swap_id) -> None                # → @require("Func003","delete")

# Trade marks / status
get_trade_marks(catchment) -> dict
set_trade_status(catchment, swap_id, status) -> None        # → @require("Func003","write")
save_trade_marks(catchment, marks) -> None                 # → @require("Func001","create")

# Market state
get_market_state(catchment) -> dict | None
save_market_state(catchment, state) -> None                # → @require("Func003","write")

# End-of-day snapshots
list_eod_snapshots(catchment) -> list[dict]                # dates + summaries
get_eod_snapshot(catchment, eod_date) -> dict | None
save_eod_snapshot(catchment, eod_date, payload) -> None    # → @require("Func003","create")
```

## 8. Classifiers (binary model artifacts)

```python
list_classifier_ids(catchment) -> list[str]                # per-gauge .joblib models
get_classifier(catchment, gauge_id) -> bytes | None
save_classifier(catchment, gauge_id, blob) -> None         # → @require("Func004","create")  (stress)
delete_classifier(catchment, gauge_id) -> None             # → @require("Func004","delete")
get_training_summary(catchment) -> dict | None
save_training_summary(catchment, payload) -> None          # → @require("Func004","write")
```

## 9. Admin & permissions (Func000)

The RBAC store lives here too, so permission checks are one call and have no SQL outside
this package. See `docs/db_users_and_permissions.md`.

```python
# Users  (all → @require("Func000", ...))
list_users() -> list[dict]
get_user(username_or_id) -> dict | None
create_user(username, display_name, *, by_user) -> str     # returns user_id
disable_user(user_id, *, by_user) -> None
set_password(user_id, new_secret, *, by_user) -> None

# Permissions
list_functions() -> list[dict]                             # the FuncNNN registry
add_function(code, name, description="") -> None
get_permissions(user_id) -> dict                           # {Func001: {read,write,create,delete}, ...}
set_permission(user_id, function_code, *, read, write, create, delete, by_user) -> None
can(user_id, function_code, capability) -> bool            # the check behind @require(...)

# Audit (append-only)
record_audit(actor_user_id, action, function_code, target) -> None
list_audit(*, user_id=None, function_code=None, since=None) -> list[dict]
```

---

## Backend selection (the migration switch)

```python
# at app/CLI startup — the ONE place the backend is chosen:
from database import configure_backend
from database.file_repo import FileRepository      # today
# from database.pg_repo import PostgresRepository  # tomorrow

configure_backend(FileRepository(config.get_input_dir().parent))
# configure_backend(PostgresRepository(dsn=os.environ["MKM_DB_DSN"]))
```

Everything in sections 1–9 is unchanged when that line flips. That is the whole point.

---

## What is intentionally NOT here

- No generic query/SQL function. Add a named function instead.
- No path or filename helpers exposed to callers (they stay private, used only by
  `file_repo.py`).
- No governance data (model inventory, lineage, audit docs) — out of migration scope.
- Report **PDFs** are not data; they stay as files/object store. The PDF *builders* read
  their inputs through the functions above.
