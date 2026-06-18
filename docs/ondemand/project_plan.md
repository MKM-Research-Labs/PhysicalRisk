# CDM Asset Review — Phase 2 plan (reassessed)

Going from a **batch** port pipeline to **on-demand** recompute is an
architectural change, not a feature. This version is rewritten after tracing the
timeseries/HC generators, the batch orchestration, and the per-field blast
radius. Sandbox-only throughout — never mutate `data/`.

---

## The two asks
1. Re-run hazard curves on commit of a RED field; show before → after.
2. Zero portfolio: add properties (form) + upload info; price them.

Both sit on one foundation: a **single-asset recompute that IS the batch code
(scoped), run against a sandbox workspace.**

---

## Port pipeline = 4 layers, and it ALREADY re-enters mid-stream

The pipeline is already segmented and already supports "step in the middle". Map
to the user's four layers (steps + their artifact files, from
`src/lineage/manifest/_topology.py`):

1. **Foundational (entities)** — `gauges`→`gauge.json`,
   `synthetic_gauges`→`gauge.json`, `properties`(in: gauge.json)→`property.json`,
   `mortgages`→`loan.json`, `commercial`→`commercial.json`/`commercial_loan.json`,
   `counterparties`→`counterparty.json`, `gaugehd`→`gaugehd/`.
2. **Hazards (all peril generators — not just flood)** — flood storms
   `stressm`(in: gauge.json, gaugehd/)→`gaugets/`,`storm_sequences.json`,
   `sequence_gauge/`; `hazard`(in: gauge.json, gaugets/)→`gaugehc.json`; PLUS the
   wind `typhoon`→`typhoon/ensemble.json`,`typhoon/damage/`, `fire`→`fire/fire.json`
   and `seismic`→`seismic/seismic.json`. typhoon/fire/seismic only need
   foundational data, so they belong HERE, with the storms — not after trades.
   (Orchestrator reordered 2026-06-17 to run them in this layer.)
3. **Hazard curves (asset pricing)** — `propertyts`(in: property.json, gauge.json,
   gaugets/)→`propertyts/`; `propertyhc`(in: propertyts/, gaugehc.json, gauge.json)
   →`propertyhc.json`; + synthetic variants `propertytsd/tse/tsb`→`propertyshd/
   she/bri.json` (the SHE/SHD/BRI waterfall bars) + spread decomposition;
   commercial mirrors; wind-coupled curves `windhazard`/`property_peril_ts`→
   `propertywin/faw/fow.json` (need timeseries + typhoon, so this layer).
4. **Trades** — `blotter`(in: gaugehc.json, counterparty.json, propertyhc/bri)→
   `prs/`,`blotter/eod/`, book/EOD. Now genuinely last, so trades can reflect all
   priced hazards (previously trading ran BEFORE the perils).

**Cut-points = the artifact files between layers.** A layer reads only the files
the layer above wrote.

### The re-entry machinery already exists (this is the crux)
- Every step has a CLI flag (`--propertyhc`, `--hazard`, `--stressm`, `--blotter`
  …). Passing one ⇒ `run_all=False`, only that segment runs
  (`orchestrator.py:77`).
- **Content-hash lineage.** Each step records hashes of its inputs/outputs in the
  manifest. `check_inputs_fresh(step)` (`validation/freshness.py`) compares a
  producer's current output hash vs what the consumer recorded last run → detects
  staleness. `resolve_prerequisites(requested)` (`validation/prerequisites.py`)
  walks the DEPENDENCY_GRAPH upstream and returns the minimal set of steps whose
  inputs are stale; the orchestrator auto-runs them (`orchestrator.py:80-107`),
  printing "Auto-running prerequisites: …". `--strict` blocks instead of
  auto-running.

So: **edit `property.json` → run `app.py port --propertyhc` → lineage sees
property.json changed ⇒ propertyts stale ⇒ reruns propertyts + propertyhc only;
storms (layer 2) unchanged ⇒ skipped.** Exactly "tinker in the middle, re-run
downstream." We DRIVE this; we don't build it.

### The one gap: stage-granularity, not asset-granularity
Lineage re-entry is per-STEP at FILE granularity. `propertyts` hashes
`property.json` as a whole — change one property and the *step* is stale, so the
batch step regenerates **every** property (it loops over all). It does NOT do
single-asset. **We get single-asset by scoping the workspace to one asset**
(the Opt-2 1-property `data/work/`): "regenerate all properties here" = the one.
That's the whole reason the scoped-workspace design is the right fit — it turns
the existing stage-level re-entry into asset-level recompute without touching the
generators.

### Consequence for the tinker question
- Edit a **property/BRI field** (layer 1) → re-enter at layer 3 (`propertyhc`,
  auto-pulling `propertyts`); layers 1-gauge & 2 untouched. ✅ single-asset via
  1-property workspace. (Tier B.)
