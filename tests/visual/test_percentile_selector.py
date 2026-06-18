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

"""Tests for the percentile storm selector feature.

Validates that:
  1. config/format.py generates correct percentile HTML and JS
  2. All four storm selector locations include the percentile widget
  3. The JS percentile-to-storm mapping formula is correct
  4. HTML escaping is safe for embedding in JS string contexts
"""

import pytest


# =========================================================================
#  config/format.py — percentile helper functions
# =========================================================================

class TestPercentileApplyJs:
    """Tests for percentile_apply_js() — the shared JS function."""

    @pytest.fixture(scope='class')
    def js(self):
        from config.format import percentile_apply_js
        return percentile_apply_js()

    def test_returns_nonempty_string(self, js):
        assert isinstance(js, str)
        assert len(js) > 50

    def test_defines_window_global(self, js):
        """Must be on window so onclick in innerHTML can reach it."""
        assert 'window._applyPercentile' in js

    def test_reads_percentile_value(self, js):
        assert 'parseFloat(pctSel.value)' in js

    def test_skips_placeholder_option(self, js):
        """Index 0 is the placeholder; storms start at index 1."""
        assert 'idx + 1' in js

    def test_uses_data_total_attribute(self, js):
        """Must read total storm count from data-total, not dropdown length."""
        assert 'data-total' in js

    def test_triggers_onchange(self, js):
        assert 'onchange' in js

    def test_dispatches_event_fallback(self, js):
        """Falls back to dispatchEvent if onchange is not a function."""
        assert 'dispatchEvent' in js

    def test_formula_clamps_to_zero(self, js):
        """Index must never go negative."""
        assert 'Math.max(0,' in js


class TestPercentileSelectorHtml:
    """Tests for percentile_selector_html() — the dropdown + Go button."""

    @pytest.fixture(scope='class')
    def html(self):
        from config.format import percentile_selector_html
        return percentile_selector_html('test-pct', 'test-storm')

    def test_returns_nonempty_string(self, html):
        assert isinstance(html, str)
        assert len(html) > 100

    def test_contains_select_with_correct_id(self, html):
        assert 'id="test-pct"' in html

    def test_contains_go_button(self, html):
        assert '>Go</button>' in html

    def test_default_selected_is_99(self, html):
        assert '<option value="99" selected>99%</option>' in html

    def test_has_50_percent_option(self, html):
        assert '<option value="50">50%</option>' in html

    def test_has_99_point_9_option(self, html):
        assert '<option value="99.9">99.9%</option>' in html

    def test_total_option_count(self, html):
        """50-99 (50 options) + 99.1-99.9 (9 options) = 59."""
        assert html.count('<option') == 59

    def test_no_raw_single_quotes_in_onclick(self, html):
        """Single quotes in onclick would break JS string delimiters.
        Must use &#39; HTML entities instead."""
        # Extract the onclick attribute value
        import re
        match = re.search(r'onclick="([^"]*)"', html)
        assert match, "No onclick attribute found"
        onclick_value = match.group(1)
        assert "'" not in onclick_value, (
            f"Raw single quotes in onclick would break JS strings: {onclick_value}"
        )
        assert '&#39;' in onclick_value

    def test_onclick_references_correct_ids(self, html):
        assert '&#39;test-pct&#39;' in html
        assert '&#39;test-storm&#39;' in html

    def test_percentile_label_present(self, html):
        assert 'Percentile:' in html


# =========================================================================
#  Location 1: Trading Desk Stress tab
# =========================================================================

