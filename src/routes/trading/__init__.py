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
Trading desk API routes.

Provides endpoints for the trader's workstation:
- Trade blotter (with deltas and P&L)
- Trade close-out
- Market state management (curve adjustments, revaluation)
- Portfolio risk grid
- Trade map data
- EOD submission, history, and PDF reports
- P&L time series
- Yield curve and hazard term structure management

Sub-modules:
- blotter: Trade blotter and close-out
- market_state: Market state GET/POST/reset
- risk: Risk grid and trade map
- eod: EOD submission, history, PDF
- curves: Yield curve, hazard TS, P&L series
- stress: Stress test scenarios
- port_stress: Portfolio stress
"""

from .blueprint import trading_bp  # noqa: F401

# Import sub-modules to register their routes on trading_bp.
from . import blotter       # noqa: E402, F401
from . import market_state  # noqa: E402, F401
from . import risk          # noqa: E402, F401
from . import eod           # noqa: E402, F401
from . import curves        # noqa: E402, F401
from . import curves_yield  # noqa: E402, F401
from . import curves_hazard # noqa: E402, F401
from . import stress        # noqa: E402, F401
from . import port_stress   # noqa: E402, F401
from . import classifiers   # noqa: E402, F401
from . import client        # noqa: E402, F401
from . import control       # noqa: E402, F401
