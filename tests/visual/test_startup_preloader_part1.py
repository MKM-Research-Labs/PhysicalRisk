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
Tests for the global page-load startup preloader (part 1).

Verifies:
  1. startup.py declares all 11 cache variables
  2. JS fires on DOMContentLoaded (not deferred to a button click)
  3. All expected endpoints are included
  4. _tdPreloadDone is set after all fetches settle
  5. Trading desk preloader no longer re-declares cache vars (no duplication)
"""

import os

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
        """Must NOT defer to a button click -- runs on DOMContentLoaded."""
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
            '/api/v1/rloans',
        ]
        for ep in endpoints:
            assert ep in js, f'Endpoint {ep!r} missing from startup.py'

    def test_market_state_label_is_hazard_curves(self):
        """'Market state' was renamed to 'Hazard curves'."""
        js = _src('src/visual/interactivity/startup.py')
        assert 'Hazard curves' in js
        assert "'Market state'" not in js and '"Market state"' not in js

    def test_shows_progress_popup(self):
        # Popup DOM creation lives in the sibling startup_popup module;
        # the progress bar id is referenced from the main loop.
        popup_js = _src('src/visual/interactivity/startup_popup.py')
        startup_js = _src('src/visual/interactivity/startup.py')
        assert 'startup-preloader-popup' in popup_js
        assert 'startup-pre-bar' in startup_js

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
