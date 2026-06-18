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
Tests for property hazard curve routes: basis table endpoint.

Covers:
  GET /api/v1/propertyhc/basis — basis table across all properties
"""

import json
import pytest


# ---------------------------------------------------------------------------
# GET /api/v1/propertyhc/basis
# ---------------------------------------------------------------------------

class TestPropertyhcBasis:

    def test_no_data_returns_404(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/propertyhc/basis")
        assert r.status_code == 404

    def test_no_data_status_error(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/propertyhc/basis")
        assert r.get_json()["status"] == "error"

    def test_options_returns_200(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/propertyhc/basis")
        assert r.status_code == 200

    def test_options_status_ok(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/propertyhc/basis")
        assert r.get_json()["status"] == "ok"

    def test_returns_200_with_data(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        assert r.status_code == 200

    def test_status_is_success(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        assert r.get_json()["status"] == "success"

    def test_response_has_count(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        assert "count" in r.get_json()

    def test_response_has_basis_table(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        assert "basis_table" in r.get_json()

    def test_basis_table_count_matches(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        data = r.get_json()
        assert data["count"] == len(data["basis_table"])

    def test_basis_table_length(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        assert r.get_json()["count"] == 2

    def test_basis_entry_has_property_id(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        entry = r.get_json()["basis_table"][0]
        assert "property_id" in entry

    def test_basis_entry_has_flood_count(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        entry = r.get_json()["basis_table"][0]
        assert "flood_count" in entry

    def test_basis_entry_has_avg_basis_bps(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        entry = r.get_json()["basis_table"][0]
        assert "avg_basis_bps" in entry

    def test_basis_entry_has_nearest_gauges(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        entry = r.get_json()["basis_table"][0]
        assert "nearest_gauges" in entry

    def test_basis_table_sorted_desc_by_basis(self, phc_env):
        """Results must be sorted highest avg_basis_bps first."""
        r = phc_env.get("/api/v1/propertyhc/basis")
        table = r.get_json()["basis_table"]
        bases = [e["avg_basis_bps"] for e in table]
        assert bases == sorted(bases, reverse=True)

    def test_nearest_gauge_has_gauge_id(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        entry = r.get_json()["basis_table"][0]
        if entry["nearest_gauges"]:
            assert "gauge_id" in entry["nearest_gauges"][0]

    def test_nearest_gauge_has_distance_km(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        entry = r.get_json()["basis_table"][0]
        if entry["nearest_gauges"]:
            assert "distance_km" in entry["nearest_gauges"][0]


class TestPropertyhcBasisEmpty:

    @pytest.fixture
    def phc_empty_basis(self, tmp_path, monkeypatch):
        from config import config
        data = {"metadata": {}, "summary": {}, "property_hazard_curves": {}}
        (tmp_path / "propertyhc.json").write_text(json.dumps(data))
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        return app.test_client()

    def test_empty_returns_200(self, phc_empty_basis):
        r = phc_empty_basis.get("/api/v1/propertyhc/basis")
        assert r.status_code == 200

    def test_empty_count_is_zero(self, phc_empty_basis):
        r = phc_empty_basis.get("/api/v1/propertyhc/basis")
        assert r.get_json()["count"] == 0

    def test_empty_basis_table_is_list(self, phc_empty_basis):
        r = phc_empty_basis.get("/api/v1/propertyhc/basis")
        assert isinstance(r.get_json()["basis_table"], list)
