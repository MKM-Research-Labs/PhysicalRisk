# Storm→Wind Coupling Specification

**Stage 1 of the Wind-into-PRS initiative — coupled storm+typhoon event generation**

| | |
|---|---|
| **Status** | **Signed off** — baseline rev. 3 (2026-06-03, Risk); **v5.0 records Stage 2 + Stage 3 + Stage 4 + Stage 5 + Stage 6 as implemented** (2026-06-03). |
| **Version** | 5.0 |
| **Date** | 2026-06-03 |
| **Owner** | Risk (risk@kerrshearer.co.uk) |
| **Scope** | Generation-layer coupling only. Pricing union, downstream UI/docs, and tests are later stages. |
| **Calibration status** | The coupling-strength parameter β is provisional ("expert conjecture"); calibration is an open work item (§9). Shipped as `config.port.COUPLING_BETA = 0.5` with a `--coupling-beta` CLI override. |

> **Changelog**
> - **v5.0 (2026-06-03)** — Stage 6 (peril outcomes in pricing) implemented; §11 renumbered to Stage 6 (peril outcomes) / Stage 7 (downstream visualisation) / Stage 8 (tests + revalidation), item 6 marked ✅. `_wind_union` now also returns the flood∩wind intersection (`joint_count`/`joint_spread_bps`); `pricing.py::_process_property` emits a `prs_perils` block with all four outcomes — `flood_only`, `wind_only`, `flood_or_wind` (union), `flood_and_wind` (intersection) — each `{count, spread_bps}`, satisfying `union = flood + wind − joint`. The four spreads also appear under `term_structure['perils']`. `generator.py::attach_spread_decomposition` attaches `peril_outcomes` at the BRI-adjusted node (fallback property node), branching the four outcomes off the end of the gauge→SHE→SHD→property→BRI waterfall. The flood `severe` spine, gauge basis and flood-vs-gauge decomposition stay unchanged — wind is a pure intersect/union at the property node, no gauge propagation. The interim Stage 5 `term_structure['union']`/`prs_union_spread_bps`/`wind_count`/`union_count` are migrated into `prs_perils`. Catchments without a typhoon stage emit no `prs_perils` block (byte-identical flood-only fallback). No change to the coupling mathematics (§2–§5).
> - **v4.0 (2026-06-03)** — Stage 5 (wind into pricing) implemented; §11 item 5 updated. `is_prs_wind` (binary damage-onset: `peak_sustained_ms ≥ threshold_ms`, the per-property BRI-adjusted threshold) added to `models/winddamage/threshold.py`; `pricing.py::_process_property` now computes the flood∪wind union over the 1:1-paired event set and exposes it as `term_structure['union']` / `prs_union_spread_bps` plus `wind_count`/`union_count`. The flood-only `prs_spread_bps`, gauge basis and decomposition are unchanged (flood/wind/joint decomposition is Stage 6); catchments without a typhoon stage are byte-identical (flood-only fallback). No change to the coupling mathematics (§2–§5).
> - **v3.0 (2026-06-03)** — Stage 4 (retire `typhoon_storm_link.py`) implemented; §11 item 4 updated to reflect delivered code. The severity-bucket linkage is replaced by a true 1:1 join on the shared `event_id` in the new `src/port/storm_typhoon_pairing.py`; `core_storms.py` simplified. No change to the coupling mathematics (§2–§5).
> - **v2.0 (2026-06-03)** — Stage 2 (joint event driver) and Stage 3 (genesis conditioned on `z`) implemented; §11 updated to reflect delivered code. No change to the coupling mathematics (§2–§5) signed off at baseline.
> - **v1.0 (baseline, rev. 3, 2026-06-03)** — coupling spec signed off (the directed-asymmetric band-draw map, §1–§10).

---

## 1. Purpose and motivation

The Property Risk Spread (PRS) is today **flood-only and frequency-only**:

```
spread_bps = count(is_prs_flood) / num_storms × 10,000
```

