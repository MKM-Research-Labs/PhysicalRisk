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

"""Data loading mixin for PropertyTimeSeriesGenerator.

Filename and JSON-key resolution comes from ``self.ASSET_CONFIG`` so the
same loader serves both residential (property.json) and commercial
(commercial.json) generators.
"""

import json
from typing import Dict, List

from config import config

from .constants import SEQUENCES_FILENAME


class LoaderMixin:
    """Mixin providing all data-loading helpers."""

    def _load_storm_sequence_map(self) -> Dict[str, str]:
        """Build storm_id → sequence_id lookup from the sequences file."""
        try:
            seq_path = config.get_input_path(SEQUENCES_FILENAME)
            with open(seq_path, 'r') as f:
                data = json.load(f)
            mapping = {}
            for seq in data.get('sequences', []):
                seq_id = seq.get('sequence_id', '')
                for storm in seq.get('storms', []):
                    sid = storm.get('storm_id', '')
                    if sid:
                        mapping[sid] = seq_id
            return mapping
        except (OSError, json.JSONDecodeError, KeyError):
            return {}

    def _load_properties(self) -> List[Dict]:
        """Load the asset portfolio for the configured asset type."""
        path = config.get_input_path(self.ASSET_CONFIG.portfolio_filename)
        with open(path, 'r') as f:
            data = json.load(f)
        return data.get(self.ASSET_CONFIG.portfolio_key, [])

    def _load_gauges(self) -> List[Dict]:
        """Load gauge portfolio."""
        path = config.get_input_path("gauge.json")
        with open(path, 'r') as f:
            data = json.load(f)
        return data.get('flood_gauges', [])

    def _load_gaugets(self) -> Dict[str, Dict]:
        """Load all gaugets files into a dict keyed by gauge_id."""
        gaugets_dir = config.get_gaugets_dir()
        gaugets = {}
        if gaugets_dir.exists():
            for f in gaugets_dir.glob('GAUGE-*.json'):
                with open(f, 'r') as fh:
                    data = json.load(fh)
                gid = data.get('gauge_id', f.stem)
                gaugets[gid] = data
        return gaugets
