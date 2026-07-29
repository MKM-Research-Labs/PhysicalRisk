# Wind Damage Model — Phase 2 Plan

**Goal:** Convert per-property peak sustained wind (already produced by
the Phase 1.7 pipeline as `data/<catchment>/typhoon/windts/EVT-NNNN.json`)
into a per-property damage ratio for each event. Mirror the flood-damage
architecture (pure curve + BRI-aware wrapper) so the wind model and the
flood model share shape, semantics, and reporting conventions.

**Phase 2 deliverable:** `data/<catchment>/typhoon/damage/EVT-NNNN.json`
written automatically by `python3 phys.py port --typhoon` alongside the
existing storm tracks and per-property wind timeseries.

---

## Architecture principles

1. **Function shape mirrors flood.** `scalar_depth_damage(depth) → ratio`
   has the parallel `scalar_peak_damage(peak_sustained_ms) → ratio`. Single
   argument in, ratio out. The BRI-aware wrapper takes a few extra args.
2. **Operational threshold lives on the property CDM.** Each property
   carries a "max peak wind it can cope with" — concrete km/h, not an
   abstract 0–1 rating. This is the v_50 of the sigmoid for that
   property. Default ~100 kph for residential when the field is absent.
3. **No separate gust factor in Phase 2.** Sustained wind drives damage
   directly. Gust modelling can be added later by replacing
   `peak_sustained_ms` with `peak_gust_ms = G * peak_sustained_ms` at the
   damage call site; the curve interface is unchanged.
4. **Existing BRI fields are reused.** `BRIWindScore` (0–1) and `BRIScore`
   (composite, 0–1) already exist on the CDM (`src/port/cdm/asset/resilience.py`).
   They modulate the curve via a log-aggregated shift to v_50, exactly
   like `bri_stilt` modulates effective depth for flood.
5. **One small CDM addition.** A new `WindThresholdKph` field is added
   to `HAZARD_PROFILE_SCHEMA` (alongside `DesignWindSpeedKmh`). Carries
   the operational threshold per property.
6. **Per-event output, atomic with `--typhoon`.** Damage is computed in
   the same port stage that already writes events/ and windts/; one more
   directory `damage/` lands beside them.

---

## Mathematical specification

### Pure curve

The piecewise-saturated sigmoid:

```
                  1
DR(v) = -------------------------
        1 + exp(-a * (v - v_50))
```

with:
- `v` — peak sustained wind at the property during the event (m/s)
- `v_50` — wind at which 50% damage is realised (m/s)
- `a` — sigmoid steepness in per-m/s

Phase 2 defaults (in `config/damage.py`):
- `WIND_SIGMOID_A_PER_MS = 0.20`
  - At a 22 m/s span, DR moves from ~10% to ~90%
- `WIND_V50_BASE_MS = 27.8` (= 100 kph / 3.6)
  - Used only when neither the CDM `WindThresholdKph` field nor the BRI
    scores are available — pure fallback

### BRI-aware version

`bri_v50_shift(bri_wind_score, bri_composite_score)` produces a signed
shift in m/s, exactly analogous to `bri_stilt(...)` in metres for flood:

```
shift = α · ln(bri_wind / μ_wind) + β · ln(bri_composite / μ_composite)
v_50_eff = WindThresholdMs + shift,    clipped to [v_50 − cap, v_50 + cap]
```

Phase 2 defaults:
- `BRI_WIND_ALPHA_MS = 6.0` — wind-specific weight (per a "1 std" BRI
  improvement, shifts v_50 by ~6 m/s upward)
- `BRI_COMPOSITE_BETA_MS = 3.0` — composite weight
- `BRI_WIND_REFERENCE = 0.50`, `BRI_COMPOSITE_REFERENCE = 0.50` — same
  reference points flood uses
- `WIND_V50_SHIFT_MAX_MS = 12.0` — cap on the signed shift (mirrors
  `BRI_STILT_MAX_M = 1.0`m for flood)

Positive shift = property is hardened, curve translates right, less
damage at the same gust. Negative shift = property is more vulnerable
than baseline, curve translates left.

### Resolution rule for `v_50`

The damage model takes the most specific value available:

```
1. property has CDM field WindThresholdKph        → v_50 = WindThresholdKph / 3.6
2. else use config default WIND_V50_BASE_MS        → v_50 = WIND_V50_BASE_MS
3. then, if either BRI score is present            → v_50_eff = v_50 + bri_v50_shift(...)
```

