# BRI Fire-Resilience Credit Model — Build Handoff

**Last updated:** 2026-06-05 (end of day)
**Worktree:** `.claude/worktrees/sweet-borg-e9d234` (branch `claude/sweet-borg-e9d234`)
**Status:** Stage 1 (Model A — Poisson initiation) BUILT, 19/19 tests passing, ruff clean, **NOT committed**.
**Next:** Stage 2 — the 15-minute stepwise progression engine (Models B/C/D) + the point-of-no-return gate.

This document is a self-contained restart brief. Read it cold tomorrow and you should be able to resume without re-deriving anything.

---

## 1. What this model is

A **fire-resilience credit model** for BRI (Building Resilience Index). It is a new hazard module designed to sit **pari-passu with the existing 10,000-storm Monte Carlo engine** so that fire loss aggregates into the **same resilience-credit currency** as wind/flood. Lenders/insurers/developers get a credit-based fire-protection product (extensible later to wind+flood).

Two reference initiatives it must align with (see memory files):
- `wind_into_prs_initiative` / `bow_baw_scenarios` — the coupled storm+typhoon engine fire must be pari-passu with.
- The output currency is a **resilience credit**: `LossFreq = (N_partial + N_total)/N_sim`, `ContainmentRate = N_contained/N_sim`.

**Source doc:** `docs/fire/Can you review the BRI user handbook on building r.pdf` (48pp). NOTE: this is **not a real handbook** — it is an exported Perplexity AI research conversation. Its structure is sound but **all numbers are uncited, uncalibrated AI seed priors**. (The PDF may not be present in this worktree — it lived in a temp `docs/fire/` previously. The numbers we need are reproduced in §6 below and in `config/fire_matrices.json`, so the PDF is not required to proceed.)

### Key principle (do not violate)
**BRIFireScore is a LATENT resilience modifier on transition probabilities — NEVER a direct outcome.** Resilience changes the *odds* of moving toward containment vs. loss; it never directly sets the loss.

### Governance separation — 4 component models
- **Model A — Initiation / Exposure Frequency** (BUILT): Poisson `N_i ~ Poisson(λ_i)`; only a subset of draws instantiate a fire (analog of storm-event generation).
- **Model B — Fire Growth & Intensity** (TODO): 15-min steps, latent intensity `I_t`.
- **Model C — Detection, Suppression & External Response** (TODO): incl. vertical/height penalty for top floors.
- **Model D — Containment, Loss & Resilience Credit** (TODO): produces the credit.

---

## 2. The working philosophy (IMPORTANT — read first)

Per explicit user direction (memory: `feedback-make-up-numbers`):
- **We are here to MAKE UP the numbers.** There is no calibration data and that is fine. Produce concrete, physically-defensible **seed** values, clearly labelled as placeholders. Do **not** list "no calibration data" as a blocker or ask for data. Calibration is a one-line future footnote, not a gating item.
- **Pick one formulation and show it working.** Do not treat "two model formulations need reconciling" as a blocker. DECISION (2026-06-05): we use the **discrete 8-state Bayesian state machine**, NOT the continuous I/X/U/V/L/K equations. The continuous equations remain a conceptual cross-check only.
- User also wants the stepwise mechanics understood: *how* we move state→state, and crucially the **point of no return** when the fire becomes uncontrollable.

Other standing user constraints (from project memory):
- **Never modify `data/` files** (property.json corruption incident 2026-04-09). `data/` is a symlink to an external SSD.
- **Never run port generation without explicit user permission.**
- **Governance data must be version-controlled, NOT in `data/`.** All fire model numbers live in `config/` (version-controlled), never in `data/`.
- **Never delete files/features without preserving their tests.**

---

## 3. The 8-state machine (the heart of the model)

State vector `P_t = [p0, p1, ..., p7]` over 15-minute steps. Each `FireState` enum value is the index into `P_t` and into the rows/cols of the 8×8 transition matrices.

| Idx | State | Role |
|-----|-------|------|
| 0 | S0_ExposureOrIgnition | transient (entry) |
| 1 | S1_Growth | transient |
| 2 | S2_Detected | transient |
| 3 | S3_InternalResponse | transient |
| 4 | S4_ExternalResponse | transient |
| 5 | **S5_Contained** | **absorbing SUCCESS** |
| 6 | S6_PartialLoss | terminal loss |
| 7 | S7_TotalLoss | terminal loss |

