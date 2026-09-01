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

"""Contract tests D-E: JS syntax validity and panel generation."""

import re
import sys

import pytest

from tests.visual.conftest import iife_src_file, iife_has_node, iife_node_check, STARTUP_CACHE_VARS, _IIFE_SRC


# ---------------------------------------------------------------------------
# CONTRACT D — JS syntax valid (node --check) for all major panels
# ---------------------------------------------------------------------------

class TestContractD_JSSyntax:
    """node --check must pass for every major generated panel.

    This catches f-string brace escaping errors, single-quote termination,
    and other Python-to-JS string generation bugs that produce invalid JS.
    A syntax error in any sub-module propagates to the entire panel IIFE,
    silently preventing the panel from ever opening.
    """

    @pytest.fixture(autouse=True)
    def require_node(self):
        if not iife_has_node():
            pytest.skip('node not available')

    def _extract_script(self, html: str) -> str:
        """Pull the inner content of <script> blocks."""
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        return '\n'.join(scripts)

    def test_trading_desk_js_syntax(self):
        sys.path.insert(0, _IIFE_SRC)
        import config  # noqa: F401 — sets sys.path
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        js = self._extract_script(TradingDeskPanel().get_js())
        iife_node_check(js, 'TradingDeskPanel')

    def test_trading_blotter_submodule_syntax(self):
        sys.path.insert(0, _IIFE_SRC)
        import config  # noqa
        from visual.interactivity.trading import blotter
        iife_node_check(blotter.get_js(), 'trading/blotter')

    def test_trading_market_submodule_syntax(self):
        sys.path.insert(0, _IIFE_SRC)
        import config  # noqa
        from visual.interactivity.trading import market
        iife_node_check(market.get_js(), 'trading/market')

    def test_trading_fs01_submodule_syntax(self):
        sys.path.insert(0, _IIFE_SRC)
        import config  # noqa
        from visual.interactivity.trading import fs01
        iife_node_check(fs01.get_js(), 'trading/fs01')

    def test_trading_eod_submodule_syntax(self):
        sys.path.insert(0, _IIFE_SRC)
        import config  # noqa
        from visual.interactivity.trading import eod
        iife_node_check(eod.get_js(), 'trading/eod')

    def test_trading_stress_submodule_syntax(self):
        sys.path.insert(0, _IIFE_SRC)
        import config  # noqa
        from visual.interactivity.trading import stress
        iife_node_check(stress.get_js(), 'trading/stress')

    def test_trading_port_stress_submodule_syntax(self):
        sys.path.insert(0, _IIFE_SRC)
        import config  # noqa
        from visual.interactivity.trading import port_stress
        iife_node_check(port_stress.get_js(), 'trading/port_stress')

    def test_trading_curves_submodule_syntax(self):
        sys.path.insert(0, _IIFE_SRC)
        import config  # noqa
        from visual.interactivity.trading import curves
        iife_node_check(curves.get_js(), 'trading/curves')

    def test_trading_aggregate_submodule_syntax(self):
        sys.path.insert(0, _IIFE_SRC)
        import config  # noqa
        from visual.interactivity.trading import aggregate
        iife_node_check(aggregate.get_js(), 'trading/aggregate')

    def test_startup_preloader_syntax(self):
        """startup.py JS must be syntactically valid."""
        sys.path.insert(0, _IIFE_SRC)
        import config  # noqa
        from visual.interactivity.startup import get_js
        js = '(function(){' + get_js() + '})();'
        iife_node_check(js, 'startup preloader')

    def test_storm_portfolio_syntax(self):
        sys.path.insert(0, _IIFE_SRC)
        import config  # noqa
        from visual.interactivity.storm import stormportfolio
        js = stormportfolio.StormPortfolioPanel().get_js()
        script = self._extract_script(js)
        if script:
            iife_node_check(script, 'StormPortfolioPanel')

class TestContractE_PanelGeneration:
    """Every panel's get_js() must complete without raising a Python exception.

    NameError from unescaped f-string braces is the most common failure mode.
    It silently breaks the panel by producing no JS at all.
    """

    @pytest.fixture(autouse=True)
    def add_src_to_path(self):
        sys.path.insert(0, _IIFE_SRC)
        import config  # noqa
        yield

    def test_trading_desk_generates(self):
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        js = TradingDeskPanel().get_js()
        assert len(js) > 50_000, f'TradingDeskPanel JS unexpectedly short: {len(js)} chars'

    def test_blotter_generates(self):
        from visual.interactivity.trading import blotter
        js = blotter.get_js()
        assert len(js) > 1000

    def test_market_generates(self):
        from visual.interactivity.trading import market
        js = market.get_js()
        assert len(js) > 1000

    def test_fs01_generates(self):
        from visual.interactivity.trading import fs01
        js = fs01.get_js()
        assert len(js) > 500

    def test_eod_generates(self):
        from visual.interactivity.trading import eod
        js = eod.get_js()
        assert len(js) > 1000

    def test_stress_generates(self):
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert len(js) > 1000

    def test_port_stress_generates(self):
        from visual.interactivity.trading import port_stress
        js = port_stress.get_js()
        assert len(js) > 1000

    def test_curves_generates(self):
        from visual.interactivity.trading import curves
        js = curves.get_js()
        assert len(js) > 1000

    def test_aggregate_generates(self):
        from visual.interactivity.trading import aggregate
        js = aggregate.get_js()
        assert len(js) > 1000

    def test_preloader_generates(self):
        from visual.interactivity.trading import preloader
        js = preloader.get_js()
        assert len(js) > 1000

    def test_startup_generates(self):
        from visual.interactivity.startup import get_js
        js = get_js()
        assert len(js) > 1000

    def test_storm_sp_table_generates(self):
        from visual.interactivity.storm import sp_table
        js = sp_table.get_js()
        assert len(js) > 500
