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

"""Data loading mixin for PropertyTimeSeriesGenerator.

Filename and JSON-key resolution comes from ``self.ASSET_CONFIG`` so the
same loader serves both residential (property.json) and commercial
(commercial.json) generators.
"""

from typing import Dict, List

import database


class LoaderMixin:
    """Mixin providing all data-loading helpers (read through the database seam)."""

    def _load_storm_sequence_map(self) -> Dict[str, str]:
        """Build storm_id → sequence_id lookup from the storm sequences."""
        try:
            data = database.get_storm_sequences(database.active_catchment()) or {}
        except (OSError, ValueError, KeyError):
            return {}
        mapping = {}
        for seq in data.get('sequences', []):
            seq_id = seq.get('sequence_id', '')
            for storm in seq.get('storms', []):
                sid = storm.get('storm_id', '')
                if sid:
                    mapping[sid] = seq_id
        return mapping

    def _load_properties(self) -> List[Dict]:
        """Load the asset portfolio for the configured asset type."""
        return self.ASSET_CONFIG.get_portfolio(database.active_catchment())

    def _load_gauges(self) -> List[Dict]:
        """Load gauge portfolio."""
        data = database.get_gauge_portfolio(database.active_catchment())
        return (data or {}).get('flood_gauges', [])

    def _load_gaugets(self) -> Dict[str, Dict]:
        """Load all gauge timeseries into a dict keyed by gauge_id."""
        catchment = database.active_catchment()
        gaugets = {}
        for gid in database.iter_gauge_timeseries_ids(catchment):
            if not gid.startswith('GAUGE-'):
                continue
            data = database.get_gauge_timeseries(catchment, gid)
            if data:
                gaugets[data.get('gauge_id', gid)] = data
        return gaugets
