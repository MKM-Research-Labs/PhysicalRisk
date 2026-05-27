# Typhoon Model — Phase 1 Plan

**Goal:** A self-contained, catchment-agnostic typhoon engine in `src/models/typhoon/` that, given a catchment configuration, produces a calibrated peak-wind distribution at each property point. Runs as an adjunct to the existing storm pipeline; no changes to `src/port/src/storm_multi/` internals in Phase 1.

**Phase 1 deliverable:** `compute_peak_wind_distribution(catchment_config, num_events)` → per-property posterior over peak sustained wind, with footprint metadata and threshold-exceedance probabilities.

---

## Architecture principles

1. **Catchment-agnostic model.** Code under `src/models/typhoon/` contains no references to any specific catchment. It defines the math, data structures, and parameter dataclasses. It imports nothing from `data/catch/*`.
2. **Three-layer separation.**
   - **Raw values** live in `data/catch/<id>/storm.py` (extending the existing file). Halong is the launch catchment, e.g. `data/catch/halong/storm.py`.
   - **Routing** is the `config` package. The active catchment is selected via `MKM_CATCHMENT` (default `thames`); `config.load_params_module()` / `config.get_catchment()` pulls `data/catch/<id>/` and exposes it. The model reads from `config`, never directly from `data/catch/*`.
   - **Math** lives in `src/models/typhoon/`. The model receives a `CatchmentTyphoonConfig` parameter dataclass (assembled by an adapter at the boundary) and operates only on that.
3. **Invocation.** End-state CLI is `python3 app.py port --typhoon`, alongside the existing `--gauges`, `--hazard`, `--stressm` flags. The flag dispatches to a new orchestrator stage that calls into `src/models/typhoon/pipeline.py`.
4. **Heavy math + forward models in `src/models/typhoon/`.** Nothing in `src/port/src/`. The orchestrator stage is a thin shim that imports from the model.
5. **Hand-rolled.** Particle filter, transitions, wind-field profiles all NumPy-only. No new heavy dependencies in Phase 1.
6. **Specs.**
   - Bayesian progression: `src/models/typhoon/bayesian_typhoon_progression_spec.pdf`
   - Parametric wind-field: tail of `src/models/typhoon/How does a storm turn into a typhoon.pdf`

---

## Module layout

```
src/models/typhoon/
├── __init__.py
├── data_structures.py     # State, Particle, Trajectory, enums, WindFieldOutput
├── parameters.py          # Parameter dataclasses (GenesisPrior, MotionParams, ...)
├── genesis.py             # Genesis prior + tail-aware peak-wind sampling
├── transitions.py         # One-step state propagator (motion / intensity / size)
├── plausibility.py        # Soft-constraint scores for simulation mode
├── particle_filter.py     # Hand-rolled SMC engine (loose for breadth in Phase 1)
├── wind_field.py          # Parametric symmetric profile + asymmetry + surface
├── pipeline.py            # End-to-end orchestration: events → property-level peak wind
├── bayesian_typhoon_progression_spec.pdf
└── How does a storm turn into a typhoon.pdf
```

```
tests/models/typhoon/
├── test_data_structures.py
├── test_genesis.py
├── test_transitions.py
├── test_plausibility.py
├── test_particle_filter.py
├── test_wind_field.py
└── test_pipeline.py
```

```
data/catch/halong/storm.py      # extended with typhoon-specific constants (raw values)
config/                         # routing layer — exposes catchment params via config.load_params_module()
app/commands/port/
├── parser.py                   # adds --typhoon flag (alongside --gauges, --hazard, --stressm)
├── stages/                     # adds typhoon_stage.py — thin shim into src/models/typhoon/pipeline.py
└── orchestrator.py             # wires the new stage
```

### Data flow

