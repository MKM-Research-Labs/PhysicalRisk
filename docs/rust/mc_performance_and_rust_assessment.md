# Monte Carlo Performance and Rust Migration Assessment

| Field | Value |
|---|---|
| Status | **On hold** (2026-10-13). Corrected against a code review; no implementation started. |
| Date | 2026-10-13 |
| Owner | David Kelly |
| Scope | PhysicalRisk simulation stages: typhoon ensemble, stressm storm/gauge responses, MC storm generation, implementation language |
| Related | Leaves-first module refactor; split audit (`split_audit.py`); test coverage programme; BCBS 239 lineage; SR 11-7 model validation; `docs/storm_freq/frequency_layer_definition_and_plan_v2.md` (typhoon run cost) |

---

## 1. Problem statement

Large simulations take approximately one day to run on the available hardware, which is compute-constrained. This limits iteration speed on model development, pricing runs and validation testing.

Two questions are addressed:

1. Should the codebase be migrated from Python to Rust?
2. Where is runtime actually spent, and what is the most effective route to reducing it?

---

## 2. Decision summary

| Question | Decision |
|---|---|
| Full migration to Rust | **Rejected.** |
| Selective use of Rust for hot kernels | **Deferred.** Considered only if, after restructuring to arrays and Numba, a kernel still misses its target (Section 3.3). The typhoon particle filter is the most likely candidate. |
| Isolate MC storm generation as a standalone module | **Largely already done** (Section 4.3). Remaining work is RNG hygiene only; generation is not the dominant cost. |
| Runtime reduction strategy | **Profile first** (typhoon and stressm stages), then **parallelise events and stream output**, then **restructure the hot loops to arrays / Numba**, then reduce simulation volume. |

---

## 3. Rust migration assessment

### 3.1 Background

Rust is a compiled systems language offering C/C++-level performance with compile-time memory safety. It integrates with Python through PyO3/maturin, allowing individual functions to be written in Rust and imported as ordinary Python modules.

### 3.2 Reasons a full migration is rejected

1. **The cost is structural, not linguistic.** The slow paths (Section 4.1) are scalar loops over per-particle, per-hour and per-property Python objects. A Rust port only pays off after that code is restructured into arrays — and once it is, NumPy vectorisation and Numba recover most of the same gain without leaving Python.
2. **Validation reset.** A re-implementation in another language constitutes a new model implementation under SR 11-7. It would require re-documentation, re-testing, re-validation and a parallel run with output reconciliation, consuming significant governance effort without adding modelling capability.
3. **Conflict with the current refactor.** The incremental, leaves-first restructuring (packaging, cohesion/coupling rules, split audit, full test coverage) would be discarded and known technical debt exchanged for unknown new debt.
4. **Ecosystem dependency.** The scientific stack (NumPy, SciPy, rasterio, statistical libraries) has no complete Rust equivalent. Much would need rebuilding or wrapping.
5. **Reviewability.** Validators, auditors and model risk staff can independently review Python; far fewer can review Rust. This weakens effective challenge and BCBS 239 lineage evidence.
6. **Limited benefit outside hot spots.** Configuration, lineage, pricing logic, reporting and orchestration gain nothing material from compiled-language performance. The frequency and capital models are already vectorised (2,000,000 years in ~0.25 s, `docs/capital/project_plan.md`).
7. **RNG reproducibility.** storm_multi and stressm draw from legacy `np.random.RandomState` (MT19937). A bitwise-reconciled Rust port would have to replicate that stream exactly.

### 3.3 Conditions for reconsidering

- After Section 7.2, a kernel still misses the runtime target with NumPy vectorisation and Numba; or
- The engine must ship to clients as a single compiled binary; or
- Performance becomes a hard commercial constraint.

In any of these cases the approach is **kernel-by-kernel**, never a big-bang rewrite (Section 7.2).

### 3.4 Candidate kernels (if Rust is later justified)

1. **Typhoon particle filter + wind field** (`src/models/typhoon/particle_filter/`, `src/models/typhoon/pipeline/event.py`, `wind_field/time_series.py`). Most likely to need it: `compute_weights` takes a Python `plausibility_fn` callback per particle (`_weights.py:45-63`), which Numba cannot compile cheaply.
2. **Stressm per-hour gauge recursion** (`storm_multi/models/sequence_response.py:172`). A good Numba fit first; Rust only if Numba falls short.

