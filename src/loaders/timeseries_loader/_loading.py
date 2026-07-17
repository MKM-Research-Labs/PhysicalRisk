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

"""Per-gauge file loading and cache management for TimeseriesLoader."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import database

logger = logging.getLogger(__name__)


class _LoadingMixin:
    """Per-gauge JSON file loading and cache handling."""

    def _get_gaugets_dir(self) -> Path:
        """Get path to gaugets directory."""
        return self.data_dir / self.dirname

    def _load_gauge_file(self, gauge_id: str) -> Optional[Dict]:
        """Load a single gauge's timeseries through the database seam."""
        if gauge_id in self._cache:
            return self._cache[gauge_id]

        data = database.get_gauge_timeseries(database.active_catchment(), gauge_id)
        if data is None:
            logger.warning(f"Gauge timeseries not found: {gauge_id}")
            return None

        self._cache[gauge_id] = data
        return data

    def _load_all_gauge_files(self) -> Dict[str, Dict]:
        """Load every gauge's timeseries through the database seam."""
        if self._cache_valid and self._cache:
            return self._cache

        catchment = database.active_catchment()
        for gauge_id in database.iter_gauge_timeseries_ids(catchment):
            if gauge_id not in self._cache:
                self._cache[gauge_id] = database.get_gauge_timeseries(catchment, gauge_id)

        self._cache_valid = True
        logger.info(f"Loaded {len(self._cache)} gauge timeseries")
        return self._cache

    def load_all(self, force_reload: bool = False) -> List[Dict[str, Any]]:
        """
        Load all timeseries records (backwards compatible).

        Returns data in the old timestep-interleaved format for
        consumers that expect it.
        """
        if force_reload:
            self.clear_cache()

        all_data = self._load_all_gauge_files()

        # Reconstruct timestep records from per-gauge data
        timestep_map = {}  # hour -> readings list
        for gauge_id, gauge_data in all_data.items():
            sim = gauge_data.get('flood_simulation', {})
            for reading in sim.get('readings', []):
                ts = reading.get('timestamp', '')
                if ts not in timestep_map:
                    timestep_map[ts] = {'timestamp': ts, 'readings': []}
                timestep_map[ts]['readings'].append(reading)

        return list(timestep_map.values())

    def clear_cache(self) -> None:
        """Clear the cache."""
        self._cache = {}
        self._cache_valid = False

    def invalidate_cache(self) -> None:
        """Invalidate the cache (alias for clear_cache)."""
        self.clear_cache()
