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
Tests for the global page-load startup preloader (part 2).

Verifies:
  6. Storm portfolio panel uses _preStorms cache variable
  8. InteractivityManager wires startup preloader in FIRST
  9. Health endpoint registered at /api/v1/health
 10. _startupDetail() stat labels -- every dataset has a stat handler
"""

import os
import pytest

# ---------------------------------------------------------------------------
# File-read helpers (avoids importing folium-dependent modules)
# ---------------------------------------------------------------------------

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _src(rel_path: str) -> str:
    """Read a source file relative to repo root.

    JS factory bodies now live in src/static/js (returned via js_static());
    fold any referenced asset back in so substring assertions still see the JS.
    """
    from tests.visual.conftest import _augment_with_static
    with open(os.path.join(_REPO, rel_path)) as f:
        return _augment_with_static(f.read(), _REPO)


# ---------------------------------------------------------------------------
# Tests: InteractivityManager wires preloader first
# ---------------------------------------------------------------------------

class TestInteractivityManagerWiring:

    def test_startup_preloader_imported_in_init(self):
        src = _src('src/visual/interactivity/manager.py')
        assert 'from .startup import StartupPreloader' in src

    def test_startup_preloader_instantiated_in_init(self):
        src = _src('src/visual/interactivity/manager.py')
        assert 'self.startup_preloader = StartupPreloader()' in src

    def test_setup_map_adds_preloader_before_notifications(self):
        src = _src('src/visual/interactivity/manager.py')
        preloader_idx = src.find('startup_preloader.add_to_map')
        notifications_idx = src.find('self.notifications.add_to_map')
        assert preloader_idx != -1
        assert notifications_idx != -1
        assert preloader_idx < notifications_idx


# ---------------------------------------------------------------------------
# Tests: panel cache-first patterns
# ---------------------------------------------------------------------------

class TestStormPortfolioCache:

    def test_checks_pre_storms_cache(self):
        src = _src('src/visual/interactivity/storm/sp_table.py')
        assert 'window._preStorms' in src

    def test_apply_storm_list_function_exists(self):
        src = _src('src/visual/interactivity/storm/sp_table.py')
        assert '_applyStormList' in src

    def test_clears_cache_after_use(self):
        """Cache var should be nulled after consuming to allow refresh."""
        src = _src('src/visual/interactivity/storm/sp_table.py')
        assert 'window._preStorms = null' in src


# ---------------------------------------------------------------------------
# Tests: health route registered at /api/v1/health
# ---------------------------------------------------------------------------

class TestHealthRoute:

    def test_health_py_has_api_v1_health_route(self):
        """health.py must declare /api/v1/health as a route alias."""
        src = _src('src/routes/health.py')
        assert '/api/v1/health' in src

    def test_health_py_has_plain_health_route(self):
        """Backward-compat: /health must still exist."""
        src = _src('src/routes/health.py')
        assert '"/health"' in src

    def test_health_check_function_serves_both(self):
        """A single function must handle both route decorators."""
        src = _src('src/routes/health.py')
        # Both route decorators should appear before health_check def
        api_idx = src.find('"/api/v1/health"')
        plain_idx = src.find('"/health"')
        fn_idx = src.find('def health_check')
        assert api_idx != -1 and plain_idx != -1 and fn_idx != -1
        # Both routes before the function definition
        assert api_idx < fn_idx
        assert plain_idx < fn_idx

    _flask_available = pytest.mark.skipif(
        __import__('importlib').util.find_spec('flask_cors') is None,
        reason='flask_cors not installed'
    )

    @pytest.fixture
    def app(self):
        import sys
        sys.path.insert(0, os.path.join(_REPO, 'src'))
        from server import create_app
        return create_app()

    @_flask_available
    def test_health_200_at_api_v1(self, app):
        with app.test_client() as c:
            r = c.get('/api/v1/health')
        assert r.status_code == 200

    @_flask_available
    def test_health_200_at_root(self, app):
        with app.test_client() as c:
            r = c.get('/health')
        assert r.status_code == 200

    @_flask_available
    def test_health_returns_ok_status(self, app):
        import json
        with app.test_client() as c:
            r = c.get('/api/v1/health')
        data = json.loads(r.data)
        assert data['status'] == 'ok'


# ---------------------------------------------------------------------------
# Tests: _startupDetail() stat labels -- every dataset has a stat handler
# ---------------------------------------------------------------------------

class TestStartupDetailStats:
    """_startupDetail() must return a non-null stat for every dataset key."""

    def _src(self):
        return _src('src/visual/interactivity/startup.py')

    def test_blotter_stat_uses_trades_length(self):
        src = self._src()
        assert "key === '_tdPreBlotter'" in src
        assert "data.trades.length + ' trades'" in src

    def test_market_stat_uses_object_keys_gauges(self):
        src = self._src()
        assert "key === '_tdPreMarket'" in src
        assert "Object.keys(data.gauges).length" in src
        assert "' gauges'" in src

    def test_gauges_stat_uses_gauges_length(self):
        src = self._src()
        assert "key === '_tdPreGauges'" in src
        assert "data.gauges.length + ' gauges'" in src

    def test_stress_storms_stat_uses_storms_length(self):
        src = self._src()
        assert "key === '_tdPreStressStorms'" in src
        assert "data.storms.length + ' scenarios'" in src

    def test_port_storms_stat_uses_storms_length(self):
        src = self._src()
        assert "key === '_tdPrePortStorms'" in src
        assert "data.storms.length + ' storms'" in src

    def test_eod_history_stat_uses_history_length(self):
        src = self._src()
        assert "key === '_tdPreEodHistory'" in src
        assert "data.history.length + ' snapshots'" in src

    def test_yield_curve_stat_uses_object_keys(self):
        src = self._src()
        assert "key === '_tdPreYieldCurve'" in src
        assert "Object.keys(data.yield_curve).length" in src
        assert "' tenors'" in src

    def test_pre_storms_stat_uses_storms_length(self):
        src = self._src()
        assert "key === '_preStorms'" in src
        assert "data.storms.length + ' storms'" in src

    def test_property_ts_stat_uses_total_properties(self):
        src = self._src()
        assert "key === '_prePropertyTS'" in src
        assert 'data.data.summary.properties_with_floods' in src
        assert "' flooded'" in src

    def test_gauge_hist_stat_uses_count(self):
        src = self._src()
        assert "key === '_preGaugeHist'" in src
        assert 'data.count' in src

    def test_mortgages_stat_uses_mortgages_length(self):
        src = self._src()
        assert "key === '_preMortgages'" in src
        assert "data.mortgages" in src

    def test_all_eleven_keys_have_stat_handler(self):
        """Every dataset key must appear in _startupDetail -- no silent blanks."""
        src = self._src()
        keys = [
            '_tdPreBlotter', '_tdPreMarket', '_tdPreGauges',
            '_tdPreStressStorms', '_tdPrePortStorms', '_tdPreEodHistory',
            '_tdPreYieldCurve', '_preStorms',
            '_prePropertyTS', '_preGaugeHist',
            '_preMortgages',
        ]
        for k in keys:
            assert f"key === '{k}'" in src, f"No stat handler for {k} in _startupDetail()"