```
data/catch/halong/storm.py
  (raw constants: HALONG_GENESIS_BBOX, HALONG_REGIME_WEIGHTS, HALONG_PEAK_WIND, ...)
        ↓
config.load_params_module()  ← active catchment chosen by MKM_CATCHMENT env var
        ↓
adapter at orchestrator boundary
  builds a CatchmentTyphoonConfig dataclass from config values
        ↓
src/models/typhoon/pipeline.simulate_typhoon_events(config_obj, ...)
  — model never imports from data/catch/* or from the config package directly;
    it just consumes the dataclass.
```

---

## Phase 1.1 — Data structures & parameter scaffolding

**Files**
- `src/models/typhoon/data_structures.py`
- `src/models/typhoon/parameters.py`
- `data/catch/halong/storm.py` (extend existing — add typhoon constants alongside the current `BASE_PRECIPITATION_MM`, `TRACK_START`, `TRACK_END`, `INTENSITY_WEIGHTS`)

**Contents of `data_structures.py`**
- `TyphoonState` dataclass: `(lon, lat, u, heading, V_max, R_max, R_outer, regime, land_flag, t)` — spec eq. 1, with explicit `R_outer` per spec emphasis
- `TyphoonParticle`: `state: TyphoonState`, `weight: float`, `parent_id: int`
- `TyphoonTrajectory`: list of `TyphoonState` per particle + metadata (genesis time, event_id, scenario_family)
- `RegimeClass` enum: `STRAIGHT_WESTWARD`, `NW_RECURVER`, `SHARP_RECURVE`, `STALLED`, `LANDFALL_DECAY`
- `ScenarioFamily` enum: `HISTORICAL`, `BASELINE`, `MODERATE`, `SEVERE`, `EXTREME`
- `WindFieldOutput`: `peak_sustained`, `peak_gust`, `time_of_peak`, `duration_above[thresholds]`, `time_series`

**Contents of `parameters.py`** (model-side parameter contract — catchment populates these)
- `@dataclass GenesisPrior`: bbox, initial-heading von Mises params, translation-speed prior, regime mixture weights, scenario-family mix
- `@dataclass PeakWindParams`: per-scenario-family `(mu, sigma, v_T, alpha)` for the hybrid truncated-normal + Pareto tail (spec eq. 14)
- `@dataclass MotionParams`: per-regime `mu_u`, `sigma_u`, `mu_psi`, `sigma_psi`, latitude-recurvature coefficients
- `@dataclass IntensityParams`: over-water drift/variance, land-decay rate `k_land`
- `@dataclass SizeParams`: lognormal means for `R_max` and `R_outer` as a function of `V_max`, plus stochastic-update stddev
- `@dataclass WindFieldParams`: `alpha_eye`, outer-decay shape `p`, asymmetry `eps_max`, `c_eps`, surface reductions `rho_surf_sea`, `rho_surf_land`, optional gust factor
- `@dataclass PlausibilityWeights`: heading-jump, speed-jump, basin-boundary, regime-consistency weights
- `@dataclass CatchmentTyphoonConfig`: aggregates the above + `land_mask`, `property_points`, output thresholds — this is the single object passed into the pipeline

**Contents of extended `data/catch/halong/storm.py`** (Halong as launch catchment — raw values only)
- `HALONG_GENESIS_BBOX`: Gulf of Tonkin region (~107°–112°E, 17°–22°N)
- `HALONG_REGIME_WEIGHTS`: tilt to `STRAIGHT_WESTWARD` + `LANDFALL_DECAY` for SCS climatology
- `HALONG_PEAK_WIND`: per-scenario-family `(mu, sigma, v_T, alpha)` reflecting SCS typhoon intensity range
- `HALONG_MOTION_PARAMS`, `HALONG_SIZE_PARAMS`, `HALONG_WIND_FIELD_PARAMS`, `HALONG_PLAUSIBILITY_WEIGHTS`
- `HALONG_HANOI_REFERENCE`: (105.85°E, 21.03°N)
- Land mask / Vietnam landmass polygon (callable or coords)
- Property points (or import path) for the Hanoi property set
- These are raw Python constants/objects. **No imports from `src/models/typhoon/`** — the catchment file doesn't know about the model.