Happy path: `S0 → S1 → S2 → S3 → S4 → S5_Contained`. Failure drains into `{S6_PartialLoss, S7_TotalLoss}`.

### The point of no return (PNR) — the central concept
Define a **latent building-scale intensity `I_t`** that grows each step. The PNR is the first step where:

> `I_t > I_crit` **and** no active suppression has yet "bitten" (taken effect).

At that step, **all transition columns INTO S5_Contained collapse to ≈0**. The chain becomes absorbing into `{S6, S7}`, with S7 dominating. Mechanically it is a **controllability race**:

> `time_to_detect + time_to_suppress`  **vs**  `time_for I_t to reach I_crit`

If suppression bites before `I_t` crosses `I_crit` → containment is still reachable. If not → PNR, switch to the `point_of_no_return` transition matrix.

Credit (Model D): `Credit = (N_partial + N_total) / N_sim` (and the containment-rate complement).

---

## 4. Files built in Stage 1 (all in this worktree, all UNCOMMITTED)

```
config/fire_matrices.json          # ALL seed numbers + 3 example 8x8 matrices (governed data)
config/fire.py                     # enums + dataclasses + load_fire_config() JSON loader
src/models/fire/__init__.py        # package docstring
src/models/fire/data_structures.py # AssetFireFeatures, IgnitionDraw, AssetInitiationResult
src/models/fire/initiation.py      # Model A: modifiers, asset_lambda, Poisson simulation
tests/models/fire/__init__.py
tests/models/fire/test_initiation.py  # 19 tests, all passing
```

### config/fire.py public surface
- Enums: `FireState` (S0..S7, int values 0-7), `InitiationClass` (7 entry-point classes).
- Dataclasses: `FireRunConfig` (n_sim=1000, step_minutes=15, max_steps=200, horizon_years=1.0; `.horizon_hours` property = 50.0), `InitiationConfig`, `ProgressionConfig`, `FireModelConfig`.
- Loader: `load_fire_config(matrices_path=DEFAULT_MATRICES_PATH, run=None) -> FireModelConfig`. Strips `_doc`/`_meta` keys recursively; pops the `classes` list out of the priors block into `InitiationConfig.initiation_classes`; converts effectiveness `[min,max]` lists to tuples.
- `DEFAULT_MATRICES_PATH = Path(__file__).parent / "fire_matrices.json"`.

### src/models/fire/initiation.py public surface (`__all__`)
`m_occ, m_proc, m_cond, m_protection, m_history, asset_lambda, sample_initiation_class, simulate_asset_initiation, simulate_portfolio_initiation`
- All modifiers take `(features: AssetFireFeatures, cfg: InitiationConfig)` and fall back to neutral `1.0` on missing/unknown options.
- `m_proc` raises (never lowers) the type base via the business-rates override (Restaurant ⇒ 1.25).
- `m_protection` maps each protection-field resilience level to its index in `RESILIENCE_LEVELS`, averages, rounds to nearest level, looks up the multiplier.
- `m_history` keys on FireDamageSeverity + recency (`years_since_last_fire <= recent_years`).
- Randomness flows through one caller-owned `np.random.Generator` (typhoon-model convention).

### src/models/fire/data_structures.py
- `AssetFireFeatures` (CDM-derived input bundle — see §5 for field provenance): `asset_id, commercial_type, occupancy_status, business_rates_category, property_condition, protection_levels: List[str], fire_damage_severity, years_since_last_fire, number_of_storeys`.
- `IgnitionDraw(draw_index, count, fire, initiation_class)`.
- `AssetInitiationResult(asset_id, lambda_annual, lambda_effective, n_sim, n_fires, fire_probability, class_counts, draws)` with `.to_dict()`.

---

## 5. CDM field provenance (v2 — authoritative)

DECISION (2026-06-04): use **CDM v2** (the live repo schema), not v1. v2 removed `FireLoadRating, IndustrialProcessRisk, SprinklerSystem, FireSuppressionType, SecuritySystem, EmergencyPower` as standalone fields. Process-load is **re-derived** as a latent score from `CommercialType + UseClassUKO + BusinessRatesCategory`.