- Edit a **gauge threshold** (layer 1 that feeds layer 2) → `gauge.json` changes
  ⇒ `hazard` (gaugehc) AND `propertyts` stale ⇒ whole basin reprices. ✅ the code
  would do it, but it's the portfolio ripple — deferred for v1. (Tier C.)
- We hold **storms fixed** (copy gaugets/storm_sequences/gaugehc into the
  workspace, never re-run layer 2) — matching "portfolio + storms stay fixed,
  only the curve moves."

## Reassessment — what the code actually says

### Reassuring
- Property **timeseries generation is stateless, order-independent, fully
  deterministic** (no RNG in propagation; nearest-gauge is local per property,
  `ts/flood/nearest.py`). Single-property regen = bit-identical to batch given
  same inputs/config. The math does not fight us.

### Hard constraints (these shape the design)
1. **Consistency contract.** `gaugehc.json`, `propertyhc.json`, `propertyts/`,
   `sequence_gauge/` are assumed to be from ONE run (same num_sims/seed/gauge
   set). ~6 consumers (Flask routes, trading desk, lineage, docs) read them with
   no validation. ⇒ Recompute only ever touches a **sandbox workspace copy**;
   writes must be atomic (temp + rename).
2. **Config singleton keyed on catchment** (`config`, `MKM_CATCHMENT`). Process
   is catchment-locked; mid-process switches re-init paths but leave stale cached
   imports. Tool is thames-only, so OK — but it constrains design (no live
   catchment switching).
3. **No per-property entry point.** Batch `generate()` deletes all stale
   per-asset files first and writes a portfolio summary
   (`ts/generator.py`, `hc/generator/_generator.py`). A subset run needs these
   guarded.

### Decisive finding — blast radius is tiered
| Tier | RED fields | Cost | Why |
|---|---|---|---|
| **A — instant (<1s)** | BRIWindScore, wind thresholds; BRIFireScore + ConstructionType; BRISeismicScore, SoilVs30 | pure function, no propagation | wind/fire/seismic damage are pure fns over stored event/outcome files, not the flood timeseries |
| **B — per-property regen** | FloorLevelMeters, StiltsHeight, GroundLevelMeters, BRIScore, BRIFloodScore (+ BRIAdjustedFloor) | regen 1 property's flood timeseries → re-price | effective depth `max(0, depth − floor − stilt)` is **baked at timeseries-generation time** (`ts/flood/propagation.py`); HC only counts events |
| **C — portfolio ripple** | FloodGauge.FloodStage.UK.FloodAlert / FloodWarning / SevereFloodWarning | re-run gauge response + every property on that gauge (50–500) | gauge thresholds re-classify severe events → transmission rates for the whole basin |

**Implication:** the gauge thresholds I just marked RED are Tier C — NOT a live
single-asset recompute. Treat gauge edits as "queue a (background) batch", or
disable live recompute for them, with a clear note. Property geometry/BRI = Tier
B (the core case). Wind/fire/seismic = Tier A (cheap bonus).

### The single biggest open question (Spike 1)
Propagation (gauge → property water level via IDW/terrain/retention) is
**independent of floor/stilt/BRI** — only the final subtraction is not. If the
timeseries stored the *pre-subtraction* attenuated depth at the property, Tier B
collapses into Tier A (instant, no re-propagation). The trace says depth is
stored *after* subtraction. **Confirm whether the attenuated/pre-floor depth is
recoverable from the stored event** (`gauge_peak_m`, `retention_factor`, terrain)
— this single fact decides whether the most common edits are instant or need
re-propagation. Do this spike first; it's the value lever.

---

## Architecture principle: dynamic = scoped batch, never a reimplementation
Whatever we build, it must call the **same** generator functions the batch uses
(a `subset=[id]` path that the batch itself also goes through), so there is one
source of truth. Reimplementing the spread math in the tool = the two-code-path
problem already rejected for the waterfall.

### Options (pick one — see decision below)
- **Opt 1 — In-process subset refactor.** Add `regenerate(subset=[id])` to the
  ts + hc generators (guard the stale-delete and summary on subset); batch
  becomes `regenerate(all)`. Tool calls it directly. Fast (ms–100ms). Needs a
  careful generator refactor + tests. Single-source if batch routes through it.
- **Opt 2 — Scoped subprocess.** Stage a 1-property sandbox workspace and run
  the real CLI (`app.py port --propertyts --propertyhc`) in a fresh process.
  Zero divergence (it IS the batch), fresh singleton, no refactor. Slower
  (seconds; subprocess + reload), so before/after is async (spinner). Safest.
