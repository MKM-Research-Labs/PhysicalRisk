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

"""Zero-event wind-coupled peril placeholders for no-typhoon runs.

When the typhoon ensemble has not run (no ``typhoon/damage/EVT-*.json``), the
wind-coupled scenario files — propertywin/faw/fow/bow/baw.json and the
commercial equivalents — would otherwise be absent, so the wind UI tabs 404
(or, worse, serve stale files left over from an earlier typhoon run that no
longer match the freshly regenerated portfolio).

The peril fan is already embedded in the freshly generated hazard curves
(``term_structure.perils`` / ``prs_perils``) with the correct degenerate
no-wind values: wind-only and flood-AND-wind collapse to zero events, while
flood-OR-wind collapses to the flood (or BRI-flood) leg. We project those
embedded fans into the standalone scenario files so the routes serve
consistent, zero-event data instead of 404.

This is deliberately defensive: any failure to write a placeholder is swallowed
so it can never break a flood-only port — the worst case is the prior
skip-and-404 behaviour.
"""

import copy
from pathlib import Path

import database

# asset mode -> (source hazard-curve mode, embedded peril-fan key).
# win/faw/baw resolve to zero events; fow/bow carry the flood / BRI-flood leg.
_SPEC = {
    "property": {
        "win": ("flood", "wind_only"),
        "faw": ("flood", "flood_and_wind"),
        "fow": ("flood", "flood_or_wind"),
        "bow": ("bri", "flood_or_wind"),
        "baw": ("bri", "flood_and_wind"),
    },
    "commercial": {
        "win": ("flood", "wind_only"),
        "faw": ("flood", "flood_and_wind"),
        "fow": ("flood", "flood_or_wind"),
        "bow": ("bri", "flood_or_wind"),
        "baw": ("bri", "flood_and_wind"),
    },
}

_MODES = ("win", "faw", "fow", "bow", "baw")

# Possible curve-collection keys across asset types.
_CURVE_KEYS = ("property_hazard_curves", "commercial_hazard_curves")


def _curves(doc: dict):
    for k in _CURVE_KEYS:
        if isinstance(doc.get(k), dict):
            return k, doc[k]
    return None, {}


def _project_peril(doc: dict, peril_key: str, mode: str) -> dict:
    """Return a deep copy of *doc* with every curve's headline severe spread
    replaced by its embedded *peril_key* fan (the zero-event projection)."""
    out = copy.deepcopy(doc)
    _key, curves = _curves(out)
    for pc in curves.values():
        ts = pc.get("term_structure", {})
        fan = ts.get("perils", {}).get(peril_key, {})
        spread = fan.get("prs_spread_bps")
        if spread is not None and isinstance(ts.get("severe"), dict):
            ts["severe"]["prs_spread_bps"] = list(spread)
        pp = pc.get("prs_perils", {}).get(peril_key, {})
        pc["prs_peril_mode"] = mode
        pc["prs_peril_count"] = pp.get("count", 0)
    md = out.setdefault("metadata", {})
    md["mode"] = mode
    md["wind_coupled"] = False
    md["placeholder_no_typhoon"] = True
    return out


def write_peril_placeholders(out_dir: Path, asset: str, log=print) -> list:
    """Write the five standalone scenario hazard-curve collections for *asset*
    from the embedded peril fans, through the database seam. Returns the list of
    modes written; ``out_dir`` is kept for call-site compatibility. Never raises."""
    catchment = database.active_catchment()
    get_hc = (database.get_property_hazard_curves if asset == "property"
              else database.get_commercial_hazard_curves)
    save_hc = (database.save_property_hazard_curves if asset == "property"
               else database.save_commercial_hazard_curves)
    spec = _SPEC[asset]
    written = []
    for mode in _MODES:
        try:
            base_mode, peril_key = spec[mode]
            doc = get_hc(catchment, mode=base_mode)
            if not doc:
                continue
            projected = _project_peril(doc, peril_key, mode)
            save_hc(catchment, projected, mode=mode)
            written.append(mode)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            log(f"   [placeholder] {asset}{mode}: skipped ({exc})")
            continue
    if written:
        log(f"   {asset}: zero-event placeholders written for "
            f"{', '.join(written)} (no typhoon)")
    return written
