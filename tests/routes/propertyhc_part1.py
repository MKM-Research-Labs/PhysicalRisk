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
Tests for property hazard curve routes: summary and per-property hazard.

Covers:
  GET /api/v1/propertyhc/summary     -- portfolio-wide hazard summary
  GET /api/v1/properties/<id>/hazard -- per-property hazard + PRS + basis
"""

import json
import pytest

from .conftest import SAMPLE_PROPERTYHC


# ---------------------------------------------------------------------------
# GET /api/v1/propertyhc/summary
# ---------------------------------------------------------------------------

class TestPropertyhcSummary:

    def test_no_data_returns_404(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/propertyhc/summary")
        assert r.status_code == 404

    def test_no_data_status_is_error(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/propertyhc/summary")
        assert r.get_json()["status"] == "error"

    def test_no_data_message_mentions_command(self, phc_client_no_data):
        msg = r.get_json()["message"] if (r := phc_client_no_data.get("/api/v1/propertyhc/summary")) else ""
        r = phc_client_no_data.get("/api/v1/propertyhc/summary")
        assert "port" in r.get_json()["message"].lower() or "propertyhc" in r.get_json()["message"].lower()

    def test_options_returns_200(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/propertyhc/summary")
        assert r.status_code == 200

    def test_options_status_ok(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/propertyhc/summary")
        assert r.get_json()["status"] == "ok"

    def test_returns_200_with_data(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        assert r.status_code == 200

    def test_status_is_success(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        assert r.get_json()["status"] == "success"

    def test_response_has_data_key(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        assert "data" in r.get_json()

    def test_response_has_metadata(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        assert "metadata" in r.get_json()["data"]

    def test_response_has_summary(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        assert "summary" in r.get_json()["data"]

    def test_response_has_distribution(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        assert "distribution" in r.get_json()["data"]

    def test_distribution_num_properties(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        dist = r.get_json()["data"]["distribution"]
        assert dist["num_properties"] == 2

    def test_distribution_avg_basis_bps(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        dist = r.get_json()["data"]["distribution"]
        assert "avg_basis_bps" in dist
        assert dist["avg_basis_bps"] >= 0

    def test_distribution_avg_flood_count(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        dist = r.get_json()["data"]["distribution"]
        assert "avg_flood_count" in dist
        assert dist["avg_flood_count"] > 0

    def test_distribution_max_depth_m(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        dist = r.get_json()["data"]["distribution"]
        assert "max_depth_m" in dist
        assert dist["max_depth_m"] > 0


class TestPropertyhcSummaryEmpty:
    """Summary when all properties have no flood events or summary data."""

    @pytest.fixture
    def phc_empty_curves(self, tmp_path, monkeypatch):
        from config import config
        data = {
            "metadata": {},
            "summary": {},
            "property_hazard_curves": {},
        }
        (tmp_path / "propertyhc.json").write_text(json.dumps(data))
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        return app.test_client()

    def test_empty_curves_returns_200(self, phc_empty_curves):
        r = phc_empty_curves.get("/api/v1/propertyhc/summary")
        assert r.status_code == 200

    def test_empty_curves_num_properties_is_zero(self, phc_empty_curves):
        r = phc_empty_curves.get("/api/v1/propertyhc/summary")
        assert r.get_json()["data"]["distribution"]["num_properties"] == 0

    def test_empty_curves_avg_flood_count_is_zero(self, phc_empty_curves):
        r = phc_empty_curves.get("/api/v1/propertyhc/summary")
        assert r.get_json()["data"]["distribution"]["avg_flood_count"] == 0


# ---------------------------------------------------------------------------
# GET /api/v1/properties/<prop_id>/hazard
# ---------------------------------------------------------------------------

class TestPropertyHazard:

    def test_no_data_returns_404(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/properties/PROP-001/hazard")
        assert r.status_code == 404

    def test_no_data_status_error(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/properties/PROP-001/hazard")
        assert r.get_json()["status"] == "error"

    def test_options_returns_200(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/properties/PROP-001/hazard")
        assert r.status_code == 200

    def test_options_status_ok(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/properties/PROP-001/hazard")
        assert r.get_json()["status"] == "ok"

    def test_unknown_property_returns_404(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-GHOST/hazard")
        assert r.status_code == 404

    def test_unknown_property_status_error(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-GHOST/hazard")
        assert r.get_json()["status"] == "error"

    def test_unknown_property_message_contains_id(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-GHOST/hazard")
        assert "PROP-GHOST" in r.get_json()["message"]

    def test_known_property_returns_200(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-001/hazard")
        assert r.status_code == 200

    def test_known_property_status_success(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-001/hazard")
        assert r.get_json()["status"] == "success"

    def test_response_has_data_key(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-001/hazard")
        assert "data" in r.get_json()

    def test_data_contains_property_id(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-001/hazard")
        assert r.get_json()["data"]["property_id"] == "PROP-001"

    def test_data_contains_hazard_curve(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-001/hazard")
        assert "hazard_curve" in r.get_json()["data"]

    def test_data_contains_summary(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-001/hazard")
        assert "summary" in r.get_json()["data"]

    def test_data_contains_nearest_gauges(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-001/hazard")
        assert "nearest_gauges" in r.get_json()["data"]

    def test_second_property_also_works(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-002/hazard")
        assert r.status_code == 200
        assert r.get_json()["data"]["property_id"] == "PROP-002"
