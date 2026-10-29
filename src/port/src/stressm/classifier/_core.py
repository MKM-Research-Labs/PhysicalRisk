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

"""GBM flood classifier training for the multi-storm stress pipeline.

v2.0 — Near-miss augmentation.  The previous classifier jumped from ~5% to ~95%
instantly because the training set lacked storms that APPROACH severe without
breaching it.  Now we synthesise near-miss hydrographs (peak 80–99% of severe)
that all carry label=0, giving the GBM gradient data in the transition zone.

v2.1 — Storm groups.  Every vector now carries the index of the storm it came
from (``groups``), so held-out scoring can split by storm rather than by row.
Near-miss hydrographs get negative group ids.  Training output is unchanged.
"""

import math
import time
from pathlib import Path

import numpy as np

from config.port import (
    LOG_END as _LOG_END,
    LOG_EPS as _LOG_EPS,
    NUM_CLASSIFIER_HOURS as _NUM_HOURS,
    NEARMISS_COUNT as _NEARMISS_COUNT,
)

from ._nearmiss import _generate_nearmiss_vectors


def hydrograph_vectors(levels, ref: float) -> list:
    """Feature vectors for one 168-hour hydrograph, labelled against ``ref``.

    Each row is ``[log(h/ref), log((t+1)/168), Δlog(h/ref), Δ²log(h/ref), flag]``
    where ``flag`` is 1 if the level reaches ``ref`` at or after hour t.  A
    non-positive ``ref`` uses the raw level and labels every hour 0.
    """
    if ref > 0:
        log_hs = [math.log(max(lv / ref, _LOG_EPS)) for lv in levels]
    else:
        log_hs = [math.log(max(lv, _LOG_EPS)) for lv in levels]

    rows = []
    for h in range(_NUM_HOURS):
        log_t = math.log((h + 1) / _LOG_END)
        delta      = log_hs[h] - log_hs[h - 1] if h > 0 else 0.0
        prev_delta = log_hs[h - 1] - log_hs[h - 2] if h > 1 else 0.0
        delta2     = delta - prev_delta

        future_max = max(levels[h:])
        flood_flag = 1 if (ref > 0 and future_max >= ref) else 0

        rows.append([
            round(log_hs[h], 6),
            round(log_t, 6),
            round(delta, 6),
            round(delta2, 6),
            flood_flag,
        ])
    return rows


