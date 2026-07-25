# Handover — unit test documentation

**Date:** 2026-07-24
**Repo:** `/Users/newdavid/Documents/PhysicalRisk`, branch `main`
**Status:** nothing committed. All work is in the working tree.

---

## 1. What this was

`app.py test --unit` runs ~11,000 tests. The question was whether a subset could be
aggregated into unit test documentation.

It could — the machinery already existed (`docs/models/test_results/generator/`,
which runs the suite and writes a per-model `test_results.tex` → `test_results.pdf`
into each `docs/models/<model>/`). The problem was that its test-to-model mapping
was 130 hand-maintained exact paths, 25 of which pointed at files that no longer
existed. Splitting a test file into `_part1`/`_part2` — routine here — silently
dropped those tests into the PLATFORM bucket, and the only symptom was a model's
documentation quietly getting shorter.

Two changes were agreed and are now done:

1. **Prefix/glob attribution rules** replacing the exact-path map.
2. **A reconciliation gate** that fails loudly when a rule stops resolving.

---

## 2. What changed

### New files

| file | what |
|---|---|
| `docs/models/test_results/generator/attribution.py` | Rule resolver, static collection walk, reconciliation |
| `tests/docs/test_model_attribution.py` | 19 tests covering the above |
| `tests/docs/__init__.py` | |
| `docs/models/trading_desk/` | New doc dir for MKM-TD-001 (Makefile only so far) |
| `docs/models/cdm_schema/` | New doc dir for CDM-ALL (Makefile only so far) |

### Modified

| file | what |
|---|---|
| `docs/models/test_results/generator/models.py` | `TEST_MODEL_MAP` → `TEST_MODEL_RULES`; doc dirs for TD and CDM |
| `docs/models/test_results/generator/collector.py` | Uses `model_for_path()` |
| `docs/models/test_results/generator/__init__.py` | Reconciles before running; `--reconcile-only`; returns an exit code |
| `docs/models/test_results/generator/__main__.py` | Propagates that exit code |
| `app/commands/test/helpers.py` | `_check_test_attribution()` |
| `app/commands/test/command.py` | Calls it as a preflight for `--unit` / `--audit` |
| `src/routes/governance/_constants.py` | `_MODEL_DOC_DIRS`: added TD and CDM |
| `docs/models/model_risk/data.py` | `_MODEL_DOC_DIRS`: added TD and CDM |
| `tests/commands/test_test_command_exit_code.py` | Stubs the new preflight; two new tests |

### Not mine — already modified when this started

`src/models/hazard/gev.py` and `tests/port/hazard/hazard_builder.py`. Left alone.

### How the rules work

A rule is either a directory prefix (`tests/models/seismic/`) or a filename glob
confined to one directory (`tests/models/typhoon/genesis*.py`). Resolution is
most-specific-first — file glob beats directory prefix, longer prefix beats
shorter — so the order they are written in doesn't matter. The glob form is what
absorbs `_part1`/`_part2` splits.

The gate fails on two conditions, both previously silent:

- a rule that claims no collected test file;
- a model with a documentation directory but no attributed tests.

---

## 3. Result

656 tests that were being lost are back on their models. Nothing moved model and
nothing that was attributed dropped to PLATFORM.

Counts from the real run (higher than static estimates because parametrised tests
expand at runtime):

| model | tests |
|---|---:|
| MKM-TC-001 Tropical Cyclone | 380 |
| MKM-TD-001 Trading Desk | 312 |
| MKM-BRI-001 Building Resilience | 223 |
| MKM-ST-001 Stress Test Pipeline | 125 |
| MKM-SI-001 Storm Intensity | 105 |
| MKM-SEIS-001 Seismic Resilience | 95 |
| MKM-GHD-001 GaugeHD Synthetic | 88 |
| MKM-PF-001 Property Flood Response | 88 |
| MKM-FIRE-001 Fire Resilience | 85 |
| MKM-SG-001 Storm-Gauge | 81 |
| CDM-ALL CDM Schema Validation | 77 |
| MKM-MP-001 Mortgage Pricer | 69 |
| *(15 others unchanged)* | |

Suite on the final run: **10,948 passed, 8 skipped, 6 xfailed, 2 xpassed,
0 failed**. (The first run showed 1 failure — see section 4.)

---

## 4. Verified

- `tests/docs/test_model_attribution.py` — 19 passed under the real conftest.
- `tests/commands/test_test_command_exit_code.py` — 7 passed.
- Gate checked in both directions: renaming `hazard_builder.py` to
  `hazard_builder_part1.py` still reconciles; renaming it to `hazard_bldr.py`
  exits 1 naming the dead rule and the model that lost its evidence.
- `ruff check` clean on all new and modified files.

One regression was found by the full run and fixed:
`test_returns_zero_without_a_unit_suite` failed because the preflight goes through
the same `subprocess.run` the test stubs, so the gate's verdict was tracking the
suite's return code. The fixture now stubs it explicitly.

---

## 5. Overnight regeneration — finished and verified

