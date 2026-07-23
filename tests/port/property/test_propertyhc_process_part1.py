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
Tests for PropertyHazardCurveGenerator._process_property (part 1):
  - Flooded/non-flooded event filtering
  - Event count pricing
  - Depth thresholds (severe only)
  - IDW gauge spreads
  - Summary statistics
"""

import pytest

from port.src.property.propertyhc import (
    TENORS,
    PropertyHazardCurveGenerator,
)

from .conftest import write_property_ts

# ===========================================================================
# _process_property — events with flooded=False excluded
# ===========================================================================

class TestProcessPropertyFloodedFilter:

    def test_non_flooded_events_excluded_from_depth_count(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-filter", n_floods=4, include_non_flooded=True)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        assert result["flood_count"] == 4

    def test_zero_flooded_events_uses_event_count_pricing(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-nofloods", n_floods=0)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        assert result["has_gev"] is False
        assert result["pricing_method"] == "event_frequency"
        assert result["flood_count"] == 0


# ===========================================================================
# _process_property — event count pricing
# ===========================================================================

class TestProcessPropertyEventCount:

    def test_spread_equals_flood_count_over_storms(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-exact", n_floods=5)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        assert result["flood_count"] == 5
        expected_spread = round((5 / 100) * 10000, 2)
        assert result["term_structure"]["severe"]["prs_spread_bps"][0] == expected_spread

    def test_few_events_still_uses_event_count(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-below", n_floods=2)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        assert result["has_gev"] is False
        assert result["pricing_method"] == "event_frequency"

    def test_many_events_uses_event_count(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-many", n_floods=10)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        assert result["flood_count"] == 10
        assert result["pricing_method"] == "event_frequency"
        assert result["has_gev"] is False


# ===========================================================================
# _process_property — depth thresholds (severe only)
# ===========================================================================

class TestDepthThresholds:

    def test_only_severe_key_in_depth_thresholds(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-floor", n_floods=3)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        assert list(result["depth_thresholds"].keys()) == ["severe"]

    def test_annual_probability_equals_count_over_storms(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-prob", n_floods=5)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        prob = result["depth_thresholds"]["severe"]["annual_probability"]
        assert abs(prob - 5 / 100) < 1e-6

    def test_return_period_none_when_zero_floods(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-rp", n_floods=0)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        rp = result["depth_thresholds"]["severe"]["return_period_yrs"]
        assert rp is None

    def test_return_period_positive_when_floods_present(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-rp2", n_floods=4)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        rp = result["depth_thresholds"]["severe"]["return_period_yrs"]
        assert rp is not None
        assert rp > 0


# ===========================================================================
# _process_property — IDW gauge spreads
# ===========================================================================

class TestIdwGaugeSpreads:

    def test_idw_gauge_spreads_computed_with_two_gauges(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-idw", n_floods=5,
                          nearest_gauges=[
                              {"gauge_id": "GAUGE-001", "distance_m": 1000,
                               "gauge_elevation_m": 3.5},
                              {"gauge_id": "GAUGE-002", "distance_m": 2000,
                               "gauge_elevation_m": 4.0},
                          ])
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        idw = result.get("idw_gauge_spreads", {})
        assert "severe" in idw
        assert len(idw["severe"]) == len(TENORS)

    def test_no_nearest_gauges_idw_returns_dict(self, basic_output_dir):
        """With empty nearest_gauges, idw_gauge_spreads is still a dict."""
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-noidw", n_floods=3,
                          nearest_gauges=[])
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        assert isinstance(result.get("idw_gauge_spreads"), dict)


# ===========================================================================
# _process_property — summary statistics
# ===========================================================================

class TestProcessPropertySummary:

    def test_max_depth_positive_for_flooded_property(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-depth", n_floods=5)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        assert result["summary"]["max_depth_m"] > 0
        assert result["summary"]["mean_depth_m"] > 0

    def test_zero_depths_for_non_flooded(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-zero", n_floods=0)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        assert result["summary"]["max_depth_m"] == 0.0
        assert result["summary"]["mean_depth_m"] == 0.0

    def test_transmission_rate_when_no_gauge_floods(self, basic_output_dir):
        """With zero flood events, gauge_flood_count=0 so transmission_rate=0."""
        output_dir, pts_dir = basic_output_dir
        prop_data = {
            "property_id": "PROP-txzero",
            "location": {"lat": 51.45, "lon": -0.30},
            "elevation_m": 5.0,
            "floor_level_m": 0.3,
            "flood_zone": "Zone 1",
            "property_type": "Detached",
            "construction_year": 2000,
            "nearest_gauges": [
                {"gauge_id": "GAUGE-001", "distance_m": 1000, "gauge_elevation_m": 3.5},
            ],
            "flood_events": [],
            "summary": {
                "property_id": "PROP-txzero",
                "floods_at_nearest_gauge": 0,
                "floods_at_property": 0,
            },
        }
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_data, gauge_hazard, None, num_storms=100)
        if result["nearest_gauges"]:
            assert result["nearest_gauges"][0]["flood_transmission_rate"] == 0.0


# ===========================================================================
# _process_property — the frequency-layer path (MKM-EF-001)
# ===========================================================================

class TestFrequencyPricing:
    """With an event frame the spread is annualised; without one the
    pre-frequency numbers are reproduced exactly."""

    @staticmethod
    def _frame(n_events=10, category="severe"):
        from models.frequency import build_event_frame
        from models.hazard.io import load_storms_from_sequences
        return build_event_frame(load_storms_from_sequences({"sequences": [
            {
                "sequence_id": f"S{i}",
                "storms": [{
                    "storm_id": f"ST-{i}", "precipitation_mm": 30.0,
                    "duration_hours": 12, "intensity_factor": 1.0,
                    "intensity_category": category,
                }],
            }
            for i in range(n_events)
        ]}))

    def test_the_spread_is_annualised_through_the_frequency_layer(
            self, basic_output_dir):
        from models.frequency import annual_exceedance_probability

        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-freq", n_floods=3)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        frame = self._frame()

        result = gen._process_property(
            pdata, gauge_hazard, None, num_storms=100,
            frame=frame, lambda_per_year=4.5)

        severe = result["depth_thresholds"]["severe"]
        expected = annual_exceedance_probability(
            4.5, frame.conditional_probability(["S0", "S1", "S2"]))

        assert result["pricing_method"] == "event_frequency"
        assert severe["annual_probability"] == pytest.approx(expected, abs=1e-8)
        assert severe["event_flood_count"] == 3
        assert severe["conditional_per_event"] > 0

    def test_the_return_period_follows_the_annual_rate(self, basic_output_dir):
        from models.frequency import return_period_years

        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-rp", n_floods=2)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        frame = self._frame()

        result = gen._process_property(
            pdata, gauge_hazard, None, num_storms=100,
            frame=frame, lambda_per_year=4.5)

        severe = result["depth_thresholds"]["severe"]
        expected = return_period_years(
            4.5, frame.conditional_probability(["S0", "S1"]))
        assert severe["return_period_yrs"] == pytest.approx(expected, abs=0.01)

    def test_several_storms_in_one_event_price_once(self, basic_output_dir):
        """Two flood records inside the same hours-clause event are one
        breach of the contract, so they must not price as two."""
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-dedup", n_floods=2)
        # Both records point at the same event.
        for event in pdata["flood_events"]:
            event["storm_id"] = "S0"

        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(
            pdata, gauge_hazard, None, num_storms=100,
            frame=self._frame(), lambda_per_year=4.5)

        assert result["flood_count"] == 2
        assert result["depth_thresholds"]["severe"]["event_flood_count"] == 1

    def test_records_from_a_different_storm_set_are_refused(self, basic_output_dir):
        """A confident small number from foreign records is worse than a
        failure — this is the guard for the silent-zero regression."""
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-foreign", n_floods=2)
        for event in pdata["flood_events"]:
            event["storm_id"] = "FROM-ANOTHER-RUN"

        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        with pytest.raises(ValueError, match="different storm sets"):
            gen._process_property(
                pdata, gauge_hazard, None, num_storms=100,
                frame=self._frame(), lambda_per_year=4.5)

    def test_without_a_frame_the_legacy_numbers_are_reproduced(
            self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-legacy", n_floods=5)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()

        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)

        severe = result["depth_thresholds"]["severe"]
        assert severe["annual_probability"] == pytest.approx(5 / 100)
        assert severe["return_period_yrs"] == pytest.approx(20.0)
