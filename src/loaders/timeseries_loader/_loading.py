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

"""Per-gauge file loading and cache management for TimeseriesLoader."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from database import read_json_document, iter_document_names

logger = logging.getLogger(__name__)


class _LoadingMixin:
    """Per-gauge JSON file loading and cache handling."""

    def _get_gaugets_dir(self) -> Path:
        """Get path to gaugets directory."""
        return self.data_dir / self.dirname

    def _load_gauge_file(self, gauge_id: str) -> Optional[Dict]:
        """Load a single per-gauge JSON file."""
        if gauge_id in self._cache:
            return self._cache[gauge_id]

        data = read_json_document(self._get_gaugets_dir(), f"{gauge_id}.json")
        if data is None:
            logger.warning(
                f"Gauge file not found: {self._get_gaugets_dir() / f'{gauge_id}.json'}")
            return None

        self._cache[gauge_id] = data
        return data

    def _load_all_gauge_files(self) -> Dict[str, Dict]:
        """Load all per-gauge files from the directory."""
        if self._cache_valid and self._cache:
            return self._cache

        gaugets_dir = self._get_gaugets_dir()
        if not gaugets_dir.exists():
            logger.warning(f"Gaugets directory not found: {gaugets_dir}")
            return {}

        for name in iter_document_names(gaugets_dir):
            gauge_id = Path(name).stem
            if gauge_id not in self._cache:
                self._cache[gauge_id] = read_json_document(gaugets_dir, name)

        self._cache_valid = True
        logger.info(f"Loaded {len(self._cache)} gauge files from {gaugets_dir}")
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
