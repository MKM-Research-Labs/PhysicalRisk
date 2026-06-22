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

"""Shared fixtures for PnL engine tests."""

import pytest

from models.trading.pnl_engine import PnLEngine
from db_helpers import tmp_catchment


@pytest.fixture
def pnl_engine(tmp_path):
    """A PnLEngine bound to a tmp-rooted database backend (catchment "thames").

    The migrated engine reads/writes trade marks + keyed EOD snapshots through
    ``database``; rooting the backend at ``tmp_path`` isolates them."""
    with tmp_catchment(tmp_path, catchment="thames"):
        yield PnLEngine()


@pytest.fixture
def sample_enriched_trades():
    return [
        {
            "swap_id": "PRS-001",
            "gauge_id": "GAUGE-A",
            "property_id": None,
            "counterparty": "Bank A",
            "trigger": "warning",
            "notional": 10_000_000,
            "tenor": 5,
            "trade_spread_bps": 250.0,
            "fair_spread_bps": 260.0,
            "is_payer": True,
            "trade_date": "2026-01-15",
            "trade_status": "Open",
            "gauge_fs01": 4500,
            "basis_dv01": 0,
            "risky_annuity": 4.35,
        },
        {
            "swap_id": "PRS-002",
            "gauge_id": "GAUGE-B",
            "property_id": "PROP-001",
            "counterparty": "Bank B",
            "trigger": "warning",
            "notional": 5_000_000,
            "tenor": 3,
            "trade_spread_bps": 180.0,
            "fair_spread_bps": 175.0,
            "is_payer": True,
            "trade_date": "2026-02-20",
            "trade_status": "Open",
            "gauge_fs01": 2200,
            "basis_dv01": 1800,
            "risky_annuity": 2.85,
        },
    ]
