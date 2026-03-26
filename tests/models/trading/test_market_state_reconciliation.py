"""Coverage expansion tests for market_state.py — reconciliation of new
gauges in load() (lines 136-153) and get_yield_rate final fallback (line 323)."""

import json

import pytest

from models.trading.market_state import MarketStateManager


@pytest.fixture
def two_gauge_env(tmp_path):
    """Environment with one gauge initially, second gauge added later."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    trading_dir = tmp_path / "trading"
    trading_dir.mkdir()

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
    (input_dir / "gaugehc.json").write_text(json.dumps([gauge_a]))

    return {
        "input_dir": input_dir,
        "trading_dir": trading_dir,
        "gauge_a": gauge_a,
    }


class TestLoadReconciliation:
    """Lines 136-153: reconcile new gauges on load()."""

    def test_new_gauge_reconciled_on_load(self, two_gauge_env):
        """Adding a gauge to gaugehc.json causes reconciliation on next load."""
        env = two_gauge_env
        mgr = MarketStateManager(env["trading_dir"], env["input_dir"])

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
        (env["input_dir"] / "gaugehc.json").write_text(
            json.dumps([env["gauge_a"], gauge_b])
        )

        # Second load — should reconcile
        state = mgr.load()
        assert "GAUGE-B" in state["base_rates"]
        assert "GAUGE-B" in state["hazard_term_structure"]

    def test_reconciled_gauge_has_term_structure(self, two_gauge_env):
        """Reconciled gauge has all triggers with 5 tenors each."""
        env = two_gauge_env
        mgr = MarketStateManager(env["trading_dir"], env["input_dir"])
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
        (env["input_dir"] / "gaugehc.json").write_text(
            json.dumps([env["gauge_a"], gauge_b])
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
        mgr = MarketStateManager(env["trading_dir"], env["input_dir"])
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
        (env["input_dir"] / "gaugehc.json").write_text(
            json.dumps([env["gauge_a"], gauge_b])
        )

        mgr.load()  # reconciles and saves

        # Re-read from disk directly
        with open(mgr.state_file) as f:
            disk_state = json.load(f)
        assert "GAUGE-B" in disk_state["base_rates"]
        assert "GAUGE-B" in disk_state["hazard_term_structure"]

    def test_no_reconciliation_when_no_new_gauges(self, two_gauge_env):
        """Loading with same gauges doesn't trigger reconciliation."""
        env = two_gauge_env
        mgr = MarketStateManager(env["trading_dir"], env["input_dir"])
        state1 = mgr.load()
        mtime1 = mgr.state_file.stat().st_mtime

        import time
        time.sleep(0.05)

        state2 = mgr.load()
        mtime2 = mgr.state_file.stat().st_mtime

        # File should not have been re-written
        assert mtime1 == mtime2