(`src/port/src/property/hc/pricing.py`). A full continuous-severity **wind-damage** model already exists (`src/models/winddamage/`, sigmoid vulnerability + BRI shift → `typhoon/damage/EVT-*.json`) but is **not** wired into pricing. The two hazards are also generated **independently**: ~20k basin-wide storms vs a separate ~50-event track-based typhoon ensemble, joined only by a post-hoc severity-bucket linkage (`src/port/typhoon_storm_link.py`) used solely in the UI.

The objective of the wider initiative is to make PRS a combination of **flood OR wind loss**. The objective of **this stage** is the prerequisite: replace independent generation with a single coupled event set of **N events** (N = 1000 in development, 20,000 in production), each carrying **one storm sequence and one typhoon, paired 1:1**, such that:

- heavy rain and strong wind co-occur in the **joint tail**;
- **low-rain / high-wind is impossible** (a strong wind requires a strong storm);
- **high-rain / low-wind is permitted at ordinary intensities** ("rain without wind");
- but in the **storm tail, wind is pulled up** (an extreme storm reliably brings strong wind).

This makes wind inherit the flood frequency basis automatically (one event, one denominator) and replaces the manufactured severity-bucket linkage with a true 1:1 pairing.

---

## 2. Coupling principle — directed and asymmetric

The relationship is a **direction of causality**, not a symmetric severity function emitting two matched hazards:

- **Directed:** storm severity → wind. Rain is never a function of wind.
- **Bounded above (ceiling):** the wind's severity rank can never exceed the storm's severity rank. This forbids low-rain/high-wind.
- **Bounded below in the tail (floor):** as the storm becomes rarer, a rising floor pulls the wind up, so extreme storms are reliably windy.
- **Free in between:** at ordinary intensities the floor is near zero, so a wet-but-calm event ("rain without wind") is allowed.
- **Stochastic, not hard-coded:** wind is a conditional *draw* within `[floor, ceiling]`, not a deterministic twin of rain.

---

## 3. Definitions

### 3.1 Severity latent `z`
The per-event upstream driver is **`base_intensity`** — the `max(0.1, Normal(mean_cat, std_cat))` draw made once per event in `src/port/src/storm_multi/generators/batch_generator.py:95`. It is the storm's meteorological severity.

The causal DAG is:

```
              intensity_category            (categorical: moderate/severe/extreme/catastrophic)
                     │
              base_intensity  =  z          (continuous severity latent — ONE draw per event)
              /              \
   intensity_factor          Vmax  (peak wind)        ← wind couples to z, the PARENT
        │                       │
   precipitation            wind field
        │                       │
   hydrology → gauge → depth     damage
        │                       │
    flood loss              wind loss
         \                  /
             PRS  (union of triggers — later stage)
```

Precipitation is a **downstream sibling** of wind (`precip = BASE_PRECIPITATION_MM × intensity_factor`), not its parent. Wind therefore couples to **`z`**, not to precipitation. This keeps wind upstream of (and uncontaminated by) hydrology, and is catchment-normalised: `base_intensity` is dimensionless, whereas `precipitation_mm` carries the per-catchment `BASE_PRECIPITATION_MM` scaling.

> **Numerical note.** Within a single catchment, ranking events by `z` is identical to ranking by `total_precipitation_mm` (precip is a positive monotone transform of `z`), so the resulting `Vmax` is unchanged. The choice of `z` matters for cross-catchment comparability, for correctness once the floor/ceiling band is in play, and for any future where `BASE_PRECIPITATION_MM` becomes stochastic — not for development numbers.

> **Persistence gap (Stage 2 task).** `base_intensity` is currently **transient** — passed into `SequenceGenerator.generate()` but not stored on `StormSequence`. Stage 2 must add it as a persisted field. The closest currently-persisted proxies are `avg_intensity_factor` / `cumulative_intensity_factor` (`src/port/src/storm_multi/core/data_structures.py:132-135`).

