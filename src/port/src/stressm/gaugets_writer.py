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
Gaugets population, classifier summary, and pipeline summary helpers.

Extracted from pipeline.py to keep each module under 300 lines.
"""

import time
from pathlib import Path


def populate_gaugets(
    input_dir: Path,
    gauge_params_list: list,
    gauge_ids: list,
    sequence_records: list,
    sequences: list,
    verbose: bool = False,
) -> None:
    """Generate gaugets files: base 168h simulation + storm_responses.

    This replaces the standalone GaugeTimeSeriesGenerator step.  The base
    flood simulation is generated first, then storm_responses from the
    stressm sequence records are appended.  Finally stress_storms.json is
    built from the populated files.

    The result is a complete gaugets/ directory that all downstream
    consumers (propertyts, hazard, animation, stress routes) can use.
    """
    from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
    from port.src.gauge.stress_storms import generate_stress_storms

    print("\n  Generating gaugets (base simulation + storm responses)...", flush=True)

    # Step 1: Generate base 168h flood simulation files
    gen = GaugeTimeSeriesGenerator(verbose=verbose)
    result = gen.generate(simulation_hours=168)
    n_gauges = result['data']['num_gauges']
    print(f"    Base simulation: {n_gauges} gauge files  →  gaugets/", flush=True)

    # Step 2: Build per-gauge storm_responses from sequence records
    # Map gauge_id -> index in the gauge_ids list
    gid_to_idx = {gid: i for i, gid in enumerate(gauge_ids)}

    # Build per-gauge response lists
    gauge_responses: dict = {gid: [] for gid in gauge_ids}
    for rec in sequence_records:
        seq_id = rec["sequence_id"]
        peaks = rec["peaks_m"]
        alerts = rec["alert"]
        warnings = rec["warning"]
        severes = rec["severe"]

        pulse_peaks_all = rec.get("pulse_peaks", [])
        seq_type = rec.get("sequence_type", "isolated")
        num_storms = rec.get("num_storms", 1)

        for gid, idx in gid_to_idx.items():
            base = gauge_params_list[idx].get("base_level", 0.0)
            peak = peaks[idx]
            resp = {
                "storm_id": seq_id,
                "base_level_m": base,
                "peak_level_m": peak,
                "level_change_m": round(peak - base, 4),
                "exceeded_alert": alerts[idx],
                "exceeded_warning": warnings[idx],
                "exceeded_severe": severes[idx],
                "sequence_type": seq_type,
                "num_storms": num_storms,
            }
            # v2.2: per-pulse peaks for compound hydrograph superposition
            if pulse_peaks_all and idx < len(pulse_peaks_all):
                resp["pulse_peaks"] = pulse_peaks_all[idx]
            gauge_responses[gid].append(resp)

    # Step 3: Merge storm_responses into each gauge's timeseries through the seam.
    # The base-simulation gaugets were written via database in step 1, so read each
    # back, attach storm_responses, and save — works whether the backend stores them
    # as files (gaugets/GAUGE-*.json) or Postgres rows.
    import database
    gaugets_dir = input_dir / "gaugets"
    catchment = database.active_catchment()
    existing = set(database.iter_gauge_timeseries_ids(catchment))
    n_updated = 0
    for gid, responses in gauge_responses.items():
        if gid not in existing:
            continue
        data = database.get_gauge_timeseries(catchment, gid)
        data["storm_responses"] = {"responses": responses}
        database.save_gauge_timeseries(catchment, gid, data)
        n_updated += 1

    n_alert = sum(1 for r in gauge_responses[gauge_ids[0]]
                  if r["exceeded_alert"]) if gauge_ids else 0
    print(f"    Storm responses: {len(sequence_records):,} sequences × "
          f"{n_updated} gauges merged into gaugets/", flush=True)

    # Step 4: Build stress_storms/ directory from the populated gaugets
    ss_dir = input_dir / "stress_storms"
    ss_result = generate_stress_storms(
        gaugets_dir=gaugets_dir,
        output_dir=ss_dir,
        storms_json_path=input_dir / "storm_sequences.json",
    )
    print(f"    Stress storms: {ss_result['total_storms']} alert-breaching  "
          f"→  stress_storms/", flush=True)


def write_classifier_summary(results: list) -> None:
    """Persist the classifier training summary through the database seam.

    Saved under the ``classifier_training_summary`` artifact
    (``classifiers/training_summary.json`` on the file backend); the trading-stress
    routes read it back via ``database.get_classifier_training_summary``. Same
    format the predictor expects ('severe_level' / 'status' per result dict).
    """
    import database

    trained = [r for r in results if r.get('status') == 'trained']
    avg_auc = (
        sum(r['metrics']['auc_roc'] for r in trained) / len(trained)
        if trained else 0.0
    )
    summary = {
        'num_gauges': len(results),
        'num_trained': len(trained),
        'num_skipped': len(results) - len(trained),
        'avg_auc_roc': round(avg_auc, 4),
        'gauges': results,
    }
    database.save_classifier_training_summary(database.active_catchment(), summary)
    print(
        f"  training_summary written  "
        f"({len(trained)}/{len(results)} trained  avg AUC: {avg_auc:.4f})",
        flush=True,
    )


def build_summary(
    sequences, type_counts, gauge_params_list,
    alert_count=0, warning_count=0, severe_count=0,
    t_start=None,
) -> dict:
    """Build the return dict for generate_stressm()."""
    n = len(sequences)
    elapsed = time.time() - t_start if t_start else 0
    return {
        "num_sequences": n,
        "num_gauges": len(gauge_params_list),
        "type_counts": type_counts,
        "alert_sequences": alert_count,
        "warning_sequences": warning_count,
        "severe_sequences": severe_count,
        "elapsed_seconds": round(elapsed, 1),
    }
