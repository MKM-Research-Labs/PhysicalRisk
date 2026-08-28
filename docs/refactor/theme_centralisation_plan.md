# Plan: centralising look and feel into `config/theme`

**Status:** PLAN ONLY — nothing has been executed.
**Date:** 2026-08-28
**Area:** `src/static/js`, `src/static/css`, `src/visual/`, `src/reports/`, `docs/models/`, `tools/cdm_property_editor/`, `config/`
**Precedent:** MKM-ModelRisk shipped this on 2026-08-22 (`docs/design/theme_config.md` there, steps 1–7 plus the generated PDFs). This document reviews what that work produced and states what replicating it in PhysicalRisk costs, where the two repos differ, and in what order to do it.

---

## 1. What ModelRisk built

The driver there was an ERM vendor cloning the platform into their own suite: their visual
language is close but not identical, so every brand value had to be changeable without
forking code. The shape they landed on has six parts.

| Part | File | What it does |
|---|---|---|
| One source of truth | `config/theme.py` (286 lines, ~90 tokens) | Every colour, type size, spacing step, radius and shadow, grouped (`BRAND`, `SURFACE`, `TEXT`, `RAG`, `STATE`, `HUE`, `GRAPH`, `TYPE`, `SPACE`, `RADIUS`, `SHADOW`) and flattened into one `THEME` dict keyed by CSS custom-property name |
| CSS emitter | `src/web/_theme.py` → `GET /theme.css` | Serialises `THEME` as a `:root { --name: value; }` block, content-hash stamped, linked ahead of `app.css`. A route, not a checked-in file, so the values exist in exactly one place |
| JS emitter | `src/web/api_theme.py` → `GET /api/theme` | Serves `THEME` plus `STATUS_COLOUR_TOKENS` / `STATUS_COLOUR_DEFAULTS` |
| JS registry | `Theme` in `src/static/js/helpers.js` | `Theme.colour(domain, value)` / `.ref(token)` / `.value(token)`. Loaded in the same `Promise.all` as the existing `Policy` registry before first render |
| Document emitter | `config/reporting.py` + `src/governance/latex_style.py` | The LaTeX preamble's colours, fonts and page geometry derive from the same dict, so a report and the screen it came from cannot disagree |
| The gate | `audit/styling.py`, rule **R10** | Three zero-tolerance checks in `python -m audit`, its own report PDF, three rows in the compliance summary |

Two design decisions carried most of the value, and both transfer directly.

**Status colour is a token name, not a colour.** Six maps in `helpers.js` held 27 entries
drawn in five colours — six spellings of one vocabulary, one of them already half-converted
by hand. They collapsed into a single `STATUS_COLOUR_TOKENS` table in config that names a
*token* per value. An adopter recolours by editing the token and re-maps by editing the
table; no `.js` file names a colour.

**The undefined-token check matters more than the literal check.** A colour literal is
visible in a diff. A `var(--token)` naming a token that does not exist is not: the browser
drops the declaration in silence and the element renders with whatever it inherits, so a
rename reaches a screen as a colour quietly falling back — on whichever control nobody
happened to open. Both are gated; the second is the one that catches a partial adopter
theme.

### What it cost them

Roughly three days for the config module, the two emitters, the CSS conversion and the
audit rule; a further day or two of mechanical work for the JavaScript literals and the
inline scale; half a day for the PDFs. Their conversion surface was **75 CSS hexes, 190 JS
hexes, 493 inline styles, and a handful in Python**.

### Three traps they recorded

1. **SVG presentation attributes do not accept `var()`.** `fill="var(--accent)"` renders
   black, silently. Those sites need a CSS class, or the literal value via `Theme.value()`.
2. **Most inline styles are not colour — they are an undocumented scale.** Their `SPACE`
   scale had to be corrected from six rungs to a ten-rung 2px step *before* use, because
   the real markup reaches for every rung and a coarse scale would have forced half the
   sites to keep a literal.
3. **The typeface is a literal too.** They defined `--font` in step 1 and did not reference
   it until step 6; a rebrand would have stopped at the colours.

---

## 2. What PhysicalRisk has today

Scanned on `main` at 2026-08-28, excluding `data/`, `.venv`, `node_modules` and worktrees.
The pattern used is the same one `audit/styling.py` uses in ModelRisk.