class TestTradingDeskStressPercentile:
    """Percentile selector in Trading Desk Stress (setup_dom.py)."""

    @pytest.fixture(scope='class')
    def dom_js(self):
        from visual.interactivity.trading.stress.setup_dom import get_js
        return get_js()

    @pytest.fixture(scope='class')
    def setup_js(self):
        from visual.interactivity.trading.stress.setup import get_js
        return get_js()

    def test_percentile_select_in_dom(self, dom_js):
        assert 'td-stress-pct' in dom_js

    def test_go_button_in_dom(self, dom_js):
        assert '_applyPercentile' in dom_js

    def test_targets_correct_storm_select(self, dom_js):
        assert 'td-stress-storm' in dom_js

    def test_apply_percentile_function_defined(self, setup_js):
        assert 'window._applyPercentile' in setup_js


# =========================================================================
#  Location 2: Portfolio Stress tab
# =========================================================================

class TestPortStressPercentile:
    """Percentile selector in Portfolio Stress (port_stress/setup.py)."""

    @pytest.fixture(scope='class')
    def js(self):
        from visual.interactivity.trading.port_stress.setup import _get_setup_js
        return _get_setup_js()

    def test_percentile_select_present(self, js):
        assert 'ps-pct-sel' in js

    def test_go_button_present(self, js):
        assert '_applyPercentile' in js

    def test_targets_correct_storm_select(self, js):
        assert 'ps-storm-sel' in js


# =========================================================================
#  Location 3: Gauge Stress tab
# =========================================================================

class TestGaugeStressPercentile:
    """Percentile selector in Gauge Stress (ghc_stress_setup.py)."""

    @pytest.fixture(scope='class')
    def js(self):
        from visual.interactivity.gauge.gaugehc.ghc_stress_setup import get_js
        return get_js()

    def test_percentile_select_present(self, js):
        assert 'stress-pct-sel' in js

    def test_go_button_present(self, js):
        assert '_applyPercentile' in js

    def test_targets_correct_storm_select(self, js):
        assert 'stress-storm-select' in js


# =========================================================================
#  Location 4: Storm Portfolio panel
# =========================================================================

class TestStormPortfolioPercentile:
    """Percentile selector in Storm Portfolio (chrome.py)."""

    @pytest.fixture(scope='class')
    def js(self):
        from visual.interactivity.storm.stormportfolio.chrome import get_js
        return get_js()

    def test_percentile_select_present(self, js):
        assert 'sp-pct-sel' in js

    def test_go_button_present(self, js):
        assert '_applyPercentile' in js

    def test_targets_correct_storm_select(self, js):
        assert 'sp-storm-select' in js


# =========================================================================
#  Cross-location consistency
# =========================================================================

class TestPercentileConsistency:
    """All four locations use the same shared function and option set."""

    @pytest.fixture(scope='class')
    def all_js(self):
        from visual.interactivity.trading.stress.setup_dom import get_js as td_dom
        from visual.interactivity.trading.port_stress.setup import _get_setup_js as ps
        from visual.interactivity.gauge.gaugehc.ghc_stress_setup import get_js as ghc
        from visual.interactivity.storm.stormportfolio.chrome import get_js as sp
        return {
            'td_stress': td_dom(),
            'port_stress': ps(),
            'gauge_stress': ghc(),
            'storm_portfolio': sp(),
        }

    def test_all_locations_have_99_percent_default(self, all_js):
        """Every location should default to 99%."""
        for name, js in all_js.items():
            assert '"99" selected' in js or "'99' selected" in js or \
                '"99" selected' in js, \
                f"{name} missing 99% default selection"

    def test_all_locations_call_apply_percentile(self, all_js):
        for name, js in all_js.items():
            assert '_applyPercentile' in js, \
                f"{name} missing _applyPercentile call"

    def test_no_raw_single_quotes_in_any_onclick(self, all_js):
        """Regression guard: single quotes in onclick break JS strings."""
        import re
        for name, js in all_js.items():
            # Find onclick="_applyPercentile(...)" patterns
            for match in re.finditer(r'onclick="(_applyPercentile\([^"]*\))"', js):
                onclick = match.group(1)
                assert "'" not in onclick, (
                    f"{name}: raw single quote in onclick would break JS: {onclick}"
                )
