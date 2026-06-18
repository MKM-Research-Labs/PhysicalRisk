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
Property flood timeseries — portfolio financial impact endpoints.

Joins property flood data with valuations and mortgages to compute
damage amounts, post-damage LTV, and negative equity counts.

Endpoints
---------
GET /propertyts/blotter
    REIT property portfolio blotter — headline info for all properties.

GET /propertyts/<storm_id>/portfolio-impact
    Impact of a single storm event (with PRS derivative payouts).

GET /propertyts/sequence/<sequence_id>/portfolio-impact
    Sequence-level impact: max flood depth across all storms in the sequence.

GET /propertyts/<storm_id>/basis
    Synthetic-gauge basis decomposition for a storm.

The implementation is split across sibling modules; this file just
imports them so their routes register on ``propertyts_bp``.
"""

# Re-export shared helpers for backward compatibility with any caller
# that previously did ``from routes.propertyts.financial import ...``.
from .financial_blotter import property_blotter  # noqa: F401
from .financial_basis import storm_basis  # noqa: F401
from .financial_impact import (  # noqa: F401
    portfolio_impact,
    sequence_portfolio_impact,
)
from .financial_loaders import (  # noqa: F401
    _build_property_entry,
    _check_options_and_dir,
    _load_gauge_elevations,
    _load_rloan_lookup,
    _load_prop_values,
    _load_property_details,
    _portfolio_totals,
)
from .financial_prs import (  # noqa: F401
    _enrich_with_prs,
    _load_all_prs_trades,
    _match_prs_to_properties,
)