def _nearmiss_groups(n_vectors: int) -> list:
    """Group ids -1, -2, ... for consecutive 168-hour near-miss hydrographs."""
    return [-1 - i // _NUM_HOURS for i in range(n_vectors)]


def build_gauge_training_set(
    sequences: list,
    gauge: dict,
    spatial_model,
    target_spatial_index: int,
    rng,
) -> dict:
    """Build the labelled training vectors for one gauge.

    Labels against ``severe_warning``; if no storm reaches it, relabels against
    ``flood_alert``.  Near-miss hydrographs are appended after the real storms.

    Returns:
        Dict with ``vector`` (rows as in :func:`hydrograph_vectors`), ``groups``
        (storm index per row, negative for near-miss), ``n_real`` (rows from
        real storms, which come first), ``label_level`` and ``label_name``.
    """
    from port.src.storm_multi.models.sequence_response import (
        SequenceGaugeParams, compute_sequence_gauge_response, _make_precip_series,
    )

    gid = gauge["gauge_id"]
    severe_l = gauge["severe_warning"]
    alert_l  = gauge["flood_alert"]
    warning_l = gauge["flood_warning"]

    gp = SequenceGaugeParams(
        gauge_id=gid,
        base_level=gauge["base_level"],
        flood_alert=alert_l,
        flood_warning=warning_l,
        severe_warning=severe_l,
    )

    def _real_vectors(ref):
        vectors, groups = [], []
        for i, seq in enumerate(sequences):
            catchment_precip = _make_precip_series(seq)
            gauge_precip_all = spatial_model.apply_to_sequence(seq, catchment_precip, rng=rng)
            levels = compute_sequence_gauge_response(
                seq, gp, precip_series=gauge_precip_all[target_spatial_index]
            )
            rows = hydrograph_vectors(levels, ref)
            vectors.extend(rows)
            groups.extend([i] * len(rows))
        return vectors, groups

    t0 = time.time()
    vectors, groups = _real_vectors(severe_l)
    flood_positive = sum(v[4] for v in vectors)

    total_v = len(vectors)
    flood_rate = flood_positive / total_v if total_v > 0 else 0
    print(f"  Real vectors: {total_v:,}  |  flood-positive: {flood_positive:,} "
          f"({flood_rate:.1%})  [{time.time()-t0:.1f}s]", flush=True)

    if flood_positive > 0:
        label_level = severe_l
        label_name = "severe_warning"
        n_real = len(vectors)
        # Near-miss augmentation: add synthetic hydrographs peaking at 80–99% of
        # severe.  These all carry label=0 and give the GBM gradient data in the
        # transition zone so P(flood) rises smoothly rather than jumping 5%→95%.
        if severe_l > 0:
            nm_rng = np.random.RandomState(rng.randint(0, 2**31))
            nearmiss = _generate_nearmiss_vectors(severe_l, gauge["base_level"], nm_rng)
            vectors.extend(nearmiss)
            groups.extend(_nearmiss_groups(len(nearmiss)))
            print(f"  Near-miss augmentation: +{len(nearmiss):,} sub-severe vectors "
                  f"({_NEARMISS_COUNT} hydrographs × {_NUM_HOURS}h)  "
                  f"→  total {len(vectors):,}", flush=True)
    else:
        # No severe events: fall back to flood_alert as the label threshold
        label_level = alert_l
        label_name = "flood_alert"
        print(f"  No severe events — relabelling against flood_alert ({alert_l:.2f} m)",
              flush=True)
        vectors, groups = _real_vectors(label_level)
        flood_positive = sum(v[4] for v in vectors)
        n_real = len(vectors)
        total_v = len(vectors)
        flood_rate = flood_positive / total_v if total_v > 0 else 0
        print(f"  Relabelled vectors: {total_v:,}  |  flood-positive: {flood_positive:,} "
              f"({flood_rate:.1%})", flush=True)

        # Near-miss augmentation against alert level
        if flood_positive > 0:
            nm_rng = np.random.RandomState(rng.randint(0, 2**31))
            nearmiss = _generate_nearmiss_vectors(alert_l, gauge["base_level"], nm_rng)
            vectors.extend(nearmiss)
            groups.extend(_nearmiss_groups(len(nearmiss)))
            print(f"  Near-miss (alert): +{len(nearmiss):,} sub-alert vectors "
                  f"→ total {len(vectors):,}", flush=True)

    return {
        "vector":      vectors,
        "groups":      groups,
        "n_real":      n_real,
        "label_level": label_level,
        "label_name":  label_name,
    }


def train_gauge_stressm_classifier(
    sequences: list,
    gauge: dict,
    spatial_model,
    target_spatial_index: int,
    output_dir: Path,
    rng,
    classifiers_dir: Path = None,
) -> dict:
    """
    Train a GBM flood classifier for one gauge using compound 168h hydrographs.

    Builds training vectors in the same format as stress.py so the classifier
    is directly comparable to the single-storm version:
      features: [log(h/s), log((t+1)/168), Δlog(h/s), Δ²log(h/s)]
      label:    1 if max(levels[h:]) >= severe_warning, else 0

    Sequences are processed one at a time (memory efficient). The classifier
    is saved to data/input/<catchment>/stressm/<gauge_id>.joblib.

    Args:
        sequences:             List of StormSequence objects.
        gauge:                 Parsed gauge dict (gauge_id, thresholds, etc.).
        spatial_model:         Fitted SpatialCorrelationModel.
        target_spatial_index:  Index of this gauge in the spatial model.
        output_dir:            Where to save the .joblib model.
        rng:                   np.random.RandomState for spatial sampling.

    Returns:
        Result dict from FloodClassifierTrainer.train_gauge().
    """
    from models.stress.flood_classifier import FloodClassifierTrainer

    gid = gauge["gauge_id"]
    stressm_dir = classifiers_dir if classifiers_dir else output_dir / "stressm"
    stressm_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  Training multi-storm GBM classifier for {gid}...", flush=True)
    training = build_gauge_training_set(
        sequences, gauge, spatial_model, target_spatial_index, rng)

    trainer = FloodClassifierTrainer(Path("_unused"), stressm_dir)
    gauge_data = {
        "gauge_id":      gid,
        "alert_level":   gauge["flood_alert"],
        "warning_level": gauge["flood_warning"],
        "severe_level":  training["label_level"],
        "vector":        training["vector"],
        "groups":        training["groups"],
    }
    result = trainer.train_gauge(gid, gauge_data)
    result["label_threshold"] = training["label_name"]
    result["label_level_m"] = training["label_level"]
    return result