| Surface | Size | Colour literals |
|---|---|---|
| `src/static/js/**` | 140 files with hits | **3,235** — and **2,346** inline `style="` attributes |
| `src/**/*.py` (visual, reports, routes, lineage) | 80 files with hits | **520** |
| `src/static/css/**` | 3 files | 19 |
| `src/static/admin/admin.html` | 1 file | 9 |
| `tools/cdm_property_editor/static/styles.css` | 1 file | **150** |
| `docs/models/**` (PDF generators) | 11+ files | 111 |
| `tests/**` | 20 files | 131 |
| **Total** | | **~3,940 literals, 214 distinct hex values** |

That is roughly **fifteen times** ModelRisk's conversion surface. The single biggest file
is `tools/cdm_property_editor/static/styles.css` (150); the biggest JS files are
`governance/mrc/mg_mrc_items.js` (105), `mg-audit-reports.js` (89) and
`governance/raci/mg_raci_dashboard.js` (86).

### The same drift, further along

The brand blue has forked exactly as it did in ModelRisk, at larger scale: **`#1976d2`
appears 248 times and `#1565c0` 122 times** in the JavaScript alone, and `#1565C0` again in
`docs/models/full_audit/_constants.py` as `BLUE`. Beyond the blue there are four reds
(`#c62828` 125, `#d32f2f` 84, `#f44336` 58, `#b71c1c`), four ambers (`#f57c00` 57,
`#e65100` 50, `#ff9800` 37, `#ffc107` 21) and three greens (`#2e7d32` 88, `#388e3c` 43,
`#4caf50` 20) — one vocabulary, spelled several ways, with no record of which spelling is
meant where.

### Thirty-six status maps, not six

ModelRisk collapsed six. A grep for `const|var|let <name>Colors` in `src/static/js` returns
**36** declarations: `tierColors`, `reviewColors`, `lifecycleColors`, `ragColors` (all four
in `governance/mg_helpers.js` alone), `rrColors`, `vqStatusColors`, `priorityColors`,
`statusColors`, `roleColors`, `triggerColors` (three separate, disagreeing definitions of
alert/warning/severe in `ghc_historical.js`, `trading/market/render.js` and
`curve_history.js`), plus a dozen Chart.js palette arrays.

### A partial home already exists — in the wrong package

`src/visual/utils/color_schemes/` (374 lines) holds `ColorSchemes` with
`FLOOD_RISK_COLORS`, `OPERATIONAL_STATUS_COLORS`, `LOAN_RISK_COLORS`,
`PROPERTY_TYPE_COLORS`, `STORM_INTENSITY_COLORS` and a gradient mixin. This is the direct
analogue of ModelRisk's `risk_policy/_defaults.py`: the right idea in the wrong place. It
is an **R1 violation** on its own — parameters in `src/` rather than `config/` — and
nothing in the JavaScript consumes it, so the flood-risk ramp is defined once in Python and
again, differently, in the front end.

### Two document surfaces ModelRisk did not have

ModelRisk's third emitter was a LaTeX preamble. Ours is bigger: **226 `colors.HexColor(...)`
call sites** across `src/reports/{property,trading,gauge,port}` and the `docs/models/**`
generators, with `docs/models/full_audit/_constants.py` holding a private palette
(`NAVY`, `STEEL`, `BLUE`, `LIGHT_BG`, `HEADER_BG`, `GREEN`, `AMBER`, `RED`, `GREY`) that
every audit PDF imports. Matplotlib figures are a third.

---

## 3. The architectural difference that shapes the whole job

ModelRisk is a conventional Flask app: one `index.html`, one `app.css`, static `.js` files
linked from the page. A `/theme.css` route inserted ahead of the stylesheet reaches
everything, and `/api/theme` is fetched once at boot.

PhysicalRisk does not work that way. Its console is a **Folium-generated page** whose
JavaScript and CSS are read off disk and *inlined* into the document —
`js_static()` / `css_static()` in `src/visual/interactivity/_jsbundle.py`, 314 call sites,
attached via `folium_map.get_root().html.add_child(folium.Element(...))`.

This is a difference in our favour, and it changes two things:

- **No fetch, no race.** The token block can be injected as a literal `<style>:root{…}</style>`
  and a `window.__THEME = {…}` object at page assembly time. ModelRisk needed an async
  `Theme.load()` with fallbacks for a failed fetch and a `Promise.all` ordering constraint
  before first render; we need none of that. The tokens are present before the first byte
  of any panel script.
- **One seam covers the console.** `InteractivityManager.setup_map_interactivity()` in
  `src/visual/interactivity/manager.py` already attaches every panel to the map root. One
  injection there themes the whole console. (Fittingly, the copyright banner hardcoded in
  that same method — `color:#555`, `rgba(255,255,255,0.85)`, `font-size:11px`,
  `font-family:Arial` — is itself four violations of the rule we are about to write.)

