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

"""Direct coverage for financial_basis loader helpers — the defensive
exception branches that swallow malformed JSON (lines 120-121, 140-141).

Catchment-agnostic: every file is synthesised inside tmp_path and
config paths are monkeypatched, so no real data/ is touched.
"""

import json

from routes.propertyts import financial_basis as fb


class TestAccumulateSynthData:

    def test_groups_by_synth_gauge_and_skips_non_prop(self, tmp_path):
        """Properties are grouped by their controlling synthetic gauge; stray
        non-``PROP-`` records in the collection are skipped (line 144)."""
        import database
        from db_helpers import tmp_catchment
        with tmp_catchment(tmp_path, catchment=fb.config.catchment_id):
            catchment = database.active_catchment()
            database.save_property_timeseries(catchment, "PROP-001", {
                "property_id": "PROP-001",
                "nearest_gauges": [{"gauge_id": "SYNTH-1"}, {"gauge_id": "GAUGE-1"}],
                "flood_events": [{"storm_id": "STORM-1", "flooded": True,
                                  "damage_ratio": 0.2, "flood_depth_m": 0.4,
                                  "exceeded_severe": True}],
            })
            # Stray non-PROP keyed record (e.g. the portfolio summary) → skipped.
            database.save_property_timeseries(catchment, "portfolio_flood_summary",
                                              {"x": 1})
            out = fb._accumulate_synth_data("STORM-1", {})
        assert set(out) == {"SYNTH-1"}
        acc = out["SYNTH-1"]
        assert acc["gauge_type"] == "Synthetic"
        assert acc["properties_linked"] == 1
        assert acc["properties_flooded"] == 1
        assert acc["real_gauge_id"] == "GAUGE-1"


class TestLoadGaugeThresholds:

    def test_missing_file_returns_empty(self, tmp_path):
        # Bind an isolated catchment so the seam is empty on both backends (pg's real
        # thames now has curves — monkeypatching get_input_dir alone doesn't isolate it).
        from db_helpers import tmp_catchment
        with tmp_catchment(tmp_path, catchment=fb.config.catchment_id):
            assert fb._load_gauge_thresholds() == {}

    def test_valid_file_parsed(self, tmp_path):
        import database
        from db_helpers import tmp_catchment
        with tmp_catchment(tmp_path, catchment=fb.config.catchment_id):
            database.save_gauge_hazard_curves(database.active_catchment(), {
                "hazard_curves": {"G1": {"gauge_name": "One",
                                         "flood_alert_m": 1.0, "elevation_m": 5}}})
            out = fb._load_gauge_thresholds()
        assert out["G1"]["gauge_name"] == "One"
        assert out["G1"]["alert_m"] == 1.0

    def test_malformed_file_swallowed(self, tmp_path):
        """Lines 120-121: corrupt gaugehc.json → warning + empty dict."""
        from db_helpers import tmp_catchment
        with tmp_catchment(tmp_path, catchment=fb.config.catchment_id):
            (tmp_path / "gaugehc.json").write_text("{not valid json")
            assert fb._load_gauge_thresholds() == {}


class TestLoadStormGaugePeaks:

    def test_missing_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(fb.config, "get_input_dir", lambda: tmp_path)
        assert fb._load_storm_gauge_peaks("STORM-X") == {}

    def test_valid_file_parsed(self, tmp_path):
        import database
        from db_helpers import tmp_catchment
        with tmp_catchment(tmp_path, catchment=fb.config.catchment_id):
            database.save_stress_storm(database.active_catchment(), "STORM-1", {
                "gauge_responses": [{"gauge_id": "G1", "peak_level_m": 2.5,
                                     "exceeded_severe": True}]})
            out = fb._load_storm_gauge_peaks("STORM-1")
        assert out["G1"]["peak_level_m"] == 2.5
        assert out["G1"]["exceeded_severe"] is True

    def test_malformed_file_swallowed(self, tmp_path, monkeypatch):
        """Lines 140-141: corrupt storm file → warning + empty dict."""
        monkeypatch.setattr(fb.config, "get_input_dir", lambda: tmp_path)
        sdir = tmp_path / "stress_storms"
        sdir.mkdir()
        (sdir / "STORM-1.json").write_text("{bad json")
        assert fb._load_storm_gauge_peaks("STORM-1") == {}
