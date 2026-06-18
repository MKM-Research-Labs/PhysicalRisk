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

"""Branch coverage for routes.trading.stress.storms.

Targets lines 53-56 (full-storm load failure + legacy fallback) and line 65
(gauge_resp lookup miss) in src/routes/trading/stress/storms.py.
"""

import json


class TestStormsLoadStormReturnsNone:
    """Line 53: when _load_stress_storm returns None for a per-storm file,
    we hit `if not full_storm: continue`.
    """

    def test_missing_storm_file_skipped(self, integration_env, monkeypatch):
        # Force _load_stress_storm to return None for any lookup
        import routes.trading.stress.storms as storms_mod

        monkeypatch.setattr(storms_mod, "_load_stress_storm", lambda sid: None)

        r = integration_env["client"].get(
            "/api/v1/trading/stress/storms?gauge_id=GAUGE-001"
        )
        assert r.status_code == 200
        data = r.get_json()
        # All per-storm loads returned None → no storms in result
        assert data["storms"] == []
        assert data["count"] == 0


class TestStormsGaugeRespMissing:
    """Line 65: gauge_resp is None (no matching response with exceeded_alert),
    so the for-loop over storms hits `continue`.
    """

    def test_gauge_resp_not_found(self, integration_env, monkeypatch):
        # Patch _load_stress_storm to return a record whose gauge_responses
        # don't include GAUGE-001 even though the index claims it had alert
        import routes.trading.stress.storms as storms_mod

        def fake_load_stress_storm(storm_id):
            return {
                "storm_id": storm_id,
                "gauge_responses": [
                    {"gauge_id": "GAUGE-OTHER", "exceeded_alert": True}
                ],
            }

        monkeypatch.setattr(
            storms_mod, "_load_stress_storm", fake_load_stress_storm
        )

        r = integration_env["client"].get(
            "/api/v1/trading/stress/storms?gauge_id=GAUGE-001"
        )
        assert r.status_code == 200
        data = r.get_json()
        # The index says GAUGE-001 had alerts, but gauge_resp lookup misses
        assert data["storms"] == []
        assert data["count"] == 0


class TestStormsLegacyFormat:
    """Lines 54-56: legacy single-file format — entry has no `gauge_ids_alert`,
    so we fall into the else branch and use idx_entry as full_storm.
    """

    def test_legacy_format(self, tmp_path, monkeypatch):
        from config import config

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "stress_storms.json").write_text(json.dumps({
            "metadata": {"generated": "legacy"},
            "storms": [
                {
                    "storm_id": "STORM-LEGACY-001",
                    "name": "Legacy Storm",
                    "intensity_category": "moderate",
                    "duration_hours": 24,
                    "peak_position": 0.5,
                    "effective_precipitation_mm": 60.0,
                    "trigger_summary": {
                        "max_trigger": "warning",
                        "gauges_severe": 0,
                    },
                    # NB: no gauge_ids_alert — legacy single-file storms
                    # carry their gauge_responses inline
                    "gauge_responses": [{
                        "gauge_id": "GAUGE-001",
                        "base_level_m": 3.0,
                        "peak_level_m": 4.6,
                        "level_change_m": 1.6,
                        "exceeded_alert": True,
                        "exceeded_warning": True,
                        "exceeded_severe": False,
                    }],
                }
            ],
        }))

        gaugets_dir = input_dir / "gaugets"
        gaugets_dir.mkdir()

        monkeypatch.setattr(config, "get_input_dir", lambda: input_dir)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: input_dir / "gaugehd")

        # Reset cache so the new file is picked up
        import routes.trading.stress._helpers as stress_helpers
        stress_helpers._stress_index_cache = None
        stress_helpers._stress_index_mtime = None

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True

        with app.test_client() as client:
            r = client.get(
                "/api/v1/trading/stress/storms?gauge_id=GAUGE-001"
            )
            assert r.status_code == 200
            data = r.get_json()
            assert data["status"] == "success"
            assert data["count"] == 1
            assert data["storms"][0]["storm_id"] == "STORM-LEGACY-001"
            assert data["storms"][0]["peak_level_m"] == 4.6


class TestStormsExceptionHandler:
    """Line 100: exception handler returns 500."""

    def test_internal_error_returns_500(self, integration_env, monkeypatch):
        import routes.trading.stress.storms as storms_mod

        def boom():
            raise RuntimeError("simulated load failure")

        monkeypatch.setattr(storms_mod, "_load_stress_storms", boom)

        r = integration_env["client"].get(
            "/api/v1/trading/stress/storms?gauge_id=GAUGE-001"
        )
        assert r.status_code == 500
        data = r.get_json()
        assert data["status"] == "error"


class TestStormsNoData:
    """Line 28-29: 404 when no stress_storms data found."""

    def test_no_data_returns_404(self, tmp_path, monkeypatch):
        from config import config

        empty_input = tmp_path / "empty"
        empty_input.mkdir()
        monkeypatch.setattr(config, "get_input_dir", lambda: empty_input)
        monkeypatch.setattr(config, "get_gaugets_dir",
                            lambda: empty_input / "gaugets")
        monkeypatch.setattr(config, "get_gaugehd_dir",
                            lambda: empty_input / "gaugehd")

        import routes.trading.stress._helpers as stress_helpers
        stress_helpers._stress_index_cache = None
        stress_helpers._stress_index_mtime = None

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True

        with app.test_client() as client:
            r = client.get("/api/v1/trading/stress/storms")
            assert r.status_code == 404
            data = r.get_json()
            assert data["status"] == "error"
            assert "not found" in data["message"]


class TestStormsGaugeNotInAlert:
    """Line 49: gauge_id not in gauge_ids_alert → continue (skip storm)."""

    def test_gauge_not_in_alert_list(self, integration_env):
        # GAUGE-999 isn't in any storm's gauge_ids_alert in SHARED_STORM_DATA
        r = integration_env["client"].get(
            "/api/v1/trading/stress/storms?gauge_id=GAUGE-999"
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["count"] == 0
        assert data["storms"] == []
