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

"""Tests for CommercialHazardCurveGenerator.

The pricing / GEV / basis logic is inherited from the residential
generator; we exercise that the asset-config wiring reads
commercialts/ and writes commercialhc.json (plus the shd/she variants).
"""

import json
from pathlib import Path

import pytest
from db_helpers import tmp_catchment

from config import config
from port.src.commercial.hc import CommercialHazardCurveGenerator
from port.src.property.hc import PropertyHazardCurveGenerator
from port.utils.asset_config import COMMERCIAL_CONFIG


@pytest.fixture(autouse=True)
def _seam_backend(tmp_path):
    """Bind a scratch backend rooted at tmp_path so the generator's hazard-curve
    reads/writes (now on the database seam) resolve there — the same path these
    tests read the commercialhc/commercialshd/... files back from."""
    with tmp_catchment(tmp_path, "thames"):
        yield


# ---------------------------------------------------------------------------
# Helpers — write minimal commercialts/ + gaugehc inputs
# ---------------------------------------------------------------------------


def _write_commercial_ts(ts_dir: Path, n_assets: int = 2):
    """Write n_assets minimal CPROP-*.json files into ts_dir."""
    ts_dir.mkdir(parents=True, exist_ok=True)
    for i in range(n_assets):
        pid = f"CPROP-{i:08x}"
        (ts_dir / f"{pid}.json").write_text(json.dumps({
            "property_id": pid,
            "location": {"lat": 51.5 + 0.001 * i, "lon": -0.1 + 0.001 * i},
            "elevation_m": 5.0,
            "floor_level_m": 0.3,
            "flood_zone": "Zone 2",
            "property_type": "Office",
            "construction_year": 2010,
            "nearest_gauges": [{"gauge_id": "GAUGE-001",
                                 "distance_m": 1200, "gauge_elevation_m": 3.5}],
            "flood_events": [{
                "storm_id": "STORM-001",
                "flood_depth_m": 0.5,
                "flooded": True,
                "damage_ratio": 0.1,
                "exceeded_severe": True,
            }],
            "summary": {"property_id": pid,
                        "floods_at_nearest_gauge": 5,
                        "floods_at_property": 1},
        }))


def _write_gaugehc(tmp_path: Path):
    """Minimal gaugehc.json + storm_sequences.json."""
    (tmp_path / "gaugehc.json").write_text(json.dumps({
        "metadata": {"catchment_id": "thames", "num_storms": 100},
        "hazard_curves": {
            "GAUGE-001": {
                "annual_hazard_rate_alert": 0.05,
                "annual_hazard_rate_warning": 0.02,
                "annual_hazard_rate_severe": 0.005,
            },
        },
    }))
    (tmp_path / "storm_sequences.json").write_text(json.dumps({
        "num_sequences": 100, "sequences": [],
    }))


@pytest.fixture
def commercial_hc_input(tmp_path):
    _write_commercial_ts(tmp_path / "commercialts")
    _write_gaugehc(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Class wiring
# ---------------------------------------------------------------------------


class TestClassWiring:

    def test_subclasses_property_hc(self):
        assert issubclass(CommercialHazardCurveGenerator, PropertyHazardCurveGenerator)

    def test_asset_config_is_commercial(self):
        assert CommercialHazardCurveGenerator.ASSET_CONFIG is COMMERCIAL_CONFIG


# ---------------------------------------------------------------------------
# End-to-end against a tmp commercialts/ + gaugehc.json
# ---------------------------------------------------------------------------


@pytest.mark.generator
class TestCommercialHazardCurveGenerate:

    def test_reads_commercialts_writes_commercialhc(self, commercial_hc_input):
        gen = CommercialHazardCurveGenerator(output_dir=commercial_hc_input, verbose=False)
        gen.generate()
        assert (commercial_hc_input / "commercialhc.json").exists()
        # Confirm we didn't write to the residential path.
        assert not (commercial_hc_input / "propertyhc.json").exists()

    def test_hc_metadata_shape(self, commercial_hc_input):
        gen = CommercialHazardCurveGenerator(output_dir=commercial_hc_input, verbose=False)
        gen.generate()
        d = json.loads((commercial_hc_input / "commercialhc.json").read_text())
        assert d["metadata"]["catchment_id"] == config.CATCHMENT
        assert d["metadata"]["num_properties"] == 2
        assert "property_hazard_curves" in d

    def test_hc_keys_use_cprop_prefix(self, commercial_hc_input):
        gen = CommercialHazardCurveGenerator(output_dir=commercial_hc_input, verbose=False)
        gen.generate()
        d = json.loads((commercial_hc_input / "commercialhc.json").read_text())
        for pid in d["property_hazard_curves"]:
            assert pid.startswith("CPROP-")

    def test_shd_mode_writes_commercialshd(self, commercial_hc_input):
        # Need a commercialtsd/ to feed shd mode.
        _write_commercial_ts(commercial_hc_input / "commercialtsd")
        gen = CommercialHazardCurveGenerator(output_dir=commercial_hc_input, verbose=False, mode="shd")
        gen.generate()
        assert (commercial_hc_input / "commercialshd.json").exists()

    def test_she_mode_writes_commercialshe(self, commercial_hc_input):
        _write_commercial_ts(commercial_hc_input / "commercialtse")
        gen = CommercialHazardCurveGenerator(output_dir=commercial_hc_input, verbose=False, mode="she")
        gen.generate()
        assert (commercial_hc_input / "commercialshe.json").exists()

    def test_missing_ts_dir_raises_helpful_error(self, tmp_path):
        _write_gaugehc(tmp_path)
        gen = CommercialHazardCurveGenerator(output_dir=tmp_path, verbose=False)
        with pytest.raises(FileNotFoundError, match="Commercial timeseries"):
            gen.generate()

    def test_attach_spread_decomposition_targets_commercial_files(self, commercial_hc_input):
        # Generate all three modes.
        _write_commercial_ts(commercial_hc_input / "commercialtsd")
        _write_commercial_ts(commercial_hc_input / "commercialtse")
        gen = CommercialHazardCurveGenerator(output_dir=commercial_hc_input, verbose=False)
        gen.generate()
        CommercialHazardCurveGenerator(output_dir=commercial_hc_input, verbose=False, mode="shd").generate()
        CommercialHazardCurveGenerator(output_dir=commercial_hc_input, verbose=False, mode="she").generate()
        # Decomposition should not touch the residential propertyhc.json
        n = gen.attach_spread_decomposition()
        assert n >= 0
        assert (commercial_hc_input / "commercialhc.json").exists()
        # Reload + assert decomposition fields landed on commercial output.
        d = json.loads((commercial_hc_input / "commercialhc.json").read_text())
        any_decomp = any("spread_decomposition" in c
                         for c in d["property_hazard_curves"].values())
        assert any_decomp
