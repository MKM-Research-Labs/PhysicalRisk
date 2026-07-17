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