There are **three other surfaces** the seam does not reach, and each needs its own
injection point: `src/static/admin/admin.html`, the standalone
`tools/cdm_property_editor/` Flask app (port 5057, its own 838-line `styles.css`), and the
generated PDFs.

One trap transfers with a different vector. We have little raw SVG, but **Leaflet path
options and Chart.js datasets are JavaScript values, not CSS** — `color:`, `fillColor:`,
`backgroundColor:` will not resolve `var(--accent)`. Those sites take the literal value
from the injected `window.__THEME`, exactly as ModelRisk's heatmap took `Theme.value()`.

---

## 4. Proposed shape

### 4.1 `config/theme/` is a package from day one

R2 caps a file at 300 lines. ModelRisk's single `config/theme.py` reached 286 with ~90
tokens; 214 distinct colours plus the scales will not fit. Start as a package (R4 — the
`__init__.py` re-exports only):

```
config/theme/
  __init__.py     # re-exports THEME, THEME_GROUPS, STATUS_COLOUR_TOKENS, … only
  _palette.py     # BRAND, SURFACE, TEXT, RAG, STATE, HUE — the colours
  _scale.py       # TYPE, SPACE, RADIUS, SHADOW — the non-colour visual parameters
  _status.py      # STATUS_COLOUR_TOKENS, STATUS_COLOUR_DEFAULTS
  _domain.py      # flood risk, gauge status, loan risk, property type, storm intensity,
                  # peril and RAG ramps — the vocabulary migrated out of ColorSchemes
  registry.py     # THEME_GROUPS, the flat THEME dict, the emitter's view
```

Token names are the CSS custom-property name without `--`, so a token is spelled
identically in config, in the stylesheet, in the JS and in an adopter's override. No
translation layer to drift.

### 4.2 Emitters

1. **Console CSS** — `src/visual/theme_css.py` renders `:root { … }`; injected by
   `InteractivityManager.setup_map_interactivity()` as the *first* element on the map root,
   ahead of every panel's inlined CSS.
2. **Console JS** — the same call emits `window.__THEME = {tokens, status_colours,
   status_defaults}`, with a small `Theme` helper (`colour(domain, value)`, `ref(token)`,
   `value(token)`) in `src/static/js/theme.js`. Synchronous, so no load ordering.
3. **Admin + CDM tool** — the same `:root` block, injected into `admin.html` at render and
   into the CDM tool's page shell.
4. **Documents** — a `config/reporting.py` deriving reportlab `HexColor` constants from the
   palette, replacing `docs/models/full_audit/_constants.py`'s private one and the 226
   scattered `HexColor(...)` calls; plus matplotlib `rcParams` from the same source.

### 4.3 How an adopter overrides it

Same two tiers ModelRisk chose. Now: `THEME` ships as defaults, overridden by JSON at
`MKM_THEME=themes/<adopter>.json` — the same env-var shape as the existing catchment and
backend switches, so an adopter ships a theme file and never forks code. Later: an Admin
panel, once a second adopter asks. Not before.

---

## 5. Migration order

Sequenced so that each step ships on its own and nothing changes visually until it is meant
to. Steps 1–5 are the load-bearing work; 6–8 are mechanical and can follow at leisure.

| # | Step | Size | Why here |
|---|---|---|---|
| 1 | ✅ **Done** — `config/theme/` package + the token vocabulary + `:root` injection at the manager seam + `theme.js` | ~1.5 d | Nothing changes visually; the vocabulary now exists and reaches every console page |
| 2 | `ColorSchemes` → `config/theme/_domain.py`; `src/visual/utils/color_schemes/` reads from it | ~0.5 d | Small, removes an existing R1 violation, and single-sources the flood/gauge/loan/property ramps the Python and the JS currently disagree about |
| 3 | The 36 JS status maps → one `STATUS_COLOUR_TOKENS` table | ~1.5 d | The highest-value step: every badge on every screen inherits, and the three disagreeing alert/warning/severe maps become one |
| 4 | The four CSS files (169 literals) → `var(--…)` | ~0.5 d | Mechanical, easy to eyeball, includes the CDM tool's 838-line stylesheet |
| 5 | `audit/` styling scanner + rule **R7** + `full_audit` §4.8 + gate test | ~1 d | What makes all of the above hold. Gate CSS/HTML/Python at zero, *report* the JS backlog with a count so step 6's remaining work is visible instead of silently passing |
| 6 | The remaining JS colour literals (~3,000 across ~140 files) | 3–4 d | The bulk. Batched by area — governance, trading, storm, property, gauge — each batch ending green |
| 7 | The inline `style=` scale: 2,346 attributes — type, spacing, radius | 2–3 d | Lowest value, cosmetic consistency. Define the spacing scale from the *actual* frequency histogram first, per ModelRisk's step-6 lesson |
| 8 | The PDF and matplotlib emitters: 226 `HexColor` sites + `_constants.py` | ~1 d | Unblocks extending the R7 gate over `docs/models/` and `src/reports/` |

