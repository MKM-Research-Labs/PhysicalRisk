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
Tests for the global page-load startup preloader.

Verifies:
  1. startup.py declares all 11 cache variables
  2. JS fires on DOMContentLoaded (not deferred to a button click)
  3. All expected endpoints are included
  4. _tdPreloadDone is set after all fetches settle
  5. Trading desk preloader no longer re-declares cache vars (no duplication)
  6. Storm portfolio panel uses _preStorms cache variable
  7. Governance documents panel uses _tdPreGovDocs cache variable
  8. InteractivityManager wires startup preloader in FIRST
  9. Health endpoint registered at /api/v1/health
"""

import os
import pytest

# ---------------------------------------------------------------------------
# File-read helpers (avoids importing folium-dependent modules)
# ---------------------------------------------------------------------------

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _src(rel_path: str) -> str:
    """Read a source file relative to repo root."""
    with open(os.path.join(_REPO, rel_path)) as f:
        return f.read()


# ---------------------------------------------------------------------------
# Tests: startup.py declares all cache variables
# ---------------------------------------------------------------------------

class TestStartupPreloaderCacheVars:

    def test_declares_td_pre_blotter(self):
        assert 'window._tdPreBlotter' in _src('src/visual/interactivity/startup.py')

    def test_declares_td_pre_market(self):
        assert 'window._tdPreMarket' in _src('src/visual/interactivity/startup.py')

    def test_declares_td_pre_gauges(self):
        assert 'window._tdPreGauges' in _src('src/visual/interactivity/startup.py')

    def test_declares_td_pre_stress_storms(self):
        assert 'window._tdPreStressStorms' in _src('src/visual/interactivity/startup.py')

    def test_declares_td_pre_port_storms(self):
        assert 'window._tdPrePortStorms' in _src('src/visual/interactivity/startup.py')

    def test_declares_td_pre_eod_history(self):
        assert 'window._tdPreEodHistory' in _src('src/visual/interactivity/startup.py')

    def test_declares_td_pre_yield_curve(self):
        assert 'window._tdPreYieldCurve' in _src('src/visual/interactivity/startup.py')

    def test_declares_td_pre_gov_docs(self):
        assert 'window._tdPreGovDocs' in _src('src/visual/interactivity/startup.py')

    def test_declares_pre_storms(self):
        assert 'window._preStorms' in _src('src/visual/interactivity/startup.py')

    def test_declares_pre_gov_audit(self):
        assert 'window._preGovAudit' in _src('src/visual/interactivity/startup.py')

    def test_declares_pre_gov_bib(self):
        assert 'window._preGovBib' in _src('src/visual/interactivity/startup.py')

    def test_declares_pre_property_ts(self):
        assert 'window._prePropertyTS' in _src('src/visual/interactivity/startup.py')

    def test_declares_pre_gauge_hist(self):
        assert 'window._preGaugeHist' in _src('src/visual/interactivity/startup.py')


# ---------------------------------------------------------------------------
# Tests: startup.py JS behaviour
# ---------------------------------------------------------------------------

class TestStartupPreloaderBehaviour:

    def test_fires_on_dom_content_loaded(self):
        """Must NOT defer to a button click — runs on DOMContentLoaded."""
        js = _src('src/visual/interactivity/startup.py')
        assert 'DOMContentLoaded' in js, (
            'Global startup preloader must register on DOMContentLoaded'
        )

    def test_sets_td_preload_done(self):
        """Sets window._tdPreloadDone so any IIFE can read it via global scope."""
        assert 'window._tdPreloadDone = true' in _src('src/visual/interactivity/startup.py')

    def test_all_fourteen_endpoints_present(self):
        js = _src('src/visual/interactivity/startup.py')
        endpoints = [
            '/api/v1/trading/blotter',
            '/api/v1/trading/market-state',
            '/api/v1/gauges',
            '/api/v1/trading/stress/storms',
            '/api/v1/trading/stress/portfolio-storms',
            '/api/v1/trading/eod/history',
            '/api/v1/trading/yield-curve',
            '/api/v1/governance/documents',
            '/api/v1/propertyts/storms',
            '/api/v1/governance/audit-trail',
            '/api/v1/governance/bibliography',
            '/api/v1/propertyts/summary',
            '/api/v1/gauges/history/summary',
            '/api/v1/mortgages',
        ]
        for ep in endpoints:
            assert ep in js, f'Endpoint {ep!r} missing from startup.py'

    def test_market_state_label_is_hazard_curves(self):
        """'Market state' was renamed to 'Hazard curves'."""
        js = _src('src/visual/interactivity/startup.py')
        assert 'Hazard curves' in js
        assert "'Market state'" not in js and '"Market state"' not in js

    def test_shows_progress_popup(self):
        js = _src('src/visual/interactivity/startup.py')
        assert 'startup-preloader-popup' in js
        assert 'startup-pre-bar' in js

    def test_startup_preloader_class_defined(self):
        src = _src('src/visual/interactivity/startup.py')
        assert 'class StartupPreloader' in src

    def test_add_to_map_method_defined(self):
        src = _src('src/visual/interactivity/startup.py')
        assert 'def add_to_map' in src


# ---------------------------------------------------------------------------
# Tests: trading desk preloader no longer duplicates cache var declarations
# ---------------------------------------------------------------------------

class TestTradingPreloaderDeduplication:

    def test_td_preloader_does_not_redeclare_td_pre_blotter(self):
        src = _src('src/visual/interactivity/trading/preloader.py')
        assert 'window._tdPreBlotter      = null' not in src, (
            'trading/preloader.py re-declares window._tdPreBlotter; '
            'that variable is now owned by startup.py'
        )

    def test_td_preloader_does_not_redeclare_td_pre_market(self):
        src = _src('src/visual/interactivity/trading/preloader.py')
        assert 'window._tdPreMarket       = null' not in src

    def test_td_preloader_does_not_redeclare_td_preload_done(self):
        src = _src('src/visual/interactivity/trading/preloader.py')
        assert 'var _tdPreloadDone = false' not in src


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


class TestGovernanceDocumentsCache:

    def test_checks_gov_docs_cache(self):
        src = _src('src/visual/interactivity/governance/mg_documents.py')
        assert 'window._tdPreGovDocs' in src

    def test_apply_documents_function_exists(self):
        src = _src('src/visual/interactivity/governance/mg_documents.py')
        assert '_applyDocuments' in src

    def test_clears_cache_after_use(self):
        src = _src('src/visual/interactivity/governance/mg_documents.py')
        assert 'window._tdPreGovDocs = null' in src


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
# Tests: _startupDetail() stat labels — every dataset has a stat handler
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

    def test_gov_docs_stat_uses_documents_length(self):
        src = self._src()
        assert "key === '_tdPreGovDocs'" in src
        assert "data.documents.length + ' docs'" in src

    def test_pre_storms_stat_uses_storms_length(self):
        src = self._src()
        assert "key === '_preStorms'" in src
        assert "data.storms.length + ' storms'" in src

    def test_gov_audit_stat_uses_events_length(self):
        src = self._src()
        assert "key === '_preGovAudit'" in src
        assert "data.total_entries + ' events'" in src

    def test_gov_bib_stat_uses_references_length(self):
        src = self._src()
        assert "key === '_preGovBib'" in src
        assert "data.references.length + ' refs'" in src

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

    def test_all_fourteen_keys_have_stat_handler(self):
        """Every dataset key must appear in _startupDetail — no silent blanks."""
        src = self._src()
        keys = [
            '_tdPreBlotter', '_tdPreMarket', '_tdPreGauges',
            '_tdPreStressStorms', '_tdPrePortStorms', '_tdPreEodHistory',
            '_tdPreYieldCurve', '_tdPreGovDocs', '_preStorms',
            '_preGovAudit', '_preGovBib', '_prePropertyTS', '_preGaugeHist',
            '_preMortgages',
        ]
        for k in keys:
            assert f"key === '{k}'" in src, f"No stat handler for {k} in _startupDetail()"
