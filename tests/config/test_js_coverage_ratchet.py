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

"""The JS coverage ratchet's classification rules."""

import pytest

from config import js_coverage


class TestClassify:
    def test_unmeasured_is_not_a_failure(self):
        """A skipped JS phase reports its own skip; it is not a coverage miss."""
        ok, msg = js_coverage.classify(None)
        assert ok is True
        assert 'no JS coverage' in msg

    def test_exactly_the_baseline_holds(self):
        ok, _ = js_coverage.classify(js_coverage.BASELINE_PCT)
        assert ok is True

    @pytest.mark.parametrize('delta', [0.01, 0.1, 1.0])
    def test_below_the_baseline_fails(self, delta):
        ok, msg = js_coverage.classify(js_coverage.BASELINE_PCT - delta)
        assert ok is False
        assert 'below' in msg

    def test_inside_the_tolerance_holds(self):
        """Statements moving between files must not trip the gate."""
        ok, _ = js_coverage.classify(
            js_coverage.BASELINE_PCT + js_coverage.TOLERANCE_PCT)
        assert ok is True

    def test_beyond_the_tolerance_asks_for_a_raise(self):
        """A real tranche of tests should force the baseline forward."""
        measured = js_coverage.BASELINE_PCT + js_coverage.TOLERANCE_PCT + 0.01
        ok, msg = js_coverage.classify(measured)
        assert ok is False
        assert 'raise' in msg
        assert f'{measured:.1f}' in msg

    def test_baseline_is_a_measured_figure_not_an_aspiration(self):
        """Guards against someone setting a target here instead of a fact.

        The baseline records what the suite currently achieves. Setting it to
        a goal makes every run fail until the goal is met, which is how a gate
        gets switched off.
        """
        assert 0 < js_coverage.BASELINE_PCT < 100
        assert js_coverage.TOLERANCE_PCT > 0