**Boundary adapter** (one file under `app/commands/port/stages/` — to be added in Phase 1.7)
- Reads catchment params via `config.load_params_module()` (already exists in the codebase)
- Assembles them into a `CatchmentTyphoonConfig` dataclass instance
- This is the only place that knows about both sides

**Tests**
- Type construction and serialization round-trip
- Halong constants load via `config.load_params_module()`
- Adapter produces a valid `CatchmentTyphoonConfig` from Halong values
- **Import-discipline test**: `src/models/typhoon/` imports nothing from `data.catch.*` and nothing from `config` (enforced by AST or grep-based test)

**Done when:** all types instantiable; `from src.models.typhoon.parameters import CatchmentTyphoonConfig` works; Halong raw constants load via the `config` routing layer; the boundary adapter assembles a valid config object.

---

## Phase 1.2 — Genesis prior with tail-aware peak-wind sampling

**File:** `src/models/typhoon/genesis.py`

**Contents**
- `sample_genesis(prior: GenesisPrior, peak_wind: PeakWindParams, scenario: ScenarioFamily, rng) -> TyphoonState`
- Samples:
  - Genesis lon/lat from bbox prior (uniform or Beta-shaped, controlled by `GenesisPrior`)
  - Initial heading: von Mises around climatological mean
  - Initial translation speed: Gamma or truncated-normal per prior
  - Initial `V_max`: **hybrid truncated-normal body + Pareto tail** per spec eq. 14:
    - `P(V > v) = 1 - Phi((v - mu) / sigma)` for `v <= v_T`
    - `P(V > v) = P(V > v_T) * (v_T / v)^alpha` for `v > v_T`
    - Scenario family selects `(mu, sigma, v_T, alpha)` — `EXTREME` has lower `alpha` (fatter tail)
  - Initial `R_max`, `R_outer`: lognormal conditioned on `V_max` with noise; `R_max < R_outer` invariant enforced
  - Regime: Categorical over `RegimeClass`, weights from `GenesisPrior.regime_weights`
- `sample_genesis_ensemble(n, config, rng)` → list of states; scenario mix from `GenesisPrior.scenario_mix`

**Tests**
- Empirical CDF of `V_max` matches the analytical hybrid distribution at p50/p95/p99
- Pareto tail produces stable rare extremes under fixed seed
- Scenario family swap shifts the upper tail in the expected direction (`EXTREME` > `SEVERE` > `BASELINE` at the 99th percentile)
- Regime sampling respects weights within 2σ at n=10k

**Done when:** 10k genesis samples reproduce the configured peak-wind distribution within tolerance; `EXTREME` shows detectably fatter tail than `BASELINE`.

---

## Phase 1.3 — Transition model (one-step propagator)

**File:** `src/models/typhoon/transitions.py`

**Contents**
- `step(state: TyphoonState, params: MotionParams | IntensityParams | SizeParams, land_mask, rng) -> TyphoonState` — advances by Δt (default 1 hour)
- **Motion update** (spec eq. 5): regime-conditioned Gaussian
  - `u_t ~ N(mu_u(s_{t-1}, k), sigma_u^2(k))`
  - `psi_t ~ N(mu_psi(s_{t-1}, k), sigma_psi^2(k))`
  - Mean functions depend on previous speed/heading, latitude (recurvature bias for `NW_RECURVER` above the configured latitude threshold), land flag
- **Position update** (spec eqs. 6–7): Haversine forward
  - `dx = u_t * dt * cos(psi_t)`, `dy = u_t * dt * sin(psi_t)`
  - Convert to (Δλ, Δφ) via Haversine — reuse any existing geodesic helpers via import only