*Superseded:* the original draft listed a 2D lateral inundation solver over the DEM grid. **No such solver exists** — `floodrisk/elevation.py` computes scalar relative elevation and `floodrisk/spatial.py` does polyline/gauge interpolation. MC storm generation was also listed; it is a moderate cost only (Section 4.1).

---

## 4. Current state of the code (review, 2026-10-13)

### 4.1 Long-running paths

| Path | Entry point | Inner loop | Assessment |
|---|---|---|---|
| **Typhoon SMC ensemble** | `app/commands/port/stages/typhoon/_run.py:126` → `simulate_typhoon_events` (`pipeline/ensemble/_simulate.py:46`) | Per event (`_simulate.py:156`) → per step (`particle_filter/_run.py:80`) → per particle, rebuilding a `TyphoonParticle` each step (`_lifecycle.py:96`); per-particle weights and list-copied histories (`_weights.py`); scalar while-loop resampling (`_resample.py:55-57`); wind field per trajectory × property (`pipeline/event.py:104-105`) with scalar maths per state. Work ≈ events × particles × steps × properties. | **Dominant cost.** In coupled mode events = storm count (default `--num-sims 10000`) × 100 particles. |
| **Stressm gauge responses** | `app/commands/port/stages/storm.py:68` → `generate_stressm` → `compute_sequence_records` (`stressm/pipeline/orchestrator/_responses.py:30`) | Per sequence (`:44`) → per gauge (`:66`) → per hour lag filter (`sequence_response.py:172`); per-hour Cholesky sample `L @ z` (`spatial_correlation.py:203-208`); per-storm-hour weights (`sequence_response.py:128`); `hydrology.py` 168-hour loops. Results accumulated as dicts of lists. | **Second cost.** Recursion is Numba-shaped; Cholesky draws vectorise across hours. |
| MC storm generation | `generate_event_set` (`storm_multi/generators/batch_generator.py:52`) | One `gen.generate(...)` per sequence (`:103`) with scalar `rng` calls. | Moderate. Already isolated and seeded per event. |
| Frequency YLT, capital | `frequency/ylt/`, `capital/one_year.py`, `over_term.py` | Vectorised NumPy. | No action. |
| Seismic | `seismic/.../occurrence/_simulate.py`, `damage.py` | Python loop over drawn events only. | Low priority. |
| Flood risk analytics | `floodrisk/risk_analytics.py:69` | Per-sim NumPy dot product. | Trivially vectorisable. |

### 4.2 Parallelism, persistence and memory

- **No parallelism on any simulation path.** No multiprocessing, `concurrent.futures`, Numba, Cython or dask in `src/` or `app/` (joblib is used only to persist classifiers).
- **Persistence is JSON:** `storm_sequences.json` (~10–12 MB per 10k sequences), typhoon `ensemble.json` plus per-event JSON. No Parquet/HDF5.
- **Memory:** every `WindFieldOutput` for every event × particle × property is held until the end of the run (`_simulate.py:137,194`).
- **Recorded cost:** typhoon stage 15 min for 1,000 events × 100 particles, plus ~20 min writing a 69 MB `ensemble.json` while swapping (`frequency_layer_definition_and_plan_v2.md`, "Run cost"). Extrapolated to the 10k coupled default: ~2.5 h compute, before serialisation and swap. I/O and memory are therefore measured costs, not a residual.

### 4.3 RNG

- **Explicit `np.random.Generator`:** typhoon (per-event `default_rng(event_seeds[i])`), frequency, seismic, capital.
- **Legacy `np.random.RandomState`, seeded via `SeedSequence.spawn`:** storm_multi and stressm (`batch_generator.py:85,94-97`, `sequence_generator.py:87`, `stressm/pipeline/orchestrator/_core.py:95`).
- **Unseeded or global state (to fix):**
  - `storm_multi/generators/duration_sampler.py:68` and `gap_sampler.py:67` default to unseeded `RandomState()`.
  - `storm_multi/models/spatial_correlation.py:205` falls back to global `np.random.randn`.
  - `floodrisk/risk_analytics.py:56` calls `np.random.seed(42)`.
  - stdlib `random` in `models/statistics/synthetic.py` and `models/intensity/distribution/_core.py` (and throughout `src/port/rand/`, which is synthetic data generation, not simulation).

---

## 5. Step 1: Profile before changing anything

**Effort:** approximately 0.5 day.

**Actions:**

