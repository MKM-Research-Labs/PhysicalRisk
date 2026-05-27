# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for the CommercialTimeSeriesGenerator.

The flood-propagation logic is identical to the residential generator
(those tests cover the inner loop in tests/port/property/). The point of
these tests is to confirm the asset-config wiring: that the commercial
subclass reads commercial.json, writes commercialts/ + CPROP- files, and
inherits everything else unchanged.
"""

import json
from pathlib import Path

import pytest

from port.src.commercial.ts import CommercialTimeSeriesGenerator
from port.src.property.ts import PropertyTimeSeriesGenerator
from port.utils.asset_config import COMMERCIAL_CONFIG


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_gauge_json(tmp_path: Path):
    """Write a minimal gauge.json with one gauge."""
    data = {
        "flood_gauges": [{
            "FloodGauge": {
                "Header": {"GaugeID": "GAUGE-001"},
                "SensorDetails": {"GaugeInformation": {
                    "GaugeLatitude": 51.50,
                    "GaugeLongitude": -0.10,
                    "GroundLevelMeters": 3.0,
                }},
                "FloodStage": {"UK": {
                    "FloodAlert": 3.5, "FloodWarning": 4.5, "SevereFloodWarning": 5.0,
                }},
            }
        }],
    }
    (tmp_path / "gauge.json").write_text(json.dumps(data))


def _write_commercial_json(tmp_path: Path, n: int = 3):
    """Write a minimal commercial.json with n assets."""
    assets = []
    for i in range(n):
        assets.append({
            "CommercialAsset": {
                "Header": {"PropertyID": f"CPROP-{i:08x}", "CatchmentID": "thames"},
                "Location": {
                    "LatitudeDegrees": 51.50 + 0.001 * i,
                    "LongitudeDegrees": -0.10 + 0.001 * i,
                },
                "RiskAssessment": {"GroundLevelMeters": 5.0},
                "Construction": {"FloorLevelMeters": 0.3},
                "CommercialAttributes": {
                    "CommercialType": "Office",
                    "ConstructionYear": 2010,
                    "PropertyPeriod": "2009-Present",
                },
            }
        })
    (tmp_path / "commercial.json").write_text(json.dumps({
        "commercial_assets": assets,
        "generation_metadata": {"catchment": "thames", "total_assets_generated": n},
    }))


def _write_gaugets(tmp_path: Path):
    """Write a minimal gaugets/GAUGE-001.json."""
    gts_dir = tmp_path / "gaugets"
    gts_dir.mkdir(parents=True)
    (gts_dir / "GAUGE-001.json").write_text(json.dumps({
        "gauge_id": "GAUGE-001",
        "storm_responses": {"responses": [{
            "storm_id": "STORM-001", "peak_level_m": 5.8,
            "exceeded_alert": True, "exceeded_warning": True, "exceeded_severe": True,
        }]},
        "flood_simulation": {"readings": [
            {"hour": h, "waterLevel": 5.8 * max(0, 1 - abs(h - 12) / 20)}
            for h in range(25)
        ]},
    }))


@pytest.fixture
def commercial_input(tmp_path, monkeypatch):
    """tmp dir wired up with commercial.json + gauge.json + gaugets/."""
    _write_gauge_json(tmp_path)
    _write_commercial_json(tmp_path)
    _write_gaugets(tmp_path)
    monkeypatch.setattr("config.config.get_gaugets_dir",
                        lambda: tmp_path / "gaugets")
    monkeypatch.setattr("config.config.get_input_path",
                        lambda name: tmp_path / name)
    return tmp_path


# ---------------------------------------------------------------------------
# Class identity + inheritance
# ---------------------------------------------------------------------------


class TestClassWiring:

    def test_subclasses_property_generator(self):
        assert issubclass(CommercialTimeSeriesGenerator, PropertyTimeSeriesGenerator)

    def test_asset_config_is_commercial(self):
        assert CommercialTimeSeriesGenerator.ASSET_CONFIG is COMMERCIAL_CONFIG

    def test_residential_unchanged_by_subclass(self):
        # Defensive — confirm the subclass didn't mutate the parent's config.
        from port.utils.asset_config import RESIDENTIAL_CONFIG
        assert PropertyTimeSeriesGenerator.ASSET_CONFIG is RESIDENTIAL_CONFIG


# ---------------------------------------------------------------------------
# End-to-end behaviour against a tmp commercial.json
# ---------------------------------------------------------------------------


@pytest.mark.generator
class TestCommercialTimeSeriesGenerate:

    def test_writes_to_commercialts_directory(self, commercial_input):
        gen = CommercialTimeSeriesGenerator(output_dir=commercial_input, verbose=False)
        gen.generate()
        assert (commercial_input / "commercialts").exists()
        # Must NOT have written to residential output.
        assert not (commercial_input / "propertyts").exists()

    def test_writes_per_asset_files_with_cprop_prefix(self, commercial_input):
        gen = CommercialTimeSeriesGenerator(output_dir=commercial_input, verbose=False)
        gen.generate()
        ts_dir = commercial_input / "commercialts"
        files = sorted(f.name for f in ts_dir.glob("CPROP-*.json"))
        assert len(files) == 3
        for fname in files:
            assert fname.startswith("CPROP-")

    def test_portfolio_flood_summary_written(self, commercial_input):
        gen = CommercialTimeSeriesGenerator(output_dir=commercial_input, verbose=False)
        gen.generate()
        summary_path = commercial_input / "commercialts" / "portfolio_flood_summary.json"
        assert summary_path.exists()
        data = json.loads(summary_path.read_text())
        assert data["catchment"] == "thames"
        assert data["summary"]["total_properties"] == 3

    def test_shd_mode_writes_to_commercialtsd(self, commercial_input):
        gen = CommercialTimeSeriesGenerator(output_dir=commercial_input, verbose=False, mode="shd")
        gen.generate()
        assert (commercial_input / "commercialtsd").exists()
        assert not (commercial_input / "propertytsd").exists()

    def test_she_mode_writes_to_commercialtse(self, commercial_input):
        gen = CommercialTimeSeriesGenerator(output_dir=commercial_input, verbose=False, mode="she")
        gen.generate()
        assert (commercial_input / "commercialtse").exists()
        assert not (commercial_input / "propertytse").exists()

    def test_per_asset_file_shape(self, commercial_input):
        gen = CommercialTimeSeriesGenerator(output_dir=commercial_input, verbose=False)
        gen.generate()
        ts_dir = commercial_input / "commercialts"
        first = next(ts_dir.glob("CPROP-*.json"))
        data = json.loads(first.read_text())
        # Shape must be identical to residential per-property output so
        # downstream consumers (commercialhc) work unchanged.
        for key in ("property_id", "location", "elevation_m", "floor_level_m",
                    "flood_zone", "nearest_gauges", "flood_events", "summary"):
            assert key in data
        # property_type field now carries the commercial-type label.
        assert data["property_type"] == "Office"