- **Land detection**: callable `land_mask(lon, lat) -> bool`, provided by catchment config — model never embeds geometry
- **Wind update** (spec eqs. 8–9):
  - Over water: `V_t ~ N(mu_V(V_{t-1}, k), sigma_V^2)` — mild drift, scenario-controlled
  - Over land: `V_t = V_{t-1} * exp(-k_land * dt)` — exponential decay
- **Size update** (spec eq. 10): stochastic, mean-reverting around climatological `(R_max, R_outer)` given `V_t`; invariant `R_max < R_outer` enforced

**Tests**
- Step preserves invariants (`R_max < R_outer`, `V_max >= 0`, lat ∈ [-90, 90])
- `STRAIGHT_WESTWARD`: lon decreases on average; heading stays within configured band
- Land-decay rule: `V` drops monotonically over multi-step inland propagation
- `NW_RECURVER`: heading curves northward above the configured recurvature latitude
- Repeated step over many seeds — distributions of `(u, psi, V)` stay in the regime envelope

**Done when:** 1000-step trajectories per regime produce statistically plausible paths and survive invariant checks.

---

## Phase 1.4 — Particle filter engine (hand-rolled SMC)

**File:** `src/models/typhoon/particle_filter.py`

**Why the order matters.** Phase 1 prioritizes a **wide** peak-wind distribution. In pure-simulation mode (no observations), Bayesian filtering with tight likelihoods would collapse particles toward the prior mode and shrink the tail. We build the full SMC architecture but configure it loosely so trajectories spread, not collapse. Tighter filtering becomes useful later when we want to assimilate real best-track data.

**Contents**
- `ParticleFilter` class:
  - `__init__(n_particles, config: CatchmentTyphoonConfig, rng)`
  - `initialize()` — sample `n_particles` from `genesis.sample_genesis_ensemble`, uniform weights
  - `propagate_one_step()` — apply `transitions.step` to each particle (vectorized over particles)
  - `compute_weights(plausibility_fn)` — multiply weight by per-particle plausibility score
  - `resample(method="systematic")` — resample when `ESS < threshold`; default ESS threshold low (e.g. `N/4`) to preserve diversity
  - `run_to_horizon(steps)` — main loop; returns `list[TyphoonTrajectory]`
- Vectorized over particles with NumPy. Target: 1000 particles × 168 hours in <10s on the Mac Mini.

**Tests**
- N particles in → N trajectories out; no collapse under uniform plausibility
- Resampling preserves total weight; ESS recovers post-resample
- Determinism under fixed seed
- Vectorized propagation matches a per-particle loop within numerical tolerance

**Done when:** 1000-particle × 168-hour run produces a diverse trajectory ensemble within target runtime.

---

## Phase 1.5 — Plausibility scoring (soft likelihoods)

**File:** `src/models/typhoon/plausibility.py`

**Contents**
- `plausibility_score(state, prev_state, weights: PlausibilityWeights) -> float` — returns a weight multiplier in (0, 1]
- Components (per spec p.6):
  - Sharp heading change penalty: Gaussian on Δψ above a threshold
  - Speed-jump penalty: Gaussian on `|Δu|`
  - Basin boundary penalty: smooth penalty as track exits the configured bbox
  - Regime-consistency penalty: e.g. `STALLED` should have low `u`; penalize if `u` stays high
- Each component weighted by `PlausibilityWeights` for tuning
- Phase 1 default: weights low (loose constraints) — breadth is the priority, not realism filtering

**Tests**
- Score = 1 for canonical trajectories; degrades smoothly for unphysical ones
- Composite score is a well-defined product of components; bounded in (0, 1]
- Tuning a single component weight up demonstrably tightens that dimension at fixed seed

**Done when:** unit tests pass and a hand-crafted "bad" trajectory gets a low cumulative score over 24 steps.

---

## Phase 1.6 — Parametric wind-field forward model

**File:** `src/models/typhoon/wind_field.py`

