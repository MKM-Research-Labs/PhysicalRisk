# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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
    from port.src.storm_multi.models.sequence_response import (
        SequenceGaugeParams, compute_sequence_gauge_response, _make_precip_series,
    )
    from models.stress.flood_classifier import FloodClassifierTrainer

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

    stressm_dir = classifiers_dir if classifiers_dir else output_dir / "stressm"
    stressm_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  Training multi-storm GBM classifier for {gid}...", flush=True)
    t0 = time.time()

    vectors = []
    flood_positive = 0

    for seq in sequences:
        catchment_precip = _make_precip_series(seq)
        gauge_precip_all = spatial_model.apply_to_sequence(seq, catchment_precip, rng=rng)
        levels = compute_sequence_gauge_response(
            seq, gp, precip_series=gauge_precip_all[target_spatial_index]
        )

        if severe_l > 0:
            log_hs = [math.log(max(lv / severe_l, _LOG_EPS)) for lv in levels]
        else:
            log_hs = [math.log(max(lv, _LOG_EPS)) for lv in levels]

        for h in range(_NUM_HOURS):
            log_t = math.log((h + 1) / _LOG_END)
            delta      = log_hs[h] - log_hs[h - 1] if h > 0 else 0.0
            prev_delta = log_hs[h - 1] - log_hs[h - 2] if h > 1 else 0.0
            delta2     = delta - prev_delta

            future_max = max(levels[h:]) if h < _NUM_HOURS else levels[h]
            flood_flag = 1 if (severe_l > 0 and future_max >= severe_l) else 0
            if flood_flag:
                flood_positive += 1

            vectors.append([
                round(log_hs[h], 6),
                round(log_t, 6),
                round(delta, 6),
                round(delta2, 6),
                flood_flag,
            ])

    total_v = len(vectors)
    flood_rate = flood_positive / total_v if total_v > 0 else 0
    print(f"  Real vectors: {total_v:,}  |  flood-positive: {flood_positive:,} "
          f"({flood_rate:.1%})  [{time.time()-t0:.1f}s]", flush=True)

    # Near-miss augmentation: add synthetic hydrographs peaking at 80–99% of
    # severe.  These all carry label=0 and give the GBM gradient data in the
    # transition zone so P(flood) rises smoothly rather than jumping 5%→95%.
    if severe_l > 0 and flood_positive > 0:
        nm_rng = np.random.RandomState(rng.randint(0, 2**31))
        nearmiss = _generate_nearmiss_vectors(severe_l, gauge["base_level"], nm_rng)
        vectors.extend(nearmiss)
        nm_count = len(nearmiss)
        total_v = len(vectors)
        print(f"  Near-miss augmentation: +{nm_count:,} sub-severe vectors "
              f"({_NEARMISS_COUNT} hydrographs × {_NUM_HOURS}h)  "
              f"→  total {total_v:,}", flush=True)

    # If no severe events, fall back to flood_alert as the label threshold
    if flood_positive == 0:
        label_level = alert_l
        label_name = "flood_alert"
        print(f"  No severe events — relabelling against flood_alert ({alert_l:.2f} m)",
              flush=True)
        vectors = []
        flood_positive = 0
        for seq in sequences:
            catchment_precip = _make_precip_series(seq)
            gauge_precip_all = spatial_model.apply_to_sequence(seq, catchment_precip, rng=rng)
            levels = compute_sequence_gauge_response(
                seq, gp, precip_series=gauge_precip_all[target_spatial_index]
            )
            ref = label_level
            log_hs = [math.log(max(lv / ref, _LOG_EPS)) for lv in levels]
            for h in range(_NUM_HOURS):
                log_t = math.log((h + 1) / _LOG_END)
                delta      = log_hs[h] - log_hs[h - 1] if h > 0 else 0.0
                prev_delta = log_hs[h - 1] - log_hs[h - 2] if h > 1 else 0.0
                delta2     = delta - prev_delta
                future_max = max(levels[h:]) if h < _NUM_HOURS else levels[h]
                flood_flag = 1 if future_max >= ref else 0
                if flood_flag:
                    flood_positive += 1
                vectors.append([
                    round(log_hs[h], 6), round(log_t, 6),
                    round(delta, 6), round(delta2, 6), flood_flag,
                ])
        total_v = len(vectors)
        flood_rate = flood_positive / total_v if total_v > 0 else 0
        print(f"  Relabelled vectors: {total_v:,}  |  flood-positive: {flood_positive:,} "
              f"({flood_rate:.1%})", flush=True)

        # Near-miss augmentation against alert level
        if flood_positive > 0:
            nm_rng = np.random.RandomState(rng.randint(0, 2**31))
            nearmiss = _generate_nearmiss_vectors(alert_l, gauge["base_level"], nm_rng)
            vectors.extend(nearmiss)
            print(f"  Near-miss (alert): +{len(nearmiss):,} sub-alert vectors "
                  f"→ total {len(vectors):,}", flush=True)
    else:
        label_level = severe_l
        label_name = "severe_warning"

    trainer = FloodClassifierTrainer(Path("_unused"), stressm_dir)
    gauge_data = {
        "gauge_id":      gid,
        "alert_level":   alert_l,
        "warning_level": warning_l,
        "severe_level":  label_level,
        "vector":        vectors,
    }
    result = trainer.train_gauge(gid, gauge_data)
    result["label_threshold"] = label_name
    result["label_level_m"] = label_level
    return result
