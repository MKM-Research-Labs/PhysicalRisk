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

"""Tests for TradingDeskPanel JS rendering and InteractivityManager integration."""

import pytest


class TestTradingDeskPanelJS:
    """Test that TradingDeskPanel JS renders without f-string errors."""

    def test_panel_renders(self):
        """TradingDeskPanel JS should render without errors."""
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        panel = TradingDeskPanel()
        js = panel.get_js()
        assert len(js) > 0
        assert '<script>' in js
        assert '</script>' in js

    def test_panel_contains_pi_symbol(self):
        """Panel should contain the Pi button."""
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        panel = TradingDeskPanel()
        js = panel.get_js()
        assert '&Pi;' in js

    def test_panel_contains_all_tabs(self):
        """Panel should contain all 7 tab IDs and labels."""
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        panel = TradingDeskPanel()
        js = panel.get_js()
        assert 'blotter' in js
        assert 'market' in js
        assert 'risk' in js
        assert 'td-map-view' in js
        assert 'eod' in js
        assert 'stress' in js
        # Tab labels
        assert 'FS01' in js
        assert 'Aggregate' in js
        assert 'Stress' in js

    def test_panel_contains_global_export(self):
        """Panel should export TradingDesk to window."""
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        panel = TradingDeskPanel()
        js = panel.get_js()
        assert 'window.TradingDesk' in js
        assert 'window.showTradingDesk' in js

    def test_no_unescaped_braces(self):
        """
        Ensure no unescaped single braces that could cause NameError.
        This is a critical check — unescaped {var} in f-strings will raise
        NameError at render time, breaking all subsequent <script> blocks.
        """
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        panel = TradingDeskPanel()
        # This call itself will raise NameError if braces are unescaped
        js = panel.get_js()
        assert len(js) > 1000  # Should be substantial

    def test_blotter_submodule(self):
        """Blotter sub-module should render with FS01 column."""
        from visual.interactivity.trading import blotter
        js = blotter.get_js()
        assert 'createBlotterView' in js
        assert 'loadBlotterData' in js
        assert 'gauge_fs01' in js
        assert 'gauge_dv01' not in js

    def test_market_submodule(self):
        """Market sub-module should render."""
        from visual.interactivity.trading import market
        js = market.get_js()
        assert 'createMarketView' in js
        assert 'loadMarketData' in js

    def test_risk_submodule(self):
        """FS01 Matrix sub-module should render."""
        from visual.interactivity.trading import fs01
        js = fs01.get_js()
        assert 'createRiskView' in js
        assert 'loadRiskData' in js
        assert 'FS01' in js

    def test_map_submodule(self):
        """Aggregate View sub-module should render."""
        from visual.interactivity.trading import aggregate
        js = aggregate.get_js()
        assert 'createMapView' in js
        assert 'loadMapData' in js
        assert 'net_fs01' in js
        assert 'extractAreaName' in js

    def test_eod_submodule(self):
        """EOD sub-module should render."""
        from visual.interactivity.trading import eod
        js = eod.get_js()
        assert 'createEodView' in js
        assert 'loadEodData' in js

    def test_add_to_map(self):
        """Panel should add to a Folium map without error."""
        import folium
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel

        panel = TradingDeskPanel()
        m = folium.Map(location=[51.48, -0.45], zoom_start=11)
        panel.add_to_map(m)

        # Map should have at least one child in html root
        html = m.get_root().html
        assert len(html._children) > 0


class TestPreloadDoneScoping:
    """Regression tests for window._tdPreloadDone cross-IIFE scoping bug.

    startup.py and tradingdesk.py run in separate IIFEs. A bare `var _tdPreloadDone`
    in startup.py's IIFE is local to that IIFE and invisible to the tradingdesk IIFE,
    causing ReferenceError when showPanel() reads it. All reads and writes MUST use
    window._tdPreloadDone to remain accessible across IIFE boundaries.
    """

    def test_startup_uses_window_preload_done_init(self):
        """startup.py must initialise via window._tdPreloadDone (not bare var)."""
        import os
        repo = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))))
        from tests.visual.conftest import _augment_with_static
        with open(os.path.join(repo, 'src/visual/interactivity/startup.py')) as f:
            src = _augment_with_static(f.read(), repo)
        assert 'window._tdPreloadDone = false' in src, (
            'startup.py must use window._tdPreloadDone = false so other IIFEs can read it'
        )
        assert 'var _tdPreloadDone = false' not in src, (
            'var _tdPreloadDone traps it in startup IIFE local scope'
        )

    def test_startup_uses_window_preload_done_set(self):
        """startup.py must set window._tdPreloadDone = true after all fetches settle."""
        import os
        repo = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))))
        from tests.visual.conftest import _augment_with_static
        with open(os.path.join(repo, 'src/visual/interactivity/startup.py')) as f:
            src = _augment_with_static(f.read(), repo)
        assert 'window._tdPreloadDone = true' in src

    def test_tradingdesk_reads_window_preload_done(self):
        """tradingdesk.py showPanel() must read window._tdPreloadDone, not bare _tdPreloadDone."""
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        js = TradingDeskPanel().get_js()
        assert 'window._tdPreloadDone' in js, (
            'showPanel() must check window._tdPreloadDone to avoid ReferenceError '
            'when startup.py IIFE has set it but tradingdesk IIFE cannot see bare var'
        )

    def test_preloader_sets_window_preload_done(self):
        """trading/preloader.py must set window._tdPreloadDone (not bare assignment)."""
        import os
        repo = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))))
        from tests.visual.conftest import _augment_with_static
        with open(os.path.join(repo, 'src/visual/interactivity/trading/preloader.py')) as f:
            src = _augment_with_static(f.read(), repo)
        assert 'window._tdPreloadDone = true' in src


class TestInteractivityManagerIntegration:
    """Test that TradingDeskPanel integrates with InteractivityManager."""

    def test_manager_has_trading_desk(self):
        """InteractivityManager should have trading_desk attribute."""
        from visual.interactivity import InteractivityManager
        mgr = InteractivityManager()
        assert hasattr(mgr, 'trading_desk')

    def test_manager_exports_trading_desk(self):
        """TradingDeskPanel should be in __all__."""
        from visual.interactivity import __all__
        assert 'TradingDeskPanel' in __all__
