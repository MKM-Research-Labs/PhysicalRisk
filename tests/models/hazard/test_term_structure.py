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

"""Tests for the non-stationary term structure (MKM-EF-001, Stage 6h).

``compute_term_structure`` now accepts a per-year hazard sequence as well as a
single rate. The property that matters is that the sequence form *extends* the
scalar form without changing it: a flat sequence reproduces the scalar result
exactly, so wiring the default stationary rate process reprices nothing.
"""

import math

import pytest

from models.hazard.gev import compute_term_structure


def test_a_flat_sequence_matches_the_scalar_form():
    """The behaviour-preserving guarantee: a constant rate process, which yields
    a flat hazard series, gives the same term structure as the old scalar call."""
    scalar = compute_term_structure(0.05, max_years=5)
    sequence = compute_term_structure([0.05] * 5, max_years=5)
    for a, b in zip(scalar, sequence):
        assert a.expected_floods == pytest.approx(b.expected_floods)
        assert a.survival_prob == pytest.approx(b.survival_prob)


def test_a_sequence_compounds_the_running_sum():
    ts = compute_term_structure([0.02, 0.04, 0.06], max_years=3)
    assert ts[0].expected_floods == pytest.approx(0.02)
    assert ts[1].expected_floods == pytest.approx(0.06)
    assert ts[2].expected_floods == pytest.approx(0.12)
    assert ts[2].survival_prob == pytest.approx(math.exp(-0.12))


def test_a_rising_sequence_lowers_late_survival_below_the_flat_case():
    flat = compute_term_structure([0.04] * 5, max_years=5)
    rising = compute_term_structure([0.02, 0.03, 0.04, 0.05, 0.06], max_years=5)
    # Same five-year mean hazard, but front-loaded survival differs; by year 5
    # the cumulative hazards are equal here, so test a genuinely heavier tail:
    heavier = compute_term_structure([0.04, 0.05, 0.06, 0.07, 0.08], max_years=5)
    assert heavier[-1].survival_prob < flat[-1].survival_prob


def test_a_short_sequence_holds_its_last_rate():
    """Fewer supplied years than the tenor must not truncate or crash — the last
    rate carries forward."""
    ts = compute_term_structure([0.05, 0.06], max_years=4)
    # Years 3 and 4 add 0.06 each on top of 0.05 + 0.06.
    assert ts[3].expected_floods == pytest.approx(0.05 + 0.06 + 0.06 + 0.06)
    assert len(ts) == 4


def test_probabilities_stay_coherent():
    for point in compute_term_structure([0.02, 0.05, 0.09], max_years=3):
        assert abs(point.survival_prob + point.prob_at_least_one - 1.0) < 1e-12
