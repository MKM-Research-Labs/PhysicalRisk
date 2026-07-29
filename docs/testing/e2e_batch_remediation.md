# E2E Remediation — Batches 1–2 (Thames) + Full-Test Run Handoff

**Date:** 2026-07-29
**Context branch:** `main` @ `d93f1c21` (the `app.py → phys.py` rename)
**Purpose:** Hand-off for a fresh session. Captures the full `phys.py test --all --audit --pdf`
run, the e2e batch status, and the remediation worklist for the failing e2e tests.

---

## 1. Where we are

- **`app.py` was renamed to `phys.py`** and every reference updated (117 files). Committed and
  **pushed to `main`** as `d93f1c21`. The CLI entry point is now `python phys.py …`.
- A full `python phys.py test --all --audit --pdf` run was started on the **thames** catchment
  (the default) in the **main checkout** (`/Users/newdavid/Documents/PhysicalRisk`), not the worktree.
- The run was **stopped deliberately mid-e2e-batch-3** so we could defer e2e batches 4–5 to
  tomorrow, generate the audit PDFs, and start e2e remediation on the completed batches.

### Results that DID complete (clean)
| Phase | Result |
|---|---|
| **Lineage** (BCBS 239) | **138 passed, 3 skipped** |
| **Unit** (`--ignore=tests/e2e`) | **12,093 passed**, 8 skipped, 6 xfailed, 2 xpassed (29m 39s) |
| **Coverage** | **99.11%** — above the 99.0% gate ✓ (core pinned to `ctrace`, so no Py3.13 sys.monitoring under-count) |
| **e2e batch 1** | complete (junit written) |
| **e2e batch 2** | complete (junit written) |

> None of the e2e failures below trace to the `phys.py` rename. The Flask server boots and serves
> every panel (verified live in-browser). These are pre-existing UI / data-state failures.

---

## 2. e2e batch structure (important)

The e2e runner (`app/commands/test/e2e.py`) splits **66 test files into batches of 15**, so **5 batches**.
Each batch is a separate pytest invocation writing `data/output/audit/e2e/e2e_junit_batch{N}.xml`.

| Batch | Status (this run) |
|---|---|
| 1 | ✅ complete — `e2e_junit_batch1.xml` (2026-07-29 15:49) |
| 2 | ✅ complete — `e2e_junit_batch2.xml` (2026-07-29 16:07) |
| 3 | ❌ **interrupted** — never wrote fresh junit (`batch3.xml` on disk is **stale from Jul 7**) |
| 4 | ⏭️ deferred to tomorrow |
| 5 | ⏭️ deferred to tomorrow (small — ~6 files) |

**Action for next session:** to get the full "batches 1–3" picture, **re-run batch 3 cleanly**
(fold it into the batch 4–5 run tomorrow, or run standalone ~12 min). The data below is
**batches 1–2 only**.

---

## 3. Remediation worklist — batches 1 & 2 (50 issues → 22 in-scope)

Grouped by **shared root cause**, not individual tests.

| # | Theme | Selector that times out | Count | In scope? |
|---|---|---|---|---|
| **A** | **Governance panel** setup timeout (`open_governance`, `helpers.py:307`) | governance tab locators | **28 (errors)** | ❌ **NO — governance is being removed** |
| **B** | **Map marker context menus** | `[class*='awesome-marker-…']` | 6 | ✅ |
| **C** | **Gauge/Blotter → Trading Desk** | `#hazard-blotter-link`, `#trading-desk-panel` | 6 | ✅ (core PRS-trader path) |
| **D** | **Property storm tabs** | `.prop-storm-tab[data-idx=…]` | 5 | ✅ |
| **E** | **Gauge panel tabs** | `.hazard-tab[data-tab='4'/'5']` | 3 | ✅ |
| **F** | **Commercial startup preloader** | `page.wait_for_function` | 2 | ✅ |

### Working hypothesis
Themes **B, C, D, E all time out waiting on map markers / popups / tabs**. This points to a
**single shared root cause**: markers/popups not initialising in the thames e2e data state
(consistent with the untrained-classifier / sparse-flood state observed live — empty FS01 grid,
"Classifier Not Available", 0/3 classifiers trained). Fixing that root cause likely clears B+C+D+E
together. **Recommended starting point**, and Theme C is the core PRS-trader path.

**Theme A is out of scope** — those 28 errors are all governance-panel tests
(AuditReports / BCBS239 / Bibliography / DataLineage / FieldLineage / MRC / RACI / Documents /
ModelWorkstream tabs). They will be deleted when the governance section is removed. Do not remediate.

---

## 4. Detailed failure list (batches 1 & 2)

### Theme B — Map marker context menus
- `test_context_menus.py::TestGaugeContextMenu::test_right_click_gauge_shows_menu` — timeout click `[class*='awesome-marker-…']`
- `test_context_menus.py::TestGaugeContextMenu::test_context_menu_has_items`
- `test_context_menus.py::TestGaugeContextMenu::test_context_menu_has_header`
- `test_context_menus.py::TestGaugeContextMenu::test_click_away_closes_menu`
- `test_context_menus.py::TestContextMenuNavigation::test_hazard_curve_item_opens_gauge_panel`
- `test_commercial_context_menu_part1.py::TestCommercialContextMenu::test_right_click_shows_commercial_menu` — `AssertionError: No context menu after right-click on commercial marker (count 0 > 0)`

