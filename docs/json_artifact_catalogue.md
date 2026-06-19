# Port JSON Artifact Catalogue — Producer → File → Consumer

**Status:** Draft — 2026-06-18. Companion to `docs/json_to_postgres_migration.md`
(this is deliverable **task 0.1**). All references are `file:line` and were grepped
from the tree, not inferred.

How to read: each row is one artifact type. "Producer" = the module that writes it
during `python app.py port ...`. "Consumers" = the modules that read it (Flask routes
+ tools). "Target" = where it lands in the PostgreSQL design (see migration doc §2.2).
`<id>` = entity id (e.g. `PROP-...`, `GAUGE-...`); `<mode>` = scenario variant.

Catchment lives in the path today (`data/input/<catchment>/...`) and becomes a
`catchment_id` column on every target table.

---

## A. Root aggregate entities → **relational tables**

| Artifact | Producer | Consumers (read sites) | Target table |
|---|---|---|---|
| `gauge.json` | `src/port/src/gauge/_gauge_generate.py:165` (+ synthetic append `src/port/src/gauge/synthetic/generator/_core.py:168`) | `_storm_enrich.py:111`, `propertyts/animation/_helpers.py:147`, `propertyts/financial_loaders.py:167`, `trading/stress/training.py:114`, `trading/risk.py:95`, `governance/lineage/_trace/_data_trace.py:79` | `gauge` |
| `property.json` | `src/port/src/property/main/generator.py:200` | `propertyts/financial_loaders.py:65,201`, `propertyts/claim.py:64`, `propertyts/core_storm_list.py:163`, `propertyts/core_storms/_helpers.py:152`, `propertyts/risk.py:74`, `propertyts/wind_impact.py:89` | `property` |
| `loan.json` | `src/port/src/mortgage/_generate.py:134` | `propertyts/financial_loaders.py:81`, `propertyts/claim.py:79`, `propertyts/risk.py:88` | `loan` |
| `commercial.json` | `src/port/src/commercial/main/generator.py:167` | `commercial/portfolio/_blotter.py:47`, `_impact.py:55`, `_list.py:45`, `commercial/storms.py:64`, `commercial/hazard/_routes.py:239`, `propertyts/wind_impact.py:57` | `commercial` |
| `commercial_loan.json` | `src/port/src/commercial_loan.py:230` | `commercial/portfolio/_blotter.py:59`, `_impact.py:80`, `_list.py:70`, `commercial/pricing.py:46` | `commercial_loan` |
| `counterparty.json` | `src/port/src/counterparty/_generator.py:93` | `routes/counterparty.py:39`, `governance/lineage/_trace/_data_trace.py:193` | `counterparty` |

## B. Hazard curves → **relational tables** (one per asset class × mode)

| Artifact | Producer | Consumers | Target table |
|---|---|---|---|
| `gaugehc.json` | `app/commands/port/stages/hazardcurves.py` (`run_gaugehc` stage) | `propertyts/financial_loaders.py:178`, `propertyts/financial_basis.py:105`, `trading/_helpers.py:100`, `trading/stress/scenario.py:112`, `trading/port_stress/_routes.py:132`, `gauges/hazard.py:54,138`, `gauges/reports.py:93`, `_storm_enrich.py:136` | `gauge_hazard_curve` |
| `propertyhc.json` | `src/port/src/property/hc/generator/_generator.py:156` (+ decomposition `_decomposition.py:228`) | `propertyhc/_helpers.py:30,39` → `_summary.py`, `_perils.py` | `property_hazard_curve` |
| `propertyshd.json` / `propertyshe.json` / `propertybri.json` | `src/port/src/property/hc/generator/_generator.py:156` (per `<mode>`) | `propertyhc/_perils.py:37,54,99` | `property_hazard_curve` (mode col) |
| `propertywin/faw/fow/bow/baw.json` | windhazard stage (`app/commands/port/stages/windhazard/_placeholders.py:114` for zero-event placeholders; real via property hc generator) | `propertyhc/_perils.py:123,132,146,160,174` | `property_hazard_curve` (mode col) |
| `commercialhc.json` / `commercialshd/she/bri/win.json` | `src/port/src/commercial/hc/generator` | `commercial/hazard/_routes.py:41,79,95,115,134` | `commercial_hazard_curve` (mode col) |

## C. Per-entity timeseries → **JSONB tables**, keyed `(catchment_id, entity_id, mode)`

