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
Tests for PropertyHazardCurveGenerator._process_property (part 2):
  - Stage 5 wind∪flood PRS union
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
# _process_property — Stage 5 wind∪flood PRS union
# ===========================================================================

class TestWindUnion:

    @staticmethod
    def _assert_inclusion_exclusion(perils):
        """union = flood + wind − joint, and joint ≤ min(flood, wind)."""
        f = perils["flood_only"]["count"]
        w = perils["wind_only"]["count"]
        u = perils["flood_or_wind"]["count"]
        j = perils["flood_and_wind"]["count"]
        assert u == f + w - j
        assert j <= min(f, w)

    def test_no_typhoon_data_is_flood_only_fallback(self, basic_output_dir):
        """Without typhoon/damage, the result carries no peril block and the
        headline severe spread is the flood-only spread (byte-identical)."""
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-nowind", n_floods=3)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(
            pts_dir / "PROP-nowind.json", gauge_hazard, None, num_storms=100)
        assert "prs_perils" not in result
        assert "perils" not in result["term_structure"]
        assert result["term_structure"]["severe"]["prs_spread_bps"][0] == round(
            (3 / 100) * 10000, 2)

    def test_four_peril_outcomes_overlap_and_wind_only(self, basic_output_dir):
        """Property floods in S0,S1 (EVT-0,EVT-1). Wind fires on EVT-0 (overlap)
        and EVT-2 (a wind-only sequence not in flood_events); EVT-1 wind is
        below threshold. flood=2, wind=2, union={EVT-0,EVT-1,EVT-2}=3, joint
        (EVT-0)=1."""
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
        perils = result["prs_perils"]
        assert perils["flood_only"]["count"] == 2
        assert perils["wind_only"]["count"] == 2          # EVT-0, EVT-2
        assert perils["flood_or_wind"]["count"] == 3      # EVT-0, EVT-1, EVT-2
        assert perils["flood_and_wind"]["count"] == 1     # EVT-0
        assert perils["flood_and_wind"]["spread_bps"] == round((1 / 100) * 10000, 2)
        self._assert_inclusion_exclusion(perils)
        # Flood spine unchanged; peril spreads ride alongside in term_structure.
        assert result["term_structure"]["severe"]["prs_spread_bps"][0] == round(
            (2 / 100) * 10000, 2)
        assert result["term_structure"]["perils"]["flood_or_wind"][
            "prs_spread_bps"][0] == round((3 / 100) * 10000, 2)

    def test_wind_below_threshold_never_triggers(self, basic_output_dir):
        """Typhoon present but every paired wind is below threshold → union ==
        flood, wind == 0, joint == 0 (block present since typhoon data exists)."""
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
        perils = result["prs_perils"]
        assert perils["wind_only"]["count"] == 0
        assert perils["flood_or_wind"]["count"] == 2
        assert perils["flood_and_wind"]["count"] == 0
        assert perils["flood_or_wind"]["spread_bps"] == round((2 / 100) * 10000, 2)
        self._assert_inclusion_exclusion(perils)

    def test_wind_only_property_no_floods(self, basic_output_dir):
        """Property never floods but is wind-damaged in a paired typhoon →
        union counts the wind event even with flood_count == 0; joint == 0."""
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
        perils = result["prs_perils"]
        assert perils["flood_only"]["count"] == 0
        assert perils["wind_only"]["count"] == 1
        assert perils["flood_or_wind"]["count"] == 1
        assert perils["flood_and_wind"]["count"] == 0
        self._assert_inclusion_exclusion(perils)

    def test_full_overlap_joint_equals_both(self, basic_output_dir):
        """Both floods are on storms whose paired typhoon also fires wind →
        flood=2, wind=2, joint=2, union=2 (every event triggers both)."""
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-both", n_floods=2)  # storms S0, S1
        _write_wind_setup(
            output_dir,
            seq_to_event={"S0": "EVT-0", "S1": "EVT-1"},
            damages_by_event={
                "EVT-0": [{"property_id": "PROP-both",
                           "peak_sustained_ms": 70.0, "threshold_ms": 30.0}],
                "EVT-1": [{"property_id": "PROP-both",
                           "peak_sustained_ms": 65.0, "threshold_ms": 30.0}],
            },
        )
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(
            pts_dir / "PROP-both.json", gauge_hazard, None, num_storms=100)
        perils = result["prs_perils"]
        assert perils["flood_only"]["count"] == 2
        assert perils["wind_only"]["count"] == 2
        assert perils["flood_and_wind"]["count"] == 2
        assert perils["flood_or_wind"]["count"] == 2
        self._assert_inclusion_exclusion(perils)

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
        perils = result["prs_perils"]
        assert perils["wind_only"]["count"] == 0
        assert perils["flood_or_wind"]["count"] == 1   # the flood on S0 still counts
        assert perils["flood_and_wind"]["count"] == 0
        self._assert_inclusion_exclusion(perils)
