# UI test coverage — closing the front-end evidence gap

**Status:** proposed, 2026-08-31 · **Driver:** IT review, ~2–3 weeks ·
**Focus:** test evidence / coverage reports, and change control.

## 1. Why

The back end is measured and gated; the front end is neither. We have just
rewritten colour and size values across all 159 served JS modules
([theme centralisation](theme_centralisation_plan.md)), which makes an
unmeasured front end the most exposed part of the estate.

## 2. Baseline, measured 2026-08-31

| Metric | Python | JavaScript |
|---|---:|---:|
| Modules shipped | — | 159 |
| Modules under unit test | — | 4 (2.5%) |
| Tests | 12,386 | 87 |
| Statement coverage | ~99% (gated) | **2.06%** (276 / 13,385) |
| Branch coverage | — | 1.95% (175 / 8,952) |
| Function coverage | — | 2.74% (48 / 1,751) |
| Coverage configured | yes, `fail_under = 99` | **no** |

E2E interaction surface (`pytest tests/e2e`, 420 tests / 66 files):

| Surface | Total | Named by e2e | Coverage |
|---|---:|---:|---:|
| `window.*` entry points | 52 | 18 | 35% |
| `onclick` handler functions | 32 | 10 | 31% |
| Element IDs | 388 | 124 | 32% |

Caveat carried into every report of these numbers: name-matching **overstates**
(a mention in a comment counts) and **understates** (a test can click a control
without naming its id). They are a lower bound on attention, not a coverage
measurement. §4.10 must count asserted interactions before it is shown to a
reviewer — a metric that flatters itself is worse than no metric.

## 3. Defects found while establishing the baseline

| # | Defect | Impact |
|---|---|---|
| D1 | `tests/js/jest.config.js` sets `rootDir: '../../'` with `testMatch: ['**/tests/js/**/*.test.js']`, so jest collects test files out of `.claude/worktrees/` | `npm test` runs 306 tests from unrelated branches instead of 87; red/green is meaningless |
| D2 | 4 pre-existing JS test failures (`backend-handler` ×3, `context-menus` ×1) | Stale expectations — e.g. asserts `http://localhost:5013/health`, code uses relative `/health`. **Not** theme-related; confirmed failing on pre-theme worktree code |
| D3 | 5 served files cannot be instrumented — babel reads embedded HTML as JSX | `propertysa.js` + 4 `loanpricer/template/_part*.js`. These are concat **fragments** from the JS-300-line split, not standalone modules; they distort any denominator |
| D4 | No runtime verification that a `var(--token)` written into an inline style resolves | A typo'd token does not error — it silently inherits. This is the theme change's live exposure |
| D5 | e2e results do not gate CI, and bare `pytest tests/e2e` produces no artefacts | Nothing enforces or evidences the front end |

## 4. Plan

### Phase 1 — make it measurable (week 1)
1. Fix **D1** (scope `testMatch` to the checkout) and **D3** (exclude concat
   fragments from `collectCoverageFrom`, or teach the loader to emit whole
   modules). Without both, no JS number is trustworthy.
2. Turn on jest coverage with a **ratchet**, not a cliff: set
   `coverageThreshold` to just under today's real figure and raise it per
   tranche. A 99% gate on a 2% baseline gets switched off in a week.
3. Fix **D2** — 4 stale tests.

### Phase 2 — publish the metric (week 1–2)
4. `full_audit` **§4.10 UI interaction coverage**: entry points, onclick
   handlers and element IDs vs. what e2e *asserts*, emitted as a ranked
   backlog. Follows the established scanner → backlog → gate-at-zero pattern
   of §4.3, §4.5 and §4.8.
5. Feed §4.10 and the JS coverage figure into the test-interpretation PDF, so
   the trend is a standing artefact rather than a one-off answer.

### Phase 3 — close the highest-risk gaps (week 2–3)
6. **Runtime theme guard** (D4): per panel, fail on any unresolved
   `var(--token)` in an inline style and on any console error during open.
7. Backlog by risk, not alphabetically:
   `commitPRSTrade` / `commitPropertyPRSTrade` (trade booking, no e2e at all)
   → `LoanPricerPanel`, `PropertyDetailsPanel`, `RLoanDetailPanel`
   → the ~14 `td*` handlers (sort, filter, new trade, EOD PDF, P&L history).
8. Fire / seismic / wind peril tabs — the newest models, near-zero e2e
   presence. Hazard-Curve-tab independent-peril rows are untested; the PRS tab
   has 2 label-only tests and no numeric reconciliation.

### Phase 4 — change control (week 3)
9. e2e in CI via `phys.py test --e2e`, publishing JUnit + `e2e_results.json`.
10. Codify as a coding rule alongside R1–R5, so new UI ships with coverage.

## 5. What this does not claim

Full interaction coverage is not achievable in this window and is not the
right target. E2E catches a *dead panel*; it cannot catch a *wrong colour* —
420 tests contain ~15 style assertions. The theme change is defensible instead
because every colour resolves through one finite token table, which §4.8
already verifies statically across 1,456 files at zero violations. Phase 3.6
adds the runtime half of that argument. State this distinction plainly in the
review rather than implying e2e covers it.