**Contents**
- `WindField` class with `evaluate(state: TyphoonState, x: tuple[lon, lat]) -> float`
- **Coordinate geometry** (spec eqs. 20–21):
  - `r(x, t) = haversine(x, c_t)` in km
  - `theta(x, t) = bearing(c_t -> x)`
- **Symmetric radial profile** (spec eqs. 22–23, piecewise — first-release default):
  - Inner core `r < R_max`: `V_sym = V_max * [alpha_eye + (1 - alpha_eye) * (r / R_max)]`
  - Outer `r >= R_max`: `V_sym = V_max * exp(-((r - R_max) / L)^p)`
  - `L` calibrated so `V_sym(R_outer) = V_outer_ref` (gale-force, ~17.5 m/s) per spec eq. 25
- **Asymmetry correction** (spec eqs. 26–28):
  - `V(r, theta) = V_sym(r) * [1 + eps * cos(theta - phi)]`
  - `eps = min(eps_max, c_eps * u / (V_max + eta))`
  - `phi` = motion azimuth (NH offset baked into `WindFieldParams`)
- **Surface reduction** (spec eq. 29): land/sea binary `rho_surf` — Hanoi is inland, so this matters
- `evaluate_time_series(trajectory, point) -> WindFieldOutput`: loops over states, captures `peak_sustained`, `time_of_peak`, `duration_above[V_thresh]`
- **Holland profile not implemented in Phase 1**; the interface admits an alternative backend later

**Tests**
- Peak occurs near `r = R_max` along the azimuth where motion + symmetric peak align
- `V_sym(R_outer) ≈ V_outer_ref` within tolerance
- Asymmetry: faster storm → larger right-side enhancement (NH)
- Distance/bearing math matches a hand-checked case
- Sensitivity: doubling `V_max` doubles local wind at fixed geometry (in the symmetric regime)

**Done when:** wind-field at a sample point traces a smooth peak-and-decay through a known synthetic track.

---

## Phase 1.7 — End-to-end pipeline + `app.py port --typhoon` wiring

**Files**
- `src/models/typhoon/pipeline.py` (model side)
- `app/commands/port/parser.py` (add `--typhoon` flag)
- `app/commands/port/stages/typhoon_stage.py` (new — boundary adapter + orchestration shim)
- `app/commands/port/orchestrator.py` (wire the new stage)

**`src/models/typhoon/pipeline.py`** (model side — catchment-agnostic)
- `simulate_typhoon_events(config: CatchmentTyphoonConfig, n_events, n_particles, horizon_hours, rng) -> EventEnsemble`
- For each event:
  - Sample genesis state(s) via `genesis.sample_genesis_ensemble`
  - Run `ParticleFilter.run_to_horizon` to produce trajectory ensemble
  - For each property point in `config.property_points`, evaluate `WindField` along each trajectory → `WindFieldOutput`
  - Aggregate per-property results across particles and across events
- Outputs (per property):
  - Posterior distribution of peak sustained wind (mean, quantiles, full samples)
  - Probability of exceeding configurable thresholds (e.g. 25, 33, 42, 50 m/s)
  - Time-of-peak distribution
  - Per-event footprint metadata (peak `V_max`, peak local wind, distance at peak)
- Writes JSON to a path supplied by the caller (no hardcoded paths)

**`app/commands/port/parser.py`** (CLI flag)
- Add `sp.add_argument("--typhoon", "--ty", action="store_true", help="Run typhoon (tropical cyclone) wind ensemble for the active catchment")` alongside the existing `--gauges`, `--hazard`, `--stressm` flags
- Optional: `--num-typhoon-events`, `--num-typhoon-particles`, `--typhoon-scenario` knobs with sensible defaults

**`app/commands/port/stages/typhoon_stage.py`** (boundary adapter — the only file that bridges both worlds)
- Reads raw catchment values via `config.load_params_module()` for the active catchment (`config.CATCHMENT`)
- Assembles them into a `CatchmentTyphoonConfig` instance
- Resolves output path via `config.get_input_path()` / `config.get_output_path()` convention
- Calls `pipeline.simulate_typhoon_events(...)`
- Mirrors the shape of existing port stages so it slots into `orchestrator.py` cleanly

