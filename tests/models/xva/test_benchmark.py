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

"""WP1 exit test: the analytic engine against an independent implementation.

Two benchmarks. The reference re-implementation (_reference) shares no
code with the engine and integrates adaptively; the engine must agree to 1e-8
relative (plan §5, WP1). The Monte Carlo test prices CVA and DVA in Green's
*expectation* form -- sampling the three default times directly -- and checks
that the *replication* integrals equal it, which is Green's Ch. 3 result.
"""

import math

import numpy as np
import pytest

from models.xva import analytic

from ._fixtures import HUMPED, case

TOLERANCE = 1e-8


@pytest.mark.parametrize("buyer", [True, False])
@pytest.mark.parametrize("curve", [None, HUMPED], ids=["flat", "humped"])
def test_engine_matches_the_reference_implementation(buyer, curve):
    trade, market, cfg, ref = case(buyer=buyer, curve=curve)
    engine = analytic.xva(trade, market, cfg)
    for view, expected in (("one_bond", ref.one_bond()),
                           ("semi_replication", ref.semi_replication())):
        for term, value in expected.items():
            assert engine[view][term] == pytest.approx(value, rel=TOLERANCE), (view, term)


def test_long_settlement_lag_and_low_spread_still_match():
    """A 60-day lag and a deep in-the-money buyer stress the pending-payout term."""
    trade, market, cfg, ref = case(buyer=True, spread=0.0050, settlement_days=60)
    engine = analytic.xva(trade, market, cfg)
    expected = ref.semi_replication()
    for term in ("cva", "dva", "fca"):
        assert engine["semi_replication"][term] == pytest.approx(expected[term], rel=TOLERANCE)


def _expectation_form(ref, n_paths, seed):
    """CVA and DVA as E[loss at the first default], by sampling default times."""
    rng = np.random.default_rng(seed)
    tau_e = rng.exponential(1 / ref.lam_e, n_paths)
    tau_c = rng.exponential(1 / ref.lam_c, n_paths)
    tau_b = rng.exponential(1 / ref.lam_b, n_paths)
    horizon = ref.T + ref.lag
    first = np.minimum(tau_c, tau_b)
    hit = first <= horizon
    losses = {"cva": np.zeros(n_paths), "dva": np.zeros(n_paths)}
    for i in np.flatnonzero(hit):
        tau = first[i]
        if tau_e[i] > tau:
            state = ref.v(tau) if tau < ref.T else 0.0
        elif tau_e[i] > tau - ref.lag and tau_e[i] <= ref.T:
            state = ref.w * ref.n * ref.df(tau_e[i] + ref.lag) / ref.df(tau)
        else:
            state = 0.0
        disc = ref.df(tau)
        if tau_c[i] < tau_b[i]:
            losses["cva"][i] = -(1 - ref.rec_c) * disc * max(state, 0.0)
        else:
            losses["dva"][i] = -(1 - ref.rec_b) * disc * min(state, 0.0)
    return {k: (v.mean(), v.std(ddof=1) / math.sqrt(n_paths)) for k, v in losses.items()}


@pytest.mark.parametrize("buyer", [True, False])
def test_replication_equals_expectation(buyer):
    """Green derives CVA by expectation (3.44) and by replication (3.70-3.71)
    and shows they agree; so must this implementation, within 4 standard errors.
    A 20-day lag makes the pending-payout state frequent enough to test."""
    trade, market, cfg, ref = case(buyer=buyer, settlement_days=20, lam_c=0.05)
    engine = analytic.xva(trade, market, cfg)["semi_replication"]
    mc = _expectation_form(ref, n_paths=200_000, seed=20261009)
    for term in ("cva", "dva"):
        mean, se = mc[term]
        assert abs(engine[term] - mean) < 4 * se, (term, engine[term], mean, se)
