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
"""Tests for tools.flood_poly_fit -- how the v2.0 coefficients were produced.

The real fit reads every gauge's GBM and storm catalogue; here those are replaced by
synthetic states whose answer is known, so what is tested is the method: that it
recovers a monotone kernel it was shown, holds the slope constraint, and measures
on the storms it did not fit.
"""

import json
from types import SimpleNamespace

import numpy as np
import pytest
from tools.flood_poly_fit import __main__ as cli
from tools.flood_poly_fit import fit as f

from config.models import (
    flood_poly_coeffs,
    flood_poly_envelope,
    flood_poly_fit_slope_margin,
    flood_poly_level_floor,
    flood_poly_terms,
)

TRUTH = np.array(flood_poly_coeffs)


def _sample(n=4000, seed=3):
    rng = np.random.RandomState(seed)
    h = rng.uniform(np.log(flood_poly_level_floor), -1e-3, n)
    t = f.held_t(h, np.log((rng.randint(0, 168, n) + 1) / 168))   # storms only go where storms go
    return h, t, f._sigma(f.design(h, t) @ TRUTH)


def test_the_design_has_one_column_per_term():
    h, t = np.array([-0.5, -0.1]), np.array([-1.0, -0.2])
    F = f.design(h, t)
    assert F.shape == (2, len(flood_poly_terms))
    for col, (i, j) in enumerate(flood_poly_terms):
        assert F[:, col] == pytest.approx(h ** i * t ** j)


def test_the_slope_design_is_the_derivative_of_the_design():
    h, t, d = np.array([-0.6, -0.2]), np.array([-1.5, -0.3]), 1e-6
    numeric = (f.design(h + d, t) - f.design(h - d, t)) / (2 * d)
    assert f.design_dh(h, t) == pytest.approx(numeric, rel=1e-6, abs=1e-9)


def test_the_time_design_is_the_derivative_of_the_design():
    h, t, d = np.array([-0.6, -0.2]), np.array([-1.5, -0.3]), 1e-6
    numeric = (f.design(h, t + d) - f.design(h, t - d)) / (2 * d)
    assert f.design_dt(h, t) == pytest.approx(numeric, rel=1e-6, abs=1e-9)


def test_the_fit_holds_the_hour_at_the_envelope_as_the_model_does():
    from models.stress import flood_poly as model
    h = np.log([0.25, 0.4, 0.7, 0.95])
    t = np.full(4, np.log(1 / 168))
    assert f.held_t(h, t) == pytest.approx([max(t[0], model.envelope_t(x)) for x in h])
    late = np.full(4, np.log(150 / 168))
    assert (f.held_t(h, late) == late).all()


def test_the_envelope_rows_are_the_slope_along_the_envelope():
    from models.stress import flood_poly as model
    n = 5
    rows = f.envelope_rows(n)
    hh = np.log([r for r, _ in flood_poly_envelope])
    h = (hh[2] + hh[3]) / 2                          # the middle point of the third segment
    t = model.envelope_t(h)
    along = model.kernel_dh(h, t) + model.kernel_dt(h, t) * model.envelope_slope(h)
    assert rows[2 * n + n // 2] @ TRUTH == pytest.approx(along, rel=1e-9)
    assert rows.shape == ((len(hh) - 1) * n, len(flood_poly_terms))


def test_the_sigmoid_is_clamped():
    assert f._sigma(np.array([1e6, -1e6])) == pytest.approx([1.0, 0.0], abs=1e-12)


def test_the_fit_recovers_a_monotone_kernel_it_was_shown():
    h, t, g = _sample()
    coeffs, min_slope = f.fit(h, t, g)
    assert np.abs(f._sigma(f.design(h, t) @ coeffs) - g).max() < 0.01
    assert min_slope >= flood_poly_fit_slope_margin - 1e-6


def test_metrics_are_per_gauge_and_split_near_from_below():
    h, t, g = _sample(400)
    gauge = np.repeat([0, 1], 200)
    out = f.metrics(TRUTH, h, t, g, gauge, near=0.5)
    assert [m["gauge"] for m in out] == [0, 1]
    for m in out:
        assert m["near_mae"] == pytest.approx(0.0, abs=1e-12)
        assert set(m) == {"gauge", "near_mae", "near_bias", "near_over", "below_mae"}


def _catalogue(n_storms=6, per_storm=30, seed=5):
    rng = np.random.RandomState(seed)
    n = n_storms * per_storm
    X = np.column_stack([rng.uniform(-2.5, 0.2, n), np.log((rng.randint(0, 168, n) + 1) / 168),
                         rng.normal(size=n), rng.normal(size=n)])
    return SimpleNamespace(gauge_id="G1", X=X, groups=np.repeat(np.arange(n_storms), per_storm),
                           n_real=n)


def test_states_pool_the_gauges_below_severe_with_the_floor_applied(monkeypatch):
    import tools.flood_classifier_challenger._data as data
    from tools.wolfram_oracle.floodpoly import gbm
    gs = _catalogue()
    monkeypatch.setattr(gbm, "gauge_ids", lambda: ["G1"])
    monkeypatch.setattr(data, "load_catalogue", lambda ids, n_storms, seed: [gs])
    monkeypatch.setattr(gbm, "classifier", lambda gid: SimpleNamespace(
        predict_proba=lambda X: np.column_stack([np.zeros(len(X)), np.full(len(X), 0.3)])))
    h, t, g, gauge, is_fit = f.states(n_storms=6, seed=1)
    below = gs.X[:, 0] < 0
    assert len(h) == below.sum()
    assert h.min() >= np.log(flood_poly_level_floor)
    assert (g == 0.3).all() and (gauge == 0).all()
    assert 0 < is_fit.sum() < len(is_fit)          # half the storms fit, half measure


def test_the_command_writes_what_it_prints(monkeypatch, tmp_path, capsys):
    h, t, g = _sample(600)
    monkeypatch.setattr(f, "states", lambda n: (h, t, g, np.zeros(len(h), int),
                                                np.arange(len(h)) % 2 == 0))
    out = tmp_path / "fit.json"
    assert cli.main(["--storms", "10", "--out", str(out)]) == 0
    written = json.loads(out.read_text())
    assert written == json.loads(capsys.readouterr().out)
    assert len(written["coefficients"]) == len(flood_poly_terms)
    assert written["fit_states"] == written["test_states"] == 300
