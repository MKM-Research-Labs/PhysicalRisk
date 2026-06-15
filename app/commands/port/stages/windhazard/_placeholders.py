# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

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
import json
from pathlib import Path

# asset mode -> (source hazard-curve file, embedded peril-fan key).
# win/faw/baw resolve to zero events; fow/bow carry the flood / BRI-flood leg.
_SPEC = {
    "property": {
        "win": ("propertyhc.json", "wind_only"),
        "faw": ("propertyhc.json", "flood_and_wind"),
        "fow": ("propertyhc.json", "flood_or_wind"),
        "bow": ("propertybri.json", "flood_or_wind"),
        "baw": ("propertybri.json", "flood_and_wind"),
    },
    "commercial": {
        "win": ("commercialhc.json", "wind_only"),
        "faw": ("commercialhc.json", "flood_and_wind"),
        "fow": ("commercialhc.json", "flood_or_wind"),
        "bow": ("commercialbri.json", "flood_or_wind"),
        "baw": ("commercialbri.json", "flood_and_wind"),
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
    """Write the five standalone scenario files for *asset* from the embedded
    peril fans. Returns the list of modes written. Never raises."""
    spec = _SPEC[asset]
    written = []
    for mode in _MODES:
        try:
            src_name, peril_key = spec[mode]
            src_path = out_dir / src_name
            out_path = out_dir / f"{asset}{mode}.json"
            if not src_path.exists():
                continue
            with open(src_path) as f:
                doc = json.load(f)
            projected = _project_peril(doc, peril_key, mode)
            with open(out_path, "w") as f:
                json.dump(projected, f, indent=2)
            written.append(mode)
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            log(f"   [placeholder] {asset}{mode}: skipped ({exc})")
            continue
    if written:
        log(f"   {asset}: zero-event placeholders written for "
            f"{', '.join(written)} (no typhoon)")
    return written
