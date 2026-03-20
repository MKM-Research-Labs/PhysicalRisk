# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for routes/propertyts/core.py — summary, floods, property storms endpoints."""

import pytest


# ===========================================================================
# /propertyts/summary
# ===========================================================================

class TestSummary:

    def test_no_data_returns_404(self, pts_client_no_data):
        r = pts_client_no_data.get("/api/v1/propertyts/summary")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_with_data_returns_success(self, pts_env):
        r = pts_env["client"].get("/api/v1/propertyts/summary")
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_options_returns_ok(self, pts_client_no_data):
        r = pts_client_no_data.options("/api/v1/propertyts/summary")
        assert r.status_code == 200


# ===========================================================================
# /properties/<id>/floods
# ===========================================================================

class TestPropertyFloods:

    def test_missing_property_returns_404(self, pts_client_no_data):
        r = pts_client_no_data.get("/api/v1/properties/PROP-GHOST/floods")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_existing_property_returns_success(self, pts_env):
        r = pts_env["client"].get("/api/v1/properties/PROP-001/floods")
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_include_readings_false_strips_readings(self, pts_env):
        r = pts_env["client"].get("/api/v1/properties/PROP-001/floods?include_readings=false")
        data = r.get_json()["data"]
        for event in data.get("flood_events", []):
            assert "readings" not in event

    def test_include_readings_true_keeps_readings(self, pts_env):
        r = pts_env["client"].get("/api/v1/properties/PROP-001/floods?include_readings=true")
        data = r.get_json()["data"]
        assert "readings" in data["flood_events"][0]
        assert len(data["flood_events"][0]["readings"]) == 168

    def test_options_returns_ok(self, pts_client_no_data):
        r = pts_client_no_data.options("/api/v1/properties/PROP-001/floods")
        assert r.status_code == 200


# ===========================================================================
# /properties/<prop_id>/storms
# ===========================================================================

class TestPropertyStorms:

    def test_missing_property_returns_404(self, pts_client_no_data):
        r = pts_client_no_data.get("/api/v1/properties/PROP-GHOST/storms")
        assert r.status_code == 404

    def test_options_returns_ok(self, pts_client_no_data):
        r = pts_client_no_data.options("/api/v1/properties/PROP-001/storms")
        assert r.status_code == 200

    def test_existing_property_returns_success(self, pts_env):
        r = pts_env["client"].get("/api/v1/properties/PROP-001/storms")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["property_id"] == "PROP-001"

    def test_response_has_flood_events(self, pts_env):
        r = pts_env["client"].get("/api/v1/properties/PROP-001/storms")
        data = r.get_json()
        assert "flood_events" in data
        assert len(data["flood_events"]) >= 1

    def test_response_has_nearest_gauges(self, pts_env):
        r = pts_env["client"].get("/api/v1/properties/PROP-001/storms")
        data = r.get_json()
        assert "nearest_gauges" in data

    def test_flood_events_tagged_with_sequence_type(self, pts_env):
        r = pts_env["client"].get("/api/v1/properties/PROP-001/storms")
        events = r.get_json()["flood_events"]
        assert len(events) >= 1
        assert "sequence_type" in events[0]

    def test_nearest_gauges_enriched_with_flood_stages(self, pts_env):
        r = pts_env["client"].get("/api/v1/properties/PROP-001/storms")
        gauges = r.get_json()["nearest_gauges"]
        assert len(gauges) >= 1
        assert "flood_stages" in gauges[0]

    def test_response_has_property_info(self, pts_env):
        r = pts_env["client"].get("/api/v1/properties/PROP-001/storms")
        data = r.get_json()
        assert "property_info" in data
        assert "elevation_m" in data["property_info"]
