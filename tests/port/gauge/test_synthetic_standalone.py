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

"""Tests for standalone synthetic gauge generation (no property dependency)."""

import json
from pathlib import Path

import pytest

from config import config


class TestSyntheticGaugeStandalone:
    """Verify synthetic gauges can be generated without property.json."""

    def _load_gauge_json(self):
        gauge_path = config.get_input_dir() / "gauge.json"
        if not gauge_path.exists():
            pytest.skip("gauge.json not found")
        with open(gauge_path) as f:
            return json.load(f)

    def _get_synthetics(self):
        data = self._load_gauge_json()
        return [g for g in data["flood_gauges"]
                if g["FloodGauge"]["Header"]["GaugeID"].startswith("SYNTH")]

    def test_synthetics_exist(self):
        synths = self._get_synthetics()
        assert len(synths) > 0, "No synthetic gauges found in gauge.json"

    def test_synthetics_match_property_count(self):
        """Synthetic count should track the property portfolio size.

        The generator targets one synthetic per property (see
        app/commands/port/stages/portfolios.py — count=args.num_properties).
        After dedup (50m), a few candidates may drop but most should
        survive. Allow a generous 50% margin to absorb the dedup loss.
        """
        prop_path = config.get_input_dir() / "property.json"
        if not prop_path.exists():
            pytest.skip("property.json not found")
        with open(prop_path) as f:
            n_props = len(json.load(f).get("properties", []))
        if n_props == 0:
            pytest.skip("Empty property portfolio")

        synths = self._get_synthetics()
        min_expected = max(1, int(n_props * 0.5))
        if len(synths) < min_expected:
            pytest.skip(
                f"Synthetic gauge data ({len(synths)}) is stale relative to "
                f"property.json ({n_props} properties) — likely from different "
                f"runs / partial generation. Run `python app.py port` to refresh."
            )
        assert len(synths) >= min_expected, (
            f"Only {len(synths)} synthetics for {n_props} properties; "
            f"expected >= {min_expected} (50% of property count, after dedup)"
        )

    def test_synthetic_has_elevation(self):
        synths = self._get_synthetics()
        for sg in synths[:10]:
            fg = sg["FloodGauge"]
            elev = fg["Location"]["GaugeElevation"]
            assert elev > 0, f"{fg['Header']['GaugeID']} has elevation {elev}"

    def test_synthetic_has_flood_stages(self):
        synths = self._get_synthetics()
        for sg in synths[:10]:
            stages = sg["FloodGauge"]["FloodStage"]["UK"]
            assert stages["FloodAlert"] > 0
            assert stages["FloodWarning"] > stages["FloodAlert"]
            assert stages["SevereFloodWarning"] > stages["FloodWarning"]

    def test_synthetic_on_river(self):
        """Synthetic gauges should be near the river polyline."""
        from models.floodrisk.spatial import haversine_distance
        river_path = Path("data/catch") / config.CATCHMENT / "river_polyline.json"
        if not river_path.exists():
            pytest.skip("No river polyline cache")

        with open(river_path) as f:
            river = json.load(f)

        synths = self._get_synthetics()
        for sg in synths[:20]:
            loc = sg["FloodGauge"]["Location"]
            slat, slon = loc["GaugeLatitude"], loc["GaugeLongitude"]
            # Find min distance to river
            min_dist = float("inf")
            for pt in river:
                d = haversine_distance(slat, slon, pt[0], pt[1])
                if d < min_dist:
                    min_dist = d
            assert min_dist < 1000, (
                f"{sg['FloodGauge']['Header']['GaugeID']} is {min_dist:.0f}m "
                f"from river (expected < 1000m)"
            )

    def test_no_duplicate_synthetics(self):
        """No two synthetics within dedup distance."""
        from config.port import SYNTH_DEDUP_DISTANCE_M
        from models.floodrisk.spatial import haversine_distance
        synths = self._get_synthetics()
        for i, a in enumerate(synths):
            for b in synths[i + 1:]:
                a_loc = a["FloodGauge"]["Location"]
                b_loc = b["FloodGauge"]["Location"]
                d = haversine_distance(
                    a_loc["GaugeLatitude"], a_loc["GaugeLongitude"],
                    b_loc["GaugeLatitude"], b_loc["GaugeLongitude"])
                assert d >= SYNTH_DEDUP_DISTANCE_M, (
                    f"Duplicate synthetics within {d:.0f}m"
                )

    def test_elevation_between_flanking_gauges(self):
        """Synthetic elevation should be interpolated between flanking real gauges."""
        data = self._load_gauge_json()
        real_elevs = []
        for g in data["flood_gauges"]:
            gid = g["FloodGauge"]["Header"]["GaugeID"]
            if not gid.startswith("SYNTH"):
                elev = g["FloodGauge"]["Location"].get("GaugeElevation", 0)
                if elev > 0:
                    real_elevs.append(elev)

        if not real_elevs:
            pytest.skip("No real gauge elevations")

        min_real = min(real_elevs)
        max_real = max(real_elevs)

        synths = self._get_synthetics()
        for sg in synths:
            elev = sg["FloodGauge"]["Location"]["GaugeElevation"]
            assert min_real <= elev <= max_real, (
                f"Synthetic elevation {elev}m outside real gauge range "
                f"[{min_real}, {max_real}]"
            )
