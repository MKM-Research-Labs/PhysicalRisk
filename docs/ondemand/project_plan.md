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

## Spikes (do FIRST — ~1 day, decide go/no-go)
1. **Attenuated-depth recoverability** (above) — instant vs re-propagation for
   Tier B. Highest value.
2. **Subset entry point** — how invasive is guarding stale-delete + portfolio
   summary in `ts/generator.py` and `hc/generator/_generator.py` for `subset`?
3. **Workspace seeding & cost** — copy which artifacts into `data/work/`
   (gaugehc.json, storm_sequences.json, sequence_gauge/, propertyts/<id>.json,
   propertyhc + shd/she/bri). Measure one-property regen wall-time (Opt 1 vs 2).
4. **Decomposition modes** — full waterfall before/after needs the property's ts
   in normal+shd+she+bri (4×). Confirm cost; decide v1 = normal(+bri) only.

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

## Decisions (locked 2026-06-17)
- **Architecture = Opt 2, scoped subprocess.** Stage a 1-property sandbox
  workspace, run the real CLI (`app.py port --propertyts --propertyhc …`) in a
  fresh process. Zero divergence from batch, no generator refactor. Recompute is
  **async** (seconds; show a spinner). Opt 3 (instant pure re-price) only added
  later IF Spike 1 shows the attenuated depth is recoverable.
- **Gauge-threshold (Tier C) edits = deferred for v1.** Allow + audit the edit,
  but show "requires a full portfolio re-run" instead of live before/after.
  v1 live recompute = single-asset only (property geometry/BRI = Tier B,
  wind/fire/seismic = Tier A).

## Still open
- **Live latency** accepted as async spinner for v1 (follows Opt 2). Revisit
  instant path only after Spike 1.
- **Upload format:** CSV column contract vs CDM-JSON — need a sample from user.
