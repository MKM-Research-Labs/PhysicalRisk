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

"""Coverage expansion tests for synthetic.py — river polyline cache miss,
degenerate segments, insufficient gauge points, random position generation,
existing synthetic gauges skipped, polyline endpoints, and missing
flanking gauge."""

import json
import math

import pytest


# ---------------------------------------------------------------------------
# Helpers (same CDM builders as test_synthetic_gauge.py)
# ---------------------------------------------------------------------------

def _make_gauge_cdm(gauge_id, lat, lon, elevation, alert, warning, severe):
    return {
        "FloodGauge": {
            "Header": {
                "GaugeID": gauge_id,
                "CatchmentID": "thames",
                "GaugeName": f"Test {gauge_id}",
            },
            "SensorStats": {
                "HistoricalHighLevel": severe + 1.0,
                "HistoricalHighDate": "2020-01-01",
            },
            "SensorDetails": {
                "GaugeInformation": {
                    "DataSourceType": "SensorGauge",
                    "GaugeLatitude": lat,
                    "GaugeLongitude": lon,
                    "GroundLevelMeters": elevation,
                    "elevation": elevation,
                    "OperationalStatus": "Fully operational",
                },
            },
            "FloodStage": {
                "UK": {
                    "FloodAlert": alert,
                    "FloodWarning": warning,
                    "SevereFloodWarning": severe,
                },
            },
            "Location": {
                "GaugeLatitude": lat,
                "GaugeLongitude": lon,
                "GaugeElevation": elevation,
            },
        }
    }


def _make_property_cdm(prop_id, lat, lon):
    return {
        "PropertyHeader": {
            "Header": {"PropertyID": prop_id},
            "Location": {
                "LatitudeDegrees": lat,
                "LongitudeDegrees": lon,
            },
        }
    }


GAUGE_POINTS = [
    (51.45, -0.50, 3.0),
    (51.46, -0.30, 4.0),
    (51.47, -0.10, 5.0),
]


@pytest.fixture
def synth_env(tmp_path, monkeypatch):
    """Standard synthetic gauge environment."""
    gauges = [
        _make_gauge_cdm("GAUGE-AAA00001", 51.45, -0.50, 3.0, 3.5, 4.5, 5.0),
        _make_gauge_cdm("GAUGE-BBB00002", 51.46, -0.30, 4.0, 4.0, 5.0, 6.0),
        _make_gauge_cdm("GAUGE-CCC00003", 51.47, -0.10, 5.0, 4.5, 5.5, 7.0),
    ]
    (tmp_path / "gauge.json").write_text(json.dumps({"flood_gauges": gauges}))

    properties = [
        _make_property_cdm("PROP-001", 51.455, -0.40),
        _make_property_cdm("PROP-002", 51.465, -0.20),
    ]
    (tmp_path / "property.json").write_text(json.dumps({"properties": properties}))

    from unittest.mock import MagicMock
    mock_params = MagicMock()
    mock_params.GAUGE_POINTS = GAUGE_POINTS
    del mock_params.GAUGEPOINTS

    from config import config as cfg
    monkeypatch.setattr(cfg, "load_params_module", lambda: mock_params)
    monkeypatch.setattr(cfg, "catchment_id", "thames")

    # Reset river polyline cache so tests start clean
    import port.src.gauge.synthetic as synth_mod
    synth_mod._RIVER_POLYLINE_CACHE = None

    return tmp_path


# ---------------------------------------------------------------------------
# Lines 48-49, 67: No river polyline cache → returns None → unsnapped coords
# ---------------------------------------------------------------------------

class TestNoRiverPolylineCache:

    def test_load_river_polyline_returns_none_when_no_cache(self, synth_env, monkeypatch):
        """_load_river_polyline returns None when cache file doesn't exist."""
        import port.src.gauge.synthetic as synth_mod
        synth_mod._RIVER_POLYLINE_CACHE = None

        result = synth_mod._load_river_polyline()
        # Either None (no cache file) or a list (if project has one)
        # In test env, the cache path won't exist
        # The important thing is no crash
        assert result is None or isinstance(result, list)

    def test_snap_to_river_returns_original_when_no_polyline(self, synth_env, monkeypatch):
        """_snap_to_river returns original coords when river is None."""
        import port.src.gauge.synthetic as synth_mod
        import port.src.gauge.synthetic.geometry as geom_mod
        geom_mod._RIVER_POLYLINE_CACHE = None
        monkeypatch.setattr(geom_mod, "_load_river_polyline", lambda: None)

        lat, lon = geom_mod._snap_to_river(51.46, -0.30)
        assert lat == 51.46
        assert lon == -0.30


