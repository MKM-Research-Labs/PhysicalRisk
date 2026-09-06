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

---

# Part 2 — Getting JavaScript coverage from 2.71% to a defensible number

**Revised 2026-09-01**, after the governance removal and after correcting a
measurement bug of my own making.

## A. Where we actually are

| | Value |
|---|---:|
| Served JS modules | **130** (was 159; governance took 29) |
| Statements | **10,167** |
| Covered by unit tests | **276 — 2.71%** |
| Modules with unit tests | **4** |
| JS tests | 87, all passing |

⚠️ **A 57.86% reading was published in error.** The `roots` fix in `eb0925ef`
scoped jest discovery to this checkout, and `collectCoverageFrom` only resolves
within `roots` — so the denominator collapsed to the 477 statements the tests
already import. Fixed in `712c821a`. **Never quote a coverage percentage
without checking the denominator is the whole shipped surface.**

The rise from 2.06% to 2.71% is *not* progress: the numerator never moved. It
is 3,218 statements of governance JS leaving the denominator.

## B. Why "99% like Python" is the wrong target for JS

At the current density — 87 tests covering 276 statements, ~3.2 statements per
test — reaching 99% by unit tests alone implies roughly **3,000 more tests**.
That is a multi-month programme, not three weeks, and much of it would be
low-value: jsdom cannot meaningfully exercise Leaflet map rendering, Chart.js
canvases, or the Folium console's inline bootstrap.

**The number that matters is what the whole suite exercises, not what jest
exercises.** The e2e suite drives a real Chromium over the real front end, so a
large share of those 130 modules already executes on every run — and none of it
is counted. The Phase 0 collector (built, `11136c30`) measures exactly that and
**has still never been run**.

So the target is a **combined measured figure** — jest plus e2e, unioned — with
a ratchet, not a fixed 99%.

## C. Plan

### Phase 0 — take the measurement (free, this run)
Run the suite with the collector armed:

```
MKM_E2E_JS_COVERAGE=1 python phys.py test --all --audit
python -m docs.models.js_coverage.report
```

Everything downstream is sized off that number. Expect it to be far above
2.71%; the useful output is the ranked list of modules **no test touches at
all**.

### Phase 1 — put JS in the test command (the explicit ask)
1. A `js` phase in `app/commands/test/`, running jest with coverage, gated on
   `node_modules` being present (skip cleanly, like the playwright preflight).
2. Emit `audit/js/js_coverage.json` + the jest JUnit XML, and add both to
   `artefacts.py` under the new phase so the freshness gate covers them.
3. Merge the jest and e2e figures into one reported number.

### Phase 2 — ratchet, never a cliff
Set `coverageThreshold` just under the *measured combined* figure and raise it
per tranche. A 99% gate on a 2.71% baseline gets switched off within a week;
a ratchet that can only go up never regresses and always tells the truth.

### Phase 3 — close the gap by risk, not by percentage
Work the never-touched list from Phase 0, in this order:

1. **Modules with money or trade state** — the PRS pricers, blotter, commit
   paths. `commitPRSTrade` and `commitPropertyPRSTrade` still have no test of
   any kind.
2. **Pure-logic modules** — formatters, mappers, calculators. Cheap in jsdom,
   high statement yield per test, no DOM needed.
3. **Panel render paths** — assert structure, not pixels.
4. **Leave alone**: Leaflet/Chart.js rendering internals, the Folium inline
   bootstrap. e2e covers these better than jsdom ever will; unit-testing them
   is how a coverage push turns into theatre.

### Phase 4 — the five uninstrumentable files

**Step 1 — excluded explicitly. Done 2026-09-06 (jest.config.js).**
`propertysa.js` and the four `loanpricer/template/_part*.js` now sit in
`coveragePathIgnorePatterns`, with the reason recorded at the exclusion.
Verified numerically inert before the change: `coverage-summary.json` listed
125 files and 10,217 statements and contained none of the five, so babel had
already been dropping them. The reported 12.04% and the ratchet in
`config/js_coverage.py` are unchanged. What it buys is ~400 lines of stack
trace off every run, and an exclusion that is deliberate and documented rather
than accidental.

**The diagnosis was more specific than "embedded HTML parses as JSX."** These
files are not JavaScript at all — they are Python format-string templates with
a `.js` extension. `_part1.js` opens with a literal `<script>` tag, escapes
every brace as `{{ }}`, and carries `{panel_width}`-style placeholders;
`propertysa.js` uses `__PANEL_W__` sentinels. `js_static()` reads them and
`.format()` substitutes before injection. So teaching the loader to emit whole
modules would not be enough on its own: the placeholders are the blocker, and
they would still have to go.

**Step 2 — make them real JavaScript. Not started, and it is the only step
that removes the blind spot.** Placeholder values move to runtime: the panel
reads them off `window` (alongside the existing `window.__BACKEND_CONFIG`)
instead of having them substituted at render time, and the `<script>` wrapper
moves to the injection site rather than living inside the fragment. That makes
all five parse, instrument, and become testable.

Size and honesty: **~1,185 lines of live UI JavaScript** — the whole loan
pricer panel and property storm analysis — that no tool can currently measure.
Their statement count is itself unmeasurable until they parse, but the
direction is not in doubt: including them would carry mostly-uncovered code
into the denominator and **lower** the reported percentage. The number in the
audit package is therefore a ceiling on a smaller codebase, not a measurement
of all of it, and the ratchet should expect a one-off step down when this step
lands. That step down is a more honest number, not a regression — treat it as
a baseline reset rather than a gate failure.

These files originate in the no-JS-in-.py rule (see the coding rules): the
fragments were moved out of the Python modules correctly, but the ones holding
placeholders could not survive the move as valid JS. Any future extraction of
a parameterised fragment should take Step 2's shape from the start.

## D. What to tell a reviewer

The honest position, which is defensible: *back-end coverage is measured and
gated at 99%; front-end coverage is now measured for the first time, reported
in the audit package, and ratcheted upward each release.* That is a stronger
story than a large number nobody can reproduce — and it is the opposite of what
the 57.86% reading would have supported.