Step 1 lets calibration analysts tune per-property; step 2 keeps the
model evaluable for un-augmented portfolios; step 3 layers the resilience
modulation on top.

---

## CDM change

**File:** `src/port/cdm/asset/resilience.py`, `HAZARD_PROFILE_SCHEMA`.

Add ONE field:

```python
"WindThresholdKph": {
    "type": "decimal",
    "description": "Operational peak sustained wind (km/h) the property "
                   "can withstand before significant damage; used as the "
                   "50%-damage threshold (v_50) in the wind damage model. "
                   "Default 100 kph for residential when absent."
},
```

That's it. `BRIWindScore`, `BRIScore`, `WindHazardClass`, `DesignWindSpeedKmh`
all already exist and need no change.

The field is shared across Residential, Commercial, and Industrial (the
resilience module is composed into each).

**Backfill policy:** properties generated before this change have no
field. The damage model reads the field with a default-on-read:
```python
threshold_kph = property.get("WindThresholdKph") or DEFAULT_WIND_THRESHOLD_KPH  # 100.0
```
No portfolio regeneration required.

---

## Source layout

```
src/models/winddamage/
├── __init__.py
├── vulnerability.py   # scalar_peak_damage(v), bri_peak_damage(v, ...)
├── bri_shift.py       # bri_v50_shift(bri_wind, bri_composite)
├── threshold.py       # resolve_threshold_ms(property_record) -> float
├── extraction.py      # load windts/EVT-NNNN.json -> {property_id: peak_sustained}
└── event.py           # run_event(windts_path, properties) -> damage payload + JSON
```

Each module is ≤ 80 lines. The pure-curve module never touches CDM or
config beyond importing the calibration constants. Threshold resolution
is its own concern. Extraction is its own concern. The composer in
`event.py` is the only place that knows all three.

### Function signatures

```python
# vulnerability.py
def scalar_peak_damage(peak_sustained_ms: float) -> float: ...
def bri_peak_damage(
    peak_sustained_ms: float,
    threshold_ms: float,
    bri_wind_score: float | None = None,
    bri_composite_score: float | None = None,
) -> float: ...

# bri_shift.py
def bri_v50_shift(bri_wind: float, bri_composite: float) -> float: ...

# threshold.py
def resolve_threshold_ms(property_record: dict) -> float:
    """WindThresholdKph if present, else DEFAULT_WIND_THRESHOLD_KPH, all in m/s."""

# extraction.py
def load_event_peaks(windts_path: Path) -> dict[str, float]:
    """{property_id: peak_sustained_ms} from a single EVT-NNNN.json."""

# event.py
def run_event(
    windts_path: Path,
    properties: list[dict],
    output_path: Path,
) -> dict: ...
```

---

## Per-event output

`data/<catchment>/typhoon/damage/EVT-NNNN.json`:

```json
{
  "event_id": "EVT-0001",
  "scenario_family": "moderate",
  "damages": [
    {
      "property_id": "PROP-...",
      "peak_sustained_ms": 32.4,
      "threshold_ms": 27.8,
      "bri_wind_score": 0.55,
      "bri_composite_score": 0.50,
      "v_50_eff_ms": 30.1,
      "damage_ratio": 0.18
    }
  ]
}
```

`damages` is an array — one entry per property. The fields parallel
flood's per-event damage report so downstream consumers can treat both
hazards with the same template.

---

## Config — extend `config/damage.py`

A new section appended to the existing file, paralleling the
`# BRI Adjustment` block already there for flood:

```python
# ===========================================================================
# Wind Vulnerability  (sigmoid; v_50 from CDM WindThresholdKph; BRI shift)
# ===========================================================================

WIND_SIGMOID_A_PER_MS: float = 0.20
WIND_V50_BASE_MS:      float = 27.8                # = 100 kph / 3.6
DEFAULT_WIND_THRESHOLD_KPH: float = 100.0

# ===========================================================================
# BRI Adjustment — wind (mirror of BRI_FLOOD_ALPHA_M etc.)
# ===========================================================================

BRI_WIND_ALPHA_MS:        float = 6.0
BRI_COMPOSITE_BETA_MS:    float = 3.0
BRI_WIND_REFERENCE:       float = 0.50
WIND_V50_SHIFT_MAX_MS:    float = 12.0
```

`BRI_COMPOSITE_REFERENCE` already exists from the flood block — reused.

---

## Pipeline integration