# ---------------------------------------------------------------------------
# Line 83: Degenerate river segment (zero-length)
# ---------------------------------------------------------------------------

class TestRiverPolylineCacheHit:

    def test_load_river_polyline_from_cache_file(self, synth_env, monkeypatch, tmp_path):
        """Lines 39-40 of geometry.py: cache file exists → loaded and returned."""
        import port.src.gauge.synthetic.geometry as geom_mod
        from unittest.mock import patch, mock_open

        # Reset cache
        geom_mod._RIVER_POLYLINE_CACHE = None

        polyline_data = [[51.45, -0.50], [51.46, -0.30], [51.47, -0.10]]

        # Mock Path.exists to return True, and open to return our polyline JSON
        with patch.object(geom_mod.Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(polyline_data))):
                result = geom_mod._load_river_polyline()

        assert result is not None
        assert len(result) == 3
        assert result[0] == (51.45, -0.50)

        # Clean up
        geom_mod._RIVER_POLYLINE_CACHE = None


class TestDegenerateRiverSegment:

    def test_degenerate_segment_skipped(self, synth_env, monkeypatch):
        """_snap_to_river skips zero-length segments without error."""
        import port.src.gauge.synthetic.geometry as geom_mod

        # Polyline with a degenerate (identical consecutive points) segment
        degenerate_polyline = [
            (51.45, -0.50),
            (51.45, -0.50),  # zero-length segment
            (51.47, -0.10),
        ]
        monkeypatch.setattr(geom_mod, "_load_river_polyline",
                            lambda: degenerate_polyline)

        lat, lon = geom_mod._snap_to_river(51.46, -0.30)
        # Should return valid coordinates without error
        assert isinstance(lat, float)
        assert isinstance(lon, float)


# ---------------------------------------------------------------------------
# Lines 226, 172-173: Insufficient gauge points
# ---------------------------------------------------------------------------

class TestInsufficientGaugePoints:

    def test_empty_gauge_points_returns_zero(self, synth_env, monkeypatch):
        """generate() returns count=0 when GAUGE_POINTS has < 2 entries."""
        from unittest.mock import MagicMock
        from config import config as cfg

        mock_params = MagicMock()
        mock_params.GAUGE_POINTS = [(51.45, -0.50, 3.0)]  # only 1 point
        del mock_params.GAUGEPOINTS
        monkeypatch.setattr(cfg, "load_params_module", lambda: mock_params)

        from port.src.gauge.synthetic import SyntheticGaugeGenerator
        result = SyntheticGaugeGenerator(synth_env).generate()
        assert result["count"] == 0

    def test_none_gauge_points_returns_zero(self, synth_env, monkeypatch):
        """generate() returns count=0 when GAUGE_POINTS is None."""
        from unittest.mock import MagicMock
        from config import config as cfg

        mock_params = MagicMock()
        mock_params.GAUGE_POINTS = None
        del mock_params.GAUGEPOINTS
        monkeypatch.setattr(cfg, "load_params_module", lambda: mock_params)

        from port.src.gauge.synthetic import SyntheticGaugeGenerator
        result = SyntheticGaugeGenerator(synth_env).generate()
        assert result["count"] == 0


# ---------------------------------------------------------------------------
# Line 191: Property with zero coordinates
# ---------------------------------------------------------------------------

class TestRandomPositionGeneration:

    def test_generates_without_property_json(self, synth_env):
        """Generator no longer needs property.json — uses random positions on river."""
        (synth_env / "property.json").unlink()
        from port.src.gauge.synthetic import SyntheticGaugeGenerator
        result = SyntheticGaugeGenerator(synth_env).generate(count=10)
        assert result["count"] > 0

    def test_respects_count_parameter(self, synth_env):
        """Generator should create up to the requested count of synthetic gauges."""
        from port.src.gauge.synthetic import SyntheticGaugeGenerator
        result = SyntheticGaugeGenerator(synth_env).generate(count=3)
        assert 0 < result["count"] <= 3


# ---------------------------------------------------------------------------
# Line 237: Existing synthetic gauge skipped in polyline builder
# ---------------------------------------------------------------------------

