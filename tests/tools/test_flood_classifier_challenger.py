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

"""Tests for tools.flood_classifier_challenger, the GBM vs Random Forest benchmark.

The storm-grouped training set is checked against the production builder (same
vectors, storms kept whole, near-miss marked synthetic); the surface-shape,
paired-statistics and decision-rule pieces against hand-built cases; and one
small synthetic run end to end, with the models shrunk so it runs in seconds.
"""

import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from tools.flood_classifier_challenger import _benchmark, _candidates, _decision, run_benchmark

from config.models import CHALLENGER_RESULTS_JSON, CHALLENGER_RESULTS_TEX
from config.port import NUM_CLASSIFIER_HOURS as H
from models.stress.flood_poly import p_flood_poly
from port.src.stressm.classifier import _core, _nearmiss


def _hydro(peak, base=1.0, centre=60, width=25.0):
    h = np.arange(H)
    return list(base + (peak - base) * np.exp(-((h - centre) / width) ** 2))


class TestHydrographVectors:
    def test_label_is_one_until_the_last_hour_at_or_above_the_threshold(self):
        rows = _core.hydrograph_vectors(_hydro(4.0), 3.0)
        flags = [r[4] for r in rows]
        last = max(i for i, lv in enumerate(_hydro(4.0)) if lv >= 3.0)
        assert flags[:last + 1] == [1] * (last + 1)
        assert flags[last + 1:] == [0] * (H - last - 1)

    def test_a_storm_below_the_threshold_is_all_zero(self):
        assert {r[4] for r in _core.hydrograph_vectors(_hydro(2.9), 3.0)} == {0}

    def test_features_are_log_level_and_log_time(self):
        rows = _core.hydrograph_vectors(_hydro(4.0), 3.0)
        assert len(rows) == H
        assert rows[10][0] == pytest.approx(np.log(_hydro(4.0)[10] / 3.0), abs=1e-6)
        assert rows[H - 1][1] == pytest.approx(0.0, abs=1e-6)


class _Spatial:
    def apply_to_sequence(self, seq, precip, rng=None):
        return [np.full(H, rng.uniform())] * 2


def _response(seq, gp, precip_series=None):
    return _hydro(gp.base_level + seq * (1 + precip_series[0]))


@pytest.fixture
def stub_response():
    import port.src.storm_multi.models.sequence_response as sr
    with patch.object(sr, "compute_sequence_gauge_response", _response), \
         patch.object(sr, "_make_precip_series", lambda s: None), \
         patch.object(_nearmiss, "_NEARMISS_COUNT", 3):
        yield


GAUGE = {"gauge_id": "G", "severe_warning": 3.0, "flood_alert": 2.0,
         "flood_warning": 2.5, "base_level": 1.0}


class TestTrainingSet:
    def test_rows_carry_their_storm_and_near_miss_is_negative(self, stub_response):
        seqs = list(np.linspace(0.5, 3.5, 12))
        ts = _core.build_gauge_training_set(seqs, GAUGE, _Spatial(), 1,
                                            np.random.RandomState(3))
        groups = np.asarray(ts["groups"])
        assert ts["label_name"] == "severe_warning"
        assert ts["n_real"] == 12 * H
        assert list(groups[:ts["n_real"]]) == [i for i in range(12) for _ in range(H)]
        assert list(groups[ts["n_real"]:]) == [-1 - i for i in range(3) for _ in range(H)]
        assert len(groups) == len(ts["vector"])

    def test_falls_back_to_alert_when_no_storm_reaches_severe(self, stub_response):
        ts = _core.build_gauge_training_set(list(np.linspace(0.5, 0.9, 5)),
                                            {**GAUGE, "severe_warning": 50.0},
                                            _Spatial(), 1, np.random.RandomState(3))
        assert ts["label_name"] == "flood_alert"
        assert sum(v[4] for v in ts["vector"][:ts["n_real"]]) > 0

    def test_production_training_receives_the_same_vectors(self, stub_response, tmp_path):
        seqs = list(np.linspace(0.5, 3.5, 12))
        seen = {}

        def capture(self, gid, gauge_data, test_size=0.2):
            seen.update(gauge_data)
            return {"status": "trained"}

        from models.stress.flood_classifier import FloodClassifierTrainer
        with patch.object(FloodClassifierTrainer, "train_gauge", capture):
            _core.train_gauge_stressm_classifier(seqs, GAUGE, _Spatial(), 1, tmp_path,
                                                 np.random.RandomState(3))
        ts = _core.build_gauge_training_set(seqs, GAUGE, _Spatial(), 1,
                                            np.random.RandomState(3))
        assert seen["vector"] == ts["vector"]
        assert seen["groups"] == ts["groups"]


class TestCandidates:
    def test_flood_polynomial_matches_production(self):
        X = np.array([[np.log(w / 3.0), np.log((h + 1) / H), 0, 0]
                      for w in (2.0, 2.9, 3.3) for h in (0, 80, 167)])
        p = _candidates.make_model("poly", {}, 0).predict(X)
        expected = [p_flood_poly(w, h, 3.0) for w in (2.0, 2.9, 3.3) for h in (0, 80, 167)]
        assert p == pytest.approx(expected, abs=1e-6)

    def test_calibrated_forest_returns_probabilities(self):
        rng = np.random.RandomState(0)
        X = rng.normal(size=(600, 4))
        y = (X[:, 0] + rng.normal(scale=0.5, size=600) > 0).astype(int)
        groups = np.repeat(np.arange(60), 10)
        m = _candidates.make_model("rf_cal", {"n_estimators": 20}, 0).fit(X, y, groups)
        p = m.predict(X)
        assert p.min() >= 0 and p.max() <= 1


