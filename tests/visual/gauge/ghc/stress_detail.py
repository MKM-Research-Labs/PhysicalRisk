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

"""Detailed regression tests for Stress Test tab (ghc_stress.py) JS generation.

Protects against regressions in storm selector, knock-out logic,
chart sub-tabs, and CDS-in-stress pricing display.
"""

import pytest


@pytest.fixture(scope='module')
def stress_js():
    """Get stress test tab JS once for all tests."""
    from visual.interactivity.gauge.gaugehc import ghc_stress
    return ghc_stress.get_js()


class TestStressTabRenders:
    """Basic rendering checks."""

    def test_stress_tab_renders(self, stress_js):
        """ghc_stress.get_js() returns valid JS."""
        assert len(stress_js) > 1000


class TestStormSelector:
    """Storm dropdown and auto-selection."""

    def test_storm_dropdown(self, stress_js):
        """Storm select element present."""
        assert 'stress-storm-select' in stress_js

    def test_auto_selects_worst_storm(self, stress_js):
        """Sorts by peak level for auto-selection."""
        assert 'peak_level_m' in stress_js


class TestChartSubTabs:
    """Three chart sub-tabs with addEventListener."""

    def test_flood_probability_tab(self, stress_js):
        """Flood Probability sub-tab present."""
        assert 'Flood Probability' in stress_js

    def test_stress_pnl_tab(self, stress_js):
        """Stress P&L sub-tab present."""
        assert 'Stress P' in stress_js

    def test_surface_tab(self, stress_js):
        """Surface sub-tab present."""
        assert 'Surface' in stress_js

    def test_event_listeners_not_inline(self, stress_js):
        """Uses addEventListener, not inline onclick for sub-tabs."""
        assert 'addEventListener' in stress_js
        assert 'stress-ctab-0' in stress_js
        assert 'stress-ctab-1' in stress_js
        assert 'stress-ctab-2' in stress_js


class TestSurfaceTable:
    """Probability surface table rendering."""

    def test_surface_wrap_element(self, stress_js):
        """Surface tab creates a wrapping div."""
        assert 'stress-surface-wrap' in stress_js

    def test_surface_reads_probability_surface(self, stress_js):
        """Surface table reads probability_surface from data."""
        assert 'probability_surface' in stress_js

    def test_surface_trigger_band_shading(self, stress_js):
        """Surface table applies trigger-band background colours."""
        assert '#FFEBEE' in stress_js  # severe
        assert '#FFF3E0' in stress_js  # warning
        assert '#FFF8E1' in stress_js  # alert

    def test_surface_ko_trim(self, stress_js):
        """Surface footer references KO trimming."""
        assert 'trimmed at KO' in stress_js

    def test_surface_renders_table(self, stress_js):
        """Renders an HTML table with monospace font."""
        assert 'border-collapse' in stress_js
        assert 'font-family:monospace' in stress_js


class TestStressEndpoints:
    """Stress tab must fetch from correct endpoints."""

    def test_storms_endpoint(self, stress_js):
        """Hits /trading/stress/storms."""
        assert '/trading/stress/storms' in stress_js

    def test_run_endpoint(self, stress_js):
        """Hits /trading/stress/run."""
        assert '/trading/stress/run' in stress_js


class TestKnockOutDisplay:
    """Knock-out status must be displayed correctly."""

    def test_triggered_hour_reference(self, stress_js):
        """References triggered_hour for KO status."""
        assert 'triggered_hour' in stress_js

    def test_ko_label(self, stress_js):
        """Shows KO H{n} label for triggered trades."""
        assert 'KO H' in stress_js

    def test_ko_annotation_line(self, stress_js):
        """Charts have KO annotation line."""
        assert 'koLine' in stress_js

    def test_first_trigger_hour(self, stress_js):
        """Charts reference first_trigger_hour for KO line."""
        assert 'first_trigger_hour' in stress_js
