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
Unit tests for generate_stress_storms — core generation, gauge_id injection,
and return value.

Updated for the directory-based output (stress_storms/ with per-storm JSON
files + _index.json) that replaced the single stress_storms.json.
"""

import json
import pytest

from tests.port.gauge.conftest import make_gauge_file, make_response


# ---------------------------------------------------------------------------
# Core generation behaviour
# ---------------------------------------------------------------------------

class TestGenerateStressStorms:

    def test_file_not_found_when_gaugets_empty(self, tmp_path):
        """Empty gaugets directory must raise FileNotFoundError."""
        from port.src.gauge.stress_storms import generate_stress_storms
        empty = tmp_path / "gaugets"
        empty.mkdir()
        out_dir = tmp_path / "stress_storms"
        with pytest.raises(FileNotFoundError):
            generate_stress_storms(empty, out_dir)

    def test_writes_index_and_storm_files(self, tmp_path):
        """Output directory must contain _index.json and per-storm files."""
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        gf = gaugets / "GAUGE-00000001.json"
        gf.write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(sid, alert=True, peak=2.0)],
        )))
        out_dir = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out_dir)
        assert (out_dir / "_index.json").exists()
        assert (out_dir / f"{sid}.json").exists()

    def test_index_has_required_top_level_keys(self, tmp_path):
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        gf = gaugets / "GAUGE-00000001.json"
        gf.write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(sid, alert=True, peak=2.0)],
        )))
        out_dir = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out_dir)
        data = json.loads((out_dir / "_index.json").read_text())
        for key in ("description", "generated_at", "storm_id_prefix", "total_storms", "storms"):
            assert key in data, f"Missing top-level key: {key}"

    def test_total_storms_matches_list_length(self, tmp_path):
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        for i, sid in enumerate(["STORM-aaaa0001", "STORM-aaaa0002"]):
            gf = gaugets / f"GAUGE-0000000{i}.json"
            gf.write_text(json.dumps(make_gauge_file(
                f"GAUGE-0000000{i}",
                [make_response(sid, alert=True, peak=2.0)],
            )))
        out_dir = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out_dir)
        data = json.loads((out_dir / "_index.json").read_text())
        assert data["total_storms"] == len(data["storms"])

    def test_sub_alert_storms_excluded(self, tmp_path):
        """Storms where no gauge exceeded alert must NOT appear in output."""
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        gf = gaugets / "GAUGE-00000001.json"
        gf.write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response("STORM-sub00001", alert=False, peak=0.5)],
        )))
        out_dir = tmp_path / "stress_storms"
        result = generate_stress_storms(gaugets, out_dir)
        assert result["total_storms"] == 0

    def test_storm_id_prefix_uses_config_constant(self, tmp_path):
        from port.src.gauge.stress_storms import generate_stress_storms
        from config.port import STORM_ID_PREFIX
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        gf = gaugets / "GAUGE-00000001.json"
        gf.write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(f"{STORM_ID_PREFIX}-testonly", alert=True, peak=2.0)],
        )))
        out_dir = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out_dir)
        data = json.loads((out_dir / "_index.json").read_text())
        assert data["storm_id_prefix"] == STORM_ID_PREFIX

    def test_index_has_gauge_ids_alert(self, tmp_path):
        """Each index entry must have gauge_ids_alert for directory-based filtering."""
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        gf = gaugets / "GAUGE-00000001.json"
        gf.write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(sid, alert=True, peak=2.0)],
        )))
        out_dir = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out_dir)
        data = json.loads((out_dir / "_index.json").read_text())
        entry = data["storms"][0]
        assert "gauge_ids_alert" in entry
        assert "GAUGE-00000001" in entry["gauge_ids_alert"]

    def test_per_storm_file_has_gauge_responses(self, tmp_path):
        """Individual storm files must contain the full gauge_responses array."""
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        gf = gaugets / "GAUGE-00000001.json"
        gf.write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(sid, alert=True, peak=2.0)],
        )))
        out_dir = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out_dir)
        storm = json.loads((out_dir / f"{sid}.json").read_text())
        assert "gauge_responses" in storm
        assert len(storm["gauge_responses"]) == 1


# ---------------------------------------------------------------------------
# gauge_id injection
# ---------------------------------------------------------------------------

class TestGaugeIdInjection:
    """gauge_id from the top-level file field must be injected into each response."""

    def test_gauge_id_present_in_all_responses(self, tmp_path):
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        gf = gaugets / "GAUGE-deadbeef.json"
        resp = make_response(sid, alert=True, peak=2.0)
        assert "gauge_id" not in resp  # pre-condition
        gf.write_text(json.dumps(make_gauge_file("GAUGE-deadbeef", [resp])))
        out_dir = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out_dir)
        storm = json.loads((out_dir / f"{sid}.json").read_text())
        for gr in storm["gauge_responses"]:
            assert gr.get("gauge_id") == "GAUGE-deadbeef", (
                f"Expected gauge_id='GAUGE-deadbeef', got {gr.get('gauge_id')!r}"
            )

    def test_multiple_gauges_have_correct_ids(self, tmp_path):
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        for gid in ["GAUGE-00000001", "GAUGE-00000002", "GAUGE-00000003"]:
            gf = gaugets / f"{gid}.json"
            gf.write_text(json.dumps(make_gauge_file(gid, [make_response(sid, alert=True, peak=2.0)])))
        out_dir = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out_dir)
        storm = json.loads((out_dir / f"{sid}.json").read_text())
        found_ids = {gr["gauge_id"] for gr in storm["gauge_responses"]}
        assert found_ids == {"GAUGE-00000001", "GAUGE-00000002", "GAUGE-00000003"}


# ---------------------------------------------------------------------------
# Return value
# ---------------------------------------------------------------------------

class TestReturnValue:

    def test_returns_dict_with_total_storms(self, tmp_path):
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        (gaugets / "GAUGE-00000001.json").write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(sid, alert=True, peak=2.0)],
        )))
        out_dir = tmp_path / "stress_storms"
        result = generate_stress_storms(gaugets, out_dir)
        assert isinstance(result, dict)
        assert "total_storms" in result
        assert result["total_storms"] == 1

    def test_returns_elapsed_s(self, tmp_path):
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        (gaugets / "GAUGE-00000001.json").write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(sid, alert=True, peak=2.0)],
        )))
        out_dir = tmp_path / "stress_storms"
        result = generate_stress_storms(gaugets, out_dir)
        assert "elapsed_s" in result
        assert result["elapsed_s"] >= 0
