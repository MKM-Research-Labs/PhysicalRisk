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

"""Tests for routes/propertyts/core.py — storm listing and missing-file edge cases. (part 1 of 2)"""

import json

import pytest


# ===========================================================================
# /propertyts/storms
# ===========================================================================

class TestListFloodStorms:

    def test_no_storms_file_returns_404(self, pts_client_no_data):
        r = pts_client_no_data.get("/api/v1/propertyts/storms")
        assert r.status_code == 404

    def test_with_data_returns_success(self, pts_env):
        r = pts_env["client"].get("/api/v1/propertyts/storms")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert "storms" in data

    def test_options_returns_ok(self, pts_client_no_data):
        r = pts_client_no_data.options("/api/v1/propertyts/storms")
        assert r.status_code == 200

    def test_storms_list_count(self, pts_env):
        r = pts_env["client"].get("/api/v1/propertyts/storms")
        data = r.get_json()
        assert data["count"] >= 1

    def test_storm_has_expected_fields(self, pts_env):
        r = pts_env["client"].get("/api/v1/propertyts/storms")
        storms = r.get_json()["storms"]
        assert len(storms) >= 1
        s = storms[0]
        assert "storm_id" in s
        assert "properties_flooded" in s
        assert "gauges_severe" in s
        assert "max_depth_m" in s

    def test_storms_sorted_by_estimated_damage(self, pts_env):
        """Default sort: storms by estimated_damage descending (most costly first)."""
        r = pts_env["client"].get("/api/v1/propertyts/storms")
        storms = r.get_json()["storms"]
        damages = [s["estimated_damage"] for s in storms]
        assert damages == sorted(damages, reverse=True)

    def test_storm_name_from_intensity_category(self, pts_env):
        """Storm name is capitalised intensity_category, not empty."""
        r = pts_env["client"].get("/api/v1/propertyts/storms")
        storms = r.get_json()["storms"]
        for s in storms:
            if s["intensity_category"]:
                assert s["name"] == s["intensity_category"].capitalize()

    def test_response_includes_total_storms(self, pts_env):
        """Response must include total_storms (full catalogue count)."""
        r = pts_env["client"].get("/api/v1/propertyts/storms")
        data = r.get_json()
        assert "total_storms" in data
        assert isinstance(data["total_storms"], int)
        assert data["total_storms"] >= data["count"]

    def test_storm_has_estimated_damage(self, pts_env):
        """Each storm must include estimated_damage field."""
        r = pts_env["client"].get("/api/v1/propertyts/storms")
        storms = r.get_json()["storms"]
        for s in storms:
            assert "estimated_damage" in s
            assert isinstance(s["estimated_damage"], (int, float))

    def test_default_sort_is_by_damage(self, pts_env):
        """Default sort (no ?sort= param) orders by estimated_damage desc."""
        r = pts_env["client"].get("/api/v1/propertyts/storms")
        storms = r.get_json()["storms"]
        damages = [s["estimated_damage"] for s in storms]
        assert damages == sorted(damages, reverse=True)

    def test_sort_by_flooded(self, pts_env):
        """?sort=flooded orders by properties_flooded desc."""
        r = pts_env["client"].get("/api/v1/propertyts/storms?sort=flooded")
        storms = r.get_json()["storms"]
        counts = [s["properties_flooded"] for s in storms]
        assert counts == sorted(counts, reverse=True)

    def test_sort_by_severity(self, pts_env):
        """?sort=severity orders by gauges_severe desc."""
        r = pts_env["client"].get("/api/v1/propertyts/storms?sort=severity")
        storms = r.get_json()["storms"]
        counts = [s["gauges_severe"] for s in storms]
        assert counts == sorted(counts, reverse=True)
