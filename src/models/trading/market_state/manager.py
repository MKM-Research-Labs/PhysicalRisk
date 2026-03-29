# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
MarketStateManager — facade class composing all curve-management mixins.

To add a new curve type (e.g. credit spreads, vol surfaces):
1. Create a new mixin module in this package (e.g. credit_spread.py)
2. Add it to the MarketStateManager bases below
"""

from pathlib import Path

from config.port import DEFAULT_YIELD_CURVE as _DEFAULT_YIELD_CURVE

from ._persistence import _PersistenceMixin
from .gauge_rates import GaugeRatesMixin
from .hazard_term import HazardTermMixin
from .yield_curve import YieldCurveMixin


class MarketStateManager(
    _PersistenceMixin,
    GaugeRatesMixin,
    YieldCurveMixin,
    HazardTermMixin,
):
    """Manages the current market state (adjusted hazard curves)."""

    # Default yield curve — centralised in config.port
    DEFAULT_YIELD_CURVE = _DEFAULT_YIELD_CURVE

    def __init__(self, trading_dir: Path, input_dir: Path):
        """
        Initialize market state manager.

        Args:
            trading_dir: Path to data/input/<catchment>/blotter/
            input_dir: Path to data/input/<catchment>/
        """
        self.trading_dir = Path(trading_dir)
        self.input_dir = Path(input_dir)
        self.state_file = self.trading_dir / 'market_state.json'
        self.trading_dir.mkdir(parents=True, exist_ok=True)
