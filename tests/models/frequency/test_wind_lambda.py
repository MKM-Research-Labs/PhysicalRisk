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

"""Tests for the per-peril wind arrival rate (MKM-EF-001, Stage 6f).

The registry is the §4.14 extension point. Two properties matter:

- **The fallback is the model, not a placeholder.** With the wind registry
  empty — every catchment today — wind shares the storm event rate, because
  under the 1:1 storm-typhoon coupling wind is not an independent arrival
  process. So ``catchment_wind_lambda`` must equal ``catchment_lambda``.
- **An override is honoured, case-insensitively**, so a catchment with a
  genuinely distinct wind rate can carry one without a code change.
"""

import config.frequency._loader as loader
from config.frequency import (
    catchment_annual_growth,
    catchment_lambda,
    catchment_wind_lambda,
)


def test_wind_falls_back_to_the_storm_rate_when_unseeded():
    assert catchment_wind_lambda("thames") == catchment_lambda("thames")
    assert catchment_wind_lambda(None) == catchment_lambda(None)
    assert catchment_wind_lambda("unseeded") == catchment_lambda("unseeded")


def test_the_registry_is_empty_by_default():
    """No catchment carries a distinct wind rate yet — the seam exists, the
    rates do not, because calibrating one needs real typhoon data and sign-off."""
    from config.frequency import CATCHMENT_WIND_LAMBDA_PER_YEAR
    assert CATCHMENT_WIND_LAMBDA_PER_YEAR == {}


def test_an_override_is_honoured_case_insensitively(monkeypatch):
    monkeypatch.setattr(loader, "CATCHMENT_WIND_LAMBDA_PER_YEAR", {"halong": 2.0})
    assert catchment_wind_lambda("halong") == 2.0
    assert catchment_wind_lambda("HALONG") == 2.0
    # A catchment absent from the override still falls back to the storm rate.
    assert catchment_wind_lambda("thames") == catchment_lambda("thames")


# ------------------------------------------------- annual growth (Stage 6h)

def test_annual_growth_is_stationary_by_default():
    """The empty registry means zero growth everywhere — the term structure is
    unchanged until a catchment is deliberately given a trend."""
    assert catchment_annual_growth("thames") == 0.0
    assert catchment_annual_growth(None) == 0.0
    assert catchment_annual_growth("unseeded") == 0.0


def test_the_growth_registry_is_empty_by_default():
    from config.frequency import CATCHMENT_ANNUAL_GROWTH
    assert CATCHMENT_ANNUAL_GROWTH == {}


def test_a_growth_override_is_honoured_case_insensitively(monkeypatch):
    monkeypatch.setattr(loader, "CATCHMENT_ANNUAL_GROWTH", {"halong": 0.02})
    assert catchment_annual_growth("halong") == 0.02
    assert catchment_annual_growth("HALONG") == 0.02
    assert catchment_annual_growth("thames") == 0.0
