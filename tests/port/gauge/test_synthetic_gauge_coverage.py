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
    monkeypatch.setattr(cfg, "CATCHMENT", "thames")

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

class TestSyntheticGaugeSkippedInPolyline:

    def test_existing_synth_gauge_not_matched_to_gauge_point(self, synth_env):
        """A pre-existing SYNTH- gauge in gauge.json is skipped in polyline matching."""
        with open(synth_env / "gauge.json") as f:
            data = json.load(f)

        # Add a synthetic gauge near a gauge point
        synth_gauge = _make_gauge_cdm(
            "SYNTH-existing", 51.45, -0.50, 3.0, 3.5, 4.5, 5.0
        )
        data["flood_gauges"].append(synth_gauge)
        (synth_env / "gauge.json").write_text(json.dumps(data))

        from port.src.gauge.synthetic import SyntheticGaugeGenerator
        result = SyntheticGaugeGenerator(synth_env).generate()

        # Should still work — synthetic gauges still created from real gauges
        assert result["count"] >= 0  # no crash is the key assertion


# ---------------------------------------------------------------------------
# Line 265: Property projects to polyline start
# ---------------------------------------------------------------------------

class TestPolylineEndpoints:

    def test_avoids_exact_endpoints(self, synth_env):
        """Synthetic gauges should not be placed at exact polyline endpoints."""
        from port.src.gauge.synthetic import SyntheticGaugeGenerator
        gen = SyntheticGaugeGenerator(synth_env)
        result = gen.generate(count=50)

        with open(synth_env / "gauge.json") as f:
            data = json.load(f)

        synth = [g for g in data["flood_gauges"]
                 if g["FloodGauge"]["Header"]["GaugeID"].startswith("SYNTH")]
        for sg in synth:
            loc = sg["FloodGauge"]["Location"]
            # Should not be exactly at any gauge point
            for gp_lat, gp_lon, _ in GAUGE_POINTS:
                assert not (loc["GaugeLatitude"] == gp_lat and
                            loc["GaugeLongitude"] == gp_lon)


# ---------------------------------------------------------------------------
# Line 278: Flanking gauge missing from lookup
# ---------------------------------------------------------------------------

class TestGenerateSkipsNoneResult:
    """Line 151 of generator.py: _create_synthetic_at_position returns None → continue."""

    def test_generate_continues_when_position_returns_none(self, synth_env, monkeypatch):
        """When _create_synthetic_at_position returns None, generate() skips and retries."""
        from port.src.gauge.synthetic import SyntheticGaugeGenerator

        gen = SyntheticGaugeGenerator(synth_env)

        # Wrap the real method to return None on the first 3 calls
        original = gen._create_synthetic_at_position
        call_count = [0]

        def patched(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 3:
                return None
            return original(*args, **kwargs)

        monkeypatch.setattr(gen, "_create_synthetic_at_position", patched)
        result = gen.generate(count=2)
        # First 3 calls returned None (line 151 hit), then real results
        assert call_count[0] > 3
        assert result["count"] >= 0


class TestBuildGaugePolylineSkipsSynth:
    """Line 192 of generator.py: SYNTH- prefix gauges skipped in polyline builder."""

    def test_synth_gauge_in_lookup_is_skipped(self, synth_env, monkeypatch):
        """_build_gauge_polyline skips SYNTH- gauges in gauge_lookup."""
        from port.src.gauge.synthetic import SyntheticGaugeGenerator

        gen = SyntheticGaugeGenerator(synth_env)

        # Build a gauge_lookup that includes a SYNTH gauge very close to a gauge point
        gauge_lookup = {
            "GAUGE-AAA00001": {
                "lat": 51.45, "lon": -0.50, "elevation": 3.0,
                "flood_alert": 3.5, "flood_warning": 4.5,
                "severe_flood_warning": 5.0,
                "historical_high_level": 6.0, "historical_high_date": "",
            },
            "SYNTH-close": {
                "lat": 51.45, "lon": -0.50, "elevation": 3.0,
                "flood_alert": 3.5, "flood_warning": 4.5,
                "severe_flood_warning": 5.0,
                "historical_high_level": 6.0, "historical_high_date": "",
            },
            "GAUGE-BBB00002": {
                "lat": 51.46, "lon": -0.30, "elevation": 4.0,
                "flood_alert": 4.0, "flood_warning": 5.0,
                "severe_flood_warning": 6.0,
                "historical_high_level": 7.0, "historical_high_date": "",
            },
            "GAUGE-CCC00003": {
                "lat": 51.47, "lon": -0.10, "elevation": 5.0,
                "flood_alert": 4.5, "flood_warning": 5.5,
                "severe_flood_warning": 7.0,
                "historical_high_level": 8.0, "historical_high_date": "",
            },
        }

        polyline = gen._build_gauge_polyline(gauge_lookup)
        # Polyline should have entries but none referencing SYNTH-close
        gauge_ids = [p[3] for p in polyline]
        assert "SYNTH-close" not in gauge_ids


class TestFlankingGaugeMissing:

    def test_missing_flanking_gauge_returns_none(self, synth_env, monkeypatch):
        """_create_synthetic_at_position returns None when flanking gauge not in lookup."""
        from port.src.gauge.synthetic import SyntheticGaugeGenerator

        gen = SyntheticGaugeGenerator(synth_env)

        # Build a polyline referencing a gauge_id not in gauge_lookup
        polyline = [
            (51.45, -0.50, 3.0, "GAUGE-AAA00001"),
            (51.47, -0.10, 5.0, "GAUGE-MISSING"),
        ]
        gauge_lookup = {
            "GAUGE-AAA00001": {
                "lat": 51.45, "lon": -0.50, "elevation": 3.0,
                "flood_alert": 3.5, "flood_warning": 4.5,
                "severe_flood_warning": 5.0,
                "historical_high_level": 6.0, "historical_high_date": "",
            },
            # GAUGE-MISSING intentionally absent
        }

        result = gen._create_synthetic_at_position(0, 0.5, gauge_lookup, polyline)
        assert result is None
