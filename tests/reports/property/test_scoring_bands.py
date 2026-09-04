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

"""Risk-band edges in the property scoring assessment.

Three uncovered arms: the unknown-LTV fallback, and the HIGH RISK band in
each of the two assessors. All three decide what a reader is told about a
loan, so they are worth pinning rather than inferring from neighbours.
"""

import pytest

from reports.property.property_page_13_scoring._assessment import (
    comprehensive_risk_assessment,
    property_risk_assessment,
)


def _property(flood_risk="Medium"):
    return {
        "PropertyHeader": {
            "Header": {"PropertyID": "PROP-001"},
            "RiskAssessment": {"OverallFloodRisk": flood_risk},
        }
    }


def _loan(ltv):
    return {"RLoan": {"CurrentStatus": {"CurrentLTV": ltv}}}


class TestLtvBand:
    def test_a_non_numeric_ltv_scores_as_unknown(self):
        """A missing or malformed LTV must not score as 0% — the safest
        reading is mid-band with the uncertainty stated, not the best case."""
        result = comprehensive_risk_assessment(_property(), _loan("n/a"))
        ltv = result["categories"]["Current LTV Risk"]
        assert ltv["impact"] == "Unknown LTV"
        assert ltv["score"] == 3

    def test_an_absent_status_block_scores_as_the_safest_band(self):
        """Documenting current behaviour, which is not obviously right.

        A missing CurrentStatus defaults CurrentLTV to 0, which is numeric,
        so it takes the arithmetic path and lands in "Low LTV (<70%)" — the
        *best* band — rather than the "Unknown LTV" fallback beside it. A loan
        with no status recorded therefore scores better than one at 60% LTV.
        Pinned so the behaviour is visible; changing it is a modelling
        decision, not a test fix.
        """
        result = comprehensive_risk_assessment(_property(), {"RLoan": {}})
        assert result["categories"]["Current LTV Risk"]["impact"] == "Low LTV (<70%)"
        assert result["categories"]["Current LTV Risk"]["score"] == 1

    @pytest.mark.parametrize("ltv,expected", [
        (0.98, "Very High LTV (>95%)"),
        (0.92, "High LTV (90-95%)"),
        (0.85, "Medium LTV (80-90%)"),
        (0.75, "Low-Medium LTV (70-80%)"),
        (0.60, "Low LTV (<70%)"),
    ])
    def test_fractional_ltvs_are_scaled_to_percentages(self, ltv, expected):
        """LTV arrives either as a fraction or as a percentage; both must land
        in the same band."""
        result = comprehensive_risk_assessment(_property(), _loan(ltv))
        assert result["categories"]["Current LTV Risk"]["impact"] == expected
        pct = comprehensive_risk_assessment(_property(), _loan(ltv * 100))
        assert pct["categories"]["Current LTV Risk"]["impact"] == expected


class TestOverallRiskBands:
    def test_the_comprehensive_assessor_reports_high_risk(self):
        """The 70-85% band, named exactly.

        Flood risk and LTV alone top out at 55%, so this band is only
        reachable once payment history and credit are in play — which is why
        a fixture carrying just a property and an LTV never reached it.
        """
        loan = {"RLoan": {
            "CurrentStatus": {"CurrentLTV": 0.92, "InArrearsFlag": True,
                              "MissedPayments12M": 2},
            "BorrowerDetails": {"BorrowerCreditScore": 650},
        }}
        result = comprehensive_risk_assessment(_property("High"), loan)
        assert result["overall_percentage"] == 80.0
        assert result["overall_level"] == "HIGH RISK"
        assert result["overall_color"] == "ORANGE"

    def test_the_property_only_assessor_reports_high_risk(self):
        """The property-only ladder has three bands, not five, so a
        very-high-flood-risk property reaches its top band on flood risk
        alone."""
        result = property_risk_assessment(_property("Very High"))
        assert result["overall_level"] == "HIGH RISK"
        assert result["overall_color"] == "ORANGE"

    def test_the_two_assessors_agree_on_direction(self):
        """Both ladders must move the same way with flood risk; a sign flip in
        one would price the same property two ways depending on which report
        rendered it."""
        low = property_risk_assessment(_property("Very Low"))
        high = property_risk_assessment(_property("Very High"))
        assert high["overall_percentage"] > low["overall_percentage"]
