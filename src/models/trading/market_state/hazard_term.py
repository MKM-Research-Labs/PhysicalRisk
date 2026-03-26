# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Hazard term structure management mixin."""

import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)


class HazardTermMixin:
    """Manages per-gauge hazard term structures (rate curves by tenor)."""

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
