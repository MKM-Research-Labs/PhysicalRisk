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

"""Gauge selection: find nearest gauges to a property."""

from typing import Dict, List

from models.floodrisk.spatial import haversine_distance

from ..constants import N_NEAREST_GAUGES


class NearestGaugeMixin:
    """Mixin providing nearest-gauge selection."""

    def _find_nearest_gauges(self, prop_lat: float, prop_lon: float,
                              gauge_lookup: Dict, n: int = N_NEAREST_GAUGES
                              ) -> List[Dict]:
        """
        Find the n nearest gauges to a property.

        Enforces at most 1 synthetic gauge (the closest SYNTH-*) plus
        (n-1) nearest real gauges, so that real gauges always dominate
        the IDW interpolation and flood propagation.
        """
        synth = []
        real = []
        for gid, ginfo in gauge_lookup.items():
            dist = haversine_distance(prop_lat, prop_lon, ginfo['lat'], ginfo['lon'])
            entry = (gid, dist, ginfo)
            if gid.startswith('SYNTH'):
                synth.append(entry)
            else:
                real.append(entry)

        synth.sort(key=lambda x: x[1])
        real.sort(key=lambda x: x[1])

        # 1 closest synthetic + (n-1) closest real gauges
        selected = real[:n - 1]
        if synth:
            selected.append(synth[0])
        else:
            # No synthetic gauges — use n nearest real
            selected = real[:n]

        # Sort real gauges by distance, but keep synthetic at position [0].
        # The synthetic gauge is the controlling boundary condition for flood
        # propagation — it represents the river at the property's location.
        synth_entry = None
        real_entries = []
        for entry in selected:
            if entry[0].startswith('SYNTH'):
                synth_entry = entry
            else:
                real_entries.append(entry)
        real_entries.sort(key=lambda x: x[1])
        selected = ([synth_entry] if synth_entry else []) + real_entries

        result = []
        for gid, dist, ginfo in selected:
            result.append({
                'gauge_id': gid,
                'distance_m': dist,
                'gauge_info': ginfo,
            })
        return result
