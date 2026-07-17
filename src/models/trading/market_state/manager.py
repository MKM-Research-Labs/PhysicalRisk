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
MarketStateManager — facade class composing all curve-management mixins.

To add a new curve type (e.g. credit spreads, vol surfaces):
1. Create a new mixin module in this package (e.g. credit_spread.py)
2. Add it to the MarketStateManager bases below
"""

from typing import Optional

import database
from config.port import DEFAULT_YIELD_CURVE as _DEFAULT_YIELD_CURVE

from ._persistence import _PersistenceMixin
from .gauge_rates import GaugeRatesMixin
from .yield_curve import YieldCurveMixin
from .hazard_term import HazardTermMixin


class MarketStateManager(
    _PersistenceMixin,
    GaugeRatesMixin,
    YieldCurveMixin,
    HazardTermMixin,
):
    """Manages the current market state (adjusted hazard curves)."""

    # Default yield curve — centralised in config.port
    DEFAULT_YIELD_CURVE = _DEFAULT_YIELD_CURVE

    def __init__(self, catchment: Optional[str] = None):
        """
        Initialize market state manager.

        Args:
            catchment: Catchment to operate on (defaults to ``database.active_catchment()``).
        """
        self.catchment = catchment or database.active_catchment()
