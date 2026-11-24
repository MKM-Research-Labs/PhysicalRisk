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

"""Tests for tools.gauge_calibration.build — how the gauge calibration is derived.

EA records are replaced by synthetic daily series with a known answer, so what is
tested is the method: water-year maxima, a datum change split out, a bad reading
excluded, the Gumbel / Gringorten levels, and the sensitivity as the geometric
mean of observed/simulated rise.
"""

import math
import statistics
from datetime import date, timedelta

import pytest
from tools.gauge_calibration import build as b


def _record(level_for_day, years=range(2000, 2010), scale=None):
    """A daily-max record, one reading per day of each water year (Oct–Sep)."""
    readings = []
    for wy in years:
        d = date(wy - 1, 10, 1)
        while d < date(wy, 10, 1):
            readings.append([d.isoformat(), level_for_day(wy, d), "Good"])
            d += timedelta(days=1)
    return {"station": "Test Lock", "km": 0.5, "measure": "m", "scale": scale or {},
            "readings": readings}


def _peaky(base, peak_of):
    """Flat at *base* except a single annual peak on 1 February."""
    return lambda wy, d: base + (peak_of(wy) if (d.month, d.day) == (2, 1) else 0.0)


class TestAnnualMaxima:

    def test_rise_is_measured_from_the_median_daily_level(self):
        am, excluded, changes = b.annual_maxima(_record(_peaky(0.2, lambda wy: 0.5)))
        assert set(am) == set(range(2000, 2010))
        assert all(v["rise_m"] == pytest.approx(0.5) for v in am.values())
        assert am[2003]["date"] == "2003-02-01"
        assert excluded == [] and changes == []

    def test_a_datum_change_is_split_not_read_as_a_flood(self):
        # Walton's record drops ~5 m in 2011: rises must stay ~0.5 either side.
        rec = _record(lambda wy, d: (8.0 if wy < 2005 else 3.0)
                      + (0.5 if (d.month, d.day) == (2, 1) else 0.0))
        am, _, changes = b.annual_maxima(rec)
        assert changes == [2005]
        assert all(v["rise_m"] == pytest.approx(0.5) for v in am.values())

    def test_a_reading_above_the_station_record_is_excluded(self):
        rec = _record(_peaky(0.2, lambda wy: 3.0 if wy == 2004 else 0.6),
                      scale={"typical_low": 0.2, "max_on_record": 1.0})
        am, excluded, _ = b.annual_maxima(rec)
        assert [x["water_year"] for x in excluded] == [2004]
        assert am[2004]["rise_m"] == pytest.approx(0.0)   # the bad day removed

    def test_the_cap_is_ignored_when_the_datums_differ(self):
        rec = _record(_peaky(8.0, lambda wy: 3.0 if wy == 2004 else 0.6),
                      scale={"typical_low": 0.2, "max_on_record": 1.0})
        _, excluded, _ = b.annual_maxima(rec)
        assert excluded == []

    def test_short_water_years_are_skipped(self):
        rec = _record(_peaky(0.2, lambda wy: 0.5))
        rec["readings"] = [r for r in rec["readings"] if not r[0].startswith("2005-0")]
        am, _, _ = b.annual_maxima(rec)
        assert 2005 not in am


class TestLevels:

    def test_gumbel_reproduces_its_own_quantiles(self):
        xi, alpha = 0.4, 0.2
        n = 400
        xs = [xi - alpha * math.log(-math.log((i + 0.5) / n)) for i in range(n)]
        for T in (2, 10, 50):
            exact = xi - alpha * math.log(-math.log(1 - 1 / T))
            assert b.gumbel_level(xs, T) == pytest.approx(exact, abs=0.02)

    def test_empirical_level_is_none_beyond_the_record(self):
        xs = [0.1 * i for i in range(1, 11)]
        assert b.empirical_level(xs, 2) == pytest.approx(statistics.median(xs), abs=0.06)
        assert b.empirical_level(xs, 50) is None


class TestCalibrateGauge:

    def test_rating_curve_recovers_the_scale_and_exponent_it_was_built_with(self):
        rec = _record(_peaky(0.2, lambda wy: 0.3 + 0.05 * (wy - 2000)), years=range(1990, 2025))
        am, _, _ = b.annual_maxima(rec)
        rises = [x["rise_m"] for x in am.values()]
        s, k = 0.5, 0.6
        # A reference run whose rises map onto the observed ones through s * r ** k.
        sim = {T: (b.gumbel_level(rises, T) / s) ** (1 / k) for T in (*b.FIT_PERIODS, 50)}
        e = b.calibrate_gauge(rec, sim)
        assert e["sensitivity"] == pytest.approx(s, rel=1e-3)
        assert e["rise_exponent"] == pytest.approx(k, rel=1e-3)
        f = e["fit"]
        for T in ("2", "10", "20", "50"):     # 10 and 50 are out of sample
            assert f["fitted_rise_m"][T] == pytest.approx(f["observed_rise_m"][T], abs=2e-3)
        r = e["rise_m"]
        assert r["alert"] < r["warning"] < r["severe"]
        assert e["record_years"] == 35
        assert e["seasonal_offset_m"] == 0.0

    def test_a_first_pass_offset_is_measured_and_taken_out(self):
        rec = _record(_peaky(0.2, lambda wy: 0.3 + 0.05 * (wy - 2000)), years=range(1990, 2025))
        rises = [x["rise_m"] for x in b.annual_maxima(rec)[0].values()]
        sim = {T: (b.gumbel_level(rises, T) / 0.5) ** (1 / 0.6) for T in (*b.FIT_PERIODS, 50)}
        # The first-pass run landed 0.1 m high everywhere: winter storms start high.
        first = {T: b.gumbel_level(rises, T) + 0.1 for T in sim}
        e = b.calibrate_gauge(rec, sim, first)
        assert e["seasonal_offset_m"] == pytest.approx(0.1, abs=1e-3)
        f = e["fit"]
        for T, tol in (("2", 1e-3), ("20", 1e-3), ("10", 0.05), ("50", 0.05)):  # 10, 50 out of sample
            assert f["fitted_rise_m"][T] == pytest.approx(f["observed_rise_m"][T], abs=tol)
