# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Phase 0 safety net for the catchment rand de-duplication.

The thames and halong `port.rand.<catchment>` trees are near-identical copies
(see the duplication report). This module pins that fact: for the byte-identical
generators, thames and halong MUST produce identical output for the same seed
(once non-deterministic ids / timestamps are normalised). It is the regression
guard for the planned consolidation into a shared `_core` — when both catchments
re-export the shared engine, these assertions still hold; if a move breaks the
import wiring or silently diverges a catchment, they fail.

It deliberately covers only the byte-identical generators. The genuinely
catchment-specific modules (commercial_random/*, property_random registries,
mortgage id/currency) are NOT asserted equal — those carry real per-catchment
data and are handled in later phases.
"""

import importlib
import json
import random
import re
from pathlib import Path

import pytest

_GOLDEN = Path(__file__).parent / "golden" / "thames_generators.json"

# Non-deterministic fields to mask before comparing: full UUIDs, prefixed hex
# ids (MORT-1669…, PROP-…), and ISO date/datetime stamps.
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_ID = re.compile(r"\b[A-Z]{2,}-[0-9a-f]{6,}\b")
_TS = re.compile(r"\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?)?")


def _norm(o):
    if isinstance(o, dict):
        return {k: _norm(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_norm(v) for v in o]
    if isinstance(o, str):
        return _TS.sub("<TS>", _ID.sub("<ID>", _UUID.sub("<UUID>", o)))
    return o


_LOC = {"lat": 51.5, "lon": -0.12, "elevation": 12.0, "name": "Test Reach"}
_LOC_INFO = {
    "lat": 51.5, "lon": -0.12, "elevation": 12.0, "name": "Camden",
    "area": "Camden", "property_type": "Detached", "property_area": 120.0,
    "renewable_system": "Solar PV", "bedrooms": 3, "value_factor": 1.0,
    "flood_risk": "Low", "construction_year": 1995,
}

# (module-suffix, function, seed, args) — byte-identical generators only.
_CASES = [
    ("gauge.gauge_random", "generate_gauge_metadata", 4242, (0, dict(_LOC), "River")),
    ("property.property_utils", "generate_postcode", 7, ()),
    ("property.property_utils", "generate_construction_year", 7, ()),
    ("property.property_utils", "generate_owner_name", 7, ()),
    ("property.property_energy", "calculate_solar_generation", 11, (dict(_LOC_INFO),)),
    ("property.property_valuation", "calculate_property_value", 13, (dict(_LOC_INFO),)),
    ("property.property_valuation", "calculate_monthly_rent", 13, (dict(_LOC_INFO),)),
    ("mortgage.financials", "generate_financial_data", 17, (dict(_LOC_INFO), 0)),
]


def _run(catchment, mod_suffix, func, seed, args):
    mod = importlib.import_module(f"port.rand.{catchment}.{mod_suffix}")
    random.seed(seed)
    fresh = tuple(dict(a) if isinstance(a, dict) else a for a in args)
    return _norm(getattr(mod, func)(*fresh))


def _json(o):
    """Round-trip through JSON so comparisons are type-stable (tuple->list etc.)."""
    return json.loads(json.dumps(o, sort_keys=True, default=str))


@pytest.mark.parametrize("mod_suffix,func,seed,args", _CASES,
                         ids=[f"{c[0]}.{c[1]}" for c in _CASES])
def test_thames_halong_byte_identical_generators_agree(mod_suffix, func, seed, args):
    t = _run("thames", mod_suffix, func, seed, args)
    h = _run("halong", mod_suffix, func, seed, args)
    assert t == h, f"{mod_suffix}.{func} diverged between thames and halong"


@pytest.mark.parametrize("mod_suffix,func,seed,args", _CASES,
                         ids=[f"{c[0]}.{c[1]}" for c in _CASES])
def test_thames_generators_match_golden(mod_suffix, func, seed, args):
    """Absolute regression guard: normalised thames output must match the
    committed golden snapshot (catches a refactor that changes BOTH catchments
    equally, which the equivalence check above would miss)."""
    golden = json.loads(_GOLDEN.read_text())
    key = f"{mod_suffix}.{func}"
    actual = _json(_run("thames", mod_suffix, func, seed, args))
    assert actual == golden[key], f"{key} drifted from golden snapshot"


# Public modules whose import surface the dynamic dispatch relies on.
_SURFACE_MODULES = [
    "gauge.gauge_random",
    "gauge.gaugets_random",
    "property.property_random",
    "mortgage.mortgage_random",
    "commercial.commercial_random",
]


@pytest.mark.parametrize("mod_suffix", _SURFACE_MODULES)
def test_thames_halong_public_surface_matches(mod_suffix):
    """Both catchments must expose the same public callables (so a later move to
    a shared engine can't silently drop part of a catchment's API)."""
    def surface(catchment):
        m = importlib.import_module(f"port.rand.{catchment}.{mod_suffix}")
        names = getattr(m, "__all__", None)
        if names is None:
            names = [n for n in dir(m) if not n.startswith("_")]
        return set(names)

    assert surface("thames") == surface("halong"), (
        f"{mod_suffix}: public API differs between thames and halong")
