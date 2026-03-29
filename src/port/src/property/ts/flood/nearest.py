# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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

        selected.sort(key=lambda x: x[1])

        result = []
        for gid, dist, ginfo in selected:
            result.append({
                'gauge_id': gid,
                'distance_m': dist,
                'gauge_info': ginfo,
            })
        return result