- **Opt 3 — Pure re-price only.** Only Tier A (+ Tier B *iff* Spike 1 says depth
  is recoverable) via the pure functions in `src/models/floodrisk/depth_damage.py`
  / `winddamage`. Fastest, no port machinery, but limited coverage and risks a
  second code path for the count/spread step.

**Recommendation:** start with **Opt 2** (safest, proves the UX, no refactor),
and if Spike 1 says the attenuated depth is recoverable, add **Opt 3** for the
instant Tier-A/B path. Migrate to **Opt 1** only if we want everything in-process
and are willing to refactor the generators behind a shared subset entry.

---

## Spikes
### Spike 1 — RESULT: GREEN (done 2026-06-18). Tier B is INSTANT, not re-propagation.
Traced the propagation math and validated on real thames data (100 properties,
76,453 events):
- **Stored `flood_depth_m` = max(0, `attenuated_wse_m` − `elevation_m` −
  `floor_level_m`) EXACTLY** — validated: `attenuated_wse_m − flood_depth_m`
  equals `elevation_m + floor_level_m` with spread 0.0000 across every flooded
  event. `attenuated_wse_m` (the property peak water-surface elevation) is the
  propagated water level and is **independent of floor/ground/BRI**; it is stored
  on EVERY event (flooded or not), in all four modes (normal/bri/shd/she).
- **0 compound events** in thames (`build_compound_property_hydrograph` path).
  So a floor / ground-level / BRI edit re-prices with **pure arithmetic** over
  stored `attenuated_wse_m` — no re-propagation, no subprocess:
  `new_depth_i = max(0, attenuated_wse_m_i − new_ground − new_eff_floor)`;
  `new_damage_i = scalar_depth_damage(new_depth_i)`; severe count =
  Σ(new_depth_i>0 AND `exceeded_severe_i`) [exceeded_severe stored, floor-indep].
  Full Gauge→SHE→SHD→Property→BRI waterfall recomputes instantly (all 4 variant
  files carry the field).
- **Caveat — compound path.** For compound (pulse) events, a currently
  NON-flooded event stores `wse_m = base_level` (true peak lost), so a
  *worsening* edit (lower floor) couldn't be detected. thames = 0% compound, but
  other catchments (typhoon-coupled / pulse storms) may differ. Mitigation:
  detect the `compound` flag per event → fall back to the subprocess re-propagation
  (Opt 2) for those events/catchments. Keep Opt 2 as the correctness oracle.

### Spike 1b — the robust recompute algorithm (validated)
No-op recompute reproduces the batch's stored `flood_count` and property spread
**exactly across all 100 properties** (0 mismatches), via
`flooded_i = round(max(0, attenuated_wse_m_i − elevation_m − floor_level_m),4) > 0`.
Same for SHE and BRI variants. **SHD mismatched (61/100)** because SHD substitutes
the *gauge* elevation for the property's, so the file's `elevation_m` metadata is
NOT SHD's effective threshold. ⇒ **Do not reconstruct thresholds from metadata.**

Robust algorithm — work in DEPTH space, not threshold space:
- **Floor raise (Δfloor>0 — the resilience lever): `new_depth_i =
  max(0, stored_flood_depth_m_i − Δfloor)`.** Uses each mode's stored depth
  (already correct from the batch), so exact for ALL modes incl. SHD, no threshold
  reconstruction. Algebraically identical to the generator (depth = max(0,
  attenuated_wse − (T+Δfloor))), not an approximation.
