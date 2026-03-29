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
Tests for Flask route endpoints — part 2.

Gauge CRUD edge cases, error handling, and server main.
"""

import json


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
        """Lines 32-34: loader.list_all() raises -> 500 response."""
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
