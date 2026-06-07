# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""End-to-end tests for CommercialPortfolioGenerator.

Each test isolates output under tmp_path so test runs do not stomp on
real data/input/thames/ files.
"""

import json
import re
from collections import Counter

import pytest

from config import config
from port.cdm import CommercialAssetCDM
from port.src.commercial import (
    CommercialPortfolioGenerator,
    generate_commercials,
)


def _catchment_latlon_bounds(margin: float = 0.5):
    """Padded (lat, lon) envelope from the active catchment's GAUGE_POINTS.

    Commercial assets are placed within ~2km of synthetic gauges (which sit
    on the catchment's gauge points), so a 0.5 degree margin comfortably
    bounds them. Catchment-agnostic: thames sits ~51-52N, halong elsewhere.
    """
    import importlib
    mod = importlib.import_module(f"catch.{config.CATCHMENT}")
    pts = getattr(mod, "GAUGE_POINTS", []) or []
    lats = [p[0] for p in pts]
    lons = [p[1] for p in pts]
    if lats and lons:
        return (
            (min(lats) - margin, max(lats) + margin),
            (min(lons) - margin, max(lons) + margin),
        )
    return ((-90.0, 90.0), (-180.0, 180.0))


@pytest.fixture
def gen(tmp_path):
    """A CommercialPortfolioGenerator with tmp-path output, suppressed logging."""
    return CommercialPortfolioGenerator(output_dir=tmp_path, verbose=False)


@pytest.mark.generator
class TestGeneratorReturn:

    def test_generate_returns_expected_keys(self, gen):
        result = gen.generate(count=10)
        assert set(result) == {"data", "file_path", "processing_stats"}
        assert set(result["data"]) == {"commercial_assets", "asset_ids", "locations"}

    def test_processing_stats_complete(self, gen):
        result = gen.generate(count=10)
        stats = result["processing_stats"]
        assert stats["total_assets"] == 10
        assert stats["successful_assets"] == 10
        assert stats["failed_assets"] == 0
        assert stats["start_time"] is not None
        assert stats["end_time"] is not None

    def test_default_count_is_ten(self, gen):
        result = gen.generate()
        assert len(result["data"]["commercial_assets"]) == 10


@pytest.mark.generator
class TestRecordStructure:

    @pytest.fixture
    def records(self, gen):
        return gen.generate(count=10)["data"]["commercial_assets"]

    def test_record_count(self, records):
        assert len(records) == 10

    def test_each_record_has_commercial_asset_root(self, records):
        for r in records:
            assert "CommercialAsset" in r

    def test_each_record_has_required_sub_sections(self, records):
        for r in records:
            ca = r["CommercialAsset"]
            for section in ("Header", "Valuation", "CommercialAttributes",
                            "Location", "Construction"):
                assert section in ca, f"missing {section}"

    def test_property_ids_unique(self, records):
        ids = [r["CommercialAsset"]["Header"]["PropertyID"] for r in records]
        assert len(set(ids)) == len(ids)

    def test_property_id_format(self, records):
        for r in records:
            pid = r["CommercialAsset"]["Header"]["PropertyID"]
            assert re.match(r"^CPROP-[a-f0-9]{8}$", pid), f"bad id: {pid}"

    def test_catchment_id_set(self, records):
        from config import config
        for r in records:
            assert r["CommercialAsset"]["Header"]["CatchmentID"] == config.CATCHMENT

    def test_lat_lon_populated(self, records):
        (lat_lo, lat_hi), (lon_lo, lon_hi) = _catchment_latlon_bounds()
        for r in records:
            loc = r["CommercialAsset"]["Location"]
            assert isinstance(loc["LatitudeDegrees"], (int, float))
            assert isinstance(loc["LongitudeDegrees"], (int, float))
            # Catchment sanity bounds derived from the active GAUGE_POINTS
            assert lat_lo < loc["LatitudeDegrees"] < lat_hi
            assert lon_lo < loc["LongitudeDegrees"] < lon_hi

    def test_commercial_type_valid_menu(self, records):
        valid = {"Office", "Retail", "Hotel", "Leisure", "Healthcare",
                 "MultiFamily", "MixedUse", "Other"}
        for r in records:
            ctype = r["CommercialAsset"]["CommercialAttributes"]["CommercialType"]
            assert ctype in valid

    def test_type_mix_matches_user_allocation(self, records):
        counts = Counter(
            r["CommercialAsset"]["CommercialAttributes"]["CommercialType"]
            for r in records
        )
        assert counts == {"Office": 3, "MultiFamily": 3, "Hotel": 1,
                          "Retail": 2, "MixedUse": 1}

    def test_property_value_is_positive(self, records):
        for r in records:
            v = r["CommercialAsset"]["Valuation"]["PropertyValue"]
            assert v > 0

    def test_property_area_is_positive(self, records):
        for r in records:
            a = r["CommercialAsset"]["CommercialAttributes"]["PropertyAreaSqm"]
            assert a > 0

    def test_records_validate_against_cdm(self, records):
        cdm = CommercialAssetCDM()
        for r in records:
            errors = cdm.validate(r)
            assert errors == {}, f"validation errors: {errors}"


@pytest.mark.generator
class TestOutputFile:

    def test_output_path_is_commercial_json(self, gen, tmp_path):
        result = gen.generate(count=10)
        assert result["file_path"] == tmp_path / "commercial.json"

    def test_output_file_exists(self, gen, tmp_path):
        gen.generate(count=10)
        assert (tmp_path / "commercial.json").exists()

    def test_output_file_is_valid_json(self, gen, tmp_path):
        gen.generate(count=10)
        d = json.loads((tmp_path / "commercial.json").read_text())
        assert "commercial_assets" in d
        assert "generation_metadata" in d
        assert d["generation_metadata"]["total_assets_generated"] == 10
        assert d["generation_metadata"]["catchment"] == config.CATCHMENT

    def test_type_mix_in_metadata(self, gen, tmp_path):
        gen.generate(count=10)
        d = json.loads((tmp_path / "commercial.json").read_text())
        mix = d["generation_metadata"]["type_mix"]
        assert mix == {"Office": 3, "MultiFamily": 3, "Hotel": 1,
                       "Retail": 2, "MixedUse": 1}


@pytest.mark.generator
class TestConvenienceFunction:

    def test_generate_commercials_calls_class(self, tmp_path):
        result = generate_commercials(count=5, output_dir=tmp_path)
        assert len(result["data"]["commercial_assets"]) == 5
        assert (tmp_path / "commercial.json").exists()


@pytest.mark.generator
class TestVariableCount:

    @pytest.mark.parametrize("count", [1, 5, 12, 20])
    def test_arbitrary_count_produces_n_records(self, tmp_path, count):
        gen = CommercialPortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=count)
        assert len(result["data"]["commercial_assets"]) == count


@pytest.mark.generator
class TestGaugeIdMap:
    """Cover the optional gauge.json sidecar load (generator.py:94-104)."""

    def test_gauge_map_populated_from_flood_gauges(self, tmp_path):
        gauge_data = {"flood_gauges": [
            {"FloodGauge": {"Header": {"GaugeID": "GAUGE-001"}}},
            {"FloodGauge": {"Header": {"GaugeID": "GAUGE-002"}}},
        ]}
        (tmp_path / "gauge.json").write_text(json.dumps(gauge_data))
        gen = CommercialPortfolioGenerator(output_dir=tmp_path, verbose=False)
        gen.generate(count=3)
        assert gen._gauge_id_map == {0: "GAUGE-001", 1: "GAUGE-002"}

    def test_gauge_map_falls_back_to_gauges_key(self, tmp_path):
        """Legacy 'gauges' key is used when 'flood_gauges' is absent."""
        gauge_data = {"gauges": [
            {"FloodGauge": {"Header": {"GaugeID": "G-9"}}},
        ]}
        (tmp_path / "gauge.json").write_text(json.dumps(gauge_data))
        gen = CommercialPortfolioGenerator(output_dir=tmp_path, verbose=False)
        gen.generate(count=2)
        assert gen._gauge_id_map == {0: "G-9"}

    def test_entries_without_gauge_id_are_skipped(self, tmp_path):
        gauge_data = {"flood_gauges": [
            {"FloodGauge": {"Header": {"GaugeID": "GAUGE-001"}}},
            {"FloodGauge": {"Header": {}}},          # no GaugeID -> skipped
            {"FloodGauge": {"Header": {"GaugeID": "GAUGE-003"}}},
        ]}
        (tmp_path / "gauge.json").write_text(json.dumps(gauge_data))
        gen = CommercialPortfolioGenerator(output_dir=tmp_path, verbose=False)
        gen.generate(count=2)
        assert gen._gauge_id_map == {0: "GAUGE-001", 2: "GAUGE-003"}

    def test_malformed_gauge_json_is_tolerated(self, tmp_path):
        """A corrupt gauge.json must not abort generation (exception branch)."""
        (tmp_path / "gauge.json").write_text("{ this is not valid json")
        gen = CommercialPortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=3)
        assert gen._gauge_id_map == {}
        assert len(result["data"]["commercial_assets"]) == 3

    def test_no_gauge_file_leaves_map_empty(self, tmp_path):
        gen = CommercialPortfolioGenerator(output_dir=tmp_path, verbose=False)
        gen.generate(count=2)
        assert gen._gauge_id_map == {}


@pytest.mark.generator
class TestAssetFailureHandling:
    """Cover the per-asset failure path in the generation loop (generator.py:135-138)."""

    def test_failed_asset_is_counted_and_skipped(self, gen, monkeypatch):
        """A metadata error on one asset is counted and the loop continues."""
        original = gen.random.generate_commercial_metadata

        def flaky(i, location):
            if i == 0:
                raise RuntimeError("synthetic metadata failure")
            return original(i, location)

        monkeypatch.setattr(gen.random, "generate_commercial_metadata", flaky)

        result = gen.generate(count=5)
        stats = result["processing_stats"]
        assert stats["failed_assets"] == 1
        assert stats["successful_assets"] == 4
        assert len(result["data"]["commercial_assets"]) == 4
        assert len(result["data"]["asset_ids"]) == 4

    def test_all_assets_failing_yields_empty_records(self, gen, monkeypatch):
        def always_boom(i, location):
            raise RuntimeError("everything is broken")

        monkeypatch.setattr(gen.random, "generate_commercial_metadata",
                            always_boom)

        result = gen.generate(count=4)
        stats = result["processing_stats"]
        assert stats["failed_assets"] == 4
        assert stats["successful_assets"] == 0
        assert result["data"]["commercial_assets"] == []
        # Output file is still written, just empty.
        assert (gen.output_dir / "commercial.json").exists()
