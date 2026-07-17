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

"""
Timeseries data loader for MKM Research Labs PRS Platform.

Handles loading and querying gauge timeseries/readings data
from per-gauge JSON files in the gaugets/ directory.
"""

from pathlib import Path
from typing import Dict, Optional

from ._loading import _LoadingMixin
from ._queries import _QueriesMixin


class TimeseriesLoader(_LoadingMixin, _QueriesMixin):
    """
    Loader for gauge timeseries data from per-gauge files.

    Reads from gaugets/ directory where each gauge has its own JSON file:
        gaugets/GAUGE-xxx.json

    Each file contains:
    {
        "gauge_id": "GAUGE-xxx",
        "flood_simulation": {
            "readings": [{"timestamp": "...", "waterLevel": ..., ...}, ...]
        },
        "storm_responses": {
            "responses": [{"storm_id": "...", "peak_level_m": ..., ...}, ...]
        }
    }
    """

    ENTITY_NAME = 'timeseries'
    DEFAULT_DIRNAME = 'gaugets'
    DEFAULT_FILENAME = 'gaugets'  # Compatibility alias for loader_registry

    def __init__(self, data_dir: Path, filename: Optional[str] = None):
        self.data_dir = Path(data_dir)
        self.dirname = filename or self.DEFAULT_DIRNAME
        self._cache: Dict[str, Dict] = {}
        self._cache_valid = False