| Artifact (path) | Producer | Consumers | Target table |
|---|---|---|---|
| `propertyts/<id>.json` + `portfolio_flood_summary.json` | `src/port/src/property/ts/flood/process.py:226` (+ summary `src/port/src/property/ts/generator.py:168`) | `propertyts/_helpers.py:30` (dir), `core_summary.py:51,71`, `risk.py:52`, `governance/lineage/_trace/_data_trace.py:159` | `property_timeseries` |
| `propertytsd/tse/tsb/tsw/tsfaw/tsfow/tsbow/tsbaw/<id>.json` | `src/port/src/property/ts/flood/process.py:226` (flood modes); wind modes `src/port/src/peril/peril_ts.py:227` | mostly consumed indirectly via the hazard-curve generators; few direct route reads | `property_timeseries` (mode col) |
| `commercialts[d/e/b/...]/<id>.json` | `src/port/src/commercial/ts` (per mode) | `commercial/portfolio/_impact.py:45`, `_blotter.py:81`, `commercial/storms.py:50` | `commercial_timeseries` |
| `gaugets/<id>.json` | `src/port/src/gauge/gaugets.py:196` (+ `src/port/src/stressm/gaugets_writer.py:106`) | `trading/stress/_helpers.py:124` (hydrograph), `propertyts/animation/_helpers.py:152`, `propertyts/core_storm_list.py:82`, `gauges/storms.py:132` | `gauge_timeseries` |
| `gaugehd/gauge_<id>_hd.json` | `src/port/src/gauge/gaugehd/nrfa.py:171`, `…/synthetic.py:120` (+ `src/port/cdm/gaugehd/generator.py:216`) | `gauges/history.py:38,60`, `gauges/reports.py:78` | `gauge_history` |
| `stress_storms/<id>.json` + `_index.json` | `src/port/src/gauge/_stress_storms_stages.py:240` (storm), `:274` (index) | `trading/stress/_helpers.py:49,96` (`_load_stress_storms` / `_load_stress_storm`, **mtime-cached**) → `storms.py`, `port_stress/_routes.py:47,125`; `_storm_enrich.py:79`; `propertyts/core_storm_list.py:53`, `financial_basis.py:129` | `stress_storm` |
| `sequence_gauge/<id>.json` + `_index.json` | `src/port/src/stressm/pipeline/stages.py:118` (gauge), `:94` (index), `:59` (summary) | `governance/lineage/_trace/_data_trace.py:99` | `sequence_gauge` |
| `storm_sequences.json` | `src/port/src/storm_multi/utils/serialization.py:65` (+ summary `:157`) | `_storm_enrich.py:51,137`, `gauges/storms.py:62`, `propertyts/claim.py:47`, `core_storm_list.py:114`, `risk.py:60`, `trading/stress/training.py:145,205`, tool `cdm_property_editor/app.py:244` | `storm_sequence` |

## D. Large blobs → **object store + metadata row**

| Artifact | Producer | Consumers | Target |
|---|---|---|---|
| `typhoon/damage/EVT-<id>.json` (≤69 MB particle/event files) | typhoon model + placeholder writer `app/commands/port/stages/windhazard/_placeholders.py:114` | `propertyts/wind_impact.py:51,178`, `propertyts/core_storms/_helpers.py` (glob) | `typhoon_event` row (metadata) + blob in S3/MinIO |

## E. Trading desk → **relational tables**

| Artifact | Producer | Consumers | Target table |
|---|---|---|---|
| `prs/PRS-<id>.json` (trade confirmations) | `src/port/src/book/book_common/_pricing.py:159` | `prs/blueprint.py:44`, `trading/client.py:40`, `trading/_helpers.py:51,65`, `trading/blotter.py:130,230`, `propertyts/financial_prs.py:42` | `prs_trade` |
| `blotter/trade_marks.json` | `app/commands/port/stages/trading.py:143` | `trading/_helpers.py:49,67`, `trading/blotter.py:131` | `trade_mark` |
| `blotter/market_state.json` | `src/port/src/historical_eod/_series.py:140` | `trading/_helpers.py:67` (trading dir) | `market_state` |
| `blotter/eod/EOD-<date>_<hhmm>.json` (~90/catchment) | `src/port/src/historical_eod/_history.py:92,180` | `trading/eod.py:68,118` | `eod_snapshot` |
| `fire/fire.json` | `app/commands/port/stages/fire.py:136` | `commercial/hazard/_helpers.py:77`, `routes/perils.py:52` | `fire_result` |
| `seismic/seismic.json` | `app/commands/port/stages/seismic.py:149` | `commercial/hazard/_helpers.py:129`, `routes/perils.py:58` | `seismic_result` |
| `classifiers/<gauge>.joblib` (model artifact, not JSON) | `trading/stress/training.py` (UI-trained, per-gauge) | `trading/stress/scenario.py:125`, `trading/classifiers/*` | object store (binary) |

---

## F. Migration notes embedded in the read paths

- **Single write chokepoint already exists for paths** (`config.get_input_path` /
  `config.get_input_dir` + the dir accessors in `config/path/`). Reads do **not** share
  a data chokepoint — hence WP0's repository seam. Note `get_reports_dir("prs")` is the
  accessor for the `prs/` trade dir; `get_trading_dir()` for `blotter/`.
- **Legacy fallbacks to preserve in the schema/repo:** stress storms fall back from
  `stress_storms/_index.json` to a single `stress_storms.json`
  (`trading/stress/_helpers.py:78`); sequence_gauge falls back to
  `sequence_gauge_summary.json` (`_data_trace.py:100`); storm metadata tries both
  `storm_sequences.json` and `storms.json` (`_storm_enrich.py:61`,
  `core_storm_list.py:114`). The importer must handle both shapes.
- **Only cache today** is the stress-storm mtime cache (`trading/stress/_helpers.py:41`);
  fold it behind the repo (task 0.7) so it survives the DB swap.
- **Zero-event placeholders:** wind/typhoon hazard files are written as empty
  placeholders when the typhoon ensemble wasn't run
  (`windhazard/_placeholders.py:114`); the schema needs an explicit "empty/placeholder"
  state, not a missing row.
- **Tools bypass `config`** and hardcode thames: `tools/cdm_property_editor/app.py`
  (`INPUT_DIR`, `FIRE_FILE:216`, `SEISMIC_FILE:217`, `storm_sequences:244`) and
  `_recompute_oracle.py:40-110` (`THAMES/...`). These need WP3 handling, not the
  transparent route swap.
