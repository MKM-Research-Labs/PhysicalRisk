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

"""Master scale and the Basel IRB corporate risk weight."""

import pytest

from config.capital import IRB_PD_FLOOR, MASTER_SCALE
from models.capital import grade_for_pd, irb_corporate_rw


def test_irb_rw_matches_basel_reference_value():
    # Basel II illustrative table: corporate, PD 1%, LGD 45%, M 2.5 -> 92.32%
    assert irb_corporate_rw(0.01, 0.45, 2.5) == pytest.approx(0.9232, abs=5e-4)


def test_irb_rw_applies_pd_floor():
    assert irb_corporate_rw(0.0, 0.45, 2.5) == irb_corporate_rw(IRB_PD_FLOOR, 0.45, 2.5)


def test_irb_rw_rises_with_pd_and_maturity():
    assert irb_corporate_rw(0.002, 0.45, 2.5) < irb_corporate_rw(0.01, 0.45, 2.5)
    assert irb_corporate_rw(0.01, 0.45, 1.0) < irb_corporate_rw(0.01, 0.45, 5.0)


@pytest.mark.parametrize("pd,grade", [(0.0030, "BBB-"), (0.0035, "BBB-"),
                                      (0.0036, "BB+"), (0.0060, "BB+")])
def test_master_scale_boundaries(pd, grade):
    assert grade_for_pd(pd)[0] == grade


def test_investment_grade_boundary_is_sa_cliff():
    assert grade_for_pd(0.0035)[1] == 0.75 and grade_for_pd(0.0036)[1] == 1.00


def test_master_scale_bounds_ascend_and_end_at_certainty():
    bounds = [upper for _, upper, _ in MASTER_SCALE]
    assert bounds == sorted(bounds) and bounds[-1] == 1.0


def test_pd_outside_the_scale_is_refused():
    with pytest.raises(ValueError, match="outside master scale"):
        grade_for_pd(1.5)