1. Define two reduced benchmark runs with fixed seed and configuration: typhoon at ~100 events × 100 particles, and stressm at ~200 sequences.
2. Profile with `py-spy record` (sampling, low overhead) and/or `cProfile` + `snakeviz`; use `line_profiler` on identified hot functions.
3. Record **peak memory** as well as time (`memray` or peak RSS), given the recorded swapping.
4. Record the breakdown: typhoon propagation / weighting / wind field / serialisation; stressm generation / gauge response / serialisation.
5. Store the benchmark configuration and baseline timings in the repository so every subsequent change is measured against it.

**Output:** fill in Section 10.

---

## 6. Step 2: Storm generation isolation and RNG hygiene

### 6.1 Status

The generator is already a separate leaf (`storm_multi/generators/batch_generator.py`) producing a sequence set from configuration and a root seed, with per-event streams from `SeedSequence.spawn`. **No further isolation work is planned.** The original 2-day to 3-week estimate is withdrawn.

### 6.2 Remaining work

1. Remove the unseeded and global RNG fallbacks listed in Section 4.3 (make `rng` required, or derive it from the run seed).
2. Replace stdlib `random` on simulation paths with a passed generator.

### 6.3 RandomState vs Generator

The original acceptance criteria required both "all randomness via `numpy.random.Generator`" and a bitwise golden-output test against the pre-refactor storm set. These conflict: switching storm_multi/stressm from `RandomState` to `Generator` changes the draws. They are therefore separated:

1. **Behaviour-preserving changes** (hygiene in 6.2, parallelism, vectorisation) keep `RandomState` and must pass the bitwise golden-output test.
2. **Generator migration** is a separate, deliberately output-changing change: documented, with a distributional (not bitwise) comparison against the previous catalogue, and a new golden baseline recorded afterwards.

### 6.4 Acceptance criteria

1. Generator depends only on configuration and seed (verified by the split audit dependency rules).
2. No unseeded, module-level or global RNG calls on simulation paths.
3. Golden-output regression test per 6.3.
4. Unit tests cover the module to the project coverage standard.

---

## 7. Step 3: Runtime reduction options

Ordered by expected benefit per unit of effort, given Section 4.

### 7.1 Use all available cores and stream output

Events are already independently seeded, so evaluation is embarrassingly parallel.

- Distribute typhoon events and stressm sequences across cores with `multiprocessing` / `concurrent.futures.ProcessPoolExecutor`, reusing the existing per-event seeds so results are identical regardless of worker count or scheduling.
- **Write results per event as they complete** instead of accumulating every `WindFieldOutput` in memory; this removes the swapping and most of the end-of-run serialisation stall.
- Move bulk outputs from JSON to Parquet, keeping a small JSON manifest.
- Record root seed and worker count in run metadata.

### 7.2 Reduce per-event cost

| Target | Change | Notes |
|---|---|---|
| Typhoon propagation | Hold particle state as arrays (structure-of-arrays) and step all 100 particles at once instead of per-object | Removes the innermost Python loop and per-step object construction |
| Typhoon weighting / resampling | Vectorise the plausibility score over the particle array; `np.searchsorted` systematic resampling; store histories as index arrays, not copied lists | The per-particle callback is the main obstacle to Numba (Section 3.4) |
| Wind field | Evaluate all properties × states in one array operation | Currently per trajectory × property × state |
| Stressm lag filter / hydrology | Numba `@njit` on the per-hour recursions | Sequential recursion; cannot be a single NumPy expression |
| Stressm spatial correlation | Draw all hours at once: `L @ Z` with `Z` of shape (gauges, hours) | Must preserve draw order to pass the golden test |
| Flood risk analytics | Replace per-sim loop with one matrix product | Trivial |

| Option | Typical effort | Typical gain | Notes |
|---|---|---|---|
| NumPy vectorisation | Hours–days per hotspot | Large where loops are pure Python | Stays fully within existing tooling |
| Numba `@njit` | 1–3 days per kernel | 10–100× on loop-heavy code | Stays in Python; reviewable; testable with existing suite |
| Rust via PyO3/maturin | 1–3 weeks per kernel incl. reconciliation | Often marginal over good Numba on CPU | Only if Section 3.3 conditions are met |

If any kernel is vectorised, moved to Numba or moved to Rust, the original Python implementation is retained as the **validated reference implementation**, and a regression test compares the optimised kernel against it on every CI run.

### 7.3 Reduce simulation volume

