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

"""Data loading for the portfolio report."""

import json
import logging
import statistics as stats_mod
from pathlib import Path

logger = logging.getLogger(__name__)


def _load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load %s: %s", path, e)
        return {}


def _count_dir(directory, pattern):
    try:
        return len(list(Path(directory).glob(pattern)))
    except (OSError, TypeError) as e:
        logger.warning("Failed to count %s/%s: %s", directory, pattern, e)
        return 0


class DataLoaderMixin:
    """Mixin providing data loading for the portfolio report."""

    def _load_all(self) -> dict:
        """Load all data sources from the input directory."""
        d = self.input_dir
        data = {}

        data['gauges_raw'] = _load(d / 'gauge.json')
        data['gauges'] = data['gauges_raw'].get('flood_gauges', [])
        data['properties_raw'] = _load(d / 'property.json')
        data['properties'] = data['properties_raw'].get('properties', [])
        data['mortgages_raw'] = _load(d / 'loan.json')
        data['mortgages'] = data['mortgages_raw'].get('loans', [])
        data['counterparties_raw'] = _load(d / 'counterparty.json')
        data['counterparties'] = data['counterparties_raw'].get('counterparties', [])
        data['gaugehc'] = _load(d / 'gaugehc.json')
        data['propertyhc'] = _load(d / 'propertyhc.json')
        data['seq_summary'] = _load(d / 'sequences_summary.json')

        # Stress storms
        ss_idx = d / 'stress_storms' / '_index.json'
        ss_leg = d / 'stress_storms.json'
        if ss_idx.exists():
            data['stress_storms'] = _load(ss_idx)
        elif ss_leg.exists():
            data['stress_storms'] = _load(ss_leg)
        else:
            data['stress_storms'] = {}

        # Classifier
        sm_dir = d / 'stressm'
        data['classifier_count'] = _count_dir(sm_dir, '*.joblib')
        data['training_summary'] = _load(sm_dir / 'training_summary.json') if sm_dir.exists() else {}

        # Counts
        data['gaugets_count'] = _count_dir(d / 'gaugets', 'GAUGE-*.json')
        data['gaugehd_count'] = _count_dir(d / 'gaugehd', 'gauge_GAUGE-*.json')
        data['propertyts_count'] = _count_dir(d / 'propertyts', 'PROP-*.json')

        # Trading
        try:
            from config import config
            prs_dir = config.get_reports_dir('prs')
            data['trade_count'] = _count_dir(prs_dir, 'PRS-*.json') if prs_dir.exists() else 0
            data['eod_count'] = _count_dir(config.get_eod_dir(), 'EOD-*')
        except Exception as e:
            logger.warning("Failed to load trading counts: %s", e)
            data['trade_count'] = 0
            data['eod_count'] = 0

        # Gaugehd baselines
        data['gaugehd_baselines'] = self._load_gaugehd_baselines(d / 'gaugehd')

        return data

    def _load_gaugehd_baselines(self, gaugehd_dir: Path) -> list:
        """Load seasonal baselines from gaugehd/ for reporting."""
        baselines = []
        if not gaugehd_dir.exists():
            return baselines
        for f in sorted(gaugehd_dir.glob('gauge_*_hd.json')):
            try:
                hd = _load(f)
                gid = hd.get('gauge_metadata', {}).get('gauge_id', f.stem)
                st = hd.get('statistics', {})
                mean_lvl = st.get('mean_level')
                mm = st.get('monthly_means', {})
                if mean_lvl is not None:
                    winter = summer = None
                    if mm:
                        winter = stats_mod.mean([float(mm.get(m, 0)) for m in ['12', '01', '02']])
                        summer = stats_mod.mean([float(mm.get(m, 0)) for m in ['06', '07', '08']])
                    baselines.append({
                        'gauge_id': gid, 'mean_level': float(mean_lvl),
                        'winter': winter, 'summer': summer,
                    })
            except Exception as e:
                logger.warning("Failed to load baseline from %s: %s", f, e)
                continue
        return baselines
