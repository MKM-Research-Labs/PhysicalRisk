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

"""Coverage tests for property_resilience.flood_compliance edge branches: the
top elevation band, the None ordinal, and the missing basement strategy.

(The post-loop `return 1.0` at line 27 is unreachable — the band table ends in
`(float("inf"), 1.00)`, so every finite elevation matches the inf band first.)"""

from port.rand.shared.property_resilience import flood_compliance as fc


class TestFloodComplianceBranches:
    def test_high_elevation_is_fully_compliant(self):
        # A 6m+ elevation matches the top (inf) band -> 1.0.
        assert fc._elevation_to_compliance(9999.0) == 1.0

    def test_ordinal_none_returns_default_missing(self):
        assert fc._ordinal_5level_compliance(None) == fc.DEFAULT_MISSING_COMPLIANCE  # line 33

    def test_lower_level_design_missing_strategy_returns_default(self):
        # Empty record -> BasementFloodStrategy resolves to None -> default.
        out = fc.compute_compliance("lower_level_flood_compatible_design", {})
        assert out == fc.DEFAULT_MISSING_COMPLIANCE  # line 92
