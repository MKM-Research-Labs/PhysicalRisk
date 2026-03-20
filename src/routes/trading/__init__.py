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

from flask import Blueprint

from ._helpers import no_cache

trading_bp = Blueprint("trading", __name__)
trading_bp.after_request(no_cache)

# Import sub-modules to register their routes on trading_bp.
# These must come after trading_bp is defined to avoid circular imports.
from . import blotter       # noqa: E402, F401
from . import market_state  # noqa: E402, F401
from . import risk          # noqa: E402, F401
from . import eod           # noqa: E402, F401
from . import curves        # noqa: E402, F401
from . import stress        # noqa: E402, F401
from . import port_stress   # noqa: E402, F401
from . import classifiers   # noqa: E402, F401
