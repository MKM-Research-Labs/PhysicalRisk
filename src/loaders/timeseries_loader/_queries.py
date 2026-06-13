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

"""Reading queries, statistics and BaseLoader-compatible registry methods."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class _QueriesMixin:
    """Timeseries query, statistics and entity-registry helpers."""

    def get_readings_for_gauge(
        self,
        gauge_id: str,
        gauge_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract all flood simulation readings for a specific gauge.

        Loads only the specific gauge file (efficient for large datasets).
        """
        gauge_data = self._load_gauge_file(gauge_id)
        if not gauge_data:
            # Try searching all files by name
            if gauge_name:
                all_data = self._load_all_gauge_files()
                for gid, gdata in all_data.items():
                    sim = gdata.get('flood_simulation', {})
                    readings = sim.get('readings', [])
                    if readings and readings[0].get('name') == gauge_name:
                        return readings
            logger.debug(f"No readings found for gauge {gauge_id}")
            return []

        sim = gauge_data.get('flood_simulation', {})
        readings = sim.get('readings', [])
        logger.debug(f"Found {len(readings)} readings for gauge {gauge_id}")
        return readings

    def get_readings_in_range(
        self,
        start: datetime,
        end: datetime,
        gauge_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get readings within a time range."""
        if gauge_id:
            readings = self.get_readings_for_gauge(gauge_id)
            results = []
            for reading in readings:
                ts_str = reading.get('timestamp')
                if not ts_str:
                    continue
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    continue
                if start <= ts <= end:
                    results.append(reading)
            return results
        else:
            # All gauges in range
            results = []
            for record in self.load_all():
                ts_str = record.get('timestamp')
                if not ts_str:
                    continue
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    continue
                if start <= ts <= end:
                    results.append(record)
            return results

    def get_latest_reading(self, gauge_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent reading for a gauge."""
        readings = self.get_readings_for_gauge(gauge_id)
        if not readings:
            return None
        sorted_readings = sorted(
            readings,
            key=lambda r: r.get('timestamp', ''),
            reverse=True
        )
        return sorted_readings[0] if sorted_readings else None

    def get_peak_reading(self, gauge_id: str) -> Optional[Dict[str, Any]]:
        """Get the peak (highest level) reading for a gauge."""
        readings = self.get_readings_for_gauge(gauge_id)
        if not readings:
            return None

        peak = None
        peak_level = float('-inf')
        for reading in readings:
            level = reading.get('waterLevel', reading.get('level', reading.get('value', 0)))
            if isinstance(level, (int, float)) and level > peak_level:
                peak_level = level
                peak = reading
        return peak

    def get_gauge_statistics(self, gauge_id: str) -> Dict[str, Any]:
        """Calculate statistics for a gauge's readings."""
        readings = self.get_readings_for_gauge(gauge_id)

        if not readings:
            return {
                'gauge_id': gauge_id,
                'reading_count': 0,
                'error': 'No readings found'
            }

        levels = []
        for reading in readings:
            level = reading.get('waterLevel', reading.get('level', reading.get('value')))
            if isinstance(level, (int, float)):
                levels.append(level)

        if not levels:
            return {
                'gauge_id': gauge_id,
                'reading_count': len(readings),
                'error': 'No numeric levels found'
            }

        return {
            'gauge_id': gauge_id,
            'reading_count': len(readings),
            'level_count': len(levels),
            'min_level': min(levels),
            'max_level': max(levels),
            'mean_level': sum(levels) / len(levels),
            'first_timestamp': readings[0].get('timestamp'),
            'last_timestamp': readings[-1].get('timestamp'),
        }

    def get_available_gauge_ids(self) -> List[str]:
        """Get list of all gauge IDs from filenames in gaugets/ directory."""
        gaugets_dir = self._get_gaugets_dir()
        if not gaugets_dir.exists():
            return []
        return sorted([f.stem for f in gaugets_dir.glob("*.json")])

    def get_storm_responses(self, gauge_id: str) -> List[Dict[str, Any]]:
        """Get storm response data for a specific gauge."""
        gauge_data = self._load_gauge_file(gauge_id)
        if not gauge_data:
            return []
        sr = gauge_data.get('storm_responses', {})
        return sr.get('responses', [])

    # Compatibility methods for BaseLoader interface
    def get_entity_id(self, entity: Dict[str, Any]) -> Optional[str]:
        """Extract timestamp as ID for a timestep record."""
        return entity.get('timestamp')

    def get_entity_summary(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary for a timestep record."""
        readings = entity.get('readings', [])
        return {
            'timestamp': entity.get('timestamp'),
            'hour': entity.get('hour'),
            'reading_count': len(readings),
            'gauge_ids': [r.get('gaugeId') for r in readings if r.get('gaugeId')],
        }

    def list_all(self) -> List[Dict[str, Any]]:
        """Get summary list of all timestep records."""
        return [self.get_entity_summary(record) for record in self.load_all()]

    def find_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Find a timestep record by timestamp."""
        for record in self.load_all():
            if self.get_entity_id(record) == entity_id:
                return record
        return None

    def exists(self, entity_id: str) -> bool:
        """Check if a timestep record exists."""
        return self.find_by_id(entity_id) is not None

    def count(self) -> int:
        """Get count of gauge files."""
        return len(self.get_available_gauge_ids())

    def get_status(self) -> Dict[str, Any]:
        """Get status information about the loader."""
        gaugets_dir = self._get_gaugets_dir()
        exists = gaugets_dir.exists()
        gauge_files = list(gaugets_dir.glob("*.json")) if exists else []
        return {
            'entity_name': self.ENTITY_NAME,
            'path': str(gaugets_dir),
            'exists': exists,
            'num_gauge_files': len(gauge_files),
            'cached': self._cache_valid,
            'cached_count': len(self._cache)
        }

    def get_file_status(self) -> Dict[str, Any]:
        """Alias for get_status (compatibility)."""
        return self.get_status()
