# Adding a catchment to the rand generators

The synthetic-portfolio generators in `port.rand` are **catchment-agnostic**.
All generation *logic* lives once under `port/rand/shared/`; everything that
genuinely varies by catchment is *data* in a per-catchment profile
(`port/rand/profiles/<id>.py`). Each `port/rand/<catchment>/…` tree is just a
set of thin shims that alias the shared engine, so onboarding a catchment is a
profile + a copy, not a forked tree.

This is the result of the rand de-duplication initiative — see
`tests/port/rand/test_catchment_equivalence.py` (the thames/halong trees are
byte-identical) and `tests/port/rand/test_profile_completeness.py` (the profile
contract, which is the authoritative list of required keys).

## Steps

Say the new catchment id is `danube`.

### 1. Write the profile — `src/port/rand/profiles/danube.py`

This is the only file with real per-catchment content. Copy the closest
existing profile as a template and edit the values:

- `thames.py` — UK / temperate, low seismicity, no commercial BRI regime.
- `halong.py` — SE-Asia / coastal, high seismicity, full commercial BRI regime.

The profile must define every key the shared engine reads. The authoritative,
enforced list is `tests/port/rand/test_profile_completeness.py`; in summary:

- **BRI toggles** (`bool`): `PUBLISH_BRI_LETTER_RATINGS`, `BRI_SCORES_ENABLED`,
  `COMMERCIAL_BRI_ENABLED`.
- **Seismic**: `SEISMIC_PGA_RANGE` `(lo, hi)`; `SEISMIC_HAZARD_CLASS_WEIGHTS`
  (5 weights for None/Low/Medium/High/Extreme, summing to 1.0).
- **Commercial archetypes**: `COMMERCIAL_TYPE_ALLOCATION` (the first-slice mix)
  plus the per-type tables `COMMERCIAL_TYPE_{AREA_RANGE, VALUE_PER_SQM,
  USE_CLASS, BUSINESS_RATES, STOREYS, TOTAL_UNITS, PARKING_SPACES,
  LOADING_BAYS}` (each must cover every type in the allocation),
  `COMMERCIAL_CONSTRUCTION_TYPES`, `COMMERCIAL_ANCHOR_TENANT_POOL` (covers every
  allocated type), `COMMERCIAL_PERIOD_BUCKETS` (last cutoff `None`), and
  `COMMERCIAL_CONSTRUCTION_YEAR_RANGE` `(min_year, max_or_None)`.
- **Optional**: `COMMERCIAL_CONSTRUCTION_YEAR_BANDS` (per-type weighted year
  bands; omit / set `None` to draw uniformly over the range).

If the catchment has a commercial BRI regime (`COMMERCIAL_BRI_ENABLED = True`),
the BRI prototype catalogue is read from
`port/rand/shared/commercial/bri_codes.py` — regional data shared by all
BRI catchments and gated by the flag.

### 2. Create the catchment shim tree — `src/port/rand/danube/`

The catchment dirs contain no logic, only shims that alias `port.rand.shared`
and a `resilience.py` that calls `install(__name__)`. Nothing in them names a
specific catchment (bar a couple of stale docstrings), so just copy one:

```sh
cp -r src/port/rand/thames src/port/rand/danube
```

This provides the `port.rand.danube.<gauge|property|mortgage|commercial>.…`
import paths that `config.load_random_module()` dispatches to.

### 3. Add the catchment parameters — `catch/danube.py`

The non-rand catchment parameter layer (currency, storm config, map centre,
bounds, gauges, …) lives under `catch/<id>` on the data path, alongside the
existing catchments. At minimum define `CURRENCY` (read by
`config.CURRENCY`); model the rest on an existing `catch/<id>`. `config`
validates a catchment id against this directory, so the id must exist here.

### 4. Verify

```sh
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/port/rand/test_profile_completeness.py \
  tests/port/rand/test_catchment_equivalence.py

# Generate under the new catchment (MKM_CATCHMENT selects it for config):
MKM_CATCHMENT=danube PYTHONPATH=src .venv/bin/python app.py port
```

(`app.py` may also expose a `--<catchment>` flag; `MKM_CATCHMENT` is the
generic selector that `config` honours regardless.)

`test_profile_completeness.py` discovers the new profile automatically and
fails with a precise message if any required key is missing or malformed.

## What you do NOT touch

The generation logic in `port/rand/shared/` — field registries, metadata
builders, valuation/energy/location helpers, the commercial engine, the
resilience facade. If a catchment needs different *behaviour* (not just
different values), that is a change to the shared engine driven by a new
profile key, not a forked copy.