### Theme C — Gauge/Blotter → Trading Desk
- `test_blotter_new_prs.py::TestBlotterNewPRSButton::test_04_new_prs_round_trip_back_to_blotter` — timeout `#hazard-blotter-link`
- `test_cross_panel_flows_part1.py::TestGaugeBlotterButtonState::test_blotter_button_click_opens_trading_desk` — timeout `#hazard-blotter-link`
- `test_cross_panel_flows_part1.py::TestGaugeBlotterFlow::test_gauge_panel_blotter_link_opens_trading_desk` — timeout `#trading-desk-panel`
- `test_cross_panel_flows_part1.py::TestFS01ToBlotter::test_fs01_tab_shows_risk_grid` — timeout `#trading-desk-panel`
- `test_gauge_panel.py / TestGaugePanelBlotterLink::test_blotter_link_opens_trading_desk` — timeout `#hazard-blotter-link`
- `test_gauge_prs_roundtrip / TestGaugePRSToBlotterRoundTrip::test_03_blotter_button_opens_td_filtered_to_gauge` — timeout `#hazard-blotter-link`

### Theme D — Property storm tabs
- `TestPropertyStormToPRS::test_02_prs_tab_opens_property_hazard_panel` — timeout `.prop-storm-tab[data-idx=…]`
- `TestPropertyStormToPRS::test_03_storm_flood_history_click_opens_timeline`
- `TestStormScenarioTabConsistency::test_distribution_and_history_show_same_flood_count`
- `TestStormScenarioTabConsistency::test_header_flood_count_matches_history`
- `TestStormScenarioTabConsistency::test_worst_storms_are_subset_of_history`

### Theme E — Gauge panel tabs
- `TestGaugePanelTabs::test_stress_tab_renders` — timeout `.hazard-tab[data-tab='5']`
- `TestGaugePanelTabs::test_historical_tab_renders` — timeout `.hazard-tab[data-tab='4']`
- `TestHistoricalTab::test_storm_scenarios_list_exists` — `AssertionError: Historical tab has no storm scenarios list or content`

### Theme F — Commercial startup preloader
- `TestStartupStatusPopupCommercial::test_preloader_cache_vars_populated` — `page.wait_for_function` timeout 20s
- `TestStartupStatusPopupCommercial::test_commercial_asset_names_in_property_names_lookup` — `page.wait_for_function` timeout 20s

### Theme A — Governance (OUT OF SCOPE, being removed) — 28 setup-timeout errors
AuditReportsTab (4), BCBS239PrincipleEdit (1), BibliographyExport (2), DataLineageTab (4),
DocumentUploadDownload (2), FieldLineageTab (4), MRCMeetingCRUD (3), MRCMeetingDetailUI (4),
ModelWorkstreamDetail (2), RACIMatrixInteraction (2). All fail in the `open_governance`
helper (`tests/e2e/helpers.py:307`) with a 10s locator timeout.

---

## 5. How to reproduce / environment

```bash
# From the MAIN checkout (mutating audit/self-heal must run in main, not a worktree)
cd /Users/newdavid/Documents/PhysicalRisk
source .venv/bin/activate          # Python 3.13; worktrees have no .venv — use main repo's

# Prerequisites (data lives on the external SSD; pg data dir is also on the SSD)
#   - SSD "David SSD" mounted (data/ -> /Volumes/David SSD/Docs/PhysicalRisk/data)
scripts/pg-native.sh start         # native Postgres :5432 (required or preflight aborts)
scripts/minio-native.sh start      # native MinIO :9000

# Full run (all suites + audit PDFs):
python phys.py test --all --audit --pdf

# Just e2e (all 5 batches):        python phys.py test --e2e
# Just the audit PDFs (no re-test): python phys.py test --audit --pdf
```

Notes:
- The **audit phase runs unconditionally after e2e** — e2e failures do NOT block PDF generation
  (`app/commands/test/command.py`, the `if do_audit:` block).
- e2e batch size / timeout: `BATCH_SIZE = 15`, `BATCH_TIMEOUT = 1800s` in `app/commands/test/e2e.py`.
- To stop a run cleanly, kill the **whole process group** (python + caffeinate + batch pytest +
  Playwright/Chromium + any orphaned `phys.py server`) — children orphan onto the SSD otherwise.

### Artifact locations
- Audit evidence + PDFs: `data/output/audit/` (on the SSD)
- e2e junit per batch: `data/output/audit/e2e/e2e_junit_batch{1..5}.xml`
- Coverage: `data/output/audit/coverage.xml`, `.../coverage/` (HTML)

---

## 6. Recommended next steps

1. **Skip governance (Theme A)** — will be deleted with the governance section.
2. **Investigate the shared root cause** behind Themes B/C/D/E: do the Leaflet map markers /
   popups actually render in the thames e2e state? Start with Theme C (Trading Desk link) since
   it's the core PRS-trader path. Likely fixes B+C+D+E together.
3. **Re-run e2e batch 3** to complete the "batches 1–3" set (defer 4–5 to a later run, or do all of 3–5).
4. Theme F (commercial preloader cache vars) is likely its own data/JS-init issue — check the
   startup preloader that populates the commercial asset-name lookup.