### 3.2 Severity quantile `q`
`qᵢ ∈ (0,1)` is the empirical rank of `zᵢ` across the N events: `qᵢ = rank(zᵢ) / (N+1)`, with `qᵢ → 1` the most severe storm. Empirical rank over the generated batch is exact and needs no parametric storm CDF.

### 3.3 Catchment wind-exceedance curve `S_cat`
`S_cat(v)` is the scenario-mix-weighted mixture of the per-family `PeakWindParams` survival functions defined in each catchment's `tc.py`:

```
S_cat(v) = Σ_family  scenario_mix[family] · peak_wind_exceedance(v, peak_wind[family])
```

It is evaluated by reusing the existing `peak_wind_exceedance` / `peak_wind_inverse_exceedance` (`src/models/typhoon/genesis.py`) over the mixture, with a 1-D numeric inverse (bisection on the monotone `S_cat`).

> **Re-roled under rev. 3:** `S_cat` defines the **attainable ceiling curve**, *not* the realised marginal. See §7.

---

## 4. The coupling map

For each event with severity quantile `q`, the wind *strength percentile* `ρ_w ∈ [0,1]` (with `ρ_w → 1` the strongest attainable wind) is drawn within a band whose bounds depend on `q`:

```
ceiling(q) = q                              # wind rank cannot exceed storm rank
floor(q)   = 1 − (1 − q)^β                  # rising floor, β ∈ (0, 1]
ρ_w        = floor(q) + B · (ceiling(q) − floor(q)) ,   B ~ Uniform[0, 1]
u          = 1 − ρ_w                        # exceedance probability
Vmax       = S_cat⁻¹(u)                      # peak wind for the event
```

### 4.1 The floor function and the role of β
`floor(q) = 1 − (1 − q)^β` is monotone increasing, satisfies `floor(q) ≤ q` for all `q ∈ [0,1]` (the band never inverts), and `floor(0) = 0`. The single parameter **β unifies the whole design family**:

| β | floor behaviour | regime |
|---|---|---|
| → 0 | `floor → 0` everywhere | **pure ceiling** — no tail pull; rain freely without wind |
| ≈ 0.52 | matches expert anchors below | **recommended interim** |
| = 1 | `floor = q` | **deterministic comonotone** — wind tracks rain exactly |

The interim **β ≈ 0.52** reproduces the expert-conjecture anchors:

| storm `q` | target wind floor | `floor(q)` at β = 0.52 |
|---|---|---|
| 0.90 | 0.70 | 0.70 |
| 0.99 | 0.90 | 0.91 |
| 0.999 | ≈ full TC | 0.97 |
| 0.50 | — | 0.30 |
| 0.10 | — | 0.05 |

### 4.2 Within-band draw
`B ~ Uniform[0,1]` distributes the wind within `[floor(q), q]`. Because the floor now provides the tail "pull", `B` does not need a skew; an optional Beta on `B` remains available as a secondary shape control if later required. **β is the primary correlation knob.**

### 4.3 Code intercept
The change is surgical. In `src/models/typhoon/genesis.py::sample_genesis`, the independent
`scenario = sample_scenario_family(...)` + `v_max_ms = sample_peak_wind(config.peak_wind[scenario], rng)`
is replaced by `v_max_ms = S_cat_inverse(1 − ρ_w)`, where `ρ_w` is derived from the paired storm's `q`. `scenario_family` becomes a *derived label* (the band that `u` falls in), retained only for downstream tagging.

---

## 5. Worked behaviour (β = 0.52, real `tc.py` numbers)

Storm marginal (both catchments): categories moderate 0.40 / severe 0.35 / extreme 0.20 / catastrophic 0.05; base intensities 1.0 / 1.8 / 3.0 / 5.0.

### 5.1 halong — composite over {HISTORICAL μ30 α3, BASELINE μ35 α2.5, MODERATE μ40 α2, SEVERE μ45 α1.5, EXTREME μ50 α1.2}

