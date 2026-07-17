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

"""
Tests for PropertyHazardCurveGenerator:
  - generate() aggregate statistics
  - log() method
  - Term structure monotonicity and survival checks
"""

import json

import pytest
from db_helpers import tmp_catchment

from port.src.property.propertyhc import (
    MIN_PRS_SPREAD_BPS,
    PropertyHazardCurveGenerator,
)

from .conftest import write_property_ts


@pytest.fixture(autouse=True)
def _seam_backend(tmp_path):
    """Bind a scratch backend rooted at tmp_path so the generator's hazard-curve
    writes (now on the database seam) resolve there."""
    with tmp_catchment(tmp_path, "thames"):
        yield


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

    def test_num_storms_in_stats(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-ms", n_floods=0)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        stats = gen.generate()
        assert "num_storms" in stats
        assert stats["num_storms"] > 0


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

class TestTermStructure:

    def test_prs_spread_non_negative(self, basic_output_dir):
        """PRS spread should be non-negative for all tenors."""
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-mono", n_floods=8)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()
        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)
        ts = data["property_hazard_curves"]["PROP-mono"]["term_structure"]
        spreads = ts["severe"]["prs_spread_bps"]
        assert all(s >= 0 for s in spreads)

    def test_term_structure_is_flat(self, basic_output_dir):
        """All tenors should have the same spread (events are independent)."""
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-flat", n_floods=8)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()
        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)
        ts = data["property_hazard_curves"]["PROP-flat"]["term_structure"]
        spreads = ts["severe"]["prs_spread_bps"]
        assert len(set(spreads)) == 1, f"Term structure not flat: {spreads}"

    def test_only_severe_threshold(self, basic_output_dir):
        """Only severe threshold should exist in term_structure."""
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-sev", n_floods=5)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()
        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)
        ts = data["property_hazard_curves"]["PROP-sev"]["term_structure"]
        assert "severe" in ts
        assert "any_flood" not in ts
        assert "moderate" not in ts
