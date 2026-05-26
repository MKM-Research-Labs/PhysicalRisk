# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Tests for SyntheticGaugeGenerator — creates virtual gauges on the
river centreline as a port pipeline step.
"""

import json
import math

import pytest

from models.floodrisk.spatial import haversine_distance


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_gauge_cdm(gauge_id, lat, lon, elevation, alert, warning, severe):
    """Minimal CDM gauge dict matching real gauge.json structure."""
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
    """Minimal CDM property dict."""
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
    """Set up gauge.json + property.json + catchment params for synthetic gauge tests."""
    gauges = [
        _make_gauge_cdm("GAUGE-AAA00001", 51.45, -0.50, 3.0, 3.5, 4.5, 5.0),
        _make_gauge_cdm("GAUGE-BBB00002", 51.46, -0.30, 4.0, 4.0, 5.0, 6.0),
        _make_gauge_cdm("GAUGE-CCC00003", 51.47, -0.10, 5.0, 4.5, 5.5, 7.0),
    ]
    gauge_data = {"flood_gauges": gauges}
    (tmp_path / "gauge.json").write_text(json.dumps(gauge_data))

    properties = [
        _make_property_cdm("PROP-001", 51.455, -0.40),
        _make_property_cdm("PROP-002", 51.465, -0.20),
    ]
    prop_data = {"properties": properties}
    (tmp_path / "property.json").write_text(json.dumps(prop_data))

    # Patch config to return our GAUGE_POINTS
    from unittest.mock import MagicMock
    mock_params = MagicMock()
    mock_params.GAUGE_POINTS = GAUGE_POINTS
    del mock_params.GAUGEPOINTS  # avoid attribute clash

    from config import config as cfg
    monkeypatch.setattr(cfg, "load_params_module", lambda: mock_params)
    monkeypatch.setattr(cfg, "catchment_id", "thames")

    return tmp_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSyntheticGaugeGenerator:

    def test_creates_synthetic_gauges(self, synth_env):
        from port.src.gauge.synthetic import SyntheticGaugeGenerator
        gen = SyntheticGaugeGenerator(synth_env)
        result = gen.generate()

        assert result["count"] > 0
        assert len(result["gauge_ids"]) == result["count"]

    def test_appends_to_gauge_json(self, synth_env):
        from port.src.gauge.synthetic import SyntheticGaugeGenerator
        gen = SyntheticGaugeGenerator(synth_env)
        gen.generate()

        with open(synth_env / "gauge.json") as f:
            data = json.load(f)

        # Original 3 + synthetic gauges
        assert len(data["flood_gauges"]) > 3
        synth = [g for g in data["flood_gauges"]
                 if g["FloodGauge"]["Header"]["GaugeID"].startswith("SYNTH")]
        assert len(synth) > 0

    def test_synthetic_gauge_has_cdm_structure(self, synth_env):
        from port.src.gauge.synthetic import SyntheticGaugeGenerator
        gen = SyntheticGaugeGenerator(synth_env)
        gen.generate()

        with open(synth_env / "gauge.json") as f:
            data = json.load(f)

        synth = [g for g in data["flood_gauges"]
                 if g["FloodGauge"]["Header"]["GaugeID"].startswith("SYNTH")]
        for sg in synth:
            fg = sg["FloodGauge"]
            # Header
            assert "GaugeID" in fg["Header"]
            assert "CatchmentID" in fg["Header"]
            # Location
            assert "GaugeLatitude" in fg["Location"]
            assert "GaugeLongitude" in fg["Location"]
            assert "GaugeElevation" in fg["Location"]
            # SensorDetails (for propertyts gauge_lookup)
            si = fg["SensorDetails"]["GaugeInformation"]
            assert "GaugeLatitude" in si
            assert "GroundLevelMeters" in si
            # FloodStage
            uk = fg["FloodStage"]["UK"]
            assert "FloodAlert" in uk
            assert "FloodWarning" in uk
            assert "SevereFloodWarning" in uk

    def test_synthetic_gauge_on_river_centreline(self, synth_env):
        """Synthetic gauge lat/lon should be on the polyline (very close to it)."""
        from port.src.gauge.synthetic import SyntheticGaugeGenerator
        gen = SyntheticGaugeGenerator(synth_env)
        gen.generate()

        with open(synth_env / "gauge.json") as f:
            data = json.load(f)

        synth = [g for g in data["flood_gauges"]
                 if g["FloodGauge"]["Header"]["GaugeID"].startswith("SYNTH")]
        for sg in synth:
            loc = sg["FloodGauge"]["Location"]
            lat, lon = loc["GaugeLatitude"], loc["GaugeLongitude"]
            # Should be on the river polyline (if available) or close to
            # the gauge polyline.  River-snapped gauges may be up to a few
            # km from the coarse gauge polyline at river bends.
            from port.src.gauge.synthetic import _load_river_polyline
            river = _load_river_polyline()
            if river and len(river) >= 2:
                from models.floodrisk.spatial import nearest_point_on_polyline
                _, _, dist_m, _, _ = nearest_point_on_polyline(lat, lon, river)
                assert dist_m < 50.0, (
                    f"Synthetic gauge at ({lat}, {lon}) is {dist_m}m from river"
                )
            else:
                from models.floodrisk.spatial import nearest_point_on_polyline
                _, _, dist_m, _, _ = nearest_point_on_polyline(lat, lon, GAUGE_POINTS)
                assert dist_m < 1.0, (
                    f"Synthetic gauge at ({lat}, {lon}) is {dist_m}m from polyline"
                )

    def test_interpolated_elevation(self, synth_env):
        from port.src.gauge.synthetic import SyntheticGaugeGenerator
        gen = SyntheticGaugeGenerator(synth_env)
        gen.generate()

        with open(synth_env / "gauge.json") as f:
            data = json.load(f)

        synth = [g for g in data["flood_gauges"]
                 if g["FloodGauge"]["Header"]["GaugeID"].startswith("SYNTH")]
        for sg in synth:
            elev = sg["FloodGauge"]["Location"]["GaugeElevation"]
            # Should be between 3.0 and 5.0 (the gauge elevation range)
            assert 3.0 <= elev <= 5.0

    def test_interpolated_flood_stages(self, synth_env):
        from port.src.gauge.synthetic import SyntheticGaugeGenerator
        gen = SyntheticGaugeGenerator(synth_env)
        gen.generate()

        with open(synth_env / "gauge.json") as f:
            data = json.load(f)

        synth = [g for g in data["flood_gauges"]
                 if g["FloodGauge"]["Header"]["GaugeID"].startswith("SYNTH")]
        for sg in synth:
            stages = sg["FloodGauge"]["FloodStage"]["UK"]
            # Alert should be between min(3.5, 4.0, 4.5) and max(3.5, 4.0, 4.5)
            assert 3.5 <= stages["FloodAlert"] <= 4.5
            assert 4.5 <= stages["FloodWarning"] <= 5.5
            assert 5.0 <= stages["SevereFloodWarning"] <= 7.0

    def test_deduplication(self, synth_env):
        """Synthetic gauges placed too close together should be deduplicated."""
        from port.src.gauge.synthetic import SyntheticGaugeGenerator

        # Request many gauges — dedup should reduce the count below the request
        gen = SyntheticGaugeGenerator(synth_env)
        result = gen.generate(count=200)

        # With only 2 polyline segments, dedup should reduce well below 200
        assert result["count"] < 200
        assert result["count"] > 0

    def test_no_gauge_json_returns_zero(self, tmp_path):
        from port.src.gauge.synthetic import SyntheticGaugeGenerator
        result = SyntheticGaugeGenerator(tmp_path).generate()
        assert result["count"] == 0

    def test_no_property_json_still_generates(self, synth_env):
        """Generator no longer needs property.json — generates random positions on river."""
        (synth_env / "property.json").unlink()
        from port.src.gauge.synthetic import SyntheticGaugeGenerator
        result = SyntheticGaugeGenerator(synth_env).generate()
        assert result["count"] > 0

    def test_small_count_request(self, synth_env):
        """Requesting a small number of synthetic gauges should work."""
        from port.src.gauge.synthetic import SyntheticGaugeGenerator
        result = SyntheticGaugeGenerator(synth_env).generate(count=5)
        assert 0 < result["count"] <= 5
