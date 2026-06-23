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

"""Coverage expansion tests for market_state.py — reconciliation of new
gauges in load() (lines 136-153) and get_yield_rate final fallback (line 323)."""

import pytest

import database
from db_helpers import seed_gauge_hazard_curves, tmp_catchment
from models.trading.market_state import MarketStateManager


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend (catchment "thames"); MarketStateManager reads gauge
    hazard curves and reads/writes market state through ``database``."""
    with tmp_catchment(tmp_path, catchment="thames"):
        yield


@pytest.fixture
def two_gauge_env():
    """Environment with one gauge initially seeded; a second gauge is added later."""
    gauge_a = {
        "gauge_id": "GAUGE-A",
        "gauge_name": "Gauge A",
        "annual_hazard_rate_alert": 0.04,
        "annual_hazard_rate_warning": 0.025,
        "annual_hazard_rate_severe": 0.01,
        "curve_points": [],
        "gev_location": 3.0,
        "gev_scale": 0.5,
        "gev_shape": 0.0,
    }
    seed_gauge_hazard_curves(database.active_catchment(), [gauge_a])

    return {"gauge_a": gauge_a}


class TestLoadReconciliation:
    """Lines 136-153: reconcile new gauges on load()."""

    def test_new_gauge_reconciled_on_load(self, two_gauge_env):
        """Adding a gauge to gaugehc.json causes reconciliation on next load."""
        env = two_gauge_env
        mgr = MarketStateManager()

        # First load — only gauge A
        state = mgr.load()
        assert "GAUGE-A" in state["base_rates"]
        assert "GAUGE-B" not in state["base_rates"]

        # Add gauge B to gaugehc.json
        gauge_b = {
            "gauge_id": "GAUGE-B",
            "gauge_name": "Gauge B",
            "annual_hazard_rate_alert": 0.06,
            "annual_hazard_rate_warning": 0.03,
            "annual_hazard_rate_severe": 0.015,
            "curve_points": [],
            "gev_location": 4.0,
            "gev_scale": 0.6,
            "gev_shape": 0.1,
        }
        seed_gauge_hazard_curves(
            database.active_catchment(), [env["gauge_a"], gauge_b]
        )

        # Second load — should reconcile
        state = mgr.load()
        assert "GAUGE-B" in state["base_rates"]
        assert "GAUGE-B" in state["hazard_term_structure"]

    def test_reconciled_gauge_has_term_structure(self, two_gauge_env):
        """Reconciled gauge has all triggers with 5 tenors each."""
        env = two_gauge_env
        mgr = MarketStateManager()
        mgr.load()  # initialize with gauge A

        gauge_b = {
            "gauge_id": "GAUGE-B",
            "gauge_name": "Gauge B",
            "annual_hazard_rate_alert": 0.06,
            "annual_hazard_rate_warning": 0.03,
            "annual_hazard_rate_severe": 0.015,
            "curve_points": [],
            "gev_location": 4.0,
            "gev_scale": 0.6,
            "gev_shape": 0.1,
        }
        seed_gauge_hazard_curves(
            database.active_catchment(), [env["gauge_a"], gauge_b]
        )

        state = mgr.load()
        ts = state["hazard_term_structure"]["GAUGE-B"]

        for trigger in ["alert", "warning", "severe"]:
            assert trigger in ts
            assert len(ts[trigger]) == 5
            # Check slope formula: base_rate * (1 + 0.05 * t)
            rate_key = f"annual_hazard_rate_{trigger}"
            base_rate = gauge_b[rate_key]
            for t in range(1, 6):
                expected = round(base_rate * (1 + 0.05 * t), 6)
                assert ts[trigger][str(t)] == expected

    def test_reconciliation_persisted_to_disk(self, two_gauge_env):
        """Reconciled state is persisted so second load doesn't re-reconcile."""
        env = two_gauge_env
        mgr = MarketStateManager()
        mgr.load()

        gauge_b = {
            "gauge_id": "GAUGE-B",
            "gauge_name": "Gauge B",
            "annual_hazard_rate_alert": 0.06,
            "annual_hazard_rate_warning": 0.03,
            "annual_hazard_rate_severe": 0.015,
            "curve_points": [],
            "gev_location": 4.0,
            "gev_scale": 0.6,
            "gev_shape": 0.1,
        }
        seed_gauge_hazard_curves(
            database.active_catchment(), [env["gauge_a"], gauge_b]
        )

        mgr.load()  # reconciles and saves

        # Re-read persisted state through the database seam
        disk_state = database.get_market_state(mgr.catchment)
        assert "GAUGE-B" in disk_state["base_rates"]
        assert "GAUGE-B" in disk_state["hazard_term_structure"]

    def test_no_reconciliation_when_no_new_gauges(self, two_gauge_env, monkeypatch):
        """Loading with same gauges doesn't re-persist the market state."""
        mgr = MarketStateManager()
        mgr.load()  # initialize + first save

        # Spy on the save: a second load with no new gauges must not re-persist.
        saves = []
        real_save = database.save_market_state
        monkeypatch.setattr(
            database, "save_market_state",
            lambda c, s: saves.append(c) or real_save(c, s),
        )

        mgr.load()
        assert saves == []
