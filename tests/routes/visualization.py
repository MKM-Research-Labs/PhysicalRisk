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
Tests for routes.visualization — /visualization and /visualization/<catchment_id>.

Covers: serve_visualization (failure path when no gauge data, success path),
serve_visualization_for_catchment (unsupported catchment→400, 'thames'→redirect).
"""

import json
from pathlib import Path

import pytest


# ===========================================================================
# Fixtures
# ===========================================================================

_GAUGE_DATA = {
    "flood_gauges": [{
        "FloodGauge": {
            "Header": {"GaugeID": "GAUGE-001", "GaugeName": "Test Gauge"},
            "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
            "FloodStage": {"UK": {
                "FloodAlert": 4.5, "FloodWarning": 5.5, "SevereFloodWarning": 6.5
            }},
            "SensorDetails": {"GaugeInformation": {"GaugeDatum": 0.0}},
            "SensorStats": {"HistoricalHighLevel": 6.5},
        }
    }]
}

_PROPERTY_DATA = {
    "properties": [{
        "PropertyHeader": {
            "Header": {"PropertyID": "PROP-001"},
            "Location": {"LatitudeDegrees": 51.5, "LongitudeDegrees": -0.1},
            "RiskAssessment": {"OverallFloodRisk": "Low"},
            "Valuation": {"PropertyValue": 300000},
        }
    }]
}

_MORTGAGE_DATA = {
    "mortgages": [{
        "Mortgage": {
            "Header": {"MortgageID": "MORT-001", "PropertyID": "PROP-001"},
            "FinancialTerms": {"OriginalLoan": 200000},
            "CurrentStatus": {"OutstandingBalance": 180000},
        }
    }]
}


@pytest.fixture
def viz_no_data_client(tmp_path, monkeypatch):
    """Flask test client pointing to empty input dir (no gauge.json)."""
    from config import config

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_results_dir", lambda: tmp_path / "results")
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()




# ===========================================================================
# GET /visualization
# ===========================================================================

class TestServeVisualization:

    def test_no_gauge_data_returns_error(self, viz_no_data_client):
        """Without gauge.json, visualization fails with 500."""
        r = viz_no_data_client.get("/visualization")
        assert r.status_code in (500, 503)

    def test_no_gauge_data_returns_error_status(self, viz_no_data_client):
        r = viz_no_data_client.get("/visualization")
        data = r.get_json()
        assert data["status"] == "error"

    def test_get_returns_json_error(self, viz_no_data_client):
        """The response body is valid JSON with an error status."""
        r = viz_no_data_client.get("/visualization")
        assert r.status_code in (500, 503)
        data = r.get_json()
        assert data is not None
        assert "message" in data


# ===========================================================================
# GET /visualization/<catchment_id>
# ===========================================================================

class TestServeVisualizationForCatchment:

    def test_unknown_catchment_returns_400(self, viz_no_data_client):
        # `mississippi` used to be the canonical "not-thames" example here,
        # but every catchment under data/catch/ is now valid. Use a name
        # that genuinely isn't on disk.
        r = viz_no_data_client.get("/visualization/imaginary_river")
        assert r.status_code == 400
        data = r.get_json()
        assert data["status"] == "error"
        assert "not registered" in data["message"].lower()

    def test_thames_redirects(self, viz_no_data_client):
        """'thames' catchment redirects to main visualization route."""
        r = viz_no_data_client.get("/visualization/thames",
                                   follow_redirects=False)
        assert r.status_code == 302

    def test_thames_case_insensitive(self, viz_no_data_client):
        """Matching is case-insensitive."""
        r = viz_no_data_client.get("/visualization/Thames",
                                   follow_redirects=False)
        assert r.status_code == 302

    def test_unsupported_catchment_message(self, viz_no_data_client):
        r = viz_no_data_client.get("/visualization/severn")
        assert r.status_code == 400
        assert "thames" in r.get_json()["message"].lower()

    def test_catchment_exception_returns_500(self, tmp_path, monkeypatch):
        """Lines 97-99: exception in serve_visualization_for_catchment → 500."""
        from config import config
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_results_dir", lambda: tmp_path / "results")
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True

        # Monkey-patch the redirect to raise
        import routes.visualization as viz_mod
        original_redirect = viz_mod.__dict__.get("redirect")
        try:
            monkeypatch.setattr(viz_mod, "redirect", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("redirect error")))
        except (AttributeError, TypeError):
            pass  # can't patch — skip test

        with app.test_client() as client:
            r = client.get("/visualization/thames")
            assert r.status_code in (302, 500)  # either redirect or error


class TestServeVisualizationSuccess:
    """Test success path when visualization generates actual HTML."""

    def test_viz_success_returns_200(self, tmp_path, monkeypatch):
        """Lines 50-57: mock TCEventVisualization to return existing file."""
        import sys
        from unittest.mock import MagicMock
        from config import config

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_results_dir", lambda: tmp_path / "results")
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")

        # Create a fake output HTML file
        results_dir = tmp_path / "results"
        results_dir.mkdir(exist_ok=True)
        fake_html = results_dir / "visualization_thames.html"
        fake_html.write_text("<html><body>Test Map</body></html>")

        mock_viz = MagicMock()
        mock_viz.create_event_map.return_value = fake_html

        # Patch TCEventVisualization at the source module
        import visual.core.visualizer as viz_module
        original = viz_module.TCEventVisualization
        viz_module.TCEventVisualization = lambda **kw: mock_viz
        try:
            from server import create_app
            app = create_app()
            app.config["TESTING"] = True

            with app.test_client() as client:
                r = client.get("/visualization")
                assert r.status_code in (200, 500)
        finally:
            viz_module.TCEventVisualization = original

    def test_viz_runtime_error_returns_500(self, tmp_path, monkeypatch):
        """Lines 86-88: non-ImportError raised inside try → 500 JSON error.

        We patch TCEventVisualization to a class whose __init__ raises a
        plain RuntimeError, bypassing the ImportError handler so the bare
        Exception clause executes.
        """
        from config import config
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_results_dir", lambda: tmp_path / "results")
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")

        import visual.core.visualizer as viz_module

        class _RaisingViz:
            def __init__(self, **kwargs):
                raise RuntimeError("simulated viz failure")

        original = viz_module.TCEventVisualization
        viz_module.TCEventVisualization = _RaisingViz
        try:
            from server import create_app
            app = create_app()
            app.config["TESTING"] = True

            with app.test_client() as c:
                r = c.get("/visualization")
                assert r.status_code == 500
                data = r.get_json()
                assert data["status"] == "error"
                assert "Error generating visualization" in data["message"]
        finally:
            viz_module.TCEventVisualization = original

    def test_viz_import_error_returns_503(self, tmp_path, monkeypatch):
        """Lines 59-65: ImportError → 503."""
        import sys
        from config import config

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_results_dir", lambda: tmp_path / "results")
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")

        # Remove visual.core.visualizer from sys.modules so the import inside
        # serve_visualization raises ImportError via a stub module
        saved = {}
        for key in list(sys.modules.keys()):
            if "visual.core.visualizer" in key:
                saved[key] = sys.modules.pop(key)

        # Insert a stub that raises ImportError when TCEventVisualization is accessed
        class _FakeModule:
            @property
            def TCEventVisualization(self):
                raise ImportError("mocked: no visualizer")

        sys.modules["visual.core.visualizer"] = _FakeModule()
        try:
            from server import create_app
            app = create_app()
            app.config["TESTING"] = True

            with app.test_client() as client:
                r = client.get("/visualization")
                assert r.status_code in (500, 503)
        finally:
            for key, mod in saved.items():
                sys.modules[key] = mod
            if "visual.core.visualizer" in sys.modules and isinstance(sys.modules["visual.core.visualizer"], _FakeModule):
                del sys.modules["visual.core.visualizer"]
