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

"""
Visual layer parameter registry.

All hard-coded configuration for the Folium map, layer rendering, and
popup/panel layout lives here. Source files import from this module rather
than embedding literal values.

Subsections:
    Map Defaults       — visual/core/map_builder.py
    Gauge RAG          — visual/layer/gauge_layer.py
    Property RAG       — visual/layer/property_layer.py
    Popup Dimensions   — gauge_layer.py + property_layer.py
"""

from typing import Tuple

# ===========================================================================
# Map Defaults  (visual/core/map_builder.py)
# ===========================================================================

# Default Leaflet/Folium zoom level (1 = world, 18 = street)
MAP_DEFAULT_ZOOM: int = 8

# Default tile provider
MAP_DEFAULT_TILES: str = 'OpenStreetMap'

# Last-resort map centre (lat, lon) — only used if the active catchment's
# BOUNDS cannot be read. Prefer get_map_center(), which follows the catchment
# in play, so maps never default to a fixed region.
MAP_DEFAULT_CENTER: Tuple[float, float] = (51.5074, -0.1278)


def get_catchment_bounds() -> Tuple[float, float, float, float]:
    """Return the active catchment's geographic bounds.

    Bounds are ``(min_lon, min_lat, max_lon, max_lat)`` read from the
    catchment params module (single source of truth). Raises if unavailable.
    """
    from config import config
    return config.load_params_module().BOUNDS


def get_map_center() -> Tuple[float, float]:
    """Return ``(lat, lon)`` centre of the active catchment.

    Derived from the catchment's BOUNDS so every map opens over the catchment
    in play rather than a hardcoded region. Falls back to MAP_DEFAULT_CENTER
    only when BOUNDS cannot be read.
    """
    try:
        min_lon, min_lat, max_lon, max_lat = get_catchment_bounds()
        return ((min_lat + max_lat) / 2.0, (min_lon + max_lon) / 2.0)
    except Exception:
        return MAP_DEFAULT_CENTER


def get_catchment_display_name() -> str:
    """Return the active catchment's human-readable name (e.g. ``Thames``,
    ``Halong``).

    Single source of truth for report/prose text that names the catchment's
    river/region, so copy follows the catchment in play rather than a
    hardcoded "Thames". Reads ``DISPLAYNAME`` from the catchment params module,
    falling back to a title-cased ``NAME`` and finally ``"catchment"``.
    """
    import inspect

    from config import config

    try:
        mod = config.load_params_module()
    except Exception:
        return "catchment"

    # Direct module-level attributes first.
    name = getattr(mod, 'DISPLAYNAME', None) or getattr(mod, 'NAME', None)
    if not name:
        # Otherwise locate the catchment class generically (its name varies
        # per catchment: ThamesCatchment, HalongCatchment, ...).
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if inspect.isclass(obj) and hasattr(obj, 'DISPLAYNAME'):
                name = getattr(obj, 'DISPLAYNAME', None) or getattr(obj, 'NAME', None)
                if name:
                    break

    if not name:
        return "catchment"
    name = str(name)
    return name if name[:1].isupper() else name.title()


def get_lat_position_label(lat: float) -> str:
    """Describe a latitude's north/south position within the active catchment.

    Returns ``"Northern part of catchment"`` / ``"Central part of catchment"``
    / ``"Southern part of catchment"`` based on which third of the catchment's
    own latitude span the point falls in — no hardcoded region. Falls back to
    ``"Location within catchment"`` when bounds are unavailable.
    """
    try:
        _, min_lat, _, max_lat = get_catchment_bounds()
        third = (max_lat - min_lat) / 3.0
        if third <= 0:
            return "Location within catchment"
        if lat >= min_lat + 2 * third:
            return "Northern part of catchment"
        if lat >= min_lat + third:
            return "Central part of catchment"
        return "Southern part of catchment"
    except Exception:
        return "Location within catchment"


def get_lon_position_label(lon: float) -> str:
    """Describe a longitude's east/west position within the active catchment.

    Returns ``"Eastern part of catchment"`` / ``"Central part of catchment"``
    / ``"Western part of catchment"`` based on which third of the catchment's
    own longitude span the point falls in — no hardcoded region. Falls back to
    ``"Location within catchment"`` when bounds are unavailable.
    """
    try:
        min_lon, _, max_lon, _ = get_catchment_bounds()
        third = (max_lon - min_lon) / 3.0
        if third <= 0:
            return "Location within catchment"
        if lon >= min_lon + 2 * third:
            return "Eastern part of catchment"
        if lon >= min_lon + third:
            return "Central part of catchment"
        return "Western part of catchment"
    except Exception:
        return "Location within catchment"


# ===========================================================================
# Gauge Flood-Frequency RAG Thresholds  (visual/layer/gauge_layer.py)
# ===========================================================================
# Thresholds are counts of flood events across the storm simulation set.
# The gauge simulation uses 10,000 storms; these thresholds are calibrated
# so that ~2.5 % of gauges are "High" and ~2.2 % are "Medium".

# flood_count > GAUGE_FLOOD_HIGH  → RAG = High   (red marker)
GAUGE_FLOOD_HIGH: int = 250

# GAUGE_FLOOD_MEDIUM <= flood_count <= GAUGE_FLOOD_HIGH → RAG = Medium (orange)
GAUGE_FLOOD_MEDIUM: int = 220

# flood_count < GAUGE_FLOOD_MEDIUM → RAG = Low  (green marker)


# ===========================================================================
# Property Flood-Frequency RAG Thresholds  (visual/layer/property_layer.py)
# ===========================================================================
# Property flood counts are much lower because properties are only exposed
# when their nearest gauge breaches alert AND depth exceeds floor level.

# flood_count > PROPERTY_FLOOD_HIGH → RAG = High  (red marker)
PROPERTY_FLOOD_HIGH: int = 5

# PROPERTY_FLOOD_MEDIUM <= flood_count <= PROPERTY_FLOOD_HIGH → RAG = Medium
PROPERTY_FLOOD_MEDIUM: int = 1

# flood_count < PROPERTY_FLOOD_MEDIUM → RAG = Low  (green marker)


# ===========================================================================
# Popup / Panel Dimensions  (gauge_layer.py + property_layer.py)
# ===========================================================================

# Maximum popup width (pixels) — controls Leaflet popup box width
POPUP_MAX_WIDTH: int = 350

# Inner HTML container width (pixels) — content area inside the popup
POPUP_CONTAINER_WIDTH: int = 320

# Inner HTML container max height (pixels) — enables scroll on long content
POPUP_MAX_HEIGHT_PX: int = 400
