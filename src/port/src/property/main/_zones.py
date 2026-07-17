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

"""EA flood-zone helpers for property location generation.

Derives EA flood zones from a property's vertical offset above the river,
and provides representative per-zone seed offsets so every zone is
represented in a generated portfolio. All logic is driven by
``EA_FLOOD_ZONE_ELEVATION_BOUNDS`` (config) so it tracks the config.
"""

from typing import List

from config.port import EA_FLOOD_ZONE_ELEVATION_BOUNDS


def _zone_from_offset(offset: float) -> str:
    """Derive EA flood zone from vertical offset above river (metres)."""
    for zone, (lo, hi) in EA_FLOOD_ZONE_ELEVATION_BOUNDS.items():
        # A None bound is unbounded on that side: Zone 3b (functional
        # floodplain) extends to/below river level (lo=None); Zone 1
        # extends arbitrarily high (hi=None).
        if (lo is None or offset >= lo) and (hi is None or offset < hi):
            return zone
    return 'Zone 1'


def _zone_seed_offsets() -> List[float]:
    """One representative in-band vertical offset (m) per EA flood zone.

    Used to guarantee every zone is represented in a generated portfolio.
    The distance x gradient placement model cannot reach the functional
    floodplain on its own — MIN_RIVER_DISTANCE_M (400 m) times the minimum
    gradient (2 m/km) already exceeds Zone 3b's 0.5 m ceiling — so a property
    would never naturally land in Zone 3b. Offsets are derived from
    EA_FLOOD_ZONE_ELEVATION_BOUNDS (not hard-coded) so they track the config.
    """
    seeds = []
    for _zone, (lo, hi) in EA_FLOOD_ZONE_ELEVATION_BOUNDS.items():
        if lo is None:        # unbounded below (Zone 3b): mid of [0, hi)
            seeds.append(hi / 2.0)
        elif hi is None:      # unbounded above (Zone 1): a bit into the band
            seeds.append(lo + 1.0)
        else:
            seeds.append((lo + hi) / 2.0)
    return seeds