**Total ≈ 11–14 days.** Steps 1–5 (≈5 days) deliver the rebrandable console and the gate
that keeps it; the rest is volume.

Three ordering notes:

- **Step 5 before step 6, deliberately.** ModelRisk brought its audit rule forward for the
  same reason: the token set is a promise until something enforces it, and 3,000 conversions
  done without a gate will have drifted before they are finished.
- **Step 3 before step 6.** Collapsing the status maps removes several hundred literals as a
  side effect and settles the vocabulary the rest of the conversion refers to.
- **Do not batch step 6 by file size.** Batch by area, so each batch is one screen a person
  can open and compare.

---

### 5.1 Step 1, as built

144 tokens in 15 groups, all 144 reaching a rendered console page. 55 tests (44 pytest,
11 jest), 100% line coverage on both new Python modules.

```
config/theme/_palette.py   BRAND 9, SURFACE 15, TEXT 8, RAG 17, STATE 6, HUE 15
config/theme/_scale.py     TYPE 14, SPACE 14, RADIUS 7, SHADOW 4
config/theme/_domain.py    PERIL 4, DEPTH 5, MAP 13, SIGN 5, SERIES 8
config/theme/registry.py   THEME (flat), THEME_GROUPS (ordered), SANCTIONED_PACKAGE
src/visual/theme_css.py    theme_css() → :root block; theme_html() → <style> + <script>
src/static/js/theme.js     window.Theme.value/ref/has/reset
```

Four things were decided during the build that the plan had left open, and one thing the
plan got wrong:

**The scales were measured, not chosen.** §5's step-7 note said to build the spacing scale
from the real histogram; it turned out to be free to do it now, so the ladders in
`_scale.py` are the live frequency counts over `src/static` and `tools`. The type scale
steps 1px from 8 to 14 (10px×376, 11px×391) and the spacing scale steps 1px from 1 to 8
(8px×327, 6px×284, 4px×269, 2px×189) — neither is a designer's ladder, both are what a
dense analytics console converges on. A six-rung scale would have forced half the sites in
step 7 to keep a literal, which is exactly the correction ModelRisk had to make mid-flight.
Rungs used fewer than ~10 times are deliberately absent and stay literals.

**`--font` is a token from the outset.** ModelRisk defined it in its step 1 and never
referenced it, so a rebrand there still stops at the colours. `TYPE["font"]` has a test
holding it. The census also found the body face spelled three ways and the mono stack two,
which step 7 collapses.

**Token names are shared with ModelRisk** wherever the two mean the same thing — `accent`,
`panel`, `muted`, `line`, the RAG hues. The two products are meant to sit in one suite and
MKM-ModelRisk was extracted from this codebase; one vocabulary is what lets a single adopter
theme file brand both. PhysicalRisk-specific meaning lives in `_domain.py`, which ModelRisk
has no equivalent of.

**One payload, not two.** ModelRisk serves `/theme.css` and `/api/theme` separately because
its front end is fetched separately from its page. Ours is inlined at assembly time, so
`theme.js` reads the values back off the `:root` block with `getComputedStyle` and memoises
them. A second copy would buy nothing and could disagree with the first.

**What the plan got wrong.** §4.2 justified injecting first on the grounds that a token must
be defined before anything refers to it. That is not how custom properties work — they
resolve at computed-value time, so a `var()` in an earlier block finds a `:root` defined
later regardless. The real reason to inject first is the cascade: a panel that redefines a
token should override the theme, never the reverse. The comments in `theme_css.py` and
`manager.py` state it correctly; the ordering itself was right for the wrong reason.

### 5.2 Two things step 1 surfaced that the plan had not

**`config/` is outside the coverage gate.** `pyproject.toml` sets
`source = ["src", "tools/cdm_property_editor"]`, so nothing under `config/` is measured —
including `config/theme`, the package R7 makes the single source of truth for every pixel.
`config/theme` is at 100% when measured explicitly, but the gate would not catch a
regression in it. This predates the theme work and affects the whole config package; it
wants fixing before step 5 relies on the gate.