Source schemas (confirmed to exist, exact option vocabularies):
- **`src/port/cdm/asset/commercial/schema.py`**
  - `COMMERCIAL_TYPE_OPTIONS = ["Office","Retail","Hotel","Leisure","Healthcare","MultiFamily","MixedUse","Other"]`
  - `OccupancyStatus`: `["Fully occupied","Partially vacant","Vacant"]`
  - `PropertyCondition`: `["Excellent","Good","Fair","Poor","Very poor"]`
  - `BusinessRatesCategory`: `["Shop and Premises","Office","Hotel","Restaurant","Leisure","Mixed","Other"]`
  - `PlantRoomLocation`: `["Basement","Ground floor","Roof","External"]`
  - `ServiceCore`: `["Central core","Multiple cores","External core","None"]`
  - `NumberOfStoreys` (integer), `UseClassUKO` (string), `LastMajorWorksDate` (date).
  - **No `HeightMeters`/`FloorLevelMeters` in commercial schema** → use `NumberOfStoreys` for the height/vertical penalty.
  - Industrial/warehouse/manufacturing live in a **separate `asset/industrial/` schema** — Stage 1 (and Stage 2) are scoped to the 8 CommercialType classes only.
- **`src/port/cdm/asset/resilience.py`**
  - `RESILIENCE_LEVELS = ["Not assessed","Partial","Meets minimum","Enhanced","Verified"]` (5 levels; index 0-4). **Import this; do not re-declare it** (single-source rule — Stage 1 already imports it).
  - Fire-protection fields (5-level menus unless noted):
    - Passive: `StructuralFireResistanceAdequate`, `CompartmentsProvided`, `FireStoppingAtPenetrations`, `ExternalMaterialsFireResistant`.
    - Active/detection: `AutomaticDetectionInstalled`, `SuppressionSystemsInstalled`.
    - Response: `AccessRouteResilient`, `BusinessContinuityPlanInPlace`, `EmergencyProceduresTested`.
    - Scores: `FireHazardClass`, `BRIFireScore` (decimal 0.0-1.0), `BRIFireRating`.
- **`src/port/cdm/asset/history.py`**
  - `FireDamageSeverity`: `["None","Minor","Moderate","Severe","Total loss"]`
  - `ClaimsHistory` (integer), `LastFireDate` (date), `VacancyCount`, `TenancyDuration`.

**Stage-2 TODO:** write a boundary adapter that reads a commercial-asset CDM record and produces `AssetFireFeatures` (Stage 1 currently takes features directly; nothing reads the raw CDM yet). `years_since_last_fire` is derived from `LastFireDate` vs the run date.

---

## 6. Seed numbers reference (mirror of config/fire_matrices.json)

All values are **engineering-judgement seeds** (placeholders), physically defensible, to be recalibrated later.

### Model A — initiation
`λ_i = λ_{0,c} · m_occ · m_proc · m_cond · m_protection · m_history`, fire if `Poisson(λ_effective) >= 1`, `λ_effective = λ_annual · horizon_years`.

