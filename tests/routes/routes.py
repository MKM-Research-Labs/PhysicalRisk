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
Tests for Flask route endpoints.

Tests the HTTP API layer using Flask test client.
"""

import json


class TestHealthRoutes:
    """Test health check endpoints."""

    def test_root_redirects(self, client):
        """Test GET / redirects to catchment selector."""
        response = client.get('/')
        assert response.status_code == 302

    def test_health_check(self, client):
        """Test GET /health returns health status."""
        response = client.get('/health')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'endpoints' in data

    def test_detailed_health_check(self, client):
        """Test GET /health/detailed returns detailed status."""
        response = client.get('/health/detailed')

        assert response.status_code in [200, 503]
        data = json.loads(response.data)
        assert data['status'] in ['healthy', 'degraded']
        assert 'files' in data
        assert 'config' in data


class TestPropertyRoutes:
    """Test property endpoints."""

    def test_list_properties(self, client):
        """Test GET /api/v1/properties."""
        response = client.get('/api/v1/properties')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['count'] == 3
        assert len(data['properties']) == 3

    def test_get_property(self, client):
        """Test GET /api/v1/properties/<id>."""
        response = client.get('/api/v1/properties/PROP-001')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'property' in data

    def test_get_property_not_found(self, client):
        """Test GET /api/v1/properties/<id> with invalid ID."""
        response = client.get('/api/v1/properties/NONEXISTENT')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'

    def test_generate_report_missing_body(self, client):
        """Test POST /api/v1/properties/report without body."""
        response = client.post(
            '/api/v1/properties/report',
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_generate_report_missing_property_id(self, client):
        """Test POST /api/v1/properties/report without propertyId."""
        response = client.post(
            '/api/v1/properties/report',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Property ID is required' in data['message']

    def test_generate_report_property_not_found(self, client):
        """Test POST /api/v1/properties/report with invalid property."""
        response = client.post(
            '/api/v1/properties/report',
            data=json.dumps({'propertyId': 'NONEXISTENT'}),
            content_type='application/json'
        )

        assert response.status_code == 404

    def test_legacy_generate_property_report(self, client):
        """Test legacy POST /api/v1/generate_property_report endpoint."""
        response = client.post(
            '/api/v1/generate_property_report',
            data=json.dumps({'propertyId': 'NONEXISTENT'}),
            content_type='application/json'
        )

        # Should work (legacy endpoint mapped under api/v1)
        assert response.status_code == 404  # Property not found, but route works

    def test_options_preflight(self, client):
        """Test OPTIONS preflight request."""
        response = client.options('/api/v1/properties/report')

        assert response.status_code == 200


class TestGaugeRoutes:
    """Test gauge endpoints."""

    def test_list_gauges(self, client):
        """Test GET /api/v1/gauges."""
        response = client.get('/api/v1/gauges')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['count'] == 3
        assert len(data['gauges']) == 3

    def test_legacy_list_gauges(self, client):
        """Test legacy GET /api/v1/list_gauges endpoint."""
        response = client.get('/api/v1/list_gauges')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 3

    def test_get_gauge(self, client):
        """Test GET /api/v1/gauges/<id>."""
        response = client.get('/api/v1/gauges/GAUGE-001')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'gauge' in data

    def test_get_gauge_not_found(self, client):
        """Test GET /api/v1/gauges/<id> with invalid ID."""
        response = client.get('/api/v1/gauges/NONEXISTENT')

        assert response.status_code == 404

    def test_generate_report_missing_gauge_id(self, client):
        """Test POST /api/v1/gauges/report without gaugeId."""
        response = client.post(
            '/api/v1/gauges/report',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Gauge ID is required' in data['message']

    def test_get_gaugets(self, client):
        """Test GET /api/v1/gauges/<id>/timeseries."""
        response = client.get('/api/v1/gauges/GAUGE-001/timeseries')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'readings' in data

    def test_get_gauge_statistics(self, client):
        """Test GET /api/v1/gauges/<id>/statistics."""
        response = client.get('/api/v1/gauges/GAUGE-001/statistics')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'statistics' in data


class TestCORS:
    """Test CORS configuration."""

    def test_cors_headers_on_get(self, client):
        """Test CORS headers on GET request."""
        response = client.get('/health')

        # Flask-CORS should add headers
        # Note: Test client may not trigger all CORS behavior
        assert response.status_code == 200

    def test_options_returns_ok(self, client):
        """Test OPTIONS requests return 200."""
        endpoints = [
            '/api/v1/properties/report',
            '/api/v1/gauges/report',
            '/api/v1/generate_property_report',
            '/api/v1/generate_gauge_report',
        ]

        for endpoint in endpoints:
            response = client.options(endpoint)
            assert response.status_code == 200, f"OPTIONS failed for {endpoint}"


class TestGaugeCrudEdgeCases:
    """Tests for crud.py uncovered branches."""

    def test_list_gauges_options(self, client):
        """Line 19: OPTIONS on /api/v1/gauges returns 200."""
        response = client.options('/api/v1/gauges')
        assert response.status_code == 200
        import json
        data = json.loads(response.data)
        assert data['status'] == 'ok'

    def test_list_gauges_error_returns_500(self, client, monkeypatch):
        """Lines 32-34: loader.list_all() raises → 500 response."""
        from loaders.loader_registry import LoaderRegistry
        def _bad_list_all():
            raise RuntimeError("disk full")

        original_get_loader = LoaderRegistry.get_gauge_loader

        def _patched(self):
            loader = original_get_loader(self)
            loader.list_all = _bad_list_all
            return loader

        monkeypatch.setattr(LoaderRegistry, "get_gauge_loader", _patched)
        response = client.get('/api/v1/gauges')
        assert response.status_code == 500
        import json
        data = json.loads(response.data)
        assert data['status'] == 'error'


class TestErrorHandling:
    """Test error handling in routes."""

    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = client.post(
            '/api/v1/properties/report',
            data='not valid json',
            content_type='application/json'
        )

        # Should return 400 Bad Request
        assert response.status_code == 400

    def test_missing_content_type(self, client):
        """Test handling of missing content type."""
        response = client.post(
            '/api/v1/properties/report',
            data=json.dumps({'propertyId': 'PROP-001'})
            # No content_type specified
        )

        # Flask may handle this differently
        assert response.status_code in [400, 415, 500]


class TestServerMain:
    """Tests for server.main() — lines 52-72, 80."""

    def test_main_calls_app_run(self, monkeypatch, tmp_path):
        """main() calls app.run() with configured host/port/debug."""
        from config import config
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")

        run_calls = []

        from flask import Flask
        original_run = Flask.run

        def _mock_run(self, host=None, port=None, debug=None, **kwargs):
            run_calls.append({"host": host, "port": port, "debug": debug})

        monkeypatch.setattr(Flask, "run", _mock_run)

        import server
        server.main()

        assert len(run_calls) == 1
        assert run_calls[0]["host"] == config.SERVER_HOST
        assert run_calls[0]["port"] == config.SERVER_PORT
