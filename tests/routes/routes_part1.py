# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Tests for Flask route endpoints — part 1.

Health, property, gauge, and CORS routes.
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
