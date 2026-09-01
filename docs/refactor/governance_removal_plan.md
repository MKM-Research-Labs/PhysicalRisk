# Removing governance from PhysicalRisk

**Status:** proposed, 2026-09-01 · **Destination:** MKM-ModelRisk ·
**Principle:** this is a *migration*, not a deletion. Nothing is removed here
until it demonstrably exists there.

## 1. Scope

**Removed** (user decision, 2026-09-01): the Model Governance panel and its 121
endpoints; all governance unit and e2e tests; the governance document
generators; model documentation under `docs/models/<model>/`; and the audit
sections that read `model_inventory.json`.

**Retained:** the data-lineage **engine** (`src/lineage/`, 2,128 lines) and the
`phys.py test --lineage` phase. Provenance is a property of the pipeline, not of
governance. Only the three lineage *tabs* and their routes go.

## 2. Measured footprint

| Component | Modules | Lines |
|---|---:|---:|
| `src/routes/governance/` (121 endpoints) | 27 | 3,641 |
| `tests/routes/governance/` | 44 | 8,224 |
| `src/static/js/governance/` + `modelgovernance-panel.js` | 27 | 4,824 |
| `src/visual/interactivity/governance/` | 38 | 1,192 |
| `docs/models/` generators (model_risk, mrc_tor, bcbs239, parameter_inventory, test_results) | 53 | 5,751 |
| e2e (`test_gov_*`, `test_governance`, `test_model_documentation`) | 12 files | 83 tests |
| Model documentation | — | 122 `.tex` |

**≈ 23,600 lines of Python/JS, 83 e2e tests, 122 LaTeX documents.**

The coupling is shallower than the size suggests — only **three import sites**
reach into governance:

- `src/routes/registry.py:34` → `governance_bp`
- `src/visual/interactivity/__init__.py:59` → `ModelGovernancePanel`
- `src/visual/interactivity/manager.py:46` → `ModelGovernancePanel`

**RBAC is NOT coupled** — the permission catalogue lives in
`src/database/_pg/_auth_models.py`. Removing governance does not touch trading
authentication. This was the one finding that could have blocked the project.

## 3. Stages

Leaves first, roots last, so the tree is never in a half-wired state.

### Stage 0 — Parity and handover (blocking)
1. Confirm MKM-ModelRisk ingests the current `model_inventory.json`, MRC
   meetings, RACI, BCBS 239 mappings, bibliography and documents.
2. **Export the governance data before any deletion.** `model_inventory.json`
   is ModelRisk's ingest source and the MRC/audit-trail data is not
   reproducible — the audit trail alone holds ~10,000 events.
3. Tag the pre-removal commit so the whole subsystem can be recovered whole.

*Gate: nothing proceeds until ModelRisk demonstrably serves this data.*

### Stage 1 — Tests
`tests/routes/governance/` (44 modules), the 12 e2e files, the governance
helpers in `tests/e2e/helpers.py` (`open_governance`, `switch_governance_tab`,
`get_governance_content_text`), the `_protect_mrc_meetings` and
`_isolated_governance_dir` conftest fixtures, and
`tests/commands/test_model_risk_report_*` + `test_model_chain_report`.

⚠️ Per the standing rule against deleting features without checking their tests:
read each file for assertions covering **non-governance** behaviour before
deleting it, and re-home anything that does.

### Stage 2 — Front end
`src/static/js/governance/`, `modelgovernance-panel.js`,
`src/visual/interactivity/governance/`, and the two import sites in
`interactivity/`. Remove the panel's launch control from the map.

### Stage 3 — Routes
`src/routes/governance/` and its registration in `registry.py`. This takes with
it the lineage routes (676 lines) and the model-documentation PDF endpoints
(`get_model_documentation_pdf`, `get_model_test_results_pdf`,
`get_model_analysis_pdf`) — both live inside the governance blueprint.

### Stage 4 — Documents and generators
`docs/models/model_risk`, `mrc_tor`, `bcbs239`, `governance_data`,
`parameter_inventory`, `test_results` (the attribution machinery), and the 26
per-model documentation directories.

### Stage 5 — Audit and the test command
This is where a removal like this usually breaks the build:

1. `full_audit` **§4.7 model chain** — deleted; it reads `model_inventory.json`.
2. **§4.5** `_EXCLUDED_PREFIXES` — drop `'src/routes/governance'`.
3. `full_audit/sections_tests/modularisation.py` — drops its inventory reference.
4. `app/commands/test/audit.py` — remove the `docs.models.test_results.generator`
   phase and the `model risk governance report` phase.
5. **`app/commands/test/artefacts.py` — remove the `Model Risk Report PDF` and
   `Test Report PDF` entries.** Left in place, the freshness gate added in
   `b9d4e3d3` will fail every run once their generators are gone.
6. **Delete the stale PDFs from `data/output/audit/`.** They would otherwise
   persist as artefacts of a subsystem that no longer exists.

### Stage 6 — Config and cleanup
`config/theme/_governance.py` may stay: those ramps are deliberately shared with
ModelRisk and cost nothing. Sweep dead tokens, dead allowlist entries, and the
`config/port/_misc.py` comment referencing `routes/governance/lineage.py`.

## 4. Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | **Coverage gate.** Removing 8,224 lines of well-covered tests alongside 3,641 lines of source moves the ratio in a direction nobody can predict from the outside. If governance was better covered than average, the total *falls*. | Measure after each stage. Budget for topping up coverage elsewhere; do not lower `fail_under`. |
| R2 | **Artefact freshness gate fails the run** the moment a generator goes but its manifest entry stays. | Stage 5 items 4–6 are a single atomic change. |
| R3 | **Irrecoverable data.** MRC meetings and the ~10k-event audit trail are not regenerable. | Stage 0 export is a hard gate. |
| R4 | **Per-model test evidence disappears.** `phys.py test` currently attributes 154 of 844 test files to 28 model groups and writes `test_results.tex` per model. That evidence chain ends. | Confirm ModelRisk reproduces it from JUnit XML before Stage 4. |
| R5 | Model documentation is a **modelling deliverable**, not a governance process artefact. Removing it leaves PhysicalRisk with no in-repo model docs. | Explicitly accepted; ModelRisk becomes the sole home. |

## 5. Verification

After each stage: full unit suite with coverage, the four zero-tolerance audits
(§4.3 paths, §4.5 JSON, §4.6 database, §4.8 styling), and — after Stages 2 and 3
— an e2e run, since the panel's removal touches the shared map page that every
e2e test loads.

## 6. Open decisions

1. **`data_lineage_report.pdf` (BCBS 239).** The engine and test phase stay, so
   the report can too — but its framing is explicitly governance. Keep as
   pipeline-provenance evidence, or send it to ModelRisk with the rest?
2. **`parameter_inventory`** (1,052 lines) documents model parameters rather
   than governance process. Included above; worth confirming.
3. **`test_interpretation`** (600 lines) reads audit output and is not
   governance-specific. Proposed: retain.
