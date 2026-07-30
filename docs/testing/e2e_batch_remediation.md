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

| Batch | Status (2026-07-29 run) | Files |
|---|---|---|
| 1 | ✅ complete — 18 failed, 52 passed, 10 skipped (`batch1.xml` 15:49) | 1–15 |
| 2 | ✅ complete — 4 failed, 51 passed, 28 errors (`batch2.xml` 16:07) | 16–30 |
| 3 | ❌ **timed out** at the 30-min batch limit — no fresh junit (`batch3.xml` stale Jul 7) | 31–45 |
| 4 | ✅ complete — (`batch4.xml` 16:48) | 46–60 |
| 5 | ❌ interrupted by the deliberate stop — no fresh junit (`batch5.xml` stale Jun 17) | 61–66 |

> **Correction (2026-07-30):** the earlier note that "batch 3 completed / batch 4 deferred" was wrong.
> Yesterday's log jumps from the batch-2 junit straight to the batch-**4** junit, so batch 4 finished
> and **batch 3 timed out** (it is heavy with the 60s marker/popup timeouts). Batch 5 was interrupted.

**Status 2026-07-30:** re-running **batches 3 and 5** directly (mirroring the runner's pytest
command, but with no 30-min kill so batch 3 can finish). Batch 3 is mostly PRS/property-lifecycle
tests (lifecycle_gauge_prs, lifecycle_property_prs, property_context_menu, property_panel_storm,
property_prs_decomposition, map_smoke, loan_calculator) — directly relevant to remediation.
The Theme table below is **batches 1, 2 (+4 once parsed)**; batch 3/5 failures will be added.

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

## 6. Recommended next steps (superseded by §7)

1. **Skip governance (Theme A)** — will be deleted with the governance section.
2. Re-run e2e batch 3 + 5 to complete the current-run set (done 2026-07-30).
3. See §7 for the grounded, root-cause-first plan.

---

## 7. Remediation plan (root-cause-first, evidence-backed 2026-07-30)

Investigated with three source dives. Findings changed the picture: it is **not** one shared
root cause. There is one big fixture-level cause (P0) plus several **genuine product bugs** in the
PRS-trader UI worth fixing on their own merits.

> **DONE 2026-07-30 — applied, verified, committed `7db56e7b`.** Targeted re-run of the
> previously-failing Theme D + F tests now passes (11 passed, 2 skipped in 3:58; the 120 s
> per-batch dead-wait is gone). Batch 5 (workflow suite) also ran clean **15/15** with P0.
> Batch 3 pre-P0 baseline: 53 failed / 53 passed / 15 skipped — feeds the residual themes below.

### P0 — Licence-gate overlay is never dismissed in the e2e session ⭐ do first (DONE)

**Root cause:** `_browser_page` (`tests/e2e/conftest.py:257-289`) loads `/visualization` and waits
for `window._tdPreloadDone===true`, but never accepts the licence gate. `license_gate.js:41-116`
creates `#license-gate-overlay` (`position:fixed; inset:0; z-index:10000`) that (a) intercepts every
non-`force` `.click()`, and (b) gates `_runStartupPreload` behind its **Accept** handler
(`startup.js:248-260`) — so the preloader never runs, `_tdPreloadDone` never flips, the wait burns
its full **120 s** every batch, then falls through with the overlay still up and no data preloaded.

**Fix** (`tests/e2e/conftest.py`, after the `.leaflet-container` wait, before the preload wait):
```python
gate = page.locator("#license-gate-overlay")
if gate.count() > 0:
    page.locator("#license-gate-overlay button:has-text('Accept')").click(timeout=10_000)
    page.wait_for_selector("#license-gate-overlay", state="detached", timeout=10_000)
```
**Clears:** Theme D (all), Theme E `TestGaugePanelTabs` (2), Theme F (both) — and removes the 120 s
dead wait per batch (major speed-up). **Partially helps** Theme B gauge right-click (removes the
overlay intercept). Does **not** fix Theme C (see C1/C2) or the Theme B viewport bug (B2).

### Theme B — Map marker context menus (residual after P0)

> **B2 DONE 2026-07-30 — committed `d85517d5`, verified.** Fixed `_extract_coordinates`
> (canonical `extract_gauges()` + commercial branch) so the map frames gauges + commercial, not
> just properties; 4 new unit tests, visualizer suite 52 passed. Framing the whole portfolio packed
> Hanoi's markers tightly enough that the commercial context-menu e2e then hit an *overlapping
> property* marker — fixed test-side by dispatching `contextmenu` on the commercial marker element
> (bypasses pixel hit-testing). Commercial context-menu e2e: 3 passed / 0 failed.
>
> **B1 DONE 2026-07-30 — committed `0341cf02`, verified.** Gauge context-menu tests switched from
> actionability-checked `.click(button='right')` (timed out on overlap) to a `dispatch_event`
> contextmenu helper; the navigation test now targets a gauge marker (`i.fa-tint`) so "Physical
> Risk Swap" opens the gauge panel. Gauge context-menu e2e: 5 passed / 0 failed. **Theme B complete.**

- **B1 (test):** `test_context_menus.py:73` right-clicks via `markers.first.click(button="right")`
  (actionability-checked) → flaky on dense/overlapping halong markers even without the overlay. Fix:
  use `bounding_box()` + `page.mouse.click(cx, cy, button="right")` (the pattern
  `test_commercial_context_menu_part1.py:94-100` already uses), or `force=True`.
