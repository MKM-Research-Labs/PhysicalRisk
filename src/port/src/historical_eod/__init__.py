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
Historical EOD series generator.

Simulates 3 months (~63 business days) of trading history:
1. Starts with an empty portfolio
2. Adds trades one-at-a-time from the book (one per day up to ~50)
3. Applies a random walk to hazard term structures each day
4. Saves market state, revalues all open trades, generates EOD snapshots

This produces realistic daily P&L, running P&L, and curve history data
for the Curves tab and EOD P&L charts.
"""

from config.port import DAILY_HAZARD_VOL, MAX_TOTAL_MOVE, NUM_BUSINESS_DAYS

from ._business_days import _business_days
from ._history import (
    generate_hazard_curve_history_file,
    generate_trade_pnl_history_file,
)
from ._series import generate_historical_eod_series

__all__ = [
    "_business_days",
    "generate_hazard_curve_history_file",
    "generate_trade_pnl_history_file",
    "generate_historical_eod_series",
    "DAILY_HAZARD_VOL",
    "MAX_TOTAL_MOVE",
    "NUM_BUSINESS_DAYS",
]
