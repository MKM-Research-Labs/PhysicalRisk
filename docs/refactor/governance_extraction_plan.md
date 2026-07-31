# Governance Extraction Plan — PhysicalRisk → MKM-ModelRisk

**Status:** PLAN ONLY — nothing has been executed. This document is the agreed design to review before any code moves.
**Date:** 2026-07-31
**Owner decision recorded:** governance becomes a **separately-distributed, gated/commercial capability** (MKM-ModelRisk). The open-source PhysicalRisk (`main`) runs **without** it; serious actors (e.g. a bank, Symphony) receive the ModelRisk drop-in that lights it up.

---

## 1. Goal & distribution model

- **PhysicalRisk (`main`)** stays **open-source (MIT)** and **fully self-sufficient without governance** — it boots, serves the map/trader/PRS UI, and passes its test suite with the governance files absent.
- **MKM-ModelRisk** owns the entire governance / model-risk capability (the "Regulatory Compliance" panel + tabs, the model-risk / full-audit / data-lineage docs generators, and the governance JSON datastore).
- **Governance is optional and gated:** present when the ModelRisk overlay is installed, absent otherwise. This lets you keep it exclusive and decide later *who* gets it.

### Distribution mechanism: overlay + `.gitignore`
1. ModelRisk holds the governance files **at the same repo-relative paths** as they occupy today (e.g. `src/routes/governance/…`).
2. A licensed actor **overlays** ModelRisk onto their PhysicalRisk checkout (files land at those same paths — see §6 for *how* the files get there).
3. PhysicalRisk **`.gitignore`s those paths**, so the OSS repo neither tracks nor ships them, and an overlaid checkout stays clean (`git status` shows nothing).
4. A small **seam** in shared files detects governance's presence and mounts it; when absent, `main` no-ops the governance wiring.

> **Future evolution (not now):** the same seam supports repackaging ModelRisk as a private `pip`-installable package with entry-point discovery. The overlay mechanism is the pragmatic first step; the seam is what makes either delivery work.

---

## 2. Two categories (the core principle)

| Category | Mechanism | Examples |
|---|---|---|
| **A. Governance-EXCLUSIVE files** | **`.gitignore` + move to ModelRisk** | `src/routes/governance/`, `src/static/js/governance/`, docs generators, gov tests |
| **B. SHARED integration points** | **Seam (conditional load)** — CANNOT be gitignored | blueprint registration, panel mount, preloader datasets, audit pipeline, model-audit writer |
| **C. Data / datastore** | **Move JSON datastore** (no DB) | `docs/models/governance_data/*.json` |

Only **A** is gitignore-able. **B** is the risk surface — those lines live inside files `main` needs regardless.

**Two findings that simplify everything:**
- Governance persistence is **JSON files, not a database** → **no DB tables/migrations to extract**.
- RBAC is **not coupled** to governance (`Func000–Func003` are admin/portfolio/trade) → **no auth changes**.

---

## 3. LIST A — Governance-exclusive paths (move to ModelRisk + `.gitignore`)

```gitignore
# --- Governance / model-risk capability (owned by MKM-ModelRisk) ---
src/routes/governance/
src/static/js/governance/
src/static/js/modelgovernance-panel.js
src/static/js/mg-bcbs239.js
src/static/js/mg-audit-reports.js
src/visual/interactivity/governance/
docs/models/model_risk/
docs/models/full_audit/
docs/models/data_lineage/
docs/models/governance_data/     # extends the partial coverage already present
docs/models/bcbs239/
docs/models/mrc_tor/
docs/models/init_audit/          # VERIFY governance-only before moving (see §8)
tests/routes/governance/
tests/e2e/test_gov_*.py
tests/e2e/test_governance.py
```

Notes:
- `src/routes/governance/**` — entire dir (blueprint, MRC CRUD ×6, mrc_pdf, audit, audit_reports, bibliography, compliance, documents, models, test_report, `_constants.py`, `_helpers*`, `lineage/`).
- `src/static/js/governance/**` — entire dir (`mg_*` + `models/`, `mrc/`, `raci/`) plus the 3 top-level files above.
- `src/visual/interactivity/governance/**` — entire dir (`ModelGovernancePanel`, `mg_*` splices, `models/`, `mrc/`, `raci/`).
- `docs/models/json_files/` and `docs/models/database_usage/` are **general** model-doc utilities → **NOT** governance, leave in PhysicalRisk.

---

## 4. LIST B — Shared seam points (stay in PhysicalRisk; make governance-optional)

**Recommended approach: one capability signal, not scattered try/except.** Backend probes whether governance is importable once at startup and exposes a capability flag; each seam gates on it. (Per-seam `try/except` is the fallback if a unified flag is over-engineering for the first pass.)

```python
# proposed: config/capabilities.py (open-source; ships in main)
def governance_present() -> bool:
    import importlib.util
    return importlib.util.find_spec("routes.governance") is not None
```
Inject the same flag into the page (e.g. `window.__CAPABILITIES = {governance: <bool>}`) so the frontend seams can read it.