The full regeneration completed cleanly. **All 26 documents are current and
correct; nothing needs re-running.**

- **10,948 passed, 8 skipped, 6 xfailed, 2 xpassed, 0 failed** in 55m06s
- 26 `test_results.pdf` written
- Trading Desk 312 tests and CDM-ALL 77 — i.e. the doubled 624/154 from the
  earlier `--model` run are gone
- Spot-checked `MKM-TD-001`: 312/312 pass, 18 pages, correct title page,
  legal page and running headers

The 26 upload-named copies are also built:

```
docs/models/test_results/unit/test_unit_<MODEL_ID>.pdf
```

One flat folder, 26 files, 106–173 KB each. Item 6.2 below is therefore **done** —
it is recorded here because the constraint it describes still applies to any
future run.

---

## 6. Open items

### 6.1 `--model` double-collects — **fix this first**

Running the generator with `--model` collects every test twice. Evidence:

| model | full run | `--model` run |
|---|---:|---:|
| MKM-TD-001 | 312 | 624 |
| CDM-ALL | 77 | 154 |

Every row in the resulting LaTeX appears twice. Likely cause: `paths_for_models()`
returns explicit file paths, and files in the `_NON_PREFIXED_DIRS` registry get
collected once as a named argument and once via the `pytest_collect_file` hook in
`tests/conftest/collection.py`.

This is not new — it also explains the `(total: 32)` row against a 16-test file in
the GH-001 history table, written by an earlier `--model GH` run. So `--model`
runs have been producing doubled documents for a while.

Until it's fixed, **generate documents with a full run only**.

### 6.2 Package as `test_unit_<modelID>.pdf` — DONE, but re-run after any regeneration

`python -m scripts.package_unit_pdfs` (from the repo root). It copies each `docs/models/<dir>/test_results.pdf` to
`docs/models/test_results/unit/test_unit_<MODEL_ID>.pdf` — 26 files, one flat
folder, easier to select for upload.

`test_results.pdf` must stay where it is under that name:
`src/routes/governance/audit.py:135` serves it by that exact path,
`_helpers_risk.py:78` labels it, and `docs/models/model_risk/data.py:175` probes
it for `has_test_results`.

### 6.3 `<` and `>` render as `¡` and `¿` in the PDFs

`tex_escape()` in `docs/models/test_results/generator/latex.py` escapes
`\ & % $ # _ { } ~ ^` but not `<` or `>`, which the default OT1 font encoding
renders as inverted punctuation. Visible in the Trading Desk PDF, where a
docstring reading `No trades at all -> empty gauge_ids list` prints as `-¿`.

Cosmetic, but it is in a governance document. Fix is either
`\textless{}` / `\textgreater{}` in `tex_escape`, or `\usepackage[T1]{fontenc}`
in the shared header.

### 6.4 History table will show a misleading jump

`update_history()` diffs test names run over run, so the 10 corrected models will
each get a row like "203 test(s) added". Those tests aren't new — they were always
running, just misattributed. Worth editing the version description before this
goes to governance.

### 6.5 Three copies of the model→directory mapping

`MODEL_INFO`, `src/routes/governance/_constants.py`, `docs/models/model_risk/data.py`.
All three now agree at 26 entries, but nothing checks that they do — the same
failure shape just fixed on the attribution side. Worth one source of truth.

### 6.6 Trading Desk and CDM have no core model document

Both now have test results, but no `trading_desk.tex` / `cdm_schema.tex`, so the
documentation and analysis routes 404 for them. Makefiles are in place ready for
a core doc.

### 6.7 `timeseries_statistics` has no test evidence

It's built by `docs/models/Makefile` and has a core doc and analysis PDF, but
isn't in `MODEL_INFO`, so it has never had a `test_results.pdf`.

---

## 7. Not started — the rest of the original proposal

Steps 3–5, agreed as separate work:

- **Tier the report.** `test_report.tex` is 2.7 MB because it enumerates all
  ~11,000 tests in a traceability matrix plus a PLATFORM appendix. Proposal was:
  Tier A per-model detail (as now), Tier B platform areas summarised only, Tier C
  raw JUnit/coverage referenced rather than typeset.
- **Publish the attribution ratio** on the report front page. Currently 154 of 817
  collected test files (18.8%) are attributed to a model.
- **Slim history.** `docs/models/test_results/test_history.json` is 43 MB, 38.6 MB
  of it PLATFORM, because it stores the full nodeid list per model per run.

---

## 8. Environment

- Use `.venv`, not `venv` — `venv` is stale and missing dependencies.
  `_resolve_python()` picks `.venv` first, so `python3 app.py …` is fine.
- Postgres and MinIO were started during this session and left running:
  ```bash
  ./scripts/pg-native.sh stop
  ./scripts/minio-native.sh stop
  ```
- Useful commands:
  ```bash
  python3 -m docs.models.test_results.generator --reconcile-only  # fast, no tests
  python3 -m docs.models.test_results.generator --pdf             # ~13 min, all 26 docs
  python3 app.py test --unit                                      # full suite + gate
  ```