- **Base annual freq λ_{0,c}** by CommercialType (events/yr): Office 0.02, Retail 0.03, Hotel 0.035, Leisure 0.03, Healthcare 0.025, MultiFamily 0.03, MixedUse 0.04, Other 0.04.
- **m_occ** (0.75–1.30): Fully occupied 1.00, Partially vacant 0.90, Vacant 0.85.
- **m_proc** (1.00–2.50) by type: Office 1.00, Retail 1.10, Hotel 1.25, Leisure 1.25, Healthcare 1.10, MultiFamily 1.05, MixedUse 1.15, Other 1.15. Business-rates override: Restaurant 1.25 (raises only).
- **m_cond** (0.85–1.40): Excellent 0.85, Good 0.95, Fair 1.05, Poor 1.20, Very poor 1.40.
- **m_protection** (0.85–1.10) by resilience level: Not assessed 1.10, Partial 1.00, Meets minimum 0.95, Enhanced 0.90, Verified 0.85. (Derived as mean level across AutomaticDetectionInstalled, SuppressionSystemsInstalled, EmergencyProceduresTested.)
- **m_history** (0.90–1.60, recent_years=5): no_prior 1.00, old_minor 1.05, recent_minor 1.10, recent_moderate_or_severe 1.40.
- **Initiation-class priors** (each row sums to 1.0). Classes order: `[InternalElectrical, KitchenOccupant, PlantTechnical, ProcessRelated, BasementService, ExternalExposure, Other]`.
  - Office: `[.35,.10,.15,.05,.15,.10,.10]`
  - Retail: `[.30,.30,.10,.05,.10,.10,.05]`
  - Hotel: `[.28,.25,.15,.05,.12,.10,.05]`
  - Leisure: `[.30,.22,.13,.05,.10,.10,.10]`
  - Healthcare: `[.32,.12,.20,.06,.12,.08,.10]`
  - MultiFamily: `[.35,.30,.08,.02,.10,.08,.07]`
  - MixedUse: `[.28,.12,.15,.12,.10,.08,.15]`
  - Other: `[.28,.12,.15,.12,.10,.08,.15]`

### Models B/C/D — progression seeds (already in JSON, consumed in Stage 2)
- **growth_per_step_intensity** (additive `I_t` growth per 15-min step before suppression): well_compartmented 1.5, poorly_compartmented 3.0.
- **i_crit_by_suppression** (critical intensity threshold): strong_suppression 75, weak_suppression 25.
- **detection_time_multiplier_by_level** (lower = faster detect; keyed on AutomaticDetectionInstalled level): Not assessed 1.00, Partial 0.90, Meets minimum 0.80, Enhanced 0.72, Verified 0.65.
- **suppression_growth_multiplier_by_level** (lower = more effective; keyed on SuppressionSystemsInstalled level): 1.00, 0.85, 0.75, 0.62, 0.50.
- **passive_effectiveness_ranges** `[min,max]` across the 5 levels: StructuralFireResistanceAdequate [0.60,0.95], CompartmentsProvided [0.55,0.90], FireStoppingAtPenetrations [0.70,0.95], ExternalMaterialsFireResistant [0.65,0.95].
- **response_effectiveness_ranges** `[min,max]`: AccessRouteResilient [0.70,0.95], EmergencyProceduresTested [0.80,0.97], BusinessContinuityPlanInPlace [0.85,0.98].
- **upper_floor_penalty_per_storey** range [1.05,1.60] (height penalty via NumberOfStoreys).

### Three example 8×8 transition matrices (rows = current state S0..S7, row-stochastic)
Stored under `progression.transition_matrices`. The progression engine selects/blends per step from the asset's controllability state.

- **AA_controllable** (strong passive+active, fire heads to containment):
  ```
  S0 [.05,.25,.70, 0 , 0 , 0 , 0 , 0 ]
  S1 [ 0 ,.10,.85, 0 , 0 , 0 ,.05, 0 ]
  S2 [ 0 , 0 , 0 ,.90,.08, 0 ,.02, 0 ]
  S3 [ 0 , 0 , 0 , 0 ,.10,.85,.05, 0 ]
  S4 [ 0 , 0 , 0 , 0 , 0 ,.75,.20,.05]
  S5 [ 0 , 0 , 0 , 0 , 0 , 1 , 0 , 0 ]
  S6 [ 0 , 0 , 0 , 0 , 0 , 0 ,.85,.15]
  S7 [ 0 , 0 , 0 , 0 , 0 , 0 , 0 , 1 ]
  ```
- **weak_controllable** (poor protection, more leakage to loss):
  ```
  S0 [.05,.70,.25, 0 , 0 , 0 , 0 , 0 ]
  S1 [ 0 ,.10,.45, 0 , 0 , 0 ,.45, 0 ]
  S2 [ 0 , 0 , 0 ,.40,.40, 0 ,.20, 0 ]
  S3 [ 0 , 0 , 0 , 0 ,.15,.15,.70, 0 ]
  S4 [ 0 , 0 , 0 , 0 , 0 ,.25,.50,.25]
  S5 [ 0 , 0 , 0 , 0 , 0 , 1 , 0 , 0 ]
  S6 [ 0 , 0 , 0 , 0 , 0 , 0 ,.50,.50]
  S7 [ 0 , 0 , 0 , 0 , 0 , 0 , 0 , 1 ]
  ```
