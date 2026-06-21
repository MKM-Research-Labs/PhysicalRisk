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

"""Persistence mixin: loading, initializing, and saving market state."""

import logging
from datetime import datetime
from typing import Dict

import database

logger = logging.getLogger(__name__)


def _build_default_hazard_ts(base: Dict) -> Dict:
    """Build a default hazard term structure for one gauge's base rates.

    Returns {trigger: {"1": rate, ..., "5": rate}} with a flat 5% annual slope.
    """
    ts = {}
    for trigger in ['alert', 'warning', 'severe']:
        rate_key = f'annual_hazard_rate_{trigger}'
        base_rate = base.get(rate_key, 0.02)
        ts[trigger] = {
            str(t): round(base_rate * (1 + 0.05 * t), 6)
            for t in range(1, 6)
        }
    return ts


class _PersistenceMixin:
    """Handles market state persistence through the database seam."""

    catchment: str

    def _load_base_curves(self) -> Dict:
        """Load base hazard curves from the gauge hazard-curve document."""
        data = database.get_gauge_hazard_curves(self.catchment)
        if data is None:
            logger.warning("gauge hazard curves not found for catchment %s", self.catchment)
            return {}

        # Handle list format, dict-of-dicts (hazard_curves key), or gauges key
        if isinstance(data, list):
            curves = data
        elif 'hazard_curves' in data:
            hc = data['hazard_curves']
            curves = hc.values() if isinstance(hc, dict) else hc
        elif 'gauges' in data:
            curves = data['gauges']
        else:
            curves = []

        base_rates = {}
        for gauge in curves:
            gauge_id = gauge.get('gauge_id', '')
            if not gauge_id:
                continue
            base_rates[gauge_id] = {
                'gauge_name': gauge.get('gauge_name', ''),
                'annual_hazard_rate_alert': gauge.get('annual_hazard_rate_alert', 0),
                'annual_hazard_rate_warning': gauge.get('annual_hazard_rate_warning', 0),
                'annual_hazard_rate_severe': gauge.get('annual_hazard_rate_severe', 0),
                'curve_points': gauge.get('curve_points', []),
                'gev_location': gauge.get('gev_location', 0),
                'gev_scale': gauge.get('gev_scale', 0),
                'gev_shape': gauge.get('gev_shape', 0),
            }

        return base_rates

    def load(self) -> Dict:
        """
        Load current market state. If none exists, initialise from base curves.

        Reconciles with gaugehc.json on every load so newly-added gauges
        (e.g. from classifier training) appear automatically.

        Returns:
            Market state dictionary with gauge_adjustments, base_rates, metadata.
        """
        state = database.get_market_state(self.catchment)
        if state is None:
            return self._initialize()

        # Reconcile: add any gauges present in the hazard curves but missing
        # from the persisted state (happens when classifiers add new gauges).
        current_base = self._load_base_curves()
        existing_base = state.get('base_rates', {})
        hazard_ts = state.get('hazard_term_structure', {})

        added = 0
        for gauge_id, base in current_base.items():
            if gauge_id not in existing_base:
                existing_base[gauge_id] = base
                hazard_ts[gauge_id] = _build_default_hazard_ts(base)
                added += 1

        if added:
            state['base_rates'] = existing_base
            state['hazard_term_structure'] = hazard_ts
            self._save(state)
            logger.info("Reconciled market state: added %d new gauges "
                        "(now %d total)", added, len(existing_base))

        return state

    def _initialize(self) -> Dict:
        """Create initial market state from base curves."""
        base_rates = self._load_base_curves()

        # Build default hazard term structures: flat at base rate, slope to 1.25x at 5Y
        hazard_ts = {gid: _build_default_hazard_ts(base)
                     for gid, base in base_rates.items()}

        state = {
            'last_updated': datetime.now().isoformat(),
            'risk_free_rate': 0.04,  # Backwards-compat average
            'recovery_rate': 0.0,
            'yield_curve': dict(self.DEFAULT_YIELD_CURVE),
            'hazard_term_structure': hazard_ts,
            'base_rates': base_rates,
            'gauge_adjustments': {},  # Only stores overrides
        }

        self._save(state)
        return state

    def _save(self, state: Dict) -> None:
        """Persist market state through the database seam."""
        state['last_updated'] = datetime.now().isoformat()
        database.save_market_state(self.catchment, state)
