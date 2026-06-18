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

"""Gauge hazard rate management mixin."""

import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class GaugeRatesMixin:
    """Manages per-gauge hazard rate adjustments."""

    def get_gauge_rate(self, state: Dict, gauge_id: str,
                       trigger: str) -> float:
        """
        Get the effective hazard rate for a gauge/trigger, applying any adjustment.

        Args:
            state: Market state dictionary
            gauge_id: Gauge identifier
            trigger: Trigger level (alert, warning, severe)

        Returns:
            Annual hazard rate (float between 0 and 1)
        """
        key = f'annual_hazard_rate_{trigger}'

        # Check adjustments first
        adj = state.get('gauge_adjustments', {}).get(gauge_id, {})
        if key in adj:
            return adj[key]

        # Fall back to base rates
        base = state.get('base_rates', {}).get(gauge_id, {})
        return base.get(key, 0.0)

    def update_gauge_rate(self, gauge_id: str, trigger: str,
                          new_rate: float,
                          notes: str = '') -> Dict:
        """
        Update a gauge's hazard rate (market-maker adjustment).

        Args:
            gauge_id: Gauge identifier
            trigger: Trigger level (alert, warning, severe)
            new_rate: New annual hazard rate
            notes: Optional adjustment notes

        Returns:
            Updated market state
        """
        state = self.load()
        key = f'annual_hazard_rate_{trigger}'

        if gauge_id not in state['gauge_adjustments']:
            state['gauge_adjustments'][gauge_id] = {}

        state['gauge_adjustments'][gauge_id][key] = new_rate
        state['gauge_adjustments'][gauge_id]['adjusted_at'] = (
            datetime.now().isoformat()
        )
        if notes:
            state['gauge_adjustments'][gauge_id]['adjustment_notes'] = notes

        self._save(state)
        logger.info("Market state updated: %s %s = %.6f", gauge_id, trigger,
                     new_rate)
        return state

    def reset(self, gauge_id: Optional[str] = None) -> Dict:
        """
        Reset market state to base curves.

        Args:
            gauge_id: If provided, reset only this gauge. Otherwise reset all.

        Returns:
            Updated market state
        """
        state = self.load()

        if gauge_id:
            state['gauge_adjustments'].pop(gauge_id, None)
        else:
            state['gauge_adjustments'] = {}

        self._save(state)
        logger.info("Market state reset%s",
                     f" for {gauge_id}" if gauge_id else " (all)")
        return state

    def get_all_effective_rates(self, state: Optional[Dict] = None) -> Dict:
        """
        Get effective rates for all gauges (base + adjustments merged).

        Returns:
            Dict mapping gauge_id -> {trigger -> rate}
        """
        if state is None:
            state = self.load()

        result = {}
        for gauge_id, base in state.get('base_rates', {}).items():
            adj = state.get('gauge_adjustments', {}).get(gauge_id, {})
            result[gauge_id] = {
                'gauge_name': base.get('gauge_name', ''),
                'annual_hazard_rate_alert': adj.get(
                    'annual_hazard_rate_alert',
                    base.get('annual_hazard_rate_alert', 0)),
                'annual_hazard_rate_warning': adj.get(
                    'annual_hazard_rate_warning',
                    base.get('annual_hazard_rate_warning', 0)),
                'annual_hazard_rate_severe': adj.get(
                    'annual_hazard_rate_severe',
                    base.get('annual_hazard_rate_severe', 0)),
                'is_adjusted': gauge_id in state.get('gauge_adjustments', {}),
                'adjusted_at': adj.get('adjusted_at', ''),
            }

        return result
