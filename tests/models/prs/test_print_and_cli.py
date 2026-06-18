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

"""Tests for print_pricing_results log content and main() CLI entry point."""

import json
import logging
from unittest.mock import patch

import pytest

try:
    HAS_QUANTLIB = True
    import QuantLib as ql
except ImportError:
    HAS_QUANTLIB = False

pytestmark = pytest.mark.skipif(not HAS_QUANTLIB, reason="QuantLib not installed")

from .conftest import make_gauge


class TestPrintPricingResultsContent:

    @pytest.fixture(scope="class")
    def result(self, gauge):
        from models.prs.prshc import price_prs
        return price_prs(gauge, trigger_level="warning", tenor_years=3)

    def test_gauge_id_in_log(self, result, caplog):
        from models.prs.prshc import print_pricing_results
        with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
            print_pricing_results(result)
        combined = " ".join(r.message for r in caplog.records)
        assert result["gauge_id"] in combined

    def test_gauge_name_in_log(self, result, caplog):
        from models.prs.prshc import print_pricing_results
        with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
            print_pricing_results(result)
        combined = " ".join(r.message for r in caplog.records)
        assert result["gauge_name"] in combined

    def test_trigger_level_in_log(self, result, caplog):
        from models.prs.prshc import print_pricing_results
        with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
            print_pricing_results(result)
        combined = " ".join(r.message for r in caplog.records)
        assert "WARNING" in combined

    def test_npv_value_in_log(self, result, caplog):
        from models.prs.prshc import print_pricing_results
        with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
            print_pricing_results(result)
        combined = " ".join(r.message for r in caplog.records)
        assert "NPV" in combined

    def test_fair_spread_in_log(self, result, caplog):
        from models.prs.prshc import print_pricing_results
        with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
            print_pricing_results(result)
        combined = " ".join(r.message for r in caplog.records)
        assert "Fair Spread" in combined

    def test_survival_curve_label_in_log(self, result, caplog):
        from models.prs.prshc import print_pricing_results
        with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
            print_pricing_results(result)
        combined = " ".join(r.message for r in caplog.records)
        assert "Survival Curve" in combined

    def test_all_survival_years_in_log(self, result, caplog):
        from models.prs.prshc import print_pricing_results
        with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
            print_pricing_results(result)
        combined = " ".join(r.message for r in caplog.records)
        for key in result["survival_probabilities"]:
            assert key in combined, f"Expected survival tenor '{key}' in log output"

    def test_severe_trigger_in_log(self, gauge, caplog):
        from models.prs.prshc import price_prs, print_pricing_results
        result = price_prs(gauge, trigger_level="severe", tenor_years=2)
        with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
            print_pricing_results(result)
        combined = " ".join(r.message for r in caplog.records)
        assert "SEVERE" in combined

    def test_alert_trigger_in_log(self, gauge, caplog):
        from models.prs.prshc import price_prs, print_pricing_results
        result = price_prs(gauge, trigger_level="alert", tenor_years=2)
        with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
            print_pricing_results(result)
        combined = " ".join(r.message for r in caplog.records)
        assert "ALERT" in combined

    def test_contract_terms_header_in_log(self, result, caplog):
        from models.prs.prshc import print_pricing_results
        with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
            print_pricing_results(result)
        combined = " ".join(r.message for r in caplog.records)
        assert "Contract Terms" in combined

    def test_premium_leg_in_log(self, result, caplog):
        from models.prs.prshc import print_pricing_results
        with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
            print_pricing_results(result)
        combined = " ".join(r.message for r in caplog.records)
        assert "Premium Leg" in combined

    def test_protection_leg_in_log(self, result, caplog):
        from models.prs.prshc import print_pricing_results
        with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
            print_pricing_results(result)
        combined = " ".join(r.message for r in caplog.records)
        assert "Protection Leg" in combined

    def test_recovery_rate_in_log(self, result, caplog):
        from models.prs.prshc import print_pricing_results
        with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
            print_pricing_results(result)
        combined = " ".join(r.message for r in caplog.records)
        assert "Recovery Rate" in combined


