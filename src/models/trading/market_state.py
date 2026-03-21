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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Market state management for the trading desk.

Stores the market-maker's adjusted hazard curves. When a trader adjusts
a gauge's annual hazard rate, this module persists the change and triggers
revaluation of affected trades.

The market state starts as a copy of the base rates from gaugehc.json.
Adjustments are stored per-gauge per-trigger level.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from config.port import DEFAULT_YIELD_CURVE as _DEFAULT_YIELD_CURVE

logger = logging.getLogger(__name__)


class MarketStateManager:
    """Manages the current market state (adjusted hazard curves)."""

    def __init__(self, trading_dir: Path, input_dir: Path):
        """
        Initialize market state manager.

        Args:
            trading_dir: Path to data/output/trading/
            input_dir: Path to data/input/<catchment>/
        """
        self.trading_dir = Path(trading_dir)
        self.input_dir = Path(input_dir)
        self.state_file = self.trading_dir / 'market_state.json'
        self.trading_dir.mkdir(parents=True, exist_ok=True)

    def _load_base_curves(self) -> Dict:
        """Load base hazard curves from gaugehc.json."""
        gaugehc_path = self.input_dir / 'gaugehc.json'
        if not gaugehc_path.exists():
            logger.warning("gaugehc.json not found at %s", gaugehc_path)
            return {}

        with open(gaugehc_path) as f:
            data = json.load(f)

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
        if not self.state_file.exists():
            return self._initialize()

        with open(self.state_file) as f:
            state = json.load(f)

        # Reconcile: add any gauges present in gaugehc.json but missing
        # from the persisted state (happens when classifiers add new gauges).
        current_base = self._load_base_curves()
        existing_base = state.get('base_rates', {})
        hazard_ts = state.get('hazard_term_structure', {})

        added = 0
        for gauge_id, base in current_base.items():
            if gauge_id not in existing_base:
                existing_base[gauge_id] = base
                # Build default term structure for the new gauge
                hazard_ts[gauge_id] = {}
                for trigger in ['alert', 'warning', 'severe']:
                    rate_key = f'annual_hazard_rate_{trigger}'
                    base_rate = base.get(rate_key, 0.02)
                    hazard_ts[gauge_id][trigger] = {
                        str(t): round(base_rate * (1 + 0.05 * t), 6)
                        for t in range(1, 6)
                    }
                added += 1

        if added:
            state['base_rates'] = existing_base
            state['hazard_term_structure'] = hazard_ts
            self._save(state)
            logger.info("Reconciled market state: added %d new gauges "
                        "(now %d total)", added, len(existing_base))

        return state

    # Default yield curve — centralised in config.port
    DEFAULT_YIELD_CURVE = _DEFAULT_YIELD_CURVE

    def _initialize(self) -> Dict:
        """Create initial market state from base curves."""
        base_rates = self._load_base_curves()

        # Build default hazard term structures: flat at base rate, slope to 1.25x at 5Y
        hazard_ts = {}
        for gauge_id, base in base_rates.items():
            hazard_ts[gauge_id] = {}
            for trigger in ['alert', 'warning', 'severe']:
                rate_key = f'annual_hazard_rate_{trigger}'
                base_rate = base.get(rate_key, 0.02)
                hazard_ts[gauge_id][trigger] = {
                    str(t): round(base_rate * (1 + 0.05 * t), 6)
                    for t in range(1, 6)
                }

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
        """Persist market state to disk."""
        state['last_updated'] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

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

    def get_yield_rate(self, state: Dict, tenor: int) -> float:
        """Get yield rate for a given tenor from the yield curve."""
        curve = state.get('yield_curve', {})
        rate = curve.get(str(tenor))
        if rate is not None:
            return rate
        # Linear interpolation for non-integer tenors
        keys = sorted(int(k) for k in curve.keys())
        if not keys:
            return state.get('risk_free_rate', 0.04)
        if tenor <= keys[0]:
            return curve[str(keys[0])]
        if tenor >= keys[-1]:
            return curve[str(keys[-1])]
        for i in range(len(keys) - 1):
            if keys[i] <= tenor <= keys[i + 1]:
                t0, t1 = keys[i], keys[i + 1]
                r0, r1 = curve[str(t0)], curve[str(t1)]
                return r0 + (r1 - r0) * (tenor - t0) / (t1 - t0)
        return state.get('risk_free_rate', 0.04)

    def update_yield_curve(self, tenor: int, rate: float) -> Dict:
        """Update a single point on the yield curve."""
        state = self.load()
        if 'yield_curve' not in state:
            state['yield_curve'] = dict(self.DEFAULT_YIELD_CURVE)
        state['yield_curve'][str(tenor)] = round(rate, 6)
        self._save(state)
        logger.info("Yield curve updated: %dY = %.4f", tenor, rate)
        return state

    def commit_yield_curve(self, rates: Dict) -> Dict:
        """Commit a full yield curve in one save.

        Args:
            rates: Dict mapping tenor (str) to rate (float), e.g. {'1': 0.035}

        Returns:
            Updated market state
        """
        state = self.load()
        if 'yield_curve' not in state:
            state['yield_curve'] = dict(self.DEFAULT_YIELD_CURVE)
        for tenor_str, rate in rates.items():
            state['yield_curve'][str(tenor_str)] = round(float(rate), 6)
        self._save(state)
        logger.info("Yield curve committed (%d tenors)", len(rates))
        return state

    def reset_yield_curve(self) -> Dict:
        """Reset yield curve to default."""
        state = self.load()
        state['yield_curve'] = dict(self.DEFAULT_YIELD_CURVE)
        self._save(state)
        logger.info("Yield curve reset to default")
        return state

    def get_hazard_rate_for_tenor(self, state: Dict, gauge_id: str,
                                   trigger: str, tenor: int) -> float:
        """Get hazard rate for a specific gauge/trigger/tenor from term structure."""
        ts = state.get('hazard_term_structure', {}).get(gauge_id, {}).get(trigger, {})
        rate = ts.get(str(tenor))
        if rate is not None:
            return rate
        # Fall back to flat rate from adjustments/base
        return self.get_gauge_rate(state, gauge_id, trigger)

    def update_hazard_term_point(self, gauge_id: str, trigger: str,
                                  tenor: int, rate: float) -> Dict:
        """Update a single point on a gauge's hazard term structure."""
        state = self.load()
        ts = state.setdefault('hazard_term_structure', {})
        gauge_ts = ts.setdefault(gauge_id, {})
        trigger_ts = gauge_ts.setdefault(trigger, {})
        trigger_ts[str(tenor)] = round(rate, 6)
        # Also update the flat rate for this trigger (use the average)
        rates = [trigger_ts[str(t)] for t in range(1, 6) if str(t) in trigger_ts]
        if rates:
            avg_rate = sum(rates) / len(rates)
            self.update_gauge_rate(gauge_id, trigger, avg_rate)
        self._save(state)
        logger.info("Hazard TS updated: %s %s %dY = %.6f", gauge_id, trigger, tenor, rate)
        return state

    def commit_hazard_term_structure(self, gauge_id: str, trigger: str,
                                       rates: Dict) -> Dict:
        """
        Commit a full hazard term structure for a gauge/trigger in one save.

        Args:
            gauge_id: Gauge identifier
            trigger: Trigger level (alert, warning, severe)
            rates: Dict mapping tenor (str) to rate (float), e.g. {'1': 0.025}

        Returns:
            Updated market state
        """
        state = self.load()
        ts = state.setdefault('hazard_term_structure', {})
        gauge_ts = ts.setdefault(gauge_id, {})
        trigger_ts = gauge_ts.setdefault(trigger, {})

        for tenor_str, rate in rates.items():
            trigger_ts[str(tenor_str)] = round(float(rate), 6)

        # Update the flat rate (average of all stored tenors)
        all_rates = [trigger_ts[str(t)] for t in range(1, 6)
                     if str(t) in trigger_ts]
        if all_rates:
            avg_rate = sum(all_rates) / len(all_rates)
            key = f'annual_hazard_rate_{trigger}'
            adj = state.setdefault('gauge_adjustments', {})
            if gauge_id not in adj:
                adj[gauge_id] = {}
            adj[gauge_id][key] = avg_rate
            adj[gauge_id]['adjusted_at'] = datetime.now().isoformat()

        self._save(state)
        logger.info("Hazard TS committed: %s %s (%d tenors)",
                     gauge_id, trigger, len(rates))
        return state

    def reset_hazard_term_structure(self, gauge_id: str = None) -> Dict:
        """Reset hazard term structure to defaults based on base rates."""
        state = self.load()
        ts = state.get('hazard_term_structure', {})
        base_rates = state.get('base_rates', {})

        if gauge_id:
            base = base_rates.get(gauge_id, {})
            ts[gauge_id] = {}
            for trigger in ['alert', 'warning', 'severe']:
                base_rate = base.get(f'annual_hazard_rate_{trigger}', 0.02)
                ts[gauge_id][trigger] = {
                    str(t): round(base_rate * (1 + 0.05 * t), 6)
                    for t in range(1, 6)
                }
        else:
            for gid, base in base_rates.items():
                ts[gid] = {}
                for trigger in ['alert', 'warning', 'severe']:
                    base_rate = base.get(f'annual_hazard_rate_{trigger}', 0.02)
                    ts[gid][trigger] = {
                        str(t): round(base_rate * (1 + 0.05 * t), 6)
                        for t in range(1, 6)
                    }

        state['hazard_term_structure'] = ts
        self._save(state)
        logger.info("Hazard TS reset%s", f" for {gauge_id}" if gauge_id else " (all)")
        return state
