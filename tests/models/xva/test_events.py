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

"""Trigger simulation: each gauge's marginal is the market's, and the event
catalogue makes gauges trigger together."""

import math

import numpy as np
import pytest

from models.xva import HazardCurve
from models.xva.cir import CirFactor, ShiftedTrigger
from models.xva.events import TriggerModel, simulate
from models.xva.paths import factor_paths

LAMBDA = -math.log(0.98)
N = 40_000
HORIZON = 5.0


def _catalogue(rate=0.1, n=100):
    weights = np.full(n, 1.0 / n)
    g1, g2 = np.zeros(n, bool), np.zeros(n, bool)
    g1[:20], g2[10:30] = True, True
    return TriggerModel(rate, weights, {"G1": g1, "G2": g2})


def _run(model, sigma=0.0, lam=LAMBDA, seed=11):
    factor = CirFactor(0.5, sigma)
    triggers = {g: ShiftedTrigger(factor, HazardCurve.flat(lam)) for g in ("G1", "G2")}
    times = np.linspace(0.0, HORIZON, 121)
    rng = np.random.default_rng(seed)
    _, clock = factor_paths(factor, times, N, rng)
    return simulate(model, triggers, times, clock, rng)


def _assert_marginal(first, lam):
    p = 1 - math.exp(-lam * HORIZON)
    hit = np.mean(first <= HORIZON)
    assert abs(hit - p) < 4 * math.sqrt(p * (1 - p) / N), (hit, p)


@pytest.mark.parametrize("sigma", [0.0, 0.5])
@pytest.mark.parametrize("rate", [0.0, 0.05, 0.1, 0.2],
                         ids=["independent", "top-up", "near", "thinned"])
def test_each_gauge_has_the_market_marginal(rate, sigma):
    """Whatever the catalogue's own rate c_g, the marginal is the market's:
    thinning where c_g > lambda_g, a top-up where it is below."""
    model = _catalogue(rate) if rate else TriggerModel.independent()
    paths = _run(model, sigma)
    for gauge in ("G1", "G2"):
        _assert_marginal(paths.first_trigger[gauge], LAMBDA)


def test_shared_events_make_gauges_trigger_together():
    paths = _run(_catalogue(0.1))
    a, b = paths.first_trigger["G1"] <= HORIZON, paths.first_trigger["G2"] <= HORIZON
    assert np.mean(a & b) > 3 * np.mean(a) * np.mean(b)


def test_independent_gauges_do_not():
    paths = _run(TriggerModel.independent())
    a, b = paths.first_trigger["G1"] <= HORIZON, paths.first_trigger["G2"] <= HORIZON
    assert np.mean(a & b) == pytest.approx(np.mean(a) * np.mean(b), abs=0.002)


def test_catalogue_rate_and_unknown_gauges():
    model = _catalogue(0.1)
    assert model.catalogue_rate("G1") == pytest.approx(0.1 * 0.2)
    assert model.catalogue_rate("G9") == 0.0


def test_from_catalogue_reads_flags_at_the_severe_level():
    class Catalogue:
        coverage = 0.5
        weights = np.array([0.5, 0.5])

        def flood_flags(self, gauge, level):
            return np.array([level < 3.0, True])

    model = TriggerModel.from_catalogue(Catalogue(), {"G1": 2.0}, 4.0)
    assert model.event_rate == 2.0
    assert model.flags["G1"].tolist() == [True, True]


def test_event_times_lie_inside_the_horizon():
    paths = _run(_catalogue(0.5))
    assert paths.event_times.size > 0
    assert np.all((paths.event_times >= 0) & (paths.event_times <= HORIZON))


@pytest.mark.parametrize("sigma", [0.0, 0.5])
def test_a_term_structure_marginal_is_the_markets(sigma):
    """Plan §16: shared catalogue events at the curve's lowest hazard, the rest
    as the shift; the marginal is the market curve whatever the shape."""
    curve = HazardCurve([1.0, 3.0], [0.006, 0.012])
    factor = CirFactor(0.5, sigma)
    triggers = {"G1": ShiftedTrigger(factor, curve)}
    times = np.linspace(0.0, HORIZON, 121)
    rng = np.random.default_rng(23)
    _, clock = factor_paths(factor, times, N, rng)
    first = simulate(_catalogue(0.1), triggers, times, clock, rng, gauges=["G1"]).first_trigger["G1"]
    for t in (1.0, 3.0, HORIZON):
        p = 1 - float(curve.survival(t))
        assert abs(np.mean(first <= t) - p) < 4 * math.sqrt(p * (1 - p) / N), t
