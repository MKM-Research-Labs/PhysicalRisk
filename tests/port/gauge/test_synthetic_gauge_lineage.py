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
Data flow lineage tests for synthetic gauges.

Verifies the critical path: gauge.json (SYNTH) → gaugets (storm responses)
→ gaugehc (hazard curves) → propertyts (1 synth + 2 real per property)
→ propertyhc (PRS pricing with real events).

These tests read from the generated data directory and verify that
synthetic gauges flow through every pipeline step correctly.
"""

import json
from pathlib import Path

import pytest

from config import config


def _input_dir() -> Path:
    return config.get_input_dir()


# Disk-based lineage integration test: it reads the on-disk ``.json`` artifact
# tree directly and globs ``SYNTH-*.json``. Skip when that tree is absent — under
# ``MKM_REPO_BACKEND=pg`` or a decommissioned tree the portfolio lives in the
# seam, not on disk, and lineage is not yet seam-aware (see
# test_lineage_backend_coupling.py). This turns silent empty-glob passes / bare
# open() errors into a clean skip.
pytestmark = pytest.mark.skipif(
    not (config.get_input_dir() / "gauge.json").is_file(),
    reason="requires the on-disk gauge.json artifact (file backend); "
    "skipped under pg backend / decommissioned tree",
)


def _load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 1. gauge.json contains synthetic gauges
# ---------------------------------------------------------------------------

class TestSyntheticGaugesInGaugeJson:

    def test_gauge_json_has_synth_gauges(self):
        data = _load_json(_input_dir() / "gauge.json")
        gauges = data.get("flood_gauges", [])
        synth = [g for g in gauges
                 if g["FloodGauge"]["Header"]["GaugeID"].startswith("SYNTH")]
        assert len(synth) > 0, "No synthetic gauges found in gauge.json"

    def test_synth_gauge_has_required_cdm_fields(self):
        data = _load_json(_input_dir() / "gauge.json")
        synth = [g for g in data["flood_gauges"]
                 if g["FloodGauge"]["Header"]["GaugeID"].startswith("SYNTH")]
        for sg in synth[:3]:
            fg = sg["FloodGauge"]
            assert fg["Header"]["GaugeID"].startswith("SYNTH")
            assert fg["Location"]["GaugeLatitude"] != 0
            assert fg["Location"]["GaugeLongitude"] != 0
            assert fg["Location"]["GaugeElevation"] > 0
            si = fg["SensorDetails"]["GaugeInformation"]
            assert si["GaugeLatitude"] != 0
            assert si["GroundLevelMeters"] > 0
            uk = fg["FloodStage"]["UK"]
            assert uk["FloodAlert"] > 0
            assert uk["FloodWarning"] > uk["FloodAlert"]
            assert uk["SevereFloodWarning"] > uk["FloodWarning"]


# ---------------------------------------------------------------------------
# 2. gaugets/ has storm responses for synthetic gauges
# ---------------------------------------------------------------------------

class TestSyntheticGaugesInGaugets:

    def test_synth_gaugets_files_exist(self):
        gaugets_dir = _input_dir() / "gaugets"
        synth_files = list(gaugets_dir.glob("SYNTH-*.json"))
        assert len(synth_files) > 0, "No SYNTH gaugets files found"

    def test_synth_gaugets_have_storm_responses(self):
        gaugets_dir = _input_dir() / "gaugets"
        synth_files = sorted(gaugets_dir.glob("SYNTH-*.json"))[:3]
        for f in synth_files:
            data = _load_json(f)
            resps = data.get("storm_responses", {}).get("responses", [])
            assert len(resps) > 0, f"{f.name} has no storm responses"

    def test_synth_gaugets_have_exceeded_alerts(self):
        """At least some storms should exceed alert at synthetic gauges."""
        gaugets_dir = _input_dir() / "gaugets"
        synth_files = sorted(gaugets_dir.glob("SYNTH-*.json"))[:3]
        for f in synth_files:
            data = _load_json(f)
            resps = data["storm_responses"]["responses"]
            exceeded = [r for r in resps if r.get("exceeded_alert")]
            assert len(exceeded) > 0, f"{f.name} has no alert-exceeding storms"


# ---------------------------------------------------------------------------
# 3. gaugehc.json has hazard curves for synthetic gauges
# ---------------------------------------------------------------------------

class TestSyntheticGaugesInGaugehc:

    def test_gaugehc_has_synth_curves(self):
        data = _load_json(_input_dir() / "gaugehc.json")
        curves = data.get("hazard_curves", {})
        synth = {k: v for k, v in curves.items() if k.startswith("SYNTH")}
        assert len(synth) > 0, "No synthetic hazard curves in gaugehc.json"

    def test_synth_hazard_rates_positive(self):
        data = _load_json(_input_dir() / "gaugehc.json")
        curves = data.get("hazard_curves", {})
        synth = {k: v for k, v in curves.items() if k.startswith("SYNTH")}
        for sid, hc in list(synth.items())[:3]:
            assert hc.get("annual_hazard_rate_alert", 0) > 0, \
                f"{sid} has zero alert hazard rate"

    def test_synth_has_term_structure(self):
        data = _load_json(_input_dir() / "gaugehc.json")
        curves = data.get("hazard_curves", {})
        synth = {k: v for k, v in curves.items() if k.startswith("SYNTH")}
        for sid, hc in list(synth.items())[:3]:
            ts = hc.get("term_structure_alert", [])
            assert len(ts) > 0, f"{sid} has no term structure"


# ---------------------------------------------------------------------------
# 4. propertyts has exactly 1 synth + 2 real gauges per property
# ---------------------------------------------------------------------------

class TestPropertyTSGaugeComposition:

    def test_every_property_has_one_synthetic_gauge(self):
        pts_dir = _input_dir() / "propertyts"
        failures = []
        for f in sorted(pts_dir.glob("PROP-*.json")):
            data = _load_json(f)
            ngs = data.get("nearest_gauges", [])
            synth_count = sum(1 for ng in ngs
                              if ng["gauge_id"].startswith("SYNTH"))
            if synth_count != 1:
                failures.append(f"{data['property_id']}: {synth_count} synthetic")
        assert not failures, \
            f"{len(failures)} properties without exactly 1 synthetic gauge: {failures[:5]}"

    def test_every_property_has_two_real_gauges(self):
        pts_dir = _input_dir() / "propertyts"
        failures = []
        for f in sorted(pts_dir.glob("PROP-*.json")):
            data = _load_json(f)
            ngs = data.get("nearest_gauges", [])
            real_count = sum(1 for ng in ngs
                             if not ng["gauge_id"].startswith("SYNTH"))
            if real_count != 2:
                failures.append(f"{data['property_id']}: {real_count} real")
        assert not failures, \
            f"{len(failures)} properties without exactly 2 real gauges: {failures[:5]}"

    def test_every_property_has_three_gauges_total(self):
        pts_dir = _input_dir() / "propertyts"
        for f in sorted(pts_dir.glob("PROP-*.json"))[:10]:
            data = _load_json(f)
            ngs = data.get("nearest_gauges", [])
            assert len(ngs) == 3, \
                f"{data['property_id']} has {len(ngs)} gauges, expected 3"


# ---------------------------------------------------------------------------
# 5. propertyhc has PRS pricing referencing synthetic gauges
# ---------------------------------------------------------------------------

class TestPropertyHCWithSyntheticGauges:

    def test_propertyhc_has_synth_in_nearest_gauges(self):
        data = _load_json(_input_dir() / "propertyhc.json")
        curves = data.get("property_hazard_curves", {})
        found_synth = False
        for pid, phc in list(curves.items())[:20]:
            for ng in phc.get("nearest_gauges", []):
                if ng["gauge_id"].startswith("SYNTH"):
                    found_synth = True
                    break
            if found_synth:
                break
        assert found_synth, "No synthetic gauges found in propertyhc nearest_gauges"

    def test_propertyhc_synth_gauge_has_basis(self):
        """Synthetic gauge in propertyhc should have basis_bps computed."""
        data = _load_json(_input_dir() / "propertyhc.json")
        curves = data.get("property_hazard_curves", {})
        for pid, phc in list(curves.items())[:20]:
            for ng in phc.get("nearest_gauges", []):
                if ng["gauge_id"].startswith("SYNTH"):
                    assert "basis_bps" in ng, \
                        f"{pid}: synthetic gauge {ng['gauge_id']} missing basis_bps"
                    return
        pytest.skip("No synthetic gauges found in sampled properties")


# ---------------------------------------------------------------------------
# 6. End-to-end: storm events flow from gauge to property
# ---------------------------------------------------------------------------

class TestStormEventFlow:

    def test_gauge_storms_reach_property_events(self):
        """
        Properties should have flood_events sourced from gauge storm responses.
        The number of events should be > 0 for at least some properties.
        """
        pts_dir = _input_dir() / "propertyts"
        properties_with_events = 0
        for f in sorted(pts_dir.glob("PROP-*.json")):
            data = _load_json(f)
            events = data.get("flood_events", [])
            if len(events) > 0:
                properties_with_events += 1
        assert properties_with_events > 0, \
            "No properties have any flood events — storm data not flowing through"

    def test_some_properties_actually_flood(self):
        """At least some properties should have flooded=True events.

        Guards against the flood_idw signal-dilution failure mode (IDW across the
        nearest gauges washing out the synthetic flood signal so nothing floods).
        A regeneration that leaves every property unflooded should fail here.
        """
        pts_dir = _input_dir() / "propertyts"
        flooded_count = 0
        for f in sorted(pts_dir.glob("PROP-*.json")):
            data = _load_json(f)
            flooded = [e for e in data.get("flood_events", [])
                       if e.get("flooded")]
            if flooded:
                flooded_count += 1
        assert flooded_count > 0, \
            "No properties have flooded events — check attenuation/elevation"