- **point_of_no_return** (S5/Contained column is ZERO for every transient state — chain absorbs into {S6,S7}):
  ```
  S0 [ 0 , 1 , 0 , 0 , 0 , 0 , 0 , 0 ]
  S1 [ 0 , 0 , 0 , 0 , 0 , 0 ,.40,.60]
  S2 [ 0 , 0 , 0 , 0 , 0 , 0 ,.40,.60]
  S3 [ 0 , 0 , 0 , 0 , 0 , 0 ,.40,.60]
  S4 [ 0 , 0 , 0 , 0 , 0 , 0 ,.40,.60]
  S5 [ 0 , 0 , 0 , 0 , 0 , 1 , 0 , 0 ]
  S6 [ 0 , 0 , 0 , 0 , 0 , 0 ,.35,.65]
  S7 [ 0 , 0 , 0 , 0 , 0 , 0 , 0 , 1 ]
  ```

---

## 7. Stage 2 build plan (tomorrow)

Goal: take each fire instantiated by Stage 1 and march it through 15-min steps (max 200 = 50h) to a terminal state, then aggregate to a resilience credit.

Suggested files:
- `src/models/fire/progression.py` — the stepwise engine (Models B/C/D).
- `src/models/fire/data_structures.py` — add `FireProgressionState` (carries `I_t`, current state, step index, suppression-active flag, detected flag), `FireOutcome` (terminal state, step reached, partial/total flag), `AssetCreditResult` (LossFreq, ContainmentRate, mean steps-to-terminal, breakdown by initiation class).
- `tests/models/fire/test_progression.py`.