- **B2 (PRODUCT BUG):** `coordinator._extract_coordinates()` (`src/visual/.../coordinator.py:165-188`)
  reads gauge coords from the wrong schema (`items` / `Location.GaugeLatitude`) while halong uses
  `flood_gauges` / `SensorDetails.GaugeInformation.GaugeLatitude`, **and ignores commercial coords
  entirely**. `fit_bounds` therefore frames *properties only* → commercial markers can render
  off-screen → coordinate right-click misses → "0 menus". Fix: correct the gauge key/path and add a
  commercial-coords branch. This is a real UX bug (map doesn't frame gauges/commercial), not just a test.

### Theme C — Gauge Blotter → Trading Desk (mostly its own product issues; core PRS path)

> **DONE 2026-07-30 — committed `9c489b02`, verified.** Theme C blotter/trading-desk e2e:
> 9 passed / 0 failed (incl. the muted-when-no-trades case). **C1 needed no change** — the P0
> startup preload loads all `_tdPre*` datasets and sets `_tdPreloadDone`, so the desk opens
> immediately (the 8-fetch `_tdRunPreload` gate is only hit when preload hasn't run). **C2 fixed:**
> fail-open in `panel_data.js` (honors `blotter.py:154`'s contract) + `first_traded_gauge_id`
> re-sourced from `/active-gauges`. No Python / unit-tested code changed.

- **C1 (PRODUCT):** first-open of `#trading-desk-panel` is gated on **8 preload fetches + 400 ms**
  (`trading/preloader.js:139-182`, `panel_lifecycle.js:21-39`); tests wait only 5 s
  (`test_cross_panel_flows_part1.py:117`) → timeout when stress/portfolio-storm/EOD endpoints are slow.
  Fix: open the panel + show the blotter tab from `_tdPreBlotter` immediately, lazy-load heavy datasets per tab.
- **C2 (PRODUCT + test):** the `#hazard-blotter-link` button is created **disabled**
  (`gauge/gaugehc/panel_create.js:82-99`) and only enabled if the gauge ∈ `/api/v1/trading/blotter/active-gauges`
  (`panel_data.js:57-69`), fetched **late** in the hazard/market await chain; `blotter.py:154` `raise`s
  on error → 500 → `.catch` leaves it disabled. Worse, the fixture `first_traded_gauge_id`
  (`conftest.py:365-389`) derives "traded" from the **PRS file `Header.TradeStatus`** while the backend
  uses **trade-marks** — divergent, so the button is disabled for the very gauge the test selects.
  Fix: enable the button early + **fail-open** on `active-gauges` error; align the fixture's "traded"
  definition with the backend; tests wait for `#hazard-blotter-link:not([disabled])` then non-force click.

### Theme D — Property storm tabs → **fixed by P0** (plain `.click()` under the overlay). Verify after P0.

### Theme E — Gauge panel tabs

> **E1 DONE 2026-07-30 — committed `08c0f12c`, verified. Theme E complete.** `switchTab` no longer
> gates the Historical (4) / Stress (5) tabs behind `hazardData` — they fetch their own data and
> resolve the gauge id via a shared `_ghcGaugeId()` helper (falls back to the panel `dataset.gaugeId`),
> so they render even when the hazard-curve fetch returns nothing. Fixed the real UX (blank tabs for a
> gauge with no curve) as well as the test. e2e: 10 passed / 1 skipped (Historical + Stress +
> TestGaugePanelTabs); cross-IIFE JS tests 74 passed.

- `TestGaugePanelTabs::test_stress_tab_renders` / `test_historical_tab_renders` → **fixed by P0** (plain clicks).
- **E1 (residual):** `TestHistoricalTab::test_storm_scenarios_list_exists` already force-clicks
  (`helpers.py:215`); it fails on content because `switchTab(4)` returns early when `hazardData` is null
  (`panel_nav.js:54`) → `renderHistorical` never writes the "Flood Storm Scenarios" scaffold. `hazardData`
  is null when `/api/v1/gauges/<id>/hazard` fails (likely untrained GBM classifiers for halong). Fix:
  seed/train classifiers for the test gauge, **or** render the static scaffold even when `hazardData` is
  absent (`ghc_historical.js:25-73`).

### Theme F — Commercial startup preloader → **fixed by P0** (preloader now runs).

- **F1 (verify):** the assertions read `_preCommercial.count` (`test_...part4.py:240-244`); confirm
  `/api/v1/commercial` exposes a numeric `count` (vs `commercial_assets.length`) once the preloader runs.

### Execution order
1. **P0** (conftest licence-gate) — one change, clears D + E-tabs + F, big speed-up, unblocks B-gauge.
2. **C1 + C2** (Trading Desk open + blotter-enable) — core PRS-trader path; product fixes.
3. **B2** (coordinator fit_bounds) — real UX bug; **B1** test-click pattern.
4. **E1** (historical scaffold / classifier data), **F1** (response-shape verify).

### Genuine product bugs surfaced (fix on their own merit, PRS-trader-relevant)
- `coordinator._extract_coordinates()` frames only properties (gauges wrong-schema, commercial ignored) — **B2**
- Trading Desk panel blocks on full 8-fetch preload before showing anything — **C1**
- Gauge-blotter enable is late + fails-closed on error; "traded" defined two different ways — **C2**

> Batches 3 + 5 (re-run 2026-07-30) add instances to the **same themes** (batch 3 = property/gauge
> lifecycle → C/D/E; batch 5 = workflow → C). Fold their failures into the themes above.
