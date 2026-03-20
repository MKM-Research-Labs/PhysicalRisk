# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Contract tests F-G: cross-panel window.* exports and Pi button sequence."""

import re
import sys

import pytest

from tests.visual.conftest import iife_src_file, iife_has_node, iife_node_check, _IIFE_SRC


# ---------------------------------------------------------------------------
# CONTRACT F — cross-panel window.* exports are consistent
# ---------------------------------------------------------------------------

class TestContractF_CrossPanelExports:
    """Functions that panels export to window.* must be consistent.

    When panel A calls window.someFunction() it was exported by panel B.
    If B stops exporting it, A silently does nothing.  These tests lock the
    contract between callers and exporters.
    """

    def test_trading_desk_exports_show_hide(self):
        """TradingDeskPanel must export TradingDesk and showTradingDesk."""
        src = iife_src_file('src/visual/interactivity/trading/tradingdesk.py')
        assert 'window.TradingDesk' in src
        assert 'window.showTradingDesk' in src

    def test_blotter_exports_apply_filter(self):
        """tdApplyFilter must be on window for FS01 cell click to work."""
        src = iife_src_file('src/visual/interactivity/trading/blotter/filters.py')
        assert 'window.tdApplyFilter' in src

    def test_fs01_exports_risk_cell_click(self):
        """tdRiskCellClick must be on window for blotter filter drill-through."""
        src = iife_src_file('src/visual/interactivity/trading/fs01/grid.py')
        assert 'window.tdRiskCellClick' in src

    def test_stress_hint_uses_window(self):
        """_stressStormHint must be set via window.* for cross-panel navigation."""
        # Historical tab sets it; trading desk stress tab reads it
        hist_src = iife_src_file('src/visual/interactivity/gauge/gaugehc/ghc_historical.py')
        assert 'window._stressStormHint' in hist_src

    def test_stress_setup_reads_window_hint(self):
        stress_src = iife_src_file('src/visual/interactivity/trading/stress/setup.py')
        assert 'window._stressStormHint' in stress_src

    def test_pending_filter_uses_window(self):
        """_tdPendingFilter must be on window for context-menu → blotter filter."""
        blotter_src = iife_src_file('src/visual/interactivity/trading/blotter/setup.py')
        assert 'window._tdPendingFilter' in blotter_src

    def test_refresh_main_map_fs01_exported(self):
        """refreshMainMapFS01 must be on window for blotter close-out to call it."""
        td_map_src = iife_src_file('src/visual/interactivity/trading/td_main_map.py')
        assert 'window.refreshMainMapFS01' in td_map_src

    def test_blotter_actions_calls_refresh_main_map(self):
        """blotter/actions.py must call window.refreshMainMapFS01 after close-out."""
        src = iife_src_file('src/visual/interactivity/trading/blotter/actions.py')
        assert 'window.refreshMainMapFS01' in src


# ---------------------------------------------------------------------------
# CONTRACT G — Pi button panel-open sequence is intact
# ---------------------------------------------------------------------------

class TestContractG_PanelOpenSequence:
    """The Pi button → panel open sequence must be complete and correct.

    This contract pins the exact sequence:
      Pi click → showPanel() → check window._tdPreloadDone
        → if done:  _tdOpenPanel()
        → if not:   _tdRunPreload(callback) → callback → _tdOpenPanel()
      _tdOpenPanel() → createPanel() → tdPanel.display='flex' → switchTab('blotter')

    If any step is missing the panel silently fails to appear.
    """

    def _td_js(self):
        sys.path.insert(0, _IIFE_SRC)
        import config  # noqa
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        import re
        html = TradingDeskPanel().get_js()
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        return '\n'.join(scripts)

    def test_show_panel_function_exists(self):
        js = self._td_js()
        assert 'function showPanel()' in js

    def test_show_panel_reads_window_preload_done(self):
        js = self._td_js()
        assert 'window._tdPreloadDone' in js, (
            'showPanel() must check window._tdPreloadDone. '
            'A bare _tdPreloadDone would throw ReferenceError from the trading IIFE.'
        )

    def test_open_panel_function_exists(self):
        js = self._td_js()
        assert '_tdOpenPanel' in js

    def test_open_panel_sets_display_flex(self):
        js = self._td_js()
        assert "style.display = 'flex'" in js

    def test_create_panel_creates_blotter_view(self):
        js = self._td_js()
        assert 'createBlotterView' in js

    def test_switch_tab_blotter_on_open(self):
        """Panel must switch to blotter tab when opened."""
        js = self._td_js()
        assert "switchTab('blotter')" in js

    def test_pi_button_calls_show_panel(self):
        js = self._td_js()
        assert 'showPanel()' in js

    def test_run_preload_function_exists(self):
        """Fallback preloader function must exist for first-open race condition."""
        js = self._td_js()
        assert '_tdRunPreload' in js