| event | `q` | band `[floor, ceiling]` | wind outcome |
|---|---|---|---|
| catastrophic | 0.99 | [0.91, 0.99] | full TC mode — super-typhoon, ~75–90 m/s, guaranteed strong |
| extreme | 0.90 | [0.70, 0.90] | strong wind even at the band floor (~70th-pct ≈ severe typhoon-force); never calm |
| median | 0.50 | [0.30, 0.50] | modest wind; can sit low (rain-without-much-wind lives here) |
| mild | 0.10 | [0.05, 0.10] | calm, ~12–20 m/s, regardless of `B` |

### 5.2 thames — mild bands (μ 14–27, caps 35–50)

Identical logic, but the ceiling curve itself is low: even a catastrophic storm at the top of its band tops out near ~45–50 m/s (a strong gale, **never typhoon force**); most events sit well below. The per-catchment envelope falls out **entirely from the existing `tc.py` bands** — no recalibration of the wind model.

---

## 6. Event identity, counts, pairing, fallback

- **Counts:** generate N events; the **typhoon count is slaved to the storm count** (`--num-storms`), not a separate `--num-typhoon-events`. 1:1, no surplus or dropped events.
- **Identity:** each event carries a shared `event_id` (e.g. `EVT-00001`) on both its storm sequence and its typhoon; the post-hoc `typhoon_storm_link.py` is retired (later stage).
- **Reproducibility:** a per-event seed is added to the storm sequence (none exists today).
- **Fallback:** catchments without a `tc.py` generate no wind component; wind contributes 0 and PRS is flood-only (consistent with `OPTIONAL_STEPS` in `src/lineage/manifest.py`). Catchments with `tc.py` (halong, thames) get a — possibly mild/calm — wind on every event.

---

## 7. Effect on the wind marginal (important)

Because winds are gated below the storm-severity ceiling, the **realised marginal distribution of `Vmax` shifts downward** relative to the standalone typhoon model: strong winds appear only in the high-`q` tail, and overall wind exposure is lower than the unconditional `PeakWindParams` mixture would produce. The `tc.py` bands now define the **attainable ceiling**, not the realised frequency.

This is the necessary and deliberate cost of "rain without wind, but no wind without rain." It **supersedes** an earlier (rev. 1) design idea of preserving the wind marginal — marginal-preservation is incompatible with the asymmetric directed coupling and is explicitly **not** a property of this model.

---

## 8. Validation criteria

A correct implementation must satisfy, over a generated event set:

1. **Stochastic ordering (no low-rain/high-wind):** for every event, wind strength-percentile `ρ_w ≤ q`. No exceptions.
2. **Tail pull (rising floor):** the minimum wind percentile among events in each high-`q` band rises with `q` and tracks `floor(q) = 1 − (1−q)^β` within sampling error.
3. **Rain-without-wind exists:** at moderate `q` (floor near 0), some events draw low `Vmax` — the asymmetry has not collapsed to comonotone.
4. **Positive association:** `corr(q, Vmax) > 0` and `E[Vmax | q]` non-decreasing in `q`.
5. **Calm floor at low `q`:** bottom-decile-`q` events stay below a low wind threshold regardless of `B`.
6. **Count parity / bijection:** N storms == N typhoons, with a bijective `event_id` pairing.
7. **Per-catchment envelope:** halong top events reach super-typhoon `Vmax`; thames top events stay `< ~50 m/s`.
8. **β limits:** β → 0 reproduces the pure-ceiling behaviour; β = 1 reproduces deterministic comonotone (`ρ_w = q`). Useful as boundary regression tests.

---

## 9. Parameters and calibration

### 9.1 Parameter inventory

