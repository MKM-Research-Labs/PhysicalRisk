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

"""Helper utilities for property random value generation."""

import hashlib
from typing import Any, Dict


def _deterministic_prop_id(location: Dict, index: int) -> str:
    """Generate a stable property ID from location + index."""
    loc_key = f"{location['lat']:.6f}:{location['lon']:.6f}:{index}"
    return f"PROP-{hashlib.sha256(loc_key.encode()).hexdigest()[:8]}"


def _ea_zone_from_elevation(info: Dict[str, Any]) -> str:
    """Derive EA flood zone from the property's vertical offset above river level."""
    from config.port import EA_FLOOD_ZONE_ELEVATION_BOUNDS
    offset = info.get('vertical_offset', 999.0)
    for zone, (lo, hi) in EA_FLOOD_ZONE_ELEVATION_BOUNDS.items():
        # A None bound is unbounded on that side: Zone 3b (functional
        # floodplain) extends to/below river level (lo=None); Zone 1
        # extends arbitrarily high (hi=None).
        if (lo is None or offset >= lo) and (hi is None or offset < hi):
            return zone
    return 'Zone 1'


def _flood_hazard_class_from_offset(info: Dict[str, Any]) -> str:
    """Derive normalised FloodHazardClass from vertical offset above river level.

    Aligned with EA_FLOOD_ZONE_ELEVATION_BOUNDS so the hazard class stays
    consistent with the property's EAFloodZone. Properties well above the
    floodplain (>10 m) get "None"; the EA zones map directly otherwise.
    """
    offset = info.get('vertical_offset', 999.0)
    if offset < 0.5:
        return "Extreme"
    if offset < 1.5:
        return "High"
    if offset < 3.0:
        return "Medium"
    if offset < 10.0:
        return "Low"
    return "None"
