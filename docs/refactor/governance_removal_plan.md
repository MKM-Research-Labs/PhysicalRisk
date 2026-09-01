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

---

## 7. Stage 0 results — 2026-09-01

### 7.1 Done

- **Recovery tag** `pre-governance-removal` created and pushed. The whole
  subsystem is recoverable from it.
- **Data exported** to `~/Documents/PhysicalRisk-governance-export-2026-09-01`
  (3.8 MB, 9 files) with a verified SHA-256 `MANIFEST.sha256`.
- Note the data was already version-controlled under
  `docs/models/governance_data/`, so risk **R3 (irrecoverable data) is lower
  than stated** — git history holds it regardless. The export exists for
  handover, not rescue.
- `governance_docs/` and `mrc_uploads/` contain only `.gitkeep` — there are **no
  uploaded documents** to migrate.

### 7.2 Parity against MKM-ModelRisk — **the gate does not pass yet**

Checked against ModelRisk at `1c2b95d`: 13 migrations, 30 `src/governance`
modules, and ingest contracts for model_inventory, model_chain, data_lineage,
field_lineage, document and ml_training_run.

| PhysicalRisk data | Size | ModelRisk home | Verdict |
|---|---:|---|---|
| `model_inventory.json` | 264 KB | module + ingest contract + view | ✅ **Ready** |
| `governance_documents.json` | 2 entries | `documents.py` + `document.schema.json` | ✅ **Ready** |
| `mrc_meetings.json` | 12 KB | `mrc/` + `0004_mrc_meeting_view.sql` | ⚠️ Feature exists, **no ingest contract** |
| `bibliography.json` | 3.5 KB | `bibliography/` | ⚠️ Feature exists, **no ingest contract** |
| `raci_matrix.json` | 7.6 KB | RACI as four roles scaffolded on a *Product* | ⚠️ **Shape mismatch** — a standalone matrix has no equivalent |
| `bcbs239_assessment.json` | 13.8 KB | none — BCBS 239 appears only as the *rationale* for field lineage | ❌ **No home** |
| `model_audit_log.json` | **10,000 events** | event store exists; no importer, no audit-trail module | ❌ **No import path** |

⚠️ **Method note:** an initial grep suggested RACI was in ModelRisk's schema.
That match was the word "ra**ci**ng" in a comment. Re-checked with word
boundaries — RACI is a Product role concept there, not PhysicalRisk's matrix.
Verify parity claims with `grep -w`, not substring.

### 7.3 RESOLVED by decision, 2026-09-01

**There is no transfer.** MKM-ModelRisk is already functional with its own
data, so nothing needs to move. This is a clean-out: the audit log, BCBS 239
assessment, RACI matrix, bibliography and MRC meetings are all removed rather
than migrated. §7.2's parity table is therefore moot — recorded above only
because it is the evidence that nothing was stranded by accident.

The recovery tag and the verified export remain the safety net: everything
deleted is recoverable from `pre-governance-removal`.

### 7.4 ⚠️ Ordering correction to §3

The staging in §3 is **wrong for the coverage gate**. Removing
`tests/routes/governance/` (8,224 lines) in Stage 1 while
`src/routes/governance/` (3,641 lines) survives until Stage 3 would leave that
source uncovered and drop the total far below `fail_under = 99` — a red build
for two whole stages.

Source and its tests must be removed **atomically**. Revised slices:

| Slice | Contents | Coverage effect |
|---|---|---|
| **A** | e2e governance tests (12 files, 83 tests) | none — e2e is `--ignore`d and contributes no coverage |
| **B** | JS + `visual/interactivity/governance` **+ their unit tests** | neutral |
| **C** | `src/routes/governance` **+ `tests/routes/governance`** | neutral |
| **D** | doc generators + model docs **+ their tests** | neutral |
| **E** | audit wiring, artefact manifest, stale PDFs | none |

Each slice is committed and verified on its own.

### 7.5 ⚠️ Slice C blocker found during slice B

**The trading desk depends on a governance route.**
`src/static/js/storm/sp_control/setup_dom.js:202` opens the Control tab's User
Guide from `/api/v1/governance/<guide_key>/guide/pdf`, defined at
`src/routes/governance/audit.py:168` with a key map at line 159 that includes
`storm-control`.

Deleting the governance blueprint outright therefore breaks a live trading-desk
feature and the e2e tests `test_guide_pdf_endpoints_respond` and
`test_user_guide_button_opens_pdf`. **Slice C must relocate the guide-PDF route
out of governance before removing the blueprint** — it serves operational user
guides, not governance.

### 7.6 Superseded

**Do not begin Stage 1** *(superseded by §7.3 — no transfer required)*. Five of seven data types are not yet safely
transferable, two of them with no destination at all. Removing governance now
would strand the BCBS 239 assessment and a 10,000-event audit trail with
nothing on the other side to receive them.

Prerequisites, in ModelRisk:

1. **An audit-trail import path.** 10,000 events with a stable shape
   (`action`, `context`, `event_type`, `model_id`, `parameters`, `source`,
   `timestamp`, `user`) — a natural fit for the existing event store, but
   nothing maps onto it today.
2. **A decision on BCBS 239.** Either build the assessment feature, or accept
   that the assessment is retired and record that as a deliberate loss.
3. **A RACI decision.** Map the matrix onto Product roles, or keep it as a
   distinct artefact.
4. **Ingest contracts for `mrc_meetings` and `bibliography`**, so the transfer
   is validated rather than hand-loaded.

Only item 1 is large. Items 2–4 are decisions first and code second.
