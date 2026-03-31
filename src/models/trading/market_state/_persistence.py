# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Persistence mixin: loading, initializing, and saving market state."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

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
    """Handles market state persistence to/from disk."""

    trading_dir: Path
    input_dir: Path
    state_file: Path

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
        """Persist market state to disk."""
        state['last_updated'] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
