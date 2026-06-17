# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

"""Editing rules for CDM fields — input widgets and numeric constraints.

Pure data + small helpers consumed by constraints.py. The CDM schema already
carries ``type`` and (for menus) ``options``; this layer adds the HTML input
kind and sensible numeric bounds so the editor can render the right widget and
the server can reject out-of-range values.
"""

# CDM type -> HTML input kind used by the editor.
TYPE_INPUT = {
    "string": "text",
    "decimal": "number",
    "integer": "number",
    "date": "date",
    "boolean": "checkbox",
    "menu": "select",
}

# Numeric default is non-negative ("must be positive"). These name fragments
# mark signed quantities (geographic / relative-to-datum) that may go negative.
ALLOW_NEGATIVE = (
    "latitude", "longitude", "elevation", "level", "ground", "datum", "vertical",
)


def _name(path):
    """The leaf field name (last dotted segment), lower-cased."""
    return (path.rsplit(".", 1)[-1] if path else path).lower()


def numeric_bounds(path, cdm_type):
    """Return (min, max, step) for a numeric field, by name and type.

    Defaults to non-negative. Years get a sensible calendar range; BRI scores
    are bounded to [0, 1]; geographic/relative measures are left unbounded.
    """
    name = _name(path)
    step = 1 if cdm_type == "integer" else "any"
    if name.endswith("year"):
        return 1900, 2100, 1
    if "bri" in name and "score" in name:
        return 0, 1, "any"
    if any(k in name for k in ALLOW_NEGATIVE):
        return None, None, step
    return 0, None, step
