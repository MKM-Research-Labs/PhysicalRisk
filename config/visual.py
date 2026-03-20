# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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

# Default map centre — central London (lat, lon)
MAP_DEFAULT_CENTER: Tuple[float, float] = (51.5074, -0.1278)


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
