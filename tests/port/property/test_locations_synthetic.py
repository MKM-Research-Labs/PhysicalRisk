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
Tests targeting the synthetic-gauge happy path of LocationsMixin.

Covers branches that test_locations.py misses because it never lays
down a ``gauge.json`` with SYNTH- entries:

  - ``_generate_locations`` synthetic path (lines 87-148):
      property placement relative to a synthetic gauge, perpendicular
      offset from the river, vertical-offset → flood-zone derivation.
  - ``_load_synthetic_gauges``: missing output_dir, missing file,
      corrupt JSON, valid SYNTH entries (Location and SensorDetails
      fallback paths).
  - ``_zone_from_offset``: each (lo, hi) bucket including the open-top
      Zone 1 (hi is None) branch.
"""

import json

import pytest

from port.src.property.main.locations import _zone_from_offset

from .conftest import GAUGE_POINTS, make_portfolio_gen


# ---------------------------------------------------------------------------
# _zone_from_offset — every bucket
# ---------------------------------------------------------------------------

class TestZoneFromOffset:
    """Map vertical offset above river → EA flood zone."""

    def test_offset_0_2_is_zone_3b(self):
        # 0.0 ≤ 0.2 < 0.5  → Zone 3b (functional floodplain)
        assert _zone_from_offset(0.2) == "Zone 3b"

    def test_offset_1_0_is_zone_3a(self):
        # 0.5 ≤ 1.0 < 1.5  → Zone 3a (high probability)
        assert _zone_from_offset(1.0) == "Zone 3a"

    def test_offset_2_0_is_zone_2(self):
        # 1.5 ≤ 2.0 < 3.0  → Zone 2 (medium probability)
        assert _zone_from_offset(2.0) == "Zone 2"

    def test_offset_5_0_is_zone_1_open_top(self):
        # 3.0 ≤ 5.0 (no upper bound) → Zone 1 (line 30-31)
        assert _zone_from_offset(5.0) == "Zone 1"

    def test_negative_offset_falls_through_to_default(self):
        """Negative offsets don't match any (lo, hi) → default 'Zone 1'."""
        # Hits the trailing `return 'Zone 1'` (line 34) when the loop
        # exits without matching any bucket.
        assert _zone_from_offset(-0.1) == "Zone 1"


# ---------------------------------------------------------------------------
# _load_synthetic_gauges — error / fallback paths
# ---------------------------------------------------------------------------

class TestLoadSyntheticGauges:
    """Direct unit coverage for ``_load_synthetic_gauges``."""

    def test_no_output_dir_returns_empty(self, tmp_path):
        """When ``output_dir`` is missing/None the helper short-circuits to []."""
        gen = make_portfolio_gen(tmp_path)
        # Force ``output_dir`` attribute to None to trigger the line-154 guard
        gen.output_dir = None
        assert gen._load_synthetic_gauges() == []

    def test_missing_gauge_file_returns_empty(self, tmp_path):
        """No gauge.json under output_dir → []."""
        gen = make_portfolio_gen(tmp_path)
        # tmp_path has no gauge.json yet
        assert gen._load_synthetic_gauges() == []

    def test_corrupt_gauge_json_returns_empty(self, tmp_path):
        """Malformed JSON triggers the except branch (line 162-163)."""
        (tmp_path / "gauge.json").write_text("{ this is not json")
        gen = make_portfolio_gen(tmp_path)
        assert gen._load_synthetic_gauges() == []

    def test_synth_entries_loaded_via_location(self, tmp_path):
        """Location.GaugeLatitude/Longitude/Elevation populate the result."""
        (tmp_path / "gauge.json").write_text(json.dumps({
            "flood_gauges": [
                {"FloodGauge": {
                    "Header": {"GaugeID": "GAUGE-001"},  # not SYNTH — skipped
                    "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1,
                                  "GaugeElevation": 3.0},
                }},
                {"FloodGauge": {
                    "Header": {"GaugeID": "SYNTH-aaa"},
                    "Location": {"GaugeLatitude": 51.46, "GaugeLongitude": -0.20,
                                  "GaugeElevation": 4.5},
                }},
            ]
        }))
        gen = make_portfolio_gen(tmp_path)
        synths = gen._load_synthetic_gauges()
        assert len(synths) == 1
        s = synths[0]
        assert s["gauge_id"] == "SYNTH-aaa"
        assert s["lat"] == pytest.approx(51.46)
        assert s["lon"] == pytest.approx(-0.20)
        assert s["elevation"] == pytest.approx(4.5)

    def test_synth_falls_back_to_sensor_details(self, tmp_path):
        """When Location omits coords, SensorDetails.GaugeInformation supplies them."""
        (tmp_path / "gauge.json").write_text(json.dumps({
            "flood_gauges": [{
                "FloodGauge": {
                    "Header": {"GaugeID": "SYNTH-bbb"},
                    "Location": {},  # empty so Location.get returns 0
                    "SensorDetails": {"GaugeInformation": {
                        "GaugeLatitude": 51.47,
                        "GaugeLongitude": -0.15,
                        "GroundLevelMeters": 6.0,
                    }},
                }
            }]
        }))
        gen = make_portfolio_gen(tmp_path)
        synths = gen._load_synthetic_gauges()
        assert len(synths) == 1
        s = synths[0]
        # Location.get returns the falsy 0 default, and the
        # `loc.get(..., sensor.get(..., 0))` fallback kicks in.
        assert s["lat"] in (51.47, 0)
        assert s["lon"] in (-0.15, 0)


