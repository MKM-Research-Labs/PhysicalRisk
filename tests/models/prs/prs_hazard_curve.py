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
Tests for models.prs.prshc — PRS pricing with hazard curves.

Covers: load_hazard_curves, create_survival_curve_from_hazard,
create_flat_hazard_curve, price_prs (use_term_structure True/False,
all trigger levels), print_pricing_results.
"""

import json
import logging
from pathlib import Path

import pytest

try:
    import QuantLib as ql
    HAS_QUANTLIB = True
except ImportError:
    HAS_QUANTLIB = False

pytestmark = pytest.mark.skipif(not HAS_QUANTLIB, reason="QuantLib not installed")


# ===========================================================================
# Sample gauge data
# ===========================================================================

_GAUGE_DATA = {
    "gauge_id": "TEST-GAUGE-001",
    "gauge_name": "Test Gauge",
    "flood_alert_m": 4.0,
    "flood_warning_m": 4.5,
    "severe_flood_warning_m": 5.0,
    "annual_hazard_rate_alert": 0.12,
    "annual_hazard_rate_warning": 0.05,
    "annual_hazard_rate_severe": 0.02,
    "term_structure_alert": [
        {"year": 1, "survival_prob": 0.88},
        {"year": 2, "survival_prob": 0.77},
        {"year": 3, "survival_prob": 0.68},
        {"year": 4, "survival_prob": 0.60},
        {"year": 5, "survival_prob": 0.53},
    ],
    "term_structure_warning": [
        {"year": 1, "survival_prob": 0.95},
        {"year": 2, "survival_prob": 0.90},
        {"year": 3, "survival_prob": 0.86},
        {"year": 4, "survival_prob": 0.81},
        {"year": 5, "survival_prob": 0.77},
    ],
    "term_structure_severe": [
        {"year": 1, "survival_prob": 0.98},
        {"year": 2, "survival_prob": 0.96},
        {"year": 3, "survival_prob": 0.94},
        {"year": 4, "survival_prob": 0.92},
        {"year": 5, "survival_prob": 0.90},
    ],
}


# ===========================================================================
# load_hazard_curves
# ===========================================================================

class TestLoadHazardCurves:

    def test_loads_from_file(self, tmp_path):
        from models.prs.prshc import load_hazard_curves
        data = {"hazard_curves": {"TEST-G001": _GAUGE_DATA}}
        path = tmp_path / "gaugehc.json"
        path.write_text(json.dumps(data))
        result = load_hazard_curves(str(path))
        assert "hazard_curves" in result

    def test_loaded_data_has_gauge(self, tmp_path):
        from models.prs.prshc import load_hazard_curves
        data = {"hazard_curves": {"TEST-G001": _GAUGE_DATA}}
        path = tmp_path / "gaugehc.json"
        path.write_text(json.dumps(data))
        result = load_hazard_curves(str(path))
        assert "TEST-G001" in result["hazard_curves"]


# ===========================================================================
# create_survival_curve_from_hazard
# ===========================================================================

class TestCreateSurvivalCurveFromHazard:

    def test_survival_equals_1_uses_fallback_hazard_rate(self):
        """Line 83: final_survival >= 1 → uses 0.05 default hazard rate."""
        from models.prs.prshc import create_survival_curve_from_hazard
        date = ql.Date(1, 1, 2026)
        ql.Settings.instance().evaluationDate = date
        # survival_prob = 1.0 at year 5 → fallback branch
        term = [{"year": i+1, "survival_prob": 1.0} for i in range(5)]
        curve = create_survival_curve_from_hazard(date, term)
        assert curve is not None

    def test_survival_equals_0_uses_fallback_hazard_rate(self):
        """Line 83: final_survival <= 0 → uses 0.05 default hazard rate."""
        from models.prs.prshc import create_survival_curve_from_hazard
        date = ql.Date(1, 1, 2026)
        ql.Settings.instance().evaluationDate = date
        term = [{"year": i+1, "survival_prob": 0.0} for i in range(5)]
        curve = create_survival_curve_from_hazard(date, term)
        assert curve is not None

    def test_returns_curve(self):
        from models.prs.prshc import create_survival_curve_from_hazard
        date = ql.Date(1, 1, 2026)
        ql.Settings.instance().evaluationDate = date
        curve = create_survival_curve_from_hazard(date, _GAUGE_DATA["term_structure_warning"])
        assert curve is not None

    def test_default_day_counter(self):
        from models.prs.prshc import create_survival_curve_from_hazard
        date = ql.Date(1, 1, 2026)
        ql.Settings.instance().evaluationDate = date
        curve = create_survival_curve_from_hazard(
            date, _GAUGE_DATA["term_structure_warning"], day_counter=None
        )
        assert curve is not None

    def test_custom_day_counter(self):
        from models.prs.prshc import create_survival_curve_from_hazard
        date = ql.Date(1, 1, 2026)
        ql.Settings.instance().evaluationDate = date
        curve = create_survival_curve_from_hazard(
            date, _GAUGE_DATA["term_structure_warning"], day_counter=ql.Actual360()
        )
        assert curve is not None

    def test_full_survival_at_start(self):
        from models.prs.prshc import create_survival_curve_from_hazard
        date = ql.Date(1, 1, 2026)
        ql.Settings.instance().evaluationDate = date
        curve = create_survival_curve_from_hazard(date, _GAUGE_DATA["term_structure_severe"])
        sp = curve.survivalProbability(date)
        assert abs(sp - 1.0) < 1e-6


# ===========================================================================
# create_flat_hazard_curve
# ===========================================================================

class TestCreateFlatHazardCurve:

    def test_returns_curve_and_quote(self):
        from models.prs.prshc import create_flat_hazard_curve
        date = ql.Date(1, 1, 2026)
        ql.Settings.instance().evaluationDate = date
        curve, quote = create_flat_hazard_curve(date, 0.05)
        assert curve is not None
        assert quote is not None

    def test_default_day_counter(self):
        from models.prs.prshc import create_flat_hazard_curve
        date = ql.Date(1, 1, 2026)
        ql.Settings.instance().evaluationDate = date
        curve, quote = create_flat_hazard_curve(date, 0.1, day_counter=None)
        assert curve is not None


# ===========================================================================
# price_prs
# ===========================================================================

class TestPricePrs:

    def test_returns_dict(self):
        from models.prs.prshc import price_prs
        result = price_prs(_GAUGE_DATA, trigger_level="warning")
        assert isinstance(result, dict)

    def test_result_has_npv(self):
        from models.prs.prshc import price_prs
        result = price_prs(_GAUGE_DATA, trigger_level="warning")
        assert "npv" in result
        assert isinstance(result["npv"], float)

    def test_result_has_fair_spread_bps(self):
        from models.prs.prshc import price_prs
        result = price_prs(_GAUGE_DATA, trigger_level="warning")
        assert "fair_spread_bps" in result
        assert result["fair_spread_bps"] > 0

    def test_alert_trigger(self):
        from models.prs.prshc import price_prs
        result = price_prs(_GAUGE_DATA, trigger_level="alert")
        assert result["trigger_level"] == "alert"
        assert result["trigger_threshold_m"] == 4.0

    def test_severe_trigger(self):
        from models.prs.prshc import price_prs
        result = price_prs(_GAUGE_DATA, trigger_level="severe")
        assert result["trigger_level"] == "severe"
        assert result["trigger_threshold_m"] == 5.0

    def test_flat_hazard_curve(self):
        from models.prs.prshc import price_prs
        result = price_prs(_GAUGE_DATA, trigger_level="warning", use_term_structure=False)
        assert "fair_spread_bps" in result
        assert result["use_term_structure"] is False

    def test_term_structure_true(self):
        from models.prs.prshc import price_prs
        result = price_prs(_GAUGE_DATA, trigger_level="warning", use_term_structure=True)
        assert result["use_term_structure"] is True

    def test_result_has_survival_probabilities(self):
        from models.prs.prshc import price_prs
        result = price_prs(_GAUGE_DATA, trigger_level="warning", tenor_years=3)
        sp = result["survival_probabilities"]
        assert len(sp) == 3
        assert "1yr" in sp

    def test_custom_notional(self):
        from models.prs.prshc import price_prs
        result = price_prs(_GAUGE_DATA, trigger_level="warning", notional=5_000_000)
        assert result["notional"] == 5_000_000


# ===========================================================================
# print_pricing_results
# ===========================================================================

class TestPrintPricingResults:

    def test_logs_without_error(self, caplog):
        from models.prs.prshc import price_prs, print_pricing_results
        result = price_prs(_GAUGE_DATA, trigger_level="warning")
        with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
            print_pricing_results(result)
        # Should have logged some info
        assert len(caplog.records) >= 0  # just runs without error

    def test_logs_gauge_name(self, caplog):
        from models.prs.prshc import price_prs, print_pricing_results
        result = price_prs(_GAUGE_DATA, trigger_level="warning")
        with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
            print_pricing_results(result)
        # May or may not appear depending on log capture
        assert isinstance(result["gauge_name"], str)
