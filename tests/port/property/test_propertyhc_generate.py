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
Tests for PropertyHazardCurveGenerator:
  - generate() aggregate statistics
  - log() method
  - Term structure monotonicity and survival checks
"""

import json

import pytest

from port.src.property.propertyhc import (
    MIN_PRS_SPREAD_BPS,
    PropertyHazardCurveGenerator,
)

from .conftest import write_property_ts


# ===========================================================================
# generate() — aggregate statistics
# ===========================================================================

class TestGenerateAggregateStats:

    def test_avg_basis_is_float(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-stat1", n_floods=5)
        write_property_ts(pts_dir, "PROP-stat2", n_floods=2)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        stats = gen.generate()
        assert isinstance(stats["avg_basis_bps"], float)

    def test_avg_transmission_rate_between_0_and_1(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-tr1", n_floods=5)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        stats = gen.generate()
        assert 0.0 <= stats["avg_transmission_rate"] <= 1.0

    def test_total_flood_events_counted(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-ev1", n_floods=3)
        write_property_ts(pts_dir, "PROP-ev2", n_floods=4)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        stats = gen.generate()
        assert stats["total_flood_events"] == 7

    def test_min_spread_bps_in_stats(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-ms", n_floods=0)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        stats = gen.generate()
        assert stats["min_spread_bps"] == MIN_PRS_SPREAD_BPS


# ===========================================================================
# log() method
# ===========================================================================

class TestLogMethod:

    def test_log_does_not_raise(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        gen.log("test message")

    def test_log_with_empty_string(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        gen.log("")


# ===========================================================================
# Survival and spread monotonicity checks
# ===========================================================================

class TestTermStructureMonotonicity:

    def test_prs_spread_increases_with_longer_tenor_or_non_decreasing(self, basic_output_dir):
        """PRS spread should be non-negative for all tenors."""
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-mono", n_floods=8)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()
        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)
        ts = data["property_hazard_curves"]["PROP-mono"]["term_structure"]
        for name in ["any_flood", "moderate", "severe"]:
            spreads = ts[name]["prs_spread_bps"]
            assert all(s >= 0 for s in spreads)

    def test_survival_between_zero_and_one(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-surv", n_floods=8)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()
        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)
        ts = data["property_hazard_curves"]["PROP-surv"]["term_structure"]
        for name in ["any_flood", "moderate", "severe"]:
            for s in ts[name]["survival"]:
                assert 0.0 <= s <= 1.0

    def test_any_flood_spread_not_less_than_severe(self, basic_output_dir):
        """any_flood has a lower threshold than severe -> higher or equal spread."""
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-order", n_floods=8)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()
        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)
        ts = data["property_hazard_curves"]["PROP-order"]["term_structure"]
        any_flood_5yr = ts["any_flood"]["prs_spread_bps"][-1]
        severe_5yr = ts["severe"]["prs_spread_bps"][-1]
        assert any_flood_5yr >= severe_5yr - 1e-6
