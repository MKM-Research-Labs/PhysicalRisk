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

"""Shared fixtures and helpers for models.prs tests (QuantLib-dependent)."""

import json

import pytest

try:
    import QuantLib as ql
    HAS_QUANTLIB = True
except ImportError:
    HAS_QUANTLIB = False

pytestmark = pytest.mark.skipif(not HAS_QUANTLIB, reason="QuantLib not installed")


def term_structure(annual_rate: float, years: int = 5):
    """Geometric survival term structure for a given annual hazard rate."""
    return [
        {"year": y, "survival_prob": (1 - annual_rate) ** y}
        for y in range(1, years + 1)
    ]


def make_gauge(
    gauge_id: str = "G-EXTRA-001",
    gauge_name: str = "Extra Test Gauge",
    alert: float = 0.12,
    warning: float = 0.06,
    severe: float = 0.02,
) -> dict:
    return {
        "gauge_id": gauge_id,
        "gauge_name": gauge_name,
        "flood_alert_m": 3.8,
        "flood_warning_m": 4.3,
        "severe_flood_warning_m": 5.1,
        "annual_hazard_rate_alert": alert,
        "annual_hazard_rate_warning": warning,
        "annual_hazard_rate_severe": severe,
        "term_structure_alert": term_structure(alert),
        "term_structure_warning": term_structure(warning),
        "term_structure_severe": term_structure(severe),
    }


if HAS_QUANTLIB:
    @pytest.fixture(scope="module")
    def today():
        t = ql.Date.todaysDate()
        ql.Settings.instance().evaluationDate = t
        return t

    @pytest.fixture(scope="module")
    def gauge():
        return make_gauge()
