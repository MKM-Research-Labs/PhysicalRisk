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
MarketStateManager — facade class composing all curve-management mixins.

To add a new curve type (e.g. credit spreads, vol surfaces):
1. Create a new mixin module in this package (e.g. credit_spread.py)
2. Add it to the MarketStateManager bases below
"""

from pathlib import Path

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