**Where:** the existing `app/commands/port/stages/typhoon.py` stage. No
new flag. When `--typhoon` runs, after the windts files are written, the
damage step iterates them and writes the per-event damage files.

```python
# inside run_typhoon(ctx), after the windts loop:
from models.winddamage.event import run_event_from_windts_dir
damage_dir = typhoon_dir / "damage"
run_event_from_windts_dir(
    windts_dir=windts_dir,
    damage_dir=damage_dir,
    properties=_load_property_portfolio(ctx),
)
print(f"   per-event damage in {damage_dir}/")
```

The property portfolio comes from the existing `property.json` /
`commercial.json` in the catchment's input dir. The damage stage doesn't
know how to generate properties; it consumes them.

---

## Tests

`tests/models/winddamage/` mirrors the source layout:

- `vulnerability.py` — sigmoid: 0 at very low v, 1 at very high v, 0.5
  at v_50, monotonic, BRI-aware shift moves the curve
- `bri_shift.py` — log-aggregated shift, capped, sign convention
- `threshold.py` — field present, field absent, default fallback,
  unit conversion
- `extraction.py` — load a known windts file, expected peaks
- `event.py` — end-to-end: synthetic property portfolio + synthetic
  windts → damage JSON with the right shape

Plus `tests/catch/halong/` extension: a thin sanity test that loading
`data/halong/typhoon/windts/EVT-0000.json` through the damage model
produces non-zero damages for at least one property at SEVERE/EXTREME
events (calibration sanity, not historical match).

---

## Inventory entry

New model `MKM-WD-001 Wind Damage`:
- **Category:** Hazard
- **Tier:** 2
- **Upstream:** `MKM-TC-001` (event windts), `MKM-WS-001` (point query),
  `MKM-BRI-001` (composite + wind sub-scores)
- **Downstream:** future MKM-PV-001 (Property Valuation) when wind loss
  feeds into property value adjustment

---

## Phased breakdown

**Phase 2.1 — Pure curve and BRI shift**
- `vulnerability.py` + `bri_shift.py`
- Tests for both
- No CDM dependency, no I/O

**Phase 2.2 — Threshold resolution and CDM extension**
- Add `WindThresholdKph` to `HAZARD_PROFILE_SCHEMA`
- `threshold.py` resolver
- Tests

**Phase 2.3 — Extraction**
- `extraction.py` — windts → property_id → peak_sustained
- Tests against a real EVT-NNNN.json fixture

**Phase 2.4 — Event composer**
- `event.py` ties extraction + threshold + curve
- Per-event JSON writer
- Tests

**Phase 2.5 — Pipeline integration**
- Wire into `app/commands/port/stages/typhoon.py`
- End-to-end CLI run produces damage/ files
- Sanity tests under `tests/catch/halong/`

**Phase 2.6 — Inventory + regulatory**
- Add `MKM-WD-001` to `data/model_inventory.json`
- Test mapping in `docs/models/test_results/generator/models.py`
- Regenerate test_results fragment

Each sub-phase is a small commit. After 2.1 we can run the curve on
synthetic numbers; after 2.4 we can hand-run the damage model against a
known windts file; after 2.5 a full `port --typhoon` produces all
three artefact directories.

---

## Open questions / deferred

- **Gust factor** — not in Phase 2. If we want it later, it slots in
  at the call site (`peak_gust = G * peak_sustained`) without changing
  any curve interface. Adds a `GustFactor` CDM field at that point.
- **Duration-aware damage** — flood doesn't do this either; deferred to
  a separate phase if calibration shows peak-only under-predicts.
- **Property archetype curves** — Phase 2 has a single curve form for
  all properties, modulated by `WindThresholdKph` and the BRI scores.
  If real residential / commercial / industrial structures need
  distinct sigmoid shapes (steepness `a`), we add an archetype field
  later.
- **Calibration against historical events** — Phase 3 work. Tail anchors
  Durian (~69 m/s) and Angela (~80 m/s) already in `halong/tc.py` are
  the natural fit points for both the typhoon tail and the damage curve.

---

## What this plan does not change

- `src/models/typhoon/` — untouched
- `src/models/windspeed/` — untouched
- The existing flood damage path (`src/models/floodrisk/depth_damage.py`)
  — untouched. The wind model parallels it, doesn't share code; if
  Phase 3 calibration shows it's worth abstracting a shared
  "hazard-damage" base, that's a refactor of both, not a Phase 2 task.
