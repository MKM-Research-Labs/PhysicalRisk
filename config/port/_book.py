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

"""Portfolio/trading parameter registry — split submodule. See config.port."""

from typing import Dict, List


# ===========================================================================
# Book / Trade Parameters  (port/src/book/book_common.py)
# ===========================================================================

# Available tenor lengths (years)
TENORS: List[int] = [1, 2, 3, 5]

# Available notional amounts (GBP)
NOTIONALS: List[int] = [5_000_000, 8_000_000, 10_000_000, 12_000_000, 20_000_000]

# Flood trigger levels used in book generation
TRIGGERS: List[str] = ['severe']

# Maps trigger name → hazard rate field name on the gauge hazard record
TRIGGER_RATE_KEY: Dict[str, str] = {
    'warning': 'annual_hazard_rate_warning',
    'severe':  'annual_hazard_rate_severe',
    'alert':   'annual_hazard_rate_alert',
}

# Recovery rate assumption for CDS-equivalent pricing (0 % = full LGD)
RECOVERY: float = 0.0

# Default yield curve: humped shape peaking at 4Y (matches market_state.py)
# Keys are tenor in years as strings; values are continuous rates.
DEFAULT_YIELD_CURVE: Dict[str, float] = {
    '1': 0.035,   # 3.5%
    '2': 0.040,   # 4.0%
    '3': 0.043,   # 4.3%
    '4': 0.045,   # 4.5%  ← peak
    '5': 0.040,   # 4.0%
    '6': 0.040,   # 4.0%
}

# Bid/ask spread construction: each side deviates SPREAD_OFFSET_MIN–SPREAD_OFFSET_MAX bp
# from fair value, giving a total bid-ask of 6–20 bp
SPREAD_OFFSET_MIN: float = 3.0    # bps
SPREAD_OFFSET_MAX: float = 10.0   # bps


# ===========================================================================
# Property Book  (port/src/book/book_property.py)
# ===========================================================================
# Generates the property-level PRS client book that populates the Trading
# Desk's Client tab.  Tenors and weights are heavier on 3Y/5Y here (vs the
# gauge book's flatter distribution) to mirror real mortgage-linked
# protection demand from REIT clients.

# Available tenor lengths (years) for property PRS trades
PROPERTY_BOOK_TENORS: List[int] = [1, 2, 3, 5]

# Weighting across PROPERTY_BOOK_TENORS (must sum to 1.0)
PROPERTY_BOOK_TENOR_WEIGHTS: List[float] = [0.10, 0.20, 0.35, 0.35]

# Notional range for property trades (smaller than the gauge-level book —
# property protection is closer in size to a single mortgage exposure)
PROPERTY_BOOK_NOTIONAL_MIN: int = 2_000_000
PROPERTY_BOOK_NOTIONAL_MAX: int = 8_000_000
PROPERTY_BOOK_NOTIONAL_STEP: int = 1_000_000

# Target number of property trades to generate per port --blotter run
PROPERTY_BOOK_NUM_TRADES: int = 15


# ===========================================================================
# EOD Simulation  (port/src/historical_eod.py)
# ===========================================================================

# Number of business days to simulate (~3 months of trading history)
NUM_BUSINESS_DAYS: int = 63

# Daily volatility for hazard curve random walk (2 bp/day)
DAILY_HAZARD_VOL: float = 0.0002

# Maximum cumulative drift from base rate across the simulation (20 bp)
MAX_TOTAL_MOVE: float = 0.0020


# ===========================================================================
# Delta Engine  (models/trading/delta_engine.py)
# ===========================================================================

# 1 basis-point bump used for numerical FS01 (Flood Sensitivity 01) calculation
BUMP_1BP: float = 0.0001