class TestShapeAndBootstrap:
    def test_monotone_surface_has_no_violations(self):
        surf = np.repeat(np.linspace(0, 1, 10)[:, None], 4, axis=1)
        assert _benchmark.shape_metrics(surf.ravel(), 10)["monotone_violations"] == 0

    def test_a_dip_in_level_is_a_violation(self):
        surf = np.repeat(np.linspace(0, 1, 10)[:, None], 4, axis=1)
        surf[5, 2] = 0.1
        s = _benchmark.shape_metrics(surf.ravel(), 10)
        assert s["monotone_violations"] == 1
        assert s["max_fall"] == pytest.approx(surf[4, 2] - 0.1)

    def test_storm_bootstrap_keeps_storms_whole(self):
        groups = np.repeat(np.arange(8), 5)
        rows, new_groups = _benchmark._bootstrap_rows(groups, np.arange(40),
                                                      np.random.RandomState(1))
        assert len(rows) == 40
        for g in np.unique(new_groups):
            assert len(set(groups[rows[new_groups == g]])) == 1


def _models(champ_brier, best_brier, champ_sd, best_sd, champ_mono, best_mono,
            better=False):
    def m(b, sd, mono, **kw):
        return {"accuracy": {"brier": b}, "seed_grid_sd": sd, "bootstrap_grid_sd": sd,
                "monotone_violation_rate": mono, **kw}
    return {"gbm_prod": m(champ_brier, champ_sd, champ_mono),
            "rf": m(best_brier, best_sd, best_mono,
                    vs_champion={"challenger_better": better}),
            "poly": m(0.5, None, 0.0, vs_champion={"challenger_better": False})}


class TestDecision:
    def test_paired_ci_is_positive_when_the_challenger_is_better(self):
        ci = _decision.paired_ci(np.full(200, 0.10), np.full(200, 0.08), 0)
        assert ci["mean"] == pytest.approx(0.02)
        assert ci["ci_low"] > 0

    def test_retain_when_the_gbm_passes_all_three(self):
        d = _decision.decide(_models(0.050, 0.050, 0.001, 0.010, 0.0, 0.02))
        assert d["best_challenger"] == "rf"
        assert d["outcome"] == "retain"

    def test_replace_when_the_gbm_fails_all_three(self):
        d = _decision.decide(_models(0.060, 0.050, 0.050, 0.001, 0.2, 0.0, better=True))
        assert d["outcome"] == "replace"

    def test_escalate_when_accuracy_and_stability_disagree(self):
        d = _decision.decide(_models(0.060, 0.050, 0.001, 0.010, 0.0, 0.0, better=True))
        assert d["tests"] == {"accuracy": False, "stability": True, "shape": True}
        assert d["outcome"] == "escalate"


@pytest.fixture
def fast_models():
    """Shrink every candidate so a synthetic run takes seconds (in-process only:
    the patches do not reach worker processes, so the run uses n_jobs=1)."""
    small = {"gbm": {"n_estimators": [20], "max_depth": [2, 3]},
             "rf": {"min_samples_leaf": [20, 50]}, "logit": {"C": [1.0]}}
    with patch.object(_candidates, "GBM_PARAMS", {"n_estimators": 20, "max_depth": 2,
                                                  "learning_rate": 0.2,
                                                  "min_samples_leaf": 20}), \
         patch.object(_candidates, "CHALLENGER_RF_PARAMS", {"n_estimators": 15,
                                                            "max_features": 2,
                                                            "min_samples_leaf": 20}), \
         patch.object(_benchmark, "CHALLENGER_SEARCH_SPACE", small), \
         patch.object(_nearmiss, "_NEARMISS_COUNT", 10):
        yield


class TestEndToEnd:
    def test_synthetic_run_scores_every_model_and_writes_reports(self, fast_models, tmp_path):
        out = run_benchmark(synthetic=2, n_storms=40, folds=3, tune_trials=2, seeds=2,
                            bootstraps=2, seed=5, out_dir=tmp_path, n_jobs=1,
                            log=lambda *a: None)
        assert out["meta"]["n_gauges_scored"] == 2
        for g in out["gauges"]:
            for name, p in g["_oof"].items():
                assert not np.isnan(p).any(), name
            assert len(g["_y"]) == 40 * H
        assert set(out["models"]) == set(_candidates.CANDIDATES)
        assert out["models"]["poly"]["seed_grid_sd"] is None
        assert out["models"]["logit"]["seed_grid_sd"] == 0.0
        assert out["decision"]["outcome"] in {"retain", "replace", "escalate"}
        saved = json.loads(Path(tmp_path, CHALLENGER_RESULTS_JSON).read_text())
        assert "_oof" not in saved["gauges"][0]
        tex = Path(tmp_path, CHALLENGER_RESULTS_TEX).read_text()
        assert "GBM (production)" in tex and "Decision:" in tex
