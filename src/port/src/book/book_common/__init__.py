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
