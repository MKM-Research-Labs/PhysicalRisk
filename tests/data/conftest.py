# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Shared helpers for tests/data/ package."""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))
from config import PortfolioConfig

_config = PortfolioConfig()


# ---------------------------------------------------------------------------
# Paths shared by blotter data tests
# ---------------------------------------------------------------------------

GAUGEHC_PATH   = pathlib.Path(_config.get_input_dir()) / "gaugehc.json"
MARKET_STATE   = pathlib.Path(_config.get_trading_dir()) / "market_state.json"
TRADE_MARKS    = pathlib.Path(_config.get_trading_dir()) / "trade_marks.json"
EOD_DIR        = pathlib.Path(_config.get_eod_dir())
PRS_DIR        = pathlib.Path(_config.get_reports_dir("prs"))


# ---------------------------------------------------------------------------
# Constants shared by blotter data tests
# ---------------------------------------------------------------------------

GAUGE_REQUIRED_FIELDS = {
    "gauge_id", "gauge_name", "latitude", "longitude",
    "flood_alert_m", "flood_warning_m", "severe_flood_warning_m",
    "annual_hazard_rate_alert", "annual_hazard_rate_warning", "annual_hazard_rate_severe",
}

MARKET_STATE_REQUIRED_KEYS = {"yield_curve", "hazard_term_structure", "base_rates"}
YIELD_CURVE_TENORS = {"1", "2", "3", "4", "5"}


# ---------------------------------------------------------------------------
# Helper for lineage validation tests
# ---------------------------------------------------------------------------

def make_manifest(steps: dict) -> dict:
    """Helper to build a manifest dict for testing."""
    return {"runs": {}, "steps": steps}
