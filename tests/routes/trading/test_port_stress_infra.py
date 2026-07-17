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

"""Tests for portfolio stress infrastructure — error handling, caching."""

from unittest.mock import MagicMock, patch

import pytest

from tests.routes.trading.conftest import STORM_PORT_ALERT, STORM_PORT_SEVERE


class TestPortfolioStressErrors:
    """Error handling paths in portfolio stress endpoints."""

    def test_no_json_body_returns_error(self, port_stress_client, port_stress_env):
        """POST with no body returns 400 or 500."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            content_type='application/json')
        assert resp.status_code in (400, 500)

    def test_engine_error_returns_500(self, port_stress_client, port_stress_env):
        """patch _get_engines to raise RuntimeError -> 500."""
        with patch('routes.trading.port_stress._routes._get_engines',
                   side_effect=RuntimeError('engine fail')):
            resp = port_stress_client.post(
                '/api/v1/trading/stress/portfolio-run',
                json={'storm_id': STORM_PORT_SEVERE})
            assert resp.status_code == 500

    def test_missing_storms_file_returns_404(self, trading_client, trading_env):
        """No stress_storms/ + cache cleared -> portfolio-run returns 404."""
        import routes.trading.stress._helpers as stress_helpers
        stress_helpers._stress_index_cache = None
        resp = trading_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        assert resp.status_code == 404