Design steps:
1. **Per-asset effectiveness extraction (Model C inputs):** from `AssetFireFeatures.protection_levels` and the resilience fields, compute: detection time (base × detection_time_multiplier_by_level), suppression-bite time, suppression growth multiplier, passive effectiveness (interpolate each field's `[min,max]` by its level index / 4), response effectiveness, and the **height penalty** = interpolate `upper_floor_penalty_per_storey` by NumberOfStoreys.
2. **Intensity track (Model B):** `I_{t+1} = I_t + growth_per_step × (passive-damping) × (suppression multiplier once active)`. Compartmentation quality (CompartmentsProvided + FireStoppingAtPenetrations levels) selects well/poorly_compartmented growth. Height penalty scales suppression difficulty / delays bite.
3. **Controllability race / PNR gate:** track `time_to_detect + time_to_suppress` vs steps for `I_t` to reach `I_crit` (choose strong/weak i_crit from suppression level). The first step `I_t > I_crit` with suppression not yet active ⇒ flip the active transition matrix to `point_of_no_return` from then on.
4. **Matrix selection per step:** before PNR, blend/choose between `AA_controllable` and `weak_controllable` by an aggregate controllability score (passive+active+response effectiveness). After PNR, use `point_of_no_return`. (Decide: hard switch vs. continuous blend — recommend hard switch first, show it working, then refine.)
5. **March the chain:** either (a) Monte-Carlo sample one trajectory per instantiated fire using the per-step matrix, or (b) propagate the full `P_t` distribution. Recommend **(a) trajectory sampling** to stay pari-passu with the storm Monte Carlo and reuse the single `rng`. Stop at an absorbing state or `max_steps`.
6. **Model D — credit:** aggregate outcomes across all instantiated fires (and across n_sim): `LossFreq = (N_partial+N_total)/N_sim`, `ContainmentRate = N_contained/N_sim`. Surface BRIFireScore as the latent dial that shifts effectiveness inputs (sensitivity check: raising BRIFireScore must lower LossFreq).
7. **Validation tests:** PNR actually zeroes containment; a high-protection asset has higher ContainmentRate than a low-protection one; reproducibility from one seed; row-stochastic invariants preserved through any blending; outcome distribution sane (most fires contained for good buildings).

Open design choices to decide tomorrow (pick one, show it working — do not stall):
- Hard matrix switch vs. continuous blend at PNR.
- Trajectory sampling vs. full-distribution propagation.
- Base detection/suppression times (in steps) — invent seeds, e.g. detect base 2 steps, suppress base 3 steps, scaled by the level multipliers and height penalty.

---

## 8. Environment & how to run (CRITICAL — SSD is disconnected overnight)

- **The `data/` directory is a symlink to an external SSD** (`/Volumes/David SSD/Docs/PhysicalRisk/data`). The user disconnects it overnight.
- **`config/__init__.py` instantiates a `PortfolioConfig` at import time**, which calls `input_dir.mkdir(...)` under `data/input/thames`. **If the SSD is not mounted, ANY `import config.*` fails at collection time** (FileNotFoundError/FileExistsError on `data/input`). This is an environment dependency, not a code bug.
  - ⇒ **Tomorrow, before running any test or python that imports `config` or `models.fire`, REMOUNT THE SSD.** Verify with `ls "/Volumes/David SSD/Docs/PhysicalRisk/data/input"` (should list halong, rhine, thames).
- **venv lives in the MAIN repo root, not the worktree:** activate with
  `source /Users/newdavid/Documents/PhysicalRisk/venv/bin/activate`
  (The worktree has no `.venv`; `source .venv/bin/activate` fails.)
- **Run the Stage-1 tests:**
  `python -m pytest tests/models/fire/ -q` (expect 19 passed).
- **Lint:** `ruff check config/fire.py src/models/fire/ tests/models/fire/` (line-length E501 is ignored repo-wide; isort enforced — first-party = config, port, routes, loaders, models, visual, catch, floodts).
- **Pytest discovery:** `python_files = ["test_*.py"]` only. Test files MUST be `test_*.py` with `test_*` functions / `Test*` classes. (Non-prefixed `*.py` files under a test dir — like typhoon's `genesis.py` — are helper modules, not collected.)
- **Import path:** `tests/conftest.py` puts both repo root and `src/` on `sys.path`, so imports are `from config.fire import ...`, `from models.fire.initiation import ...`, `from port.cdm.asset.resilience import RESILIENCE_LEVELS`.

---

## 9. Conventions to match (from typhoon model — the template)

- Every `.py` starts with the 19-line MKM copyright header (copy from any existing file, e.g. `config/typhoon.py`).
- Config modules: dataclasses + enums + a loader; spec-referenced docstrings; "all numeric defaults are seeds/placeholders" note. **No numbers embedded in model code** — they come from `config/fire_matrices.json`.
- Model modules: `__all__` export list; pure functions taking an injected `rng: np.random.Generator`; defensive renormalisation of categorical weights; section banners (`# ===...===`).
- Value-object dataclasses with a `to_dict()` for JSON serialisation; invariants enforced in the logic layer, not the dataclass.

---

## 10. Memory files (auto-memory, persist across sessions)

- `fire_bri_model.md` (project) — architecture, v2 decision, build status, what's next. **Updated 2026-06-05** to record Stage 1 done + Stage 2 next.
- `feedback_make_up_numbers.md` (feedback) — invent seed numbers; don't flag missing calibration as a blocker; pick one formulation.
- Other relevant: `data_on_external_ssd.md`, `feedback_port_data_protection.md`, `governance_data_not_in_data_dir.md`, `feedback_venv_activation.md`, `test_architecture.md`, `wind_into_prs_initiative.md`, `bow_baw_scenarios.md`.

---

## 11. Quick-start checklist for tomorrow

1. Reconnect SSD; verify `ls "/Volumes/David SSD/Docs/PhysicalRisk/data/input"`.
2. `cd` to the worktree `.claude/worktrees/sweet-borg-e9d234`.
3. `source /Users/newdavid/Documents/PhysicalRisk/venv/bin/activate`.
4. `python -m pytest tests/models/fire/ -q` → confirm 19 passing (sanity that Stage 1 still works).
5. Decide whether to commit Stage 1 first (currently uncommitted) before starting Stage 2.
6. Build Stage 2 per §7: `src/models/fire/progression.py` + extend `data_structures.py` + `tests/models/fire/test_progression.py`.
7. Keep all new numbers in `config/fire_matrices.json` (the progression seeds are already there).