class TestMain:

    def _make_hazard_file(self, tmp_path, gauge_id="THAMES-G001"):
        gauge = make_gauge(gauge_id=gauge_id, gauge_name=f"Gauge {gauge_id}")
        data = {"hazard_curves": {gauge_id: gauge}}
        p = tmp_path / "gaugehc.json"
        p.write_text(json.dumps(data))
        return str(p)

    def test_list_flag_returns_zero(self, tmp_path):
        from models.prs.prshc import main
        path = self._make_hazard_file(tmp_path)
        with patch("sys.argv", ["prshc.py", "--hazard-file", path, "--list"]):
            rc = main()
        assert rc == 0

    def test_missing_gauge_returns_one(self, tmp_path):
        from models.prs.prshc import main
        path = self._make_hazard_file(tmp_path)
        with patch("sys.argv", ["prshc.py", "--hazard-file", path, "--gauge", "NO-SUCH-GAUGE"]):
            rc = main()
        assert rc == 1

    def test_default_gauge_selection_returns_zero(self, tmp_path):
        from models.prs.prshc import main
        path = self._make_hazard_file(tmp_path)
        with patch("sys.argv", ["prshc.py", "--hazard-file", path]):
            rc = main()
        assert rc == 0

    def test_explicit_gauge_returns_zero(self, tmp_path):
        from models.prs.prshc import main
        path = self._make_hazard_file(tmp_path, gauge_id="THAMES-G001")
        with patch("sys.argv", ["prshc.py", "--hazard-file", path, "--gauge", "THAMES-G001"]):
            rc = main()
        assert rc == 0

    def test_flat_flag_dispatches_flat_mode(self, tmp_path, caplog):
        from models.prs.prshc import main
        path = self._make_hazard_file(tmp_path)
        with patch("sys.argv", ["prshc.py", "--hazard-file", path, "--flat"]):
            with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
                rc = main()
        assert rc == 0

    def test_trigger_warning_explicit(self, tmp_path):
        from models.prs.prshc import main
        path = self._make_hazard_file(tmp_path)
        with patch("sys.argv", ["prshc.py", "--hazard-file", path, "--trigger", "warning"]):
            rc = main()
        assert rc == 0

    def test_trigger_alert_explicit(self, tmp_path):
        from models.prs.prshc import main
        path = self._make_hazard_file(tmp_path)
        with patch("sys.argv", ["prshc.py", "--hazard-file", path, "--trigger", "alert"]):
            rc = main()
        assert rc == 0

    def test_trigger_severe_explicit(self, tmp_path):
        from models.prs.prshc import main
        path = self._make_hazard_file(tmp_path)
        with patch("sys.argv", ["prshc.py", "--hazard-file", path, "--trigger", "severe"]):
            rc = main()
        assert rc == 0

    def test_custom_notional_and_spread(self, tmp_path):
        from models.prs.prshc import main
        path = self._make_hazard_file(tmp_path)
        with patch("sys.argv", [
            "prshc.py", "--hazard-file", path,
            "--notional", "5000000",
            "--spread", "0.005",
        ]):
            rc = main()
        assert rc == 0

    def test_list_flag_logs_gauge_names(self, tmp_path, caplog):
        from models.prs.prshc import main
        path = self._make_hazard_file(tmp_path, gauge_id="THAMES-TEST-99")
        with patch("sys.argv", ["prshc.py", "--hazard-file", path, "--list"]):
            with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
                main()
        combined = " ".join(r.message for r in caplog.records)
        assert "THAMES-TEST-99" in combined

    def test_missing_gauge_logs_error(self, tmp_path, caplog):
        from models.prs.prshc import main
        path = self._make_hazard_file(tmp_path)
        with patch("sys.argv", ["prshc.py", "--hazard-file", path, "--gauge", "GHOST-GAUGE"]):
            with caplog.at_level(logging.ERROR, logger="models.prs.prshc"):
                main()
        assert any("GHOST-GAUGE" in r.message for r in caplog.records)

    def test_missing_gauge_logs_available_gauges(self, tmp_path, caplog):
        from models.prs.prshc import main
        path = self._make_hazard_file(tmp_path, gauge_id="THAMES-G042")
        with patch("sys.argv", ["prshc.py", "--hazard-file", path, "--gauge", "GHOST-GAUGE"]):
            with caplog.at_level(logging.INFO, logger="models.prs.prshc"):
                main()
        combined = " ".join(r.message for r in caplog.records)
        assert "THAMES-G042" in combined
