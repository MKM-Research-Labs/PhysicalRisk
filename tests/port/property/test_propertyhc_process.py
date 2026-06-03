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
Tests for PropertyHazardCurveGenerator._process_property:
  - Flooded/non-flooded event filtering
  - Event count pricing
  - Depth thresholds (severe only)
  - IDW gauge spreads
  - Summary statistics
"""

import json

import pytest

from port.src.property.propertyhc import (
    TENORS,
    PropertyHazardCurveGenerator,
)

from .conftest import write_property_ts


def _write_wind_setup(output_dir, seq_to_event, damages_by_event):
    """Lay down storm_sequences.json (event_id per sequence) and
    typhoon/damage/<event_id>.json for the wind-union path.

    seq_to_event:      {sequence_id: event_id}
    damages_by_event:  {event_id: [ {property_id, peak_sustained_ms,
                                     threshold_ms}, ... ]}
    """
    (output_dir / "storm_sequences.json").write_text(json.dumps({
        "sequences": [
            {"sequence_id": sid, "event_id": eid}
            for sid, eid in seq_to_event.items()
        ],
    }))
    dmg = output_dir / "typhoon" / "damage"
    dmg.mkdir(parents=True, exist_ok=True)
    for eid, rows in damages_by_event.items():
        (dmg / f"{eid}.json").write_text(json.dumps({
            "event_id": eid,
            "scenario_family": "extreme",
            "damages": rows,
        }))


# ===========================================================================
# _process_property — events with flooded=False excluded
# ===========================================================================

class TestProcessPropertyFloodedFilter:

    def test_non_flooded_events_excluded_from_depth_count(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-filter", n_floods=4, include_non_flooded=True)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-filter.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        assert result["flood_count"] == 4

    def test_zero_flooded_events_uses_event_count_pricing(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-nofloods", n_floods=0)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-nofloods.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        assert result["has_gev"] is False
        assert result["pricing_method"] == "event_count"
        assert result["flood_count"] == 0


# ===========================================================================
# _process_property — event count pricing
# ===========================================================================

class TestProcessPropertyEventCount:

    def test_spread_equals_flood_count_over_storms(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-exact", n_floods=5)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-exact.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        assert result["flood_count"] == 5
        expected_spread = round((5 / 100) * 10000, 2)
        assert result["term_structure"]["severe"]["prs_spread_bps"][0] == expected_spread

    def test_few_events_still_uses_event_count(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-below", n_floods=2)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-below.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        assert result["has_gev"] is False
        assert result["pricing_method"] == "event_count"

    def test_many_events_uses_event_count(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-many", n_floods=10)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-many.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        assert result["flood_count"] == 10
        assert result["pricing_method"] == "event_count"
        assert result["has_gev"] is False


# ===========================================================================
# _process_property — depth thresholds (severe only)
# ===========================================================================

class TestDepthThresholds:

    def test_only_severe_key_in_depth_thresholds(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-floor", n_floods=3)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-floor.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        assert list(result["depth_thresholds"].keys()) == ["severe"]

    def test_annual_probability_equals_count_over_storms(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-prob", n_floods=5)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-prob.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        prob = result["depth_thresholds"]["severe"]["annual_probability"]
        assert abs(prob - 5 / 100) < 1e-6

    def test_return_period_none_when_zero_floods(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-rp", n_floods=0)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-rp.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        rp = result["depth_thresholds"]["severe"]["return_period_yrs"]
        assert rp is None

    def test_return_period_positive_when_floods_present(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-rp2", n_floods=4)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-rp2.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        rp = result["depth_thresholds"]["severe"]["return_period_yrs"]
        assert rp is not None
        assert rp > 0


# ===========================================================================
# _process_property — IDW gauge spreads
# ===========================================================================

class TestIdwGaugeSpreads:

    def test_idw_gauge_spreads_computed_with_two_gauges(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-idw", n_floods=5,
                          nearest_gauges=[
                              {"gauge_id": "GAUGE-001", "distance_m": 1000,
                               "gauge_elevation_m": 3.5},
                              {"gauge_id": "GAUGE-002", "distance_m": 2000,
                               "gauge_elevation_m": 4.0},
                          ])
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-idw.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        idw = result.get("idw_gauge_spreads", {})
        assert "severe" in idw
        assert len(idw["severe"]) == len(TENORS)

    def test_no_nearest_gauges_idw_returns_dict(self, basic_output_dir):
        """With empty nearest_gauges, idw_gauge_spreads is still a dict."""
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-noidw", n_floods=3,
                          nearest_gauges=[])
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-noidw.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        assert isinstance(result.get("idw_gauge_spreads"), dict)


# ===========================================================================
# _process_property — summary statistics
# ===========================================================================

class TestProcessPropertySummary:

    def test_max_depth_positive_for_flooded_property(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-depth", n_floods=5)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-depth.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        assert result["summary"]["max_depth_m"] > 0
        assert result["summary"]["mean_depth_m"] > 0

    def test_zero_depths_for_non_flooded(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-zero", n_floods=0)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-zero.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
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
        (pts_dir / "PROP-txzero.json").write_text(json.dumps(prop_data))
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-txzero.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        if result["nearest_gauges"]:
            assert result["nearest_gauges"][0]["flood_transmission_rate"] == 0.0


# ===========================================================================
# _process_property — Stage 5 wind∪flood PRS union
# ===========================================================================

class TestWindUnion:

    def test_no_typhoon_data_is_flood_only_fallback(self, basic_output_dir):
        """Without typhoon/damage, the result carries no wind/union keys and the
        headline severe spread is the flood-only spread (byte-identical)."""
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-nowind", n_floods=3)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(
            pts_dir / "PROP-nowind.json", gauge_hazard, None, num_storms=100)
        assert "union_count" not in result
        assert "wind_count" not in result
        assert "union" not in result["term_structure"]
        assert result["term_structure"]["severe"]["prs_spread_bps"][0] == round(
            (3 / 100) * 10000, 2)

    def test_union_dedups_overlap_and_adds_wind_only(self, basic_output_dir):
        """Property floods in S0,S1 (EVT-0,EVT-1). Wind fires on EVT-0 (overlap)
        and EVT-2 (a wind-only sequence not in flood_events); EVT-1 wind is
        below threshold. Union = {EVT-0,EVT-1,EVT-2} = 3, no double-count."""
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-u", n_floods=2)  # storms S0, S1
        _write_wind_setup(
            output_dir,
            seq_to_event={"S0": "EVT-0", "S1": "EVT-1", "S-WIND": "EVT-2"},
            damages_by_event={
                "EVT-0": [{"property_id": "PROP-u",
                           "peak_sustained_ms": 70.0, "threshold_ms": 30.0}],
                "EVT-1": [{"property_id": "PROP-u",
                           "peak_sustained_ms": 20.0, "threshold_ms": 30.0}],
                "EVT-2": [{"property_id": "PROP-u",
                           "peak_sustained_ms": 50.0, "threshold_ms": 30.0}],
            },
        )
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(
            pts_dir / "PROP-u.json", gauge_hazard, None, num_storms=100)
        assert result["flood_count"] == 2
        assert result["wind_count"] == 2          # EVT-0, EVT-2
        assert result["union_count"] == 3         # EVT-0, EVT-1, EVT-2
        # Flood-only severe spread unchanged; union exposed separately.
        assert result["term_structure"]["severe"]["prs_spread_bps"][0] == round(
            (2 / 100) * 10000, 2)
        assert result["term_structure"]["union"]["prs_spread_bps"][0] == round(
            (3 / 100) * 10000, 2)
        assert result["prs_union_spread_bps"] == round((3 / 100) * 10000, 2)

    def test_wind_below_threshold_never_triggers(self, basic_output_dir):
        """Typhoon present but every paired wind is below threshold → union ==
        flood, wind_count == 0 (but keys present since typhoon data exists)."""
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-calm", n_floods=2)
        _write_wind_setup(
            output_dir,
            seq_to_event={"S0": "EVT-0", "S1": "EVT-1"},
            damages_by_event={
                "EVT-0": [{"property_id": "PROP-calm",
                           "peak_sustained_ms": 10.0, "threshold_ms": 30.0}],
                "EVT-1": [{"property_id": "PROP-calm",
                           "peak_sustained_ms": 12.0, "threshold_ms": 30.0}],
            },
        )
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(
            pts_dir / "PROP-calm.json", gauge_hazard, None, num_storms=100)
        assert result["wind_count"] == 0
        assert result["union_count"] == 2
        assert result["prs_union_spread_bps"] == round((2 / 100) * 10000, 2)

    def test_wind_only_property_no_floods(self, basic_output_dir):
        """Property never floods but is wind-damaged in a paired typhoon →
        union counts the wind event even with flood_count == 0."""
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-windonly", n_floods=0)
        _write_wind_setup(
            output_dir,
            seq_to_event={"S-W": "EVT-9"},
            damages_by_event={
                "EVT-9": [{"property_id": "PROP-windonly",
                           "peak_sustained_ms": 55.0, "threshold_ms": 30.0}],
            },
        )
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(
            pts_dir / "PROP-windonly.json", gauge_hazard, None, num_storms=100)
        assert result["flood_count"] == 0
        assert result["wind_count"] == 1
        assert result["union_count"] == 1

    def test_other_property_wind_not_attributed(self, basic_output_dir):
        """A damage roll naming a different property must not trigger wind for
        this one."""
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-self", n_floods=1)
        _write_wind_setup(
            output_dir,
            seq_to_event={"S0": "EVT-0"},
            damages_by_event={
                "EVT-0": [{"property_id": "PROP-OTHER",
                           "peak_sustained_ms": 80.0, "threshold_ms": 30.0}],
            },
        )
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(
            pts_dir / "PROP-self.json", gauge_hazard, None, num_storms=100)
        assert result["wind_count"] == 0
        assert result["union_count"] == 1   # the flood on S0 still counts
