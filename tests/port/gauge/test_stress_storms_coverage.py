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
Coverage-expansion tests for port.src.gauge.stress_storms.

Targets uncovered lines: 78-80 (_derive_intensity_category warning>=3 path),
133-134 (corrupt storms.json exception handling),
151-153 (corrupt gauge file skip),
161 (response with empty storm_id skip).
"""

import json
import pytest

from tests.port.gauge.conftest import make_gauge_file, make_response


# ---------------------------------------------------------------------------
# _derive_intensity_category — warning>=3 branch (lines 78-80)
# ---------------------------------------------------------------------------

class TestDeriveIntensityCategoryWarningPath:

    def test_negative_severe_with_three_warnings_returns_moderate(self):
        """Lines 78-79: gauges_severe < 0 (doesn't match any threshold),
        gauges_warning >= 3 → 'moderate'. This exercises the post-loop path."""
        from port.src.gauge.stress_storms import _derive_intensity_category
        assert _derive_intensity_category(-1, 3) == "moderate"

    def test_negative_severe_with_five_warnings_returns_moderate(self):
        from port.src.gauge.stress_storms import _derive_intensity_category
        assert _derive_intensity_category(-1, 5) == "moderate"

    def test_negative_severe_low_warnings_returns_baseline(self):
        """Line 80: after loop exhausted, gauges_warning < 3 → 'baseline'."""
        from port.src.gauge.stress_storms import _derive_intensity_category
        assert _derive_intensity_category(-1, 2) == "baseline"

    def test_negative_severe_zero_warnings_returns_baseline(self):
        from port.src.gauge.stress_storms import _derive_intensity_category
        assert _derive_intensity_category(-1, 0) == "baseline"

    def test_zero_severe_matches_baseline_in_loop(self):
        """gauges_severe=0 matches (0, 'baseline') in the severity table."""
        from port.src.gauge.stress_storms import _derive_intensity_category
        assert _derive_intensity_category(0, 0) == "baseline"

    def test_severe_overrides_warning(self):
        """When severe >= 1, warning count is irrelevant."""
        from port.src.gauge.stress_storms import _derive_intensity_category
        assert _derive_intensity_category(1, 10) == "moderate"


# ---------------------------------------------------------------------------
# Corrupt storms.json exception handling (lines 133-134)
# ---------------------------------------------------------------------------

class TestCorruptStormsJson:

    def test_corrupt_storms_json_does_not_crash(self, tmp_path):
        """Lines 133-134: invalid JSON in storms.json logs warning, continues."""
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        (gaugets / "GAUGE-00000001.json").write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(sid, alert=True, peak=2.0)],
        )))
        # Write corrupt storms.json
        storms_json = tmp_path / "storms.json"
        storms_json.write_text("{not valid json!!!}")
        out = tmp_path / "stress_storms"
        # Should not raise — just warn and continue
        result = generate_stress_storms(gaugets, out, storms_json_path=storms_json)
        assert out.exists() and (out / "_index.json").exists()
        assert result["total_storms"] == 1


# ---------------------------------------------------------------------------
# Corrupt gauge file skip (lines 151-153)
# ---------------------------------------------------------------------------

class TestCorruptGaugeFile:

    def test_corrupt_gauge_file_skipped(self, tmp_path):
        """Lines 151-153: unreadable gauge file is skipped with warning."""
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        # Write one valid gauge file
        sid = "STORM-aabbccdd"
        (gaugets / "GAUGE-00000001.json").write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(sid, alert=True, peak=2.0)],
        )))
        # Write one corrupt gauge file
        (gaugets / "GAUGE-00000002.json").write_text("this is not json {{{")
        out = tmp_path / "stress_storms"
        result = generate_stress_storms(gaugets, out)
        assert out.exists() and (out / "_index.json").exists()
        # The valid gauge file's storm should still appear
        assert result["total_storms"] == 1

    def test_all_corrupt_gauge_files_no_storms(self, tmp_path):
        """All gauge files corrupt → no storms (but file still written)."""
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        (gaugets / "GAUGE-00000001.json").write_text("corrupt")
        (gaugets / "GAUGE-00000002.json").write_text("also corrupt")
        out = tmp_path / "stress_storms"
        result = generate_stress_storms(gaugets, out)
        assert result["total_storms"] == 0


# ---------------------------------------------------------------------------
# Seam fallback: no gaugets files -> read per-gauge timeseries from the database
# (the Postgres backend stores gaugets as rows, not files)
# ---------------------------------------------------------------------------

class TestSeamFallback:

    def test_reads_gaugets_from_seam_when_no_files(self, tmp_path):
        """With no GAUGE-*.json files, scan reads the seam for the active catchment.

        Seeds a gauge timeseries through the seam, then runs generate_stress_storms
        against an empty directory so the file glob misses and the seam fallback
        supplies the gauge — exercised here on the file backend (and the same path
        is what makes the pipeline work on Postgres)."""
        import database
        from db_helpers import tmp_catchment
        from port.src.gauge.stress_storms import generate_stress_storms
        sid = "STORM-deadbeef"
        with tmp_catchment(tmp_path / "catchment"):
            database.save_gauge_timeseries(
                database.active_catchment(), "GAUGE-00000001",
                make_gauge_file("GAUGE-00000001",
                                [make_response(sid, alert=True, peak=2.0)]),
            )
            empty = tmp_path / "no_files"
            empty.mkdir()
            out = tmp_path / "stress_storms"
            result = generate_stress_storms(empty, out)
        assert result["total_storms"] == 1
        assert (out / f"{sid}.json").exists()

    def test_non_gauge_keys_skipped_in_seam(self, tmp_path):
        """Seam fallback only scans GAUGE-* timeseries (e.g. SYNTH-* are ignored)."""
        import database
        from db_helpers import tmp_catchment
        from port.src.gauge.stress_storms import generate_stress_storms
        with tmp_catchment(tmp_path / "catchment"):
            database.save_gauge_timeseries(
                database.active_catchment(), "SYNTH-00000001",
                make_gauge_file("SYNTH-00000001",
                                [make_response("STORM-aaaa0001", alert=True)]),
            )
            empty = tmp_path / "no_files"
            empty.mkdir()
            out = tmp_path / "stress_storms"
            with pytest.raises(FileNotFoundError):
                generate_stress_storms(empty, out)


# ---------------------------------------------------------------------------
# Empty storm_id skip (line 161)
# ---------------------------------------------------------------------------

class TestEmptyStormIdSkip:

    def test_empty_storm_id_skipped(self, tmp_path):
        """Line 160-161: responses with empty storm_id are skipped."""
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        # Build a gauge file with one valid and one empty-id response
        gauge_data = {
            "gauge_id": "GAUGE-00000001",
            "flood_simulation": {"simulation_hours": 168, "readings": []},
            "storm_responses": {
                "responses": [
                    {
                        "storm_id": "",  # empty — should be skipped
                        "base_level_m": 1.0,
                        "peak_level_m": 2.0,
                        "level_change_m": 1.0,
                        "exceeded_alert": True,
                        "exceeded_warning": False,
                        "exceeded_severe": False,
                    },
                    {
                        "storm_id": "STORM-valid001",
                        "base_level_m": 1.0,
                        "peak_level_m": 2.5,
                        "level_change_m": 1.5,
                        "exceeded_alert": True,
                        "exceeded_warning": False,
                        "exceeded_severe": False,
                    },
                ],
            },
        }
        (gaugets / "GAUGE-00000001.json").write_text(json.dumps(gauge_data))
        out = tmp_path / "stress_storms"
        result = generate_stress_storms(gaugets, out)
        data = json.loads((out / "_index.json").read_text())
        # Only the valid storm should appear
        assert result["total_storms"] == 1
        assert data["storms"][0]["storm_id"] == "STORM-valid001"

    def test_response_missing_storm_id_key_skipped(self, tmp_path):
        """storm_id key missing entirely → resp.get('storm_id', '') == '' → skip."""
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        gauge_data = {
            "gauge_id": "GAUGE-00000001",
            "flood_simulation": {"simulation_hours": 168, "readings": []},
            "storm_responses": {
                "responses": [
                    {
                        # no storm_id key at all
                        "base_level_m": 1.0,
                        "peak_level_m": 2.0,
                        "level_change_m": 1.0,
                        "exceeded_alert": True,
                    },
                    make_response("STORM-valid002", alert=True, peak=2.0),
                ],
            },
        }
        (gaugets / "GAUGE-00000001.json").write_text(json.dumps(gauge_data))
        out = tmp_path / "stress_storms"
        result = generate_stress_storms(gaugets, out)
        assert result["total_storms"] == 1
