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

"""Tests for Stress tab KO behaviour and gauge function definitions."""

import pytest


class TestStressKnockOut:
    """Regression: Stress test knock-out behaviour."""

    def test_stress_ko_status_in_table(self):
        """Stress table must show KO status per trade."""
        from visual.interactivity.gauge.gaugehc import ghc_stress
        js = ghc_stress.get_js()
        assert 'triggered_hour' in js, \
            "Stress table must reference triggered_hour"
        assert 'KO H' in js, "Must show 'KO H{n}' label for triggered trades"

    def test_stress_ko_annotation_on_charts(self):
        """Both stress charts must show KO vertical annotation line."""
        from visual.interactivity.gauge.gaugehc import ghc_stress
        js = ghc_stress.get_js()
        assert 'koLine' in js, "Charts must have KO annotation line"
        assert 'first_trigger_hour' in js, \
            "Charts must reference first_trigger_hour for KO line"

    def test_stress_stats_bar_ko_info(self):
        """Stats bar must show knock-out count."""
        from visual.interactivity.gauge.gaugehc import ghc_stress
        js = ghc_stress.get_js()
        assert 'num_triggered' in js, "Stats bar must show num_triggered"
        assert 'Knocked Out' in js, "Stats bar must show 'Knocked Out' label"


class TestStressGaugeFunctions:
    """All stress gauge/storm functions must be defined and reachable.

    'None of the gauge functions are available' means these must all exist
    in the rendered JS output.
    """

    @pytest.fixture(scope='class')
    def stress_js(self):
        from visual.interactivity.trading import stress
        return stress.get_js()

    @pytest.fixture(scope='class')
    def full_js(self):
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        return TradingDeskPanel().get_js()

    def test_populate_gauge_dropdown_function_defined(self, stress_js):
        """_tdPopulateGaugeDropdown must exist -- builds gauge selector."""
        assert '_tdPopulateGaugeDropdown' in stress_js, \
            "_tdPopulateGaugeDropdown missing -- gauge list cannot be built"

    def test_stress_gauge_changed_function_defined(self, stress_js):
        """tdStressGaugeChanged must exist -- called when gauge is selected."""
        assert 'function tdStressGaugeChanged' in stress_js, \
            "tdStressGaugeChanged missing -- gauge selection has no handler"

    def test_populate_storm_dropdown_function_defined(self, stress_js):
        """_tdPopulateStormDropdown must exist -- builds storm list for selected gauge."""
        assert '_tdPopulateStormDropdown' in stress_js, \
            "_tdPopulateStormDropdown missing -- storm list cannot be populated"

    def test_stress_storm_changed_function_defined(self, stress_js):
        """tdStressStormChanged must exist -- called when storm is selected."""
        assert 'function tdStressStormChanged' in stress_js, \
            "tdStressStormChanged missing -- storm selection has no handler"

    def test_stress_gauge_changed_binds_to_dropdown(self, stress_js):
        """gauge onchange must call tdStressGaugeChanged."""
        assert 'tdStressGaugeChanged()' in stress_js, \
            "gauge dropdown onchange must invoke tdStressGaugeChanged()"

    def test_stress_storm_changed_binds_to_dropdown(self, stress_js):
        """storm onchange must call tdStressStormChanged."""
        assert 'tdStressStormChanged()' in stress_js, \
            "storm dropdown onchange must invoke tdStressStormChanged()"

    def test_gauge_selector_element_id_present(self, stress_js):
        """td-stress-gauge element must be present for JS to find it."""
        assert "getElementById('td-stress-gauge')" in stress_js, \
            "JS must look up td-stress-gauge element by ID"

    def test_storm_selector_element_id_present(self, stress_js):
        """td-stress-storm element must be present for JS to find it."""
        assert "getElementById('td-stress-storm')" in stress_js, \
            "JS must look up td-stress-storm element by ID"

    def test_full_js_contains_stress_gauge_changed(self, full_js):
        """tdStressGaugeChanged must survive f-string rendering in tradingdesk.py."""
        assert 'tdStressGaugeChanged' in full_js, \
            "tdStressGaugeChanged lost during f-string rendering -- check brace escaping"

    def test_full_js_contains_populate_gauge_dropdown(self, full_js):
        """_tdPopulateGaugeDropdown must survive f-string rendering."""
        assert '_tdPopulateGaugeDropdown' in full_js, \
            "_tdPopulateGaugeDropdown lost during f-string rendering"

    def test_full_js_no_unclosed_template_literal(self, full_js):
        """Rendered JS must not have unescaped f-string brace artifacts."""
        # A NameError during render produces empty/short output
        assert len(full_js) > 10000, \
            "Rendered JS suspiciously short -- likely f-string brace error"

    def test_stress_functions_not_before_iife_close(self, full_js):
        """Stress functions must be INSIDE the IIFE, not after it."""
        iife_close = full_js.rfind('})();')
        idx_gauge_changed = full_js.find('tdStressGaugeChanged')
        assert idx_gauge_changed > 0, "tdStressGaugeChanged not found in full JS"
        assert idx_gauge_changed < iife_close, \
            "tdStressGaugeChanged is outside the IIFE -- functions not reachable"
