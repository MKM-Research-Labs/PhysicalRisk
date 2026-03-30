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
from .book_thames import (  # noqa: F401
    THAMES_CENTRAL_AREAS,
    _AREA_TO_GAUGE_NAME,
    _THAMES_TRADE_SPECS,
    generate_thames_central_book,
)
