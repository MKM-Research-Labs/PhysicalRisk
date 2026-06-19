# WP0.5 — Writer migration scoping (Group B)

Mirror of the WP0.6 read-path migration: route every direct JSON **write** through the
`database` package's `save_*` / `commit_*` / `delete_*` API so the file-vs-Postgres
choice stays inside `src/database/`. Discovery scan done on branch
`claude/quirky-chaplygin-a2a625` (read-only; no port runs in a worktree).

Same disciplines as WP0.6: behaviour-preserving, per-file commits, ≥99% coverage per
stage, database package stays 100%, **0 new path-audit findings**, and the recurring
**test-fixture gotcha** (fixtures that stage data under `output/` must be repointed to
the production `input/<catchment>/…` location the artifacts resolve to; tests that
assert "file exists on disk" should read back through the database instead).

## ⚠️ BLOCKER discovered during Batch-1 spike (resolve before implementing)

**Every writer is directory-injected, not catchment-keyed.** Both the port generators
and the trading engines are constructed with an explicit output directory and write
to it:

```python
# generators (gauge/property/loan/commercial/commercial_loan/counterparty, …)
self.output_dir = Path(output_dir) if output_dir else config.get_input_dir()
# engines
def __init__(self, trading_dir): self.marks_file = trading_dir / 'trade_marks.json'
```

The database write API is **catchment-keyed** — `save_gauges(catchment, payload)`
resolves to *that catchment's* dir. It has no "write to directory X" primitive, and
correctly so: a directory is meaningless for the Postgres backend. So the readers
migrated cleanly (routes always read the active catchment via `config` accessors) but
the writers do **not** — `output_dir` is a first-class parameter threaded from the port
orchestrator and passed by **~74 test files**.

In production `output_dir` is effectively always the catchment being generated (the port
pipeline runs one catchment per invocation), so it *equals* `config.get_input_dir()`.
But the abstraction mismatch is real and can't be papered over.

**Options:**
1. **Catchment-context refactor (preferred; = WP2.4).** Replace `output_dir` threading
   with a run-scoped *catchment* context; generators/engines call `save_*(catchment, …)`.
   This is the right end-state and the memory already earmarks WP2.4 for the
   global-catchment-context fix. Cost: orchestrator + engine constructors + ~74 test
   files repointed (mechanical: pass/monkeypatch catchment instead of `output_dir`).
   **Recommendation: fold WP0.5 into WP2.4 and do them together**, rather than migrate
   writers twice.
2. Add a per-operation "bind FileRepository to this dir" escape hatch to the database —
   rejected: leaky abstraction, no Postgres analogue, defeats the seam.
3. Reverse-map `output_dir` → catchment at each writer boundary — rejected: fragile.

**Serialization sub-requirement (needed by whichever option):** generator payloads carry
`datetime` + numpy (`np.integer/np.floating/np.ndarray`) values; today they serialize via
`port.utils.encoders.DateTimeEncoder` / `port.src.property.hc.encoder.json_default`
(both → `isoformat()` / `int`/`float`/`tolist`). The database's `file_repo.save` uses a
plain `json.dumps(payload, indent=2)` with **no encoder**, so it will `TypeError` on these
payloads. Before any writer migration, give the database a canonical JSON default that
mirrors `DateTimeEncoder` (datetime→isoformat, numpy→native) so callers stop passing
encoders. This is a clean, self-contained prep step that can land independently.

**Net:** the per-file writer→`save_*` mapping below is still correct, but Batch 1 cannot
proceed as a standalone step — it needs (a) the database serialization default, then
(b) the catchment-context decision. Treat the table below as the work-list *once that
decision is made*.

## In-scope writers → target `save_*`

### Port generators (`src/port/`) — the bulk
| Writer (file:line) | Artifact / file | Target saver |
|---|---|---|
| `src/port/src/gauge/_gauge_generate.py:164` | gauge.json | `save_gauges` |
| `src/port/src/gauge/synthetic/generator/_core.py:167` | synthetic gauge.json | `save_gauges` |
| `src/port/src/property/main/generator.py:199` | property.json | `save_properties` |
| `src/port/src/mortgage/_generate.py:133` | loan.json | `save_loans` |
| `src/port/src/commercial/main/generator.py:166` | commercial.json | `save_commercial` |
| `src/port/src/commercial_loan.py:229` | commercial_loan.json | `save_commercial_loans` |
| `src/port/src/counterparty/_generator.py:92` | counterparty.json | `save_counterparties` |
| `src/port/src/property/hc/generator/_generator.py:155` + `_decomposition.py:227` | propertyhc.json (+ modes) | `save_property_hazard_curves` |
| `src/port/src/gauge/gaugets.py:195` + `src/port/src/stressm/gaugets_writer.py:106` | gaugets/GAUGE-*.json | `save_gauge_timeseries` |
| `src/port/src/property/ts/flood/process.py:225` | propertyts/PROP-*.json | `save_property_timeseries` |
| `src/port/src/property/ts/generator.py:167` | propertyts/portfolio_flood_summary.json | **NEW `save_portfolio_flood_summary`** |
| `src/port/src/peril/peril_ts.py:188-226` | peril ts by mode (`cfg.ts_dirs[mode]`) | `save_property_timeseries` / `save_commercial_timeseries` (mode-mapped) — **verify mode→dir map** |
| `src/port/cdm/gaugehd/generator.py:215` + `gauge/gaugehd/{nrfa,synthetic}.py` | gaugehd/GAUGE-*_hd.json | `save_gauge_history` |
| `src/port/src/gauge/_stress_storms_stages.py:239` | stress_storms/{id}.json | `save_stress_storm` |
| `src/port/src/gauge/_stress_storms_stages.py:273` | stress_storms/_index.json | **NEW `save_stress_storm_index`** |
| `src/port/src/stressm/pipeline/stages.py:116` | sequence_gauge/{gid}.json | `save_sequence_gauge` |
| `src/port/src/stressm/pipeline/stages.py:92` | sequence_gauge/_index.json | **NEW `save_sequence_gauge_index`** (or new artifact) |
| `src/port/src/stressm/pipeline/stages.py:57` + `:121` | legacy flat `sequence_gauge_*.json` + `GAUGE_SUMMARY_FILENAME` | **DECISION: keep legacy writer or drop** (parallels the WP0.6 legacy read decision) |
| `src/port/src/stressm/summary.py:37` | training_summary.json | `save_classifier_training_summary` — **RECONCILE dir: writer uses `stressm_dir`, route reads `get_classifiers_dir()`; confirm same path** |
| `src/port/src/storm_multi/utils/serialization.py:64` | storm_sequences.json | `save_storm_sequences` |
| `src/port/src/storm_multi/utils/serialization.py:156` | storm-multi run summary | **DECISION: port artifact (new) vs model-internal (leave)** |
| `src/port/src/storm_multi/models/_spatial_math.py:128` | spatial-correlation cfg | **DECISION: port artifact (new) vs model-internal (leave)** |
| `src/port/src/historical_eod/_history.py:91,179` | blotter/eod/EOD-*.json | `save_eod_snapshot` |
| `src/port/src/historical_eod/_series.py:139` | blotter/market_state.json | `save_market_state` |
| `src/port/src/book/book_common/_pricing.py:158` | prs/PRS-*.json | `save_prs_trade` / `commit_prs_trade` |

