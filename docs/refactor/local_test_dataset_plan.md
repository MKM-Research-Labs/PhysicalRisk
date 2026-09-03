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


---

# Revision — ephemeral fixture, 2026-09-03

**Constraint stated:** no capacity for large files on the internal disk. The
fixture must be created for a run and removed afterwards, and should be small —
around 10 gauges.

That is a better fit for the constraint than a persistent tree, but it moves
the difficulty. A committed fixture is *data*; an ephemeral one is a
*generator invocation*, and the generator has three requirements the plan above
did not account for.

## R1. Catchment parameters are generation INPUTS, and they are on the SSD

`data/catch/<id>/` is not output — it is what generation reads:

- `data/catch/<id>/fault_trace.json` — seismic source-to-site geometry
- `data/catch/<id>/tc.py` — tropical-cyclone exposure
- `data/catch/halong/BRI-PRS Building Prototypes.xlsx` — BRI code sampling
- sequence-generator configs under `data/catch/<name>.py`

So **generating a thames portfolio offline is not currently possible at all** —
not for lack of a data root, but because the parameters live on the unplugged
volume. Either they are small enough to vendor into the repo (they look it,
excepting the xlsx), or the fixture must be generated once *with* the SSD and
then kept.

Vendoring them is worth doing on its own merits: they are configuration, they
are version-controllable, and [[governance_data_not_in_data_dir]] already
established that repo-level content should not sit under `data/`.

## R2. The core generators are not seeded

Only three seed flags exist — `--typhoon-seed`, `--fire-seed`,
`--seismic-seed` — and all default to `None`, "nondeterministic". There is **no
seed for gauges, properties, storms, hazard curves or the blotter**.

An ephemeral dataset regenerated per run would therefore contain different
gauge locations, property attributes and storm sequences every time. Any test
asserting on values rather than structure becomes flaky, and a failure could
not be reproduced from the same command.

**A global `--seed` covering the core stages is a prerequisite**, not a
refinement. Until it exists, ephemeral generation buys a dataset nobody can
debug against.

## R3. Ten gauges trips two existing assertions

`>= 40` gauges (`test_blotter_data_part1.py:65`) fails outright at 10, and
`>= 10` storm-covered gauges (`test_storm_data_storms_part2.py:114`) sits
exactly on the boundary. Both need to become relative to the dataset, or those
tests scoped out of small-fixture runs.

## The cheaper alternative, worth considering first

**A committed fixture sidesteps R1 and R2 entirely.** Fixed data needs no
catchment parameters, needs no seed to be reproducible, and costs no generation
time per run. "No large files" and "a few MB in git" are not in conflict —
and it is the only option that makes the suite runnable in CI, where there is
no SSD to plug in.

The ephemeral route is right if the fixture turns out too big to commit. That
is the fact to establish first, and it needs one generation run with the SSD
attached to measure.

## Revised order of work

1. **Size it.** With the SSD attached, generate `-ng 10 -np 1 -nc 1 -ns 100`
   into a scratch root and measure. Everything below depends on the answer.
2. `MKM_DATA_ROOT` override in `PortfolioConfig` (needed either way).
3. If small enough → commit the fixture. Stop here; R1 and R2 do not arise.
4. If too large → vendor the catchment parameters (R1), add a global `--seed`
   (R2), then build generate → test → teardown with guaranteed cleanup
   (`try/finally` plus a stale-sweep at startup, as `_sweep_stale_clones`
   already does for the e2e catchment clones).
5. Relax the volume assertions (R3).