| Parameter | Value / source | Status |
|---|---|---|
| N (event count) | `--num-storms`; typhoon count slaved | existing flag, reused |
| Severity latent `z` | `base_intensity` | **persist as new `StormSequence` field (Stage 2)** |
| Coupling strength `β` | new config; default ≈ 0.5 | **new — primary knob; calibration open** |
| Within-band draw `B` | `Uniform[0,1]` (optional Beta skew) | new — secondary |
| Ceiling curve `S_cat` | `tc.py` `peak_wind` + `scenario_mix` | calibration **unchanged**; re-roled as ceiling |
| Storm intensity calibration | `config/port.py` weights + `BASE_INTENSITY_PARAMS` | **unchanged** |

### 9.2 Calibrating β (open work item)

β is provisional expert conjecture. Calibration routes, in rough order of rigour:

1. **Empirical joint dependence.** Co-located historical precipitation and wind for each basin — ERA5 reanalysis and/or IBTrACS (TC `Vmax`) joined to precipitation — then regress the *conditional lower quantile* of wind-percentile on storm-percentile; that empirical lower envelope **is** `floor(q)`, and β is its fit. Per-catchment: South-China-Sea super-typhoons for halong; an extratropical windstorm catalogue (e.g. XWS) for thames.
2. **Target upper-tail dependence.** Choose β to hit a specified `λ_U = P(wind extreme | rain extreme)` — a single defensible statistical target rather than a curve.
3. **Expert anchors + sensitivity (interim, recommended now).** Adopt the 70%/90% anchors (β ≈ 0.5), document as an expert prior, and attach a **PRS sensitivity study over β ∈ [0.3, 0.7]** showing how the wind contribution to the spread moves. This avoids being blocked on data; upgrade to route 1 when basin data is in hand.

Ship β as an explicit, documented config parameter (default ≈ 0.5).

---

## 10. Assumptions and limitations (model-risk notes)

- **Directed, asymmetric dependence.** Wind is bounded above by storm severity and pulled up in the tail by the floor; it is free below at ordinary intensities. A deliberate causal asymmetry — a storm enables and, in the tail, compels wind, but ordinary rain does not.
- **The wind marginal is conditional and shifts downward** vs the standalone typhoon model (§7). The `tc.py` bands define the attainable ceiling, not realised frequency.
- **Severity ordering = `base_intensity`** (≡ precipitation within a catchment).
- **Spatial decoupling remains.** Storms are basin-wide; typhoons are track-based. The coupling is at the severity level only — not physical co-location. A physically unified track that deposits both rainfall and wind (Strategy B) is explicitly **out of scope** for this stage.
- **β is provisional** until calibrated (§9.2).

---

## 11. Relationship to the staged plan

This document is **Stage 1** (the coupling spec). Subsequent stages:

