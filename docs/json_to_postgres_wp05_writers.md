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
