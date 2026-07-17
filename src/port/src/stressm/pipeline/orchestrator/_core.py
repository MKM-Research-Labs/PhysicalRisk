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

"""
Multi-storm stress pipeline orchestrator (--stressm).

Pipeline stages
---------------
1. Generate sequences -> storm_sequences.json + sequences_summary.json
2. Load gauge portfolio  -> SequenceGaugeParams + lat/lon per gauge
3. Build SpatialCorrelationModel from gauge locations
4. For each sequence: compute spatial compound gauge responses
5. Write output files + optional classifier training
"""

import logging
import time
from pathlib import Path
from typing import Optional

import numpy as np

import database

from ...gauge_parser import (
    _extract_gauges,
    _load_gaugehd_baselines,
    _parse_gauge,
    _seasonal_base_level,
)
from ...gaugets_writer import build_summary
from .. import stages
from ._responses import compute_sequence_records

logger = logging.getLogger(__name__)


def generate_stressm(
    input_dir: Path,
    output_dir: Path,
    count: int = 20_000,
    catchment_id: str = "thames",
    seed: int = 42,
    verbose: bool = False,
    gauge_id: Optional[str] = None,
    train_classifier: bool = False,
) -> dict:
    """
    Run the full multi-storm stress pipeline.

    Args:
        input_dir:         data/input/<catchment>/
        output_dir:        data/input/<catchment>/ — used for classifier model output
        count:             Number of sequences to generate (default 10,000)
        catchment_id:      Catchment identifier string
        seed:              Random seed for reproducibility
        verbose:           Extra logging
        gauge_id:          If set, restrict gauge response computation to this one gauge
        train_classifier:  If True, train a GBM flood classifier per gauge.

    Returns:
        Summary dict with generation and response statistics.
    """
    from port.src.storm_multi.generators.batch_generator import generate_event_set
    from port.src.storm_multi.models.sequence_response import (
        SequenceGaugeParams,
        _make_precip_series,
        compute_sequence_gauge_response,
    )
    from port.src.storm_multi.models.spatial_correlation import SpatialCorrelationModel
    from port.src.storm_multi.utils.serialization import (
        SEQUENCES_FILENAME,
        save_sequences,
        save_summary,
    )

    input_dir = Path(input_dir)
    rng = np.random.RandomState(seed)

    # ------------------------------------------------------------------
    # Stage 1: Generate sequences
    # ------------------------------------------------------------------
    t0 = time.time()
    print(f"  Generating {count:,} storm sequences...", flush=True)
    sequences = generate_event_set(count=count, catchment_id=catchment_id, seed=seed)

    save_sequences(sequences, catchment_id)
    save_summary(sequences, catchment_id)

    type_counts: dict = {}
    for s in sequences:
        type_counts[s.sequence_type] = type_counts.get(s.sequence_type, 0) + 1

    t1 = time.time()
    print(f"  {count:,} sequences  ->  {SEQUENCES_FILENAME}  ({t1 - t0:.1f}s)", flush=True)
    tc_str = "  ".join(f"{k}: {v:,}" for k, v in sorted(type_counts.items()))
    print(f"  Types: {tc_str}", flush=True)

    # ------------------------------------------------------------------
    # Stage 2: Load gauge portfolio
    # ------------------------------------------------------------------
    gauge_json = database.get_gauge_portfolio(catchment_id)
    if not gauge_json:
        logger.warning("gauge portfolio not found for %s — skipping spatial responses",
                       catchment_id)
        return build_summary(sequences, type_counts, gauge_params_list=[], t_start=t0)

    # Load historical baselines from gaugehd (mean daily water level per gauge)
    baselines = _load_gaugehd_baselines(catchment_id)
    if baselines:
        print(f"  Loaded {len(baselines)} gauge baselines from gaugehd/", flush=True)
    else:
        print("  No gaugehd data found — using heuristic base levels (0.35 x alert)", flush=True)

    raw_gauges = _extract_gauges(gauge_json)
    all_gauges_list = [parsed for rec in raw_gauges
                       if (parsed := _parse_gauge(rec, baselines)) is not None]

    n_all = len(all_gauges_list)
    print(f"  Loaded {n_all} gauges from gauge.json", flush=True)

    if n_all == 0:
        logger.warning("No valid gauges parsed from gauge.json")
        return build_summary(sequences, type_counts, gauge_params_list=[], t_start=t0)

    # Single-gauge mode: validate and filter
    single_gauge_mode = gauge_id is not None
    if single_gauge_mode:
        matched = [g for g in all_gauges_list if g["gauge_id"] == gauge_id]
        if not matched:
            available = [g["gauge_id"] for g in all_gauges_list]
            raise ValueError(
                f"Gauge '{gauge_id}' not found in gauge.json.\n"
                f"Available IDs: {', '.join(available[:10])}"
                + (" ..." if len(available) > 10 else "")
            )
        gauge_params_list = matched
        print(f"  Single-gauge mode: {gauge_id}", flush=True)
    else:
        gauge_params_list = all_gauges_list

    # ------------------------------------------------------------------
    # Stage 3: Build spatial correlation model (always uses all gauges)
    # ------------------------------------------------------------------
    all_locations = [(g["lat"], g["lon"]) for g in all_gauges_list]
    spatial_model = SpatialCorrelationModel(all_locations)
    all_gauge_ids = [g["gauge_id"] for g in all_gauges_list]

    if single_gauge_mode:
        target_indices = [all_gauge_ids.index(g["gauge_id"]) for g in gauge_params_list]
    else:
        target_indices = list(range(len(all_gauges_list)))

    n_gauges = len(gauge_params_list)
    gauge_ids = [g["gauge_id"] for g in gauge_params_list]

    print(f"  Spatial model: {len(all_gauges_list)} gauges, "
          f"max distance {spatial_model.dist_matrix.max():.0f} km", flush=True)

    # Build base SequenceGaugeParams (annual mean base_level);
    # these are cloned per-sequence with seasonal adjustment below.
    _base_gauge_params = [
        {
            "gauge_id": g["gauge_id"],
            "base_level": g["base_level"],
            "monthly_means": g.get("monthly_means"),
            "flood_alert": g["flood_alert"],
            "flood_warning": g["flood_warning"],
            "severe_warning": g["severe_warning"],
        }
        for g in gauge_params_list
    ]

    def _make_seasonal_params(seq) -> list:
        """Build SequenceGaugeParams with base_level adjusted for the month."""
        month = 1
        try:
            month = int(seq.sequence_start[5:7])
        except (ValueError, IndexError, TypeError):
            pass
        params = []
        for g in _base_gauge_params:
            bl = _seasonal_base_level(
                g["monthly_means"], g["base_level"], month
            )
            params.append(SequenceGaugeParams(
                gauge_id=g["gauge_id"],
                base_level=bl,
                flood_alert=g["flood_alert"],
                flood_warning=g["flood_warning"],
                severe_warning=g["severe_warning"],
            ))
        return params

    # ------------------------------------------------------------------
    # Stage 4: Compute spatial compound gauge responses
    # ------------------------------------------------------------------
    mode_str = f"1 gauge ({gauge_id})" if single_gauge_mode else f"{n_gauges} gauges"
    has_seasonal = any(g.get("monthly_means") for g in _base_gauge_params)
    base_str = "seasonal" if has_seasonal else "annual mean"
    print(f"  Computing compound gauge responses ({count:,} sequences x {mode_str})...",
          flush=True)
    print(f"  Base levels: {base_str}", flush=True)

    alert_arr   = np.array([g["flood_alert"]   for g in gauge_params_list])
    warning_arr = np.array([g["flood_warning"]  for g in gauge_params_list])
    severe_arr  = np.array([g["severe_warning"] for g in gauge_params_list])

    sequence_records, alert_count, warning_count, severe_count = compute_sequence_records(
        sequences, count, verbose, n_gauges, target_indices,
        spatial_model, rng, alert_arr, warning_arr, severe_arr,
        _make_seasonal_params, _make_precip_series, compute_sequence_gauge_response,
    )

    # ------------------------------------------------------------------
    # Stage 4b + 5: Write output
    # ------------------------------------------------------------------
    if not single_gauge_mode:
        stages.write_gaugets(
            input_dir, gauge_params_list, gauge_ids,
            sequence_records, sequences, verbose,
        )

    if single_gauge_mode:
        stages.write_single_gauge_output(
            input_dir, catchment_id, count, n_gauges,
            gauge_ids, gauge_id, sequence_records,
        )
    else:
        stages.write_split_output(
            input_dir, catchment_id, count, n_gauges,
            gauge_ids, sequence_records,
        )

    stages.run_classifier_training(
        single_gauge_mode=single_gauge_mode,
        gauge_id=gauge_id,
        gauge_params_list=gauge_params_list,
        sequence_records=sequence_records,
        count=count,
        sequences=sequences,
        spatial_model=spatial_model,
        target_indices=target_indices,
        output_dir=output_dir,
        seed=seed,
        n_gauges=n_gauges,
        train_classifier=train_classifier,
    )

    return build_summary(
        sequences, type_counts, gauge_params_list,
        alert_count=alert_count, warning_count=warning_count,
        severe_count=severe_count, t_start=t0,
    )
