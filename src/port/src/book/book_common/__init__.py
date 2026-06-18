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
Book generator — shared constants and pricing helpers.

Constants, yield curve, CDM record builder, leg PV computation, and
counterparty loading used by both market-making and Thames Central styles.
"""

from ._constants import (  # noqa: F401
    DEFAULT_YIELD_CURVE,
    NOTIONALS,
    RECOVERY,
    SPREAD_OFFSET_MAX,
    SPREAD_OFFSET_MIN,
    TENORS,
    TRIGGER_RATE_KEY,
    TRIGGERS,
    _REIT_PARTY_ID,
)
from ._records import _build_cdm_record, _load_counterparties
from ._pricing import _compute_leg_pvs, _price_and_save_trade

__all__ = [
    "DEFAULT_YIELD_CURVE",
    "NOTIONALS",
    "RECOVERY",
    "SPREAD_OFFSET_MAX",
    "SPREAD_OFFSET_MIN",
    "TENORS",
    "TRIGGER_RATE_KEY",
    "TRIGGERS",
    "_REIT_PARTY_ID",
    "_build_cdm_record",
    "_load_counterparties",
    "_compute_leg_pvs",
    "_price_and_save_trade",
]