- **Floor lower (Δfloor<0):** needs the absolute margin for currently-non-flooded
  events → `attenuated_wse_m − T_mode`. T is elevation+floor for property/SHE/BRI;
  SHD needs the gauge elevation (in the file's `nearest_gauges`). Implement, but
  the raise case is the primary one.
- **BRI improve:** maps to an effective-floor uplift via `bri_floor_uplift`
  (pure fn) → same depth-delta on the BRI variant.
- Spread/count = Σ(new_flooded_i AND `exceeded_severe_i`)/num_storms×10000, then
  reuse `_process_property`/decomposition for the full waterfall (single-source).

### Spikes 2–4 — status after Spike 1
- 4 (decomposition modes): ANSWERED — all 4 variant files carry
  `attenuated_wse_m`, so full 4-mode before/after is instant; no 4× propagation.
- 3 (workspace seeding/cost): the instant path needs only the property's variant
  ts files + gaugehc.json (read + arithmetic = ms). Subprocess fallback seeding
  unchanged.
- 2 (subset entry point): only needed for the subprocess fallback/oracle — the
  instant path sidesteps the generator refactor entirely.

---

## Workstream A — recompute + before/after (after spikes)
- A1. Sandbox `data/work/` workspace; point tool read paths there, fall back to
  `INPUT_DIR`. Atomic writes.
- A2. RED gate in commit path; branch by tier (A instant / B regen / C → "needs
  full re-run", deferred).
- A3. Capture before (current `spread_decomposition`), recompute, capture after.
- A4. Before/after on the PRS Waterfall — extend the **shared**
  `phc_basis_waterfall.js` to overlay a second (ghost) series + Δ; do not fork.
- A5. Record spread Δ on the audit entry.
- v1 scope: Tier A + Tier B(normal+bri); gauge edits (C) deferred with a clear
  message; full 4-mode decomposition = v2.

## Workstream B — zero portfolio + add/upload (reuses the foundation)
- B1. Empty/new sandbox per asset + reset-to-seeded (extend `_seed_*`).
- B2. Add-property form from `PROPERTY_SCHEMA` (reuse `makeFieldInput` +
  `cdm_edit`); POST mints `PROP-` id, validates, writes sandbox, audits.
- B3. Upload (CSV or CDM-JSON) → map → per-field validate → append; report
  rejected rows (no silent truncation).
- B4. Pricing a new asset = run the foundation recompute for it against the
  existing gauges/storms in `work/`. Until the foundation lands, new assets are
  CDM-only (perils/waterfall show "not yet priced").

---

## Execution order (tomorrow)
1. Spikes 1–4 (go/no-go + instant-vs-async decision).
2. Foundation: `data/work/` workspace + chosen recompute path (Opt 2 first).
3. Workstream A v1 (Tier A + B, before/after waterfall, audit Δ).
4. Workstream B (empty portfolio → add → upload), pricing via the foundation.

## Decisions
### UPGRADE after Spike 1 (2026-06-18) — recommend instant hybrid, pending user OK
Spike 1 passed, which the locked decision said unlocks Opt 3. Proposed primary
path is a **hybrid that keeps pricing single-source**:
1. **Re-depth shortcut** (replaces only the propagation step): recompute each
   event's `flood_depth_m` / `damage_ratio` / `flooded` from stored
   `attenuated_wse_m` + the new effective floor/ground (pure, ms), write the
   property's ts files into `data/work/`.
2. **Reuse the batch pricing**: run the existing `propertyhc` `_process_property`
   (in-process, stateless, cheap) over the rewritten ts → spread + decomposition.
   No new spread/count code → no second source of truth.
Result: **instant** before/after (no async spinner) for floor/ground/BRI edits,
full 4-mode waterfall. Subprocess (below) stays as the fallback for compound
events/catchments and as the correctness oracle to validate the shortcut.

### BUILT & VALIDATED 2026-06-18
- `tools/cdm_property_editor/recompute.py` — the instant shortcut:
  `severe_count(ts, Δfloor)`, `mode_deltas(field, old, new)` (FloorLevelMeters →
  all modes; BRIFloodScore → bri via `bri_floor_uplift`; ground/other → None
  fallback), `recompute_decomposition(...)` → full before/after waterfall.
  Counting via shared `is_prs_flood` (single-source); compound events → None.
- `tools/cdm_property_editor/_recompute_oracle.py` — validates the shortcut vs a
  REAL `PropertyTimeSeriesGenerator` re-run (temp workspace via
  `MKM_CATCHMENT_INPUT_OVERRIDE`, never touches data/). **Result: EXACT match**
  on a 155-flood property across Δ = +0/+0.5/+1/+2/−0.5 m (155/99/68/23/193 both
  sides). Lowering matches too (stored `attenuated_wse_m` covers non-flooded
  events in the simple path). Next: wire into the tool (workspace + commit flow).

### Locked 2026-06-17 (still valid as the fallback/oracle)
- **Opt 2, scoped subprocess.** Stage a 1-property sandbox workspace, run the
  real CLI (`app.py port --propertyts --propertyhc …`) in a fresh process. Zero
  divergence from batch. Now the FALLBACK (compound events) + oracle, not the
  primary path.
- **Gauge-threshold (Tier C) edits = deferred for v1.** Allow + audit the edit,
  but show "requires a full portfolio re-run" instead of live before/after.
  v1 live recompute = single-asset only (property geometry/BRI = Tier B,
  wind/fire/seismic = Tier A).

## Still open
- **Live latency** accepted as async spinner for v1 (follows Opt 2). Revisit
  instant path only after Spike 1.

## Resolved since
- **Upload format = .xlsx aligned to the CDM** (not CSV/JSON). Generator
  `tools/cdm_property_editor/cdm_workbook.py` builds `docs/cdm/cdm_upload_workbook.xlsx`
  from the CDM schemas via `cdm_edit.schema_specs`. Template header row = CDM
  dotted path = the upload key. Workstream B's importer reads that header, maps
  each column → CDM, validates with `cdm_edit.validate_value`, writes the sandbox.
