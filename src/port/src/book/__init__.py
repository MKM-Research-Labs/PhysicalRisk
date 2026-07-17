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

"""Book generators — market-making and Thames Central trading books."""

# Re-export public API for backward compatibility
from .book import (  # noqa: F401
    generate_market_making_book,
    generate_trade_pdfs,
    print_book_summary,
)
from .book_common import (  # noqa: F401
    DEFAULT_YIELD_CURVE,
    NOTIONALS,
    RECOVERY,
    SPREAD_OFFSET_MAX,
    SPREAD_OFFSET_MIN,
    TENORS,
    TRIGGER_RATE_KEY,
    TRIGGERS,
    _build_cdm_record,
    _compute_leg_pvs,
    _load_counterparties,
)
from .book_property import generate_property_book  # noqa: F401
from .book_thames import (  # noqa: F401
    THAMES_CENTRAL_AREAS,
    _AREA_TO_GAUGE_NAME,
    _THAMES_TRADE_SPECS,
    generate_thames_central_book,
)