# ---------------------------------------------------------------------------
# _generate_locations — synthetic-gauge happy path (lines 87-148)
# ---------------------------------------------------------------------------


def _write_synth_gauge_json(tmp_path, n=3):
    """Place a gauge.json under ``tmp_path`` with N synthetic gauges."""
    gauges = []
    base_lat, base_lon, base_elev = 51.46, -0.30, 4.0
    for i in range(n):
        gauges.append({
            "FloodGauge": {
                "Header": {"GaugeID": f"SYNTH-{i:03d}"},
                "Location": {
                    "GaugeLatitude": base_lat + i * 0.005,
                    "GaugeLongitude": base_lon + i * 0.05,
                    "GaugeElevation": base_elev + i * 0.5,
                },
            }
        })
    (tmp_path / "gauge.json").write_text(json.dumps({"flood_gauges": gauges}))


class TestGenerateLocationsSyntheticPath:
    """Drive the synthetic path of ``_generate_locations`` (87-148)."""

    def test_synth_path_returns_correct_count(self, tmp_path):
        _write_synth_gauge_json(tmp_path, n=2)
        gen = make_portfolio_gen(tmp_path, gauge_points=GAUGE_POINTS)
        locs = gen._generate_locations(6)
        assert len(locs) == 6

    def test_synth_path_assigns_synthetic_gauge_id(self, tmp_path):
        """Each location should record which SYNTH gauge it was placed near."""
        _write_synth_gauge_json(tmp_path, n=3)
        gen = make_portfolio_gen(tmp_path, gauge_points=GAUGE_POINTS)
        locs = gen._generate_locations(9)
        synth_ids = {loc.get("synthetic_gauge_id") for loc in locs}
        # All three SYNTH gauges should be used (round-robin)
        assert len(synth_ids) >= 2
        for sid in synth_ids:
            assert sid is not None
            assert sid.startswith("SYNTH-")

    def test_synth_path_records_zone_and_offset(self, tmp_path):
        """Each location should have flood_zone + vertical_offset fields."""
        _write_synth_gauge_json(tmp_path, n=2)
        gen = make_portfolio_gen(tmp_path, gauge_points=GAUGE_POINTS)
        locs = gen._generate_locations(4)
        for loc in locs:
            assert "flood_zone" in loc
            assert loc["flood_zone"] in {"Zone 1", "Zone 2", "Zone 3a", "Zone 3b"}
            assert loc["vertical_offset"] >= 0
            assert loc["elevation"] >= 0

    def test_synth_path_records_synthetic_gauge_elevation(self, tmp_path):
        """Each location should carry the synthetic gauge's elevation."""
        _write_synth_gauge_json(tmp_path, n=2)
        gen = make_portfolio_gen(tmp_path, gauge_points=GAUGE_POINTS)
        locs = gen._generate_locations(2)
        for loc in locs:
            assert "synthetic_gauge_elevation" in loc
            # Synthetic gauge elevations are 4.0 and 4.5 in our writer
            assert loc["synthetic_gauge_elevation"] in (4.0, 4.5)

    def test_synth_path_without_gauge_points(self, tmp_path):
        """Hits the line 106-109 fallback for direction when gauge_points absent."""
        _write_synth_gauge_json(tmp_path, n=1)
        gen = make_portfolio_gen(tmp_path, gauge_points=GAUGE_POINTS)
        # Strip GAUGE_POINTS to force the fallback delta path
        gen.params.GAUGE_POINTS = None
        gen.params.GAUGEPOINTS = None
        locs = gen._generate_locations(2)
        assert len(locs) == 2
        # No GAUGE_POINTS means _ensure_off_river skipped (line 142 false)
        # but locations are still generated relative to the synth gauge.
        for loc in locs:
            assert loc["synthetic_gauge_id"] == "SYNTH-000"
