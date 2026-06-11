# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package root for full license text)

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

import json
import logging
import time
from pathlib import Path
from typing import Optional

import numpy as np

from ..gauge_parser import (
    _extract_gauges, _parse_gauge, _load_gaugehd_baselines, _seasonal_base_level,
)
from ..gaugets_writer import build_summary
from ._helpers import _extract_pulse_peaks
from . import stages

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
    from port.src.storm_multi.utils.serialization import (
        save_sequences, save_summary,
        SEQUENCES_FILENAME, SUMMARY_FILENAME,
    )
    from port.src.storm_multi.models.sequence_response import (
        SequenceGaugeParams, compute_sequence_gauge_response, _make_precip_series,
    )
    from port.src.storm_multi.models.spatial_correlation import SpatialCorrelationModel

    input_dir = Path(input_dir)
    rng = np.random.RandomState(seed)

    # ------------------------------------------------------------------
    # Stage 1: Generate sequences
    # ------------------------------------------------------------------
    t0 = time.time()
    print(f"  Generating {count:,} storm sequences...", flush=True)
    sequences = generate_event_set(count=count, catchment_id=catchment_id, seed=seed)

    seq_path = input_dir / SEQUENCES_FILENAME
    sum_path = input_dir / SUMMARY_FILENAME
    save_sequences(sequences, seq_path)
    save_summary(sequences, sum_path)

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
    gauge_path = input_dir / "gauge.json"
    if not gauge_path.exists():
        logger.warning("gauge.json not found at %s — skipping spatial responses", gauge_path)
        return build_summary(sequences, type_counts, gauge_params_list=[], t_start=t0)

    with open(gauge_path) as f:
        gauge_json = json.load(f)

    # Load historical baselines from gaugehd/ (mean daily water level per gauge)
    gaugehd_dir = input_dir / "gaugehd"
    baselines = _load_gaugehd_baselines(gaugehd_dir)
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

    sequence_records = []
    alert_count = warning_count = severe_count = 0
    t2 = time.time()

    for i, seq in enumerate(sequences):
        if verbose and (i % 100 == 0) and i > 0:
            elapsed = time.time() - t2
            rate = i / elapsed
            eta = (count - i) / rate
            print(f"    [{i:,}/{count:,}]  {rate:.0f}/s  ETA {eta:.0f}s", flush=True)
        elif not verbose and (i % 2000 == 0) and i > 0:
            elapsed = time.time() - t2
            rate = i / elapsed
            eta = (count - i) / rate
            print(f"    [{i:,}/{count:,}]  ETA {eta / 60:.1f}m", flush=True)

        # Seasonal base levels: winter storms start from higher baseline
        seq_gauge_params = _make_seasonal_params(seq)

        catchment_precip = _make_precip_series(seq)
        gauge_precip_all = spatial_model.apply_to_sequence(seq, catchment_precip, rng=rng)

        peaks = np.empty(n_gauges)
        peak_hours = np.empty(n_gauges, dtype=int)
        pulse_peaks_per_gauge = []  # v2.2: per-pulse peaks per gauge

        for local_i, (gp, spatial_i) in enumerate(zip(seq_gauge_params, target_indices)):
            levels = compute_sequence_gauge_response(
                seq, gp, precip_series=gauge_precip_all[spatial_i]
            )
            pk_idx = int(np.argmax(levels))
            peaks[local_i] = levels[pk_idx]
            peak_hours[local_i] = pk_idx

            # v2.2: extract per-pulse peaks from the 168h hydrograph
            pp = _extract_pulse_peaks(levels, seq, lag=gp.response_lag_hours)
            pulse_peaks_per_gauge.append(pp)

        is_alert   = peaks >= alert_arr
        is_warning = peaks >= warning_arr
        is_severe  = peaks >= severe_arr

        if is_alert.any():
            alert_count += 1
        if is_warning.any():
            warning_count += 1
        if is_severe.any():
            severe_count += 1

        sequence_records.append({
            "sequence_id":        seq.sequence_id,
            "sequence_type":      seq.sequence_type,
            "intensity_category": seq.intensity_category,
            "num_storms":         len(seq.storms),
            "total_precip_mm":    round(seq.total_precipitation_mm, 1),
            "peaks_m":            [round(float(p), 3) for p in peaks],
            "peak_hours":         [int(h) for h in peak_hours],
            "alert":              [bool(v) for v in is_alert],
            "warning":            [bool(v) for v in is_warning],
            "severe":             [bool(v) for v in is_severe],
            "pulse_peaks":        pulse_peaks_per_gauge,
        })

    t3 = time.time()
    print(f"  Gauge responses computed in {(t3 - t2) / 60:.1f} min", flush=True)

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