| Technique | Description | Governance note |
|---|---|---|
| **Catalogue reuse** | Generate the storm catalogue once and persist (Parquet); resample a cached event set rather than regenerating (as already recommended in `frequency_layer_definition_and_plan.md`). | Record seed, config hash, code version and file hash alongside the catalogue for BCBS 239 lineage. |
| **Importance sampling** | Oversample severe storms in the tail and reweight. | Sampling and reweighting scheme must be documented and validated; weights retained in outputs. |
| **Stratified / Latin hypercube sampling** | Coverage of the input space with fewer draws. | Document strata definitions. |
| **Antithetic variates** | Pair each draw with its mirror. | Low implementation risk. |
| **Quasi-Monte Carlo (Sobol)** | `scipy.stats.qmc`; faster convergence for smooth integrands. | Use scrambled sequences for error estimation. |
| **Convergence-based stopping** | Stop at a target standard error rather than a fixed count. | Target precision in central configuration and reported with results. |
| **Particle count** | Test whether fewer than 100 typhoon particles per event gives stable outputs. | Document the sensitivity analysis. |

### 7.4 General hygiene

- Keep pandas out of inner loops (currently true; `iterrows` appears only in `floodrisk/risk_visualization.py`).
- Consider `float32` where precision analysis shows it is sufficient (document the analysis).
- Precompute and cache quantities that do not vary by event (e.g. property geometry for the wind field).

---

## 8. Governance and compliance considerations

| Requirement | How this plan addresses it |
|---|---|
| SR 11-7 / model validation | Behaviour-preserving changes proven by golden-output regression tests; output-changing changes (Generator migration, variance reduction, particle count) documented and validated separately. |
| BCBS 239 data lineage | Persisted catalogues carry seed, config hash, code version and file hash; parallel runs record root seed and worker count. |
| Reproducibility | No unseeded or global RNG on simulation paths; per-event seeds independent of scheduling. |
| Duplication | No parallel implementations except a deliberately retained reference implementation for regression testing. |
| Centralised configuration | Sampling scheme, convergence target, particle count and parallelism settings held in central config, not hard-coded. |

---

## 9. Plan and sequencing

| # | Activity | Effort | Dependency |
|---|---|---|---|
| 1 | Profile typhoon and stressm benchmarks (time and peak memory); record baseline | 0.5 day | — |
| 2 | Golden-output tests for typhoon and stressm at benchmark size | 1 day | 1 |
| 3 | RNG hygiene (Section 6.2) | 0.5–1 day | 2 |
| 4 | Parallel events + per-event streaming output + Parquet | 2–4 days | 2 |
| 5 | Typhoon particle filter and wind field to arrays | 1–2 weeks | 2 |
| 6 | Numba on stressm per-hour recursions; vectorised correlation draws | 2–4 days | 2 |
| 7 | Catalogue reuse with lineage metadata | 1–2 days | 4 |
| 8 | Convergence-based stopping; particle-count sensitivity | 2–4 days | 4 |
| 9 | Variance reduction (start with importance sampling) incl. validation | 1–2 weeks | 7, 8 |
| 10 | Optional: RandomState → Generator migration (Section 6.3) | 1–2 days | 2 |
| 11 | Re-assess need for Rust against Section 3.3 | 0.5 day | 5, 6 |

Expected outcome: steps 4–6 alone are likely to cut a one-day run to a small number of hours, and remove the memory/swap stall, without leaving Python.

---

## 10. Profiling results

*To be completed after step 1. "Expected" column is from the code review (Section 4), not measurement.*

| Component | Expected | Measured share | Peak memory | Notes |
|---|---|---|---|---|
| Typhoon propagation + weighting + resampling | High | | | Per-particle object loops |
| Typhoon wind field | High | | | Per trajectory × property × state |
| Typhoon ensemble serialisation | High (recorded ~20 min / 1k events) | | High (swap) | All outputs held in memory |
| Stressm gauge responses | Medium–high | | | Per sequence × gauge × hour |
| Storm generation | Low–medium | | | Already isolated |
| Frequency / capital | Negligible | | | Vectorised |
| Other I/O | | | | JSON outputs |

---

## 11. Revision history

| Date | Change |
|---|---|
| 2026-10-13 | Initial version |
| 2026-10-13 | Corrected against code review: no inundation solver exists; hot paths are the typhoon particle filter/wind field and stressm gauge recursion; storm generation already isolated; no parallelism on simulation paths; I/O and memory are measured costs; RandomState/Generator conflict in acceptance criteria resolved; plan resequenced (parallelise and stream before per-event optimisation). Put on hold. |
