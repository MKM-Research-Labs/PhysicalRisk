# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

"""PRS spread waterfall — the single source for the basis decomposition view.

Turns a property/commercial hazard-curve ``spread_decomposition`` into the
ordered stages the waterfall renders: Gauge -> SHE (elevation) -> SHD
(distance) -> Property -> BRI (resilient). Each stage carries its spread (bps),
its effect vs the gauge spread (the resilient stage vs the property spread),
and its colours. Used by both the main-app basis waterfall and the CDM Asset
Review tool so the definition lives in one place.
"""

# Stage colours (base + muted-for-inactive), keyed by stage.
WATERFALL_PALETTE = {
    "gauge":    {"colour": "#EF5350", "muted": "#FFCDD2"},
    "she":      {"colour": "#FF9800", "muted": "#FFE0B2"},
    "shd":      {"colour": "#66BB6A", "muted": "#C8E6C9"},
    "property": {"colour": "#42A5F5", "muted": "#BBDEFB"},
    "bri":      {"colour": "#7E57C2", "muted": "#D1C4E9"},
}


def _stage(key, label, bps, effect):
    pal = WATERFALL_PALETTE[key]
    return {
        "key": key,
        "label": label,
        "bps": round(float(bps), 1),
        "effect": None if effect is None else round(float(effect), 1),
        "colour": pal["colour"],
        "muted": pal["muted"],
    }


def waterfall_stages(spread_decomposition):
    """Ordered waterfall stages for a ``spread_decomposition`` dict.

    The BRI (resilient) stage is appended only when the propertybri stage has
    run (``bri_spread_bps`` present). Returns an empty list for a missing/empty
    decomposition.
    """
    sd = spread_decomposition or {}
    if not sd:
        return []
    gauge = sd.get("gauge_spread_bps") or 0.0
    she = sd.get("she_spread_bps") or 0.0
    shd = sd.get("shd_spread_bps") or 0.0
    prop = sd.get("property_spread_bps") or 0.0
    stages = [
        _stage("gauge", "Gauge", gauge, None),
        _stage("she", "SHE (elevation)", she, she - gauge),
        _stage("shd", "SHD (distance)", shd, shd - gauge),
        _stage("property", "Property", prop, prop - gauge),
    ]
    if sd.get("bri_spread_bps") is not None:
        bri = sd.get("bri_spread_bps") or 0.0
        stages.append(_stage("bri", "BRI (resilient)", bri, bri - prop))
    return stages