2. **Joint event driver** — persist `base_intensity`; slave typhoon count to `--num-storms`; shared `event_id` pairing; per-event seed. **✅ Implemented (v2.0).** `StormSequence` carries `event_id` / `base_intensity` / `seed`; `batch_generator` assigns `EVT-NNNNN` + per-event seeds from a separate `SeedSequence` stream (storm draws stay bit-identical); `simulate_typhoon_events` accepts `event_ids` to slave the count; the typhoon stage loads drivers from `storm_sequences.json`.
3. **Condition typhoon genesis on `z`** — implement the §4 intercept in `genesis.py` / the typhoon pipeline. **✅ Implemented (v2.0).** `genesis.coupled_genesis_wind` realises the §4 band draw (`coupling_floor`, `mixture_peak_wind_exceedance`, `mixture_peak_wind_inverse`, `derive_scenario_family`); `sample_genesis` takes a `v_max_override`; `ParticleFilter` accepts `genesis_v_max_override` / `genesis_scenario_override` so every particle of an event starts at the one coupled `Vmax` (SMC still explores track/size/location/regime). `simulate_typhoon_events` gained `event_severity_q` / `event_seeds` / `coupling_beta`; the typhoon stage computes `q_i = rank(z_i)/(N+1)` from the drivers and reseeds per event. β is `config.port.COUPLING_BETA` (default 0.5) with a `--coupling-beta` override.
4. **Retire `typhoon_storm_link.py`** — replace the severity-bucket linkage with the true 1:1 map; simplify `src/routes/propertyts/core_storms.py`. **✅ Implemented (v3.0).** `typhoon_storm_link.py` (and its test) deleted; replaced by `src/port/storm_typhoon_pairing.py`, which builds the pairing by a direct join on the shared `event_id` (`storm_sequences.json` sequence → `typhoon/damage/<event_id>.json`) — no severity-bucket alignment, no precip/wind ranking. Public API: `get_pairing()` (cached), `invalidate_cache()`, `typhoon_for_storm(sequence_id)`, `storm_for_typhoon(event_id)`, with `build_pairing()` returning `storm_to_typhoon` / `typhoon_to_storm` / `diagnostics`. Consumers updated: `wind_impact.py` (`typhoon_for_storm`), `core_storm_list.py` (`get_pairing`). `core_storms.py` simplified to derive `sequence_id → event_id` directly from the already-loaded `_storm_meta` and surface `scenario_family` from the per-event damage file (no pairing-module dependency).
5. **Wind into pricing** — define `is_prs_wind`; union trigger in `pricing.py::_process_property`; flood-only fallback. **✅ Implemented (v4.0).** `is_prs_wind(wind_row)` in `models/winddamage/threshold.py` is the binary damage-onset trigger `peak_sustained_ms ≥ threshold_ms` (the threshold is BRI-adjusted per property at damage-roll time, so resilient buildings fire less readily — wind-without-flood frequency is governed by where that exceedance sits). `_process_property` builds the flood∪wind PRS count over the shared `event_id` (flood leg keyed by `storm_id`==`sequence_id` → `event_id` via `storm_sequences.json`; wind leg keyed by `event_id` from a once-built `typhoon/damage/EVT-*.json` index), deduping events that trigger both. PRS stays a binary frequency payout — the continuous wind damage amount (the `wind-impact` insurance view) is deliberately NOT fed into the spread. The flood-only `prs_spread_bps`/basis/decomposition are untouched. (In Stage 5 the union was surfaced as the interim `term_structure['union']`/`prs_union_spread_bps`/`wind_count`/`union_count`; **Stage 6 supersedes this** with the four-outcome `prs_perils` block — see item 6.) No typhoon stage → `_wind_damage_index` empty → union==flood, output byte-identical.
6. **Peril outcomes in pricing** — emit all four peril outcomes at the property/BRI node. **✅ Implemented (v5.0).** `_wind_union` now also returns the intersection (`joint_count`/`joint_spread_bps`) alongside the wind and union legs. `_process_property` emits a `prs_perils` block — `flood_only`, `wind_only`, `flood_or_wind` (union), `flood_and_wind` (intersection) — each `{count, spread_bps}`, satisfying inclusion-exclusion `union = flood + wind − joint` with `joint ≤ min(flood, wind)`. The four spreads also ride alongside the flood spine as `term_structure['perils'][<outcome>].prs_spread_bps` (flat term structure). The flood `severe` spine, gauge basis and the flood-vs-gauge spread decomposition stay unchanged — wind is a **pure intersect/union at the property/BRI node with no gauge propagation**. `attach_spread_decomposition` attaches `peril_outcomes` to each asset, preferring the BRI-adjusted node (`bri_pc['prs_perils']`) and falling back to the property node — the four outcomes branch at the BRI-adjusted end of the gauge→SHE→SHD→property→BRI waterfall. The interim Stage 5 `term_structure['union']`/`prs_union_spread_bps`/`wind_count`/`union_count` are migrated into `prs_perils` (nothing downstream consumed them yet). No typhoon stage → no `prs_perils` block, output byte-identical (flood-only fallback).
7. **Downstream** — Basis Explorer, term structure, governance docs visualise/decompose the spread into the four peril outcomes (flood-only / wind-only / flood-or-wind / flood-and-wind).
8. **Tests + revalidation** — the §8 criteria, fallback tests, and re-validation of flood numbers under the new N.