### The 5 must-fix seams (would break the OSS build)

**B1 — Blueprint registration** · `src/routes/registry.py:34,57`
```python
# before: from .governance import governance_bp ; app.register_blueprint(governance_bp, ...)
if governance_present():
    from .governance import governance_bp
    app.register_blueprint(governance_bp, url_prefix="/api/v1")
```

**B2 — "Regulatory Compliance" panel mount** · `src/visual/interactivity/manager.py:45,80,101` (+ `__init__.py:59,75`)
```python
# optional import; skip mount when absent
try:
    from .governance.modelgovernance import ModelGovernancePanel
except ImportError:
    ModelGovernancePanel = None
...
if ModelGovernancePanel is not None:
    self.model_governance = ModelGovernancePanel()
    self.model_governance.add_to_map(folium_map)
```
(The Leaflet toolbar button itself is created by `mg_main_setup.js` — a LIST A file — so it simply isn't loaded when governance is absent.)

**B3 — `test --audit` doc generators** · `app/commands/test/audit.py:111-113`
```python
# filter the three governance generators to those importable
_GOV_GENERATORS = [
    ('data lineage report (BCBS 239)', 'docs.models.data_lineage'),
    ('model risk governance report',   'docs.models.model_risk'),
    ('full audit report',              'docs.models.full_audit'),
]
generators = [(n, m) for (n, m) in _GOV_GENERATORS if importlib.util.find_spec(m)]
```
Also gate `app/commands/test/lineage.py` (`_run_data_lineage_tests`) + its wiring in `command.py:29,32,113-114` so `--lineage`/`--audit` no-op governance pieces cleanly. (`phys.py:44-48` help text can note the audit package is governance-gated.)

**B4 — Startup preloader datasets** · `src/static/js/startup.js:108-139`
Make the four governance rows conditional on the capability flag:
```js
// _tdPreGovDocs, _preGovAudit, _preGovBib, _preAuditReports
var _startupDatasets = _baseDatasets;
if ((window.__CAPABILITIES || {}).governance) _startupDatasets = _startupDatasets.concat(_govDatasets);
```
(Also the var-inits at lines 28,30,31,35 and `_startupDetail` cases 132,134,135,139 — leave inits, they're harmless nulls; just don't fetch.)

**B5 — Model-audit writer (the tricky one)** · `src/models/audit.py:86-91`
Ordinary model execution (pricing, generation, hazard) writes `model_audit_log.json` into `config.get_governance_data_dir()`. When that dir is gitignored/absent the writer must tolerate it:
```python
def _get_audit_path():
    d = config.get_governance_data_dir()
    if not os.path.isdir(d):
        return None          # governance absent → skip audit-log emission
    ...
# callers: if path is None, no-op the write
```
Callers to check (non-governance): `src/port/rand/shared/property/property_valuation.py`, `src/port/src/property/hc/pricing/_process.py`, `src/port/src/property/ts/generator.py`, `src/port/src/gauge/gaugehd/synthetic.py`, `src/routes/propertyts/risk.py`, `src/routes/gauges/hazard.py`.

### Lower-risk seams
- **B6 — model-registration checklist** · `docs/models/new_model.md:9-15,97` documents adding to `model_inventory.json`. Reword to "if governance is installed." Cosmetic.
- **B7 — e2e conftest** · `tests/e2e/conftest.py` sets `MKM_GOVERNANCE_DATA_OVERRIDE` + copies a tmp governance dir. Make the governance fixture skip when governance is absent (the gov e2e tests are LIST A and won't be collected anyway).
- **B8 — config accessors** · `config/path/_config_paths.py:102-118` and `config/path/_portfolio_paths.py:216-234` (`get_governance_data_dir()`, incl. `MKM_GOVERNANCE_DATA_OVERRIDE`) — **stay** in main (shared config); they just point at the now-optional dir.

### Explicitly NOT moved
- **`src/lineage/**`** — shared pipeline plumbing consumed by BOTH governance and the port/test pipeline (`app/commands/port/orchestrator.py:65-66,178`, `context.py:87`, `pdf_reports.py:58`, `command.py:32`). Governance only *reads* its output (`data/data_lineage.json`, `data/field_lineage_registry.json`). **Stays open-source**; ModelRisk's lineage routes import it.

---

## 5. LIST C — Data / datastore

- **No DB tables, no migrations.** Governance state is JSON under `docs/models/governance_data/` (paths declared in `src/routes/governance/_constants.py:35-43`):
  `model_inventory.json`, `model_audit_log.json` (already gitignored), `mrc_meetings.json` + `mrc_uploads/`, `bcbs239_assessment.json`, `raci_matrix.json`, `bibliography.json`, `governance_documents.json` + `governance_docs/`.
- The whole dir moves to ModelRisk and is gitignored in PhysicalRisk (extends existing `.gitignore:24-29`).
- One config knob relocates the datastore: `config.get_governance_data_dir()` with `MKM_GOVERNANCE_DATA_OVERRIDE`.
- **Stay in `data/` (shared):** `data/data_lineage.json`, `data/field_lineage_registry.json` — pipeline outputs, not governance-owned.

---

## 6. How the overlay reaches the working tree (open design decision)

Governance dirs are **scattered** (routes, static/js, visual, docs, tests), so a single git submodule is awkward. Options for delivery to a licensed actor:

| Option | How | Trade-off |
|---|---|---|
| **Sync script** ⭐ (first step) | `scripts/governance-overlay.sh` rsyncs/symlinks a ModelRisk checkout into PhysicalRisk at the mapped paths | Simple, transparent; actor runs one command. Symlinks keep it live-editable. |
| **Private pip package** (evolution) | ModelRisk ships as `mkm-governance`; a post-install step drops files, or the seam imports from the installed package instead of same-path files | Cleanest long-term; needs the seams to import from the package namespace, not just detect files |
| **Multiple submodules** | one submodule per governance dir | Ugly, brittle — not recommended |

**Recommendation:** ship the **sync script** now (overlay + gitignore), and keep the door open to the pip-package once actors are committed. ModelRisk's internal layout should mirror PhysicalRisk's paths so the overlay is a straight path map.

---

## 7. Phased execution plan (when approved)

> All phases keep `main` green. Each ends with the OSS-build-safety check (§8).

- **Phase 0 — ModelRisk repo skeleton.** Create the private MKM-ModelRisk repo mirroring PhysicalRisk paths; add its own licence/headers; add the overlay sync script + path map.
- **Phase 1 — Build the seams in `main` (governance still in-tree).** Add `governance_present()` + capability flag; convert B1–B8 to conditional. Verify `main` still works *with* governance present (no behaviour change yet).
- **Phase 2 — Prove absence.** Temporarily hide the governance dirs (or point the capability flag false) and run the OSS-build-safety check — `main` boots, serves, and its non-governance suite passes. Fix any missed seam.
- **Phase 3 — Move.** Copy LIST A + LIST C into ModelRisk; wire the overlay so an overlaid checkout reproduces today's behaviour (governance e2e/unit run *in ModelRisk's* CI).
- **Phase 4 — Delete from `main` + gitignore.** Remove LIST A/C from PhysicalRisk, add the `.gitignore` block, commit. `main` is now governance-free OSS.
- **Phase 5 — Distribution.** Document the actor onboarding (clone ModelRisk → run overlay script → governance lights up). Decide exclusivity/licensing terms.

---

## 8. OSS-build-safety checklist (the definition of done for `main` without governance)

With governance absent, all of these must hold:
- [ ] `python phys.py server` boots; `/visualization` renders the map (no "Regulatory Compliance" button).
- [ ] `python phys.py config` / `check` run clean.
- [ ] `python phys.py test --e2e` collects **no** `test_gov_*` and passes (the current governance e2e reds disappear by removal).
- [ ] `python phys.py test --unit` passes (no import of governance modules).
- [ ] `python phys.py test --audit --pdf` runs and **skips** the 3 governance generators gracefully (produces the non-governance audit artefacts).
- [ ] Port generation (`phys.py port`) runs — model-audit writes no-op cleanly (B5).
- [ ] No `ImportError`/404 in server logs referencing governance.
- [ ] `git status` is clean on an overlaid checkout (gitignore correct).

---

## 9. Risks & open questions

1. **B5 model-audit coupling** — the highest-risk seam: non-governance model code emits governance audit events. Confirm every caller no-ops on a `None` path (§4 B5 list).
2. **`docs/models/init_audit/`** — VERIFY it's governance-only before moving (agent flagged it as "likely"); `report.py` referenced `model_risk`.
3. **Overlay delivery** — confirm sync-script vs pip-package for v1 (§6).
4. **Docs cross-references** — many `.md`/`.tex`/`.py` mention `model_inventory` / governance in prose; harmless, but decide whether to scrub OSS docs of governance references or leave them as "available in the commercial module."
5. **`test --audit` identity** — with governance gone, "full audit evidence package" in `main` is the non-governance subset. Confirm that's the intended OSS story (the *full* audit remains a ModelRisk deliverable).
6. **Exclusivity trigger** — the mechanism supports gating now; the *decision* of when/who is exclusive is yours (post-actor-identification), and needs no further code beyond keeping ModelRisk private.

---

## 10. Summary

- **Gitignore + move:** LIST A (whole governance trees) and LIST C (JSON datastore).
- **Seam (not gitignore):** LIST B — 5 must-fix (`registry.py`, `manager.py`, `audit.py`, `startup.js`, `models/audit.py`) + 3 minor.
- **No DB migrations, no RBAC changes.** `src/lineage/**` stays open-source.
- **Delivery:** ModelRisk overlay at same paths + a sync script; PhysicalRisk gitignores the paths; capability seam lights it up when present.
- Net: `main` is clean OSS that runs without governance; ModelRisk is the gated capability you hand to serious actors.