### Trading engines (`src/models/trading/`) — deferred from WP0.6 (write side)
| Writer | File | Target saver |
|---|---|---|
| trade marks | `models/trading/trade_marks.py:57` | `save_trade_marks` |
| market state | `models/trading/market_state/_persistence.py:156` | `save_market_state` |
| EOD snapshot | `models/trading/pnl_engine/_pnl.py:197` | `save_eod_snapshot` |

### Hazard / wind models
| Writer | File | Target saver |
|---|---|---|
| gaugehc | `models/hazard/io/_save.py:59,117` | `save_gauge_hazard_curves` |
| typhoon ensemble/damage | `models/typhoon/pipeline/ensemble/_io.py:35,71,104` | `save_typhoon_event` (verify granularity) |
| wind damage event | `models/winddamage/event.py:153` | `save_typhoon_event` (or new wind artifact) |

## New database API needed (WP0.5)
1. `save_portfolio_flood_summary(catchment, payload, mode=…)` — artifact + getter already exist.
2. `save_stress_storm_index(catchment, payload)` — `stress_storm_index` artifact exists (read-only today).
3. `save_sequence_gauge_index(...)` — needs a `sequence_gauge_index` artifact (`sequence_gauge/_index.json`), mirroring `stress_storm_index`.
4. Possibly: storm-multi summary + spatial-correlation artifacts (pending the model-internal vs port-artifact decision).

## Decisions to make before/while implementing
- **Legacy writers** (flat `sequence_gauge_*.json`, `GAUGE_SUMMARY_FILENAME`, any legacy storm summary): keep writing for back-compat, or drop now that readers prefer the sharded `_index.json` layout? (WP0.6 *kept* the legacy *readers*.)
- **training_summary path**: port writer uses `stressm_dir`; the classifiers route reads `get_classifiers_dir()`. Confirm these are the same directory (artifact resolves to `classifiers/training_summary.json`) or fix the mismatch.
- **storm-multi summary + spatial-correlation cfg**: are these port artifacts (migrate) or model-internal scratch (leave on file I/O)?
- **typhoon/winddamage granularity**: one `typhoon_event` per EVT id vs an ensemble blob — confirm the artifact shape matches `save_typhoon_event`.

## Out of scope (do NOT migrate)
- **PDF read/write** everywhere (blotter, eod, prs, report PDFs) — stay as files/object store.
- **`src/reports/property/property_integrator.py`, `src/reports/gauge/gauge_integrator.py`** — write `*.txt`/report files under `data/output/` (generated reports, not port input artifacts).
- **`src/lineage/manifest/_core.py`** — version-controlled lineage manifest (governance-class, not in `data/`).
- **`src/models/audit.py`** — app-level audit log (credential/governance-class).
- **`src/models/intensity/cli.py`** — `json.dumps` to **stdout**, not a file.
- **`src/visual/interactivity/context_menus.py`** — `json.dumps` into embedded JS config strings, not file writes.
- **`src/routes/trading/_admin_auth.py`** — shared admin credential file.

## Suggested batching (per-file commits, test-repoint as needed)
1. **Portfolio entities** (gauge, property, loan, commercial, commercial_loan, counterparty) — all map to existing savers; lowest risk.
2. **Hazard curves** (property hc + models/hazard gaugehc).
3. **Timeseries** (gaugets, propertyts + portfolio_flood_summary[new], peril ts).
4. **Storms/sequences** (stress_storms + index[new], sequence_gauge + index[new], storm_sequences) — handle legacy decision here.
5. **Trading writers** (engines: trade_marks, market_state, eod; book pricing → prs).
6. **gaugehd** + **typhoon/winddamage** (typhoon_event granularity).
7. Then **task 0.8 audits** (sanction `src/database` in path-audit; build the no-SQL-outside-`database` audit) and **task 0.7** (stress mtime cache).

After WP0.5, all port-artifact file I/O is funnelled through `database`, clearing the way for the `PostgresRepository` swap (WP1).
