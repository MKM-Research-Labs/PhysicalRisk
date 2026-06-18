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

"""Tests for price_prs — types, leg signs, gauge passthrough, risk-free, recovery."""

import pytest

try:
    HAS_QUANTLIB = True
    import QuantLib as ql
except ImportError:
    HAS_QUANTLIB = False

pytestmark = pytest.mark.skipif(not HAS_QUANTLIB, reason="QuantLib not installed")


class TestPricePrsTypes:

    def test_npv_is_float(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="warning")
        assert isinstance(r["npv"], float)

    def test_fair_upfront_is_float(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="warning")
        assert isinstance(r["fair_upfront"], float)

    def test_fair_spread_is_float(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="warning")
        assert isinstance(r["fair_spread"], float)

    def test_running_spread_bps_identity(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="warning", running_spread=0.0075)
        assert r["running_spread_bps"] == pytest.approx(r["running_spread"] * 10000, rel=1e-9)

    def test_use_term_structure_stored_true(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="warning", use_term_structure=True)
        assert r["use_term_structure"] is True

    def test_use_term_structure_stored_false(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="warning", use_term_structure=False)
        assert r["use_term_structure"] is False

    def test_survival_probs_all_in_zero_one(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="alert", tenor_years=5)
        for key, val in r["survival_probabilities"].items():
            assert 0.0 < val <= 1.0, f"Survival prob out of range for {key}: {val}"

    def test_tenor_1yr_gives_one_survival_entry(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="warning", tenor_years=1)
        assert len(r["survival_probabilities"]) == 1
        assert "1yr" in r["survival_probabilities"]


class TestPricePrsLegSigns:

    def test_protection_leg_positive(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="warning")
        assert r["protection_leg_npv"] > 0

    def test_premium_leg_negative(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="warning")
        assert r["premium_leg_npv"] < 0

    def test_npv_is_sum_of_legs(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="warning")
        assert r["npv"] == pytest.approx(
            r["protection_leg_npv"] + r["premium_leg_npv"], rel=1e-3
        )


class TestPricePrsGaugePassthrough:

    def test_gauge_id_in_result(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="warning")
        assert r["gauge_id"] == gauge["gauge_id"]

    def test_gauge_name_in_result(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="warning")
        assert r["gauge_name"] == gauge["gauge_name"]

    def test_annual_hazard_rate_matches_input(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="warning")
        assert r["annual_hazard_rate"] == gauge["annual_hazard_rate_warning"]

    def test_severe_annual_hazard_rate_matches_input(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="severe")
        assert r["annual_hazard_rate"] == gauge["annual_hazard_rate_severe"]


class TestPricePrsRiskFreeRate:

    def test_higher_risk_free_rate_changes_npv(self, gauge):
        from models.prs.prshc import price_prs
        r_low = price_prs(gauge, trigger_level="warning", risk_free_rate=0.01)
        r_high = price_prs(gauge, trigger_level="warning", risk_free_rate=0.08)
        assert r_low["npv"] != pytest.approx(r_high["npv"], rel=1e-4)

    def test_risk_free_rate_not_in_output(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="warning", risk_free_rate=0.05)
        assert "risk_free_rate" not in r


class TestPricePrsRecoveryRate:

    def test_nonzero_recovery_rate_stored(self, gauge):
        from models.prs.prshc import price_prs
        r = price_prs(gauge, trigger_level="warning", recovery_rate=0.4)
        assert r["recovery_rate"] == pytest.approx(0.4)

    def test_recovery_rate_affects_fair_spread(self, gauge):
        from models.prs.prshc import price_prs
        r0 = price_prs(gauge, trigger_level="warning", recovery_rate=0.0)
        r40 = price_prs(gauge, trigger_level="warning", recovery_rate=0.4)
        assert r0["fair_spread_bps"] > r40["fair_spread_bps"]