**`app/commands/port/orchestrator.py`** (dispatch)
- Add a branch: if `args.typhoon`, call the typhoon stage. Matches the dispatch pattern used by `--gauges`, `--hazard`, etc.

**Invocation (end state)**
```
MKM_CATCHMENT=halong python3 app.py port --typhoon --num-typhoon-events 1000
```

**Tests**
- Smoke test: 100 events × 5 properties runs to completion via the stage adapter (not just the model)
- Peak wind distribution shows positive skew (Pareto tail visible)
- Scenario family swap shifts distribution (`SEVERE` > `BASELINE` at p99)
- Property closer to the typical track centerline gets higher mean peak wind than a far property
- Output JSON validates against schema
- `python3 app.py port --typhoon` exits 0 with `MKM_CATCHMENT=halong`

**Done when:** `MKM_CATCHMENT=halong python3 app.py port --typhoon --num-typhoon-events 1000` produces a Hanoi peak-wind distribution file in <2 minutes, with quantile spread that reflects the configured tail.

---

## Phase 1.8 — Tests, calibration knobs, sanity checks

**Files**
- All `tests/models/typhoon/test_*.py` listed in the module layout
- Pytest discipline: one test file per source module + one integration test in `test_pipeline.py`

**Calibration knobs (externalized to `data/catch/halong/storm.py`)**
- Scenario-family parameter sets `(mu, sigma, v_T, alpha)` for peak wind
- Regime mixture weights at genesis
- Motion mean and sigma per regime
- Land-decay rate `k_land`
- Size–intensity coupling coefficients
- Wind-field `alpha_eye`, `L`, `p`, `eps_max`, `c_eps`, `rho_surf_land`
- Plausibility weights (kept loose in Phase 1)

**Sanity / validation sketches** (full historical calibration is Phase 3)
- Visual: do tracks pass through northern Vietnam at a plausible rate?
- Distribution: Hanoi peak-wind quantiles within order-of-magnitude of historical typhoon impacts (e.g. Yagi 2024, Rammasun 2014)
- Import-discipline test confirms no `data/catch/*` references in `src/models/typhoon/`

**Done when:** all tests green; baseline run reproducible from seed; a calibration-knob change in `halong/storm.py` propagates to outputs as expected without touching model code.

---

## What's deferred to later phases

- Joint surge / rain hazard layer + residual copula (Phase 2)
- Regime transitions over time (Phase 1 fixes regime at genesis)
- Environmental forcing `z_t` — SST, shear (Phase 3)
- Gust conversion (Phase 3 — interface is in place)
- Holland-profile alternate backend (Phase 3 — interface is in place)
- Real-observation likelihood / best-track assimilation (Phase 3)
- Historical calibration against JMA RSMC Tokyo best-track archive (Phase 3)
- Tight integration with `storm_multi/` sequence machinery (only adjunct invocation in Phase 1)

---

## Acceptance criteria for Phase 1 as a whole

1. `src/models/typhoon/` contains all math; nothing in `src/port/src/` touched
2. No catchment-specific values inside `src/models/typhoon/`; no imports from `data.catch.*` or from the `config` package
3. `data/catch/halong/storm.py` extended with typhoon constants (raw values); no new files in `data/catch/halong/`
4. Catchment params reach the model via the `config` package + a single boundary adapter at `app/commands/port/stages/typhoon_stage.py`
5. `MKM_CATCHMENT=halong python3 app.py port --typhoon --num-typhoon-events 1000` produces a per-property peak-wind distribution at Hanoi locations
6. Scenario-family swap demonstrably moves the upper tail
7. Test suite green; import-discipline test confirms catchment-agnosticism of the model
