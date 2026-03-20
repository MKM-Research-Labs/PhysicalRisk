# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Data availability tests — Blotter.

Verifies that all files required by the trading blotter are present on
disk and structurally correct.  These tests use the real production data
files, not fixtures.

Run `python app.py book` first to generate PRS trade files if they are
absent.
"""

import json
import pathlib
import pytest

import sys
sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))
from config import PortfolioConfig

config = PortfolioConfig()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

GAUGEHC_PATH   = pathlib.Path(config.get_input_dir()) / "gaugehc.json"
MARKET_STATE   = pathlib.Path(config.get_trading_dir()) / "market_state.json"
PRS_DIR        = pathlib.Path(config.get_reports_dir("prs"))

GAUGE_REQUIRED_FIELDS = {
    "gauge_id", "gauge_name", "latitude", "longitude",
    "flood_alert_m", "flood_warning_m", "severe_flood_warning_m",
    "annual_hazard_rate_alert", "annual_hazard_rate_warning", "annual_hazard_rate_severe",
}

MARKET_STATE_REQUIRED_KEYS = {"yield_curve", "hazard_term_structure", "base_rates"}
YIELD_CURVE_TENORS = {"1", "2", "3", "4", "5"}


# ---------------------------------------------------------------------------
# Gauge hazard curves (gaugehc.json)
# ---------------------------------------------------------------------------

class TestGaugehcData:
    """gaugehc.json must exist and contain valid hazard curve data for all gauges."""

    @pytest.fixture(scope="class")
    def gaugehc(self):
        assert GAUGEHC_PATH.exists(), f"gaugehc.json not found at {GAUGEHC_PATH}"
        return json.loads(GAUGEHC_PATH.read_text())

    def test_file_exists(self):
        assert GAUGEHC_PATH.exists(), f"Missing: {GAUGEHC_PATH}"

    def test_has_hazard_curves_key(self, gaugehc):
        assert "hazard_curves" in gaugehc, "gaugehc.json missing top-level 'hazard_curves' key"

    def test_gauge_count_at_least_40(self, gaugehc):
        count = len(gaugehc["hazard_curves"])
        assert count >= 40, f"Expected at least 40 gauges, got {count}"

    def test_each_gauge_has_required_fields(self, gaugehc):
        missing = {}
        for gid, g in gaugehc["hazard_curves"].items():
            absent = GAUGE_REQUIRED_FIELDS - set(g.keys())
            if absent:
                missing[gid] = absent
        assert not missing, f"Gauges missing required fields: {missing}"

    def test_gauge_ids_are_well_formed(self, gaugehc):
        bad = [gid for gid in gaugehc["hazard_curves"] if not gid.startswith("GAUGE-")]
        assert not bad, f"Gauge IDs not in GAUGE-xxxx format: {bad[:5]}"

    def test_flood_trigger_ordering(self, gaugehc):
        """alert < warning < severe for every gauge."""
        violations = []
        for gid, g in gaugehc["hazard_curves"].items():
            a = g.get("flood_alert_m", 0)
            w = g.get("flood_warning_m", 0)
            s = g.get("severe_flood_warning_m", 0)
            if not (a < w < s):
                violations.append((gid, a, w, s))
        assert not violations, f"Flood trigger ordering violated: {violations[:3]}"

    def test_hazard_rates_positive(self, gaugehc):
        violations = []
        for gid, g in gaugehc["hazard_curves"].items():
            for field in ("annual_hazard_rate_alert", "annual_hazard_rate_warning", "annual_hazard_rate_severe"):
                v = g.get(field, -1)
                if v <= 0:
                    violations.append((gid, field, v))
        assert not violations, f"Non-positive hazard rates found: {violations[:3]}"

    def test_hazard_rate_ordering(self, gaugehc):
        """alert > warning > severe (higher trigger = lower probability)."""
        violations = []
        for gid, g in gaugehc["hazard_curves"].items():
            ra = g.get("annual_hazard_rate_alert", 0)
            rw = g.get("annual_hazard_rate_warning", 0)
            rs = g.get("annual_hazard_rate_severe", 0)
            if not (ra > rw > rs):
                violations.append((gid, ra, rw, rs))
        assert not violations, f"Hazard rate ordering violated: {violations[:3]}"

    def test_curve_points_present(self, gaugehc):
        missing = [gid for gid, g in gaugehc["hazard_curves"].items()
                   if not g.get("curve_points")]
        assert not missing, f"Gauges with empty curve_points: {missing[:5]}"

    def test_term_structure_present(self, gaugehc):
        missing = [gid for gid, g in gaugehc["hazard_curves"].items()
                   if not g.get("term_structure_alert")]
        assert not missing, f"Gauges missing term_structure_alert: {missing[:5]}"


# ---------------------------------------------------------------------------
# Market state (market_state.json)
# ---------------------------------------------------------------------------

class TestMarketStateData:
    """market_state.json must exist and contain a valid yield curve and hazard term structures."""

    @pytest.fixture(scope="class")
    def ms(self):
        assert MARKET_STATE.exists(), f"market_state.json not found at {MARKET_STATE}"
        return json.loads(MARKET_STATE.read_text())

    def test_file_exists(self):
        assert MARKET_STATE.exists(), f"Missing: {MARKET_STATE}"

    def test_has_required_keys(self, ms):
        missing = MARKET_STATE_REQUIRED_KEYS - set(ms.keys())
        assert not missing, f"market_state.json missing keys: {missing}"

    def test_yield_curve_has_all_tenors(self, ms):
        yc = ms.get("yield_curve", {})
        present = set(str(k) for k in yc.keys())
        missing = YIELD_CURVE_TENORS - present
        assert not missing, f"Yield curve missing tenors: {missing}"

    def test_yield_curve_rates_in_range(self, ms):
        yc = ms.get("yield_curve", {})
        bad = {t: r for t, r in yc.items() if not (0 < r < 1)}
        assert not bad, f"Yield curve rates outside (0,1): {bad}"

    def test_hazard_term_structure_not_empty(self, ms):
        hts = ms.get("hazard_term_structure", {})
        assert hts, "hazard_term_structure is empty"

    def test_hazard_term_structure_has_triggers(self, ms):
        hts = ms.get("hazard_term_structure", {})
        for gid, triggers in hts.items():
            assert "alert" in triggers, f"GAUGE {gid} missing 'alert' in hazard_term_structure"
            break  # spot-check first gauge

    def test_base_rates_not_empty(self, ms):
        br = ms.get("base_rates", {})
        assert br, "base_rates is empty in market_state.json"

    def test_last_updated_present(self, ms):
        assert "last_updated" in ms, "market_state.json missing 'last_updated' field"


# ---------------------------------------------------------------------------
# PRS trade files (data/output/prs/)
# ---------------------------------------------------------------------------

class TestPRSTradeData:
    """PRS trade files must be present and follow CDM structure.

    If the prs/ directory is empty, tests are skipped with a hint to run
    `python app.py book` to generate trades.
    """

    @pytest.fixture(scope="class")
    def prs_files(self):
        assert PRS_DIR.exists(), f"PRS directory not found: {PRS_DIR}"
        files = list(PRS_DIR.glob("PRS-*.json"))
        if not files:
            pytest.skip(
                f"No PRS trade files found in {PRS_DIR}. "
                "Run `python app.py book` to generate the trading book."
            )
        return files

    def test_prs_directory_exists(self):
        assert PRS_DIR.exists(), f"Missing PRS directory: {PRS_DIR}"

    def test_trades_are_present(self, prs_files):
        assert len(prs_files) >= 1, "Expected at least one PRS trade file"

    def test_trade_count_thames_central(self, prs_files):
        """Thames Central book has 16 trades."""
        assert len(prs_files) >= 16, (
            f"Expected >= 16 trades for Thames Central book, got {len(prs_files)}"
        )

    def test_each_trade_has_physical_swap_root(self, prs_files):
        bad = []
        for f in prs_files:
            d = json.loads(f.read_text())
            if "PhysicalSwap" not in d:
                bad.append(f.name)
        assert not bad, f"Trade files missing 'PhysicalSwap' root: {bad}"

    def test_each_trade_has_swap_id(self, prs_files):
        bad = []
        for f in prs_files:
            d = json.loads(f.read_text())
            swap = d.get("PhysicalSwap", {})
            header = swap.get("Header", {})
            if not header.get("SwapID"):
                bad.append(f.name)
        assert not bad, f"Trades missing SwapID in Header: {bad}"

    def test_swap_id_matches_filename(self, prs_files):
        bad = []
        for f in prs_files:
            d = json.loads(f.read_text())
            swap_id = d.get("PhysicalSwap", {}).get("Header", {}).get("SwapID", "")
            expected_name = f"{swap_id}.json"
            if f.name != expected_name:
                bad.append((f.name, expected_name))
        assert not bad, f"Filename/SwapID mismatch: {bad}"

    def test_trade_statuses_are_valid(self, prs_files):
        valid_statuses = {"open", "closed", "expired", "committed"}
        bad = []
        for f in prs_files:
            d = json.loads(f.read_text())
            status = d.get("PhysicalSwap", {}).get("Header", {}).get("TradeStatus", "")
            if status.lower() not in valid_statuses:
                bad.append((f.name, status))
        assert not bad, f"Trades with invalid TradeStatus: {bad}"

    def test_trades_have_gauge_set(self, prs_files):
        bad = []
        for f in prs_files:
            d = json.loads(f.read_text())
            swap = d.get("PhysicalSwap", {})
            if not swap.get("GaugeSet", {}).get("GaugeBasket"):
                bad.append(f.name)
        assert not bad, f"Trades missing GaugeSet.GaugeBasket: {bad}"
