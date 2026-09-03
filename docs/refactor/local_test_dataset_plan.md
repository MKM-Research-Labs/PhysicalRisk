# A local test dataset, off the SSD

**Status:** proposed, 2026-09-03 · **Question asked:** is a small local
test-only database worth building, so runs never touch the main data?

## 1. Answer: yes — but the database is the smaller half

The blocker is wider than the database. **Both** data stores live on the
external SSD:

| Store | Location |
|---|---|
| File data (`data/`) | symlink → `/Volumes/David SSD/Docs/PhysicalRisk/data` |
| Postgres cluster | `/Volumes/David SSD/.../physicalrisk/pgdata` |

And the default backend is **`file`**, not `pg` (`MKM_REPO_BACKEND` defaults to
`"file"`), so most tests read the *file* tree rather than the database. A
test-only database alone would not let a single one of them run.

**It is worse than "tests cannot run".** With the SSD absent, `phys.py --help`
itself crashes: `config/__init__.py` builds `PortfolioConfig()` at import time,
which calls `input_dir.mkdir(parents=True)` and dies on the dangling symlink.
The whole CLI is unusable, not just the suite.

## 2. Why it cannot be done with today's seams

`PortfolioConfig` (`config/path/_portfolio_paths.py`) hardcodes the data root:

```
self.input_dir      = self.project_root / 'data' / 'input' / catchment_id
self.results_dir    = self.project_root / 'data' / 'output' / 'results'
self.catchments_dir  = self.project_root / 'data' / 'catch'
self.data_root      = self.project_root / 'data'
```

The only escape is `MKM_CATCHMENT_INPUT_OVERRIDE`, which moves *input* and
nothing else — verified: with it set and the SSD absent, config still dies
trying to create the output tree. The sibling `_config_paths.py` class does
honour `MKM_INPUT_DIR`/`MKM_OUTPUT_DIR`, but it is not the class the app uses.

**So the first piece of work is a data-root override, not a dataset.**

## 3. Plan

### Phase 1 — make the data root relocatable *(the actual blocker)*
Add `MKM_DATA_ROOT` to `PortfolioConfig`, defaulting to
`project_root / 'data'`, and derive input / output / catch / results from it.
This belongs in the config package, which is where paths are required to live
(§4.3), so it costs nothing in audit terms.

Done alone, this already means the CLI and the fixture-based ~80% of the suite
work with the SSD unplugged.

### Phase 2 — generate the small fixture
```
MKM_DATA_ROOT=$HOME/PhysicalRisk-testdata \
  python phys.py port --thames -np 1 -nc 1 -ns 100
```
Keep `-ng` at its default **52 gauges** — see Phase 4; gauges are cheap, and
several assertions need at least 40. Properties × storms is what makes the real
dataset large, and that is exactly what this cuts.

⚠️ Generation must never target the real root. Phase 1 should refuse to
generate when `MKM_DATA_ROOT` is unset, so a mistyped command cannot overwrite
the shared data.

Worth deciding: if the result is a few MB, **commit it**. A version-controlled
fixture is reproducible, reviewable, and makes the suite runnable in CI — which
no amount of local generation does.

### Phase 3 — a local Postgres for the pg-backed tests
A second cluster on the internal disk (`~/PhysicalRisk-testdb/pgdata`, port
5434) with a `scripts/pg-test.sh` beside `pg-native.sh`. `MKM_PG_DATA_DIR` is
already the single source for the data dir, so this is configuration, not code.
This is what stops the ~57 `tests/database/*` skips.

### Phase 4 — reconcile the volume assertions
Only **five** absolute-volume assertions exist in `tests/data`, and none
concern properties:

| Assertion | File |
|---|---|
| `>= 40` gauges | `test_blotter_data_part1.py:65` |
| `>= 16` PRS trades | `test_blotter_data_part2.py:60` |
| `>= 50` EOD files | `test_blotter_data_part2.py:143` |
| `>= 10` storm-covered gauges | `test_storm_data_storms_part2.py:114` |

Keeping 52 gauges satisfies two of them. The trade and EOD counts come from the
book/blotter generator and need either a fixture that generates enough, or
thresholds expressed relative to the dataset.

### Phase 5 — wire it into the test command
An env preset (or `--testdata`) so `phys.py test` selects the fixture root, and
the audit output goes somewhere that is not the shared tree.

## 4. What this is not

**A replacement for the full run.** A 1-property portfolio cannot meaningfully
exercise IDW spatial interpolation, portfolio VaR, or aggregation across a
book — the very things the 200-property dataset exists to test. Treat it as the
everyday smoke/regression dataset and keep the full thames run for
pre-review and nightly.

⚠️ **Not yet audited: the e2e suite.** 105 test files read the real data tree,
5 of them under `tests/e2e/`. The e2e assertions were written against the full
portfolio (marker counts, table rows, VaR panels) and I have not gone through
them. Expect a round of triage there, and budget for it — this is the part most
likely to be underestimated.

**Two datasets must be kept in step.** The lineage hash manifest is
dataset-specific (`test_output_hashes_current` already warns about 23
mismatches on the real data), so the fixture needs its own manifest or that
check must be scoped.
