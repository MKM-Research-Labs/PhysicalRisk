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

"""Tests for the lineage-drift ratchet.

The check this guards previously called ``warnings.warn()`` and could not fail
on any dataset — 23 mismatches were printed and passed over on every run. The
ratchet accepts that level and freezes it, because asserting outright would put
the build red until a ~24-hour regeneration.
"""

import pytest

from tests.data.test_id_consistency_pipeline_part2 import (
    KNOWN_HASH_DRIFT,
    assert_drift_within_baseline,
)


class TestRatchet:
    def test_at_the_baseline_passes(self):
        assert_drift_within_baseline(["x"] * 5, 5)

    def test_no_drift_against_a_zero_baseline_passes(self):
        assert_drift_within_baseline([], 0)

    def test_new_drift_fails(self):
        """The point of the exercise: more drift than accepted must go red."""
        with pytest.raises(AssertionError, match="above the accepted baseline"):
            assert_drift_within_baseline(["a", "b", "c"], 2)

    def test_cleared_drift_also_fails_and_says_what_to_do(self):
        """Fewer mismatches must fail too, or the baseline stays high for ever
        and a later regression back up to it would pass unnoticed."""
        with pytest.raises(AssertionError, match="lower KNOWN_HASH_DRIFT to 1"):
            assert_drift_within_baseline(["a"], 5)

    def test_failure_names_the_drifted_outputs(self):
        with pytest.raises(AssertionError, match="fire/fire.json"):
            assert_drift_within_baseline(["fire/fire.json: recorded=aaa current=bbb"], 0)

    def test_long_lists_are_truncated_with_a_count(self):
        """A hundred names would bury the instruction at the end."""
        with pytest.raises(AssertionError, match=r"and 15 more"):
            assert_drift_within_baseline([f"o{i}" for i in range(25)], 0)

    def test_regeneration_command_is_given(self):
        with pytest.raises(AssertionError, match=r"phys\.py port"):
            assert_drift_within_baseline(["a"], 0)


class TestBaselineValue:
    def test_baseline_is_a_non_negative_int(self):
        assert isinstance(KNOWN_HASH_DRIFT, int) and KNOWN_HASH_DRIFT >= 0

    def test_baseline_is_documented_as_temporary(self):
        """The constant carries the reasoning for the accepted level; losing
        that comment would turn a ratchet into a permanent exemption."""
        import pathlib
        src = pathlib.Path(
            "tests/data/test_id_consistency_pipeline_part2.py").read_text()
        i = src.index("KNOWN_HASH_DRIFT =")
        preamble = src[max(0, i - 900):i]
        assert "ratchet" in preamble
        assert "phys.py port" in preamble