**The static-asset loader is in the wrong package.** `js_static` lives in
`src/visual/interactivity/_jsbundle.py`, but it is a generic reader with no interactivity
dependency of its own. `theme_css.py` is a sibling of `interactivity`, and importing the
loader at module scope closes a cycle — `theme_css` → `interactivity/__init__` → `manager`
→ `theme_css` — of exactly the kind the R2 Tier 1 work removed. It is currently a deferred
import inside `theme_html()` with a comment. The loader wants relocating a level up to
`src/visual/`, which is a small change touching many importers and belongs in its own
commit, not here.

## 6. Enforcement — rule R7

`docs/rules/coding_rules.md` currently runs R1–R6, so this is **R7 — every visual parameter
comes from `config/theme`**. It is a close sibling of the existing path-definitions audit
(`docs/models/full_audit/sections_tests/path_definitions.py` + the zero-tolerance gate in
`tests/commands/test_path_definitions_report.py`), and should be built the same way:

- a scanner package `docs/models/styling/` (`scanners.py`, `report.py`, `pdf.py`), matching
  the shape of `docs/models/path_definitions/`;
- a `_build_styling` section registered in `docs/models/full_audit/sections_tests/` as
  **§4.8**, joining copyright headers (4.2), path definitions (4.3), JSON files (4.5),
  database usage (4.6) and model chain (4.7);
- a gate test `tests/commands/test_styling_report.py`, zero-tolerance on the gated suffixes
  with the ungated backlog reported as a count.

Three checks, mirroring ModelRisk's:

1. No colour literal — hex, `rgb()`, `rgba()`, `hsl()` — outside `config/theme/`.
2. Every `var(--token)` referenced resolves to a token the theme defines.
3. No bare `RRGGBB` string in Python (ModelRisk found two colour literals that had escaped a
   `#`-anchored scan for months; ours has 226 `HexColor('#…')` sites and will have more).

Two scanner details worth copying rather than rediscovering: the regex needs a `(?<!&)`
lookbehind so HTML numeric character references (`&#9888;` — the warning sign) are not read
as colours, and a `(?![-\w])` guard so `#abc-panel` id selectors are not either. The Python
scan must be comment-aware — naming a colour while explaining why colours are not written
down must not itself be a finding.

**Scope knob.** A `STYLING_GATED_SUFFIXES` constant decides which suffixes gate and which
merely report, so step 6 can proceed in batches with the gate tightening behind it, and a
new asset type surfaces rather than being exempted in silence.

---

## 7. Other rules this work has to satisfy

- **R1** — the whole point: the parameters end up in `config`.
- **R2** — hence a package, not a file (§4.1).
- **R3** — ≥99% coverage: the theme package, both emitters, `theme.js` and the scanner all
  need tests. The load-bearing one, per ModelRisk, is *every `var(--…)` the front end reads
  resolves to a token that exists*.
- **R4** — `config/theme/__init__.py` re-exports only.
- **R5** — canonical copyright header on every new `.py` and `.js`.
- **No JS in `.py`** — the emitter writes a `<style>` block and a JSON object, and the
  `Theme` helper lives in `src/static/js/theme.js`. Note `_strip_inlined_header()`: an
  injected fragment's leading `//` header is stripped at inline time, and the token block
  must be injected in a form that survives that path.

---

## 8. What this buys

The same trade the database migration bought: the work costs days once, and every rebrand
after it costs an hour. Concretely, after steps 1–5 an adopter changes one
`themes/<company>.json` of roughly 40 values and the console matches their house style;
after step 8 the generated PDFs match it too, and a report can no longer disagree with the
screen it came from — which today it does, because the audit PDFs are drawn in `#1565C0`
and the console in `#1976d2`.

The secondary payoff is legibility. Four reds and four ambers with no record of which means
what is not a palette, it is an accident; naming them forces the decision of which
distinctions are real (an alert level *is* different from a risk rating) and which are
drift.

---

## 9. Deferred, recorded so the next pass is chosen rather than discovered

- **Runtime theming.** Env-var theme file first; an Admin › Branding panel only once a
  second adopter asks.
- **A validated theme contract.** A JSON Schema for `theme.json` so a partial adopter theme
  fails at start-up naming the missing token, rather than rendering half-branded. Cheap
  alongside check 2 of the gate.
- **Chart.js defaults.** ~15 palette arrays are chart series colours. A single categorical
  ramp in the theme, applied through `Chart.defaults`, would remove them all at once and is
  worth folding into step 6 rather than converting them one by one.
- **Map layer geometry.** `src/visual/layer/` carries marker radii, weights and opacities as
  inline numbers alongside its 33 colours. Same argument as the palette, same package.
