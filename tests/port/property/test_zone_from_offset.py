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

"""EA flood-zone classification from vertical offset above river level.

Locks in the fix that a property at or below river level (offset < 0.5 m,
including negative offsets) is Zone 3b (functional floodplain) rather than
falling through to Zone 1. All four classifier copies — the two
``_zone_from_offset`` (flood process + property locations) and the two
catchment ``_ea_zone_from_elevation`` helpers — must agree.
"""

import pytest

from port.src.property.main.locations import _zone_from_offset as zone_locations
from port.src.property.ts.flood.process import FloodMixin
from port.rand.thames.property.property_random.helpers import (
    _ea_zone_from_elevation as zone_thames,
)
from port.rand.halong.property.property_random.helpers import (
    _ea_zone_from_elevation as zone_halong,
)


# (offset_m, expected_zone) — boundaries are half-open [lo, hi).
_CASES = [
    (-5.0, "Zone 3b"),   # well below river — functional floodplain
    (-0.01, "Zone 3b"),  # just below river
    (0.0, "Zone 3b"),    # at river level
    (0.3, "Zone 3b"),
    (0.5, "Zone 3a"),    # lower edge of 3a
    (1.0, "Zone 3a"),
    (1.5, "Zone 2"),
    (2.99, "Zone 2"),
    (3.0, "Zone 1"),
    (25.0, "Zone 1"),
]


@pytest.mark.parametrize("offset,expected", _CASES)
def test_zone_from_offset_locations(offset, expected):
    assert zone_locations(offset) == expected


@pytest.mark.parametrize("offset,expected", _CASES)
def test_zone_from_offset_flood_process(offset, expected):
    assert FloodMixin._zone_from_offset(offset) == expected


@pytest.mark.parametrize("offset,expected", _CASES)
def test_ea_zone_thames(offset, expected):
    assert zone_thames({"vertical_offset": offset}) == expected


@pytest.mark.parametrize("offset,expected", _CASES)
def test_ea_zone_halong(offset, expected):
    assert zone_halong({"vertical_offset": offset}) == expected


def test_all_four_classifiers_agree():
    for offset, _ in _CASES:
        results = {
            zone_locations(offset),
            FloodMixin._zone_from_offset(offset),
            zone_thames({"vertical_offset": offset}),
            zone_halong({"vertical_offset": offset}),
        }
        assert len(results) == 1, f"classifiers disagree at offset={offset}: {results}"


def test_below_river_is_3b_not_zone1():
    """Regression: a below-river property must not be classed lowest-risk."""
    assert zone_locations(-2.0) == "Zone 3b"
    assert FloodMixin._zone_from_offset(-2.0) == "Zone 3b"
